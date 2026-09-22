from __future__ import annotations

import json

import pytest

from backend.app.execution_contract import build_start_command
from .helpers import prepare_confirm_mint


def test_paper_worker_uses_replaceable_waytoweb4_command(client, fresh_state):
    minted = prepare_confirm_mint(client)
    record = fresh_state.passports[minted["passport_id"]]
    command = build_start_command(record, "policy.json")
    payload = command.model_dump(mode="json")

    canonical = json.loads(record.canonical_intent)
    assert payload["spec_hash"] == record.confirmed_spec_hash
    assert payload["notional_cents"] == int(canonical["notionalCents"])
    assert payload["max_loss_cents"] == int(canonical["maxLossCents"])
    assert payload["paper"] is True
    assert not any("key" in name.lower() or "secret" in name.lower() for name in payload)


def test_execution_command_rejects_unconfirmed_record(client, fresh_state):
    minted = prepare_confirm_mint(client)
    record = fresh_state.passports[minted["passport_id"]]
    record.confirmed_spec_hash = None
    with pytest.raises(ValueError, match="hash-bound authorized"):
        build_start_command(record, "policy.json")
