# Team workflow cleanup handoff

## Result and scope
Reorganized the shared repo for three independently owned workstreams and one integrated product. Prepared against local commit `97effe9f2f6cf23b895d50ec1ef8e3f5cd78083e`. At start, six root instruction/roadmap files were already modified, and CS1-SENDER.md, T02 protocol/vectors/handoff and tools/ were untracked. Those existing contents were preserved as input to the cleanup; no user work was reset, stashed or deleted. The old roadmap is preserved under docs/reference/previous-roadmap.md as historical context.

Roles supplied by user: @Aiden360-stack sender/CS1, @Xsist receiver/CS2, @volyxge firmware/CE. The user did not select a sole shared-contract approver; shared paths request all three through prepared CODEOWNERS, while an integration owner is chosen per integration PR. Handles are recorded as supplied, not verified account/write access.

## Changes
- Replaced duplicated workflow instructions with root entry points and per-component AGENTS.md, README.md, TASKS.md, dependency/config placeholders and artifact manifests. Normal component work no longer edits a shared task tracker.
- Added shared contract source, semantic digest and three consumer pins; generated Python/JS/C++ constants and common Python/JS boundary helpers. Existing T02 packet bytes and event examples unchanged; known v1 event validators explicitly reject unknown extra fields.
- Added immutable host constants, event fixtures, owner scope/dependency/artifact checks and meaningful negative regression tests. Preserved the original T02 conformance checker/vectors.
- Added folder CODEOWNERS, component-author/branch scope check, PR template and prepared GitHub workflow for integrated compatibility/ownership plus component-owned Windows verify.py hooks. Shared changes use integration/ branches. No GitHub configuration or review requests were actually sent.
- Each language/component owns isolated dependencies and local storage; Python/firmware runtimes remain explicitly unconfigured until implementation tasks resolve exact compatible versions. Receiver Node baseline is pinned to observed Node24.15.0/npm11.12.1, with a real empty npm lock generated offline. No application runtime packages/models were installed.
- Updated WORKFLOW.md with branch/scope rules, shared-change process, checks, offline preparation, and required GitHub activation steps. integration/README.md documents staged assembly of one product and the same clean release commit/contract digest on both laptops.

All C1/CE/CS2 implementation tasks remain pending. No firmware, speech pipeline, model adapter, product audio or UI was built. Shared helpers are contract infrastructure, not proof of those implementations.

## Verification performed in isolated preparation copy
- `python tools/generate_contract.py --check`: generated outputs and all consumer pins match.
- `python tools/check_repo.py`: shared event vocabulary, T02 metadata, ownership layout, CODEOWNERS mapping, pin/lock rules and artifact metadata pass.
- `python tools/validate_protocol_vectors.py`: 15 packet cases / 8 serial cases pass fixture checks.
- `python -m unittest discover -s tests -v`: 10 tests pass, including rejection of unpinned/unhashed dependencies, Python/npm lock mismatches, stale generated output/consumer pins, cross-owner edits/renames, invalid sender input and immutable constants. Fixtures run as subtests.
- `node tools/check_js_contract.mjs`: agrees with Python expectations on all 29 valid/invalid event examples.
- `python tools/run_component_checks.py firmware` and sender/receiver: explicitly report scaffold-only; none is misreported as an implemented component test suite.
- Python compilation and initial workflow YAML parsing passed; matrix job was then added and final YAML parsing is repeated at installation.

Initial temporary-directory tests hit this execution environment's temporary-folder permissions; tests were changed to use explicitly repo-local ignored scratch storage, then passed. No ignored scratch files are included in the install.

Not run: native C++ header compilation (no local g++/clang++ discovered), GitHub Actions, actual PR review requests, live branch protection, full Python wheel resolution, firmware build/SRAM, microphone/serial/IR/model/audio/UI or offline demo. Prepared CI includes a native header smoke test, distinct from a real Uno firmware build.

## Operational limits
Folder separation minimizes normal conflicts, but cannot guarantee zero conflicts. CODEOWNERS lists owners; it does not itself enforce reviews, all-listed-owner approval, or write permissions. Prepared scope CI depends on named branch prefixes and supplied account identities. Integration PRs intentionally permit shared changes and need agreed owner review; required checks and up-to-date/merge-queue rules must be activated on GitHub after publication. Never require a sole author to approve their own owner review without backup owners.

The setup is local and uncommitted/unpushed. Teammates cannot use these files from GitHub until this baseline is reviewed and shared. Use separate clones/worktrees, not a multi-writer synced checkout. No changes to repository permissions were attempted.

## Independent review
Pending; no Gemini call was made. Review this integration diff and the installed file/hash manifest, including new files. Do not treat prior T01/T02 review hashes as covering these revised instructions/contracts.

Ready-to-paste prompt:

> Review the TEAM-20261031-workflow integration changes in HackOrTreat. Read AGENTS.md, WORKFLOW.md, shared/contract.json, consumer pins and this handoff. Inspect generated outputs, Python/JS boundary helpers, fixtures/tests, ownership/dependency checks and GitHub workflow. Check for incompatible field meanings, missing drift detection, cross-owner merge hazards, Python-vs-JS validation disagreement, misleading readiness claims or CI gaps. Preserve the three-person majors table and one-task-per-request workflow. Do not edit files, install tools/models, contact teammates, or implement application tasks. Return actionable findings with stable IDs and evidence, or no actionable findings with verification limits.

Final self-review added cross-language cases for array-valued error codes and integral JSON numbers (1 versus 1.0). Both validators agree; booleans remain invalid numeric protocol fields.
