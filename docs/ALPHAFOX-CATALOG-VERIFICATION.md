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
| 6 | `trading.traders.create` | official CLI `--dry-run` | pass; high-risk write not sent |
| 7 | `trading.traders.byId.start` | official CLI `--dry-run` | pass; high-risk write not sent |
| 8 | `trading.traders.byId.stop` | official CLI `--dry-run` | pass; high-risk write not sent |

No trader was created, started or stopped by this verification. The current
account has two active Paper connectors and both are occupied by existing
traders, so a new isolated create cannot be executed until a separate Paper
connector is available. Existing traders are not reused or modified as test
fixtures.

## Validated Demo proposal

| JSON path / setting | Proposed value | Source |
|---|---|---|
| `strategyDefinitionId` | `simple_copy_trading` | verified catalog definition |
| `configSchemaVersion` | `4` | definition contract |
| `exchangeConnectorId` | unresolved dedicated Paper connector | required; both current connectors occupied |
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

## Mutation gate

The final field mutation requires all of the following:

1. a dedicated, unoccupied Paper connector;
2. confirmation of the selected signal source and the full table above;
3. the existing WayToWeb4 hash authorization and per-run human gate;
4. create/start/stop dry-run immediately before `--yes`;
5. saved trader ID and readback without exposing OAuth credentials.

