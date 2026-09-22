# waytoweb4-backend

FastAPI service for the waytoweb4-agent hackathon project.

## Run locally

```bash
# install both packages (agent + backend) editable
python -m pip install -e agent[dev]
python -m pip install -e backend[dev]

# default: passport backend = mock
python -m uvicorn backend.app.main:app --port 8000

# Sepolia-shaped adapter (no real chain broadcast; keccak hashes only)
PASSPORT_BACKEND=sepolia python -m uvicorn backend.app.main:app --port 8000
```

Open <http://localhost:8000/docs> for the auto-generated OpenAPI UI.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/spec/check` | Heuristic check: which Spec fields are still missing? |
| POST | `/api/spec/clarify` | One round of clarification (calls Kiln `clarify` flow). |
| POST | `/api/spec/emit` | Emit the locked Spec (calls Kiln `spec_emit` flow). |
| POST | `/api/face/verify` | Mock face gate. Requires `passport_id`. |
| POST | `/api/passport/mint` | Mint a Strategy Passport; returns `tx_hash`. |
| POST | `/api/passport/{id}/revoke` | Revoke a passport; returns a second `tx_hash`. |
| GET  | `/api/passport/{id}` | One passport record. |
| POST | `/api/engine/start` | Start the deterministic mock engine. |
| POST | `/api/engine/stop` | Stop the engine (does not revoke). |
| POST | `/api/engine/tick?amount=N` | Synchronous drawdown advance. |
| POST | `/api/redline/judge` | Run RedLine; auto-revokes on TRIP. |
| POST | `/api/redline/inject/hynix` | Inject the canonical Hynix crash pack. |
| GET  | `/api/state` | Single snapshot for the frontend (passports + events + token report). |
| GET  | `/api/state/tokens` | Plain-text markdown table (paste into README). |
| POST | `/api/state/reset` | Wipe in-memory state + JSON ledger (token totals NOT reset). |
| GET  | `/api/health` | Smoke check. |

## Environment variables

| Name | Default | Purpose |
|---|---|---|
| `PASSPORT_BACKEND` | `mock` | `mock` or `sepolia`. |
| `KILN_API_KEY` | (unset) | If set, switch to the real Kiln HTTP client. |
| `TRIP_SECONDS` | `60` | Seconds for the mock engine drawdown to reach `maxLossUsd`. |
| `LEDGER_PATH` | `backend/var/passports.json` | Persisted mock passport ledger. |
| `FRONTEND_ORIGIN` | `http://localhost:5173` | CORS allow-origin for the React dev server. |

## Tests

```bash
PYTHONPATH=. python -m pytest backend/tests -v
```
31 tests cover happy paths, every 4xx error code, the spec
re-validation guard, and the full end-to-end demo flow.

## Honest disclaimer

The `sepolia` backend adapter does NOT broadcast transactions. It
computes real `keccak256` hashes from the canonical-JSON Spec so
the output looks like a Sepolia tx, but no RPC call is made. To
broadcast for real you would need:
1. A deployed `PassportRegistry` contract on Sepolia.
2. `SEPOLIA_RPC_URL` + `SEPOLIA_PRIVATE_KEY` env vars.
3. Replace the `SepoliaPassportBackend.mint/revoke` bodies with
   `web3.eth.send_transaction(...)` calls.

This is documented honestly in the README's §10 so judges don't
think we shipped a real on-chain tx in the time budget.