import fs from "node:fs";
import path from "node:path";
import { createHash } from "node:crypto";
import solc from "solc";

const root = path.resolve(import.meta.dirname, "..");
const sourcePath = path.join(root, "contracts", "StrategyPassport.sol");
const source = fs.readFileSync(sourcePath, "utf8");
const input = {
  language: "Solidity",
  sources: { "StrategyPassport.sol": { content: source } },
  settings: {
    evmVersion: "paris",
    optimizer: { enabled: true, runs: 200 },
    outputSelection: { "*": { "*": ["abi", "evm.bytecode.object"] } },
  },
};
const output = JSON.parse(solc.compile(JSON.stringify(input)));
const errors = (output.errors || []).filter((item) => item.severity === "error");
if (errors.length) throw Error(errors.map((item) => item.formattedMessage).join("\n"));
const contract = output.contracts["StrategyPassport.sol"].StrategyPassport;
const artifact = {
  compiler: solc.version(),
  source_sha256: createHash("sha256").update(source).digest("hex"),
  abi: contract.abi,
  bytecode: `0x${contract.evm.bytecode.object}`,
};
const target = path.join(root, "artifacts", "StrategyPassport.json");
fs.mkdirSync(path.dirname(target), { recursive: true });
fs.writeFileSync(target, `${JSON.stringify(artifact, null, 2)}\n`, "utf8");
process.stdout.write(`wrote ${target}\n`);
