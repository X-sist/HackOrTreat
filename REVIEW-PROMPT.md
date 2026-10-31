Review HackOrTreat using Gemini as the independent reviewer. Read AGENTS.md and the task handoff at:

[Replace with component/handoffs/<unique-task>.md or docs/ai/tasks/<integration-task>/handoff.md; specify firmware, sender, receiver or integration role.]

Inspect the specified changes and enough surrounding code to assess correctness against the acceptance criteria. Include the new/untracked files listed in the handoff. Respect notes about pre-existing user changes. Verify that the current state matches the review target; report any mismatch before drawing conclusions.

Check scoped ownership, shared contract revision/consumer pins, generated constants, event fixtures and dependency locks. Read WORKFLOW.md and the selected component's AGENTS.md. Distinguish mock checks from actual hardware, local inference and offline readiness. Do not start the next task or assume other teammates' progress.

Do not edit source or tracked project files. Prefer read-only checks. Report actionable correctness, regression, security, or missing-requirement issues, not style preferences. For each finding give severity, file and line, triggering scenario, practical impact, suggested correction or focused test, and whether the finding is confirmed or suspected. Clearly state which checks you actually ran and what remains unverified.

Return a concise report in chat for me to paste into Codex. If there are no actionable findings, say so with the scope and verification limits. Do not mark checks passed unless you ran them.

Record the reviewed commit or file hashes from the handoff. Give each finding a stable ID such as R1 or R2, plus severity, file/line, evidence, trigger, impact, and a suggested fix or test. Return status as findings, no-actionable-findings, or incomplete; these are distinct outcomes. Keep findings independent of the author's implementation narrative. If asked to re-review fixes, focus on prior finding IDs and changed behavior rather than restarting a broad review.
