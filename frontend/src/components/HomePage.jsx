import Hero from './Hero.jsx'
import PrimitivesGrid from './PrimitivesGrid.jsx'
import JudgeChecklist from './JudgeChecklist.jsx'
import SecurityStrip from './SecurityStrip.jsx'
import SpecSimulator from './SpecSimulator.jsx'
import LiveDataPanel from './LiveDataPanel.jsx'
import StatTicker from './StatTicker.jsx'
import AcceptanceBar from './AcceptanceBar.jsx'
import { useI18n } from '../i18n.jsx'

export default function HomePage({ snapshot, onTryDemo }) {
  const { t } = useI18n()

  return (
    <div className="space-y-10 pb-12">
      <Hero onTryDemo={onTryDemo} />
      <StatTicker snapshot={snapshot} />
      <AcceptanceBar />
      <PrimitivesGrid />
      <JudgeChecklist />
      <SpecSimulator />
      <SecurityStrip />
      <LiveDataPanel snapshot={snapshot} />

      <div className="text-center pt-4">
        <button
          onClick={onTryDemo}
          className="px-6 py-3 rounded-lg bg-sky-500 hover:bg-sky-400 text-slate-950 font-medium shadow-lg shadow-sky-500/30"
        >
          {t('home.cta')}
          <i className="fa fa-arrow-right ml-2"></i>
        </button>
        <div className="text-xs text-slate-500 mt-2">{t('home.cta_sub')}</div>
      </div>
    </div>
  )
}