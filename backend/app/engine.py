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
# Serializes start_engine per passport: the gate checks run before the awaits
# that spawn the worker, so two concurrent first-starts would otherwise both
# pass and orphan a controller (found by the 2026-09-24 vulnerability scan).
_START_LOCKS: dict[str, asyncio.Lock] = {}


class EngineStartError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


class PaperWorkerController:
    def __init__(self, passport_id: str, state: AppState, backend, execution_adapter=None):
        self.passport_id = passport_id
        self.state = state
        self.backend = backend
        self.process: asyncio.subprocess.Process | None = None
        self.reader_task: asyncio.Task | None = None
        self.heartbeat_task: asyncio.Task | None = None
        self.ready = asyncio.Event()
        self.stopped = asyncio.Event()
        self.stopping = asyncio.Event()
        self.execution_adapter = execution_adapter
        self.external_stop_attempted = False
        self.external_stop_succeeded = False
        self.external_stop_failed = False

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
            if self.stopping.is_set() or self.stopped.is_set():
                return
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
        rec = self.state.passports.get(self.passport_id)
        if (
            self.execution_adapter
            and rec
            and rec.external_execution_id
            and not self.external_stop_attempted
        ):
            self.external_stop_attempted = True
            try:
                await self.execution_adapter.stop(rec.external_execution_id)
                self.external_stop_succeeded = True
                rec.external_execution_status = "stopped"
            except Exception:  # noqa: BLE001 - remote uncertainty must fail closed.
                self.external_stop_failed = True
                rec.external_execution_status = "uncertain"
                failed = True
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
        self.stopping.set()
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


async def start_engine(passport_id: str, state: AppState, trip_seconds: int, backend, execution_adapter=None) -> PassportRecord:
    rec = state.passports.get(passport_id)
    if rec is None: raise KeyError(passport_id)
    lock = _START_LOCKS.setdefault(passport_id, asyncio.Lock())
    async with lock:
        return await _start_engine_locked(passport_id, state, trip_seconds, backend, execution_adapter)


async def _start_engine_locked(passport_id: str, state: AppState, trip_seconds: int, backend, execution_adapter=None) -> PassportRecord:
    rec = state.passports.get(passport_id)
    if rec is None: raise KeyError(passport_id)
    if rec.authorization_status != "authorized" or rec.confirmed_spec_hash != rec.spec_hash:
        raise EngineStartError("PASSPORT_NOT_AUTHORIZED", f"passport {passport_id} is not authorized")
    if not rec.face_verified or rec.face_gate_status != "active":
        raise EngineStartError("FACE_GATE_REQUIRED", f"passport {passport_id} has not passed the human gate")
    if rec.stop_requested or is_expired(rec.expiry) or rec.engine_status in {"stopped", "stop_failed"}:
        raise EngineStartError("PASSPORT_STOPPED_OR_EXPIRED", f"passport {passport_id} is stopped or expired")
    if rec.engine_running: return rec
    controller = PaperWorkerController(passport_id, state, backend, execution_adapter)
    rec.engine_status = "starting"; rec.status = "starting"; state.upsert_passport(rec)
    await controller.start(rec)
    if execution_adapter:
        command = build_start_command(rec, str(state.ledger_path.parent / "policy.json"))
        try:
            rec.external_execution_id = await execution_adapter.start(command)
            rec.external_execution_provider = execution_adapter.provider
            rec.external_execution_status = "running"
            if controller.stopped.is_set() or rec.authorization_status != "authorized":
                await execution_adapter.stop(rec.external_execution_id)
                rec.external_execution_status = "stopped"
                raise RuntimeError("local safety controller stopped during external start")
        except Exception as exc:  # noqa: BLE001 - do not retry an uncertain mutation.
            await controller.force_terminate()
            external_stopped = rec.external_execution_status == "stopped"
            rec.engine_running = False
            rec.engine_status = "start_failed"
            rec.status = "stopped" if external_stopped else "uncertain"
            if not external_stopped or rec.authorization_status == "authorized":
                rec.authorization_status = "uncertain"
            rec.stop_requested = True
            rec.external_execution_provider = getattr(execution_adapter, "provider", "external")
            if not external_stopped:
                rec.external_execution_status = "uncertain"
            rec.stop_reason = "EXTERNAL_START_FAILED"
            rec.invalidate_face_gate("EXTERNAL_START_FAILED")
            state.upsert_passport(rec)
            raise EngineStartError("ALPHAFOX_START_FAILED", str(exc)) from exc
    _WORKERS[passport_id] = controller
    rec.engine_started_at = datetime.now(timezone.utc).isoformat(); rec.drawdown_usd = 0.0
    rec.engine_running = True; rec.engine_status = "running"; rec.status = "active"; rec.trip_seconds = trip_seconds
    rec.face_gate_status = "consumed"
    state.upsert_passport(rec)
    return rec


async def stop_engine(passport_id: str, state: AppState, backend, reason: str = "STOP_REQUESTED", execution_adapter=None) -> PassportRecord:
    rec = state.passports.get(passport_id)
    if rec is None: raise KeyError(passport_id)
    rec.stop_requested = True; state.upsert_passport(rec)
    controller = _WORKERS.pop(passport_id, None)
    if controller:
        await controller.stop(reason)
        rec = state.passports[passport_id]
        if execution_adapter and rec.external_execution_id and not controller.external_stop_attempted:
            controller.external_stop_attempted = True
            try:
                await execution_adapter.stop(rec.external_execution_id)
                controller.external_stop_succeeded = True
            except Exception:  # noqa: BLE001 - remote uncertainty must fail closed.
                controller.external_stop_failed = True
        if controller.external_stop_failed:
            rec.external_execution_status = "uncertain"
            rec.engine_status = "stop_failed"
            rec.status = "uncertain"
            state.upsert_passport(rec)
            raise EngineStartError("ALPHAFOX_STOP_FAILED", "AlphaFox stop outcome is uncertain")
        if execution_adapter and rec.external_execution_id:
            # Reconcile the public record after the stop coroutine completes.
            # The worker-reader and request tasks may both persist the record;
            # a successful idempotent stop always wins over an earlier
            # snapshot that still said ``running``.
            rec.external_execution_status = "stopped"
            state.upsert_passport(rec)
    else:
        if execution_adapter and rec.external_execution_id and rec.external_execution_status != "stopped":
            try:
                await execution_adapter.stop(rec.external_execution_id)
                rec.external_execution_status = "stopped"
            except Exception:  # noqa: BLE001
                rec.external_execution_status = "uncertain"
                rec.engine_status = "stop_failed"
                rec.status = "uncertain"
                state.upsert_passport(rec)
                raise EngineStartError("ALPHAFOX_STOP_FAILED", "AlphaFox stop outcome is uncertain")
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


__all__ = ["start_engine", "stop_engine", "tick_drawdown", "cancel_all", "run_judge", "PaperWorkerController", "EngineStartError"]
