"""Run the two offline Challenge-A authorization scenarios."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.app.deps import get_state
from backend.app.main import create_app
from backend.app.policy import write_policy
from backend.app.state import AppState


def valid_spec():
    return {"mode": "copy", "leaderId": "leader-demo-001", "venue": "paper", "notionalUsd": 500, "maxLossUsd": 50, "expiry": "2099-01-01T00:00:00+00:00", "faceVerified": False, "paper": True}


def _prepare(client, spec, prefix):
    prepared = client.post("/api/passport/prepare", json={"spec": spec, "request_id": f"{prefix}-prepare"}).json()
    client.post("/api/passport/confirm", json={"passport_id": prepared["passport_id"], "spec_hash": prepared["spec_hash"], "request_id": f"{prefix}-confirm"})
    minted = client.post("/api/passport/mint", json={"passport_id": prepared["passport_id"], "request_id": f"{prefix}-mint"})
    assert minted.status_code == 200, minted.text
    return minted.json()


def _run_round(root: Path, name: str, spec: dict, policy_revoked: bool):
    round_root = root / name
    app = create_app()
    state = AppState(round_root / "ledger.json")
    app.state.app_state = state
    app.dependency_overrides[get_state] = lambda: state
    with TestClient(app) as client:
        passport = _prepare(client, spec, name)
        client.post("/api/face/verify", json={
            "passport_id": passport["passport_id"],
            "method": "button",
            "session_id": str(uuid4()),
        })
        write_policy(round_root / "policy.json", 1, [spec["leaderId"]])
        assert client.post("/api/engine/start", json={"passport_id": passport["passport_id"]}).status_code == 200
        if policy_revoked:
            write_policy(round_root / "policy.json", 2, [])
            record = {}
            for _ in range(50):
                record = client.get(f"/api/passport/{passport['passport_id']}").json()
                if record.get("engine_status") == "stopped":
                    break
                time.sleep(0.02)
            assert record.get("stop_reason") == "POLICY_REVOKED", record
        else:
            client.post("/api/engine/tick?amount=10", json={"passport_id": passport["passport_id"]})
            assert client.post("/api/engine/stop", json={"passport_id": passport["passport_id"]}).status_code == 200
            record = client.get(f"/api/passport/{passport['passport_id']}").json()
    app.dependency_overrides.clear()
    return record, state.evidence.dir if state.evidence else None


def run(output: str | Path) -> dict:
    root = Path(output)
    root.mkdir(parents=True, exist_ok=True)
    comparison_id = str(uuid4())
    spec = valid_spec()
    first_state, first_evidence = _run_round(root, "round-a", spec, False)
    second_state, second_evidence = _run_round(root, "round-b", spec, True)
    assert first_state["run_id"] != second_state["run_id"]
    assert first_state["spec_hash"] == second_state["spec_hash"]
    comparison = {
        "comparison_id": comparison_id,
        "source_mode": "offline",
        "round_a": first_state,
        "round_b": second_state,
        "policy_change": {"before": [spec["leaderId"]], "after": [], "version": 2},
    }
    (root / "comparison.json").write_text(json.dumps(comparison, indent=2), encoding="utf-8")
    paths = {"round_a": str(first_evidence), "round_b": str(second_evidence)}
    (root / "evidence-paths.json").write_text(json.dumps(paths, indent=2), encoding="utf-8")
    if second_evidence:
        (root / "evidence-path.txt").write_text(str(second_evidence), encoding="utf-8")
    return comparison


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--mode", choices=["offline", "live"], default="offline"); parser.add_argument("--output", default="artifacts/rehearsal")
    args = parser.parse_args()
    if args.mode != "offline": raise SystemExit("live rehearsal requires explicit field credentials and is not enabled by this local build")
    print(json.dumps(run(args.output), indent=2))
