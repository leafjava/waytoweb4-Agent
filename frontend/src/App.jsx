import { useState } from 'react'
import Header from './components/Header.jsx'
import ChatPanel from './components/ChatPanel.jsx'
import SpecCard from './components/SpecCard.jsx'
import PassportCard from './components/PassportCard.jsx'
import RedLinePanel from './components/RedLinePanel.jsx'
import HomePage from './components/HomePage.jsx'
import { apiPost } from './api'
import { usePoll } from './usePoll'
import InferenceEvidencePanel from './components/InferenceEvidencePanel.jsx'

const INITIAL_DRAFT = () => ({
  draft_id: 'draft-' + Math.random().toString(36).slice(2, 8),
  history: [],
  locked_spec: null,
  passport_id: null,
  mint: null,
})

export default function App() {
  const [view, setView] = useState('home')
  const [draft, setDraft] = useState(INITIAL_DRAFT)
  const { data: snapshot } = usePoll('/api/state', 1500)
  const { data: health } = usePoll('/api/health', 5000)

  async function handleReset() {
    try {
      await apiPost('/api/state/reset', null)
    } catch (e) {
      alert(`reset failed: ${e.message || e}`)
      return
    }
    setDraft(INITIAL_DRAFT())
  }

  return (
    <div className="min-h-screen flex flex-col">
      <Header
        health={health}
        onReset={handleReset}
        view={view}
        onGoDemo={() => setView('demo')}
        onGoHome={() => setView('home')}
      />
      <main className="mx-auto w-full max-w-7xl flex-1 overflow-x-clip p-4 md:p-6">
        {view === 'home' ? (
          <HomePage snapshot={snapshot} onTryDemo={() => setView('demo')} />
        ) : (
          <div className="grid grid-cols-12 gap-4">
            <section className="col-span-12 min-h-[60vh] lg:col-span-5 lg:min-h-[70vh]">
              <ChatPanel draft={draft} setDraft={setDraft} onSpecLocked={() => {}} />
            </section>
            <section className="col-span-12 space-y-4 lg:col-span-7">
              <SpecCard draft={draft} setDraft={setDraft} onMinted={() => {}} />
              <PassportCard draft={draft} snapshot={snapshot} onAction={() => {}} />
              <RedLinePanel draft={draft} snapshot={snapshot} onAction={() => {}} />
              <InferenceEvidencePanel snapshot={snapshot} />
            </section>
          </div>
        )}
      </main>
    </div>
  )
}
