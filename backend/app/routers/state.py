"""State + reset router."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse

from ..deps import get_state
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
async def reset_state(state: AppState = Depends(get_state)):
    await state.reset()
    return DemoResetResponse(ok=True)


__all__ = ["router"]