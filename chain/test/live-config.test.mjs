import test from "node:test";
import assert from "node:assert/strict";

import { readLiveConfig } from "../src/live-runtime.mjs";

const valid = {
  RPC_URL: "https://rpc.example.invalid",
  PRIVATE_KEY: "0x" + "11".repeat(32),
  CHAIN_ID: "11155111",
  TX_TIMEOUT_MS: "60000",
};

test("live chain config accepts public testnets without making a request", () => {
  const config = readLiveConfig(valid);
  assert.equal(config.chainId, 11155111);
  assert.equal(config.rpcUrl, valid.RPC_URL);
});

test("live chain config rejects missing credentials, mainnet and insecure RPC", () => {
  assert.throws(() => readLiveConfig({}), /MISSING/);
  assert.throws(() => readLiveConfig({ ...valid, CHAIN_ID: "1" }), /PUBLIC_TESTNET_REQUIRED/);
  assert.throws(() => readLiveConfig({ ...valid, RPC_URL: "http://rpc.example.invalid" }), /HTTPS_REQUIRED/);
  assert.throws(() => readLiveConfig({ ...valid, PRIVATE_KEY: "test" }), /PRIVATE_KEY_INVALID/);
});
