# T01: development and demo inventory

Recorded October 31, 2026, approximately 11:11 a.m. America/New_York. This is an inventory task, not installation, implementation, performance testing, or offline certification.

## Result
Inventory complete with explicit unknowns. The accessible Windows computer matches the proposed CPU/RAM class. The user confirmed this is one demo laptop and reports the second is identical. Both boards are reported Uno R3; IR modules are V1221 Tx and V1222 Rx. These identities are user-confirmed, not physically tested. The supplied event/category pages have now been reviewed; see SOFTWARE-REQUIREMENTS.md. Full eligibility remains unverified beyond the published category description.

## Confirmed local computer
| Item | Observation | Evidence |
| --- | --- | --- |
| OS | Windows 11 Pro, 64-bit; version 10.0.26200, build 26200 | Win32_OperatingSystem |
| Machine | Dell Inspiron 15 3530 | Win32_ComputerSystem |
| CPU | Intel Core i5-1334U; 10 cores, 12 logical processors | Win32_Processor |
| RAM | 31.7 GiB reported physical memory, consistent with nominal 32 GB | Win32_ComputerSystem |
| Graphics | Intel Iris Xe Graphics | Win32_VideoController |
| Storage | C: approximately 633.7 GiB free at inspection | Get-PSDrive; available space can change |
| Audio devices | Realtek microphone and speakers reported present/OK | Get-PnpDevice AudioEndpoint; capture/playback not tested |
| Serial devices | No devices returned by Win32_SerialPort at inspection | Does not prove no boards are owned or that all USB/driver states are covered |

## Development software
| Component | Observation and scope |
| --- | --- |
| Node.js | `node --version`: v24.15.0 |
| npm | `npm --version`: 11.12.1 |
| Python | `python --version`: 3.14.4; `py --list` lists Python 3.14 64-bit |
| Git | `git --version`: 2.54.0.windows.1 |
| VS Code | Windows uninstall metadata: 1.144.0 |
| Antigravity | Windows uninstall metadata: 2.28.2; desktop installation present |
| Python packages | Default interpreter's `python -m pip list --format=json` does not list faster-whisper, pyserial, piper-tts, pedalboard, ctranslate2, or onnxruntime. Other environments were not exhaustively searched. No audio/ML compatibility test was run. |
| Ollama / Arduino / audio tools | `ollama`, `arduino-cli`, `piper`, `whisper-cli`, and `ffmpeg` were not discoverable on PATH. No Ollama/Arduino application entry was found in the inspected uninstall metadata. This is not an exhaustive absence claim. |
| Provider CLI | `agy` and `gemini` were not discoverable on PATH. No provider invocation or authentication test was made. |
| Arduino user data | `%LOCALAPPDATA%/Arduino15` exists and contained `inventory.yaml` only at its top level. This alone does not establish a working compiler, board core, or IRremote library. `Documents/Arduino` was not found. |

Python 3.14 is an observed version, not a selected ML runtime. Verify supported versions and available wheels in T07/T10 before choosing or installing a runtime. Electron, serialport, IRremote, and the speech/model stack are not configured as project dependencies in this repo.

## Model, voice, asset, and rules inventory
- Default `.ollama/models` and `.cache/huggingface/hub` directories were not found. `OLLAMA_MODELS`, `HF_HOME`, `HUGGINGFACE_HUB_CACHE`, and `WHISPER_CACHE` were unset in this process.
- No matching Qwen/Whisper/Piper GGUF/ONNX artifacts were found in the bounded searches of HackOrTreat or the separately discovered Downloads/HackathonShootoutProject folder. No matching top-level model/tool download filenames were found in Downloads. Large caches, alternate drives, and arbitrary custom paths were not exhaustively searched.
- HackOrTreat contains workflow/brief/roadmap Markdown and its README, with no application manifests, source implementation, tests, or model/audio/image artifacts at inspection. No project-specific build/test command exists to run yet.
- No model ID, quantization, voice file, license record, or offline inference readiness is confirmed. Qwen 2.5 1.5B/3B, tiny.en, Piper, and Pedalboard remain proposals from PROJECT-BRIEF.md.
- No files were listed under this chat project's `sources/` directory. The user subsequently supplied the official MLH event URL. Its Best Open-Source AI Project category was fetched and checked; Gemma 4/ElevenLabs are separate categories. See SOFTWARE-REQUIREMENTS.md for primary sources and unestablished policies.

## Physical hardware: reported versus verified
| Item | User-supplied plan | Still needed |
| --- | --- | --- |
| Laptops | User confirms this laptop is in the demo and reports both identical | Second-machine installed environment and peripherals not directly checked |
| Arduino boards | Two Uno R3 boards (user wording: Uno 3), one per laptop | Physical identity/USB connection, installed drivers, available ports, data cables not tested |
| IR transmitter | Exactly one V1221, user-confirmed | Primary module pinout, circuit, driver/current limits, voltage/carrier behavior unverified |
| IR receiver | Exactly one V1222, user-confirmed; supersedes TSOP38238 example | Primary module pinout, power requirements, modulation/timing compatibility unverified |
| Circuit/props | Breadboards, jumpers, beam-interrupting prop, receiver shroud proposed | Physical availability, wiring, bench observations |

Nothing was flashed, no ports were opened, no microphone recording was made, and no beam or audio test was performed. The one-transmitter/one-receiver constraint remains fixed; a return IR acknowledgement is unavailable.

## Blockers and next decisions
1. **Eligibility:** supplied official event and selected category reviewed; substantive open-source/open-weight AI required. Confirm remaining organizer policies on advance work, team eligibility, assistant use, publication, and submissions. No blanket eligibility claim.
2. **Hardware firmware:** Uno R3/V1221/V1222 identities now supplied; verify actual module pin labels/manufacturer documentation and connection before T04/T05 wiring/firmware assumptions.
3. **Second machine:** repeat the bounded inventory there before selecting deployment roles or claiming two-machine readiness.
4. **Offline runtime:** model/voice artifacts and working runtimes are not verified. Later tasks must select, provision, and test them explicitly; no downloads were made in T01.
5. **Framework:** desktop shell remains undecided until U01. Installed Node/Python versions alone do not settle packaging or library compatibility.

T02 can specify a board-independent protocol and document provisional timing/size limits; actual throughput and board-specific capacity remain hardware-validation items. Do not begin T02 automatically.

## Evidence and collection limits
Read-only checks performed: `Get-CimInstance` for operating system, computer, processor, graphics, and serial ports; `Get-PnpDevice -PresentOnly -Class AudioEndpoint`; `Get-PSDrive -PSProvider FileSystem`; `Get-Command` for named tools; version commands listed above; `py --list`; default-interpreter `python -m pip list --format=json`; filtered Windows uninstall registry entries; bounded file/directory searches; and `git status --short`, `git rev-parse HEAD`, and `git ls-files` for HackOrTreat.

Initial restricted system queries were unavailable; the same system inventory succeeded with approved read access. No computer identifiers, full package dump, authentication state, or credentials are stored in this report. Findings establish only what was observed at this time. Wi-Fi was not disabled and no fresh-process offline acceptance test was run.

Sources: direct local system observations; the user-supplied blueprint in this chat as summarized in PROJECT-BRIEF.md. Update: official event/category and Qwen publisher sources reviewed after the user reply; see SOFTWARE-REQUIREMENTS.md. Model metadata supports the preferred candidate, not actual installed-artifact or full component-license verification.
