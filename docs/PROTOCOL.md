# HackOrTreat transport contract v1

Status: T02 design complete; conformance fixtures checked; Gemini review pending; physical timing and firmware feasibility not yet validated. This specifies the host/board and one-way IR boundary, not the desktop UI contract (U01), firmware (T04/T05), or app/parser implementation (T03/T06).

Team implementation note: `shared/contract.json` is the machine-readable source for these constants and event fields. Reuse generated Python/JS/C++ outputs, shared host validators and consumer pins; do not hand-copy variables. Known v1 event objects reject extra fields at the shared host boundary. Existing packet bytes/serial examples are unchanged. See WORKFLOW.md for coordinated changes.

## 1. Scope and decisions
- Path: sender laptop USB -> Uno R3 A -> V1221 IR -> V1222 -> Uno R3 B USB -> receiver laptop. No return IR path, remote acknowledgements, network transport, or remote retry requests.
- One message in flight. At most 48 printable ASCII bytes per message; English demo phrases fit. No compression, fragmentation, Unicode transport, or implicit truncation in v1. Host may normalize whitespace to ordinary spaces and trim before displaying the exact outgoing text. Non-ASCII must be explicitly edited or rejected, never silently stripped. Empty/all-space messages are rejected.
- Packet identity is a 32-bit host-created session plus 16-bit sequence. New random session on each sender process start; sequence starts at 0 and increments for each new message. On wrap, choose a different session before reusing 0. Collision resistance is best effort, not authentication. An intentional new rendition of the same text gets a new sequence. A retry of the same logical message must retain its identity and identical bytes.
- Heartbeats are **disabled and unsupported in v1**. The baseline staged demo interrupts a packet already in progress. Silence at startup or a completely missed packet cannot be detected as a loss by the receiver. Idle beam-loss detection requires a later explicitly versioned heartbeat design, not an invented UI error.
- No automatic retransmissions. A later user-initiated retry is possible after local sender ready, with explicit uncertainty that delivery may already have occurred. CRC detects many accidental errors; it does not authenticate the sender or guarantee that every corruption is detected.

## 2. Logical IR packet
Numbers are unsigned. Multibyte numeric fields and the CRC are big-endian. Payload bytes are ASCII, not a null-terminated string. There is no physical LF inside the IR packet.

| Byte offset | Size | Field |
| --- | --- | --- |
| 0 | 1 | version = 0x01 |
| 1 | 1 | type = 0x01 (TEXT); all other values reserved/rejected |
| 2 | 4 | session, 0..0xFFFFFFFF |
| 6 | 2 | sequence, 0..65535 |
| 8 | 1 | payload length N, 1..48 |
| 9 | N | printable ASCII 0x20..0x7E, with at least one non-space |
| 9+N | 2 | CRC-16/CCITT-FALSE over bytes 0 through 8+N inclusive |

Packet size is 11+N bytes (12..59). CRC parameters: polynomial 0x1021, initial 0xFFFF, RefIn=false, RefOut=false, XorOut=0x0000. Check string ASCII `123456789` -> 0x29B1. Calculate on binary header/payload, not hexadecimal characters or serial lines. Fixture vectors supply full examples.

Length and indexed symbols provide framing; there is no ambiguous printable START/END delimiter and no byte-stuffing inside the binary packet. Length is only provisional until the CRC passes; a corrupted but in-range length may cause timeout or CRC failure rather than delivery. Never allocate dynamically from a received length.

## 3. Provisional physical encoding
Use full NEC-style frames through a pinned, later-validated Arduino-IRremote version. For logical packet byte at index i (0..58): address = `0xA700 | i`; command = that byte; send one full frame with repeat count 0. Nominal carrier 38 kHz. Address and command are the library's decoded numeric fields; NEC's physical bit order is handled by the library and is distinct from the logical packet byte order above. Do not send raw host integers as replacement bit patterns.

Receiver accepts a complete NEC-family frame with valid command inversion, full address high byte 0xA7, and index <=58. Ignore special short repeat frames, unknown protocols, parity-invalid symbols, other address prefixes, and out-of-range indexes. Full NEC/NEC2 classification may differ across pinned versions; accept full 32-bit frames with these field semantics, not a short repeat reconstructed from a prior command. The 0xA7 prefix is a namespace filter, not secure sender identity. For indexes 0..58, the low address byte never complements 0xA7, avoiding address reduction to an 8-bit NEC address under normal decoding. T04/T05 must verify actual library behavior with known vectors.

Provisional scheduling constants (all monotonic elapsed times):
- `SYMBOL_PERIOD_MS=120`: full-symbol start-to-start, not 120 ms added after each blocking send call. Never start before the prior symbol has finished. A missed sender deadline fails the local operation rather than rushing subsequent symbols.
- Sender target starts are first-symbol start + i*120 ms. `SYMBOL_MAX_LATE_MS=20`: if a symbol cannot start by target+20 ms, abort with local TX_FAILED and observe the guard; do not compress gaps to catch up. The small scheduling tolerance must be validated on the actual board.
- `INTER_SYMBOL_TIMEOUT_MS=500`: while assembling, abort once time since the last accepted symbol is >=500 ms. Ignored noise does not reset this timer.
- `PACKET_TIMEOUT_MS=9000`: abort once elapsed time since index 0 is >=9000 ms, regardless of continuing noise/traffic.
- `PACKET_GUARD_MS=600`: after the final symbol's start, wait at least 600 ms before advertising ready or starting the next packet. On local abort, guard from the last attempted symbol start. This also lets an incomplete receiver reset.
- A maximum-size packet occupies 59 symbol slots: nominal last start 6960 ms and ready at 7560 ms, with the permitted final scheduling lateness adding at most 20 ms if transmission succeeds. Actual duration and error recovery must be measured. Do not promise subsecond transfer. Shorter phrases take proportionately less time.

These are design targets, not established V1221/V1222 specifications. Pinout, supply/drive constraints, receiver AGC behavior, alignment/range, event-processing budget, and actual timing remain physical validation gates. Do not infer module wiring from a bare TSOP38238 example. Do not silently change wire format/timing in one implementation: update this contract and fixtures together.

## 4. Receiver assembly and validation
Maintain one bounded 59-byte assembly buffer, expected index, and timers.

1. IDLE ignores any symbol except index 0 with byte 0x01. This pair starts assembly and its timers. No message identity is trusted yet.
2. While ASSEMBLING, accept exactly the next index. An index 0/version 1 restarts: emit one INCOMPLETE_PACKET with reason RESTART for the abandoned packet, then start anew. Any other relevant full symbol with the wrong index emits INCOMPLETE_PACKET/INDEX_GAP and returns to IDLE. Ignored noise/protocols do not advance assembly.
3. Validate version/type as soon as available. Unsupported type emits PROTOCOL_ERROR/UNSUPPORTED_TYPE and resets. At index 8, length outside 1..48 emits PROTOCOL_ERROR/INVALID_LENGTH and resets. Never consume a declared larger packet. The wrong index-0 byte in IDLE is ignored as non-start traffic.
4. At either timeout emit INCOMPLETE_PACKET with reason INTER_SYMBOL_TIMEOUT or PACKET_TIMEOUT, then IDLE. If both expire together, PACKET_TIMEOUT takes precedence. Apply timeouts before processing a symbol at the same timestamp. No event for IDLE silence.
5. After exactly 11+N bytes, calculate CRC first. Mismatch emits CHECKSUM_FAILED, resets, and discards all text. Matching CRC but invalid printable/nonblank text emits PROTOCOL_ERROR/INVALID_TEXT. No corrupted payload is surfaced as text or guessed by Qwen.
6. Only a CRC-valid, well-formed TEXT packet can be delivered or deduplicated. Extra symbols after completion cannot extend it; IDLE ignores nonzero indexes.

Duplicate policy: retain only the most recently **delivered** identity and full payload, for 60,000 ms since delivery. Expire at age >=60,000 ms. Within that window, identical identity+payload emits `duplicate` without delivery, animation, or inference; same identity with different valid payload emits ID_CONFLICT without replacing the cache. Other identities are delivered and replace the cache. Duplicate events do not extend TTL. This is bounded last-message deduplication, not a historical replay window: an older identity can be accepted after an intervening delivery, expiry, or reboot. No claim of exactly-once delivery. Invalid packets never alter the cache.

Firmware should use static bounds and avoid constructing large JSON documents in RAM. Library capture buffers, UART buffers, and stack must be included in a real Uno SRAM/compile measurement in T04/T05; this design alone does not prove memory fit. Resets discard unfinished assembly and the dedup cache. Hosts clear connection-scoped state on board hello/reconnect.

## 5. USB serial command contract
115200 baud, 8 data bits, no parity, 1 stop bit, no hardware flow control. ASCII LF (`0A`) terminates each record; optionally accept one CR immediately before LF. All limits exclude LF and that optional CR. Blank lines are ignored. Process split reads incrementally and multiple lines individually. After overflow, discard through the next LF before accepting another record; never execute a truncated prefix. Do not mix free-form debug output into this channel.

Host -> board lines (strict uppercase keywords and hexadecimal; no extra fields):

| Command | Board | Meaning |
| --- | --- | --- |
| `HELLO` | Both | Request current version/role; tx also reports ready if idle |
| `SEND\tSSSSSSSS\tQQQQ\tHEX` | Tx only | Tabs are actual byte 09; session exactly 8 hex digits, sequence exactly 4, payload exactly 2*N hex digits |

Hex digits must be uppercase 0-9/A-F. Reject embedded controls, odd hex, invalid text, empty fields, noncanonical widths, or extra tabs. Maximum host line buffer is 128 ASCII bytes; a maximum-size valid SEND line is 115 bytes. Receiver rejects SEND as UNKNOWN_COMMAND; neither board accepts arbitrary JSON commands. No host-supplied CRC: Tx constructs the binary envelope/CRC.

On boot each board emits `hello`. Sender then emits `ready`. A host that missed boot requests HELLO once idle; it waits for the correct `v`, role, and sender ready before sending. Give board boot/serial discovery up to 5 seconds, then report a local connection error rather than assume readiness. Opening USB can reset the board: reconnect invalidates old local ready/in-flight state.

Stop-and-wait: host sends one SEND only after ready, then waits for accepted, sent or error, and a new ready. No queued host commands while busy, including HELLO. A small host-side queue may hold at most one pending message; additional attempts receive a visible BUSY rather than silent drops. Tx validates the entire command before accepted. It consumes readiness immediately on acceptance, emits accepted, transmits once, emits sent, observes guard, and emits ready. It must not block sending the accepted event behind the entire IR operation.

Rejected idle commands emit error then ready; do not transmit. Unexpected commands while transmitting must not change the in-flight operation: if parsed, emit BUSY (no ready); if UART overflow makes recovery uncertain, host times out and reconnects explicitly. Correct host pacing avoids this unsupported flood path.

Host timeout: accepted within 2 seconds of SEND; sent and ready within 12 seconds of SEND. On missing events/disconnection, mark local result uncertain and require reconnect/HELLO, not automatic resend. sent means the local modulation routine completed, not that the receiver got anything. A tx-local failure emits error/TX_FAILED, then ready only after the guard if the board remains healthy.

## 6. Board -> host NDJSON events
Each event is one compact JSON object plus LF, maximum 256 bytes excluding LF. Required fields below; no raw corrupt text or dynamic debug strings. All objects have `v:1`. `session` is 8 uppercase hex characters and `seq` a JSON integer 0..65535. Use JSON numbers/booleans, not their quoted equivalents. Missing or invalid required fields are host protocol errors, not IR disturbance. Unknown event/version is ignored with local diagnostics and no inference; U01 may adapt these into desktop events.

| event | Role | Additional required fields |
| --- | --- | --- |
| hello | tx/rx | `role` = "tx" or "rx", `max_text_bytes` = 48 |
| ready | tx | none |
| accepted | tx | session, seq |
| sent | tx | session, seq |
| error | both | `code`: MALFORMED_COMMAND, LINE_TOO_LONG, INVALID_TEXT, UNKNOWN_COMMAND, BUSY, or TX_FAILED; session/seq omitted |
| message | rx | session, seq, `payload_hex` (2..96 uppercase hex chars decoding to valid text) |
| duplicate | rx | session, seq |
| disturbance | rx | `code`: CHECKSUM_FAILED or INCOMPLETE_PACKET; `reason` as below; `session:null`, `seq:null` |
| protocol_error | rx | `code`: UNSUPPORTED_TYPE, INVALID_LENGTH, INVALID_TEXT, or ID_CONFLICT; session/seq omitted |

CHECKSUM_FAILED reason is CRC_MISMATCH; INCOMPLETE_PACKET reason is INDEX_GAP, RESTART, INTER_SYMBOL_TIMEOUT, or PACKET_TIMEOUT. Unverified packet metadata stays null, even if its header looked sensible. Host `message` hex parsing must validate the full schema and text bounds before display/model use. Only message supplies new user text. Disturbance may trigger a short model response with explicit status and optional last valid text labeled as prior context. It cannot supply a newly recovered question. Cap/coalesce automatic disturbance-triggered model/audio requests to one outstanding request and at most one new trigger per 5 seconds; preserve distinct transport diagnostics.

Examples (each followed by LF):
```json
{"v":1,"event":"hello","role":"tx","max_text_bytes":48}
{"v":1,"event":"ready"}
{"v":1,"event":"accepted","session":"12345678","seq":1}
{"v":1,"event":"sent","session":"12345678","seq":1}
{"v":1,"event":"message","session":"12345678","seq":1,"payload_hex":"4869"}
{"v":1,"event":"disturbance","code":"CHECKSUM_FAILED","reason":"CRC_MISMATCH","session":null,"seq":null}
```

Host display maps confirmed CRC failure to `CHECKSUM_FAILED: AETHER DISTURBED`; incomplete packet to `INCOMPLETE_PACKET: AETHER DISTURBED`. Local serial framing errors, invalid message schemas, ID conflicts, or model errors must have their own labels, not a fake beam-break explanation. A software error does not establish a physical cause. The staged beam interruption will often drop symbols instead of yielding a complete bad-CRC packet; demonstrate whichever genuine transport event occurs.

## 7. Fixtures and verification boundaries
`protocol-vectors.json` contains binary envelope/CRC, indexed-symbol, serial, duplicate, partial, oversized, and silent-loss examples with explicit expected outcomes. Times are milliseconds relative to the first symbol. `tools/validate_protocol_vectors.py` verifies arithmetic, CRC known-answer checks, fixture metadata, index range/address convention, and serial bounds without installing packages or touching hardware. It is a conformance-data check, not a production parser, firmware, or proof that event state machines work. T03/T04/T05 must implement and test those behaviors independently against these examples, including timestamp boundaries, reconnects, malformed serial input, and full-frame library decoding.

Hardware gates: verify real module documentation/pinout, full decoded symbols, worst packet timing, receiver event throughput, SRAM, cable/USB behavior, idle silence, checksum rejection, actual mid-frame obstruction/recovery, range/alignment, and venue lighting. If 48-byte latency is unacceptable, propose a separate protocol revision rather than silently swapping encoding.

Primary technical references checked October 31, 2026:
- [Uno R3 board documentation](https://docs.arduino.cc/hardware/uno-rev3/): target board family; no V1221/V1222 pinout implied.
- [Arduino-IRremote](https://github.com/Arduino-IRremote/Arduino-IRremote): structured address/command sending, repeat behavior, and bounded capture considerations.
- [NEC implementation](https://github.com/Arduino-IRremote/Arduino-IRremote/blob/master/src/ir_NEC.hpp): full-frame encoding/decoding reference. These moving references are not a pinned installed dependency; T04/T05 select and record an exact version.
