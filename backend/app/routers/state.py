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


router = APIRouter(prefix="/api/state", tags=["state"])


@router.get("")
def get_state_snapshot(state: AppState = Depends(get_state)):
    snap = state.snapshot()
    snap["token_report"] = render_report()
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
