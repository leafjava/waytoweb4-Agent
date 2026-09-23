"""RedLine tests."""

from __future__ import annotations

from .helpers import prepare_confirm_mint, verify_face
from agent.redline_agent import KilnEventClassifier
from backend.app.deps import get_redline_judge


def _mint_and_face(client) -> str:
    body = prepare_confirm_mint(client)
    pid = body["passport_id"]
    verify_face(client, pid)
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


def test_live_mode_wires_kiln_classifier(monkeypatch):
    monkeypatch.setenv("KILN_MODE", "live")
    monkeypatch.setenv("KILN_API_KEY", "test-key")
    judge = get_redline_judge()
    assert isinstance(judge.classifier, KilnEventClassifier)
