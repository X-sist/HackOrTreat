# CS Major 2 workspace — @Xsist

Laptop 2 only: serial input, validated plain text, local Qwen, Piper/effects and local Ouija UI. Import `shared/js/contract.mjs` and `shared/generated/protocol.mjs`; isolated Python audio helpers may use `shared/python`. No sender imports or Arduino firmware edits.

---

## ⚡ Quick Environment Setup

Run the automated setup script from repository root:
```powershell
.\receiver\setup_env.ps1
```
This script:
1. Validates Python 3.14 (or your installed Python 3).
2. Creates the isolated `receiver/.venv` virtual environment (tracked by `receiver/.gitignore`).
3. Confirms your Node.js v24.15.0 and npm v11.12.1 baseline.
4. Executes the 28 unit and fixture assertions in `receiver/tests/test_stream_parser.mjs`.

---

## 🐍 Python Environment Setup (.venv)

To manually set up or activate your Python environment:

```powershell
# 1. Create the virtual environment
python -m venv receiver/.venv

# 2. Activate in PowerShell
.\receiver\.venv\Scripts\Activate.ps1

# 3. Verify component verification hook
python receiver/verify.py --ci

# 4. Run repository integrity checks
python tools/check_repo.py
python tools/validate_protocol_vectors.py
```

All virtual environment artifacts (`.venv/`, `__pycache__/`, audio outputs, and models) are ignored by [`receiver/.gitignore`](.gitignore).

---

## 🟢 Node.js Environment Setup

The receiver component is designed around **Node.js 24.15.0** and standard library modules (`node:http`, `node:fs`, `node:path`, `node:url`). **Zero external npm packages are required to run the parser, test suite, and Ouija web UI.**

### Starting the Applications

```powershell
# 1. Launch the interactive Ouija Spirit Plane Web UI
node receiver/src/server.mjs
# Navigate to: http://localhost:3000

# 2. Run the Plain-Text CLI in simulation mode
node receiver/src/cli.mjs --simulate

# 3. Replay all shared contract v1 fixtures in the CLI
node receiver/src/cli.mjs --fixtures

# 4. Run the StreamParser test suite
node receiver/tests/test_stream_parser.mjs
```

---

## 📋 Hackathon Checklist (Must Download Tonight Before Offline Demo)

Wi-Fi will be disabled during the live judging performance. Ensure all assets and models are cached on Laptop 2:

### 1. Local Offline AI Model (Ollama + Qwen 2.5)
- Install Ollama for Windows: [ollama.com/download](https://ollama.com/download)
- Pull model weights tonight:
  ```powershell
  ollama pull qwen2.5:1.5b
  # Or 3B if RAM permits:
  ollama pull qwen2.5:3b
  ```
- **Verify offline**: Disconnect Wi-Fi and test: `ollama run qwen2.5:1.5b "Spirit, are you there?"`

### 2. Text-to-Speech (Piper TTS) & Ghost Audio FX (for T10)
Inside your activated `receiver/.venv`:
```powershell
pip install piper-tts pedalboard
```
- Download an ONNX voice model (e.g. `en_US-lessac-medium.onnx` + `.json`) to `receiver/models/`.

### 3. Physical Hardware Baseline (Laptop 2 / Spirit Plane)
- Laptop: i5-1334U, 32GB RAM, fully charged.
- Arduino: Uno R3 B (Receiver) with TSOP38238 IR sensor (connected to USB, baud: 115200).
