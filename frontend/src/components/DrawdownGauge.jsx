import { useI18n } from '../i18n.jsx'

// A horizontal bar showing drawdown / max_loss as a percentage.

export default function DrawdownGauge({ drawdown = 0, maxLoss = 0 }) {
  const { t } = useI18n()
  const safeMax = Math.max(maxLoss, 0.0001)
  const pct = Math.min(1, Math.max(0, drawdown / safeMax))
  const pctText = Math.round(pct * 100)
  let color = 'bg-emerald-500'
  if (pct >= 0.7) color = 'bg-amber-500'
  if (pct >= 0.95) color = 'bg-rose-500'

  return (
    <div>
      <div className="flex justify-between text-xs mb-1">
        <span className="text-slate-400">{t('gauge.drawdown')}</span>
        <span className="text-slate-200 font-mono">
          ${drawdown.toFixed(1)} / ${maxLoss.toFixed(1)}
        </span>
      </div>
      <div className="h-3 w-full rounded bg-slate-800 overflow-hidden">
        <div
          className={`h-full ${color} transition-all`}
          style={{ width: `${pctText}%` }}
        />
      </div>
    </div>
  )
}