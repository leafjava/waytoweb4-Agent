"""Tests for the clarifier and emitter."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from agent.follow_agent import Clarifier, Emitter, MockKilnClient
from agent.shared.exceptions import SpecValidationError


def test_first_question_when_everything_present() -> None:
    c = Clarifier(MockKilnClient())
    text = "follow leader-demo-001 with 500 USD, max loss 50 USD, 48 hours"
    q = c.first_question(text)
    assert q.field == ""


def test_first_question_asks_for_leader_first() -> None:
    c = Clarifier(MockKilnClient())
    q = c.first_question("500 USD 跟单，亏 50")
    assert q.field == "leaderId"
    assert q.attempt == 1


def test_clarifier_does_not_ask_third_round() -> None:
    c = Clarifier(MockKilnClient(), max_rounds=2)
    q1 = c.first_question("跟单 500 USD")  # missing leader + max loss
    assert q1.field == "leaderId"
    q2 = c.next_question("...", prior=q1)
    # Even with same answer the clarifier refuses to ask a 3rd time
    # because attempt would exceed max_rounds.
    assert q2 is None


def test_emitter_produces_valid_spec_from_mock() -> None:
    e = Emitter(MockKilnClient())
    e.add_user("follow leader-demo-001 with 500 USD max loss 50 48 hours")
    spec = e.emit()
    assert spec.mode == "copy"
    assert spec.venue == "paper"
    assert spec.paper is True


def test_emitter_rejects_malformed_payload() -> None:
    """If the mock returned garbage, the emitter must surface an error
    instead of silently returning something."""
    class BrokenClient:
        model = "broken"

        def chat(self, messages, flow_tag):  # noqa: D401
            from agent.follow_agent.kiln_client import KilnReply
            return KilnReply(
                text="not json at all, just prose",
                tokens_in=1,
                tokens_out=1,
                latency_s=0.0,
                model="broken",
            )

    e = Emitter(BrokenClient())
    e.add_user("whatever")
    with pytest.raises(SpecValidationError):
        e.emit()


def test_emitter_uses_code_validation_for_mode() -> None:
    """A spec that says mode='grid_bot' (even after the mock) must be
    rejected by the validator inside the emitter."""
    class GridBotClient:
        model = "broken"

        def chat(self, messages, flow_tag):
            import json
            from datetime import datetime, timedelta, timezone
            from agent.follow_agent.kiln_client import KilnReply
            payload = {
                "mode": "grid_bot",  # forbidden
                "leaderId": "x",
                "venue": "paper",
                "notionalUsd": 100,
                "maxLossUsd": 50,
                "expiry": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
                "faceVerified": False,
                "paper": True,
            }
            return KilnReply(
                text=json.dumps(payload),
                tokens_in=1, tokens_out=1, latency_s=0.0, model="broken",
            )

    e = Emitter(GridBotClient())
    e.add_user("whatever")
    with pytest.raises(SpecValidationError):
        e.emit()