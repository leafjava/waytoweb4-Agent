"""Hynix-style event injection for the Demo and the eval set.

This is the PRD §8 "one-click Hynix" button. The event pack is a
deterministic sequence of MarketEvents that -- when fed through the
RedLine judge -- produces a TRIP verdict without any real market data.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from agent.redline_agent.llm_classifier import MarketEvent

# Where the eval JSON lives. Relative to the repo root so the demo
# script can find it from any cwd.
DEFAULT_EVAL_PATH = Path(__file__).resolve().parents[2] / "docs" / "eval" / "hynix-cases.json"


def hynix_crash_pack() -> list[MarketEvent]:
    """The canonical 'hynix circuit breaker' pack used in demos.

    Three moves, each progressively worse:
      - Hynix -12% (single-stock drawdown)
      - 2x Hynix ETF -27% (leveraged amplification)
      - KOSPI 200 circuit breaker (index halt)

    When fed to the local keyword mock, the result is a TRIP verdict
    with reason_codes CB_LIKE + LEV_ETF_AMP. The hard gate is not
    involved (drawdown is structurally simulated by events).
    """
    ts = datetime.now(timezone.utc).isoformat()
    return [
        MarketEvent(symbol="000660.KS", change_pct=-12.0, kind="tick", timestamp=ts),
        MarketEvent(symbol="HIYS2X.KS", change_pct=-27.0, kind="leveraged_etf", timestamp=ts),
        MarketEvent(symbol="KS200", change_pct=-8.5, kind="circuit_breaker", timestamp=ts),
    ]


def events_to_json(events: Iterable[MarketEvent]) -> str:
    """Serialise events as JSON for logs / on-chain event payloads."""
    return json.dumps([asdict(e) for e in events], ensure_ascii=False)


def load_eval_cases(path: Path | str = DEFAULT_EVAL_PATH) -> list[dict]:
    """Load the hynix-cases.json eval set.

    The file is intentionally simple: a top-level object with
    `schema_version` / `description` and a `cases` list. Each case has
    `events` (a list of MarketEvent-shaped dicts) and `expected_level`
    (HOLD / WATCH / TRIP). Teammates use this to score their model.

    Returns an empty list if the file is missing. Returns just the
    `cases` list if it exists, even when the wrapper fields are
    absent (older files).
    """
    p = Path(path)
    if not p.exists():
        return []
    body = json.loads(p.read_text(encoding="utf-8"))
    if isinstance(body, list):
        return body
    if isinstance(body, dict):
        cases = body.get("cases", [])
        return list(cases) if isinstance(cases, list) else []
    return []


def write_default_eval_cases(path: Path | str = DEFAULT_EVAL_PATH) -> None:
    """Write a starter eval set if the file doesn't already exist.

    The seed is intentionally small (~10 cases) so it's obvious to
    read; the teammate is expected to grow it to the PRD's 30-50
    case target.
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.exists():
        return
    seed = {
        "schema_version": 1,
        "description": (
            "Hynix-style eval set. Each case has 'events' (one or more "
            "MarketEvent-shaped dicts) and 'expected_level' (HOLD/WATCH/"
            "TRIP). The judge should produce expected_level for every "
            "case when drawdown is below the spec limit."
        ),
        "cases": [
            {
                "id": "hynix_single_leg",
                "events": [
                    {"symbol": "000660.KS", "change_pct": -12.0, "kind": "tick"}
                ],
                "expected_level": "TRIP",
                "expected_codes": ["CB_LIKE"],
                "note": "Single Hynix leg down 12% counts as CB-grade.",
            },
            {
                "id": "lev_etf_only",
                "events": [
                    {"symbol": "HIYS2X.KS", "change_pct": -27.0, "kind": "leveraged_etf"}
                ],
                "expected_level": "TRIP",
                "expected_codes": ["LEV_ETF_AMP", "CB_LIKE"],
                "note": "Leveraged ETF triggers LEV_ETF_AMP + CB on threshold.",
            },
            {
                "id": "kospi_circuit",
                "events": [
                    {"symbol": "KS200", "change_pct": -8.5, "kind": "circuit_breaker"}
                ],
                "expected_level": "TRIP",
                "expected_codes": ["CB_LIKE"],
                "note": "Index circuit breaker text + 8% move.",
            },
            {
                "id": "small_dip",
                "events": [
                    {"symbol": "005930.KS", "change_pct": -1.5, "kind": "tick"}
                ],
                "expected_level": "HOLD",
                "expected_codes": [],
                "note": "Routine 1.5% Samsung move, no action.",
            },
            {
                "id": "moderate_lev",
                "events": [
                    {"symbol": "KODEX2X.KS", "change_pct": -5.0, "kind": "leveraged_etf"}
                ],
                "expected_level": "WATCH",
                "expected_codes": ["LEV_ETF_AMP"],
                "note": "Leveraged ETF at -5% is concerning but not CB-grade.",
            },
            {
                "id": "gap_pre_market",
                "events": [
                    {"symbol": "000660.KS", "change_pct": -3.0, "kind": "pre-market_gap"}
                ],
                "expected_level": "WATCH",
                "expected_codes": ["GAP_ORACLE"],
                "note": "Pre-market gap detected; tighten but don't stop.",
            },
            {
                "id": "cascade_text",
                "events": [
                    {"symbol": "KS200", "change_pct": -2.0, "kind": "liquidation_cascade"}
                ],
                "expected_level": "TRIP",
                "expected_codes": ["LIQ_CASCADE"],
                "note": "Liquidation cascade text + index moves.",
            },
            {
                "id": "human_override",
                "events": [
                    {"symbol": "005930.KS", "change_pct": 0.0, "kind": "human_kill"}
                ],
                "expected_level": "TRIP",
                "expected_codes": ["HUMAN_OVERRIDE"],
                "note": "Human override always trips regardless of PnL.",
            },
            {
                "id": "mixed_calm",
                "events": [
                    {"symbol": "005930.KS", "change_pct": 0.5, "kind": "tick"},
                    {"symbol": "000660.KS", "change_pct": -0.3, "kind": "tick"},
                ],
                "expected_level": "HOLD",
                "expected_codes": [],
                "note": "Two benign ticks.",
            },
            {
                "id": "lev_then_cb",
                "events": [
                    {"symbol": "HIYS2X.KS", "change_pct": -10.0, "kind": "leveraged_etf"},
                    {"symbol": "KS200", "change_pct": -8.0, "kind": "circuit_breaker"},
                ],
                "expected_level": "TRIP",
                "expected_codes": ["LEV_ETF_AMP", "CB_LIKE"],
                "note": "Leveraged ETF followed by index CB -> TRIP.",
            },
        ],
    }
    p.write_text(json.dumps(seed, ensure_ascii=False, indent=2), encoding="utf-8")


__all__ = [
    "hynix_crash_pack",
    "events_to_json",
    "load_eval_cases",
    "write_default_eval_cases",
    "DEFAULT_EVAL_PATH",
]