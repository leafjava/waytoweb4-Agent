import fs from "node:fs";
import path from "node:path";
import { createHash } from "node:crypto";

let artifact;

export function compileContract() {
  if (artifact) return artifact;
  const source = fs.readFileSync(path.join(import.meta.dirname, "../contracts/StrategyPassport.sol"), "utf8");
  const expectedHash = createHash("sha256").update(source).digest("hex");
  artifact = JSON.parse(
    fs.readFileSync(path.join(import.meta.dirname, "../artifacts/StrategyPassport.json"), "utf8"),
  );
  if (artifact.source_sha256 !== expectedHash) throw Error("CONTRACT_ARTIFACT_STALE");
  if (!Array.isArray(artifact.abi) || !/^0x[0-9a-f]+$/i.test(artifact.bytecode)) {
    throw Error("CONTRACT_ARTIFACT_INVALID");
  }
  return artifact;
}
