# FuriosaAI demo continuation plan

This plan incorporates the team sync from 2026-09-23. The teammate repository
remains the product baseline. Each task below should be implemented as a small,
reviewable commit and must preserve the existing fail-closed authorization,
RedLine and evidence behavior.

## Product position

The demo is a real financial-agent workload with a narrow spending authority:
natural language produces a frozen copy-trading Spec, a human approves this
specific mandate, waytoweb4 runs paper execution, and a separate RedLine agent
can stop execution and revoke the Strategy Passport.

For FuriosaAI, the value is the combination of sustained inference and
governance: multi-user, 24/7 agent workloads need high tokens/s and users/kW,
while every action that can spend or trade needs explicit authorization,
hard stops and replayable records.

## Current baseline

- English/Korean locale switching exists in local commit `23eb4f3`.
- The backend already refuses engine start when `face_verified` is false.
- The gate is currently a button-only simulation; there is no camera preview.
- `verified_at` is emitted in an audit event but is not persisted on the
  passport record. `method` and a dedicated gate `session_id` are missing.
- A stopped passport cannot restart because stop/revoke is terminal. The UI
  must make the expired gate visible and guide the user to a fresh mandate.
- Offline tests, local EVM, evidence verification and the guarded public
  testnet transport already exist. Live credentials remain field-only work.

## P0 — freeze and verify the bilingual baseline

Commit goal: `chore: verify English and Korean demo baseline`

1. Rebase or merge only after checking the teammate's latest `master`.
2. Review every visible demo string in English and Korean. Keep identifiers,
   error codes, model names and transaction hashes untranslated.
3. Build the frontend and run the full Python and chain suites.
4. Update `IMPLEMENTATION-STATUS.md` with the exact teammate base SHA and test
   counts. Do not claim that the local locale commit is in the PR until pushed.

Acceptance:

- Locale survives refresh.
- Home, demo, errors and evidence labels contain no Chinese user-facing copy.
- No behavior change to authorization or evidence generation.

## P1 — complete the A-tier human gate contract

Commit goal: `feat: persist per-mandate human gate evidence`

Backend contract:

```json
POST /api/face/verify
{
  "passport_id": "...",
  "method": "button",
  "session_id": "browser-generated UUID"
}
```

```json
{
  "ok": true,
  "passport_id": "...",
  "session_id": "...",
  "verified_at": "ISO-8601 UTC",
  "method": "button"
}
```

Persist these fields on `PassportRecord` and expose them in the public passport
view:

- `face_verified`
- `face_verified_at`
- `face_verification_method`
- `face_verification_session_id`

Rules:

- Only `button` is accepted for the A-tier demo. Reserve
  `vendor_liveness` for a later adapter; never pretend it ran.
- The backend creates the timestamp and binds the session to one passport and
  its confirmed Spec hash.
- Duplicate submissions for the same session are idempotent. Reusing a session
  for another passport or Spec is rejected.
- Direct start without a current gate returns HTTP 409 with stable code
  `FACE_GATE_REQUIRED`, not an English-only free-form message.
- Gate evidence is included in the `face_verify` and `engine_start` events.

Likely files:

- `backend/app/models.py`
- `backend/app/state.py`
- `backend/app/routers/face.py`
- `backend/app/engine.py`
- `backend/app/errors.py`
- `backend/tests/test_face.py`
- `backend/tests/test_engine.py`

Acceptance:

- A start call before approval fails with `FACE_GATE_REQUIRED`.
- The four gate fields survive process reload.
- An LLM or incoming Spec cannot set any gate field.
- Tests cover replay, wrong-passport session reuse and direct API bypass.

## P2 — build the camera-preview approval page

Commit goal: `feat: add local camera preview human gate`

1. Replace the small passport button with a focused approval panel or modal.
2. Display the exact frozen mandate being approved: leader, notional, maximum
   loss, paper mode and expiry.
3. Request `getUserMedia({ video: true, audio: false })` only while the panel is
   open. Render a local preview and stop every media track on close/unmount.
4. Do not capture, upload or persist frames. Show this privacy statement in
   English and Korean.
5. Enable “I am present — approve and start” only after the preview is ready
   and the user checks the explicit consent box.
6. Keep approval and start as two backend calls so a failed start does not
   fabricate approval state. Show both stages clearly.
7. Provide a clear camera-denied state. It must not silently mark the gate as
   passed.

Likely files:

- `frontend/src/components/HumanGate.jsx` (new)
- `frontend/src/components/PassportCard.jsx`
- `frontend/src/i18n.jsx`
- frontend component tests if a test harness is added by the teammate

Acceptance, visible in 30 seconds:

- Start is unavailable before approval.
- The judge sees the mandate and camera preview before approving.
- Approval changes the passport to verified and shows time/method/session.
- Browser network inspection shows that no image payload is sent.
- Camera denial leaves start blocked with an English/Korean explanation.

## P3 — make stop invalidate the human mandate visibly

Commit goal: `fix: expire human gate on every terminal stop`

The existing lifecycle revokes the passport and permanently blocks its restart.
Keep that stronger rule. On every manual, RedLine, drawdown, policy, lease or
restart-reconciliation stop:

1. Mark the gate as no longer current while retaining the original approval
   fields as historical audit evidence.
2. Add `face_gate_status: active | consumed | invalidated` and an invalidation
   timestamp/reason, or an equivalent explicit model.
3. Show “new authorization and new human approval required” in the UI.
4. A changed condition creates a new frozen Spec, new passport and new gate
   session. Never reactivate or mutate the revoked passport.

Acceptance:

- Every stop source leaves the worker stopped and passport revoked/uncertain as
  appropriate.
- Clicking start on the old passport fails.
- The old approval remains auditable but cannot authorize a new run.
- The second run in rehearsal uses a distinct passport and gate session.

## P4 — sharpen the FuriosaAI workload evidence

Commit goal: `feat: expose inference workload and governance evidence`

Add a compact demo panel and evidence summary showing:

- exact model: `gpt-oss-120b`
- per-flow input/output tokens, latency and API/estimated source
- energy estimate using the required 180 W assumption
- active users/sessions and agent calls for the current run
- authorization → execution → stop/revoke timeline

Do not invent RNGD benchmark numbers. Explain that tokens/s, users/kW and TCO
are the hardware evaluation dimensions, while this project supplies a credible
agentic-finance workload. Any actual RNGD result must come from a measured run.

Acceptance:

- A judge can point to both inference demand and financial control evidence.
- Offline data is labeled simulated/estimated.
- Live mode accepts only API-reported token usage for final evidence.

## P5 — external adapters after official documentation arrives

Commit goal: `feat: connect documented waytoweb4 paper adapter`

Map the existing frozen execution DTO to the official start, stop and status
endpoints. Do not guess endpoint names, authentication or idempotency behavior.
The adapter must preserve request/run/passport IDs, confirmed Spec hash, integer
cents, expiry and paper-only enforcement. RedLine and hard-stop paths must wait
for or reconcile a documented stop result before reporting success.

Acceptance:

- One paper session starts only after the human gate.
- A changed condition starts a separate session.
- RedLine stops the external session and records its external session ID.
- Credentials never reach the worker or frontend.

## P6 — field acceptance with real credentials

This phase requires authorized credentials and must be run once, fresh:

1. Run Kiln in live mode and verify a real `gpt-oss-120b` response with
   API-reported token usage.
2. Run the same flow twice with one changed condition.
3. Demonstrate that the changed or disallowed condition stops execution and
   leaves a structured log.
4. Broadcast at least one authorized public-testnet passport mint or revoke and
   record its new transaction hash, receipt and readback.
5. Run the live evidence verifier; only then paste the token table and hashes
   into README.
6. Record the three-minute video in English or Korean and build the Deck around
   the sequence: frozen mandate → human approval → inference workload → start →
   RedLine stop → passport/evidence replay.

Never use a mock, local-chain hash, historical transaction or estimated token
count as live evidence.

## Recommended assignment order

| Order | Owner profile | Work |
|---|---|---|
| 1 | Backend AI | P1 gate DTO, persistence, stable error and tests |
| 2 | Frontend AI | P2 camera preview, mandate card and bilingual states |
| 3 | Backend AI | P3 invalidation across all stop sources and rehearsal |
| 4 | Frontend/data AI | P4 inference and audit evidence panel |
| 5 | Teammate with docs | P5 official waytoweb4 adapter |
| 6 | Credential holder | P6 live Kiln and public-testnet field run |

Do not parallelize P1 and P3 against the same state model. P2 may begin against
the frozen P1 request/response schema, and P4 can proceed independently after
the evidence file format is confirmed.

