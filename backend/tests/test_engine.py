"""Engine tests."""

from __future__ import annotations

from .helpers import prepare, prepare_confirm_mint


def _mint_and_face(client) -> str:
    body = prepare_confirm_mint(client)
    pid = body["passport_id"]
    client.post("/api/face/verify", json={"passport_id": pid})
    return pid


def test_engine_start_requires_authorized_passport(client):
    pid = prepare(client)["passport_id"]
    r = client.post("/api/engine/start", json={"passport_id": pid})
    assert r.status_code == 409


def test_engine_start_and_tick(client):
    pid = _mint_and_face(client)
    r = client.post("/api/engine/start", json={"passport_id": pid})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "active"
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


def test_engine_stop_is_terminal_before_revoke(client):
    pid = _mint_and_face(client)
    client.post("/api/engine/start", json={"passport_id": pid})
    r = client.post("/api/engine/stop", json={"passport_id": pid})
    assert r.status_code == 200
    pr = client.get(f"/api/passport/{pid}").json()
    assert pr["status"] == "stopped"
    assert pr["tx_revoke_hash"] is None
    assert pr["stop_requested"] is True
    assert client.post("/api/engine/start", json={"passport_id": pid}).status_code == 409
