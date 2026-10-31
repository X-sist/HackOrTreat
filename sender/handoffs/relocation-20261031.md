# Sender checkout relocation

The user requested that the sender work appear in the usual Source Control repository and be accessible to Antigravity.

Current repo: C:/Users/aiden/OneDrive/Documents/GitHub/HackOrTreat
Current local branch: sender/C1-02-microphone

The usual repo was clean. The sender branch was released from the separate worktree, checked out here, and fast-forwarded to current main (1f568203870a92f3998625f80d2ed319f26010c9). Sender source files were identical between the two committed bases. Uncommitted sender changes and local model/wheel/sample caches were copied here and hash-verified. The Python environment was recreated here from the exact offline lock rather than moving a path-bound venv.

The old separate checkout remains detached with its original uncommitted contents as a backup; do future work in this usual repository. No commits/pushes or remote changes were made. Prior task handoffs describe their original execution context; the C1-02 review location is updated to this repository.

Source Control now sees the branch and sender changes directly. Models, wheels and environment remain ignored by Git. Live microphone testing and Gemini review remain pending.

Verified at the usual location: all 19 sender tests pass, pip check/imports pass, shared compatibility check passes, and CLI local-file inference again produced 'Spirit, what is your name?'. No microphone recording was performed. Git confirms this usual checkout is on sender/C1-02-microphone with only sender source changes.

