# CS Major 1 workspace — @Aiden360-stack

**C1-02 CLI is implemented; your live offline microphone check is pending.** See [CLI.md](CLI.md) for the start command and Enter-to-record/stop controls. Current branch: `sender/C1-02-microphone`, in your usual HackOrTreat repository, including the uncommitted C1-01 work. C1-03 now adds the serial adapter and manual simulator; no other component changes.

**C1-03 is implemented; Gemini review is pending.** See [SERIAL.md](SERIAL.md) for manual text and simulated Arduino scenarios. This does not complete C1-02 live microphone acceptance or start C1-04.

**C1-01 is prepared.** Read [SETUP.md](SETUP.md) for the two local verification commands and offline preparation details. The prepared runtime and C1-02 CLI are now together on `sender/C1-02-microphone` in this repository. Model files, wheel cache and the environment are local/ignored; they do not arrive through Git alone.

Laptop 1 only: offline Whisper, Python microphone/transcript CLI, normalization and paced USB serial output. Import shared.python.contract and shared.generated.protocol. No receiver, model-response, audio-output, Electron or firmware dependencies.

Branch: `sender/<task-id>-<short-description>`. Own clone/worktree; never point multiple writers at the same checkout. Start from current main after the collaboration baseline is merged. Read TASKS.md, then implement one task. Work can proceed against shared fixtures before the other components exist. Ordinary PRs modify only `sender/` except its integration-owned contract.lock.json. Root docs/contracts require a separate `integration/` PR.

Run from repository root:
```
python tools/check_repo.py
python tools/validate_protocol_vectors.py
python tools/check_repo.py --role sender --base origin/main
```
The last command checks committed branch changes; inspect `git status --short` as well for unstaged/untracked work. It is not a substitute for component tests or a required GitHub check. First implementation task configures the component runtime/dependencies; this skeleton is not a working app. See root WORKFLOW.md for locks, review and integration.
