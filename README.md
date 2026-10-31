# Beyond the Grave

Talk to an undead spirit through a real infrared link. Laptop 1 turns speech into text with local Whisper. Its Arduino sends the text over infrared to the Arduino on Laptop 2, where local Qwen generates the spirit's reply and Piper speaks it through the Ouija display.

The repository is named **HackOrTreat**. The project and demo are **Beyond the Grave**.

## Which laptop runs what?

| Laptop | Connected Arduino | What to run |
| --- | --- | --- |
| **Laptop 1: sender / Living Plane** | Transmitter | Python sender commands below; speak into this laptop |
| **Laptop 2: receiver / Spirit Plane** | Receiver | Receiver launcher below; open the Ouija page and use its speakers |

Run every command below from this repository's root in PowerShell. Both laptops need the same version of the code. They do **not** need the same COM port numbers. This sender most recently identified as **COM9**; find the receiver's port on its own laptop.

Only infrared carries the question between laptops. Each laptop connects by USB to its own Arduino. The receiver's local web page and Ollama service stay on that laptop; do not use the other laptop's IP address.

## Before the demo

1. Update both clean checkouts to the revision containing `tools/demo_receiver.mjs`. Preserve any uncommitted teammate work before updating. If these changes have not been committed/published yet, the other laptop cannot obtain them with `git pull`.
2. Confirm the transmitter and receiver have the correct production firmware. See [firmware instructions](firmware/README.md). Close Arduino Serial Monitor and other serial tools before starting the apps; only one program can open a board's port at a time.
3. Align the infrared transmitter with the receiver. Start at the short distance already tested by CE. Avoid moving or rewiring the modules during setup.
4. Check microphone input on Laptop 1 and speaker volume on Laptop 2.
5. Prepare local models and software **before disabling networking**. Having the same Git checkout does not copy model weights, voices, or environments: these are ignored local files.

### Laptop 1 requirements

- The prepared `sender/.venv` and the local Whisper files in `sender/models/tiny.en`.
- Follow [sender setup](sender/SETUP.md) to recreate them on a different machine. The sender uses its hash-locked environment, not a global Python installation.

### Laptop 2 requirements

- Node.js 24.15.0, the local Ollama service, and the **`qwen2.5:1.5b`** model.
- Piper and an English voice: the `.onnx` file **and its matching `.onnx.json` file**.
- Put the chosen voice at `receiver/models/piper/en_US-lessac-medium.onnx` with its JSON next to it, or give the launcher the real installed path using `--voice`.
- The launcher finds Piper on PATH or in `receiver/audio/.venv/Scripts/piper.exe` or `receiver/.venv/Scripts/piper.exe`. Use `--piper` if installed elsewhere.
- No additional npm serial package is needed: the launcher uses Windows' local serial support.

If the Qwen model is not already cached, prepare it **while online** with your installed Ollama:

```powershell
ollama pull qwen2.5:1.5b
```

Start the installed Ollama app/service. If it is not running, use a separate receiver terminal for `ollama serve`; leave that terminal open. If Ollama already runs, do not start a second copy. See [Ollama](https://ollama.com/download) and [Piper](https://github.com/OHF-Voice/piper1-gpl) for their respective installation instructions. Do not install receiver dependencies into the sender's environment.

## Step 1 — start Laptop 2, the receiver

Find the receiver's port:

```powershell
node tools/demo_receiver.mjs --list-ports
```

The returned port is local to Laptop 2. Replace `COM4` in the examples below with its actual receiver port.

Check the local model and voice before opening serial hardware:

```powershell
node tools/demo_receiver.mjs --check
```

This generates a short local Qwen response and a short Piper speech WAV. It fails clearly if the model service, voice, JSON, or Piper executable is missing. It does not open an Arduino, record a microphone, or download anything.

Start the receiver:

```powershell
node tools/demo_receiver.mjs --port COM4
```

If your voice/executable live elsewhere, provide their actual paths instead:

```powershell
node tools/demo_receiver.mjs --port COM4 --piper "C:\your\piper\piper.exe" --voice "C:\your\voices\en_US-lessac-medium.onnx"
```

Those paths are examples to replace, not files supplied by this repository. The same `--piper` and `--voice` options work with `--check`.

Leave the terminal open. Wait for **`RECEIVER READY`**, then open [http://127.0.0.1:3000](http://127.0.0.1:3000) **on Laptop 2**. Click **Enable sound** before the first question. If port 3000 is occupied, close your old receiver server or use `--web-port 3001` and open the printed address.

This launcher starts the receiver page, warms the local model, checks speech synthesis, verifies an Rx board identity, and forwards only validated serial events to the local display. It refuses a transmitter selected by mistake. Simulation buttons and the simulation API are disabled in this mode. A model or voice error is displayed honestly: a canned response or atmospheric tone does not count as a working live AI/voice demo.

Press **Ctrl+C** in this terminal to close the bridge and the server it started. After a disconnect, stop, fix the cable/port, and explicitly run the launcher again. Nothing is automatically resent.

## Step 2 — test manual text on Laptop 1, the sender

Confirm the current sender port:

```powershell
sender/.venv/Scripts/python.exe sender/cli.py --list-ports
sender/.venv/Scripts/python.exe sender/cli.py --check-serial --port COM9
```

Use the current Tx port if it changed from COM9. A connection check must report **Local Tx ready** before you proceed.

With the receiver running and the infrared modules aligned, send:

```powershell
sender/.venv/Scripts/python.exe sender/cli.py --send --port COM9 --text "Spirit, what is your name?"
```

Check both sides:

- **Laptop 1:** `Local result: local_sent` and `local_sent=True`.
- **Laptop 2 terminal:** `[REAL IR INPUT] Spirit, what is your name?`.
- **Laptop 2 page:** the received question appears separately from the generated spirit reply; the planchette spells the reply and the speakers play it.

`local_sent` only describes the transmitting Arduino. Receipt must be observed on Laptop 2. If it never receives a packet, silence alone cannot tell it that something was lost.

## Step 3 — test speech on Laptop 1

**This command runs on the sender laptop, not the receiver.**

```powershell
sender/.venv/Scripts/python.exe sender/cli.py --send --port COM9 --record --seconds 5
```

Speak **“Spirit, what is your name?”** into Laptop 1 during the five-second recording. It then transcribes locally, shows the exact outgoing text, and sends it. Laptop 2 remains running the receiver. Wait for the reply, voice, and spelling animation to finish before asking another question.

Repeat the command for each question. `--record` here is timed; it is not the interactive Enter-to-stop loop. The plain command `sender/.venv/Scripts/python.exe sender/cli.py` is useful for microphone/transcription practice but **does not send** anything.

Keep outgoing questions within **48 printable ASCII bytes**. Long or non-ASCII transcripts are rejected without truncation; edit the question and use `--text`. Ctrl+C during recording cancels the recording before sending. Cancellation after a SEND starts cannot undo a transmission; treat its result as uncertain.

## Step 4 — rehearse the actual offline demo

Once setup and local file preparation succeed, disable Wi-Fi/Ethernet on both laptops yourself. Leave localhost services available. Start both applications from fresh processes using the same steps above, then verify manual text, live speech, real receipt, generated response, voice, and visuals together.

For the beam-interruption demonstration, interrupt a transmission already in progress, then clear the path and send another question. The receiver may report a damaged/incomplete packet, or it may receive nothing at all. Show what actually happens; do not promise that every obstruction causes a checksum error. A subsequent clear-path question should arrive successfully.

## If something fails

| Symptom | What to check |
| --- | --- |
| Port busy / access denied | Close Serial Monitor and other apps using that Arduino. Stop a previous launcher before restarting. |
| Tx selected as receiver | Choose the other board's port on Laptop 2. Port numbers from CE's bench may differ on your laptops. |
| No Tx ready / no Rx hello | Correct port, production firmware, USB data cable, and board role. |
| Sender reports sent, receiver shows nothing | IR alignment, obstruction, module power/wiring, and actual Rx port. Sender status is not delivery proof. |
| Ollama/model check fails | Start the local service; check `ollama list` includes `qwen2.5:1.5b`. Download missing files before going offline. |
| Missing Piper/voice | Supply the installed `--piper` and `--voice` paths; the `.onnx.json` must sit beside the `.onnx`. Installing Piper does not automatically download a voice. |
| Page has text but no voice | Click Enable sound, check speakers/volume and visible Piper/playback errors. A drone tone is not synthesized speech. |
| Page is still spelling | Wait before sending again. Short replies are easier to demonstrate. |
| Browser cannot open the page | Use the receiver laptop's printed localhost address and keep its launcher terminal open. |

## Development checks and ownership

```powershell
sender/.venv/Scripts/python.exe sender/verify.py
python receiver/verify.py
node --test tools/tests/test_demo_receiver.mjs
python tools/generate_contract.py --check
python tools/check_repo.py
python tools/validate_protocol_vectors.py
node tools/check_js_contract.mjs
```

The repository consistency checker currently flags pre-existing root `package.json` / `package-lock.json` files, which conflict with WORKFLOW.md. This launcher does not use those packages; their placement still needs owner cleanup.

Fixture/simulation tests are development checks, not physical IR evidence. Direct `node receiver/src/server.mjs` and `--simulate` are still available for isolated diagnostics, but **the server alone does not read the Arduino**. Use the integrated launcher for the real demo.

| Role | Owner | Component details |
| --- | --- | --- |
| Arduino firmware / IR | @volyxge | [firmware](firmware/README.md) |
| Whisper / sender | @Aiden360-stack | [sender](sender/README.md) |
| Receiver / local AI / voice / display | @Xsist | [receiver](receiver/README.md) |

Read [WORKFLOW.md](WORKFLOW.md) before implementation. Shared protocol/constants/fixtures are integration-owned; do not change the wire format in one component. See [the protocol](docs/PROTOCOL.md), [project brief](PROJECT-BRIEF.md), and [requirements](SOFTWARE-REQUIREMENTS.md). Model files, local environments and machine-specific paths are not distributed by Git. [The integration handoff](docs/ai/tasks/demo-startup-20261031.md) records actual checks and remaining two-laptop acceptance rather than treating task labels as evidence.
