#!/usr/bin/env python3
import os
import sys
import argparse
from datetime import datetime, timezone

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

PROCESS_OWNERS = {
    "P01-RFP": {"chiranjeevi", "chiranjeevi005"},
    "P02-SUPPLIER-DELIVERY": {"vrushali", "vrushaliapoojary"},
    "P03-REPLENISHMENT": {"bhushan", "bhushanshenoy07"},
    "P04-INVOICE-EXCEPTIONS": {"ashwin", "ashwinash19"}
}

def record_art_test(process_id, test_id, capability, status, notes, screenshot_path, repo_root, actor=None):
    valid_statuses = {'PASS', 'FAIL', 'BLOCKED', 'NOT_TESTED', 'PLANNED'}
    status_upper = status.upper()
    if status_upper not in valid_statuses:
        raise ValueError(f"Invalid status: '{status}'. Allowed: {sorted(list(valid_statuses))}")
        
    # Process ownership verification
    if actor:
        actor_clean = actor.strip().lower()
        expected_owners = PROCESS_OWNERS.get(process_id, set())
        if expected_owners and actor_clean not in expected_owners:
            raise PermissionError(
                f"Process ownership violation: Actor '{actor}' is not authorized to log tests for {process_id}. "
                f"Assigned owner is '{sorted(list(expected_owners))[0]}'."
            )
            
    # Execution evidence verification
    # Distinguish Planned tests, Actual executions, and Blocked tests
    test_type = "Planned Test"
    evidence_line = ""
    
    if status_upper in {'PASS', 'FAIL'}:
        test_type = "Actual Execution"
        has_file_evidence = bool(screenshot_path and os.path.exists(screenshot_path))
        notes_stripped = (notes or "").strip()
        has_detailed_notes = len(notes_stripped) >= 20 and notes_stripped.lower() != "automated test execution record."
        
        if not (has_file_evidence or has_detailed_notes):
            raise ValueError(
                f"Fabricated execution error: Actual execution status '{status_upper}' requires verifiable empirical "
                "execution evidence (an existing screenshot/artifact file on disk or a detailed execution trace). "
                "Never claim an execution occurred or passed/failed without empirical evidence."
            )
        if has_file_evidence:
            evidence_line = f"- **Evidence:** [{os.path.basename(screenshot_path)}]({screenshot_path})"
        else:
            evidence_line = f"- **Execution Evidence:** Trace notes verified on session output."
            
    elif status_upper == 'BLOCKED':
        test_type = "Blocked Test"
        notes_stripped = (notes or "").strip()
        if not notes_stripped or notes_stripped.lower() == "automated test execution record.":
            raise ValueError(
                "Blocked test requires specific notes explaining the dependency, outage, or blocker preventing execution."
            )
        evidence_line = f"- **Blocker Details:** {notes_stripped}"
        
    elif status_upper in {'NOT_TESTED', 'PLANNED'}:
        test_type = "Planned Test"
        evidence_line = "- **Status Note:** Test planned; not executed against live ART agent."

    proc_file = os.path.join(repo_root, 'research', 'procurement', 'processes', process_id, 'art-validation.md')
    if not os.path.exists(proc_file):
        raise FileNotFoundError(f"Process art-validation file not found: {proc_file}")
        
    now_iso = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    nl = chr(10)
    lines = [
        '',
        f"### Test Run: {test_id} ({now_iso})",
        f"- **Test Type:** {test_type}",
        f"- **Capability:** {capability}",
        f"- **Status:** **{status_upper}**",
        f"- **Notes:** {notes or 'No additional notes.'}"
    ]
    if evidence_line:
        lines.append(evidence_line)
    lines.append('')
    
    with open(proc_file, 'a', encoding='utf-8') as fp:
        fp.write(nl.join(lines))
        
    print(f"Recorded ART test ({test_type}) for {process_id} in {proc_file}: {status_upper}")
    return True

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--process-id', required=True, choices=['P01-RFP', 'P02-SUPPLIER-DELIVERY', 'P03-REPLENISHMENT', 'P04-INVOICE-EXCEPTIONS'])
    parser.add_argument('--test-id', required=True)
    parser.add_argument('--capability', required=True)
    parser.add_argument('--status', required=True, choices=['PASS', 'FAIL', 'BLOCKED', 'NOT_TESTED', 'PLANNED'])
    parser.add_argument('--notes', default='Automated test execution record.')
    parser.add_argument('--screenshot', default='')
    parser.add_argument('--actor', default='')
    parser.add_argument('--repo-root', default='.')
    args = parser.parse_args()
    record_art_test(args.process_id, args.test_id, args.capability, args.status, args.notes, args.screenshot, args.repo_root, actor=args.actor)
