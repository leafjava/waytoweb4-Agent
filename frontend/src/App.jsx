import { useState } from 'react'
import Header from './components/Header.jsx'
import ChatPanel from './components/ChatPanel.jsx'
import SpecCard from './components/SpecCard.jsx'
import PassportCard from './components/PassportCard.jsx'
import RedLinePanel from './components/RedLinePanel.jsx'
import { apiGet, apiPost } from './api'
import { usePoll } from './usePoll'

const INITIAL_DRAFT = {
  draft_id: 'draft-' + Math.random().toString(36).slice(2, 8),
  history: [],
  locked_spec: null,
  passport_id: null,
  mint: null,
}

export default function App() {
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
    setDraft({ ...INITIAL_DRAFT, draft_id: 'draft-' + Math.random().toString(36).slice(2, 8) })
  }

  // Trigger a snapshot refresh after a mutating action by re-polling.
  // The /api/state poller will pick it up within 1.5s.
  function refreshSoon() { /* no-op: poll does the work */ }

  return (
    <div className="min-h-screen flex flex-col">
      <Header health={health} onReset={handleReset} />
      <main className="flex-1 grid grid-cols-12 gap-4 p-4">
        <section className="col-span-5 min-h-[70vh]">
          <ChatPanel
            draft={draft}
            setDraft={setDraft}
            onSpecLocked={() => {}}
          />
        </section>
        <section className="col-span-7 space-y-4">
          <SpecCard
            draft={draft}
            setDraft={setDraft}
            onMinted={() => {}}
          />
          <PassportCard
            draft={draft}
            snapshot={snapshot}
            onAction={refreshSoon}
          />
          <RedLinePanel
            draft={draft}
            snapshot={snapshot}
            onAction={refreshSoon}
          />
          <div className="bg-slate-900/40 border border-slate-800 rounded-lg p-3">
            <div className="text-xs text-slate-400 mb-1">token / energy report (paste into README §9)</div>
            <pre className="text-[11px] text-slate-200 whitespace-pre-wrap font-mono">
{snapshot?.token_report || '—'}
            </pre>
          </div>
        </section>
      </main>
    </div>
  )
}
