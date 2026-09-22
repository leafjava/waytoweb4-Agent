"""Versioned, cross-language copy-intent canonicalization."""

from __future__ import annotations

import json
import math
import re
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

from web3 import Web3

HASH_VERSION = "intent-keccak-v1"
_LEADER = re.compile(r"^[A-Za-z0-9_-]+$")


class IntentError(ValueError):
    pass


def _cents(value: Any, name: str) -> int:
    if isinstance(value, bool):
        raise IntentError(f"{name} must be a finite decimal amount")
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise IntentError(f"{name} must be a finite decimal amount") from exc
    if not amount.is_finite() or amount <= 0:
        raise IntentError(f"{name} must be positive and finite")
    if amount.as_tuple().exponent < -2:
        raise IntentError(f"{name} accepts at most two decimal places")
    cents = amount * 100
    if cents != cents.to_integral_value():
        raise IntentError(f"{name} cannot be represented exactly in cents")
    return int(cents)


def _expiry(value: Any, *, creating: bool, now: datetime | None) -> int:
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise IntentError("expiry must be an ISO-8601 datetime") from exc
    else:
        raise IntentError("expiry must be an ISO-8601 datetime")
    if dt.tzinfo is None:
        raise IntentError("expiry must include a timezone")
    dt = dt.astimezone(timezone.utc)
    if dt.microsecond:
        raise IntentError("expiry must use whole seconds")
    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    if creating and dt < current + timedelta(minutes=5):
        raise IntentError("expiry must be at least five minutes in the future")
    return int(dt.timestamp())


def canonicalize_intent(
    spec: dict[str, Any], *, creating: bool = True, now: datetime | None = None
) -> tuple[str, str, int, int, int]:
    if spec.get("mode") != "copy" or spec.get("venue") != "paper" or spec.get("paper") is not True:
        raise IntentError("only copy mode on the paper venue is supported")
    leader = spec.get("leaderId")
    if not isinstance(leader, str) or not _LEADER.fullmatch(leader):
        raise IntentError("leaderId must contain only ASCII letters, digits, '-' or '_'")
    if not 1 <= len(leader.encode("ascii")) <= 64:
        raise IntentError("leaderId must be between 1 and 64 ASCII bytes")
    notional = _cents(spec.get("notionalUsd"), "notionalUsd")
    max_loss = _cents(spec.get("maxLossUsd"), "maxLossUsd")
    if notional > 1_000_000:
        raise IntentError("notionalUsd cannot exceed 10000")
    if max_loss > notional:
        raise IntentError("maxLossUsd cannot exceed notionalUsd")
    expiry = _expiry(spec.get("expiry"), creating=creating, now=now)
    payload = {
        "expiryUnix": str(expiry),
        "leaderId": leader,
        "maxLossCents": str(max_loss),
        "mode": "copy",
        "notionalCents": str(notional),
        "paper": True,
        "venue": "paper",
        "version": HASH_VERSION,
    }
    canonical = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    digest = "0x" + Web3.keccak(text=canonical).hex().lower().removeprefix("0x")
    return canonical, digest, notional, max_loss, expiry


def is_expired(expiry: str | datetime, now: datetime | None = None) -> bool:
    try:
        unix = _expiry(expiry, creating=False, now=now)
    except IntentError:
        return True
    current = int((now or datetime.now(timezone.utc)).timestamp())
    return unix <= current


__all__ = ["HASH_VERSION", "IntentError", "canonicalize_intent", "is_expired"]
