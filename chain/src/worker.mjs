import readline from "node:readline";
import { createLocalRuntime } from "./runtime.mjs";

if (process.env.CHAIN_MODE !== "local") {
  process.stderr.write("CHAIN_MODE must be local for this offline worker; live transport is intentionally disabled until configured.\n");
  process.exit(2);
}
const runtime = await createLocalRuntime();
const rl = readline.createInterface({ input: process.stdin, crlfDelay: Infinity });
for await (const line of rl) {
  let request;
  try {
    request = JSON.parse(line);
    if (request.protocol_version !== 1 || !request.request_id || !request.run_id) throw Error("INVALID_ENVELOPE");
    const result = await runtime.handle(request);
    process.stdout.write(`${JSON.stringify({ protocol_version: 1, request_id: request.request_id, ...result })}\n`);
  } catch (error) {
    process.stdout.write(`${JSON.stringify({ protocol_version: 1, request_id: request?.request_id || null, status: "failed", error_code: error.message })}\n`);
  }
}
await runtime.close();
