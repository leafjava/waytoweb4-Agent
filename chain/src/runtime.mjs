import fs from "node:fs";
import path from "node:path";
import ganache from "ganache";
import solc from "solc";
import { BrowserProvider, ContractFactory } from "ethers";
import { validateCanonicalIntent } from "./intent.mjs";

function compile() {
  const source = fs.readFileSync(path.join(import.meta.dirname, "../contracts/StrategyPassport.sol"), "utf8");
  const input = { language: "Solidity", sources: { "StrategyPassport.sol": { content: source } }, settings: { evmVersion: "paris", optimizer: { enabled: true, runs: 200 }, outputSelection: { "*": { "*": ["abi", "evm.bytecode.object"] } } } };
  const out = JSON.parse(solc.compile(JSON.stringify(input)));
  const errors = (out.errors || []).filter((x) => x.severity === "error");
  if (errors.length) throw Error(errors.map((x) => x.formattedMessage).join("\n"));
  const c = out.contracts["StrategyPassport.sol"].StrategyPassport;
  return { abi: c.abi, bytecode: `0x${c.evm.bytecode.object}` };
}

export async function createLocalRuntime() {
  const eip1193 = ganache.provider({ logging: { quiet: true }, chain: { chainId: 1337 }, wallet: { totalAccounts: 2 } });
  const provider = new BrowserProvider(eip1193);
  const signer = await provider.getSigner();
  const artifact = compile();
  const contract = await new ContractFactory(artifact.abi, artifact.bytecode, signer).deploy();
  await contract.waitForDeployment();
  const address = await contract.getAddress();
  async function inspect(id) {
    const p = await contract.passports(BigInt(id));
    return { author: p.author, spec_hash: p.specHash.toLowerCase(), leader_id: p.leaderId, notional_cents: p.notionalCents.toString(), max_loss_cents: p.maxLossCents.toString(), expiry_unix: p.expiry.toString(), human_confirmed: p.humanConfirmed, status: Number(p.status) === 0 ? "active" : "revoked" };
  }
  return {
    chainId: 1337, contractAddress: address,
    async handle(request) {
      const { op, payload = {} } = request;
      if (op === "health") return { status: "confirmed", chain_id: 1337, contract_address: address };
      if (op === "mint") {
        const parsed = validateCanonicalIntent(payload.canonical_intent);
        if (parsed.hash.toLowerCase() !== payload.spec_hash?.toLowerCase() || payload.confirmed_spec_hash?.toLowerCase() !== payload.spec_hash?.toLowerCase()) throw Error("HASH_MISMATCH");
        const tx = await contract.mint(parsed.hash, parsed.value.leaderId, parsed.notional, parsed.loss, parsed.expiry, true);
        const receipt = await tx.wait();
        const event = receipt.logs.map((x) => { try { return contract.interface.parseLog(x); } catch { return null; } }).find((x) => x?.name === "PassportMinted");
        const id = event.args.id.toString(), state = await inspect(id);
        return { status: "confirmed", tx_hash: tx.hash, chain_passport_id: id, chain_id: 1337, contract_address: address, receipt: { status: Number(receipt.status), block_number: receipt.blockNumber }, state };
      }
      if (op === "inspect" || op === "reconcile") return { status: "confirmed", chain_passport_id: String(payload.chain_passport_id), state: await inspect(payload.chain_passport_id), chain_id: 1337, contract_address: address };
      if (op === "revoke") {
        const tx = await contract.revoke(BigInt(payload.chain_passport_id), payload.reason_code || "STOP_REQUESTED");
        const receipt = await tx.wait();
        return { status: "confirmed", tx_hash: tx.hash, chain_passport_id: String(payload.chain_passport_id), receipt: { status: Number(receipt.status), block_number: receipt.blockNumber }, state: await inspect(payload.chain_passport_id), chain_id: 1337, contract_address: address };
      }
      throw Error("UNKNOWN_OPERATION");
    },
    close: async () => eip1193.disconnect(),
  };
}
