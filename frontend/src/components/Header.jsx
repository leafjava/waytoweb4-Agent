import { apiPost } from '../api'

export default function Header({ health, onReset }) {
  return (
    <header className="px-6 py-3 border-b border-slate-800 bg-slate-900/70 flex items-center gap-4">
      <div className="flex items-center gap-2">
        <i className="fa fa-bolt text-amber-400"></i>
        <h1 className="text-lg font-semibold tracking-wide">
          waytoweb4 copy-trading agent
        </h1>
      </div>

      <div className="ml-auto flex items-center gap-3 text-xs">
        <Pill label="Kiln" value={health?.kiln ?? '—'} />
        <Pill label="Passport" value={health?.passport_backend ?? '—'} />
        <button
          onClick={onReset}
          className="px-3 py-1 rounded bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200"
        >
          <i className="fa fa-rotate-right mr-1"></i> Reset
        </button>
      </div>
    </header>
  )
}

function Pill({ label, value }) {
  return (
    <div className="flex items-center gap-1.5 px-2 py-1 rounded bg-slate-800 border border-slate-700">
      <span className="text-slate-400">{label}:</span>
      <span className="text-slate-100 font-mono">{value}</span>
    </div>
  )
}
