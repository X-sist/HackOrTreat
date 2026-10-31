# CE tasks — @volyxge
Only this owner updates these statuses. One task per prompt. Ready next: **T04** (T02 hardware feasibility is not yet proven).

| ID | Status | Dependencies | Scope/evidence |
| --- | --- | --- | --- |
| T04 | pending | T02 design | Confirm actual Uno/module docs and wiring; pin Arduino CLI/core/IRremote versions; implement Tx serial/IR using shared constants/fixtures. Record compile/SRAM and actual timing/hardware evidence. Propose any required contract change before implementing a different format. |
| T05 | pending | T04 | Implement Rx framing/CRC/events with generated constants. Test real transfer, dropped/corrupt/partial packets, silence, duplicate behavior and recovery. |

Suggested subfolders: tx/, rx/, tests/, handoffs/. Both firmware targets use the same dependency pins and shared contract. No sender/receiver host edits. Do not infer module pins from labels alone. Compile/simulation alone is not real IR acceptance.
