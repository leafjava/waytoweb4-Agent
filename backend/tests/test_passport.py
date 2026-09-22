"""Authorization lifecycle and intent boundary tests."""

from __future__ import annotations

import asyncio

import pytest

from backend.app.authorization import AuthorizationError, AuthorizationService
from backend.app.engine import stop_engine
from backend.app.state import AppState
from .helpers import prepare, prepare_confirm_mint, valid_spec


def test_prepare_returns_uuid_hash_and_no_fake_transaction(client):
    body = prepare(client)
    assert len(body["passport_id"]) == 36
    assert len(body["spec_hash"]) == 66
    assert body["tx_hash"] is None
    assert body["status"] == "prepared"


def test_raw_spec_cannot_bypass_confirm_at_mint(client):
    response = client.post("/api/passport/mint", json={"spec": valid_spec()})
    assert response.status_code == 422


def test_mint_requires_confirmation(client):
    prepared = prepare(client)
    response = client.post("/api/passport/mint", json={
        "passport_id": prepared["passport_id"], "request_id": "mint-unconfirmed"
    })
    assert response.status_code == 409


def test_confirmation_rejects_wrong_hash(client):
    prepared = prepare(client)
    response = client.post("/api/passport/confirm", json={
        "passport_id": prepared["passport_id"], "spec_hash": "0x" + "00" * 32,
        "request_id": "confirm-wrong",
    })
    assert response.status_code == 409


def test_mock_mint_uses_simulation_id_not_transaction_hash(client):
    body = prepare_confirm_mint(client)
    assert body["status"] == "authorized"
    assert body["tx_hash"] is None
    record = client.get(f"/api/passport/{body['passport_id']}").json()
    assert record["simulation_id"].startswith("sim-")


def test_prepare_strips_client_face_claim(client):
    body = prepare(client, valid_spec(faceVerified=True))
    record = client.get(f"/api/passport/{body['passport_id']}").json()
    assert record["face_verified"] is False


def test_invalid_mode_and_limit_are_rejected_at_prepare(client):
    assert client.post("/api/passport/prepare", json={
        "spec": valid_spec(mode="grid_bot"), "request_id": "bad-mode"
    }).status_code == 422
    assert client.post("/api/passport/prepare", json={
        "spec": valid_spec(notionalUsd=100, maxLossUsd=999), "request_id": "bad-loss"
    }).status_code == 422


def test_fractional_cents_nan_and_infinity_are_rejected(client):
    for index, value in enumerate(("1.001", "NaN", "Infinity")):
        response = client.post("/api/passport/prepare", json={
            "spec": valid_spec(notionalUsd=value), "request_id": f"bad-money-{index}"
        })
        assert response.status_code == 422


def test_request_id_is_idempotent_and_payload_bound(client):
    first = prepare(client, request_id="same-prepare")
    second = prepare(client, request_id="same-prepare")
    assert second["passport_id"] == first["passport_id"]
    changed = client.post("/api/passport/prepare", json={
        "spec": valid_spec(leaderId="different"), "request_id": "same-prepare"
    })
    assert changed.status_code == 409


def test_second_mint_request_reuses_authorization_without_fake_tx(client):
    body = prepare_confirm_mint(client)
    response = client.post("/api/passport/mint", json={
        "passport_id": body["passport_id"], "request_id": "another-mint-request"
    })
    assert response.status_code == 200
    assert response.json()["tx_hash"] is None
    assert response.json()["passport_id"] == body["passport_id"]


def test_revoke_is_terminal_and_has_no_mock_tx_hash(client):
    body = prepare_confirm_mint(client)
    response = client.post(f"/api/passport/{body['passport_id']}/revoke")
    assert response.status_code == 200
    assert response.json()["tx_hash"] is None
    assert client.post(f"/api/passport/{body['passport_id']}/revoke").status_code == 409
    assert client.post("/api/engine/start", json={"passport_id": body["passport_id"]}).status_code == 409


def test_revoke_unknown_returns_404(client):
    assert client.post("/api/passport/missing/revoke").status_code == 404


class _DelayedChainBackend:
    label = "local"

    def __init__(self):
        self.mint_started = asyncio.Event()
        self.release_mint = asyncio.Event()
        self.revoke_calls = 0

    async def mint_record(self, rec):
        self.mint_started.set()
        await self.release_mint.wait()
        return {
            "status": "confirmed",
            "tx_hash": "0x" + "11" * 32,
            "chain_passport_id": "1",
            "chain_id": 1337,
            "contract_address": "0x" + "22" * 20,
            "receipt": {"status": 1, "block_number": 1},
            "state": {"spec_hash": rec.spec_hash, "status": "active"},
        }

    async def revoke_record(self, rec, reason_code):
        self.revoke_calls += 1
        return {
            "status": "confirmed",
            "tx_hash": "0x" + "33" * 32,
            "chain_passport_id": rec.chain_passport_id,
            "chain_id": 1337,
            "contract_address": rec.contract_address,
            "receipt": {"status": 1, "block_number": 2},
            "state": {"spec_hash": rec.spec_hash, "status": "revoked"},
        }


@pytest.mark.asyncio
async def test_stop_during_pending_mint_revokes_after_confirmation(tmp_path):
    state = AppState(tmp_path / "passports.json")
    service = AuthorizationService()
    backend = _DelayedChainBackend()
    rec = await service.prepare(state, valid_spec(), "race-prepare")
    await service.confirm(state, rec.passport_id, rec.spec_hash, "race-confirm")

    mint_task = asyncio.create_task(service.mint(state, rec.passport_id, "race-mint", backend))
    await backend.mint_started.wait()
    with pytest.raises(AuthorizationError, match="cannot be revoked"):
        await stop_engine(rec.passport_id, state, backend)
    backend.release_mint.set()

    result = await mint_task
    assert result.authorization_status == "revoked"
    assert result.stop_reason == "STOP_REQUESTED"
    assert result.tx_revoke_hash == "0x" + "33" * 32
    assert backend.revoke_calls == 1
