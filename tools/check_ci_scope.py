"""Check actual PR file scope and supplied role/author mapping without a shell."""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.check_repo import check_scope

def main():
    event_name = os.environ['GITHUB_EVENT_NAME']
    if event_name == 'merge_group':
        print('Merge queue: component scope was checked on each PR; compatibility runs on the combined tree')
        return
    if event_name != 'pull_request':
        print('Ownership applies to PRs; compatibility still runs')
        return
    event = json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text())
    pr = event['pull_request']
    role = pr['head']['ref'].split('/', 1)[0]
    author = pr['user']['login'].lower()
    owners = json.loads((ROOT / 'shared/team.json').read_text())
    if role == 'integration':
        if author not in {entry['github'].lower() for entry in owners.values()}:
            raise SystemExit('Integration PR author is not in supplied team mapping')
    elif role not in owners or author != owners[role]['github'].lower():
        raise SystemExit('Use the matching firmware/, sender/, receiver/ branch and supplied owner account, or a coordinated integration/ PR')
    base, head = pr['base']['sha'], pr['head']['sha']
    if not all(re.fullmatch('[0-9a-fA-F]{40}', sha) for sha in (base, head)):
        raise SystemExit('Invalid commit ID')
    raw = subprocess.check_output(['git', 'diff', '--name-only', '-z', '--no-renames', f'{base}...{head}'], cwd=ROOT)
    paths = [path for path in raw.decode().split('\0') if path]
    check_scope(role, paths)
    print(f'PASS: {role} scope and author mapping; {len(paths)} changed files')

if __name__ == '__main__':
    main()
