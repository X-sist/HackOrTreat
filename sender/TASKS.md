# CS Major 1 tasks — @Aiden360-stack
Only this owner updates these statuses. One task per prompt. Ready next: **C1-01**.

| ID | Status | Dependencies | Scope/evidence |
| --- | --- | --- | --- |
| C1-01 | pending | T01/T02 design | Select one supported Python + Whisper runtime; pin exact Python/tooling/dependencies and hash-locked transitive requirements; prepare local tiny.en artifact provenance. Verify fresh-process local-sample transcription offline or record the blocker. No microphone CLI or serial yet. |
| C1-02 | pending | C1-01 | Python microphone/transcript CLI, capture controls, manual input and useful errors; real offline mic evidence. |
| C1-03 | pending | T02 design | Serial adapter with shared send builder/event validator, manual text, pacing, split reads, bounds/timeouts and simulated board events. No firmware changes or real IR claim. |
| C1-04 | pending | C1-02/C1-03, CE-compatible Tx | Speech -> CLI -> local Uno; real board acceptance/pacing/recovery evidence. No remote delivery claim. |

Review C1-03 against the shared fixtures without waiting for firmware. C1-04 hardware checks remain pending if CE firmware/boards are unavailable. Cleanup is explicit whitespace normalization; no private compression or silent truncation. T07/T08 are shared milestones, updated by the integration owner only.
