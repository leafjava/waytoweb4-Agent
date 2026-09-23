"""State + reset router."""

from __future__ import annotations

import os

from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse

from ..deps import get_passport_backend, get_state
from ..engine import cancel_all
from ..errors import conflict
from ..models import DemoResetResponse
from ..state import AppState
from ..token_report import render_report
from agent.shared.energy import NPU_POWER_W
from agent.shared.token_logger import get_default_logger


router = APIRouter(prefix="/api/state", tags=["state"])


@router.get("")
def get_state_snapshot(state: AppState = Depends(get_state)):
    snap = state.snapshot()
    snap["token_report"] = render_report()
    token_summary = get_default_logger().snapshot()
    snap["token_summary"] = token_summary
    snap["workload"] = {
        "run_id": state.run_id,
        "model": "gpt-oss-120b",
        "source_mode": os.environ.get("KILN_MODE", "offline").lower(),
        "power_assumption_w": NPU_POWER_W,
        "active_sessions": sum(rec.engine_running for rec in state.passports.values()),
        "passport_count": len(state.passports),
        "agent_calls": token_summary["total"]["calls"],
    }
    return snap


@router.get("/tokens", response_class=PlainTextResponse)
def get_token_report() -> PlainTextResponse:
    return PlainTextResponse(render_report())


@router.post("/reset", response_model=DemoResetResponse)
async def reset_state(
    state: AppState = Depends(get_state),
    backend=Depends(get_passport_backend),
):
    if backend.label != "mock" or os.environ.get("KILN_MODE", "offline").lower() == "live":
        raise conflict("demo reset is disabled for chain-backed or live runs")
    await cancel_all()
    await state.reset()
    return DemoResetResponse(ok=True)


__all__ = ["router"]
