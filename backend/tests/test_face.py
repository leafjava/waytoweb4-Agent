"""Face gate tests."""

from __future__ import annotations

from uuid import uuid4

from backend.app.state import AppState

from .helpers import prepare_confirm_mint, valid_spec, verify_face


def test_face_verify_flips_flag(client):
    body = prepare_confirm_mint(client)
    pid = body["passport_id"]
    session_id = uuid4()
    r = verify_face(client, pid, session_id)
    assert r.status_code == 200
    assert r.json()["method"] == "button"
    assert r.json()["session_id"] == str(session_id)
    pr = client.get(f"/api/passport/{pid}").json()
    assert pr["face_verified"] is True
    assert pr["face_verified_at"] == r.json()["verified_at"]
    assert pr["face_verification_method"] == "button"
    assert pr["face_verification_session_id"] == str(session_id)
    assert pr["face_gate_status"] == "active"


def test_face_verify_unknown_returns_404(client):
    r = verify_face(client, "0xnope")
    assert r.status_code == 404


def test_face_session_is_idempotent_but_cannot_cross_mandates(client):
    first = prepare_confirm_mint(client)["passport_id"]
    second = prepare_confirm_mint(
        client, valid_spec(leaderId="leader-demo-002")
    )["passport_id"]
    session_id = uuid4()
    one = verify_face(client, first, session_id)
    replay = verify_face(client, first, session_id)
    reused = verify_face(client, second, session_id)
    assert replay.status_code == 200
    assert replay.json() == one.json()
    assert reused.status_code == 409


def test_face_gate_fields_survive_reload(client, fresh_state):
    pid = prepare_confirm_mint(client)["passport_id"]
    response = verify_face(client, pid)
    loaded = AppState(ledger_path=fresh_state.ledger_path)
    loaded.load()
    record = loaded.passports[pid]
    assert record.face_verified_at == response.json()["verified_at"]
    assert record.face_verification_method == "button"
    assert record.face_verification_session_id == response.json()["session_id"]
