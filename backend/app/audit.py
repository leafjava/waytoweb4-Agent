"""Audit events for the demo.

Every mutating operation appends one event to the in-memory log.
The frontend reads the log via `GET /api/state`; a third-party
auditor could replay it to answer "what happened, when, and why".

We deliberately keep this as a plain dataclass + an in-process list
(no DB). The event log is intentionally append-only; there is no API
to delete or mutate past events.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class AuditEvent:
    """One entry in the audit log.

    `kind` is the closed set below; new operations add a new kind
    in one place rather than scattering string literals.

    `passport_id` is optional so we can log "demo/reset" events that
    aren't tied to any passport.

    `payload` is intentionally `dict[str, Any]` -- we do not want a
    rigid schema here because the variety of mutations is wide. The
    serialiser is canonical-JSON for the on-chain variant.
    """

    kind: str
    passport_id: str | None
    payload: dict[str, Any]
    ts: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# Closed set of audit event kinds. Used by tests to assert that no
# unknown kind sneaks into the log.
AUDIT_KINDS: frozenset[str] = frozenset(
    {
        "spec_clarify",
        "spec_emit",
        "prepare",
        "confirm",
        "mint_simulated",
        "revoke_simulated",
        "revoke_confirmed",
        "revoke_readback",
        "revoke_uncertain",
        "mint",
        "face_verify",
        "face_gate_invalidated",
        "engine_start",
        "engine_stop",
        "engine_tick",
        "revoke",
        "redline_judge",
        "demo_inject",
        "demo_reset",
        "restart_reconcile",
    }
)


def make_event(kind: str, passport_id: str | None, payload: dict[str, Any]) -> AuditEvent:
    """Factory that rejects unknown kinds at construction time."""
    if kind not in AUDIT_KINDS:
        raise ValueError(
            f"Unknown audit kind {kind!r}; must be one of {sorted(AUDIT_KINDS)}."
        )
    return AuditEvent(kind=kind, passport_id=passport_id, payload=payload)


__all__ = ["AuditEvent", "AUDIT_KINDS", "make_event"]
