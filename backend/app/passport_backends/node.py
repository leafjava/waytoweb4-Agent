"""Local-EVM Node bridge backend used for offline integration tests."""

from __future__ import annotations

from ..chain_bridge import ChainBridge


class NodePassportBackend:
    label = "local"

    def __init__(self, bridge: ChainBridge | None = None):
        self.bridge = bridge or ChainBridge()

    async def mint_record(self, rec):
        return await self.bridge.call("mint", rec.run_id, {
            "canonical_intent": rec.canonical_intent,
            "spec_hash": rec.spec_hash,
            "confirmed_spec_hash": rec.confirmed_spec_hash,
        })

    async def revoke_record(self, rec, reason_code: str):
        return await self.bridge.call("revoke", rec.run_id, {
            "chain_passport_id": rec.chain_passport_id, "reason_code": reason_code,
        })

    async def close(self):
        await self.bridge.close()


__all__ = ["NodePassportBackend"]
