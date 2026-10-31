# Efficient multi-agent coordination

## Default routing

| Task | Workflow |
| --- | --- |
| Trivial copy, formatting, or isolated obvious edit | Codex implements and checks; no external review unless requested |
| Ordinary feature or bug fix | Codex implements and checks; Gemini reviews once |
| Independent modules with agreed interfaces | When delegation is authorized, at most two implementation workers in separate worktrees; one coordinator integrates; Gemini reviews the combined result |
| Authentication, permissions, payments, migrations, destructive operations, or broad refactor | Agree on invariants first; stronger focused checks and review depth; do not add reviewers just to increase agent count |

Before parallelizing, compare the expected benefit with the cost of extra context, worktree setup, merge conflicts, and integration. Small or tightly coupled tasks stay sequential. This policy does not itself authorize creating user-visible chats, contacting services, or installing provider tools.

## Ownership and dependencies

One coordinator owns the task brief, interfaces, shared configuration, dependency manifests and lockfiles, integration, and final verification. Worker assignments specify acceptance criteria, owned files, excluded files, dependencies, and expected output. Workers receive only relevant context and report their changed files, checks, and blockers.

Use distinct branches/worktrees for concurrent writers. Never let two agents edit the same checkout concurrently. Do not assign dependent tasks in parallel until their interface is settled. A frontend worker and backend worker may proceed together after their API contract is agreed. Merge one worker at a time and check the integrated result. Worker tests do not establish that integration works.

Uncommitted instruction files do not automatically appear in a new worktree. Ensure each worker receives the applicable instructions and task brief explicitly without silently committing the user's files. If isolation is unavailable, serialize writes. Gemini can analyze settled requirements or propose edge cases while coding proceeds, but final code review waits for the completed review target.

## Compact task state

Keep `docs/ai/tasks/<task-id>/handoff.md` as the coordinator-owned source of truth. Add these fields to the normal handoff only for multi-agent tasks:
- Status: planned, implementing, ready-for-review, changes-requested, verified, or blocked.
- Coordinator and worker assignments with file ownership and dependencies.
- Acceptance criteria and decisions, including agreed interfaces.
- Review target: verified base/head commits for committed work; for uncommitted work, starting commit, exact file list, and SHA-256 hashes of reviewed file contents, including new files and noting deleted files.
- Review status: pending, findings, no-actionable-findings, incomplete, or stale. Record the target against which the result was issued.
- Findings by stable ID, evidence, disposition, and verification result.
- Next action and unresolved blockers.

Keep worker outputs in separate files if persistence is necessary. Only the coordinator updates shared task state, preventing a second coordination conflict. Do not create a separate global mutable state file. A chat without local access receives the current handoff explicitly; it cannot infer the latest state from an old conversation.

If reviewed files, relevant callers, interfaces, configuration, dependencies, or other behavior-affecting context change, mark the review stale and revalidate affected behavior. An unchanged diff summary or unchanged HEAD is not sufficient for uncommitted changes. Never call a run verified when required checks fail or review is incomplete.

## Context and usage budget

Start with one implementation and one review. Use a focused second pass only for substantial fixes or unresolved concerns. Do not automatically retry provider failures or start extra agents when quota is exhausted; retain the handoff and report the blocker.

Provide Gemini the acceptance criteria, exact review target, file map, and actual check outcomes. Let it inspect the code independently before reading extensive author rationale. Request at most the most important actionable findings first, with stable IDs and evidence. Do not suppress a critical finding to meet an output budget. Codex validates each finding and records accepted, rejected-with-evidence, or deferred decisions. Use a focused reproduction to resolve disagreement.

Measure a few real tasks: elapsed time, provider-reported usage if available, actionable findings, false positives, and integration rework. Keep parallelism only if those observations justify it. Agent count is not a quality metric.

## Automation upgrade path

Inspection on October 31, 2026 found Codex on PATH and the Antigravity desktop installation. No `agy` or `gemini` command was discoverable on PATH; no headless provider call or authentication test was performed. This does not establish that a CLI is absent everywhere.

Google documents `agy -p` for one-shot requests and JSON output. Once the official CLI is installed, authenticated, and verified locally, a coordinator could send a bounded review request and save the result without clipboard transfers. Validate supported flags against the installed version; do not treat the desktop executable as an equivalent headless interface.

A future bridge should select an available Gemini model explicitly, preserve existing permission settings, use an isolated review copy with source writes denied where supported, set a bounded timeout, validate process exit and JSON status, and attach the result to its exact code target. Authentication, quota, permission, timeout, or malformed-output failures mean review incomplete, never a pass. Do not enable blanket permission bypass. Keep manual review available.

No automatic cross-provider bridge, new CLI installation, login change, or background process is installed by this guide. A ChatGPT chat without repository/tool access continues to supply a handoff for Codex rather than claiming it executed the pipeline.

Official references:
- Codex worktrees: https://learn.chatgpt.com/docs/environments/git-worktrees
- Codex scripted execution: https://learn.chatgpt.com/docs/non-interactive-mode
- Antigravity headless execution: https://antigravity.google/docs/cli/headless/
