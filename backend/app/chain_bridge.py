"""Line-delimited JSON bridge to the isolated Node chain worker."""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from uuid import uuid4


class ChainBridgeError(RuntimeError):
    pass


class ChainBridge:
    def __init__(self, root: Path | None = None, timeout: float = 15.0, mode: str = "local"):
        if mode not in {"local", "live"}:
            raise ValueError("chain bridge mode must be local or live")
        self.root = root or Path(__file__).resolve().parents[2] / "chain"
        self.timeout = timeout
        self.mode = mode
        self.process: asyncio.subprocess.Process | None = None
        self._lock = asyncio.Lock()

    async def start(self):
        if self.process and self.process.returncode is None:
            return
        allowed = ("PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP", "APPDATA", "LOCALAPPDATA", "USERPROFILE", "COMSPEC", "PATHEXT")
        if self.mode == "live":
            allowed += ("RPC_URL", "PRIVATE_KEY", "CHAIN_ID", "PASSPORT_ADDRESS", "TX_TIMEOUT_MS", "CHAIN_JOURNAL_DIR")
        env = {name: os.environ[name] for name in allowed if name in os.environ}
        env["CHAIN_MODE"] = self.mode
        self.process = await asyncio.create_subprocess_exec(
            "node", str(self.root / "src" / "worker.mjs"), cwd=self.root,
            stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE, env=env,
        )

    async def call(self, op: str, run_id: str, payload: dict, request_id: str | None = None):
        async with self._lock:
            await self.start()
            assert self.process and self.process.stdin and self.process.stdout
            if self.process.returncode is not None:
                raise ChainBridgeError("chain worker exited")
            request = {"protocol_version": 1, "request_id": request_id or str(uuid4()), "run_id": run_id, "op": op, "payload": payload}
            self.process.stdin.write((json.dumps(request, separators=(",", ":")) + "\n").encode())
            await self.process.stdin.drain()
            try:
                line = await asyncio.wait_for(self.process.stdout.readline(), self.timeout)
            except TimeoutError as exc:
                raise ChainBridgeError("chain worker response timeout; outcome uncertain") from exc
            if not line:
                diagnostic = ""
                if self.process.stderr:
                    diagnostic = (await self.process.stderr.read()).decode(errors="replace")[-500:]
                raise ChainBridgeError(f"chain worker closed protocol stream: {diagnostic}")
            response = json.loads(line)
            if response.get("request_id") != request["request_id"]:
                raise ChainBridgeError("chain worker response id mismatch")
            if response.get("status") in {"failed", "uncertain"}:
                raise ChainBridgeError(response.get("error_code", "chain operation failed"))
            return response

    async def close(self):
        if self.process and self.process.returncode is None:
            self.process.stdin.close()
            try:
                await asyncio.wait_for(self.process.wait(), 3)
            except TimeoutError:
                self.process.terminate()
                await self.process.wait()
        self.process = None


__all__ = ["ChainBridge", "ChainBridgeError"]
