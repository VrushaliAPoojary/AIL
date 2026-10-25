#!/usr/bin/env python3
import os
import re
import argparse
from urllib.parse import quote

def compile_master_ledger(bugs_root: str, output_path: str):
    bug_records = []
    
    for feature in sorted(os.listdir(bugs_root)):
        fpath = os.path.join(bugs_root, feature)
        if not os.path.isdir(fpath):
            continue
        for folder in sorted(os.listdir(fpath)):
            folder_path = os.path.join(fpath, folder)
            if not os.path.isdir(folder_path):
                continue
            
            md_files = [fn for fn in os.listdir(folder_path) if fn.endswith('.md')]
            if not md_files:
                continue
            md_path = os.path.join(folder_path, md_files[0])
            
            with open(md_path, 'r', encoding='utf-8', errors='ignore') as fp:
                c = fp.read()
                
            title_m = re.search(r'^#\s+(?:ART-[A-Z]+-\d+|DRAFT-[A-Z0-9\-]+)\s+—\s+(.+)$', c, re.MULTILINE)
            title = title_m.group(1).strip() if title_m else folder.split('__')[-1].replace('-', ' ').title()
            
            sev_m = re.search(r'-\s+\*\*Severity:\*\*\s*([A-Za-z0-9]+)', c)
            severity = sev_m.group(1).strip().upper() if sev_m else 'MEDIUM'
            
            stat_m = re.search(r'-\s+\*\*Status:\*\*\s*([A-Za-z0-9]+)', c)
            status = stat_m.group(1).strip().upper() if stat_m else 'OPEN'
            
            dev_idx = c.find('## Developer Update')
            dev_str = 'Pending.'
            if dev_idx != -1:
                after_dev = c[dev_idx + len('## Developer Update'):].strip()
                next_sec = after_dev.find('## ')
                sec_text = after_dev[:next_sec].strip() if next_sec != -1 else after_dev.strip()
                if sec_text:
                    dev_str = sec_text.splitlines()[0].strip()
            if len(dev_str) > 60: dev_str = dev_str[:57] + '...'
            if not dev_str: dev_str = 'Pending.'
            
            ret_idx = c.find('## Retest')
            ret_str = 'Pending.'
            if ret_idx != -1:
                after_ret = c[ret_idx + len('## Retest'):].strip()
                next_sec = after_ret.find('## ')
                sec_text = after_ret[:next_sec].strip() if next_sec != -1 else after_ret.strip()
                if sec_text:
                    ret_str = sec_text.splitlines()[0].strip()
            if len(ret_str) > 60: ret_str = ret_str[:57] + '...'
            if not ret_str: ret_str = 'Pending.'
            
            bug_id = md_files[0].replace('.md', '')
            rel_feature = quote(feature)
            rel_path = f'bugs/{rel_feature}/{folder}/{md_files[0]}'
            
            bug_records.append({
                'id': bug_id,
                'feature': feature,
                'title': title,
                'severity': severity,
                'status': status,
                'dev_update': dev_str,
                'retest': ret_str,
                'rel_path': rel_path
            })

    bug_records.sort(key=lambda x: x['id'])
    
    total = len(bug_records)
    open_cnt = sum(1 for b in bug_records if b['status'] == 'OPEN')
    fixing_cnt = sum(1 for b in bug_records if b['status'] == 'FIXING')
    retest_cnt = sum(1 for b in bug_records if b['status'] == 'RETEST')
    verified_cnt = sum(1 for b in bug_records if b['status'] == 'VERIFIED')
    closed_cnt = sum(1 for b in bug_records if b['status'] == 'CLOSED')
    blocked_cnt = sum(1 for b in bug_records if b['status'] == 'BLOCKED')

    lines = [
        '# ART Product Validation Ledger',
        '',
        '## Summary',
        '',
        f'- **Total Bugs:** {total}',
        f'- **Open:** {open_cnt}',
        f'- **Fixing:** {fixing_cnt}',
        f'- **Retest:** {retest_cnt}',
        f'- **Verified:** {verified_cnt}',
        f'- **Closed:** {closed_cnt}',
        f'- **Blocked:** {blocked_cnt}',
        '',
        '## Bugs',
        '',
        '| Bug ID | Title | Severity | Status | Developer Update | Retest |',
        '| --- | --- | --- | --- | --- | --- |'
    ]

    for b in bug_records:
        link_str = f'[{b["id"]}]({b["rel_path"]})'
        lines.append(f'| {link_str} | {b["title"]} | {b["severity"]} | {b["status"]} | {b["dev_update"]} | {b["retest"]} |')

    lines.append('')
    content = "\n".join(lines) + "\n"
    
    with open(output_path, 'w', encoding='utf-8') as fp:
        fp.write(content)
        
    print(f'Successfully compiled master ledger: {output_path} ({total} bugs)')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--bugs-root', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    compile_master_ledger(args.bugs_root, args.output)
