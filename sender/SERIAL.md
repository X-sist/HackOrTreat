# C1-03: manual serial adapter and simulator

Run from the usual repository root in PowerShell:

```powershell
sender/.venv/Scripts/python.exe sender/serial_cli.py --simulate --text "Spirit, what is your name?" --text "Hi"
sender/.venv/Scripts/python.exe sender/serial_cli.py --simulate --text "Hi" --scenario ready-timeout
```

This command only simulates a Tx Arduino. It opens no serial port, microphone, model, or network connection. Repeated `--text` arguments are processed sequentially, after each new local `ready`; they are not pipelined to the board. The simulator uses a virtual clock, so its running time is not measured hardware latency. Other scenarios: `accept-timeout`, `send-timeout`, `tx-failed`, `disconnect`. Success exits 0; invalid text or unsuccessful/uncertain local operations exit 2. `--simulate` is mandatory. C1-02's `cli.py` remains a transcript-only command; speech-to-board integration is C1-04.

Cleanup converts ASCII whitespace runs into a space and trims them. The exact outgoing text and byte count are displayed. Reject blank text, non-ASCII, remaining controls, more than 48 outgoing bytes, or raw inputs over 4096 characters. Nothing is compressed, silently stripped, or truncated. Edit rejected text explicitly.

## Adapter boundary

`sender.serial_adapter.SerialAdapter(write)` accepts a `write(bytes) -> byte_count` callable. `start(monotonic_seconds)` sends one `HELLO`; `feed(bytes, now)` handles split/multiple LF or CRLF records; `tick(now)` enforces deadlines even during silence. `send(text, now)` returns a result object whose status changes as events arrive. Call from one thread, with a monotonic clock. The parser holds at most 257 bytes (256 plus optional CR), discards overflow through LF, and retains at most 32 diagnostic strings. Shared `build_send`, `validate_event`, generated constants and fixtures define the boundary; no consumer pin or shared protocol is changed.

Initial readiness requires a validated Tx `hello` followed by `ready` within the shared boot timeout. There is no host queue: a send while unavailable raises visible BUSY/disconnected feedback. Each send consumes readiness and a new message identity. Acceptance must arrive within 2 seconds; `sent` and the next `ready` within 12 seconds of SEND. The Arduino owns symbol/guard timing; the host waits for its ready event rather than guessing that guard time has elapsed. Invalid/unknown events are diagnosed and ignored; wrong identities, illegal lifecycle ordering, and a board reset require explicit reconnection.

Results distinguish awaiting acceptance, accepted, local sent while waiting for ready, local sent, local board failure, and uncertain. `local_sent=True` records a validated matching `sent`, even if the subsequent ready times out. **Local sent never means remote received.** Missing completion events, partial writes, serial errors, or reconnect during an operation mark its result uncertain. No automatic resend or reconnect is performed. This task exposes no retry operation; a new manual rendition gets a new identity. Session IDs are random per adapter/process; sequence wrap requires a different session.

`poll_once(adapter, transport, time.monotonic)` reads at most the shared event bound. A bounded/nonblocking `transport.read(size)` must return `b''` for no data and raise `OSError` for a known disconnect. `open_local_port('COM3')` is a lazy pySerial backend with 115200/8N1, no flow control, a 50 ms read timeout and 500 ms write timeout; only explicit Windows COM names are accepted, never serial URLs/network transports. This helper was tested with a fake constructor, not a real port. [pySerial API reference](https://pyserial.readthedocs.io/en/latest/pyserial_api.html).

For future C1-04 integration, the caller owns transport closure: use the port's context manager, close after a fault/cancel, and explicitly open a fresh connection before `start()`. Continue polling while waiting, including during silence; never call HELLO while an operation is busy. USB opening may reset an Uno, and some physical disconnects present as silence until timeout. Real boot behavior, drivers, unplug detection and board/IR timing still need hardware evidence. Do not expose the backend as a successful real send until those checks are done.

## Verification and review

`sender/.venv/Scripts/python.exe sender/verify.py` runs sender tests, package consistency and native imports without recording audio or opening serial hardware. pySerial 3.5 adds one official SHA-256-verified wheel, for 29 total; all prior dependency pins and model artifacts are preserved. Gemini review is pending; see `handoffs/C1-03-20261031.md` for the focused review prompt and verification evidence.
