// Single source of truth for status -> color.
// Keep this aligned with backend/app/state.py status constants.

export const PASS_COLORS = {
  prepared: { fg: 'text-cyan-300', bg: 'bg-cyan-900/40', border: 'border-cyan-700' },
  confirmed: { fg: 'text-sky-300', bg: 'bg-sky-900/40', border: 'border-sky-700' },
  authorized: { fg: 'text-emerald-300', bg: 'bg-emerald-900/40', border: 'border-emerald-700' },
  mint_pending: { fg: 'text-amber-300', bg: 'bg-amber-900/40', border: 'border-amber-700' },
  revoke_pending: { fg: 'text-amber-300', bg: 'bg-amber-900/40', border: 'border-amber-700' },
  uncertain: { fg: 'text-orange-300', bg: 'bg-orange-900/40', border: 'border-orange-700' },
  pending_face: { fg: 'text-amber-300', bg: 'bg-amber-900/40', border: 'border-amber-700' },
  active: { fg: 'text-emerald-300', bg: 'bg-emerald-900/40', border: 'border-emerald-700' },
  stopped: { fg: 'text-slate-300', bg: 'bg-slate-800/60', border: 'border-slate-700' },
  revoked: { fg: 'text-rose-300', bg: 'bg-rose-900/40', border: 'border-rose-700' },
}

export const LEVEL_COLORS = {
  HOLD: { fg: 'text-emerald-300', bg: 'bg-emerald-900/40' },
  WATCH: { fg: 'text-amber-300', bg: 'bg-amber-900/40' },
  TRIP: { fg: 'text-rose-300', bg: 'bg-rose-900/40' },
}

export const KIND_COLORS = {
  mint: 'text-emerald-300',
  revoke: 'text-rose-300',
  face_verify: 'text-amber-300',
  engine_start: 'text-sky-300',
  engine_stop: 'text-slate-300',
  engine_tick: 'text-slate-300',
  redline_judge: 'text-orange-300',
  demo_inject: 'text-fuchsia-300',
  demo_reset: 'text-slate-400',
  spec_emit: 'text-cyan-300',
  spec_clarify: 'text-cyan-300',
}
