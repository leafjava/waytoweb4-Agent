# waytoweb4 Agent PRD

**Agent 开通跟单 · 策略护照上链 · RedLine 一票否决**  
GWDC 2026 Korea · FuriosaAI × Bricksum · Challenge A  
（RedLine 同时覆盖 Challenge B 的「可停、可审计」加分项）

版本：2026-09-22  
状态：可开工  
协作方：waytoweb4（执行层） / 参赛队（开通层、护照、熔断、Demo）

---

## 0. README 必须写死的一句话（官方验收）

> We built a **copy-trading authorization agent**: natural language produces a locked Spec, a human face-gate starts Paper copy-trading via waytoweb4, the Spec is minted as a revocable on-chain Strategy Passport, and a separate RedLine agent can halt the engine and burn the passport without looking at PnL.

评委按你声明的功能打分，不是按功能清单打分。这一句放 README 第一段。

---

## 1. 一句话产品

用户用自然语言配好并启动跟单（单策略，或两本护照的权重组合）→ 人脸开闸 → Spec 铸成链上策略护照 → 执行走 waytoweb4（不重写策略与下单）→ 收益再高，独立 RedLine 也可以熔断并撤销护照。

---

## 2. 为什么做（对齐官方 Brief + 韩国语境）

### 2.1 FuriosaAI × Bricksum Challenge A 原文要点

官方题目：Build a Financial Service Powered by AI Agents and Blockchain。

必须同时做到：

1. **用户需求与工作流**：说清服务谁、解决什么问题；从输入到结果跑通；标明哪一段是 Agent、哪一段是代码。
2. **Kiln API + 能效**：Agent 必须走 **NPU-based Kiln API，模型 `gpt-oss-120b`**。要有真实 API 调用，且调用结果影响决策。Token **按流程拆开报**，不能只报一个总数。功耗可用测量或**写清假设**（本次用 180W 估算即可，禁止真测芯片）。
3. **链**：devnet/testnet 端到端至少 **1 笔链上交易**（支付 / 结算 / 写记录），提交 **tx hash + 对应日志**。说清 Agent 读了什么、写了什么、结算了什么。
4. **声明功能**：README 一句话声明（见第 0 节）。
5. **条件对照实验**：同样流程跑两遍，改用户条件（额度变小、不允许的 Leader/商户、期限已过）。越权必须停下，并留下记录。

官方 Brief：  
https://docs.google.com/document/d/13qh7oePGl7Flrl-Zh_A6hfr02L266PvS/edit

### 2.2 为什么跟单能打中 A，RedLine 能顺便打中 B

- Challenge A 要的是「代办申购/支付/资产管理」的金融 Agent。跟单 = 资产管理委托。
- 韩国监管叙事：责任在人、必须能切断。原型只能 **Paper、可撤、可熔断**。
- Challenge B 要的是：边界在哪执行、被推出边界时必须停、第三人只看记录能复原「当时允不允许」。RedLine + 护照就是这件事。
- 组合用自然语言配权重，比网页配权重轻，适合 3 分钟 Demo。

### 2.3 GWDC 现场约束

| 项 | 内容 |
|---|---|
| 赛事 | GWDC Hackathon 2026 Korea |
| 地点 | aT Center, Seoul（Seocho, Gangnam-daero 27） |
| Kickoff | 9/28 17:00–20:00 KST |
| 编码 | 9/28 20:00 – 9/30 11:00 KST |
| 提交截止 | **9/30 12:00 KST** |
| Demo Day | 9/30 15:00–17:00 KST，Innovation Stage |
| 提交物 | 公开 GitHub、≤3 分钟 Demo 视频、项目材料、Pitch Deck |
| 奖池 | 全场 $100K+ USD（生态赛道另计） |
| 官网 | https://www.gwdc.net / https://wap.gwdc.net/hackathon.html |
| Luma | https://luma.com/be2le0l0 |
| TG | https://t.me/GWDC_Global |

3 分钟必须看见：**手续办完 + 链上能打开 + Kiln 调用发生过 + token 分流程**。

---

## 3. 系统结构

```
用户说话
  → Follow Agent（Kiln / gpt-oss-120b）出 Spec 或权重
  → 人脸开闸（人，不在模型）
  → waytoweb4 执行 Paper 跟单（start/stop）
  → Strategy Passport 上链（specHash, 可撤, 已核验）
  → RedLine Agent 独立判决 HOLD/WATCH/TRIP
       TRIP → stop 引擎 + revoke 护照
```

硬规则：

- 赚钱 Agent 和停钱 Agent **分开**。
- RedLine **不看收益率**。
- 自然语言只能配 Spec，**不能改限亏、不能关 RedLine**。
- 模型无权启动真/模拟盘；人脸后代码才调 `start`。

---

## 4. 对象模型

### 4.1 Spec（跟单意图，锁死）

| 字段 | 说明 | Demo 默认 |
|---|---|---|
| mode | 只允许普通跟单 | `copy` |
| leaderId | 可跟的 Leader | 现场确认的 waytoweb4 Leader |
| venue | 只 Paper | `paper` |
| notionalUsd | 额度 | `500` |
| maxLossUsd | 限亏 | `50` |
| expiry | 有效期 | 48h |
| faceVerified | 人脸已核 | `false`→`true` |
| paper | 固定 true | `true` |

禁止：新策略类型、网格自研、回测工厂。

### 4.2 Strategy Passport（链上授权单元）

```
passportId
specHash
author
leaderId
notionalUsd
feeBps
expiry
revocable = true
faceVerified
status = active | revoked
```

链的职责：存授权与状态，不跑行情。

### 4.3 Basket Passport（有余力再做）

```
[{ passportId, bps }] + basketMaxLossUsd
```

拼的是别人的许可，不发明行业因子。组合模板若 waytoweb4 未开放：两路普通跟单 + 链上 Basket。

### 4.4 RedLine 判决（结构化，训练队友从这里接）

只允许：

```json
{
  "level": "HOLD | WATCH | TRIP",
  "reason_codes": ["DD_LIMIT"],
  "evidence": ["drawdownUsd=50"],
  "action": "none | tighten | stop_and_revoke",
  "model_may_override_hard_limit": false
}
```

原因码：

| code | 含义 |
|---|---|
| DD_LIMIT | 回撤打到 Spec.限亏 → **规则强制 TRIP**，模型无权放行 |
| CB_LIKE | 熔断级指数/板块冲击（海力士/KOSPI 风格） |
| LEV_ETF_AMP | 2x/杠杆产品放大 |
| LIQ_CASCADE | 清算踩踏 |
| GAP_ORACLE | 薄流动性/盘前异常价 |
| HUMAN_OVERRIDE | 人脸/人工一票否决 |

规则优先：

```
if drawdown >= spec.maxLossUsd → TRIP
else model 只对「是不是结构冲击」打分
if TRIP → waytoweb4.stop + passport.revoke
```

---

## 5. 官方验收映射（按这个做就不会跑偏）

| 官方条款 | 我们怎么交 |
|---|---|
| User Need | 散户/评委：想用自然语言委托跟单，但怕 Agent 代客后无法切断 |
| Agent vs Code | Agent：澄清 + 出 Spec + RedLine 分类。Code：校验 Spec、人脸、start/stop、铸/烧护照、限亏硬闸 |
| Kiln `gpt-oss-120b` | Follow 多轮澄清、RedLine 事件分类，必须打到真 API |
| Token 分流程 | 见 §9：clarify / spec / redline_hold / redline_trip / demo_inject |
| 能耗 | `energyWh ≈ tokens × 180W × latencySec / 3600`，假设写进 README |
| 链上至少 1 tx | mint Passport；TRIP 时再发 revoke tx。提交 hash |
| 条件对照跑两遍 | Run1：500U / 亏50停。Run2：额度改 100U 或注入海力士熔断包。两次都有日志 |
| 越权即停 | 限亏击穿、禁止 Leader、过期、RedLine 注入事件 → stop 并记录 |
| 第三人可审计 | 只凭护照 + 日志能回答：跟谁、额度、是否人脸、为何停 |

Challenge B 加分（不必改赛道，但 Demo 讲出来）：

- 边界写在哪：Spec 硬编码 + 合约 status + RedLine
- 被推出边界的两次 run
- 另一人只看记录能复原

---

## 6. 48 小时范围

### 必做（没有就不要上台）

- [ ] 对话产出一套合法 Spec
- [ ] 人脸后才 `start`
- [ ] 铸 **一本** Strategy Passport，浏览器能打开
- [ ] waytoweb4 模拟盘运行中
- [ ] RedLine 能停并 `revoke`
- [ ] Kiln 真调用 + 分流程 token 表
- [ ] 两次条件对照 + 日志
- [ ] README 一句话功能声明 + tx hash

### 有余力

- [ ] 两本护照 + 权重
- [ ] 第二地址凭护照跟
- [ ] 确认卡显示本单 token
- [ ] 「一键海力士」事件注入按钮

### 明确不做

新策略类型、回测工厂、K 线、币安真 KYC、花费总账、真测芯片功耗、战争模型、分账商城、让模型看收益率放行。

---

## 7. Demo 脚本（3 分钟）

1. 「跟这条、500 U、模拟盘、亏 50 停」  
2. 配置卡（Spec 可视化）  
3. 人脸 → 状态「运行中」  
4. 打开护照（tx hash）  
5. 可选：组合 / 第二地址  
6. 点 RedLine 或注入海力士包 → 停 + revoked  
7. 收尾 15 秒：token 分流程表 + 「接口可换 Furiosa / Kiln 卡」+ 180W 估算

对照实验（视频里剪 20 秒）：把额度改成 100 或限亏改成 10，再跑一遍，展示提前停。

---

## 8. 海力士黑天鹅（评委追问稿，不是要做交易策略）

2026 年夏：海力士 + 三星约占 KOSPI 一半，个股 2 倍 ETF 日再平衡放大波动。正股可单日 -10%～-15%，2x ETF 更深，指数约 -8% 触发全市熔断。基本面可以仍强，仓位先爆。

评委问：「策略对了也会爆，谁切断？」

答法：

- 策略 Agent 可以继续看多。
- RedLine 不看赚了多少。
- 限亏先于强平。
- 护照可撤、人脸闸、独立熔断。
- Demo 用模拟事件包，不赌现场真行情。

---

## 9. Kiln / Token / 功耗（上场必带表）

模型：`gpt-oss-120b` via Kiln。  
禁止把 Follow 和 RedLine 打成一次超长推理。

| flow | 何时 | 预期 |
|---|---|---|
| `clarify` | 缺 Leader/额度/限亏 | 1–2 轮 |
| `spec_emit` | 产出 JSON Spec | 1 次 |
| `redline_hold` | 心跳/常规摘要 | 短 |
| `redline_trip` | 限亏或事件包 | 短，结构化 JSON |
| `demo_inject` | 一键海力士 | 1 次 |

README 模板：

```
flow          tokens_in  tokens_out  latency_s  energy_Wh_est
clarify       ...
spec_emit     ...
redline_trip  ...
total         ...
assumption    180W NPU-class, energy = 180 * latency / 3600
```

省 token：规则先判限亏；模型只看文本事件；Spec 用 schema，禁止自由散文。

---

## 10. 接口分工

### 参赛队

对话、Spec schema、人脸闸、护照 mint/revoke、RedLine、Kiln 封装、Demo、token 表。

### waytoweb4（需书面确认）

- 可跟 Leader 列表  
- 创建 Paper 跟单  
- `start` / `stop`  
- 组合模板：若无，用两路 copy + 链上 Basket  

卡点兜底：评委只要求「授权与记录在链上、执行有 start/stop」。执行失败时用 mock 引擎 + 真实护照交易，README 写清哪些是 waytoweb4、哪些是 mock。不要卡死在对方 API。

### 模型队友（LLaMA 方向，不碰链）

今日即可：

1. `redline_schema.md`（上表 JSON）  
2. 30–50 条海力士风格评测集  
3. 规则 + LLM 混合：限亏硬闸，模型只打结构冲击  
4. 一键事件包 → 必须 TRIP  

不要让他做护照、钱包、回测。

---

## 11. 建议仓库结构

```
README.md                 # 一句话功能 + tx hash + token 表 + 180W 假设
prd.md                    # 本文件
apps/web/                 # 对话、配置卡、人脸、护照链接、RedLine 按钮
apps/follow-agent/        # Kiln clarify + spec_emit
apps/redline-agent/       # schema + 规则闸 + 事件注入
apps/passport/            # mint / revoke / specHash
apps/waytoweb4-adapter/   # start/stop/paper
docs/security-arch.md     # 产品架构 + 安全性架构（评委/合作方会要）
docs/eval/hynix-cases.json
```

链选 **便宜 testnet**（与 Kiln/现场网无关）。目标是稳定出 hash，不是选对的主网叙事。

---

## 12. 安全性架构（最小可讲）

1. **交易前**：无人脸不得 start；Spec 字段白名单。  
2. **调用中**：Kiln 只出 JSON，后端校验；无校验不调 waytoweb4。  
3. **交易中**：Paper only；限亏代码硬闸；RedLine 独立进程。  
4. **事后**：护照 + 日志可被第三人复原。  
5. **AI 不能做的事**：改 maxLoss、关 RedLine、自己开闸、看 PnL 豁免。

---

## 13. 路线（对 Furiosa 评委说的三句）

- 短期芯片（本次）：金融 Agent 负载 + 护照；180W 估算。  
- 中期能源：多用户 24/7，比 users/kW。  
- 长期存储：护照成为配置/授权/成绩哈希单元；分账上架不做。

---

## 14. 开工顺序（今天就按这个排）

1. Spec JSON schema + 校验器  
2. Kiln Hello：`gpt-oss-120b` 产出合法 Spec  
3. 人脸开关（可先 mock 通过）+ start/stop  
4. Passport mint，记下 hash  
5. 限亏硬闸  
6. RedLine JSON + 海力士注入 → revoke  
7. 两次对照日志  
8. token 表写进 README  
9. 3 分钟录屏  

先闭环再加 Basket。

---

## 15. 注意事项（避免现场被刷）

1. 不接 Kiln / 不用 `gpt-oss-120b` = Challenge A 硬伤。  
2. 只有 PPT 没有 tx hash = 链条款失败。  
3. token 只报一个总数 = 能效条款失败。  
4. 改条件后 Agent 仍下单 = 控制条款失败。  
5. Demo 超时：删组合、删第二地址，保「配 → 闸 → 护照 → 烧」。  
6. 真盘、真 KYC、真功耗测试一律不做。  
7. 提交截止 **9/30 12:00 KST**，Demo 15:00 开始，预留上传和网。  
8. 官方 Q&A：https://t.me/GWDC_Global/392/742  

---

## 16. 协作方 / 导师一页纸

策略可以错，黑天鹅可以来。  
评委要看的是：自然语言能配完、人脸才能开、链上能打开授权、RedLine 能停并能烧护照。  
执行外包 waytoweb4，责任留在人和规则，不留在模型。
