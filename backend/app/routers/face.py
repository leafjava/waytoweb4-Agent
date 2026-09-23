"""Face gate router.

The demo's "face verification" is a button. We still go through a
backend endpoint because:
    1. `faceVerified` lives on the Spec and is server-controlled.
    2. The Spec can only flip to face-verified AFTER mint; mint
       rejects any Spec that already has `faceVerified=true`.
    3. The audit log records when the gate fired.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from ..audit import make_event
from ..deps import get_state
from ..errors import conflict, not_found
from ..models import FaceVerifyRequest, FaceVerifyResponse
from ..state import AppState


router = APIRouter(prefix="/api/face", tags=["face"])


@router.post("/verify", response_model=FaceVerifyResponse)
async def verify_face(
    req: FaceVerifyRequest,
    state: AppState = Depends(get_state),
):
    session_id = str(req.session_id)
    session_key = f"face:{session_id}"
    fingerprint = hashlib.sha256(json.dumps(
        {"passport_id": req.passport_id, "method": req.method},
        sort_keys=True,
        separators=(",", ":"),
    ).encode()).hexdigest()

    async with state._lock:
        rec = state.passports.get(req.passport_id)
        if rec is None:
            raise not_found(f"passport {req.passport_id} not found")
        existing = state.requests.get(session_key)
        if existing and existing.get("fingerprint") != fingerprint:
            raise conflict("face session was already used for a different mandate")
        if existing:
            return FaceVerifyResponse(
                ok=True,
                passport_id=rec.passport_id,
                session_id=req.session_id,
                verified_at=rec.face_verified_at,
                method="button",
            )
        if rec.stop_requested or rec.authorization_status in {"revoked", "failed"}:
            raise conflict(
                f"passport {req.passport_id} cannot be face-verified in its current state"
            )
        if rec.authorization_status != "authorized" or rec.confirmed_spec_hash != rec.spec_hash:
            raise conflict("passport must be authorized before human approval")
        if rec.face_verified:
            raise conflict("passport already has a different human-approval session")

        ts = datetime.now(timezone.utc).isoformat()
        rec.face_verified = True
        rec.face_verification_mode = "button"
        rec.face_verified_at = ts
        rec.face_verification_method = "button"
        rec.face_verification_session_id = session_id
        rec.face_gate_status = "active"
        state.requests[session_key] = {
            "fingerprint": fingerprint,
            "passport_id": rec.passport_id,
            "spec_hash": rec.spec_hash,
        }
        state._save_locked()

    state.append_event(make_event(
        "face_verify",
        rec.passport_id,
        {
            "verified_at": ts,
            "method": "button",
            "session_id": session_id,
            "spec_hash": rec.spec_hash,
        },
    ))

    return FaceVerifyResponse(
        ok=True,
        passport_id=rec.passport_id,
        session_id=req.session_id,
        verified_at=ts,
        method="button",
    )


__all__ = ["router"]
