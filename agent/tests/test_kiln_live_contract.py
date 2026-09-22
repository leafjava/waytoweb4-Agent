from __future__ import annotations

import json
import pytest

from agent.follow_agent.kiln_client import ChatMessage, HttpKilnClient, KilnReply, build_kiln_client
from agent.redline_agent.llm_classifier import KilnEventClassifier, MarketEvent


def test_live_mode_without_key_refuses_mock():
    with pytest.raises(RuntimeError, match="requires KILN_API_KEY"):
        build_kiln_client(env={"KILN_MODE": "live"})


class StubClient:
    def chat(self, messages, flow_tag):
        assert flow_tag == "redline_hold"
        return KilnReply('{"level":"WATCH","reason_codes":["LEV_ETF_AMP"],"evidence":["stub"]}', 1, 2, 0.01, "gpt-oss-120b")


def test_kiln_classifier_uses_strict_json_contract():
    verdict = KilnEventClassifier(StubClient()).classify([MarketEvent("KS200", -2.0)])
    assert verdict.level.value == "WATCH"
    assert verdict.source == "kiln"


def test_http_client_rejects_response_without_model(monkeypatch):
    import httpx

    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "choices": [{"message": {"content": "{}"}}],
                "usage": {"prompt_tokens": 1, "completion_tokens": 1},
            }

    monkeypatch.setattr(httpx, "post", lambda *args, **kwargs: Response())
    client = HttpKilnClient("https://kiln.invalid/v1", "key", "gpt-oss-120b")
    with pytest.raises(RuntimeError, match="response model mismatch"):
        client.chat([ChatMessage("user", "test")], "clarify")
