# HackOrTreat project brief

## Goal and success
Target the hackathon's open-weight award with a theatrical, fully offline voice-to-IR spirit communication demo. Award name, eligibility, permitted preparation, model requirements, and judging criteria are not yet verified: obtain official rules before making compliance claims. The supplied blueprint is the design source, not evidence that components have been installed or tested. The six-hour sprint is a planning constraint, not a verified delivery estimate.

Minimum demonstrable system: speak into Laptop 1, show the offline transcription, transmit its text over a real one-way IR link, and display decoded plain text on Laptop 2. This hardware path is the first priority. Local AI response, distorted speech, planchette animation, and ambiance enhance the demo after that path works.

## Desktop product
The final deliverable is a desktop app with a shared codebase and two selectable modes, one per laptop. A command-line-only demo is not the product target.

## Desktop UI and backend development
- Living Plane: microphone controls/state, transcript display/editing, manual text input, serial port selection/connection state, send action, and local busy/error feedback. Do not claim remote delivery acknowledgement.
- Spirit Plane: received plain text separate from generated response, connection and transport/error states, later Ouija board/planchette, and audio controls.
- Build the minimal shell early against explicit local event/command contracts and visibly labeled mock adapters. Replace mocks incrementally with serial, speech, model, and audio services. Basic UI and backend develop together; decorative polish follows working real IR.
- Include a collapsible diagnostic panel for events/timing and a readable presentation view for judges. Final rehearsal must use real inputs, not mocks.
- Keep UI separate from hardware/process adapters. Cover disconnected, busy, cancelled, unavailable-model, and failed states. UI does not directly execute arbitrary commands or access serial/files; validate the service boundary.
- Electron is provisional, not selected or installed. U01 confirms target OS, shell, UI/service boundary, local Python/audio/model process startup/shutdown, and packaging approach.
- Packaging is an explicit task: document bundled versus preinstalled dependencies and local artifact paths; verify microphone/serial access, missing-artifact errors, and launch without a development server or internet on each laptop.

## Hardware constraints
- Two laptops, proposed specification i5-1334U and 32 GB RAM each. Confirm actual machines and operating systems.
- Two Arduino boards connected by USB data cables, one board per laptop. Board models and pins are still unconfirmed.
- Exactly one IR transmitter and one IR receiver total. Arduino A transmits; Arduino B receives. No bidirectional link, receiver acknowledgements, or remote retransmission requests.
- Proposed receiver: TSOP38238 or equivalent, and a transmitter using a 38 kHz carrier. Confirm actual parts, wiring, voltage/current requirements, modulation support, and library compatibility before firmware implementation.
- No inter-laptop network, cloud inference, or internet at runtime. Localhost services and USB to each local Arduino are allowed. Do not use shared storage or another hidden channel to carry the prompt between laptops.

## Target performance for judges
Establish that Wi-Fi is disabled on both laptops and no other inter-laptop data path is active. On Laptop 1, say: "Spirit, what is your name?" Show the transcription and a transmit indicator while Arduino A sends IR across the table. IR is invisible; the screen or a separate status LED may indicate transmission, but do not describe the IR LED itself as visibly flashing.

A judge interrupts the beam during a transmission. Laptop 2 shows an appropriate transport event; the desired dramatic label for a confirmed checksum mismatch is `CHECKSUM_FAILED: AETHER DISTURBED`. Local Qwen interprets the structured disturbance event and produces a short spirit response. Example tone: "The living disrupt us. I am... trapped." This is an example, not a guaranteed model output. An offline voice plays with distortion while a digital planchette spells the response across a rusted Ouija board. Start animation while audio is generating to reduce perceived delay. Exact latency, synchronization, and legibility must be measured on the demo machines.

## System boundary and proposed components
1. Laptop 1: local Whisper speech-to-text, transcript display, bounded text encoding, USB serial output.
2. Arduino A: newline-delimited host input, bounded packet framing and checksum, carrier-modulated IR output, local ready/busy status over USB.
3. Arduino B: decode and validate IR, classify errors/timeouts, emit bounded structured newline-delimited serial events.
4. Laptop 2: display received text and transport state first; later consume local Qwen responses and drive local audio/UI.

Proposed starting stack from the supplied blueprint:
- STT: faster-whisper or whisper.cpp with tiny.en model files. Choose one in a small task after checking installation and offline startup.
- LLM: Ollama with locally downloaded Qwen 2.5 1.5B or 3B, Q4_K_M quantization where supported. Benchmark on the receiving laptop before choosing. Record the exact model artifact, license, source, and local identifier rather than assuming a tag names a particular quantization.
- Speech output: Piper with a local ONNX voice and its required configuration; optional Pedalboard effects. Verify voice and software licenses separately. Keep intelligibility and playback reliability ahead of heavy effects.
- Desktop integration/UI: shared sender/receiver shell with local HTML/CSS/JS; proposed Node.js/serialport adapters and local Python speech worker. A Python sender CLI is a development aid only. Confirm framework and service lifecycle in U01; pin actual dependencies once selected.
- Firmware: proposed Arduino IDE/toolchain and IRremote. Verify feasible packet encoding, timing, and payload limits on the actual boards rather than assuming arbitrary strings are supported directly.
- Assets: locally stored board background, transparent planchette, ambient drone, fonts, and all associated license/source records. No CDN or streamed media.

These are proposed choices, not permission to install every alternative or replace existing working components. No app implementation or hardware validation existed when this brief was introduced.

## Transport correctness and disturbance behavior
- Specify protocol before building either host or firmware implementation: version, sequence ID, encoding, length, delimiters/escaping, checksum algorithm/coverage, limits, timeout behavior, and serial event schema.
- Serial speed and IR throughput differ. Proposed serial speed is 115200 baud, configurable and identical within each host/board pair. Buffer newline-delimited input with strict maximum sizes; partial or multiple serial reads must parse correctly. Sender pacing uses local Arduino ready/busy notifications, not a remote acknowledgement.
- On checksum mismatch, discard the payload as untrusted. Emit a structured checksum-failure event. Do not ask Qwen to repair bytes and present the result as a faithful transmission.
- On a started but incomplete frame, emit an incomplete-packet timeout after a defined interval. Keep that event distinct from checksum mismatch.
- If the entire transmission is lost, the receiver cannot know that a message was sent from silence alone. If idle beam-loss detection is required, define periodic one-way heartbeat frames and a missed-heartbeat window. This is an optional protocol extension; until then, no disturbance event is promised for a completely missed frame.
- LLM input contains validated text, explicit transport status, and optionally the last valid message labeled as prior context. Disturbance may trigger a generic in-character response; never invent the lost question or claim recovered text.
- Bound queues, deduplicate repeated sequence IDs when appropriate, recover after interruption, and test back-to-back messages. Repetition, if used, is transmitter-controlled and bounded.
- A receiver shroud can reduce off-axis ambient light; it is not a frequency filter. Validate alignment, range, timing, and venue-light tolerance experimentally.

## Offline acceptance and provenance
Prepare weights, model configuration, tokenizers, voices, binaries, libraries, toolchains, and assets while online. Use local paths and disable remote update/model lookups for the chosen components; `HF_HUB_OFFLINE=1` is relevant only to components that honor it, not a universal offline guarantee.

The final acceptance test starts both apps from a fresh process with Wi-Fi disabled on both machines, rather than relying on already-loaded sessions. Verify microphone capture, actual IR transfer, local model inference, local speech playback, and locally served UI/assets. Distinguish mock transport tests from physical transport evidence. Record measured latency and failures. No cloud fallback or pre-recorded response may be presented as live model inference. A clearly labeled diagnostic/mock mode is allowed for development only.

Keep exact dependency/model versions, license/source records, install/preload instructions, and startup commands. Do not commit large model artifacts or secrets without an explicit storage plan. Open weights do not automatically mean a model or voice meets the hackathon's award rules.

## Human roles and six-hour planning envelope
CE teammate owns wiring, board compatibility, IR firmware, real transport throughput/reliability, and interruption recovery. CS teammate 1 owns offline STT, sender desktop mode and speech adapter, and paced USB serial output. CS teammate 2 owns receiver events/plain-text display, local Qwen, speech/effects, and Ouija UI. One coordinator owns protocol contracts and integration. These human assignments are not automatic authorization to spawn software agents.

Within six hours, prioritize contract and smoke tests, then plain-text IR, then offline speech input and local AI output, then theater and rehearsal. Drop decorative effects or animation polish before compromising offline operation or the real transport path. Use TASKS.md for individual prompts and dependencies. Do not execute the full sprint in one request.

## Unresolved facts to confirm in relevant tasks
- Official hackathon rules and precise open-weight category requirements.
- Actual board models, IR parts, wiring, laptop operating systems, and installed artifacts.
- Chosen protocol encoding and tested IR payload/rate/range; whether heartbeats are needed.
- STT/LLM/TTS latency, microphone conditions, voice intelligibility, and asset provenance.
