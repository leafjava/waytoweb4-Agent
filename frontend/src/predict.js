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

// Keyword matchers accept EN / KO / ZH event phrasing. The KO entries let
// Demo Day input in Korean classify correctly; the ZH entries are input
// parsing (not user-visible copy). Kept in lockstep with
// agent/redline_agent/llm_classifier.py KEYWORD_RULES.
const KEYWORD_RULES = [
  { kws: ['熔断', 'circuit', 'halt', '서킷브레이커', '거래정지'], code: 'CB_LIKE' },
  { kws: ['清算', 'liq', 'cascade', '청산'], code: 'LIQ_CASCADE' },
  { kws: ['杠杆', 'leveraged', '2x', 'lev_etf', '레버리지'], code: 'LEV_ETF_AMP' },
  { kws: ['盘前', 'pre-market', 'gap', '薄流动性', '갭', '얇은 유동성'], code: 'GAP_ORACLE' },
  { kws: ['人工', 'human', 'override', 'kill', '즉시 중지'], code: 'HUMAN_OVERRIDE' },
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