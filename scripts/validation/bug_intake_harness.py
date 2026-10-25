#!/usr/bin/env python3
import os
import sys
import re
import shutil
import hashlib
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

CANONICAL_MODULES = {'AGENT', 'GOV', 'SFN', 'ORCHESTRATOR', 'ORC', 'TOOL', 'TOOLBUILDER', 'AGENTX', 'ADK', 'TRIGGER', 'MCP', 'CRED'}

MODULE_TO_FEATURE = {
    'AGENT': 'Agent Lab',
    'ORCHESTRATOR': 'Orchestrator',
    'ORC': 'Orchestrator',
    'TOOL': 'Tool Builder',
    'TOOLBUILDER': 'Tool Builder',
    'SFN': 'Serverless Functions',
    'GOV': 'Governance',
    'AGENTX': 'Agent X',
    'ADK': 'ART Deployment Kit (ADK)',
    'MCP': 'MCP Servers',
    'TRIGGER': 'Triggers',
    'CRED': 'Credential Manager'
}

CONTRIBUTOR_PROCESS_MAP = {
    'chiranjeevi': 'P01',
    'chiranjeevi005': 'P01',
    'vrushali': 'P02',
    'vrushaliapoojary': 'P02',
    'bhushan': 'P03',
    'bhushanshenoy07': 'P03',
    'ashwin': 'P04',
    'ashwinash19': 'P04'
}

def create_slug(title):
    clean = re.sub(r'[^a-zA-Z0-9 -]', '', title).lower()
    return re.sub(r'[ -]+', '-', clean).strip('-')[:50]

def check_duplicates(title, description, bugs_root):
    matches = []
    norm_title_words = set(re.findall(r'[a-zA-Z0-9]+', title.lower())) - {'a', 'an', 'the', 'is', 'in', 'at', 'to', 'for', 'and', 'art'}
    if not os.path.exists(bugs_root): return matches
    for feature in os.listdir(bugs_root):
        fpath = os.path.join(bugs_root, feature)
        if not os.path.isdir(fpath): continue
        for folder in os.listdir(fpath):
            folder_path = os.path.join(fpath, folder)
            if not os.path.isdir(folder_path): continue
            md_files = [f for f in os.listdir(folder_path) if f.endswith('.md')]
            if not md_files: continue
            md_path = os.path.join(folder_path, md_files[0])
            with open(md_path, 'r', errors='ignore') as fp:
                c = fp.read()
            doc_words = set(re.findall(r'[a-zA-Z0-9]+', c.lower()))
            overlap = norm_title_words & doc_words
            ratio = len(overlap) / len(norm_title_words) if norm_title_words else 0
            if ratio >= 0.5:
                matches.append((md_files[0].replace('.md', ''), ratio, folder))
    return sorted(matches, key=lambda x: x[1], reverse=True)

def create_draft(contributor, module, title, description, severity, evidence_files, repo_root, actor=None):
    if actor:
        actor_clean = actor.strip().lower()
        expected_code = CONTRIBUTOR_PROCESS_MAP.get(actor_clean)
        if expected_code and contributor.strip().upper() != expected_code:
            raise PermissionError(
                f"Process ownership violation: Actor '{actor}' is assigned to {expected_code}, not {contributor}."
            )
            
    nl = chr(10)
    module_norm = module.strip().upper()
    if module_norm not in CANONICAL_MODULES:
        raise ValueError('Invalid module: ' + module + '. Allowed: ' + str(sorted(list(CANONICAL_MODULES))))
    
    feature = MODULE_TO_FEATURE.get(module_norm, 'Agent Lab')
    bugs_root = os.path.join(repo_root, 'services', 'bugs-ledger', 'ART-Product-Validation', 'bugs')
    drafts_root = os.path.join(repo_root, 'services', 'bugs-ledger', 'ART-Product-Validation', 'drafts')
    os.makedirs(drafts_root, exist_ok=True)
    
    dups = check_duplicates(title, description, bugs_root)
    if dups:
        print('[NOTICE] Potential duplicate bugs detected:')
        for d_id, ratio, d_folder in dups[:3]:
            print('  - ' + d_id + ' (' + str(round(ratio*100, 1)) + '% overlap): ' + d_folder)
            
    existing_drafts = [d for d in os.listdir(drafts_root) if os.path.isdir(os.path.join(drafts_root, d))]
    seq = 1
    for ed in existing_drafts:
        m = re.match(r'^DRAFT-' + contributor + r'-' + module_norm + r'-([0-9]{3})', ed)
        if m:
            s_num = int(m.group(1))
            if s_num >= seq: seq = s_num + 1
            
    draft_id = 'DRAFT-' + contributor + '-' + module_norm + '-' + str(seq).zfill(3)
    slug = create_slug(title)
    folder_name = draft_id + '__' + slug
    draft_dir = os.path.join(drafts_root, folder_name)
    os.makedirs(draft_dir, exist_ok=True)
    
    ev_lines = []
    now_date = datetime.now(timezone.utc).strftime('%Y%m%d')
    for idx, ef in enumerate(evidence_files or [], start=1):
        if not os.path.exists(ef):
            print('Warning: Evidence file not found: ' + ef)
            continue
        ext = os.path.splitext(ef)[1].lower()
        ev_dest_name = draft_id + '__' + now_date + '__' + str(idx).zfill(3) + ext
        ev_dest_path = os.path.join(draft_dir, ev_dest_name)
        shutil.copy2(ef, ev_dest_path)
        ev_lines.append('- [' + ev_dest_name + '](./' + ev_dest_name + ')')
        
    if not ev_lines:
        ev_lines = ['- Pending evidence capture.']
        
    lines = [
        '# ' + draft_id + ' — ' + title,
        '',
        '- **Severity:** ' + severity.upper(),
        '- **Status:** OPEN',
        '',
        '## Bug',
        '',
        description,
        '',
        '## Expected',
        '',
        'Expected platform behavior per contract specifications.',
        '',
        '## Actual',
        '',
        'Observed behavior as documented in evidence.',
        '',
        '## Evidence',
        ''
    ] + ev_lines + [
        '',
        '## Production-Grade Fix Proposal',
        '',
        '### Required implementation',
        '',
        '1. Investigate affected component logic in ' + feature + '.',
        '2. Ensure contract validation blocks invalid state.',
        '',
        '### Acceptance criteria',
        '',
        '- Defect is reproducible with attached evidence.',
        '- Verified resolution passes regression retest.',
        '',
        '## Developer Update',
        '',
        'Pending.',
        '',
        '## Retest',
        '',
        'Pending.',
        '',
        '## Azure DevOps',
        '',
        '- **Work Item ID:** Pending Coordinator Review',
        '- **Assigned To:** Unassigned',
        '- **Sync Status:** DRAFT',
        ''
    ]
    
    md_path = os.path.join(draft_dir, draft_id + '.md')
    with open(md_path, 'w', encoding='utf-8') as fp:
        fp.write(nl.join(lines))
        
    print('Created draft bug record: ' + md_path)
    return draft_id, draft_dir

def submit_retest(bug_id, verdict, actor, actor_role, evidence_files, notes, repo_root):
    nl = chr(10)
    actor_clean = (actor or '').strip().lower()
    if actor_role == 'AI' or actor_clean in {'ai', 'antigravity', 'assistant', 'bot', 'agent'}:
        raise PermissionError('AI actors are strictly forbidden from submitting verification or confirming VERIFIED status. Verification must be performed and signed off by a human team member.')
    
    valid_verdicts = {'PASSED', 'FAILED', 'INCONCLUSIVE', 'VERIFIED'}
    if verdict.upper() not in valid_verdicts:
        raise ValueError('Invalid verdict: ' + verdict + '. Allowed: ' + str(valid_verdicts))
        
    bugs_root = os.path.join(repo_root, 'services', 'bugs-ledger', 'ART-Product-Validation', 'bugs')
    target_md = None
    target_dir = None
    for feature in os.listdir(bugs_root):
        fpath = os.path.join(bugs_root, feature)
        if not os.path.isdir(fpath): continue
        for folder in os.listdir(fpath):
            if folder.startswith(bug_id + '__'):
                target_dir = os.path.join(fpath, folder)
                target_md = os.path.join(target_dir, bug_id + '.md')
                break
        if target_md: break
        
    if not target_md or not os.path.exists(target_md):
        raise FileNotFoundError('Bug record not found for ID: ' + bug_id)
        
    now_date = datetime.now(timezone.utc).strftime('%Y%m%d')
    copied_ev = []
    for idx, ef in enumerate(evidence_files or [], start=1):
        if os.path.exists(ef):
            ext = os.path.splitext(ef)[1]
            ev_name = bug_id + '__RETEST_' + now_date + '__' + str(idx).zfill(2) + ext
            shutil.copy2(ef, os.path.join(target_dir, ev_name))
            copied_ev.append('- [' + ev_name + '](./' + ev_name + ')')
            
    with open(target_md, 'r', encoding='utf-8') as fp:
        content = fp.read()
        
    new_status = 'VERIFIED' if verdict.upper() == 'VERIFIED' else ('FIXING' if verdict.upper() == 'FAILED' else 'RETEST')
    content = re.sub(r'-\s+\*\*Status:\*\*\s*[A-Za-z]+', '- **Status:** ' + new_status, content)
    
    retest_entry = (
        nl + '### Retest Execution (' + now_date + ')' + nl +
        '- **Tester:** ' + actor + ' (Role: ' + actor_role + ')' + nl +
        '- **Verdict:** ' + verdict.upper() + nl +
        '- **Notes:** ' + notes + nl
    )
    if copied_ev:
        retest_entry += nl + nl.join(copied_ev) + nl
        
    content = content.replace('## Retest' + nl + nl + 'Pending.', '## Retest' + nl + retest_entry)
    if ('## Retest' + nl + nl + 'Pending.') not in content and '## Retest' in content:
        content = re.sub(r'## Retest', '## Retest' + nl + retest_entry, content, count=1)
        
    with open(target_md, 'w', encoding='utf-8') as fp:
        fp.write(content)
        
    print('Successfully updated retest on ' + bug_id + ': Status -> ' + new_status)
    return new_status

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='action')
    
    p_draft = subparsers.add_parser('create-draft')
    p_draft.add_argument('--contributor', required=True, choices=['P01', 'P02', 'P03', 'P04'])
    p_draft.add_argument('--module', required=True)
    p_draft.add_argument('--title', required=True)
    p_draft.add_argument('--desc', required=True)
    p_draft.add_argument('--severity', default='HIGH')
    p_draft.add_argument('--evidence', nargs='*', default=[])
    p_draft.add_argument('--actor', default='')
    p_draft.add_argument('--repo-root', default='.')

    p_retest = subparsers.add_parser('retest')
    p_retest.add_argument('--bug-id', required=True)
    p_retest.add_argument('--verdict', required=True, choices=['PASSED', 'FAILED', 'INCONCLUSIVE', 'VERIFIED'])
    p_retest.add_argument('--actor', required=True)
    p_retest.add_argument('--actor-role', default='HUMAN', choices=['HUMAN', 'AI'])
    p_retest.add_argument('--evidence', nargs='*', default=[])
    p_retest.add_argument('--notes', default='Retest completed.')
    p_retest.add_argument('--repo-root', default='.')

    args = parser.parse_args()
    if args.action == 'create-draft':
        create_draft(args.contributor, args.module, args.title, args.desc, args.severity, args.evidence, args.repo_root, actor=args.actor)
    elif args.action == 'retest':
        submit_retest(args.bug_id, args.verdict, args.actor, args.actor_role, args.evidence, args.notes, args.repo_root)
