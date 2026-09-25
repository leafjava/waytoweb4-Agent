from __future__ import annotations

import json

import pytest

from agent.shared.evidence import EvidenceWriter
from backend.app.evidence_report import export_report
from backend.app.verify_evidence import EvidenceError


def test_offline_report_is_visibly_non_submission_evidence(tmp_path):
    writer = EvidenceWriter(tmp_path, "run-offline", "offline")
    report = export_report(writer.dir)
    markdown = (writer.dir / "submission-report.md").read_text(encoding="utf-8")
    assert report["evidence_class"] == "OFFLINE_DEMO_ONLY"
    assert "NOT LIVE SUBMISSION EVIDENCE" in markdown
    assert "No public-chain transaction is claimed" in markdown
    assert len(report["flows"]) == 5


def test_live_export_refuses_offline_run(tmp_path):
    writer = EvidenceWriter(tmp_path, "run-offline", "offline")
    with pytest.raises(EvidenceError, match="source_mode=live"):
        export_report(writer.dir, live=True)


def test_report_aggregates_calls_by_flow(tmp_path):
    writer = EvidenceWriter(tmp_path, "run-calls", "offline")
    writer.append("calls.jsonl", {
        "run_id": "run-calls", "flow": "clarify", "tokens_in": 10,
        "tokens_out": 4, "latency_s": 2.0, "energy_Wh_est": 0.1,
        "usage_source": "estimated",
    })
    report = export_report(writer.dir)
    clarify = next(row for row in report["flows"] if row["flow"] == "clarify")
    assert clarify == {
        "flow": "clarify", "calls": 1, "tokens_in": 10, "tokens_out": 4,
        "latency_s": 2.0, "energy_Wh_est": 0.1, "usage_source": "estimated",
    }
    persisted = json.loads((writer.dir / "submission-report.json").read_text(encoding="utf-8"))
    assert persisted["evidence_class"] == "OFFLINE_DEMO_ONLY"
