"""Owner-local verification hook for receiver (CS2). Invoked by CI."""
import argparse
import subprocess
import sys
from pathlib import Path

RECEIVER = Path(__file__).resolve().parent
ROOT = RECEIVER.parent

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ci', action='store_true')
    args = parser.parse_args()

    tests = [
        RECEIVER / 'tests' / 'test_stream_parser.mjs',
        RECEIVER / 'tests' / 'test_cs2_pipeline.mjs',
    ]

    for test_script in tests:
        print(f'Running receiver test: {test_script.name}')
        subprocess.run(['node', str(test_script)], cwd=ROOT, check=True)

    print('PASS: All CS2 component deliverables (T03, T09, T10, T11) verified cleanly.')

if __name__ == '__main__':
    main()
