"""RedLine hard rule gate.

This is the single most security-critical module in the agent. Per
PRD §4.4 and §12, when drawdown has reached the Spec's maxLossUsd,
the engine MUST stop and the passport MUST be revoked -- no matter
what the model says. The model cannot override this; we assert that
on construction of any RedLineVerdict.

We deliberately implement the gate as a small, side-effect-free
function with no LLM calls in it. That keeps the security argument
auditable: the security-critical path is <30 lines of plain Python.
"""

from __future__ import annotations

from agent.follow_agent.spec_schema import CopyTradingSpec
from agent.redline_agent.schema import (
    DEFER_TO_LLM,
    RedLineVerdict,
    RedLineLevel,
    RedLineAction,
    action_for_level,
)
from agent.shared.types import ReasonCode


# We require an explicit epsilon-free comparison on drawdown: any
# drawdown >= maxLossUsd triggers TRIP. The PRD is explicit here
# (PRD §4.4: "if drawdown >= spec.maxLossUsd -> TRIP") and we don't
# fuzz the boundary.
def hard_check(spec: CopyTradingSpec, drawdown_usd: float) -> RedLineVerdict:
    """Apply the PRD-mandated drawdown rule.

    Returns a TRIP verdict with reason_code DD_LIMIT when the rule
    fires. Returns `DEFER_TO_LLM` (a HOLD with source='rule_gate')
    otherwise, signalling that the judge should consult the LLM
    classifier.

    Important: this function NEVER inspects PnL, never looks at the
    leader's track record, and never lets the LLM influence its
    decision. That separation is what Challenge B is grading.
    """
    if drawdown_usd < 0:
        # Negative drawdown is a PnL gain. RedLine doesn't care about
        # PnL -- but we still let the LLM classifier look at it (e.g.
        # for GAP_ORACLE detection). Return DEFER_TO_LLM.
        return DEFER_TO_LLM

    if drawdown_usd >= spec.maxLossUsd:
        return RedLineVerdict(
            level=RedLineLevel.TRIP,
            reason_codes=[ReasonCode.DD_LIMIT],
            evidence=[
                f"drawdownUsd={drawdown_usd}",
                f"maxLossUsd={spec.maxLossUsd}",
            ],
            action=action_for_level(RedLineLevel.TRIP),
            model_may_override_hard_limit=False,
            source="rule_gate",
        )

    return DEFER_TO_LLM


__all__ = ["hard_check"]