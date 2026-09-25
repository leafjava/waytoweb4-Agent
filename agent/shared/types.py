"""Shared types used by both the follow agent and the redline agent."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class ReasonCode(str, Enum):
    """Closed-set reason codes emitted by RedLine.

    These strings are part of the application evidence contract and
    third-party auditors rely on them being stable. Never invent a new code in
    flight -- add it here and bump a versioned event log instead.
    """

    DD_LIMIT = "DD_LIMIT"            # drawdown >= spec.maxLossUsd -> TRIP
    CB_LIKE = "CB_LIKE"              # circuit-breaker-grade index/sector shock
    LEV_ETF_AMP = "LEV_ETF_AMP"      # 2x / leveraged product amplification
    LIQ_CASCADE = "LIQ_CASCADE"      # liquidation cascade
    GAP_ORACLE = "GAP_ORACLE"        # thin liquidity / pre-market gap
    HUMAN_OVERRIDE = "HUMAN_OVERRIDE"  # human kill-switch override


@dataclass(frozen=True)
class PassportRef:
    """A reference to a minted on-chain Strategy Passport.

    The passport is minted by the backend after explicit human approval. The
    agents themselves never mint -- they only consume the reference to
    label their decisions and (in the case of RedLine) to issue a revoke
    request.
    """

    passport_id: str
    spec_hash: str
    leader_id: str
    notional_usd: float
    expiry: datetime

    def is_expired(self, now: Optional[datetime] = None) -> bool:
        ts = now or datetime.utcnow()
        return ts >= self.expiry
