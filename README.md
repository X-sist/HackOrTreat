# HackOrTreat
An offline spirit-communication demo: Laptop 1 transcribes speech, an Arduino sends text over one-way IR, and Laptop 2 displays the received text and generates a local open-weight spirit response with audio/visuals. Target: Best Open-Source AI Project; full readiness/eligibility is not yet established.

**Start with [WORKFLOW.md](WORKFLOW.md).** Three independent workspaces, one versioned contract:

| Role | Owner | Start |
| --- | --- | --- |
| CE: both Arduinos/IR | @volyxge | [firmware](firmware/README.md) |
| CS1: Whisper/Python CLI/serial | @Aiden360-stack | [sender](sender/README.md) |
| CS2: receiver/Qwen/audio/visuals | @Xsist | [receiver](receiver/README.md) |

Contracts/constants/fixtures live under shared/ and docs/PROTOCOL.md. Each person edits their own dependencies, task file and handoffs. Root docs/CI/shared contracts change only in coordinated integration PRs. Each uses their own clone/environment; no cross-component source imports or shared mutable runtime state.

Current state: collaboration scaffolding and T01/T02 evidence only. Speech, firmware, model inference, audio and product UI have not been implemented. Hardware/offline behavior remains unverified. See [team milestones](TASKS.md), [project brief](PROJECT-BRIEF.md), and [software/award requirements](SOFTWARE-REQUIREMENTS.md).
