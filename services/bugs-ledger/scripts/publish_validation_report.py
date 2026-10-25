"""
scripts/publish_validation_report.py

CLI entry point for ART Public Validation Report Publisher (Harness 04).
Generates a sanitized local HTML report (docs/index.html) adhering to Harness 04 Refinement.
"""

import sys
import os
import argparse

# Add repo root to sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from core.reporting.public_report import PublicReportGenerator


def main():
    parser = argparse.ArgumentParser(description="ART Public Validation Report Publisher (Harness 04)")
    parser.add_argument("--ledger", help="Path to input master ledger markdown file")
    parser.add_argument("--output", help="Path to output HTML file (default: docs/index.html)")
    args = parser.parse_args()

    # Base repo root for project
    project_root = os.path.abspath(os.path.join(REPO_ROOT, "..", ".."))

    generator = PublicReportGenerator(repo_root=project_root)
    result = generator.generate_report(ledger_path=args.ledger, output_path=args.output)

    # Output Section M & Refinement completion format
    impl_status = "PASS" if result.success else "BLOCKED"
    print(f"IMPLEMENTATION: {impl_status}")
    print("HARNESS: HARNESS 04")
    print(f"SOURCE LEDGER: {'PASS' if result.source_ledger_ok else 'FAIL'}")
    print(f"6-COLUMN COMPATIBILITY: {'PASS' if result.six_column_compatibility_ok else 'FAIL'}")
    print(f"7-COLUMN OWNER COMPATIBILITY: {'PASS' if result.seven_column_owner_compatibility_ok else 'FAIL'}")
    print(f"OWNER PRIVACY: {'PASS' if result.owner_privacy_ok else 'FAIL'}")
    print(f"PUBLIC MODEL: {'PASS' if result.public_model_ok else 'FAIL'}")
    print(f"SUMMARY VALIDATION: {'PASS' if result.summary_validation_ok else 'FAIL'}")
    print(f"UNIQUE BUG ROWS: {'PASS' if result.unique_rows_ok else 'FAIL'}")
    print(f"STATUS FIDELITY: {'PASS' if result.status_fidelity_ok else 'FAIL'}")
    print(f"RETEST FIDELITY: {'PASS' if result.retest_fidelity_ok else 'FAIL'}")
    print(f"AZURE STATE SOURCE: {'PASS' if result.azure_state_source_ok else 'FAIL'}")
    print(f"AZURE STATE FIDELITY: {'PASS' if result.azure_state_fidelity_ok else 'FAIL'}")
    print(f"AZURE STATE FALLBACK: {'PASS' if result.azure_state_fallback_ok else 'FAIL'}")
    print(f"AZURE STATE FILTER: {'PASS' if result.azure_state_filter_ok else 'FAIL'}")
    print(f"AZURE/ART STATUS SEPARATION: {'PASS' if result.azure_art_status_separation_ok else 'FAIL'}")
    print(f"LATEST UPDATE: {'PASS' if result.latest_update_ok else 'FAIL'}")
    print(f"LIFECYCLE TIMESTAMP: {'PASS' if result.lifecycle_timestamp_ok else 'FAIL'}")
    print(f"HTML GENERATION: {'PASS' if result.html_generation_ok else 'FAIL'}")
    print(f"LIGHT THEME: {'PASS' if result.light_theme_ok else 'FAIL'}")
    print(f"SEARCH: {'PASS' if result.search_ok else 'FAIL'}")
    print(f"STATUS FILTER: {'PASS' if result.status_filter_ok else 'FAIL'}")
    print(f"FEATURE FILTER: {'PASS' if result.feature_filter_ok else 'FAIL'}")
    print(f"SEVERITY FILTER: {'PASS' if result.severity_filter_ok else 'FAIL'}")
    print(f"SANITIZATION: {'PASS' if result.sanitization_ok else 'FAIL'}")
    print(f"PRIVATE DATA SCAN: {'PASS' if result.private_data_scan_ok else 'FAIL'}")
    print(f"SOURCE IMMUTABILITY: {'PASS' if result.source_immutability_ok else 'FAIL'}")
    print(f"H03 FILES MODIFIED: {'YES' if result.h03_files_modified else 'NO'}")
    print(f"AZURE CONTACTED: {'YES' if result.azure_contacted else 'NO'}")
    print(f"AZURE MUTATIONS: {result.azure_mutations}")
    print(f"LEDGER MUTATIONS: {result.ledger_mutations}")
    print(f"SQLITE MUTATIONS: {result.sqlite_mutations}")
    print(f"LOCAL REPORT: {result.local_report_path or 'NOT_GENERATED'}")
    print("PUBLICATION: NOT PERFORMED")
    print("FILES CHANGED:")
    if result.files_changed:
        for f in result.files_changed:
            print(f"- {f}")
    else:
        print("NONE")
    print(f"BLOCKER: {result.blocker or 'NONE'}")
    print("\nSTOP.")

    return 0 if result.success else 1


if __name__ == "__main__":
    sys.exit(main())
