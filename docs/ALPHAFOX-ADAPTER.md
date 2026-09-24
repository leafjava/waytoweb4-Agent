# AlphaFox Paper execution adapter

Status: **official catalog verified on 2026-09-24; live mutations disabled by default**.

The adapter uses AlphaFox CLI `0.3.24`, contract `2026-08-31`, and OAuth
credentials held by the operating-system keychain. Tokens, browser cookies and
wallet credentials never enter this repository or the execution DTO.

## Demo operation allowlist

1. `trading.signal_sources.list`
2. `trading.strategy_definitions.list`
3. `trading.strategy_definitions.byId.get`
4. `trading.strategy_definitions.byId.validate_config`
5. `trading.traders.list`
6. `trading.traders.create`
7. `trading.traders.byId.start`
8. `trading.traders.byId.stop`

The verified copy definition is `simple_copy_trading`, schema version `4`.
`notional_cents` maps to `config.strategy.fixedEquity`, which the official
schema describes as a fixed capital amount. The mandate expiry maps to the
leader subscription `exitTime`. The local worker remains responsible for the
absolute `max_loss_cents` hard stop because AlphaFox's similarly named leader
drawdown setting has different semantics.

Every mutation runs through `--dry-run` before `--yes`. Create uses
`autoStart: true` only after the existing hash confirmation and human gate.
Stop requires an explicit `ALPHAFOX_STOP_CLOSE_POSITIONS=true|false`; the code
does not silently choose whether to flatten Paper positions.

## Required field configuration

```powershell
$env:EXECUTION_BACKEND = 'alphafox'
$env:ALPHAFOX_PAPER_CONNECTOR_ID = '<active paper connector id>'
$env:ALPHAFOX_LEVERAGE = '1'
$env:ALPHAFOX_STOP_CLOSE_POSITIONS = 'true'
alphafox auth status --verify --format json --no-input
```

Do not commit these values. Before a live demo, select an allowed signal source
from the catalog, review every effective strategy parameter, then run the
field preflight. A live create/start/stop still needs the operator's final
parameter approval.
