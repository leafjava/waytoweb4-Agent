"""Tests for the event injector and eval set helpers."""

from __future__ import annotations

import json
from pathlib import Path

from agent.redline_agent import (
    DEFAULT_EVAL_PATH,
    HynixMockClassifier,
    RedLineJudge,
    events_to_json,
    hynix_crash_pack,
    load_eval_cases,
    write_default_eval_cases,
)
from agent.redline_agent.schema import RedLineLevel


def test_hynix_pack_trips_judge() -> None:
    spec = __import__(
        "agent.follow_agent.spec_schema", fromlist=["demo_default_spec"]
    ).demo_default_spec()
    j = RedLineJudge(classifier=HynixMockClassifier())
    v = j.judge(spec, drawdown_usd=10.0, events=hynix_crash_pack())
    assert v.level == RedLineLevel.TRIP


def test_events_to_json_is_valid_json() -> None:
    s = events_to_json(hynix_crash_pack())
    parsed = json.loads(s)
    assert isinstance(parsed, list)
    assert all("symbol" in p for p in parsed)


def test_write_default_eval_cases_creates_file(tmp_path: Path) -> None:
    target = tmp_path / "hynix-cases.json"
    write_default_eval_cases(target)
    assert target.exists()
    data = json.loads(target.read_text(encoding="utf-8"))
    assert "cases" in data
    assert len(data["cases"]) >= 5


def test_write_default_eval_cases_is_idempotent(tmp_path: Path) -> None:
    target = tmp_path / "hynix-cases.json"
    write_default_eval_cases(target)
    first = target.read_text(encoding="utf-8")
    write_default_eval_cases(target)
    second = target.read_text(encoding="utf-8")
    assert first == second


def test_load_eval_cases_handles_missing(tmp_path: Path) -> None:
    assert load_eval_cases(tmp_path / "missing.json") == []


def test_eval_cases_judge_correctly(tmp_path: Path) -> None:
    """End-to-end: write the seed, load it, run the judge on every
    case, and assert the level matches the expectation. This is the
    '≥90% hit rate' smoke test from the PRD plan."""
    target = tmp_path / "hynix-cases.json"
    write_default_eval_cases(target)
    cases = load_eval_cases(target)
    spec = __import__(
        "agent.follow_agent.spec_schema", fromlist=["demo_default_spec"]
    ).demo_default_spec()
    j = RedLineJudge(classifier=HynixMockClassifier())
    passed = 0
    for case in cases:
        events = [MarketEvent(**e) for e in case["events"]]
        v = j.judge(spec, drawdown_usd=10.0, events=events)
        if v.level.value == case["expected_level"]:
            passed += 1
    hit_rate = passed / max(len(cases), 1)
    assert hit_rate >= 0.9, f"hit_rate={hit_rate} on {len(cases)} cases"


# Late import for the helper used above -- avoids polluting module
# scope with a name we don't actually need at top level.
from agent.redline_agent.llm_classifier import MarketEvent  # noqa: E402