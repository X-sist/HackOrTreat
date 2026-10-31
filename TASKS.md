# Team task index
This is an integration-owned index, not a tracker all three people edit. Component files below are the sole live task-status sources. Prior broad roadmap: docs/reference/previous-roadmap.md (historical only).

| Person | Own workspace / task tracker | Next independent task |
| --- | --- | --- |
| @volyxge — CE | [firmware/TASKS.md](firmware/TASKS.md) | T04: Tx firmware/hardware validation |
| @Aiden360-stack — CS1 | [sender/TASKS.md](sender/TASKS.md) | C1-01: offline Whisper preparation |
| @Xsist — CS2 | [receiver/TASKS.md](receiver/TASKS.md) | T03: event parser/plain-text output |

All can proceed independently against the v1 contract/fixtures. A generic "next task" uses the selected component or branch prefix, never another person's queue. This chat's user works as sender; the shared root agent instructions do not force every teammate into that role.

Shared completed design/inventory: T01 (unknowns recorded) and T02 (design checked, physical validation and Gemini review pending). Evidence remains under docs/ai/tasks/. No application task has been implemented by the collaboration setup.

Integration milestones (one agreed integrator updates these only):

| ID | Status | Evidence needed |
| --- | --- | --- |
| T06 | pending | Sender manual text -> CE physical IR -> CS2 received plain text |
| T07 | pending | C1-01/C1-02 real offline Whisper + CLI evidence |
| T08 | pending | Sender speech -> actual two-machine text transfer |
| T12 | pending | T08 + live local Qwen/audio/visual receiver integration |
| T13 | pending | Fresh-process full offline team rehearsal, real beam obstruction, provenance and rules review |
| U01/U02/U03 | deferred | Optional later shared desktop design/shell/packaging; no CLI prerequisite |

For integration choose an `integration/<milestone>` branch and review the changed interfaces with affected owners. Never mark shared milestones complete from mocks alone.
