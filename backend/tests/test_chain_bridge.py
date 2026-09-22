from __future__ import annotations

import pytest
import json
from pathlib import Path

from backend.app.chain_bridge import ChainBridge
from backend.app.deps import get_passport_backend
from backend.app.intent import canonicalize_intent
from backend.app.passport_backends.node import NodePassportBackend
from .helpers import valid_spec


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
