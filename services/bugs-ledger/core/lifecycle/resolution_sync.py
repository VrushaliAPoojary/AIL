"""
core/lifecycle/resolution_sync.py

Harness 03 — Azure Resolution & Feedback Synchronization Harness
Synchronizes post-creation Azure DevOps lifecycle changes back into the
canonical ART bug record, SQLite operational database, and master bugs ledger.

Guarantees:
- Read-only against Azure DevOps (zero mutations).
- AZURE STATE != ART VALIDATION DISPOSITION.
- A bug marked Resolved/Closed in Azure does NOT produce VERIFIED_FIXED without real ART retest evidence.
- Preserves canonical historical bug evidence; only appends/updates lifecycle sections.
- Captures and synchronizes current Azure assignee / workflow ownership.
- Distinguishes QA ownership handoff + fix from assignment alone.
- Updates the existing primary Bugs-table row in ART_PRODUCT_VALIDATION_LEDGER.md:
    * Primary Status (e.g. BLOCKED for PRODUCT_DECISION_PENDING)
    * Primary Owner (e.g. Chiranjeevi, Prajwal, Unassigned)
    * Developer Update
    * Primary Retest (e.g. Not Required, Required)
- Recomputes Summary from all primary Bugs rows (Total Bugs, Open, Fixing, Retest, Verified, Closed, Blocked).
- Enforces Summary Invariant: Open + Fixing + Retest + Verified + Closed + Blocked == Total Bugs.
- Stale Local Projection Reconciliation: Reconciles stale local ledger projection even if Azure has no change.
- Idempotent: returns NO_CHANGE when Azure has not changed AND local projections are already reconciled.
"""

import os
import re
import html
import uuid
import sqlite3
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass

from integrations.azure_devops.client import AzureDevOpsClient
from integrations.azure_devops.models import (
    AzureDevOpsConfig,
    AzureDevOpsError,
)
from core.storage.db import get_connection
from core.storage.integrations import get_external_work_item
from core.query.service import InvestigationQueryService


DEFAULT_QA_OWNER = "Chiranjeevi"


def get_qa_owner() -> str:
    """Returns the configured QA / Retest owner from environment or default."""
    return os.environ.get("ART_QA_OWNER", DEFAULT_QA_OWNER).strip()


def is_qa_owner(identity: Optional[str]) -> bool:
    """Checks whether an identity string matches the configured QA owner."""
    if not identity:
        return False
    qa_owner = get_qa_owner().lower()
    return qa_owner in identity.strip().lower()


VALID_DISPOSITIONS = {
    "OPEN",
    "IN_PROGRESS",
    "FIX_CLAIMED",
    "RETEST_REQUIRED",
    "VERIFIED_FIXED",
    "REPRODUCED_AFTER_FIX",
    "INTENTIONAL_BEHAVIOR",
    "PRODUCT_DECISION_PENDING",
    "NOT_A_BUG",
    "DUPLICATE",
    "BLOCKED",
}

VALID_ACTIONS = {
    "NONE",
    "AWAIT_DEVELOPER",
    "AWAIT_PRODUCT_DECISION",
    "RETEST",
    "PROVIDE_INFORMATION",
    "REOPEN_RECOMMENDED",
    "REVIEW_DUPLICATE",
    "INVESTIGATE_BLOCKER",
}

DISPOSITION_TO_PRIMARY_STATUS = {
    "PRODUCT_DECISION_PENDING": "BLOCKED",
    "BLOCKED": "BLOCKED",
    "INTENTIONAL_BEHAVIOR": "CLOSED",
    "NOT_A_BUG": "CLOSED",
    "DUPLICATE": "CLOSED",
    "VERIFIED_FIXED": "VERIFIED",
    "RETEST_REQUIRED": "RETEST",
    "IN_PROGRESS": "FIXING",
    "REPRODUCED_AFTER_FIX": "OPEN",
    "FIX_CLAIMED": "FIXING",
    "OPEN": "OPEN",
}


@dataclass
class ResolutionSyncResult:
    success: bool
    status: str  # UPDATED, NO_CHANGE, FAILED
    canonical_bug_id: str
    work_item_id: Optional[int] = None
    azure_state: Optional[str] = None
    azure_reason: Optional[str] = None
    new_developer_feedback: bool = False
    art_disposition: Optional[str] = None
    retest_required: bool = False
    action_required: Optional[str] = None
    assessment_reason: Optional[str] = None
    developer_comment: Optional[str] = None
    changed_by: Optional[str] = None
    current_assignee: Optional[str] = None
    previous_assignee: Optional[str] = None
    lifecycle_updated_at: Optional[str] = None
    primary_status: Optional[str] = None
    primary_owner: Optional[str] = None
    primary_retest: Optional[str] = None
    primary_developer_update: Optional[str] = None
    ledger_updated: bool = False
    canonical_history_updated: bool = False
    summary_recomputed: bool = False
    summary_invariant: bool = False
    lifecycle_table_updated: bool = False
    ledger_consistent: bool = False
    azure_mutations: int = 0
    blocker: Optional[str] = None


def strip_html(text: str) -> str:
    """Removes HTML tags and unescapes HTML entities."""
    if not text:
        return ""
    clean = re.sub(r"<[^>]+>", " ", text)
    clean = html.unescape(clean)
    return " ".join(clean.split()).strip()


def is_system_comment(text: str) -> bool:
    """Detects automated/system comments to exclude from human developer feedback."""
    clean = strip_html(text).lower()
    if "created automatically by art" in clean:
        return True
    if "synchronized via art" in clean:
        return True
    if "attached by art" in clean:
        return True
    return False


def map_disposition_to_primary_ledger(
    disposition: str,
    retest_required: bool,
    developer_comment: Optional[str],
    assessment_reason: Optional[str] = None,
    current_assignee: Optional[str] = None,
) -> Tuple[str, str, str, str]:
    """
    Maps an ART disposition and ownership to primary Bugs table values per Sections 16A, 31K, 32F:
    Returns (primary_status, primary_owner, primary_retest, primary_developer_update).
    """
    primary_status = DISPOSITION_TO_PRIMARY_STATUS.get(disposition, "OPEN")
    primary_owner = (current_assignee or "Unassigned").strip()

    if disposition == "VERIFIED_FIXED":
        primary_retest = "Passed"
    elif disposition == "REPRODUCED_AFTER_FIX":
        primary_retest = "Failed"
    elif retest_required:
        primary_retest = "Required"
    elif disposition in ("PRODUCT_DECISION_PENDING", "INTENTIONAL_BEHAVIOR", "NOT_A_BUG", "DUPLICATE", "BLOCKED"):
        primary_retest = "Not Required"
    elif disposition in ("OPEN", "IN_PROGRESS"):
        primary_retest = "Pending."
    elif retest_required is False:
        primary_retest = "Not Required"
    else:
        primary_retest = "Pending."

    comment_clean = (developer_comment or "").strip()
    if comment_clean:
        if not comment_clean.endswith((".", "!", "?")):
            comment_clean += "."
        primary_dev_update = f"{disposition}: {comment_clean}"
    elif assessment_reason:
        reason_clean = assessment_reason.strip()
        if not reason_clean.endswith((".", "!", "?")):
            reason_clean += "."
        primary_dev_update = f"{disposition}: {reason_clean}"
    else:
        primary_dev_update = f"{disposition}."

    return primary_status, primary_owner, primary_retest, primary_dev_update


def derive_disposition_and_action(
    azure_state: str,
    azure_reason: Optional[str],
    developer_feedback: Optional[str],
    current_assignee: Optional[str] = None,
    previous_assignee: Optional[str] = None,
    has_art_retest_evidence: bool = False,
    retest_passed: Optional[bool] = None,
) -> Tuple[str, bool, str, str]:
    """
    Evaluates Azure state, reason, current assignee, human developer comments, and local ART retest evidence
    per Sections 9, 31E-J, and 32C to determine: (ART disposition, retest_required, action_required, assessment_reason).
    """
    state_norm = (azure_state or "").strip().lower()
    reason_norm = (azure_reason or "").strip().lower()
    feedback_clean = strip_html(developer_feedback or "")
    fb_lower = feedback_clean.lower()
    is_qa = is_qa_owner(current_assignee)

    # 1. Real ART retest evidence takes precedence
    if has_art_retest_evidence:
        if retest_passed is True:
            return (
                "VERIFIED_FIXED",
                False,
                "NONE",
                "ART retest confirmed that the original defect no longer reproduces and all Acceptance Criteria pass.",
            )
        elif retest_passed is False:
            return (
                "REPRODUCED_AFTER_FIX",
                False,
                "REOPEN_RECOMMENDED",
                "ART retest reproduced the original defect after claimed fix; reopening is recommended.",
            )

    # 2. Check human developer feedback signals
    if feedback_clean:
        # Product decision pending: mentions intentional for now / discuss with / under discussion / product confirmation
        if any(kw in fb_lower for kw in [
            "intentional for now", "will discuss", "discuss with",
            "decision pending", "under discussion", "discuss and change",
            "product confirmation required", "product confirmation", "product decision"
        ]):
            return (
                "PRODUCT_DECISION_PENDING",
                False,
                "AWAIT_PRODUCT_DECISION",
                f"Azure is marked {azure_state}/{azure_reason or 'Not provided'}, but developer feedback indicates the behavior is intentional for now and pending product discussion. No changed implementation is ready for retest.",
            )

        # Definitively intentional behavior without pending decision
        if any(kw in fb_lower for kw in [
            "is intentional behavior", "intentional and will remain",
            "as designed", "not a bug", "intended behavior"
        ]):
            return (
                "INTENTIONAL_BEHAVIOR",
                False,
                "NONE",
                "Authoritative developer/product feedback confirmed the behavior is intentional and as designed.",
            )

        # Duplicate
        if any(kw in fb_lower for kw in ["duplicate of", "duplicate bug", "is a duplicate"]):
            return (
                "DUPLICATE",
                False,
                "REVIEW_DUPLICATE",
                "Developer feedback identified the defect as a duplicate of another work item.",
            )

        # Cannot reproduce / need more info / workflow request
        if any(kw in fb_lower for kw in [
            "cannot reproduce", "unable to reproduce", "need more info",
            "please provide", "more details needed", "workflow used to reproduce",
            "provide additional reproduction", "provide the workflow"
        ]):
            return (
                "BLOCKED",
                False,
                "PROVIDE_INFORMATION",
                "Developer requested additional reproduction information or could not reproduce.",
            )

        # Explicit retest request
        if any(kw in fb_lower for kw in [
            "please verify", "please retest", "retest", "fixed and deployed",
            "deployed. please verify", "available in build", "ready for testing"
        ]):
            return (
                "RETEST_REQUIRED",
                True,
                "RETEST",
                "Developer stated fix is implemented/deployed and requested verification against original Acceptance Criteria.",
            )

        # Fix completed / implemented / resolved
        if any(kw in fb_lower for kw in ["fixed", "implemented", "resolved", "fix completed", "ui updated", "change deployed"]):
            if is_qa:
                return (
                    "RETEST_REQUIRED",
                    True,
                    "RETEST",
                    f"Issue fix completed and assigned to QA owner ({current_assignee}) for retest.",
                )
            else:
                return (
                    "FIX_CLAIMED",
                    False,
                    "AWAIT_DEVELOPER",
                    f"Developer ({current_assignee or 'engineering'}) claimed fix is completed, but verification has not been requested or handed off to QA.",
                )

        # Active development
        if any(kw in fb_lower for kw in ["investigating", "working on", "in progress", "active"]):
            return (
                "IN_PROGRESS",
                False,
                "AWAIT_DEVELOPER",
                f"Azure work item is actively under investigation or development by {current_assignee or 'engineering'}.",
            )

    # 3. Azure State & Assignee signals when no specific comment keywords matched
    if state_norm in ("resolved", "closed"):
        if reason_norm in ("by design", "as designed"):
            return (
                "INTENTIONAL_BEHAVIOR",
                False,
                "NONE",
                f"Azure work item marked {azure_state} with reason {azure_reason}.",
            )
        elif reason_norm == "duplicate":
            return (
                "DUPLICATE",
                False,
                "REVIEW_DUPLICATE",
                "Azure work item closed as Duplicate.",
            )
        elif reason_norm == "cannot reproduce":
            return (
                "BLOCKED",
                False,
                "PROVIDE_INFORMATION",
                "Azure work item closed as Cannot Reproduce.",
            )
        else:
            # Resolved/Fixed or Closed/Fixed - NEVER VERIFIED_FIXED without ART retest!
            if is_qa:
                return (
                    "RETEST_REQUIRED",
                    True,
                    "RETEST",
                    f"Azure work item moved to {azure_state} ({azure_reason or 'Fixed'}) and assigned to QA owner ({current_assignee}) for retest.",
                )
            else:
                return (
                    "FIX_CLAIMED",
                    False,
                    "AWAIT_DEVELOPER",
                    f"Azure work item moved to {azure_state} ({azure_reason or 'Fixed'}), but developer ({current_assignee or 'engineering'}) still owns ticket; no ART retest has verified the fix.",
                )

    if state_norm in ("active", "in progress"):
        return (
            "IN_PROGRESS",
            False,
            "AWAIT_DEVELOPER",
            f"Azure work item is actively under investigation or development by {current_assignee or 'engineering'}.",
        )

    # Default
    return (
        "OPEN",
        False,
        "AWAIT_DEVELOPER",
        "Issue remains open in Azure with no implementation or resolution claim established.",
    )


class AzureResolutionSyncHarness:
    """
    Production Harness 03 implementation for ART bug resolution lifecycle synchronization.
    """

    def __init__(self, repo_root: str, db_path: Optional[str] = None):
        self.repo_root = os.path.abspath(repo_root)
        self.bugs_dir = os.path.join(self.repo_root, "ART-Product-Validation", "bugs")
        if not os.path.isdir(self.bugs_dir):
            alt_dir = os.path.join(self.repo_root, "services", "bugs-ledger", "ART-Product-Validation", "bugs")
            if os.path.isdir(alt_dir):
                self.bugs_dir = alt_dir

        self.ledger_path = os.path.join(self.repo_root, "ART-Product-Validation", "ART_PRODUCT_VALIDATION_LEDGER.md")
        if not os.path.isfile(self.ledger_path):
            alt_ledger = os.path.join(self.repo_root, "services", "bugs-ledger", "ART-Product-Validation", "ART_PRODUCT_VALIDATION_LEDGER.md")
            if os.path.isfile(alt_ledger):
                self.ledger_path = alt_ledger

        self.db_path = db_path or os.path.join(self.repo_root, ".local", "art_product_resolution.db")
        self._init_sqlite_schema()

    def _init_sqlite_schema(self) -> None:
        """Ensures the backward-compatible azure_resolution_syncs table exists in the operational DB."""
        if not os.path.exists(os.path.dirname(self.db_path)):
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
            CREATE TABLE IF NOT EXISTS azure_resolution_syncs (
                id TEXT PRIMARY KEY,
                investigation_key TEXT NOT NULL,
                canonical_bug_id TEXT NOT NULL,
                work_item_id INTEGER NOT NULL,
                azure_state TEXT NOT NULL,
                azure_reason TEXT NULL,
                changed_by TEXT NULL,
                last_comment_id TEXT NULL,
                last_comment_text TEXT NULL,
                art_disposition TEXT NOT NULL,
                retest_required INTEGER NOT NULL,
                action_required TEXT NOT NULL,
                assessment_reason TEXT NULL,
                synced_at TEXT NOT NULL,
                assigned_to TEXT NULL,
                assigned_to_email TEXT NULL,
                previous_assigned_to TEXT NULL,
                lifecycle_updated_at TEXT NULL
            );
            """)
            # Check existing columns and alter table if needed
            cursor = conn.execute("PRAGMA table_info(azure_resolution_syncs)")
            existing_cols = {row[1] for row in cursor.fetchall()}
            for col_name, col_type in [
                ("assigned_to", "TEXT NULL"),
                ("assigned_to_email", "TEXT NULL"),
                ("previous_assigned_to", "TEXT NULL"),
                ("lifecycle_updated_at", "TEXT NULL"),
            ]:
                if col_name not in existing_cols:
                    try:
                        conn.execute(f"ALTER TABLE azure_resolution_syncs ADD COLUMN {col_name} {col_type}")
                    except Exception:
                        pass
            conn.commit()
        finally:
            conn.close()

    def find_canonical_bug_file(self, canonical_bug_id: str) -> Optional[Tuple[str, str, str]]:
        """
        Locates the canonical bug Markdown file across all feature folders.
        Returns (full_path, feature_folder, slug_folder) or None.
        """
        if not os.path.exists(self.bugs_dir):
            return None
        for feat_name in os.listdir(self.bugs_dir):
            feat_path = os.path.join(self.bugs_dir, feat_name)
            if not os.path.isdir(feat_path):
                continue
            for bug_folder in os.listdir(feat_path):
                if bug_folder.startswith(f"{canonical_bug_id}__") or bug_folder == canonical_bug_id:
                    candidate = os.path.join(feat_path, bug_folder, f"{canonical_bug_id}.md")
                    if os.path.isfile(candidate):
                        return candidate, feat_name, bug_folder
        return None

    def read_canonical_azure_metadata(self, md_path: str) -> Dict[str, Any]:
        """Extracts Work Item ID and Azure DevOps metadata from canonical bug markdown."""
        with open(md_path, "r", encoding="utf-8") as f:
            content = f.read()

        meta: Dict[str, Any] = {}
        wi_match = re.search(r"-\s*\*\*Work Item ID:\*\*\s*(.+)", content)
        if wi_match:
            val = wi_match.group(1).strip()
            if val.isdigit():
                meta["work_item_id"] = int(val)
            else:
                meta["work_item_id"] = None

        url_match = re.search(r"-\s*\*\*URL:\*\*\s*(.+)", content)
        if url_match:
            meta["url"] = url_match.group(1).strip()

        parent_match = re.search(r"-\s*\*\*Parent Feature ID:\*\*\s*(.+)", content)
        if parent_match:
            val = parent_match.group(1).strip()
            if val.isdigit():
                meta["parent_feature_id"] = int(val)

        status_match = re.search(r"-\s*\*\*Sync Status:\*\*\s*(.+)", content)
        if status_match:
            meta["sync_status"] = status_match.group(1).strip()

        # Metadata Status
        meta_status_match = re.search(r"-\s*\*\*Status:\*\*\s*([A-Za-z_]+)", content)
        if meta_status_match:
            meta["metadata_status"] = meta_status_match.group(1).strip().upper()

        return meta

    def get_latest_local_sync(self, canonical_bug_id: str) -> Optional[Dict[str, Any]]:
        """Reads the most recent sync event from SQLite."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            row = conn.execute(
                "SELECT * FROM azure_resolution_syncs WHERE canonical_bug_id = ? ORDER BY synced_at DESC LIMIT 1",
                (canonical_bug_id,)
            ).fetchone()
            if row:
                return dict(row)
            return None
        finally:
            conn.close()

    def check_is_local_stale(
        self,
        canonical_bug_id: str,
        md_path: str,
        expected_status: str,
        expected_owner: str,
        expected_retest: str,
        expected_dev_update: str,
        expected_disposition: str,
    ) -> bool:
        """
        Checks whether any of the local projections (ledger row, ledger summary, markdown, sqlite)
        are stale or inconsistent with the expected resolution state.
        """
        # 1. Check canonical markdown metadata, disposition, and current assignee
        if os.path.isfile(md_path):
            with open(md_path, "r", encoding="utf-8") as f:
                md_content = f.read()
            m = re.search(r"-\s*\*\*Status:\*\*\s*([A-Za-z_]+)", md_content)
            if not m or m.group(1).strip().upper() != expected_status:
                return True
            if f"- **ART Disposition:** {expected_disposition}" not in md_content:
                return True
            if expected_owner:
                m_owner = re.search(r"-\s*\*\*Current Azure Assignee:\*\*\s*(.+)", md_content)
                if not m_owner or m_owner.group(1).strip() != expected_owner:
                    return True
        else:
            return True

        # 2. Check SQLite investigations status and assignee
        if os.path.isfile(self.db_path):
            conn = sqlite3.connect(self.db_path)
            try:
                row = conn.execute(
                    "SELECT status, assignee FROM investigations WHERE canonical_bug_id = ?",
                    (canonical_bug_id,)
                ).fetchone()
                if not row or (row[0] or "").upper() != expected_status:
                    return True
                if expected_owner and (row[1] or "").strip() != expected_owner:
                    return True
            finally:
                conn.close()

        # 3. Check primary ledger row
        if os.path.isfile(self.ledger_path):
            with open(self.ledger_path, "r", encoding="utf-8") as f:
                ledger = f.read()

            # Check if ledger table has Owner column
            bugs_sec_match = re.search(r"## Bugs\n(.*?)(?=(\n## |\Z))", ledger, flags=re.DOTALL)
            if not bugs_sec_match:
                return True
            bugs_text = bugs_sec_match.group(1)
            has_owner_col = "| Owner |" in bugs_text or "| owner |" in bugs_text.lower()

            if has_owner_col:
                pattern = rf"\|\s*\[{re.escape(canonical_bug_id)}\]\((?:<[^>]+>|[^)]+)\)\s*\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|"
                match = re.search(pattern, ledger)
                if not match:
                    return True
                row_status = match.group(3).strip().upper()
                row_owner = match.group(4).strip()
                row_dev = match.group(5).strip()
                row_retest = match.group(6).strip()

                if row_status != expected_status:
                    return True
                if row_owner != expected_owner:
                    return True
                if row_retest != expected_retest:
                    return True
                if row_dev != expected_dev_update:
                    return True
            else:
                pattern = rf"\|\s*\[{re.escape(canonical_bug_id)}\]\((?:<[^>]+>|[^)]+)\)\s*\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|"
                match = re.search(pattern, ledger)
                if not match:
                    return True
                row_status = match.group(3).strip().upper()
                row_dev = match.group(4).strip()
                row_retest = match.group(5).strip()

                if row_status != expected_status:
                    return True
                if row_retest != expected_retest:
                    return True
                if row_dev != expected_dev_update:
                    return True

            # Check detailed lifecycle tracking table
            track_pattern = rf"\|\s*{re.escape(canonical_bug_id)}\s*\|[^|]+\|[^|]+\|[^|]+\|[^|]+\|\s*([^|]+)\|"
            track_match = re.search(track_pattern, ledger)
            if not track_match or track_match.group(1).strip() != expected_disposition:
                return True

            # 4. Check summary counts consistency
            summary_match = re.search(r"-\s*\*\*Blocked:\*\*\s*(\d+)", ledger)
            if expected_status == "BLOCKED" and summary_match and int(summary_match.group(1)) == 0:
                return True
        else:
            return True

        return False

    def sync_bug(
        self,
        canonical_bug_id: str,
        force_sync: bool = False,
        client: Optional[AzureDevOpsClient] = None
    ) -> ResolutionSyncResult:
        """
        Executes Harness 03 resolution synchronization for a given Bug ID.
        """
        # 1. Locate canonical bug
        loc = self.find_canonical_bug_file(canonical_bug_id)
        if not loc:
            return ResolutionSyncResult(
                success=False,
                status="FAILED",
                canonical_bug_id=canonical_bug_id,
                blocker="CANONICAL BUG NOT FOUND"
            )
        md_path, feat_folder, slug_folder = loc

        # 2. Check canonical Azure metadata
        azure_meta = self.read_canonical_azure_metadata(md_path)
        wi_id = azure_meta.get("work_item_id")
        if not wi_id or azure_meta.get("sync_status") == "NOT_SYNCED":
            return ResolutionSyncResult(
                success=False,
                status="FAILED",
                canonical_bug_id=canonical_bug_id,
                blocker="AZURE NOT SYNCED"
            )

        # 3. Check SQLite reference consistency
        conn = get_connection(self.db_path)
        record_key = None
        try:
            q_service = InvestigationQueryService(conn)
            inv_data = q_service.get_by_canonical_bug_id(canonical_bug_id)
            if not inv_data:
                return ResolutionSyncResult(
                    success=False,
                    status="FAILED",
                    canonical_bug_id=canonical_bug_id,
                    blocker="INVESTIGATION RECORD NOT FOUND IN SQLITE"
                )
            record_key = inv_data["record_key"]
            ext = get_external_work_item(conn, record_key, system="AZURE_DEVOPS")
            if ext and ext.get("external_id") and int(ext["external_id"]) != wi_id:
                return ResolutionSyncResult(
                    success=False,
                    status="FAILED",
                    canonical_bug_id=canonical_bug_id,
                    blocker="AZURE REFERENCE CONFLICT"
                )
        finally:
            conn.close()

        # 4. Azure Client Preflight (READ-ONLY)
        if client is None:
            config = AzureDevOpsConfig.from_env()
            client = AzureDevOpsClient(config)

        try:
            wi = client.get_work_item(wi_id, expand_relations=True)
        except AzureDevOpsError as ade:
            return ResolutionSyncResult(
                success=False,
                status="FAILED",
                canonical_bug_id=canonical_bug_id,
                blocker=f"AZURE GET FAILED: {ade.message}"
            )

        fields = wi.get("fields", {})
        wi_type = fields.get("System.WorkItemType")
        if wi_type != "Bug":
            return ResolutionSyncResult(
                success=False,
                status="FAILED",
                canonical_bug_id=canonical_bug_id,
                blocker=f"WORK ITEM TYPE MISMATCH: expected 'Bug', got '{wi_type}'"
            )

        tags_str = fields.get("System.Tags", "")
        if f"ART:{canonical_bug_id}" not in tags_str:
            return ResolutionSyncResult(
                success=False,
                status="FAILED",
                canonical_bug_id=canonical_bug_id,
                blocker=f"MISSING ART TAG MARKER: 'ART:{canonical_bug_id}' not found in '{tags_str}'"
            )

        # 5. Fetch Azure Lifecycle Snapshot (Section 32A)
        azure_state = fields.get("System.State", "Unknown")
        azure_reason = fields.get("System.Reason")
        changed_date = fields.get("System.ChangedDate")
        changed_by_field = fields.get("System.ChangedBy", {})
        if isinstance(changed_by_field, dict):
            changed_by_name = changed_by_field.get("displayName") or "Unknown"
        else:
            changed_by_name = str(changed_by_field or "Unknown")

        # Assignee details (Section 31A)
        assigned_to_field = fields.get("System.AssignedTo")
        assigned_to_name = "Unassigned"
        assigned_to_email = None
        if isinstance(assigned_to_field, dict):
            assigned_to_name = assigned_to_field.get("displayName") or "Unassigned"
            assigned_to_email = assigned_to_field.get("uniqueName")
        elif assigned_to_field:
            assigned_to_name = str(assigned_to_field).strip()

        # Comments
        try:
            comments = client.get_comments(wi_id)
        except Exception:
            comments = []

        # Find latest human developer comment
        latest_human_comment = None
        latest_comment_id = None
        latest_comment_date = None
        for c in reversed(comments):
            c_text = c.get("text", "")
            if not is_system_comment(c_text):
                latest_human_comment = strip_html(c_text)
                latest_comment_id = str(c.get("id"))
                latest_comment_date = c.get("createdDate")
                author = c.get("createdBy", {}).get("displayName")
                if author:
                    changed_by_name = author
                break

        lifecycle_updated_at = latest_comment_date or changed_date

        # Determine previous assignee from local sync or Azure revisions
        last_sync = self.get_latest_local_sync(canonical_bug_id)
        previous_assignee = None
        if last_sync and last_sync.get("assigned_to"):
            previous_assignee = last_sync.get("assigned_to")
        else:
            # Check revisions if available
            try:
                if hasattr(client, "get_revisions"):
                    revs = client.get_revisions(wi_id)
                    if len(revs) > 1:
                        prev_fields = revs[-2].get("fields", {})
                        prev_assignee_field = prev_fields.get("System.AssignedTo")
                        if isinstance(prev_assignee_field, dict):
                            previous_assignee = prev_assignee_field.get("displayName")
                        elif prev_assignee_field:
                            previous_assignee = str(prev_assignee_field)
            except Exception:
                pass

        # 6. Check if local approved ART retest evidence exists
        has_retest = False
        retest_passed = None
        conn_check = sqlite3.connect(self.db_path)
        try:
            r_rows = conn_check.execute(
                "SELECT * FROM retest_artifacts WHERE investigation_key = ?",
                (record_key,)
            ).fetchall()
            if r_rows:
                has_retest = True
        finally:
            conn_check.close()

        # 7. Derive Disposition, Retest, Action, and Primary Status (Section 31E-J, 32C)
        disposition, retest_req, action_req, assessment_reason = derive_disposition_and_action(
            azure_state=azure_state,
            azure_reason=azure_reason,
            developer_feedback=latest_human_comment,
            current_assignee=assigned_to_name,
            previous_assignee=previous_assignee,
            has_art_retest_evidence=has_retest,
            retest_passed=retest_passed,
        )

        primary_status, primary_owner, primary_retest, primary_dev_update = map_disposition_to_primary_ledger(
            disposition=disposition,
            retest_required=retest_req,
            developer_comment=latest_human_comment,
            assessment_reason=assessment_reason,
            current_assignee=assigned_to_name,
        )

        # 8. Change Detection against last local sync & local ledger staleness
        is_meaningful_change = False
        if last_sync is None:
            is_meaningful_change = True
        else:
            if (
                last_sync.get("azure_state") != azure_state
                or last_sync.get("azure_reason") != azure_reason
                or (latest_comment_id and str(last_sync.get("last_comment_id")) != latest_comment_id)
                or (assigned_to_name and last_sync.get("assigned_to") != assigned_to_name)
            ):
                is_meaningful_change = True

        # Check if local ledger or files are stale even if Azure didn't change
        is_local_stale = self.check_is_local_stale(
            canonical_bug_id=canonical_bug_id,
            md_path=md_path,
            expected_status=primary_status,
            expected_owner=primary_owner,
            expected_retest=primary_retest,
            expected_dev_update=primary_dev_update,
            expected_disposition=disposition,
        )

        if not is_meaningful_change and not is_local_stale and not force_sync:
            # Everything is already up to date and consistent
            ledger_consistent = self.verify_ledger_consistency(
                canonical_bug_id=canonical_bug_id,
                expected_status=primary_status,
                expected_disposition=disposition,
                expected_owner=primary_owner,
                expected_retest=primary_retest,
                expected_dev_update=primary_dev_update,
            )
            return ResolutionSyncResult(
                success=True,
                status="NO_CHANGE",
                canonical_bug_id=canonical_bug_id,
                work_item_id=wi_id,
                azure_state=azure_state,
                azure_reason=azure_reason,
                new_developer_feedback=False,
                art_disposition=disposition,
                retest_required=retest_req,
                action_required=action_req,
                assessment_reason=assessment_reason,
                developer_comment=latest_human_comment,
                changed_by=changed_by_name,
                current_assignee=assigned_to_name,
                previous_assignee=previous_assignee,
                lifecycle_updated_at=lifecycle_updated_at,
                primary_status=primary_status,
                primary_owner=primary_owner,
                primary_retest=primary_retest,
                primary_developer_update=primary_dev_update,
                ledger_updated=False,
                canonical_history_updated=False,
                summary_recomputed=True,
                summary_invariant=True,
                lifecycle_table_updated=True,
                ledger_consistent=ledger_consistent,
                azure_mutations=0,
            )

        now_iso = datetime.now(timezone.utc).isoformat()
        today_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        # 9. Update Canonical Bug Markdown (Metadata Status, Resolution Status, Resolution History)
        self._update_markdown_file(
            md_path=md_path,
            wi_id=wi_id,
            azure_state=azure_state,
            azure_reason=azure_reason,
            changed_by=changed_by_name,
            current_assignee=assigned_to_name,
            previous_assignee=previous_assignee,
            developer_comment=latest_human_comment,
            disposition=disposition,
            primary_status=primary_status,
            retest_required=retest_req,
            action_required=action_req,
            assessment_reason=assessment_reason,
            lifecycle_updated_at=lifecycle_updated_at,
            sync_timestamp=now_iso,
            today_date=today_date,
        )

        # 10. Update SQLite investigations & azure_resolution_syncs
        conn_update = sqlite3.connect(self.db_path)
        try:
            conn_update.execute(
                "UPDATE investigations SET status = ?, assignee = ?, updated_at = ? WHERE canonical_bug_id = ?",
                (primary_status, assigned_to_name, now_iso, canonical_bug_id)
            )
            # Record in azure_resolution_syncs
            event_id = f"RSYNC-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}-{uuid.uuid4().hex[:6]}-{canonical_bug_id}"
            conn_update.execute("""
            INSERT OR REPLACE INTO azure_resolution_syncs (
                id, investigation_key, canonical_bug_id, work_item_id,
                azure_state, azure_reason, changed_by, last_comment_id,
                last_comment_text, art_disposition, retest_required,
                action_required, assessment_reason, synced_at,
                assigned_to, assigned_to_email, previous_assigned_to, lifecycle_updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event_id,
                record_key,
                canonical_bug_id,
                wi_id,
                azure_state,
                azure_reason,
                changed_by_name,
                latest_comment_id,
                latest_human_comment,
                disposition,
                1 if retest_req else 0,
                action_req,
                assessment_reason,
                now_iso,
                assigned_to_name,
                assigned_to_email,
                previous_assignee,
                lifecycle_updated_at,
            ))
            conn_update.commit()
        finally:
            conn_update.close()

        # 11. Update Master Bugs Ledger (Section 16D, 31K, 32F)
        (
            primary_row_updated,
            lifecycle_table_updated,
            summary_recomputed,
            summary_invariant,
        ) = self._update_master_ledger(
            canonical_bug_id=canonical_bug_id,
            feature_name=feat_folder,
            wi_id=wi_id,
            azure_state=azure_state,
            azure_reason=azure_reason,
            disposition=disposition,
            primary_status=primary_status,
            primary_owner=primary_owner,
            primary_retest=primary_retest,
            primary_dev_update=primary_dev_update,
            retest_required=retest_req,
            action_required=action_req,
            sync_timestamp=now_iso,
            summary_text=latest_human_comment or assessment_reason,
        )

        if not primary_row_updated:
            return ResolutionSyncResult(
                success=False,
                status="FAILED",
                canonical_bug_id=canonical_bug_id,
                blocker="PRIMARY LEDGER ROW NOT SYNCHRONIZED",
                ledger_updated=False,
                summary_recomputed=summary_recomputed,
                summary_invariant=summary_invariant,
                lifecycle_table_updated=lifecycle_table_updated,
            )

        if not summary_recomputed:
            return ResolutionSyncResult(
                success=False,
                status="FAILED",
                canonical_bug_id=canonical_bug_id,
                blocker="LEDGER SUMMARY NOT SYNCHRONIZED",
                ledger_updated=False,
                summary_recomputed=False,
                summary_invariant=summary_invariant,
                lifecycle_table_updated=lifecycle_table_updated,
            )

        if not summary_invariant:
            return ResolutionSyncResult(
                success=False,
                status="FAILED",
                canonical_bug_id=canonical_bug_id,
                blocker="LEDGER SUMMARY INVARIANT FAILED",
                ledger_updated=False,
                summary_recomputed=True,
                summary_invariant=False,
                lifecycle_table_updated=lifecycle_table_updated,
            )

        # 12. Verify Consistency across all representations
        ledger_consistent = self.verify_ledger_consistency(
            canonical_bug_id=canonical_bug_id,
            expected_status=primary_status,
            expected_disposition=disposition,
            expected_owner=primary_owner,
            expected_retest=primary_retest,
            expected_dev_update=primary_dev_update,
        )

        if not ledger_consistent:
            return ResolutionSyncResult(
                success=False,
                status="FAILED",
                canonical_bug_id=canonical_bug_id,
                blocker="LEDGER CONSISTENCY FAILED",
                ledger_updated=False,
                summary_recomputed=True,
                summary_invariant=True,
                lifecycle_table_updated=lifecycle_table_updated,
                ledger_consistent=False,
            )

        return ResolutionSyncResult(
            success=True,
            status="UPDATED",
            canonical_bug_id=canonical_bug_id,
            work_item_id=wi_id,
            azure_state=azure_state,
            azure_reason=azure_reason,
            new_developer_feedback=bool(latest_human_comment),
            art_disposition=disposition,
            retest_required=retest_req,
            action_required=action_req,
            assessment_reason=assessment_reason,
            developer_comment=latest_human_comment,
            changed_by=changed_by_name,
            current_assignee=assigned_to_name,
            previous_assignee=previous_assignee,
            lifecycle_updated_at=lifecycle_updated_at,
            primary_status=primary_status,
            primary_owner=primary_owner,
            primary_retest=primary_retest,
            primary_developer_update=primary_dev_update,
            ledger_updated=True,
            canonical_history_updated=True,
            summary_recomputed=True,
            summary_invariant=True,
            lifecycle_table_updated=True,
            ledger_consistent=True,
            azure_mutations=0,
        )

    def _update_markdown_file(
        self,
        md_path: str,
        wi_id: int,
        azure_state: str,
        azure_reason: Optional[str],
        changed_by: str,
        current_assignee: str,
        previous_assignee: Optional[str],
        developer_comment: Optional[str],
        disposition: str,
        primary_status: str,
        retest_required: bool,
        action_required: str,
        assessment_reason: str,
        lifecycle_updated_at: Optional[str],
        sync_timestamp: str,
        today_date: str,
    ) -> None:
        """Updates the canonical markdown with primary Status in Metadata, Resolution Status, and Resolution History."""
        with open(md_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Update - **Status:** in Metadata
        content = re.sub(
            r"(-\s*\*\*Status:\*\*\s*)([A-Za-z_]+)",
            rf"\g<1>{primary_status}",
            content
        )

        retest_str = "YES" if retest_required else "NO"
        reason_display = azure_reason or "Not provided"
        lifecycle_time_display = lifecycle_updated_at or "Not Available"

        status_section = (
            f"## Resolution Status\n\n"
            f"- **ART Disposition:** {disposition}\n"
            f"- **Current Azure Assignee:** {current_assignee}\n"
            f"- **Azure State:** {azure_state}\n"
            f"- **Azure Reason:** {reason_display}\n"
            f"- **Retest Required:** {retest_str}\n"
            f"- **Action Required:** {action_required}\n"
            f"- **Latest Lifecycle Update:** {lifecycle_time_display}\n"
            f"- **Last Azure Sync:** {sync_timestamp}\n"
        )

        assignment_block = ""
        if previous_assignee and previous_assignee != current_assignee:
            assignment_block = f"Assignment: {previous_assignee} → {current_assignee}\n\n"

        history_event = (
            f"### {today_date} — Azure Lifecycle Update\n\n"
            f"Azure Work Item: #{wi_id}\n"
            f"Azure State: {azure_state}\n"
            f"Azure Reason: {reason_display}\n"
            f"Current Azure Assignee: {current_assignee}\n"
            f"Changed By: {changed_by}\n\n"
            f"{assignment_block}"
            f"Developer Feedback:\n\n"
            f"{developer_comment or 'Not provided'}\n\n"
            f"ART Assessment:\n\n"
            f"{disposition}\n\n"
            f"Retest Required:\n\n"
            f"{retest_str}\n\n"
            f"Action Required:\n\n"
            f"{action_required}\n\n"
            f"Assessment Reason:\n\n"
            f"{assessment_reason}\n"
        )

        # 1. Update or append ## Resolution Status
        if "## Resolution Status" in content:
            content = re.sub(
                r"## Resolution Status\n.*?(?=(\n## |\Z))",
                status_section + "\n",
                content,
                flags=re.DOTALL
            )
        else:
            if "## 19. Azure DevOps" in content:
                content = re.sub(
                    r"(## 19\. Azure DevOps\n.*?(?=(\n## |\Z)))",
                    r"\1\n\n" + status_section,
                    content,
                    flags=re.DOTALL
                )
            else:
                content = content.rstrip() + "\n\n" + status_section

        # 2. Append to ## Resolution History
        if "## Resolution History" in content:
            if f"### {today_date} — Azure Lifecycle Update" in content and (developer_comment or "Not provided") in content and current_assignee in content:
                pass
            else:
                content = content.rstrip() + "\n\n" + history_event
        else:
            content = content.rstrip() + "\n\n## Resolution History\n\n" + history_event

        with open(md_path, "w", encoding="utf-8") as f:
            f.write(content.strip() + "\n")

    def _update_master_ledger(
        self,
        canonical_bug_id: str,
        feature_name: str,
        wi_id: int,
        azure_state: str,
        azure_reason: Optional[str],
        disposition: str,
        primary_status: str,
        primary_owner: str,
        primary_retest: str,
        primary_dev_update: str,
        retest_required: bool,
        action_required: str,
        sync_timestamp: str,
        summary_text: Optional[str],
    ) -> Tuple[bool, bool, bool, bool]:
        """
        Updates the master ledger following Section 16D transaction order:
        Step 5. Update existing primary Bugs-table row (Status, Owner, Developer Update, Retest).
        Step 6. Update detailed lifecycle tracking row.
        Step 7. Recalculate Summary from primary Bugs table.
        Step 8. Re-read ledger.
        Step 9. Verify representations agree.
        Returns (primary_row_updated, lifecycle_table_updated, summary_recomputed, summary_invariant).
        """
        if not os.path.isfile(self.ledger_path):
            return False, False, False, False

        with open(self.ledger_path, "r", encoding="utf-8") as f:
            ledger = f.read()

        retest_flag = "YES" if retest_required else "NO"
        reason_str = azure_reason or "Not provided"
        short_summary = (summary_text or "").replace("\n", " ").strip()
        if len(short_summary) > 90:
            short_summary = short_summary[:87] + "..."

        # Step 5: Check if ## Bugs table has Owner column
        bugs_sec_match = re.search(r"## Bugs\n(.*?)(?=(\n## |\Z))", ledger, flags=re.DOTALL)
        if not bugs_sec_match:
            return False, False, False, False

        bugs_table_text = bugs_sec_match.group(1)
        has_owner_col = "| Owner |" in bugs_table_text or "| owner |" in bugs_table_text.lower()

        primary_row_updated = False

        if has_owner_col:
            # Update row with Owner column: Bug ID | Title | Severity | Status | Owner | Developer Update | Retest
            pattern_row = rf"(\|\s*\[{re.escape(canonical_bug_id)}\]\((?:<[^>]+>|[^)]+)\)\s*\|\s*[^|]+\|\s*[^|]+\|\s*)([^|]+)(\|\s*)([^|]+)(\|\s*)([^|]+)(\|\s*)([^|]+)(\|)"
            def replace_row_with_owner(m):
                prefix = m.group(1)
                sep1 = m.group(3)
                sep2 = m.group(5)
                sep3 = m.group(7)
                suffix = m.group(9)
                return f"{prefix}{primary_status} {sep1}{primary_owner} {sep2}{primary_dev_update} {sep3}{primary_retest} {suffix}"

            if re.search(pattern_row, ledger):
                ledger = re.sub(pattern_row, replace_row_with_owner, ledger)
                primary_row_updated = True
        else:
            # Table does not yet have Owner column: extend table header & rows per Section 31K
            # First check if the row exists in the 6-col table
            pattern_6col = rf"(\|\s*\[{re.escape(canonical_bug_id)}\]\((?:<[^>]+>|[^)]+)\)\s*\|\s*[^|]+\|\s*[^|]+\|\s*)([^|]+)(\|\s*)([^|]+)(\|\s*)([^|]+)(\|)"
            if re.search(pattern_6col, ledger):
                # Migrate header
                ledger = re.sub(
                    r"(\|\s*Bug ID\s*\|\s*Title\s*\|\s*Severity\s*\|\s*Status\s*\|\s*)(Developer Update)(\s*\|\s*Retest\s*\|)",
                    r"\g<1>Owner | \g<2>\g<3>",
                    ledger
                )
                ledger = re.sub(
                    r"(\|\s*---(?:\s*\|\s*---){4}\s*\|\s*---\s*\|)",
                    r"| --- | --- | --- | --- | --- | --- | --- |",
                    ledger
                )

                # Now update the target row with Owner column
                def update_and_add_owner(m):
                    prefix = m.group(1)
                    sep1 = m.group(3)
                    sep2 = m.group(5)
                    suffix = m.group(7)
                    return f"{prefix}{primary_status} | {primary_owner} {sep1}{primary_dev_update} {sep2}{primary_retest} {suffix}"

                ledger = re.sub(pattern_6col, update_and_add_owner, ledger)
                primary_row_updated = True

                # For all other remaining 6-col rows, add "| Unassigned "
                other_rows_pattern = r"(\|\s*\[(?:ART-[A-Z0-9]+-[0-9]+)\]\([^\)]+\)\s*\|\s*[^|]+\|\s*[^|]+\|\s*[^|]+\|\s*)([^|]+\|\s*[^|]+\|)"
                def add_unassigned_if_missing(m):
                    full = m.group(0)
                    parts = [c.strip() for c in full.split("|")]
                    if len(parts) == 8:  # 6 data cols + 2 ends
                        # insert Unassigned after status (parts[4])
                        return f"| {parts[1]} | {parts[2]} | {parts[3]} | {parts[4]} | Unassigned | {parts[5]} | {parts[6]} |"
                    return full

                lines = []
                for line in ledger.splitlines():
                    if line.strip().startswith("| [ART-") and f"[{canonical_bug_id}]" not in line:
                        parts = [c.strip() for c in line.split("|")]
                        if len(parts) == 8:
                            line = f"| {parts[1]} | {parts[2]} | {parts[3]} | {parts[4]} | Unassigned | {parts[5]} | {parts[6]} |"
                    lines.append(line)
                ledger = "\n".join(lines)

        # Step 6: Maintain ## Azure Resolution & Lifecycle Tracking section
        tracking_row = (
            f"| {canonical_bug_id} | {feature_name} | #{wi_id} | {azure_state} | {reason_str} | "
            f"{disposition} | {retest_flag} | {action_required} | {sync_timestamp} | {short_summary} |\n"
        )

        lifecycle_table_updated = False
        if "## Azure Resolution & Lifecycle Tracking" in ledger:
            row_pattern = rf"\|\s*{re.escape(canonical_bug_id)}\s*\|[^\n]+"
            if re.search(row_pattern, ledger):
                ledger = re.sub(row_pattern, tracking_row.strip(), ledger)
                lifecycle_table_updated = True
            else:
                ledger = ledger.rstrip() + "\n" + tracking_row
                lifecycle_table_updated = True
        else:
            tracking_header = (
                "## Azure Resolution & Lifecycle Tracking\n\n"
                "| Bug ID | Feature | Azure ID | Azure State | Azure Reason | ART Disposition | Retest Required | Action Required | Last Azure Sync | Resolution Summary |\n"
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n"
            )
            ledger = ledger.rstrip() + "\n\n" + tracking_header + tracking_row
            lifecycle_table_updated = True

        # Step 7: Recalculate ## Summary from all rows in ## Bugs table
        ledger, summary_recomputed, summary_invariant = self._recompute_summary(ledger)

        # Write to disk
        with open(self.ledger_path, "w", encoding="utf-8") as f:
            f.write(ledger.strip() + "\n")

        # Step 8: Re-read ledger from disk
        with open(self.ledger_path, "r", encoding="utf-8") as f:
            _ = f.read()

        return primary_row_updated, lifecycle_table_updated, summary_recomputed, summary_invariant

    def _recompute_summary(self, ledger_content: str) -> Tuple[str, bool, bool]:
        """
        Parses all rows in ## Bugs table and generates accurate summary counts.
        Enforces invariant: Open + Fixing + Retest + Verified + Closed + Blocked == Total Bugs.
        """
        bugs_sec_match = re.search(r"## Bugs\n(.*?)(?=(\n## |\Z))", ledger_content, flags=re.DOTALL)
        if not bugs_sec_match:
            return ledger_content, False, False

        bugs_table_text = bugs_sec_match.group(1)
        counts = {
            "Total Bugs": 0,
            "Open": 0,
            "Fixing": 0,
            "Retest": 0,
            "Verified": 0,
            "Closed": 0,
            "Blocked": 0,
        }

        for line in bugs_table_text.splitlines():
            line_str = line.strip()
            if not line_str.startswith("|") or "---" in line_str or "Bug ID" in line_str:
                continue
            cols = [c.strip() for c in line_str.split("|")]
            # Format: | (empty) | Bug ID (1) | Title (2) | Severity (3) | Status (4) | ...
            if len(cols) >= 6:
                counts["Total Bugs"] += 1
                status_val = cols[4].upper()
                if status_val == "OPEN":
                    counts["Open"] += 1
                elif status_val == "FIXING":
                    counts["Fixing"] += 1
                elif status_val == "RETEST":
                    counts["Retest"] += 1
                elif status_val == "VERIFIED":
                    counts["Verified"] += 1
                elif status_val == "CLOSED":
                    counts["Closed"] += 1
                elif status_val == "BLOCKED":
                    counts["Blocked"] += 1
                else:
                    counts["Open"] += 1

        sum_parts = counts["Open"] + counts["Fixing"] + counts["Retest"] + counts["Verified"] + counts["Closed"] + counts["Blocked"]
        invariant_holds = (sum_parts == counts["Total Bugs"])

        summary_block = (
            "## Summary\n\n"
            f"- **Total Bugs:** {counts['Total Bugs']}\n"
            f"- **Open:** {counts['Open']}\n"
            f"- **Fixing:** {counts['Fixing']}\n"
            f"- **Retest:** {counts['Retest']}\n"
            f"- **Verified:** {counts['Verified']}\n"
            f"- **Closed:** {counts['Closed']}\n"
            f"- **Blocked:** {counts['Blocked']}\n"
        )

        updated_ledger = re.sub(
            r"## Summary\n.*?(?=(\n## |\Z))",
            summary_block + "\n",
            ledger_content,
            flags=re.DOTALL
        )

        return updated_ledger, True, invariant_holds

    def verify_ledger_consistency(
        self,
        canonical_bug_id: str,
        expected_status: str,
        expected_disposition: str,
        expected_owner: Optional[str] = None,
        expected_retest: Optional[str] = None,
        expected_dev_update: Optional[str] = None,
    ) -> bool:
        """
        Verifies Section 16C and 31N consistency across 5 representations:
        1. Canonical Markdown (## Metadata Status, ## Resolution Status, Current Azure Assignee)
        2. SQLite investigations table (status, assignee)
        3. Primary ledger row (Status, Owner, Retest, Developer Update)
        4. Primary ledger Summary (Total Bugs invariant and counts)
        5. Azure lifecycle tracking table (ART Disposition)
        """
        # 1. Canonical Markdown
        loc = self.find_canonical_bug_file(canonical_bug_id)
        if not loc:
            return False
        md_path, _, _ = loc
        with open(md_path, "r", encoding="utf-8") as f:
            md = f.read()
        m_status = re.search(r"-\s*\*\*Status:\*\*\s*([A-Za-z_]+)", md)
        if not m_status or m_status.group(1).strip().upper() != expected_status:
            return False
        if f"- **ART Disposition:** {expected_disposition}" not in md:
            return False
        if expected_owner:
            m_assignee = re.search(r"-\s*\*\*Current Azure Assignee:\*\*\s*(.+)", md)
            if not m_assignee or m_assignee.group(1).strip() != expected_owner:
                return False

        # 2. SQLite
        conn = sqlite3.connect(self.db_path)
        try:
            row = conn.execute(
                "SELECT status, assignee FROM investigations WHERE canonical_bug_id = ?",
                (canonical_bug_id,)
            ).fetchone()
            if not row or (row[0] or "").upper() != expected_status:
                return False
            if expected_owner and (row[1] or "").strip() != expected_owner:
                return False
        finally:
            conn.close()

        # 3, 4, 5. Ledger
        if not os.path.isfile(self.ledger_path):
            return False
        with open(self.ledger_path, "r", encoding="utf-8") as f:
            ledger = f.read()

        bugs_sec_match = re.search(r"## Bugs\n(.*?)(?=(\n## |\Z))", ledger, flags=re.DOTALL)
        if not bugs_sec_match:
            return False
        bugs_text = bugs_sec_match.group(1)
        has_owner_col = "| Owner |" in bugs_text or "| owner |" in bugs_text.lower()

        if has_owner_col:
            pattern = rf"\|\s*\[{re.escape(canonical_bug_id)}\]\((?:<[^>]+>|[^)]+)\)\s*\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|"
            m_row = re.search(pattern, ledger)
            if not m_row:
                return False
            if m_row.group(3).strip().upper() != expected_status:
                return False
            if expected_owner and m_row.group(4).strip() != expected_owner:
                return False
            if expected_dev_update and m_row.group(5).strip() != expected_dev_update:
                return False
            if expected_retest and m_row.group(6).strip() != expected_retest:
                return False
        else:
            pattern = rf"\|\s*\[{re.escape(canonical_bug_id)}\]\((?:<[^>]+>|[^)]+)\)\s*\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|"
            m_row = re.search(pattern, ledger)
            if not m_row:
                return False
            if m_row.group(1).strip().upper() != expected_status:
                return False
            if expected_retest and m_row.group(3).strip() != expected_retest:
                return False
            if expected_dev_update and m_row.group(2).strip() != expected_dev_update:
                return False

        # Lifecycle tracking table
        tracking_pattern = rf"\|\s*{re.escape(canonical_bug_id)}\s*\|[^|]+\|[^|]+\|[^|]+\|[^|]+\|\s*([^|]+)\|"
        m_track = re.search(tracking_pattern, ledger)
        if not m_track or m_track.group(1).strip() != expected_disposition:
            return False

        # Summary counts & invariant
        total_m = re.search(r"-\s*\*\*Total Bugs:\*\*\s*(\d+)", ledger)
        open_m = re.search(r"-\s*\*\*Open:\*\*\s*(\d+)", ledger)
        fixing_m = re.search(r"-\s*\*\*Fixing:\*\*\s*(\d+)", ledger)
        retest_m = re.search(r"-\s*\*\*Retest:\*\*\s*(\d+)", ledger)
        ver_m = re.search(r"-\s*\*\*Verified:\*\*\s*(\d+)", ledger)
        close_m = re.search(r"-\s*\*\*Closed:\*\*\s*(\d+)", ledger)
        block_m = re.search(r"-\s*\*\*Blocked:\*\*\s*(\d+)", ledger)
        if not (total_m and open_m and fixing_m and retest_m and ver_m and close_m and block_m):
            return False
        sum_total = (
            int(open_m.group(1)) + int(fixing_m.group(1)) + int(retest_m.group(1)) +
            int(ver_m.group(1)) + int(close_m.group(1)) + int(block_m.group(1))
        )
        if sum_total != int(total_m.group(1)):
            return False

        return True
