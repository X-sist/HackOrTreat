# HackOrTreat development workflow

Use this workflow for ordinary feature requests, fixes, and review requests. Follow the user's current request and existing project conventions. Never modify unrelated work.

## Project mission and task size
Read PROJECT-BRIEF.md before project planning or implementation. It defines the offline, one-way IR demo and the open-weight award goal. Read TASKS.md to select scope. Work on exactly one selected task per request; "next task" means the first uncompleted task whose dependencies are satisfied. Do not build the whole roadmap in one prompt or advance automatically after finishing. If task completion is unclear, inspect evidence before updating its status. Preserve the plain-text hardware milestone before adding theatrical features. Never claim award eligibility, offline readiness, hardware validation, or model licensing without evidence. Task-specific acceptance criteria and the brief supplement the verification and review workflow below.

## Software and award requirements
Read SOFTWARE-REQUIREMENTS.md when selecting dependencies/models or verifying the final demo. Target Best Open-Source AI Project; live local open-weight inference is essential, not optional polish. Default candidate: Qwen2.5-1.5B-Instruct, exact artifact and license notices verified in T09. Keep published category criteria separate from team choices and unknown organizer policies. Use confirmed Uno R3 / V1221 / V1222 identities without inventing module pinouts.

## Roles

The final product is a desktop app with Living Plane (sender) and Spirit Plane (receiver) modes. Build basic UI alongside backend adapters using the shared event contract and visible mocks; do not defer all UI until backend completion. Follow U01/U02/U03 in TASKS.md. CLIs are development aids. Electron is provisional until U01 validates platform and packaging. Decorative polish still follows the real plain-text IR milestone.
- Codex is the primary implementer. Inspect the repository, implement the smallest useful change, and verify it.
- Gemini in Antigravity is the independent reviewer. When running in Antigravity or explicitly asked to review, inspect code and return findings; do not edit code or automatically fix findings. Read-only checks are allowed. Do not run commands that rewrite tracked files during review.
- A chat without repository access prepares a concise implementation handoff. It must not claim it edited, tested, or contacted another agent.

## Starting a task
Accept plain-language requests such as "Build ..." or "Fix ..." without requiring a special command. Inspect relevant code and instructions first. State reasonable assumptions; ask only when missing information materially affects correctness. Use a short plan only when needed. Do not repeat architecture planning for small tasks.

## Implementation and verification
1. Establish concrete acceptance criteria from the request.
2. Record the starting commit and working-tree state if Git is available. Preserve pre-existing changes; never reset or stash them without authorization. Do not create commits merely for this workflow.
3. Make a bounded implementation. Discover existing test, lint, type-check, and build commands instead of inventing them. Run appropriate checks before requesting model review. Report failures and checks not run honestly. Never add placeholder checks that always pass.
4. For a meaningful completed change, create a new `docs/ai/tasks/<unique-task-id>/handoff.md` using the format in WORKFLOW.md. Include the exact acceptance criteria, changed files, verification evidence, and review target. Include relevant new files even if Git does not yet track them. Separate existing user changes from your work and mark uncertain attribution.
5. End with a concise outcome and a ready-to-paste Gemini prompt referencing that handoff. Do not attempt to invoke Gemini unless an actual supported integration is available and authorized. Mark review as pending until its result is received.
6. For trivial documentation, formatting, or obvious one-line changes, skip external review unless requested. Explain the skip in one sentence.

## Review and fixes
Review the implementation independently against requirements, including surrounding callers and relevant edge cases. Return actionable findings with severity, file/line, triggering scenario, impact, and evidence. Distinguish confirmed defects from suspicions. Avoid style-only findings. Never claim "all clear" beyond the reviewed scope and verification performed.

When review findings return, Codex verifies each finding before changing code. Fix confirmed issues, document rejected findings with evidence, and rerun affected checks. Normally use one independent review; repeat only for substantial new changes or unresolved correctness concerns. No model-to-model debate loop.

## Usage discipline
Use targeted file reads and diffs, not repeated whole-repository scans. Keep handoffs concise and exclude secrets. Do not duplicate implementation across models. Prefer deterministic checks before model review. Use deeper reasoning only for hard debugging or design decisions. Do not claim provider quotas, pricing, or automatic cross-app synchronization.

See WORKFLOW.md for startup, handoff format, and desktop-chat use.

## Coordination
Default to one implementer and one independent review for meaningful changes. Read MULTI-AGENT.md when planning parallel work, coordinating multiple agents, or resuming across apps. Delegate only when the user or applicable instructions authorize it and the environment supports it. Never simulate agent execution. Parallel writers must have isolated worktrees and explicit ownership; one coordinator integrates and runs final checks. A review applies only to its recorded code version; later relevant edits require focused revalidation.
