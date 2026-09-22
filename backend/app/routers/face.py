"""Face gate router.

The demo's "face verification" is a button. We still go through a
backend endpoint because:
    1. `faceVerified` lives on the Spec and is server-controlled.
    2. The Spec can only flip to face-verified AFTER mint; mint
       rejects any Spec that already has `faceVerified=true`.
    3. The audit log records when the gate fired.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from ..audit import make_event
from ..deps import get_state
from ..errors import conflict, not_found
from ..models import FaceVerifyRequest, FaceVerifyResponse
from ..state import PASS_PENDING_FACE, AppState


router = APIRouter(prefix="/api/face", tags=["face"])


@router.post("/verify", response_model=FaceVerifyResponse)
async def verify_face(
    req: FaceVerifyRequest,
    state: AppState = Depends(get_state),
):
    rec = state.passports.get(req.passport_id)
    if rec is None:
        raise not_found(f"passport {req.passport_id} not found")
    if rec.status != PASS_PENDING_FACE:
        raise conflict(
            f"passport {req.passport_id} is in status {rec.status!r}; "
            "face verify only valid from pending_face"
        )

    # Simulate the human-in-the-loop face match.
    await asyncio.sleep(0.5)

    rec.face_verified = True
    state.upsert_passport(rec)

    ts = datetime.now(timezone.utc).isoformat()
    state.append_event(make_event(
        "face_verify", rec.passport_id, {"verified_at": ts},
    ))

    return FaceVerifyResponse(ok=True, passport_id=rec.passport_id, verified_at=ts)


__all__ = ["router"]