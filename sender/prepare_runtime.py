"""C1-01 online preparation: verify cached wheels and fetch pinned local model.

Run once while online. Never imported by the offline verification path.
"""
import concurrent.futures
import hashlib
import json
import platform
import urllib.request
import zipfile
from email.parser import BytesParser
from pathlib import Path

SENDER = Path(__file__).resolve().parent
REPOSITORY = 'Systran/faster-whisper-tiny.en'
REVISION = '0d3d19a32d3338f10357c0889762bd8d64bbdeba'
FILES = ('config.json', 'model.bin', 'tokenizer.json', 'vocabulary.txt', 'README.md')
MODEL_SHA256 = '1a5afae06a4db91c975c9a9d78be5cc110ee4ea022ad57d55492e4550e936b2a'

def get_json(url):
    with urllib.request.urlopen(url, timeout=60) as response:
        return json.load(response)

def wheel_record(wheel):
    with zipfile.ZipFile(wheel) as archive:
        metadata_name = next(name for name in archive.namelist() if name.endswith('.dist-info/METADATA'))
        metadata = BytesParser().parsebytes(archive.read(metadata_name))
    name, version = metadata['Name'], metadata['Version']
    source = f'https://pypi.org/pypi/{name}/{version}/json'
    published = get_json(source)
    candidates = [item for item in published['urls'] if item['filename'] == wheel.name]
    if len(candidates) != 1:
        raise RuntimeError(f'No unique official artifact for {wheel.name}')
    digest = hashlib.sha256(wheel.read_bytes()).hexdigest()
    if candidates[0]['digests']['sha256'] != digest:
        raise RuntimeError(f'Official package digest mismatch: {wheel.name}')
    license_name = metadata.get('License-Expression') or metadata.get('License')
    if not license_name:
        license_name = '; '.join(value for value in metadata.get_all('Classifier', []) if value.startswith('License ::')) or 'See upstream wheel license files'
    return {'name': name, 'version': version, 'sha256': digest, 'wheel': wheel.name, 'source': source, 'download_url': candidates[0]['url'], 'license_metadata': license_name, 'requires_dist': metadata.get_all('Requires-Dist', [])}

def main():
    if platform.system() != 'Windows' or platform.python_version() != '3.14.4':
        raise SystemExit('This lock targets Windows x64 / CPython 3.14.4; do not silently resolve a different runtime.')
    wheels = sorted((SENDER / 'wheelhouse').glob('*.whl'))
    if not wheels:
        raise SystemExit('Download the declared wheels first; see SETUP.md.')
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        records = sorted(pool.map(wheel_record, wheels), key=lambda item: item['name'].lower())
    selected = {item['name'].lower().replace('_', '-'): item['version'] for item in records}
    if len(selected) != len(records) or any(selected.get(name) != version for name, version in {'faster-whisper': '1.2.1', 'av': '16.0.1', 'pip': '26.2.2', 'sounddevice': '0.5.6', 'pyserial': '3.5'}.items()):
        raise RuntimeError('Wheel cache has duplicate/incorrect direct versions; preserve the declared runtime pins.')
    (SENDER / 'requirements.in').write_text('# Windows x64 / CPython 3.14.4. PyAV pinned: 19 removes metadata_errors used by faster-whisper1.2.1.\nfaster-whisper==1.2.1\nav==16.0.1\npip==26.2.2\nsounddevice==0.5.6\npyserial==3.5\n', encoding='utf-8')
    (SENDER / 'requirements.lock').write_text('# Resolved Windows x64 / CPython 3.14.4 wheels; every artifact verified against official PyPI.\n' + ''.join(f"{item['name']}=={item['version']} --hash=sha256:{item['sha256']}\n" for item in records), encoding='utf-8')
    (SENDER / 'dependencies.json').write_text(json.dumps({'platform': 'win_amd64', 'python': '3.14.4', 'packages': records}, indent=2) + '\n', encoding='utf-8')
    runtime = {'status': 'configured', 'python': '3.14.4', 'platform': 'Windows x64', 'pip': '26.2.2', 'implementation': 'faster-whisper', 'implementation_version': '1.2.1', 'device': 'cpu', 'compute_type': 'int8', 'cpu_threads': 4, 'model_relative_path': 'models/tiny.en', 'microphone_backend': 'sounddevice', 'microphone_backend_version': '0.5.6', 'serial_backend': 'pyserial', 'serial_backend_version': '3.5', 'note': 'Isolated sender/.venv; never install into the receiver or global Python.'}
    (SENDER / 'runtime.json').write_text(json.dumps(runtime, indent=2) + '\n', encoding='utf-8')
    print(f'Verified and locked {len(records)} official wheels', flush=True)
    published_model = get_json(f'https://huggingface.co/api/models/{REPOSITORY}/revision/{REVISION}?blobs=true')
    if published_model['sha'] != REVISION or published_model.get('cardData', {}).get('license') != 'mit':
        raise RuntimeError('Unexpected publisher revision/license metadata')
    published_files = {item['rfilename']: item for item in published_model['siblings']}
    model_dir = SENDER / 'models/tiny.en'
    model_dir.mkdir(parents=True, exist_ok=True)
    artifacts = []
    for name in FILES:
        source = f'https://huggingface.co/{REPOSITORY}/resolve/{REVISION}/{name}'
        target = model_dir / name
        partial = model_dir / (name + '.part')
        if not target.exists():
            with urllib.request.urlopen(source, timeout=120) as response, partial.open('wb') as stream:
                while chunk := response.read(1024 * 1024):
                    stream.write(chunk)
            partial.replace(target)
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        published_file = published_files[name]
        if target.stat().st_size != published_file['size']:
            raise RuntimeError(f'Model file size mismatch: {name}')
        if published_file.get('lfs'):
            if digest != published_file['lfs']['sha256']:
                raise RuntimeError(f'Publisher LFS digest mismatch: {name}')
        else:
            content = target.read_bytes()
            object_digest = hashlib.sha1(f'blob {len(content)}\0'.encode() + content).hexdigest()
            if object_digest != published_file['blobId']:
                raise RuntimeError(f'Publisher Git object mismatch: {name}')
        if name == 'model.bin' and digest != MODEL_SHA256:
            raise RuntimeError('Model binary does not match publisher LFS digest')
        artifacts.append({'id': 'whisper-tiny-en-' + name.replace('.', '-'), 'source': source, 'revision': REVISION, 'license': 'MIT (publisher model-card declaration)', 'sha256': digest, 'local_path': f'models/tiny.en/{name}', 'bytes': target.stat().st_size})
        print(f'Prepared {name}: {target.stat().st_size} bytes', flush=True)
    (SENDER / 'artifacts.json').write_text(json.dumps({'status': 'local-files-prepared', 'model_repository': REPOSITORY, 'revision': REVISION, 'license_source': f'https://huggingface.co/{REPOSITORY}/blob/{REVISION}/README.md', 'artifacts': artifacts}, indent=2) + '\n', encoding='utf-8')

if __name__ == '__main__':
    main()
