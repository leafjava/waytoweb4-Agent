// Single source of truth for status -> color.
// Keep this aligned with backend/app/state.py status constants.

export const PASS_COLORS = {
  prepared: { fg: 'text-cyan-700', bg: 'bg-cyan-50', border: 'border-cyan-200' },
  confirmed: { fg: 'text-blue-700', bg: 'bg-blue-50', border: 'border-blue-200' },
  authorized: { fg: 'text-emerald-700', bg: 'bg-emerald-50', border: 'border-emerald-200' },
  mint_pending: { fg: 'text-amber-700', bg: 'bg-amber-50', border: 'border-amber-200' },
  revoke_pending: { fg: 'text-amber-700', bg: 'bg-amber-50', border: 'border-amber-200' },
  uncertain: { fg: 'text-orange-700', bg: 'bg-orange-50', border: 'border-orange-200' },
  pending_face: { fg: 'text-amber-700', bg: 'bg-amber-50', border: 'border-amber-200' },
  active: { fg: 'text-emerald-700', bg: 'bg-emerald-50', border: 'border-emerald-200' },
  stopped: { fg: 'text-slate-700', bg: 'bg-black/[0.04]', border: 'border-black/10' },
  revoked: { fg: 'text-rose-700', bg: 'bg-rose-50', border: 'border-rose-200' },
}

export const LEVEL_COLORS = {
  HOLD: { fg: 'text-emerald-700', bg: 'bg-emerald-50' },
  WATCH: { fg: 'text-amber-700', bg: 'bg-amber-50' },
  TRIP: { fg: 'text-rose-700', bg: 'bg-rose-50' },
}

export const KIND_COLORS = {
  mint: 'text-emerald-700',
  revoke: 'text-rose-700',
  face_verify: 'text-amber-700',
  engine_start: 'text-blue-700',
  engine_stop: 'text-slate-700',
  engine_tick: 'text-slate-700',
  redline_judge: 'text-orange-700',
  demo_inject: 'text-fuchsia-700',
  demo_reset: 'text-slate-500',
  spec_emit: 'text-cyan-700',
  spec_clarify: 'text-cyan-700',
}
