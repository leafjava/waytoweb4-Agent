"""Hash determinism tests."""

from __future__ import annotations

from backend.app.hash import mint_tx_hash, revoke_tx_hash, short_id, spec_hash


def _spec_dict():
    return {
        "mode": "copy",
        "leaderId": "leader-demo-001",
        "venue": "paper",
        "notionalUsd": 500.0,
        "maxLossUsd": 50.0,
        "expiry": "2099-01-01T00:00:00+00:00",
        "faceVerified": False,
        "paper": True,
    }


def test_spec_hash_stable():
    a = spec_hash(_spec_dict())
    b = spec_hash(_spec_dict())
    assert a == b
    assert a.startswith("0x")
    assert len(a) == 66


def test_different_specs_different_hashes():
    a = spec_hash(_spec_dict())
    b = spec_hash({**_spec_dict(), "leaderId": "leader-other"})
    assert a != b


def test_short_id_is_8_bytes():
    sid = short_id(_spec_dict())
    # 0x + 16 hex chars
    assert sid.startswith("0x")
    assert len(sid) == 18


def test_mint_and_revoke_hashes_differ():
    sh = spec_hash(_spec_dict())
    m = mint_tx_hash(sh)
    r = revoke_tx_hash("0x" + sh[2:18], m)
    assert m != r
    assert m.startswith("0x")
    assert r.startswith("0x")