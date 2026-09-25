// PassportLifecycleStrip.jsx -- the 5-stage strip that visualises
// PRD §4.4 / §12. Each node is a Pill-tinted circle + label; current
// stage highlighted in sky, completed stages emerald, tripped stage
// rose. The state machine is:
//
//   1. Spec locked         -> after /api/spec/emit
//   2. Face verified       -> after /api/face/verify
//   3. Authorized          -> after passport mint
//   4. Running             -> after /api/engine/start
//   5. Tripped             -> after RedLine TRIP + revoke
//
// The strip is intentionally read-only: it just reflects the latest
// state on the passport; all mutations go through the existing
// backend endpoints. No new dependencies.

import Pill from './Pill.jsx'
import { useI18n } from '../i18n.jsx'

const STAGES = [
  { n: 1, key: 'life.1.title' },
  { n: 2, key: 'life.2.title' },
  { n: 3, key: 'life.3.title' },
  { n: 4, key: 'life.4.title' },
  { n: 5, key: 'life.5.title' },
]

// Map passport.status (or none) to which stage the strip is on.
// pending_face / active / stopped / revoked are the engine-level
// statuses already defined in backend/app/state.py.
function currentStage(status, faceVerified, engineRunning) {
  if (status === 'revoked') return { idx: 4, tone: 'danger' } // last stage = tripped
  if (engineRunning) return { idx: 3, tone: 'ok' } // running = stage 4 of 5
  if (status === 'active') return { idx: 3, tone: 'ok' }
  if (status === 'stopped') return { idx: 3, tone: 'neutral' }
  if (faceVerified) return { idx: 2, tone: 'ok' } // face verified = stage 2/3
  if (status === 'pending_face') return { idx: 1, tone: 'ok' }
  return { idx: -1, tone: 'neutral' } // nothing yet
}

export default function PassportLifecycleStrip({ status, faceVerified, engineRunning }) {
  const { t } = useI18n()
  const cur = currentStage(status, faceVerified, engineRunning)
  const isTripped = status === 'revoked'

  return (
    <section className="bg-slate-900/40 border border-slate-800 rounded-xl p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-xs uppercase tracking-wider text-slate-400">
          <i className="fa fa-route mr-2"></i>
          {t('life.label')}
        </h3>
        <Pill tone={cur.tone}>{status || '—'}</Pill>
      </div>

      <ol className="relative grid grid-cols-1 md:grid-cols-5 gap-3">
        {STAGES.map((s, i) => {
          const isDone = i < cur.idx
          const isCurrent = i === cur.idx && !isTripped
          const isTrippedThis = isTripped && i === cur.idx
          const tone = isDone
            ? 'ok'
            : isCurrent
              ? 'brand'
              : isTrippedThis
                ? 'danger'
                : 'neutral'
          return (
            <li
              key={s.n}
              className={
                'relative flex md:flex-col items-start gap-3 md:gap-1 ' +
                (isCurrent ? 'md:scale-[1.03]' : '')
              }
            >
              {/* Connector (desktop only) */}
              {i < STAGES.length - 1 && (
                <span
                  aria-hidden="true"
                  className={
                    'hidden md:block absolute top-4 left-1/2 w-full h-0.5 ' +
                    (i < cur.idx ? 'bg-emerald-500/70' : 'bg-slate-700')
                  }
                />
              )}
              <span
                className={
                  'shrink-0 w-8 h-8 rounded-full border-2 flex items-center justify-center text-xs font-semibold font-mono ' +
                  (isCurrent
                    ? 'border-sky-400 bg-sky-500/20 text-sky-100 shadow-lg shadow-sky-500/30'
                    : isDone
                      ? 'border-emerald-500/70 bg-emerald-700/30 text-emerald-100'
                      : isTrippedThis
                        ? 'border-rose-500 bg-rose-500/30 text-rose-100'
                        : 'border-slate-700 bg-slate-800 text-slate-500')
                }
              >
                {isDone ? '✓' : s.n}
              </span>
              <span className="flex-1 min-w-0">
                <span className="block text-[10px] uppercase tracking-wider text-slate-500">
                  stage {s.n}
                </span>
                <span className="block text-sm text-slate-100">{t(s.key)}</span>
              </span>
            </li>
          )
        })}
      </ol>

      {isTripped && (
        <div className="mt-3 text-[11px] text-rose-300">
          <i className="fa fa-ban mr-1"></i>
          {t('life.tripped_note')}
        </div>
      )}
    </section>
  )
}