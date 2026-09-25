#!/usr/bin/env python3
"""Execute one explicit StrategyPassport lifecycle on a public testnet."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4


def load_env(path: Path) -> None:
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ[key.strip()] = value.strip()


def post(client, path: str, body: dict) -> dict:
    response = client.post(path, json=body)
    if response.status_code >= 400:
        raise RuntimeError(f"{path} failed ({response.status_code}): {response.text}")
    return response.json()


def save_contract_address(path: Path, address: str) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    replacement = f"PASSPORT_ADDRESS={address}"
    updated = False
    for index, line in enumerate(lines):
        if line.startswith("PASSPORT_ADDRESS="):
            lines[index] = replacement
            updated = True
            break
    if not updated:
        lines.append(replacement)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(env_file: Path, output: Path) -> dict:
    load_env(env_file)
    os.environ.update({
        "PASSPORT_BACKEND": "testnet",
        "EXECUTION_BACKEND": "paper",
        "KILN_MODE": "offline",
        "CHAIN_JOURNAL_DIR": str((output.parent / "chain-journal").resolve()),
    })
    if os.environ.get("CHAIN_ID") != "11155111":
        raise RuntimeError("this field script is locked to Sepolia chain 11155111")

    # Configuration is read during these imports, after the environment is set.
    from fastapi.testclient import TestClient

    from backend.app.deps import get_state
    from backend.app.main import create_app
    from backend.app.policy import write_policy
    from backend.app.state import AppState

    root = output.parent / f"run-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    state = AppState(root / "ledger.json")
    leader_id = "leader-demo-001"
    write_policy(root / "policy.json", 1, [leader_id])
    spec = {
        "mode": "copy",
        "leaderId": leader_id,
        "venue": "paper",
        "notionalUsd": 500,
        "maxLossUsd": 50,
        "expiry": (datetime.now(timezone.utc) + timedelta(hours=48)).replace(microsecond=0).isoformat(),
        "faceVerified": False,
        "paper": True,
    }

    app = create_app()
    app.state.app_state = state
    app.dependency_overrides[get_state] = lambda: state
    prefix = str(uuid4())
    with TestClient(app) as client:
        prepared = post(client, "/api/passport/prepare", {
            "spec": spec, "request_id": f"{prefix}-prepare",
        })
        post(client, "/api/passport/confirm", {
            "passport_id": prepared["passport_id"],
            "spec_hash": prepared["spec_hash"],
            "request_id": f"{prefix}-confirm",
        })
        minted = post(client, "/api/passport/mint", {
            "passport_id": prepared["passport_id"],
            "request_id": f"{prefix}-mint",
        })
        after_mint = client.get(f"/api/passport/{prepared['passport_id']}").json()
        if not after_mint.get("tx_mint_hash") or after_mint.get("chain_id") != 11155111:
            raise RuntimeError(f"mint evidence incomplete: {after_mint}")

        post(client, "/api/face/verify", {
            "passport_id": prepared["passport_id"],
            "method": "button",
            "session_id": str(uuid4()),
        })
        post(client, "/api/engine/start", {"passport_id": prepared["passport_id"]})
        stopped = post(client, "/api/engine/stop", {"passport_id": prepared["passport_id"]})
        final = client.get(f"/api/passport/{prepared['passport_id']}").json()
        if not final.get("tx_revoke_hash") or final.get("authorization_status") != "revoked":
            raise RuntimeError(f"revoke evidence incomplete: {final}")

    app.dependency_overrides.clear()
    save_contract_address(env_file, final["contract_address"])
    result = {
        "verified_at": datetime.now(timezone.utc).isoformat(),
        "network": "Sepolia",
        "chain_id": final["chain_id"],
        "contract_address": final["contract_address"],
        "passport_id": final["passport_id"],
        "chain_passport_id": final["chain_passport_id"],
        "spec_hash": final["spec_hash"],
        "mint_tx_hash": final["tx_mint_hash"],
        "revoke_tx_hash": final["tx_revoke_hash"],
        "authorization_status": final["authorization_status"],
        "engine_status": final["engine_status"],
        "face_gate_status": final["face_gate_status"],
        "stop_status": stopped["status"],
        "evidence_dir": str(state.evidence.dir if state.evidence else ""),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--env-file", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("artifacts/testnet-field/result.json"))
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("refusing public-testnet mutation without --execute")
    print(json.dumps(run(args.env_file, args.output), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
