import { useState } from 'react'
import { HYNIX_EVENTS, predictFromLLM, predictFromRuleGate } from '../predict'
import { useI18n } from '../i18n.jsx'

const SPEC_RANGES = {
  notionalUsd: { min: 100, max: 10000, step: 50, default: 500 },
  maxLossUsd: { min: 10, max: 200, step: 5, default: 50 },
  expiryHours: 48,
}

export default function SpecSimulator({ initialSpec, snapshot }) {
  const { t } = useI18n()
  const [notional, setNotional] = useState(initialSpec?.notionalUsd ?? SPEC_RANGES.notionalUsd.default)
  const [maxLoss, setMaxLoss] = useState(
    Math.min(initialSpec?.maxLossUsd ?? SPEC_RANGES.maxLossUsd.default, notional),
  )

  const spec = {
    mode: 'copy',
    leaderId: initialSpec?.leaderId ?? 'leader-demo-001',
    venue: 'paper',
    notionalUsd: notional,
    maxLossUsd: maxLoss,
    expiryHours: SPEC_RANGES.expiryHours,
  }

  const ruleGate = predictFromRuleGate(spec)
  const llmTrip = predictFromLLM(HYNIX_EVENTS)
  const invalid = maxLoss > notional

  return (
    <div className="border border-black/10 rounded-2xl p-6 shadow-sm" style={{ backgroundColor: '#ecf2f8' }}>
      {/* Advice #3: turn-budget strip */}
      <div className="mb-5 grid grid-cols-2 md:grid-cols-3 gap-2 text-xs">
        <BudgetStat
          label={t('sim.budget.clarify')}
          value={`${(snapshot?.events || []).filter((e) => e.kind === 'spec_clarify').length} / 2`}
          tone="brand"
        />
        <BudgetStat label={t('sim.budget.rule_gate')} value={t('sim.budget.fires_first')} tone="ok" />
        <BudgetStat
          label={t('sim.budget.llm_saved')}
          value={snapshot ? Object.values(snapshot.passports || {}).filter((p) => p.last_verdict?.source === 'rule_gate').length : 0}
          tone="emerald"
        />
      </div>

      <h3 className="text-sm uppercase tracking-wider text-slate-500 mb-4">
        <i className="fa fa-calculator mr-2"></i> {t('sim.title')}
      </h3>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-5">
          <Slider
            label={t('sim.notional')}
            value={notional}
            min={SPEC_RANGES.notionalUsd.min}
            max={SPEC_RANGES.notionalUsd.max}
            step={SPEC_RANGES.notionalUsd.step}
            onChange={(v) => {
              setNotional(v)
              if (maxLoss > v) setMaxLoss(v)
            }}
            format={(v) => `$${v}`}
          />
          <Slider
            label={t('sim.maxloss')}
            value={maxLoss}
            min={SPEC_RANGES.maxLossUsd.min}
            max={Math.min(SPEC_RANGES.maxLossUsd.max, notional)}
            step={SPEC_RANGES.maxLossUsd.step}
            onChange={setMaxLoss}
            format={(v) => `$${v}`}
          />
          <div className="text-xs text-slate-500">
            {t('sim.expiry')}: <span className="text-[#1d1d1f]">{t('sim.expiry_val', { hours: SPEC_RANGES.expiryHours })}</span> &nbsp;
            {t('sim.venue')}: <span className="text-[#1d1d1f]">{t('sim.venue_val')}</span> &nbsp;
            {t('sim.mode')}: <span className="text-[#1d1d1f]">{t('sim.mode_val')}</span>
          </div>
          {invalid && (
            <div className="text-xs text-rose-700">{t('sim.invalid')}</div>
          )}
        </div>

        <div className="space-y-4">
          <Outcome
            tone="rose"
            title={t('sim.outcome.no_events')}
            via={ruleGate.via}
            level={invalid ? t('sim.outcome.dash') : ruleGate.level}
            codes={invalid ? [] : ruleGate.reasonCodes}
            note={
              invalid
                ? t('sim.outcome.dash')
                : t('sim.outcome.no_events.note', { sec: ruleGate.timeToTripSec, maxLoss: spec.maxLossUsd })
            }
            bullet={invalid ? null : t('sim.frozen_attr')}
          />
          <Outcome
            tone="fuchsia"
            title={t('sim.outcome.hynix')}
            via={llmTrip.via}
            level={invalid ? t('sim.outcome.dash') : llmTrip.level}
            codes={invalid ? [] : llmTrip.reasonCodes}
            note={
              invalid
                ? t('sim.outcome.dash')
                : t('sim.outcome.hynix.note', { pct: llmTrip.worstChange })
            }
            bullet={null}
          />
        </div>
      </div>
    </div>
  )
}

function Slider({ label, value, min, max, step, onChange, format }) {
  const pct = ((value - min) / Math.max(1, max - min)) * 100
  return (
    <div>
      <div className="flex justify-between text-xs mb-1.5">
        <span className="text-slate-500">{label}</span>
        <span className="text-[#1d1d1f] font-mono">{format(value)}</span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full accent-sky-500"
      />
      <div className="mt-0.5 h-1 rounded bg-slate-200 relative overflow-hidden">
        <div className="absolute inset-y-0 left-0 bg-sky-400" style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}

function Outcome({ tone, title, via, level, codes, note, bullet }) {
  const { t } = useI18n()
  const palette = {
    rose: 'border-rose-200 bg-rose-50 text-rose-700',
    fuchsia: 'border-violet-200 bg-violet-50 text-violet-700',
    emerald: 'border-emerald-200 bg-emerald-50 text-emerald-700',
  }[tone]
  return (
    <div className={`border rounded-lg p-3 ${palette}`}>
      <div className="text-[11px] uppercase tracking-wider opacity-80 mb-1">{title}</div>
      <div className="flex items-center gap-2 text-sm">
        <span className="font-semibold">{level}</span>
        <span className="opacity-60">·</span>
        <span className="text-xs opacity-80">{t('verdict.via')} {via}</span>
      </div>
      {codes?.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {codes.map((c) => (
            <span key={c} className="text-[10px] px-1.5 py-0.5 rounded font-mono bg-rose-100 border border-rose-200 text-rose-700">
              {c}
            </span>
          ))}
        </div>
      )}
      {note && <div className="mt-2 text-[11px] opacity-80">{note}</div>}
      {bullet && <div className="mt-1 text-[10px] opacity-60 font-mono">{bullet}</div>}
    </div>
  )
}

function BudgetStat({ label, value, tone }) {
  const palette = {
    brand: 'border-sky-200 bg-sky-50 text-sky-700',
    ok: 'border-emerald-200 bg-emerald-50 text-emerald-700',
    emerald: 'border-emerald-200 bg-emerald-50 text-emerald-700',
  }[tone] || 'border-slate-200 bg-slate-50 text-slate-700'
  return (
    <div className={`border rounded-md px-2 py-1.5 ${palette}`}>
      <div className="text-[10px] uppercase tracking-wider opacity-75">{label}</div>
      <div className="text-sm font-mono tabular-nums text-[#1d1d1f]">{value}</div>
    </div>
  )
}
