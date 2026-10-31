# CS Major 2 workspace — @Xsist

Laptop 2 only: serial input, validated plain text, local Qwen, Piper/effects and local Ouija UI. Import shared/js/contract.mjs and shared/generated/protocol.mjs; isolated Python audio helpers may use shared/python. No sender imports or Arduino firmware edits.

Branch: `receiver/<task-id>-<short-description>`. Own clone/worktree; never point multiple writers at the same checkout. Start from current main after the collaboration baseline is merged. Read TASKS.md, then implement one task. Work can proceed against shared fixtures before the other components exist. Ordinary PRs modify only `receiver/` except its integration-owned contract.lock.json. Root docs/contracts require a separate `integration/` PR.

Run from repository root:
```
python tools/check_repo.py
python tools/validate_protocol_vectors.py
python tools/check_repo.py --role receiver --base origin/main
```
The last command checks committed branch changes; inspect `git status --short` as well for unstaged/untracked work. It is not a substitute for component tests or a required GitHub check. First implementation task configures the component runtime/dependencies; this skeleton is not a working app. See root WORKFLOW.md for locks, review and integration.
