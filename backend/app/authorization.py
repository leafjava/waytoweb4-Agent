"""Single owner of the passport authorization lifecycle."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from agent.follow_agent.spec_schema import CopyTradingSpec

from .intent import HASH_VERSION, IntentError, canonicalize_intent, is_expired
from .state import PassportRecord, AppState


class AuthorizationError(ValueError):
    pass


def _fingerprint(op: str, payload: dict[str, Any]) -> str:
    raw = json.dumps({"op": op, "payload": payload}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode()).hexdigest()


class AuthorizationService:
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
                run_id=str(uuid4()),
                canonical_intent=canonical,
                hash_version=HASH_VERSION,
            )
            state.passports[pid] = rec
            state.requests[request_id] = {"fingerprint": fp, "passport_id": pid}
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
            if backend.label != "local":
                raise AuthorizationError("public-chain transport is not configured")
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
            state._save_locked()
            return rec


authorization_service = AuthorizationService()

__all__ = ["AuthorizationError", "AuthorizationService", "authorization_service"]
