"""Provisional anti-corruption contract for the waytoweb4 execution adapter.

The external endpoint names are intentionally absent until the teammate receives
the official documentation. The paper subprocess consumes this same command so
the mock exercises the boundary that a future HTTP adapter must implement.
"""

from __future__ import annotations

import json
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from .state import PassportRecord


class ExecutionStartCommand(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    protocol_version: Literal[1] = 1
    request_id: str = Field(min_length=1, max_length=128)
    run_id: str = Field(min_length=1, max_length=128)
    passport_id: str = Field(min_length=1, max_length=128)
    spec_hash: str = Field(pattern=r"^0x[0-9a-fA-F]{64}$")
    leader_id: str = Field(min_length=1, max_length=64)
    notional_cents: int = Field(gt=0)
    max_loss_cents: int = Field(gt=0)
    expiry: str
    paper: Literal[True] = True
    policy_path: str
    lease_s: float = Field(gt=0, le=30)


def build_start_command(
    rec: PassportRecord,
    policy_path: str,
    lease_s: float = 3.0,
) -> ExecutionStartCommand:
    canonical = json.loads(rec.canonical_intent)
    if rec.confirmed_spec_hash != rec.spec_hash or rec.authorization_status != "authorized":
        raise ValueError("execution requires a hash-bound authorized passport")
    return ExecutionStartCommand(
        request_id=str(uuid4()),
        run_id=rec.run_id,
        passport_id=rec.passport_id,
        spec_hash=rec.spec_hash,
        leader_id=canonical["leaderId"],
        notional_cents=int(canonical["notionalCents"]),
        max_loss_cents=int(canonical["maxLossCents"]),
        expiry=rec.expiry,
        policy_path=policy_path,
        lease_s=lease_s,
    )


__all__ = ["ExecutionStartCommand", "build_start_command"]
