"""Locked Spec schema for copy-trading intent.

This is the single contract between the natural-language layer and
every downstream consumer (face gate, waytoweb4 adapter, passport
minter, RedLine). Per PRD §4.1 the Spec is deliberately narrow:

    - mode is forced to 'copy' (no new strategy types)
    - venue is forced to 'paper' (no live trading)
    - paper is forced to True
    - extra fields are forbidden

Anything not representable here cannot reach the engine, even if a
prompt-injection convinces the LLM to emit it.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)
from pydantic import ValidationError as PydanticValidationError

from agent.shared.exceptions import SpecValidationError

# ---- Demo / PRD defaults -----------------------------------------------------

# PRD §4.1 "Demo 默认" column. These are the values the demo uses when
# the user is vague and the clarifier has to fill in blanks. They are
# kept here (not in prompts) so the contract is one place to audit.
DEMO_DEFAULT_NOTIONAL_USD: float = 500.0
DEMO_DEFAULT_MAX_LOSS_USD: float = 50.0
DEMO_DEFAULT_EXPIRY: timedelta = timedelta(hours=48)

# Hard ceiling on notional. Big enough for the demo (500), small enough
# that a hallucinated "1000000" gets rejected before it ever reaches
# the waytoweb4 adapter.
MAX_NOTIONAL_USD: float = 10_000.0

# Minimum expiry window. Anything shorter than this is almost certainly
# a typo and we refuse it.
MIN_EXPIRY_DELTA: timedelta = timedelta(minutes=5)


# ---- The Spec model ----------------------------------------------------------


class CopyTradingSpec(BaseModel):
    """The locked copy-trading intent.

    Construct with a dict from the LLM (or from JSON the backend
    receives from the client). Validation is strict; any violation
    raises `SpecValidationError` via `model_validate`.
    """

    model_config = ConfigDict(
        extra="forbid",          # no silent fields
        frozen=True,             # immutable after construction
        str_strip_whitespace=True,
    )

    mode: Literal["copy"]
    leaderId: Annotated[str, Field(min_length=1, max_length=64)]
    venue: Literal["paper"]
    notionalUsd: float = Field(gt=0, le=MAX_NOTIONAL_USD, strict=True)
    maxLossUsd: float = Field(gt=0, strict=True)
    expiry: datetime
    faceVerified: bool = False
    paper: bool = Field(default=True, strict=True)

    # ---- field-level validators ------------------------------------------

    @field_validator("paper")
    @classmethod
    def _paper_must_be_true(cls, v: bool) -> bool:
        if v is not True:
            raise SpecValidationError(f"paper must be True, got {v!r}.")
        return v

    @field_validator("leaderId")
    @classmethod
    def _leader_id_clean(cls, v: str) -> str:
        # Allow alphanumerics, dash, underscore. Reject anything that
        # looks like a JSON-injection probe.
        if not v.replace("-", "").replace("_", "").isalnum():
            raise SpecValidationError(
                f"leaderId {v!r} contains illegal characters; "
                "expected alphanumerics, '-', '_'."
            )
        return v

    @field_validator("expiry")
    @classmethod
    def _expiry_must_be_future(cls, v: datetime) -> datetime:
        # Normalize to UTC so downstream comparisons don't depend on the
        # caller's local timezone. We compare in UTC.
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        else:
            v = v.astimezone(timezone.utc)
        now = datetime.now(timezone.utc)
        if v <= now:
            raise SpecValidationError(
                f"expiry {v.isoformat()} is not in the future (now={now.isoformat()})."
            )
        if v - now < MIN_EXPIRY_DELTA:
            raise SpecValidationError(
                f"expiry must be at least {MIN_EXPIRY_DELTA} in the future."
            )
        return v

    # ---- cross-field validators -------------------------------------------

    @model_validator(mode="after")
    def _cross_field(self) -> "CopyTradingSpec":
        # PRD says: maxLossUsd cannot exceed notionalUsd. This is the
        # whole point of the "限亏不能超过本金" guard rail.
        if self.maxLossUsd > self.notionalUsd:
            raise SpecValidationError(
                f"maxLossUsd ({self.maxLossUsd}) cannot exceed "
                f"notionalUsd ({self.notionalUsd})."
            )
        return self

    # ---- public constructors ---------------------------------------------

    @classmethod
    def model_validate(cls, data):  # type: ignore[override]
        """Re-wrap Pydantic's ValidationError as SpecValidationError.

        We translate every Pydantic-level failure into our own
        exception type so callers only have to catch one error class.
        The wrapped `__cause__` keeps the original traceback for
        debugging.
        """
        try:
            return super().model_validate(data)
        except PydanticValidationError as e:
            raise SpecValidationError(f"Spec validation failed: {e}") from e


def demo_default_spec(leader_id: str = "leader-demo-001") -> CopyTradingSpec:
    """Return the PRD §4.1 default Spec verbatim. For tests and the demo
    script; never used on the real request path because `faceVerified`
    starts False."""
    return CopyTradingSpec(
        mode="copy",
        leaderId=leader_id,
        venue="paper",
        notionalUsd=DEMO_DEFAULT_NOTIONAL_USD,
        maxLossUsd=DEMO_DEFAULT_MAX_LOSS_USD,
        expiry=datetime.now(timezone.utc) + DEMO_DEFAULT_EXPIRY,
        faceVerified=False,
        paper=True,
    )


__all__ = [
    "CopyTradingSpec",
    "demo_default_spec",
    "DEMO_DEFAULT_NOTIONAL_USD",
    "DEMO_DEFAULT_MAX_LOSS_USD",
    "DEMO_DEFAULT_EXPIRY",
    "MAX_NOTIONAL_USD",
    "MIN_EXPIRY_DELTA",
]