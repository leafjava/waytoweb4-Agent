"""Tests for the locked CopyTradingSpec schema.

These are the most security-critical tests in the repo: the Spec
schema is the single contract between the LLM and every downstream
component. If any of these regress, the demo is at risk of letting
LLM output leak into production behaviour.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from agent.follow_agent.spec_schema import (
    DEMO_DEFAULT_MAX_LOSS_USD,
    DEMO_DEFAULT_NOTIONAL_USD,
    MAX_NOTIONAL_USD,
    CopyTradingSpec,
    demo_default_spec,
)
from agent.shared.exceptions import SpecValidationError


def _future(minutes: int = 60) -> datetime:
    return datetime.now(timezone.utc) + timedelta(minutes=minutes)


def _payload(**overrides) -> dict:
    base = {
        "mode": "copy",
        "leaderId": "leader-demo-001",
        "venue": "paper",
        "notionalUsd": DEMO_DEFAULT_NOTIONAL_USD,
        "maxLossUsd": DEMO_DEFAULT_MAX_LOSS_USD,
        "expiry": _future(minutes=60 * 48).isoformat(),
        "faceVerified": False,
        "paper": True,
    }
    base.update(overrides)
    return base


# ---- happy path -------------------------------------------------------------


def test_default_spec_validates() -> None:
    spec = CopyTradingSpec.model_validate(_payload())
    assert spec.mode == "copy"
    assert spec.venue == "paper"
    assert spec.paper is True
    assert spec.faceVerified is False


def test_demo_default_spec_is_frozen() -> None:
    spec = demo_default_spec()
    assert spec.notionalUsd == DEMO_DEFAULT_NOTIONAL_USD
    assert spec.maxLossUsd == DEMO_DEFAULT_MAX_LOSS_USD
    # Pydantic v2 frozen=True forbids attribute mutation.
    with pytest.raises(Exception):
        spec.notionalUsd = 9999.0  # type: ignore[misc]


# ---- mode must be copy ------------------------------------------------------


@pytest.mark.parametrize("bad_mode", ["grid_bot", "scalp", "martingale", "", "COPY"])
def test_mode_must_be_literal_copy(bad_mode: str) -> None:
    with pytest.raises(SpecValidationError):
        CopyTradingSpec.model_validate(_payload(mode=bad_mode))


# ---- venue must be paper ----------------------------------------------------


@pytest.mark.parametrize("bad_venue", ["binance", "live", "", "PAPER"])
def test_venue_must_be_literal_paper(bad_venue: str) -> None:
    with pytest.raises(SpecValidationError):
        CopyTradingSpec.model_validate(_payload(venue=bad_venue))


# ---- paper must be True -----------------------------------------------------


@pytest.mark.parametrize("bad_paper", [False, "true", 1, None])
def test_paper_must_be_true(bad_paper) -> None:
    with pytest.raises(SpecValidationError):
        CopyTradingSpec.model_validate(_payload(paper=bad_paper))


# ---- extra fields are forbidden --------------------------------------------


def test_extra_fields_forbidden() -> None:
    with pytest.raises(SpecValidationError):
        CopyTradingSpec.model_validate(_payload(sneaky_field="lol"))


def test_unknown_field_in_llm_payload_rejected() -> None:
    # Simulate the LLM trying to sneak in a "leverage" field.
    bad = _payload()
    bad["leverage"] = 5
    with pytest.raises(SpecValidationError):
        CopyTradingSpec.model_validate(bad)


# ---- notional bounds --------------------------------------------------------


def test_notional_must_be_positive() -> None:
    with pytest.raises(SpecValidationError):
        CopyTradingSpec.model_validate(_payload(notionalUsd=0))


def test_notional_must_be_at_most_ceiling() -> None:
    with pytest.raises(SpecValidationError):
        CopyTradingSpec.model_validate(_payload(notionalUsd=MAX_NOTIONAL_USD + 1))


def test_notional_ceiling_constant_is_sane() -> None:
    # Guard against accidental lowering of the ceiling.
    assert MAX_NOTIONAL_USD >= DEMO_DEFAULT_NOTIONAL_USD


# ---- max loss cannot exceed notional ----------------------------------------


def test_max_loss_cannot_exceed_notional() -> None:
    with pytest.raises(SpecValidationError):
        CopyTradingSpec.model_validate(_payload(notionalUsd=100, maxLossUsd=101))


def test_max_loss_equal_to_notional_ok() -> None:
    # Edge case: 100% max-loss is allowed (though we recommend smaller).
    spec = CopyTradingSpec.model_validate(_payload(notionalUsd=100, maxLossUsd=100))
    assert spec.maxLossUsd == spec.notionalUsd == 100


def test_max_loss_must_be_positive() -> None:
    with pytest.raises(SpecValidationError):
        CopyTradingSpec.model_validate(_payload(maxLossUsd=0))


# ---- expiry -----------------------------------------------------------------


def test_expiry_in_past_rejected() -> None:
    past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    with pytest.raises(SpecValidationError):
        CopyTradingSpec.model_validate(_payload(expiry=past))


def test_expiry_too_soon_rejected() -> None:
    # Within MIN_EXPIRY_DELTA window.
    soon = (datetime.now(timezone.utc) + timedelta(minutes=1)).isoformat()
    with pytest.raises(SpecValidationError):
        CopyTradingSpec.model_validate(_payload(expiry=soon))


def test_expiry_naive_datetime_is_normalised() -> None:
    # Pydantic should accept a naive ISO string and treat it as UTC.
    naive = (datetime.now(timezone.utc) + timedelta(hours=24)).replace(tzinfo=None).isoformat()
    spec = CopyTradingSpec.model_validate(_payload(expiry=naive))
    assert spec.expiry.tzinfo is not None


# ---- leaderId ----------------------------------------------------------------


@pytest.mark.parametrize(
    "bad_leader",
    [
        "",
        "leader with space",
        "leader;DROP",
        "leader\ninjection",
    ],
)
def test_leader_id_rejects_unsafe_chars(bad_leader: str) -> None:
    with pytest.raises(SpecValidationError):
        CopyTradingSpec.model_validate(_payload(leaderId=bad_leader))


def test_leader_id_accepts_safe_chars() -> None:
    spec = CopyTradingSpec.model_validate(_payload(leaderId="leader-007_ok"))
    assert spec.leaderId == "leader-007_ok"