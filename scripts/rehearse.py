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


def run(output: str | Path) -> dict:
    root = Path(output); root.mkdir(parents=True, exist_ok=True)
    comparison_id = str(uuid4())
    app = create_app(); state = AppState(root / "ledger.json")
    app.state.app_state = state
    app.dependency_overrides[get_state] = lambda: state
    with TestClient(app) as client:
            spec = valid_spec()
            first = _prepare(client, spec, "round-a")
            client.post("/api/face/verify", json={"passport_id": first["passport_id"]})
            write_policy(state.ledger_path.parent / "policy.json", 1, [spec["leaderId"]])
            client.post("/api/engine/start", json={"passport_id": first["passport_id"]})
            client.post("/api/engine/tick?amount=10", json={"passport_id": first["passport_id"]})
            client.post("/api/engine/stop", json={"passport_id": first["passport_id"]})
            first_state = client.get(f"/api/passport/{first['passport_id']}").json()

            second = _prepare(client, spec, "round-b")
            client.post("/api/face/verify", json={"passport_id": second["passport_id"]})
            client.post("/api/engine/start", json={"passport_id": second["passport_id"]})
            write_policy(state.ledger_path.parent / "policy.json", 2, [])
            second_state = {}
            for _ in range(50):
                second_state = client.get(f"/api/passport/{second['passport_id']}").json()
                if second_state.get("engine_status") == "stopped": break
                time.sleep(0.02)
            assert second_state.get("stop_reason") == "POLICY_REVOKED", second_state
            comparison = {"comparison_id": comparison_id, "source_mode": "offline", "round_a": first_state, "round_b": second_state, "policy_change": {"before": [spec["leaderId"]], "after": [], "version": 2}}
            (root / "comparison.json").write_text(json.dumps(comparison, indent=2), encoding="utf-8")
            evidence_dir = state.evidence.dir if state.evidence else None
            if evidence_dir: (root / "evidence-path.txt").write_text(str(evidence_dir), encoding="utf-8")
            app.dependency_overrides.clear()
            return comparison


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--mode", choices=["offline", "live"], default="offline"); parser.add_argument("--output", default="artifacts/rehearsal")
    args = parser.parse_args()
    if args.mode != "offline": raise SystemExit("live rehearsal requires explicit field credentials and is not enabled by this local build")
    print(json.dumps(run(args.output), indent=2))
