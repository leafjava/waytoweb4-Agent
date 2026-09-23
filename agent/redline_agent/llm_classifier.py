"""LLM event classifier interface for RedLine.

The actual risk-control model is being trained by the LLaMA teammate;
this module owns the *contract* it must satisfy and ships a small
deterministic fallback so we can run end-to-end without the model.

Design intent: the classifier is a `Protocol`, not an ABC. Teammates
can drop in their model wrapper as long as it exposes `classify`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Protocol
import json

from agent.redline_agent.schema import (
    RedLineAction,
    RedLineLevel,
    RedLineVerdict,
    action_for_level,
)
from agent.shared.types import ReasonCode


@dataclass(frozen=True)
class MarketEvent:
    """One observation that RedLine might judge.

    `symbol` is the affected ticker or sector (e.g. "000660.KS" for
    Hynix, "KS200" for KOSPI 200). `change_pct` is the percentage
    move since the previous tick; positive means up. `kind` is a
    short tag like "tick" / "halt" / "news". `timestamp` is ISO-8601
    UTC; not used by the gate, kept for logs.
    """

    symbol: str
    change_pct: float
    kind: str = "tick"
    timestamp: str = ""


class EventClassifier(Protocol):
    """Anything that turns a sequence of MarketEvents into a verdict."""

    def classify(self, events: Iterable[MarketEvent]) -> RedLineVerdict: ...


# ---- Local keyword-based fallback ------------------------------------------


# A small lookup table that the fallback classifier uses to pick
# reason codes. The model teammate's job is to do the same thing but
# with semantic understanding; for our purposes we just need a
# deterministic answer that doesn't make the demo look broken when
# the real model isn't loaded.
# Keyword matchers accept EN / KO / ZH event phrasing. The KO entries let
# Demo Day input in Korean classify correctly; the ZH entries are input
# parsing (not user-visible copy). Kept in lockstep with
# frontend/src/predict.js KEYWORD_RULES.
KEYWORD_RULES: tuple[tuple[tuple[str, ...], ReasonCode], ...] = (
    (("熔断", "circuit", "halt", "halted", "서킷브레이커", "거래정지"), ReasonCode.CB_LIKE),
    (("清算", "liq", "cascade", "청산"), ReasonCode.LIQ_CASCADE),
    (("杠杆", "leveraged", "2x", "lev_etf", "레버리지"), ReasonCode.LEV_ETF_AMP),
    (("盘前", "pre-market", "gap", "薄流动性", "갭", "얇은 유동성"), ReasonCode.GAP_ORACLE),
    (("人工", "human", "override", "kill", "즉시 중지"), ReasonCode.HUMAN_OVERRIDE),
)


def _classify_text(text: str) -> list[ReasonCode]:
    lowered = text.lower()
    codes: list[ReasonCode] = []
    for kws, code in KEYWORD_RULES:
        if any(kw in lowered for kw in kws):
            if code not in codes:
                codes.append(code)
    return codes


# A single -8% or worse move is treated as circuit-breaker-grade even
# if the event text doesn't mention "circuit". Keeps the demo honest:
# "Hynix -12%" alone still TRIPs.
CB_THRESHOLD_PCT: float = -8.0


class HynixMockClassifier:
    """A minimal local classifier.

    Recognises a handful of English / Korean / Chinese keywords
    (Hynix, circuit-breaker, leveraged, gap, etc.) and emits a verdict
    with the matching reason code. Used by the demo and by tests so
    the agent works end-to-end before the LLaMA teammate's model
    lands.

    The teammate's model must satisfy the same `EventClassifier`
    Protocol and emit a `RedLineVerdict` with the same shape; nothing
    else is required.
    """

    name: str = "hynix-keyword-mock"

    def classify(self, events: Iterable[MarketEvent]) -> RedLineVerdict:
        evs = list(events)
        worst_change = min((e.change_pct for e in evs), default=0.0)
        text = " ".join(f"{e.symbol} {e.kind} {e.change_pct}" for e in evs)
        codes = _classify_text(text)

        # Add CB_LIKE if the worst move is bad enough, but don't
        # duplicate if it's already there.
        if worst_change <= CB_THRESHOLD_PCT and ReasonCode.CB_LIKE not in codes:
            codes.append(ReasonCode.CB_LIKE)

        if any(c in (ReasonCode.CB_LIKE, ReasonCode.LIQ_CASCADE) for c in codes):
            level = RedLineLevel.TRIP
        elif any(c in (ReasonCode.LEV_ETF_AMP, ReasonCode.GAP_ORACLE) for c in codes):
            level = RedLineLevel.WATCH
        else:
            level = RedLineLevel.HOLD

        return RedLineVerdict(
            level=level,
            reason_codes=codes if level != RedLineLevel.HOLD else [],
            evidence=[f"worst_change={worst_change}", f"events={len(evs)}"],
            action=action_for_level(level),
            model_may_override_hard_limit=False,
            source="llm",
        )


class KilnEventClassifier:
    """Strict adapter for the real Kiln event-classification call."""

    def __init__(self, client, flow_tag: str = "redline_hold"):
        self.client = client
        self.flow_tag = flow_tag

    def classify(self, events: Iterable[MarketEvent]) -> RedLineVerdict:
        from agent.follow_agent.kiln_client import ChatMessage
        payload = [
            {"symbol": e.symbol, "change_pct": e.change_pct, "kind": e.kind, "timestamp": e.timestamp}
            for e in events
        ]
        reply = self.client.chat([
            ChatMessage("system", "Return JSON only: level HOLD/WATCH/TRIP, reason_codes array, evidence array."),
            ChatMessage("user", json.dumps(payload, ensure_ascii=False, separators=(",", ":"))),
        ], flow_tag=self.flow_tag)
        try:
            body = json.loads(reply.text)
            level = RedLineLevel(str(body["level"]).upper())
            codes = [ReasonCode(str(x)) for x in body.get("reason_codes", [])]
            evidence = [str(x) for x in body.get("evidence", [])]
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise RuntimeError("Kiln classifier returned invalid verdict JSON") from exc
        return RedLineVerdict(level=level, reason_codes=codes, evidence=evidence, action=action_for_level(level), model_may_override_hard_limit=False, source="kiln")


__all__ = [
    "MarketEvent",
    "EventClassifier",
    "HynixMockClassifier",
    "KEYWORD_RULES",
    "CB_THRESHOLD_PCT",
    "KilnEventClassifier",
]
