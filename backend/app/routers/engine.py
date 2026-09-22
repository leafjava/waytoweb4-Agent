"""Engine router: start / stop / tick."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from ..audit import make_event
from ..authorization import AuthorizationError
from ..deps import get_passport_backend, get_state, get_trip_seconds
from ..engine import start_engine, stop_engine, tick_drawdown
from ..errors import not_found
from ..models import (
    EngineStartRequest,
    EngineStartResponse,
    EngineStopResponse,
    EngineTickResponse,
)
from ..state import AppState


router = APIRouter(prefix="/api/engine", tags=["engine"])


@router.post("/start", response_model=EngineStartResponse)
async def engine_start(
    req: EngineStartRequest,
    state: AppState = Depends(get_state),
    trip_seconds: int = Depends(get_trip_seconds),
    backend=Depends(get_passport_backend),
):
    try:
        rec = await start_engine(req.passport_id, state, trip_seconds, backend)
    except KeyError:
        raise not_found(f"passport {req.passport_id} not found")
    except ValueError as e:
        from ..errors import conflict
        raise conflict(str(e))
    state.append_event(make_event(
        "engine_start", req.passport_id,
        {"drawdown_usd": rec.drawdown_usd, "trip_seconds": trip_seconds},
    ))
    return EngineStartResponse(
        status=rec.status, drawdown_usd=rec.drawdown_usd, trip_seconds=trip_seconds,
    )


@router.post("/stop", response_model=EngineStopResponse)
async def engine_stop(
    req: EngineStartRequest,
    state: AppState = Depends(get_state),
    backend=Depends(get_passport_backend),
):
    try:
        rec = await stop_engine(req.passport_id, state, backend)
    except KeyError:
        raise not_found(f"passport {req.passport_id} not found")
    except AuthorizationError as exc:
        from ..errors import conflict
        raise conflict(str(exc))
    state.append_event(make_event(
        "engine_stop", req.passport_id, {"drawdown_usd": rec.drawdown_usd},
    ))
    return EngineStopResponse(status=rec.status, drawdown_usd=rec.drawdown_usd)


@router.post("/tick", response_model=EngineTickResponse)
async def engine_tick(
    req: EngineStartRequest,
    amount: float = Query(..., ge=0.0, description="Drawdown advance in USD."),
    state: AppState = Depends(get_state),
):
    try:
        rec = await tick_drawdown(req.passport_id, amount, state)
    except KeyError:
        raise not_found(f"passport {req.passport_id} not found")
    except ValueError as e:
        from ..errors import conflict
        raise conflict(str(e))
    state.append_event(make_event(
        "engine_tick", req.passport_id, {"drawdown_usd": rec.drawdown_usd},
    ))
    return EngineTickResponse(
        passport_id=rec.passport_id,
        drawdown_usd=rec.drawdown_usd,
        max_loss_usd=float(rec.spec["maxLossUsd"]),
    )


__all__ = ["router"]
