"""Credential-free paper worker with independent hard-stop checks."""

from __future__ import annotations

import json
import math
import queue
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path


def emit(kind: str, **payload):
    print(json.dumps({"kind": kind, **payload}, separators=(",", ":")), flush=True)


def reader(commands: queue.Queue):
    for line in sys.stdin:
        try:
            commands.put(json.loads(line))
        except Exception:
            commands.put({"op": "invalid"})
    commands.put({"op": "disconnect"})


def load_policy(path: Path):
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value.get("version"), int) or not isinstance(value.get("allowed_leaders"), list):
        raise ValueError("invalid policy")
    return value


def main():
    commands: queue.Queue = queue.Queue()
    threading.Thread(target=reader, args=(commands,), daemon=True).start()
    config = commands.get(timeout=5)
    if config.get("op") != "init":
        emit("stopped", reason="INIT_REQUIRED"); return 2
    leader = config["leader_id"]
    max_loss = float(config["max_loss_usd"])
    expiry = datetime.fromisoformat(config["expiry"].replace("Z", "+00:00")).astimezone(timezone.utc)
    policy_path = Path(config["policy_path"])
    lease_s = float(config.get("lease_s", 3.0))
    last_heartbeat = time.monotonic()
    drawdown = 0.0
    emit("ready")
    while True:
        while True:
            try: command = commands.get_nowait()
            except queue.Empty: break
            op = command.get("op")
            if op == "heartbeat": last_heartbeat = time.monotonic(); emit("heartbeat_ack")
            elif op == "tick":
                try:
                    value = float(command["amount"])
                    if not math.isfinite(value) or value < 0: raise ValueError
                    drawdown = value; emit("tick", drawdown_usd=drawdown)
                except Exception: emit("stopped", reason="INVALID_MARKET_INPUT", drawdown_usd=drawdown); return 0
            elif op == "stop": emit("stopped", reason=command.get("reason", "STOP_REQUESTED"), drawdown_usd=drawdown); return 0
            elif op in {"disconnect", "invalid"}: emit("stopped", reason="CONTROLLER_DISCONNECTED", drawdown_usd=drawdown); return 0
        if time.monotonic() - last_heartbeat > lease_s:
            emit("stopped", reason="CONTROLLER_LEASE_EXPIRED", drawdown_usd=drawdown); return 0
        if datetime.now(timezone.utc) >= expiry:
            emit("stopped", reason="EXPIRY", drawdown_usd=drawdown); return 0
        try:
            policy = load_policy(policy_path)
            if leader not in policy["allowed_leaders"]:
                emit("stopped", reason="POLICY_REVOKED", policy_version=policy["version"], drawdown_usd=drawdown); return 0
        except Exception:
            emit("stopped", reason="POLICY_INVALID", drawdown_usd=drawdown); return 0
        if drawdown >= max_loss:
            emit("stopped", reason="DD_LIMIT", drawdown_usd=drawdown); return 0
        time.sleep(0.1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
