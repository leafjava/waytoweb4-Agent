// GateBadges.jsx -- two side-by-side contract badges that surface the
// PRD §4.4 / §12 promises. Light theme to match PrimitivesGrid.

import { useI18n } from '../i18n.jsx'

const GATE_PALETTE = {
  approval: 'border-sky-200 bg-sky-50 text-sky-700',
  risk: 'border-rose-200 bg-rose-50 text-rose-700',
}

const ICON_COLOR = {
  approval: 'text-sky-500',
  risk: 'text-rose-500',
}

const PILL_CLASS = {
  approval: 'bg-sky-100 border border-sky-300 text-sky-700',
  risk: 'bg-rose-100 border border-rose-300 text-rose-700',
}

function Gate({ kind, title, subtitle, bullets }) {
  return (
    <div className={`border rounded-2xl p-5 shadow-sm ${GATE_PALETTE[kind]}`} style={{ backgroundColor: '#ecf2f8' }}>
      <div className="flex items-center justify-between mb-2">
        <div>
          <div className="text-[11px] uppercase tracking-wider text-slate-500">{subtitle}</div>
          <div className="text-base font-semibold text-[#1d1d1f] mt-0.5">{title}</div>
        </div>
        <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-mono ${PILL_CLASS[kind]}`}>
          ON
        </span>
      </div>
      <ul className="space-y-1 text-[12px] text-slate-700">
        {bullets.map((b, i) => (
          <li key={i} className="flex items-start gap-2">
            <i className={`fa ${b.icon} mt-0.5 ${ICON_COLOR[kind]}`}></i>
            <span>{b.text}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}

export default function GateBadges() {
  const { t } = useI18n()

  const approval = {
    kind: 'approval',
    title: t('gate.approval.title'),
    subtitle: t('gate.subtitle.approval'),
    bullets: [
      { icon: 'fa-user-circle-o', text: t('gate.approval.b1') },
      { icon: 'fa-link',          text: t('gate.approval.b2') },
      { icon: 'fa-ban',           text: t('gate.approval.b3') },
    ],
  }
  const risk = {
    kind: 'risk',
    title: t('gate.risk.title'),
    subtitle: t('gate.subtitle.risk'),
    bullets: [
      { icon: 'fa-shield',    text: t('gate.risk.b1') },
      { icon: 'fa-ban',       text: t('gate.risk.b2') },
      { icon: 'fa-eye-slash', text: t('gate.risk.b3') },
    ],
  }

  return (
    <section className="grid grid-cols-1 md:grid-cols-2 gap-3">
      <Gate {...approval} />
      <Gate {...risk} />
    </section>
  )
}