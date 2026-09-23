"""Generate an honest, submission-oriented report from one evidence run."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from .verify_evidence import verify_run


FLOW_ORDER = ("clarify", "spec_emit", "redline_hold", "redline_trip", "demo_inject")


def _jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def export_report(run: str | Path, *, live: bool = False) -> dict:
    root = Path(run)
    verified = verify_run(root, live=live)
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    calls = _jsonl(root / "calls.jsonl")
    chains = _jsonl(root / "chain.jsonl")
    events = _jsonl(root / "events.jsonl")
    buckets: dict[str, dict] = defaultdict(lambda: {"calls": 0, "tokens_in": 0, "tokens_out": 0, "latency_s": 0.0, "energy_Wh_est": 0.0, "sources": set()})
    for call in calls:
        row = buckets[str(call.get("flow", "unknown"))]
        row["calls"] += 1
        row["tokens_in"] += int(call.get("tokens_in", 0))
        row["tokens_out"] += int(call.get("tokens_out", 0))
        row["latency_s"] += float(call.get("latency_s", 0))
        row["energy_Wh_est"] += float(call.get("energy_Wh_est", 0))
        row["sources"].add(str(call.get("usage_source", "unknown")))
    flow_names = list(FLOW_ORDER) + sorted(set(buckets) - set(FLOW_ORDER))
    flows = []
    for name in flow_names:
        row = buckets[name]
        flows.append({
            "flow": name,
            "calls": row["calls"],
            "tokens_in": row["tokens_in"],
            "tokens_out": row["tokens_out"],
            "latency_s": round(row["latency_s"], 6),
            "energy_Wh_est": round(row["energy_Wh_est"], 6),
            "usage_source": next(iter(row["sources"])) if len(row["sources"]) == 1 else ("mixed" if row["sources"] else "none"),
        })
    txs = [
        {
            "action": row.get("action"),
            "tx_hash": row.get("tx_hash"),
            "chain_id": row.get("chain_id"),
            "contract_address": row.get("contract_address"),
            "block_number": row.get("receipt", {}).get("block_number"),
        }
        for row in chains
        if row.get("action") in {"mint_confirmed", "revoke_confirmed"}
    ]
    report = {
        "schema_version": 1,
        "run_id": manifest["run_id"],
        "evidence_class": "LIVE_SUBMISSION_EVIDENCE" if live else "OFFLINE_DEMO_ONLY",
        "verified": verified,
        "model": "gpt-oss-120b",
        "power_assumption_w": 180,
        "flows": flows,
        "transactions": txs,
        "timeline": [{"at": row.get("ts"), "kind": row.get("kind"), "passport_id": row.get("passport_id")} for row in events],
    }
    (root / "submission-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    banner = "LIVE SUBMISSION EVIDENCE" if live else "OFFLINE DEMO ONLY — NOT LIVE SUBMISSION EVIDENCE"
    lines = [
        f"# Evidence report: {report['run_id']}",
        "",
        f"> **{banner}**",
        "",
        "Model: `gpt-oss-120b`  ",
        "Power assumption: `180 W`; energy = `180 × latency / 3600`  ",
        "",
        "| flow | calls | tokens in | tokens out | latency s | energy Wh | source |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in flows:
        lines.append(f"| {row['flow']} | {row['calls']} | {row['tokens_in']} | {row['tokens_out']} | {row['latency_s']:.3f} | {row['energy_Wh_est']:.4f} | {row['usage_source']} |")
    lines.extend(["", "## Transactions", ""])
    if txs:
        lines.extend(["| action | chain | transaction | block | contract |", "|---|---:|---|---:|---|"])
        for tx in txs:
            lines.append(f"| {tx['action']} | {tx['chain_id']} | `{tx['tx_hash']}` | {tx['block_number']} | `{tx['contract_address']}` |")
    else:
        lines.append("No public-chain transaction is claimed for this run.")
    (root / "submission-report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report


__all__ = ["export_report"]
