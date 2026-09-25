# How to reproduce the demo

If you are a judge with 5 minutes and a shell, this is enough:

```bash
git clone <repo-url> waytoweb4-agent
cd waytoweb4-agent
bash scripts/reproduce.sh         # Linux / macOS / Git Bash
# or, on Windows PowerShell:
powershell -ExecutionPolicy Bypass -File scripts/reproduce.ps1
```

The script will:

1. Install Python + frontend deps.
2. Boot the FastAPI backend on `:8000`.
3. Boot the Vite dev server on `:5173`.
4. Run the **PRD §5 two-run controlled experiment** via
   `scripts/two_runs_demo.py`:
   - **Run 1**: 500 USD notional / 50 USD loss cap → rule-gate trips at limit.
   - **Run 2**: 100 USD notional / 10 USD loss cap → same gate, tighter budget.
   - Both runs end with `status: revoked` and `reason_codes: ["DD_LIMIT"]`
     from `rule_gate`. Mock mode records simulation IDs and leaves transaction
     hashes empty.
5. Write `./evidence.txt` containing the token / energy table and the latest
   controlled-run payload. Offline values remain clearly labelled.

Open <http://localhost:5173/> in your browser:

- The **Home** page shows the live system metrics, PRD §5 acceptance
  checklist, the four primitives, the spec simulator (with rule-gate
  + LLM predictions), the security architecture strip, and the live
  evidence panel.
- The **Demo** view has the chat panel, the locked Spec card, the
  passport card with mint/revoke hashes, the RedLine panel with drawdown
  gauge + verdict, and the **controlled-runs** comparison card.

## What to verify (5-point checklist)

| Acceptance check | Where to look |
|---|---|
| User need (NL delegation with kill switch) | Home → "Four primitives" |
| Agent vs code (what is LLM, what is Pydantic) | Home → "What the judges will check" |
| Kiln + token / flow split | Home → "Live system metrics" + "Live evidence" |
| ≥1 fresh public-testnet tx | Field run only; offline output must remain empty |
| 越权即停 (model cannot widen limit) | `agent/follow_agent/spec_schema.py` |
| Third-party audit (only passport + log needed) | `agent/redline_agent/rule_gate.py` + `docs/security-arch.md` |

## Honest disclaimer

- **Kiln**: defaults to `MockKilnClient`. Set `KILN_API_KEY` to switch to the real `gpt-oss-120b` endpoint.
- **Passport**: mock mode never fabricates a transaction hash. The guarded
  `testnet` mode can broadcast only with explicit RPC, wallet, chain and
  contract configuration; this reproduction stays offline.
- **Engine**: the default paper worker runs in a separate process. The optional
  AlphaFox adapter performs a CLI dry-run before any approved Paper mutation.
- **Face gate**: local camera preview plus an explicit confirmation button. No
  face recognition, KYC, image upload or image storage is claimed.

These are documented honestly in the top-level `README.md` so judges
can decide what to grade.

## Files of interest

- `agent/follow_agent/spec_schema.py` — locked CopyTradingSpec schema
- `agent/redline_agent/rule_gate.py` — drawdown hard gate
- `backend/app/main.py` — FastAPI app factory
- `backend/app/passport_backends/` — mock, local-EVM and guarded testnet paths
- `contracts/PassportRegistry.sol` — the Solidity target we did not deploy
- `scripts/two_runs_demo.py` — the controlled-run experiment
- `frontend/src/components/HomePage.jsx` — the landing page judges see first
