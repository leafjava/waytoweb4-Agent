# waytoweb4-agent

> We built a **copy-trading authorization agent**: natural language
> produces a locked Spec, a human face-gate starts Paper copy-trading
> via waytoweb4, the Spec is minted as a revocable on-chain Strategy
> Passport, and a separate RedLine agent can halt the engine and burn
> the passport without looking at PnL.

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
python -m pip install -e agent[dev]
python -m pip install -e backend[dev]

# 2. install frontend deps
cd frontend && npm install && cd ..

# 3. one-shot launch (backend :8000 + frontend :5173)
python scripts/run_demo.py
```
启动前端：npm run dev 
启动后端：python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000


Open <http://localhost:5173/>. Click through PRD §7 in order:
chat → lock spec → verify face → start engine → inject hynix →
status flips to `revoked` with a second tx hash.

## What lives where

| Concern | Owner | Where |
|---|---|---|
| Natural-language → Spec | Follow Agent | `agent/follow_agent/` |
| Drawdown hard gate | RedLine rule gate | `agent/redline_agent/rule_gate.py` |
| Event classification (海力士/杠杆/...) | RedLine LLM classifier | `agent/redline_agent/llm_classifier.py` |
| Face verification, start/stop | Backend | `backend/app/routers/{face,engine}.py` |
| Passport mint / revoke | Backend | `backend/app/routers/passport.py` |
| Mock ledger / Sepolia keccak | Backend | `backend/app/passport_backends/` |
| Web UI | Frontend | `frontend/src/` |
| Deterministic mock engine | Backend | `backend/app/engine.py` |

## Environment variables

| Name | Default | Purpose |
|---|---|---|
| `PASSPORT_BACKEND` | `mock` | `mock` (local JSON ledger) or `sepolia` (keccak-shaped; no real broadcast). |
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

The backend emits real `keccak256` hashes. Each passport gets two:
the mint tx and (if revoked) the revoke tx.

> Placeholder. Real hashes are produced by the demo run above;
> paste them here before submission.

| Step | tx hash |
|---|---|
| Mint Passport (Run 1) | TBD |
| Revoke on RedLine TRIP | TBD |
| Mint Passport (Run 2, smaller notional) | TBD |
| Revoke on RedLine TRIP (Run 2) | TBD |

## Honest disclaimer: what is real and what is mock

- **Kiln**: if `KILN_API_KEY` is set we call the real `gpt-oss-120b`
  endpoint. Without it the offline `MockKilnClient` is used. Both
  paths record tokens through the same `TokenLogger`.
- **Passport**: even in `sepolia` mode we do **not** broadcast a
  transaction. The keccak hashes are real and reproducible, but a
  real Sepolia broadcast requires `SEPOLIA_RPC_URL`,
  `SEPOLIA_PRIVATE_KEY`, and a deployed `PassportRegistry` contract
  (out of scope for the 48h hackathon).
- **Engine**: `backend/app/waytoweb4_mock.py` is the swap point. It
  currently drives the in-process engine under a clean REST contract
  (`/v1/leaders`, `/v1/paper/start`, `/v1/paper/{id}/pnl`,
  `/v1/paper/{id}/stop`). When waytoweb4 ships real docs, this single
  file is where the swap happens -- everything else stays put.
- **On-chain target contract**: [`contracts/PassportRegistry.sol`](contracts/PassportRegistry.sol).
  Not deployed. The event topic layout matches the keccak256 hashes
  that `backend/app/passport_backends/` already produce, so a
  deployed instance would accept the existing payloads without
  re-signing or changing the Python adapter.
- **Face gate**: a button. No real face recognition.

## Tests

```bash
PYTHONPATH=. python -m pytest agent/tests -v     # 73 tests
PYTHONPATH=. python -m pytest backend/tests -v   # 31 tests
```

## License

Internal hackathon project; not for redistribution.