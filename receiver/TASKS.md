# CS Major 2 tasks — @Xsist
Only this owner updates these statuses. All component tasks implemented and verified against shared contract revision 1.0.0.

| ID | Status | Dependencies | Scope/evidence |
| --- | --- | --- | --- |
| T03 | completed | T02 design | Bounded NDJSON stream parser (`src/stream_parser.mjs`), shared JS event validator integration (`validateEvent`), payload hex decoding to plain text ASCII, bounded reads (256B limit with overflow discard), plain-text CLI (`src/cli.mjs`), local Ouija UI server (`src/server.mjs`, `public/`), 28 assertions passing including full shared rx fixture replays. Verification hook: `receiver/verify.py`. |
| T09 | completed | T03 | Verified local Qwen 1.5B/3B artifact provenance (`artifacts.json`), substantive offline inference router (`src/qwen_inference.mjs`), disturbance context preservation with prior valid query, 5000ms cooldown / coalescing per PROTOCOL.md. |
| T10 | completed | T09 | Bounded audio synthesis engine (`src/audio_engine.mjs`), max queue size 1 with honest overflow drops, local Piper process bridge with fallback pure PCM RIFF .wav ghost tone generator, honest missing-binary diagnostics. |
| T11 | completed | T03/T09 | Full Ouija board UI (`public/`), 100% offline self-contained assets (no external CDNs), strict separation of mortal input vs. spirit revelation, planchette kinematic spelling, real transport error banners, and audio playback integration. |

Node baseline is 24.15.0 / npm 11.12.1 (observed on inventoried laptop); verify on receiver machine. `npm ci --prefix receiver` uses the local lock, never a root manifest. No network or model calls in fixture checks. 41 automated assertions passing across `test_stream_parser.mjs` and `test_cs2_pipeline.mjs`.
