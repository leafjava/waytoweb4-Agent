# waytoweb4-agent

> We built a **copy-trading authorization agent**: natural language produces a locked Spec, a human face-gate starts Paper copy-trading via waytoweb4, the Spec is minted as a revocable on-chain Strategy Passport, and a separate RedLine agent can halt the engine and burn the passport without looking at PnL.

**GWDC 2026 Korea · FuriosaAI × Bricksum · Challenge A** — with
Challenge B ("stoppable, auditable") covered by the RedLine kill switch.

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

Open <http://localhost:5173/>. Offline flow is prepare → explicit confirm → mock authorization → local camera preview + per-mandate human approval → paper worker → automatic stop/revoke. The preview never leaves the browser. The two-round rehearsal is `python scripts/rehearse.py --mode offline`.

## What lives where

| Concern | Owner | Where |
|---|---|---|
| Natural-language → Spec | Follow Agent | `agent/follow_agent/` |
| Drawdown hard gate | RedLine rule gate | `agent/redline_agent/rule_gate.py` |
| Event classification (Hynix / leverage / ...) | RedLine LLM classifier | `agent/redline_agent/llm_classifier.py` |
| Face verification, start/stop | Backend | `backend/app/routers/{face,engine}.py` |
| Provisional waytoweb4 adapter contract | Backend + docs | `backend/app/execution_contract.py`, `docs/WAYTOWEB4-INTERFACE-CONTRACT.md` |
| Passport mint / revoke | Backend + isolated Node worker | `backend/app/routers/passport.py`, `chain/` |
| Mock ledger / Sepolia keccak | Backend | `backend/app/passport_backends/` |
| Web UI | Frontend | `frontend/src/` |
| Independent paper engine | Backend + subprocess | `backend/app/engine.py`, `backend/app/paper_worker_process.py` |
| Human-gate and inference evidence UI | Frontend | `frontend/src/components/{HumanGate,InferenceEvidencePanel}.jsx` |

## Environment variables

| Name | Default | Purpose |
|---|---|---|
| `PASSPORT_BACKEND` | `mock` | `mock` (offline simulation), `local` (temporary Ganache EVM), or `testnet` (real public-testnet transport). Legacy `sepolia` is accepted as an alias for `testnet`. |
| `KILN_MODE` | `offline` | `offline` permits mock; `live` requires `KILN_API_KEY` and never falls back. |
| `KILN_API_KEY` | (unset) | Required with `KILN_MODE=live`; ignored in offline mode to prevent accidental live calls. |
| `RPC_URL` | (unset) | HTTPS JSON-RPC endpoint required by `PASSPORT_BACKEND=testnet`. |
| `PRIVATE_KEY` | (unset) | Dedicated funded testnet wallet; passed only to the isolated Node worker. |
| `CHAIN_ID` | (unset) | Public testnet chain ID: Kairos `1001` or Sepolia `11155111`. |
| `PASSPORT_ADDRESS` | (unset) | Existing StrategyPassport v2 address; when absent, the live worker deploys it before minting. |
| `TX_TIMEOUT_MS` | `60000` | Receipt wait timeout, constrained to 1–120 seconds. |
| `TRIP_SECONDS` | `60` | Seconds for the mock engine drawdown to reach `maxLossUsd`. |
| `LEDGER_PATH` | `backend/var/passports.json` | Mock passport ledger. |
| `FRONTEND_ORIGIN` | `http://localhost:5173` | CORS origin for the backend. |

The one-shot launcher binds both services to loopback. The demo API has no
account authentication and must not be exposed as a shared or public service.

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

The offline Kiln client emits deterministic estimated token counts (CJK ≈ 1
tok, ASCII ≈ 1 tok / 4 chars) and labels their usage source as estimated. Only
API-reported usage from a live run is acceptable as final evidence.

## On-chain tx hashes

`PASSPORT_BACKEND=local` produces local-EVM transaction hashes. `PASSPORT_BACKEND=testnet` enables the real isolated public-testnet worker only when its explicit RPC, wallet and chain configuration is present. Offline simulation stores a `simulation_id` and leaves transaction fields null. No public-chain transaction was made by this integration work.

> Public testnet hashes must be pasted only after the authorized field rehearsal; never copy historical hashes into a new run.

| Step | tx hash |
|---|---|
| Mint Passport (field live run) | pending field rehearsal |
| Revoke on RedLine TRIP | pending field rehearsal |

## Honest disclaimer: what is real and what is mock

- **Kiln**: if `KILN_API_KEY` is set we call the real `gpt-oss-120b`
  endpoint. Without it the offline `MockKilnClient` is used. Both
  paths record tokens through the same `TokenLogger`.
- **Passport**: offline mode never fabricates a tx hash. The local chain worker uses a temporary EVM and the v2 contract. The guarded testnet worker supports Kairos or Sepolia, but no public transaction was broadcast in this local pass.
- **Engine**: the paper worker is a separate process with drawdown, expiry, policy and lease hard stops. No real waytoweb4 service is called.
- **waytoweb4 interface**: official endpoint documentation is still pending. The paper worker consumes the provisional internal adapter DTO so a documented HTTP transport can replace it without changing authorization rules.
- **Human gate**: a local camera preview plus an explicit confirmation button. No image is captured, uploaded or stored, and no face recognition or KYC is claimed. Approval time, method and session live in the persisted application passport and audit log; StrategyPassport v2 stores the frozen mandate confirmation but not those three metadata fields on-chain.

## FuriosaAI workload view

The demo panel reports the exact `gpt-oss-120b` model, calls and tokens split by
flow, wall-clock latency, the required 180W energy estimate, active execution
sessions and the authorization-to-stop timeline. This is evidence of the
agentic-finance workload and its controls. It does not claim measured RNGD
tokens/s, users/kW or TCO; those numbers require a real hardware run.

## Tests

```bash
python -m pytest --import-mode=importlib agent/tests backend/tests
npm --prefix chain test
npm --prefix frontend run build
npm --prefix frontend audit
npm --prefix chain audit --omit=dev
python scripts/rehearse.py --mode offline
python -m backend.app.verify_evidence --run <evidence-dir-from-artifacts/rehearsal/evidence-path.txt>
```

## License

Internal hackathon project; not for redistribution.
