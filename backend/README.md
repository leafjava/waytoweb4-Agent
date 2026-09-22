# waytoweb4-backend

FastAPI service for the waytoweb4-agent hackathon project.

## Run locally

```bash
# install both packages (agent + backend) editable
python -m pip install -e agent[dev]
python -m pip install -e backend[dev]

# default: passport backend = mock
python -m uvicorn backend.app.main:app --port 8000

# Real public-testnet transport (requires explicit RPC/wallet settings)
PASSPORT_BACKEND=testnet RPC_URL=https://... CHAIN_ID=11155111 PRIVATE_KEY=0x... python -m uvicorn backend.app.main:app --port 8000
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
| POST | `/api/engine/stop` | Stop the engine and revoke its authorization. |
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
| `PASSPORT_BACKEND` | `mock` | `mock`, `local`, or `testnet`; legacy `sepolia` aliases to `testnet`. |
| `KILN_MODE` | `offline` | `live` selects the real Kiln HTTP client and requires its key. |
| `KILN_API_KEY` | (unset) | Required only in Kiln live mode. |
| `RPC_URL` | (unset) | HTTPS public-testnet JSON-RPC endpoint. |
| `PRIVATE_KEY` | (unset) | Dedicated funded testnet wallet for the isolated worker. |
| `CHAIN_ID` | (unset) | Kairos `1001` or Sepolia `11155111`. |
| `PASSPORT_ADDRESS` | (unset) | Existing v2 contract; omit to deploy during the authorized live run. |
| `TRIP_SECONDS` | `60` | Seconds for the mock engine drawdown to reach `maxLossUsd`. |
| `LEDGER_PATH` | `backend/var/passports.json` | Persisted mock passport ledger. |
| `FRONTEND_ORIGIN` | `http://localhost:5173` | CORS allow-origin for the React dev server. |

## Tests

```bash
PYTHONPATH=. python -m pytest backend/tests -v
```
The combined suite covers the authorization boundary, worker stops,
local-EVM receipts/readback, evidence contracts and the end-to-end flow.

## Honest disclaimer

Mock mode never fabricates transaction hashes, and local mode uses a
temporary Ganache chain. Testnet mode contains a real transport but does
nothing until explicitly selected with a valid HTTPS RPC, public-testnet
chain ID and dedicated wallet. No public-chain transaction is created by
installation, tests or offline rehearsal; only an authorized live run may
broadcast one.
