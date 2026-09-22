"""Passport mint / revoke tests."""

from __future__ import annotations

import pytest


def _mint(client, spec_extra: dict | None = None) -> dict:
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
            **(spec_extra or {}),
        }
    }
    r = client.post("/api/passport/mint", json=payload)
    assert r.status_code == 200, r.text
    return r.json()


def test_mint_returns_valid_hash(client):
    body = _mint(client)
    assert body["passport_id"].startswith("0x")
    assert len(body["tx_hash"]) == 66
    assert body["backend"] in {"mock", "sepolia"}


def test_mint_rejects_mode_grid_bot(client):
    payload = {
        "spec": {
            "mode": "grid_bot",
            "leaderId": "leader-demo-001",
            "venue": "paper",
            "notionalUsd": 500,
            "maxLossUsd": 50,
            "expiry": "2099-01-01T00:00:00+00:00",
            "faceVerified": False,
            "paper": True,
        }
    }
    r = client.post("/api/passport/mint", json=payload)
    assert r.status_code == 422


def test_mint_rejects_max_loss_above_notional(client):
    payload = {
        "spec": {
            "mode": "copy",
            "leaderId": "leader-demo-001",
            "venue": "paper",
            "notionalUsd": 100,
            "maxLossUsd": 999,
            "expiry": "2099-01-01T00:00:00+00:00",
            "faceVerified": False,
            "paper": True,
        }
    }
    r = client.post("/api/passport/mint", json=payload)
    assert r.status_code == 422


def test_mint_strips_face_verified_even_if_client_claims_true(client):
    # The spec claims faceVerified=true; server must force false.
    body = _mint(client, spec_extra={"faceVerified": True})
    # Backend still mints, but face_verified on the record is False.
    r = client.get(f"/api/passport/{body['passport_id']}")
    assert r.status_code == 200
    assert r.json()["face_verified"] is False


def test_revoke_returns_distinct_tx_hash(client):
    body = _mint(client)
    r = client.post(f"/api/passport/{body['passport_id']}/revoke")
    assert r.status_code == 200
    rev = r.json()
    assert rev["status"] == "revoked"
    assert rev["tx_hash"] != body["tx_hash"]


def test_revoke_twice_returns_409(client):
    body = _mint(client)
    client.post(f"/api/passport/{body['passport_id']}/revoke")
    r = client.post(f"/api/passport/{body['passport_id']}/revoke")
    assert r.status_code == 409


def test_revoke_unknown_returns_404(client):
    r = client.post("/api/passport/0xdeadbeef/revoke")
    assert r.status_code == 404