import { apiPost } from '../api'
import { useI18n } from '../i18n.jsx'

export default function Header({ health, onReset, view, onGoDemo, onGoHome }) {
  const { locale, toggle, t } = useI18n()

  return (
    <header className="site-header sticky top-0 z-40 flex min-w-0 items-center gap-3 overflow-hidden border-b border-black/[0.06] bg-white/75 px-4 py-3 backdrop-blur-2xl md:px-8">
      <button
        onClick={onGoHome}
        className="group flex min-w-0 items-center gap-2.5"
        title={t('header.back_home')}
      >
        <span className="flex h-8 w-8 items-center justify-center rounded-[10px] bg-[#0071e3] text-sm text-white shadow-sm shadow-blue-500/20 transition-transform group-hover:scale-[1.03]">
          <i className="fa fa-shield"></i>
        </span>
        <h1 className="font-semibold tracking-[-0.015em] text-[#1d1d1f]">
          <span className="sm:hidden">waytoweb4 agent</span>
          <span className="hidden text-lg sm:inline">waytoweb4 copy-trading agent</span>
        </h1>
      </button>

      <div className="site-header__actions ml-auto flex min-w-0 items-center justify-end gap-2 text-xs">
        <div className="hidden items-center gap-2 xl:flex">
          <Pill label="Kiln" value={health?.kiln ?? '—'} />
          <Pill label="Passport" value={health?.passport_backend ?? '—'} />
          <Pill label={t('header.execution')} value={health?.execution_backend ?? '—'} />
        </div>

        <button
          onClick={toggle}
          className="nav-control flex min-h-9 items-center gap-1.5 px-3 py-1 text-slate-700"
          title={t('header.switch_language')}
        >
          <i className="fa fa-globe"></i>
          <span className="font-mono">
            {locale === 'en' ? t('header.lang.ko') : t('header.lang.en')}
          </span>
        </button>

        {view === 'home' ? (
          <button
            onClick={onGoDemo}
            className="primary-button hidden min-h-9 px-4 py-1.5 text-sm sm:block"
          >
            {t('header.try_demo')} <i className="fa fa-arrow-right ml-1"></i>
          </button>
        ) : (
          <button
            onClick={onGoHome}
            className="nav-control min-h-9 px-3 py-1 text-slate-700"
          >
            <i className="fa fa-arrow-left mr-1"></i> {t('header.back_home')}
          </button>
        )}

        <button
          onClick={onReset}
          className="nav-control hidden min-h-9 px-3 py-1 text-slate-700 sm:block"
          title={t('header.reset')}
        >
          <i className="fa fa-rotate-right mr-1"></i> {t('header.reset')}
        </button>
      </div>
    </header>
  )
}

function Pill({ label, value }) {
  return (
    <div className="flex items-center gap-1.5 rounded-full bg-black/[0.035] px-2.5 py-1">
      <span className="text-slate-500">{label}</span>
      <span className="font-mono text-[#1d1d1f]">{value}</span>
    </div>
  )
}
