import { apiPost } from '../api'
import { useI18n } from '../i18n.jsx'

export default function Header({ health, onReset, view, onGoDemo, onGoHome }) {
  const { locale, toggle, t } = useI18n()

  return (
    <header className="site-header flex min-w-0 items-center gap-3 overflow-hidden border-b border-slate-800 bg-slate-900/70 px-4 py-3 md:px-6">
      <button
        onClick={onGoHome}
        className="flex min-w-0 items-center gap-2 hover:opacity-80"
        title={t('header.back_home')}
      >
        <i className="fa fa-bolt text-amber-400"></i>
        <h1 className="font-semibold tracking-wide">
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
          className="flex min-h-9 items-center gap-1.5 rounded border border-slate-700 bg-slate-800 px-2.5 py-1 text-slate-200 hover:bg-slate-700"
          title="Switch language"
        >
          <i className="fa fa-globe"></i>
          <span className="font-mono">{
            // Show the label of the NEXT locale so users see what they will get.
            locale === 'en' ? t('header.lang.zh')
              : locale === 'zh' ? t('header.lang.ko')
              : t('header.lang.en')
          }</span>
        </button>

        {view === 'home' ? (
          <button
            onClick={onGoDemo}
            className="hidden min-h-9 rounded bg-sky-600 px-3 py-1 font-medium text-white hover:bg-sky-500 sm:block"
          >
            {t('header.try_demo')} <i className="fa fa-arrow-right ml-1"></i>
          </button>
        ) : (
          <button
            onClick={onGoHome}
            className="min-h-9 rounded border border-slate-700 bg-slate-800 px-3 py-1 text-slate-200 hover:bg-slate-700"
          >
            <i className="fa fa-arrow-left mr-1"></i> {t('header.back_home')}
          </button>
        )}

        <button
          onClick={onReset}
          className="hidden min-h-9 rounded border border-slate-700 bg-slate-800 px-3 py-1 text-slate-200 hover:bg-slate-700 sm:block"
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
    <div className="flex items-center gap-1.5 px-2 py-1 rounded bg-slate-800 border border-slate-700">
      <span className="text-slate-400">{label}:</span>
      <span className="text-slate-100 font-mono">{value}</span>
    </div>
  )
}
