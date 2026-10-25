"""
integrations/azure_devops/client.py

Production-safe Azure DevOps REST API Adapter for Bug Work Item creation.

Guarantees:
- Strictly outside domain lifecycle and persistence code.
- Builds RFC 6902 JSON-Patch requests required by Azure DevOps Work Items API.
- Escapes all HTML user-controlled ticket fields to prevent injection.
- Tags every work item with the canonical ART Bug ID (e.g. 'ART:ART-AGENT-001')
  to allow search-based reconciliation in case of network disconnects.
- Sanitizes all errors (strictly zero PAT tokens or Authorization headers leaked).
"""

import re
import base64
from urllib.parse import quote
from typing import Dict, Any, List, Optional, Tuple, Union
import httpx

from integrations.azure_devops.models import (
    AzureDevOpsConfig,
    AzureWorkItemResult,
    AzureDevOpsError,
    EvidenceSyncError
)


class AzureDevOpsClient:
    def __init__(self, config: AzureDevOpsConfig, http_client: Optional[httpx.Client] = None):
        self.config = config
        self._external_client = http_client

    def _get_auth_header(self) -> str:
        # Azure DevOps PAT authentication: Basic base64(:PAT)
        token_bytes = f":{self.config.pat}".encode("utf-8")
        b64_token = base64.b64encode(token_bytes).decode("utf-8")
        return f"Basic {b64_token}"

    def _mask_secrets(self, text: str) -> str:
        if not text:
            return text
        masked = text
        if self.config.pat:
            masked = masked.replace(self.config.pat, "******")
        return masked

    def _build_html_repro_steps(
        self,
        ticket: Dict[str, Any],
        canonical_bug_id: str,
        projection: Optional[Any] = None
    ) -> str:
        """
        Renders the developer-ready resolution brief into safe Azure-compatible HTML
        for Microsoft.VSTS.TCM.ReproSteps using DeveloperTicketProjection and AzureDescriptionFormatter.
        """
        # pyrefly: ignore [missing-import]
        from integrations.azure_devops.projection import (
            DeveloperTicketProjector,
            AzureDescriptionFormatter,
            DeveloperTicketProjection
        )

        if isinstance(projection, DeveloperTicketProjection):
            proj = projection
        else:
            proj = DeveloperTicketProjector.project_ticket(ticket, canonical_bug_id)

        return AzureDescriptionFormatter.format_html(proj)


    def _build_tags_string(
        self,
        ticket: Dict[str, Any],
        canonical_bug_id: str,
        projection: Optional[Any] = None
    ) -> str:
        """
        Azure DevOps System.Tags is a semicolon-delimited string.
        Includes:
        - Technical idempotency marker 'ART:<canonical_bug_id>'
        - Canonical bug ID '<canonical_bug_id>'
        - Controlled ART taxonomy tags (Product, Module, Capability, Concern)
        """
        tags = [f"ART:{canonical_bug_id}", canonical_bug_id]
        if "ART" not in tags:
            tags.append("ART")

        # Add projection tags if available
        if projection and getattr(projection, "tags", None):
            for t in projection.tags:
                t_clean = str(t).strip()
                if t_clean and t_clean not in tags:
                    tags.append(t_clean)
        else:
            module = ticket.get("module")
            if module and module != "Not provided":
                tags.append(str(module).lower())

            custom_tags = ticket.get("tags") or []
            for t in custom_tags:
                t_clean = str(t).strip()
                if t_clean and t_clean not in tags:
                    tags.append(t_clean)

        return "; ".join(tags)

    def _map_ticket_to_patch(
        self,
        ticket: Dict[str, Any],
        canonical_bug_id: str,
        parent_work_item_id: Optional[int] = None,
        assigned_to: Optional[str] = None,
        projection: Optional[Any] = None
    ) -> List[Dict[str, Any]]:
        # pyrefly: ignore [missing-import]
        from integrations.azure_devops.projection import (
            DeveloperTicketProjector,
            DeveloperTicketProjection
        )
        if isinstance(projection, DeveloperTicketProjection):
            proj = projection
        else:
            proj = DeveloperTicketProjector.project_ticket(ticket, canonical_bug_id)

        title = ticket.get("title", f"Bug {canonical_bug_id}")
        repro_html = self._build_html_repro_steps(ticket, canonical_bug_id, projection=proj)
        tags_str = self._build_tags_string(ticket, canonical_bug_id, projection=proj)

        patch = [
            {
                "op": "add",
                "path": "/fields/System.Title",
                "value": f"[{canonical_bug_id}] {title}"
            },
            {
                "op": "add",
                "path": "/fields/Microsoft.VSTS.TCM.ReproSteps",
                "value": repro_html
            },
            {
                "op": "add",
                "path": "/fields/System.Tags",
                "value": tags_str
            },
            {
                "op": "add",
                "path": "/fields/System.History",
                "value": f"Created automatically by ART Product Resolution System for {canonical_bug_id}."
            }
        ]

        # Severity mapping: canonical -> Azure Microsoft.VSTS.Common.Severity
        sev_raw = proj.severity or ticket.get("severity")
        if sev_raw and sev_raw != "Not provided":
            sev_str = str(sev_raw).strip().upper()
            sev_map = {
                "CRITICAL": "1 - Critical",
                "HIGH": "2 - High",
                "MEDIUM": "3 - Medium",
                "LOW": "4 - Low",
                "1": "1 - Critical",
                "2": "2 - High",
                "3": "3 - Medium",
                "4": "4 - Low",
            }
            azure_sev = sev_map.get(sev_str, sev_raw)
            patch.append({
                "op": "add",
                "path": "/fields/Microsoft.VSTS.Common.Severity",
                "value": azure_sev
            })

        # Priority mapping: canonical/PM -> Azure Microsoft.VSTS.Common.Priority (integer 1-4)
        pri_val = proj.priority or ticket.get("priority")
        if pri_val and pri_val != "Not provided":
            try:
                pri_int = int(pri_val)
                patch.append({
                    "op": "add",
                    "path": "/fields/Microsoft.VSTS.Common.Priority",
                    # pyrefly: ignore [bad-assignment]
                    "value": pri_int
                })
            except (ValueError, TypeError):
                pass

        # Environment mapping: Microsoft.VSTS.TCM.SystemInfo, ONLY when known/not empty/"Not provided"
        env_val = ticket.get("environment")
        if env_val and env_val.strip() and env_val.strip() != "Not provided":
            patch.append({
                "op": "add",
                "path": "/fields/Microsoft.VSTS.TCM.SystemInfo",
                "value": env_val.strip()
            })

        # Initial assignment support
        if assigned_to and str(assigned_to).strip().upper() in ("UNASSIGNED", "NOT PROVIDED", "NONE"):
            assignee = None
        else:
            assignee = assigned_to or self.config.assigned_to

        if assignee:
            patch.append({
                "op": "add",
                "path": "/fields/System.AssignedTo",
                "value": str(assignee).strip()
            })

        if parent_work_item_id:
            org_enc = quote(self.config.organization, safe="")
            proj_enc = quote(self.config.project, safe="")
            parent_url = f"https://dev.azure.com/{org_enc}/{proj_enc}/_apis/wit/workItems/{parent_work_item_id}"
            patch.append({
                "op": "add",
                "path": "/relations/-",
                # pyrefly: ignore [bad-assignment]
                "value": {
                    "rel": "System.LinkTypes.Hierarchy-Reverse",
                    "url": parent_url,
                    "attributes": {
                        "comment": "Parent Feature link established during creation"
                    }
                }
            })

        return patch

    def find_existing_work_item_by_art_id(self, canonical_bug_id: str) -> Optional[AzureWorkItemResult]:
        """
        Reconciliation mechanism for uncertain outcome:
        Queries Azure DevOps WIQL to check if a work item with tag 'ART:<canonical_bug_id>' exists.
        """
        org_enc = quote(self.config.organization, safe="")
        proj_enc = quote(self.config.project, safe="")
        url = f"https://dev.azure.com/{org_enc}/{proj_enc}/_apis/wit/wiql?api-version={self.config.api_version}"
        headers = {
            "Authorization": self._get_auth_header(),
            "Content-Type": "application/json"
        }
        # WIQL query searching for the specific canonical tag
        query = {
            "query": f"SELECT [System.Id], [System.Title] FROM WorkItems WHERE [System.TeamProject] = '{self.config.project}' AND [System.Tags] CONTAINS 'ART:{canonical_bug_id}'"
        }

        client = self._external_client or httpx.Client(timeout=self.config.timeout_seconds)
        should_close = self._external_client is None
        try:
            res = client.post(url, headers=headers, json=query)
            if res.status_code == 200:
                data = res.json()
                work_items = data.get("workItems", [])
                if work_items:
                    wi = work_items[0]
                    wi_id = int(wi["id"])
                    wi_url = wi.get("url", f"https://dev.azure.com/{org_enc}/{proj_enc}/_workitems/edit/{wi_id}")
                    return AzureWorkItemResult(
                        work_item_id=wi_id,
                        work_item_url=wi_url,
                        canonical_bug_id=canonical_bug_id,
                        is_existing=True
                    )
            return None
        except Exception:
            # Query reconciliation failure should not block standard flow
            return None
        finally:
            if should_close:
                client.close()

    def get_work_item(self, work_item_id: int, expand_relations: bool = True) -> Dict[str, Any]:
        """
        Reads a work item by ID with optional relation expansion.
        """
        org_enc = quote(self.config.organization, safe="")
        proj_enc = quote(self.config.project, safe="")
        expand_param = "&$expand=1" if expand_relations else ""
        url = (
            f"https://dev.azure.com/{org_enc}/{proj_enc}"
            f"/_apis/wit/workitems/{work_item_id}?api-version={self.config.api_version}{expand_param}"
        )
        headers = {
            "Authorization": self._get_auth_header(),
            "Content-Type": "application/json"
        }
        client = self._external_client or httpx.Client(timeout=self.config.timeout_seconds)
        should_close = self._external_client is None
        try:
            response = client.get(url, headers=headers)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                raise AzureDevOpsError(
                    code="NOT_FOUND",
                    message=f"Work item {work_item_id} not found.",
                    status_code=404
                )
            else:
                body_text = self._mask_secrets(response.text)
                raise AzureDevOpsError(
                    code="EXTERNAL_SERVICE_ERROR",
                    message=f"Failed to get work item {work_item_id}: {body_text}",
                    status_code=response.status_code
                )
        except AzureDevOpsError:
            raise
        except Exception as e:
            clean_err = self._mask_secrets(str(e))
            raise AzureDevOpsError(
                code="EXTERNAL_SERVICE_ERROR",
                message=f"Azure DevOps integration communication error: {clean_err}",
                status_code=502
            )
        finally:
            if should_close:
                client.close()

    def get_comments(self, work_item_id: int) -> List[Dict[str, Any]]:
        """
        Retrieves comments for a work item using the Azure DevOps comments API.
        Returns a list of comment dicts sorted chronologically.
        """
        org_enc = quote(self.config.organization, safe="")
        proj_enc = quote(self.config.project, safe="")
        url = (
            f"https://dev.azure.com/{org_enc}/{proj_enc}"
            f"/_apis/wit/workItems/{work_item_id}/comments?api-version=7.1-preview.3"
        )
        headers = {
            "Authorization": self._get_auth_header(),
            "Content-Type": "application/json"
        }
        client = self._external_client or httpx.Client(timeout=self.config.timeout_seconds)
        should_close = self._external_client is None
        try:
            response = client.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                return data.get("comments", [])
            elif response.status_code == 404:
                raise AzureDevOpsError(
                    code="NOT_FOUND",
                    message=f"Work item {work_item_id} comments not found.",
                    status_code=404
                )
            else:
                body_text = self._mask_secrets(response.text)
                raise AzureDevOpsError(
                    code="EXTERNAL_SERVICE_ERROR",
                    message=f"Failed to get comments for work item {work_item_id}: {body_text}",
                    status_code=response.status_code
                )
        except AzureDevOpsError:
            raise
        except Exception as e:
            clean_err = self._mask_secrets(str(e))
            raise AzureDevOpsError(
                code="EXTERNAL_SERVICE_ERROR",
                message=f"Azure DevOps integration communication error: {clean_err}",
                status_code=502
            )
        finally:
            if should_close:
                client.close()

    def get_revisions(self, work_item_id: int) -> List[Dict[str, Any]]:
        """
        Retrieves revision history for a work item using the Azure DevOps revisions API.
        Returns a list of work item revisions sorted chronologically.
        """
        org_enc = quote(self.config.organization, safe="")
        proj_enc = quote(self.config.project, safe="")
        url = (
            f"https://dev.azure.com/{org_enc}/{proj_enc}"
            f"/_apis/wit/workItems/{work_item_id}/revisions?api-version=7.1-preview.3"
        )
        headers = {
            "Authorization": self._get_auth_header(),
            "Content-Type": "application/json"
        }
        client = self._external_client or httpx.Client(timeout=self.config.timeout_seconds)
        should_close = self._external_client is None
        try:
            response = client.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                return data.get("value", [])
            return []
        except Exception:
            return []
        finally:
            if should_close:
                client.close()

    def upload_attachment(self, file_content_or_path: Any, filename: str) -> str:
        """
        Uploads an attachment file to Azure DevOps.
        Returns the attachment URL.
        """
        import os
        if isinstance(file_content_or_path, (str, bytes, os.PathLike)):
            if isinstance(file_content_or_path, (str, os.PathLike)) and os.path.exists(str(file_content_or_path)):
                with open(file_content_or_path, "rb") as f:
                    data = f.read()
            elif isinstance(file_content_or_path, bytes):
                data = file_content_or_path
            else:
                raise ValueError(f"Invalid file content or path: {file_content_or_path}")
        else:
            raise ValueError(f"Invalid file content or path type: {type(file_content_or_path)}")

        org_enc = quote(self.config.organization, safe="")
        proj_enc = quote(self.config.project, safe="")
        fname_enc = quote(os.path.basename(filename))
        url = (
            f"https://dev.azure.com/{org_enc}/{proj_enc}"
            f"/_apis/wit/attachments?fileName={fname_enc}&api-version={self.config.api_version}"
        )
        headers = {
            "Authorization": self._get_auth_header(),
            "Content-Type": "application/octet-stream"
        }
        client = self._external_client or httpx.Client(timeout=self.config.timeout_seconds)
        should_close = self._external_client is None
        try:
            res = client.post(url, headers=headers, content=data)
            if res.status_code in (200, 201):
                return res.json()["url"]
            else:
                body_text = self._mask_secrets(res.text)
                raise AzureDevOpsError(
                    code="EXTERNAL_SERVICE_ERROR",
                    message=f"Failed to upload attachment {filename}: {body_text}",
                    status_code=res.status_code
                )
        except AzureDevOpsError:
            raise
        except Exception as e:
            clean_err = self._mask_secrets(str(e))
            raise AzureDevOpsError(
                code="EXTERNAL_SERVICE_ERROR",
                message=f"Attachment upload error: {clean_err}",
                status_code=502
            )
        finally:
            if should_close:
                client.close()

    def attach_file_to_work_item(self, work_item_id: int, attachment_url: str, comment: str) -> Dict[str, Any]:
        """
        Links an uploaded attachment URL to a work item via AttachedFile relation.
        """
        org_enc = quote(self.config.organization, safe="")
        proj_enc = quote(self.config.project, safe="")
        url = (
            f"https://dev.azure.com/{org_enc}/{proj_enc}"
            f"/_apis/wit/workitems/{work_item_id}?api-version={self.config.api_version}"
        )
        headers = {
            "Authorization": self._get_auth_header(),
            "Content-Type": "application/json-patch+json"
        }
        patch = [
            {
                "op": "add",
                "path": "/relations/-",
                "value": {
                    "rel": "AttachedFile",
                    "url": attachment_url,
                    "attributes": {
                        "comment": comment
                    }
                }
            }
        ]
        client = self._external_client or httpx.Client(timeout=self.config.timeout_seconds)
        should_close = self._external_client is None
        try:
            res = client.patch(url, headers=headers, json=patch)
            if res.status_code == 200:
                return res.json()
            else:
                body_text = self._mask_secrets(res.text)
                raise AzureDevOpsError(
                    code="EXTERNAL_SERVICE_ERROR",
                    message=f"Failed to attach file to work item {work_item_id}: {body_text}",
                    status_code=res.status_code
                )
        except AzureDevOpsError:
            raise
        except Exception as e:
            clean_err = self._mask_secrets(str(e))
            raise AzureDevOpsError(
                code="EXTERNAL_SERVICE_ERROR",
                message=f"Error attaching file to work item {work_item_id}: {clean_err}",
                status_code=502
            )
        finally:
            if should_close:
                client.close()

    def sync_evidence_attachments(
        self,
        work_item_id: int,
        canonical_bug_id: str,
        file_paths: List[str]
    ) -> Tuple[int, int]:
        """
        Synchronizes evidence file attachments (images and videos) idempotently to the work item.
        Guarantees:
        - Never attach evidence belonging to another bug.
        - Check existing attachments before uploading (prevent duplicates).
        - If Azure rejects a file (size/type/API limitations), reports:
          EVIDENCE_SYNC_FAILED: <filename> — <actual reason>
        Returns: (total_attached_count, newly_uploaded_count)
        """
        import os
        wi = self.get_work_item(work_item_id, expand_relations=True)
        existing_attached = set()
        for rel in wi.get("relations", []):
            if rel.get("rel") == "AttachedFile":
                name = rel.get("attributes", {}).get("name")
                if name:
                    existing_attached.add(name)
                rel_url = rel.get("url", "")
                if "fileName=" in rel_url:
                    existing_attached.add(rel_url.split("fileName=")[-1])

        newly_uploaded = 0
        for fpath in file_paths:
            fname = os.path.basename(fpath)

            # Ownership check: Ensure evidence file belongs to canonical_bug_id
            match_file = re.search(r"ART-[A-Z]+-\d+", fname)
            if match_file and match_file.group(0) != canonical_bug_id:
                raise EvidenceSyncError(
                    filename=fname,
                    reason=f"Evidence file '{fname}' belongs to {match_file.group(0)}, not {canonical_bug_id}. Attachment rejected.",
                    status_code=400
                )
            parent_dir = os.path.basename(os.path.dirname(os.path.abspath(fpath)))
            match_dir = re.search(r"ART-[A-Z]+-\d+", parent_dir)
            if match_dir and match_dir.group(0) != canonical_bug_id:
                raise EvidenceSyncError(
                    filename=fname,
                    reason=f"Evidence file in directory '{parent_dir}' belongs to {match_dir.group(0)}, not {canonical_bug_id}. Attachment rejected.",
                    status_code=400
                )

            # Prevent duplicate uploads
            if fname in existing_attached:
                continue

            try:
                att_url = self.upload_attachment(fpath, fname)
                comment = f"Canonical evidence for {canonical_bug_id}: {fname}"
                self.attach_file_to_work_item(work_item_id, att_url, comment)
                existing_attached.add(fname)
                newly_uploaded += 1
            except Exception as e:
                clean_err = self._mask_secrets(str(e))
                if isinstance(e, AzureDevOpsError) and hasattr(e, "message"):
                    clean_err = e.message
                raise EvidenceSyncError(
                    filename=fname,
                    reason=clean_err,
                    status_code=getattr(e, "status_code", 502)
                )

        return len(existing_attached), newly_uploaded

    def update_work_item_repro_steps(self, work_item_id: int, repro_steps_html: str) -> Dict[str, Any]:
        """
        Updates Microsoft.VSTS.TCM.ReproSteps field on an existing work item.
        """
        org_enc = quote(self.config.organization, safe="")
        proj_enc = quote(self.config.project, safe="")
        url = (
            f"https://dev.azure.com/{org_enc}/{proj_enc}"
            f"/_apis/wit/workitems/{work_item_id}?api-version={self.config.api_version}"
        )
        headers = {
            "Authorization": self._get_auth_header(),
            "Content-Type": "application/json-patch+json"
        }
        patch = [
            {
                "op": "add",
                "path": "/fields/Microsoft.VSTS.TCM.ReproSteps",
                "value": repro_steps_html
            }
        ]
        client = self._external_client or httpx.Client(timeout=self.config.timeout_seconds)
        should_close = self._external_client is None
        try:
            res = client.patch(url, headers=headers, json=patch)
            if res.status_code == 200:
                return res.json()
            else:
                body_text = self._mask_secrets(res.text)
                raise AzureDevOpsError(
                    code="EXTERNAL_SERVICE_ERROR",
                    message=f"Failed to update repro steps for work item {work_item_id}: {body_text}",
                    status_code=res.status_code
                )
        except AzureDevOpsError:
            raise
        except Exception as e:
            clean_err = self._mask_secrets(str(e))
            raise AzureDevOpsError(
                code="EXTERNAL_SERVICE_ERROR",
                message=f"Error updating work item {work_item_id}: {clean_err}",
                status_code=502
            )
        finally:
            if should_close:
                client.close()

    def create_bug(
        self,
        ticket: Dict[str, Any],
        canonical_bug_id: str,
        parent_work_item_id: Optional[int] = None,
        assigned_to: Optional[str] = None,
        projection: Optional[Any] = None,
        evidence_paths: Optional[List[str]] = None
    ) -> AzureWorkItemResult:
        """
        Creates an Azure DevOps Bug work item using JSON-Patch.
        """
        # First check remote reconciliation
        reconciled = self.find_existing_work_item_by_art_id(canonical_bug_id)
        if reconciled:
            if evidence_paths:
                self.sync_evidence_attachments(reconciled.work_item_id, canonical_bug_id, evidence_paths)
            return reconciled

        org_enc = quote(self.config.organization, safe="")
        proj_enc = quote(self.config.project, safe="")
        url = (
            f"https://dev.azure.com/{org_enc}/{proj_enc}"
            f"/_apis/wit/workitems/$Bug?api-version={self.config.api_version}"
        )
        headers = {
            "Authorization": self._get_auth_header(),
            "Content-Type": "application/json-patch+json"
        }
        patch_payload = self._map_ticket_to_patch(
            ticket,
            canonical_bug_id,
            parent_work_item_id=parent_work_item_id,
            assigned_to=assigned_to,
            projection=projection
        )

        client = self._external_client or httpx.Client(timeout=self.config.timeout_seconds)
        should_close = self._external_client is None

        try:
            response = client.post(url, headers=headers, json=patch_payload)
            res = self._handle_response(response, canonical_bug_id)
            if evidence_paths:
                self.sync_evidence_attachments(res.work_item_id, canonical_bug_id, evidence_paths)
            return res
        except httpx.TimeoutException as e:
            raise AzureDevOpsError(
                code="TIMEOUT",
                message="Timeout connecting to Azure DevOps REST API.",
                status_code=504
            )
        except AzureDevOpsError:
            raise
        except Exception as e:
            clean_err = self._mask_secrets(str(e))
            raise AzureDevOpsError(
                code="EXTERNAL_SERVICE_ERROR",
                message=f"Azure DevOps integration communication error: {clean_err}",
                status_code=502
            )
        finally:
            if should_close:
                client.close()

    def _handle_response(self, response: httpx.Response, canonical_bug_id: str) -> AzureWorkItemResult:
        status_code = response.status_code

        if status_code in (200, 201):
            try:
                data = response.json()
                wi_id = int(data["id"])
                wi_url = data.get("_links", {}).get("html", {}).get("href")
                if not wi_url:
                    org_enc = quote(self.config.organization, safe="")
                    proj_enc = quote(self.config.project, safe="")
                    wi_url = f"https://dev.azure.com/{org_enc}/{proj_enc}/_workitems/edit/{wi_id}"
                return AzureWorkItemResult(
                    work_item_id=wi_id,
                    work_item_url=wi_url,
                    canonical_bug_id=canonical_bug_id,
                    is_existing=False
                )
            except Exception as e:
                raise AzureDevOpsError(
                    code="EXTERNAL_SERVICE_ERROR",
                    message="Failed to parse Azure DevOps work item response.",
                    status_code=502
                )

        # Handle specific error status codes
        body_text = self._mask_secrets(response.text)
        if status_code in (401, 403):
            raise AzureDevOpsError(
                code="AUTHENTICATION_ERROR",
                message="Azure DevOps authentication or authorization failed. Verify organization, project, and PAT permissions.",
                status_code=502
            )
        elif status_code == 404:
            raise AzureDevOpsError(
                code="NOT_FOUND",
                message=f"Azure DevOps project '{self.config.project}' or resource not found.",
                status_code=502
            )
        elif status_code == 400:
            raise AzureDevOpsError(
                code="VALIDATION_ERROR",
                message=f"Azure DevOps rejected work item payload: {body_text}",
                status_code=400
            )
        elif status_code == 429:
            raise AzureDevOpsError(
                code="RATE_LIMITED",
                message="Azure DevOps rate limit exceeded.",
                status_code=429
            )
        elif status_code >= 500:
            raise AzureDevOpsError(
                code="EXTERNAL_SERVICE_ERROR",
                message=f"Azure DevOps service error ({status_code}).",
                status_code=502
            )
        else:
            raise AzureDevOpsError(
                code="EXTERNAL_SERVICE_ERROR",
                message=f"Azure DevOps unexpected response ({status_code}): {body_text}",
                status_code=502
            )

    def _map_feature_to_patch(
        self,
        feature: Dict[str, Any],
        canonical_feature_id: str,
        parent_work_item_id: Optional[int] = None,
        assigned_to: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        import html
        title = feature.get("title", f"Feature {canonical_feature_id}")
        module = feature.get("module", "Not provided")
        classification = feature.get("classification", "NEW_FEATURE")
        prob = feature.get("problem_opportunity", "")
        curr = feature.get("current_behavior", "")
        prop = feature.get("proposed_behavior", "")
        biz = feature.get("business_impact", "")
        ux = feature.get("user_experience", "")
        guidance = feature.get("implementation_guidance", "")
        related = feature.get("related_bugs", [])
        criteria = feature.get("acceptance_criteria", [])

        desc_parts = [
            f"<div><strong>Classification:</strong> {html.escape(str(classification))}</div>",
            f"<div><strong>Module:</strong> {html.escape(str(module))}</div>",
            f"<h3>Problem / Opportunity</h3><div>{html.escape(str(prob))}</div>"
        ]
        if curr:
            desc_parts.append(f"<h3>Current Behavior</h3><div>{html.escape(str(curr))}</div>")
        if prop:
            desc_parts.append(f"<h3>Proposed Behavior</h3><div>{html.escape(str(prop))}</div>")
        if biz:
            desc_parts.append(f"<h3>Business Impact</h3><div>{html.escape(str(biz))}</div>")
        if ux:
            desc_parts.append(f"<h3>User Experience</h3><div>{html.escape(str(ux))}</div>")
        if guidance:
            desc_parts.append(f"<h3>Implementation Guidance</h3><div>{html.escape(str(guidance))}</div>")
        if related:
            rel_str = ", ".join(str(r) for r in related)
            desc_parts.append(f"<h3>Related Bugs / Dependencies</h3><div>{html.escape(rel_str)}</div>")

        description_html = "".join(desc_parts)

        ac_items = []
        if isinstance(criteria, list):
            for c in criteria:
                ac_items.append(f"<li>{html.escape(str(c))}</li>")
        elif criteria:
            ac_items.append(f"<li>{html.escape(str(criteria))}</li>")
        ac_html = f"<ol>{''.join(ac_items)}</ol>" if ac_items else "<div>Pending formal acceptance criteria.</div>"

        tags = [f"ART-ID:{canonical_feature_id}", f"ART:{canonical_feature_id}", canonical_feature_id, "ART", "Feature", str(classification)]
        if module and module != "Not provided":
            tags.append(str(module).lower())
        tags_str = "; ".join(dict.fromkeys(tags))

        patch: List[Dict[str, Any]] = [
            {
                "op": "add",
                "path": "/fields/System.Title",
                "value": f"[{canonical_feature_id}] {title}"
            },
            {
                "op": "add",
                "path": "/fields/System.Description",
                "value": description_html
            },
            {
                "op": "add",
                "path": "/fields/Microsoft.VSTS.Common.AcceptanceCriteria",
                "value": ac_html
            },
            {
                "op": "add",
                "path": "/fields/System.Tags",
                "value": tags_str
            },
            {
                "op": "add",
                "path": "/fields/System.History",
                "value": f"Created automatically by ART Feature Backlog Pipeline for {canonical_feature_id}."
            },
            {
                "op": "add",
                "path": "/fields/Microsoft.VSTS.Common.ValueArea",
                "value": "Business"
            }
        ]

        pri_val = feature.get("priority", 2)
        try:
            pri_int = int(pri_val)
            patch.append({
                "op": "add",
                "path": "/fields/Microsoft.VSTS.Common.Priority",
                "value": pri_int
            })
        except (ValueError, TypeError):
            pass

        if assigned_to and str(assigned_to).strip().upper() not in ("UNASSIGNED", "NOT PROVIDED", "NONE"):
            assignee = assigned_to
        else:
            assignee = self.config.assigned_to

        if assignee:
            patch.append({
                "op": "add",
                "path": "/fields/System.AssignedTo",
                "value": str(assignee).strip()
            })

        if parent_work_item_id:
            org_enc = quote(self.config.organization, safe="")
            proj_enc = quote(self.config.project, safe="")
            parent_url = f"https://dev.azure.com/{org_enc}/{proj_enc}/_apis/wit/workItems/{parent_work_item_id}"
            patch.append({
                "op": "add",
                "path": "/relations/-",
                "value": {
                    "rel": "System.LinkTypes.Hierarchy-Reverse",
                    "url": parent_url,
                    "attributes": {
                        "comment": "Parent Feature link established during creation under Backlog Tickets"
                    }
                }
            })

        return patch

    def create_user_story(
        self,
        feature: Dict[str, Any],
        canonical_feature_id: str,
        parent_work_item_id: Optional[int] = None,
        assigned_to: Optional[str] = None,
        evidence_paths: Optional[List[str]] = None
    ) -> AzureWorkItemResult:
        """
        Creates an Azure DevOps User Story work item using JSON-Patch.
        """
        # First check remote reconciliation
        reconciled = self.find_existing_work_item_by_art_id(canonical_feature_id)
        if reconciled:
            if evidence_paths:
                self.sync_evidence_attachments(reconciled.work_item_id, canonical_feature_id, evidence_paths)
            return reconciled

        org_enc = quote(self.config.organization, safe="")
        proj_enc = quote(self.config.project, safe="")
        url = (
            f"https://dev.azure.com/{org_enc}/{proj_enc}"
            f"/_apis/wit/workitems/$User%20Story?api-version={self.config.api_version}"
        )
        headers = {
            "Authorization": self._get_auth_header(),
            "Content-Type": "application/json-patch+json"
        }
        patch_payload = self._map_feature_to_patch(
            feature,
            canonical_feature_id,
            parent_work_item_id=parent_work_item_id,
            assigned_to=assigned_to
        )

        client = self._external_client or httpx.Client(timeout=self.config.timeout_seconds)
        should_close = self._external_client is None

        try:
            response = client.post(url, headers=headers, json=patch_payload)
            res = self._handle_response(response, canonical_feature_id)
            if evidence_paths:
                self.sync_evidence_attachments(res.work_item_id, canonical_feature_id, evidence_paths)
            return res
        except httpx.TimeoutException:
            raise AzureDevOpsError(
                code="TIMEOUT",
                message="Timeout connecting to Azure DevOps REST API.",
                status_code=504
            )
        except AzureDevOpsError:
            raise
        except Exception as e:
            clean_err = self._mask_secrets(str(e))
            raise AzureDevOpsError(
                code="EXTERNAL_SERVICE_ERROR",
                message=f"Azure DevOps integration communication error: {clean_err}",
                status_code=502
            )
        finally:
            if should_close:
                client.close()
