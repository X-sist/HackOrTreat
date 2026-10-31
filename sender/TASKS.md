# CS Major 1 tasks — @Aiden360-stack
Only this owner updates these statuses. One task per prompt. Current: **C1-03 implemented; independent Gemini review pending**. C1-02 live offline microphone check and Gemini review remain pending. Stop here; do not auto-advance to C1-04.

| ID | Status | Dependencies | Scope/evidence |
| --- | --- | --- | --- |
| C1-01 | complete; physical Wi-Fi-off rehearsal pending | T01/T02 design | Windows x64 / Python3.14.4, faster-whisper1.2.1, PyAV16.0.1, 25 hash-locked wheels and pinned local tiny.en artifacts prepared. Fresh-process local test phrase transcribed correctly with Python networking blocked. Five sender tests/imports/pip consistency and shared checks passed. See SETUP.md and handoffs/C1-01-20261031.md. No mic CLI/serial implemented. |
| C1-02 | implemented; user live offline microphone check and Gemini review pending | C1-01 | Local Whisper CLI, Enter start/stop, bounded capture, manual/file/device modes, model reuse and useful errors. No mic recording was performed by the agent at the user's request. See CLI.md and handoffs/C1-02-20261031.md for verification and the user's remaining acceptance check. |
| C1-03 | implemented; Gemini review pending | T02 design | Shared-helper Python serial adapter, manual simulator, bounded split reads, handshake/pacing, timeouts/disconnect/reset uncertainty and local-only status. 39 sender tests pass; shared checks pass. pySerial3.5 is hash-locked; no real port/Arduino used. See SERIAL.md and handoffs/C1-03-20261031.md. |
| C1-04 | pending | C1-02/C1-03, CE-compatible Tx | Speech -> CLI -> local Uno; real board acceptance/pacing/recovery evidence. No remote delivery claim. |

Review C1-03 against the shared fixtures without waiting for firmware. C1-04 hardware checks remain pending if CE firmware/boards are unavailable. Cleanup is explicit whitespace normalization; no private compression or silent truncation. T07/T08 are shared milestones, updated by the integration owner only.
