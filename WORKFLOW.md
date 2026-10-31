# Three teammates, one product

## Start here
Each person uses their own clone (or separate worktree on one machine). Do not use a single OneDrive-synced checkout as a multi-writer folder. Shared Git history combines the product; environments, serial devices, caches and app state stay local.

| Owner | Folder | Branch prefix | Component task file |
| --- | --- | --- | --- |
| @volyxge | firmware/ | firmware/ | firmware/TASKS.md |
| @Aiden360-stack | sender/ | sender/ | sender/TASKS.md |
| @Xsist | receiver/ | receiver/ | receiver/TASKS.md |

1. After the collaboration baseline lands, update your clean main (`git switch main`, `git pull --ff-only`), then create your component feature branch. Preserve/commit your own uncommitted work before switching. No teammate feature-branch merges or force pushes.
2. Implement one task inside your folder, including tests, manifests/locks, config examples and unique handoffs. The root TASKS.md is an integration index; update only your own task file.
3. Run shared checks below and your real component tests. Open one component-scoped PR, review with Gemini if useful, fix confirmed issues, and merge only after required checks/reviews. CI validates the integrated merge result on PRs.
4. Bring main into your next branch before starting the next task. Only an intentionally coordinated integration PR edits shared interfaces. Nobody routinely resolves conflicts in another person's implementation.

## Shared boundary, not shared variables
`shared/contract.json` is the machine-readable protocol source. It drives generated Python/JS/C++ constants and consumer pins. `docs/PROTOCOL.md` defines framing/state-machine behavior; `docs/protocol-vectors.json` and `shared/fixtures/events.json` are common examples. Hosts reuse shared boundary helpers and validate received data. Firmware includes the generated header. Consumer contract.lock.json files all pin the same semantic contract digest. Keep source and fixtures together in a reviewed integration change; generated files are never hand-edited.

No cross-imports between sender/receiver/firmware, private field renames, hidden compression, network shortcuts or mutable data file passed between laptops. Serial payload/events are the only live inter-component boundary. Match baud, limits, IDs and event names through shared constants. Ports, microphone IDs and model paths live in ignored per-component config.local.json. Distinguish local sent status, remote received text, and model output.

Fixtures let CE implement firmware, CS1 implement transcription/serial and CS2 implement receiver/model/visuals simultaneously. The current product is a CLI/service team MVP; a shared desktop shell remains optional later work.

## Dependencies and artifacts
There is no root dependency manifest or shared virtualenv. A component owns its complete dependency files and local environment. Shared boundary tooling uses only standard Python/Node libraries.
- Sender Python: sender/requirements.in lists exact direct pins. sender/requirements.lock pins all transitive dependencies with SHA-256 hashes; sender/runtime.json records the tested exact Python version. Own sender/.venv. Once selected, install with that interpreter: `python -m pip install --require-hashes -r sender/requirements.lock`. For demo preparation cache matching wheels, then use --no-index/--find-links offline. Empty files currently mean unconfigured, not ready. No dependencies were installed by this setup.
- Receiver Node: receiver/package.json plus package-lock.json; exact dependency versions, Node 24.15.0 and npm 11.12.1 baseline. Use `npm ci --prefix receiver`, not a global install/root lock. Receiver Python audio, if chosen, has its own receiver/audio/.venv, hashed requirements and exact runtime, never sender's environment.
- Firmware: firmware/dependencies.json records exact Arduino CLI/core/IRremote versions and Uno FQBN when selected. Both boards use those pins. No .ino accepted by the scaffold check until tooling/libraries are configured. Actual reproducible build and SRAM checks belong to CE.
- Each component owns artifacts.json: exact source/revision/license/digest/local path for models/voices/assets. Large binaries go into ignored component storage. Paths/ports may differ between laptops; protocol field meanings and artifact identity must not. Missing artifacts in CI are not offline readiness; actual preparation and live tests remain mandatory.

Static lock checks catch missing pins/hash metadata and manifest mismatches. They do not resolve dependencies, prove wheel compatibility or verify a missing model. First implementation tasks must resolve/install/test their complete lock in a clean environment. A shared contract is how different languages agree; they do not need the same library stack.

Each component adds its own `verify.py --ci` when introducing code. The prepared Windows CI matrix invokes that hook using the component's pinned Python (sender/runtime.json or receiver/audio/runtime.json) and the Node baseline. Hooks install only owner-local locked dependencies and run bounded tests without hardware, secrets or model downloads; physical/model/offline tests stay explicit manual evidence. Firmware hook installs its exact declared toolchain/core/libraries and builds both targets. No hook with code is a failing job; no implementation yet is explicitly reported as scaffold-only. This lets owners expand tests without editing the root workflow. These component jobs have not run on GitHub yet.

## Shared change procedure
Use integration/<task> for contracts, docs, CI/tools or a coordinated milestone. State the compatibility impact, update source/fixtures, run `python tools/generate_contract.py`, and commit all consumer pins/generated files together. Breaking field/byte changes require a new wire version and migration; compatible clarifications bump contract revision. If CE finds physical encoding infeasible, propose the change here before hosts assume a different format. Rebase/update existing feature branches onto the new main before integrating them; stale pins fail checks.

## Checks
From root, without hardware/models/network:
```
python tools/generate_contract.py --check
python tools/check_repo.py
python tools/validate_protocol_vectors.py
python -m unittest discover -s tests -v
node tools/check_js_contract.mjs
```
To inspect committed feature scope: `python tools/check_repo.py --role sender --base origin/main` (replace sender as appropriate). Also inspect git status for uncommitted/untracked work. Scope checks inspect renames as deletes/adds. These scripts validate collaboration/contracts, not app implementation or physical readiness.

## GitHub activation
Prepared `.github/CODEOWNERS` names the supplied handles; GitHub requires them to have write access. Ordinary PRs request their component owner; shared changes request all three. CODEOWNERS does not require all listed people to approve and does not prevent conflicts by itself.

After these files are reviewed, committed and pushed, enable the Actions workflow and protect main: require pull requests, dismiss stale approvals, require the `compatibility` and `ownership` checks, require the branch up to date (or a merge queue with checks rerun), and restrict direct/force pushes. Choose review counts that let the two other people review a component owner's work; CODEOWNERS cannot make an author approve their own PR. For shared integration PRs request affected owners explicitly. Ownership CI enforces folder scope and supplied branch-author mapping; integration branches intentionally allow coordinated cross-folder changes.

Also require `component (firmware)`, `component (sender)` and `component (receiver)` once the workflow is registered. Do not require the sole component author to approve their own CODEOWNERS review; use non-author reviews or add agreed backup owners if enforcing owner approval.

No GitHub permissions/rulesets were changed and nothing was committed/pushed by this setup. The files are not visible to teammates until shared through Git. Verify supplied usernames/write access before relying on automatic requests. Official references: [CODEOWNERS](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners), [workflow events](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows), [pip hash-locked installs](https://pip.pypa.io/en/stable/topics/secure-installs/).
