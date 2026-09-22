"""Single owner of the passport authorization lifecycle."""

from __future__ import annotations

import hashlib
import json
import asyncio
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from agent.follow_agent.spec_schema import CopyTradingSpec

from .intent import HASH_VERSION, IntentError, canonicalize_intent, is_expired
from .audit import make_event
from .state import PassportRecord, AppState


class AuthorizationError(ValueError):
    pass


def _fingerprint(op: str, payload: dict[str, Any]) -> str:
    raw = json.dumps({"op": op, "payload": payload}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode()).hexdigest()


class AuthorizationService:
    def __init__(self) -> None:
        self._revoke_locks: dict[str, asyncio.Lock] = {}

    async def _idempotent(self, state: AppState, request_id: str, op: str, payload: dict[str, Any]):
        fp = _fingerprint(op, payload)
        existing = state.requests.get(request_id)
        if existing and existing["fingerprint"] != fp:
            raise AuthorizationError("request_id was already used with a different payload")
        return existing, fp

    async def prepare(self, state: AppState, spec: dict[str, Any], request_id: str) -> PassportRecord:
        try:
            model = CopyTradingSpec.model_validate(spec)
            normalized = model.model_dump(mode="json")
            normalized["faceVerified"] = False
            canonical, digest, _, _, expiry = canonicalize_intent(normalized)
        except Exception as exc:
            raise AuthorizationError(str(exc)) from exc
        async with state._lock:
            existing, fp = await self._idempotent(state, request_id, "prepare", {"spec_hash": digest})
            if existing:
                return state.passports[existing["passport_id"]]
            pid = str(uuid4())
            rec = PassportRecord(
                passport_id=pid,
                spec_hash=digest,
                spec=normalized,
                leader_id=normalized["leaderId"],
                notional_usd=float(normalized["notionalUsd"]),
                fee_bps=25,
                expiry=datetime.fromtimestamp(expiry, timezone.utc).isoformat(),
                face_verified=False,
                status="prepared",
                tx_mint_hash=None,
                run_id=state.run_id,
                canonical_intent=canonical,
                hash_version=HASH_VERSION,
            )
            state.passports[pid] = rec
            state.requests[request_id] = {"fingerprint": fp, "passport_id": pid}
            if state.evidence:
                state.evidence.write_json("intent.json", {"run_id": state.run_id, "passport_id": pid, "spec": normalized, "canonical_intent": canonical, "spec_hash": digest, "hash_version": HASH_VERSION})
            state._save_locked()
            return rec

    async def confirm(self, state: AppState, passport_id: str, spec_hash: str, request_id: str) -> PassportRecord:
        async with state._lock:
            rec = state.passports.get(passport_id)
            if rec is None:
                raise KeyError(passport_id)
            existing, fp = await self._idempotent(
                state, request_id, "confirm", {"passport_id": passport_id, "spec_hash": spec_hash}
            )
            if existing:
                return rec
            if rec.spec_hash != spec_hash:
                raise AuthorizationError("confirmation hash does not match the frozen intent")
            if rec.stop_requested:
                raise AuthorizationError("authorization has already been stopped")
            rec.confirmed_spec_hash = spec_hash
            rec.confirmed_at = datetime.now(timezone.utc).isoformat()
            rec.confirmation_kind = "manual"
            rec.authorization_status = "confirmed"
            rec.status = "confirmed"
            state.requests[request_id] = {"fingerprint": fp, "passport_id": passport_id}
            state._save_locked()
            return rec

    async def mint(self, state: AppState, passport_id: str, request_id: str, backend) -> PassportRecord:
        revoke_after_mint = False
        async with state._lock:
            rec = state.passports.get(passport_id)
            if rec is None:
                raise KeyError(passport_id)
            existing, fp = await self._idempotent(
                state, request_id, "mint", {"passport_id": passport_id}
            )
            if existing:
                return rec
            if rec.authorization_status == "authorized" and rec.confirmed_spec_hash == rec.spec_hash:
                state.requests[request_id] = {"fingerprint": fp, "passport_id": passport_id}
                state._save_locked()
                return rec
            if rec.confirmed_spec_hash != rec.spec_hash or rec.authorization_status != "confirmed":
                raise AuthorizationError("passport must be confirmed before mint")
            if rec.stop_requested or is_expired(rec.expiry):
                raise AuthorizationError("authorization is stopped or expired")
            state.requests[request_id] = {"fingerprint": fp, "passport_id": passport_id}
            if backend.label == "mock":
                rec.authorization_status = "authorized"
                rec.status = "authorized"
                rec.simulation_id = f"sim-{uuid4()}"
                rec.backend_label = "mock"
                rec.tx_mint_hash = None
                state._save_locked()
                return rec
            if not hasattr(backend, "mint_record"):
                raise AuthorizationError("configured backend cannot mint a chain passport")
            rec.authorization_status = "mint_pending"
            rec.status = "mint_pending"
            rec.backend_label = backend.label
            state._save_locked()
        try:
            result = await backend.mint_record(rec)
        except Exception as exc:
            async with state._lock:
                rec.authorization_status = "uncertain"
                rec.status = "uncertain"
                state._save_locked()
            raise AuthorizationError(f"chain mint outcome uncertain: {exc}") from exc
        async with state._lock:
            if result.get("status") != "confirmed" or result.get("receipt", {}).get("status") != 1:
                rec.authorization_status = "uncertain"
                rec.status = "uncertain"
                state._save_locked()
                raise AuthorizationError("chain mint did not return a confirmed successful receipt")
            chain_state = result["state"]
            if chain_state["spec_hash"].lower() != rec.spec_hash.lower():
                rec.authorization_status = "uncertain"
                state._save_locked()
                raise AuthorizationError("chain readback hash mismatch")
            rec.tx_mint_hash = result["tx_hash"]
            rec.chain_passport_id = result["chain_passport_id"]
            rec.chain_id = result["chain_id"]
            rec.contract_address = result["contract_address"]
            rec.authorization_status = "authorized"
            rec.status = "authorized"
            if rec.stop_requested:
                rec.authorization_status = "revoke_pending"
                rec.status = "revoke_pending"
                revoke_after_mint = True
            if state.evidence:
                state.evidence.append("chain.jsonl", {"run_id": state.run_id, "action": "mint_confirmed", "passport_id": rec.passport_id, **result})
            state._save_locked()
        if revoke_after_mint:
            rec, _, _ = await self.revoke(state, passport_id, backend, "STOP_DURING_MINT")
        return rec

    async def revoke(
        self,
        state: AppState,
        passport_id: str,
        backend,
        reason_code: str,
    ) -> tuple[PassportRecord, str, dict[str, Any] | None]:
        lock = self._revoke_locks.setdefault(passport_id, asyncio.Lock())
        async with lock:
            return await self._revoke_once(state, passport_id, backend, reason_code)

    async def _revoke_once(
        self,
        state: AppState,
        passport_id: str,
        backend,
        reason_code: str,
    ) -> tuple[PassportRecord, str, dict[str, Any] | None]:
        """Revoke one authorization and persist evidence exactly once.

        Engine, RedLine and passport routes all use this method so a stopped
        chain-backed passport cannot be reported as revoked before its receipt
        and readback have been verified.
        """
        async with state._lock:
            rec = state.passports.get(passport_id)
            if rec is None:
                raise KeyError(passport_id)
            previous = rec.authorization_status
            if previous == "revoked":
                return rec, previous, None
            rec.stop_requested = True
            rec.engine_running = False
            if rec.engine_status not in {"stopped", "stop_failed"}:
                rec.engine_status = "stopped"
            rec.stop_reason = rec.stop_reason or reason_code
            if backend.label == "mock":
                rec.authorization_status = "revoked"
                rec.status = "revoked"
                state._save_locked()
            else:
                if not rec.chain_passport_id or not hasattr(backend, "revoke_record"):
                    raise AuthorizationError("chain-backed passport cannot be revoked by the configured backend")
                rec.authorization_status = "revoke_pending"
                rec.status = "revoke_pending"
                state._save_locked()

        if backend.label == "mock":
            state.append_event(make_event(
                "revoke_simulated", passport_id,
                {"previous_status": previous, "reason_code": reason_code},
            ))
            return rec, previous, None

        try:
            result = await backend.revoke_record(rec, reason_code)
        except Exception as exc:
            async with state._lock:
                rec.authorization_status = "uncertain"
                rec.status = "uncertain"
                state._save_locked()
            state.append_event(make_event(
                "revoke_uncertain", passport_id,
                {"previous_status": previous, "reason_code": reason_code, "error": str(exc)},
            ))
            raise AuthorizationError(f"revoke outcome uncertain: {exc}") from exc

        receipt = result.get("receipt", {})
        chain_state = result.get("state", {})
        if result.get("already_revoked") is True and chain_state.get("status") == "revoked":
            async with state._lock:
                rec.authorization_status = "revoked"
                rec.status = "revoked"
                state._save_locked()
            if state.evidence:
                state.evidence.append("chain.jsonl", {
                    "run_id": state.run_id,
                    "action": "revoke_readback",
                    "passport_id": passport_id,
                    "reason_code": reason_code,
                    **result,
                })
            state.append_event(make_event(
                "revoke_readback", passport_id,
                {"previous_status": previous, "reason_code": reason_code},
            ))
            return rec, previous, result
        if (
            result.get("status") != "confirmed"
            or receipt.get("status") != 1
            or chain_state.get("status") != "revoked"
        ):
            async with state._lock:
                rec.authorization_status = "uncertain"
                rec.status = "uncertain"
                state._save_locked()
            state.append_event(make_event(
                "revoke_uncertain", passport_id,
                {"previous_status": previous, "reason_code": reason_code, "error": "receipt or readback mismatch"},
            ))
            raise AuthorizationError("chain revoke did not return a confirmed revoked readback")

        async with state._lock:
            rec.tx_revoke_hash = result["tx_hash"]
            rec.authorization_status = "revoked"
            rec.status = "revoked"
            state._save_locked()
        if state.evidence:
            state.evidence.append("chain.jsonl", {
                "run_id": state.run_id,
                "action": "revoke_confirmed",
                "passport_id": passport_id,
                "reason_code": reason_code,
                **result,
            })
        state.append_event(make_event(
            "revoke_confirmed", passport_id,
            {"tx_hash": rec.tx_revoke_hash, "previous_status": previous, "reason_code": reason_code},
        ))
        return rec, previous, result


authorization_service = AuthorizationService()

__all__ = ["AuthorizationError", "AuthorizationService", "authorization_service"]
