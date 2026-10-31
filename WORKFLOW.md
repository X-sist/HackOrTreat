# HackOrTreat: prompt, build, review

## Start in Codex
Open this repository in Codex desktop or VS Code with Codex. Prompt normally: "Build [feature]" or "Fix [bug]." AGENTS.md defines the workflow. For an existing session, say "Read AGENTS.md and use this workflow for my next request."

## Start in ChatGPT desktop
Paste DESKTOP-INSTRUCTIONS.md into your project's instructions once, or into a chat at the start. ChatGPT can prepare the task; access to your local repository is not implied. Copy its implementation handoff into Codex opened on this repo. For accurate continuation, attach or paste the current task handoff and relevant files when the chat cannot read them.

## Review in Antigravity
Open the same repository and select Gemini. After Codex finishes, paste its review prompt. Gemini reads AGENTS.md and the task handoff, inspects the implementation, and responds with findings without editing source code. Paste that response back into Codex with: "Verify these findings, fix confirmed issues, and rerun relevant checks."

This setup does not send messages between applications or consume Gemini usage automatically. Review is a manual handoff. Instructions guide behavior; they are not an operating-system read-only enforcement mechanism.

## Task handoff format
Codex creates `docs/ai/tasks/<unique-task-id>/handoff.md` for each meaningful completed task. Use a descriptive identifier with a timestamp or unique suffix; never overwrite another active task.

Include:
- Goal and acceptance criteria.
- Scope and assumptions.
- Starting commit, current commit, and whether changes are committed or uncommitted.
- Exact changed files, including new/untracked files. Note pre-existing changes and attribution limits.
- Short implementation summary.
- Exact verification commands, outcomes, and relevant failure details. Explicitly list important checks not run.
- Known limitations and focused reviewer questions.
- Review status: pending, findings received, or fixes verified. No findings received is not a pass.
- A self-contained prompt for Gemini, naming this handoff and the review target. For uncommitted changes, direct Gemini to inspect both staged and unstaged diffs plus listed untracked files. For committed changes, supply verified base and head IDs. Freeze edits during review; record the reviewed state and do not silently review a moving target.

Keep the handoff short. Do not paste conversation history, dependency lockfiles, credentials, or the entire repository into it. Pause new edits until the review finishes. Git diff alone misses untracked files and can include pre-existing changes: use the file list and attribution notes.

## Review prompt
Use REVIEW-PROMPT.md if you need to start a review manually. Replace its placeholder with the exact handoff path.

## Current setup

See MULTI-AGENT.md for task sizing, ownership, shared state, review validity, and the automation upgrade path. Do not load that guide for trivial edits.
Installed in the local HackOrTreat repository. No application source, test suite, provider login, or automatic agent bridge is created by this setup. Commit or push these instruction files when you want to share them; installation itself does neither.

## Documentation
- Codex instructions: https://learn.chatgpt.com/docs/agent-configuration/agents-md
- Antigravity rules: https://antigravity.google/docs/rules/
