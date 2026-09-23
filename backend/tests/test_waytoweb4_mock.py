"""Tests for the waytoweb4 REST-shaped mock router."""

from __future__ import annotations


def _start_payload(**overrides):
    base = {
        "leader_id": "leader-demo-001",
        "notional_usd": 500,
        "max_loss_usd": 50,
        "expiry_iso": "2099-01-01T00:00:00+00:00",
        "venue": "paper",
    }
    base.update(overrides)
    return base


def test_list_leaders_returns_seed(client):
    r = client.get("/v1/leaders")
    assert r.status_code == 200
    body = r.json()
    assert "leaders" in body
    assert len(body["leaders"]) >= 1
    ids = [l["leader_id"] for l in body["leaders"]]
    assert "leader-demo-001" in ids


def test_list_leader_positions_is_always_empty(client):
    r = client.get("/v1/leaders/leader-demo-001/positions")
    assert r.status_code == 200
    assert r.json() == {"leader_id": "leader-demo-001", "positions": []}


def test_start_paper_returns_paper_id_and_status(client):
    r = client.post("/v1/paper/start", json=_start_payload())
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "active"
    assert body["paper_id"].startswith("0x")
    assert body["trip_seconds"] >= 1


def test_start_paper_rejects_non_paper_venue(client):
    r = client.post("/v1/paper/start", json=_start_payload(venue="binance"))
    assert r.status_code == 422


def test_start_paper_rejects_max_loss_over_notional(client):
    r = client.post("/v1/paper/start", json=_start_payload(notional_usd=100, max_loss_usd=999))
    assert r.status_code == 422


def test_get_paper_pnl_returns_drawdown(client):
    started = client.post("/v1/paper/start", json=_start_payload()).json()
    pid = started["paper_id"]
    r = client.get(f"/v1/paper/{pid}/pnl")
    assert r.status_code == 200
    body = r.json()
    assert body["paper_id"] == pid
    assert body["drawdown_usd"] == 0.0  # engine just started
    assert body["status"] == "active"
    assert body["engine_running"] is True


def test_get_paper_pnl_unknown_returns_404(client):
    r = client.get("/v1/paper/0xnope/pnl")
    assert r.status_code == 404


def test_stop_paper_user_halts_engine(client):
    started = client.post("/v1/paper/start", json=_start_payload()).json()
    pid = started["paper_id"]
    r = client.post(f"/v1/paper/{pid}/stop", json={"reason": "user"})
    assert r.status_code == 200
    assert r.json()["status"] == "stopped"
    # No revoke tx hash -- user halt does not burn passport
    assert r.json().get("revoke_tx_hash") is None


def test_stop_paper_kill_revokes_passport(client):
    started = client.post("/v1/paper/start", json=_start_payload()).json()
    pid = started["paper_id"]
    r = client.post(f"/v1/paper/{pid}/stop", json={"reason": "kill"})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "revoked"
    assert body.get("revoke_tx_hash", "").startswith("0x")
    # passport state mirrors the kill
    r2 = client.get(f"/api/passport/{pid}")
    assert r2.status_code == 200
    assert r2.json()["status"] == "revoked"
    assert r2.json()["tx_revoke_hash"] is not None


def test_stop_paper_unknown_returns_404(client):
    r = client.post("/v1/paper/0xnope/stop", json={"reason": "user"})
    assert r.status_code == 404