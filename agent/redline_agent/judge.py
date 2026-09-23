"""RedLine Agent: independent kill switch.

The judge combines the hard rule gate with the LLM event classifier:

    1. hard_check(spec, drawdown_usd)  -- if it TRIPs, return immediately
       (we do NOT spend tokens on the LLM when the rule already fired).
    2. otherwise, call classifier.classify(events) to let the LLM
       judge structural shocks (Hynix / leverage / liquidation / pre-market gap).

This module is intentionally tiny. Anyone reading the security story
should be able to follow the control flow in one screen.
"""

from __future__ import annotations

from agent.follow_agent.spec_schema import CopyTradingSpec
from agent.redline_agent.llm_classifier import EventClassifier, MarketEvent
from agent.redline_agent.rule_gate import hard_check
from agent.redline_agent.schema import DEFER_TO_LLM, RedLineVerdict


class RedLineJudge:
    """Apply the rule gate, then defer to the LLM if needed."""

    def __init__(self, classifier: EventClassifier) -> None:
        self.classifier = classifier

    def judge(
        self,
        spec: CopyTradingSpec,
        drawdown_usd: float,
        events: list[MarketEvent] | None = None,
    ) -> RedLineVerdict:
        """Produce one RedLineVerdict.

        - drawdown_usd: the current drawdown in USD (>=0 is a loss).
        - events: optional market events. If omitted or empty, the LLM
          is not consulted and the verdict is whatever the gate
          produced (typically DEFER_TO_LLM, i.e. HOLD).
        """
        gate = hard_check(spec, drawdown_usd)
        if gate is not DEFER_TO_LLM:
            # Hard rule fired. Return immediately without spending
            # tokens on the model. This is intentional: PRD §9
            # demands we minimise Kiln calls and PRD §12 makes the
            # model irrelevant to the drawdown cap.
            return gate

        if not events:
            return DEFER_TO_LLM

        return self.classifier.classify(events)


__all__ = ["RedLineJudge"]