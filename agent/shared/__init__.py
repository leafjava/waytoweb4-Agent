"""Shared types and helpers used by both agents.

Importing from this package should be cheap and side-effect free; the
submodules are small and independent so callers can pull only what they
need.
"""

from .energy import NPU_POWER_W, assumption_note, estimate_wh
from .exceptions import (
    AgentError,
    KilnUnavailableError,
    RedLineRefusedError,
    SpecValidationError,
    UnauthorizedOverrideError,
)
from .token_logger import (
    ALLOWED_FLOWS,
    TokenLogger,
    get_default_logger,
    reset_default_logger,
)
from .types import PassportRef, ReasonCode

__all__ = [
    "NPU_POWER_W",
    "assumption_note",
    "estimate_wh",
    "AgentError",
    "KilnUnavailableError",
    "RedLineRefusedError",
    "SpecValidationError",
    "UnauthorizedOverrideError",
    "ALLOWED_FLOWS",
    "TokenLogger",
    "get_default_logger",
    "reset_default_logger",
    "PassportRef",
    "ReasonCode",
]