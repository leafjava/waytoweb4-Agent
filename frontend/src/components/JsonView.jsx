// JsonView.jsx -- typed JSON renderer with structured/raw toggle.
// Replaces the <pre>{JSON.stringify(x,null,2)}</pre> blob that gives
// "we didn't finish the UI" vibes. Mirrors Nerya's JsonView: object
// -> key/value table, object array -> real table, primitive array
// -> chip row, primitive -> typed pill. Auto-collapse past depth 6.

import { useState } from 'react'

const MAX_DEPTH = 6
const MAX_STR = 200

function valueKind(v) {
  if (v === null) return 'null'
  if (Array.isArray(v)) return 'array'
  return typeof v  // 'object' | 'string' | 'number' | 'boolean' | 'undefined'
}

function isObjectArray(v) {
  return (
    Array.isArray(v) &&
    v.length > 0 &&
    v.every((x) => x && typeof x === 'object' && !Array.isArray(x))
  )
}

function Pill({ tone = 'slate', children }) {
  const palette = {
    slate: 'bg-slate-700/40 border-slate-600/40 text-slate-200',
    sky: 'bg-sky-700/30 border-sky-600/40 text-sky-200',
    emerald: 'bg-emerald-700/30 border-emerald-600/40 text-emerald-200',
    amber: 'bg-amber-700/30 border-amber-600/40 text-amber-200',
    rose: 'bg-rose-700/30 border-rose-600/40 text-rose-200',
  }[tone]
  return (
    <span className={`inline-flex items-center px-1.5 py-0.5 rounded border text-[11px] font-mono ${palette}`}>
      {children}
    </span>
  )
}

function PrimitiveValue({ v }) {
  const k = valueKind(v)
  if (k === 'null' || k === 'undefined') return <Pill tone="slate">—</Pill>
  if (k === 'boolean')
    return (
      <Pill tone={v ? 'emerald' : 'rose'}>
        {v ? '✓ true' : '✗ false'}
      </Pill>
    )
  if (k === 'number')
    return <span className="font-mono text-sky-200 tabular-nums">{String(v)}</span>
  if (k === 'string') {
    const s = v.length > MAX_STR ? v.slice(0, MAX_STR) + '…' : v
    return <span className="font-mono text-slate-200">"{s}"</span>
  }
  return null
}

function JsonRow({ k, v, depth = 0 }) {
  const kind = valueKind(v)
  const label =
    k === undefined ? null : (
      <span className="font-mono text-slate-400 mr-2">{k}:</span>
    )
  const body = (() => {
    if (kind === 'object') return <ObjectTable v={v} depth={depth} />
    if (kind === 'array') {
      if (isObjectArray(v)) return <ObjectArrayTable v={v} depth={depth} />
      return <PrimitiveArray v={v} />
    }
    return <PrimitiveValue v={v} />
  })()
  return (
    <div className="flex items-start gap-1 py-0.5">
      {label}
      <div className="flex-1 min-w-0">{body}</div>
    </div>
  )
}

function ObjectTable({ v, depth }) {
  if (depth > MAX_DEPTH) {
    return <Pill tone="slate">…nested deeper…</Pill>
  }
  const entries = Object.entries(v)
  return (
    <div className="border border-slate-800 rounded p-2 bg-slate-950/40">
      {entries.map(([k, val]) => (
        <JsonRow key={k} k={k} v={val} depth={depth + 1} />
      ))}
    </div>
  )
}

function ObjectArrayTable({ v, depth }) {
  if (depth > MAX_DEPTH) return <Pill tone="slate">…nested deeper…</Pill>
  const cols = Object.keys(v[0] || {})
  return (
    <table className="w-full border border-slate-800 rounded text-[11px] divide-y divide-slate-800 bg-slate-950/40">
      <thead>
        <tr className="divide-x divide-slate-800">
          {cols.map((c) => (
            <th key={c} className="text-left px-2 py-1 font-mono text-slate-400">
              {c}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {v.map((row, i) => (
          <tr key={i} className="divide-x divide-slate-800">
            {cols.map((c) => (
              <td key={c} className="px-2 py-1 align-top">
                <PrimitiveValue v={row[c]} />
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  )
}

function PrimitiveArray({ v }) {
  return (
    <div className="flex flex-wrap gap-1">
      {v.map((item, i) => (
        <Pill key={i} tone={typeof item === 'number' ? 'sky' : 'slate'}>
          {typeof item === 'string' ? `"${item}"` : String(item)}
        </Pill>
      ))}
    </div>
  )
}

export default function JsonView({ value, initialCollapsed = false, showRawToggle = true }) {
  const [mode, setMode] = useState('structured') // 'structured' | 'raw'

  if (value === undefined) return <Pill tone="slate">undefined</Pill>

  return (
    <div className="relative">
      {showRawToggle && (
        <div className="absolute right-0 top-0 flex gap-1 text-[10px]">
          <button
            onClick={() => setMode('structured')}
            className={
              'px-1.5 py-0.5 rounded ' +
              (mode === 'structured'
                ? 'bg-sky-500 text-slate-950 font-semibold'
                : 'bg-slate-800 text-slate-400 hover:text-slate-200')
            }
          >
            Structured
          </button>
          <button
            onClick={() => setMode('raw')}
            className={
              'px-1.5 py-0.5 rounded ' +
              (mode === 'raw'
                ? 'bg-sky-500 text-slate-950 font-semibold'
                : 'bg-slate-800 text-slate-400 hover:text-slate-200')
            }
          >
            Raw
          </button>
        </div>
      )}
      {mode === 'raw' ? (
        <pre className="text-[11px] text-slate-200 whitespace-pre-wrap font-mono bg-slate-950 border border-slate-800 rounded p-2 pt-6 max-h-72 overflow-auto">
          {JSON.stringify(value, null, 2)}
        </pre>
      ) : valueKind(value) === 'object' ? (
        <div className={showRawToggle ? 'pt-6' : ''}>
          <ObjectTable v={value} depth={0} />
        </div>
      ) : valueKind(value) === 'array' ? (
        <div className={showRawToggle ? 'pt-6' : ''}>
          {isObjectArray(value) ? <ObjectArrayTable v={value} depth={0} /> : <PrimitiveArray v={value} />}
        </div>
      ) : (
        <div className={showRawToggle ? 'pt-6' : ''}>
          <PrimitiveValue v={value} />
        </div>
      )}
    </div>
  )
}