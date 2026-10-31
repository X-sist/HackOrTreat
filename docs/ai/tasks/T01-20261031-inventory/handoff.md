# T01 handoff: inventory only

## Goal and acceptance
Inventory accessible hardware, OS, installed tools/models, and supplied official rules. Save observations, evidence, unknowns, and blockers without installing or implementing anything. Inventory is complete; device readiness and award eligibility remain unverified.

## Scope and repository state
- Repository: HackOrTreat, local checkout under `<REPO_ROOT>`.
- Starting commit: `107826d7d84a1379e995e531d4fb665ffdc67387`.
- Starting working tree: clean according to `git status --short`.
- No commits, pushes, stashes, resets, installations, or app implementation performed for T01.
- Initial T01 changed files: `TASKS.md` (T01 status, status introduction, and evidence link), this handoff, and `docs/ai/tasks/T01-20261031-inventory/inventory.md`. Both report files are new/untracked at creation.

## Findings and checks
Read inventory.md for bounded evidence. Confirmed local Windows 11 Pro / Dell i5-1334U / nominal 32 GB machine, Node 24.15.0, npm 11.12.1, Python 3.14.4, Git 2.54.0, VS Code 1.144.0, and Antigravity 2.28.2. No serial device was enumerated. Proposed model/voice files and relevant tools were not found in the inspected locations. Those are bounded observations, not global absence claims.

Read-only system/device/registry/package/file checks completed; report copies and task status are verified during installation. No app test suite or package manifest exists. Hardware transmission, microphone capture, playback, inference, offline startup, model licensing, second-machine inventory, and hackathon eligibility were not tested or confirmed.

T01 update: user supplied event link and Uno R3/V1221/V1222 identities, confirmed this demo laptop, and reported the second identical. Public category and model provenance sources are checked in SOFTWARE-REQUIREMENTS.md. Physical module documentation, second-machine environment, runtime artifacts, and additional organizer policies remain unresolved. T02 can use Uno R3 as the target while keeping physical link limits provisional.

## Confirmation update scope
Updated PROJECT-BRIEF.md, AGENTS.md, DESKTOP-INSTRUCTIONS.md, TASKS.md, inventory.md, and this handoff; added SOFTWARE-REQUIREMENTS.md. Changes record user-confirmed identities, verified sources, preferred model provenance, and a required open-weight runtime milestone. No source code, install, or T02 work. Existing changes before this update were TASKS.md and the untracked docs directory.

## Review
Status: pending. No Gemini run was invoked. Review target is the confirmation-update files listed above. No prior pending review can validate their revised contents. Record current commit and hashes below to identify the inventory and roadmap version; this handoff's own hash is intentionally omitted to avoid self-reference.

Ready-to-paste Gemini prompt:

> Review T01 only in HackOrTreat. Read AGENTS.md, PROJECT-BRIEF.md, SOFTWARE-REQUIREMENTS.md, and docs/ai/tasks/T01-20261031-inventory/inventory.md plus this handoff. Check the sourced category/software requirements and supplied hardware updates. Inspect the TASKS.md T01 status change. Check that claims distinguish direct observations, bounded searches, user proposals, and unresolved facts. Flag unsupported readiness, eligibility, model availability, or hardware claims. Do not edit files or install/run models. Return concise findings with stable IDs and evidence, or no actionable findings with verification limits. Do not start T02.

Next suggested task: T02 only. Await a separate user request.

## Recorded review target
Current commit: 107826d7d84a1379e995e531d4fb665ffdc67387
SHA-256 SOFTWARE-REQUIREMENTS.md: 9CA3532E2C1173284429E06584A5F0F1A90CA944A52184B29C1BE857CFA3547A
SHA-256 PROJECT-BRIEF.md: DC86482F9D47F9C45B7A5A113E57F388CFE4AE67780B909EF06B60870AD78A0C
SHA-256 AGENTS.md: 811197163DB123AF9DDE827514A036BCFB92E3B4F2125CC762FD7010BF191FE8
SHA-256 DESKTOP-INSTRUCTIONS.md: B724303548666E32574075ECE381D8E259C799BFD56ADCD906935726189C9A38
SHA-256 TASKS.md: 5F1BA37A74DDB62DD3D2164310541D241AA84211EE6705A300FA3277C905CCFB
SHA-256 docs\ai\tasks\T01-20261031-inventory\inventory.md: D398D9FB59B506A903C1B5697C83C47C72C311A12F92976EF0CEEC890B63A65A
