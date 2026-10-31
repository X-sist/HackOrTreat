# Living Plane: microphone and transcript

Run commands from the sender feature checkout root. Use its sender/.venv, not a global Python.

## Start
```powershell
sender/.venv/Scripts/python.exe sender/cli.py
```
- Press **Enter** to start recording; speak, then press **Enter** again to stop.
- Recording automatically stops at 10 seconds. `--seconds 5` changes the limit; maximum is 30 seconds.
- **Ctrl+C while recording cancels** and discards that recording.
- The transcript appears as `Recognized: ...`. The local model loads on first use and stays loaded for subsequent utterances.
- Type **t** for manual text, **d** for input-device IDs, **q** to quit.
- This default interactive mode does not send to an Arduino. Explicit one-shot sending is described below. Audio stays in memory and is not saved by this CLI. Transcripts are printed, not written to a transcript log.

If Windows chooses the wrong microphone:
```powershell
sender/.venv/Scripts/python.exe sender/cli.py --list-devices
sender/.venv/Scripts/python.exe sender/cli.py --device 1
```
Choose the ID for your actual microphone; IDs can change after reboot or plugging devices in. Prefer an actual microphone rather than Stereo Mix or a speaker-loopback input. If capture fails, enable microphone access for desktop apps in Windows privacy settings and check Windows Sound input selection. No microphone permissions are changed automatically.

## Other modes
```powershell
sender/.venv/Scripts/python.exe sender/cli.py --text "Spirit, what is your name?"
sender/.venv/Scripts/python.exe sender/cli.py --record --seconds 5
sender/.venv/Scripts/python.exe sender/cli.py --audio sender/.local/samples/demo.wav
```
Manual text never opens a microphone or loads the model. --record captures one timed utterance and exits; Ctrl+C cancels. --audio uses an existing local file. Non-interactive sessions must select a mode explicitly. URLs and remote model IDs are not accepted as audio/model sources.

## Live microphone evidence and remaining offline check
You ran the live microphone test yourself and demonstrated multiple captures plus the exact demo phrase; the agent has not recorded your microphone. To establish the remaining physical offline evidence, repeat with networking disabled. Disable Wi-Fi/network connectivity, start the interactive CLI, press Enter, say **“Spirit, what is your name?”**, press Enter to stop, and check the words after `Recognized:`. Try a second utterance to verify stop/restart and model reuse. Ctrl+C during a recording should cancel without transcription. Report the text or exact error back in this chat.

Local file inference, synthetic capture tests and device enumeration do not establish real offline microphone acceptance. The user has since demonstrated repeated live capture and the exact demo phrase; network-disabled status remains unconfirmed. See the C1-04 handoff. The software also uses offline HF flags/local_files_only and denies Python networking throughout model initialization and lazy transcription. This is not a firewall change or an automatic adapter disconnection.

## Scope and dependencies
C1-02 adds sounddevice0.5.6 (with exact cffi/pycparser transitive pins), keeping all 25 previously selected packages at their existing versions. C1-03 added pySerial3.5; requirements.lock and dependencies.json now contain 29 verified official wheels. PyAV16.0.1 remains pinned. If recreating the environment, follow SETUP.md with the updated lock; no other component needs microphone libraries.

C1-04 adds explicit serial sending using the C1-03 adapter; firmware/IR and receiver implementation remain other owners' workstreams. Recognition is displayed unchanged; outgoing text uses the shared 48-byte ASCII limit and explicit whitespace cleanup. Microphone native sample rate is wrapped as an in-memory PCM WAV and resampled by the existing Whisper audio decoder, avoiding an assumption that every microphone natively supports 16 kHz.

## Explicit Arduino sending (C1-04)

Compatible CE Tx firmware is required. The currently detected COM8 board has not yet received it. Check the current port before testing; no real SEND has been verified.

```powershell
sender/.venv/Scripts/python.exe sender/cli.py --list-ports
sender/.venv/Scripts/python.exe sender/cli.py --check-serial --port COM8
sender/.venv/Scripts/python.exe sender/cli.py --send --port COM8 --text "Spirit, what is your name?"
sender/.venv/Scripts/python.exe sender/cli.py --send --port COM8 --record --seconds 5
```

`--check-serial` opens the port and checks Tx hello/ready without sending text. `--send` requires an explicit local COM port and one of `--text`, `--audio`, or `--record`; default interactive mode remains text-only. Recording/transcription and text validation finish before opening a send connection. The exact outgoing normalized text is displayed before SEND. Each invocation waits for local accepted/sent/ready, reports the outcome, and closes its port. No automatic reconnect or retry occurs. Local sent never proves remote receipt. See handoffs/C1-04-20261031.md for evidence, recovery limits and Gemini review instructions.
