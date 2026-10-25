"""
core/features/storage.py

Canonical Markdown persistence, evidence storage, and ledger compiler
for ART Feature Requests and Enhancements.
"""

import os
import re
import shutil
import hashlib
from typing import List, Dict, Optional
from urllib.parse import quote

from core.repository.paths import resolve_feature_folder, resolve_feature_storage_path
from core.features.models import (
    FeatureRecord,
    FeatureClassification,
    FeatureStatus,
    AzureSyncStatus,
    _now_iso,
)


def slugify(text: str) -> str:
    """Converts a title into a clean URL/filesystem slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-") or "feature"


class FeatureStorageManager:
    """
    Authoritative manager for canonical feature records on disk:
    ART-Product-Validation/features/<MODULE>/<FEATURE-ID>__<slug>/
    """

    def __init__(self, validation_root: Optional[str] = None):
        if validation_root:
            self.validation_root = os.path.abspath(validation_root)
        else:
            self.validation_root = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "../../ART-Product-Validation")
            )
        self.features_root = os.path.join(self.validation_root, "features")
        self.ledger_path = os.path.join(self.validation_root, "ART_FEATURE_BACKLOG_LEDGER.md")

    def ensure_directories(self) -> None:
        """Ensures the root features directory and all canonical module directories exist."""
        os.makedirs(self.features_root, exist_ok=True)
        from core.repository.registry import get_canonical_feature_folders
        for folder in get_canonical_feature_folders():
            os.makedirs(os.path.join(self.features_root, folder), exist_ok=True)

    def get_feature_dir(self, module: str, feature_id: str, slug: Optional[str] = None) -> str:
        """Resolves the feature directory path on disk."""
        canonical_folder = resolve_feature_folder(module)
        clean_slug = slug or "feature"
        folder_name = f"{feature_id}__{clean_slug}"
        return os.path.join(self.features_root, canonical_folder, folder_name)

    def serialize_markdown(self, record: FeatureRecord) -> str:
        """Renders a FeatureRecord into canonical Markdown."""
        lines = [
            f"# {record.feature_id} — {record.title}",
            "",
            f"- **Module:** {record.module}",
            f"- **Classification:** {record.classification}",
            f"- **Status:** {record.status}",
            f"- **Priority:** P{record.priority}",
            f"- **Azure Work Item ID:** {f'#{record.azure_work_item_id}' if record.azure_work_item_id else 'None'}",
            f"- **Azure Sync Status:** {record.azure_sync_status}",
            "",
            "## Problem / Opportunity",
            "",
            record.problem_opportunity or "Not provided.",
            "",
            "## Current Behavior",
            "",
            record.current_behavior or "Not provided.",
            "",
            "## Proposed Behavior",
            "",
            record.proposed_behavior or "Not provided.",
            "",
            "## Business Impact",
            "",
            record.business_impact or "Not provided.",
            "",
            "## User Experience",
            "",
            record.user_experience or "Not provided.",
            "",
            "## Acceptance Criteria",
            "",
        ]

        if record.acceptance_criteria:
            for i, ac in enumerate(record.acceptance_criteria, start=1):
                lines.append(f"{i}. {ac}")
        else:
            lines.append("Pending formal acceptance criteria.")

        lines.extend([
            "",
            "## Implementation Guidance",
            "",
            record.implementation_guidance or "Not provided.",
            "",
            "## Related Bugs / Dependencies",
            "",
        ])

        if record.related_bugs:
            for b in record.related_bugs:
                lines.append(f"- {b}")
        else:
            lines.append("None identified.")

        lines.extend([
            "",
            "## Evidence and Provenance",
            "",
            f"- **Provenance:** {record.provenance}",
            f"- **Created At:** {record.created_at}",
            f"- **Updated At:** {record.updated_at}",
        ])

        if record.evidence_files:
            lines.append("- **Evidence Files:**")
            for ev in record.evidence_files:
                fn = ev.get("filename", "")
                sha = ev.get("sha256", "")
                lines.append(f"  - `{fn}` (SHA-256: `{sha}`)")
        else:
            lines.append("- **Evidence Files:** None attached.")

        lines.append("")
        return "\n".join(lines)

    def parse_markdown(self, content: str, filepath: Optional[str] = None) -> FeatureRecord:
        """Parses a canonical feature Markdown file back into a FeatureRecord."""
        title_match = re.search(r"^#\s+(ART-FEAT-[A-Z]+-\d{3})\s+—\s+(.+)$", content, re.MULTILINE)
        if not title_match:
            # Fallback pattern if ID prefix differs
            title_match = re.search(r"^#\s+([A-Z0-9-]+)\s+—\s+(.+)$", content, re.MULTILINE)

        feature_id = title_match.group(1).strip() if title_match else "UNKNOWN-FEAT"
        title = title_match.group(2).strip() if title_match else "Untitled Feature"

        def get_meta(field_name: str, default: str = "") -> str:
            m = re.search(rf"^-\s+\*\*{field_name}:\*\*\s*(.+)$", content, re.MULTILINE)
            return m.group(1).strip() if m else default

        module = get_meta("Module", "Agent Lab")
        classification = get_meta("Classification", FeatureClassification.NEW_FEATURE.value)
        status = get_meta("Status", FeatureStatus.PROPOSED.value)
        pri_str = get_meta("Priority", "P2").lstrip("P")
        try:
            priority = int(pri_str)
        except ValueError:
            priority = 2

        raw_azure_id = get_meta("Azure Work Item ID", "None").lstrip("#")
        try:
            azure_work_item_id = int(raw_azure_id) if raw_azure_id != "None" else None
        except ValueError:
            azure_work_item_id = None

        azure_sync_status = get_meta("Azure Sync Status", AzureSyncStatus.NOT_SYNCED.value)

        # Extract sections by heading
        sections: Dict[str, str] = {}
        current_section = None
        current_lines = []

        for line in content.splitlines():
            if line.startswith("## "):
                if current_section:
                    sections[current_section] = "\n".join(current_lines).strip()
                current_section = line[3:].strip()
                current_lines = []
            elif current_section:
                current_lines.append(line)

        if current_section:
            sections[current_section] = "\n".join(current_lines).strip()

        # Parse acceptance criteria list
        ac_text = sections.get("Acceptance Criteria", "")
        acceptance_criteria = []
        for line in ac_text.splitlines():
            m = re.match(r"^\d+\.\s*(.+)$", line.strip())
            if m:
                acceptance_criteria.append(m.group(1).strip())
            elif line.strip().startswith("- ") and "pending" not in line.lower():
                acceptance_criteria.append(line.strip()[2:].strip())

        # Parse related bugs list
        rel_text = sections.get("Related Bugs / Dependencies", "")
        related_bugs = []
        for line in rel_text.splitlines():
            line_str = line.strip()
            if line_str.startswith("- ") and "none" not in line_str.lower():
                related_bugs.append(line_str[2:].strip())

        # Parse evidence files from Evidence section
        ev_text = sections.get("Evidence and Provenance", "")
        evidence_files = []
        for m in re.finditer(r"`([^`]+)`\s*\(SHA-256:\s*`([^`]+)`\)", ev_text):
            evidence_files.append({"filename": m.group(1), "sha256": m.group(2)})

        created_at = get_meta("Created At", _now_iso())
        updated_at = get_meta("Updated At", _now_iso())

        slug = "feature"
        if filepath:
            parent_name = os.path.basename(os.path.dirname(filepath))
            if "__" in parent_name:
                slug = parent_name.split("__", 1)[1]

        return FeatureRecord(
            feature_id=feature_id,
            title=title,
            module=module,
            classification=classification,
            status=status,
            priority=priority,
            problem_opportunity=sections.get("Problem / Opportunity", ""),
            current_behavior=sections.get("Current Behavior", ""),
            proposed_behavior=sections.get("Proposed Behavior", ""),
            business_impact=sections.get("Business Impact", ""),
            user_experience=sections.get("User Experience", ""),
            acceptance_criteria=acceptance_criteria,
            implementation_guidance=sections.get("Implementation Guidance", ""),
            related_bugs=related_bugs,
            evidence_files=evidence_files,
            azure_work_item_id=azure_work_item_id,
            azure_sync_status=azure_sync_status,
            created_at=created_at,
            updated_at=updated_at,
            slug=slug,
        )

    def save_feature(
        self,
        record: FeatureRecord,
        source_evidence_files: Optional[List[str]] = None
    ) -> str:
        """
        Saves a FeatureRecord and attached evidence files to disk under:
        features/<MODULE>/<FEATURE-ID>__<slug>/<FEATURE-ID>.md
        Returns the absolute path to the written markdown file.
        """
        self.ensure_directories()
        feature_dir = self.get_feature_dir(record.module, record.feature_id, record.slug)
        os.makedirs(feature_dir, exist_ok=True)

        # Copy source evidence files into feature_dir once
        if source_evidence_files:
            for src_path in source_evidence_files:
                if not os.path.isfile(src_path):
                    continue
                fname = os.path.basename(src_path)
                dst_path = os.path.join(feature_dir, fname)
                if not os.path.exists(dst_path) or os.path.abspath(src_path) != os.path.abspath(dst_path):
                    shutil.copy2(src_path, dst_path)

                # Compute sha256
                with open(dst_path, "rb") as fh:
                    sha256 = hashlib.sha256(fh.read()).hexdigest()

                if not any(e.get("filename") == fname for e in record.evidence_files):
                    record.evidence_files.append({"filename": fname, "sha256": sha256})

        record.updated_at = _now_iso()
        md_content = self.serialize_markdown(record)
        md_file_path = os.path.join(feature_dir, f"{record.feature_id}.md")
        with open(md_file_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        # Update ledger
        self.compile_ledger()
        return md_file_path

    def load_feature(self, feature_id: str) -> Optional[FeatureRecord]:
        """Searches features directory and loads a FeatureRecord by Feature ID."""
        if not os.path.isdir(self.features_root):
            return None

        clean_id = feature_id.strip()
        for root, dirs, files in os.walk(self.features_root):
            for file in files:
                if file == f"{clean_id}.md":
                    full_path = os.path.join(root, file)
                    with open(full_path, "r", encoding="utf-8") as f:
                        return self.parse_markdown(f.read(), filepath=full_path)
        return None

    def list_all_features(self) -> List[FeatureRecord]:
        """Lists all feature records on disk, sorted by feature_id."""
        records: List[FeatureRecord] = []
        if not os.path.isdir(self.features_root):
            return records

        for root, dirs, files in os.walk(self.features_root):
            for file in files:
                if file.endswith(".md") and ("ART-FEAT-" in file or "FEAT-" in file):
                    full_path = os.path.join(root, file)
                    try:
                        with open(full_path, "r", encoding="utf-8") as f:
                            rec = self.parse_markdown(f.read(), filepath=full_path)
                            records.append(rec)
                    except Exception:
                        pass

        records.sort(key=lambda r: r.feature_id)
        return records

    def compile_ledger(self) -> str:
        """
        Compiles the ART Feature Backlog Ledger into:
        ART-Product-Validation/ART_FEATURE_BACKLOG_LEDGER.md
        """
        features = self.list_all_features()

        total = len(features)
        proposed = sum(1 for f in features if f.status == FeatureStatus.PROPOSED.value)
        accepted = sum(1 for f in features if f.status == FeatureStatus.ACCEPTED.value)
        in_prog = sum(1 for f in features if f.status == FeatureStatus.IN_PROGRESS.value)
        implemented = sum(1 for f in features if f.status == FeatureStatus.IMPLEMENTED.value)
        rejected = sum(1 for f in features if f.status == FeatureStatus.REJECTED.value)
        blocked = sum(1 for f in features if f.status == FeatureStatus.BLOCKED.value)

        lines = [
            "# ART Feature Backlog Ledger",
            "",
            "## Summary",
            "",
            f"- **Total Features:** {total}",
            f"- **Proposed:** {proposed}",
            f"- **Accepted:** {accepted}",
            f"- **In Progress:** {in_prog}",
            f"- **Implemented:** {implemented}",
            f"- **Rejected:** {rejected}",
            f"- **Blocked:** {blocked}",
            "",
            "## Features",
            "",
            "| Feature ID | Title | Module | Classification | Status | Azure Work Item |",
            "| --- | --- | --- | --- | --- | --- |",
        ]

        for f in features:
            module_folder = resolve_feature_folder(f.module)
            module_enc = quote(module_folder)
            folder_name = f"{f.feature_id}__{f.slug}"
            folder_enc = quote(folder_name)
            link_path = f"features/{module_enc}/{folder_enc}/{f.feature_id}.md"

            azure_link = f"[#{f.azure_work_item_id}](https://dev.azure.com/BixBytesSolutions/ART%20IPR-0063/_workitems/edit/{f.azure_work_item_id})" if f.azure_work_item_id else "Pending"

            lines.append(
                f"| [{f.feature_id}]({link_path}) | {f.title} | {f.module} | {f.classification} | {f.status} | {azure_link} |"
            )

        lines.append("")
        content = "\n".join(lines)
        with open(self.ledger_path, "w", encoding="utf-8") as fh:
            fh.write(content)

        return self.ledger_path
