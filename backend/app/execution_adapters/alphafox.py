"""Official AlphaFox CLI transport for Paper copy-trading.

The CLI owns OAuth tokens in the OS keychain.  This adapter never accepts a
token, never invokes a shell, and only uses the eight catalog operations listed
in ``docs/ALPHAFOX-ADAPTER.md``.  Mutations are preceded by CLI dry-run.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import shutil
import tempfile
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, Mapping

from ..execution_contract import ExecutionStartCommand


class AlphaFoxExecutionError(RuntimeError):
    """A safe, token-free AlphaFox transport failure."""


@dataclass(frozen=True)
class AlphaFoxConfig:
    connector_id: str
    leverage: int
    close_positions_on_stop: bool
    strategy_definition_id: str = "simple_copy_trading"
    cli_path: str = "alphafox"
    timeout_s: float = 20.0

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "AlphaFoxConfig":
        source = os.environ if env is None else env
        connector_id = source.get("ALPHAFOX_PAPER_CONNECTOR_ID", "").strip()
        if not connector_id:
            raise ValueError("ALPHAFOX_PAPER_CONNECTOR_ID is required")
        try:
            leverage = int(source.get("ALPHAFOX_LEVERAGE", ""))
        except ValueError as exc:
            raise ValueError("ALPHAFOX_LEVERAGE must be a positive integer") from exc
        if leverage <= 0:
            raise ValueError("ALPHAFOX_LEVERAGE must be a positive integer")
        close_raw = source.get("ALPHAFOX_STOP_CLOSE_POSITIONS", "").strip().lower()
        if close_raw not in {"true", "false"}:
            raise ValueError("ALPHAFOX_STOP_CLOSE_POSITIONS must be explicitly true or false")
        strategy = source.get("ALPHAFOX_STRATEGY_DEFINITION_ID", "simple_copy_trading").strip()
        if strategy != "simple_copy_trading":
            raise ValueError("only the verified simple_copy_trading definition is supported")
        return cls(
            connector_id=connector_id,
            leverage=leverage,
            close_positions_on_stop=close_raw == "true",
            strategy_definition_id=strategy,
            cli_path=source.get("ALPHAFOX_CLI", "alphafox").strip() or "alphafox",
        )


def build_create_payload(command: ExecutionStartCommand, config: AlphaFoxConfig) -> dict[str, Any]:
    """Map the frozen mandate to AlphaFox's verified v4 copy schema."""
    capital = Decimal(command.notional_cents) / Decimal(100)
    return {
        "name": f"WayToWeb4 {command.passport_id[:12]}",
        "strategyDefinitionId": config.strategy_definition_id,
        "exchangeConnectorId": config.connector_id,
        "configSchemaVersion": 4,
        "config": {
            "common": {
                "execution": {"leverage": config.leverage, "openMinPosition": False},
                "riskControl": {},
                "orderExecution": {},
            },
            "strategy": {
                "fixedEquity": float(capital),
                "followSignalLeverage": False,
                "positionFollowMode": "proportional",
                "signalSourceConfigs": [{
                    "signalSourceId": command.leader_id,
                    "marginPercent": 100,
                    "followSide": "BOTH",
                    "exitTime": command.expiry,
                }],
                "syncPositionsOnTrade": True,
                "useAmountPercent": False,
            },
        },
        "shareParameters": False,
        "autoStart": True,
    }


class AlphaFoxCliAdapter:
    provider = "alphafox"

    def __init__(self, config: AlphaFoxConfig):
        self.config = config

    async def start(self, command: ExecutionStartCommand) -> str:
        payload = build_create_payload(command, self.config)
        result = await self._mutation(
            ["trading", "traders", "create"], payload, operation="create trader"
        )
        trader = (result.get("data") or {}).get("trader") or {}
        trader_id = trader.get("id")
        if not isinstance(trader_id, str) or not trader_id:
            raise AlphaFoxExecutionError("AlphaFox create response omitted trader id")
        return trader_id

    async def stop(self, trader_id: str) -> None:
        if re.fullmatch(r"[A-Za-z0-9_-]{1,128}", trader_id) is None:
            raise AlphaFoxExecutionError("invalid AlphaFox trader id")
        payload = {"closePositions": self.config.close_positions_on_stop}
        await self._mutation(
            ["trading", "traders", "byId", "stop", "--traderId", trader_id],
            payload,
            operation="stop trader",
        )

    async def start_existing(self, trader_id: str) -> None:
        """Expose the eighth allowlisted operation for a reviewed stopped trader."""
        if re.fullmatch(r"[A-Za-z0-9_-]{1,128}", trader_id) is None:
            raise AlphaFoxExecutionError("invalid AlphaFox trader id")
        await self._mutation(
            ["trading", "traders", "byId", "start", "--traderId", trader_id],
            {},
            operation="start trader",
        )

    async def _mutation(self, command: list[str], payload: dict[str, Any], *, operation: str) -> dict[str, Any]:
        with tempfile.TemporaryDirectory(prefix="w2w4-alphafox-") as tmp:
            path = Path(tmp) / "payload.json"
            path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            config_arg = f"@{path}"
            base = [*command, "--config", config_arg]
            await self._run([*base, "--dry-run", "--format", "json", "--no-input"], operation=f"dry-run {operation}")
            return await self._run([*base, "--yes", "--format", "json", "--no-input"], operation=operation)

    async def _run(self, args: list[str], *, operation: str) -> dict[str, Any]:
        executable = shutil.which(self.config.cli_path)
        if not executable:
            raise AlphaFoxExecutionError("AlphaFox CLI is not installed")
        allowed_env = {
            "PATH", "PATHEXT", "SYSTEMROOT", "WINDIR", "COMSPEC", "TEMP", "TMP",
            "USERPROFILE", "APPDATA", "LOCALAPPDATA", "PROGRAMDATA",
        }
        env = {k: v for k, v in os.environ.items() if k.upper() in allowed_env}
        env["NO_COLOR"] = "1"
        process = None
        try:
            process = await asyncio.create_subprocess_exec(
                executable,
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )
            stdout, stderr = await asyncio.wait_for(process.communicate(), self.config.timeout_s)
        except TimeoutError as exc:
            if process and process.returncode is None:
                process.kill()
                await process.wait()
            raise AlphaFoxExecutionError(f"AlphaFox {operation} outcome is uncertain after timeout") from exc
        except OSError as exc:
            raise AlphaFoxExecutionError(f"AlphaFox {operation} could not start") from exc
        try:
            raw = stdout if stdout.strip() else stderr
            envelope = json.loads(raw.decode("utf-8-sig"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise AlphaFoxExecutionError(f"AlphaFox {operation} returned invalid JSON") from exc
        if process.returncode != 0 or envelope.get("ok") is not True:
            error = envelope.get("error") or {}
            code = error.get("type") or error.get("code") or "ALPHAFOX_REJECTED"
            raise AlphaFoxExecutionError(f"AlphaFox {operation} failed: {code}")
        return envelope


__all__ = [
    "AlphaFoxCliAdapter",
    "AlphaFoxConfig",
    "AlphaFoxExecutionError",
    "build_create_payload",
]
