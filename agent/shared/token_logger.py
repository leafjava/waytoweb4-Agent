"""Per-flow token / latency / energy logger.

PRD §9 requires the README to report tokens split by flow:

    flow          tokens_in  tokens_out  latency_s  energy_Wh_est
    clarify       ...
    spec_emit     ...
    redline_trip  ...
    total         ...
    assumption    180W NPU-class, energy = 180 * latency / 3600

This module is the single source of truth that the README table is
generated from. Both the Follow Agent and the RedLine Agent push their
records here.
"""

from __future__ import annotations

import threading
import os
import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Iterable

from .energy import assumption_note, estimate_wh


# The PRD defines five flow tags. Anything else should be rejected at
# record() time so we don't silently leak un-bucketed token usage into
# the README.
ALLOWED_FLOWS: tuple[str, ...] = (
    "clarify",
    "spec_emit",
    "redline_hold",
    "redline_trip",
    "demo_inject",
)


@dataclass
class _FlowBucket:
    calls: int = 0
    tokens_in: int = 0
    tokens_out: int = 0
    latency_s: float = 0.0

    @property
    def energy_wh(self) -> float:
        return estimate_wh(self.latency_s, self.tokens_in + self.tokens_out)


@dataclass
class TokenLogger:
    """Thread-safe per-flow token logger.

    The backend may call into both agents concurrently. We use a
    reentrant lock so the report() path can call totals() without
    deadlocking on itself. The cost of RLock over Lock is one extra
    attribute per acquire; we are nowhere near the bottleneck.
    """

    _buckets: dict[str, _FlowBucket] = field(default_factory=dict)
    _lock: threading.RLock = field(default_factory=threading.RLock)

    def record(self, flow: str, tokens_in: int, tokens_out: int, latency_s: float, *, usage_source: str = "api", model: str = "gpt-oss-120b", request_id: str | None = None) -> None:
        """Append one Kiln call to the named flow bucket."""
        if flow not in ALLOWED_FLOWS:
            raise ValueError(
                f"Unknown flow tag {flow!r}; must be one of {ALLOWED_FLOWS}. "
                "If you need a new tag, add it to ALLOWED_FLOWS in token_logger.py."
            )
        if tokens_in < 0 or tokens_out < 0:
            raise ValueError("Token counts must be non-negative.")
        with self._lock:
            b = self._buckets.setdefault(flow, _FlowBucket())
            b.calls += 1
            b.tokens_in += tokens_in
            b.tokens_out += tokens_out
            b.latency_s += latency_s
        from .evidence import get_evidence_writer
        writer = get_evidence_writer()
        if writer:
            writer.append("calls.jsonl", {"run_id": writer.run_id, "call_id": request_id or str(uuid.uuid4()), "flow": flow, "model": model, "tokens_in": tokens_in, "tokens_out": tokens_out, "usage_source": usage_source, "latency_s": latency_s, "energy_Wh_est": estimate_wh(latency_s), "at": datetime.now(timezone.utc).isoformat()})

    def flows(self) -> Iterable[str]:
        with self._lock:
            return tuple(self._buckets.keys())

    def totals(self) -> _FlowBucket:
        """Aggregate across every flow seen so far."""
        with self._lock:
            agg = _FlowBucket()
            for b in self._buckets.values():
                agg.calls += b.calls
                agg.tokens_in += b.tokens_in
                agg.tokens_out += b.tokens_out
                agg.latency_s += b.latency_s
            return agg

    def report(self) -> str:
        """Render the PRD §9 markdown table.

        The output is plain markdown so it can be pasted straight into
        the README. The width is fixed so columns line up in both the
        GitHub renderer and most terminals.
        """
        with self._lock:
            rows = [(name, self._buckets.get(name, _FlowBucket())) for name in ALLOWED_FLOWS]
            totals = self.totals()

        header = (
            f"{'flow':<14}  {'tokens_in':>10}  {'tokens_out':>11}  "
            f"{'latency_s':>10}  {'energy_Wh_est':>13}"
        )
        sep = "-" * len(header)
        lines = [header, sep]
        for name, b in rows:
            lines.append(
                f"{name:<14}  {b.tokens_in:>10}  {b.tokens_out:>11}  "
                f"{b.latency_s:>10.3f}  {b.energy_wh:>13.4f}"
            )
        lines.append(sep)
        lines.append(
            f"{'total':<14}  {totals.tokens_in:>10}  {totals.tokens_out:>11}  "
            f"{totals.latency_s:>10.3f}  {totals.energy_wh:>13.4f}"
        )
        lines.append(sep)
        lines.append(f"assumption    {assumption_note()}")
        return "\n".join(lines)


# Process-wide default logger. Modules in this package use this unless
# the caller wires a fresh one in (which is what the tests do).
_default_logger: TokenLogger | None = None
_default_lock = threading.Lock()


def get_default_logger() -> TokenLogger:
    global _default_logger
    if _default_logger is None:
        with _default_lock:
            if _default_logger is None:
                _default_logger = TokenLogger()
    return _default_logger


def reset_default_logger() -> None:
    """Reset the default logger. Test-only utility."""
    global _default_logger
    with _default_lock:
        _default_logger = None
