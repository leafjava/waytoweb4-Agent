# Security audit — 2026-09-25

## Verdict

The current build is suitable for a **loopback-only, Paper-trading and public-testnet hackathon demo**. It is not approved for public Internet exposure, real-money trading, mainnet funds, or unattended production use.

The audit covered the FastAPI boundary, Spec and RedLine validation, human gate, worker lifecycle, AlphaFox adapter, chain worker and Solidity contract, secret handling, evidence generation, browser supply chain, and Python/Node dependencies.

## Fixed in this audit

| Severity | Finding | Resolution |
|---|---|---|
| High | A stop could race an in-flight local or AlphaFox start. The later start completion could overwrite the fail-safe stop intent with `running`. | Start and stop now share a per-passport transition lock. Stop publishes `stop_requested` before waiting; start rechecks it after local and remote awaits. A remote instance created during the race is stopped exactly once. |
| High | Live Kiln credentials could be sent to a cleartext or ambiguous `KILN_API_BASE`. | Live mode now requires HTTPS and rejects embedded credentials, queries and fragments before constructing the client. |
| Medium | `/api/redline/inject/hynix` ran the synchronous live Kiln client on the event loop, potentially delaying heartbeats and emergency stop for up to the HTTP timeout. | The classifier now runs in a worker thread, matching the normal judge route. |
| Medium | Text prompts and RedLine event batches were unbounded, allowing avoidable memory and Kiln-cost exhaustion. | Prompt text is capped at 4,096 characters; identifiers and event fields are bounded; event batches are capped at 100 and reject non-finite or extreme changes. |
| Medium | `/api/state` iterated mutable passport state without taking the documented lock. | Snapshot and workload counts are now captured under the state lock. |
| Medium | The browser fetched Font Awesome from a third-party CDN at runtime without SRI or CSP. | Font Awesome is now an exact, lockfile-pinned local dependency bundled by Vite. |
| Low | Unexpected agent exceptions reflected raw implementation/provider details in HTTP 500 responses. | Unknown errors now return a generic message; detailed provider bodies are not sent to clients. |

Regression coverage includes stop-during-local-start, stop-during-AlphaFox-start with exactly-once compensation, unsafe Kiln endpoints, and oversized RedLine batches.

## Controls that passed review

- Specs forbid extra fields and lock execution to `mode=copy`, `venue=paper`, `paper=true`, a USD 10,000 ceiling, a future expiry and `maxLossUsd <= notionalUsd`.
- The engine requires exact Spec confirmation, active authorization and a one-use human gate. Stop, RedLine, policy failure, controller loss and restart fail closed and invalidate the gate.
- AlphaFox writes are built with fixed argument arrays rather than a shell, receive only an allowlisted environment, and remain Paper-only. Remote uncertainty is recorded as `uncertain` rather than success.
- The live chain worker accepts only Kairos or Sepolia, requires HTTPS RPC and a dedicated private-key format, verifies chain ID, receipts, events, author and contract readback, and journals submissions before receipt waits.
- Worker subprocesses do not inherit Kiln, chain or AlphaFox secrets.
- Mock runs keep transaction hashes null. The recorded Sepolia evidence uses a dedicated test wallet and confirmed deploy, mint and revoke receipts.
- Demo launch scripts bind Vite and FastAPI to `127.0.0.1`; live reset is disabled.
- Repository and history scans found no committed private key or Kiln API key.

## Residual risks and operating rules

### High if the service is exposed publicly: no API authentication

The backend has no user authentication or authorization layer. CORS is a browser policy, not access control. Any process that can reach the API can prepare, approve, start, stop or trigger RedLine. Run it only on `127.0.0.1` for the event. A public deployment requires authenticated sessions, per-user ownership checks, CSRF protection and rate limits before use.

### Medium: the Demo human gate proves consent in the UI, not identity

The A-grade camera/button flow does not perform liveness or cryptographic user presence. A direct API caller can submit the button verification payload. The correct claim is “the demonstrated UI requires an explicit per-run approval”; do not claim KYC, biometric identity, anti-bot protection or unforgeable consent. Production hardening requires WebAuthn or a reviewed vendor liveness/approval service bound to the frozen Spec hash.

### Medium: local chain development dependencies

`npm audit` reports 11 advisories (including two critical) in the Ganache/Solc development tree. Production dependencies report zero vulnerabilities, and the credential-bearing live worker dynamically imports only `live-runtime.mjs`, so Ganache is not loaded in live mode. Keep Ganache local, never expose its RPC, and replace it when a maintained compatible test runtime is available.

### Medium: local evidence is not tamper-evident

Evidence JSON is structurally verified and public-chain fields can be independently checked, but local logs are not signed. Judges should verify the displayed Sepolia transaction hashes and contract readback. A production audit trail needs append-only remote storage or signatures.

### Medium: on-chain `humanConfirmed` is the frozen-Spec confirmation

Passport v2 mints after manual Spec confirmation and before the camera/button gate. Therefore the contract field `humanConfirmed` must not be described as an on-chain face-verification proof. The per-run face approval remains in the local Passport audit record. Moving that claim on-chain requires a new contract transition after the gate.

### Low: dependency and CI reproducibility

Node packages are lockfile-pinned. Python project metadata uses minimum versions rather than a committed cross-platform lock, and GitHub Actions use major-version tags instead of commit SHAs. Before production, generate a reviewed Python lock and pin actions by commit digest.

## Verification evidence

- Python: `170 passed` after the final security changes.
- Chain: `4 passed` (local EVM mint/readback/revoke and live-config guards).
- Frontend: Vite production build passed.
- `pip-audit`: no known vulnerabilities in auditable installed packages; the two editable local packages are not published on PyPI and were reviewed directly.
- `npm audit --omit=dev`: zero production vulnerabilities in both frontend and chain workspaces.
- Frontend full `npm audit`: zero vulnerabilities.
- Secret scan: no committed private key or Kiln API key detected. Public transaction/spec hashes are expected evidence, not secrets.
