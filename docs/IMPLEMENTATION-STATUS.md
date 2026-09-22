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

Status: pending.
