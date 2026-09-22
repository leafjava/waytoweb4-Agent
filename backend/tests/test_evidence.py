from __future__ import annotations

import json
import pytest

from agent.shared.evidence import EvidenceWriter
from backend.app.verify_evidence import EvidenceError, verify_run


def test_offline_evidence_verifies_and_live_rejects(tmp_path):
    writer = EvidenceWriter(tmp_path, "run-1", "offline")
    writer.append("events.jsonl", {"run_id": "run-1", "kind": "revoke_simulated"})
    assert verify_run(writer.dir)["ok"] is True
    with pytest.raises(EvidenceError, match="source_mode"):
        verify_run(writer.dir, live=True)


def test_live_verifier_rejects_estimated_usage(tmp_path):
    writer = EvidenceWriter(tmp_path, "run-2", "live")
    writer.write_json("intent.json", {"run_id": "run-2", "spec_hash": "0x" + "44" * 32})
    writer.append("calls.jsonl", {"run_id": "run-2", "call_id": "call-1", "usage_source": "estimated", "model": "gpt-oss-120b", "tokens_in": 1, "tokens_out": 1})
    with pytest.raises(EvidenceError, match="API usage"):
        verify_run(writer.dir, live=True)


def _write_valid_live_run(tmp_path):
    run_id = "live-run"
    writer = EvidenceWriter(tmp_path, run_id, "live")
    spec_hash = "0x" + "44" * 32
    contract = "0x" + "55" * 20
    author = "0x" + "66" * 20
    writer.write_json("intent.json", {"run_id": run_id, "spec_hash": spec_hash})
    writer.append("calls.jsonl", {
        "run_id": run_id, "call_id": "call-1", "flow": "spec_emit",
        "usage_source": "api", "model": "gpt-oss-120b", "tokens_in": 10, "tokens_out": 5,
    })
    writer.append("events.jsonl", {"run_id": run_id, "kind": "engine_stop", "payload": {"reason": "REDLINE_TRIP"}})
    common = {
        "run_id": run_id, "chain_id": 11155111, "contract_address": contract,
        "chain_passport_id": "1",
    }
    writer.append("chain.jsonl", {
        **common, "action": "mint_confirmed", "tx_hash": "0x" + "11" * 32,
        "receipt": {"status": 1, "block_number": 10, "block_hash": "0x" + "22" * 32},
        "state": {"spec_hash": spec_hash, "status": "active", "human_confirmed": True, "author": author},
    })
    writer.append("chain.jsonl", {
        **common, "action": "revoke_confirmed", "tx_hash": "0x" + "33" * 32,
        "receipt": {"status": 1, "block_number": 11, "block_hash": "0x" + "77" * 32},
        "state": {"spec_hash": spec_hash, "status": "revoked", "human_confirmed": True, "author": author},
    })
    return writer


def test_live_verifier_requires_receipts_readback_and_real_revoke(tmp_path):
    writer = _write_valid_live_run(tmp_path)
    assert verify_run(writer.dir, live=True)["ok"] is True

    writer.append("events.jsonl", {"run_id": "live-run", "kind": "revoke_simulated"})
    with pytest.raises(EvidenceError, match="simulated revoke"):
        verify_run(writer.dir, live=True)


def test_live_verifier_rejects_local_chain_and_cross_run_rows(tmp_path):
    writer = _write_valid_live_run(tmp_path)
    chain_path = writer.dir / "chain.jsonl"
    rows = [json.loads(line) for line in chain_path.read_text(encoding="utf-8").splitlines()]
    rows[0]["chain_id"] = 1337
    chain_path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
    with pytest.raises(EvidenceError, match="public testnet"):
        verify_run(writer.dir, live=True)

    rows[0]["chain_id"] = 11155111
    rows[0]["run_id"] = "another-run"
    chain_path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
    with pytest.raises(EvidenceError, match="run_id mismatch"):
        verify_run(writer.dir, live=True)
