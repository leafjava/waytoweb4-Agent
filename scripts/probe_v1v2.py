"""One-shot dynamic re-verification of the V1/V2 vulnerability fixes."""
import asyncio
import json
import os
import sys
import urllib.request
import uuid

BASE = os.environ.get("PROBE_BASE", "http://127.0.0.1:8127")
SPEC = {
    "mode": "copy", "leaderId": "leader-demo-001", "venue": "paper",
    "notionalUsd": 500, "maxLossUsd": 50, "expiry": "2099-01-01T00:00:00Z", "paper": True,
}

def call(path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method="POST" if body is not None else "GET",
                                 headers={"content-type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")

async def main():
    code, rec = call("/api/passport/prepare", {"request_id": "x1", "spec": SPEC})
    assert code == 200, (code, rec)
    pid = rec["passport_id"]
    sh = rec["spec_hash"]

    # V2: stop an unauthorized (prepared) passport must now be refused.
    # Use a throwaway passport: a refused stop still records stop_requested
    # (fail-safe intent flag), which would block this mandate's own confirm.
    code, throwaway = call("/api/passport/prepare", {"request_id": "v2-throwaway", "spec": {**SPEC, "leaderId": "leader-demo-002"}})
    assert code == 200, (code, "throwaway prepare")
    code, body = call("/api/engine/stop", {"passport_id": throwaway["passport_id"]})
    print("V2 unauthorized stop ->", code, body.get("detail") if isinstance(body.get("detail"), str) else body)
    assert code == 409, "V2 fix failed"

    code, _ = call("/api/passport/confirm", {"passport_id": pid, "spec_hash": sh, "request_id": "x2"})
    assert code == 200, (code, "confirm", _)
    code, _ = call("/api/passport/mint", {"passport_id": pid, "request_id": "x3"})
    assert code == 200, (code, "mint")
    code, _ = call("/api/face/verify", {"passport_id": pid, "method": "button", "session_id": str(uuid.uuid4())})
    assert code == 200, (code, "face")

    # V1: concurrent first starts — exactly one must win, one worker spawned.
    async def start():
        return await asyncio.to_thread(call, "/api/engine/start", {"passport_id": pid})
    results = await asyncio.gather(*(start() for _ in range(5)))
    codes = [c for c, _ in results]
    ok = [c for c in codes if c == 200]
    rejected = [ (c, b) for c, b in results if c != 200 ]
    print("V1 concurrent starts ->", codes)
    for c, b in rejected:
        d = b.get("detail")
        print("   rejected:", c, d.get("code") if isinstance(d, dict) else d)
    assert len(ok) == 1, f"expected exactly one 200, got {codes}"

    code, snap = call("/api/state")
    p = snap["passports"][pid]
    print("final: engine_running=%s engine_status=%s" % (p["engine_running"], p["engine_status"]))
    assert p["engine_status"] == "running", p["engine_status"]

    code, _ = call("/api/engine/stop", {"passport_id": pid})
    assert code == 200, (code, "cleanup stop")
    print("PASS: exactly one concurrent start won; unauthorized stop refused; cleanup ok")

asyncio.run(main())
