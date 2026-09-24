import { ONE_LINE_DECLARATION, ONE_LINE_PRODUCT } from '../constants'
import { useI18n } from '../i18n.jsx'
import ChainMandateMotion from './ChainMandateMotion.jsx'

export default function Hero({ onTryDemo }) {
  const { t } = useI18n()

  return (
    <section className="hero-command relative overflow-hidden px-6 py-12 md:px-14 md:py-16">
      <div className="hero-command__beam" aria-hidden="true"></div>
      <div className="hero-command__layout relative grid min-w-0 items-center gap-10">
        <div className="hero-command__copy min-w-0">
          <p className="mb-4 text-sm font-semibold tracking-tight text-[#0071e3]">AI agent controls for finance</p>
          <h1 className="max-w-2xl text-5xl font-semibold leading-[1.02] tracking-[-0.05em] text-[#1d1d1f] md:text-7xl">
            {t('hero.title.line1')}
            <br />
            <span className="text-[#6e6e73]">{t('hero.title.line2')}</span>
          </h1>

          <p className="mt-6 max-w-xl text-lg leading-relaxed text-[#6e6e73] md:text-xl">
            {ONE_LINE_DECLARATION}
          </p>

          <p className="mt-4 max-w-xl text-xs leading-relaxed text-slate-500 md:text-sm">
            {ONE_LINE_PRODUCT}
          </p>

          <div className="mt-7 flex flex-wrap items-center gap-3">
            <button
              onClick={onTryDemo}
              className="primary-button hero-command__primary px-6 py-2.5 font-medium"
            >
              {t('hero.cta')}
              <i className="fa fa-arrow-right ml-2"></i>
            </button>
            <a
              href="https://docs.google.com/document/d/13qh7oePGl7Flrl-Zh_A6hfr02L266PvS/edit"
              target="_blank"
              rel="noopener noreferrer"
              className="secondary-button hero-command__secondary px-6 py-2.5 font-medium"
            >
              <i className="fa fa-file-text-o mr-1"></i>
              {t('hero.prd')}
            </a>
          </div>

          <p className="hero-command__challenge mt-5 flex items-center gap-2 text-xs leading-relaxed text-slate-500">
            <i className="fa fa-bolt" aria-hidden="true"></i>
            {t('hero.eyebrow')}
          </p>
        </div>
        <ChainMandateMotion />
      </div>
    </section>
  )
}
