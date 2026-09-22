"""Face gate tests."""

from __future__ import annotations

from .helpers import prepare_confirm_mint


def test_face_verify_flips_flag(client):
    body = prepare_confirm_mint(client)
    pid = body["passport_id"]
    r = client.post("/api/face/verify", json={"passport_id": pid})
    assert r.status_code == 200
    pr = client.get(f"/api/passport/{pid}").json()
    assert pr["face_verified"] is True


def test_face_verify_unknown_returns_404(client):
    r = client.post("/api/face/verify", json={"passport_id": "0xnope"})
    assert r.status_code == 404
