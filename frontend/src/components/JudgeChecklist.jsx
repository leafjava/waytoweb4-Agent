// PRD §5 — official acceptance criteria. We surface every row here
// so judges can verify, line by line, that what we promised is what
// we shipped. "Where" is a path the judges can `cat` themselves.

const ROWS = [
  {
    icon: 'fa-users',
    label: 'User need',
    body: 'Retail / judges want NL-driven copy-trading delegation, but the agent must not be able to widen loss limits.',
    where: 'docs/security-arch.md',
  },
  {
    icon: 'fa-code-fork',
    label: 'Agent vs code',
    body: 'Agent: clarify, spec_emit, event classification. Code: schema validation, face gate, start/stop, mint/revoke, hard drawdown gate.',
    where: 'agent/ + backend/app/',
  },
  {
    icon: 'fa-server',
    label: 'Kiln gpt-oss-120b',
    body: 'Follow multi-round clarify; RedLine event classifier. Mock fallback when KILN_API_KEY is unset (offline-safe).',
    where: 'agent/follow_agent/kiln_client.py',
  },
  {
    icon: 'fa-table',
    label: 'Tokens split per flow',
    body: 'clarify / spec_emit / redline_hold / redline_trip / demo_inject — never a single total.',
    where: 'live table at the bottom of this page',
  },
  {
    icon: 'fa-bolt',
    label: 'Energy estimate',
    body: '180W NPU-class assumption; energy_Wh = 180 × latency / 3600. Stated in README §9.',
    where: 'agent/shared/energy.py',
  },
  {
    icon: 'fa-link',
    label: '≥1 on-chain tx',
    body: 'Mint returns keccak256 tx hash; revoke returns a distinct second tx hash. Honest disclaimer: no Sepolia broadcast unless RPC + contract deployed.',
    where: 'live panel below',
  },
  {
    icon: 'fa-clone',
    label: 'Two controlled runs',
    body: 'Run 1 (500U/50 loss) → engine trips at limit. Run 2 (smaller notional or Hynix inject) → trips sooner. Both leave a full event log.',
    where: 'demo page · EventLog',
  },
  {
    icon: 'fa-ban',
    label: '越权即停',
    body: 'mode=grid_bot, paper=False, maxLoss>notional, expired expiry, blocked leader — all rejected at validation, no engine call.',
    where: 'agent/follow_agent/spec_schema.py',
  },
  {
    icon: 'fa-search',
    label: '第三方可审计',
    body: 'Passport + audit log alone let a third party answer: who, how much, face-verified?, why stopped? Every verdict carries reason_codes + source.',
    where: 'docs/security-arch.md',
  },
]

export default function JudgeChecklist() {
  return (
    <section>
      <h2 className="text-sm uppercase tracking-wider text-slate-400 mb-4">
        <i className="fa fa-check-square-o mr-2"></i> What the judges will check
      </h2>
      <div className="bg-slate-900/40 border border-slate-800 rounded-xl overflow-hidden">
        <ul className="divide-y divide-slate-800">
          {ROWS.map((r) => (
            <li key={r.label} className="p-4 flex gap-4 items-start hover:bg-slate-900/60">
              <i className={`fa ${r.icon} text-sky-400 mt-1 w-5 text-center`}></i>
              <div className="flex-1 min-w-0">
                <div className="text-sm font-semibold text-slate-100">{r.label}</div>
                <div className="text-sm text-slate-400 mt-0.5">{r.body}</div>
              </div>
              <code className="text-[11px] text-slate-500 font-mono whitespace-nowrap ml-3 hidden md:block">
                {r.where}
              </code>
            </li>
          ))}
        </ul>
      </div>
    </section>
  )
}