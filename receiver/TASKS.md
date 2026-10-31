# CS Major 2 tasks — @Xsist
Only this owner updates these statuses. One task per prompt. Ready next: **T03**, using shared event fixtures without waiting for hardware.

| ID | Status | Dependencies | Scope/evidence |
| --- | --- | --- | --- |
| T03 | pending | T02 design | Serial stream parser/plain-text CLI or local display, shared JS event validator, fixture replays, bounded reads/error states. Pin any dependencies in this folder. |
| T09 | pending | T03 | Verify exact preferred local Qwen1.5B artifact/license/digest and substantive offline inference; use validated messages/disturbance context. |
| T10 | pending | T09 | Local Piper audio and optional effects; isolated audio Python environment/pins if used; bounded queue and honest errors. |
| T11 | pending | T03/T09 | Local Ouija UI/animation with offline assets, response/input separation and readable real transport errors. |

Node baseline is 24.15.0 / npm 11.12.1 (observed on inventoried laptop); verify on receiver machine. `npm ci --prefix receiver` uses the local lock, never a root manifest. No network or model calls in fixture checks. T09 must verify real local inference separately. Shared desktop shell enhancement remains deferred.
