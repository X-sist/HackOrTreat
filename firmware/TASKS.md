# CE tasks — @volyxge
Only this owner updates these statuses. Implemented means software behavior is in place and compile-verified; complete requires real-world validation.

| ID | Status | Dependencies | Scope/evidence |
| --- | --- | --- | --- |
| T04 | complete | T02 design | Tx serial/IR implementation, pinned toolchain and shared packet framing compile-verified. Corrected board mapping is Rx COM4 / Tx COM5. Live short transfer and eight consecutive 48-byte maximum-payload transfers passed; a user-operated physical obstruction produced no received message, and a subsequent clear-path recovery message passed. Rx-reported `sent` is not delivery proof. Longer range, ambient-light behavior, measured timing, and primary module electrical documentation remain outstanding. |
| T05 | complete | T04 | Rx NEC/NEC2 framing, ordered packet assembly, CRC/text validation, protocol/disturbance events, 60-second duplicate tracking, and HELLO support implemented. Live message, duplicate, ID-conflict, partial-timeout, CRC-corruption, index-gap, whole-packet-timeout, and physical-obstruction behaviors verified; eight maximum-size transfers passed, along with clear-path recovery after injected errors and physical obstruction. Idle silence passed for 15 seconds. Longer range, ambient-light behavior, measured timing, and primary module electrical documentation remain broader hardware follow-ups, not claims of tested behavior. |

Suggested subfolders: tx/, rx/, tests/, handoffs/. Both firmware targets use the same dependency pins and shared contract. No sender/receiver host edits. Do not infer module pins from labels alone. Compile/simulation alone is not real IR acceptance.
