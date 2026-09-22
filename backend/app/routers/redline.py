"""RedLine router: judge + inject hynix.

If the verdict is TRIP we automatically call the passport backend's
revoke and stop the engine, then return side_effects so the
frontend can show the second tx hash.
"""

from __future__ import annotations

from agent.redline_agent import (
    HynixMockClassifier,
    MarketEvent,
    hynix_crash_pack,
)
from agent.redline_agent.schema import RedLineAction, RedLineLevel
from fastapi import APIRouter, Depends

from ..audit import make_event
from ..deps import get_passport_backend, get_state
from ..engine import run_judge, stop_engine
from ..errors import not_found
from ..models import RedLineJudgeRequest, RedLineJudgeResponse
from ..state import AppState


router = APIRouter(prefix="/api/redline", tags=["redline"])


def _verdict_to_dict(v) -> dict:
    return {
        "level": v.level.value,
        "reason_codes": [c.value for c in v.reason_codes],
        "evidence": v.evidence,
        "action": v.action.value,
        "source": v.source,
        "model_may_override_hard_limit": v.model_may_override_hard_limit,
    }


@router.post("/judge", response_model=RedLineJudgeResponse)
async def judge(
    req: RedLineJudgeRequest,
    state: AppState = Depends(get_state),
    backend=Depends(get_passport_backend),
):
    rec = state.passports.get(req.passport_id)
    if rec is None:
        raise not_found(f"passport {req.passport_id} not found")

    events = [MarketEvent(**e) for e in (req.events or [])] if req.events else None
    verdict = run_judge(rec.spec, rec.drawdown_usd, events)

    flow = "redline_trip" if verdict.level == RedLineLevel.TRIP else "redline_hold"
    side_effects: dict | None = None

    if verdict.action == RedLineAction.STOP_AND_REVOKE:
        await stop_engine(req.passport_id, state)
        try:
            new_rec = backend.revoke(req.passport_id, state)
        except (KeyError, ValueError):
            new_rec = None
        if new_rec is not None:
            state.append_event(make_event(
                "revoke", req.passport_id,
                {"tx_hash": new_rec.tx_revoke_hash, "trigger": "redline_trip"},
            ))
            side_effects = {
                "stopped": True,
                "revoked": True,
                "revoke_tx_hash": new_rec.tx_revoke_hash,
            }

    rec.last_verdict = _verdict_to_dict(verdict)
    state.upsert_passport(rec)
    state.append_event(make_event(
        "redline_judge", req.passport_id,
        {"level": verdict.level.value, "reason_codes": [c.value for c in verdict.reason_codes]},
    ))
    return RedLineJudgeResponse(
        passport_id=req.passport_id,
        verdict=_verdict_to_dict(verdict),
        flow=flow,
        side_effects=side_effects,
    )


@router.post("/inject/hynix", response_model=RedLineJudgeResponse)
async def inject_hynix(
    req: RedLineJudgeRequest,
    state: AppState = Depends(get_state),
    backend=Depends(get_passport_backend),
):
    """Inject the canonical Hynix crash pack and judge."""
    rec = state.passports.get(req.passport_id)
    if rec is None:
        raise not_found(f"passport {req.passport_id} not found")

    events = hynix_crash_pack()
    verdict = run_judge(rec.spec, rec.drawdown_usd, events)

    side_effects: dict | None = None
    if verdict.action == RedLineAction.STOP_AND_REVOKE:
        await stop_engine(req.passport_id, state)
        try:
            new_rec = backend.revoke(req.passport_id, state)
        except (KeyError, ValueError):
            new_rec = None
        if new_rec is not None:
            state.append_event(make_event(
                "revoke", req.passport_id,
                {"tx_hash": new_rec.tx_revoke_hash, "trigger": "demo_inject"},
            ))
            side_effects = {
                "stopped": True,
                "revoked": True,
                "revoke_tx_hash": new_rec.tx_revoke_hash,
            }

    rec.last_verdict = _verdict_to_dict(verdict)
    state.upsert_passport(rec)
    state.append_event(make_event(
        "demo_inject", req.passport_id,
        {"level": verdict.level.value, "events": [e.symbol for e in events]},
    ))
    return RedLineJudgeResponse(
        passport_id=req.passport_id,
        verdict=_verdict_to_dict(verdict),
        flow="redline_trip",
        side_effects=side_effects,
    )


__all__ = ["router"]