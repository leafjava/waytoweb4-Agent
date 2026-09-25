import { useI18n } from '../i18n.jsx'

const TIMELINE_KINDS = new Set([
  'prepare',
  'confirm',
  'mint',
  'mint_simulated',
  'face_verify',
  'engine_start',
  'redline_judge',
  'engine_stop',
  'face_gate_invalidated',
  'revoke_simulated',
  'revoke_confirmed',
  'revoke_readback',
  'revoke_uncertain',
])

export default function InferenceEvidencePanel({ snapshot }) {
  const { locale, t } = useI18n()
  const workload = snapshot?.workload || {}
  const flows = snapshot?.token_summary?.flows || []
  const total = snapshot?.token_summary?.total || {}
  const timeline = (snapshot?.events || []).filter((event) => TIMELINE_KINDS.has(event.kind)).slice(-8)
  const number = new Intl.NumberFormat(locale === 'ko' ? 'ko-KR' : 'en-US')

  return (
    <section className="inference-evidence-panel overflow-hidden rounded-2xl surface-card shadow-xl shadow-black/20">
      <div className="flex flex-col gap-4 border-b border-black/10 p-5 md:flex-row md:items-start md:justify-between">
        <div>
          <h2 className="text-base font-semibold text-white">
            <i className="fa fa-microchip mr-2 text-cyan-700" aria-hidden="true"></i>
            {t('evidence.title')}
          </h2>
          <p className="mt-1 max-w-2xl text-sm leading-6 text-slate-500">{t('evidence.subtitle')}</p>
        </div>
        <div className="flex flex-wrap gap-2 text-xs">
          <EvidenceTag label={t('evidence.model')} value={workload.model || 'gpt-oss-120b'} />
          <EvidenceTag label={t('evidence.mode')} value={workload.source_mode || 'offline'} tone={workload.source_mode === 'live' ? 'live' : 'offline'} />
          <EvidenceTag label={t('evidence.power')} value={`${workload.power_assumption_w ?? 180} W`} />
        </div>
      </div>

      <div className="grid lg:grid-cols-[1.4fr_0.6fr]">
        <div className="min-w-0 border-b border-black/10 p-5 lg:border-b-0 lg:border-r">
          <div className="mb-3 flex flex-wrap items-end justify-between gap-3">
            <h3 className="text-sm font-medium text-slate-800">{t('evidence.flows')}</h3>
            <div className="text-xs text-slate-500">
              {t('evidence.calls')} <span className="font-mono text-white">{number.format(total.calls || 0)}</span>
              <span className="mx-2 text-slate-700">/</span>
              {t('evidence.sessions')} <span className="font-mono text-white">{number.format(workload.active_sessions || 0)}</span>
              <span className="mx-2 text-slate-700">/</span>
              {t('evidence.passports')} <span className="font-mono text-white">{number.format(workload.passport_count || 0)}</span>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full min-w-[640px] text-left text-xs tabular-nums">
              <thead className="text-slate-500">
                <tr className="border-b border-black/10">
                  <th className="py-2 pr-4 font-medium">{t('evidence.flow')}</th>
                  <th className="px-3 py-2 text-right font-medium">{t('evidence.in')}</th>
                  <th className="px-3 py-2 text-right font-medium">{t('evidence.out')}</th>
                  <th className="px-3 py-2 text-right font-medium">{t('evidence.latency')}</th>
                  <th className="px-3 py-2 text-right font-medium">{t('evidence.energy')}</th>
                  <th className="py-2 pl-4 text-right font-medium">{t('evidence.source')}</th>
                </tr>
              </thead>
              <tbody>
                {flows.map((row) => (
                  <tr key={row.flow} className="border-b border-black/10 last:border-0">
                    <td className="py-2.5 pr-4 font-mono text-cyan-700">{row.flow}</td>
                    <td className="px-3 py-2.5 text-right text-slate-800">{number.format(row.tokens_in)}</td>
                    <td className="px-3 py-2.5 text-right text-slate-800">{number.format(row.tokens_out)}</td>
                    <td className="px-3 py-2.5 text-right text-slate-700">{row.latency_s.toFixed(3)} s</td>
                    <td className="px-3 py-2.5 text-right text-slate-700">{row.energy_Wh_est.toFixed(4)} Wh</td>
                    <td className="py-2.5 pl-4 text-right">
                      <span className={row.usage_source === 'api' ? 'text-emerald-700' : 'text-amber-700'}>
                        {row.usage_source}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr className="border-t border-black/10 font-medium text-white">
                  <td className="py-3 pr-4">{t('evidence.total')}</td>
                  <td className="px-3 py-3 text-right">{number.format(total.tokens_in || 0)}</td>
                  <td className="px-3 py-3 text-right">{number.format(total.tokens_out || 0)}</td>
                  <td className="px-3 py-3 text-right">{(total.latency_s || 0).toFixed(3)} s</td>
                  <td className="px-3 py-3 text-right">{(total.energy_Wh_est || 0).toFixed(4)} Wh</td>
                  <td className="py-3 pl-4 text-right text-slate-500">{total.usage_source || 'none'}</td>
                </tr>
              </tfoot>
            </table>
          </div>
          <p className="mt-3 text-xs leading-5 text-slate-500">{t('evidence.assumption')}</p>
        </div>

        <div className="p-5">
          <h3 className="text-sm font-medium text-slate-800">{t('evidence.timeline')}</h3>
          {timeline.length ? (
            <ol className="mt-4 space-y-3">
              {timeline.map((event, index) => (
                <li key={`${event.ts}-${event.kind}-${index}`} className="grid grid-cols-[3.75rem_0.75rem_minmax(0,1fr)] items-center gap-2 text-xs">
                  <time className="font-mono text-slate-500">{event.ts?.slice(11, 19)}</time>
                  <span className="h-2 w-2 rounded-full bg-cyan-400" aria-hidden="true"></span>
                  <span className="min-w-0 break-words font-mono text-slate-700">{event.kind}</span>
                </li>
              ))}
            </ol>
          ) : (
            <p className="mt-4 text-sm leading-6 text-slate-500">{t('evidence.timeline_empty')}</p>
          )}
          <div className="mt-5 rounded-xl bg-[#f5f5f7] p-3 text-xs leading-5 text-slate-500">
            <span className="text-slate-800">{t('evidence.run')}</span>
            <div className="mt-1 break-all font-mono">{workload.run_id || '—'}</div>
          </div>
        </div>
      </div>
    </section>
  )
}

function EvidenceTag({ label, value, tone }) {
  const colors = tone === 'live'
    ? 'bg-emerald-50 text-emerald-700'
    : tone === 'offline'
      ? 'bg-amber-50 text-amber-700'
      : 'bg-black/[0.04] text-slate-800'
  return (
    <span className={`rounded-lg px-2.5 py-1.5 ${colors}`}>
      <span className="text-slate-500">{label}</span> <strong className="font-mono font-medium">{value}</strong>
    </span>
  )
}
