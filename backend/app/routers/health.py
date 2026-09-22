"""Health + smoke router."""

from __future__ import annotations

from agent.follow_agent.kiln_client import (
    HttpKilnClient,
    KILN_API_KEY_ENV,
)
from fastapi import APIRouter

from ..config import settings
from ..models import HealthResponse


router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    import os
    has_key = bool(os.environ.get(KILN_API_KEY_ENV))
    kiln_label = "http" if has_key else "mock"
    return HealthResponse(ok=True, kiln=kiln_label, passport_backend=settings.passport_backend)


__all__ = ["router"]