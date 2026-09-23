"""Map agent exceptions to HTTP status codes.

Centralised so every router stays small. The mapping is small and
deliberate -- anything new should be discussed, not silently added.
"""

from __future__ import annotations

from fastapi import HTTPException, status

from agent.shared.exceptions import (
    KilnUnavailableError,
    RedLineRefusedError,
    SpecValidationError,
    UnauthorizedOverrideError,
)


def spec_error(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)


def unauthorized(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


def not_found(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


def conflict(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)


def coded_conflict(code: str, message: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail={"code": code, "message": message},
    )


def map_agent_error(exc: Exception) -> HTTPException:
    """Best-effort mapping for the agent's exception hierarchy."""
    if isinstance(exc, SpecValidationError):
        return spec_error(str(exc))
    if isinstance(exc, UnauthorizedOverrideError):
        return unauthorized(str(exc))
    if isinstance(exc, RedLineRefusedError):
        return unauthorized(str(exc))
    if isinstance(exc, KilnUnavailableError):
        return HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


__all__ = [
    "spec_error",
    "unauthorized",
    "not_found",
    "conflict",
    "coded_conflict",
    "map_agent_error",
]
