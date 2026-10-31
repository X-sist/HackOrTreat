# CS Major 2 workspace — @Xsist

Laptop 2 only: serial input, validated plain text, local Qwen, Piper/effects and local Ouija UI. Import shared/js/contract.mjs and shared/generated/protocol.mjs; isolated Python audio helpers may use shared/python. No sender imports or Arduino firmware edits.

## Implemented Deliverables

### T03: Bounded Stream Parser, Shared Contract Validator & Ouija Display
- **Bounded Stream Parser (`src/stream_parser.mjs`)**: NDJSON line accumulator with 256-byte maximum line limits, line discarding on overflow, ASCII hex decoding, and shared contract event validation (`validateEvent` with role `rx`).
- **Plain-Text CLI (`src/cli.mjs`)**: Console inspector supporting `--stdin`, `--replay <file>`, `--fixtures`, and `--simulate`.
- **Ouija Spirit Plane UI & Server (`src/server.mjs`, `public/`)**: Zero-dependency local web server (Node 24 native HTTP + SSE) providing real-time Ouija board animations, letter-by-letter planchette spelling, and disturbance alert glitching.
- **Verification Hook (`verify.py`)**: Runs `node receiver/tests/test_stream_parser.mjs` (28 assertions passing).

## Commands

Run from repository root:

```powershell
# Run receiver unit tests and fixture replays
node receiver/tests/test_stream_parser.mjs

# Run component verification hook
python receiver/verify.py --ci

# Run CLI simulation
node receiver/src/cli.mjs --simulate

# Run Ouija Spirit Plane Web UI
node receiver/src/server.mjs
# Open http://localhost:3000 in your browser

# Run repo integrity checks
python tools/check_repo.py
python tools/validate_protocol_vectors.py
python tools/check_repo.py --role receiver --base origin/main
```

See [handoffs/T03-20261031.md](handoffs/T03-20261031.md) for full T03 implementation evidence.
