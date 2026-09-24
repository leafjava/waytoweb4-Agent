#!/usr/bin/env python3
"""PRD §5 two-run controlled experiment.

Run 1: 500 USD notional / 50 loss cap  -> rule-gate trips at limit.
Run 2: 100 USD notional / 10 loss cap  -> same gate, tighter budget.

Both runs use the existing /api/* endpoints (no backend changes).
Output: prints Run1/Run2 summary to stdout and writes
`runs/two_runs_*.json` for the frontend ConditionalRunPanel to pick up.

NOTE on the offline MockKilnClient: the demo's MockKilnClient always
returns a single canned Spec (notional=500, maxLoss=50) regardless of
user input. That's deliberate for the demo flow but it would make both
runs identical. So Run 2 sends a *constructed* Spec dict directly to
/api/passport/mint -- the backend still re-validates it with
CopyTradingSpec.model_validate, so the security story is unchanged.

Usage:
    python scripts/two_runs_demo.py [--base http://localhost:8000]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = ROOT / "frontend" / "public" / "runs"


def _iso_future(hours: int = 48) -> str:
    # Drop microseconds -- the CopyTradingSpec validator parses with
    # fromisoformat() and rejects the 6-digit fractional second form on
    # some platforms.
    dt = datetime.now(timezone.utc).replace(microsecond=0) + __import__("datetime").timedelta(hours=hours)
    s = dt.isoformat()
    return s.replace("+00:00", "Z") if s.endswith("+00:00") else s


def _post(client, path, body=None):
    r = client.post(path, json=body or {})
    r.raise_for_status()
    return r.json()


def _run_one(client, label, notional, max_loss, tick_amount):
    """Run a complete paper-copy flow once. Returns the result dict."""
    print(f"\n=== {label}: notional={notional}, maxLoss={max_loss}, tick={tick_amount} ===")

    # 1. reset state
    _post(client, "/api/state/reset")

    # 2. Build the spec directly. The offline MockKilnClient returns a
    # hard-coded 500/50 spec; we bypass it so Run 2 can differ.
    spec = {
        "mode": "copy",
        "leaderId": "leader-demo-001",
        "venue": "paper",
        "notionalUsd": float(notional),
        "maxLossUsd": float(max_loss),
        "expiry": _iso_future(48),
        "faceVerified": False,
        "paper": True,
    }

    # 3. mint (the backend re-validates this with CopyTradingSpec)
    minted = _post(client, "/api/passport/mint", {"spec": spec})

    # 4. face verify
    _post(client, "/api/face/verify", {"passport_id": minted["passport_id"]})

    # 5. start engine
    _post(client, "/api/engine/start", {"passport_id": minted["passport_id"]})

    # 6. tick drawdown to the limit (rule gate fires)
    _post(
        client,
        f"/api/engine/tick?amount={tick_amount}",
        {"passport_id": minted["passport_id"]},
    )

    # 7. judge (no events -> rule gate alone)
    judge = _post(
        client,
        "/api/redline/judge",
        {"passport_id": minted["passport_id"]},
    )

    # 8. read back
    time.sleep(0.3)
    state = client.get("/api/state").json()
    p = state["passports"][minted["passport_id"]]

    result = {
        "label": label,
        "spec": spec,
        "passport_id": minted["passport_id"],
        "mint_tx_hash": minted["tx_hash"],
        "drawdown_usd": p["drawdown_usd"],
        "max_loss_usd": p["max_loss_usd"],
        "status": p["status"],
        "verdict_level": judge["verdict"]["level"],
        "verdict_codes": judge["verdict"]["reason_codes"],
        "verdict_source": judge["verdict"]["source"],
        "revoke_tx_hash": p.get("tx_revoke_hash") or None,
        "side_effects": judge.get("side_effects") or {},
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8000")
    args = parser.parse_args()

    with httpx.Client(base_url=args.base, timeout=15.0) as client:
        try:
            client.get("/api/health").raise_for_status()
        except Exception as e:
            print(f"ERROR: backend not reachable at {args.base}: {e}", file=sys.stderr)
            sys.exit(1)

        runs = [
            ("Run 1 (500U / 50 loss)", 500, 50, 50),
            ("Run 2 (100U / 10 loss)", 100, 10, 10),
        ]
        results = []
        for label, n, ml, tick in runs:
            results.append(_run_one(client, label, n, ml, tick))

    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_file = RUNS_DIR / f"two_runs_{ts}.json"
    payload = {
        "ts": ts,
        "runs": results,
        "summary": {
            "both_tripped": all(r["verdict_level"] == "TRIP" for r in results),
            "both_revoked": all(r["status"] == "revoked" for r in results),
            "rule_gate_only": all(r["verdict_source"] == "rule_gate" for r in results),
        },
    }
    out_file.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSaved: {out_file}")


if __name__ == "__main__":
    main()