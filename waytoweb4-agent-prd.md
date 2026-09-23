# waytoweb4 Agent PRD

**Agent-activated copy-trading · Strategy Passport on-chain · RedLine one-vote veto**  
GWDC 2026 Korea · FuriosaAI × Bricksum · Challenge A  
(RedLine also covers Challenge B's "stoppable and auditable" bonus criteria)

Version: 2026-09-22  
Status: ready to build  
Collaborators: waytoweb4 (execution layer) / the competing team (activation layer, passport, kill switch, Demo)

---

## 0. The One Sentence the README Must State Verbatim (Official Acceptance)

> We built a **copy-trading authorization agent**: natural language produces a locked Spec, a human face-gate starts Paper copy-trading via waytoweb4, the Spec is minted as a revocable on-chain Strategy Passport, and a separate RedLine agent can halt the engine and burn the passport without looking at PnL.

Judges score against the function you declare, not against a feature checklist. Put this sentence in the first paragraph of the README.

---

## 1. The Product in One Sentence

The user configures and launches copy-trading in natural language (a single strategy, or a weighted combination of two passports) → the face gate opens → the Spec is minted as an on-chain Strategy Passport → execution runs through waytoweb4 (strategies and order placement are not rewritten) → no matter how high the returns go, the independent RedLine can still trip the kill switch and revoke the passport.

---

## 2. Why We Build This (Aligned with the Official Brief + Korean Context)

### 2.1 Key Points of the FuriosaAI × Bricksum Challenge A Brief

Official prompt: Build a Financial Service Powered by AI Agents and Blockchain.

You must do all of the following at once:

1. **User need and workflow**: state clearly who the service is for and what problem it solves; demonstrate a working path from input to result; mark which part is the Agent and which part is code.
2. **Kiln API + energy efficiency**: the Agent must go through the **NPU-based Kiln API with the `gpt-oss-120b` model**. There must be real API calls, and the call results must affect decisions. Tokens must be **reported broken down by flow**, not as one total. Power draw may be measured or the **assumption must be stated clearly** (for this event, estimating at 180W is sufficient; actually measuring the chip is forbidden).
3. **Chain**: at least **1 on-chain transaction** end-to-end on devnet/testnet (payment / settlement / record write), submitting the **tx hash + corresponding logs**. State clearly what the Agent read, what it wrote, and what it settled.
4. **Declared function**: the one-sentence README declaration (see Section 0).
5. **Conditional comparison runs**: run the same flow twice, changing the user conditions (smaller allowance, a disallowed Leader/merchant, expired validity). Out-of-scope actions must be stopped, and a record must be left.

Official Brief:  
https://docs.google.com/document/d/13qh7oePGl7Flrl-Zh_A6hfr02L266PvS/edit

### 2.2 Why Copy-Trading Hits Challenge A and RedLine Also Hits Challenge B

- Challenge A wants a financial Agent for "subscription, payment, and asset management on a user's behalf". Copy-trading = delegated asset management.
- The Korean regulatory narrative: responsibility rests with humans, and there must be a way to cut off. The prototype must be **Paper-only, revocable, and kill-switchable**.
- Challenge B asks: where is the boundary enforced, does it stop when pushed past the boundary, and can a third party reconstruct "was it allowed at the time" from the records alone. RedLine + the passport is exactly that.
- Configuring combination weights in natural language is lighter than configuring them on a web page, and fits a 3-minute Demo.

### 2.3 On-Site Constraints at GWDC

| Item | Content |
|---|---|
| Event | GWDC Hackathon 2026 Korea |
| Venue | aT Center, Seoul (Seocho, Gangnam-daero 27) |
| Kickoff | 9/28 17:00–20:00 KST |
| Coding | 9/28 20:00 – 9/30 11:00 KST |
| Submission deadline | **9/30 12:00 KST** |
| Demo Day | 9/30 15:00–17:00 KST, Innovation Stage |
| Deliverables | Public GitHub, ≤3-minute Demo video, project materials, Pitch Deck |
| Prize pool | $100K+ USD overall (ecosystem tracks counted separately) |
| Website | https://www.gwdc.net / https://wap.gwdc.net/hackathon.html |
| Luma | https://luma.com/be2le0l0 |
| TG | https://t.me/GWDC_Global |

In 3 minutes the judges must see: **the paperwork completed + the passport opens on-chain + a Kiln call actually happened + tokens broken down by flow**.

---

## 3. System Architecture

```
The user speaks
  → Follow Agent (Kiln / gpt-oss-120b) produces a Spec or weights
  → Face gate opens (a human, not the model)
  → waytoweb4 executes Paper copy-trading (start/stop)
  → Strategy Passport goes on-chain (specHash, revocable, verified)
  → RedLine Agent issues an independent verdict HOLD/WATCH/TRIP
       TRIP → stop the engine + revoke the passport
```

Hard rules:

- The money-making Agent and the money-stopping Agent are **separate**.
- RedLine **never looks at returns**.
- Natural language can only configure the Spec; it **cannot change the loss limit and cannot turn off RedLine**.
- The model has no authority to start live/paper trading; only after the face gate does the code call `start`.

---

## 4. Object Model

### 4.1 Spec (copy-trading intent, locked)

| Field | Description | Demo default |
|---|---|---|
| mode | Only plain copy-trading allowed | `copy` |
| leaderId | Leaders eligible for copying | A waytoweb4 Leader confirmed on site |
| venue | Paper only | `paper` |
| notionalUsd | Allowance | `500` |
| maxLossUsd | Loss limit | `50` |
| expiry | Validity period | 48h |
| faceVerified | Face verified | `false`→`true` |
| paper | Fixed to true | `true` |

Forbidden: new strategy types, in-house grid trading, backtest factories.

### 4.2 Strategy Passport (on-chain authorization unit)

```
passportId
specHash
author
leaderId
notionalUsd
feeBps
expiry
revocable = true
faceVerified
status = active | revoked
```

The chain's job: store authorization and status; it does not run market data.

### 4.3 Basket Passport (only if there is spare capacity)

```
[{ passportId, bps }] + basketMaxLossUsd
```

What you assemble is other people's permissions; you do not invent industry factors. If waytoweb4 has not opened up combination templates: two plain copy-trading lanes + an on-chain Basket.

### 4.4 RedLine Verdict (structured; this is where the model teammate plugs in)

Only the following is allowed:

```json
{
  "level": "HOLD | WATCH | TRIP",
  "reason_codes": ["DD_LIMIT"],
  "evidence": ["drawdownUsd=50"],
  "action": "none | tighten | stop_and_revoke",
  "model_may_override_hard_limit": false
}
```

Reason codes:

| code | Meaning |
|---|---|
| DD_LIMIT | Drawdown hits the Spec loss limit → **rules force TRIP**; the model has no authority to let it pass |
| CB_LIKE | Circuit-breaker-level index/sector shock (SK Hynix/KOSPI style) |
| LEV_ETF_AMP | Amplification by 2x/leveraged products |
| LIQ_CASCADE | Liquidation cascade |
| GAP_ORACLE | Thin liquidity / abnormal pre-market prices |
| HUMAN_OVERRIDE | Face/human one-vote veto |

Rules take priority:

```
if drawdown >= spec.maxLossUsd → TRIP
else the model only scores "is this a structural shock"
if TRIP → waytoweb4.stop + passport.revoke
```

---

## 5. Official Acceptance Mapping (follow this and you won't drift off track)

| Official clause | How we deliver |
|---|---|
| User Need | Retail users/judges: want to delegate copy-trading in natural language, but fear that once the Agent trades on their behalf it cannot be cut off |
| Agent vs Code | Agent: clarification + producing the Spec + RedLine classification. Code: validating the Spec, the face gate, start/stop, minting/burning the passport, the hard loss-limit gate |
| Kiln `gpt-oss-120b` | Follow's multi-turn clarification and RedLine's event classification must hit the real API |
| Tokens by flow | See §9: clarify / spec / redline_hold / redline_trip / demo_inject |
| Energy | `energyWh ≈ tokens × 180W × latencySec / 3600`, with the assumption written into the README |
| At least 1 on-chain tx | Mint the Passport; on TRIP send a revoke tx as well. Submit the hashes |
| Two conditional comparison runs | Run1: 500U / stop at a 50 loss. Run2: change the allowance to 100U or inject the Hynix circuit-breaker pack. Both runs leave logs |
| Out-of-scope actions are stopped | Loss-limit breach, disallowed Leader, expiry, RedLine-injected event → stop and record |
| Third-party auditability | From the passport + logs alone, one can answer: who is copied, the allowance, whether the face gate passed, why it stopped |

Challenge B bonus points (no need to switch tracks, but say it in the Demo):

- Where the boundary lives: hardcoded Spec + contract status + RedLine
- The two runs pushed past the boundary
- Another person can reconstruct it from the records alone

---

## 6. 48-Hour Scope

### Must-do (without these, don't take the stage)

- [ ] A conversation produces a valid Spec
- [ ] `start` only after the face gate
- [ ] Mint **one** Strategy Passport that opens in a browser
- [ ] waytoweb4 paper trading running
- [ ] RedLine can stop and `revoke`
- [ ] Real Kiln calls + a per-flow token table
- [ ] Two controlled comparison runs + logs
- [ ] The one-sentence README function declaration + tx hash

### If there is spare capacity

- [ ] Two passports + weights
- [ ] A second address copies using the passport
- [ ] The confirmation card shows this order's tokens
- [ ] A "one-click Hynix" event injection button

### Explicitly not doing

New strategy types, backtest factories, candlestick charts, real Binance KYC, a spending ledger, actually measuring chip power draw, war-scenario models, a profit-splitting marketplace, letting the model look at returns to grant an approval.

---

## 7. Demo Script (3 minutes)

1. "Copy this one, 500 U, paper trading, stop at a 50 loss"  
2. Configuration card (Spec visualization)  
3. Face gate → status "running"  
4. Open the passport (tx hash)  
5. Optional: combination / second address  
6. Click RedLine or inject the Hynix pack → stop + revoked  
7. Final 15 seconds: the per-flow token table + "the interface can be swapped for Furiosa / Kiln cards" + the 180W estimate

Controlled comparison run (cut 20 seconds into the video): change the allowance to 100 or the loss limit to 10, run it again, and show the earlier stop.

---

## 8. The SK Hynix Black Swan (a script for judge Q&A, not a trading strategy to build)

Summer 2026: SK Hynix + Samsung account for roughly half of the KOSPI; the daily rebalancing of 2x single-stock ETFs amplifies volatility. The underlying stock can drop -10% to -15% in a single day, the 2x ETF falls deeper, and at roughly -8% the index triggers a market-wide circuit breaker. Fundamentals can still be strong while positions blow up first.

A judge asks: "Even with the right strategy it can still blow up — who cuts it off?"

The answer:

- The strategy Agent can keep being bullish.
- RedLine does not look at how much was made.
- The loss limit fires before forced liquidation.
- A revocable passport, a face gate, an independent kill switch.
- The Demo uses a simulated event pack instead of betting on real market moves on site.

---

## 9. Kiln / Tokens / Power (bring this table on stage)

Model: `gpt-oss-120b` via Kiln.  
It is forbidden to merge Follow and RedLine into one extra-long inference.

| flow | When | Expectation |
|---|---|---|
| `clarify` | Missing Leader/allowance/loss limit | 1–2 turns |
| `spec_emit` | Producing the JSON Spec | once |
| `redline_hold` | Heartbeat / routine summary | short |
| `redline_trip` | Loss limit or event pack | short, structured JSON |
| `demo_inject` | One-click Hynix | once |

README template:

```
flow          tokens_in  tokens_out  latency_s  energy_Wh_est
clarify       ...
spec_emit     ...
redline_trip  ...
total         ...
assumption    180W NPU-class, energy = 180 * latency / 3600
```

Saving tokens: rules judge the loss limit first; the model only reads text events; the Spec uses a schema — free-form prose is forbidden.

---

## 10. Interface Division of Labor

### The competing team

Conversation, Spec schema, face gate, passport mint/revoke, RedLine, the Kiln wrapper, the Demo, the token table.

### waytoweb4 (written confirmation needed)

- List of Leaders available for copying  
- Creating a Paper copy-trading run  
- `start` / `stop`  
- Combination templates: if unavailable, use two copy lanes + an on-chain Basket  

Fallback if blocked: judges only require "authorization and records on-chain, execution with start/stop". If execution fails, use a mock engine + real passport transactions, and state clearly in the README which parts are waytoweb4 and which are mock. Do not get stuck on their API.

### The model teammate (LLaMA direction, no chain work)

Can be done today:

1. `redline_schema.md` (the JSON above)  
2. A 30–50 case SK Hynix-style eval set  
3. A rules + LLM hybrid: the loss limit is a hard gate; the model only scores structural shocks  
4. A one-click event pack → must TRIP  

Do not have them work on the passport, wallets, or backtesting.

---

## 11. Suggested Repository Structure

```
README.md                 # one-sentence function + tx hash + token table + 180W assumption
prd.md                    # this file
apps/web/                 # conversation, configuration card, face gate, passport link, RedLine button
apps/follow-agent/        # Kiln clarify + spec_emit
apps/redline-agent/       # schema + rules gate + event injection
apps/passport/            # mint / revoke / specHash
apps/waytoweb4-adapter/   # start/stop/paper
docs/security-arch.md     # product architecture + security architecture (judges/partners will ask for it)
docs/eval/hynix-cases.json
```

Choose a **cheap testnet** for the chain (independent of Kiln/the on-site network). The goal is reliably producing hashes, not picking the right mainnet narrative.

---

## 12. Security Architecture (the minimum you can present)

1. **Before the trade**: no start without the face gate; Spec fields are whitelisted.  
2. **During the call**: Kiln only outputs JSON and the backend validates; no waytoweb4 call without validation.  
3. **During the trade**: Paper only; the loss limit is a hardcoded gate; RedLine runs as an independent process.  
4. **After the fact**: the passport + logs let a third party reconstruct what happened.  
5. **What AI cannot do**: change maxLoss, turn off RedLine, open the gate by itself, or get an exemption by looking at PnL.

---

## 13. Roadmap (three lines for the Furiosa judges)

- Short term — the chip (this event): financial Agent workloads + the passport; 180W estimate.  
- Mid term — energy: multi-user 24/7, benchmarked as users/kW.  
- Long term — storage: the passport becomes the hash unit for configuration/authorization/track record; a profit-splitting marketplace listing is out of scope.

---

## 14. Build Order (schedule by this starting today)

1. Spec JSON schema + validator  
2. Kiln Hello: `gpt-oss-120b` produces a valid Spec  
3. Face-gate switch (a mock pass is fine at first) + start/stop  
4. Passport mint; record the hash  
5. The loss-limit hard gate  
6. RedLine JSON + Hynix injection → revoke  
7. Logs from the two comparison runs  
8. Write the token table into the README  
9. The 3-minute screen recording  

Close the loop first, then add the Basket.

---

## 15. Cautions (avoid getting eliminated on site)

1. Not integrating Kiln / not using `gpt-oss-120b` = a fatal flaw for Challenge A.  
2. Only slides and no tx hash = failure of the chain clause.  
3. Reporting only a single token total = failure of the energy-efficiency clause.  
4. The Agent still placing orders after the conditions change = failure of the control clause.  
5. If the Demo runs long: cut the combination and the second address, and keep "configure → gate → passport → burn".  
6. No live trading, no real KYC, no real power-draw testing — none of it.  
7. The submission deadline is **9/30 12:00 KST** and the Demo starts at 15:00; leave buffer for uploading and the network.  
8. Official Q&A: https://t.me/GWDC_Global/392/742  

---

## 16. One-Pager for Collaborators / Mentors

The strategy can be wrong; the black swan can come.  
What the judges want to see: configuration completes in natural language, only a face opens the gate, the authorization opens on-chain, and RedLine can stop the engine and burn the passport.  
Execution is outsourced to waytoweb4; responsibility stays with humans and rules, not with the model.
