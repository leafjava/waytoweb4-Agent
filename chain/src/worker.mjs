import readline from "node:readline";

const mode = process.env.CHAIN_MODE || "local";
if (!new Set(["local", "live"]).has(mode)) {
  process.stderr.write("CHAIN_MODE must be local or live.\n");
  process.exit(2);
}
// Do not load Ganache or any of its development-only dependency tree in a
// credential-bearing live worker.
const runtime = mode === "live"
  ? await import("./live-runtime.mjs").then(({ createLiveRuntime }) => createLiveRuntime())
  : await import("./runtime.mjs").then(({ createLocalRuntime }) => createLocalRuntime());
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
