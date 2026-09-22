"""FastAPI dependencies.

Centralised so routers can request what they need without caring
about lifetimes. The `get_state()` dependency is the only one that
hits the singleton; everything else is cheap.
"""

from __future__ import annotations

from fastapi import Request

from .config import settings
from .state import AppState

_node_backend = None


def get_state(request: Request) -> AppState:
    """Return the process-wide AppState stored on app.state."""
    return request.app.state.app_state


def get_passport_backend(request: Request):
    """Return the configured passport backend.

    We resolve on every call rather than caching on app.state so a
    test can monkey-patch the backend via `app.dependency_overrides`.
    """
    if settings.passport_backend in {"local", "testnet"}:
        global _node_backend
        if _node_backend is None:
            from .chain_bridge import ChainBridge
            from .passport_backends.node import NodePassportBackend
            mode = "live" if settings.passport_backend == "testnet" else "local"
            _node_backend = NodePassportBackend(ChainBridge(mode=mode), label=settings.passport_backend)
        return _node_backend
    from .passport_backends.mock import MockPassportBackend
    return MockPassportBackend()


async def close_passport_backend():
    global _node_backend
    if _node_backend is not None:
        await _node_backend.close()
        _node_backend = None


def get_trip_seconds() -> int:
    return settings.trip_seconds


def get_redline_judge():
    from agent.follow_agent.kiln_client import HttpKilnClient, build_kiln_client
    from agent.redline_agent import HynixMockClassifier, KilnEventClassifier, RedLineJudge

    client = build_kiln_client()
    classifier = KilnEventClassifier(client) if isinstance(client, HttpKilnClient) else HynixMockClassifier()
    return RedLineJudge(classifier=classifier)


__all__ = ["get_state", "get_passport_backend", "get_trip_seconds", "get_redline_judge", "close_passport_backend"]
