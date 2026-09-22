import { LEVEL_COLORS } from '../colors'

export default function VerdictBadge({ verdict }) {
  if (!verdict) {
    return <span className="text-xs text-slate-500 italic">no verdict yet</span>
  }
  const lvl = verdict.level
  const palette = LEVEL_COLORS[lvl] ?? LEVEL_COLORS.HOLD
  return (
    <div className="space-y-1">
      <div className="flex items-center gap-2">
        <span className={`text-xs px-2 py-0.5 rounded ${palette.bg} ${palette.fg}`}>
          {lvl}
        </span>
        <span className="text-xs text-slate-400">via {verdict.source}</span>
      </div>
      {(verdict.reason_codes || []).length > 0 && (
        <div className="flex flex-wrap gap-1">
          {verdict.reason_codes.map((c) => (
            <span key={c} className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-200">
              {c}
            </span>
          ))}
        </div>
      )}
      {verdict.evidence?.length > 0 && (
        <div className="text-[11px] text-slate-400 space-y-0.5">
          {verdict.evidence.map((e, i) => <div key={i} className="txhash">{e}</div>)}
        </div>
      )}
    </div>
  )
}
