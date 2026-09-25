import { useEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { apiPost } from '../api'
import { useI18n } from '../i18n.jsx'

function newSessionId() {
  if (globalThis.crypto?.randomUUID) return globalThis.crypto.randomUUID()
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (char) => {
    const value = Math.floor(Math.random() * 16)
    const nibble = char === 'x' ? value : (value & 0x3) | 0x8
    return nibble.toString(16)
  })
}

export default function HumanGate({ open, passport, spec, onClose, onComplete }) {
  const { locale, t } = useI18n()
  const videoRef = useRef(null)
  const closeRef = useRef(null)
  const streamRef = useRef(null)
  const [cameraState, setCameraState] = useState('idle')
  const [consented, setConsented] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [sessionId, setSessionId] = useState('')

  useEffect(() => {
    if (!open) return undefined
    let cancelled = false
    setCameraState('requesting')
    setConsented(false)
    setError('')
    setSessionId(newSessionId())

    if (!navigator.mediaDevices?.getUserMedia) {
      setCameraState('unsupported')
      return undefined
    }

    navigator.mediaDevices.getUserMedia({ video: true, audio: false })
      .then((stream) => {
        if (cancelled) {
          stream.getTracks().forEach((track) => track.stop())
          return
        }
        streamRef.current = stream
        if (videoRef.current) {
          videoRef.current.srcObject = stream
          videoRef.current.play().catch(() => {})
        }
        setCameraState('ready')
      })
      .catch(() => setCameraState('denied'))

    return () => {
      cancelled = true
      streamRef.current?.getTracks().forEach((track) => track.stop())
      streamRef.current = null
      if (videoRef.current) videoRef.current.srcObject = null
    }
  }, [open])

  useEffect(() => {
    if (!open) return undefined
    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    closeRef.current?.focus()
    const handleKeyDown = (event) => {
      if (event.key === 'Escape' && !busy) onClose()
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => {
      document.body.style.overflow = previousOverflow
      window.removeEventListener('keydown', handleKeyDown)
    }
  }, [open, busy])

  if (!open) return null

  async function approveAndStart() {
    if (!passport?.passport_id || cameraState !== 'ready' || !consented || busy) return
    setBusy(true)
    setError('')
    try {
      const verification = await apiPost('/api/face/verify', {
        passport_id: passport.passport_id,
        method: 'button',
        session_id: sessionId,
      })
      await onComplete?.({ phase: 'verified', verification })
      const started = await apiPost('/api/engine/start', { passport_id: passport.passport_id })
      await onComplete?.({ phase: 'started', verification, started })
      onClose()
    } catch (cause) {
      if (cause.code === 'FACE_GATE_REQUIRED') {
        setError(t('gate.error.required'))
      } else {
        setError(cause.message || t('gate.error.generic'))
      }
    } finally {
      setBusy(false)
    }
  }

  const dateLocale = locale === 'ko' ? 'ko-KR' : 'en-US'
  const expiry = spec?.expiry ? new Intl.DateTimeFormat(dateLocale, {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(spec.expiry)) : '—'

  const modal = (
    <div
      className="fixed inset-0 z-[1000] flex items-center justify-center bg-black/25 p-3 backdrop-blur-xl sm:p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="human-gate-title"
    >
      <div className="max-h-[calc(100dvh-1.5rem)] w-full max-w-4xl overscroll-contain overflow-y-auto rounded-2xl bg-white shadow-2xl shadow-black/50 sm:max-h-[calc(100dvh-2rem)]">
        <div className="flex items-start justify-between gap-6 border-b border-black/10 px-5 py-4 md:px-7">
          <div>
            <h2 id="human-gate-title" className="text-xl font-semibold text-[#1d1d1f] md:text-2xl">
              {t('gate.title')}
            </h2>
            <p className="mt-1 max-w-2xl text-sm leading-6 text-slate-700">{t('gate.subtitle')}</p>
          </div>
          <button
            ref={closeRef}
            type="button"
            onClick={onClose}
            disabled={busy}
            className="shrink-0 rounded-lg px-3 py-2 text-sm text-slate-700 hover:bg-black/[0.04] hover:text-[#1d1d1f] focus:outline-none focus:ring-2 focus:ring-cyan-400 disabled:opacity-50"
            aria-label={t('gate.close')}
          >
            <i className="fa fa-times" aria-hidden="true"></i>
          </button>
        </div>

        <div className="grid gap-0 md:grid-cols-[1.15fr_0.85fr]">
          <section className="bg-black p-4 md:p-6">
            <div className="relative aspect-video overflow-hidden rounded-xl bg-[#f5f5f7]">
              <video
                ref={videoRef}
                muted
                playsInline
                className="h-full w-full object-cover -scale-x-100"
                aria-label={t('gate.preview')}
              />
              {cameraState !== 'ready' && (
                <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 p-6 text-center text-slate-700" aria-live="polite">
                  <i className={`fa ${cameraState === 'requesting' ? 'fa-circle-o-notch fa-spin' : 'fa-video-camera'} text-2xl`} aria-hidden="true"></i>
                  <p className="max-w-sm text-sm leading-6">
                    {t(`gate.camera.${cameraState}`)}
                  </p>
                </div>
              )}
              {cameraState === 'ready' && (
                <div className="absolute bottom-3 left-3 rounded-full bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700">
                  <i className="fa fa-circle mr-2 text-[8px]" aria-hidden="true"></i>
                  {t('gate.camera.ready')}
                </div>
              )}
            </div>
            <p className="mt-3 text-xs leading-5 text-slate-500">
              <i className="fa fa-lock mr-2" aria-hidden="true"></i>
              {t('gate.privacy')}
            </p>
          </section>

          <section className="flex flex-col p-5 md:p-6">
            <h3 className="text-sm font-semibold text-[#1d1d1f]">{t('gate.mandate')}</h3>
            <dl className="mt-4 space-y-3 text-sm">
              <GateRow label={t('spec.leader')} value={spec?.leaderId || '—'} />
              <GateRow label={t('spec.notional')} value={`${spec?.notionalUsd ?? '—'} USD`} />
              <GateRow label={t('spec.maxloss')} value={`${spec?.maxLossUsd ?? '—'} USD`} />
              <GateRow label={t('spec.venue')} value={spec?.paper ? t('gate.paper_only') : String(spec?.venue || '—')} />
              <GateRow label={t('spec.expiry')} value={expiry} />
            </dl>

            <label className="mt-6 flex cursor-pointer items-start gap-3 rounded-xl bg-black/[0.04] p-4 text-sm leading-6 text-slate-800">
              <input
                type="checkbox"
                checked={consented}
                onChange={(event) => setConsented(event.target.checked)}
                className="mt-1 h-4 w-4 accent-cyan-500"
              />
              <span>{t('gate.consent')}</span>
            </label>

            {error && (
              <div className="mt-4 rounded-xl bg-rose-50 p-3 text-sm leading-5 text-rose-700" role="alert">
                <i className="fa fa-exclamation-triangle mr-2" aria-hidden="true"></i>
                {error}
              </div>
            )}

            <button
              type="button"
              onClick={approveAndStart}
              disabled={cameraState !== 'ready' || !consented || busy}
              className="mt-5 w-full rounded-xl bg-[#0071e3] px-4 py-3 text-sm font-semibold text-white hover:bg-[#0077ed] focus:outline-none focus:ring-2 focus:ring-cyan-300 focus:ring-offset-2 focus:ring-offset-white disabled:cursor-not-allowed disabled:bg-slate-200 disabled:text-slate-500"
            >
              <i className={`fa ${busy ? 'fa-circle-o-notch fa-spin' : 'fa-check-circle'} mr-2`} aria-hidden="true"></i>
              {busy ? t('gate.approving') : t('gate.approve_start')}
            </button>
          </section>
        </div>
      </div>
    </div>
  )

  return createPortal(modal, document.body)
}

function GateRow({ label, value }) {
  return (
    <div className="grid grid-cols-[minmax(0,0.8fr)_minmax(0,1.2fr)] gap-4 border-b border-black/10 pb-3 last:border-0">
      <dt className="text-slate-500">{label}</dt>
      <dd className="min-w-0 break-words text-right font-medium text-[#1d1d1f]">{value}</dd>
    </div>
  )
}
