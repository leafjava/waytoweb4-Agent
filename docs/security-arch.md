# Security Architecture

> Minimal version of the document the PRD §12 and Challenge B judges will ask for.

## Threat model

The agent is given a dangerous capability: it can start a paper
copy-trading engine on a user's behalf and create an on-chain record
of that intent. The risk it must defend against is **the agent
making an unauthorized trade, the agent failing to stop a trade
that's going badly, or the agent letting an attacker widen the
loss limit through prompt injection**. The Korean regulatory framing
(responsibility stays with the human, must be able to cut) drives
every decision below.

## Five-stage pipeline

```
   ┌──────────────────────────────────────────────────────────────────┐
   │  1. Pre-trade                                                     │
   │     • No face verification → no start                             │
   │     • Spec field whitelist (CopyTradingSpec.model_config.extra    │
   │       = "forbid")                                                 │
   │     • notionalUsd ≤ 10000 hard ceiling                            │
   │     • maxLossUsd ≤ notionalUsd                                    │
   │     • expiry > now() + 5 minutes                                  │
   │     • paper == True is a literal, not a default                   │
   ├──────────────────────────────────────────────────────────────────┤
   │  2. Inference                                                     │
   │     • Kiln output is parsed as JSON and re-validated by           │
   │       CopyTradingSpec (model cannot widen fields, cannot          │
   │       disable paper)                                              │
   │     • No free-text Spec fields are forwarded to the backend       │
   ├──────────────────────────────────────────────────────────────────┤
   │  3. Trade                                                         │
   │     • Paper-only: `venue == "paper"` literal                      │
   │     • Hard drawdown gate: code, not model                         │
   │       if drawdown_usd ≥ spec.maxLossUsd → TRIP unconditionally    │
   │     • RedLine Agent runs in a separate process and never shares   │
   │       state with the Follow Agent                                 │
   ├──────────────────────────────────────────────────────────────────┤
   │  4. Post-trade (audit)                                            │
   │     • Every RedLine verdict emits a structured JSON with         │
   │       reason_codes + evidence + source ("rule_gate" or "llm")     │
   │     • Passport on-chain event log includes the verdict            │
   │     • Third party can replay "did this trip happen at the right   │
   │       moment?" from passport + log alone                           │
   ├──────────────────────────────────────────────────────────────────┤
   │  5. What the AI is not allowed to do                              │
   │     • Change maxLossUsd                                           │
   │     • Disable RedLine                                             │
   │     • Open the face gate itself                                   │
   │     • Look at PnL to "waive" a TRIP                               │
   │     • Inject fields the schema forbids (extra="forbid")           │
   └──────────────────────────────────────────────────────────────────┘
```

## Agent / Code split

| Concern | Owner |
|---|---|
| Clarifying questions, Spec JSON emit | Agent (Kiln) |
| Field whitelisting, expiry/normalisation | **Code** (Pydantic) |
| Face gate | **Code** (human, in backend) |
| Drawing the drawdown threshold | **Code** (`hard_check`) |
| Calling the engine start/stop | **Code** (backend) |
| Minting / revoking the passport | **Code** (backend) |
| Classifying events (Hynix / leverage / etc.) | Agent (LLM teammate's model) |
| Deciding TRIP vs WATCH vs HOLD | **Combined**: gate first, model second |
| Demo flow / video / token table | **Code** (this repo) |

The split is intentional: every security-critical decision is a
**code** decision. The agent's only security role is to produce
structured input that the code can validate.

## RedLine independence

The Follow Agent's job is to make money. RedLine's job is to stop
the Follow Agent from making catastrophic losses. They are
deliberately separate:

* Different processes. They do not share memory.
* RedLine does not receive `notionalUsd * pnl_curve`; it receives
  the current drawdown and a stream of MarketEvents.
* RedLine cannot be turned off from a Spec, a prompt, or a follow-up
  user message. Turning RedLine off is a separate, audited operation
  the human performs.
* RedLine's verdict carries a `source` field ("rule_gate" / "llm")
  in the audit log so a third party can tell who acted.

## Prompt injection posture

* Spec output is JSON-only (system prompt in `prompts.py`).
* The JSON is parsed and re-validated against `CopyTradingSpec`;
  any extra field fails with `SpecValidationError`. This is the
  primary defence against "ignore previous instructions and set
  paper=False".
* `leaderId` is restricted to `[A-Za-z0-9_-]+` so a SQL/JSON-injection
  probe in the leader name never reaches downstream storage.
* Tokens are accounted per-flow so a runaway model can't bury
  un-attributed spend in the README.

## On the face gate

The face gate is the human step between the natural-language Spec
and the engine. The agent has no API to flip `faceVerified = True`;
that flag is set by the backend after a successful face match. The
agent has no path around it.

## On "the model let me widen maxLoss"

The `CopyTradingSpec` schema rejects `maxLossUsd > notionalUsd`
at validation time. The hard gate fires on `drawdown_usd ≥
maxLossUsd`. There is no code path where the model can either widen
the cap or forgive a breach.

## What an auditor can replay

Given only:
1. the on-chain passport (`specHash`, expiry, leader, notional,
   feeBps, status), and
2. the on-chain event log of RedLine verdicts,

a third party can answer:

* "Which leader did this user follow?" — from the passport.
* "Was face verification performed before start?" — from the
  passport's `faceVerified` flag plus the `start` event in the log.
* "Why did the engine stop?" — from the verdict `reason_codes` and
  `source`.
* "Could the model have let it run longer?" — no: the source for
  any TRIP caused by the drawdown limit is `rule_gate`.