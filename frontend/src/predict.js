// Client-side helpers that mirror the agent's prediction logic.
// Kept in lockstep with agent/redline_agent/llm_classifier.py.
//
// These do NOT call the backend. The HomePage's "Spec Simulator"
// uses them to predict what RedLine will do *before* the user
// runs anything, so the homepage's promise ("this would TRIP")
// is grounded in the same code that the backend runs.

export const HYNIX_EVENTS = [
  { symbol: '000660.KS', change_pct: -12.0, kind: 'tick' },
  { symbol: 'HIYS2X.KS', change_pct: -27.0, kind: 'leveraged_etf' },
  { symbol: 'KS200', change_pct: -8.5, kind: 'circuit_breaker' },
]

const KEYWORD_RULES = [
  { kws: ['熔断', 'circuit', 'halt'], code: 'CB_LIKE' },
  { kws: ['清算', 'liq', 'cascade'], code: 'LIQ_CASCADE' },
  { kws: ['杠杆', 'leveraged', '2x', 'lev_etf'], code: 'LEV_ETF_AMP' },
  { kws: ['盘前', 'pre-market', 'gap', '薄流动性'], code: 'GAP_ORACLE' },
  { kws: ['人工', 'human', 'override', 'kill'], code: 'HUMAN_OVERRIDE' },
]

const CB_THRESHOLD_PCT = -8.0

export function predictFromRuleGate(spec, tripSeconds = 60) {
  // The hard rule gate always fires at exactly `tripSeconds`,
  // because the mock engine ticks drawdown linearly from 0 to
  // maxLossUsd over `tripSeconds` (see backend/app/engine.py).
  return {
    level: 'TRIP',
    timeToTripSec: tripSeconds,
    reasonCodes: ['DD_LIMIT'],
    via: 'rule_gate',
    modelMayOverride: false,
    note: `engine reaches maxLoss=$${spec.maxLossUsd} in ${tripSeconds}s; rule gate fires; model never gets a say`,
  }
}

export function predictFromLLM(events = HYNIX_EVENTS) {
  const worstChange = Math.min(...events.map((e) => e.change_pct))
  const text = events.map((e) => `${e.symbol} ${e.kind}`).join(' ').toLowerCase()
  const codes = []
  for (const r of KEYWORD_RULES) {
    if (r.kws.some((kw) => text.includes(kw))) {
      if (!codes.includes(r.code)) codes.push(r.code)
    }
  }
  if (worstChange <= CB_THRESHOLD_PCT && !codes.includes('CB_LIKE')) {
    codes.push('CB_LIKE')
  }
  let level = 'HOLD'
  if (codes.some((c) => c === 'CB_LIKE' || c === 'LIQ_CASCADE' || c === 'HUMAN_OVERRIDE')) {
    level = 'TRIP'
  } else if (codes.some((c) => c === 'LEV_ETF_AMP' || c === 'GAP_ORACLE')) {
    level = 'WATCH'
  }
  return {
    level,
    reasonCodes: codes,
    via: 'llm',
    modelMayOverride: false,
    worstChange,
  }
}

export function predictHoldOutcome(spec, tripSeconds = 60) {
  // What happens if the user just lets the engine run to the cap
  // without injecting any events? -> rule_gate TRIP.
  return predictFromRuleGate(spec, tripSeconds)
}