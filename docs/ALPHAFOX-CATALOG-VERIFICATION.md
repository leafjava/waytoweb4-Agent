# AlphaFox catalog verification

Verified on 2026-09-24 against production with AlphaFox CLI `0.3.24`, contract
and catalog `2026-08-31`. OAuth remained in Windows Credential Manager. Raw
responses are kept only under the ignored local `artifacts/alphafox-contract/`
directory.

## Eight-operation demo surface

| # | operationId | Verification | Result |
|---|---|---|---|
| 1 | `trading.signal_sources.list` | live read | pass; 394 sources |
| 2 | `trading.strategy_definitions.list` | live read | pass; 21 active definitions |
| 3 | `trading.strategy_definitions.byId.get` | live read | pass; `simple_copy_trading`, schema v4 |
| 4 | `trading.strategy_definitions.byId.validate_config` | live server validation | pass |
| 5 | `trading.traders.list` | live read | pass; two existing Paper traders observed |
| 6 | `trading.traders.create` | dry-run + isolated Paper execution | pass; trader created after human gate |
| 7 | `trading.traders.byId.start` | create with `autoStart: true` | pass; runtime became active |
| 8 | `trading.traders.byId.stop` | dry-run + isolated Paper execution | pass; runtime read back as stopped |

A dedicated internal Paper connector was created for WayToWeb4; the two
pre-existing teammate connectors and traders were not modified. The final
application-level rehearsal created and auto-started trader
`01a0d35b-d3ab-7a1c-adb0-1dc34c393cac` only after hash authorization and a
fresh human approval. The application then stopped it with
`closePositions: true`. AlphaFox readback reported `enabled: false`,
`desiredState: disabled`, and `runtime.state: stopped`.

The pre-gate start attempt failed with `FACE_GATE_REQUIRED`. Local Passport
state ended `revoked` with `external_execution_status: stopped`. Passport
transactions remained null because this rehearsal deliberately used the mock
Passport backend and did not broadcast a public-chain transaction.

## Validated Demo proposal

| JSON path / setting | Proposed value | Source |
|---|---|---|
| `strategyDefinitionId` | `simple_copy_trading` | verified catalog definition |
| `configSchemaVersion` | `4` | definition contract |
| `exchangeConnectorId` | dedicated internal Paper connector | created for this rehearsal; pre-existing connectors untouched |
| `config.common.execution.leverage` | `1` | WayToWeb4 conservative override |
| `config.common.execution.openMinPosition` | `false` | skip orders below venue minimum |
| `config.common.riskControl` | `{}` | optional AlphaFox controls omitted; local RedLine remains authoritative |
| `config.common.orderExecution` | `{}` | optional price buffer omitted |
| `config.strategy.fixedEquity` | `500` USD | frozen Demo mandate |
| `config.strategy.followSignalLeverage` | `false` | use configured leverage |
| `config.strategy.positionFollowMode` | `proportional` | schema enum/default |
| `config.strategy.signalSourceConfigs[0].signalSourceId` | selected active catalog source | catalog read; must be reconfirmed for field run |
| `config.strategy.signalSourceConfigs[0].marginPercent` | `100` | full proportional copy ratio |
| `config.strategy.signalSourceConfigs[0].followSide` | `BOTH` | schema enum |
| `config.strategy.signalSourceConfigs[0].exitTime` | frozen mandate expiry | WayToWeb4 Spec |
| source start time, leader drawdown and symbol filters | omitted | optional; no implicit value claimed |
| `config.strategy.syncPositionsOnTrade` | `true` | synchronize target position on leader events |
| `config.strategy.useAmountPercent` | `false` | keep margin-proportional sizing |
| top-level symbol filters | omitted | optional |
| `shareParameters` | `false` | Demo privacy choice |
| `autoStart` | `true` | create only after hash authorization and human gate |
| stop `closePositions` | `true` | field proposal; flatten Paper positions on stop |

The frozen 50 USD absolute loss limit is enforced by the local RedLine worker.
It is not mapped to AlphaFox's leader-drawdown percentage because the two fields
have different meanings.

## Field result

The mutation gate was exercised through `scripts/alphafox_paper_rehearsal.py`.
It retained the WayToWeb4 hash authorization and one-use human gate, used the
reviewed configuration above, performed official CLI dry-runs before writes,
and saved only sanitized IDs and state. OAuth credentials remained in Windows
Credential Manager.

Trader inspection:
`https://www.alphafox.app/zh/dashboard/traders/01a0d35b-d3ab-7a1c-adb0-1dc34c393cac`.
