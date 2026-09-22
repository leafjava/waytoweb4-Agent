import test from "node:test";
import assert from "node:assert/strict";
import { createLocalRuntime } from "../src/runtime.mjs";
import { keccak256, toUtf8Bytes } from "ethers";
import fs from "node:fs";
import path from "node:path";
import { validateCanonicalIntent } from "../src/intent.mjs";

test("golden intent fixture matches the independent Node implementation", () => {
  const fixture = JSON.parse(fs.readFileSync(path.join(import.meta.dirname, "../../fixtures/intent-v1.json"), "utf8"));
  assert.equal(validateCanonicalIntent(fixture.canonical).hash, fixture.hash);
});

test("local EVM mint, readback and revoke", async (t) => {
  const runtime = await createLocalRuntime();
  t.after(() => runtime.close());
  const canonical = '{"expiryUnix":"4070908800","leaderId":"leader-demo-001","maxLossCents":"5000","mode":"copy","notionalCents":"50000","paper":true,"venue":"paper","version":"intent-keccak-v1"}';
  const hash = keccak256(toUtf8Bytes(canonical));
  const mint = await runtime.handle({ op: "mint", payload: { canonical_intent: canonical, spec_hash: hash, confirmed_spec_hash: hash } });
  assert.equal(mint.receipt.status, 1); assert.equal(mint.state.notional_cents, "50000"); assert.equal(mint.state.max_loss_cents, "5000");
  const revoked = await runtime.handle({ op: "revoke", payload: { chain_passport_id: mint.chain_passport_id, reason_code: "TEST" } });
  assert.equal(revoked.state.status, "revoked");
});
