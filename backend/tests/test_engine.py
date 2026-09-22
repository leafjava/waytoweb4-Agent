"""Engine tests."""

from __future__ import annotations
import time

from .helpers import prepare, prepare_confirm_mint
from backend.app.engine import _WORKERS
from backend.app.policy import write_policy


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


def test_drawdown_limit_stops_without_judge_click(client):
    pid = _mint_and_face(client)
    client.post("/api/engine/start", json={"passport_id": pid})
    r = client.post(f"/api/engine/tick?amount=999", json={"passport_id": pid})
    assert r.status_code == 200
    body = r.json()
    assert body["drawdown_usd"] == 999.0
    for _ in range(30):
        record = client.get(f"/api/passport/{pid}").json()
        if record["engine_status"] == "stopped": break
        time.sleep(0.02)
    assert record["stop_reason"] == "DD_LIMIT"
    assert record["stop_requested"] is True


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


def test_policy_change_stops_worker_without_button(client, fresh_state):
    pid = _mint_and_face(client)
    assert client.post("/api/engine/start", json={"passport_id": pid}).status_code == 200
    write_policy(fresh_state.ledger_path.parent / "policy.json", 2, [])
    for _ in range(30):
        record = client.get(f"/api/passport/{pid}").json()
        if record["engine_status"] == "stopped": break
        time.sleep(0.02)
    assert record["stop_reason"] == "POLICY_REVOKED"


def test_controller_disconnect_stops_real_worker_process(client):
    pid = _mint_and_face(client)
    assert client.post("/api/engine/start", json={"passport_id": pid}).status_code == 200
    controller = _WORKERS[pid]
    client.portal.call(controller.process.stdin.close)
    for _ in range(50):
        record = client.get(f"/api/passport/{pid}").json()
        if record["engine_status"] == "stopped": break
        time.sleep(0.02)
    assert record["stop_reason"] == "CONTROLLER_DISCONNECTED"
    assert controller.process.returncode == 0
