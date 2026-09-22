import { KIND_COLORS } from '../colors'
import { useI18n } from '../i18n.jsx'

export default function EventLog({ events }) {
  const { t } = useI18n()
  return (
    <div>
      <div className="text-xs text-slate-400 mb-1">{t('events.title')}</div>
      <div className="bg-slate-950 border border-slate-800 rounded p-2 max-h-40 overflow-y-auto text-[11px] space-y-0.5">
        {events?.length ? events.map((e, i) => (
          <div key={i} className="flex gap-2">
            <span className="text-slate-500 font-mono">{e.ts?.slice(11, 19) ?? ''}</span>
            <span className={`font-mono ${KIND_COLORS[e.kind] ?? 'text-slate-300'}`}>
              {e.kind}
            </span>
            {e.passport_id && (
              <span className="text-slate-500 font-mono truncate">{e.passport_id.slice(0, 12)}</span>
            )}
          </div>
        )) : (
          <div className="text-slate-600 italic">{t('events.empty')}</div>
        )}
      </div>
    </div>
  )
}