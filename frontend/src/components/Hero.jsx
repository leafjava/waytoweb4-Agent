import { ONE_LINE_DECLARATION, ONE_LINE_PRODUCT } from '../constants'
import { useI18n } from '../i18n.jsx'
import ChainMandateMotion from './ChainMandateMotion.jsx'

export default function Hero({ onTryDemo }) {
  const { t } = useI18n()

  return (
    <section className="hero-command relative overflow-hidden border border-slate-800 bg-slate-950 px-6 py-8 md:px-10 md:py-10">
      <div className="hero-command__beam" aria-hidden="true"></div>
      <div className="hero-command__layout relative grid min-w-0 items-center gap-10">
        <div className="hero-command__copy min-w-0">
          <h1 className="max-w-2xl text-4xl font-semibold leading-[1.06] tracking-[-0.035em] text-slate-50 md:text-5xl">
            {t('hero.title.line1')}
            <br />
            <span className="text-sky-300">{t('hero.title.line2')}</span>
          </h1>

          <p className="mt-5 max-w-2xl text-base leading-relaxed text-slate-300 md:text-lg">
            {ONE_LINE_DECLARATION}
          </p>

          <p className="mt-4 max-w-xl font-mono text-xs leading-relaxed text-slate-500 md:text-sm">
            {ONE_LINE_PRODUCT}
          </p>

          <div className="mt-7 flex flex-wrap items-center gap-3">
            <button
              onClick={onTryDemo}
              className="hero-command__primary px-5 py-2.5 bg-sky-400 hover:bg-sky-300 text-slate-950 font-semibold shadow-lg shadow-sky-500/20 transition-colors"
            >
              {t('hero.cta')}
              <i className="fa fa-arrow-right ml-2"></i>
            </button>
            <a
              href="https://docs.google.com/document/d/13qh7oePGl7Flrl-Zh_A6hfr02L266PvS/edit"
              target="_blank"
              rel="noopener noreferrer"
              className="hero-command__secondary px-5 py-2.5 bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-700 transition-colors"
            >
              <i className="fa fa-file-text-o mr-1"></i>
              {t('hero.prd')}
            </a>
          </div>

          <p className="hero-command__challenge mt-5 flex items-center gap-2 text-xs leading-relaxed text-sky-200/80">
            <i className="fa fa-bolt" aria-hidden="true"></i>
            {t('hero.eyebrow')}
          </p>
        </div>
        <ChainMandateMotion />
      </div>
    </section>
  )
}
