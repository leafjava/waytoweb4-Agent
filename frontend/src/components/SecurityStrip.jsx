const STAGES = [
  {
    n: '1',
    title: 'Pre-trade',
    body: 'No face → no start. Spec field whitelist (extra="forbid"). Notional ≤ 10k. maxLoss ≤ notional. Expiry > now.',
  },
  {
    n: '2',
    title: 'Inference',
    body: 'Kiln output is JSON; backend re-validates with Pydantic. No free-text Spec field is forwarded.',
  },
  {
    n: '3',
    title: 'Trade',
    body: 'Paper only (venue="paper"). Hard drawdown gate in code: if drawdown ≥ maxLoss → TRIP unconditionally. RedLine is a separate process.',
  },
  {
    n: '4',
    title: 'Post-trade (audit)',
    body: 'Every RedLine verdict emits structured JSON with reason_codes + evidence + source. Third parties replay from passport + log alone.',
  },
  {
    n: '5',
    title: 'What the AI cannot do',
    body: 'Change maxLoss. Disable RedLine. Open the face gate. Look at PnL to "waive" a TRIP. Inject schema-forbidden fields.',
  },
]

export default function SecurityStrip() {
  return (
    <section>
      <h2 className="text-sm uppercase tracking-wider text-slate-400 mb-4">
        <i className="fa fa-lock mr-2"></i> Security architecture
      </h2>
      <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
        {STAGES.map((s) => (
          <div
            key={s.n}
            className="bg-slate-900/50 border border-slate-800 rounded-lg p-4 relative"
          >
            <span className="absolute -top-3 -left-2 w-7 h-7 rounded-full bg-sky-500 text-slate-950 font-bold flex items-center justify-center text-sm">
              {s.n}
            </span>
            <div className="text-sm font-semibold text-slate-100 mb-1 mt-1">{s.title}</div>
            <div className="text-xs text-slate-400 leading-relaxed">{s.body}</div>
          </div>
        ))}
      </div>
    </section>
  )
}