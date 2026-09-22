"""Spec router: clarify / emit / check.

The router is deliberately thin -- every security-critical validator
lives in the `agent` package. We call it, shape the JSON, return it.
"""

from __future__ import annotations

import asyncio

from agent.follow_agent import Clarifier as AgentClarifier
from agent.follow_agent import Emitter, build_kiln_client
from agent.follow_agent.clarifier import REQUIRED_FIELDS, _looks_like_answer
from agent.shared.exceptions import SpecValidationError
from fastapi import APIRouter, Depends, Request

from ..deps import get_state
from ..errors import map_agent_error, spec_error
from ..models import (
    CheckRequest,
    CheckResponse,
    ClarifyRequest,
    ClarifyResponse,
    EmitRequest,
    EmitResponse,
)
from ..state import AppState


router = APIRouter(prefix="/api/spec", tags=["spec"])


def _kiln():
    return build_kiln_client()


def _missing_fields(text: str) -> list[str]:
    return [f for f in REQUIRED_FIELDS if not _looks_like_answer(f, text)]


@router.post("/check", response_model=CheckResponse)
def spec_check(req: CheckRequest) -> CheckResponse:
    missing = _missing_fields(req.user_text)
    return CheckResponse(missing_fields=missing, ready=not missing)


@router.post("/clarify", response_model=ClarifyResponse)
def spec_clarify(req: ClarifyRequest, request: Request) -> ClarifyResponse:
    client = _kiln()
    clarifier = AgentClarifier(client)
    draft_id = req.draft_id or "draft-pending"
    q = clarifier.first_question(req.user_text)
    if not q.field:
        return ClarifyResponse(
            draft_id=draft_id,
            question=q.question,
            field="",
            attempt=q.attempt,
            missing_fields=[],
        )
    return ClarifyResponse(
        draft_id=draft_id,
        question=q.question,
        field=q.field,
        attempt=q.attempt,
        missing_fields=[q.field],
    )


@router.post("/emit", response_model=EmitResponse)
def spec_emit(req: EmitRequest) -> EmitResponse:
    client = _kiln()
    emitter = Emitter(client)
    emitter.add_user(req.user_text)
    try:
        spec = emitter.emit()
    except SpecValidationError as e:
        raise spec_error(str(e))
    except Exception as e:  # noqa: BLE001 -- translate to HTTP
        raise map_agent_error(e)
    payload = spec.model_dump(mode="json")
    # Force faceVerified off. Defence in depth.
    payload["faceVerified"] = False
    return EmitResponse(
        draft_id=req.draft_id or "draft-locked",
        spec=payload,
    )


__all__ = ["router"]