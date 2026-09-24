"""Read-only field readiness checks.

This module validates local tooling, committed contract integrity and live
configuration.  The optional RPC probe performs JSON-RPC reads only; it never
signs or broadcasts a transaction and never calls the Kiln generation API.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import socket
import subprocess
import sys
from pathlib import Path
from typing import Mapping
from urllib.parse import urlparse


PUBLIC_TESTNETS = {1001: "Kairos", 11155111: "Sepolia"}


def _check(name: str, ok: bool, detail: str, *, required: bool = True) -> dict:
    return {
        "name": name,
        "status": "pass" if ok else ("fail" if required else "warn"),
        "detail": detail,
    }


def _free(port: int) -> bool:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1", port))
        return True
    except OSError:
        return False


def _safe_https(value: str) -> bool:
    try:
        parsed = urlparse(value)
    except ValueError:
        return False
    return (
        parsed.scheme == "https"
        and bool(parsed.hostname)
        and parsed.username is None
        and parsed.password is None
        and not parsed.query
        and not parsed.fragment
    )


def _node_major() -> int | None:
    try:
        executable = shutil.which("node")
        if not executable:
            return None
        value = subprocess.run(
            [executable, "--version"],
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        ).stdout.strip()
        return int(value.removeprefix("v").split(".", 1)[0])
    except (OSError, ValueError, subprocess.SubprocessError):
        return None


def _artifact_matches(root: Path) -> bool:
    source = root / "chain" / "contracts" / "StrategyPassport.sol"
    artifact = root / "chain" / "artifacts" / "StrategyPassport.json"
    try:
        payload = json.loads(artifact.read_text(encoding="utf-8"))
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        return payload.get("source_sha256") == digest
    except (OSError, ValueError):
        return False


def _alphafox_checks(env: Mapping[str, str]) -> list[dict]:
    checks = [_check("alphafox_cli", shutil.which(env.get("ALPHAFOX_CLI", "alphafox")) is not None, "official CLI is installed")]
    connector = env.get("ALPHAFOX_PAPER_CONNECTOR_ID", "").strip()
    checks.append(_check("alphafox_paper_connector", bool(connector), "Paper connector id is configured (value redacted)"))
    try:
        leverage = int(env.get("ALPHAFOX_LEVERAGE", ""))
    except ValueError:
        leverage = 0
    checks.append(_check("alphafox_leverage", leverage > 0, "positive leverage is explicitly configured"))
    close_positions = env.get("ALPHAFOX_STOP_CLOSE_POSITIONS", "").strip().lower()
    checks.append(_check("alphafox_stop_policy", close_positions in {"true", "false"}, "closePositions is explicitly configured"))
    checks.append(_check(
        "alphafox_definition",
        env.get("ALPHAFOX_STRATEGY_DEFINITION_ID", "simple_copy_trading") == "simple_copy_trading",
        "verified simple_copy_trading definition is selected",
    ))
    return checks


def _rpc_probe(env: Mapping[str, str], chain_id: int) -> list[dict]:
    """Perform read-only RPC calls. No signer sends a transaction."""
    checks: list[dict] = []
    try:
        from web3 import Web3

        provider = Web3.HTTPProvider(env["RPC_URL"], request_kwargs={"timeout": 10})
        web3 = Web3(provider)
        actual_chain = int(web3.eth.chain_id)
        checks.append(_check("rpc_chain_id", actual_chain == chain_id, f"RPC returned chain {actual_chain}"))
        account = web3.eth.account.from_key(env["PRIVATE_KEY"])
        balance = int(web3.eth.get_balance(account.address))
        checks.append(_check("testnet_gas", balance > 0, f"wallet {account.address} balance is {balance} wei"))
        address = env.get("PASSPORT_ADDRESS", "").strip()
        if address:
            valid_address = Web3.is_address(address)
            has_code = valid_address and web3.eth.get_code(Web3.to_checksum_address(address)) not in {b"", b"\x00"}
            checks.append(_check("passport_contract", bool(has_code), "configured address has deployed bytecode"))
        else:
            checks.append(_check("passport_contract", True, "unset; live worker will deploy v2", required=False))
    except Exception as exc:  # noqa: BLE001 - provider failures become a concise check.
        checks.append(_check("rpc_read_only_probe", False, f"read-only RPC probe failed: {type(exc).__name__}"))
    return checks


def run_preflight(
    root: str | Path,
    env: Mapping[str, str] | None = None,
    *,
    live: bool = False,
    network: bool = False,
) -> dict:
    root = Path(root).resolve()
    source = dict(os.environ if env is None else env)
    checks = [
        _check("python", sys.version_info >= (3, 11), f"Python {sys.version_info.major}.{sys.version_info.minor}"),
        _check("node", (major := _node_major()) is not None and major >= 22, f"Node major {major or 'unavailable'}"),
        _check("frontend_dependencies", (root / "frontend" / "node_modules" / "vite").exists(), "Vite dependency installed"),
        _check("chain_dependencies", (root / "chain" / "node_modules" / "ethers").exists(), "Ethers dependency installed"),
        _check("contract_artifact", _artifact_matches(root), "artifact source hash matches Solidity"),
    ]
    backend_port = int(source.get("BACKEND_PORT", "8000"))
    frontend_port = int(source.get("FRONTEND_PORT", "5173"))
    backend_free = _free(backend_port)
    frontend_free = _free(frontend_port)
    checks.extend([
        _check("backend_port", backend_free, f"127.0.0.1:{backend_port} is {'available' if backend_free else 'already in use'}"),
        _check("frontend_port", frontend_free, f"127.0.0.1:{frontend_port} is {'available' if frontend_free else 'already in use'}"),
    ])
    if source.get("EXECUTION_BACKEND", "paper").strip().lower() == "alphafox":
        checks.extend(_alphafox_checks(source))

    if live:
        kiln_base = source.get("KILN_API_BASE", "").strip()
        rpc_url = source.get("RPC_URL", "").strip()
        key = source.get("PRIVATE_KEY", "").strip()
        try:
            chain_id = int(source.get("CHAIN_ID", "0"))
        except ValueError:
            chain_id = 0
        checks.extend([
            _check("kiln_mode", source.get("KILN_MODE", "").lower() == "live", "KILN_MODE must be live"),
            _check("kiln_model", source.get("KILN_MODEL", "gpt-oss-120b") == "gpt-oss-120b", "model must be gpt-oss-120b"),
            _check("kiln_api_base", _safe_https(kiln_base), "Kiln base must be a credential-free HTTPS URL"),
            _check("kiln_api_key", bool(source.get("KILN_API_KEY", "").strip()), "credential is present (value redacted)"),
            _check("passport_backend", source.get("PASSPORT_BACKEND", "").lower() == "testnet", "PASSPORT_BACKEND must be testnet"),
            _check("rpc_url", _safe_https(rpc_url), "RPC must be a credential-free HTTPS URL"),
            _check("private_key", re.fullmatch(r"0x[0-9a-fA-F]{64}", key) is not None, "dedicated test key is present (value redacted)"),
            _check("public_testnet", chain_id in PUBLIC_TESTNETS, f"chain {chain_id}: {PUBLIC_TESTNETS.get(chain_id, 'unsupported')}"),
            _check("kiln_live_call", False, "real generation call and API usage still required", required=False),
        ])
        if network and _safe_https(rpc_url) and re.fullmatch(r"0x[0-9a-fA-F]{64}", key) and chain_id in PUBLIC_TESTNETS:
            checks.extend(_rpc_probe(source, chain_id))
        elif network:
            checks.append(_check("rpc_read_only_probe", False, "skipped because RPC configuration is invalid"))
        else:
            checks.append(_check("rpc_read_only_probe", False, "not requested; pass --network for read-only checks", required=False))

    failed = [row["name"] for row in checks if row["status"] == "fail"]
    warnings = [row["name"] for row in checks if row["status"] == "warn"]
    return {
        "mode": "live" if live else "offline",
        "read_only": True,
        "broadcast_performed": False,
        "configuration_ready": not failed,
        "checks": checks,
        "failed": failed,
        "warnings": warnings,
    }


__all__ = ["run_preflight"]
