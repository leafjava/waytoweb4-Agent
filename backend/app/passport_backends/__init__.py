"""Passport backends: pluggable mint/revoke implementations.

The Protocol is intentionally tiny -- just `mint(spec, spec_hash)`
and `revoke(passport_id)`. Both backends write to disk-backed state
via the `AppState` they receive at construction time.
"""

from __future__ import annotations

from typing import Any, Protocol

from ..hash import mint_tx_hash, revoke_tx_hash, short_id
from ..state import (
    PASS_ACTIVE,
    PASS_PENDING_FACE,
    PASS_REVOKED,
    AppState,
    PassportRecord,
)


class PassportBackend(Protocol):
    """The minimal contract a passport backend must satisfy."""

    label: str  # surfaced to the frontend / README

    def mint(self, spec: dict[str, Any], spec_hash_hex: str, state: AppState) -> PassportRecord: ...

    def revoke(self, passport_id: str, state: AppState) -> PassportRecord: ...


def _fee_bps_for(notional_usd: float) -> int:
    """25 bps flat fee. Capped to keep the demo ledger readable."""
    return 25


def build_record(
    *,
    spec: dict[str, Any],
    spec_hash_hex: str,
    passport_id: str,
    tx_mint_hash: str,
    backend_label: str,
) -> PassportRecord:
    return PassportRecord(
        passport_id=passport_id,
        spec_hash=spec_hash_hex,
        spec=spec,
        leader_id=str(spec["leaderId"]),
        notional_usd=float(spec["notionalUsd"]),
        fee_bps=_fee_bps_for(float(spec["notionalUsd"])),
        expiry=str(spec["expiry"]),
        face_verified=False,
        status=PASS_PENDING_FACE,
        tx_mint_hash=tx_mint_hash,
        backend_label=backend_label,
    )


__all__ = [
    "PassportBackend",
    "build_record",
    "mint_tx_hash",
    "revoke_tx_hash",
    "short_id",
    "PASS_ACTIVE",
    "PASS_PENDING_FACE",
    "PASS_REVOKED",
]