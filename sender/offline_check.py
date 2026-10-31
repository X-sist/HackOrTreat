"""C1-01 fresh-process local-file speech check; no microphone or serial code."""
import argparse
import hashlib
import json
import os
import re
import socket
import time
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

SENDER = Path(__file__).resolve().parent

def verify_model_files(model_dir):
    model_dir = Path(model_dir).resolve()
    if not model_dir.is_dir() or not model_dir.is_relative_to(SENDER):
        raise ValueError('Use an existing sender-local model directory, not a remote model ID.')
    manifest = json.loads((SENDER / 'artifacts.json').read_text(encoding='utf-8'))
    entries = {entry['local_path']: entry for entry in manifest['artifacts']}
    for name in ('config.json', 'model.bin', 'tokenizer.json', 'vocabulary.txt'):
        path = model_dir / name
        relative = path.relative_to(SENDER).as_posix()
        if not path.is_file() or relative not in entries:
            raise ValueError(f'Missing local artifact/provenance: {name}; prepare while online.')
        if hashlib.sha256(path.read_bytes()).hexdigest() != entries[relative]['sha256']:
            raise ValueError(f'Artifact hash mismatch: {name}')
    return model_dir

def deny_network(*args, **kwargs):
    raise OSError('Python network access disabled for offline verification')

def canonical(text):
    return ' '.join(re.findall(r'[a-z0-9]+', text.lower()))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--audio', type=Path, default=SENDER / '.local/samples/demo.wav')
    parser.add_argument('--model', type=Path, default=SENDER / 'models/tiny.en')
    parser.add_argument('--expected', default='Spirit, what is your name?')
    args = parser.parse_args()
    if not args.audio.is_file():
        raise SystemExit('Missing local WAV sample; see SETUP.md. No audio/model will be fetched.')
    model_path = verify_model_files(args.model)
    os.environ.update({'HF_HUB_OFFLINE': '1', 'TRANSFORMERS_OFFLINE': '1', 'HF_HUB_DISABLE_TELEMETRY': '1', 'DO_NOT_TRACK': '1'})
    started = time.perf_counter()
    with ExitStack() as guard:
        for owner, name in ((socket, 'create_connection'), (socket, 'getaddrinfo'), (socket.socket, 'connect'), (socket.socket, 'connect_ex')):
            guard.enter_context(patch.object(owner, name, deny_network))
        # Prove the guard is active without actually reaching any host.
        try:
            socket.create_connection(('example.invalid', 443))
        except OSError as error:
            if 'disabled for offline' not in str(error):
                raise
        else:
            raise RuntimeError('Network guard did not activate')
        from faster_whisper import WhisperModel
        model = WhisperModel(str(model_path), device='cpu', compute_type='int8', cpu_threads=4, local_files_only=True)
        segments, info = model.transcribe(str(args.audio), language='en', beam_size=1, temperature=0, vad_filter=False, condition_on_previous_text=False)
        text = ' '.join(segment.text.strip() for segment in segments).strip()
    passed = canonical(text) == canonical(args.expected)
    result = {'passed': passed, 'transcript': text, 'expected': args.expected, 'elapsed_seconds': round(time.perf_counter() - started, 3), 'language': info.language, 'device': 'cpu', 'compute_type': 'int8', 'fresh_process': True, 'local_files_only': True, 'python_network_guard': True, 'wifi_disabled': False, 'note': 'Software network denial is verified; an actual disconnected-adapter rehearsal remains separate.'}
    output = SENDER / '.local/verification/offline-result.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))
    if not passed:
        raise SystemExit('Transcription did not match the sample; do not claim this check passed.')

if __name__ == '__main__':
    main()
