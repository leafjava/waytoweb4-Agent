"""Fail-closed verifier for per-run evidence directories."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


class EvidenceError(ValueError):
    pass


def _json(path: Path):
    if not path.exists(): raise EvidenceError(f"missing {path.name}")
    return json.loads(path.read_text(encoding="utf-8"))


def _jsonl(path: Path):
    if not path.exists(): return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def verify_run(run: str | Path, live: bool = False) -> dict:
    root = Path(run)
    manifest = _json(root / "manifest.json")
    if not manifest.get("run_id") or manifest.get("source_mode") not in {"offline", "live"}:
        raise EvidenceError("invalid manifest")
    calls = _jsonl(root / "calls.jsonl")
    events = _jsonl(root / "events.jsonl")
    chains = _jsonl(root / "chain.jsonl")
    if live:
        if manifest["source_mode"] != "live": raise EvidenceError("live verification requires source_mode=live")
        if not calls or any(c.get("usage_source") != "api" or c.get("model") != "gpt-oss-120b" for c in calls):
            raise EvidenceError("live run requires API usage and gpt-oss-120b calls")
        confirmed = [c for c in chains if c.get("action") == "mint_confirmed"]
        if not confirmed or any(not re.fullmatch(r"0x[0-9a-fA-F]{64}", c.get("tx_hash", "")) for c in confirmed):
            raise EvidenceError("live run requires confirmed real transaction hashes")
        if not any(e.get("kind") in {"revoke", "revoke_confirmed", "revoke_simulated"} for e in events + chains):
            raise EvidenceError("live run requires stop/revoke evidence")
    result = {"run_id": manifest["run_id"], "calls": len(calls), "events": len(events), "chain_records": len(chains), "live": live, "ok": True}
    (root / "summary.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    try:
        print(json.dumps(verify_run(args.run, args.live), indent=2))
    except EvidenceError as exc:
        parser.error(str(exc))


if __name__ == "__main__": main()
