"""Passport preparation, confirmation, mint and revoke routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Path

from ..audit import make_event
from ..authorization import AuthorizationError, authorization_service
from ..deps import get_passport_backend, get_state
from ..engine import stop_engine
from ..errors import conflict, not_found, spec_error
from ..models import ConfirmRequest, MintRequest, MintResponse, PrepareRequest, RevokeResponse
from ..state import AppState

router = APIRouter(prefix="/api/passport", tags=["passport"])


def _response(rec) -> MintResponse:
    return MintResponse(
        passport_id=rec.passport_id, spec_hash=rec.spec_hash, tx_hash=rec.tx_mint_hash,
        status=rec.authorization_status, leader_id=rec.leader_id,
        notional_usd=rec.notional_usd, fee_bps=rec.fee_bps, expiry=rec.expiry,
        backend=rec.backend_label,
    )


@router.post("/prepare", response_model=MintResponse)
async def prepare_passport(req: PrepareRequest, state: AppState = Depends(get_state)):
    try:
        rec = await authorization_service.prepare(state, req.spec, req.request_id)
    except AuthorizationError as exc:
        if "request_id" in str(exc):
            raise conflict(str(exc))
        raise spec_error(str(exc))
    state.append_event(make_event("prepare", rec.passport_id, {"spec_hash": rec.spec_hash}))
    return _response(rec)


@router.post("/confirm", response_model=MintResponse)
async def confirm_passport(req: ConfirmRequest, state: AppState = Depends(get_state)):
    try:
        rec = await authorization_service.confirm(state, req.passport_id, req.spec_hash, req.request_id)
    except KeyError:
        raise not_found(f"passport {req.passport_id} not found")
    except AuthorizationError as exc:
        raise conflict(str(exc))
    state.append_event(make_event("confirm", rec.passport_id, {"spec_hash": rec.spec_hash}))
    return _response(rec)


@router.post("/mint", response_model=MintResponse)
async def mint_passport(req: MintRequest, state: AppState = Depends(get_state), backend=Depends(get_passport_backend)):
    try:
        rec = await authorization_service.mint(state, req.passport_id, req.request_id, backend)
    except KeyError:
        raise not_found(f"passport {req.passport_id} not found")
    except AuthorizationError as exc:
        raise conflict(str(exc))
    state.append_event(make_event(
        "mint_simulated" if rec.backend_label == "mock" else "mint", rec.passport_id,
        {"tx_hash": rec.tx_mint_hash, "simulation_id": rec.simulation_id, "spec_hash": rec.spec_hash},
    ))
    return _response(rec)


@router.post("/{passport_id}/revoke", response_model=RevokeResponse)
async def revoke_passport(passport_id: str = Path(...), state: AppState = Depends(get_state), backend=Depends(get_passport_backend)):
    rec = state.passports.get(passport_id)
    if rec is None:
        raise not_found(f"passport {passport_id} not found")
    if rec.authorization_status == "revoked":
        raise conflict(f"passport {passport_id} already revoked")
    previous = rec.authorization_status
    try:
        rec = await stop_engine(passport_id, state, backend, "PASSPORT_REVOKE")
    except AuthorizationError as exc:
        raise conflict(str(exc))
    return RevokeResponse(passport_id=passport_id, tx_hash=rec.tx_revoke_hash, status=rec.authorization_status, previous_status=previous)


@router.get("/{passport_id}")
def get_passport(passport_id: str = Path(...), state: AppState = Depends(get_state)):
    rec = state.passports.get(passport_id)
    if rec is None:
        raise not_found(f"passport {passport_id} not found")
    return rec.to_public_dict()


__all__ = ["router"]
