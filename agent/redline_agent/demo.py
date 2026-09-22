"""Demo entry point for the RedLine Agent.

Run with:

    python -m agent.redline_agent.demo
    python -m agent.redline_agent.demo --inject hynix
    python -m agent.redline_agent.demo --drawdown 50.0   # should TRIP via hard gate

Walks the user through:
    1. start with the PRD demo default Spec
    2. apply the hard gate (drawdown)
    3. (optional) feed the hynix crash pack into the LLM classifier
    4. print the final RedLineVerdict
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from datetime import datetime, timezone

from agent.follow_agent.spec_schema import demo_default_spec
from agent.redline_agent import (
    HynixMockClassifier,
    MarketEvent,
    RedLineJudge,
    hynix_crash_pack,
)
from agent.redline_agent.schema import RedLineLevel
from agent.shared.token_logger import get_default_logger


def _verdict_to_dict(v) -> dict:
    return {
        "level": v.level.value,
        "reason_codes": [c.value for c in v.reason_codes],
        "evidence": v.evidence,
        "action": v.action.value,
        "source": v.source,
        "model_may_override_hard_limit": v.model_may_override_hard_limit,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the RedLine Agent demo.")
    parser.add_argument(
        "--inject",
        choices=("hynix", "none"),
        default="hynix",
        help="Which event pack to feed into the LLM classifier.",
    )
    parser.add_argument(
        "--drawdown",
        type=float,
        default=20.0,
        help="Drawdown in USD to feed into the hard rule gate. "
        "PRD default Spec has maxLossUsd=50, so 50+ trips the gate.",
    )
    args = parser.parse_args(argv)

    spec = demo_default_spec()
    print(f"Spec: leaderId={spec.leaderId}, notional={spec.notionalUsd}, "
          f"maxLoss={spec.maxLossUsd}, drawdown_arg={args.drawdown}")

    events: list[MarketEvent]
    if args.inject == "hynix":
        events = hynix_crash_pack()
        print(f"Injected {len(events)} Hynix events")
    else:
        events = []

    judge = RedLineJudge(classifier=HynixMockClassifier())
    verdict = judge.judge(spec, args.drawdown, events)

    print("\nRedLine verdict:")
    print(json.dumps(_verdict_to_dict(verdict), indent=2, ensure_ascii=False))

    # Demonstrate that we can use the verdict downstream.
    if verdict.level == RedLineLevel.TRIP:
        print("\n>> Action: stop the engine and revoke the passport.")
    elif verdict.level == RedLineLevel.WATCH:
        print("\n>> Action: tighten (reduce position size, raise alerts).")
    else:
        print("\n>> Action: no change.")

    print("\nToken usage so far:")
    print(get_default_logger().report())

    return 0


if __name__ == "__main__":
    raise SystemExit(main())