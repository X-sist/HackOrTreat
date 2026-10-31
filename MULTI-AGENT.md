# Agent coordination
Human ownership is defined in root AGENTS.md and WORKFLOW.md. Software agents stay inside the selected human workstream; do not automatically create agents/chats or contact teammates. One implementer and one independent reviewer normally suffice. Delegation requires task authorization and an actual available tool.

If authorized parallel writers are useful, give each an isolated worktree, bounded files/task and acceptance criteria. Avoid overlapping edits even inside a component. One coordinator integrates and verifies; worker checks do not replace integrated checks. Workers update separate handoffs rather than a common status file.

Gemini review receives requirements, exact diff/files, shared contract revision and actual test results. Return actionable findings with IDs/evidence; Codex confirms and fixes them. Do not review as passed after a timeout or provider failure. Later relevant changes make earlier reviews stale. Default one pass; re-review only substantial fixes or unresolved questions. No automatic provider bridge is configured.
