#!/usr/bin/env python3
"""
scripts/feature_pipeline.py

CLI executable for the ART Feature Backlog Pipeline.
Supports local-only feature intake, duplicate checking, and Azure synchronization.
"""

import sys
import os
import argparse
import json

# Ensure services/bugs-ledger is on sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICE_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
if SERVICE_ROOT not in sys.path:
    sys.path.insert(0, SERVICE_ROOT)

from core.features.models import FeatureClassification
from core.features.storage import FeatureStorageManager
from core.features.intake import FeatureIntakeHarness
from core.features.azure_sync import AzureFeatureSyncHarness
from core.features.pipeline import FeaturePipeline


def cmd_intake(args):
    storage = FeatureStorageManager()
    harness = FeatureIntakeHarness(storage)
    raw_input = {
        "title": args.title,
        "module": args.module,
        "classification": args.classification or FeatureClassification.NEW_FEATURE.value,
        "problem_opportunity": args.problem or args.desc or "",
        "current_behavior": args.current or "",
        "proposed_behavior": args.proposed or "",
        "business_impact": args.business_impact or "",
        "user_experience": args.user_experience or "",
        "implementation_guidance": args.guidance or "",
        "acceptance_criteria": args.criteria or [],
        "related_bugs": args.related_bugs or [],
        "feature_id": args.feature_id,
        "allow_update": args.allow_update,
    }

    result = harness.process_intake(
        raw_input=raw_input,
        evidence_files=args.evidence,
        is_test=getattr(args, "is_test", False)
    )

    if result.success and result.record:
        print("=" * 60)
        print("FEATURE INTAKE: SUCCESS")
        print(f"FEATURE ID: {result.feature_id}")
        print(f"TITLE: {result.record.title}")
        print(f"MODULE: {result.record.module}")
        print(f"CLASSIFICATION: {result.record.classification}")
        print(f"STORAGE PATH: {result.storage_path}")
        print(f"READY FOR AZURE: {'YES' if result.ready_for_azure else 'NO'}")
        if result.is_existing:
            print("MODE: EXISTING FEATURE UPDATED")
        if result.advisory:
            print(f"ADVISORY: {result.advisory}")
        print("=" * 60)
        return 0
    else:
        print("=" * 60, file=sys.stderr)
        print("FEATURE INTAKE: FAILED", file=sys.stderr)
        print(f"BLOCKER: {result.blocker}", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        return 1


def cmd_sync(args):
    storage = FeatureStorageManager()
    harness = AzureFeatureSyncHarness(storage_manager=storage)
    result = harness.sync_feature(
        feature_id=args.feature_id,
        assigned_to=args.assigned_to,
        dry_run=getattr(args, "dry_run", False)
    )

    if result.success:
        print("=" * 60)
        print("AZURE FEATURE SYNC: SUCCESS")
        print(f"FEATURE ID: {result.feature_id}")
        wi_str = f"#{result.work_item_id}" if result.work_item_id else "None (Dry Run / Unsynced)"
        print(f"WORK ITEM ID: {wi_str}")
        print(f"PARENT FEATURE ID: #{result.parent_feature_id}")
        print(f"WORK ITEM URL: {result.work_item_url or 'None'}")
        print(f"SYNC STATUS: {result.sync_status}")
        print(f"TICKET STATUS: {'EXISTING' if result.is_existing else 'CREATED'}")
        print("=" * 60)
        return 0
    else:
        print("=" * 60, file=sys.stderr)
        print("AZURE FEATURE SYNC: FAILED", file=sys.stderr)
        print(f"BLOCKER: {result.blocker}", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        return 1


def cmd_pipeline(args):
    storage = FeatureStorageManager()
    pipeline = FeaturePipeline(storage_manager=storage)
    raw_input = {
        "title": args.title,
        "module": args.module,
        "classification": args.classification or FeatureClassification.NEW_FEATURE.value,
        "problem_opportunity": args.problem or args.desc or "",
        "current_behavior": args.current or "",
        "proposed_behavior": args.proposed or "",
        "business_impact": args.business_impact or "",
        "user_experience": args.user_experience or "",
        "implementation_guidance": args.guidance or "",
        "acceptance_criteria": args.criteria or [],
        "related_bugs": args.related_bugs or [],
        "feature_id": args.feature_id,
        "allow_update": args.allow_update,
    }

    result = pipeline.run(
        raw_input=raw_input,
        evidence_files=args.evidence,
        local_only=args.local_only,
        assigned_to=args.assigned_to,
        is_test=getattr(args, "is_test", False),
        dry_run=getattr(args, "dry_run", False)
    )

    print("=" * 60)
    print(f"PIPELINE STATUS: {result.status}")
    print(f"FEATURE ID: {result.feature_id}")
    print(f"TITLE: {result.title}")
    print(f"MODULE: {result.module}")
    print(f"CLASSIFICATION: {result.classification}")
    if result.local_storage_path:
        print(f"LOCAL STORAGE: {result.local_storage_path}")
    if result.work_item_id:
        print(f"AZURE WORK ITEM: #{result.work_item_id}")
        print(f"PARENT FEATURE: #{result.parent_feature_id}")
        print(f"AZURE URL: {result.work_item_url}")
    print(f"AZURE STATUS: {result.azure_status}")
    if result.blocker:
        print(f"BLOCKER: {result.blocker}", file=sys.stderr)
    if result.advisory:
        print(f"ADVISORY: {result.advisory}")
    print("=" * 60)
    return 0 if result.success else 1


def cmd_compile(args):
    storage = FeatureStorageManager()
    ledger_path = storage.compile_ledger()
    print(f"Feature backlog ledger compiled successfully: {ledger_path}")
    return 0


def main():
    parser = argparse.ArgumentParser(description="ART Feature Backlog Pipeline CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # intake
    p_in = subparsers.add_parser("intake", help="Run Feature Intake Harness (Harness 01)")
    p_in.add_argument("--title", required=True, help="Feature title")
    p_in.add_argument("--module", required=True, help="Target ART module")
    p_in.add_argument("--problem", "--desc", dest="problem", help="Problem or opportunity description")
    p_in.add_argument("--current", help="Current behavior")
    p_in.add_argument("--proposed", help="Proposed behavior")
    p_in.add_argument("--business-impact", dest="business_impact", help="Business impact")
    p_in.add_argument("--user-experience", dest="user_experience", help="User experience")
    p_in.add_argument("--guidance", help="Implementation guidance")
    p_in.add_argument("--criteria", nargs="*", help="Acceptance criteria items")
    p_in.add_argument("--related-bugs", nargs="*", help="Related bug IDs or work items")
    p_in.add_argument("--classification", choices=["NEW_FEATURE", "ENHANCEMENT"], default="NEW_FEATURE")
    p_in.add_argument("--evidence", nargs="*", help="Evidence screenshot/file paths")
    p_in.add_argument("--feature-id", help="Existing feature ID for updates")
    p_in.add_argument("--allow-update", action="store_true", help="Allow updating near-duplicate feature")
    p_in.add_argument("--is-test", action="store_true", help="Allocate test prefix TEST-ART-FEAT-*")
    p_in.set_defaults(func=cmd_intake)

    # sync
    p_sync = subparsers.add_parser("sync", help="Run Azure Feature Ticket Harness (Harness 02)")
    p_sync.add_argument("--feature-id", required=True, help="Canonical Feature ID (e.g. ART-FEAT-AGENT-001)")
    p_sync.add_argument("--assigned-to", help="Assignee identity")
    p_sync.add_argument("--dry-run", action="store_true", help="Simulate sync without Azure mutation")
    p_sync.set_defaults(func=cmd_sync)

    # pipeline
    p_pipe = subparsers.add_parser("pipeline", help="Run Unified Feature Pipeline (Harness 01 -> Harness 02)")
    p_pipe.add_argument("--title", required=True, help="Feature title")
    p_pipe.add_argument("--module", required=True, help="Target ART module")
    p_pipe.add_argument("--problem", "--desc", dest="problem", help="Problem or opportunity description")
    p_pipe.add_argument("--current", help="Current behavior")
    p_pipe.add_argument("--proposed", help="Proposed behavior")
    p_pipe.add_argument("--business-impact", dest="business_impact", help="Business impact")
    p_pipe.add_argument("--user-experience", dest="user_experience", help="User experience")
    p_pipe.add_argument("--guidance", help="Implementation guidance")
    p_pipe.add_argument("--criteria", nargs="*", help="Acceptance criteria items")
    p_pipe.add_argument("--related-bugs", nargs="*", help="Related bug IDs or work items")
    p_pipe.add_argument("--classification", choices=["NEW_FEATURE", "ENHANCEMENT"], default="NEW_FEATURE")
    p_pipe.add_argument("--evidence", nargs="*", help="Evidence screenshot/file paths")
    p_pipe.add_argument("--feature-id", help="Existing feature ID for updates")
    p_pipe.add_argument("--allow-update", action="store_true", help="Allow updating near-duplicate feature")
    p_pipe.add_argument("--local-only", action="store_true", help="Store locally only; skip Azure sync")
    p_pipe.add_argument("--assigned-to", help="Assignee identity")
    p_pipe.add_argument("--is-test", action="store_true", help="Allocate test prefix TEST-ART-FEAT-*")
    p_pipe.add_argument("--dry-run", action="store_true", help="Dry run Azure sync")
    p_pipe.set_defaults(func=cmd_pipeline)

    # compile-ledger
    p_comp = subparsers.add_parser("compile-ledger", help="Recompile ART_FEATURE_BACKLOG_LEDGER.md")
    p_comp.set_defaults(func=cmd_compile)

    parsed = parser.parse_args()
    return parsed.func(parsed)


if __name__ == "__main__":
    sys.exit(main())
