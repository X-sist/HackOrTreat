# CE major workspace — @volyxge

Both Uno R3 firmwares, V1221/V1222 wiring verification, IR transport and physical recovery. Use shared/generated/protocol.h; do not redefine protocol constants. Shared generated files are integration-owned. Document a reproducible way to expose the header to the Arduino build without maintaining another hand-edited copy.

Branch: `firmware/<task-id>-<short-description>`. Own clone/worktree; never point multiple writers at the same checkout. Start from current main after the collaboration baseline is merged. Read TASKS.md, then implement one task. Work can proceed against shared fixtures before the other components exist. Ordinary PRs modify only `firmware/` except its integration-owned contract.lock.json. Root docs/contracts require a separate `integration/` PR.

Run from repository root:
```
python tools/check_repo.py
python tools/validate_protocol_vectors.py
python tools/check_repo.py --role firmware --base origin/main
```
The last command checks committed branch changes; inspect `git status --short` as well for unstaged/untracked work. It is not a substitute for component tests or a required GitHub check. First implementation task configures the component runtime/dependencies; this skeleton is not a working app. See root WORKFLOW.md for locks, review and integration.
