"""Exceptions raised by the agents.

These are deliberately a small set -- a few well-named errors are far
easier for the backend to translate into user-facing copy than a deep
hierarchy.
"""

from __future__ import annotations


class AgentError(Exception):
    """Base class for all agent errors."""


class SpecValidationError(AgentError):
    """A Spec (or a candidate Spec) violated PRD-defined invariants.

    Examples: mode != 'copy', paper=False, maxLossUsd > notionalUsd,
    expiry in the past, or any extra field not in the schema. The
    backend should translate these into 422-style user-facing errors --
    they are not bugs, they are guard rails doing their job.
    """


class UnauthorizedOverrideError(AgentError):
    """A caller tried to override a hard guard that the agent owns.

    Examples: trying to set model_may_override_hard_limit=True, trying
    to set maxLossUsd from a free-text LLM output without going through
    the locked Spec path, or trying to disable RedLine from the spec.
    """


class KilnUnavailableError(AgentError):
    """The Kiln API call failed and no mock fallback was available."""


class RedLineRefusedError(AgentError):
    """RedLine refused to act on a request, typically because the call
    bypassed the hard gate. The backend should treat this as a 403.
    """