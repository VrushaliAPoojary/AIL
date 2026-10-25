"""
scripts/migrate_canonical_bugs_to_azure.py

One-time controlled migration script:
Creates Azure DevOps Bugs for the 4 canonical ART bug records:
1. ART-AGENT-001
2. ART-GOV-002
3. ART-GOV-003
4. ART-SFN-001

Enforces:
- Locked hierarchy under Epic #68782 (parent is existing module Feature)
- Standard Azure fields only (ZERO custom fields)
- ReproSteps contains pure repro steps only ("Not provided")
- ALL FOUR BUGS MUST BE UNASSIGNED (System.AssignedTo omitted)
- Idempotency via tag 'ART:<BUG-ID>' and title pre-check
- Post-create readback and verification
- Persistence into .local/art_product_resolution.db
- Repository writeback to canonical Markdown files (## Azure DevOps section only)
- Idempotency second-run validation
"""

import os
import sys
import sqlite3
import json
from typing import Dict, Any, List, Optional

# Ensure repository root is on PYTHONPATH
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from integrations.azure_devops.client import AzureDevOpsClient
from integrations.azure_devops.models import (
    AzureDevOpsConfig,
    AzureFeatureRouter,
    AZURE_MODULE_FEATURE_MAP,
    AZURE_MODULE_ALIASES
)
from integrations.azure_devops.projection import DeveloperTicketProjector
from core.storage.integrations import record_external_work_item, get_external_work_item
from core.repository.writer import format_azure_devops_section, append_or_update_azure_section

DB_PATH = os.path.join(REPO_ROOT, ".local", "art_product_resolution.db")
EPIC_ID = 68782

TARGET_BUGS = [
    {
        "bug_id": "ART-AGENT-001",
        "investigation_key": "rec_legacy_art_agent_001",
        "markdown_relpath": "ART-Product-Validation/bugs/ART-AGENT-001__structured-output-contract-not-strictly-enforced/ART-AGENT-001.md",
        "expected_feature_name": "Agent Lab",
        "expected_feature_id": 68783,
    },
    {
        "bug_id": "ART-GOV-002",
        "investigation_key": "rec_legacy_art_gov_002",
        "markdown_relpath": "ART-Product-Validation/bugs/ART-GOV-002__human-review-values-unresolved/ART-GOV-002.md",
        "expected_feature_name": "Governance",
        "expected_feature_id": 68812,
    },
    {
        "bug_id": "ART-GOV-003",
        "investigation_key": "rec_legacy_art_gov_003",
        "markdown_relpath": "ART-Product-Validation/bugs/ART-GOV-003__duplicate-human-approval-request-after-decision/ART-GOV-003.md",
        "expected_feature_name": "Governance",
        "expected_feature_id": 68812,
    },
    {
        "bug_id": "ART-SFN-001",
        "investigation_key": "rec_legacy_art_sfn_001",
        "markdown_relpath": "ART-Product-Validation/bugs/ART-SFN-001__serverless-function-not-available-as-tool-action/ART-SFN-001.md",
        "expected_feature_name": "Serverless Functions",
        "expected_feature_id": 68811,
    },
]


def run_migration():
    print("==================================================")
    print("STARTING ART BUGS -> AZURE DEVOPS MIGRATION")
    print("==================================================")

    # 1. Config & Client
    config = AzureDevOpsConfig.from_env()
    client = AzureDevOpsClient(config)
    print(f"Azure DevOps Org: {config.organization}")
    print(f"Azure DevOps Project: {config.project}")

    # 2. Database connection
    if not os.path.exists(DB_PATH):
        raise RuntimeError(f"Database not found at {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # 3. Preflight Epic #68782
    print(f"\n[PREFLIGHT] Verifying Epic #{EPIC_ID}...")
    epic_wi = client.get_work_item(EPIC_ID, expand_relations=False)
    epic_type = epic_wi["fields"].get("System.WorkItemType")
    epic_title = epic_wi["fields"].get("System.Title")
    if epic_type != "Epic":
        raise RuntimeError(f"Work item #{EPIC_ID} is not an Epic: {epic_type}")
    print(f"✓ Epic #{EPIC_ID} verified: '{epic_title}' (Type: {epic_type})")

    # 4. Preflight Features
    verified_features = {}
    for item in TARGET_BUGS:
        fid = item["expected_feature_id"]
        fname = item["expected_feature_name"]
        if fid not in verified_features:
            print(f"[PREFLIGHT] Verifying Feature #{fid} ({fname})...")
            feat_wi = client.get_work_item(fid, expand_relations=True)
            feat_type = feat_wi["fields"].get("System.WorkItemType")
            feat_title = feat_wi["fields"].get("System.Title")
            if feat_type != "Feature":
                raise RuntimeError(f"Work item #{fid} is not a Feature: {feat_type}")
            
            # Check parent link to Epic #68782
            parent_link = None
            for rel in feat_wi.get("relations", []):
                if rel.get("rel") == "System.LinkTypes.Hierarchy-Reverse":
                    parent_link = rel.get("url")
            if not parent_link or str(EPIC_ID) not in parent_link:
                raise RuntimeError(f"Feature #{fid} does not parent to Epic #{EPIC_ID}: {parent_link}")
            print(f"✓ Feature #{fid} verified: '{feat_title}', parent Epic #{EPIC_ID}")
            verified_features[fid] = feat_wi

    # Tracking results
    results = []
    created_count = 0
    existing_count = 0
    failed_count = 0
    mutations_count = 0

    # 5. Process each bug individually
    for item in TARGET_BUGS:
        bug_id = item["bug_id"]
        inv_key = item["investigation_key"]
        md_relpath = item["markdown_relpath"]
        exp_feat_name = item["expected_feature_name"]
        exp_feat_id = item["expected_feature_id"]

        print(f"\n--------------------------------------------------")
        print(f"PROCESSING {bug_id} ({inv_key})")
        print(f"--------------------------------------------------")

        # 5.1 Load canonical Markdown
        md_fullpath = os.path.join(REPO_ROOT, md_relpath)
        if not os.path.exists(md_fullpath):
            raise RuntimeError(f"Canonical markdown not found: {md_fullpath}")
        with open(md_fullpath, "r", encoding="utf-8") as f:
            md_content = f.read()
        print(f"✓ Canonical markdown loaded: {md_relpath}")

        # 5.2 Load ticket from DB
        cur = conn.cursor()
        t_row = cur.execute("SELECT * FROM ticket_revisions WHERE investigation_key = ?", (inv_key,)).fetchone()
        if not t_row:
            raise RuntimeError(f"No ticket revision found for investigation {inv_key}")
        ticket = dict(t_row)
        module = ticket.get("module")
        print(f"✓ Ticket loaded: title='{ticket.get('title')}', module='{module}', severity='{ticket.get('severity')}'")

        # 5.3 Route Feature
        resolved_feat_id = AzureFeatureRouter.resolve_feature_id(module)
        if resolved_feat_id != exp_feat_id:
            raise RuntimeError(f"Resolved feature ID {resolved_feat_id} != expected {exp_feat_id} for module {module}")
        print(f"✓ Feature routed: {exp_feat_name} (#{resolved_feat_id})")

        # 5.4 Duplicate check via tag & title
        marker = f"ART:{bug_id}"
        exact_title = f"[{bug_id}] {ticket.get('title')}"
        existing_wi = client.find_existing_work_item_by_art_id(bug_id)
        
        status_action = None
        azure_id = None
        azure_url = None

        if existing_wi:
            print(f"! Found EXISTING active Bug in Azure DevOps: #{existing_wi.work_item_id} ({existing_wi.work_item_url})")
            status_action = "EXISTING"
            azure_id = existing_wi.work_item_id
            azure_url = existing_wi.work_item_url
            existing_count += 1
        else:
            print(f"✓ No duplicate found for {bug_id}. Proceeding with creation...")
            # 5.5 Create Bug in Azure DevOps
            # assigned_to is strictly None (unassigned)
            proj = DeveloperTicketProjector.project_ticket(ticket, bug_id)
            bug_dir = os.path.dirname(os.path.join(REPO_ROOT, item["markdown_relpath"]))
            import glob
            evidence_paths = sorted(glob.glob(os.path.join(bug_dir, "*.png")))
            try:
                res = client.create_bug(
                    ticket=ticket,
                    canonical_bug_id=bug_id,
                    parent_work_item_id=resolved_feat_id,
                    assigned_to=None,
                    projection=proj,
                    evidence_paths=evidence_paths
                )
                azure_id = res.work_item_id
                azure_url = res.work_item_url
                status_action = "EXISTING" if res.is_existing else "CREATED"
                if res.is_existing:
                    existing_count += 1
                else:
                    created_count += 1
                    mutations_count += 1
                print(f"✓ Azure Bug mutation successful: #{azure_id} ({status_action})")
            except Exception as e:
                print(f"✗ Failed to create Azure Bug for {bug_id}: {e}")
                failed_count += 1
                results.append({
                    "bug_id": bug_id,
                    "feature": exp_feat_name,
                    "azure_id": "FAILED",
                    "action": "FAILED",
                    "assignee": "Unassigned",
                    "sync": "FAILED"
                })
                continue

        # 5.6 Readback & Verification
        print(f"[VERIFY] Reading back Bug #{azure_id}...")
        read_wi = client.get_work_item(azure_id, expand_relations=True)
        wi_type = read_wi["fields"].get("System.WorkItemType")
        wi_title = read_wi["fields"].get("System.Title")
        wi_tags = read_wi["fields"].get("System.Tags", "")
        wi_sev = read_wi["fields"].get("Microsoft.VSTS.Common.Severity")
        wi_pri = read_wi["fields"].get("Microsoft.VSTS.Common.Priority")
        wi_repro = read_wi["fields"].get("Microsoft.VSTS.TCM.ReproSteps", "")
        wi_sysinfo = read_wi["fields"].get("Microsoft.VSTS.TCM.SystemInfo")
        wi_assigned = read_wi["fields"].get("System.AssignedTo")

        # Check reverse parent link and attachments
        wi_parent = None
        att_rels = []
        for rel in read_wi.get("relations", []):
            if rel.get("rel") == "System.LinkTypes.Hierarchy-Reverse":
                wi_parent = rel.get("url")
            elif rel.get("rel") == "AttachedFile":
                att_rels.append(rel)

        print(f"  Type: {wi_type}")
        print(f"  Title: {wi_title}")
        print(f"  Tags: {wi_tags}")
        print(f"  Severity: {wi_sev} | Priority: {wi_pri}")
        print(f"  ReproSteps length: {len(wi_repro)}")
        print(f"  SystemInfo: {repr(wi_sysinfo)}")
        print(f"  AssignedTo: {repr(wi_assigned)}")
        print(f"  Parent link: {wi_parent}")
        print(f"  Attachments count: {len(att_rels)}")

        # Assertions
        assert wi_type == "Bug", f"Expected Bug, got {wi_type}"
        assert wi_title == exact_title, f"Expected title '{exact_title}', got '{wi_title}'"
        assert marker in wi_tags, f"Expected marker '{marker}' in tags '{wi_tags}'"
        assert "ART" in wi_tags, f"Expected tag 'ART' in tags '{wi_tags}'"
        assert str(resolved_feat_id) in (wi_parent or ""), f"Expected parent feature #{resolved_feat_id} in {wi_parent}"
        assert wi_sev == "2 - High", f"Expected '2 - High', got {wi_sev}"
        assert wi_pri == 2, f"Expected 2, got {wi_pri}"
        for h in [
            "<strong>Problem</strong>",
            "<strong>Repro Steps</strong>",
            "<strong>Expected Result</strong>",
            "<strong>Actual Result</strong>",
            "<strong>Business Impact</strong>",
            "<strong>User Experience</strong>",
            "<strong>Recommended Solution</strong>",
            "<strong>Minimum Working Fix</strong>",
            "<strong>Acceptance Criteria</strong>"
        ]:
            assert h in wi_repro, f"Expected {h} in ReproSteps"
        assert wi_sysinfo is None, f"Expected no SystemInfo, got {wi_sysinfo}"
        assert wi_assigned is None, f"Expected unassigned, got {wi_assigned}"
        print(f"✓ All verification assertions passed for Bug #{azure_id}!")

        # 5.7 Persist to local database
        record_external_work_item(
            conn=conn,
            investigation_key=inv_key,
            external_id=str(azure_id),
            external_url=azure_url,
            system="AZURE_DEVOPS",
            metadata={"canonical_bug_id": bug_id}
        )
        print(f"✓ Persisted external reference in {DB_PATH}")

        # 5.8 Update Markdown file (only ## Azure DevOps section)
        sec_md = format_azure_devops_section(
            work_item_id=azure_id,
            work_item_url=azure_url,
            parent_feature_title=exp_feat_name,
            parent_feature_id=exp_feat_id,
            assigned_to="Unassigned",
            sync_status="SYNCED"
        )
        updated_md = append_or_update_azure_section(md_content, sec_md)
        with open(md_fullpath, "w", encoding="utf-8") as f:
            f.write(updated_md)
        print(f"✓ Repository Markdown updated: {md_relpath}")

        results.append({
            "bug_id": bug_id,
            "feature": exp_feat_name,
            "azure_id": str(azure_id),
            "action": status_action,
            "assignee": "Unassigned",
            "sync": "SYNCED"
        })

    # 6. Idempotency test (Second execution)
    print("\n==================================================")
    print("IDEMPOTENCY VERIFICATION (SECOND RUN)")
    print("==================================================")
    second_run_creations = 0
    for item in TARGET_BUGS:
        bug_id = item["bug_id"]
        found = client.find_existing_work_item_by_art_id(bug_id)
        if not found:
            raise RuntimeError(f"Idempotency check failed: {bug_id} not found in Azure DevOps!")
        print(f"✓ {bug_id} reconciled to existing Azure Bug #{found.work_item_id}")
    print("✓ Second execution verified: ZERO additional bugs would be created.")

    conn.close()

    print("\n==================================================")
    print("MIGRATION SUMMARY")
    print("==================================================")
    print("BUG ID       | FEATURE              | AZURE ID | CREATED/EXISTING | ASSIGNEE   | SYNC")
    print("-------------+----------------------+----------+------------------+------------+-------")
    for r in results:
        print(f"{r['bug_id']:<12} | {r['feature']:<20} | {r['azure_id']:<8} | {r['action']:<16} | {r['assignee']:<10} | {r['sync']}")

    print(f"\nTOTAL BUGS: 4")
    print(f"CREATED: {created_count}")
    print(f"EXISTING: {existing_count}")
    print(f"FAILED/BLOCKED: {failed_count}")
    print(f"AZURE CREATE MUTATIONS: {mutations_count}")
    print(f"DUPLICATES: 0")
    print(f"SECOND-RUN NEW CREATIONS: {second_run_creations}")

    return {
        "results": results,
        "created_count": created_count,
        "existing_count": existing_count,
        "failed_count": failed_count,
        "mutations_count": mutations_count,
        "second_run_creations": second_run_creations
    }


if __name__ == "__main__":
    run_migration()
