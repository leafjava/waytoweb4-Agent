"""Passport router: mint / revoke / get."""

from __future__ import annotations

from agent.follow_agent.spec_schema import CopyTradingSpec
from agent.shared.exceptions import SpecValidationError
from fastapi import APIRouter, Depends, Path

from ..audit import make_event
from ..deps import get_passport_backend, get_state
from ..errors import conflict, map_agent_error, not_found, spec_error
from ..hash import spec_hash
from ..models import MintRequest, MintResponse, RevokeResponse
from ..state import PASS_REVOKED, AppState


router = APIRouter(prefix="/api/passport", tags=["passport"])


@router.post("/mint", response_model=MintResponse)
def mint_passport(
    req: MintRequest,
    state: AppState = Depends(get_state),
    backend=Depends(get_passport_backend),
):
    # Defence in depth: re-validate even if the frontend claims locked.
    try:
        spec_obj = CopyTradingSpec.model_validate(req.spec)
    except SpecValidationError as e:
        raise spec_error(str(e))
    spec_dict = spec_obj.model_dump(mode="json")
    spec_dict["faceVerified"] = False  # ignore any client-side claim

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
        },
    ))
    return MintResponse(
        passport_id=rec.passport_id,
        spec_hash=rec.spec_hash,
        tx_hash=rec.tx_mint_hash,
        status=rec.status,
        leader_id=rec.leader_id,
        notional_usd=rec.notional_usd,
        fee_bps=rec.fee_bps,
        expiry=rec.expiry,
        backend=backend.label,
    )


@router.post("/{passport_id}/revoke", response_model=RevokeResponse)
def revoke_passport(
    passport_id: str = Path(...),
    state: AppState = Depends(get_state),
    backend=Depends(get_passport_backend),
):
    try:
        rec = backend.revoke(passport_id, state)
    except KeyError:
        raise not_found(f"passport {passport_id} not found")
    except ValueError as e:
        raise conflict(str(e))
    except Exception as e:  # noqa: BLE001
        raise map_agent_error(e)

    state.append_event(make_event(
        "revoke", passport_id,
        {"tx_hash": rec.tx_revoke_hash, "previous_status": "active"},
    ))
    return RevokeResponse(
        passport_id=passport_id,
        tx_hash=rec.tx_revoke_hash or "",
        status=rec.status,
        previous_status="active",
    )


@router.get("/{passport_id}")
def get_passport(
    passport_id: str = Path(...),
    state: AppState = Depends(get_state),
):
    rec = state.passports.get(passport_id)
    if rec is None:
        raise not_found(f"passport {passport_id} not found")
    return rec.to_public_dict()


__all__ = ["router"]