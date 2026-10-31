# HackOrTreat team instructions

Read WORKFLOW.md for collaboration and PROJECT-BRIEF.md / SOFTWARE-REQUIREMENTS.md for mission, offline acceptance and award evidence. Team goal: offline speech -> one-way real IR -> received text -> meaningful local open-weight spirit response. Hardware: Uno R3 pair, one V1221 Tx and one V1222 Rx; no remote ACK/network shortcut. No hardware/model/eligibility claims without evidence.

Select the human role from the request, branch prefix, or folder:
- `firmware/`: @volyxge, both Arduinos/IR (CE).
- `sender/`: @Aiden360-stack, Whisper/Python CLI/serial (CS1).
- `receiver/`: @Xsist, Laptop 2 serial/Qwen/audio/local visuals (CS2).
- `integration/` branch: coordinated shared contracts/configuration/tools/CI and team integration.

If role cannot be inferred, clarify it before implementation. This repo is shared by all three people; do not impose one person's default on the others. Read the chosen folder's AGENTS.md and TASKS.md. One selected task per request; "next" selects that owner's ready task. Do not auto-advance or implement another owner's queue.

Ordinary component work modifies only its folder, task status and unique handoffs. Component contract.lock.json files are integration-owned. No root manifests, global virtualenv, cross-component imports, shared mutable runtime data or shared task-status edits. Use shared/contract.json, generated constants, validators and fixtures; never copy or rename protocol fields privately. Contract revision/pin changes require one integration PR refreshing all three consumer pins and relevant tests together. Timing/physical behavior remain provisional until bench-tested.

Each person uses a separate clone/worktree and feature branch. Never reset/stash/discard unrelated work, force-push a teammate branch or merge their branch into your feature branch. Integrate through main. Do not create agents/chats, contact teammates, commit/push or alter GitHub settings without task authorization.

Codex implements and verifies; Gemini reviews meaningful diffs independently and returns evidence-based findings without editing source. No automatic provider bridge exists. Run component checks plus `python tools/check_repo.py`, `python tools/validate_protocol_vectors.py` and `node tools/check_js_contract.mjs` where available. Record real results and unavailable checks. Task handoffs live inside the owner's folder; shared setup/integration handoffs live under docs/ai/tasks/. Independent review remains pending until received. See MULTI-AGENT.md for agent-specific boundaries.
