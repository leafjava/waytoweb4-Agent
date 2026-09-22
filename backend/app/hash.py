"""Deterministic hashing helpers for Spec / Passport.

We use real `web3.keccak` so the hashes are the exact same bytes
EVM contracts would compute -- important so that a Sepolia-deployed
PassportRegistry can verify them without any re-hashing.
"""

from __future__ import annotations

from typing import Any

from web3 import Web3

from .spec_canon import canonical_json


def _to_hex(keccak_result) -> str:
    """`web3.keccak(...).hex()` strips the `0x` prefix in recent versions.
    Normalise to the conventional 0x-prefixed 32-byte hex string."""
    h = keccak_result.hex()
    if not h.startswith("0x"):
        h = "0x" + h
    return h


def spec_hash(spec: dict[str, Any]) -> str:
    """keccak256 of the canonical-JSON-encoded Spec.

    Returns a 0x-prefixed hex string (66 chars).
    """
    return _to_hex(Web3.keccak(text=canonical_json(spec)))


def short_id(spec: dict[str, Any]) -> str:
    """8-byte (16 hex char) short id used as `passport_id`.

    Deterministic from the Spec, so the same Spec always mints the
    same passport id, regardless of mint tx ordering.
    """
    full = spec_hash(spec)
    return "0x" + full[2:18]


def mint_tx_hash(spec_hash_hex: str) -> str:
    """keccak256('mint:' + spec_hash). The first 8 bytes become a
    visible short id, the full 32 bytes are stored as the tx hash."""
    return _to_hex(Web3.keccak(text=f"mint:{spec_hash_hex}"))


def revoke_tx_hash(passport_id: str, prev_tx_hash: str | None) -> str:
    """keccak256('revoke:' + passport_id + ':' + prev_tx_hash).

    Binding to the previous mint tx hash means a revoke tx can be
    audited as 'this passport, that mint, this revoke'.
    """
    return _to_hex(Web3.keccak(text=f"revoke:{passport_id}:{prev_tx_hash or ''}"))


__all__ = ["spec_hash", "short_id", "mint_tx_hash", "revoke_tx_hash"]