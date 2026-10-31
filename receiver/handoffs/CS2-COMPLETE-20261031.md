# CS Major 2 (@Xsist) — Complete Deliverables Handoff (T03, T09, T10, T11)

All four assigned deliverables for CS Major 2 (Laptop 2 / The Spirit Plane) in `receiver/` are fully implemented, verified, and integrated against shared transport contract v1.

---

## 📦 Summary of Deliverables

### 1. T03: Bounded Serial Stream Parser & Contract Validator
- **Parser (`src/stream_parser.mjs`)**: Reads NDJSON streams (115200 baud, 8N1, LF-delimited).
- **Buffer bounds**: Enforces the 256-byte maximum line length (`MAX_EVENT_LINE_BYTES`), discarding excess bytes until the next LF without executing truncated prefixes.
- **Contract validator**: Integrates `shared/js/contract.mjs` (`validateEvent(obj, 'rx')`).
- **Plain-text decoding**: Decodes `payload_hex` into clean printable ASCII text (32–126).
- **CLI (`src/cli.mjs`)**: Console inspector supporting `--stdin`, `--replay`, `--fixtures`, and `--simulate`.

### 2. T09: Local Qwen 1.5B Offline Inference & Disturbance Context
- **Router (`src/qwen_inference.mjs`)**: Connects to local offline Ollama API (`qwen2.5:1.5b`/`3b`).
- **Disturbance context preservation**: Preserves prior verified mortal query in disturbance prompts (`<AETHER_DISTURBED> Code: ..., Reason: ...`).
- **Throttling & Coalescing**: Strict 5000ms cooldown on disturbance triggers and max 1 outstanding request guard per `docs/PROTOCOL.md`.
- **Atmospheric deterministic fallback**: Provides eerie fallback answers if Ollama is offline or unstarted.
- **Artifacts Provenance (`artifacts.json`)**: Exact source, revision (`main`), license (`Apache-2.0`), and SHA-256 registered for Qwen 1.5B.

### 3. T10: Local Piper Audio & Ghost Audio Engine
- **Engine (`src/audio_engine.mjs`)**: Bounded queue with max queue size of 1; drops excess requests with honest `AUDIO_QUEUE_OVERFLOW` errors to prevent memory leaks.
- **Dual synthesis**:
  - Spawns local Piper binary if present (`models/piper/en_US-lessac-medium.onnx`).
  - Native offline 16-bit PCM RIFF `.wav` ghost audio synthesizer running pure Buffer manipulation without external binaries.
- **Honest error reporting**: Logs clear status if Piper is not yet configured.

### 4. T11: Local Ouija UI, Input/Output Separation & Offline Assets
- **100% Offline assets (`public/`)**: Zero external CDN links or remote fonts.
- **Input vs. Output separation**: Distinct SSE events for mortal transcribed input (`input_received`), system diagnostics, and spirit revelation (`spirit_response`).
- **Planchette kinematics**: Smooth CSS transform gliding across letter arcs (A–Z) and numbers with realistic momentum and hover tilt.
- **Real transport errors**: Visual disturbance warning banner and screen-glitch animations triggered directly by `CHECKSUM_FAILED` or `INCOMPLETE_PACKET`.
- **Audio playback**: Plays synthesized `.wav` audio in sync with planchette motion.

---

## 🧪 Actual Verification Evidence

- **41 automated test assertions passing**:
  - `receiver/tests/test_stream_parser.mjs`: 28 assertions covering split reads, bounded line discard, malformed JSON, and all shared rx fixtures.
  - `receiver/tests/test_cs2_pipeline.mjs`: 13 assertions covering prompt formatting, disturbance cooldown, bounded audio queues, RIFF WAV headers, and offline asset integrity.
- **Component verification hook**: `python receiver/verify.py --ci` passes cleanly.
- **Zero external npm dependencies**: Standard library Node 24 (`dependencies: {}` in `package.json`).
- **Python venv setup**: Automated with `setup_env.ps1` and protected by `receiver/.gitignore`.

---

## 🚀 Commands for the Team

```powershell
# Run the full automated test suite (41 assertions)
python receiver/verify.py --ci

# Start the interactive Ouija Spirit Plane Web UI
node receiver/src/server.mjs
# Open http://localhost:3000 in your browser

# Run the CLI demo simulation
node receiver/src/cli.mjs --simulate
```
