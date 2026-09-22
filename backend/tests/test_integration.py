"""End-to-end integration test: spec → mint → face → start → trip → revoke."""

from __future__ import annotations


def test_full_happy_path_to_redline_trip(client):
    # 1. emit a Spec
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

    # 2. mint the passport
    r = client.post("/api/passport/mint", json={"spec": spec})
    assert r.status_code == 200
    mint_body = r.json()
    pid = mint_body["passport_id"]
    assert mint_body["tx_hash"].startswith("0x")

    # 3. face verify
    r = client.post("/api/face/verify", json={"passport_id": pid})
    assert r.status_code == 200
    assert r.json()["ok"] is True

    # 4. start engine
    r = client.post("/api/engine/start", json={"passport_id": pid})
    assert r.status_code == 200

    # 5. tick drawdown to the limit (maxLossUsd = 50)
    r = client.post("/api/engine/tick?amount=50", json={"passport_id": pid})
    assert r.status_code == 200
    assert r.json()["drawdown_usd"] == 50.0

    # 6. judge with no events: the rule gate should TRIP because drawdown >= maxLoss.
    r = client.post("/api/redline/judge", json={"passport_id": pid})
    assert r.status_code == 200
    body = r.json()
    assert body["verdict"]["level"] == "TRIP"
    assert "DD_LIMIT" in body["verdict"]["reason_codes"]
    assert body["flow"] == "redline_trip"
    assert body["side_effects"]["revoked"] is True
    revoke_tx = body["side_effects"]["revoke_tx_hash"]
    assert revoke_tx != mint_body["tx_hash"]

    # 7. state snapshot reflects all of the above
    r = client.get("/api/state")
    snap = r.json()
    assert pid in snap["passports"]
    pr = snap["passports"][pid]
    assert pr["status"] == "revoked"
    assert pr["tx_mint_hash"] == mint_body["tx_hash"]
    assert pr["tx_revoke_hash"] == revoke_tx
    # Audit log has every step
    kinds = [ev["kind"] for ev in snap["events"]]
    for required in ("mint", "face_verify", "engine_start", "revoke"):
        assert required in kinds, f"missing {required} in {kinds}"

    # 8. token report is non-empty
    assert "flow" in snap["token_report"]