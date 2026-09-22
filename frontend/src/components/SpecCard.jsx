import { apiPost } from '../api'

function requestId(prefix) {
  const id = globalThis.crypto?.randomUUID?.() || Math.random().toString(36).slice(2)
  return `${prefix}-${id}`
}

export default function SpecCard({ draft, setDraft, onMinted }) {
  const spec = draft.locked_spec
  const prepared = !!draft.passport_id
  const confirmed = draft.mint?.status === 'confirmed' || draft.mint?.status === 'authorized' || draft.mint?.status === 'mint_pending'
  const busy = draft.busy

  async function handleAction() {
    if (!spec || busy) return
    setDraft((d) => ({ ...d, busy: true }))
    try {
      if (!prepared) {
        const r = await apiPost('/api/passport/prepare', { spec, request_id: requestId('prepare') })
        setDraft((d) => ({ ...d, passport_id: r.passport_id, mint: r }))
        return
      }
      if (!draft.confirmed) {
        const r = await apiPost('/api/passport/confirm', { passport_id: draft.passport_id, spec_hash: draft.mint.spec_hash, request_id: requestId('confirm') })
        setDraft((d) => ({ ...d, confirmed: true, mint: r }))
        const minted = await apiPost('/api/passport/mint', { passport_id: draft.passport_id, request_id: requestId('mint') })
        setDraft((d) => ({ ...d, mint: minted }))
        onMinted?.(minted)
      }
    } catch (e) {
      alert(`authorization failed: ${e.message || e}`)
    } finally {
      setDraft((d) => ({ ...d, busy: false }))
    }
  }

  return (
    <div className="bg-slate-900/40 border border-slate-800 rounded-lg p-4">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-sm uppercase tracking-wider text-slate-400"><i className="fa fa-file-text-o mr-2"></i> Spec</h2>
        {spec && <span className="text-xs px-2 py-0.5 rounded bg-cyan-900/40 border border-cyan-700 text-cyan-200">frozen</span>}
      </div>
      {!spec ? <div className="text-slate-500 italic text-sm">No spec yet. Send a message in Chat to fill in the fields.</div> : (
        <div className="space-y-1.5 text-sm font-mono">
          <Row k="leader" v={spec.leaderId} /><Row k="notional" v={`${spec.notionalUsd} USD`} /><Row k="max loss" v={`${spec.maxLossUsd} USD`} />
          <Row k="expiry" v={spec.expiry} /><Row k="venue" v={spec.venue} /><Row k="paper" v={String(spec.paper)} />
          {draft.mint?.spec_hash && <Row k="intent hash" v={draft.mint.spec_hash} />}
        </div>
      )}
      <div className="mt-4">
        <button disabled={!spec || confirmed || busy} onClick={handleAction} className="w-full px-3 py-2 rounded bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-sm font-medium">
          <i className="fa fa-link mr-1"></i>{busy ? 'Working…' : !prepared ? 'Prepare Passport' : !draft.confirmed ? 'Confirm & Mint Passport' : 'Passport authorized'}
        </button>
      </div>
    </div>
  )
}

function Row({ k, v }) { return <div className="flex justify-between gap-4"><span className="text-slate-400">{k}</span><span className="text-slate-100 text-right break-all">{v}</span></div> }
