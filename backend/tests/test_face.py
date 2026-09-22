"""Face gate tests."""

from __future__ import annotations


def _mint(client) -> dict:
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
    r = client.post("/api/passport/mint", json=payload)
    assert r.status_code == 200
    return r.json()


def test_face_verify_flips_flag(client):
    body = _mint(client)
    pid = body["passport_id"]
    r = client.post("/api/face/verify", json={"passport_id": pid})
    assert r.status_code == 200
    pr = client.get(f"/api/passport/{pid}").json()
    assert pr["face_verified"] is True


def test_face_verify_unknown_returns_404(client):
    r = client.post("/api/face/verify", json={"passport_id": "0xnope"})
    assert r.status_code == 404