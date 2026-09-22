"""Thin wrapper around `agent.shared.token_logger`.

The frontend needs the rendered markdown table so it can paste it
straight into the README. The backend keeps no extra state of its
own -- the global TokenLogger is the single source of truth.
"""

from __future__ import annotations

from agent.shared.token_logger import get_default_logger


def render_report() -> str:
    """Return the PRD §9 markdown table as a string."""
    return get_default_logger().report()


__all__ = ["render_report"]