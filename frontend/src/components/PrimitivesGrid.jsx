const PRIMITIVES = [
  {
    icon: 'fa-commenting',
    color: 'sky',
    title: 'Follow Agent',
    tag: 'Kiln · gpt-oss-120b',
    body: 'NL → frozen Spec. 1–2 round clarification; JSON-only emit; backend re-validates with Pydantic. Model never sees face or max-loss after lock.',
  },
  {
    icon: 'fa-user-circle-o',
    color: 'amber',
    title: 'Face Gate',
    tag: 'human-in-the-loop',
    body: 'Face verification is the ONLY path to flip faceVerified=true. The agent has no API to do this. No LLM ever decides to start.',
  },
  {
    icon: 'fa-id-card',
    color: 'emerald',
    title: 'Strategy Passport',
    tag: 'keccak256 · mock | sepolia',
    body: 'Spec hashes via keccak256. Mint returns a 0x… tx hash; revoke returns a distinct second 0x… tx hash. Backend never lets the agent widen the cap.',
  },
  {
    icon: 'fa-shield',
    color: 'fuchsia',
    title: 'RedLine Agent',
    tag: 'independent · no PnL',
    body: 'Hard rule gate fires first (DD_LIMIT, no model override). LLM classifier only scores structural impact (Hynix / leverage / gap).',
  },
]

const COLOR_CLASSES = {
  sky: 'border-sky-700/50 bg-sky-900/20 text-sky-300',
  amber: 'border-amber-700/50 bg-amber-900/20 text-amber-300',
  emerald: 'border-emerald-700/50 bg-emerald-900/20 text-emerald-300',
  fuchsia: 'border-fuchsia-700/50 bg-fuchsia-900/20 text-fuchsia-300',
}

export default function PrimitivesGrid() {
  return (
    <section>
      <h2 className="text-sm uppercase tracking-wider text-slate-400 mb-4">
        <i className="fa fa-cubes mr-2"></i> Four primitives
      </h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {PRIMITIVES.map((p) => (
          <div
            key={p.title}
            className={`border rounded-xl p-5 ${COLOR_CLASSES[p.color]} bg-slate-900/40`}
          >
            <div className="flex items-center justify-between mb-3">
              <i className={`fa ${p.icon} text-2xl`}></i>
              <span className="text-[10px] uppercase tracking-wider opacity-70">{p.tag}</span>
            </div>
            <h3 className="text-lg font-semibold text-slate-50 mb-1.5">{p.title}</h3>
            <p className="text-sm text-slate-400 leading-relaxed">{p.body}</p>
          </div>
        ))}
      </div>
    </section>
  )
}