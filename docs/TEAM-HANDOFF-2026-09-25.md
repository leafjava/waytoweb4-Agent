# WayToWeb4 当前交接报告（2026-09-25）

## 1. 接手入口

- 上游仓库：<https://github.com/leafjava/waytoweb4-Agent>
- 工作分支：`codex/chain-and-evidence`
- PR：<https://github.com/leafjava/waytoweb4-Agent/compare/main...codex/chain-and-evidence?expand=1>
- 原则：队友仓库为主线；后续合并冲突优先保留队友的接口和业务决策，再移植本分支的安全控制、证据链与 UI。

```bash
git fetch origin
git switch codex/chain-and-evidence
git pull --ff-only
```

## 2. 当前产品行为

系统是一套可停止、可审计的 Paper 跟单授权流程：

1. 用户用自然语言描述 leader、金额、最大亏损和期限；
2. Agent 生成并锁定 Spec，后端重新校验全部约束；
3. 用户显式确认后创建 Strategy Passport；
4. 本地摄像头仅作现场预览，用户对本次委托执行一次性人工批准；
5. 只有已授权、Spec hash 匹配且通过本次人工门的 Passport 才能启动；
6. Paper worker 或 AlphaFox Paper transport 执行跟单；
7. RedLine、最大回撤、策略撤销、租约失败或人工停止会统一停机并撤销 Passport；
8. 旧的人脸门批准在启动或停止后失效，下次运行必须重新创建并批准委托。

Agent 无权扩大额度、修改最大亏损、绕过人工门、关闭 RedLine 或把 Paper 模式切成真钱模式。

## 3. 已完成模块

### 核心与安全

- `intent-keccak-v1` 冻结 Spec 与 hash-bound prepare → confirm → mint 生命周期。
- FastAPI 启动边界强制检查授权状态、Spec hash、人工门和 Paper-only 字段。
- 独立 Paper 子进程与控制器心跳；drawdown、expiry、policy、lease 均可硬停。
- 所有停止来源共用 stop-and-revoke 路径，避免只停 UI、不撤销授权。
- Human Gate 保存 `verifiedAt`、`method`、`sessionId`，批准只能使用一次。
- Kiln live/offline 显式分离；live 缺少凭据时 fail closed，不回退 mock。
- gpt-oss-120b 调用按 flow 保存 token、延迟、usage source 和 180W 能耗估算。
- 证据 verifier 会拒绝 mock token、伪造 hash、错误链、缺失回执和不完整停机日志。

### 外部执行和链上

- AlphaFox 官方 CLI 八项 catalog 操作已完成适配、dry-run 与 Paper 生命周期验证。
- 已完成隔离 Paper trader 的创建、启动、停止和服务端状态回读。
- 已完成授权的 Sepolia StrategyPassport v2 部署、mint、启动后 revoke 和独立 RPC readback。
- 未使用主网、个人真钱钱包或真实资金账户。

### 前端

- English / Korean 双语，语言选择持久化并同步 `<html lang>`。
- 保留 Chat → Spec → Passport → Human Gate → Engine → RedLine 全流程。
- 摄像头预览不上传、不存储、不做人脸识别。
- 当前首页采用冰蓝晶体安全风格：CloudFront 视频、玻璃导航、右侧控制摘要面板。
- 桌面标题已展开为两行；韩语使用独立字号和断行；Header 为左品牌、中状态、右 Demo CTA。
- Demo 中可查看两轮受控运行、token/energy 分流表和授权到停机时间线。

## 4. 已验证结果

最近完整验证：

```text
Python:   170 passed
Chain:    4 passed
Frontend: npm run build passed
Security: Python 与 frontend production dependency audit 为 0 个已知漏洞
```

前端本轮修改后再次执行 `npm run build` 和 `git diff --check`，均通过。没有通过删除失败测试或弱化断言获得通过。

## 5. 本地运行

项目根目录：

```powershell
.\.venv\Scripts\python.exe scripts\run_demo.py
```

或分别启动：

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
cd frontend
npm run dev
```

打开 <http://127.0.0.1:5173/>。默认状态应显示：

```text
Kiln: mock
Passport: mock
Execution: paper
```

这代表离线演示模式，不得将其截图或日志描述成真实 Kiln 或本轮公测网交易。

## 6. 三分钟演示顺序

1. 首页切换 English / Korean，进入 Demo；
2. 输入 `follow leader-demo-001 with 500 USD max loss 50 USD for 48 hours`；
3. 锁定 Spec 并确认创建 Passport；
4. 未通过人工门时直接启动，展示 `FACE_GATE_REQUIRED`；
5. 打开摄像头预览，勾选本次委托并批准；
6. 启动 Paper engine，展示批准时间、方法和 session；
7. 注入事件或触发 RedLine，展示 engine stop、Passport revoke 和 gate invalidated；
8. 展示 token/energy 分流表与事件时间线；
9. 换一项条件创建第二张 Passport，再次批准并运行，证明旧批准不能复用。

## 7. 真实证据边界

README 中记录的 Sepolia 交易来自已授权测试钱包现场运行：

- Deploy：`0xa61aafa30896d6abc9c4d16f1c5e87c2519d4fd043584df68074d9957fb4adea`
- Mint：`0xf482be1f0ee4bf233ed7ad48ef30020ff86713f296b661b5f3931a0b254e4839`
- Revoke：`0x77bb51bab499e98ff5d71cc2f13f4c5359f017d23fa7f4864380a5a1afecb64f`
- Contract：`0x818AF51261940013ba6c40aFa74937a3BFd1887D`

这些 hash 可以作为该次授权测试的证据，不得冒充未来重新运行产生的新交易。离线模式必须继续显示 null transaction hash 与 simulation ID。

## 8. 仍需完成的现场任务

1. 配置真实 Kiln API 凭据，以 `KILN_MODE=live` 调用 `gpt-oss-120b`；保存 API 返回的分 flow token usage。
2. 用 live verifier 检查 Kiln model、usage source、停机日志和链上证据，再更新 README token table。
3. 在实际演示电脑复验摄像头允许、拒绝、关闭释放和再次开闸。
4. 对 AlphaFox 演示参数作最后确认：Paper connector、leverage、停止时是否 `closePositions`。
5. 录制不超过三分钟的视频，突出“模型不能自己启动或扩大权限”。
6. 完成 Deck，并将 GitHub、视频、Deck 提交链接统一检查一遍。
7. PR 合并前先同步队友最新 main；冲突处理以队友实现为高优先级。

## 9. 不要提交的内容

- `.env`、Kiln key、钱包私钥、AlphaFox OAuth/session；
- `node_modules`、虚拟环境、浏览器缓存和本地临时证据；
- 未经 verifier 检查的现场日志；
- 把 mock、local-chain 或历史交易标记成本轮真实证据的文件。

更完整的阶段历史见 [`IMPLEMENTATION-STATUS.md`](IMPLEMENTATION-STATUS.md)，安全审计见 [`SECURITY-AUDIT-2026-09-25.md`](SECURITY-AUDIT-2026-09-25.md)。
