"""Follow Agent: turn natural language into a complete Spec.

The clarifier handles the multi-round Q&A that PRD §9 expects (1-2
rounds). The emitter handles the final, locked Spec emit.

Design intent: the LLM only produces text. Every numerical or
enumerated field is re-validated through `CopyTradingSpec` before it
can reach the backend. A hallucinated "paper": false, "mode":
"grid_bot", or "maxLossUsd": 99999 will be rejected here, not in
production.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable

from agent.shared.exceptions import SpecValidationError
from agent.follow_agent.kiln_client import ChatMessage, KilnClient
from agent.follow_agent.prompts import CLARIFY_SYSTEM, SPEC_EMIT_SYSTEM
from agent.follow_agent.spec_schema import CopyTradingSpec


# ---- Clarifier -------------------------------------------------------------


# Fields we treat as required for the Spec to be "complete". The order
# here matters: the clarifier asks about the earliest missing field
# first, so the user gets a predictable experience.
REQUIRED_FIELDS: tuple[str, ...] = (
    "leaderId",
    "notionalUsd",
    "maxLossUsd",
    "expiry",
)


@dataclass
class ClarificationQuestion:
    """One round of clarification.

    `field` is the schema field we're asking about. `question` is the
    Chinese / English sentence to show the user. `attempt` is the
    1-based round number, useful for the frontend to show "round 2 of
    2" progress.
    """

    field: str
    question: str
    attempt: int


# Cheap heuristics for parsing the user's answer. We use these so the
# clarifier can do "still missing?" checks without round-tripping to
# the LLM for every reply.
_AMOUNT_RE = re.compile(r"(\d{1,6}(?:\.\d+)?)\s*(u|usd|美元|元|\$)?", re.IGNORECASE)
_LEADER_RE = re.compile(r"\bleader[-_a-zA-Z0-9]{1,32}\b")
_LOSS_RE = re.compile(r"(亏|止损|loss)[^\d]{0,8}(\d{1,6}(?:\.\d+)?)", re.IGNORECASE)


def _looks_like_answer(field: str, text: str) -> bool:
    t = text.strip()
    if not t:
        return False
    if field == "leaderId":
        return bool(_LEADER_RE.search(t))
    if field in ("notionalUsd", "maxLossUsd"):
        return bool(_AMOUNT_RE.search(t))
    if field == "expiry":
        # Accept anything that mentions a duration or a date.
        return bool(re.search(r"(\d+\s*(h|hour|d|day|天|小时|分钟|分))|(20\d{2}-)", t, re.IGNORECASE))
    return True


class Clarifier:
    """Multi-round Q&A driver. Wraps a KilnClient for the question
    generation, but uses local heuristics to detect "still missing".

    The user-facing loop is:
        1. user types something
        2. clarifier checks what fields are obviously filled
        3. if any required field is missing -> ask the LLM to phrase
           a question, return ClarificationQuestion
        4. if all required fields are filled -> caller can call the
           Emitter
    """

    def __init__(self, client: KilnClient, max_rounds: int = 2) -> None:
        self.client = client
        self.max_rounds = max_rounds

    def first_question(self, user_text: str) -> ClarificationQuestion:
        """Return the first question for the user, if any."""
        missing = self._missing_fields(user_text)
        if not missing:
            return ClarificationQuestion(field="", question="字段都齐了，可以出 Spec。", attempt=1)
        first = missing[0]
        prompt = (
            f"用户说：{user_text!r}\n"
            f"还缺字段：{first}（{', '.join(missing)}）。请用中文问 1 个聚焦的问题。"
        )
        reply = self.client.chat(
            messages=[
                ChatMessage(role="system", content=CLARIFY_SYSTEM),
                ChatMessage(role="user", content=prompt),
            ],
            flow_tag="clarify",
        )
        return ClarificationQuestion(field=first, question=reply.text.strip(), attempt=1)

    def next_question(
        self,
        user_text: str,
        prior: ClarificationQuestion,
    ) -> ClarificationQuestion | None:
        """Either ask the next missing field, or return None if done."""
        if prior.attempt >= self.max_rounds:
            return None
        missing = self._missing_fields(user_text)
        if not missing:
            return None
        next_field = missing[0]
        if next_field == prior.field:
            # Same field still missing -- user didn't actually answer.
            # Refuse to ask a third time; let the backend surface a
            # "please answer the previous question" error.
            return None
        prompt = (
            f"用户补充说：{user_text!r}\n"
            f"现在缺：{next_field}。请用中文问 1 个聚焦的问题。"
        )
        reply = self.client.chat(
            messages=[
                ChatMessage(role="system", content=CLARIFY_SYSTEM),
                ChatMessage(role="user", content=prompt),
            ],
            flow_tag="clarify",
        )
        return ClarificationQuestion(
            field=next_field,
            question=reply.text.strip(),
            attempt=prior.attempt + 1,
        )

    def _missing_fields(self, text: str) -> list[str]:
        return [f for f in REQUIRED_FIELDS if not _looks_like_answer(f, text)]


# ---- Emitter ----------------------------------------------------------------


def _coerce_expiry(raw: object) -> datetime:
    """Coerce an LLM-emitted expiry string to a tz-aware UTC datetime."""
    if not isinstance(raw, str):
        raise SpecValidationError(f"expiry must be a string, got {type(raw).__name__}")
    s = raw.strip()
    # Accept 'Z' suffix by translating to '+00:00' for fromisoformat.
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(s)
    except ValueError as e:
        raise SpecValidationError(f"expiry {raw!r} is not a valid ISO-8601 datetime") from e
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt


def _parse_spec_payload(raw_text: str) -> dict:
    """Extract the JSON object from an LLM reply.

    The model is instructed to emit JSON-only but we still tolerate
    accidental code fences or leading prose.
    """
    text = raw_text.strip()
    # Strip code fences if present.
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    # Find the first '{' and the matching closing brace.
    start = text.find("{")
    if start < 0:
        raise SpecValidationError("LLM reply did not contain JSON.")
    depth = 0
    for i in range(start, len(text)):
        c = text[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                candidate = text[start:i + 1]
                try:
                    return json.loads(candidate)
                except json.JSONDecodeError as e:
                    raise SpecValidationError(f"LLM reply JSON was malformed: {e}") from e
    raise SpecValidationError("LLM reply had an unterminated JSON object.")


class Emitter:
    """Emit a locked CopyTradingSpec from a conversation.

    `client` -- KilnClient to talk to (mock or real).
    `history` -- full conversation (system + user + assistant turns).
    The emitter prepends SPEC_EMIT_SYSTEM as the system message.
    """

    def __init__(self, client: KilnClient, history: Iterable[ChatMessage] | None = None) -> None:
        self.client = client
        self.history: list[ChatMessage] = list(history or [])

    def add_user(self, text: str) -> None:
        self.history.append(ChatMessage(role="user", content=text))

    def emit(self) -> CopyTradingSpec:
        """Call Kiln, parse the JSON, validate via CopyTradingSpec."""
        messages = [ChatMessage(role="system", content=SPEC_EMIT_SYSTEM), *self.history]
        reply = self.client.chat(messages, flow_tag="spec_emit")
        self.history.append(ChatMessage(role="assistant", content=reply.text))

        payload = _parse_spec_payload(reply.text)

        # Coerce expiry before validation so Pydantic sees a real
        # datetime (and so we surface LLM-style date mistakes with a
        # useful message).
        if "expiry" in payload:
            payload["expiry"] = _coerce_expiry(payload["expiry"])

        try:
            spec = CopyTradingSpec.model_validate(payload)
        except Exception as e:
            # Pydantic's own errors are fine; just re-raise as our type
            # so the backend has one exception class to catch.
            raise SpecValidationError(f"Spec validation failed: {e}") from e
        return spec


__all__ = [
    "ClarificationQuestion",
    "Clarifier",
    "Emitter",
    "REQUIRED_FIELDS",
]