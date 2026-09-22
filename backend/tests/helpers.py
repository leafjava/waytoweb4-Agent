from __future__ import annotations

from uuid import uuid4


def valid_spec(**updates):
    spec = {
        "mode": "copy", "leaderId": "leader-demo-001", "venue": "paper",
        "notionalUsd": 500, "maxLossUsd": 50,
        "expiry": "2099-01-01T00:00:00+00:00", "faceVerified": False, "paper": True,
    }
    spec.update(updates)
    return spec


def prepare(client, spec=None, request_id=None):
    response = client.post("/api/passport/prepare", json={
        "spec": spec or valid_spec(), "request_id": request_id or f"prepare-{uuid4()}"
    })
    assert response.status_code == 200, response.text
    return response.json()


def prepare_confirm_mint(client, spec=None):
    prepared = prepare(client, spec)
    confirmed = client.post("/api/passport/confirm", json={
        "passport_id": prepared["passport_id"], "spec_hash": prepared["spec_hash"],
        "request_id": f"confirm-{uuid4()}",
    })
    assert confirmed.status_code == 200, confirmed.text
    minted = client.post("/api/passport/mint", json={
        "passport_id": prepared["passport_id"], "request_id": f"mint-{uuid4()}"
    })
    assert minted.status_code == 200, minted.text
    return minted.json()
