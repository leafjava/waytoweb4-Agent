# Integration handoff

Base: teammate `fd8af21b2512c0f91de5e5aecd2cf406f6094299`; branch `codex/chain-and-evidence`.

Commits, in order:

1. `31e6dc4` — clean editable Python baseline and frontend build baseline.
2. `3aa9c3f` — intent-keccak-v1, UUID records, prepare/confirm/mint lifecycle and atomic state.
3. `102e6be` — isolated Node chain worker, StrategyPassport v2, local-EVM bridge and golden fixture.
4. `8af80ad` — independent paper worker, heartbeat/lease and fail-closed automatic stops.
5. `cb08dab` — explicit Kiln modes, strict classifier contract and per-run evidence verifier.
6. `794109d` — ignore generated evidence runs.

Current offline verification: Python combined suite 118 passed; Node chain suite 2 passed; frontend build passed; two-round offline rehearsal passed. µWS fallback is expected on this Node build. npm reports transitive dependency advisories; no forced upgrade was applied.

Field-only items remain: obtain the authorized Kiln developer pack and use the exact endpoint/key with `KILN_MODE=live`, perform at least one public testnet mint and revoke, preserve confirmed hashes and receipts, run the same frozen intent after a policy change, and update README/video/Deck with those fresh records. No public transaction or real Kiln call is claimed by this handoff.

Rollback is local and reversible: check out the teammate base commit or remove the integration branch. Do not copy `.env`, keys, `node_modules`, generated evidence, or historical chain records into a submission.
