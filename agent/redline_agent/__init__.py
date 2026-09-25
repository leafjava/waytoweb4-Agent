"""RedLine Agent: independent kill switch for copy-trading.

This package exports:

  * `RedLineJudge` -- the main entrypoint that combines the hard
    rule gate and the LLM event classifier.
  * `RedLineVerdict` / `RedLineLevel` / `RedLineAction` / `ReasonCode`
    -- the structured output schema (PRD §4.4).
  * `MarketEvent` -- the input shape for the LLM classifier.
  * `EventClassifier` -- the protocol teammates satisfy with their
    risk-control model; `HynixMockClassifier` is the keyword-based
    fallback.
  * `hynix_crash_pack` / `load_eval_cases` -- demo and eval helpers.

Design rules baked into this package:

  * The hard rule gate fires first and never consults the model.
  * The model never sees PnL (it judges events, not returns).
  * The model cannot override the hard gate -- `RedLineVerdict` will
    refuse to construct with `model_may_override_hard_limit=True`.
"""

from .event_injector import (
    DEFAULT_EVAL_PATH,
    events_to_json,
    hynix_crash_pack,
    load_eval_cases,
    write_default_eval_cases,
)
from .judge import RedLineJudge
from .llm_classifier import (
    CB_THRESHOLD_PCT,
    EventClassifier,
    HynixMockClassifier,
    KilnEventClassifier,
    KEYWORD_RULES,
    MarketEvent,
)
from .rule_gate import hard_check
from .schema import (
    DEFER_TO_LLM,
    RedLineAction,
    RedLineLevel,
    RedLineVerdict,
    action_for_level,
)

__all__ = [
    "RedLineJudge",
    "RedLineLevel",
    "RedLineAction",
    "RedLineVerdict",
    "action_for_level",
    "DEFER_TO_LLM",
    "hard_check",
    "EventClassifier",
    "HynixMockClassifier",
    "KilnEventClassifier",
    "MarketEvent",
    "KEYWORD_RULES",
    "CB_THRESHOLD_PCT",
    "hynix_crash_pack",
    "events_to_json",
    "load_eval_cases",
    "write_default_eval_cases",
    "DEFAULT_EVAL_PATH",
]
