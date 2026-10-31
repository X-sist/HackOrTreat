"""Owner-local verification hook. --ci installs only the hash-locked runtime."""
import argparse
import json
import os
import platform
import subprocess
import sys
from pathlib import Path

SENDER = Path(__file__).resolve().parent
ROOT = SENDER.parent

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ci', action='store_true')
    args = parser.parse_args()
    runtime = json.loads((SENDER / 'runtime.json').read_text())
    if platform.system() != 'Windows' or platform.python_version() != runtime['python']:
        raise SystemExit(f"Use Windows x64 CPython {runtime['python']}; this is a platform-specific wheel lock.")
    environment = SENDER / '.venv'
    python = environment / 'Scripts/python.exe'
    temp = SENDER / '.local/tmp'
    temp.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, 'TEMP': str(temp), 'TMP': str(temp), 'PIP_DISABLE_PIP_VERSION_CHECK': '1'}
    if args.ci:
        if not python.exists():
            subprocess.run([sys.executable, '-m', 'venv', str(environment)], check=True, env=env)
        subprocess.run([str(python), '-m', 'pip', 'install', '--only-binary=:all:', '--require-hashes', '--index-url', 'https://pypi.org/simple', '-r', str(SENDER / 'requirements.lock')], check=True, env=env)
    runner = str(python) if python.exists() else sys.executable
    subprocess.run([runner, '-m', 'unittest', 'discover', '-s', str(SENDER / 'tests'), '-v'], cwd=ROOT, check=True, env=env)
    if python.exists():
        subprocess.run([runner, '-m', 'pip', 'check'], check=True, env=env)
        subprocess.run([runner, '-c', 'import faster_whisper,ctranslate2,av,sounddevice,serial; print("Whisper/native CPU/microphone/serial imports passed")'], check=True, env=env)
    else:
        raise SystemExit('Unit checks ran, but sender runtime is missing; prepare it before claiming readiness.')
    print('Runtime/unit checks passed. Model/audio check is separate: sender/.venv/Scripts/python.exe sender/offline_check.py')

if __name__ == '__main__':
    main()
