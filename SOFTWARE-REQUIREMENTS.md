# Software requirements and award evidence

Verified public pages October 31, 2026. This document separates published category criteria from the team's own offline/product requirements. It is not a declaration of organizer approval or complete eligibility.

## Published award target
Event: Hacktoberfest Hack Day Lexington x Women in Data Science at UK. Target category: **Best Open-Source AI Project**.

The category asks for an original project with open-source or open-weight AI serving a significant function. It gives model-based projects, agent skills, and model harnesses as examples. It does not specify a mandatory model or inference vendor. The event lists Gemma 4 and ElevenLabs as separate prize categories; their technology descriptions are not requirements of this selected category.

Primary sources:
- [Event page](https://www.mlh.com/events/hacktoberfest-hack-day-lexington-x-women-in-data-science-at-uk)
- [Selected category](https://www.mlh.com/events/hacktoberfest-hack-day-lexington-x-women-in-data-science-at-uk/challenges/01a0d987-0c41-12ea-13ac-5b85755dc2f3)

No complete event-specific policy for advance work, team eligibility/size, coding-assistant use, submission artifacts, or source-publication/license requirements was established by these pages. The registration destination required sign-in when accessed. Confirm missing details with organizers; do not infer that silence means permission. Local planning and workflow files already existed before this verification; disclose prior work if required.

## Project decisions for this category
These are our acceptance criteria, not additional rules attributed to MLH:

| ID | Requirement | Evidence needed before claiming readiness |
| --- | --- | --- |
| SW01 | An open-weight model is central to the running product | Live local generation of spirit responses from validated text or structured disturbance state; visible distinction between received input and generated response |
| SW02 | Preferred baseline is Qwen2.5-1.5B-Instruct, with a locally stored Q4_K_M artifact if supported | Exact origin, revision, filename/digest, quantization, runtime model identifier, and successful local load recorded in T09; no download performed by this requirements task |
| SW03 | Offline inference and speech | Local STT, LLM, TTS/voice/configuration, assets, and dependencies present; fresh startup with network unavailable; no cloud fallback |
| SW04 | Real one-way physical transport | Actual Uno R3 transmitter/receiver path transfers text; no second IR channel or network payload bridge; separate mock mode is explicit and off for acceptance |
| SW05 | Team MVP first; desktop enhancement deferred | Python sender CLI plus receiver service/local visual space run offline with clear diagnostics/startup/shutdown; shared desktop shell packaging follows later if selected. This is a team product choice, not a published award requirement. |
| SW06 | Reproducibility and provenance | Versions, model/voice/asset origins and licenses, required notices, preparation/startup instructions, and bounded verification evidence; review licenses before redistributing artifacts |
| SW07 | Honest submission and demo | Identify the original contribution, the model's essential role, known limitations, and development tools used; confirm any additional organizer submission rules |

A speech-to-IR plain-text demo is an engineering checkpoint. It is not the final award-targeted submission until substantive open-weight model behavior is integrated and verified. Codex/Gemini used during development do not themselves satisfy SW01. Local Qwen response generation must not be replaced by prerecorded or fixed responses while being presented as live inference.

## Model provenance checked
Qwen's official [1.5B Instruct model card](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct) declares Apache 2.0 and exposes the [license file](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct/blob/main/LICENSE). Its official [GGUF repository](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF) also declares Apache 2.0 and documents quantized use. This supports choosing that candidate; it does not verify the artifact installed on a demo machine.

Do not treat the proposed 3B variant as license-equivalent: [Qwen's release documentation](https://qwenlm.github.io/blog/qwen2.5-llm/) identifies Qwen2.5-3B under its Research License. Prefer the 1.5B candidate unless a later task deliberately evaluates another exact model. No finding here establishes that every software component or voice uses the same license.

## Hardware update supplied by the user
The accessible computer is a demo laptop; the second is reported identical. Two Arduino Uno R3 boards are intended (user wording: "Uno 3"). Exactly one V1221 transmitter and one V1222 receiver are available. These are user-confirmed identities, not electronically detected parts. Local USB connectivity, physical pin labels, manufacturer documentation, voltage/current constraints, carrier behavior, and actual link timing remain untested. Do not reuse the earlier example TSOP38238 pinout as if it identified the V1222 module. [Arduino's official Uno R3 page](https://docs.arduino.cc/hardware/uno-rev3/) is the board reference; a primary module datasheet/pinout remains to be confirmed before wiring/firmware assumptions.

## Current status
Award description and preferred-model license metadata checked; design aligned with the published category. Runtime implementation, offline acceptance, full software-license inventory, physical transfer, second-machine environment, and remaining organizer policies are pending. Stop after this T01 update; T02 requires a separate request.
