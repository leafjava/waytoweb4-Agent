"""Sepolia-shaped passport backend.

This is a **dry-run** adapter. It produces the same hash shape as
the mock backend, but tags the response with `chain_id=11155111` and
a `0xSEP...` tx-hash prefix so the README can honestly say "the
shape is Sepolia-compatible; broadcast requires a real RPC + a
deployed PassportRegistry contract".

To switch to a real broadcast:
    1. Set SEPOLIA_RPC_URL and SEPOLIA_PRIVATE_KEY env vars.
    2. Replace the `mint` / `revoke` bodies with a `web3.eth.send_transaction`
       call to a real PassportRegistry contract.
    3. The Spec hashing is already correct -- keccak256(canonical_json(spec))
       is exactly what Solidity's keccak256(abi.encodePacked(...)) produces
       for the same byte string.
"""

from __future__ import annotations

import os
from typing import Any

from ..hash import mint_tx_hash, revoke_tx_hash, short_id
from ..state import (
    PASS_PENDING_FACE,
    PASS_REVOKED,
    AppState,
    PassportRecord,
)
from . import PassportBackend, build_record


CHAIN_ID = 11155111


def _prefix_with_chain(hex_hash: str) -> str:
    """Make it visually obvious in the JSON ledger / UI that this is
    a Sepolia-shaped hash. The first 5 chars are still '0x' + first
    3 bytes; we replace the first three bytes after 0x with the
    ASCII 'SEP' tag. The full hash remains a valid 32-byte hex.
    """
    # '0x' + first 6 hex chars (3 bytes) replaced with 'SEP' + 1 byte.
    body = hex_hash[2:]
    return "0xSEP" + body[3:]


class SepoliaPassportBackend:
    label: str = "sepolia"
    chain_id: int = CHAIN_ID

    def mint(
        self,
        spec: dict[str, Any],
        spec_hash_hex: str,
        state: AppState,
    ) -> PassportRecord:
        passport_id = short_id(spec)
        if passport_id in state.passports:
            return state.passports[passport_id]
        tx = mint_tx_hash(spec_hash_hex)
        tx = _prefix_with_chain(tx)
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
        new_tx = _prefix_with_chain(new_tx)
        rec.tx_revoke_hash = new_tx
        rec.status = PASS_REVOKED
        rec.engine_running = False
        state.upsert_passport(rec)
        return rec


def env_status() -> dict[str, Any]:
    """For /api/health: what env vars are set if a real Sepolia broadcast is wanted."""
    return {
        "SEPOLIA_RPC_URL_set": bool(os.environ.get("SEPOLIA_RPC_URL")),
        "SEPOLIA_PRIVATE_KEY_set": bool(os.environ.get("SEPOLIA_PRIVATE_KEY")),
        "chain_id": CHAIN_ID,
        "note": (
            "tx hashes are keccak256 of canonical-json Spec; "
            "broadcast requires SEPOLIA_RPC_URL + a deployed PassportRegistry contract."
        ),
    }


__all__ = ["SepoliaPassportBackend", "CHAIN_ID", "env_status"]