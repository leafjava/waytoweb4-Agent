import { useI18n } from '../i18n.jsx'

function CopyHash({ label, value, emptyText }) {
  if (!value) {
    return (
      <div className="flex justify-between text-xs">
        <span className="text-slate-400">{label}</span>
        <span className="text-slate-600 italic">{emptyText}</span>
      </div>
    )
  }
  return (
    <div className="text-xs">
      <div className="text-slate-400 mb-0.5">{label}</div>
      <div className="txhash text-slate-200">{value}</div>
    </div>
  )
}

export default function LiveDataPanel({ snapshot }) {
  const { t } = useI18n()
  const passports = snapshot?.passports || {}
  const ids = Object.keys(passports)
  const latest = ids.length ? passports[ids[ids.length - 1]] : null
  const tokenReport = snapshot?.token_report || ''
  const eventCount = (snapshot?.events || []).length

  return (
    <section className="bg-slate-900/50 border border-slate-800 rounded-xl p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-sm uppercase tracking-wider text-slate-400">
          <i className="fa fa-signal mr-2"></i> {t('live.title')}
        </h2>
        <span className="text-[10px] uppercase tracking-wider text-slate-500">
          {t('live.polled')} <code>/api/state</code> {t('live.polled.every')}
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-3">
          <div className="text-xs uppercase tracking-wider text-slate-400">
            {t('live.latest')}
          </div>
          {!latest ? (
            <div className="text-sm text-slate-500 italic">{t('live.no_passport')}</div>
          ) : (
            <div className="space-y-2 bg-slate-950 border border-slate-800 rounded-lg p-3">
              <div className="text-xs">
                <span className="text-slate-400">{t('live.id')}</span>
                <div className="txhash text-slate-200">{latest.passport_id}</div>
              </div>
              <CopyHash label={t('live.spec_hash')} value={latest.spec_hash} emptyText="—" />
              <CopyHash label={t('live.mint_tx')} value={latest.tx_mint_hash} emptyText="—" />
              <CopyHash label={t('live.revoke_tx')} value={latest.tx_revoke_hash} emptyText="—" />
              <div className="flex justify-between text-xs pt-1">
                <span className="text-slate-400">{t('live.status')}</span>
                <span className="text-slate-200 font-mono">{latest.status}</span>
              </div>
            </div>
          )}
          <div className="text-[11px] text-slate-500">
            {t('live.audit_count')} <span className="text-slate-300">{eventCount}</span>
          </div>
        </div>

        <div>
          <div className="text-xs uppercase tracking-wider text-slate-400 mb-2">
            {t('live.token_table')}
          </div>
          <pre className="text-[11px] text-slate-200 whitespace-pre-wrap font-mono bg-slate-950 border border-slate-800 rounded-lg p-3 max-h-72 overflow-auto">
{tokenReport || t('live.empty_table')}
          </pre>
          <div className="text-[11px] text-slate-500 mt-2">
            {t('live.footer_note')} <code>GET /api/state/tokens</code>{t('live.footer_note.tail')}
          </div>
        </div>
      </div>
    </section>
  )
}