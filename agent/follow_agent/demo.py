"""Demo entry point for the Follow Agent.

Run with:

    python -m agent.follow_agent.demo "follow leader-demo-001, 500 USD, stop if I lose 50"

The demo walks the user through:
    1. (optional) one round of clarification
    2. emit a frozen Spec
    3. print it as JSON

If no argument is given we use the PRD §4.1 demo defaults so the
demo is reproducible.
"""

from __future__ import annotations

import argparse
import json
import sys

from agent.follow_agent import Clarifier, Emitter, build_kiln_client, demo_default_spec
from agent.follow_agent.spec_schema import CopyTradingSpec


def _print_section(title: str) -> None:
    print(f"\n=== {title} ===")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the Follow Agent demo.")
    parser.add_argument(
        "intent",
        nargs="?",
        default="follow leader-demo-001 with 500 USD on paper, stop if I lose 50, valid for 48 hours",
        help="Natural-language intent in English, Korean or Chinese.",
    )
    parser.add_argument(
        "--emit-only",
        action="store_true",
        help="Skip clarification and go straight to spec_emit (uses PRD defaults).",
    )
    args = parser.parse_args(argv)

    client = build_kiln_client()

    _print_section("Follow Agent demo")
    print(f"intent: {args.intent}")

    if args.emit_only:
        spec = demo_default_spec()
        _print_section("Frozen Spec")
        print(spec.model_dump_json(indent=2))
        return 0

    clarifier = Clarifier(client)
    emitter = Emitter(client)
    emitter.add_user(args.intent)

    question = clarifier.first_question(args.intent)
    if question.field:
        _print_section(f"Clarification round {question.attempt}")
        print(f"  field:  {question.field}")
        print(f"  prompt: {question.question}")

        # For the offline demo we synthesize a plausible user answer
        # so the script is non-interactive. The real backend replaces
        # this with the actual user input.
        synthetic_answer = "leader-demo-001, 500 USD, stop if I lose 50, 48 hours"
        print(f"  (synthetic answer): {synthetic_answer}")
        emitter.add_user(synthetic_answer)
        nxt = clarifier.next_question(synthetic_answer, prior=question)
        if nxt is not None:
            print(f"  follow-up: {nxt.question}")

    try:
        spec: CopyTradingSpec = emitter.emit()
    except Exception as e:  # noqa: BLE001 -- demo: surface the type
        print(f"\nSpec emit FAILED: {type(e).__name__}: {e}", file=sys.stderr)
        return 1

    _print_section("Frozen Spec (validated)")
    print(json.dumps(json.loads(spec.model_dump_json()), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())