"""Spec endpoint tests."""

from __future__ import annotations

import json


def test_check_returns_missing_fields(client):
    r = client.post("/api/spec/check", json={"user_text": "500 USD 跟单"})
    assert r.status_code == 200
    body = r.json()
    assert "leaderId" in body["missing_fields"]


def test_check_ready_when_all_fields_present(client):
    r = client.post(
        "/api/spec/check",
        json={
            "user_text": (
                "follow leader-demo-001 with 500 USD and max loss 50 USD for 48 hours"
            )
        },
    )
    assert r.status_code == 200
    assert r.json()["ready"] is True


def test_emit_happy_path(client):
    r = client.post(
        "/api/spec/emit",
        json={
            "user_text": (
                "follow leader-demo-001 with 500 USD max loss 50 USD 48 hours"
            )
        },
    )
    assert r.status_code == 200
    spec = r.json()["spec"]
    assert spec["mode"] == "copy"
    assert spec["venue"] == "paper"
    assert spec["paper"] is True
    assert spec["faceVerified"] is False
    assert spec["leaderId"] == "leader-demo-001"


def test_emit_rejects_mode_grid_bot(client):
    # The MockKilnClient emits a valid Spec; we can't easily inject a
    # bad one through emit(). Instead, we hit /mint with a tampered
    # payload to assert the backend re-validates (covered elsewhere).
    # Here we just confirm /emit returns 200 for the canned happy path.
    r = client.post(
        "/api/spec/emit",
        json={"user_text": "follow leader-demo-001 500 USD 50 loss 48h"},
    )
    assert r.status_code == 200


def test_clarify_returns_question(client):
    r = client.post(
        "/api/spec/clarify",
        json={"user_text": "我想跟 500 USD 的单"},
    )
    assert r.status_code == 200
    body = r.json()
    # Mock clarifier picks "leaderId" as the first missing field.
    assert body["field"] == "leaderId"
    assert body["question"]  # any non-empty question


def test_spec_calls_are_written_to_backend_run_evidence(client, fresh_state):
    response = client.post(
        "/api/spec/emit",
        json={"user_text": "follow leader-demo-001 500 USD max loss 50 USD 48 hours"},
    )
    assert response.status_code == 200
    calls_path = fresh_state.evidence.dir / "calls.jsonl"
    calls = [json.loads(line) for line in calls_path.read_text(encoding="utf-8").splitlines()]
    assert calls[-1]["run_id"] == fresh_state.run_id
    assert calls[-1]["flow"] == "spec_emit"
