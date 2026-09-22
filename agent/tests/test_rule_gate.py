"""Tests for the RedLine hard rule gate.

These guard the most security-critical behaviour: a drawdown that
hits maxLossUsd must produce TRIP with reason DD_LIMIT, regardless
of any LLM involvement.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from agent.follow_agent.spec_schema import CopyTradingSpec
from agent.redline_agent.rule_gate import hard_check
from agent.redline_agent.schema import (
    DEFER_TO_LLM,
    RedLineAction,
    RedLineLevel,
)
from agent.shared.exceptions import UnauthorizedOverrideError
from agent.shared.types import ReasonCode


def _spec(max_loss: float = 50.0, notional: float = 500.0) -> CopyTradingSpec:
    return CopyTradingSpec(
        mode="copy",
        leaderId="leader-demo-001",
        venue="paper",
        notionalUsd=notional,
        maxLossUsd=max_loss,
        expiry=datetime.now(timezone.utc) + timedelta(hours=24),
        faceVerified=False,
        paper=True,
    )


def test_drawdown_at_limit_trips() -> None:
    spec = _spec(max_loss=50.0)
    v = hard_check(spec, drawdown_usd=50.0)
    assert v.level == RedLineLevel.TRIP
    assert v.action == RedLineAction.STOP_AND_REVOKE
    assert v.reason_codes == [ReasonCode.DD_LIMIT]
    assert v.source == "rule_gate"
    assert v.model_may_override_hard_limit is False


def test_drawdown_above_limit_trips() -> None:
    spec = _spec(max_loss=50.0)
    v = hard_check(spec, drawdown_usd=51.0)
    assert v.level == RedLineLevel.TRIP
    assert ReasonCode.DD_LIMIT in v.reason_codes


def test_drawdown_just_below_limit_defers() -> None:
    spec = _spec(max_loss=50.0)
    v = hard_check(spec, drawdown_usd=49.999)
    assert v is DEFER_TO_LLM


def test_zero_drawdown_defers() -> None:
    spec = _spec()
    assert hard_check(spec, drawdown_usd=0.0) is DEFER_TO_LLM


def test_negative_drawdown_defers() -> None:
    """A PnL gain is not RedLine's concern -- defer to the LLM."""
    spec = _spec()
    assert hard_check(spec, drawdown_usd=-10.0) is DEFER_TO_LLM


def test_evidence_records_numbers() -> None:
    spec = _spec(max_loss=50.0)
    v = hard_check(spec, drawdown_usd=75.0)
    # Useful for the on-chain audit log.
    assert any("drawdownUsd=75" in e for e in v.evidence)
    assert any("maxLossUsd=50" in e for e in v.evidence)


def test_model_override_flag_is_rejected() -> None:
    """A buggy LLM integration cannot smuggle True here."""
    from agent.redline_agent.schema import RedLineVerdict, action_for_level

    with pytest.raises(UnauthorizedOverrideError):
        RedLineVerdict(
            level=RedLineLevel.TRIP,
            reason_codes=[ReasonCode.DD_LIMIT],
            evidence=["x"],
            action=action_for_level(RedLineLevel.TRIP),
            model_may_override_hard_limit=True,  # nope
            source="rule_gate",
        )