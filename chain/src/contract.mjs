import fs from "node:fs";
import path from "node:path";
import solc from "solc";

let artifact;

export function compileContract() {
  if (artifact) return artifact;
  const source = fs.readFileSync(path.join(import.meta.dirname, "../contracts/StrategyPassport.sol"), "utf8");
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
  artifact = { abi: contract.abi, bytecode: `0x${contract.evm.bytecode.object}` };
  return artifact;
}
