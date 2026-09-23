# `agent/` — Follow Agent + RedLine Agent

This directory contains the two agents that participate in the
waytoweb4 copy-trading flow. Everything in here is a Python library
the backend imports; it has no opinion about HTTP frameworks,
storage, or blockchain clients.

## Layout

```
agent/
├── follow_agent/      # NL → Spec
│   ├── spec_schema.py     Locked CopyTradingSpec (Pydantic v2)
│   ├── kiln_client.py     Kiln API client + deterministic mock
│   ├── prompts.py         System prompts for clarify / spec_emit
│   ├── clarifier.py       Clarifier + Emitter
│   └── demo.py            `python -m agent.follow_agent.demo`
├── redline_agent/     # Independent kill switch
│   ├── schema.py          RedLineVerdict (PRD §4.4)
│   ├── rule_gate.py       Drawdown hard gate (PRD §12)
│   ├── llm_classifier.py  EventClassifier Protocol + keyword mock
│   ├── judge.py           RedLineJudge: gate first, LLM second
│   ├── event_injector.py  Hynix crash pack + eval set helpers
│   └── demo.py            `python -m agent.redline_agent.demo`
├── shared/            # Types and infra shared by both agents
│   ├── types.py           ReasonCode, PassportRef
│   ├── exceptions.py      AgentError hierarchy
│   ├── energy.py          180W assumption, Wh estimator
│   └── token_logger.py    Per-flow token / latency / energy logger
└── tests/             # pytest
```

## Install

```bash
cd waytoweb4-agent
python -m pip install -e agent[dev]
```

## Run the demos

Both demos run with the mock Kiln client by default (no API key
needed), so they work offline.

```bash
# Follow Agent: clarify + emit a frozen Spec
python -m agent.follow_agent.demo "follow leader-demo-001 with 500 USD, stop if I lose 50, 48h"

# Follow Agent: emit-only (PRD defaults, no clarification)
python -m agent.follow_agent.demo --emit-only

# RedLine Agent: hard gate + Hynix event injection -> TRIP
python -m agent.redline_agent.demo

# RedLine Agent: drive the gate directly
python -m agent.redline_agent.demo --drawdown 75.0
```

## Run the tests

```bash
cd waytoweb4-agent
python -m pytest agent/tests -v
```

The tests cover:

* `test_spec_schema.py` — Spec whitelist and the model-cannot-
  widen-fields guarantees.
* `test_kiln_client_mock.py` — Mock client behaviour and the
  factory's HTTP-vs-mock selection.
* `test_clarifier.py` — Multi-round Q&A and emitter validation.
* `test_rule_gate.py` — Drawdown threshold and the model-cannot-
  override-hard-limit guard.
* `test_judge.py` — Hard gate precedence (rule fires, LLM never
  called) and the LLM-only path.
* `test_event_injector.py` — Eval-set round-trip and ≥90% hit rate.
* `test_token_logger.py` — Per-flow buckets and the PRD §9 table.

## Use the real Kiln API

Set the environment variables before importing:

```bash
export KILN_API_KEY="your-key"
export KILN_API_BASE="https://api.kiln.ai/v1"   # default
export KILN_MODEL="gpt-oss-120b"                 # default
```

The factory in `kiln_client.build_kiln_client()` will pick
`HttpKilnClient` automatically. If the key is missing (or the
network is down at the venue), the mock client is used so the demo
keeps moving.

## Plug in the risk-control model

The LLaMA teammate's classifier just needs to satisfy the
`EventClassifier` Protocol:

```python
from agent.redline_agent import EventClassifier, MarketEvent, RedLineVerdict

class MyRiskModel:
    def classify(self, events):
        # ...your model logic here...
        return RedLineVerdict(
            level=RedLineLevel.TRIP,
            reason_codes=[ReasonCode.CB_LIKE],
            evidence=["..."],
            action=RedLineAction.STOP_AND_REVOKE,
            model_may_override_hard_limit=False,  # must stay False
            source="llm",
        )

judge = RedLineJudge(classifier=MyRiskModel())
```

The hard rule gate still runs first; your model is only consulted
when the gate defers. `model_may_override_hard_limit=True` is
rejected at construction time (`UnauthorizedOverrideError`) so a
buggy wrapper can't smuggle the flag through.

## Token / energy table for the README

After running the demo:

```python
from agent.shared.token_logger import get_default_logger
print(get_default_logger().report())
```

This prints the PRD §9 markdown table. Paste it into the top-level
README verbatim.