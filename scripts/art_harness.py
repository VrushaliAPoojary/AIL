#!/usr/bin/env python3
"""
ART Unified Harness CLI — art_harness.py

Unified entry point for:
- Workspace & Bug Ledger Validation
- ART Test Execution Logging (Harness A)
- Draft Bug Creation & Duplicate Detection (Harness B)
- Bug Retest Recording (Harness B)
- Canonical Bug ID Promotion (Harness C — Coordinator Only)
- Summary Ledger Compilation
- Authorized Azure DevOps Synchronization (Guarded — Coordinator Only)
"""

import sys
import os
import argparse
import subprocess
import getpass
from typing import Tuple, Optional

# Configure UTF-8 console output for cross-platform consistency (Windows/Linux)
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Ensure child processes inherit UTF-8 encoding
os.environ["PYTHONUTF8"] = "1"
os.environ["PYTHONIOENCODING"] = "utf-8"

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BUGS_ROOT = os.path.join(REPO_ROOT, "services", "bugs-ledger", "ART-Product-Validation", "bugs")
SCRIPTS_DIR = os.path.join(REPO_ROOT, "scripts", "validation")
COORDINATOR_USER = "chiranjeevi"
COORDINATOR_GITHUB_LOGIN = "Chiranjeevi005"

# Approved Research Ownership Architecture
PROCESS_MAP = {
    "P01-RFP": {
        "owner": "chiranjeevi",
        "github": "Chiranjeevi005",
        "code": "P01",
        "name": "RFP Requirement Review & Response Coordination",
        "dir": "research/procurement/processes/P01-RFP",
        "branch": "research/chiranjeevi",
        "role": "coordinator and contributor",
    },
    "P02-SUPPLIER-DELIVERY": {
        "owner": "vrushali",
        "github": "VrushaliAPoojary",
        "code": "P02",
        "name": "Supplier Delivery Confirmation & Delay Escalation",
        "dir": "research/procurement/processes/P02-SUPPLIER-DELIVERY",
        "branch": "research/vrushali",
        "role": "contributor",
    },
    "P03-REPLENISHMENT": {
        "owner": "bhushan",
        "github": "BhushanShenoy07",
        "code": "P03",
        "name": "Inventory Replenishment & Reorder Exceptions",
        "dir": "research/procurement/processes/P03-REPLENISHMENT",
        "branch": "research/bhushan",
        "role": "contributor",
    },
    "P04-INVOICE-EXCEPTIONS": {
        "owner": "ashwin",
        "github": "ashwinash19",
        "code": "P04",
        "name": "Invoice Discrepancy Resolution",
        "dir": "research/procurement/processes/P04-INVOICE-EXCEPTIONS",
        "branch": "research/ashwin",
        "role": "contributor",
    },
}

CONTRIBUTOR_TO_PROCESS = {
    "chiranjeevi": "P01-RFP",
    "chiranjeevi005": "P01-RFP",
    "vrushali": "P02-SUPPLIER-DELIVERY",
    "vrushaliapoojary": "P02-SUPPLIER-DELIVERY",
    "bhushan": "P03-REPLENISHMENT",
    "bhushanshenoy07": "P03-REPLENISHMENT",
    "ashwin": "P04-INVOICE-EXCEPTIONS",
    "ashwinash19": "P04-INVOICE-EXCEPTIONS",
}

CONTRIBUTOR_TO_CODE = {
    "chiranjeevi": "P01",
    "chiranjeevi005": "P01",
    "vrushali": "P02",
    "vrushaliapoojary": "P02",
    "bhushan": "P03",
    "bhushanshenoy07": "P03",
    "ashwin": "P04",
    "ashwinash19": "P04",
}

CODE_TO_OWNER = {
    "P01": "chiranjeevi",
    "P02": "vrushali",
    "P03": "bhushan",
    "P04": "ashwin",
}

def verify_coordinator_authorization(declared_user: Optional[str] = None) -> Tuple[bool, str]:
    """
    Verify that the execution environment genuinely possesses Project Coordinator authority.
    Never treats local OS usernames, local Git configuration (user.name/email),
    or self-declared command-line arguments as sufficient privilege verification.
    Requires a verified, trusted authentication session matching GitHub identity 'Chiranjeevi005'.
    Fails closed for privileged operations when trusted authorization is unavailable.
    """
    # 1. Reject if declared user contradicts coordinator
    if declared_user and declared_user.strip().lower() not in {COORDINATOR_USER, COORDINATOR_GITHUB_LOGIN.lower()}:
        return False, f"Declared user '{declared_user}' is not authorized. Coordinator operations are restricted to '{COORDINATOR_GITHUB_LOGIN}'."

    # 2. Local OS usernames, environment variables, and Git config are easily spoofed locally
    # and are strictly rejected as insufficient evidence of coordinator authority.

    # 3. Trusted verification: Query active GitHub authenticated identity via GitHub CLI
    try:
        res_gh = subprocess.run(
            ["gh", "api", "user", "--jq", ".login"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
            timeout=10
        )
        if res_gh.returncode == 0:
            authenticated_login = res_gh.stdout.strip()
            if authenticated_login.lower() == COORDINATOR_GITHUB_LOGIN.lower():
                return True, f"Verified coordinator authority: authenticated GitHub identity '{authenticated_login}'"
            else:
                return False, (
                    f"Coordinator verification failed: Authenticated GitHub identity is '{authenticated_login}', "
                    f"but coordinator operations are restricted to '{COORDINATOR_GITHUB_LOGIN}'. Failing closed."
                )
    except Exception:
        pass

    # If trusted verification is unavailable or failed, fail closed
    return False, (
        f"Coordinator authorization failed: Trusted GitHub authenticated session for '{COORDINATOR_GITHUB_LOGIN}' is unavailable.\n"
        "Local OS usernames, Git config (user.name/email), and self-declared flags are unverified and insufficient for privileged operations.\n"
        "Failing closed."
    )

def cmd_validate(args):
    """Run validation checks across research workspace, bugs ledger, and unit tests."""
    print("=" * 60)
    print("ART INVESTIGATION LAB — UNIFIED SYSTEM VALIDATION")
    print("=" * 60)
    
    all_passed = True
    
    # 1. Procurement workspace check
    proc_script = os.path.join(REPO_ROOT, "scripts", "procurement", "validate-procurement-workspace.py")
    if os.path.exists(proc_script):
        print("\n[1/3] Validating Procurement Research Workspace...")
        res = subprocess.run([sys.executable, proc_script, "--repo-root", REPO_ROOT])
        if res.returncode != 0:
            print("❌ Procurement workspace validation FAILED")
            all_passed = False
        else:
            print("✅ Procurement workspace validation PASSED")
            
    # 2. Bug ledger schema & link check
    bugs_script = os.path.join(SCRIPTS_DIR, "validate-art-bugs.py")
    if os.path.exists(bugs_script):
        print("\n[2/3] Validating ART Bugs Ledger & Evidence Links...")
        res = subprocess.run([sys.executable, bugs_script, "--bugs-root", BUGS_ROOT])
        if res.returncode != 0:
            print("❌ Bugs ledger validation FAILED")
            all_passed = False
        else:
            print("✅ Bugs ledger validation PASSED")
            
    # 3. Unit tests check
    tests_dir = os.path.join(REPO_ROOT, "services", "bugs-ledger", "tests")
    if os.path.exists(tests_dir) and not getattr(args, "skip_unit_tests", False):
        print("\n[3/3] Running Bugs Ledger Unit Tests (pytest)...")
        res = subprocess.run([sys.executable, "-m", "pytest", "tests/", "-q"], cwd=os.path.join(REPO_ROOT, "services", "bugs-ledger"))
        if res.returncode != 0:
            print("❌ Unit test suite FAILED")
            all_passed = False
        else:
            print("✅ All 264 unit tests PASSED")
            
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL VALIDATIONS PASSED CLEANLY")
        return 0
    else:
        print("⚠️ VALIDATION FAILURES DETECTED")
        return 1

def cmd_record_test(args):
    """Record an ART test outcome linked to research (Harness A)."""
    # Verify process ownership if actor is supplied
    if getattr(args, "actor", None):
        actor_clean = args.actor.strip().lower()
        expected_proc = CONTRIBUTOR_TO_PROCESS.get(actor_clean)
        if expected_proc and expected_proc != args.process_id:
            proc_meta = PROCESS_MAP.get(expected_proc, {})
            print(f"❌ PROCESS OWNERSHIP VIOLATION: Contributor '{args.actor}' is assigned to {expected_proc} ({proc_meta.get('name')}), not {args.process_id}.", file=sys.stderr)
            print(f"   Each contributor must record test executions strictly within their assigned process boundary.", file=sys.stderr)
            return 1
            
    # Distinguish Planned Tests, Actual Executions, and Blocked Tests
    status_upper = args.status.upper()
    if status_upper in {"PASS", "FAIL"}:
        # Requires empirical execution evidence
        has_file = bool(args.screenshot and os.path.exists(args.screenshot))
        notes_str = (args.notes or "").strip()
        has_detailed_notes = len(notes_str) >= 20 and notes_str.lower() != "automated test execution record."
        if not (has_file or has_detailed_notes):
            print(f"❌ FABRICATED EXECUTION REJECTED: Status '{status_upper}' requires verifiable empirical execution evidence.", file=sys.stderr)
            print("   Please provide an existing screenshot/artifact file or a detailed execution trace.", file=sys.stderr)
            return 1
    elif status_upper == "BLOCKED":
        notes_str = (args.notes or "").strip()
        if not notes_str or notes_str.lower() == "automated test execution record.":
            print("❌ BLOCKED TEST INCOMPLETE: Blocked tests require specific notes explaining the dependency or obstacle.", file=sys.stderr)
            return 1

    script = os.path.join(SCRIPTS_DIR, "art_validation_harness.py")
    cmd = [
        sys.executable, script,
        "--process-id", args.process_id,
        "--test-id", args.test_id,
        "--capability", args.capability,
        "--status", args.status,
        "--notes", args.notes or "",
        "--repo-root", REPO_ROOT
    ]
    if args.actor:
        cmd.extend(["--actor", args.actor])
    if args.screenshot:
        cmd.extend(["--screenshot", args.screenshot])
    return subprocess.run(cmd, cwd=REPO_ROOT).returncode

def cmd_draft_bug(args):
    """Create a new draft bug with duplicate detection (Harness B)."""
    contributor_val = args.contributor.strip().upper()
    
    # Process ownership verification if actor is supplied
    if getattr(args, "actor", None):
        actor_clean = args.actor.strip().lower()
        expected_code = CONTRIBUTOR_TO_CODE.get(actor_clean)
        if expected_code and contributor_val != expected_code:
            expected_proc = CONTRIBUTOR_TO_PROCESS.get(actor_clean)
            proc_meta = PROCESS_MAP.get(expected_proc, {})
            print(f"❌ PROCESS OWNERSHIP VIOLATION: Contributor '{args.actor}' is assigned to {expected_code} ({proc_meta.get('name')}), not {contributor_val}.", file=sys.stderr)
            return 1
            
    script = os.path.join(SCRIPTS_DIR, "bug_intake_harness.py")
    cmd = [
        sys.executable, script, "create-draft",
        "--contributor", contributor_val,
        "--module", args.module,
        "--title", args.title,
        "--desc", args.desc,
        "--severity", args.severity or "MEDIUM",
        "--repo-root", REPO_ROOT
    ]
    if getattr(args, "actor", None):
        cmd.extend(["--actor", args.actor])
    if args.evidence:
        cmd.append("--evidence")
        cmd.extend(args.evidence)
    return subprocess.run(cmd, cwd=REPO_ROOT).returncode

def cmd_retest(args):
    """Record a retest verification against an existing bug (Harness B)."""
    actor_clean = (args.actor or "").strip().lower()
    actor_role = getattr(args, "actor_role", "HUMAN").strip().upper()
    
    # Strict Human-Only Verification Guard
    if actor_role == "AI" or actor_clean in {"ai", "antigravity", "assistant", "bot", "agent"}:
        print("❌ PERMISSION DENIED: AI actors are strictly forbidden from submitting verification or confirming bug status.", file=sys.stderr)
        print("   Human verification is required. Retest sign-off must be performed by a human team member.", file=sys.stderr)
        return 1
        
    script = os.path.join(SCRIPTS_DIR, "bug_intake_harness.py")
    cmd = [
        sys.executable, script, "retest",
        "--bug-id", args.bug_id,
        "--actor", args.actor,
        "--actor-role", actor_role,
        "--verdict", args.verdict,
        "--notes", args.notes or "",
        "--repo-root", REPO_ROOT
    ]
    if args.evidence:
        cmd.append("--evidence")
        cmd.extend(args.evidence)
    return subprocess.run(cmd, cwd=REPO_ROOT).returncode

def cmd_promote(args):
    """Promote a draft bug to a canonical ART-* ID (Harness C — Coordinator Only)."""
    # Strict Coordinator Authorization Verification (Does not trust self-declared flags)
    authorized, reason = verify_coordinator_authorization(declared_user=args.coordinator)
    if not authorized:
        print(f"❌ PERMISSION DENIED: {reason}", file=sys.stderr)
        print("   Canonical ID promotion is strictly reserved for verified Project Coordinator Chiranjeevi.", file=sys.stderr)
        return 1
        
    script = os.path.join(SCRIPTS_DIR, "promote_canonical_bug.py")
    cmd = [
        sys.executable, script,
        "--draft-id", args.draft_id,
        "--coordinator", COORDINATOR_USER,
        "--repo-root", REPO_ROOT
    ]
    return subprocess.run(cmd, cwd=REPO_ROOT).returncode

def cmd_compile_ledger(args):
    """Compile ART_PRODUCT_VALIDATION_LEDGER.md from disk bug records."""
    script = os.path.join(SCRIPTS_DIR, "compile_ledger.py")
    output_path = os.path.join(REPO_ROOT, "services", "bugs-ledger", "ART-Product-Validation", "ART_PRODUCT_VALIDATION_LEDGER.md")
    return subprocess.run([
        sys.executable, script,
        "--bugs-root", BUGS_ROOT,
        "--output", output_path
    ], cwd=REPO_ROOT).returncode

def cmd_sync_azure(args):
    """Synchronize canonical bug records to Azure DevOps (Guarded — Coordinator Only)."""
    # Strict Coordinator Authorization Verification
    authorized, reason = verify_coordinator_authorization(declared_user=args.coordinator)
    if not authorized:
        print(f"❌ PERMISSION DENIED: {reason}", file=sys.stderr)
        return 1

    # Check for Azure credentials in environment
    azure_pat = os.environ.get("AZURE_DEVOPS_EXT_PAT") or os.environ.get("AZURE_DEVOPS_PAT")
    if not azure_pat and not getattr(args, "dry_run", False):
        print("❌ AZURE AUTHENTICATION UNAVAILABLE: Neither AZURE_DEVOPS_EXT_PAT nor AZURE_DEVOPS_PAT found in environment.", file=sys.stderr)
        print("   Cannot synchronize to Azure DevOps without authenticated credentials. Failing closed.", file=sys.stderr)
        return 1

    if not getattr(args, "confirm_azure_sync", False) and not getattr(args, "dry_run", False):
        print("❌ AUTHORIZATION REQUIRED: Writing to Azure DevOps requires the explicit '--confirm-azure-sync' flag.", file=sys.stderr)
        print("   Use '--dry-run' for read-only inspection.", file=sys.stderr)
        return 1

    script = os.path.join(SCRIPTS_DIR, "migrate_canonical_bugs_to_azure.py")
    if not os.path.exists(script):
        print(f"❌ Azure migration script not found: {script}", file=sys.stderr)
        return 1

    cmd = [sys.executable, script]
    if getattr(args, "dry_run", False):
        cmd.append("--dry-run")
    return subprocess.run(cmd, cwd=REPO_ROOT).returncode

def main():
    parser = argparse.ArgumentParser(
        description="ART Unified Harness CLI — Coordinates research, testing, bug lifecycle, and validations."
    )
    subparsers = parser.add_subparsers(dest="command", required=True, help="Available subcommands")
    
    # validate
    val_p = subparsers.add_parser("validate", help="Run workspace, bug ledger, and test suite validations.")
    val_p.add_argument("--skip-unit-tests", action="store_true", help="Skip running pytest unit tests.")
    val_p.set_defaults(func=cmd_validate)
    
    # record-test (Harness A)
    rt_p = subparsers.add_parser("record-test", help="Record an ART test outcome (Harness A).")
    rt_p.add_argument("--process-id", required=True, choices=["P01-RFP", "P02-SUPPLIER-DELIVERY", "P03-REPLENISHMENT", "P04-INVOICE-EXCEPTIONS"], help="Procurement process ID")
    rt_p.add_argument("--test-id", required=True, help="Test execution ID (e.g. TEST-P02-001)")
    rt_p.add_argument("--capability", required=True, help="Target ART capability evaluated")
    rt_p.add_argument("--status", required=True, choices=["PASS", "FAIL", "BLOCKED", "NOT_TESTED", "PLANNED"], help="Execution verdict")
    rt_p.add_argument("--notes", help="Execution observation notes or blocker reason")
    rt_p.add_argument("--screenshot", help="Path to evidence screenshot or artifact")
    rt_p.add_argument("--actor", help="Contributor username (e.g. vrushali)")
    rt_p.set_defaults(func=cmd_record_test)
    
    # draft-bug (Harness B)
    db_p = subparsers.add_parser("draft-bug", help="Create a draft bug with duplicate detection (Harness B).")
    db_p.add_argument("--contributor", required=True, choices=["P01", "P02", "P03", "P04"], help="Contributor process code")
    db_p.add_argument("--module", required=True, help="Target module (Agent, Governance, Orchestrator, Serverless, Tool, AgentX)")
    db_p.add_argument("--title", required=True, help="Concise bug title")
    db_p.add_argument("--desc", required=True, help="Bug description / repro steps")
    db_p.add_argument("--severity", choices=["LOW", "MEDIUM", "HIGH", "CRITICAL"], default="MEDIUM", help="Bug severity")
    db_p.add_argument("--evidence", nargs="*", help="Evidence screenshot paths")
    db_p.add_argument("--actor", help="Contributor username (e.g. vrushali)")
    db_p.set_defaults(func=cmd_draft_bug)
    
    # retest (Harness B)
    ret_p = subparsers.add_parser("retest", help="Submit a retest verification against an existing bug (Harness B).")
    ret_p.add_argument("--bug-id", required=True, help="Canonical bug ID (e.g. ART-AGENT-001)")
    ret_p.add_argument("--actor", required=True, help="Contributor username (must be human member, e.g. ashwin)")
    ret_p.add_argument("--actor-role", default="HUMAN", choices=["HUMAN", "AI"], help="Actor role (AI is forbidden from confirming verification)")
    ret_p.add_argument("--verdict", required=True, choices=["PASSED", "FAILED", "INCONCLUSIVE", "VERIFIED"], help="Retest verdict")
    ret_p.add_argument("--notes", help="Retest observation notes")
    ret_p.add_argument("--evidence", nargs="*", help="Evidence screenshot paths")
    ret_p.set_defaults(func=cmd_retest)
    
    # promote-bug (Harness C)
    pb_p = subparsers.add_parser("promote-bug", help="Promote a draft bug to canonical ART ID (Harness C — Coordinator Only).")
    pb_p.add_argument("--draft-id", required=True, help="Draft ID (e.g. DRAFT-P03-AGENT-001)")
    pb_p.add_argument("--coordinator", default=None, help="Coordinator username (must be verified 'chiranjeevi')")
    pb_p.set_defaults(func=cmd_promote)
    
    # compile-ledger
    cl_p = subparsers.add_parser("compile-ledger", help="Recompile ART_PRODUCT_VALIDATION_LEDGER.md summary table.")
    cl_p.set_defaults(func=cmd_compile_ledger)
    
    # sync-azure
    az_p = subparsers.add_parser("sync-azure", help="Synchronize canonical bugs to Azure DevOps (Guarded — Coordinator Only).")
    az_p.add_argument("--coordinator", default=None, help="Coordinator username (must be verified 'chiranjeevi')")
    az_p.add_argument("--confirm-azure-sync", action="store_true", help="Explicit human confirmation for writing to Azure DevOps")
    az_p.add_argument("--dry-run", action="store_true", help="Perform dry-run inspection without writing to Azure DevOps")
    az_p.set_defaults(func=cmd_sync_azure)
    
    args = parser.parse_args()
    sys.exit(args.func(args))

if __name__ == "__main__":
    main()
