"""State + reset tests."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from backend.app.deps import get_passport_backend
from backend.app.engine import _WORKERS
from backend.app.state import AppState
from .helpers import prepare, prepare_confirm_mint, verify_face


def test_state_snapshot_shape(client):
    r = client.get("/api/state")
    assert r.status_code == 200
    body = r.json()
    assert "passports" in body
    assert "events" in body
    assert "token_report" in body


def test_tokens_endpoint_returns_markdown(client):
    r = client.get("/api/state/tokens")
    assert r.status_code == 200
    assert "flow" in r.text
    assert "tokens_in" in r.text


def test_reset_wipes_everything(client):
    prepare(client)
    assert client.get("/api/state").json()["passports"] != {}

    r = client.post("/api/state/reset")
    assert r.status_code == 200
    assert client.get("/api/state").json()["passports"] == {}


def test_reset_stops_worker_before_wiping_state(client):
    body = prepare_confirm_mint(client)
    passport_id = body["passport_id"]
    verify_face(client, passport_id)
    assert client.post("/api/engine/start", json={"passport_id": passport_id}).status_code == 200
    assert passport_id in _WORKERS

    assert client.post("/api/state/reset").status_code == 200
    assert passport_id not in _WORKERS
    assert client.get("/api/state").json()["passports"] == {}


def test_reset_is_disabled_for_chain_runs(client):
    client.app.dependency_overrides[get_passport_backend] = lambda: SimpleNamespace(label="local")
    try:
        response = client.post("/api/state/reset")
        assert response.status_code == 409
    finally:
        client.app.dependency_overrides.pop(get_passport_backend, None)


def test_reset_is_disabled_for_live_kiln_runs(client, monkeypatch):
    monkeypatch.setenv("KILN_MODE", "live")
    response = client.post("/api/state/reset")
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_restart_reconciliation_fails_closed(client, fresh_state):
    body = prepare_confirm_mint(client)
    record = fresh_state.passports[body["passport_id"]]
    record.engine_running = True
    record.engine_status = "running"
    record.status = "active"
    fresh_state.upsert_passport(record)

    loaded = AppState(fresh_state.ledger_path)
    loaded.load()
    await loaded.reconcile_after_restart()
    recovered = loaded.passports[record.passport_id]
    assert recovered.engine_running is False
    assert recovered.authorization_status == "revoked"
    assert recovered.stop_reason == "PROCESS_RESTART"
    assert any(event.kind == "restart_reconcile" for event in loaded.events)


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["kiln"] in {"mock", "http", "misconfigured"}
    assert body["passport_backend"] in {"mock", "local", "testnet"}
