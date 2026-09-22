"""Engine tests."""

from __future__ import annotations


def _mint_and_face(client) -> str:
    payload = {
        "spec": {
            "mode": "copy",
            "leaderId": "leader-demo-001",
            "venue": "paper",
            "notionalUsd": 500,
            "maxLossUsd": 50,
            "expiry": "2099-01-01T00:00:00+00:00",
            "faceVerified": False,
            "paper": True,
        }
    }
    body = client.post("/api/passport/mint", json=payload).json()
    pid = body["passport_id"]
    client.post("/api/face/verify", json={"passport_id": pid})
    return pid


def test_engine_start_requires_face_verified(client):
    payload = {
        "spec": {
            "mode": "copy",
            "leaderId": "leader-demo-001",
            "venue": "paper",
            "notionalUsd": 500,
            "maxLossUsd": 50,
            "expiry": "2099-01-01T00:00:00+00:00",
            "faceVerified": False,
            "paper": True,
        }
    }
    pid = client.post("/api/passport/mint", json=payload).json()["passport_id"]
    r = client.post("/api/engine/start", json={"passport_id": pid})
    assert r.status_code == 409  # face not verified


def test_engine_start_and_tick(client):
    pid = _mint_and_face(client)
    r = client.post("/api/engine/start", json={"passport_id": pid})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] in {"active", "pending_face"}
    assert body["drawdown_usd"] == 0.0


def test_tick_advances_drawdown(client):
    pid = _mint_and_face(client)
    client.post("/api/engine/start", json={"passport_id": pid})
    r = client.post(f"/api/engine/tick?amount=25", json={"passport_id": pid})
    assert r.status_code == 200
    body = r.json()
    assert body["drawdown_usd"] == 25.0
    assert body["max_loss_usd"] == 50.0


def test_tick_clamps_to_max_loss(client):
    pid = _mint_and_face(client)
    client.post("/api/engine/start", json={"passport_id": pid})
    r = client.post(f"/api/engine/tick?amount=999", json={"passport_id": pid})
    assert r.status_code == 200
    body = r.json()
    assert body["drawdown_usd"] == 50.0  # clamped to maxLossUsd


def test_engine_stop_does_not_revoke(client):
    pid = _mint_and_face(client)
    client.post("/api/engine/start", json={"passport_id": pid})
    r = client.post("/api/engine/stop", json={"passport_id": pid})
    assert r.status_code == 200
    pr = client.get(f"/api/passport/{pid}").json()
    assert pr["status"] == "stopped"
    assert pr["tx_revoke_hash"] is None