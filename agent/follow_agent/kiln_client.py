"""Kiln / gpt-oss-120b client with a deterministic mock fallback.

The PRD requires real Kiln calls (Challenge A scoring rule 2), but we
also need the agents to run end-to-end without network access (the
demo venue is shaky) and inside unit tests. The strategy is:

    * `KilnClient` -- abstract protocol defining the chat surface.
    * `HttpKilnClient` -- talks to the real Kiln API over HTTPS. Reads
      its endpoint / key from environment variables so the deployment
      can swap models or providers without code changes.
    * `MockKilnClient` -- returns deterministic responses from a small
      set of canned reply scripts. Behaviour is driven by the latest
      user message plus the `flow_tag`, so tests can assert on the
      exact conversation shape.
    * `build_kiln_client()` -- factory: returns `HttpKilnClient` if
      `KILN_API_KEY` is set, otherwise `MockKilnClient`. This makes
      "no key in env" the dev/test default, which is what we want.

Every call records tokens / latency into the shared `TokenLogger`
under the supplied `flow_tag` so the README table is automatic.
"""

from __future__ import annotations

import json
import os
import re
import time
import uuid
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Protocol

from agent.shared.token_logger import get_default_logger
from agent.shared.evidence import get_evidence_writer

# ---- Environment configuration ---------------------------------------------

KILN_API_BASE_ENV = "KILN_API_BASE"
KILN_API_KEY_ENV = "KILN_API_KEY"
KILN_MODEL_ENV = "KILN_MODEL"

DEFAULT_API_BASE = "https://api.kiln.ai/v1"
DEFAULT_MODEL = "gpt-oss-120b"


# ---- Public types -----------------------------------------------------------


@dataclass(frozen=True)
class ChatMessage:
    """A single message in a Kiln chat completion.

    `role` is one of "system" / "user" / "assistant". We use a frozen
    dataclass rather than a TypedDict so that callers can't mutate a
    message after it has been sent.
    """

    role: str
    content: str

    def to_dict(self) -> dict[str, str]:
        return {"role": self.role, "content": self.content}


@dataclass(frozen=True)
class KilnReply:
    """One completion returned by a Kiln client."""

    text: str
    tokens_in: int
    tokens_out: int
    latency_s: float
    model: str
    usage_source: str = "api"
    request_id: str | None = None


class KilnClient(Protocol):
    """The contract every Kiln client must satisfy."""

    model: str

    def chat(self, messages: Iterable[ChatMessage], flow_tag: str) -> KilnReply: ...


# ---- Mock implementation ----------------------------------------------------


# A very rough tokenizer. We only need it to count tokens for the
# README table; the real API will return the canonical count via the
# usage field. The 4-chars-per-token heuristic is good enough for
# English / Chinese mixed prose and matches what most cost calculators
# use as a default.
def _approx_tokens(text: str) -> int:
    if not text:
        return 0
    # Treat CJK characters more aggressively: one token per character is
    # close to what BPE-style tokenizers do for short Chinese strings.
    cjk = sum(1 for c in text if "一" <= c <= "鿿")
    other = len(text) - cjk
    return cjk + (other + 3) // 4


def _total_tokens_in(messages: Iterable[ChatMessage]) -> int:
    return sum(_approx_tokens(m.content) for m in messages)


class MockKilnClient:
    """Deterministic mock that emits canned JSON for the demo flows.

    Behaviour depends on the latest user message:

      * if it asks a follow-up question (matches "leader", "额度",
        "限亏", "expiry", etc.) -> returns a clarifying question
      * otherwise -> returns a frozen demo Spec in JSON form

    The mock also recognises a small "trigger" language for the
    redline-as-LLM-classifier path (海力士 / circuit breaker keywords
    etc.) but the actual redline judgments are exercised in
    redline_agent tests; this mock is only for the follow agent.
    """

    model: str = DEFAULT_MODEL

    # Match the patterns users will actually type. We deliberately
    # match keyword clusters, not exact strings. Keep these aligned
    # with the heuristic patterns in clarifier._looks_like_answer() so
    # the mock and the real flow agree on what counts as "filled".
    _LEADER_RE = re.compile(r"\bleader[-_a-zA-Z0-9]{1,32}\b")
    _AMOUNT_RE = re.compile(r"(\d{2,5})\s*(u|usd|美元|元|\$)?", re.IGNORECASE)
    _LOSS_RE = re.compile(r"(亏|止损|maxloss|stop\s*loss)", re.IGNORECASE)

    def chat(self, messages: Iterable[ChatMessage], flow_tag: str) -> KilnReply:
        msgs = list(messages)
        last_user = next((m for m in reversed(msgs) if m.role == "user"), None)
        text = (last_user.content if last_user else "").lower()

        t0 = time.perf_counter()
        if flow_tag == "spec_emit":
            reply_text = self._mock_spec_json()
        elif flow_tag == "demo_inject":
            reply_text = self._mock_inject_response(text)
        else:
            reply_text = self._mock_clarify(text)
        # Account for the simulated generation time on the latency
        # number so the energy estimate is non-trivial in dev.
        time.sleep(0.02)
        latency = time.perf_counter() - t0

        tokens_in = _total_tokens_in(msgs)
        tokens_out = _approx_tokens(reply_text)
        call_id = str(uuid.uuid4())
        get_default_logger().record(flow_tag, tokens_in, tokens_out, latency, usage_source="estimated", model=self.model, request_id=call_id)
        return KilnReply(
            text=reply_text,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            latency_s=latency,
            model=self.model,
            usage_source="estimated", request_id=call_id,
        )

    # -- canned replies -----------------------------------------------------

    @staticmethod
    def _mock_spec_json() -> str:
        # Deliberately matches the PRD demo defaults. The emitter is
        # expected to parse this with json.loads and then re-validate
        # via CopyTradingSpec; tests assert both paths.
        from datetime import datetime, timedelta, timezone
        expiry = (datetime.now(timezone.utc) + timedelta(hours=48)).replace(microsecond=0).isoformat()
        payload = {
            "mode": "copy",
            "leaderId": "leader-demo-001",
            "venue": "paper",
            "notionalUsd": 500,
            "maxLossUsd": 50,
            "expiry": expiry,
            "faceVerified": False,
            "paper": True,
        }
        return json.dumps(payload, ensure_ascii=False)

    @staticmethod
    def _mock_clarify(text: str) -> str:
        if not MockKilnClient._LEADER_RE.search(text):
            return "你想跟哪个 leader？给我一个 leader id（比如 leader-demo-001）。"
        if not MockKilnClient._AMOUNT_RE.search(text):
            return "跟多少额度（USD）？Demo 默认 500。"
        if not MockKilnClient._LOSS_RE.search(text):
            return "限亏多少？Demo 默认 50（不超过本金）。"
        return "字段都齐了，可以出 Spec。"

    @staticmethod
    def _mock_inject_response(text: str) -> str:
        # Used by the redline demo path; just acknowledge.
        return json.dumps(
            {"level": "TRIP", "reason_codes": ["CB_LIKE"], "evidence": [text[:120]]},
            ensure_ascii=False,
        )


# ---- HTTP implementation ---------------------------------------------------


class HttpKilnClient:
    """Real Kiln client. Lazy-imports httpx so unit tests don't pay the
    import cost and so the module is still importable on a stripped
    image without httpx."""

    model: str

    def __init__(self, api_base: str, api_key: str, model: str) -> None:
        self.api_base = api_base.rstrip("/")
        self.api_key = api_key
        self.model = model

    def chat(self, messages: Iterable[ChatMessage], flow_tag: str) -> KilnReply:
        try:
            import httpx  # type: ignore
        except ImportError as e:  # pragma: no cover - environment guard
            raise RuntimeError(
                "httpx is required for HttpKilnClient. "
                "Install with `pip install httpx` or unset KILN_API_KEY to use the mock."
            ) from e

        msgs = [m.to_dict() for m in messages]
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": msgs,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        url = f"{self.api_base}/chat/completions"

        t0 = time.perf_counter()
        resp = httpx.post(url, json=payload, headers=headers, timeout=30.0)
        latency = time.perf_counter() - t0
        resp.raise_for_status()
        body = resp.json()

        # Try the OpenAI-style usage block first; fall back to a rough
        # approximation if the provider omits it.
        response_model = body.get("model")
        if response_model != self.model:
            raise RuntimeError(f"Kiln response model mismatch: expected {self.model!r}, got {response_model!r}")
        usage = body.get("usage") or {}
        usage_source = "api" if "prompt_tokens" in usage and "completion_tokens" in usage else "unavailable"
        tokens_in = int(usage.get("prompt_tokens") or 0)
        tokens_out = int(usage.get("completion_tokens") or 0)

        try:
            text = body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as e:
            raise RuntimeError(f"Unexpected Kiln response shape: {body!r}") from e

        call_id = str(uuid.uuid4())
        get_default_logger().record(flow_tag, tokens_in, tokens_out, latency, usage_source=usage_source, model=self.model, request_id=call_id)
        return KilnReply(
            text=text,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            latency_s=latency,
            model=self.model,
            usage_source=usage_source, request_id=call_id,
        )


# ---- Factory ----------------------------------------------------------------


def _env(name: str, default: str | None = None) -> str | None:
    val = os.environ.get(name)
    if val is None or val == "":
        return default
    return val


def build_kiln_client(env: Mapping[str, str] | None = None) -> KilnClient:
    """Pick the right Kiln client for the current environment.

    Resolution order:
      1. If `env` (a mapping like os.environ) has `KILN_API_KEY` set,
         use `HttpKilnClient` with the rest of the env-derived config.
      2. Otherwise fall back to `MockKilnClient`. This is the desired
         behaviour for unit tests and for offline development.

    Passing an explicit `env` makes the function easy to test; we also
    read `os.environ` directly so the production code path doesn't
    need plumbing.
    """
    src: Mapping[str, str] = env if env is not None else os.environ  # type: ignore[assignment]
    mode = (src.get("KILN_MODE") or _env("KILN_MODE") or "offline").lower()
    key = src.get(KILN_API_KEY_ENV) or _env(KILN_API_KEY_ENV)
    if mode not in {"offline", "live"}:
        raise RuntimeError(f"KILN_MODE must be 'offline' or 'live'; got {mode!r}")
    if mode == "live":
        if not key:
            raise RuntimeError("KILN_MODE=live requires KILN_API_KEY; refusing mock fallback")
        base = src.get(KILN_API_BASE_ENV) or _env(KILN_API_BASE_ENV) or DEFAULT_API_BASE
        model = src.get(KILN_MODEL_ENV) or _env(KILN_MODEL_ENV) or DEFAULT_MODEL
        if model != DEFAULT_MODEL:
            raise RuntimeError(f"Challenge A requires KILN_MODEL={DEFAULT_MODEL}; got {model!r}")
        return HttpKilnClient(api_base=base, api_key=key, model=DEFAULT_MODEL)
    return MockKilnClient()


__all__ = [
    "ChatMessage",
    "KilnReply",
    "KilnClient",
    "MockKilnClient",
    "HttpKilnClient",
    "build_kiln_client",
    "KILN_API_BASE_ENV",
    "KILN_API_KEY_ENV",
    "KILN_MODEL_ENV",
    "DEFAULT_API_BASE",
    "DEFAULT_MODEL",
]
