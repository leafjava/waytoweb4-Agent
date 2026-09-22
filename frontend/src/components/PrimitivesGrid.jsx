import { useI18n } from '../i18n.jsx'

const PRIMITIVES_KEYS = [
  { icon: 'fa-commenting', color: 'sky', prefix: 'prim.follow' },
  { icon: 'fa-user-circle-o', color: 'amber', prefix: 'prim.face' },
  { icon: 'fa-id-card', color: 'emerald', prefix: 'prim.passport' },
  { icon: 'fa-shield', color: 'fuchsia', prefix: 'prim.redline' },
]

const COLOR_CLASSES = {
  sky: 'border-sky-700/50 bg-sky-900/20 text-sky-300',
  amber: 'border-amber-700/50 bg-amber-900/20 text-amber-300',
  emerald: 'border-emerald-700/50 bg-emerald-900/20 text-emerald-300',
  fuchsia: 'border-fuchsia-700/50 bg-fuchsia-900/20 text-fuchsia-300',
}

export default function PrimitivesGrid() {
  const { t } = useI18n()

  return (
    <section>
      <h2 className="text-sm uppercase tracking-wider text-slate-400 mb-4">
        <i className="fa fa-cubes mr-2"></i> {t('primitives.title')}
      </h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {PRIMITIVES_KEYS.map((p) => (
          <div
            key={p.prefix}
            className={`border rounded-xl p-5 ${COLOR_CLASSES[p.color]} bg-slate-900/40`}
          >
            <div className="flex items-center justify-between mb-3">
              <i className={`fa ${p.icon} text-2xl`}></i>
              <span className="text-[10px] uppercase tracking-wider opacity-70">
                {t(`${p.prefix}.tag`)}
              </span>
            </div>
            <h3 className="text-lg font-semibold text-slate-50 mb-1.5">
              {t(`${p.prefix}.title`)}
            </h3>
            <p className="text-sm text-slate-400 leading-relaxed">
              {t(`${p.prefix}.body`)}
            </p>
          </div>
        ))}
      </div>
    </section>
  )
}