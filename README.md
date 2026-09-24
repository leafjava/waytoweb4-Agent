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
启动前端：npm run dev
启动后端：python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000


Open <http://localhost:5173/>. Offline flow is prepare → explicit confirm → mock authorization → local camera preview + per-mandate human approval → paper worker → automatic stop/revoke. The preview never leaves the browser. The two-round rehearsal is `python scripts/rehearse.py --mode offline`.

## What lives where

| Concern | Owner | Where |
|---|---|---|
| Natural-language → Spec | Follow Agent | `agent/follow_agent/` |
| Drawdown hard gate | RedLine rule gate | `agent/redline_agent/rule_gate.py` |
| Event classification (Hynix / leverage / ...) | RedLine LLM classifier | `agent/redline_agent/llm_classifier.py` |
| Face verification, start/stop | Backend | `backend/app/routers/{face,engine}.py` |
| AlphaFox Paper execution adapter | Backend + official CLI | `backend/app/execution_adapters/alphafox.py`, `docs/ALPHAFOX-ADAPTER.md` |
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
| `EXECUTION_BACKEND` | `paper` | `paper` keeps the isolated offline worker; `alphafox` adds the official CLI Paper transport after authorization and the human gate. |
| `ALPHAFOX_PAPER_CONNECTOR_ID` | (unset) | Required for the AlphaFox backend; must name an active Paper connector. |
| `ALPHAFOX_LEVERAGE` | (unset) | Required positive integer; never silently inferred for a live AlphaFox create. |
| `ALPHAFOX_STOP_CLOSE_POSITIONS` | (unset) | Required `true` or `false`; makes the RedLine flatten/leave-position decision explicit. |

The one-shot launcher binds both services to loopback. The demo API has no
account authentication and must not be exposed as a shared or public service.

Before the field run, validate local tooling and configuration without making
an inference request or broadcasting a transaction:

```bash
python scripts/field_preflight.py
python scripts/field_preflight.py --live --network  # RPC reads only
```

After a run, verify and export its report. `--live` fails closed on mock usage,
local-chain hashes, missing receipts, wrong models or incomplete stop evidence:

```bash
python scripts/export_evidence.py --run <evidence-directory>
python scripts/export_evidence.py --run <evidence-directory> --live
```

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

`PASSPORT_BACKEND=local` produces local-EVM transaction hashes. `PASSPORT_BACKEND=testnet` enables the real isolated public-testnet worker only when its explicit RPC, wallet and chain configuration is present. Offline simulation stores a `simulation_id` and leaves transaction fields null. The authorized Sepolia field rehearsal below was executed on 2026-09-24.

> Public testnet hashes must be pasted only after the authorized field rehearsal; never copy historical hashes into a new run.

| Step | tx hash |
|---|---|
| Deploy StrategyPassport v2 | [`0xa61a…adea`](https://sepolia.etherscan.io/tx/0xa61aafa30896d6abc9c4d16f1c5e87c2519d4fd043584df68074d9957fb4adea) |
| Mint Passport #1 | [`0xf482…4839`](https://sepolia.etherscan.io/tx/0xf482be1f0ee4bf233ed7ad48ef30020ff86713f296b661b5f3931a0b254e4839) |
| Revoke on controlled stop | [`0x77bb…b64f`](https://sepolia.etherscan.io/tx/0x77bb51bab499e98ff5d71cc2f13f4c5359f017d23fa7f4864380a5a1afecb64f) |

Contract: [`0x818A…87D`](https://sepolia.etherscan.io/address/0x818AF51261940013ba6c40aFa74937a3BFd1887D). Independent RPC readback returned version `2-cents`, the frozen spec hash, `humanConfirmed: true`, and final status `revoked`.

## Honest disclaimer: what is real and what is mock

- **Kiln**: if `KILN_API_KEY` is set we call the real `gpt-oss-120b`
  endpoint. Without it the offline `MockKilnClient` is used. Both
  paths record tokens through the same `TokenLogger`.
- **Passport**: offline mode never fabricates a tx hash. The local chain worker uses a temporary EVM and the v2 contract. The guarded testnet worker completed an authorized Sepolia deploy, mint and revoke with successful receipts and final contract readback.
- **Engine**: the paper worker is a separate process with drawdown, expiry, policy and lease hard stops. It remains the default execution path.
- **AlphaFox transport**: the optional adapter uses the official AlphaFox CLI and its eight catalog operations. An isolated Paper trader was created and auto-started only after authorization and human approval, then stopped with server readback confirming `runtime.state: stopped`. OAuth credentials stay in the OS keychain; mutations remain opt-in.
- **Human gate**: a local camera preview plus an explicit confirmation button. No image is captured, uploaded or stored, and no face recognition or KYC is claimed. Approval time, method and session live in the persisted application passport and audit log; StrategyPassport v2 stores the frozen mandate confirmation but not those three metadata fields on-chain.
- **WayToWeb4 mock transport**: `backend/app/waytoweb4_mock.py` exposes the teammate's clean REST swap point (`/v1/leaders`, `/v1/paper/start`, `/v1/paper/{id}/pnl`, `/v1/paper/{id}/stop`) for the production integration described in `docs/reproduce.md`.
- **Reference contract**: [`contracts/PassportRegistry.sol`](contracts/PassportRegistry.sol) is not deployed; the isolated v2 chain worker remains the executable local/testnet path.

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
