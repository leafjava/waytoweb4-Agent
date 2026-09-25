import { useState } from 'react'
import { apiPost } from '../api'
import { PASS_COLORS } from '../colors'
import { useI18n } from '../i18n.jsx'
import HumanGate from './HumanGate.jsx'
import Pill, { TONE_FOR } from './Pill.jsx'
import JsonView from './JsonView.jsx'
import Advanced from './Advanced.jsx'

function CopyableHash({ label, value, copyText, copiedText }) {
  const { t } = useI18n()
  const [copied, setCopied] = useState(false)
  if (!value) {
    return (
      <div className="flex justify-between text-xs">
        <span className="text-slate-500">{label}</span>
        <span className="text-slate-400">—</span>
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
        <span className="text-slate-500">{label}</span>
        <button className="copy-btn" onClick={copy} title={copyText}>
          <i className="fa fa-clipboard"></i> {copied ? copiedText : copyText}
        </button>
      </div>
      <div className="txhash text-slate-800">{value}</div>
    </div>
  )
}

export default function PassportCard({ draft, snapshot, onAction }) {
  const { locale, t } = useI18n()
  const passport = draft.passport_id ? snapshot?.passports?.[draft.passport_id] : null
  const mint = draft.mint
  const [busy, setBusy] = useState(null)
  const [gateOpen, setGateOpen] = useState(false)

  async function call(path, body) {
    if (!draft.passport_id) return
    setBusy(path)
    try {
      await apiPost(path, body ?? { passport_id: draft.passport_id })
      onAction?.()
    } catch (e) {
      alert(`${t('pass.action_failed')}: ${e.message || e}`)
    } finally {
      setBusy(null)
    }
  }

  if (!draft.passport_id) {
    return (
      <div className="surface-card border border-black/10 rounded-lg p-4">
        <h2 className="text-sm uppercase tracking-wider text-slate-500 mb-2">
          <i className="fa fa-id-card-o mr-2"></i> {t('pass.title')}
        </h2>
        <div className="text-slate-500 italic text-sm">{t('pass.empty')}</div>
      </div>
    )
  }

  const status = passport?.status ?? mint?.status ?? 'pending_face'
  const palette = PASS_COLORS[status] ?? PASS_COLORS.pending_face
  const faceVerified = !!passport?.face_verified
  const gateStatus = passport?.face_gate_status ?? 'pending'
  const authorizationReady = passport?.authorization_status === 'authorized'
  const executionProvider = passport?.external_execution_provider
  const executionId = passport?.external_execution_id
  const executionStatus = passport?.external_execution_status
  const executionTone = executionStatus === 'running'
    ? 'border-emerald-200 bg-emerald-50 text-emerald-700'
    : executionStatus
      ? 'border-black/10 bg-white text-slate-700'
      : ''

  return (
    <div className={`surface-card border ${palette.border} rounded-lg p-4 space-y-2`}>
      <div className="flex items-center justify-between">
        <h2 className="text-sm uppercase tracking-wider text-slate-500">
          <i className="fa fa-id-card-o mr-2"></i> {t('pass.title')}
        </h2>
        <span className={`text-xs px-2 py-0.5 rounded ${palette.bg} ${palette.fg} border ${palette.border}`}>
          <Pill tone={TONE_FOR[status] ?? 'neutral'}>{status}</Pill>
        </span>
      </div>

      <div className="text-xs space-y-2">
        <div>
          <div className="text-slate-500">{t('pass.id')}</div>
          <div className="txhash text-slate-800">{draft.passport_id}</div>
        </div>
        <CopyableHash
          label={t('pass.spec_hash')}
          value={passport?.spec_hash ?? mint?.spec_hash}
          copyText={t('pass.copy')}
          copiedText={t('pass.copied')}
        />
        <CopyableHash
          label={t('pass.mint_tx')}
          value={passport?.tx_mint_hash ?? mint?.tx_hash}
          copyText={t('pass.copy')}
          copiedText={t('pass.copied')}
        />
        <CopyableHash
          label={t('pass.revoke_tx')}
          value={passport?.tx_revoke_hash}
          copyText={t('pass.copy')}
          copiedText={t('pass.copied')}
        />
        <div className="flex justify-between text-xs">
          <span className="text-slate-500">{t('pass.face')}</span>
          <span className={faceVerified ? 'text-emerald-700' : 'text-amber-700'}>
            {faceVerified
              ? gateStatus === 'invalidated' ? t('pass.face_historical') : t('pass.face_verified')
              : t('pass.face_not_verified')}
          </span>
        </div>
        {passport?.face_verified_at && (
          <>
            <div className="flex justify-between gap-4 text-xs">
              <span className="text-slate-500">{t('pass.verified_at')}</span>
              <span className="min-w-0 break-words text-right text-slate-800">
                {new Intl.DateTimeFormat(locale === 'ko' ? 'ko-KR' : 'en-US', { dateStyle: 'medium', timeStyle: 'medium' }).format(new Date(passport.face_verified_at))}
              </span>
            </div>
            <div className="flex justify-between gap-4 text-xs">
              <span className="text-slate-500">{t('pass.gate_status')}</span>
              <span className={gateStatus === 'invalidated' ? 'text-rose-700' : 'text-cyan-700'}>
                {t(`pass.gate_${gateStatus}`)}
              </span>
            </div>
            <div className="flex justify-between gap-4 text-xs">
              <span className="text-slate-500">{t('pass.method')}</span>
              <span className="text-slate-800">{passport.face_verification_method}</span>
            </div>
            <div className="text-xs">
              <div className="text-slate-500">{t('pass.session')}</div>
              <div className="txhash text-slate-800">{passport.face_verification_session_id}</div>
            </div>
          </>
        )}
        {gateStatus === 'invalidated' && (
          <div className="rounded-xl bg-rose-50 p-3 text-xs leading-5 text-rose-700" role="status">
            <i className="fa fa-ban mr-2" aria-hidden="true"></i>
            {t('pass.gate_invalidated_help')}
            {passport?.face_gate_invalidation_reason && (
              <span className="mt-1 block font-mono text-rose-700">
                {passport.face_gate_invalidation_reason}
              </span>
            )}
          </div>
        )}
        {(executionProvider || executionId || executionStatus) && (
          <div className="mt-3 border-t border-black/10 pt-3">
            <div className="mb-2 flex items-center justify-between gap-3">
              <span className="text-slate-500">{t('pass.execution_backend')}</span>
              <span className="font-mono text-blue-700">{executionProvider}</span>
            </div>
            {executionId && (
              <CopyableHash
                label={t('pass.trader_id')}
                value={executionId}
                copyText={t('pass.copy')}
                copiedText={t('pass.copied')}
              />
            )}
            {executionStatus && (
              <div className="mt-2 flex items-center justify-between gap-3">
                <span className="text-slate-500">{t('pass.execution_status')}</span>
                <span className={`rounded border px-2 py-0.5 font-mono ${executionTone}`}>
                  {executionStatus}
                </span>
              </div>
            )}
          </div>
        )}
      </div>

      <Advanced title="Raw passport payload" storageKey={`passport.${draft.passport_id}.raw`}>
        <JsonView value={passport} />
      </Advanced>

      <div className="grid grid-cols-2 gap-2 pt-2">
        <button
          disabled={!authorizationReady || faceVerified || status === 'revoked' || busy === '/api/face/verify'}
          onClick={() => setGateOpen(true)}
          className="px-2 py-1.5 rounded bg-amber-600 hover:bg-amber-500 disabled:opacity-50 text-xs"
        >
          <i className="fa fa-user-circle-o mr-1"></i>
          {faceVerified
            ? t('pass.face_ok')
            : authorizationReady ? t('pass.verify_face') : t('pass.authorize_first')}
        </button>
        <button
          disabled={!faceVerified || gateStatus !== 'active' || status === 'revoked' || passport?.engine_running || busy === '/api/engine/start'}
          onClick={() => call('/api/engine/start')}
          className="px-2 py-1.5 rounded bg-sky-600 hover:bg-sky-500 disabled:opacity-50 text-xs"
        >
          <i className="fa fa-play mr-1"></i>
          {passport?.engine_running ? t('pass.engine_running') : t('pass.start_engine')}
        </button>
      </div>
      <HumanGate
        open={gateOpen}
        passport={passport}
        spec={draft.locked_spec}
        onClose={() => setGateOpen(false)}
        onComplete={() => onAction?.()}
      />
    </div>
  )
}
