import { useState } from 'react'
import { apiPost } from '../api'
import { PASS_COLORS } from '../colors'

function CopyableHash({ label, value }) {
  const [copied, setCopied] = useState(false)
  if (!value) {
    return (
      <div className="flex justify-between text-xs">
        <span className="text-slate-400">{label}</span>
        <span className="text-slate-600">—</span>
      </div>
    )
  }
  async function copy() {
    try {
      await navigator.clipboard.writeText(value)
      setCopied(true)
      setTimeout(() => setCopied(false), 1200)
    } catch (_) { /* ignore */ }
  }
  return (
    <div className="text-xs">
      <div className="flex justify-between">
        <span className="text-slate-400">{label}</span>
        <button className="copy-btn" onClick={copy} title="Copy">
          <i className="fa fa-clipboard"></i> {copied ? 'copied' : 'copy'}
        </button>
      </div>
      <div className="txhash text-slate-200">{value}</div>
    </div>
  )
}

export default function PassportCard({ draft, snapshot, onAction }) {
  const passport = draft.passport_id ? snapshot?.passports?.[draft.passport_id] : null
  const mint = draft.mint
  const [busy, setBusy] = useState(null)

  async function call(path, body) {
    if (!draft.passport_id) return
    setBusy(path)
    try {
      await apiPost(path, body ?? { passport_id: draft.passport_id })
      onAction?.()
    } catch (e) {
      alert(`action failed: ${e.message || e}`)
    } finally {
      setBusy(null)
    }
  }

  if (!draft.passport_id) {
    return (
      <div className="bg-slate-900/40 border border-slate-800 rounded-lg p-4">
        <h2 className="text-sm uppercase tracking-wider text-slate-400 mb-2">
          <i className="fa fa-id-card-o mr-2"></i> Passport
        </h2>
        <div className="text-slate-500 italic text-sm">No passport yet. Lock a Spec first.</div>
      </div>
    )
  }

  const status = passport?.status ?? mint?.status ?? 'pending_face'
  const palette = PASS_COLORS[status] ?? PASS_COLORS.pending_face
  const faceVerified = !!passport?.face_verified

  return (
    <div className={`bg-slate-900/40 border ${palette.border} rounded-lg p-4 space-y-2`}>
      <div className="flex items-center justify-between">
        <h2 className="text-sm uppercase tracking-wider text-slate-400">
          <i className="fa fa-id-card-o mr-2"></i> Passport
        </h2>
        <span className={`text-xs px-2 py-0.5 rounded ${palette.bg} ${palette.fg} border ${palette.border}`}>
          {status}
        </span>
      </div>

      <div className="text-xs space-y-2">
        <div>
          <div className="text-slate-400">id</div>
          <div className="txhash text-slate-200">{draft.passport_id}</div>
        </div>
        <CopyableHash label="spec hash" value={passport?.spec_hash ?? mint?.spec_hash} />
        <CopyableHash label="mint tx" value={passport?.tx_mint_hash ?? mint?.tx_hash} />
        <CopyableHash label="revoke tx" value={passport?.tx_revoke_hash} />
        <div className="flex justify-between text-xs">
          <span className="text-slate-400">face</span>
          <span className={faceVerified ? 'text-emerald-300' : 'text-amber-300'}>
            {faceVerified ? 'verified' : 'not verified'}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2 pt-2">
        <button
          disabled={faceVerified || status === 'revoked' || busy === '/api/face/verify'}
          onClick={() => call('/api/face/verify')}
          className="px-2 py-1.5 rounded bg-amber-600 hover:bg-amber-500 disabled:opacity-50 text-xs"
        >
          <i className="fa fa-user-circle-o mr-1"></i>
          {faceVerified ? 'Face OK' : 'Verify Face'}
        </button>
        <button
          disabled={!faceVerified || status === 'revoked' || passport?.engine_running || busy === '/api/engine/start'}
          onClick={() => call('/api/engine/start')}
          className="px-2 py-1.5 rounded bg-sky-600 hover:bg-sky-500 disabled:opacity-50 text-xs"
        >
          <i className="fa fa-play mr-1"></i>
          {passport?.engine_running ? 'Engine running' : 'Start Engine'}
        </button>
      </div>
    </div>
  )
}
