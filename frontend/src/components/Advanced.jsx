// Advanced.jsx -- collapsible section with localStorage memory.
// Port of Nerya's <Advanced title storageKey defaultOpen>. Renders a
// chevron toggle; remembers open/closed across reloads; supports
// stacked siblings inside the same card. Use this whenever a detail
// block is shown to <10% of sessions.

import { useEffect, useState } from 'react'

export default function Advanced({
  title,
  storageKey,
  defaultOpen = false,
  children,
}) {
  const lsKey = storageKey ? `w2w4.advanced.${storageKey}` : null
  const [open, setOpen] = useState(() => {
    if (!lsKey) return defaultOpen
    try {
      const v = localStorage.getItem(lsKey)
      if (v === '1') return true
      if (v === '0') return false
    } catch (_) { /* localStorage unavailable */ }
    return defaultOpen
  })
  useEffect(() => {
    if (!lsKey) return
    try {
      localStorage.setItem(lsKey, open ? '1' : '0')
    } catch (_) { /* ignore */ }
  }, [lsKey, open])

  return (
    <div className="mt-2 border-t border-slate-800 pt-2">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 transition-colors"
        aria-expanded={open}
      >
        <i className={`fa fa-chevron-${open ? 'down' : 'right'} text-[10px]`}></i>
        <span className="font-mono">{title}</span>
      </button>
      {open && <div className="mt-2">{children}</div>}
    </div>
  )
}