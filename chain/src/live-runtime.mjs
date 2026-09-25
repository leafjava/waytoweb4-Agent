import fs from "node:fs";
import path from "node:path";
import {
  Contract,
  ContractFactory,
  FetchRequest,
  JsonRpcProvider,
  Wallet,
  getAddress,
} from "ethers";

import { validateCanonicalIntent } from "./intent.mjs";
import { compileContract } from "./contract.mjs";

const PUBLIC_TESTNETS = new Set([1001, 11155111]);

export function readLiveConfig(env = process.env) {
  const rpcUrl = env.RPC_URL || "";
  const privateKey = env.PRIVATE_KEY || "";
  const chainId = Number(env.CHAIN_ID || 0);
  const txTimeoutMs = Number(env.TX_TIMEOUT_MS || 60000);
  if (!rpcUrl || !privateKey || !chainId) throw Error("LIVE_CHAIN_CONFIG_MISSING");
  const parsed = new URL(rpcUrl);
  if (parsed.protocol !== "https:") throw Error("LIVE_CHAIN_HTTPS_REQUIRED");
  if (!/^0x[0-9a-fA-F]{64}$/.test(privateKey)) throw Error("LIVE_CHAIN_PRIVATE_KEY_INVALID");
  if (!PUBLIC_TESTNETS.has(chainId)) throw Error("PUBLIC_TESTNET_REQUIRED");
  if (!Number.isFinite(txTimeoutMs) || txTimeoutMs < 1000 || txTimeoutMs > 120000) throw Error("TX_TIMEOUT_INVALID");
  const contractAddress = env.PASSPORT_ADDRESS ? getAddress(env.PASSPORT_ADDRESS) : null;
  return Object.freeze({
    rpcUrl,
    privateKey,
    chainId,
    txTimeoutMs,
    contractAddress,
    journalDir: path.resolve(env.CHAIN_JOURNAL_DIR || "var/live-journal"),
  });
}

function appendJournal(config, runId, value) {
  fs.mkdirSync(config.journalDir, { recursive: true });
  const safeRunId = String(runId).replace(/[^A-Za-z0-9_-]/g, "_");
  fs.appendFileSync(
    path.join(config.journalDir, `${safeRunId}.jsonl`),
    JSON.stringify({ at: new Date().toISOString(), run_id: runId, ...value }) + "\n",
    "utf8",
  );
}

export async function createLiveRuntime(env = process.env) {
  const config = readLiveConfig(env);
  const request = new FetchRequest(config.rpcUrl);
  request.timeout = config.txTimeoutMs;
  const provider = new JsonRpcProvider(request, undefined, { cacheTimeout: -1 });
  const wallet = new Wallet(config.privateKey, provider);
  const network = await provider.getNetwork();
  if (Number(network.chainId) !== config.chainId) throw Error("RPC_CHAIN_ID_MISMATCH");
  if ((await provider.getBalance(wallet.address)) <= 0n) throw Error("TESTNET_GAS_REQUIRED");

  const artifact = compileContract();
  let address = config.contractAddress;
  let contract = address ? new Contract(address, artifact.abi, wallet) : null;
  if (contract && (await contract.VERSION()) !== "2-cents") throw Error("WRONG_PASSPORT_CONTRACT");

  async function feeOverrides() {
    const fee = await provider.getFeeData();
    const gasPrice = (fee.maxFeePerGas ?? fee.gasPrice ?? 1000000000n) * 2n;
    return { type: 0, gasPrice: gasPrice < 2000000000n ? 2000000000n : gasPrice };
  }

  async function waitFor(tx, runId, action, extra = {}) {
    const submitted = {
      action: `${action}_submitted`,
      status: "submitted",
      tx_hash: tx.hash,
      nonce: tx.nonce,
      chain_id: config.chainId,
      contract_address: address,
      from: wallet.address,
      ...extra,
    };
    appendJournal(config, runId, submitted);
    const receipt = await tx.wait(1, config.txTimeoutMs);
    if (!receipt || Number(receipt.status) !== 1) throw Error("TRANSACTION_NOT_CONFIRMED");
    const confirmed = {
      ...submitted,
      action: `${action}_confirmed`,
      status: "confirmed",
      receipt: {
        status: Number(receipt.status),
        block_number: receipt.blockNumber,
        block_hash: receipt.blockHash,
      },
    };
    appendJournal(config, runId, confirmed);
    return { receipt, confirmed };
  }

  async function ensureContract(runId) {
    if (contract) return;
    const factory = new ContractFactory(artifact.abi, artifact.bytecode, wallet);
    const deployed = await factory.deploy(await feeOverrides());
    address = await deployed.getAddress();
    const deployment = deployed.deploymentTransaction();
    await waitFor(deployment, runId, "deploy", { contract_address: address });
    contract = deployed;
  }

  async function inspect(id) {
    if (!contract) throw Error("PASSPORT_CONTRACT_UNAVAILABLE");
    const passport = await contract.passports(BigInt(id));
    return {
      author: passport.author,
      spec_hash: passport.specHash.toLowerCase(),
      leader_id: passport.leaderId,
      notional_cents: passport.notionalCents.toString(),
      max_loss_cents: passport.maxLossCents.toString(),
      expiry_unix: passport.expiry.toString(),
      human_confirmed: passport.humanConfirmed,
      status: Number(passport.status) === 0 ? "active" : "revoked",
    };
  }

  return {
    async handle(requestEnvelope) {
      const { op, payload = {}, run_id: runId } = requestEnvelope;
      if (op === "health") return { status: "confirmed", chain_id: config.chainId, contract_address: address };
      if (op === "mint") {
        const parsed = validateCanonicalIntent(payload.canonical_intent);
        if (parsed.hash.toLowerCase() !== payload.spec_hash?.toLowerCase() || payload.confirmed_spec_hash?.toLowerCase() !== payload.spec_hash?.toLowerCase()) throw Error("HASH_MISMATCH");
        await ensureContract(runId);
        const tx = await contract.mint(
          parsed.hash,
          parsed.value.leaderId,
          parsed.notional,
          parsed.loss,
          parsed.expiry,
          true,
          await feeOverrides(),
        );
        const { receipt, confirmed } = await waitFor(tx, runId, "mint", { spec_hash: parsed.hash, contract_address: address });
        const event = receipt.logs
          .map((log) => { try { return contract.interface.parseLog(log); } catch { return null; } })
          .find((item) => item?.name === "PassportMinted");
        if (!event) throw Error("MINT_EVENT_MISSING");
        const id = event.args.id.toString();
        const state = await inspect(id);
        if (
          state.author.toLowerCase() !== wallet.address.toLowerCase()
          || state.spec_hash !== parsed.hash.toLowerCase()
          || state.leader_id !== parsed.value.leaderId
          || state.notional_cents !== parsed.notional.toString()
          || state.max_loss_cents !== parsed.loss.toString()
          || state.expiry_unix !== parsed.expiry.toString()
          || state.human_confirmed !== true
          || state.status !== "active"
        ) throw Error("MINT_READBACK_MISMATCH");
        return { ...confirmed, chain_passport_id: id, chain_id: config.chainId, contract_address: address, state };
      }
      if (op === "inspect" || op === "reconcile") {
        if (!contract) throw Error("PASSPORT_ADDRESS_REQUIRED");
        return { status: "confirmed", chain_passport_id: String(payload.chain_passport_id), state: await inspect(payload.chain_passport_id), chain_id: config.chainId, contract_address: address };
      }
      if (op === "revoke") {
        if (!contract) throw Error("PASSPORT_ADDRESS_REQUIRED");
        const before = await inspect(payload.chain_passport_id);
        if (before.author.toLowerCase() !== wallet.address.toLowerCase()) throw Error("PASSPORT_AUTHOR_MISMATCH");
        if (before.status === "revoked") return { status: "confirmed", already_revoked: true, chain_passport_id: String(payload.chain_passport_id), chain_id: config.chainId, contract_address: address, state: before };
        const tx = await contract.revoke(BigInt(payload.chain_passport_id), payload.reason_code || "STOP_REQUESTED", await feeOverrides());
        const { confirmed } = await waitFor(tx, runId, "revoke", { chain_passport_id: String(payload.chain_passport_id), contract_address: address, reason_code: payload.reason_code || "STOP_REQUESTED" });
        const state = await inspect(payload.chain_passport_id);
        if (state.status !== "revoked") throw Error("REVOKE_READBACK_MISMATCH");
        return { ...confirmed, chain_passport_id: String(payload.chain_passport_id), chain_id: config.chainId, contract_address: address, state };
      }
      throw Error("UNKNOWN_OPERATION");
    },
    close: async () => provider.destroy(),
  };
}
