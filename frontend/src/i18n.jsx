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
    'prim.passport.tag': 'keccak256 · mock | sepolia',
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

    // ---- ConditionalRunPanel (PRD §5 two-run) ------------------------
    'demo.cond.title': 'Controlled runs (PRD §5)',
    'demo.cond.empty': 'No two-runs report yet. Run `python scripts/two_runs_demo.py` from the project root to populate this panel.',
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
    'prim.passport.tag': 'keccak256 · mock | sepolia',
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

    // ---- ConditionalRunPanel (PRD §5 two-run) ------------------------
    'demo.cond.title': '控制对照运行 (PRD §5)',
    'demo.cond.empty': '暂无两轮对照报告。在项目根目录运行 `python scripts/two_runs_demo.py` 以填充此面板。',
  },
  ko: {
    // ---- Header -------------------------------------------------------
    // ---- Header -------------------------------------------------------
    'header.try_demo': '데모 시작',
    'header.back_home': '← 홈으로',
    'header.reset': '초기화',
    'header.lang.zh': '中文',
    'header.lang.en': 'EN',
    // ---- Hero ---------------------------------------------------------
    'hero.eyebrow': 'GWDC 2026 코리아 · FuriosaAI × Bricksum · Challenge A + B',
    'hero.title.line1': '카피 트레이딩, AI가 잠그고,',
    'hero.title.line2': '당신이 문을 엽니다.',
    'hero.product': '자연어 → Spec → 얼굴 인증 → 모의 트레이딩 → 온체인 패스포트 → RedLine 킬 스위치.',
    'hero.cta': '데모 시작',
    'hero.prd': 'PRD / 과제서',
    'primitives.title': '네 가지 핵심 요소',
    // ---- Primitives grid ---------------------------------------------
    'prim.follow.title': 'Follow Agent',
    'prim.follow.tag': 'Kiln · gpt-oss-120b',
    'prim.follow.body': '자연어를 잠긴 Spec으로. 1-2회 명확화; JSON 전용 출력; 백엔드는 Pydantic으로 재검증. 잠근 후 모델은 얼굴·손실한도를 보지 못함.',
    'prim.face.title': '얼굴 게이트',
    'prim.face.tag': '인간 개입',
    'prim.face.body': '얼굴 인증은 faceVerified=true로 뒤집는 유일한 경로. Agent는 변경 API 없음. 모델이 시작을 결정하는 일 없음.',
    'prim.passport.title': '전략 패스포트',
    'prim.passport.tag': 'keccak256 · mock | sepolia',
    'prim.passport.body': 'Spec을 keccak256 해시. Mint는 0x... 트랜잭션 해시 반환; Revoke는 두 번째 다른 0x... 해시 반환. 백엔드는 모델이 손실한도를 풀지 못하게 함.',
    'prim.redline.title': 'RedLine Agent',
    'prim.redline.tag': '독립 프로세스 · 수익 무시',
    'prim.redline.body': '하드 게이트 우선 (DD_LIMIT, 모델 우회 불가). LLM 분류기는 구조적 충격만 평가 (하이닉스 / 레버리지 / 갭).',
    // ---- Judge checklist ---------------------------------------------
    'judge.title': '심사위원 검증 체크리스트',
    'judge.user_need': '사용자 요구',
    'judge.user_need.body': '개인 투자자 / 심사위원은 자연어로 카피 트레이딩을 위임하고 싶지만 Agent가 손실한도를 임의로 풀지 못할까 우려함.',
    'judge.agent_vs_code': 'Agent vs Code',
    'judge.agent_vs_code.body': 'Agent 담당: 명확화, Spec 산출, 이벤트 분류. Code 담당: 필드 검증, 얼굴 게이트, 시작/정지, 패스포트 발행/소각, 손실한도 하드 게이트.',
    'judge.kiln': 'Kiln gpt-oss-120b',
    'judge.kiln.body': 'Follow 다회 명확화 + RedLine 이벤트 분류. KILN_API_KEY 미설정 시 오프라인 Mock으로 자동 fallback.',
    'judge.tokens': 'Token 단계별 분할',
    'judge.tokens.body': 'clarify / spec_emit / redline_hold / redline_trip / demo_inject — 절대 합계만 보고하지 않음.',
    'judge.energy': '에너지 추정',
    'judge.energy.body': '180W NPU 가정; energy_Wh = 180 × latency / 3600. README §9 명시.',
    'judge.ontx': '온체인 tx ≥1건',
    'judge.ontx.body': 'Mint는 keccak256 트랜잭션 해시 반환; Revoke는 두 번째 다른 해시 반환. 정직한 고지: Sepolia RPC 및 컨트랙트 배포 전 실제 트랜잭션 미발행.',
    'judge.twice': '두 번의 통제 비교 실행',
    'judge.twice.body': 'Run 1 (500U / 50 손실) → 엔진 한도 도달 시 정지. Run 2 (작은 금액 또는 하이닉스 주입) → 더 일찍 정지. 두 번 모두 전체 이벤트 로그 보관.',
    'judge.overshoot': '권한 초과 시 즉시 정지',
    'judge.overshoot.body': 'mode=grid_bot, paper=False, maxLoss>notional, 만료, 금지 Leader — 모두 검증 단계에서 거부, 엔진 호출 없음.',
    'judge.audit': '제3자 감사 가능',
    'judge.audit.body': '패스포트 + 로그만으로 제3자가 답��� 가능: 누구를, 얼마만큼, 얼굴 인증 여부, 왜 정지했는가. 모든 판결에 reason_codes + source 포함.',
    // ---- Spec simulator ---------------------------------------------
    'sim.title': 'Spec 시뮬레이터',
    'sim.notional': '원금 (USD)',
    'sim.maxloss': '최대 손실 (USD)',
    'sim.expiry': '만료',
    'sim.venue': '장소',
    'sim.mode': '유형',
    'sim.expiry_val': '+{hours}시간',
    'sim.venue_val': '모의',
    'sim.mode_val': '카피',
    'sim.invalid': '최대 손실은 원금을 초과할 수 없음 — 백엔드가 이 Spec을 거부함.',
    'sim.outcome.no_events': '이벤트 없음',
    'sim.outcome.no_events.note': '{sec}초 후 엔진이 maxLoss=${maxLoss}에 도달; 하드 게이트 발동; 모델 개입 없음',
    'sim.outcome.hynix': '하이닉스 이벤트 팩 주입',
    'sim.outcome.hynix.note': 'LLM 분류기가 구조적 충격 평가; 최악 단일 변동 {pct}%',
    'sim.outcome.dash': '—',
    'sim.frozen_attr': 'model_may_override = false',
    // ---- Security strip ---------------------------------------------
    'sec.title': '보안 아키텍처',
    'sec.1.title': '거래 전',
    'sec.1.body': '얼굴 인증 없으면 시작 불가. Spec 필드 화이트리스트 (extra="forbid"). 원금 ≤ 10k. maxLoss ≤ 원금. 만료 > 현재.',
    'sec.2.title': '추론 중',
    'sec.2.body': 'Kiln 출력은 JSON; 백엔드가 Pydantic으로 재검증. 자유 텍스트 필드는 하류로 전달되지 않음.',
    'sec.3.title': '거래 중',
    'sec.3.body': '모의 거래만 (venue="paper"). 코드 하드 게이트: drawdown ≥ maxLoss이면 무조건 TRIP. RedLine은 독립 프로세스.',
    'sec.4.title': '거래 후 (감사)',
    'sec.4.body': '모든 RedLine 판결은 구조화된 JSON 출력, reason_codes + evidence + source 포함. 제3자는 패스포트 + 로그만으로 재구성 가능.',
    'sec.5.title': 'AI가 할 수 없는 것',
    'sec.5.body': 'maxLoss 변경. RedLine 비활성화. 얼굴 게이트 자체 열기. PnL을 보고 TRIP "면제". 스키마 금지 필드 주입.',
    // ---- Live data panel ---------------------------------------------
    'live.title': '실시간 증거',
    'live.polled': '다음에서 폴링',
    'live.polled.every': '1.5초마다',
    'live.latest': '최신 패스포트',
    'live.no_passport': '아직 발행된 패스포트 없음. 데모를 열고 Spec을 잠그면 발행됨.',
    'live.id': 'ID',
    'live.spec_hash': 'Spec 해시',
    'live.mint_tx': 'Mint 트랜잭션',
    'live.revoke_tx': 'Revoke 트랜잭션',
    'live.status': '상태',
    'live.token_table': 'Token / 에너지 표',
    'live.empty_table': '(아직 Kiln 호출 없음 — 데모를 열고 Spec을 실행하면 채워짐)',
    'live.audit_count': '지금까지 감사 이벤트:',
    'live.footer_note': '동일 내용이 다음에서도 제공됨',
    'live.footer_note.tail': '. 제출 전 README §9에 붙여넣기.',
    // ---- Home page CTA -----------------------------------------------
    'home.cta': '데모 시작',
    'home.cta_sub': '3분 둘러보기 · PRD §7',
    // ---- Demo view: ChatPanel ----------------------------------------
    'chat.empty': '카피 트레이딩 의도를 한 문장으로 설명. 예: "leader-demo-001, 500 USD, 손실 50까지, 48시간".',
    'chat.user_prefix': '사용자>',
    'chat.agent_prefix': 'Agent>',
    'chat.placeholder': '카피 트레이딩 의도 입력...',
    'chat.send': '전송',
    'chat.locked_note': 'Spec 잠김.',
    // ---- Demo view: SpecCard -----------------------------------------
    'spec.title': 'Spec',
    'spec.locked': '잠김',
    'spec.empty': '아직 Spec 없음. 채팅에서 메시지를 보내 필드를 채움.',
    'spec.leader': 'leader',
    'spec.notional': '원금',
    'spec.maxloss': '최대 손실',
    'spec.expiry': '만료',
    'spec.venue': '장소',
    'spec.paper': 'paper',
    'spec.lock_btn': 'Spec 잠그고 패스포트 발행',
    'spec.locked_btn': 'Spec이 패스포트에 잠김',
    // ---- Demo view: PassportCard -------------------------------------
    'pass.title': '패스포트',
    'pass.empty': '아직 패스포트 없음. 먼저 Spec을 잠그기.',
    'pass.id': 'ID',
    'pass.spec_hash': 'Spec 해시',
    'pass.mint_tx': 'Mint 트랜잭션',
    'pass.revoke_tx': 'Revoke 트랜잭션',
    'pass.face': '얼굴',
    'pass.face_verified': '인증됨',
    'pass.face_not_verified': '미인증',
    'pass.verify_face': '얼굴 인증',
    'pass.face_ok': '얼굴 통과',
    'pass.start_engine': '엔진 시작',
    'pass.engine_running': '엔진 실행 중',
    'pass.copy': '복사',
    'pass.copied': '복사됨',
    // ---- Demo view: RedLinePanel -------------------------------------
    'red.title': 'RedLine',
    'red.running': '실행 중',
    'red.drawdown': '드로다운',
    'red.verdict': '판결',
    'red.inject_hynix': '하이닉스 주입',
    'red.trigger': 'RedLine 트리거',
    // ---- VerdictBadge ------------------------------------------------
    'verdict.no_verdict': '아직 판결 없음',
    'verdict.via': '출처',
    // ---- EventLog ----------------------------------------------------
    'events.title': '최근 이벤트',
    'events.empty': '이벤트 없음',
    // ---- DrawdownGauge -----------------------------------------------
    'gauge.drawdown': '드로다운',
    // ---- Demo: token strip -------------------------------------------
    'tokens.title': 'Token / 에너지 보고서',
    'tokens.empty': '—',

    // ---- ConditionalRunPanel (PRD §5 two-run) ------------------------
    'demo.cond.title': '통제 비교 실행 (PRD §5)',
    'demo.cond.empty': '두 라운드 보고서 없음. 프로젝트 루트에서 `python scripts/two_runs_demo.py` 실행하여 이 패널 채우기.',
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
    if (next !== 'en' && next !== 'zh' && next !== 'ko') return
    setLocaleState(next)
  }
  function toggle() {
    // Cycle: en -> zh -> ko -> en. Show the next locale's name in the
    // switcher (handled by Header.jsx) so users see what they will get.
    setLocaleState((cur) => (cur === 'en' ? 'zh' : cur === 'zh' ? 'ko' : 'en'))
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
  { code: 'ko', label: '한국어' },
]