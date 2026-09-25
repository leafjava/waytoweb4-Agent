import { useEffect, useState } from 'react'
import Header from './components/Header.jsx'
import ChatPanel from './components/ChatPanel.jsx'
import SpecCard from './components/SpecCard.jsx'
import PassportCard from './components/PassportCard.jsx'
import RedLinePanel from './components/RedLinePanel.jsx'
import HomePage from './components/HomePage.jsx'
import ConditionalRunPanel from './components/ConditionalRunPanel.jsx'
import { apiPost } from './api'
import { usePoll } from './usePoll'
import InferenceEvidencePanel from './components/InferenceEvidencePanel.jsx'
import { useI18n } from './i18n.jsx'

const INITIAL_DRAFT = () => ({
  draft_id: 'draft-' + Math.random().toString(36).slice(2, 8),
  history: [],
  locked_spec: null,
  passport_id: null,
  mint: null,
})

async function fetchLatestTwoRuns() {
  try {
    const res = await fetch('/runs/latest.json', { cache: 'no-store' })
    if (!res.ok) return null
    return await res.json()
  } catch {
    return null
  }
}

export default function App() {
  const { t } = useI18n()
  const [view, setView] = useState('home')
  const [draft, setDraft] = useState(INITIAL_DRAFT)
  const { data: snapshot } = usePoll('/api/state', 1500)
  const { data: health } = usePoll('/api/health', 5000)

  async function handleReset() {
    try {
      await apiPost('/api/state/reset', null)
    } catch (e) {
      alert(`${t('common.reset_failed')}: ${e.message || e}`)
      return
    }
    setDraft(INITIAL_DRAFT())
  }

  return (
    <div className="app-shell min-h-screen flex flex-col">
      <Header
        health={health}
        onReset={handleReset}
        view={view}
        onGoDemo={() => setView('demo')}
        onGoHome={() => setView('home')}
      />
      <main className="mx-auto w-full max-w-[1280px] flex-1 overflow-x-clip px-4 pb-12 pt-6 md:px-8 md:pt-10">
        {view === 'home' ? (
          <HomePage snapshot={snapshot} onTryDemo={() => setView('demo')} />
        ) : (
          <DemoView
            snapshot={snapshot}
            draft={draft}
            setDraft={setDraft}
          />
        )}
      </main>
    </div>
  )
}
function DemoView({ snapshot, draft, setDraft }) {
  const [latestRuns, setLatestRuns] = useState(null)
  useEffect(() => {
    fetchLatestTwoRuns().then(setLatestRuns)
    const id = setInterval(() => fetchLatestTwoRuns().then(setLatestRuns), 5000)
    return () => clearInterval(id)
  }, [])
  return (
    <div className="demo-grid grid grid-cols-12 gap-5 lg:gap-6">
      <section className="col-span-12 min-h-[60vh] lg:col-span-5 lg:min-h-[70vh]">
        <ChatPanel draft={draft} setDraft={setDraft} onSpecLocked={() => {}} />
      </section>
      <section className="col-span-12 space-y-4 lg:col-span-7">
        <SpecCard draft={draft} setDraft={setDraft} onMinted={() => {}} />
        <PassportCard draft={draft} snapshot={snapshot} onAction={() => {}} />
        <RedLinePanel draft={draft} snapshot={snapshot} onAction={() => {}} />
        <ConditionalRunPanel latestRuns={latestRuns} />
        <InferenceEvidencePanel snapshot={snapshot} />
      </section>
    </div>
  )
}
