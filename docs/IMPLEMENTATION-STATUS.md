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
- Public-chain transport is implemented behind explicit `PASSPORT_BACKEND=testnet` configuration, with public-testnet/HTTPS/key validation, submitted/confirmed journaling, receipt checks and full contract readback. No public transaction was broadcast during local implementation.

Validation: Node chain tests 2 passed; combined Python suite 112 passed, including FastAPI → Node → Ganache integration.

Dependency note: Ganache reports a µWS native-binary fallback on Node 24 and npm reports advisories in its transitive development tree; the tests use the JavaScript fallback successfully.

### T3 — independent paper worker and hard stops

Status: complete for offline scope.

- Replaced the broken in-process asyncio loop with a credential-free Python subprocess and controller.
- Worker checks drawdown, expiry, atomic policy version/leader allowlist, invalid inputs and a 3-second controller lease every 100ms.
- Controller heartbeats every 500ms, records stop reason, handles protocol errors, waits for acknowledgement and terminates an unresponsive process.
- RedLine, worker hard stops, explicit engine stop and passport revoke share one stop-and-revoke path. Mock authorization is marked revoked without inventing a transaction hash; local-chain authorization becomes revoked only after a successful receipt and revoked readback.
- Added tests for no-button DD_LIMIT, POLICY_REVOKED and real controller-disconnect process exit.

Validation: T3 engine/RedLine/integration tests: 11 passed. Full combined suite remains the gate after T4 changes.

### T4 — Kiln contract and per-run evidence

Status: complete for code/stub/offline scope; real Kiln remains a field validation item.

- `KILN_MODE=live` now fails closed when the key is missing; it never silently selects mock.
- HTTP responses are checked for the configured `gpt-oss-120b` model. Usage source is classified as `api`, `estimated` or `unavailable`; all calls retain flow, model, request ID, latency and 180W-derived energy estimate.
- Added a strict `KilnEventClassifier` under the teammate EventClassifier protocol and wired it into backend RedLine requests in live mode. Rule-first hard trips still avoid a model call.
- Added per-run `manifest.json`, `intent.json`, `events.jsonl`, `calls.jsonl`, `chain.jsonl` and a fail-closed evidence verifier. Live verification rejects offline mode, estimated/unavailable usage, malformed hashes and missing stop evidence.

Validation: full combined suite: 118 passed. No real Kiln request was made; no public transaction was broadcast.

### T5 — frontend flow and two-round rehearsal

Status: complete for offline scope.

- React SpecCard now performs prepare → explicit confirmation → mint with request IDs; it never sends a raw Spec to mint.
- Status colors and cards support prepared/confirmed/authorized/pending/uncertain states; transaction fields remain empty in mock mode.
- Added `scripts/rehearse.py --mode offline`, which runs round A, then a fresh round B with the same frozen intent and a policy allowlist removal. The worker stops round B automatically with `POLICY_REVOKED` and records the shared comparison ID.

Validation: offline rehearsal completed and produced `comparison.json`; frontend `npm run build` passed. Browser interaction is still a manual field check, not claimed here.

### T6 — delivery package

Status: complete for local delivery package.

- Updated README to describe the real offline behavior, isolated chain worker, explicit Kiln modes, null simulation hashes, and local verification commands.
- Added `docs/INTEGRATION-HANDOFF.md` with commit order, test results, rollback and field-only checklist.
- Added the two-round rehearsal output contract and evidence verifier invocation.

Validation: Python 118 passed; Node chain 2 passed; frontend build passed; offline rehearsal and offline evidence verification passed.

Field acceptance still required: real Kiln `gpt-oss-120b` call with API usage, at least one authorized public testnet transaction and hash, a fresh two-round live run with changed policy condition and stop log, final README token table, video and Deck. These are intentionally not fabricated locally.

### Teammate mainline sync

Status: synchronized with teammate `master` at `fdb3c8a`.

- Adopted the teammate's English/Chinese locale switcher and translated home/demo components as the frontend baseline.
- Preserved the integrated prepare → explicit confirmation → mint authorization flow and added localized labels for each stage.
- Removed tracked runtime/build artifacts deleted by the teammate mainline.

Validation: Python 118 passed; Node chain 2 passed; frontend production build passed; offline two-round rehearsal passed.

### Post-integration hardening

Status: local stop/revoke and live Kiln routing complete; external field calls remain pending.

- Centralized revocation in the authorization service so every stop source uses the same state transition, receipt validation, readback validation and evidence path.
- Added local-EVM integration coverage proving both RedLine TRIP and drawdown hard stop revoke the contract passport, rather than only changing the UI state.
- Backend RedLine now selects `KilnEventClassifier` for live HTTP mode and the deterministic classifier for offline mode.
- Live Kiln rejects any requested or returned model other than `gpt-oss-120b`, including responses that omit the model identity.
- Bound token-call evidence to the active backend run, avoiding a separate environment-only evidence destination.
- Enforced the teammate UI's face-gate requirement in the backend engine boundary, so direct API calls cannot bypass it.
- Serialized revoke attempts per Passport and added stop-during-mint recovery: once a pending mint confirms, an already-requested stop immediately performs and verifies the revoke.
- Demo reset now stops active workers before clearing state and is refused for chain-backed or live runs. Persisted running states fail closed on restart and emit `restart_reconcile` evidence.

Validation: Python 129 passed; Node chain 2 passed; frontend production build passed. No real Kiln request or public-chain transaction was made by this hardening pass.

### Public-testnet transport and evidence hardening

Status: implementation and offline validation complete; authorized field transaction still pending.

- Replaced the fake Sepolia-shaped adapter with an isolated real testnet worker selected only by `PASSPORT_BACKEND=testnet` (`sepolia` remains a compatibility alias).
- Restricted live RPC to HTTPS and public testnet IDs Kairos `1001` or Sepolia `11155111`; validated the dedicated key format, RPC chain ID, wallet gas balance and StrategyPassport v2 version.
- Added deployment/mint/revoke submission journaling before receipt waits, bounded receipt timeouts, author/event/receipt checks and full contract readback against the canonical keccak intent.
- Strengthened live evidence verification to require one run ID, exact Kiln model/API token usage, public-testnet receipts, matching contract/passport IDs, active→revoked readback and an engine-stop log. Local-chain hashes and simulated revoke events now fail live verification.
- Split the two-round rehearsal into independent run directories so the second intent can no longer overwrite the first run's evidence.

Validation: Python 131 passed; Node chain 4 passed; frontend production build passed; both independent offline run directories passed evidence verification. No public transaction was broadcast.

### Provisional waytoweb4 adapter boundary

Status: mock contract complete; official endpoint mapping pending teammate documentation.

- Added a frozen, extra-forbidden execution start DTO with request/run/passport IDs, confirmed Spec hash, integer cents, expiry and paper-only mode.
- The existing isolated paper worker now consumes that DTO, so offline development exercises the same trust boundary that a future HTTP adapter must satisfy.
- Added `docs/WAYTOWEB4-INTERFACE-CONTRACT.md` with idempotency, stop, status, evidence and official-document mapping requirements. It deliberately contains no guessed endpoint names or authentication scheme.

Validation: Python 133 passed after adding adapter-boundary and unconfirmed-record tests.

### English/Korean demo baseline and human-gate follow-up

Status: localization implemented locally; human-gate completion planned.

- Local commit `23eb4f3` replaces the prior Chinese locale with Korean and keeps
  English as the other user-facing locale.
- A 2026-09-23 product review confirmed that the backend blocks start before
  `face_verified`, but the A-tier gate still lacks a local camera preview.
- `verified_at` currently exists only in the audit event; gate method and
  session ID are not yet persisted on the passport record.
- Terminal stop/revoke already prevents reuse of the old passport. The next
  implementation pass will also expose gate invalidation clearly and require a
  new passport/session for the next run.
- The execution plan and field acceptance boundary are recorded in
  `docs/FURIOSA-DEMO-NEXT-PLAN.md`.

### P0 — English/Korean baseline verification

Status: complete.

- Checked the integration branch against teammate `master` at `fdb3c8a`; the
  branch is not behind the teammate mainline.
- Confirmed that visible frontend locale data is English/Korean and that the
  locale choice persists in browser storage.

Validation: Python 133 passed; Node chain 4 passed; frontend production build
passed.

### P1 — per-mandate human-gate evidence

Status: complete.

- The human-gate endpoint now accepts `method=button` and a caller-generated
  UUID session ID, and returns the method, session and server timestamp.
- Persisted `face_verified_at`, `face_verification_method` and
  `face_verification_session_id` on the application passport and included the
  same binding in face/start audit events.
- Gate sessions are idempotent for the same passport and cannot be replayed
  across mandates. Only an authorized passport with the exact confirmed Spec
  hash can be approved.
- Direct engine start without approval now returns stable code
  `FACE_GATE_REQUIRED`.

Validation: full combined Python suite 135 passed, including persistence,
session replay and direct API bypass coverage.

### P2 — local camera-preview approval

Status: complete for browser implementation; physical-camera rehearsal pending.

- Added a focused English/Korean human-approval dialog that displays the exact
  frozen leader, notional, loss limit, expiry and paper-only mode.
- The dialog requests a local video-only browser stream, sends no image data,
  stops every media track on close/unmount and blocks approval when permission
  is denied or the camera API is unavailable.
- Explicit consent triggers two visible trust-boundary calls: record the gate
  result first, then start the paper engine. A start failure cannot fabricate
  or erase the recorded human approval.
- Added localized permission, loading, privacy and recovery states; improved the
  demo grid for narrow screens and made coded backend errors readable.
- The application passport now displays approval time, method and session ID.

Validation: frontend production build passed; English and Korean key sets both
contain 158 entries with no missing counterpart. A physical-camera browser run
remains a field check because no camera device is available in the CLI test
environment.

### P3 — terminal human-gate invalidation

Status: complete.

- Added the explicit gate lifecycle `pending → active → consumed → invalidated`.
  Approval becomes consumed only after the isolated worker starts successfully.
- Central stop/revoke now invalidates the gate for manual stop, RedLine,
  drawdown, policy, lease and controller failures while retaining the original
  approval timestamp, method and session as historical evidence.
- Restart reconciliation also invalidates the gate and emits a dedicated audit
  event. Repeated revoke calls cannot duplicate that event.
- The frontend marks the old approval as expired, displays the invalidation
  reason and tells the user to create and approve a new frozen mandate.
- Offline rehearsal now asserts distinct passport and gate-session IDs between
  rounds, even when the frozen intent is the same and only policy changes.

Validation: Python 135 passed; Node chain 4 passed; frontend production build
passed; both independent offline rehearsal evidence directories passed the
evidence verifier. English and Korean key sets both contain 165 entries.

### P4 — Furiosa inference and governance evidence

Status: complete for measured application data; RNGD hardware measurements are
not claimed.

- Added a structured token snapshot alongside the paste-ready markdown report.
  Each flow exposes calls, input/output tokens, latency, 180W energy estimate,
  usage source and returned model identity.
- `/api/state` now reports the exact required model, offline/live mode, power
  assumption, run ID, active execution sessions, passport count and agent-call
  count.
- Replaced the demo's raw token block with an English/Korean workload panel and
  authorization/control timeline. API usage is visually distinct from
  offline/estimated evidence.
- The panel makes the Furiosa relationship concrete without inventing RNGD
  throughput, users/kW or TCO measurements.

Validation: full combined Python suite 136 passed; frontend production build
passed; English and Korean key sets both contain 185 entries with no missing
counterpart.

### P5 — official waytoweb4 adapter

Status: pending official teammate documentation.

- The frozen paper-only execution DTO and isolated worker boundary are ready.
- Endpoint paths, authentication, idempotency and stop/status semantics remain
  intentionally unmapped rather than guessed.

### P6 — field acceptance

Status: pending authorized credentials and a physical-camera rehearsal.

- No real Kiln request or public-chain transaction was made during this pass.
- Required live work is limited to a fresh `gpt-oss-120b` run with API usage,
  a changed-condition rerun with stop evidence, at least one fresh public
  testnet transaction/receipt/readback, physical camera permission checks, and
  the final README/video/Deck evidence update.

### P7 — security and contest-readiness audit

Status: code-level audit complete; live acceptance remains pending.

- Bound the Vite demo server to loopback and disabled credentialed CORS. The
  unauthenticated demo must not be hosted on a public or shared interface.
- Upgraded Vite/plugin-react and Ethers; their production audits report zero
  known vulnerabilities. Python runtime dependencies also report zero known
  vulnerabilities via `pip-audit`. The live chain worker no longer imports
  Ganache or solc, and verifies a committed contract artifact against the
  source hash.
- Marked offline RedLine classification as `mock` instead of `llm` so mock
  output cannot be mistaken for Kiln evidence.
- Removed RPC worker stderr from HTTP-facing errors to avoid leaking a
  credential-bearing provider URL.
- Corrected the security document to reflect the actual process boundary,
  button-based human gate and application evidence log.
- The launcher now fails clearly when its exact ports are occupied instead of
  mistaking an older demo instance for the process it just started.
- Ganache and solc retain nine known advisories in the development-only local
  test/compile toolchain. Neither is loaded by the live worker; Ganache uses an
  in-memory provider and never listens on a socket in this project.

Field blockers are unchanged: a fresh live Kiln/gpt-oss-120b trace with API
usage, a fresh public-testnet receipt/readback, the official waytoweb4 adapter,
physical-camera rehearsal, and final video/Deck artifacts.

### P8 — field tooling and continuous verification

Status: complete for credential-free scope.

- Added a read-only field preflight that checks tool versions, dependency
  presence, exact contract artifact hash, loopback ports and live configuration
  without printing secrets. Its optional network mode performs only RPC chain,
  balance and bytecode reads and records that no broadcast occurred.
- Added an evidence exporter that runs the fail-closed verifier first, renders
  per-flow token/latency/180W energy tables and extracts confirmed transaction
  receipts. Offline output is permanently labelled `OFFLINE_DEMO_ONLY`; the
  `--live` path rejects mock or incomplete evidence.
- Added GitHub Actions coverage for Python tests, chain tests, deterministic
  contract compilation, frontend build and production dependency audits.

Validation: Python 144 passed; chain 4 passed; frontend production build and
both production dependency audits passed. Offline preflight and evidence export
passed; live variants failed closed without credentials, as required.
