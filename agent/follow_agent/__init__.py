"""Follow Agent: turn natural language into a locked copy-trading Spec.

The follow agent is the *only* path by which a copy-trading intent
reaches the rest of the system. It has two responsibilities:

  1. Drive a short clarifying conversation until the user has named a
     leader, a notional, a max-loss, and an expiry.
  2. Emit a JSON Spec that the backend then re-validates with
     `CopyTradingSpec` (extra fields forbidden, paper locked to True,
     etc.).

It does NOT touch the face gate, the waytoweb4 engine, or the
passport. Those are owned by the backend; this module just produces
the locked Spec.
"""

from .clarifier import Clarifier, ClarificationQuestion, Emitter
from .kiln_client import (
    ChatMessage,
    HttpKilnClient,
    KilnClient,
    KilnReply,
    MockKilnClient,
    build_kiln_client,
)
from .spec_schema import (
    DEMO_DEFAULT_EXPIRY,
    DEMO_DEFAULT_MAX_LOSS_USD,
    DEMO_DEFAULT_NOTIONAL_USD,
    MAX_NOTIONAL_USD,
    MIN_EXPIRY_DELTA,
    CopyTradingSpec,
    demo_default_spec,
)

__all__ = [
    "Clarifier",
    "ClarificationQuestion",
    "Emitter",
    "ChatMessage",
    "HttpKilnClient",
    "KilnClient",
    "KilnReply",
    "MockKilnClient",
    "build_kiln_client",
    "CopyTradingSpec",
    "demo_default_spec",
    "DEMO_DEFAULT_EXPIRY",
    "DEMO_DEFAULT_MAX_LOSS_USD",
    "DEMO_DEFAULT_NOTIONAL_USD",
    "MAX_NOTIONAL_USD",
    "MIN_EXPIRY_DELTA",
]