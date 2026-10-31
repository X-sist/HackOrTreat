# Shared, integration-owned contract
Source: contract.json (protocol constants, event fields/codes and roles). Generate with `python tools/generate_contract.py`; CI --check fails for stale outputs or consumer pins. Python, JS and Arduino consumers read generated/protocol.py, generated/protocol.mjs and generated/protocol.h. Do not hand-copy constants or modify generated files. contract.lock.json pins semantic JSON, ignoring platform line-ending differences.

team.json is the supplied human ownership mapping; check_repo.py verifies CODEOWNERS agrees with it. Handle syntax is checked locally, but account existence/write permissions have not been verified through GitHub.

Reuse Python shared.python.contract for SEND construction/event validation and JS shared/js/contract.mjs for events. Use fixtures/events.json and docs/protocol-vectors.json for independent implementations. Python helpers are imported from repo root; JS imports are relative to the repository, not an npm dependency. Firmware owner documents header include/build setup without a second maintained copy. No source import between component folders.

Host event validators intentionally reject extra fields in known v1 objects; unknown versions/events are local diagnostics, never model input. They validate complete decoded objects, not a serial stream; framing/timeouts remain component work. This tightens the explicit contract without changing existing T02 bytes/examples. Bump/version the contract deliberately for extensions. Physical encoding remains unverified.
