# T02 handoff: transport contract v1

## Goal and result
Define one-way IR packet/USB serial contracts with valid, corrupted, partial, duplicate, and oversized examples; explicitly decide on heartbeat behavior. Design completed, with physical timings and library feasibility provisional. No app, firmware, installations, model downloads, or T03/U01 implementation performed.

Starting commit: `97effe9f2f6cf23b895d50ec1ef8e3f5cd78083e`. Starting working tree: clean. T01 complete with documented unknowns. All new files and the roadmap edit below belong to this T02 task; no existing user changes were present at inspection.

## Files
- `docs/PROTOCOL.md`: canonical v1 envelope, bounds, CRC, indexed NEC symbols, timing, assembly/dedup/error rules, and serial commands/events.
- `docs/protocol-vectors.json`: 15 packet cases and 8 serial cases, including nominal demo phrase, CRC mismatch, partial/whole timeout, duplicate, conflict, expiry, oversize, and total silence.
- `tools/validate_protocol_vectors.py`: dependency-free fixture arithmetic/CRC/consistency checker, not a production parser or encoder.
- `TASKS.md`: T02 marked complete (design; hardware unverified), linked to evidence; no other task advanced.
- This task handoff.

## Decisions and risks
48 printable ASCII bytes maximum; 59-byte maximum binary packet. CRC-16/CCITT-FALSE; 32-bit session and 16-bit sequence. Provisional full NEC frame per indexed byte, conservative 120 ms slots, bounded assembly and one in-flight message. Nominal maximum-size sending operation is about 7.56 seconds before local ready; no low-latency hardware claim. No remote ACK, compression, automatic retries, or Unicode/fragmentation in v1.

Heartbeats disabled. Only a started packet can time out; completely missed transmissions and idle silence produce no fabricated failure. Real beam obstruction may drop a symbol rather than cause a CRC failure, so the UI must show the genuine event. CRC-invalid payload never becomes model input. Deduplication covers only the last valid delivered message for a bounded interval, not exactly-once delivery.

Uno SRAM/compiled sizes, exact pinned IRremote version, actual NEC decoder semantics, module pinouts/drive, carrier/timing behavior, range, obstruction recovery, and serial throughput remain T04/T05 verification gates. U01 uses this boundary but defines its own desktop UX/event mapping. Framework remains provisional.

## Verification
Ran `python t02-output/create_vectors.py` in the preparation workspace to author JSON fixtures (generator is not installed into the repo). Ran `python t02-output/validate_protocol_vectors.py t02-output/protocol-vectors.json`; initial 14 packet / 8 serial vectors passed, then added the whole-packet timeout example. Final installed command is `python tools/validate_protocol_vectors.py`; record its actual result below during installation.

Checks validate the standard CRC check word, packet lengths and CRC signs, identity byte order, symbol/index bounds, JSON event lengths, serial maximum/overflow, split-line fixture reconstruction, and key timing/cache fixture boundaries. They do not execute an assembler, parser, UART, firmware, or model. Test state machines independently in their implementation tasks. No existing app test/build command exists. Hardware and offline end-to-end tests were not performed.

## Review
Pending independent Gemini review; no reviewer has been invoked. Relevant file hashes/current commit will be recorded below. This handoff itself is excluded from its hash list to avoid self-reference.

Ready-to-paste Gemini prompt:

> Review T02 only in HackOrTreat. Read AGENTS.md, PROJECT-BRIEF.md, docs/PROTOCOL.md, docs/protocol-vectors.json, and docs/ai/tasks/T02-20261031-protocol/handoff.md. Inspect tools/validate_protocol_vectors.py and the T02 roadmap status. Look for inconsistent framing/byte order/CRC, unbounded buffers, one-way ACK assumptions, duplicate identity errors, timeout boundary issues, misleading disturbance/model input semantics, serial pacing/overflow mistakes, and unsupported hardware claims. Check distinctions between fixture consistency, actual state-machine tests, and physical validation. Do not edit files, install tools, flash hardware, or start U01/T03. Return actionable findings with stable IDs and evidence, or no actionable findings with limitations.

Next suggested task: U01 only, upon a separate request. Do not automatically begin it.

## Installed verification and review target
Installed command: python tools/validate_protocol_vectors.py
Result: PASS, 15 packet cases and 8 serial cases; fixture consistency only.
Current commit: 97effe9f2f6cf23b895d50ec1ef8e3f5cd78083e
Changes remain uncommitted. Independent review pending.
SHA-256 docs\PROTOCOL.md: 3DE03540403BECD1E4E55CA65B02B76DE39615DA636A9627AFE71A3BAD9C3102
SHA-256 docs\protocol-vectors.json: 04C68EABE79D0CB1DB63221B91B96078410D8B2B8467F47D3C4A7CBC42289B66
SHA-256 tools\validate_protocol_vectors.py: 83CF5E5CEE38B4BB205B0D20279E0BA60D10709D6A3E673264CE01C14CE86FBE
SHA-256 TASKS.md: 3A1C6EB92730D0DEB53C2DC7AF58390E67C55F7904396E4EB7FA831C66E84070
