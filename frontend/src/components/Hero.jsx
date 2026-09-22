import { ONE_LINE_DECLARATION, ONE_LINE_PRODUCT } from '../constants'

export default function Hero({ onTryDemo }) {
  return (
    <section className="relative overflow-hidden rounded-2xl border border-slate-800 bg-gradient-to-br from-slate-900 via-slate-900 to-sky-950 p-8 md:p-12">
      <div className="absolute -top-32 -right-32 w-80 h-80 rounded-full bg-sky-500/10 blur-3xl pointer-events-none"></div>
      <div className="absolute -bottom-32 -left-32 w-80 h-80 rounded-full bg-fuchsia-500/10 blur-3xl pointer-events-none"></div>

      <div className="relative">
        <div className="flex items-center gap-2 text-xs uppercase tracking-widest text-sky-300 mb-3">
          <i className="fa fa-bolt"></i>
          GWDC 2026 Korea · FuriosaAI × Bricksum · Challenge A + B
        </div>

        <h1 className="text-3xl md:text-4xl font-semibold leading-tight text-slate-50">
          Copy-trading, locked by AI,<br />
          <span className="text-sky-300">unlocked by you.</span>
        </h1>

        <p className="mt-5 text-base md:text-lg text-slate-300 max-w-3xl leading-relaxed">
          {ONE_LINE_DECLARATION}
        </p>

        <p className="mt-4 text-sm text-slate-400 font-mono">
          {ONE_LINE_PRODUCT}
        </p>

        <div className="mt-7 flex flex-wrap items-center gap-3">
          <button
            onClick={onTryDemo}
            className="px-5 py-2.5 rounded-lg bg-sky-500 hover:bg-sky-400 text-slate-950 font-medium shadow-lg shadow-sky-500/20"
          >
            Try the Demo
            <i className="fa fa-arrow-right ml-2"></i>
          </button>
          <a
            href="https://docs.google.com/document/d/13qh7oePGl7Flrl-Zh_A6hfr02L266PvS/edit"
            target="_blank"
            rel="noopener noreferrer"
            className="px-5 py-2.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700"
          >
            <i className="fa fa-file-text-o mr-1"></i>
            PRD / Brief
          </a>
        </div>
      </div>
    </section>
  )
}