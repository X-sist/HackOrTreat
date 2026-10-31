# Joining the three components

Use this folder for coordinated integration PRs. Choose one integration owner per milestone/PR; routine work stays in firmware/, sender/ or receiver/.

1. Land this collaboration baseline first. All teammates branch from that same main commit and use the same shared contract digest.
2. CE verifies the board-side serial events and real IR. CS1 verifies Whisper/CLI/serial. CS2 verifies receiver/model/audio/visuals. Each records actual checks and limits in their own folder.
3. Integrate manual text -> actual IR -> received text (T06), then real speech (T08), then local model/audio/visuals (T12). Component unit tests do not establish end-to-end operation.
4. For the demo both laptops use the same clean commit/tag and compare shared/contract.lock.json. Install each role's exact dependency lock and prepare matching artifact digests. No downloads during the offline demonstration.
5. Record startup commands, versions/artifacts, fresh-process offline evidence, real obstruction/recovery and timings. Never present mocks as live hardware or inference.

For protocol changes use one integration PR updating source, fixtures, generated constants and all consumer pins. Get affected owners' agreement, then update feature branches from main. No private compatibility shim or silent protocol fork. See root TASKS.md for team milestones and component TASKS.md files for implementation.
