import { useI18n } from '../i18n.jsx'

const PRIMITIVES_KEYS = [
  { icon: 'fa-commenting', color: 'sky', prefix: 'prim.follow' },
  { icon: 'fa-user-circle-o', color: 'amber', prefix: 'prim.face' },
  { icon: 'fa-id-card', color: 'emerald', prefix: 'prim.passport' },
  { icon: 'fa-shield', color: 'fuchsia', prefix: 'prim.redline' },
]

const COLOR_CLASSES = {
  sky: 'bg-blue-50 text-blue-600',
  amber: 'bg-orange-50 text-orange-600',
  emerald: 'bg-emerald-50 text-emerald-600',
  fuchsia: 'bg-violet-50 text-violet-600',
}

export default function PrimitivesGrid() {
  const { t } = useI18n()

  return (
    <section className="home-primitives">
      <h2 className="text-sm uppercase tracking-wider text-slate-500 mb-4">
        <i className="fa fa-cubes mr-2"></i> {t('primitives.title')}
      </h2>
      <div className="home-primitives__rail grid grid-cols-1 gap-0 md:grid-cols-2 lg:grid-cols-4">
        {PRIMITIVES_KEYS.map((p) => (
          <div
            key={p.prefix}
            className={`feature-card p-6 ${COLOR_CLASSES[p.color]}`}
          >
            <div className="flex items-center justify-between mb-3">
              <i className={`fa ${p.icon} text-2xl`}></i>
              <span className="text-[10px] uppercase tracking-wider opacity-70">
                {t(`${p.prefix}.tag`)}
              </span>
            </div>
            <h3 className="mb-1.5 text-lg font-semibold tracking-[-0.02em] text-[#1d1d1f]">
              {t(`${p.prefix}.title`)}
            </h3>
            <p className="text-sm text-slate-500 leading-relaxed">
              {t(`${p.prefix}.body`)}
            </p>
          </div>
        ))}
      </div>
    </section>
  )
}
