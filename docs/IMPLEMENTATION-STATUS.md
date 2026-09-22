# Implementation status

## Baseline

- Teammate base: `fd8af21b2512c0f91de5e5aecd2cf406f6094299` (`master`).
- Integration branch: `codex/chain-and-evidence`.
- Donor reference: `7630d83`; code is copied by module, never merged wholesale.
- Initial worktree: clean. No applicable `AGENTS.md` was present.

## T0 — clean baseline

Status: complete.

Initial observations before changes:

- Combined pytest collection stopped because the active Python environment lacked `web3`.
- Frontend `npm ci` could not use the user npm cache in the sandbox and left no usable Vite install.
- Both editable Python projects described package discovery from the wrong directory; the backend also depended on the unrelated distribution name `agent` instead of `waytoweb4-agent`.

Changes:

- Declared the actual `agent.*` and `backend.*` package layouts explicitly.
- Selected pytest importlib mode to avoid the two `tests` packages colliding.

Validation:

- `.venv` editable install succeeded; `agent` and `backend` import from this worktree.
- `python -m pytest --import-mode=importlib agent/tests backend/tests`: 104 passed.
- `npm ci` and `npm run build` in `frontend`: passed (npm reports one moderate and one high dependency advisory; no forced breaking upgrade applied).

## T1–T6

### T1 — contract and lifecycle

Status: complete.

- Added `intent-keccak-v1` canonicalization with exact cents, whole-second UTC expiry, ASCII leader IDs and a 10,000 USD cap.
- Replaced raw-Spec mint with prepare → hash-bound manual confirm → mint.
- Added UUID local identities, independent authorization/engine states, terminal stop flag, atomic ledger writes and request-id payload binding.
- Offline authorization uses `simulation_id`; transaction hash fields remain null.
- Updated prior backend tests to exercise the new API without removing their validation, engine, RedLine, face or reset coverage; added boundary/idempotency tests.

Validation: combined agent/backend suite: 109 passed.

### T2 — isolated chain bridge

Status: complete for offline/local-EVM scope.

- Added a Node 22 JSON-lines worker containing only intent verification and passport chain operations.
- Ported StrategyPassport v2 and exact cents handling; Python and Node independently verify a golden canonical-intent fixture.
- Added the Python bridge with a minimal environment allowlist, request correlation and timeout/uncertain errors.
- FastAPI can use the local backend for prepare → confirm → mint/readback → revoke; duplicate mint requests reuse the recorded transaction.
- Public-chain mode remains intentionally disabled in the worker and no public transaction was broadcast.

Validation: Node chain tests 2 passed; combined Python suite 112 passed, including FastAPI → Node → Ganache integration.

Dependency note: Ganache reports a µWS native-binary fallback on Node 24 and npm reports advisories in its transitive development tree; the tests use the JavaScript fallback successfully.

### T3 — independent paper worker and hard stops

Status: complete for offline scope.

- Replaced the broken in-process asyncio loop with a credential-free Python subprocess and controller.
- Worker checks drawdown, expiry, atomic policy version/leader allowlist, invalid inputs and a 3-second controller lease every 100ms.
- Controller heartbeats every 500ms, records stop reason, handles protocol errors, waits for acknowledgement and terminates an unresponsive process.
- RedLine and explicit stop routes share the worker stop path; mock authorization is marked revoked without inventing a transaction hash, while local-chain records become revoke_pending.
- Added tests for no-button DD_LIMIT, POLICY_REVOKED and real controller-disconnect process exit.

Validation: T3 engine/RedLine/integration tests: 11 passed. Full combined suite remains the gate after T4 changes.

### T4–T6

Status: pending.
