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
from agent.shared.evidence import use_evidence_writer
from fastapi import APIRouter, Depends

from ..audit import make_event
from ..authorization import AuthorizationError
from ..deps import get_passport_backend, get_redline_judge, get_state
from ..engine import run_judge, stop_engine
from ..errors import not_found
from ..models import RedLineJudgeRequest, RedLineJudgeResponse
from ..state import AppState


router = APIRouter(prefix="/api/redline", tags=["redline"])


async def _apply_trip(passport_id: str, state: AppState, backend, trigger: str) -> dict:
    try:
        rec = await stop_engine(passport_id, state, backend, trigger.upper())
    except AuthorizationError as exc:
        from ..errors import conflict
        raise conflict(str(exc))
    return {
        "stopped": True,
        "revoked": rec.authorization_status == "revoked",
        "revoke_tx_hash": rec.tx_revoke_hash,
    }


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
    redline_judge=Depends(get_redline_judge),
):
    rec = state.passports.get(req.passport_id)
    if rec is None:
        raise not_found(f"passport {req.passport_id} not found")

    events = [MarketEvent(**e) for e in (req.events or [])] if req.events else None
    with use_evidence_writer(state.evidence):
        verdict = run_judge(rec.spec, rec.drawdown_usd, events, redline_judge)

    flow = "redline_trip" if verdict.level == RedLineLevel.TRIP else "redline_hold"
    side_effects: dict | None = None

    if verdict.action == RedLineAction.STOP_AND_REVOKE:
        side_effects = await _apply_trip(req.passport_id, state, backend, "redline_trip")

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
    redline_judge=Depends(get_redline_judge),
):
    """Inject the canonical Hynix crash pack and judge."""
    rec = state.passports.get(req.passport_id)
    if rec is None:
        raise not_found(f"passport {req.passport_id} not found")

    events = hynix_crash_pack()
    with use_evidence_writer(state.evidence):
        verdict = run_judge(rec.spec, rec.drawdown_usd, events, redline_judge)

    side_effects: dict | None = None
    if verdict.action == RedLineAction.STOP_AND_REVOKE:
        side_effects = await _apply_trip(req.passport_id, state, backend, "demo_inject")

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
