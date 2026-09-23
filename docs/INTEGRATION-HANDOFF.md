# Integration handoff

Base: teammate `master` at `fdb3c8a`; integration branch
`codex/chain-and-evidence`. The branch was checked again on 2026-09-23 and was
not behind the teammate mainline.

## Implemented milestones

The branch preserves the teammate repository as the product baseline and moves
donor functionality by module. The current commit sequence after the teammate
base covers:

1. hash-bound prepare → confirm → mint authorization;
2. isolated local/public-testnet EVM worker and StrategyPassport v2;
3. credential-free paper worker with fail-closed stops;
4. explicit live/offline Kiln modes and per-run evidence verification;
5. frontend authorization flow and independent two-round rehearsal;
6. centralized stop/revoke, restart recovery and guarded testnet transport;
7. replaceable waytoweb4 execution DTO pending official endpoint mapping;
8. English/Korean UI (`23eb4f3`);
9. per-mandate human-gate evidence (`6e0d4d3`);
10. local camera-preview approval UI (`612418c`);
11. terminal gate invalidation (`64beab0`); and
12. Furiosa inference/governance evidence panel (`d784f63`).

The detailed phase history is in `docs/IMPLEMENTATION-STATUS.md`; the remaining
execution order is in `docs/FURIOSA-DEMO-NEXT-PLAN.md`.

## Current offline verification

- Combined Python suite: 136 passed.
- Node chain suite: 4 passed. Ganache uses its JavaScript µWS fallback on the
  installed Node build.
- Frontend production build: passed.
- English/Korean catalogs: 185 keys each, no missing counterpart.
- Independent round A and round B rehearsal: passed with distinct passport,
  run and human-gate session IDs.
- Both offline evidence directories: verifier passed.

No failed test was removed or weakened to obtain these results.

## External work still required

### Official waytoweb4 adapter

The internal start DTO is frozen, but the teammate's official endpoint
documentation is still required. Do not guess endpoint paths, authentication,
idempotency or stop semantics. Once supplied, map the documented API to
`backend/app/execution_contract.py` and preserve the current paper-only,
hash-bound authorization boundary.

### Field acceptance

Run these once with authorized credentials and retain only fresh evidence:

1. Start with `KILN_MODE=live` and confirm a real `gpt-oss-120b` response with
   API-reported token usage.
2. Run the same workflow again after changing one policy condition; confirm
   execution stops and the log records the reason.
3. Broadcast at least one authorized Kairos or Sepolia passport transaction and
   retain its hash, successful receipt and contract readback.
4. Test the camera gate with a physical browser: denial must block start;
   approval must show time/method/session; closing must release the camera.
5. Run the live evidence verifier, then update the README token table and
   transaction table.
6. Record the three-minute English/Korean video and finalize the Deck.

Do not use offline estimates, mock records, local-chain hashes or historical
transactions as live evidence. Do not copy `.env`, private keys, `node_modules`
or generated evidence into the submission.
