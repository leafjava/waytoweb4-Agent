import { keccak256, toUtf8Bytes } from "ethers";

export const HASH_VERSION = "intent-keccak-v1";
const keys = ["expiryUnix", "leaderId", "maxLossCents", "mode", "notionalCents", "paper", "venue", "version"];

export function validateCanonicalIntent(raw) {
  const value = JSON.parse(raw);
  if (JSON.stringify(Object.keys(value)) !== JSON.stringify(keys)) throw Error("INTENT_KEY_ORDER");
  if (value.version !== HASH_VERSION || value.mode !== "copy" || value.venue !== "paper" || value.paper !== true) throw Error("INTENT_MODE");
  if (!/^[A-Za-z0-9_-]{1,64}$/.test(value.leaderId)) throw Error("INTENT_LEADER");
  for (const name of ["notionalCents", "maxLossCents", "expiryUnix"]) if (!/^[1-9][0-9]*$/.test(value[name])) throw Error(`INTENT_${name}`);
  const notional = BigInt(value.notionalCents), loss = BigInt(value.maxLossCents), expiry = BigInt(value.expiryUnix);
  if (notional > 1_000_000n || loss > notional) throw Error("INTENT_LIMITS");
  return { value, notional, loss, expiry, hash: keccak256(toUtf8Bytes(raw)) };
}
