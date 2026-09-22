"""RedLine tests."""

from __future__ import annotations

from .helpers import prepare_confirm_mint


def _mint_and_face(client) -> str:
    body = prepare_confirm_mint(client)
    pid = body["passport_id"]
    client.post("/api/face/verify", json={"passport_id": pid})
    client.post("/api/engine/start", json={"passport_id": pid})
    return pid


def test_redline_judge_no_events_returns_hold(client):
    pid = _mint_and_face(client)
    r = client.post("/api/redline/judge", json={"passport_id": pid})
    assert r.status_code == 200
    body = r.json()
    assert body["verdict"]["level"] == "HOLD"
    assert body["flow"] == "redline_hold"


def test_redline_inject_hynix_trips(client):
    pid = _mint_and_face(client)
    r = client.post("/api/redline/inject/hynix", json={"passport_id": pid})
    assert r.status_code == 200
    body = r.json()
    assert body["verdict"]["level"] == "TRIP"
    assert body["flow"] == "redline_trip"
    # Offline side effects are explicit and never masquerade as a transaction.
    assert body["side_effects"]["revoked"] is True
    assert body["side_effects"]["revoke_tx_hash"] is None
    # passport is now revoked
    pr = client.get(f"/api/passport/{pid}").json()
    assert pr["status"] == "revoked"
    assert pr["tx_revoke_hash"] is None


def test_redline_judge_unknown_returns_404(client):
    r = client.post("/api/redline/judge", json={"passport_id": "0xnope"})
    assert r.status_code == 404
