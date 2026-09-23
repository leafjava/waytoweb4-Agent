from __future__ import annotations

import pytest
import json
import time
from pathlib import Path

from backend.app.chain_bridge import ChainBridge
from backend.app.deps import get_passport_backend
from backend.app.intent import canonicalize_intent
from backend.app.passport_backends.node import NodePassportBackend
from .helpers import valid_spec, verify_face


def _mint_local_passport(client, backend, prefix: str) -> dict:
    client.app.dependency_overrides[get_passport_backend] = lambda: backend
    prepared = client.post("/api/passport/prepare", json={
        "spec": valid_spec(), "request_id": f"{prefix}-prepare",
    })
    assert prepared.status_code == 200, prepared.text
    body = prepared.json()
    assert client.post("/api/passport/confirm", json={
        "passport_id": body["passport_id"],
        "spec_hash": body["spec_hash"],
        "request_id": f"{prefix}-confirm",
    }).status_code == 200
    minted = client.post("/api/passport/mint", json={
        "passport_id": body["passport_id"], "request_id": f"{prefix}-mint",
    })
    assert minted.status_code == 200, minted.text
    return minted.json()


def test_golden_intent_fixture_matches_python_implementation():
    fixture = json.loads((Path(__file__).resolve().parents[2] / "fixtures" / "intent-v1.json").read_text())
    canonical, digest, _, _, _ = canonicalize_intent(fixture["spec"])
    assert canonical == fixture["canonical"]
    assert digest == fixture["hash"]


@pytest.mark.asyncio
async def test_python_node_local_evm_mint_read_revoke():
    bridge = ChainBridge(timeout=30)
    try:
        canonical, digest, _, _, _ = canonicalize_intent(valid_spec())
        mint = await bridge.call("mint", "test-run", {
            "canonical_intent": canonical, "spec_hash": digest, "confirmed_spec_hash": digest,
        })
        assert mint["receipt"]["status"] == 1
        assert mint["state"]["notional_cents"] == "50000"
        read = await bridge.call("inspect", "test-run", {"chain_passport_id": mint["chain_passport_id"]})
        assert read["state"]["spec_hash"] == digest
        revoke = await bridge.call("revoke", "test-run", {"chain_passport_id": mint["chain_passport_id"], "reason_code": "TEST"})
        assert revoke["state"]["status"] == "revoked"
    finally:
        await bridge.close()


def test_fastapi_to_node_to_local_evm(client):
    backend = NodePassportBackend()
    client.app.dependency_overrides[get_passport_backend] = lambda: backend
    try:
        prepared = client.post("/api/passport/prepare", json={"spec": valid_spec(), "request_id": "api-prepare"})
        assert prepared.status_code == 200, prepared.text
        body = prepared.json()
        assert client.post("/api/passport/confirm", json={
            "passport_id": body["passport_id"], "spec_hash": body["spec_hash"], "request_id": "api-confirm"
        }).status_code == 200
        minted = client.post("/api/passport/mint", json={"passport_id": body["passport_id"], "request_id": "api-mint"})
        assert minted.status_code == 200, minted.text
        assert minted.json()["tx_hash"].startswith("0x")
        duplicate = client.post("/api/passport/mint", json={"passport_id": body["passport_id"], "request_id": "api-mint-again"})
        assert duplicate.status_code == 200
        assert duplicate.json()["tx_hash"] == minted.json()["tx_hash"]
        record = client.get(f"/api/passport/{body['passport_id']}").json()
        assert record["chain_id"] == 1337 and record["chain_passport_id"] == "1"
        revoked = client.post(f"/api/passport/{body['passport_id']}/revoke")
        assert revoked.status_code == 200, revoked.text
        assert revoked.json()["tx_hash"].startswith("0x")
    finally:
        client.portal.call(backend.close)
        client.app.dependency_overrides.pop(get_passport_backend, None)


def test_redline_trip_revokes_local_evm_passport(client):
    backend = NodePassportBackend()
    try:
        minted = _mint_local_passport(client, backend, "redline-local")
        passport_id = minted["passport_id"]
        verify_face(client, passport_id)
        assert client.post("/api/engine/start", json={"passport_id": passport_id}).status_code == 200

        tripped = client.post("/api/redline/inject/hynix", json={"passport_id": passport_id})
        assert tripped.status_code == 200, tripped.text
        assert tripped.json()["side_effects"]["revoke_tx_hash"].startswith("0x")

        record = client.get(f"/api/passport/{passport_id}").json()
        assert record["authorization_status"] == "revoked"
        chain = client.portal.call(
            backend.bridge.call,
            "inspect",
            record["run_id"],
            {"chain_passport_id": record["chain_passport_id"]},
        )
        assert chain["state"]["status"] == "revoked"
    finally:
        client.portal.call(backend.close)
        client.app.dependency_overrides.pop(get_passport_backend, None)


def test_drawdown_hard_stop_revokes_local_evm_passport(client):
    backend = NodePassportBackend()
    try:
        minted = _mint_local_passport(client, backend, "drawdown-local")
        passport_id = minted["passport_id"]
        verify_face(client, passport_id)
        assert client.post("/api/engine/start", json={"passport_id": passport_id}).status_code == 200
        assert client.post(
            "/api/engine/tick?amount=999", json={"passport_id": passport_id}
        ).status_code == 200

        for _ in range(100):
            record = client.get(f"/api/passport/{passport_id}").json()
            if record["authorization_status"] == "revoked":
                break
            time.sleep(0.02)
        assert record["stop_reason"] == "DD_LIMIT"
        assert record["tx_revoke_hash"].startswith("0x")
        chain = client.portal.call(
            backend.bridge.call,
            "inspect",
            record["run_id"],
            {"chain_passport_id": record["chain_passport_id"]},
        )
        assert chain["state"]["status"] == "revoked"
    finally:
        client.portal.call(backend.close)
        client.app.dependency_overrides.pop(get_passport_backend, None)
