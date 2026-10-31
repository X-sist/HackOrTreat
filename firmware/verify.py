import argparse
import hashlib
import json
import shutil
import subprocess
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / 'firmware' / '.local'


def load_manifest():
    return json.loads((ROOT / 'firmware' / 'dependencies.json').read_text(encoding='utf-8'))


def ensure_cli(manifest):
    version = manifest['arduino_cli']
    binary_dir = LOCAL / 'toolchain'
    binary = binary_dir / 'arduino-cli.exe'
    if binary.exists():
        return binary

    binary_dir.mkdir(parents=True, exist_ok=True)
    archive_path = LOCAL / f'arduino-cli_{version}_Windows_64bit.zip'
    url = f'https://github.com/arduino/arduino-cli/releases/download/v{version}/arduino-cli_{version}_Windows_64bit.zip'
    with urllib.request.urlopen(url, timeout=60) as response, archive_path.open('wb') as archive:
        shutil.copyfileobj(response, archive)
    digest = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    if digest != manifest['arduino_cli_sha256_windows_x64']:
        archive_path.unlink(missing_ok=True)
        raise RuntimeError('Arduino CLI archive SHA-256 mismatch')
    with zipfile.ZipFile(archive_path) as archive:
        archive.extractall(binary_dir)
    archive_path.unlink(missing_ok=True)
    if not binary.exists():
        raise RuntimeError('Arduino CLI archive did not contain arduino-cli.exe')
    return binary


def run(binary, config, arguments):
    subprocess.run([str(binary), '--config-file', str(config), *arguments], cwd=ROOT, check=True)


def prepare_cli(binary):
    config = LOCAL / 'arduino-cli.yaml'
    LOCAL.mkdir(parents=True, exist_ok=True)
    if not config.exists():
        run(binary, config, ['config', 'init', '--dest-file', str(config)])
    for key, path in (
        ('directories.data', LOCAL / 'data'),
        ('directories.downloads', LOCAL / 'downloads'),
        ('directories.user', LOCAL / 'user'),
    ):
        run(binary, config, ['config', 'set', key, str(path)])
    return config


def compile_target(binary, config, manifest, target):
    run(binary, config, ['core', 'update-index'])
    run(binary, config, ['core', 'install', f"arduino:avr@{manifest['avr_core']}"])
    for library in manifest['libraries']:
        run(binary, config, ['lib', 'install', f"{library['name']}@{library['version']}"])
    build_path = LOCAL / 'build' / target
    shutil.rmtree(build_path, ignore_errors=True)
    include_flag = f'compiler.cpp.extra_flags=-I{ROOT.as_posix()}'
    run(binary, config, [
        'compile', '--fqbn', manifest['fqbn'], '--warnings', 'all',
        '--build-path', str(build_path), '--build-property', include_flag,
        str(ROOT / 'firmware' / target),
    ])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ci', action='store_true')
    parser.parse_args()
    manifest = load_manifest()
    if manifest.get('status') != 'configured':
        raise SystemExit('Firmware dependency pins are not configured')
    binary = ensure_cli(manifest)
    config = prepare_cli(binary)
    for target in ('tx', 'rx'):
        compile_target(binary, config, manifest, target)


if __name__ == '__main__':
    main()