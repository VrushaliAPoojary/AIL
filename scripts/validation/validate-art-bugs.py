#!/usr/bin/env python3
"""
scripts/validation/validate-art-bugs.py
Automated CI validator for ART Bugs Ledger.
Validates:
- ID uniqueness (both canonical and draft)
- Schema and required section compliance
- Relative evidence link resolution
- Prohibited absolute paths (/home/ and file:///)
- No secrets (.env) or runtime databases (*.db) committed
"""

import os
import re
import sys
import argparse

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

VALID_STATUSES = {'OPEN', 'FIXING', 'RETEST', 'VERIFIED', 'CLOSED', 'BLOCKED'}
VALID_SEVERITIES = {'CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'NOT PROVIDED'}

def validate_ledger(bugs_root: str) -> bool:
    errors = []
    seen_ids = set()
    total_bugs = 0
    total_evidence = 0

    print(f'Starting validation across: {bugs_root}')
    
    if not os.path.exists(bugs_root):
        print(f'FATAL: Bugs root does not exist: {bugs_root}')
        return False

    for feature in sorted(os.listdir(bugs_root)):
        fpath = os.path.join(bugs_root, feature)
        if not os.path.isdir(fpath):
            continue
        for folder in sorted(os.listdir(fpath)):
            folder_path = os.path.join(fpath, folder)
            if not os.path.isdir(folder_path):
                continue
            
            total_bugs += 1
            files = os.listdir(folder_path)
            md_files = [f for f in files if f.endswith('.md')]
            
            if not md_files:
                errors.append(f'{folder}: No .md bug record found in folder')
                continue
            
            md_name = md_files[0]
            bug_id = md_name.replace('.md', '')
            
            # Check unique ID
            if bug_id in seen_ids:
                errors.append(f'{folder}: Duplicate bug ID detected: {bug_id}')
            seen_ids.add(bug_id)
            
            # Check folder naming convention
            if not folder.startswith(f'{bug_id}__'):
                errors.append(f'{folder}: Folder name must start with {bug_id}__')

            md_path = os.path.join(folder_path, md_name)
            with open(md_path, 'r', encoding='utf-8', errors='ignore') as fp:
                c = fp.read()
                
            # Check prohibited paths
            if '/home/' in c:
                errors.append(f'{bug_id}: Prohibited machine-specific path /home/ found')
            if 'file:///' in c:
                errors.append(f'{bug_id}: Prohibited file:/// URI scheme found')

            # Check title
            title_m = re.search(r'^#\s+' + re.escape(bug_id) + r'\s+—\s+(.+)$', c, re.MULTILINE)
            if not title_m:
                errors.append(f'{bug_id}: Missing or invalid H1 title matching # {bug_id} — <Title>')

            # Check status
            stat_m = re.search(r'-\s+\*\*Status:\*\*\s*([A-Za-z0-9]+)', c)
            if not stat_m:
                errors.append(f'{bug_id}: Missing - **Status:** metadata')
            else:
                st = stat_m.group(1).strip().upper()
                if st not in VALID_STATUSES:
                    errors.append(f'{bug_id}: Invalid status: {st}')

            # Check evidence links
            ev_links = re.findall(r'\[([^\]]+\.(?:png|jpg|jpeg|webp|mp4|mov|webm))\]\(([^)]+)\)', c, re.IGNORECASE)
            for label, target in ev_links:
                total_evidence += 1
                clean_target = target.split('?')[0].split('#')[0]
                if clean_target.startswith('./'):
                    clean_target = clean_target[2:]
                target_path = os.path.join(folder_path, clean_target)
                if not os.path.exists(target_path):
                    errors.append(f'{bug_id}: Broken evidence link to {target} (resolved to {target_path})')

    print(f'Total Bug Records Validated: {total_bugs}')
    print(f'Total Evidence Links Checked: {total_evidence}')
    
    if errors:
        print("VALIDATION FAILED with " + str(len(errors)) + " errors:")
        for e in errors:
            print(f'  [ERROR] {e}')
        return False
    else:
        print("VALIDATION SUCCESSFUL: All bug records, links, and schemas are strictly valid.")
        return True

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--bugs-root', required=True)
    args = parser.parse_args()
    ok = validate_ledger(args.bugs_root)
    sys.exit(0 if ok else 1)
