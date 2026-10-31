# Historical roadmap — superseded

Do not use this as the task queue. See component TASKS.md files and root TASKS.md.

# Small-task roadmap

Statuses below reflect recorded task evidence. Update a status only with evidence from the repository or actual verification. Do one task per request, then stop with results, unresolved items, and a suggested next task. Do not install models, implement firmware, and build UI in one prompt. Split a task further if it becomes too broad. Completion of mocks does not mean hardware or offline acceptance passed.

## Active track: CS Major 1
Follow CS1-SENDER.md and the original three-person majors table. Default "next task" uses this table only. One request completes one selected task, then stops. The shared roadmap below preserves other teammates' work; it is not this user's automatic execution queue.

| ID | Status | Depends on | Bounded task |
| --- | --- | --- | --- |
| C1-01 | pending | T01, T02 | Select/prepare one offline Whisper runtime and supported Python environment, record local tiny.en artifacts/versions/licenses, and verify a local sample from a fresh process offline or state the exact blocker. No CLI, serial, receiver, or UI yet. |
| C1-02 | pending | C1-01 | Implement and verify the microphone/transcript Python CLI with manual input and useful errors. No serial yet. |
| C1-03 | pending | T02 | Implement manual text cleanup/bounds and the Python serial adapter against agreed protocol fixtures/simulated board responses. Check pacing, framing, timeouts, disconnects, and clear status; no firmware or real IR claims. |
| C1-04 | pending | C1-02, C1-03 | Connect speech/CLI/serial and verify on the real transmitting Arduino after CE confirms firmware compatibility. Record unavailable board tests as pending. Stop at the sender-board boundary; shared reception is a team test. |

Immediate next task: **C1-01**. T07 aggregates C1-01/C1-02 evidence; do not auto-complete T07/T08 from fixture-only sender work. Keep UI optional until the CLI team MVP is integrated. No sender task requires U01/U02/U03, receiver implementation, Qwen, or TTS.

## Shared team roadmap
Ownership: CE = T04/T05; CS Major 1 = C1 tasks/T07 and sender portion of T06/T08; CS Major 2 = T03/T09/T10/T11; T06/T08/T12/T13 are coordinated integration milestones. U01/U02/U03 are deferred enhancements, selected only explicitly. Keep shared task IDs and prior evidence intact.

| ID | Status | Depends on | Bounded task and completion evidence |
| --- | --- | --- | --- |
| T01 | complete (unknowns recorded) | â€” | Inventory actual hardware, OS, installed tools/models, and supplied official hackathon rules. Save confirmed facts, unknowns, sources, and blockers. Do not install dependencies or claim award eligibility without rules. Unknown facts may remain explicitly unresolved. |
| T02 | complete (design; hardware unverified) | T01 | Specify one-way IR packet and serial event contracts. Include example valid, checksum-failure, partial-timeout, duplicate, and oversized cases. Decide whether idle heartbeat detection is required; record event semantics and limits. No firmware or full app yet. |
| U01 | pending | T01, T02 | Define sender/receiver screen sketches, actions/states, local UI/service event and command contracts, mock/live boundary, target OS, desktop framework decision, and service lifecycle/packaging plan. Electron is provisional. Design/contracts only; no full app. |
| U02 | pending | U01 | Implement minimal desktop shell with sender/receiver mode selection, transcript editing/manual send, plain-text receiver, connection/errors, and collapsible diagnostics using visible mock mode. Render both screens and verify interactions. No real hardware, model, audio, or decorative art. |
| T03 | pending | T02 | CS Major 2: build the receiver event parser and a plain-text CLI/local display using fixture/mock serial input; shared desktop shell is optional later. Check split reads, multiple lines, malformed/oversized records, and distinct disturbance states. No LLM, audio, or art. |
| T04 | pending | T02 | Implement Arduino A sender firmware and local serial pacing/status on the confirmed board/parts. Send a fixed text frame. Record compile evidence and any physical tests; mark unavailable hardware checks blocked. |
| T05 | pending | T02, T04 | Implement Arduino B receive/validate firmware. Demonstrate fixed text over real IR and recovery after an interrupted frame. Distinguish real checksum failure, incomplete timeout, and silence. Hardware evidence required for completion. |
| T06 | pending | T03, T04, T05 | Connect manual text entry on Laptop 1 through USB/IR to the plain-text display on Laptop 2. Check ordering, pacing, bounds, and recovery. No speech or model yet. Record real two-machine evidence. |
| T07 | pending | C1-01, C1-02 | CS Major 1 aggregate milestone: offline STT and Python CLI transcript display, established through C1-01/C1-02 evidence. Verify local artifacts and fresh-process transcription with Wi-Fi disabled. No IR integration in this task. |
| T08 | pending | T06, T07 | Connect bounded STT output to the sender. Demonstrate speech-to-text-to-IR-to-received-text offline. This is the minimum demo milestone. |
| T09 | pending | T03, T01 | Required for the award-targeted demo: follow SOFTWARE-REQUIREMENTS.md, verify the exact preferred Qwen2.5-1.5B-Instruct artifact, revision/digest, license notices, and runtime identifier; add local Ollama/Qwen adapter using validated text or explicit disturbance fixtures. Keep raw received text visible and model output separate. Test local startup, timeouts, unavailable model, short responses, and provenance. No audio/UI animation. |
| T10 | pending | T09 | Add offline Piper speech playback with a bounded single-response queue and graceful errors. Verify voice files/license and intelligibility; add distortion only if reliable playback remains intact. |
| T11 | pending | T03, T09 | Add locally bundled Ouija board and planchette animation driven by response text. Test spaces, punctuation, cancellation, repeat responses, and readable transport errors. No CDN assets. |
| T12 | pending | T08, T09, T10, T11 | Integrate the theatrical receiver flow. Begin animation during speech generation, avoid overlapping voices, and keep transport/error text honest. Exercise valid and disturbed physical transmissions. |
| U03 | pending | T12 | Package the desktop app for both demo machines with sender/receiver setup instructions. Verify launch without a development server, local artifact discovery, microphone/serial access, missing-dependency feedback, and clean service shutdown. Record bundled versus preinstalled dependencies; no online installer at demo time. |
| T13 | pending | T12 | Run the team CLI/service-based demo (or explicitly selected packaged desktop variant) on both machines offline from fresh processes, including a judge breaking the beam during a frame. Verify mock mode is off. Record commands, versions, licenses, timings, failures, and readiness against verified rules. Document remaining blockers instead of claiming a pass. |

Parallel candidates after T02: host parser (T03), sender firmware (T04), and STT (T07) can proceed under distinct human owners. Model adapter T09 can use parser fixtures after T03. Software agents still follow MULTI-AGENT.md and require authorization before delegation. Keep shared protocol/config changes under one coordinator; integration tasks wait for their dependencies.

Priority correction: the majors table governs immediate work. T06/T08 integrate the sender Python CLI with CE firmware and the receiver service. Desktop shell tasks are deferred and are not default next tasks. T13 may rehearse the CLI/service-based team MVP with a locally bundled receiver visual interface; U03 is only a prerequisite when rehearsing a packaged desktop variant. Existing T02 remains a shared proposal; agree on compatibility before physical integration.

Suggested prompts:
- "Do T01 only for HackOrTreat. Record confirmed facts and unknowns; do not install anything or build the app."
- "Do the next ready task only. Follow PROJECT-BRIEF.md and TASKS.md, verify the result, update evidence, and stop."
- "Review the implementation of T02 only against the project brief; return actionable findings without editing code."

The roadmap is intentionally more granular than the three human roles in the blueprint. Each task is a prompt boundary, not a promise that it takes a fixed number of minutes. When the user selects a task with unmet dependencies, explain the concrete missing contract or evidence and complete only independent work inside that task if useful.

T01 evidence: [inventory and blockers](docs/ai/tasks/T01-20261031-inventory/inventory.md), collected October 31, 2026. Updated with user-confirmed Uno R3/V1221/V1222 identities, identical demo-laptop report, and verified public category sources in SOFTWARE-REQUIREMENTS.md. Runtime/physical readiness, second-machine environment, and remaining organizer policies are unverified.

T02 evidence: [transport contract](docs/PROTOCOL.md), [conformance vectors](docs/protocol-vectors.json), and [handoff](docs/ai/tasks/T02-20261031-protocol/handoff.md). Fixture consistency checked; independent review pending; hardware timing/library/memory validation deferred to T04/T05. Heartbeats disabled in v1. No other task advanced.
