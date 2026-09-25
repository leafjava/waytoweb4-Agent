// EvidenceView.jsx -- "Can a stranger reconstruct this mandate?" page.
// Advice #4. Renders the latest two-runs payload (from
// /runs/latest.json, served by Vite from frontend/public/runs/) as
// a single audit page. Nothing here mutates state -- it's a
// read-only window onto what the backend already emitted.
//
// Data sources:
//   - /runs/latest.json  -- the latest two_runs_demo.py output
//   - /api/state          -- live passport + event log
//   - /api/state/tokens   -- PRD §9 token / energy table

import { useEffect, useState } from 'react'
import { useI18n } from '../i18n.jsx'

async function fetchJson(url) {
  try {
    const r = await fetch(url, { cache: 'no-store' })
    if (!r.ok) return null
    return await r.json()
  } catch {
    return null
  }
}

function Section({ title, children, tone = 'neutral' }) {
  const palette = {
    neutral: 'border-slate-700 bg-slate-900/40',
    brand: 'border-sky-700/60 bg-sky-900/20',
    danger: 'border-rose-700/60 bg-rose-900/20',
    ok: 'border-emerald-700/60 bg-emerald-900/20',
  }[tone]
  return (
    <section className={`border ${palette} rounded-lg p-4`}>
      <h3 className="text-xs uppercase tracking-wider text-slate-400 mb-3">
        {title}
      </h3>
      <div className="text-sm text-slate-200">{children}</div>
    </section>
  )
}

function Field({ k, v, mono = true }) {
  return (
    <div className="flex items-baseline justify-between gap-3 py-1">
      <span className="text-xs text-slate-400 shrink-0">{k}</span>
      <span
        className={
          'text-right break-all truncate ' +
          (mono ? 'font-mono text-[12px] text-slate-100' : 'text-slate-100')
        }
        title={typeof v === 'string' ? v : undefined}
      >
        {v ?? '—'}
      </span>
    </div>
  )
}

function shortHash(h) {
  if (!h) return '—'
  if (h.length > 22) return h.slice(0, 18) + '…' + h.slice(-4)
  return h
}

export default function EvidenceView() {
  const { t } = useI18n()
  const [runs, setRuns] = useState(null)
  const [state, setState] = useState(null)

  useEffect(() => {
    let cancelled = false
    async function tick() {
      const [r, s] = await Promise.all([
        fetchJson('/runs/latest.json'),
        fetchJson('/api/state'),
      ])
      if (!cancelled) {
        setRuns(r)
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

  const runList = runs?.runs ?? []
  const passports = state?.passports ?? {}
  const events = state?.events ?? []

  return (
    <div className="evidence-page mx-auto max-w-5xl p-6 space-y-5">
      <div>
        <h1 className="text-2xl font-semibold text-slate-100">
          {t('evidence.heading')}
        </h1>
        <p className="mt-1 text-sm text-slate-400">{t('evidence.sub')}</p>
      </div>

      <Section title={t('evidence.runs.title')} tone="brand">
        {runList.length === 0 ? (
          <div className="text-xs italic text-slate-400">
            {t('evidence.runs.empty')}
          </div>
        ) : (
          <div className="space-y-4">
            {runList.map((r, i) => (
              <div key={r.passport_id ?? i} className="border border-slate-800 rounded p-3 bg-slate-950/40">
                <div className="text-xs uppercase tracking-wider text-slate-500 mb-2">
                  {r.label}
                </div>
                <Field k="passport_id" v={r.passport_id} />
                <Field k="spec.notionalUsd" v={r.spec?.notionalUsd} />
                <Field k="spec.maxLossUsd" v={r.spec?.maxLossUsd} />
                <Field k="drawdown_usd" v={r.drawdown_usd} />
                <Field k="status" v={r.status} />
                <Field k="mint_tx_hash" v={shortHash(r.mint_tx_hash)} />
                <Field k="revoke_tx_hash" v={shortHash(r.revoke_tx_hash)} />
                <Field
                  k="verdict_level / codes / source"
                  v={`${r.verdict_level} · ${(r.verdict_codes || []).join(',')} · ${r.verdict_source}`}
                />
              </div>
            ))}
          </div>
        )}
      </Section>

      <Section title={t('evidence.live.title')} tone="ok">
        {Object.keys(passports).length === 0 ? (
          <div className="text-xs italic text-slate-400">
            {t('evidence.live.empty')}
          </div>
        ) : (
          <div className="space-y-2">
            {Object.values(passports).map((p) => (
              <div key={p.passport_id} className="border border-slate-800 rounded p-3 bg-slate-950/40">
                <Field k="passport_id" v={p.passport_id} />
                <Field k="leader / status" v={`${p.leader_id} / ${p.status}`} />
                <Field k="face_verified" v={String(p.face_verified)} />
                <Field k="drawdown_usd" v={p.drawdown_usd} />
                <Field k="tx_mint_hash" v={shortHash(p.tx_mint_hash)} />
                <Field k="tx_revoke_hash" v={shortHash(p.tx_revoke_hash)} />
              </div>
            ))}
          </div>
        )}
      </Section>

      <Section title={t('evidence.events.title')} tone="neutral">
        {events.length === 0 ? (
          <div className="text-xs italic text-slate-400">
            {t('evidence.events.empty')}
          </div>
        ) : (
          <div className="space-y-1">
            {events
              .slice()
              .reverse()
              .slice(0, 30)
              .map((e, i) => (
                <div
                  key={i}
                  className="flex items-baseline gap-2 text-xs font-mono py-0.5"
                >
                  <span className="text-slate-500 shrink-0">
                    {e.ts?.slice(11, 19) ?? ''}
                  </span>
                  <span className="text-slate-300">{e.kind}</span>
                  {e.passport_id && (
                    <span className="text-slate-500 truncate">
                      {e.passport_id.slice(0, 12)}
                    </span>
                  )}
                </div>
              ))}
          </div>
        )}
      </Section>
    </div>
  )
}