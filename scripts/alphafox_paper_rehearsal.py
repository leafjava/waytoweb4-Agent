#!/usr/bin/env python3
"""Run one authorized AlphaFox Paper create/start/stop field rehearsal.

This script intentionally requires ``--execute``. It never handles OAuth
tokens; the AlphaFox CLI reads them from the operating-system keychain.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4


def _post(client, path: str, body: dict) -> dict:
    response = client.post(path, json=body)
    if response.status_code >= 400:
        raise RuntimeError(f"{path} failed ({response.status_code}): {response.text}")
    return response.json()


def run(connector_id: str, signal_source_id: str, output: Path) -> dict:
    # Import only after the caller has supplied the explicit AlphaFox settings.
    from fastapi.testclient import TestClient

    from backend.app.deps import get_state
    from backend.app.main import create_app
    from backend.app.policy import write_policy
    from backend.app.state import AppState

    expiry = (datetime.now(timezone.utc) + timedelta(hours=48)).replace(microsecond=0).isoformat()
    spec = {
        "mode": "copy",
        "leaderId": signal_source_id,
        "venue": "paper",
        "notionalUsd": 500,
        "maxLossUsd": 50,
        "expiry": expiry,
        "faceVerified": False,
        "paper": True,
    }

    with TemporaryDirectory(prefix="w2w4-alphafox-field-") as tmp:
        root = Path(tmp)
        state = AppState(root / "ledger.json")
        write_policy(root / "policy.json", 1, [signal_source_id])
        app = create_app()
        app.state.app_state = state
        app.dependency_overrides[get_state] = lambda: state

        with TestClient(app) as client:
            prefix = str(uuid4())
            prepared = _post(client, "/api/passport/prepare", {
                "spec": spec, "request_id": f"{prefix}-prepare",
            })
            _post(client, "/api/passport/confirm", {
                "passport_id": prepared["passport_id"],
                "spec_hash": prepared["spec_hash"],
                "request_id": f"{prefix}-confirm",
            })
            _post(client, "/api/passport/mint", {
                "passport_id": prepared["passport_id"],
                "request_id": f"{prefix}-mint",
            })

            blocked = client.post("/api/engine/start", json={"passport_id": prepared["passport_id"]})
            if blocked.status_code != 409 or blocked.json().get("detail", {}).get("code") != "FACE_GATE_REQUIRED":
                raise RuntimeError(f"pre-gate start did not fail closed: {blocked.status_code} {blocked.text}")

            approval_session = str(uuid4())
            _post(client, "/api/face/verify", {
                "passport_id": prepared["passport_id"],
                "method": "button",
                "session_id": approval_session,
            })
            started = _post(client, "/api/engine/start", {"passport_id": prepared["passport_id"]})
            running = client.get(f"/api/passport/{prepared['passport_id']}").json()
            if running.get("external_execution_status") != "running":
                raise RuntimeError(f"AlphaFox trader did not reach running: {running}")

            stopped = _post(client, "/api/engine/stop", {"passport_id": prepared["passport_id"]})
            final = client.get(f"/api/passport/{prepared['passport_id']}").json()
            if final.get("external_execution_status") != "stopped":
                raise RuntimeError(f"AlphaFox trader did not stop cleanly: {final}")

        app.dependency_overrides.clear()

    result = {
        "verified_at": datetime.now(timezone.utc).isoformat(),
        "mode": "paper",
        "connector_id": connector_id,
        "signal_source_id": signal_source_id,
        "passport_id": final["passport_id"],
        "spec_hash": final["spec_hash"],
        "pre_gate_start_code": "FACE_GATE_REQUIRED",
        "approval_session_id": approval_session,
        "trader_id": final["external_execution_id"],
        "start_status": started["status"],
        "stop_status": stopped["status"],
        "external_execution_status": final["external_execution_status"],
        "passport_status": final["authorization_status"],
        "mint_tx_hash": final.get("tx_mint_hash"),
        "revoke_tx_hash": final.get("tx_revoke_hash"),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--connector-id", required=True)
    parser.add_argument("--signal-source-id", required=True)
    parser.add_argument("--output", type=Path, default=Path("artifacts/alphafox-field/result.json"))
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("refusing AlphaFox mutation without --execute")

    os.environ.update({
        "EXECUTION_BACKEND": "alphafox",
        "PASSPORT_BACKEND": "mock",
        "KILN_MODE": "offline",
        "ALPHAFOX_PAPER_CONNECTOR_ID": args.connector_id,
        "ALPHAFOX_LEVERAGE": "1",
        "ALPHAFOX_STOP_CLOSE_POSITIONS": "true",
    })
    print(json.dumps(run(args.connector_id, args.signal_source_id, args.output), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
