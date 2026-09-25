"""CLI for the read-only field preflight."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from backend.app.field_preflight import run_preflight


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate field readiness without sending a transaction.")
    parser.add_argument("--live", action="store_true", help="require live Kiln and public-testnet configuration")
    parser.add_argument("--network", action="store_true", help="perform read-only RPC chain/balance checks")
    parser.add_argument("--output", help="optional JSON output path")
    args = parser.parse_args()
    result = run_preflight(Path(__file__).resolve().parents[1], live=args.live, network=args.network)
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    print(rendered)
    if args.output:
        Path(args.output).write_text(rendered + "\n", encoding="utf-8")
    raise SystemExit(0 if result["configuration_ready"] else 2)
