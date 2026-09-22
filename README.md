# waytoweb4-agent

> We built a **copy-trading authorization agent**: natural language produces a locked Spec, a human face-gate starts Paper copy-trading via waytoweb4, the Spec is minted as a revocable on-chain Strategy Passport, and a separate RedLine agent can halt the engine and burn the passport without looking at PnL.

**GWDC 2026 Korea · FuriosaAI × Bricksum · Challenge A** — with
Challenge B ("可停、可审计") covered by the RedLine kill switch.

See [`waytoweb4-agent-prd.md`](waytoweb4-agent-prd.md) for the full
product brief, and [`docs/security-arch.md`](docs/security-arch.md)
for the security architecture.

## Repository layout

```
waytoweb4-agent/
├── frontend/                # Vite + React (CDN Tailwind + Font Awesome)
├── backend/                 # FastAPI (uvicorn :8000)
├── agent/                   # Follow Agent + RedLine Agent (Python lib)
├── chain/                   # isolated Node chain worker + StrategyPassport v2
├── scripts/
│   └── run_demo.py          # one-shot launcher: backend + frontend
├── docs/
│   ├── security-arch.md
│   └── eval/hynix-cases.json
└── waytoweb4-agent-prd.md
```

## Quick start

```bash
# 1. install Python deps (both packages editable)
python -m pip install -e "./agent[dev]" -e "./backend[dev]"

# 2. install frontend deps
cd frontend && npm install && cd ..

# 3. one-shot launch (backend :8000 + frontend :5173)
python scripts/run_demo.py
```

Open <http://localhost:5173/>. Offline flow is prepare → explicit confirm → mock authorization → face mock → paper worker → automatic stop/revoke. The two-round rehearsal is `python scripts/rehearse.py --mode offline`.

## What lives where

| Concern | Owner | Where |
|---|---|---|
| Natural-language → Spec | Follow Agent | `agent/follow_agent/` |
| Drawdown hard gate | RedLine rule gate | `agent/redline_agent/rule_gate.py` |
| Event classification (海力士/杠杆/...) | RedLine LLM classifier | `agent/redline_agent/llm_classifier.py` |
| Face verification, start/stop | Backend | `backend/app/routers/{face,engine}.py` |
| Passport mint / revoke | Backend + isolated Node worker | `backend/app/routers/passport.py`, `chain/` |
| Mock ledger / Sepolia keccak | Backend | `backend/app/passport_backends/` |
| Web UI | Frontend | `frontend/src/` |
| Independent paper engine | Backend + subprocess | `backend/app/engine.py`, `backend/app/paper_worker_process.py` |

## Environment variables

| Name | Default | Purpose |
|---|---|---|
| `PASSPORT_BACKEND` | `mock` | `mock` (offline simulation), `local` (temporary Ganache EVM), or `sepolia` (disabled until a real bridge is configured). |
| `KILN_MODE` | `offline` | `offline` permits mock; `live` requires `KILN_API_KEY` and never falls back. |
| `KILN_API_KEY` | (unset) | Set to switch from `MockKilnClient` to `HttpKilnClient`. |
| `TRIP_SECONDS` | `60` | Seconds for the mock engine drawdown to reach `maxLossUsd`. |
| `LEDGER_PATH` | `backend/var/passports.json` | Mock passport ledger. |
| `FRONTEND_ORIGIN` | `http://localhost:5173` | CORS origin for the backend. |

## Token / energy table (PRD §9)

After a demo run, hit `http://localhost:8000/api/state/tokens` and
paste the markdown table here:

```
flow          tokens_in  tokens_out  latency_s  energy_Wh_est
--------------------------------------------------------------
clarify       ...
spec_emit     ...
redline_hold  ...
redline_trip  ...
demo_inject   ...
--------------------------------------------------------------
total         ...
assumption    180W NPU-class, energy = 180 * latency / 3600
```

The mock Kiln client emits realistic token counts (CJK ≈ 1 tok,
ASCII ≈ 1 tok / 4 chars) and 8 ms per call.

## On-chain tx hashes

Only `PASSPORT_BACKEND=local` produces actual local-EVM transaction hashes. Offline simulation stores a `simulation_id` and leaves transaction fields null. No public-chain transaction was made by this integration work.

> Public testnet hashes must be pasted only after the authorized field rehearsal; never copy historical hashes into a new run.

| Step | tx hash |
|---|---|
| Mint Passport (field live run) | pending field rehearsal |
| Revoke on RedLine TRIP | pending field rehearsal |

## Honest disclaimer: what is real and what is mock

- **Kiln**: if `KILN_API_KEY` is set we call the real `gpt-oss-120b`
  endpoint. Without it the offline `MockKilnClient` is used. Both
  paths record tokens through the same `TokenLogger`.
- **Passport**: offline mode never fabricates a tx hash. The local chain worker uses a temporary EVM and the v2 contract; public Sepolia broadcast is deliberately not enabled in this local pass.
- **Engine**: the paper worker is a separate process with drawdown, expiry, policy and lease hard stops. No real waytoweb4 service is called.
- **Face gate**: a button. No real face recognition.

## Tests

```bash
python -m pytest --import-mode=importlib agent/tests backend/tests
npm --prefix chain test
npm --prefix frontend run build
python scripts/rehearse.py --mode offline
python -m backend.app.verify_evidence --run <evidence-dir-from-artifacts/rehearsal/evidence-path.txt>
```

## License

Internal hackathon project; not for redistribution.
