from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from backend.app.execution_adapters.alphafox import (
    AlphaFoxCliAdapter,
    AlphaFoxConfig,
    AlphaFoxExecutionError,
    build_create_payload,
)
from backend.app.execution_contract import ExecutionStartCommand


def _command() -> ExecutionStartCommand:
    return ExecutionStartCommand(
        request_id="request-1",
        run_id="run-1",
        passport_id="passport-123456789",
        spec_hash="0x" + "ab" * 32,
        leader_id="hl-leader-1",
        notional_cents=50_000,
        max_loss_cents=5_000,
        expiry="2026-09-30T03:00:00Z",
        policy_path="policy.json",
        lease_s=3,
    )


def _config() -> AlphaFoxConfig:
    return AlphaFoxConfig("paper-connector", 1, True)


def test_build_create_payload_uses_capital_cap_and_paper_connector():
    payload = build_create_payload(_command(), _config())
    assert payload["strategyDefinitionId"] == "simple_copy_trading"
    assert payload["exchangeConnectorId"] == "paper-connector"
    assert payload["autoStart"] is True
    assert payload["config"]["strategy"]["fixedEquity"] == 500.0
    source = payload["config"]["strategy"]["signalSourceConfigs"][0]
    assert source == {
        "signalSourceId": "hl-leader-1",
        "marginPercent": 100,
        "followSide": "BOTH",
        "exitTime": "2026-09-30T03:00:00Z",
    }
    encoded = json.dumps(payload)
    assert "max_loss_cents" not in encoded
    assert "token" not in encoded.lower()


def test_config_requires_explicit_safety_choices():
    with pytest.raises(ValueError, match="PAPER_CONNECTOR"):
        AlphaFoxConfig.from_env({})
    with pytest.raises(ValueError, match="LEVERAGE"):
        AlphaFoxConfig.from_env({"ALPHAFOX_PAPER_CONNECTOR_ID": "paper"})
    with pytest.raises(ValueError, match="explicitly"):
        AlphaFoxConfig.from_env({"ALPHAFOX_PAPER_CONNECTOR_ID": "paper", "ALPHAFOX_LEVERAGE": "1"})


@pytest.mark.asyncio
async def test_start_dry_runs_before_mutation(monkeypatch, tmp_path):
    calls = []

    class Process:
        def __init__(self, payload):
            self.returncode = 0
            self.payload = payload

        async def communicate(self):
            return json.dumps(self.payload).encode(), b""

    async def fake_exec(*args, **kwargs):
        calls.append(args)
        assert "PRIVATE_KEY" not in kwargs["env"]
        assert "KILN_API_KEY" not in kwargs["env"]
        is_dry = "--dry-run" in args
        return Process({"ok": True, "data": {} if is_dry else {"trader": {"id": "trader-1"}}})

    monkeypatch.setattr("backend.app.execution_adapters.alphafox.shutil.which", lambda _: "alphafox")
    monkeypatch.setattr("backend.app.execution_adapters.alphafox.asyncio.create_subprocess_exec", fake_exec)
    monkeypatch.setenv("PRIVATE_KEY", "must-not-reach-cli")
    monkeypatch.setenv("KILN_API_KEY", "must-not-reach-cli")
    adapter = AlphaFoxCliAdapter(_config())
    assert await adapter.start(_command()) == "trader-1"
    assert "--dry-run" in calls[0]
    assert "--yes" in calls[1]
    assert not any("token" in str(part).lower() for call in calls for part in call)


@pytest.mark.asyncio
async def test_stop_rejects_untrusted_trader_id():
    adapter = AlphaFoxCliAdapter(_config())
    with pytest.raises(AlphaFoxExecutionError, match="invalid"):
        await adapter.stop("bad id")
