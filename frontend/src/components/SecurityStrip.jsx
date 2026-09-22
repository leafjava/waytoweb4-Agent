import { useI18n } from '../i18n.jsx'

const STAGE_KEYS = [1, 2, 3, 4, 5]

export default function SecurityStrip() {
  const { t } = useI18n()

  return (
    <section>
      <h2 className="text-sm uppercase tracking-wider text-slate-400 mb-4">
        <i className="fa fa-lock mr-2"></i> {t('sec.title')}
      </h2>
      <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
        {STAGE_KEYS.map((n) => (
          <div
            key={n}
            className="bg-slate-900/50 border border-slate-800 rounded-lg p-4 relative"
          >
            <span className="absolute -top-3 -left-2 w-7 h-7 rounded-full bg-sky-500 text-slate-950 font-bold flex items-center justify-center text-sm">
              {n}
            </span>
            <div className="text-sm font-semibold text-slate-100 mb-1 mt-1">
              {t(`sec.${n}.title`)}
            </div>
            <div className="text-xs text-slate-400 leading-relaxed">
              {t(`sec.${n}.body`)}
            </div>
          </div>
        ))}
      </div>
    </section>
  )
}