import { apiPost } from '../api'

export default function SpecCard({ draft, setDraft, onMinted }) {
  const spec = draft.locked_spec

  async function handleLock() {
    if (!spec) return
    try {
      const r = await apiPost('/api/passport/mint', { spec })
      setDraft((d) => ({ ...d, passport_id: r.passport_id, mint: r }))
      onMinted?.(r)
    } catch (e) {
      // surface inline via console; user can also see error in ChatPanel if needed.
      console.error(e)
      alert(`mint failed: ${e.message || e}`)
    }
  }

  return (
    <div className="bg-slate-900/40 border border-slate-800 rounded-lg p-4">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-sm uppercase tracking-wider text-slate-400">
          <i className="fa fa-file-text-o mr-2"></i> Spec
        </h2>
        {spec && (
          <span className="text-xs px-2 py-0.5 rounded bg-cyan-900/40 border border-cyan-700 text-cyan-200">
            locked
          </span>
        )}
      </div>

      {!spec ? (
        <div className="text-slate-500 italic text-sm">
          No spec yet. Send a message in Chat to fill in the fields.
        </div>
      ) : (
        <div className="space-y-1.5 text-sm font-mono">
          <Row k="leader" v={spec.leaderId} />
          <Row k="notional" v={`${spec.notionalUsd} USD`} />
          <Row k="max loss" v={`${spec.maxLossUsd} USD`} />
          <Row k="expiry" v={spec.expiry} />
          <Row k="venue" v={spec.venue} />
          <Row k="paper" v={String(spec.paper)} />
        </div>
      )}

      <div className="mt-4">
        <button
          disabled={!spec || draft.passport_id}
          onClick={handleLock}
          className="w-full px-3 py-2 rounded bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-sm font-medium"
        >
          <i className="fa fa-link mr-1"></i>
          {draft.passport_id ? 'Spec locked in passport' : 'Lock Spec & Mint Passport'}
        </button>
      </div>
    </div>
  )
}

function Row({ k, v }) {
  return (
    <div className="flex justify-between gap-4">
      <span className="text-slate-400">{k}</span>
      <span className="text-slate-100 text-right break-all">{v}</span>
    </div>
  )
}
