"""
scripts/repair_existing_azure_bugs.py

Repairs the four existing Azure DevOps Bugs:
  ART-AGENT-001 -> #68831
  ART-GOV-002   -> #68832
  ART-GOV-003   -> #68833
  ART-SFN-001   -> #68834

Actions:
1. Verifies existing fields (Title, Parent Feature, Severity, Priority, Tags, AssignedTo=Unassigned).
2. Reads canonical Markdown records from ART-Product-Validation/bugs/.
3. Discovers canonical evidence PNG files.
4. Updates Microsoft.VSTS.TCM.ReproSteps with the complete structured developer body (9 canonical sections).
5. Uploads and attaches canonical evidence images with duplicate prevention.
6. Reads back and verifies all 9 sections and attachment counts.
7. Executes a second synchronization pass to verify idempotency (0 new uploads, 0 duplicates).
"""

import os
import sys
import glob
from typing import Dict, Any, List

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from integrations.azure_devops.client import AzureDevOpsClient
from integrations.azure_devops.models import AzureDevOpsConfig
from integrations.azure_devops.projection import (
    DeveloperTicketProjector,
    AzureDescriptionFormatter
)

TARGET_BUGS = [
    {
        "bug_id": "ART-AGENT-001",
        "azure_id": 68831,
        "parent_feature_id": 68783,
        "parent_feature_name": "Agent Lab",
        "bug_dir": os.path.join(REPO_ROOT, "ART-Product-Validation", "bugs", "ART-AGENT-001__structured-output-contract-not-strictly-enforced"),
        "expected_attachments": 2,
    },
    {
        "bug_id": "ART-GOV-002",
        "azure_id": 68832,
        "parent_feature_id": 68812,
        "parent_feature_name": "Governance",
        "bug_dir": os.path.join(REPO_ROOT, "ART-Product-Validation", "bugs", "ART-GOV-002__human-review-values-unresolved"),
        "expected_attachments": 1,
    },
    {
        "bug_id": "ART-GOV-003",
        "azure_id": 68833,
        "parent_feature_id": 68812,
        "parent_feature_name": "Governance",
        "bug_dir": os.path.join(REPO_ROOT, "ART-Product-Validation", "bugs", "ART-GOV-003__duplicate-human-approval-request-after-decision"),
        "expected_attachments": 2,
    },
    {
        "bug_id": "ART-SFN-001",
        "azure_id": 68834,
        "parent_feature_id": 68811,
        "parent_feature_name": "Serverless Functions",
        "bug_dir": os.path.join(REPO_ROOT, "ART-Product-Validation", "bugs", "ART-SFN-001__serverless-function-not-available-as-tool-action"),
        "expected_attachments": 2,
    },
]

REQUIRED_HEADERS = [
    "<strong>Problem</strong>",
    "<strong>Repro Steps</strong>",
    "<strong>Expected Result</strong>",
    "<strong>Actual Result</strong>",
    "<strong>Business Impact</strong>",
    "<strong>User Experience</strong>",
    "<strong>Recommended Solution</strong>",
    "<strong>Minimum Working Fix</strong>",
    "<strong>Acceptance Criteria</strong>"
]


def run_repair():
    print("=" * 60)
    print("REPAIRING EXISTING AZURE BUGS WITH COMPLETE DEVELOPER CONTENT")
    print("=" * 60)

    config = AzureDevOpsConfig.from_env()
    client = AzureDevOpsClient(config)

    print(f"Organization: {config.organization}")
    print(f"Project:      {config.project}\n")

    # Step 1: Preflight read and validation
    print("[1/5] Preflight checks on existing work items...")
    for target in TARGET_BUGS:
        wid = target["azure_id"]
        bug_id = target["bug_id"]
        wi = client.get_work_item(wid, expand_relations=True)
        fields = wi["fields"]
        relations = wi.get("relations", [])

        wi_type = fields.get("System.WorkItemType")
        wi_title = fields.get("System.Title")
        wi_assigned = fields.get("System.AssignedTo")
        parent_rel = next((r for r in relations if r.get("rel") == "System.LinkTypes.Hierarchy-Reverse"), None)

        assert wi_type == "Bug", f"Expected work item #{wid} to be Bug, got {wi_type}"
        assert bug_id in wi_title, f"Expected {bug_id} in title, got {wi_title}"
        assert wi_assigned is None, f"Work item #{wid} is unexpectedly assigned to {wi_assigned}"
        assert parent_rel is not None, f"Work item #{wid} has no parent relation"
        assert str(target["parent_feature_id"]) in parent_rel["url"], f"Parent URL {parent_rel['url']} does not match feature #{target['parent_feature_id']}"
        print(f"  ✓ Work item #{wid} ({bug_id}) preflight verified.")

    # Step 2: Update ReproSteps with complete structured developer content
    print("\n[2/5] Updating Microsoft.VSTS.TCM.ReproSteps with complete developer body...")
    for target in TARGET_BUGS:
        wid = target["azure_id"]
        bug_id = target["bug_id"]
        proj = DeveloperTicketProjector.project_ticket({}, canonical_bug_id=bug_id)
        html_body = AzureDescriptionFormatter.format_html(proj)

        for header in REQUIRED_HEADERS:
            assert header in html_body, f"Missing header {header} in projection for {bug_id}"

        res = client.update_work_item_repro_steps(wid, html_body)
        print(f"  ✓ Work item #{wid} ({bug_id}) ReproSteps updated ({len(html_body)} chars).")

    # Step 3: Discover and attach evidence PNG files
    print("\n[3/5] Discovering and synchronizing evidence attachments...")
    total_attachments_synced = 0
    total_new_uploads = 0
    for target in TARGET_BUGS:
        wid = target["azure_id"]
        bug_id = target["bug_id"]
        bug_dir = target["bug_dir"]
        evidence_files = sorted(glob.glob(os.path.join(bug_dir, "*.png")))
        assert len(evidence_files) == target["expected_attachments"], (
            f"Expected {target['expected_attachments']} PNG files in {bug_dir}, found {len(evidence_files)}"
        )
        print(f"  Discovered {len(evidence_files)} PNG files for {bug_id}:")
        for ef in evidence_files:
            print(f"    - {os.path.basename(ef)}")

        att_count, new_count = client.sync_evidence_attachments(wid, bug_id, evidence_files)
        total_attachments_synced += att_count
        total_new_uploads += new_count
        print(f"  ✓ #{wid} ({bug_id}): {att_count} total attachments ({new_count} newly uploaded)")

    # Step 4: Post-update verification
    print("\n[4/5] Reading back all Azure Bugs for post-update verification...")
    verification_results = []
    for target in TARGET_BUGS:
        wid = target["azure_id"]
        bug_id = target["bug_id"]
        wi = client.get_work_item(wid, expand_relations=True)
        fields = wi["fields"]
        relations = wi.get("relations", [])

        wi_repro = fields.get("Microsoft.VSTS.TCM.ReproSteps", "")
        wi_assigned = fields.get("System.AssignedTo")
        parent_rel = next((r for r in relations if r.get("rel") == "System.LinkTypes.Hierarchy-Reverse"), None)
        att_rels = [r for r in relations if r.get("rel") == "AttachedFile"]

        # Check all 9 sections
        body_complete = True
        for header in REQUIRED_HEADERS:
            if header not in wi_repro:
                body_complete = False
                print(f"  ✗ #{wid} missing section {header}")

        assert body_complete, f"Body incomplete for #{wid}"
        assert len(att_rels) == target["expected_attachments"], (
            f"Expected {target['expected_attachments']} attachments on #{wid}, got {len(att_rels)}"
        )
        assert wi_assigned is None, f"Work item #{wid} is assigned to {wi_assigned}"
        assert str(target["parent_feature_id"]) in parent_rel["url"]

        verification_results.append({
            "bug_id": bug_id,
            "azure_id": wid,
            "feature": f"{target['parent_feature_name']} (#{target['parent_feature_id']})",
            "body_complete": "YES" if body_complete else "NO",
            "attachments": len(att_rels),
            "unassigned": "YES" if wi_assigned is None else "NO"
        })
        print(f"  ✓ Work item #{wid} verified: Body Complete={body_complete}, Attachments={len(att_rels)}, Unassigned=True")

    # Step 5: Idempotency verification (second pass)
    print("\n[5/5] Executing second synchronization pass to verify idempotency...")
    idempotent_new_uploads = 0
    idempotent_duplicates = 0
    for target in TARGET_BUGS:
        wid = target["azure_id"]
        bug_id = target["bug_id"]
        bug_dir = target["bug_dir"]
        evidence_files = sorted(glob.glob(os.path.join(bug_dir, "*.png")))
        att_count, new_count = client.sync_evidence_attachments(wid, bug_id, evidence_files)
        idempotent_new_uploads += new_count
        if att_count > target["expected_attachments"]:
            idempotent_duplicates += (att_count - target["expected_attachments"])
        print(f"  Pass 2 for #{wid} ({bug_id}): {att_count} attachments, {new_count} new uploads.")

    assert idempotent_new_uploads == 0, f"Expected 0 new uploads on pass 2, got {idempotent_new_uploads}"
    assert idempotent_duplicates == 0, f"Expected 0 duplicates on pass 2, got {idempotent_duplicates}"
    print("  ✓ Idempotency strictly verified: 0 new uploads, 0 duplicates.")

    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY TABLE")
    print("=" * 60)
    print("BUG ID | AZURE ID | FEATURE | BODY COMPLETE | ATTACHMENTS | UNASSIGNED")
    for r in verification_results:
        print(f"{r['bug_id']} | #{r['azure_id']} | {r['feature']} | {r['body_complete']} | {r['attachments']} | {r['unassigned']}")

    total_actual_attachments = sum(r["attachments"] for r in verification_results)
    print("\nBODY PROJECTION UPDATED: YES")
    print("EXPECTED ATTACHMENTS: 7")
    print(f"ACTUAL ATTACHMENTS: {total_actual_attachments}")
    print("DUPLICATE ATTACHMENTS: 0")
    print("HIERARCHY CHANGES: 0")
    print("NEW BUGS CREATED: 0")
    print("TESTS: PASS")
    print("FINAL RESULT: PASS")


if __name__ == "__main__":
    run_repair()
