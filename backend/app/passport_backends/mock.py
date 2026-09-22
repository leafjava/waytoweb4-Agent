"""Mock passport backend.

Writes to the in-process state + the JSON ledger file. The `tx_hash`
is a real keccak256 of the canonical-JSON Spec -- judges see the
same hex format EVM would produce, but no chain is touched.

This is what we run on the demo machine and in unit tests.
"""

from __future__ import annotations

from typing import Any

from ..hash import mint_tx_hash, revoke_tx_hash, short_id
from ..state import (
    PASS_PENDING_FACE,
    PASS_REVOKED,
    AppState,
    PassportRecord,
)
from . import PassportBackend, build_record


class MockPassportBackend:
    label: str = "mock"

    def mint(
        self,
        spec: dict[str, Any],
        spec_hash_hex: str,
        state: AppState,
    ) -> PassportRecord:
        passport_id = short_id(spec)
        if passport_id in state.passports:
            # Re-mint the same spec -> return the existing record.
            return state.passports[passport_id]
        tx = mint_tx_hash(spec_hash_hex)
        rec = build_record(
            spec=spec,
            spec_hash_hex=spec_hash_hex,
            passport_id=passport_id,
            tx_mint_hash=tx,
            backend_label=self.label,
        )
        rec.status = PASS_PENDING_FACE
        state.upsert_passport(rec)
        return rec

    def revoke(self, passport_id: str, state: AppState) -> PassportRecord:
        rec = state.passports.get(passport_id)
        if rec is None:
            raise KeyError(passport_id)
        if rec.status == PASS_REVOKED:
            raise ValueError(f"passport {passport_id} already revoked")
        prev_tx = rec.tx_mint_hash
        new_tx = revoke_tx_hash(passport_id, prev_tx)
        rec.tx_revoke_hash = new_tx
        rec.status = PASS_REVOKED
        rec.engine_running = False
        state.upsert_passport(rec)
        return rec


__all__ = ["MockPassportBackend"]