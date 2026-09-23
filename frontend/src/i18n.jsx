// Tiny i18n: a flat key namespace, two locales (en / ko), localStorage
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
    'header.lang.ko': '한국어',
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
    'judge.overshoot': 'Out-of-scope stops',
    'judge.overshoot.body': 'mode=grid_bot, paper=False, maxLoss>notional, expired expiry, blocked leader — all rejected at validation, no engine call.',
    'judge.audit': 'Third-party auditable',
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
    'pass.face_historical': 'verified · expired',
    'pass.face_not_verified': 'not verified',
    'pass.verify_face': 'Verify Face',
    'pass.authorize_first': 'Authorize first',
    'pass.face_ok': 'Face OK',
    'pass.verified_at': 'approved at',
    'pass.method': 'method',
    'pass.session': 'approval session',
    'pass.gate_status': 'gate status',
    'pass.gate_pending': 'pending',
    'pass.gate_active': 'ready to start',
    'pass.gate_consumed': 'used for this run',
    'pass.gate_invalidated': 'invalidated',
    'pass.gate_invalidated_help': 'This approval cannot authorize another run. Create a new frozen mandate and approve it again.',
    'pass.start_engine': 'Start Engine',
    'pass.engine_running': 'Engine running',
    'pass.copy': 'copy',
    'pass.copied': 'copied',

    // ---- Human gate --------------------------------------------------
    'gate.title': 'Approve this mandate',
    'gate.subtitle': 'Execution cannot begin until a person reviews this exact paper-trading mandate and approves it now.',
    'gate.close': 'Close human approval',
    'gate.preview': 'Local camera preview',
    'gate.camera.idle': 'Camera preview is waiting to start.',
    'gate.camera.requesting': 'Requesting camera access…',
    'gate.camera.ready': 'Local preview ready',
    'gate.camera.denied': 'Camera access was denied. Allow camera access in the browser, then reopen this approval.',
    'gate.camera.unsupported': 'This browser does not provide camera access. Use a current browser to approve the mandate.',
    'gate.privacy': 'The preview stays in this browser. No image is captured, uploaded, stored, or used for training.',
    'gate.mandate': 'Mandate under approval',
    'gate.paper_only': 'Paper trading only',
    'gate.consent': 'I am present and approve this leader, amount, loss limit, expiry, and paper-only execution.',
    'gate.approve_start': 'Approve and start paper execution',
    'gate.approving': 'Recording approval and starting…',
    'gate.error.required': 'Approval was not recorded. Review the mandate and try again.',
    'gate.error.generic': 'Approval could not be completed. Check the connection and try again.',

    // ---- Inference evidence -----------------------------------------
    'evidence.title': 'Inference workload & control evidence',
    'evidence.subtitle': 'Per-flow inference demand is shown beside the authorization and stop timeline for this run.',
    'evidence.model': 'model',
    'evidence.mode': 'source',
    'evidence.power': 'power assumption',
    'evidence.flows': 'Token and energy by flow',
    'evidence.calls': 'calls',
    'evidence.sessions': 'active sessions',
    'evidence.passports': 'passports',
    'evidence.flow': 'flow',
    'evidence.in': 'tokens in',
    'evidence.out': 'tokens out',
    'evidence.latency': 'latency',
    'evidence.energy': 'energy est.',
    'evidence.source': 'usage source',
    'evidence.total': 'total',
    'evidence.assumption': 'Energy is estimated as 180 W × API latency ÷ 3600. Offline values are simulated or estimated; final live evidence requires API-reported usage.',
    'evidence.timeline': 'Authorization and control timeline',
    'evidence.timeline_empty': 'Run the demo to build a replayable authorization and stop timeline.',
    'evidence.run': 'run ID',

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

  ko: {
    // ---- Header -------------------------------------------------------
    'header.try_demo': '데모 체험',
    'header.back_home': '← 홈으로',
    'header.reset': '초기화',
    'header.lang.ko': '한국어',
    'header.lang.en': 'EN',

    // ---- Hero ---------------------------------------------------------
    'hero.eyebrow': 'GWDC 2026 한국 · FuriosaAI × Bricksum · Challenge A + B',
    'hero.title.line1': '카피 트레이딩을 AI가 잠그고,',
    'hero.title.line2': '멈추는 것은 당신입니다.',
    'hero.product': '자연어 → Spec → 페이스 게이트 → 페이퍼 카피 트레이딩 → 온체인 패스포트 → RedLine 킬 스위치.',
    'hero.cta': '데모 체험',
    'hero.prd': 'PRD / 브리프',

    // ---- Primitives grid ----------------------------------------------
    'primitives.title': '네 가지 핵심 구성요소',
    'prim.follow.title': 'Follow Agent',
    'prim.follow.tag': 'Kiln · gpt-oss-120b',
    'prim.follow.body': '자연어 → 고정된 Spec. 1–2회 명확화 질의; JSON 전용 출력; 백엔드가 Pydantic으로 재검증합니다. 잠긴 후에는 모델이 face나 최대 손실 한도를 볼 수 없습니다.',
    'prim.face.title': '페이스 게이트',
    'prim.face.tag': '사람이 개입',
    'prim.face.body': 'faceVerified를 true로 바꿀 수 있는 유일한 경로는 페이스 게이트입니다. 에이전트에게는 이를 위한 API가 없습니다. 시작을 LLM이 결정하는 일은 없습니다.',
    'prim.passport.title': '전략 패스포트',
    'prim.passport.tag': 'keccak256 · mock | local | testnet',
    'prim.passport.body': 'Spec은 keccak256으로 해시됩니다. 민팅은 0x… 트랜잭션 해시를, 철회(revoke)는 별개의 두 번째 해시를 반환합니다. 백엔드는 에이전트가 한도를 넓히지 못하게 막습니다.',
    'prim.redline.title': 'RedLine Agent',
    'prim.redline.tag': '독립 프로세스 · PnL 미사용',
    'prim.redline.body': '하드 규칙 게이트가 먼저 작동합니다(DD_LIMIT, 모델이 덮어쓸 수 없음). LLM 분류기는 구조적 충격(하이닉스 / 레버리지 / 갭)만 점수화합니다.',

    // ---- Judge checklist ----------------------------------------------
    'judge.title': '심사위원 체크리스트',
    'judge.user_need': '사용자 니즈',
    'judge.user_need.body': '개인 투자자와 심사위원은 자연어로 카피 트레이딩을 위임하고 싶지만, 에이전트가 손실 한도를 넓힐 수 없어야 한다고 우려합니다.',
    'judge.agent_vs_code': 'Agent vs Code',
    'judge.agent_vs_code.body': 'Agent: 명확화, spec_emit, 이벤트 분류. Code: 스키마 검증, 페이스 게이트, 시작/정지, 민팅/철회, 드로다운 하드 게이트.',
    'judge.kiln': 'Kiln gpt-oss-120b',
    'judge.kiln.body': 'Follow 다중 명확화 + RedLine 이벤트 분류. KILN_API_KEY 미설정 시 오프라인 안전 Mock으로 폴백합니다.',
    'judge.tokens': '플로우별 토큰 분리',
    'judge.tokens.body': 'clarify / spec_emit / redline_hold / redline_trip / demo_inject — 총합 하나로만 보고하지 않습니다.',
    'judge.energy': '에너지 추정',
    'judge.energy.body': '180W NPU급 가정; energy_Wh = 180 × latency / 3600. README §9에 명시.',
    'judge.ontx': '온체인 트랜잭션 ≥ 1건',
    'judge.ontx.body': '민팅은 트랜잭션 해시를, 철회는 별개의 두 번째 해시를 반환합니다. 정직한 고지: Sepolia RPC와 배포된 컨트랙트 없이는 실제 브로드캐스트를 하지 않습니다.',
    'judge.twice': '두 번의 조건 대조 실행',
    'judge.twice.body': 'Run 1(500U / 손실 50) → 한도에서 정지. Run 2(더 작은 명목 금액 또는 하이닉스 이벤트 주입) → 더 일찍 정지. 두 실행 모두 전체 이벤트 로그를 남깁니다.',
    'judge.overshoot': '권한 밖 실행 즉시 정지',
    'judge.overshoot.body': 'mode=grid_bot, paper=False, maxLoss>notional, 만기 경과, 차단된 리더 — 모두 검증 단계에서 거부되며 엔진을 호출하지 않습니다.',
    'judge.audit': '제3자 감사 가능',
    'judge.audit.body': '패스포트 + 감사 로그만으로 제3자가 답할 수 있습니다: 누구를, 얼마나, face 인증 여부, 왜 멈췄는지. 모든 판정에는 reason_codes + source가 포함됩니다.',

    // ---- Spec simulator ----------------------------------------------
    'sim.title': 'Spec 시뮬레이터',
    'sim.notional': '명목 금액 (USD)',
    'sim.maxloss': '최대 손실 (USD)',
    'sim.expiry': '만기',
    'sim.venue': '거래 장소',
    'sim.mode': '유형',
    'sim.expiry_val': '+{hours}시간',
    'sim.venue_val': '페이퍼',
    'sim.mode_val': '카피',
    'sim.invalid': '최대 손실은 명목 금액을 초과할 수 없습니다 — 백엔드가 이 Spec을 거부합니다.',
    'sim.outcome.no_events': '이벤트 없이 방치하면',
    'sim.outcome.no_events.note': '{sec}초 후 엔진이 maxLoss=${maxLoss} 도달; 하드 규칙 게이트 발동; 모델은 발언권 없음',
    'sim.outcome.hynix': '하이닉스 이벤트 팩 주입 시',
    'sim.outcome.hynix.note': 'LLM 분류기가 구조적 충격을 점수화; 최악 변동 {pct}%',
    'sim.outcome.dash': '—',
    'sim.frozen_attr': 'model_may_override = false',

    // ---- Security strip ----------------------------------------------
    'sec.title': '보안 아키텍처',
    'sec.1.title': '거래 전',
    'sec.1.body': '페이스 인증 없이는 시작 불가. Spec 필드 화이트리스트(extra="forbid"). 명목 금액 ≤ 1만. 최대 손실 ≤ 명목 금액. 만기 > 현재.',
    'sec.2.title': '추론 중',
    'sec.2.body': 'Kiln 출력은 JSON; 백엔드가 Pydantic으로 재검증합니다. 자유 텍스트 Spec 필드는 어디에도 전달되지 않습니다.',
    'sec.3.title': '거래 중',
    'sec.3.body': '페이퍼만 실행(venue="paper"). 코드 손실 하드 게이트: drawdown ≥ maxLoss이면 무조건 TRIP. RedLine은 별도 프로세스입니다.',
    'sec.4.title': '거래 후(감사)',
    'sec.4.body': '모든 RedLine 판정은 reason_codes + evidence + source가 담긴 구조화 JSON을 출력합니다. 제3자는 패스포트 + 로그만으로 재현할 수 있습니다.',
    'sec.5.title': 'AI가 할 수 없는 일',
    'sec.5.body': 'maxLoss 변경. RedLine 비활성화. 페이스 게이트 통과. PnL을 보고 TRIP "면제". 스키마 금지 필드 주입.',

    // ---- Live data panel ---------------------------------------------
    'live.title': '실시간 증거',
    'live.polled': '폴링 대상',
    'live.polled.every': '1.5초마다',
    'live.latest': '최신 패스포트',
    'live.no_passport': '아직 민팅된 패스포트가 없습니다. 데모를 열고 Spec을 잠그고 민팅하세요.',
    'live.id': 'ID',
    'live.spec_hash': 'Spec 해시',
    'live.mint_tx': '민팅 트랜잭션',
    'live.revoke_tx': '철회 트랜잭션',
    'live.status': '상태',
    'live.token_table': '토큰 / 에너지 표',
    'live.empty_table': '(아직 Kiln 호출 없음 — 데모를 열어 Spec을 실행하면 채워집니다)',
    'live.audit_count': '지금까지의 감사 이벤트:',
    'live.footer_note': '동일한 콘텐츠 제공 위치',
    'live.footer_note.tail': '. 제출 전 README §9에 붙여넣으세요.',

    // ---- Home page CTA -----------------------------------------------
    'home.cta': '데모 체험',
    'home.cta_sub': '3분 워크스루 · PRD §7',

    // ---- Demo view: ChatPanel ----------------------------------------
    'chat.empty': '카피 트레이딩 의도를 설명해 주세요. 예: "leader-demo-001을 500 USD로, 최대 손실 50, 48시간".',
    'chat.user_prefix': '사용자>',
    'chat.agent_prefix': 'Agent>',
    'chat.placeholder': '카피 트레이딩 의도를 입력하세요...',
    'chat.send': '전송',
    'chat.locked_note': 'Spec이 잠겼습니다.',

    // ---- Demo view: SpecCard -----------------------------------------
    'spec.title': 'Spec',
    'spec.locked': '잠김',
    'spec.empty': '아직 Spec이 없습니다. 채팅에서 메시지를 보내 필드를 채우세요.',
    'spec.leader': 'leader',
    'spec.notional': '명목 금액',
    'spec.maxloss': '최대 손실',
    'spec.expiry': '만기',
    'spec.venue': '거래 장소',
    'spec.paper': 'paper',
    'spec.lock_btn': 'Spec 잠그고 패스포트 민팅',
    'spec.locked_btn': 'Spec이 패스포트에 민팅됨',
    'spec.intent_hash': 'intent 해시',
    'spec.prepare_btn': '패스포트 준비',
    'spec.confirm_mint_btn': '확인 및 패스포트 민팅',
    'spec.authorized_btn': '패스포트 승인됨',
    'spec.working': '처리 중…',
    'spec.authorization_failed': '승인 실패',

    // ---- Demo view: PassportCard -------------------------------------
    'pass.title': '패스포트',
    'pass.empty': '아직 패스포트가 없습니다. 먼저 Spec을 잠그세요.',
    'pass.id': 'ID',
    'pass.spec_hash': 'Spec 해시',
    'pass.mint_tx': '민팅 트랜잭션',
    'pass.revoke_tx': '철회 트랜잭션',
    'pass.face': '페이스',
    'pass.face_verified': '인증됨',
    'pass.face_historical': '인증 기록 · 만료됨',
    'pass.face_not_verified': '미인증',
    'pass.verify_face': '페이스 인증',
    'pass.authorize_first': '먼저 위임 승인',
    'pass.face_ok': '페이스 확인됨',
    'pass.verified_at': '승인 시각',
    'pass.method': '승인 방식',
    'pass.session': '승인 세션',
    'pass.gate_status': '게이트 상태',
    'pass.gate_pending': '승인 대기',
    'pass.gate_active': '시작 가능',
    'pass.gate_consumed': '이번 실행에 사용됨',
    'pass.gate_invalidated': '무효화됨',
    'pass.gate_invalidated_help': '이 승인은 다른 실행에 사용할 수 없습니다. 새로운 고정 위임을 만들고 다시 승인하세요.',
    'pass.start_engine': '엔진 시작',
    'pass.engine_running': '엔진 실행 중',
    'pass.copy': '복사',
    'pass.copied': '복사됨',

    // ---- Human gate --------------------------------------------------
    'gate.title': '이 위임을 승인하세요',
    'gate.subtitle': '사람이 이 페이퍼 트레이딩 위임 내용을 직접 확인하고 지금 승인해야 실행할 수 있습니다.',
    'gate.close': '사용자 승인 닫기',
    'gate.preview': '로컬 카메라 미리보기',
    'gate.camera.idle': '카메라 미리보기를 시작할 준비 중입니다.',
    'gate.camera.requesting': '카메라 접근 권한을 요청하는 중…',
    'gate.camera.ready': '로컬 미리보기 준비됨',
    'gate.camera.denied': '카메라 접근이 거부되었습니다. 브라우저에서 카메라를 허용한 뒤 승인 화면을 다시 여세요.',
    'gate.camera.unsupported': '이 브라우저에서는 카메라를 사용할 수 없습니다. 최신 브라우저에서 위임을 승인하세요.',
    'gate.privacy': '미리보기는 이 브라우저 안에서만 처리됩니다. 이미지를 촬영·업로드·저장하거나 학습에 사용하지 않습니다.',
    'gate.mandate': '승인할 위임 내용',
    'gate.paper_only': '페이퍼 트레이딩 전용',
    'gate.consent': '본인이 직접 이 리더, 금액, 손실 한도, 만료 시각과 페이퍼 전용 실행을 승인합니다.',
    'gate.approve_start': '승인하고 페이퍼 실행 시작',
    'gate.approving': '승인을 기록하고 실행하는 중…',
    'gate.error.required': '승인이 기록되지 않았습니다. 위임 내용을 확인한 뒤 다시 시도하세요.',
    'gate.error.generic': '승인을 완료하지 못했습니다. 연결 상태를 확인하고 다시 시도하세요.',

    // ---- Inference evidence -----------------------------------------
    'evidence.title': '추론 워크로드 및 통제 증거',
    'evidence.subtitle': '이번 실행의 단계별 추론 수요를 승인 및 중지 타임라인과 함께 표시합니다.',
    'evidence.model': '모델',
    'evidence.mode': '출처',
    'evidence.power': '전력 가정',
    'evidence.flows': '단계별 토큰 및 에너지',
    'evidence.calls': '호출',
    'evidence.sessions': '활성 세션',
    'evidence.passports': '패스포트',
    'evidence.flow': '단계',
    'evidence.in': '입력 토큰',
    'evidence.out': '출력 토큰',
    'evidence.latency': '지연 시간',
    'evidence.energy': '에너지 추정',
    'evidence.source': '사용량 출처',
    'evidence.total': '합계',
    'evidence.assumption': '에너지는 180 W × API 지연 시간 ÷ 3600으로 추정합니다. 오프라인 값은 시뮬레이션 또는 추정치이며, 최종 라이브 증거에는 API가 보고한 사용량이 필요합니다.',
    'evidence.timeline': '승인 및 통제 타임라인',
    'evidence.timeline_empty': '데모를 실행하면 재현 가능한 승인 및 중지 타임라인이 생성됩니다.',
    'evidence.run': '실행 ID',

    // ---- Demo view: RedLinePanel -------------------------------------
    'red.title': 'RedLine',
    'red.running': '실행 중',
    'red.drawdown': '드로다운',
    'red.verdict': '판정',
    'red.inject_hynix': '하이닉스 주입',
    'red.trigger': 'RedLine 트리거',

    // ---- VerdictBadge ------------------------------------------------
    'verdict.no_verdict': '아직 판정 없음',
    'verdict.via': '경로',

    // ---- EventLog ----------------------------------------------------
    'events.title': '최근 이벤트',
    'events.empty': '이벤트 없음',

    // ---- DrawdownGauge -----------------------------------------------
    'gauge.drawdown': '드로다운',

    // ---- Demo: token strip -------------------------------------------
    'tokens.title': '토큰 / 에너지 리포트',
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
    if (next !== 'en' && next !== 'ko') return
    setLocaleState(next)
  }
  function toggle() {
    setLocaleState((cur) => (cur === 'en' ? 'ko' : 'en'))
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
  { code: 'ko', label: '한국어' },
]
