import { useI18n } from '../i18n.jsx'

// 5 stages of the waytoweb4-agent security pipeline. Pattern borrowed
// from web3labs-gwdc's ComplianceFlow.tsx -- a horizontal stepper
// makes the architecture read as "pre-trade -> inference -> trade ->
// post-trade -> AI cannot", not as "5 parallel features".

const STAGE_KEYS = [1, 2, 3, 4, 5]

const STAGE_ICONS = {
  1: 'fa-lock',
  2: 'fa-code',
  3: 'fa-shield',
  4: 'fa-search',
  5: 'fa-ban',
}

export default function SecurityStrip() {
  const { t } = useI18n()

  return (
    <section>
      <h2 className="text-sm uppercase tracking-wider text-slate-400 mb-6">
        <i className="fa fa-lock mr-2"></i> {t('sec.title')}
      </h2>

      {/* Desktop / md+: horizontal stepper */}
      <div className="hidden md:block relative">
        {/* Connector line behind the nodes */}
        <div
          aria-hidden="true"
          className="absolute top-8 left-[10%] right-[10%] h-0.5 bg-gradient-to-r from-sky-700 via-emerald-600 to-fuchsia-700 opacity-50"
        />
        <div className="relative grid grid-cols-5 gap-4">
          {STAGE_KEYS.map((n) => (
            <StepNode key={n} n={n} />
          ))}
        </div>
      </div>

      {/* Mobile: vertical stepper with a single left rail */}
      <ol className="md:hidden space-y-3 border-l-2 border-sky-700/60 pl-4">
        {STAGE_KEYS.map((n) => (
          <li key={n} className="relative">
            <span className="absolute -left-[26px] top-1 w-6 h-6 rounded-full bg-sky-500 text-slate-950 font-bold flex items-center justify-center text-xs shadow-md shadow-sky-500/30">
              {n}
            </span>
            <div className="text-sm font-semibold text-slate-100">{t(`sec.${n}.title`)}</div>
            <div className="text-xs text-slate-400 mt-0.5 leading-relaxed">{t(`sec.${n}.body`)}</div>
          </li>
        ))}
      </ol>
    </section>
  )
}

function StepNode({ n }) {
  const { t } = useI18n()
  return (
    <div className="flex flex-col items-center text-center">
      <div className="relative w-16 h-16 rounded-full bg-slate-900 border-2 border-sky-500/70 shadow-lg shadow-sky-500/20 flex items-center justify-center">
        <i className={`fa ${STAGE_ICONS[n]} text-xl text-sky-300`}></i>
        <span className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-emerald-500 text-slate-950 font-bold flex items-center justify-center text-[10px] border-2 border-slate-900">
          ✓
        </span>
      </div>
      <div className="mt-3 text-sm font-semibold text-slate-100">{t(`sec.${n}.title`)}</div>
      <div className="mt-1 text-xs text-slate-400 leading-relaxed max-w-[180px]">
        {t(`sec.${n}.body`)}
      </div>
    </div>
  )
}