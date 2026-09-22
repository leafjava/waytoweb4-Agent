"""Mock copy-trading engine.

The real waytoweb4 service would stream market data and execute
paper trades; we don't have it on the demo machine, so we model it
as a deterministic state machine:

    drawdown_usd(t) = maxLossUsd * (t - t0) / trip_seconds

This means a fresh engine ticks up from 0 to `maxLossUsd` exactly
over `trip_seconds` seconds. At `drawdown_usd >= maxLossUsd`, the
RedLine rule gate would TRIP. We let the engine loop run; the
trigger of TRIP is the user clicking "Inject Hynix" (immediate) or
the demo running to completion naturally.

The loop is one asyncio.Task per passport; cancellation is clean
via `task.cancel()`. We expose `tick(amount)` as a synchronous
advance hook so the demo runner can skip the wait.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

from agent.redline_agent import HynixMockClassifier, RedLineJudge

from .state import (
    PASS_ACTIVE,
    PASS_PENDING_FACE,
    PASS_STOPPED,
    AppState,
    PassportRecord,
)


_JUDGE = RedLineJudge(classifier=HynixMockClassifier())


# Per-passport task registry. The module-level dict makes it easy to
# cancel from any router without going through a class.
_TASKS: dict[str, asyncio.Task] = {}


async def _engine_loop(passport_id: str, state: AppState, trip_seconds: int) -> None:
    """Tick the engine once a second until cancelled or status flips.

    Each tick updates `drawdown_usd` deterministically. We do NOT call
    RedLine here -- the engine advances drawdown regardless; RedLine
    is invoked explicitly via /api/redline/judge or /inject/hynix so
    the demo can show the events explicitly.
    """
    try:
        while True:
            async with state._lock:
                rec = state.passports.get(passport_id)
                if rec is None or rec.status != PASS_ACTIVE or not rec.engine_running:
                    return
                started = datetime.fromisoformat(rec.engine_started_at) if rec.engine_started_at else datetime.now(timezone.utc)
                elapsed = (datetime.now(timezone.utc) - started).total_seconds()
                ratio = min(1.0, max(0.0, elapsed / max(trip_seconds, 1)))
                rec.drawdown_usd = float(rec.spec["maxLossUsd"]) * ratio
                state.upsert_passport(rec)
            await asyncio.sleep(1.0)
    except asyncio.CancelledError:
        return


async def start_engine(passport_id: str, state: AppState, trip_seconds: int) -> PassportRecord:
    """Start the engine task for one passport. Idempotent.

    Async so we can `asyncio.create_task` inside the running loop.
    """
    rec = state.passports.get(passport_id)
    if rec is None:
        raise KeyError(passport_id)
    from .intent import is_expired
    if rec.authorization_status != "authorized":
        raise ValueError(f"passport {passport_id} is not authorized")
    if rec.confirmed_spec_hash != rec.spec_hash:
        raise ValueError(f"passport {passport_id} confirmation no longer matches")
    if rec.stop_requested or is_expired(rec.expiry):
        raise ValueError(f"passport {passport_id} is stopped or expired")
    if rec.engine_status in {"stopped", "stop_failed"}:
        raise ValueError(f"passport {passport_id} cannot be restarted")
    rec.status = PASS_ACTIVE
    if rec.engine_running:
        return rec
    rec.engine_started_at = datetime.now(timezone.utc).isoformat()
    rec.drawdown_usd = 0.0
    rec.engine_running = True
    rec.engine_status = "running"
    rec.trip_seconds = trip_seconds
    state.upsert_passport(rec)
    task = asyncio.create_task(_engine_loop(passport_id, state, trip_seconds))
    _TASKS[passport_id] = task
    return rec


async def stop_engine(passport_id: str, state: AppState) -> PassportRecord:
    """Stop the engine without revoking."""
    rec = state.passports.get(passport_id)
    if rec is None:
        raise KeyError(passport_id)
    task = _TASKS.get(passport_id)
    if task is not None and not task.done():
        task.cancel()
    _TASKS.pop(passport_id, None)
    if rec.status == PASS_ACTIVE:
        rec.status = PASS_STOPPED
    rec.engine_running = False
    rec.engine_status = "stopped"
    rec.stop_requested = True
    state.upsert_passport(rec)
    return rec


def tick_drawdown(passport_id: str, amount_usd: float, state: AppState) -> PassportRecord:
    """Synchronous drawdown advance. Used by tests and by the demo's
    'skip the wait' knob.

    Clamps the value to `maxLossUsd` so we never overshoot.
    """
    rec = state.passports.get(passport_id)
    if rec is None:
        raise KeyError(passport_id)
    max_loss = float(rec.spec["maxLossUsd"])
    rec.drawdown_usd = min(max_loss, max(0.0, float(amount_usd)))
    state.upsert_passport(rec)
    return rec


async def cancel_all() -> None:
    """Stop every running engine task. Called on app shutdown."""
    tasks = list(_TASKS.values())
    _TASKS.clear()
    for t in tasks:
        t.cancel()
    for t in tasks:
        try:
            await t
        except (asyncio.CancelledError, Exception):
            pass


def run_judge(spec: dict[str, Any], drawdown_usd: float, events: list[Any] | None):
    """Thin wrapper around RedLineJudge for routers. Returned object
    is a RedLineVerdict (from the agent package)."""
    # Build a transient CopyTradingSpec object so the judge sees the
    # real locked spec, not a dict.
    from agent.follow_agent.spec_schema import CopyTradingSpec

    cspec = CopyTradingSpec.model_validate(spec)
    return _JUDGE.judge(cspec, drawdown_usd, events or [])


__all__ = [
    "start_engine",
    "stop_engine",
    "tick_drawdown",
    "cancel_all",
    "run_judge",
]
