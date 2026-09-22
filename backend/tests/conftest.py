"""Shared pytest fixtures for backend tests.

The big idea: each test gets its own `AppState` and its own FastAPI
client, both pointing at the same in-memory state. The persisted
JSON ledger is replaced with a tmp file per test.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from agent.shared.token_logger import TokenLogger, reset_default_logger

from backend.app.config import settings
from backend.app.engine import cancel_all
from backend.app.main import create_app
from backend.app.state import AppState


@pytest.fixture(autouse=True)
def _fresh_token_logger():
    reset_default_logger()
    yield
    reset_default_logger()


@pytest.fixture
def tmp_ledger(tmp_path, monkeypatch):
    """Replace the global ledger path with a temp file."""
    p = tmp_path / "passports.json"
    # settings is frozen; we mutate by replacing the underlying file
    # via a fresh AppState instead. The trick is to override the
    # `get_state` dependency.
    return p


@pytest.fixture
def app_and_state(tmp_ledger: Path):  # noqa: F821 -- Path not imported; fix below
    """Return (app, AppState) with a clean, isolated state per test.

    We re-create the AppState on app startup via the lifespan context;
    the dependency `get_state` returns whatever is on `app.state`.
    """
    import asyncio

    from backend.app import state as state_module

    # Patch default ledger path used by the lifespan. The cleanest
    # way is to monkeypatch the ledger_path argument by replacing
    # `settings` in the engine module's view. But settings is frozen,
    # so we instead just rely on the AppState we attach directly.
    app = create_app()

    # Build the state manually and inject; the lifespan will also
    # build its own, but our override below wins.
    fresh = AppState(ledger_path=tmp_ledger)
    app.state.app_state = fresh

    # Override the get_state dependency so even if the lifespan ran,
    # the test always sees our fresh state.
    from backend.app.deps import get_state as _get_state

    def _state_override():
        return fresh

    app.dependency_overrides[_get_state] = _state_override
    yield app, fresh

    # Cleanup: cancel engine tasks between tests.
    asyncio.get_event_loop().run_until_complete(cancel_all())
    app.dependency_overrides.clear()


@pytest.fixture
def client(app_and_state):
    app, _state = app_and_state
    with TestClient(app) as c:
        yield c


@pytest.fixture
def fresh_state(app_and_state):
    _app, state = app_and_state
    return state
