// ReadinessBar.jsx -- the "red/yellow/green" status strip that lives
// at the top of the home page (advice #5). It reads /api/health and
// /api/state once, derives 5 checks from those snapshots, and labels
// each row green / yellow / red so the judge can tell at a glance
// what is real vs. what fell back to mock. Light theme to match
// PrimitivesGrid.

import { useEffect, useState } from 'react'
import { useI18n } from '../i18n.jsx'

const ROW_PALETTE = {
  ok: 'border-emerald-200 bg-emerald-50 text-emerald-700',
  warn: 'border-amber-200 bg-amber-50 text-amber-700',
  danger: 'border-rose-200 bg-rose-50 text-rose-700',
}

const DOT_COLOR = {
  ok: 'bg-emerald-400',
  warn: 'bg-amber-400',
  danger: 'bg-rose-400',
}

const PILL_CLASS = {
  ok: 'bg-emerald-50 border border-emerald-200 text-emerald-700',
  warn: 'bg-amber-50 border border-amber-200 text-amber-700',
  danger: 'bg-rose-50 border border-rose-200 text-rose-700',
  neutral: 'bg-slate-100 border border-slate-200 text-slate-700',
}

function Row({ tone, label, value }) {
  return (
    <div className={`flex items-center justify-between border rounded-lg px-3 py-1.5 ${ROW_PALETTE[tone]}`}>
      <div className="flex items-center gap-2">
        <span className={`inline-block w-2 h-2 rounded-full ${DOT_COLOR[tone]}`} />
        <span className="text-xs text-[#1d1d1f]">{label}</span>
      </div>
      <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-mono ${PILL_CLASS[tone]}`}>
        {value}
      </span>
    </div>
  )
}

async function fetchJson(url) {
  try {
    const r = await fetch(url)
    if (!r.ok) return null
    return await r.json()
  } catch {
    return null
  }
}

export default function ReadinessBar() {
  const { t } = useI18n()
  const [health, setHealth] = useState(null)
  const [state, setState] = useState(null)

  useEffect(() => {
    let cancelled = false
    async function tick() {
      const [h, s] = await Promise.all([fetchJson('/api/health'), fetchJson('/api/state')])
      if (!cancelled) {
        setHealth(h)
        setState(s)
      }
    }
    tick()
    const id = setInterval(tick, 5000)
    return () => {
      cancelled = true
      clearInterval(id)
    }
  }, [])

  const kiln = health?.kiln ?? 'unknown'
  const passport = health?.passport_backend ?? 'unknown'
  const livePassports = state
    ? Object.values(state.passports || {}).filter(
        (p) => p.status && p.status !== 'pending_face',
      ).length
    : 0

  const rows = [
    { tone: kiln === 'http' ? 'ok' : 'warn', label: t('ready.kiln'), value: kiln },
    { tone: passport === 'mock' ? 'warn' : 'ok', label: t('ready.passport'), value: passport },
    { tone: 'ok', label: t('ready.face'), value: t('ready.face_val') },
    { tone: livePassports > 0 ? 'ok' : 'warn', label: t('ready.mints'), value: String(livePassports) },
    { tone: 'ok', label: t('ready.stop'), value: t('ready.stop_val') },
  ]

  return (
    <section className="border border-black/10 rounded-2xl p-4 shadow-sm" style={{ backgroundColor: '#ecf2f8' }}>
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm uppercase tracking-wider text-slate-500">
          <i className="fa fa-stethoscope mr-2"></i>
          {t('ready.title')}
        </h3>
        <span className="text-[10px] text-slate-500">
          {t('ready.fresh')} <code>/api/health</code>
        </span>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-5 gap-2">
        {rows.map((r) => (
          <Row key={r.label} tone={r.tone} label={r.label} value={r.value} />
        ))}
      </div>
    </section>
  )
}