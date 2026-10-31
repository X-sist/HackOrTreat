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

    # Run StreamParser unit tests and fixture replays
    test_script = RECEIVER / 'tests' / 'test_stream_parser.mjs'
    print(f'Running receiver tests: {test_script}')
    subprocess.run(['node', str(test_script)], cwd=ROOT, check=True)

    print('PASS: Receiver (CS2) T03 stream parser and fixture tests passed cleanly.')

if __name__ == '__main__':
    main()
