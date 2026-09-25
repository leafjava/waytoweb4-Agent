import { useState } from 'react'
import DrawdownGauge from './DrawdownGauge'
import VerdictBadge from './VerdictBadge'
import EventLog from './EventLog'
import { apiPost } from '../api'
import { useI18n } from '../i18n.jsx'

export default function RedLinePanel({ draft, snapshot, onAction }) {
  const { t } = useI18n()
  const [busy, setBusy] = useState(null)

  const passport = draft.passport_id ? snapshot?.passports?.[draft.passport_id] : null
  const drawdown = passport?.drawdown_usd ?? 0
  const maxLoss = passport?.max_loss_usd ?? (draft.locked_spec?.maxLossUsd ?? 0)
  const verdict = passport?.last_verdict

  async function call(path, body) {
    if (!draft.passport_id) return
    setBusy(path)
    try {
      const r = await apiPost(path, body ?? { passport_id: draft.passport_id })
      if (r?.side_effects) console.info('redline side effects:', r.side_effects)
      onAction?.()
    } catch (e) {
      alert(`${t('red.failed')}: ${e.message || e}`)
    } finally {
      setBusy(null)
    }
  }

  const revoked = passport?.status === 'revoked'
  const running = !!passport?.engine_running

  return (
    <div className="surface-card border border-black/10 rounded-lg p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-sm uppercase tracking-wider text-slate-500">
          <i className="fa fa-shield mr-2"></i> {t('red.title')}
        </h2>
        {running && (
          <span className="text-xs text-emerald-700 flex items-center gap-1.5">
            <span className="inline-block w-2 h-2 rounded-full bg-emerald-400 pulse-running"></span>
            {t('red.running')}
          </span>
        )}
      </div>

      <DrawdownGauge drawdown={drawdown} maxLoss={maxLoss} />

      <div>
        <div className="text-xs text-slate-500 mb-1">{t('red.verdict')}</div>
        <VerdictBadge verdict={verdict} />
      </div>

      <div className="grid grid-cols-2 gap-2">
        <button
          disabled={!draft.passport_id || revoked || busy === '/api/redline/inject/hynix'}
          onClick={() => call('/api/redline/inject/hynix')}
          className="px-2 py-1.5 rounded bg-fuchsia-600 hover:bg-fuchsia-500 disabled:opacity-50 text-xs"
        >
          <i className="fa fa-bolt mr-1"></i> {t('red.inject_hynix')}
        </button>
        <button
          disabled={!draft.passport_id || revoked || busy === '/api/redline/judge'}
          onClick={() => call('/api/redline/judge')}
          className="px-2 py-1.5 rounded bg-orange-600 hover:bg-orange-500 disabled:opacity-50 text-xs"
        >
          <i className="fa fa-gavel mr-1"></i> {t('red.trigger')}
        </button>
      </div>

      <EventLog events={(snapshot?.events || []).slice().reverse().slice(0, 12)} />
    </div>
  )
}
