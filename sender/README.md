# CS Major 1 workspace — @Aiden360-stack

Laptop 1 only: offline Whisper, Python microphone/transcript CLI, normalization and paced USB serial output. Import shared.python.contract and shared.generated.protocol. No receiver, model-response, audio-output, Electron or firmware dependencies.

Branch: `sender/<task-id>-<short-description>`. Own clone/worktree; never point multiple writers at the same checkout. Start from current main after the collaboration baseline is merged. Read TASKS.md, then implement one task. Work can proceed against shared fixtures before the other components exist. Ordinary PRs modify only `sender/` except its integration-owned contract.lock.json. Root docs/contracts require a separate `integration/` PR.

Run from repository root:
```
python tools/check_repo.py
python tools/validate_protocol_vectors.py
python tools/check_repo.py --role sender --base origin/main
```
The last command checks committed branch changes; inspect `git status --short` as well for unstaged/untracked work. It is not a substitute for component tests or a required GitHub check. First implementation task configures the component runtime/dependencies; this skeleton is not a working app. See root WORKFLOW.md for locks, review and integration.
