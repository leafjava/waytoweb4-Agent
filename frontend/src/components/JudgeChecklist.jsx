import { useI18n } from '../i18n.jsx'

const ROW_KEYS = [
  { icon: 'fa-users', labelKey: 'judge.user_need', bodyKey: 'judge.user_need.body', where: 'docs/security-arch.md' },
  { icon: 'fa-code-fork', labelKey: 'judge.agent_vs_code', bodyKey: 'judge.agent_vs_code.body', where: 'agent/ + backend/app/' },
  { icon: 'fa-server', labelKey: 'judge.kiln', bodyKey: 'judge.kiln.body', where: 'agent/follow_agent/kiln_client.py' },
  { icon: 'fa-table', labelKey: 'judge.tokens', bodyKey: 'judge.tokens.body', where: 'live table at the bottom of this page' },
  { icon: 'fa-bolt', labelKey: 'judge.energy', bodyKey: 'judge.energy.body', where: 'agent/shared/energy.py' },
  { icon: 'fa-link', labelKey: 'judge.ontx', bodyKey: 'judge.ontx.body', where: 'live panel below' },
  { icon: 'fa-clone', labelKey: 'judge.twice', bodyKey: 'judge.twice.body', where: 'demo page · EventLog' },
  { icon: 'fa-ban', labelKey: 'judge.overshoot', bodyKey: 'judge.overshoot.body', where: 'agent/follow_agent/spec_schema.py' },
  { icon: 'fa-search', labelKey: 'judge.audit', bodyKey: 'judge.audit.body', where: 'docs/security-arch.md' },
]

export default function JudgeChecklist() {
  const { t } = useI18n()

  return (
    <section>
      <h2 className="text-sm uppercase tracking-wider text-slate-400 mb-4">
        <i className="fa fa-check-square-o mr-2"></i> {t('judge.title')}
      </h2>
      <div className="bg-slate-900/40 border border-slate-800 rounded-xl overflow-hidden">
        <ul className="divide-y divide-slate-800">
          {ROW_KEYS.map((r) => (
            <li key={r.labelKey} className="p-4 flex gap-4 items-start hover:bg-slate-900/60">
              <i className={`fa ${r.icon} text-sky-400 mt-1 w-5 text-center`}></i>
              <div className="flex-1 min-w-0">
                <div className="text-sm font-semibold text-slate-100">{t(r.labelKey)}</div>
                <div className="text-sm text-slate-400 mt-0.5">{t(r.bodyKey)}</div>
              </div>
              <code className="text-[11px] text-slate-500 font-mono whitespace-nowrap ml-3 hidden md:block">
                {r.where}
              </code>
            </li>
          ))}
        </ul>
      </div>
    </section>
  )
}