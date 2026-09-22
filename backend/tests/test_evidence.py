from __future__ import annotations

import json
import pytest

from agent.shared.evidence import EvidenceWriter
from backend.app.verify_evidence import EvidenceError, verify_run


def test_offline_evidence_verifies_and_live_rejects(tmp_path):
    writer = EvidenceWriter(tmp_path, "run-1", "offline")
    writer.append("events.jsonl", {"kind": "revoke_simulated"})
    assert verify_run(writer.dir)["ok"] is True
    with pytest.raises(EvidenceError, match="source_mode"):
        verify_run(writer.dir, live=True)


def test_live_verifier_rejects_estimated_usage(tmp_path):
    writer = EvidenceWriter(tmp_path, "run-2", "live")
    writer.append("calls.jsonl", {"usage_source": "estimated", "model": "gpt-oss-120b"})
    writer.append("chain.jsonl", {"action": "mint_confirmed", "tx_hash": "0x" + "11" * 32})
    writer.append("events.jsonl", {"kind": "revoke"})
    with pytest.raises(EvidenceError, match="API usage"):
        verify_run(writer.dir, live=True)
