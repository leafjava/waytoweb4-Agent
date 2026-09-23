import { apiPost } from '../api'
import { useI18n } from '../i18n.jsx'

export default function Header({ health, onReset, view, onGoDemo, onGoHome }) {
  const { locale, toggle, t } = useI18n()

  return (
    <header className="px-6 py-3 border-b border-slate-800 bg-slate-900/70 flex items-center gap-4">
      <button
        onClick={onGoHome}
        className="flex items-center gap-2 hover:opacity-80"
        title={t('header.back_home')}
      >
        <i className="fa fa-bolt text-amber-400"></i>
        <h1 className="text-lg font-semibold tracking-wide">
          waytoweb4 copy-trading agent
        </h1>
      </button>

      <div className="ml-auto flex items-center gap-3 text-xs">
        <Pill label="Kiln" value={health?.kiln ?? '—'} />
        <Pill label="Passport" value={health?.passport_backend ?? '—'} />

        <button
          onClick={toggle}
          className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200"
          title="Switch language"
        >
          <i className="fa fa-globe"></i>
          <span className="font-mono">{locale === 'en' ? t('header.lang.ko') : t('header.lang.en')}</span>
        </button>

        {view === 'home' ? (
          <button
            onClick={onGoDemo}
            className="px-3 py-1 rounded bg-sky-600 hover:bg-sky-500 text-white font-medium"
          >
            {t('header.try_demo')} <i className="fa fa-arrow-right ml-1"></i>
          </button>
        ) : (
          <button
            onClick={onGoHome}
            className="px-3 py-1 rounded bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200"
          >
            <i className="fa fa-arrow-left mr-1"></i> {t('header.back_home')}
          </button>
        )}

        <button
          onClick={onReset}
          className="px-3 py-1 rounded bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200"
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