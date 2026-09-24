// StatTicker.jsx — three large numbers computed from /api/state.
// We render ONLY real values; no fake jitter. A short count-up
// animation runs on number change so the page "feels alive" without
// lying to the judges (PRD honest-disclaimer rule).

import { useEffect, useRef, useState } from 'react'

function useAnimatedNumber(value, durationMs = 600) {
  const [display, setDisplay] = useState(value)
  const fromRef = useRef(value)
  useEffect(() => {
    const from = fromRef.current
    const to = value
    if (from === to) {
      setDisplay(to)
      return
    }
    const start = performance.now()
    let raf
    const tick = (now) => {
      const t = Math.min(1, (now - start) / durationMs)
      // ease-out cubic
      const eased = 1 - Math.pow(1 - t, 3)
      setDisplay(Math.round(from + (to - from) * eased))
      if (t < 1) raf = requestAnimationFrame(tick)
      else fromRef.current = to
    }
    raf = requestAnimationFrame(tick)
    return () => raf && cancelAnimationFrame(raf)
  }, [value, durationMs])
  return display
}

// Tailwind JIT does not scan dynamic class names like `bg-${accent}-500/10`.
// Resolve the full class string from the accent value.
const ACCENT_GLOW = {
  sky: 'bg-sky-500/10',
  amber: 'bg-amber-500/10',
  emerald: 'bg-emerald-500/10',
  rose: 'bg-rose-500/10',
  fuchsia: 'bg-fuchsia-500/10',
  slate: 'bg-slate-500/10',
}
const ACCENT_TEXT = {
  sky: 'text-sky-400',
  amber: 'text-amber-400',
  emerald: 'text-emerald-400',
  rose: 'text-rose-400',
  fuchsia: 'text-fuchsia-400',
  slate: 'text-slate-400',
}

function Tile({ icon, value, label, accent = 'sky', suffix }) {
  const v = useAnimatedNumber(typeof value === 'number' ? value : 0)
  return (
    <div className="relative bg-slate-900/60 border border-slate-800 rounded-xl p-5 overflow-hidden">
      <div className={`absolute -top-12 -right-12 w-32 h-32 rounded-full ${ACCENT_GLOW[accent] || ACCENT_GLOW.sky} blur-2xl pointer-events-none`} />
      <div className="relative">
        <i className={`fa ${icon} ${ACCENT_TEXT[accent] || ACCENT_TEXT.sky} text-lg`}></i>
        <div className="mt-3 text-4xl md:text-5xl font-semibold text-slate-50 tabular-nums">
          {typeof value === 'number' ? v.toLocaleString() : value}
          {suffix && <span className="text-xl text-slate-400 ml-1">{suffix}</span>}
        </div>
        <div className="mt-1 text-xs uppercase tracking-wider text-slate-400">{label}</div>
      </div>
    </div>
  )
}

// Parse the PRD §9 token table string into per-flow totals.
function parseTokenTable(tokenReport) {
  if (!tokenReport || typeof tokenReport !== 'string') {
    return { tokensIn: 0, tokensOut: 0, latencyS: 0, energyWh: 0, calls: 0 }
  }
  const rows = {}
  let inRow = null
  for (const line of tokenReport.split('\n')) {
    const trimmed = line.trim()
    const match = trimmed.match(/^(\S+)\s+(\d+)\s+(\d+)\s+([\d.]+)\s+([\d.]+)/)
    if (match && ['clarify', 'spec_emit', 'redline_hold', 'redline_trip', 'demo_inject'].includes(match[1])) {
      rows[match[1]] = {
        in: Number(match[2]),
        out: Number(match[3]),
        latency: Number(match[4]),
        energy: Number(match[5]),
      }
      inRow = match[1]
    } else if (inRow && /^total\s+/.test(trimmed)) {
      // The total row mirrors the per-flow row but with "total" name;
      // we don't need it because we sum below.
      inRow = null
    }
  }
  let tokensIn = 0
  let tokensOut = 0
  let latencyS = 0
  let energyWh = 0
  for (const v of Object.values(rows)) {
    tokensIn += v.in
    tokensOut += v.out
    latencyS += v.latency
    energyWh += v.energy
  }
  return { tokensIn, tokensOut, latencyS, energyWh, calls: Object.keys(rows).length }
}

export default function StatTicker({ snapshot }) {
  const passports = snapshot?.passports || {}
  const passportCount = Object.keys(passports).length
  const revokedCount = Object.values(passports).filter(
    (p) => p.status === 'revoked',
  ).length
  const eventCount = (snapshot?.events || []).length
  const tok = parseTokenTable(snapshot?.token_report)

  return (
    <section>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-sm uppercase tracking-wider text-slate-400">
          <i className="fa fa-signal mr-2"></i> Live system metrics
        </h2>
        <span className="text-[10px] uppercase tracking-wider text-slate-500">
          counts derived from <code>/api/state</code>
        </span>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Tile icon="fa-id-card" value={passportCount} label="passports minted" accent="emerald" />
        <Tile icon="fa-ban" value={revokedCount} label="passports revoked" accent="rose" />
        <Tile icon="fa-list" value={eventCount} label="audit events" accent="sky" />
        <Tile icon="fa-bolt" value={tok.tokensIn + tok.tokensOut} label="Kiln tokens (in+out)" accent="amber" suffix=" tok" />
        <Tile icon="fa-bolt" value={Math.round(tok.energyWh * 1000) / 1000} label="energy @180W" accent="fuchsia" suffix=" Wh" />
        <Tile icon="fa-clock-o" value={Math.round(tok.latencyS * 100) / 100} label="Kiln latency (cum)" accent="sky" suffix=" s" />
        <Tile icon="fa-tasks" value={tok.calls} label="flows touched" accent="emerald" />
        <Tile icon="fa-shield" value={revokedCount > 0 ? 'safe' : '—'} label="RedLine state" accent={revokedCount > 0 ? 'fuchsia' : 'slate'} />
      </div>
    </section>
  )
}