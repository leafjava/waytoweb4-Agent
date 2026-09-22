"""State + reset tests."""

from __future__ import annotations

from .helpers import prepare


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


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["kiln"] in {"mock", "http"}
    assert body["passport_backend"] in {"mock", "sepolia"}
