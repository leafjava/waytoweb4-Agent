// Pill.jsx -- 5-tone status chip. Mirrors Nerya's <Pill tone=...> pattern.
// Used everywhere a status enum is rendered (passport state machine,
// verdict level, lifecycle stages) so the page reads as a system
// of colored chips rather than a string wall.

const TONES = {
  neutral: 'bg-slate-700/30 border-slate-600/40 text-slate-300',
  ok: 'bg-emerald-700/30 border-emerald-600/50 text-emerald-200',
  warn: 'bg-amber-700/30 border-amber-600/50 text-amber-200',
  danger: 'bg-rose-700/30 border-rose-600/50 text-rose-200',
  brand: 'bg-sky-700/30 border-sky-600/50 text-sky-200',
}

export default function Pill({ tone = 'neutral', children, className = '', title }) {
  return (
    <span
      title={title}
      className={
        'inline-flex items-center gap-1 px-2 py-0.5 rounded border text-xs font-mono ' +
        (TONES[tone] || TONES.neutral) +
        (className ? ' ' + className : '')
      }
    >
      {children}
    </span>
  )
}

// Convenience map: app-specific states -> tone. Centralized so the
// mapping stays consistent across every card on the page.
export const TONE_FOR = {
  // passport state machine
  pending_face: 'warn',
  authorized: 'brand',
  active: 'ok',
  stopped: 'neutral',
  revoked: 'danger',
  // verdict levels
  HOLD: 'ok',
  WATCH: 'warn',
  TRIP: 'danger',
  // lifecycle stages (used by PassportLifecycleStrip)
  pending: 'neutral',
  current: 'brand',
  done: 'ok',
  tripped: 'danger',
}