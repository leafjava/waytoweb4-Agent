"""Engine tests."""

from __future__ import annotations
import time

from .helpers import prepare, prepare_confirm_mint, verify_face
from backend.app.engine import _WORKERS
from backend.app.deps import get_execution_adapter
from backend.app.policy import write_policy


def _mint_and_face(client) -> str:
    body = prepare_confirm_mint(client)
    pid = body["passport_id"]
    verify_face(client, pid)
    return pid


def test_engine_start_requires_authorized_passport(client):
    pid = prepare(client)["passport_id"]
    r = client.post("/api/engine/start", json={"passport_id": pid})
    assert r.status_code == 409


def test_engine_start_requires_face_gate_after_authorization(client):
    body = prepare_confirm_mint(client)
    response = client.post("/api/engine/start", json={"passport_id": body["passport_id"]})
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "FACE_GATE_REQUIRED"


def test_engine_start_and_tick(client):
    pid = _mint_and_face(client)
    r = client.post("/api/engine/start", json={"passport_id": pid})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "active"
    assert body["drawdown_usd"] == 0.0
    assert client.get(f"/api/passport/{pid}").json()["face_gate_status"] == "consumed"


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


def test_engine_stop_stops_then_revokes(client):
    pid = _mint_and_face(client)
    client.post("/api/engine/start", json={"passport_id": pid})
    r = client.post("/api/engine/stop", json={"passport_id": pid})
    assert r.status_code == 200
    pr = client.get(f"/api/passport/{pid}").json()
    assert pr["status"] == "revoked"
    assert pr["tx_revoke_hash"] is None
    assert pr["stop_requested"] is True
    assert pr["face_verified"] is True
    assert pr["face_gate_status"] == "invalidated"
    assert pr["face_gate_invalidated_at"]
    assert pr["face_gate_invalidation_reason"] == "STOP_REQUESTED"
    events = client.get("/api/state").json()["events"]
    assert sum(event["kind"] == "face_gate_invalidated" for event in events) == 1
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
    assert record["face_gate_status"] == "invalidated"
    assert record["face_gate_invalidation_reason"] == "POLICY_REVOKED"


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


def test_alphafox_adapter_runs_only_after_human_gate(app_and_state):
    from fastapi.testclient import TestClient

    app, _state = app_and_state

    class Adapter:
        provider = "alphafox"

        def __init__(self): self.calls = []
        async def start(self, command):
            self.calls.append(("start", command.leader_id, command.paper))
            return "trader-demo-1"
        async def stop(self, trader_id): self.calls.append(("stop", trader_id))

    adapter = Adapter()
    app.dependency_overrides[get_execution_adapter] = lambda: adapter
    with TestClient(app) as local_client:
        body = prepare_confirm_mint(local_client)
        pid = body["passport_id"]
        assert local_client.post("/api/engine/start", json={"passport_id": pid}).status_code == 409
        assert adapter.calls == []
        verify_face(local_client, pid)
        assert local_client.post("/api/engine/start", json={"passport_id": pid}).status_code == 200
        record = local_client.get(f"/api/passport/{pid}").json()
        assert record["external_execution_id"] == "trader-demo-1"
        assert adapter.calls[0][0] == "start"
        assert local_client.post("/api/engine/stop", json={"passport_id": pid}).status_code == 200
        assert adapter.calls[-1] == ("stop", "trader-demo-1")


def test_alphafox_uncertain_start_invalidates_mandate(app_and_state):
    from fastapi.testclient import TestClient

    app, _state = app_and_state

    class FailingAdapter:
        provider = "alphafox"
        async def start(self, command): raise RuntimeError("outcome uncertain")
        async def stop(self, trader_id): raise AssertionError("no id was returned")

    app.dependency_overrides[get_execution_adapter] = lambda: FailingAdapter()
    with TestClient(app) as local_client:
        body = prepare_confirm_mint(local_client)
        pid = body["passport_id"]
        verify_face(local_client, pid)
        response = local_client.post("/api/engine/start", json={"passport_id": pid})
        assert response.status_code == 409
        assert response.json()["detail"]["code"] == "ALPHAFOX_START_FAILED"
        record = local_client.get(f"/api/passport/{pid}").json()
        assert record["status"] == "uncertain"
        assert record["authorization_status"] == "uncertain"
        assert record["face_gate_status"] == "invalidated"
        assert record["stop_requested"] is True
