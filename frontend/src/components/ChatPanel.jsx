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
    <div className="surface-card flex h-full flex-col overflow-hidden">
      <div className="border-b border-black/10 px-5 py-4 text-sm font-semibold text-[#1d1d1f]">
        <i className="fa fa-comments mr-2"></i> Chat
      </div>

      <div className="flex-1 space-y-3 overflow-y-auto p-5 text-sm">
        {draft.history.length === 0 && (
          <div className="text-slate-500 italic">{t('chat.empty')}</div>
        )}
        {draft.history.map((m, i) => (
          <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[88%] rounded-2xl px-4 py-2.5 leading-6 ${m.role === 'user' ? 'rounded-br-md bg-[#0071e3] text-white' : 'rounded-bl-md bg-black/[0.055] text-[#1d1d1f]'}`}>
              <span className={`mb-0.5 block text-[10px] font-semibold uppercase tracking-wider ${m.role === 'user' ? 'text-white/65' : 'text-slate-500'}`}>
                {m.role === 'user' ? t('chat.user_prefix') : t('chat.agent_prefix')}
              </span>
              {m.text}
            </div>
          </div>
        ))}
      </div>

      {error && (
        <div className="px-4 py-2 bg-rose-50 border-t border-rose-200 text-xs text-rose-700">
          {error}
        </div>
      )}

      <div className="flex gap-2 border-t border-black/10 p-4">
        <textarea
          rows={2}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          className="min-w-0 flex-1 resize-none rounded-2xl border border-black/10 bg-black/[0.035] px-3 py-2 text-sm focus:border-blue-400 focus:outline-none"
          placeholder={t('chat.placeholder')}
        />
        <button
          onClick={handleSend}
          disabled={busy}
          className="primary-button px-4 py-1 text-sm font-medium disabled:opacity-50"
        >
          <i className="fa fa-paper-plane mr-1"></i>
          {t('chat.send')}
        </button>
      </div>
    </div>
  )
}
