"""REST-shaped mock of the waytoweb4 trading service.

This module exists because the real waytoweb4 API documentation is not
yet available (PRD §10). Rather than letting `engine.py` look like
"an in-process asyncio task pretending to be a remote service", we
expose the same operations behind a clean REST shape that mirrors
what a real broker / copy-trading service would expose:

    GET    /v1/leaders
    GET    /v1/leaders/{leader_id}/positions
    POST   /v1/paper/start
    GET    /v1/paper/{paper_id}/pnl
    POST   /v1/paper/{paper_id}/stop

When waytoweb4 ships their docs, every endpoint in this file is the
single point of contact to swap. The internal engine / passport
pipeline below stays unchanged.

This module owns NO business logic of its own. It composes the
existing `engine.*` and `passport_backends.*` functions so all
state and audit-log behaviour stays in one place.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from .audit import make_event
from .config import settings
from .deps import get_passport_backend, get_state
from .engine import start_engine, stop_engine, tick_drawdown
from .hash import spec_hash
from .state import PASS_ACTIVE, PASS_REVOKED, PASS_STOPPED, AppState


router = APIRouter(prefix="/v1", tags=["waytoweb4-mock"])


# ---- Seed data ----------------------------------------------------------

_LEADERS_PATH = Path(__file__).resolve().parent / "waytoweb4_leaders.json"


def _load_leaders() -> list[dict[str, Any]]:
    if not _LEADERS_PATH.exists():
        return []
    body = json.loads(_LEADERS_PATH.read_text(encoding="utf-8"))
    return list(body.get("leaders", []))


# ---- DTOs ---------------------------------------------------------------


class StartPaperRequest(BaseModel):
    leader_id: str = Field(..., description="waytoweb4 leader id")
    notional_usd: float = Field(..., gt=0)
    max_loss_usd: float = Field(..., gt=0)
    expiry_iso: str = Field(..., description="ISO-8601 datetime")
    venue: str = Field(default="paper", description="forbidden to set non-paper here")


class StopPaperRequest(BaseModel):
    reason: str = Field(default="user", description="'user' or 'kill' (RedLine)")


# ---- Endpoints ----------------------------------------------------------


@router.get("/leaders")
def list_leaders():
    """Return the seeded list of copy-trade leaders.

    Real waytoweb4 will return live track records. For the demo we
    return the static seed in `waytoweb4_leaders.json`.
    """
    return {"leaders": _load_leaders()}


@router.get("/leaders/{leader_id}/positions")
def get_leader_positions(leader_id: str):
    """Return current open positions for a leader.

    Paper-copy trading never holds real positions, so this always
    returns an empty list. Kept in the contract so the frontend can
    iterate the same shape as it would against the real service.
    """
    return {"leader_id": leader_id, "positions": []}


@router.post("/paper/start", status_code=status.HTTP_201_CREATED)
async def start_paper(
    req: StartPaperRequest,
    state: AppState = Depends(get_state),
    backend=Depends(get_passport_backend),
):
    """Start a paper copy-trade run.

    Internally this:
      1. builds a frozen CopyTradingSpec (and re-validates server-side)
      2. mints a Strategy Passport via the configured backend
      3. flips faceVerified (mock face gate)
      4. starts the deterministic engine

    The returned `paper_id` is the passport_id; downstream endpoints
    accept that as the document key.
    """
    if req.venue != "paper":
        raise HTTPException(status_code=422, detail="venue must be 'paper'")
    if req.max_loss_usd > req.notional_usd:
        raise HTTPException(status_code=422, detail="max_loss_usd cannot exceed notional_usd")

    # Build the locked Spec server-side; reject any value the caller
    # might inject that the agent schema forbids.
    spec_dict = {
        "mode": "copy",
        "leaderId": req.leader_id,
        "venue": "paper",
        "notionalUsd": req.notional_usd,
        "maxLossUsd": req.max_loss_usd,
        "expiry": req.expiry_iso,
        "faceVerified": False,
        "paper": True,
    }

    # Re-validate through the agent schema (defence in depth).
    from agent.follow_agent.spec_schema import CopyTradingSpec
    from agent.shared.exceptions import SpecValidationError

    try:
        CopyTradingSpec.model_validate(spec_dict)
    except SpecValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))

    sh = spec_hash(spec_dict)
    rec = backend.mint(spec_dict, sh, state)
    state.append_event(make_event(
        "mint", rec.passport_id,
        {
            "tx_hash": rec.tx_mint_hash,
            "spec_hash": rec.spec_hash,
            "leader_id": rec.leader_id,
            "notional_usd": rec.notional_usd,
            "fee_bps": rec.fee_bps,
            "expiry": rec.expiry,
            "backend": backend.label,
            "via": "waytoweb4-mock /v1/paper/start",
        },
    ))

    # Mock face gate (matches routers/face.py behaviour).
    rec.face_verified = True
    state.upsert_passport(rec)

    await start_engine(rec.passport_id, state, settings.trip_seconds)
    return {
        "paper_id": rec.passport_id,
        "status": PASS_ACTIVE,
        "trip_seconds": settings.trip_seconds,
    }


@router.get("/paper/{paper_id}/pnl")
def get_paper_pnl(paper_id: str, state: AppState = Depends(get_state)):
    """Return current drawdown for a paper run.

    Real waytoweb4 would return position + unrealised PnL. For the
    demo we only expose `drawdown_usd` because that is what RedLine
    actually consumes (PRD §4.4).
    """
    rec = state.passports.get(paper_id)
    if rec is None:
        raise HTTPException(status_code=404, detail=f"paper {paper_id} not found")
    return {
        "paper_id": paper_id,
        "drawdown_usd": rec.drawdown_usd,
        "max_loss_usd": float(rec.spec.get("maxLossUsd", 0.0)),
        "status": rec.status,
        "engine_running": rec.engine_running,
        "last_update": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/paper/{paper_id}/stop")
async def stop_paper(
    paper_id: str,
    req: StopPaperRequest,
    state: AppState = Depends(get_state),
    backend=Depends(get_passport_backend),
):
    """Stop a paper run.

    `reason='user'` (default) just halts the engine.
    `reason='kill'` halts the engine AND revokes the passport on
    chain -- the equivalent of pressing the RedLine kill switch.
    """
    rec = state.passports.get(paper_id)
    if rec is None:
        raise HTTPException(status_code=404, detail=f"paper {paper_id} not found")

    await stop_engine(paper_id, state)

    if req.reason == "kill":
        try:
            new_rec = backend.revoke(paper_id, state)
        except (KeyError, ValueError) as e:
            raise HTTPException(status_code=409, detail=str(e))
        state.append_event(make_event(
            "revoke", paper_id,
            {"tx_hash": new_rec.tx_revoke_hash, "trigger": "waytoweb4-mock kill"},
        ))
        return {"paper_id": paper_id, "status": PASS_REVOKED, "revoke_tx_hash": new_rec.tx_revoke_hash}

    return {"paper_id": paper_id, "status": PASS_STOPPED}


__all__ = ["router", "_load_leaders"]