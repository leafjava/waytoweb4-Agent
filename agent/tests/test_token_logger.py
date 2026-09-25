"""Tests for the TokenLogger and energy estimation."""

from __future__ import annotations

import re

import pytest

from agent.shared.energy import NPU_POWER_W, estimate_wh
from agent.shared.token_logger import ALLOWED_FLOWS, TokenLogger


def test_estimate_wh_zero_latency() -> None:
    assert estimate_wh(0.0) == 0.0


def test_estimate_wh_one_hour() -> None:
    assert estimate_wh(3600.0) == pytest.approx(NPU_POWER_W)


def test_estimate_wh_negative_latency_clamped() -> None:
    assert estimate_wh(-10.0) == 0.0


def test_logger_rejects_unknown_flow() -> None:
    lg = TokenLogger()
    with pytest.raises(ValueError):
        lg.record("made_up_flow", 1, 1, 0.1)


def test_logger_rejects_negative_tokens() -> None:
    lg = TokenLogger()
    with pytest.raises(ValueError):
        lg.record("clarify", -1, 0, 0.1)


def test_logger_aggregates_totals() -> None:
    lg = TokenLogger()
    lg.record("clarify", 100, 50, 1.0)
    lg.record("clarify", 200, 50, 1.0)
    lg.record("spec_emit", 150, 80, 0.5)
    t = lg.totals()
    assert t.tokens_in == 450
    assert t.tokens_out == 180
    assert t.latency_s == pytest.approx(2.5)
    assert t.calls == 3


def test_report_has_required_columns() -> None:
    lg = TokenLogger()
    lg.record("clarify", 100, 50, 1.0)
    lg.record("spec_emit", 150, 80, 0.5)
    report = lg.report()
    for col in ("flow", "tokens_in", "tokens_out", "latency_s", "energy_Wh_est", "total", "assumption"):
        assert col in report


def test_report_lists_all_allowed_flows() -> None:
    """Even unused flows should appear as zero rows so the README
    table is complete from the first run."""
    lg = TokenLogger()
    report = lg.report()
    for flow in ALLOWED_FLOWS:
        assert flow in report


def test_report_assumption_matches_prd() -> None:
    lg = TokenLogger()
    report = lg.report()
    assert "180" in report  # the 180W assumption
    assert "latency / 3600" in report


def test_snapshot_preserves_flow_source_model_and_energy() -> None:
    lg = TokenLogger()
    lg.record(
        "clarify", 100, 25, 2.0,
        usage_source="api", model="gpt-oss-120b", request_id="call-1",
    )
    snapshot = lg.snapshot()
    clarify = next(row for row in snapshot["flows"] if row["flow"] == "clarify")
    assert clarify == {
        "flow": "clarify",
        "calls": 1,
        "tokens_in": 100,
        "tokens_out": 25,
        "latency_s": 2.0,
        "energy_Wh_est": 0.1,
        "usage_source": "api",
        "model": "gpt-oss-120b",
    }
    assert snapshot["total"]["calls"] == 1
