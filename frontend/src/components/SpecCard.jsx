import { apiPost } from '../api'
import { useI18n } from '../i18n.jsx'

function requestId(prefix) {
  const id = globalThis.crypto?.randomUUID?.() || Math.random().toString(36).slice(2)
  return `${prefix}-${id}`
}

export default function SpecCard({ draft, setDraft, onMinted }) {
  const { t } = useI18n()
  const spec = draft.locked_spec
  const prepared = !!draft.passport_id
  const confirmed = draft.mint?.status === 'confirmed' || draft.mint?.status === 'authorized' || draft.mint?.status === 'mint_pending'
  const busy = draft.busy

  async function handleAction() {
    if (!spec || busy) return
    setDraft((d) => ({ ...d, busy: true }))
    try {
      if (!prepared) {
        const result = await apiPost('/api/passport/prepare', { spec, request_id: requestId('prepare') })
        setDraft((d) => ({ ...d, passport_id: result.passport_id, mint: result }))
        return
      }
      if (!draft.confirmed) {
        const confirmation = await apiPost('/api/passport/confirm', {
          passport_id: draft.passport_id,
          spec_hash: draft.mint.spec_hash,
          request_id: requestId('confirm'),
        })
        setDraft((d) => ({ ...d, confirmed: true, mint: confirmation }))
        const minted = await apiPost('/api/passport/mint', {
          passport_id: draft.passport_id,
          request_id: requestId('mint'),
        })
        setDraft((d) => ({ ...d, mint: minted }))
        onMinted?.(minted)
      }
    } catch (error) {
      console.error(error)
      alert(`${t('spec.authorization_failed')}: ${error.message || error}`)
    } finally {
      setDraft((d) => ({ ...d, busy: false }))
    }
  }

  const actionLabel = busy
    ? t('spec.working')
    : !prepared
      ? t('spec.prepare_btn')
      : !draft.confirmed
        ? t('spec.confirm_mint_btn')
        : t('spec.authorized_btn')

  return (
    <div className="surface-card border border-black/10 rounded-lg p-4">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-sm uppercase tracking-wider text-slate-500">
          <i className="fa fa-file-text-o mr-2"></i> {t('spec.title')}
        </h2>
        {spec && (
          <span className="text-xs px-2 py-0.5 rounded bg-cyan-50 border border-cyan-200 text-cyan-700">
            {t('spec.locked')}
          </span>
        )}
      </div>

      {!spec ? (
        <div className="text-slate-500 italic text-sm">{t('spec.empty')}</div>
      ) : (
        <div className="space-y-1.5 text-sm font-mono">
          <Row k={t('spec.leader')} v={spec.leaderId} />
          <Row k={t('spec.notional')} v={`${spec.notionalUsd} USD`} />
          <Row k={t('spec.maxloss')} v={`${spec.maxLossUsd} USD`} />
          <Row k={t('spec.expiry')} v={spec.expiry} />
          <Row k={t('spec.venue')} v={spec.venue} />
          <Row k={t('spec.paper')} v={String(spec.paper)} />
          {draft.mint?.spec_hash && <Row k={t('spec.intent_hash')} v={draft.mint.spec_hash} />}
        </div>
      )}

      <div className="mt-4">
        <button
          disabled={!spec || confirmed || busy}
          onClick={handleAction}
          className="w-full px-3 py-2 rounded bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-sm font-medium"
        >
          <i className="fa fa-link mr-1"></i>
          {actionLabel}
        </button>
      </div>
    </div>
  )
}

function Row({ k, v }) {
  return (
    <div className="flex justify-between gap-4">
      <span className="text-slate-500">{k}</span>
      <span className="text-[#1d1d1f] text-right break-all">{v}</span>
    </div>
  )
}
