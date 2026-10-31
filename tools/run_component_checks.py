"""Owner-controlled CI hook, so component tests don't require root workflow edits."""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPONENTS = ('firmware', 'sender', 'receiver')

def has_code(folder):
    return any(path.suffix in ('.py', '.js', '.mjs', '.cjs', '.ino', '.cpp', '.h') and not any(part in ('.venv', 'node_modules', '.local', '__pycache__', 'build', 'dist') for part in path.relative_to(folder).parts) for path in folder.rglob('*') if path.is_file())

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('component', choices=COMPONENTS)
    parser.add_argument('--select-python', action='store_true')
    args = parser.parse_args()
    folder = ROOT / args.component
    if args.select_python:
        runtime_path = folder / ('runtime.json' if args.component == 'sender' else 'audio/runtime.json')
        version = json.loads(runtime_path.read_text()).get('python') if runtime_path.exists() else None
        if version is not None and re.fullmatch(r'3\.\d+\.\d+', version) is None:
            raise SystemExit('Invalid pinned Python version')
        with open(os.environ['GITHUB_OUTPUT'], 'a', encoding='utf-8') as stream:
            stream.write('python=' + (version or '3.12') + '\n')
        return
    hook = folder / 'verify.py'
    if not hook.exists():
        if has_code(folder):
            raise SystemExit(f'{args.component}: add owner-local verify.py --ci before merging code')
        print(f'{args.component}: SCAFFOLD ONLY; no implementation or component tests yet')
        return
    subprocess.run([sys.executable, str(hook), '--ci'], cwd=ROOT, check=True)

if __name__ == '__main__':
    main()
