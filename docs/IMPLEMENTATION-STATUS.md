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

### T3–T6

Status: pending.
