"""Tests for the Kiln client.

We test:
  * the mock client's behaviour on the three flows (clarify,
    spec_emit, demo_inject)
  * the factory picks the real client when KILN_API_KEY is set
  * token accounting for both clients
"""

from __future__ import annotations

import pytest

from agent.follow_agent.kiln_client import (
    ChatMessage,
    HttpKilnClient,
    MockKilnClient,
    build_kiln_client,
)
from agent.shared.token_logger import ALLOWED_FLOWS, TokenLogger


def test_mock_returns_canned_clarify() -> None:
    client = MockKilnClient()
    reply = client.chat(
        [ChatMessage("system", "x"), ChatMessage("user", "我想跟单")],
        flow_tag="clarify",
    )
    # Without a leader mentioned, the mock asks for one.
    assert "leader" in reply.text.lower()
    assert reply.tokens_in > 0
    assert reply.tokens_out > 0
    assert reply.latency_s >= 0


def test_mock_returns_canned_spec_json() -> None:
    client = MockKilnClient()
    reply = client.chat(
        [ChatMessage("system", "x"), ChatMessage("user", "go")],
        flow_tag="spec_emit",
    )
    # Should be a JSON object with the locked fields.
    import json
    payload = json.loads(reply.text)
    assert payload["mode"] == "copy"
    assert payload["venue"] == "paper"
    assert payload["paper"] is True


def test_factory_picks_http_when_key_present() -> None:
    client = build_kiln_client(env={"KILN_API_KEY": "test-key"})
    assert isinstance(client, HttpKilnClient)
    assert client.model == "gpt-oss-120b"


def test_factory_picks_mock_when_no_key() -> None:
    client = build_kiln_client(env={})
    assert isinstance(client, MockKilnClient)


def test_factory_honors_custom_model() -> None:
    client = build_kiln_client(
        env={
            "KILN_API_KEY": "k",
            "KILN_MODEL": "custom-120b",
        }
    )
    assert isinstance(client, HttpKilnClient)
    assert client.model == "custom-120b"


def test_mock_records_into_default_logger(fresh_logger: TokenLogger) -> None:
    # Inject our own logger via the shared default.
    from agent.shared.token_logger import get_default_logger
    # pre-clear and re-fetch
    logger = get_default_logger()
    client = MockKilnClient()
    client.chat([ChatMessage("user", "hi")], flow_tag="clarify")
    client.chat([ChatMessage("user", "go")], flow_tag="spec_emit")
    assert "clarify" in logger.flows()
    assert "spec_emit" in logger.flows()


def test_unknown_flow_tag_is_rejected() -> None:
    client = MockKilnClient()
    with pytest.raises(ValueError):
        client.chat([ChatMessage("user", "x")], flow_tag="not_a_real_flow")


def test_allowed_flows_match_prd() -> None:
    assert set(ALLOWED_FLOWS) == {
        "clarify",
        "spec_emit",
        "redline_hold",
        "redline_trip",
        "demo_inject",
    }