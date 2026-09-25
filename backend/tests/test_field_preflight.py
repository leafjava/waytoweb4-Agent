from __future__ import annotations

import hashlib
import json

from backend.app import field_preflight


def _root(tmp_path):
    source = tmp_path / "chain" / "contracts" / "StrategyPassport.sol"
    source.parent.mkdir(parents=True)
    source.write_text("contract Test {}", encoding="utf-8")
    artifact = tmp_path / "chain" / "artifacts" / "StrategyPassport.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_text(json.dumps({"source_sha256": hashlib.sha256(source.read_bytes()).hexdigest()}), encoding="utf-8")
    (tmp_path / "chain" / "node_modules" / "ethers").mkdir(parents=True)
    (tmp_path / "frontend" / "node_modules" / "vite").mkdir(parents=True)
    return tmp_path


def test_offline_preflight_is_read_only(monkeypatch, tmp_path):
    monkeypatch.setattr(field_preflight, "_node_major", lambda: 22)
    monkeypatch.setattr(field_preflight, "_free", lambda port: True)
    result = field_preflight.run_preflight(_root(tmp_path), env={})
    assert result["configuration_ready"] is True
    assert result["broadcast_performed"] is False
    assert result["read_only"] is True


def test_live_preflight_redacts_credentials(monkeypatch, tmp_path):
    monkeypatch.setattr(field_preflight, "_node_major", lambda: 22)
    monkeypatch.setattr(field_preflight, "_free", lambda port: True)
    secret = "kiln-super-secret"
    key = "0x" + "11" * 32
    result = field_preflight.run_preflight(
        _root(tmp_path),
        env={
            "KILN_MODE": "live",
            "KILN_MODEL": "gpt-oss-120b",
            "KILN_API_BASE": "https://api.kiln.ai/v1",
            "KILN_API_KEY": secret,
            "PASSPORT_BACKEND": "testnet",
            "RPC_URL": "https://rpc.example.invalid/project",
            "PRIVATE_KEY": key,
            "CHAIN_ID": "11155111",
        },
        live=True,
    )
    rendered = json.dumps(result)
    assert result["configuration_ready"] is True
    assert secret not in rendered
    assert key not in rendered
    assert "kiln_live_call" in result["warnings"]
    assert "rpc_read_only_probe" in result["warnings"]


def test_live_preflight_fails_closed_without_credentials(monkeypatch, tmp_path):
    monkeypatch.setattr(field_preflight, "_node_major", lambda: 22)
    monkeypatch.setattr(field_preflight, "_free", lambda port: True)
    result = field_preflight.run_preflight(_root(tmp_path), env={}, live=True)
    assert result["configuration_ready"] is False
    assert "kiln_api_key" in result["failed"]
    assert "private_key" in result["failed"]


def test_alphafox_preflight_requires_explicit_paper_controls(monkeypatch, tmp_path):
    monkeypatch.setattr(field_preflight, "_node_major", lambda: 22)
    monkeypatch.setattr(field_preflight, "_free", lambda port: True)
    monkeypatch.setattr(field_preflight.shutil, "which", lambda name: "alphafox" if name == "alphafox" else "node")
    env = {
        "EXECUTION_BACKEND": "alphafox",
        "ALPHAFOX_PAPER_CONNECTOR_ID": "paper-1",
        "ALPHAFOX_LEVERAGE": "1",
        "ALPHAFOX_STOP_CLOSE_POSITIONS": "true",
    }
    result = field_preflight.run_preflight(_root(tmp_path), env=env)
    names = {row["name"]: row["status"] for row in result["checks"]}
    assert names["alphafox_cli"] == "pass"
    assert names["alphafox_paper_connector"] == "pass"
    assert names["alphafox_stop_policy"] == "pass"
