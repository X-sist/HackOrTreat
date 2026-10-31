# CE major workspace — @volyxge

Both Uno R3 firmwares, V1221/V1222 wiring verification, IR transport and physical recovery. Use shared/generated/protocol.h; do not redefine protocol constants. Shared generated files are integration-owned. Document a reproducible way to expose the header to the Arduino build without maintaining another hand-edited copy.

Branch: `firmware/<task-id>-<short-description>`. Own clone/worktree; never point multiple writers at the same checkout. Start from current main after the collaboration baseline is merged. Read TASKS.md, then implement one task. Work can proceed against shared fixtures before the other components exist. Ordinary PRs modify only `firmware/` except its integration-owned contract.lock.json. Root docs/contracts require a separate `integration/` PR.

Run from repository root:
```
python tools/check_repo.py
python tools/validate_protocol_vectors.py
python tools/check_repo.py --role firmware --base origin/main
```
The last command checks committed branch changes; inspect `git status --short` as well for unstaged/untracked work. It is not a substitute for component tests or a required GitHub check. First implementation task configures the component runtime/dependencies; this skeleton is not a working app. See root WORKFLOW.md for locks, review and integration.

## Transmitter (T04)

Edit `tx/tx.ino` in VS Code. `python firmware/verify.py --ci` installs the component-pinned Arduino CLI,
AVR core and IRremote into ignored `firmware/.local/`, then compiles both Uno
targets. The build adds the repository root as an include path so both sketches
use `shared/generated/protocol.h` without a copied header.

The current user-confirmed wiring is transmitter DATA to Uno D2 and receiver
DATA to Uno D3. Only D2 is used by this Tx sketch. Module power, ground,
polarity, drive limits and exact V1221/V1222 pin documentation are not yet
verified; do not infer those connections from this note. Compile with the
command above, then upload through Arduino CLI after selecting the actual port:

```
arduino-cli --config-file firmware/.local/arduino-cli.yaml upload \
	--fqbn arduino:avr:uno --port COMx firmware/tx
```

The Tx accepts `HELLO` and `SEND<TAB>session<TAB>sequence<TAB>payload_hex`
records at the shared baud rate. It emits compact JSON-line events and sends
each packet byte as a full NEC frame with address `0xA700 | index`, on D2.
Reported `sent` means local modulation completed; it does not confirm receiver
delivery. Build evidence is not physical IR acceptance.

## Receiver (T05)

The Rx sketch is `rx/rx.ino` and uses the user-confirmed receiver DATA pin D3.
It decodes full NEC/NEC2 frames with the shared address prefix (IRremote can
classify the Tx's closely-spaced full frames as NEC2), assembles
strictly ordered indexed bytes, and validates packet version/type, declared
length, CRC-16/CCITT-FALSE, and printable nonblank ASCII before emitting a
`message`. It reports the shared incomplete-packet, checksum, and protocol
error events, ignores unrelated IR/noise and total-loss silence, and supports
`HELLO` over serial. Duplicate identity tracking is bounded to 32 entries with
the shared 60-second expiry.

Compile the Rx with the verification command above. Uploading the Rx sketch
replaces the firmware currently on the selected Uno; use the actual receiver
board/port and verify the transmitter remains on the other Uno. A successful
compile or serial `hello` does not prove IR decoding, timing, duplicate
handling, or recovery. Those require a two-board bench test.
