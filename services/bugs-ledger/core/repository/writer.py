"""
core/repository/writer.py

Deterministic repository bug record writer and ledger synchronization.
Preserves existing markdown structure and updates/appends ## Azure DevOps metadata.
Authoritative source remains individual bug records under ART-Product-Validation/bugs/.
"""

import os
import re
from typing import Dict, Any, Optional, List


def format_azure_devops_section(
    work_item_id: int,
    work_item_url: str,
    parent_feature_title: str,
    parent_feature_id: int,
    assigned_to: str,
    sync_status: str = "SYNCED"
) -> str:
    """
    Produces deterministic Azure DevOps markdown section for bug record.
    """
    return (
        f"## Azure DevOps\n\n"
        f"- **Work Item ID:** {work_item_id}\n"
        f"- **URL:** {work_item_url}\n"
        f"- **Parent Feature:** {parent_feature_title}\n"
        f"- **Parent Feature ID:** {parent_feature_id}\n"
        f"- **Assigned To:** {assigned_to}\n"
        f"- **Sync Status:** {sync_status}\n"
    )


def append_or_update_azure_section(markdown_content: str, azure_section_str: str) -> str:
    """
    Appends or updates ## Azure DevOps section deterministically without altering other content.
    """
    pattern = r"## Azure DevOps\n.*?(?=(\n## |\Z))"
    cleaned_section = azure_section_str.strip() + "\n"
    if re.search(pattern, markdown_content, flags=re.DOTALL):
        # Replace existing section
        updated = re.sub(pattern, cleaned_section, markdown_content, flags=re.DOTALL)
        return updated
    else:
        # Append before EOF, ensuring clean trailing newline
        content_stripped = markdown_content.rstrip()
        return f"{content_stripped}\n\n{cleaned_section}"


def render_ledger(bug_records: List[Dict[str, str]]) -> str:
    """
    Renders deterministic ART_PRODUCT_VALIDATION_LEDGER.md table from individual bug records.
    Each item in bug_records:
    {
        'id': 'ART-AGENT-001',
        'rel_path': 'bugs/.../ART-AGENT-001.md',
        'name': 'Structured output contract is not strictly enforced',
        'severity': 'HIGH',
        'status': 'OPEN',
        'dev_update': 'Pending.',
        'retest': 'Pending.'
    }
    """
    total = len(bug_records)
    open_count = sum(1 for b in bug_records if b.get("status") == "OPEN")

    lines = [
        "# ART Product Validation Ledger\n",
        "## Summary\n",
        f"- Total: {total}",
        f"- Open: {open_count}\n",
        "## Bugs\n",
        "| Bug ID | Bug | Severity | Status | Developer Update | Retest |",
        "| ------ | --- | -------- | ------ | ---------------- | ------ |"
    ]

    for b in bug_records:
        b_id = b.get("id", "")
        path = b.get("rel_path", "")
        name = b.get("name", "")
        sev = b.get("severity", "HIGH")
        status = b.get("status", "OPEN")
        dev = b.get("dev_update", "")
        retest = b.get("retest", "")
        safe_path = path.replace(" ", "%20")
        lines.append(f"| [{b_id}]({safe_path}) | {name} | {sev} | {status} | {dev} | {retest} |")

    lines.append("\n## Notes\n")
    return "\n".join(lines)
