# C1-01: offline Whisper runtime

C1-02 update: the same sender environment now includes hash-locked sounddevice0.5.6 and its cffi/pycparser dependencies (28 wheels at C1-02). See CLI.md for microphone controls and the pending user-run live offline check. C1-01's model/decoder selection remains unchanged.

C1-03 update: hash-locked pySerial3.5 adds one verified wheel (29 total now), with no changes to prior package pins or model artifacts. See SERIAL.md for the explicit manual simulator and physical-backend evidence limits.

This task prepares file-based transcription only. Microphone CLI is C1-02; serial output is C1-03. Start commands below from the repository root in the sender feature checkout.

## Prepared selection
- Windows x64, **CPython 3.14.4** (already installed on the inventoried laptop).
- **faster-whisper 1.2.1**, CPU INT8, four CPU threads. Exact transitive versions and official wheel hashes are in requirements.lock / dependencies.json. No GPU or separate system FFmpeg install is used by this selection.
- **PyAV 16.0.1** is explicitly pinned: the first real test found PyAV19 incompatible with the metadata_errors argument used by faster-whisper1.2.1. Do not remove this pin based only on dependency resolver success.
- **Systran/faster-whisper-tiny.en**, revision `0d3d19a32d3338f10357c0889762bd8d64bbdeba`. Four required model/tokenizer files plus its model card are stored locally under sender/models/tiny.en (ignored by Git). artifacts.json records source/revision/license declaration/digests. Never pass a remote model name to the offline checker.
- Global Python and the other two components are unchanged. sender/.venv, wheelhouse, models and .local are machine-local and ignored; a Git pull alone does not supply them.

## Use the prepared environment
```powershell
sender/.venv/Scripts/python.exe sender/verify.py
sender/.venv/Scripts/python.exe sender/offline_check.py
```
The first command runs artifact-boundary/version checks, pip dependency consistency and native imports. The second starts a new Python process, checks local model hashes, denies Python socket/DNS operations, loads only local files and transcribes the local WAV. It fails if recognized words differ from the supplied expected text. Its elapsed time includes imports/loading/inference, not just model decoding.

The test WAV is generated locally by an installed Windows voice, not recorded from a microphone:
```powershell
./sender/make_sample.ps1
```
If no US-English SAPI voice is installed, supply a local English WAV and expected phrase:
```powershell
sender/.venv/Scripts/python.exe sender/offline_check.py --audio C:/path/local.wav --expected "The words in that file"
```
No generated test voice is part of the final spirit TTS pipeline. The sample/results remain under ignored sender/.local/. Use an audio path/phrase together; do not treat an arbitrary sample as passing the default phrase.

## Recreate on an identical Windows laptop while online
First verify `python --version` is 3.14.4. Then:
```powershell
python -m venv sender/.venv
sender/.venv/Scripts/python.exe -m pip download --only-binary=:all: --require-hashes -r sender/requirements.lock --dest sender/wheelhouse
sender/.venv/Scripts/python.exe -m pip install --no-index --find-links sender/wheelhouse --only-binary=:all: --require-hashes -r sender/requirements.lock
sender/.venv/Scripts/python.exe sender/prepare_runtime.py
./sender/make_sample.ps1
sender/.venv/Scripts/python.exe sender/verify.py
sender/.venv/Scripts/python.exe sender/offline_check.py
```
prepare_runtime.py is **online preparation**, not demo startup. It verifies cached wheel hashes against official version-specific PyPI metadata and downloads the model only from the pinned revision. Existing model files are checked against publisher size/Git/LFS metadata before recording SHA-256. It refreshes the lock from the wheel cache: keep only this declared dependency set there and review any resulting diff. Do not run it to opportunistically upgrade versions during a demo. The selected direct pins are faster-whisper1.2.1, av16.0.1, pip26.2.2, sounddevice0.5.6 and pyserial3.5; the checked-in lock makes repeat setup deterministic for this platform.

Once the cache exists, environment installation can be repeated with --no-index/--find-links as above. Keep the model directory and wheel cache with the demo machine; no runtime downloads. Native runtime/OS compatibility must still be verified on the second laptop; the lock is intentionally Windows/CPython-specific. Full wheel license metadata and immutable artifact links are recorded in dependencies.json; packages/models are not committed or redistributed by this task.

## Offline evidence boundary
Python networking is denied during the fresh-process speech check; HF offline flags and local_files_only are also enabled. This is evidence of local-file inference without Python network access. Wi-Fi/Ethernet were **not physically disabled** by the agent. Before the demo, disable network connectivity yourself and rerun the same checker from a fresh process. Live microphone behavior remains C1-02, and Arduino/IR behavior remains later tasks.

## CI and references
`python sender/verify.py --ci` creates the sender-only environment if needed, installs the hash-locked wheels and runs non-model checks. CI does not download model/audio artifacts or claim offline demo readiness. Model verification is an explicit local step.

Primary sources: [faster-whisper](https://github.com/SYSTRAN/faster-whisper), [versioned package metadata](https://pypi.org/pypi/faster-whisper/1.2.1/json), [pinned tiny.en source/model card](https://huggingface.co/Systran/faster-whisper-tiny.en/tree/0d3d19a32d3338f10357c0889762bd8d64bbdeba). Package/model declarations are not a blanket license statement for all dependencies; consult the recorded individual wheel notices before redistribution.
