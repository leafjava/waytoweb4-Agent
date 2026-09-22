"""FastAPI dependencies.

Centralised so routers can request what they need without caring
about lifetimes. The `get_state()` dependency is the only one that
hits the singleton; everything else is cheap.
"""

from __future__ import annotations

from fastapi import Request

from .config import settings
from .state import AppState


def get_state(request: Request) -> AppState:
    """Return the process-wide AppState stored on app.state."""
    return request.app.state.app_state


def get_passport_backend(request: Request):
    """Return the configured passport backend.

    We resolve on every call rather than caching on app.state so a
    test can monkey-patch the backend via `app.dependency_overrides`.
    """
    if settings.passport_backend == "sepolia":
        from .passport_backends.sepolia import SepoliaPassportBackend
        return SepoliaPassportBackend()
    from .passport_backends.mock import MockPassportBackend
    return MockPassportBackend()


def get_trip_seconds() -> int:
    return settings.trip_seconds


__all__ = ["get_state", "get_passport_backend", "get_trip_seconds"]