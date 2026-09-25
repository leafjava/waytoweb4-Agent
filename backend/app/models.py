"""API DTOs.

The wire format is deliberately separate from `CopyTradingSpec` so
we can:
    * accept a dict from the LLM (re-validated server-side)
    * add request/response-only fields without polluting the Spec
    * keep the public JSON contract versionable

`SpecPayload` is `dict[str, Any]` rather than a typed model so we
can re-validate it via the agent's `CopyTradingSpec.model_validate`
without a layer of translation.
"""

from __future__ import annotations

from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class ClarifyRequest(BaseModel):
    user_text: str = Field(min_length=1, max_length=4096)
    draft_id: str | None = Field(default=None, min_length=1, max_length=128)


class ClarifyResponse(BaseModel):
    draft_id: str
    question: str
    field: str
    attempt: int
    missing_fields: list[str]
    flow: str = "clarify"


class CheckRequest(BaseModel):
    user_text: str = Field(min_length=1, max_length=4096)


class CheckResponse(BaseModel):
    missing_fields: list[str]
    ready: bool


class EmitRequest(BaseModel):
    user_text: str = Field(min_length=1, max_length=4096)
    draft_id: str | None = Field(default=None, min_length=1, max_length=128)


class EmitResponse(BaseModel):
    draft_id: str
    spec: dict[str, Any]
    flow: str = "spec_emit"


class FaceVerifyRequest(BaseModel):
    passport_id: str = Field(min_length=1, max_length=128)
    method: Literal["button"]
    session_id: UUID


class FaceVerifyResponse(BaseModel):
    ok: bool
    passport_id: str
    session_id: UUID
    verified_at: str
    method: Literal["button"]


class PrepareRequest(BaseModel):
    spec: dict[str, Any]
    request_id: str = Field(min_length=1, max_length=128)


class ConfirmRequest(BaseModel):
    passport_id: str
    spec_hash: str
    request_id: str = Field(min_length=1, max_length=128)


class MintRequest(BaseModel):
    passport_id: str
    request_id: str = Field(min_length=1, max_length=128)


class MintResponse(BaseModel):
    passport_id: str
    spec_hash: str
    tx_hash: str | None
    status: str
    leader_id: str
    notional_usd: float
    fee_bps: int
    expiry: str
    backend: str


class RevokeResponse(BaseModel):
    passport_id: str
    tx_hash: str | None
    status: str
    previous_status: str


class EngineStartRequest(BaseModel):
    passport_id: str = Field(min_length=1, max_length=128)


class EngineStartResponse(BaseModel):
    status: str
    drawdown_usd: float
    trip_seconds: int


class EngineStopResponse(BaseModel):
    status: str
    drawdown_usd: float


class EngineTickResponse(BaseModel):
    passport_id: str
    drawdown_usd: float
    max_loss_usd: float


class MarketEventPayload(BaseModel):
    symbol: str = Field(min_length=1, max_length=64)
    change_pct: float = Field(ge=-100_000, le=100_000, allow_inf_nan=False)
    kind: str = Field(default="tick", min_length=1, max_length=32)
    timestamp: str = Field(default="", max_length=64)


class RedLineJudgeRequest(BaseModel):
    passport_id: str = Field(min_length=1, max_length=128)
    events: list[MarketEventPayload] | None = Field(default=None, max_length=100)


class RedLineJudgeResponse(BaseModel):
    passport_id: str
    verdict: dict[str, Any]
    flow: str
    side_effects: dict[str, Any] | None = None


class HealthResponse(BaseModel):
    ok: bool = True
    kiln: str
    passport_backend: str
    execution_backend: str


class DemoResetResponse(BaseModel):
    ok: bool = True


__all__ = [
    "ClarifyRequest",
    "ClarifyResponse",
    "CheckRequest",
    "CheckResponse",
    "EmitRequest",
    "EmitResponse",
    "FaceVerifyRequest",
    "FaceVerifyResponse",
    "PrepareRequest",
    "ConfirmRequest",
    "MintRequest",
    "MintResponse",
    "RevokeResponse",
    "EngineStartRequest",
    "EngineStartResponse",
    "EngineStopResponse",
    "EngineTickResponse",
    "RedLineJudgeRequest",
    "RedLineJudgeResponse",
    "HealthResponse",
    "DemoResetResponse",
]
