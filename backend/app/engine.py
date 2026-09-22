"""Controller for credential-free, fail-closed paper worker subprocesses."""

from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .authorization import AuthorizationError, authorization_service
from .audit import make_event
from .execution_contract import build_start_command
from .intent import is_expired
from .policy import write_policy
from .state import AppState, PassportRecord

_WORKERS: dict[str, "PaperWorkerController"] = {}


class PaperWorkerController:
    def __init__(self, passport_id: str, state: AppState, backend):
        self.passport_id = passport_id
        self.state = state
        self.backend = backend
        self.process: asyncio.subprocess.Process | None = None
        self.reader_task: asyncio.Task | None = None
        self.heartbeat_task: asyncio.Task | None = None
        self.ready = asyncio.Event()
        self.stopped = asyncio.Event()

    async def start(self, rec: PassportRecord):
        policy_path = self.state.ledger_path.parent / "policy.json"
        if not policy_path.exists():
            write_policy(policy_path, 1, [rec.leader_id])
        allowed = ("PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP", "PYTHONPATH")
        env = {k: os.environ[k] for k in allowed if k in os.environ}
        self.process = await asyncio.create_subprocess_exec(
            sys.executable, "-m", "backend.app.paper_worker_process",
            stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE, env=env,
        )
        self.reader_task = asyncio.create_task(self._read())
        command = build_start_command(rec, str(policy_path))
        await self._send({"op": "init", **command.model_dump(mode="json")})
        try:
            await asyncio.wait_for(self.ready.wait(), 2)
        except TimeoutError as exc:
            await self.force_terminate()
            raise RuntimeError("paper worker did not become ready") from exc
        self.heartbeat_task = asyncio.create_task(self._heartbeat())

    async def _send(self, value: dict):
        if not self.process or self.process.returncode is not None or not self.process.stdin:
            raise RuntimeError("paper worker is unavailable")
        self.process.stdin.write((json.dumps(value, separators=(",", ":")) + "\n").encode())
        await self.process.stdin.drain()

    async def _heartbeat(self):
        try:
            while not self.stopped.is_set():
                await self._send({"op": "heartbeat"})
                await asyncio.sleep(0.5)
        except Exception:
            await self._record_stop("CONTROLLER_HEARTBEAT_FAILED", failed=True)

    async def _read(self):
        assert self.process and self.process.stdout
        try:
            while line := await self.process.stdout.readline():
                event = json.loads(line)
                if event.get("kind") == "ready": self.ready.set()
                elif event.get("kind") == "tick": await self._record_tick(float(event["drawdown_usd"]))
                elif event.get("kind") == "stopped":
                    await self._record_stop(event.get("reason", "WORKER_STOPPED"), drawdown=event.get("drawdown_usd"))
                    break
        except Exception:
            await self._record_stop("WORKER_PROTOCOL_ERROR", failed=True)
        finally:
            self.stopped.set()

    async def _record_tick(self, amount: float):
        async with self.state._lock:
            rec = self.state.passports.get(self.passport_id)
            if rec:
                rec.drawdown_usd = amount
                self.state._save_locked()

    async def _record_stop(self, reason: str, drawdown=None, failed=False):
        should_log = False
        async with self.state._lock:
            rec = self.state.passports.get(self.passport_id)
            if rec:
                should_log = rec.engine_running or rec.engine_status not in {"stopped", "stop_failed"}
                if drawdown is not None: rec.drawdown_usd = float(drawdown)
                rec.stop_requested = True
                rec.engine_running = False
                rec.engine_status = "stop_failed" if failed else "stopped"
                if rec.authorization_status not in {"revoked", "uncertain"}:
                    rec.status = rec.engine_status
                rec.stop_reason = reason
                self.state._save_locked()
        try:
            await authorization_service.revoke(self.state, self.passport_id, self.backend, reason)
        except (AuthorizationError, KeyError):
            # The authorization service has already persisted an uncertain
            # outcome. The worker must remain stopped even when chain status
            # cannot be confirmed.
            pass
        if should_log:
            self.state.append_event(make_event(
                "engine_stop", self.passport_id,
                {"reason": reason, "drawdown_usd": drawdown, "failed": failed},
            ))

    async def tick(self, amount: float):
        await self._send({"op": "tick", "amount": amount})
        for _ in range(20):
            await asyncio.sleep(0.02)
            rec = self.state.passports[self.passport_id]
            if rec.drawdown_usd == amount or rec.engine_status != "running": return rec
        return self.state.passports[self.passport_id]

    async def stop(self, reason="STOP_REQUESTED"):
        if self.process and self.process.returncode is None:
            try: await self._send({"op": "stop", "reason": reason})
            except Exception: pass
            try: await asyncio.wait_for(self.stopped.wait(), 2)
            except TimeoutError: await self.force_terminate()
        await self._record_stop(reason)

    async def force_terminate(self):
        if self.process and self.process.returncode is None:
            self.process.kill()
            await self.process.wait()
        self.stopped.set()

    async def close(self):
        if self.heartbeat_task: self.heartbeat_task.cancel()
        await self.stop("CONTROLLER_SHUTDOWN")
        if self.reader_task:
            try: await self.reader_task
            except (asyncio.CancelledError, Exception): pass


async def start_engine(passport_id: str, state: AppState, trip_seconds: int, backend) -> PassportRecord:
    rec = state.passports.get(passport_id)
    if rec is None: raise KeyError(passport_id)
    if rec.authorization_status != "authorized" or rec.confirmed_spec_hash != rec.spec_hash:
        raise ValueError(f"passport {passport_id} is not authorized")
    if not rec.face_verified:
        raise ValueError(f"passport {passport_id} has not passed the face gate")
    if rec.stop_requested or is_expired(rec.expiry) or rec.engine_status in {"stopped", "stop_failed"}:
        raise ValueError(f"passport {passport_id} is stopped or expired")
    if rec.engine_running: return rec
    controller = PaperWorkerController(passport_id, state, backend)
    rec.engine_status = "starting"; rec.status = "starting"; state.upsert_passport(rec)
    await controller.start(rec)
    _WORKERS[passport_id] = controller
    rec.engine_started_at = datetime.now(timezone.utc).isoformat(); rec.drawdown_usd = 0.0
    rec.engine_running = True; rec.engine_status = "running"; rec.status = "active"; rec.trip_seconds = trip_seconds
    state.upsert_passport(rec)
    return rec


async def stop_engine(passport_id: str, state: AppState, backend, reason: str = "STOP_REQUESTED") -> PassportRecord:
    rec = state.passports.get(passport_id)
    if rec is None: raise KeyError(passport_id)
    rec.stop_requested = True; state.upsert_passport(rec)
    controller = _WORKERS.pop(passport_id, None)
    if controller: await controller.stop(reason)
    else:
        rec.engine_running = False; rec.engine_status = "stopped"; rec.status = "stopped"; rec.stop_reason = rec.stop_reason or reason; state.upsert_passport(rec)
    rec, _, _ = await authorization_service.revoke(state, passport_id, backend, reason)
    return rec


async def tick_drawdown(passport_id: str, amount_usd: float, state: AppState) -> PassportRecord:
    if not isinstance(amount_usd, (int, float)) or amount_usd < 0: raise ValueError("invalid drawdown")
    controller = _WORKERS.get(passport_id)
    if not controller: raise ValueError("paper worker is not running")
    return await controller.tick(float(amount_usd))


async def cancel_all() -> None:
    controllers = list(_WORKERS.values()); _WORKERS.clear()
    await asyncio.gather(*(c.close() for c in controllers), return_exceptions=True)


def run_judge(spec: dict[str, Any], drawdown_usd: float, events: list[Any] | None, judge):
    from agent.follow_agent.spec_schema import CopyTradingSpec
    return judge.judge(CopyTradingSpec.model_validate(spec), drawdown_usd, events or [])


__all__ = ["start_engine", "stop_engine", "tick_drawdown", "cancel_all", "run_judge", "PaperWorkerController"]
