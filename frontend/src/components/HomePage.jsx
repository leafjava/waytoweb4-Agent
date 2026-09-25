import Hero from './Hero.jsx'
import PrimitivesGrid from './PrimitivesGrid.jsx'
import SecurityStrip from './SecurityStrip.jsx'
import StatTicker from './StatTicker.jsx'
import { useI18n } from '../i18n.jsx'

export default function HomePage({ snapshot, onTryDemo }) {
  const { t } = useI18n()

  return (
    <div className="home-page space-y-14 pb-12 md:space-y-20">
      <Hero onTryDemo={onTryDemo} />
      <StatTicker snapshot={snapshot} />
      <PrimitivesGrid />
      <SecurityStrip />

      <div className="home-final-cta rounded-[32px] bg-[#1d1d1f] px-6 py-14 text-center text-white md:py-20">
        <div className="mx-auto mb-6 max-w-xl text-3xl font-semibold tracking-[-0.035em] md:text-5xl">{t('home.headline')}</div>
        <button
          onClick={onTryDemo}
          className="rounded-full bg-white px-6 py-3 font-medium text-[#1d1d1f] transition-transform hover:scale-[1.02]"
        >
          {t('home.cta')}
          <i className="fa fa-arrow-right ml-2"></i>
        </button>
        <div className="mt-3 text-xs text-white/55">{t('home.cta_sub')}</div>
      </div>
    </div>
  )
}
