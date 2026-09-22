import { useState } from 'react'
import { apiPost } from '../api'
import { useI18n } from '../i18n.jsx'

const DEMO_PROMPT = 'follow leader-demo-001 with 500 USD max loss 50 USD for 48 hours'

export default function ChatPanel({ onSpecLocked, draft, setDraft }) {
  const { t } = useI18n()
  const [input, setInput] = useState(DEMO_PROMPT)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)

  async function handleSend() {
    if (!input.trim() || busy) return
    setBusy(true)
    setError(null)
    try {
      const chk = await apiPost('/api/spec/check', { user_text: input })
      let spec
      if (chk.ready) {
        const r = await apiPost('/api/spec/emit', { user_text: input, draft_id: draft.draft_id })
        spec = r.spec
        setDraft((d) => ({
          ...d,
          history: [
            ...d.history,
            { role: 'user', text: input },
            { role: 'agent', text: t('chat.locked_note') },
          ],
        }))
      } else {
        const r = await apiPost('/api/spec/clarify', { user_text: input, draft_id: draft.draft_id })
        setDraft((d) => ({
          ...d,
          history: [
            ...d.history,
            { role: 'user', text: input },
            { role: 'agent', text: r.question || '(clarifying question)' },
          ],
        }))
        setBusy(false)
        return
      }
      setDraft((d) => ({ ...d, locked_spec: spec, passport_id: null, mint: null, draft_id: draft.draft_id }))
      onSpecLocked?.(spec)
    } catch (e) {
      setError(e.message || String(e))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="flex flex-col h-full bg-slate-900/40 border border-slate-800 rounded-lg overflow-hidden">
      <div className="px-4 py-2 border-b border-slate-800 text-sm uppercase tracking-wider text-slate-400">
        <i className="fa fa-comments mr-2"></i> Chat
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-2 text-sm">
        {draft.history.length === 0 && (
          <div className="text-slate-500 italic">{t('chat.empty')}</div>
        )}
        {draft.history.map((m, i) => (
          <div key={i} className={m.role === 'user' ? 'text-sky-300' : 'text-emerald-300'}>
            <span className="text-slate-500 mr-2">
              {m.role === 'user' ? t('chat.user_prefix') : t('chat.agent_prefix')}
            </span>
            {m.text}
          </div>
        ))}
      </div>

      {error && (
        <div className="px-4 py-2 bg-rose-900/40 border-t border-rose-700 text-xs text-rose-200">
          {error}
        </div>
      )}

      <div className="border-t border-slate-800 p-3 flex gap-2">
        <textarea
          rows={2}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          className="flex-1 bg-slate-950 border border-slate-700 rounded px-2 py-1 text-sm resize-none focus:outline-none focus:border-sky-500"
          placeholder={t('chat.placeholder')}
        />
        <button
          onClick={handleSend}
          disabled={busy}
          className="px-4 py-1 bg-sky-600 hover:bg-sky-500 disabled:opacity-50 rounded text-sm font-medium"
        >
          <i className="fa fa-paper-plane mr-1"></i>
          {t('chat.send')}
        </button>
      </div>
    </div>
  )
}