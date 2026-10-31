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
- Nothing is sent to an Arduino yet. Audio stays in memory and is not saved by this CLI. Transcripts are printed, not written to a transcript log.

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

## Your remaining acceptance check
You chose to run the live microphone test yourself; the agent has not recorded your microphone. Disable Wi-Fi/network connectivity, start the interactive CLI, press Enter, say **“Spirit, what is your name?”**, press Enter to stop, and check the words after `Recognized:`. Try a second utterance to verify stop/restart and model reuse. Ctrl+C during a recording should cancel without transcription. Report the text or exact error back in this chat.

Local file inference, synthetic capture tests and device enumeration do not establish real offline microphone acceptance. C1-02 stays awaiting that user check. The software also uses offline HF flags/local_files_only and denies Python networking throughout model initialization and lazy transcription. This is not a firewall change or an automatic adapter disconnection.

## Scope and dependencies
C1-02 adds sounddevice0.5.6 (with exact cffi/pycparser transitive pins), keeping all 25 previously selected packages at their existing versions. requirements.lock and dependencies.json now contain 28 verified official wheels. PyAV16.0.1 remains pinned. If recreating the environment, follow SETUP.md with the updated lock; no other component needs microphone libraries.

No serial ports, transmit controls, compression, IR or receiver changes are included. Those remain C1-03/C1-04 and the other majors' workstreams. Recognition is displayed unchanged; wire-length checks/cleanup belong to the serial task. Microphone native sample rate is wrapped as an in-memory PCM WAV and resampled by the existing Whisper audio decoder, avoiding an assumption that every microphone natively supports 16 kHz.
