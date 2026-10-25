"""
scripts/resolution_sync.py

CLI entry point for ART Bug Azure Resolution & Feedback Synchronization (Harness 03).
"""

import sys
import os
import argparse

# Add repo root to sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from core.lifecycle.resolution_sync import AzureResolutionSyncHarness


def main():
    parser = argparse.ArgumentParser(description="ART Azure Resolution & Feedback Sync Harness (Harness 03)")
    parser.add_argument("bug_id", nargs="?", help="Canonical ART Bug ID (e.g. ART-TOOL-003)")
    parser.add_argument("--all", action="store_true", help="Synchronize all tracked bugs in the master ledger")
    parser.add_argument("--force", action="store_true", help="Force sync even if no change is detected")
    args = parser.parse_args()

    if not args.bug_id and not args.all:
        parser.print_help()
        return 1

    harness = AzureResolutionSyncHarness(repo_root=REPO_ROOT)

    if args.all:
        import re
        ledger_path = os.path.join(REPO_ROOT, "ART-Product-Validation", "ART_PRODUCT_VALIDATION_LEDGER.md")
        with open(ledger_path, "r", encoding="utf-8") as f:
            ledger_text = f.read()
        bug_ids = re.findall(r"\[(ART-[A-Z0-9]+-[0-9]+)\]", ledger_text)

        print("==================================================")
        print("ART AZURE RESOLUTION SYNC (HARNESS 03) — BATCH")
        print(f"Total bugs to evaluate: {len(bug_ids)}")
        print("==================================================")

        results = []
        updated_count = 0
        no_change_count = 0
        failed_count = 0

        for bid in bug_ids:
            res = harness.sync_bug(canonical_bug_id=bid, force_sync=args.force)
            results.append(res)
            if res.status == "UPDATED":
                updated_count += 1
                print(f"[{bid}] UPDATED -> {res.art_disposition} (Primary: {res.primary_status}, Retest: {res.primary_retest})")
            elif res.status == "NO_CHANGE":
                no_change_count += 1
                print(f"[{bid}] NO_CHANGE -> {res.art_disposition} (Primary: {res.primary_status})")
            else:
                failed_count += 1
                print(f"[{bid}] FAILED -> Blocker: {res.blocker}")

        print("\n==================================================")
        print("BATCH SYNCHRONIZATION SUMMARY")
        print(f"Total Evaluated: {len(results)}")
        print(f"Updated: {updated_count}")
        print(f"No Change: {no_change_count}")
        print(f"Failed / Skipped: {failed_count}")
        print("==================================================")
        return 0

    result = harness.sync_bug(canonical_bug_id=args.bug_id, force_sync=args.force)

    print("==================================================")
    print("ART AZURE RESOLUTION & FEEDBACK SYNC (HARNESS 03)")
    print("==================================================")
    print(f"RESOLUTION SYNC: {result.status}")
    print(f"BUG ID: {result.canonical_bug_id}")
    if result.work_item_id:
        print(f"WORK ITEM: #{result.work_item_id}")
    if result.azure_state:
        print(f"AZURE STATE: {result.azure_state}")
    if result.azure_reason is not None:
        print(f"AZURE REASON: {result.azure_reason or 'Not provided'}")
    if result.current_assignee:
        print(f"CURRENT ASSIGNEE: {result.current_assignee}")
    print(f"NEW DEVELOPER FEEDBACK: {'YES' if result.new_developer_feedback else 'NO'}")
    if result.art_disposition:
        print(f"ART DISPOSITION: {result.art_disposition}")
    print(f"RETEST REQUIRED: {'YES' if result.retest_required else 'NO'}")
    if result.action_required:
        print(f"ACTION REQUIRED: {result.action_required}")
    print(f"LEDGER: {'UPDATED' if result.ledger_updated else ('NO_CHANGE' if result.status == 'NO_CHANGE' else 'FAILED')}")
    print(f"CANONICAL HISTORY: {'UPDATED' if result.canonical_history_updated else ('NO_CHANGE' if result.status == 'NO_CHANGE' else 'FAILED')}")
    print(f"AZURE MUTATIONS: {result.azure_mutations}")

    if result.art_disposition == "RETEST_REQUIRED":
        print("RETEST: REQUIRED")
    elif result.art_disposition == "PRODUCT_DECISION_PENDING":
        print("WAITING ON: PRODUCT DECISION")
    elif result.art_disposition == "REPRODUCED_AFTER_FIX":
        print("REOPEN: RECOMMENDED")

    print(f"PRIMARY LEDGER ROW: {'PASS' if result.success and result.primary_status else 'FAIL'}")
    print(f"PRIMARY STATUS: {result.primary_status or 'UNKNOWN'}")
    print(f"PRIMARY RETEST: {result.primary_retest or 'UNKNOWN'}")
    print(f"SUMMARY RECOMPUTED: {'PASS' if result.summary_recomputed else 'FAIL'}")
    print(f"SUMMARY INVARIANT: {'PASS' if result.summary_invariant else 'FAIL'}")
    print(f"LIFECYCLE TABLE: {'PASS' if result.lifecycle_table_updated else 'FAIL'}")
    print(f"LEDGER CONSISTENCY: {'PASS' if result.ledger_consistent else 'FAIL'}")

    if result.blocker:
        print(f"BLOCKER: {result.blocker}")

    return 0 if result.success else 1


if __name__ == "__main__":
    sys.exit(main())
