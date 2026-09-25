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


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise EvidenceError(message)


def _valid_hash(value: object) -> bool:
    return isinstance(value, str) and re.fullmatch(r"0x[0-9a-fA-F]{64}", value) is not None


def _valid_address(value: object) -> bool:
    return isinstance(value, str) and re.fullmatch(r"0x[0-9a-fA-F]{40}", value) is not None


def verify_run(run: str | Path, live: bool = False) -> dict:
    root = Path(run)
    manifest = _json(root / "manifest.json")
    if not manifest.get("run_id") or manifest.get("source_mode") not in {"offline", "live"}:
        raise EvidenceError("invalid manifest")
    calls = _jsonl(root / "calls.jsonl")
    events = _jsonl(root / "events.jsonl")
    chains = _jsonl(root / "chain.jsonl")
    run_id = manifest["run_id"]
    for row in calls + events + chains:
        _require(row.get("run_id") == run_id, "evidence run_id mismatch")
    if live:
        _require(manifest["source_mode"] == "live", "live verification requires source_mode=live")
        intent = _json(root / "intent.json")
        _require(intent.get("run_id") == run_id, "intent run_id mismatch")
        _require(_valid_hash(intent.get("spec_hash")), "live run requires a valid intent hash")
        _require(bool(calls), "live run requires Kiln calls")
        call_ids: set[str] = set()
        for call in calls:
            _require(call.get("usage_source") == "api", "live run requires API usage")
            _require(call.get("model") == "gpt-oss-120b", "live run requires gpt-oss-120b calls")
            _require(isinstance(call.get("tokens_in"), int) and call["tokens_in"] > 0, "live call requires input tokens")
            _require(isinstance(call.get("tokens_out"), int) and call["tokens_out"] > 0, "live call requires output tokens")
            _require(isinstance(call.get("call_id"), str) and call["call_id"], "live call requires call_id")
            _require(call["call_id"] not in call_ids, "duplicate live call_id")
            call_ids.add(call["call_id"])
        confirmed = [c for c in chains if c.get("action") == "mint_confirmed"]
        _require(bool(confirmed), "live run requires confirmed mint transaction")
        mint = confirmed[-1]
        _require(_valid_hash(mint.get("tx_hash")), "live mint requires transaction hash")
        _require(mint.get("chain_id") in {1001, 11155111}, "live mint requires a public testnet")
        _require(_valid_address(mint.get("contract_address")), "live mint requires contract address")
        _require(mint.get("receipt", {}).get("status") == 1, "live mint requires successful receipt")
        _require(isinstance(mint.get("receipt", {}).get("block_number"), int), "live mint requires block number")
        _require(_valid_hash(mint.get("receipt", {}).get("block_hash")), "live mint requires block hash")
        mint_state = mint.get("state", {})
        _require(mint_state.get("spec_hash", "").lower() == intent["spec_hash"].lower(), "mint readback hash mismatch")
        _require(mint_state.get("status") == "active", "mint readback must be active")
        _require(mint_state.get("human_confirmed") is True, "mint readback requires confirmation")
        _require(_valid_address(mint_state.get("author")), "mint readback requires author")

        revoked = [c for c in chains if c.get("action") == "revoke_confirmed"]
        _require(bool(revoked), "live run requires confirmed revoke transaction")
        revoke = revoked[-1]
        _require(_valid_hash(revoke.get("tx_hash")), "live revoke requires transaction hash")
        _require(revoke.get("chain_id") == mint.get("chain_id"), "mint/revoke chain mismatch")
        _require(revoke.get("contract_address", "").lower() == mint["contract_address"].lower(), "mint/revoke contract mismatch")
        _require(revoke.get("chain_passport_id") == mint.get("chain_passport_id"), "mint/revoke passport mismatch")
        _require(revoke.get("receipt", {}).get("status") == 1, "live revoke requires successful receipt")
        _require(isinstance(revoke.get("receipt", {}).get("block_number"), int), "live revoke requires block number")
        _require(_valid_hash(revoke.get("receipt", {}).get("block_hash")), "live revoke requires block hash")
        _require(revoke.get("state", {}).get("status") == "revoked", "revoke readback must be revoked")
        _require(any(event.get("kind") == "engine_stop" for event in events), "live run requires engine stop log")
        _require(not any(event.get("kind") == "revoke_simulated" for event in events), "live run cannot contain simulated revoke evidence")
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
