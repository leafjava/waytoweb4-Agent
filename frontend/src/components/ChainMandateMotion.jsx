import { useEffect, useRef, useState } from 'react'
import { useI18n } from '../i18n.jsx'

const NODE_LABELS = [
  { key: 'motion.node.spec', x: 74, y: 94, tone: 'cyan' },
  { key: 'motion.node.human', x: 366, y: 94, tone: 'amber' },
  { key: 'motion.node.passport', x: 366, y: 326, tone: 'emerald' },
  { key: 'motion.node.redline', x: 74, y: 326, tone: 'rose' },
]

const PROOF_ITEMS = [
  ['motion.proof.spec_label', 'motion.proof.spec_value'],
  ['motion.proof.gate_label', 'motion.proof.gate_value'],
  ['motion.proof.mode_label', 'motion.proof.mode_value'],
]

export default function ChainMandateMotion() {
  const { t } = useI18n()
  const figureRef = useRef(null)
  const [isPlaying, setIsPlaying] = useState(true)

  useEffect(() => {
    const figure = figureRef.current
    if (!figure) return undefined

    let isIntersecting = true
    const syncPlayback = () => setIsPlaying(isIntersecting && !document.hidden)
    const observer = new IntersectionObserver(([entry]) => {
      isIntersecting = entry.isIntersecting
      syncPlayback()
    }, { threshold: 0.08 })

    observer.observe(figure)
    document.addEventListener('visibilitychange', syncPlayback)

    return () => {
      observer.disconnect()
      document.removeEventListener('visibilitychange', syncPlayback)
    }
  }, [])

  return (
    <figure
      ref={figureRef}
      className={`chain-mandate${isPlaying ? '' : ' chain-mandate--paused'}`}
      aria-label={t('motion.aria')}
    >
      <div className="chain-mandate__topline">
        <span>{t('motion.graph')}</span>
        <span className="chain-mandate__status">
          <i aria-hidden="true" /> {t('motion.status')}
        </span>
      </div>

      <div className="chain-mandate__canvas" aria-hidden="true">
        <svg viewBox="0 0 440 420" role="presentation">
          <defs>
            <linearGradient id="chain-flow" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0" stopColor="#38bdf8" />
              <stop offset="0.55" stopColor="#34d399" />
              <stop offset="1" stopColor="#fb7185" />
            </linearGradient>
            <radialGradient id="core-glow">
              <stop offset="0" stopColor="#38bdf8" stopOpacity="0.2" />
              <stop offset="1" stopColor="#38bdf8" stopOpacity="0" />
            </radialGradient>
            <filter id="node-glow" x="-100%" y="-100%" width="300%" height="300%">
              <feGaussianBlur stdDeviation="4" result="blur" />
              <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
            </filter>
          </defs>

          <circle className="chain-core-glow" cx="220" cy="210" r="150" fill="url(#core-glow)" />
          <ellipse className="chain-orbit chain-orbit--outer" cx="220" cy="210" rx="176" ry="142" />
          <ellipse className="chain-orbit chain-orbit--inner" cx="220" cy="210" rx="132" ry="105" />

          <path className="chain-route chain-route--base" d="M74 94 H366 V326 L220 210 L74 326 V94" />
          <path className="chain-route chain-route--flow" d="M74 94 H366 V326 L220 210" />
          <path className="chain-route chain-route--stop" d="M220 210 L74 326" />

          <g className="chain-packet chain-packet--lead">
            <circle r="5" fill="#e0f2fe" filter="url(#node-glow)" />
          </g>
          <g className="chain-packet chain-packet--trail">
            <circle r="3" fill="#34d399" />
          </g>

          {NODE_LABELS.map((node, index) => (
            <g
              key={node.key}
              className={`chain-node chain-node--${node.tone}`}
              style={{ '--node-delay': `${index * 1.15}s` }}
            >
              <circle className="chain-node__halo" cx={node.x} cy={node.y} r="27" />
              <circle className="chain-node__body" cx={node.x} cy={node.y} r="18" />
              <circle className="chain-node__dot" cx={node.x} cy={node.y} r="4" />
              <text x={node.x} y={node.y + (node.y < 210 ? -36 : 42)} textAnchor="middle">
                {t(node.key)}
              </text>
            </g>
          ))}

          <g className="chain-core">
            <path d="M220 151 L271 180 L271 240 L220 269 L169 240 L169 180 Z" />
            <path className="chain-core__inner" d="M220 169 L255 189 L255 231 L220 251 L185 231 L185 189 Z" />
            <path className="chain-core__shield" d="M220 188 L238 196 V210 C238 224 230 234 220 239 C210 234 202 224 202 210 V196 Z" />
            <path className="chain-core__check" d="M211 211 L218 218 L231 203" />
            <text className="chain-core__label" x="220" y="282" textAnchor="middle">{t('motion.core')}</text>
          </g>
        </svg>
      </div>

      <figcaption className="sr-only">{t('motion.caption')}</figcaption>
      <div className="chain-mandate__proof" aria-hidden="true">
        {PROOF_ITEMS.map(([label, value]) => (
          <span key={label}><b>{t(label)}</b> {t(value)}</span>
        ))}
      </div>
    </figure>
  )
}
