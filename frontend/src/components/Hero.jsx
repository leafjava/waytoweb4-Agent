import { useI18n } from '../i18n.jsx'

export default function Hero({ onTryDemo }) {
  const { t } = useI18n()

  return (
    <section className="hero-command hero-cinematic relative overflow-hidden px-6 py-12 md:px-14 md:py-16">
      <video className="hero-cinematic__video" autoPlay muted loop playsInline preload="auto" disablePictureInPicture aria-hidden="true" poster="https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260912_105822_bf7c2d53-9957-4521-bbbf-7c1ab7a70130.png">
        <source src="https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260912_105953_21ad8049-9088-4a00-bad3-aee6b5575a2b.mp4" type="video/mp4" />
      </video>
      <div className="hero-cinematic__veil" aria-hidden="true"></div>
      <div className="hero-command__beam" aria-hidden="true"></div>
      <div className="hero-command__layout relative grid min-w-0 items-center gap-10">
        <div className="hero-command__copy min-w-0">
          <p className="hero-cinematic__eyebrow mb-4 text-sm font-semibold tracking-tight">{t('hero.tagline')}</p>
          <h1 className="max-w-2xl text-5xl font-semibold leading-[1.02] tracking-[-0.05em] text-[#1d1d1f] md:text-7xl">
            {t('hero.title.line1')}
            <br />
            <span className="text-[#6e6e73]">{t('hero.title.line2')}</span>
          </h1>

          <p className="hero-cinematic__declaration mt-6 max-w-xl text-lg leading-relaxed md:text-xl">
            {t('hero.declaration')}
          </p>

          <p className="hero-cinematic__route mt-4 max-w-xl text-xs leading-relaxed md:text-sm">
            {t('hero.product')}
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
        <aside className="sentinel-panel" aria-label={t('motion.aria')}>
          <div className="sentinel-panel__head">
            <div>
              <span>{t('hero.tagline')}</span>
              <strong>{t('motion.core')}</strong>
            </div>
            <div className="sentinel-panel__shield" aria-hidden="true">
              <i className="fa fa-shield"></i>
            </div>
          </div>
          <div className="sentinel-panel__steps">
            <span><b>01</b>{t('motion.proof.spec_value')}</span>
            <span><b>02</b>{t('motion.proof.gate_value')}</span>
            <span><b>03</b>{t('motion.proof.mode_value')}</span>
          </div>
          <div className="sentinel-panel__track"><i></i></div>
        </aside>
      </div>
    </section>
  )
}
