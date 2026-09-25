"""RedLine judgment schema.

The shape of every RedLine output is locked here. The PRD §4.4
defines exactly the fields we must emit, and Challenge B scoring
(third-party auditability) treats this schema as a stable public
contract -- not a class that drifts between deployments.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Literal

from agent.shared.exceptions import UnauthorizedOverrideError
from agent.shared.types import ReasonCode


class RedLineLevel(str, Enum):
    HOLD = "HOLD"      # nothing to do
    WATCH = "WATCH"    # tighten, but do not stop
    TRIP = "TRIP"      # stop the engine and revoke the passport


class RedLineAction(str, Enum):
    NONE = "none"
    TIGHTEN = "tighten"
    STOP_AND_REVOKE = "stop_and_revoke"


# Closed mapping from level -> action. We expose it as a function so
# the judge can never accidentally emit "WATCH" with "stop_and_revoke"
# or any other inconsistent combination.
def action_for_level(level: RedLineLevel) -> RedLineAction:
    if level == RedLineLevel.HOLD:
        return RedLineAction.NONE
    if level == RedLineLevel.WATCH:
        return RedLineAction.TIGHTEN
    return RedLineAction.STOP_AND_REVOKE


@dataclass(frozen=True)
class RedLineVerdict:
    """The structured output of a single RedLine judgment.

    `source` is purely for logging -- it tells the audit log whether
    this verdict came from the hard rule gate (`rule_gate`), the
    deterministic offline classifier (`mock`), or live Kiln (`kiln`).
    """

    level: RedLineLevel
    reason_codes: list[ReasonCode]
    evidence: list[str]
    action: RedLineAction
    model_may_override_hard_limit: bool = False
    source: Literal["rule_gate", "mock", "kiln"] = "rule_gate"

    def __post_init__(self) -> None:
        # The hard guard: the model must NEVER be allowed to override
        # the drawdown limit. We assert this on construction so a
        # buggy LLM integration can't sneak through with the wrong
        # flag set.
        if self.model_may_override_hard_limit:
            raise UnauthorizedOverrideError(
                "model_may_override_hard_limit must remain False. "
                "The hard rule gate is not negotiable."
            )
        # Action must match level.
        if action_for_level(self.level) != self.action:
            raise ValueError(
                f"action {self.action!r} is inconsistent with level {self.level!r}. "
                "Use action_for_level() to derive the right action."
            )
        # Reason codes must be non-empty for TRIP and WATCH; HOLD may
        # omit them but should carry at least an empty list (so the
        # audit trail always has the field).
        if self.level in (RedLineLevel.WATCH, RedLineLevel.TRIP) and not self.reason_codes:
            raise ValueError(
                f"reason_codes must be non-empty for level {self.level!r}; "
                "third-party auditors require a justification."
            )


# A sentinel "no rule fired, defer to LLM" payload. We use this to
# keep the judge code branch-free when the hard gate decides not to
# trip.
DEFER_TO_LLM: RedLineVerdict = RedLineVerdict(
    level=RedLineLevel.HOLD,
    reason_codes=[],
    evidence=[],
    action=RedLineAction.NONE,
    model_may_override_hard_limit=False,
    source="rule_gate",
)


__all__ = [
    "RedLineLevel",
    "RedLineAction",
    "RedLineVerdict",
    "action_for_level",
    "DEFER_TO_LLM",
]
