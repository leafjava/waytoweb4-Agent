"""In-process application state.

A single `AppState` instance is created at app startup (see
`main.py`) and lives for the life of the process. Mutations are
serialised by a single asyncio lock to keep the audit log
self-consistent under concurrent requests.

Persisted artifacts:
    * `passports.json` -- the on-chain-shaped ledger (created on
      first mint if missing).
"""

from __future__ import annotations

import asyncio
import json
import os
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .audit import AuditEvent, make_event


# Statuses a passport can be in. Keep these strings stable; they end
# up in the README and the on-chain event log.
PASS_PENDING_FACE = "pending_face"
PASS_ACTIVE = "active"
PASS_STOPPED = "stopped"
PASS_REVOKED = "revoked"


@dataclass
class PassportRecord:
    """Everything the backend needs to remember about one passport."""

    passport_id: str
    spec_hash: str
    spec: dict[str, Any]
    leader_id: str
    notional_usd: float
    fee_bps: int
    expiry: str
    face_verified: bool
    status: str
    tx_mint_hash: str | None
    tx_revoke_hash: str | None = None
    engine_running: bool = False
    engine_started_at: str | None = None
    drawdown_usd: float = 0.0
    trip_seconds: int = 60
    last_verdict: dict[str, Any] | None = None
    backend_label: str = "mock"
    run_id: str = ""
    chain_passport_id: str | None = None
    chain_id: int | None = None
    contract_address: str | None = None
    hash_version: str = "intent-keccak-v1"
    canonical_intent: str = ""
    confirmed_spec_hash: str | None = None
    confirmed_at: str | None = None
    confirmation_kind: str | None = None
    face_verification_mode: str = "mock"
    authorization_status: str = "prepared"
    engine_status: str = "idle"
    stop_requested: bool = False
    simulation_id: str | None = None
    stop_reason: str | None = None

    def to_public_dict(self) -> dict[str, Any]:
        """Shape returned to the frontend. Stable field names so the
        frontend doesn't need to track internal renames."""
        return {
            "passport_id": self.passport_id,
            "spec_hash": self.spec_hash,
            "leader_id": self.leader_id,
            "notional_usd": self.notional_usd,
            "fee_bps": self.fee_bps,
            "expiry": self.expiry,
            "face_verified": self.face_verified,
            "status": self.status,
            "tx_mint_hash": self.tx_mint_hash,
            "tx_revoke_hash": self.tx_revoke_hash,
            "engine_running": self.engine_running,
            "engine_started_at": self.engine_started_at,
            "drawdown_usd": self.drawdown_usd,
            "max_loss_usd": float(self.spec.get("maxLossUsd", 0.0)),
            "trip_seconds": self.trip_seconds,
            "last_verdict": self.last_verdict,
            "backend": self.backend_label,
            "run_id": self.run_id,
            "chain_passport_id": self.chain_passport_id,
            "chain_id": self.chain_id,
            "contract_address": self.contract_address,
            "hash_version": self.hash_version,
            "confirmed_spec_hash": self.confirmed_spec_hash,
            "confirmed_at": self.confirmed_at,
            "confirmation_kind": self.confirmation_kind,
            "face_verification_mode": self.face_verification_mode,
            "authorization_status": self.authorization_status,
            "engine_status": self.engine_status,
            "stop_requested": self.stop_requested,
            "simulation_id": self.simulation_id,
            "stop_reason": self.stop_reason,
        }


@dataclass
class AppState:
    """Singleton state holder. One instance per process.

    Concurrency model: a single `asyncio.Lock` guards all mutations.
    Reads (e.g. `GET /api/state`) acquire the lock briefly to take a
    shallow copy. Tests reset state with `reset()`.
    """

    ledger_path: Path
    passports: dict[str, PassportRecord] = field(default_factory=dict)
    events: list[AuditEvent] = field(default_factory=list)
    requests: dict[str, dict[str, Any]] = field(default_factory=dict)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    # ---- persistence ------------------------------------------------------

    def load(self) -> None:
        """Load passports from the JSON ledger. Missing file is OK."""
        if not self.ledger_path.exists():
            return
        raw = json.loads(self.ledger_path.read_text(encoding="utf-8"))
        for pid, p in raw.get("passports", {}).items():
            self.passports[pid] = PassportRecord(**p)
        self.requests = raw.get("requests", {})

    def _save_locked(self) -> None:
        """Write passports to the JSON ledger. Caller must hold the lock."""
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        body = {
            "passports": {
                pid: _dataclass_to_jsonable(rec) for pid, rec in self.passports.items()
            },
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "requests": self.requests,
        }
        content = json.dumps(body, indent=2, ensure_ascii=False)
        fd, tmp_name = tempfile.mkstemp(prefix=self.ledger_path.name, dir=self.ledger_path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp_name, self.ledger_path)
        finally:
            if os.path.exists(tmp_name):
                os.unlink(tmp_name)

    # ---- mutation helpers (caller still holds the lock) -------------------

    def upsert_passport(self, rec: PassportRecord) -> None:
        self.passports[rec.passport_id] = rec
        self._save_locked()

    def append_event(self, ev: AuditEvent) -> None:
        self.events.append(ev)
        # Cap the in-memory log so it doesn't grow unbounded.
        if len(self.events) > 500:
            self.events = self.events[-500:]

    # ---- snapshot for read endpoints --------------------------------------

    def snapshot(self) -> dict[str, Any]:
        """Return a JSON-serialisable snapshot of the world.

        The lock is *not* held here -- callers acquire it before
        calling. This means snapshots are not perfectly consistent
        if a mutator runs concurrently, but for the demo this is fine
        and avoids holding the lock across serialisation.
        """
        return {
            "passports": {
                pid: rec.to_public_dict()
                for pid, rec in self.passports.items()
            },
            "events": [ev.to_dict() for ev in self.events[-50:]],
            "saved_at": datetime.now(timezone.utc).isoformat(),
        }

    # ---- demo / reset -----------------------------------------------------

    async def reset(self) -> None:
        """Wipe in-memory state + delete the ledger.

        Does NOT reset the global TokenLogger -- multiple runs should
        accumulate into the same totals table (per PRD §9 we want
        one table per README, not one per run).
        """
        async with self._lock:
            self.passports.clear()
            self.events.clear()
            self.requests.clear()
            if self.ledger_path.exists():
                self.ledger_path.unlink()
            self.append_event_unlocked(make_event("demo_reset", None, {}))

    def append_event_unlocked(self, ev: AuditEvent) -> None:
        """Append an event without acquiring the lock. Tests / callers
        that already hold the lock use this."""
        self.append_event(ev)


def _dataclass_to_jsonable(rec: PassportRecord) -> dict[str, Any]:
    """Serialize a PassportRecord. Excludes derived/public-only fields."""
    return {
        "passport_id": rec.passport_id,
        "spec_hash": rec.spec_hash,
        "spec": rec.spec,
        "leader_id": rec.leader_id,
        "notional_usd": rec.notional_usd,
        "fee_bps": rec.fee_bps,
        "expiry": rec.expiry,
        "face_verified": rec.face_verified,
        "status": rec.status,
        "tx_mint_hash": rec.tx_mint_hash,
        "tx_revoke_hash": rec.tx_revoke_hash,
        "engine_running": rec.engine_running,
        "engine_started_at": rec.engine_started_at,
        "drawdown_usd": rec.drawdown_usd,
        "trip_seconds": rec.trip_seconds,
        "last_verdict": rec.last_verdict,
        "backend_label": rec.backend_label,
        "run_id": rec.run_id,
        "chain_passport_id": rec.chain_passport_id,
        "chain_id": rec.chain_id,
        "contract_address": rec.contract_address,
        "hash_version": rec.hash_version,
        "canonical_intent": rec.canonical_intent,
        "confirmed_spec_hash": rec.confirmed_spec_hash,
        "confirmed_at": rec.confirmed_at,
        "confirmation_kind": rec.confirmation_kind,
        "face_verification_mode": rec.face_verification_mode,
        "authorization_status": rec.authorization_status,
        "engine_status": rec.engine_status,
        "stop_requested": rec.stop_requested,
        "simulation_id": rec.simulation_id,
        "stop_reason": rec.stop_reason,
    }


__all__ = [
    "AppState",
    "PassportRecord",
    "PASS_PENDING_FACE",
    "PASS_ACTIVE",
    "PASS_STOPPED",
    "PASS_REVOKED",
]
