"""Offline collaboration checks; no dependency installation or model/hardware use."""
import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.generate_contract import outputs
from shared.python.contract import validate_event

COMPONENTS = ('firmware', 'sender', 'receiver')

def require(ok, message):
    if not ok:
        raise ValueError(message)

def allowed_path(role, path):
    parts = PurePosixPath(path).parts
    if not parts or '..' in parts or PurePosixPath(path).is_absolute():
        return False
    if role == 'integration':
        return True
    # Consumer pins are shared integration-owned, even inside component folders.
    return role in COMPONENTS and parts[0] == role and path != f'{role}/contract.lock.json'

def check_scope(role, paths):
    forbidden = [path for path in paths if not allowed_path(role, path)]
    require(not forbidden, f'{role} PR crosses ownership boundaries: {forbidden}; split it or coordinate an integration PR')

def logical_requirements(text):
    lines = []
    pending = ''
    for raw in text.splitlines():
        line = raw.split('#', 1)[0].strip()
        if not line:
            continue
        pending += line.rstrip('\\').strip() + ' '
        if not line.endswith('\\'):
            lines.append(pending.strip())
            pending = ''
    require(not pending, 'unterminated requirement continuation')
    return lines

def requirement_pins(text, hashed=False):
    pins = {}
    for line in logical_requirements(text):
        match = re.fullmatch(r'([A-Za-z0-9_.-]+)(?:\[[A-Za-z0-9_,.-]+\])?==(\d+(?:\.\d+)*(?:(?:a|b|rc)\d+|\.post\d+|\.dev\d+)?(?:\+[A-Za-z0-9.]+)?)((?:\s+--hash=sha256:[0-9a-fA-F]{64})*)', line)
        require(match is not None, f'Unpinned/unsupported requirement: {line}')
        name, version, hashes = match.groups()
        key = re.sub(r'[-_.]+', '-', name).lower()
        require(key not in pins, f'duplicate dependency {key}')
        require(not hashed or bool(hashes), f'missing SHA-256 for {name}')
        pins[key] = version
    return pins

def check_python_environment(folder):
    direct = folder / 'requirements.in'
    if not direct.exists():
        return
    lock = folder / 'requirements.lock'
    require(lock.exists(), f'{folder}: missing requirements.lock')
    declared = requirement_pins(direct.read_text())
    resolved = requirement_pins(lock.read_text(), hashed=True)
    require(all(resolved.get(name) == version for name, version in declared.items()), f'{folder}: manifest/lock mismatch')
    runtime = json.loads((folder / 'runtime.json').read_text())
    source = any(folder.rglob('*.py'))
    if declared or resolved or source:
        require(runtime.get('status') == 'configured' and re.fullmatch(r'3\.\d+\.\d+', str(runtime.get('python'))), f'{folder}: pin/test exact Python runtime before adding code or dependencies')

def check_node_environment(folder):
    manifest = folder / 'package.json'
    if not manifest.exists():
        return
    package = json.loads(manifest.read_text())
    dependencies = {**package.get('dependencies', {}), **package.get('devDependencies', {})}
    exact = r'\d+\.\d+\.\d+(?:-[A-Za-z0-9.-]+)?'
    require(re.fullmatch(exact, package['engines']['node']) is not None, 'pin exact Node version')
    require(re.fullmatch(r'npm@\d+\.\d+\.\d+', package['packageManager']) is not None, 'pin npm version')
    for name, version in dependencies.items():
        require(re.fullmatch(exact, version) is not None, f'{name}: use exact version, not {version}')
    lock = json.loads((folder / 'package-lock.json').read_text())
    root = lock['packages']['']
    require(root.get('dependencies', {}) == package.get('dependencies', {}) and root.get('devDependencies', {}) == package.get('devDependencies', {}), 'npm manifest/lock mismatch')
    for path, entry in lock['packages'].items():
        if path:
            require(entry.get('version') and entry.get('integrity') and not entry.get('link'), f'unlocked npm package {path}')

def check_artifacts(folder):
    data = json.loads((folder / 'artifacts.json').read_text())
    seen = set()
    for item in data['artifacts']:
        require(item['id'] not in seen, 'duplicate artifact ID')
        seen.add(item['id'])
        require(all(item.get(key) for key in ('source', 'revision', 'license', 'sha256', 'local_path')), 'incomplete artifact provenance')
        require(re.fullmatch(r'[0-9a-f]{64}', item['sha256']) is not None, 'invalid artifact SHA-256')
        relative = PurePosixPath(item['local_path'])
        require(not relative.is_absolute() and '..' not in relative.parts and str(relative).startswith(('.local/', 'models/')), 'artifacts belong in ignored component-local storage')
        actual = folder / str(relative)
        if actual.is_file():
            require(hashlib.sha256(actual.read_bytes()).hexdigest() == item['sha256'], f'artifact digest mismatch: {actual}')
        # Missing large artifacts are expected in CI; never call this offline readiness.

def check_repo(root=ROOT):
    for name, expected in outputs(root).items():
        path = root / name
        require(path.exists() and path.read_text(encoding='utf-8') == expected, f'stale shared output or consumer pin: {name}')
    c = json.loads((root / 'shared/contract.json').read_text())['constants']
    owners = json.loads((root / 'shared/team.json').read_text())
    handles = [owners[role]['github'] for role in ('sender', 'receiver', 'firmware')]
    require(all(re.fullmatch(r'[A-Za-z0-9-]+', handle) for handle in handles), 'invalid GitHub handle syntax')
    all_handles = ' '.join('@' + handle for handle in handles)
    expected_ownership = [f'* {all_handles}'] + [f'/{role}/ @{owners[role]["github"]}' for role in ('sender', 'receiver', 'firmware')] + [f'/{role}/contract.lock.json {all_handles}' for role in ('sender', 'receiver', 'firmware')]
    actual_ownership = [line.strip() for line in (root / '.github/CODEOWNERS').read_text().splitlines() if line.strip() and not line.lstrip().startswith('#')]
    require(actual_ownership == expected_ownership, 'CODEOWNERS/team mapping drift')
    require(c['MAX_PACKET_BYTES'] == c['MAX_TEXT_BYTES'] + c['PACKET_OVERHEAD_BYTES'], 'packet size relationship')
    require(c['PACKET_GUARD_MS'] > c['INTER_SYMBOL_TIMEOUT_MS'], 'guard must exceed receive gap timeout')
    fixtures = json.loads((root / 'shared/fixtures/events.json').read_text())
    for case in fixtures:
        try:
            validate_event(case['value'], case['role'])
            accepted = True
        except (ValueError, TypeError):
            accepted = False
        require(accepted == case['valid'], f'event fixture disagreement: {case["id"]}')
    # Validate all T02 expected events using the same vocabulary as all consumers.
    vectors = json.loads((root / 'docs/protocol-vectors.json').read_text())
    require(vectors['contract_version'] == c['PROTOCOL_VERSION'] and vectors['max_text_bytes'] == c['MAX_TEXT_BYTES'], 'T02 fixture/contract drift')
    for case in vectors['packet_cases']:
        for event in case['expected_events']:
            validate_event(event, 'rx')
    for component in COMPONENTS:
        folder = root / component
        require((folder / 'AGENTS.md').exists() and (folder / 'TASKS.md').exists(), f'missing component entrypoint: {component}')
        check_artifacts(folder)
    check_python_environment(root / 'sender')
    check_python_environment(root / 'receiver/audio')
    check_node_environment(root / 'receiver')
    firmware = json.loads((root / 'firmware/dependencies.json').read_text())
    if any((root / 'firmware').rglob('*.ino')):
        require(firmware.get('status') == 'configured', 'pin firmware tooling/core/libraries before adding sketches')
        require(firmware.get('fqbn') == 'arduino:avr:uno' and all(re.fullmatch(r'\d+\.\d+\.\d+', str(firmware.get(key))) for key in ('arduino_cli', 'avr_core')), 'missing exact Uno build/toolchain pins')
        require(bool(firmware.get('libraries')), 'record exact firmware libraries')
        for library in firmware['libraries']:
            require(library.get('name') and re.fullmatch(r'\d+\.\d+\.\d+', library.get('version', '')), 'pin firmware library versions')
    for filename in ('package.json', 'package-lock.json', 'requirements.txt', 'requirements.in', 'requirements.lock', 'pyproject.toml', 'uv.lock'):
        require(not (root / filename).exists(), f'root dependency manifest forbidden: {filename}; use owner folder')
    for component in COMPONENTS:
        for path in (root / component).rglob('*'):
            if any(part in ('.venv', 'node_modules', '.local', '__pycache__') for part in path.parts):
                continue
            if path.suffix in ('.py', '.js', '.mjs', '.cjs', '.ino', '.cpp', '.h') and path.is_file():
                text = path.read_text(encoding='utf-8')
                for other in set(COMPONENTS) - {component}:
                    require(re.search(rf'(?:from\s+{other}(?:\.|\s)|(?:\.\./)+{other}/)', text) is None, f'cross-component source import: {path}')
    print('PASS: shared contract pins, event fixtures, ownership layout, dependency declarations and artifact metadata. App/hardware readiness not established.')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--role', choices=(*COMPONENTS, 'integration'))
    parser.add_argument('--base')
    parser.add_argument('--head', default='HEAD')
    args = parser.parse_args()
    if args.base:
        require(args.role is not None, '--base needs --role')
        # --no-renames checks both old and new locations of moved files.
        raw = subprocess.check_output(['git', 'diff', '--name-only', '-z', '--no-renames', f'{args.base}...{args.head}'], cwd=ROOT)
        paths = [path for path in raw.decode('utf-8').split('\0') if path]
        check_scope(args.role, paths)
        print(f'PASS: {args.role} scope for {len(paths)} changed files')
    check_repo()

if __name__ == '__main__':
    main()
