# Beyond The Grave — The Spirit Plane (Laptop 2)

A rudimentary, offline Node.js interface for **Laptop 2 ("The Spirit Plane")** in the six-hour IR-linked Ouija hackathon performance.

This server powers:
1. **Serial Listener:** Listens to incoming Arduino optical IR signals (115200 baud) and beam disruptions (`<AETHER_DISTURBED>`).
2. **Offline LLM Router:** Routes incoming text and corrupted disturbance flags to local Ollama (`qwen2.5:1.5b` or `3b`).
3. **Ouija Board Planchette UI:** A weathered mahogany wood / slate-grey visual interface where a digital planchette glides to spell out the spirit's words letter-by-letter with smooth CSS transforms.
4. **Simulation Bench:** Built-in test controls to test the full pipeline before hardware is plugged in.

---

## ⚡ Quick Start (Zero-Dependency Mode)

The server is built to run immediately using Node's native HTTP engine—even before installing any `npm` packages!

```powershell
# 1. Start the server
node server.js

# 2. Open the UI in your browser:
# http://localhost:3000
```

---

## 📋 Missing Dependencies Checklist (Download Tonight!)

Since Wi-Fi will be disabled during the live demo, **all of the following dependencies must be installed and cached while you still have internet access.**

### 1. Node.js Project Dependencies
Run in this folder:
```powershell
npm install
```
Installed packages:
- `serialport` (^12.0.0): For reading USB serial data from the receiving Arduino.
- `@serialport/parser-readline` (^12.0.0): To cleanly buffer incoming packets until a newline (`\n`).
- `dotenv` (^16.4.5): For environment variables (`.env`).

*(Optional if expanding the server)*:
- `ws` or `express` (if replacing standard HTTP server).

---

### 2. Local Offline AI Model (Ollama + Qwen 2.5)
The spirit's brain runs entirely offline on Laptop 2 via Ollama:
1. **Install Ollama for Windows:** [https://ollama.com/download](https://ollama.com/download)
2. **Download Qwen 2.5 tonight:**
   ```powershell
   ollama pull qwen2.5:1.5b
   # Or for richer vocabulary if RAM permits:
   ollama pull qwen2.5:3b
   ```
3. **Verify offline:** Turn off Wi-Fi and verify the model responds:
   ```powershell
   ollama run qwen2.5:1.5b "Are you there?"
   ```

---

### 3. Text-to-Speech (Piper TTS) & Audio FX
1. **Piper TTS Binary or Python package:**
   ```powershell
   pip install piper-tts
   ```
2. **Voice Model (.onnx & .json):**
   Download an ONNX voice model file (e.g., `en_US-lessac-medium.onnx` or a deep raspy voice) and place it in an `./audio/` directory.
3. **Spotify Pedalboard (for supernatural reverb/distortion):**
   ```powershell
   pip install pedalboard
   ```
4. **Audio Assets:**
   - Ambient drone `.mp3` background loop.

---

### 4. Arduino Physical Layer (CE Major)
1. **Arduino IDE:** [https://www.arduino.cc/en/software](https://www.arduino.cc/en/software)
2. **`IRremote` Library:**
   - In Arduino IDE: `Tools` > `Manage Libraries...` > Search `IRremote` by shirriff / z3t0 > `Install`.
3. **Hardware Config:**
   - Baud Rate: `115200`
   - IR Receiver: TSOP38238 (connected to 5V, GND, and Pin 2/11 depending on board).
   - Format: Packets must end with `\n` to prevent buffer starvation.

---

### 5. Laptop 1 Dependencies (Living Plane / Speech-to-Text)
For your teammate on Laptop 1:
```powershell
pip install faster-whisper pyserial
# CRITICAL: Prevent huggingface from pinging network offline
$env:HF_HUB_OFFLINE="1"
```
Ensure `tiny.en` model weights are loaded and cached locally.

---

## 🛠️ Configuration (.env)

Copy `.env.example` to `.env`:
```ini
PORT=3000
SERIAL_PORT=COM3
BAUD_RATE=115200
OLLAMA_HOST=http://127.0.0.1:11434
OLLAMA_MODEL=qwen2.5:1.5b
```

---

## 🎭 Running the Simulation (No Hardware Needed)

1. Launch `node server.js`
2. Open `http://localhost:3000`
3. Click:
   - **Ask: "What is your name?"**: Simulates Laptop 1 sending a voice transcription.
   - **Simulate Beam Disturbance**: Simulates a judge breaking the IR beam, triggering a glitch flash, `CHECKSUM_FAILED: AETHER DISTURBED` alert banner, and agitated spirit response.
   - **Center Planchette**: Resets the planchette to the center.
