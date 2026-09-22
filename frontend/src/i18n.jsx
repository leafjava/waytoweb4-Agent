// Tiny i18n: a flat key namespace, two locales (en / zh), localStorage
// persistence. Intentionally not using react-i18next -- 80 keys do not
// justify a dependency.
//
// Translation rules baked into this file:
//   * PRD §0 declaration (the long English sentence in Hero) is NOT
//     translated -- it is a verbatim quote from the PRD that judges
//     score against. See constants.js for the source string.
//   * Status enums (active / pending_face / revoked), verdict levels
//     (HOLD / WATCH / TRIP), and reason codes (DD_LIMIT / CB_LIKE /
//     etc.) are NOT translated -- they are code contracts that the
//     on-chain event log and the agent/ schema share. Localising
//     them would break auditability.

import { createContext, useContext, useEffect, useState } from 'react'

const STORAGE_KEY = 'w2w4.locale'

const STRINGS = {
  en: {
    // ---- Header -------------------------------------------------------
    'header.try_demo': 'Try the Demo',
    'header.back_home': '← Back to Home',
    'header.reset': 'Reset',
    'header.lang.zh': '中文',
    'header.lang.en': 'EN',

    // ---- Hero ---------------------------------------------------------
    'hero.eyebrow': 'GWDC 2026 Korea · FuriosaAI × Bricksum · Challenge A + B',
    'hero.title.line1': 'Copy-trading, locked by AI,',
    'hero.title.line2': 'unlocked by you.',
    'hero.product': 'NL → Spec → face → Paper copy-trading → on-chain passport → RedLine kill switch.',
    'hero.cta': 'Try the Demo',
    'hero.prd': 'PRD / Brief',

    // ---- Primitives grid ----------------------------------------------
    'primitives.title': 'Four primitives',
    'prim.follow.title': 'Follow Agent',
    'prim.follow.tag': 'Kiln · gpt-oss-120b',
    'prim.follow.body': 'NL → frozen Spec. 1–2 round clarification; JSON-only emit; backend re-validates with Pydantic. Model never sees face or max-loss after lock.',
    'prim.face.title': 'Face Gate',
    'prim.face.tag': 'human-in-the-loop',
    'prim.face.body': 'Face verification is the ONLY path to flip faceVerified=true. The agent has no API to do this. No LLM ever decides to start.',
    'prim.passport.title': 'Strategy Passport',
    'prim.passport.tag': 'keccak256 · mock | local | testnet',
    'prim.passport.body': 'Spec hashes via keccak256. Mint returns a 0x… tx hash; revoke returns a distinct second 0x… tx hash. Backend never lets the agent widen the cap.',
    'prim.redline.title': 'RedLine Agent',
    'prim.redline.tag': 'independent · no PnL',
    'prim.redline.body': 'Hard rule gate fires first (DD_LIMIT, no model override). LLM classifier only scores structural impact (Hynix / leverage / gap).',

    // ---- Judge checklist ----------------------------------------------
    'judge.title': 'What the judges will check',
    'judge.user_need': 'User need',
    'judge.user_need.body': 'Retail / judges want NL-driven copy-trading delegation, but the agent must not be able to widen loss limits.',
    'judge.agent_vs_code': 'Agent vs code',
    'judge.agent_vs_code.body': 'Agent: clarify, spec_emit, event classification. Code: schema validation, face gate, start/stop, mint/revoke, hard drawdown gate.',
    'judge.kiln': 'Kiln gpt-oss-120b',
    'judge.kiln.body': 'Follow multi-round clarify; RedLine event classifier. Mock fallback when KILN_API_KEY is unset (offline-safe).',
    'judge.tokens': 'Tokens split per flow',
    'judge.tokens.body': 'clarify / spec_emit / redline_hold / redline_trip / demo_inject — never a single total.',
    'judge.energy': 'Energy estimate',
    'judge.energy.body': '180W NPU-class assumption; energy_Wh = 180 × latency / 3600. Stated in README §9.',
    'judge.ontx': '≥1 on-chain tx',
    'judge.ontx.body': 'Mint returns keccak256 tx hash; revoke returns a distinct second tx hash. Honest disclaimer: no Sepolia broadcast unless RPC + contract deployed.',
    'judge.twice': 'Two controlled runs',
    'judge.twice.body': 'Run 1 (500U/50 loss) → engine trips at limit. Run 2 (smaller notional or Hynix inject) → trips sooner. Both leave a full event log.',
    'judge.overshoot': '越权即停',
    'judge.overshoot.body': 'mode=grid_bot, paper=False, maxLoss>notional, expired expiry, blocked leader — all rejected at validation, no engine call.',
    'judge.audit': '第三方可审计',
    'judge.audit.body': 'Passport + audit log alone let a third party answer: who, how much, face-verified?, why stopped? Every verdict carries reason_codes + source.',

    // ---- Spec simulator ----------------------------------------------
    'sim.title': 'Spec simulator',
    'sim.notional': 'notional (USD)',
    'sim.maxloss': 'max loss (USD)',
    'sim.expiry': 'expiry',
    'sim.venue': 'venue',
    'sim.mode': 'mode',
    'sim.expiry_val': '+{hours}h',
    'sim.venue_val': 'paper',
    'sim.mode_val': 'copy',
    'sim.invalid': 'max loss cannot exceed notional — backend will reject this Spec.',
    'sim.outcome.no_events': 'Without any events',
    'sim.outcome.no_events.note': 'engine reaches maxLoss=${maxLoss} in {sec}s; rule gate fires; model never gets a say',
    'sim.outcome.hynix': 'With Hynix event pack injected',
    'sim.outcome.hynix.note': 'LLM classifier scores structural impact; worst move {pct}%',
    'sim.outcome.dash': '—',
    'sim.frozen_attr': 'model_may_override = false',

    // ---- Security strip ----------------------------------------------
    'sec.title': 'Security architecture',
    'sec.1.title': 'Pre-trade',
    'sec.1.body': 'No face → no start. Spec field whitelist (extra="forbid"). Notional ≤ 10k. maxLoss ≤ notional. Expiry > now.',
    'sec.2.title': 'Inference',
    'sec.2.body': 'Kiln output is JSON; backend re-validates with Pydantic. No free-text Spec field is forwarded.',
    'sec.3.title': 'Trade',
    'sec.3.body': 'Paper only (venue="paper"). Hard drawdown gate in code: if drawdown ≥ maxLoss → TRIP unconditionally. RedLine is a separate process.',
    'sec.4.title': 'Post-trade (audit)',
    'sec.4.body': 'Every RedLine verdict emits structured JSON with reason_codes + evidence + source. Third parties replay from passport + log alone.',
    'sec.5.title': 'What the AI cannot do',
    'sec.5.body': 'Change maxLoss. Disable RedLine. Open the face gate. Look at PnL to "waive" a TRIP. Inject schema-forbidden fields.',

    // ---- Live data panel ---------------------------------------------
    'live.title': 'Live evidence',
    'live.polled': 'polled from',
    'live.polled.every': 'every 1.5s',
    'live.latest': 'Latest passport',
    'live.no_passport': 'No passport minted yet. Open the demo, lock a Spec, mint one.',
    'live.id': 'id',
    'live.spec_hash': 'spec hash',
    'live.mint_tx': 'mint tx',
    'live.revoke_tx': 'revoke tx',
    'live.status': 'status',
    'live.token_table': 'Token / energy table',
    'live.empty_table': '(no Kiln calls yet — open the demo and run a Spec to fill this in)',
    'live.audit_count': 'Audit events so far:',
    'live.footer_note': 'Same content served at',
    'live.footer_note.tail': '. Paste into the README §9 before submission.',

    // ---- Home page CTA -----------------------------------------------
    'home.cta': 'Try the Demo',
    'home.cta_sub': '3-minute walkthrough · PRD §7',

    // ---- Demo view: ChatPanel ----------------------------------------
    'chat.empty': 'Describe your copy-trading intent. Example: "follow leader-demo-001, 500 USD, max loss 50, 48h".',
    'chat.user_prefix': 'User>',
    'chat.agent_prefix': 'Agent>',
    'chat.placeholder': 'Type your follow-trading intent...',
    'chat.send': 'Send',
    'chat.locked_note': 'Spec locked.',

    // ---- Demo view: SpecCard -----------------------------------------
    'spec.title': 'Spec',
    'spec.locked': 'locked',
    'spec.empty': 'No spec yet. Send a message in Chat to fill in the fields.',
    'spec.leader': 'leader',
    'spec.notional': 'notional',
    'spec.maxloss': 'max loss',
    'spec.expiry': 'expiry',
    'spec.venue': 'venue',
    'spec.paper': 'paper',
    'spec.lock_btn': 'Lock Spec & Mint Passport',
    'spec.locked_btn': 'Spec locked in passport',
    'spec.intent_hash': 'intent hash',
    'spec.prepare_btn': 'Prepare Passport',
    'spec.confirm_mint_btn': 'Confirm & Mint Passport',
    'spec.authorized_btn': 'Passport authorized',
    'spec.working': 'Working…',
    'spec.authorization_failed': 'Authorization failed',

    // ---- Demo view: PassportCard -------------------------------------
    'pass.title': 'Passport',
    'pass.empty': 'No passport yet. Lock a Spec first.',
    'pass.id': 'id',
    'pass.spec_hash': 'spec hash',
    'pass.mint_tx': 'mint tx',
    'pass.revoke_tx': 'revoke tx',
    'pass.face': 'face',
    'pass.face_verified': 'verified',
    'pass.face_not_verified': 'not verified',
    'pass.verify_face': 'Verify Face',
    'pass.face_ok': 'Face OK',
    'pass.start_engine': 'Start Engine',
    'pass.engine_running': 'Engine running',
    'pass.copy': 'copy',
    'pass.copied': 'copied',

    // ---- Demo view: RedLinePanel -------------------------------------
    'red.title': 'RedLine',
    'red.running': 'running',
    'red.drawdown': 'drawdown',
    'red.verdict': 'verdict',
    'red.inject_hynix': 'Inject Hynix',
    'red.trigger': 'Trigger RedLine',

    // ---- VerdictBadge ------------------------------------------------
    'verdict.no_verdict': 'no verdict yet',
    'verdict.via': 'via',

    // ---- EventLog ----------------------------------------------------
    'events.title': 'events (latest)',
    'events.empty': 'no events yet',

    // ---- DrawdownGauge -----------------------------------------------
    'gauge.drawdown': 'drawdown',

    // ---- Demo: token strip -------------------------------------------
    'tokens.title': 'token / energy report',
    'tokens.empty': '—',
  },

  zh: {
    // ---- Header -------------------------------------------------------
    'header.try_demo': '进入 Demo',
    'header.back_home': '← 返回首页',
    'header.reset': '重置',
    'header.lang.zh': 'English',
    'header.lang.en': '中',

    // ---- Hero ---------------------------------------------------------
    'hero.eyebrow': 'GWDC 2026 韩国站 · FuriosaAI × Bricksum · Challenge A + B',
    'hero.title.line1': '跟单委托,AI 来锁,',
    'hero.title.line2': '你来开闸。',
    'hero.product': '自然语言 → Spec → 人脸闸 → 模拟盘跟单 → 链上护照 → RedLine 熔断。',
    'hero.cta': '进入 Demo',
    'hero.prd': 'PRD / 任务书',

    // ---- Primitives grid ----------------------------------------------
    'primitives.title': '四个核心组件',
    'prim.follow.title': 'Follow Agent',
    'prim.follow.tag': 'Kiln · gpt-oss-120b',
    'prim.follow.body': '自然语言 → 锁死的 Spec。1–2 轮澄清;JSON-only 输出;后端用 Pydantic 再校验一次。模型锁定后看不到人脸和限亏。',
    'prim.face.title': '人脸闸',
    'prim.face.tag': '人参与',
    'prim.face.body': '人脸闸是唯一把 faceVerified 翻成 true 的路径。Agent 没有 API 能改。模型永远不能决定开跑。',
    'prim.passport.title': '策略护照',
    'prim.passport.tag': 'keccak256 · mock | local | testnet',
    'prim.passport.body': 'Spec 用 keccak256 哈希。Mint 返回一条 0x… 交易哈希;Revoke 返回第二条不同的 0x… 哈希。后端永远不让模型放宽限亏。',
    'prim.redline.title': 'RedLine Agent',
    'prim.redline.tag': '独立进程 · 不看收益',
    'prim.redline.body': '硬闸先判(DD_LIMIT,模型无权覆盖)。LLM 分类器只打分结构冲击(海力士 / 杠杆 / 盘前异常)。',

    // ---- Judge checklist ----------------------------------------------
    'judge.title': '评委验收清单',
    'judge.user_need': '用户需求',
    'judge.user_need.body': '散户 / 评委想用自然语言委托跟单,但担心 Agent 代客后无法切断。',
    'judge.agent_vs_code': 'Agent vs Code',
    'judge.agent_vs_code.body': 'Agent 负责:澄清、Spec 产出、事件分类。Code 负责:字段校验、人脸闸、起停、铸烧护照、限亏硬闸。',
    'judge.kiln': 'Kiln gpt-oss-120b',
    'judge.kiln.body': 'Follow 多轮澄清 + RedLine 事件分类。KILN_API_KEY 未设时自动 fallback 到离线 Mock。',
    'judge.tokens': 'Token 按流程分桶',
    'judge.tokens.body': 'clarify / spec_emit / redline_hold / redline_trip / demo_inject —— 永远不报总数。',
    'judge.energy': '能耗估算',
    'judge.energy.body': '180W NPU 假设;energy_Wh = 180 × latency / 3600。README §9 已写明。',
    'judge.ontx': '≥1 笔链上交易',
    'judge.ontx.body': 'Mint 返回 keccak256 交易哈希;Revoke 返回第二条不同的哈希。诚实声明:未接 Sepolia RPC 与部署合约前不发真实交易。',
    'judge.twice': '两次条件对照',
    'judge.twice.body': 'Run 1(500U / 50 亏)→ 引擎到限停。Run 2(小额度 或注入海力士)→ 更早停。两次都留完整事件日志。',
    'judge.overshoot': '越权即停',
    'judge.overshoot.body': 'mode=grid_bot、paper=False、maxLoss>notional、过期、禁 Leader —— 全部在校验阶段拒绝,不调引擎。',
    'judge.audit': '第三方可审计',
    'judge.audit.body': '仅凭护照 + 日志,第三方就能回答:跟谁、多少钱、是否人脸、为何停。每次判决都带 reason_codes + source。',

    // ---- Spec simulator ----------------------------------------------
    'sim.title': 'Spec 模拟器',
    'sim.notional': '本金 (USD)',
    'sim.maxloss': '限亏 (USD)',
    'sim.expiry': '到期',
    'sim.venue': '场所',
    'sim.mode': '类型',
    'sim.expiry_val': '+{hours} 小时',
    'sim.venue_val': '模拟盘',
    'sim.mode_val': '跟单',
    'sim.invalid': '限亏不能超过本金 —— 后端会拒绝这个 Spec。',
    'sim.outcome.no_events': '无任何事件',
    'sim.outcome.no_events.note': '{sec} 秒后引擎画线到 maxLoss=$${maxLoss};硬闸触发;模型无发言权',
    'sim.outcome.hynix': '注入海力士事件包',
    'sim.outcome.hynix.note': 'LLM 分类器评估结构冲击;最差单笔跌幅 {pct}%',
    'sim.outcome.dash': '—',
    'sim.frozen_attr': 'model_may_override = false',

    // ---- Security strip ----------------------------------------------
    'sec.title': '安全架构',
    'sec.1.title': '交易前',
    'sec.1.body': '无人脸不开跑。Spec 字段白名单(extra="forbid")。本金 ≤ 10k。限亏 ≤ 本金。到期 > 当前。',
    'sec.2.title': '推理中',
    'sec.2.body': 'Kiln 输出 JSON;后端用 Pydantic 再校验。任何自由文本字段都不透传到下游。',
    'sec.3.title': '交易中',
    'sec.3.body': '只跑模拟盘(venue="paper")。代码硬闸:drawdown ≥ maxLoss 即无条件 TRIP。RedLine 独立进程。',
    'sec.4.title': '事后(审计)',
    'sec.4.body': '每次 RedLine 判决都产结构化 JSON,带 reason_codes + evidence + source。第三方仅凭护照 + 日志即可复���。',
    'sec.5.title': 'AI 不能做的事',
    'sec.5.body': '改 maxLoss。关 RedLine。自己开人脸闸。看 PnL 给 TRIP"放行"。塞 schema 禁止的字段。',

    // ---- Live data panel ---------------------------------------------
    'live.title': '实时证据',
    'live.polled': '从',
    'live.polled.every': '每 1.5 秒轮询',
    'live.latest': '最新护照',
    'live.no_passport': '还没有护照。打开 Demo,锁一个 Spec,mint 一本。',
    'live.id': 'ID',
    'live.spec_hash': 'Spec 哈希',
    'live.mint_tx': 'Mint 交易',
    'live.revoke_tx': 'Revoke 交易',
    'live.status': '状态',
    'live.token_table': 'Token / 能耗表',
    'live.empty_table': '(还没有 Kiln 调用 —— 打开 Demo 跑一个 Spec 即可填上)',
    'live.audit_count': '审计事件数:',
    'live.footer_note': '同样的内容也可以从',
    'live.footer_note.tail': '拿到。提交前贴进 README §9。',

    // ---- Home page CTA -----------------------------------------------
    'home.cta': '进入 Demo',
    'home.cta_sub': '3 分钟走完 · PRD §7',

    // ---- Demo view: ChatPanel ----------------------------------------
    'chat.empty': '用一句话描述你想怎么跟单。例:"跟 leader-demo-001,500 USD,亏 50 停,48 小时"。',
    'chat.user_prefix': '用户>',
    'chat.agent_prefix': 'Agent>',
    'chat.placeholder': '输入跟单意图...',
    'chat.send': '发送',
    'chat.locked_note': 'Spec 已锁定。',

    // ---- Demo view: SpecCard -----------------------------------------
    'spec.title': 'Spec',
    'spec.locked': '已锁定',
    'spec.empty': '还没有 Spec。在聊天里发一句话,把字段填齐。',
    'spec.leader': 'leader',
    'spec.notional': '本金',
    'spec.maxloss': '限亏',
    'spec.expiry': '到期',
    'spec.venue': '场所',
    'spec.paper': 'paper',
    'spec.lock_btn': '锁定 Spec 并铸护照',
    'spec.locked_btn': 'Spec 已铸入护照',
    'spec.intent_hash': '意图哈希',
    'spec.prepare_btn': '准备护照',
    'spec.confirm_mint_btn': '确认并铸造护照',
    'spec.authorized_btn': '护照已授权',
    'spec.working': '处理中…',
    'spec.authorization_failed': '授权失败',

    // ---- Demo view: PassportCard -------------------------------------
    'pass.title': '护照',
    'pass.empty': '还没有护照。先锁一个 Spec。',
    'pass.id': 'ID',
    'pass.spec_hash': 'Spec 哈希',
    'pass.mint_tx': 'Mint 交易',
    'pass.revoke_tx': 'Revoke 交易',
    'pass.face': '人脸',
    'pass.face_verified': '已验证',
    'pass.face_not_verified': '未验证',
    'pass.verify_face': '人脸验证',
    'pass.face_ok': '人脸已通过',
    'pass.start_engine': '启动引擎',
    'pass.engine_running': '引擎运行中',
    'pass.copy': '复制',
    'pass.copied': '已复制',

    // ---- Demo view: RedLinePanel -------------------------------------
    'red.title': 'RedLine',
    'red.running': '运行中',
    'red.drawdown': '回撤',
    'red.verdict': '判决',
    'red.inject_hynix': '注入海力士',
    'red.trigger': '触发 RedLine',

    // ---- VerdictBadge ------------------------------------------------
    'verdict.no_verdict': '暂无判决',
    'verdict.via': '经',

    // ---- EventLog ----------------------------------------------------
    'events.title': '最近事件',
    'events.empty': '暂无事件',

    // ---- DrawdownGauge -----------------------------------------------
    'gauge.drawdown': '回撤',

    // ---- Demo: token strip -------------------------------------------
    'tokens.title': 'Token / 能耗报告',
    'tokens.empty': '—',
  },
}

const I18nCtx = createContext({
  locale: 'en',
  setLocale: () => {},
  toggle: () => {},
  t: (key) => key,
})

export function I18nProvider({ children }) {
  const [locale, setLocaleState] = useState(() => {
    try {
      return localStorage.getItem(STORAGE_KEY) || 'en'
    } catch (_) {
      return 'en'
    }
  })

  // Persist on change. Skip the initial mount where we just read.
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, locale)
    } catch (_) {
      // localStorage unavailable (private window) -- just ignore.
    }
  }, [locale])

  function setLocale(next) {
    if (next !== 'en' && next !== 'zh') return
    setLocaleState(next)
  }
  function toggle() {
    setLocaleState((cur) => (cur === 'en' ? 'zh' : 'en'))
  }
  function t(key) {
    return STRINGS[locale]?.[key] ?? STRINGS.en?.[key] ?? key
  }

  return (
    <I18nCtx.Provider value={{ locale, setLocale, toggle, t }}>
      {children}
    </I18nCtx.Provider>
  )
}

export function useI18n() {
  return useContext(I18nCtx)
}

export const LOCALES = [
  { code: 'en', label: 'English' },
  { code: 'zh', label: '中文' },
]
