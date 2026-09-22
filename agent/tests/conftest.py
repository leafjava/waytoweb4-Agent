"""Shared pytest fixtures.

In particular, we make sure each test gets a fresh TokenLogger so
tests can't bleed buckets into each other.
"""

from __future__ import annotations

import pytest

from agent.shared.token_logger import TokenLogger, reset_default_logger


@pytest.fixture(autouse=True)
def _fresh_logger():
    """Reset the process-wide default logger before each test.

    This fixture is intentionally parameter-less; tests that need
    direct access to a logger should use the explicit `fresh_logger`
    fixture below. Returning a value from an autouse fixture is a
    known footgun (pytest will try to inject it into every test).
    """
    reset_default_logger()
    yield


@pytest.fixture
def fresh_logger() -> TokenLogger:
    """An explicit, isolated TokenLogger for tests that need it."""
    return TokenLogger()