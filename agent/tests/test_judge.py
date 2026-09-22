"""Tests for the combined RedLine judge."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from agent.follow_agent.spec_schema import CopyTradingSpec
from agent.redline_agent import (
    HynixMockClassifier,
    MarketEvent,
    RedLineJudge,
    hynix_crash_pack,
)
from agent.redline_agent.schema import (
    DEFER_TO_LLM,
    RedLineAction,
    RedLineLevel,
)
from agent.shared.types import ReasonCode


def _spec(max_loss: float = 50.0) -> CopyTradingSpec:
    return CopyTradingSpec(
        mode="copy",
        leaderId="leader-demo-001",
        venue="paper",
        notionalUsd=500.0,
        maxLossUsd=max_loss,
        expiry=datetime.now(timezone.utc) + timedelta(hours=24),
        faceVerified=False,
        paper=True,
    )


# ---- Hard gate precedence ---------------------------------------------------


def test_hard_gate_wins_over_llm() -> None:
    """If drawdown hits the limit, we TRIP even if the LLM says HOLD."""
    class AlwaysHoldClassifier:
        def classify(self, events): return DEFER_TO_LLM

    j = RedLineJudge(classifier=AlwaysHoldClassifier())
    v = j.judge(_spec(max_loss=50.0), drawdown_usd=200.0, events=hynix_crash_pack())
    assert v.level == RedLineLevel.TRIP
    assert ReasonCode.DD_LIMIT in v.reason_codes


def test_llm_not_called_when_gate_fires() -> None:
    """The gate fires; the LLM must not even be consulted. We detect
    this with a classifier that throws if called."""

    class BoomClassifier:
        def classify(self, events):
            raise AssertionError("LLM should not be called when gate fires")

    j = RedLineJudge(classifier=BoomClassifier())
    v = j.judge(_spec(max_loss=50.0), drawdown_usd=999.0, events=hynix_crash_pack())
    assert v.level == RedLineLevel.TRIP


# ---- LLM path ---------------------------------------------------------------


def test_hynix_pack_trips_via_llm() -> None:
    j = RedLineJudge(classifier=HynixMockClassifier())
    v = j.judge(_spec(max_loss=50.0), drawdown_usd=10.0, events=hynix_crash_pack())
    assert v.level == RedLineLevel.TRIP
    assert v.action == RedLineAction.STOP_AND_REVOKE
    assert ReasonCode.CB_LIKE in v.reason_codes


def test_calm_market_holds() -> None:
    j = RedLineJudge(classifier=HynixMockClassifier())
    events = [MarketEvent(symbol="005930.KS", change_pct=0.2, kind="tick")]
    v = j.judge(_spec(), drawdown_usd=5.0, events=events)
    assert v.level == RedLineLevel.HOLD
    assert v.action == RedLineAction.NONE


def test_lev_etf_watches() -> None:
    j = RedLineJudge(classifier=HynixMockClassifier())
    events = [MarketEvent(symbol="KODEX2X.KS", change_pct=-5.0, kind="leveraged_etf")]
    v = j.judge(_spec(), drawdown_usd=5.0, events=events)
    assert v.level == RedLineLevel.WATCH


def test_no_events_means_no_llm_call() -> None:
    class BoomClassifier:
        def classify(self, events):
            raise AssertionError("LLM should not be called with no events")

    j = RedLineJudge(classifier=BoomClassifier())
    v = j.judge(_spec(), drawdown_usd=10.0, events=[])
    assert v is DEFER_TO_LLM