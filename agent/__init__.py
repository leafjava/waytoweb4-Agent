"""waytoweb4-agent: Follow Agent + RedLine Agent.

This top-level package exposes the two agents that participate in the
copy-trading authorization flow. The follow agent turns natural-language
intent into a locked CopyTradingSpec; the redline agent is the
independent kill switch that can stop the engine and revoke the on-chain
passport without ever looking at PnL.
"""

from .follow_agent.spec_schema import CopyTradingSpec
from .redline_agent.schema import (
    RedLineVerdict,
    RedLineLevel,
    RedLineAction,
    ReasonCode,
)
from .shared.types import PassportRef

__all__ = [
    "CopyTradingSpec",
    "RedLineVerdict",
    "RedLineLevel",
    "RedLineAction",
    "ReasonCode",
    "PassportRef",
]