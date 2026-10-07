import assert from "node:assert/strict";
import { mkdir, stat, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { performance } from "node:perf_hooks";
import { Client } from "@modelcontextprotocol/client";
import { StdioClientTransport } from "@modelcontextprotocol/client/stdio";

const [targetArg, scoreArg, featureArg, outArg, entryArg, snapshotArg, oneShotScoreArg, oneShotFeatureArg] = process.argv.slice(2);
if (!targetArg || !scoreArg || !featureArg || !outArg || !entryArg || !snapshotArg) {
  throw new Error("usage: persistent_mcp_probe.mjs <target> <score-addr> <feature-addr> <out-json> <rea-entry> <snapshot> [oneshot-score-seconds] [oneshot-feature-seconds]");
}
const oneShotScoreMs = Number(oneShotScoreArg) * 1000;
const oneShotFeatureMs = Number(oneShotFeatureArg) * 1000;
const targetPath = resolve(targetArg);
const outPath = resolve(outArg);
const entrypoint = resolve(entryArg);
const snapshotPath = resolve(snapshotArg);
await mkdir(dirname(outPath), { recursive: true });

const norm = (value) => {
  const s = String(value).trim().toLowerCase();
  const hex = s.startsWith("0x") ? s : "0x" + s;
  if (!/^0x[0-9a-f]+$/u.test(hex)) {
    throw new Error("not a flat hexadecimal address: " + s);
  }
  return "0x" + BigInt(hex).toString(16);
};
const flatNorm = (value) => {
  const s = String(value ?? "").trim().toLowerCase();
  if (!/^0x[0-9a-f]+$/u.test(s)) return null;
  return "0x" + BigInt(s).toString(16);
};
const scoreAddress = norm(scoreArg);
const featureAddress = norm(featureArg);

const env = Object.fromEntries(
  Object.entries(process.env).filter(([, value]) => value !== undefined),
);
env.REA_LOG_LEVEL = "silent";
env.REA_ANALYSIS_PROVIDER = "ghidra";

async function connect(label) {
  const transport = new StdioClientTransport({
    command: process.execPath,
    args: [entrypoint, "mcp"],
    env,
    stderr: "pipe",
  });
  let stderr = "";
  transport.stderr?.on("data", (chunk) => {
    stderr = (stderr + chunk.toString()).slice(-65536);
  });
  const client = new Client({ name: "p2p-rea-canary-02-" + label, version: "1" });
  const started = performance.now();
  await client.connect(transport);
  return { client, transport, connect_ms: performance.now() - started, stderr: () => stderr };
}

async function tool(client, name, args = {}) {
  const result = await client.callTool(
    { name, arguments: args },
    { timeout: 240000 },
  );
  if (result.isError === true) {
    throw new Error(name + " failed: " + JSON.stringify(result));
  }
  if (result.structuredContent && Object.prototype.hasOwnProperty.call(result.structuredContent, "result")) {
    return result.structuredContent.result;
  }
  const text = result.content?.find((item) => item.type === "text")?.text;
  if (typeof text === "string") {
    const parsed = JSON.parse(text);
    return parsed.result ?? parsed;
  }
  throw new Error(name + " omitted structured result");
}

async function timed(fn) {
  const start = performance.now();
  const value = await fn();
  return { ms: performance.now() - start, value };
}

async function allTools(client) {
  const tools = [];
  let cursor;
  do {
    const page = await client.listTools(cursor ? { cursor } : {});
    tools.push(...(page.tools ?? []));
    cursor = page.nextCursor;
  } while (cursor);
  return tools;
}

function dossierFacts(dossier) {
  return {
    procedure: dossier?.procedure ?? null,
    pseudocode: dossier?.pseudocode ?? "",
    callers: dossier?.callers ?? [],
    callees: dossier?.callees ?? [],
    limitations: dossier?.limitations ?? [],
    native_value_flow: dossier?.native_value_flow ?? null,
  };
}

function hasCallee(dossier, address) {
  const wanted = norm(address);
  return (dossier?.callees ?? []).some((item) => flatNorm(item.address) === wanted);
}

const selectedNames = [
  "open_binary",
  "close_binary",
  "binary_session",
  "list_procedures",
  "analyze_function",
  "get_call_graph",
  "search_strings",
  "procedure_info",
];

const first = await connect("persistent");
let firstClosed = false;
let fullTools = [];
let procedures = [];
let coldScore;
let coldFeature;
let warmScore;
let warmFeature;
let graph;
let session;
let closeWithSnapshot;
try {
  fullTools = await allTools(first.client);
  const open = await timed(() => tool(first.client, "open_binary", {
    path: targetPath,
    provider_id: "ghidra",
  }));
  const listed = await timed(() => tool(first.client, "list_procedures"));
  procedures = listed.value;
  session = await timed(() => tool(first.client, "binary_session"));
  coldScore = await timed(() => tool(first.client, "analyze_function", { procedure: scoreAddress }));
  coldFeature = await timed(() => tool(first.client, "analyze_function", { procedure: featureAddress }));
  warmScore = await timed(() => tool(first.client, "analyze_function", { procedure: scoreAddress }));
  warmFeature = await timed(() => tool(first.client, "analyze_function", { procedure: featureAddress }));
  graph = await timed(() => tool(first.client, "get_call_graph", {
    address: featureAddress,
    direction: "forward",
  }));
  closeWithSnapshot = await timed(() => tool(first.client, "close_binary", {
    snapshot_path: snapshotPath,
    overwrite: true,
  }));
  firstClosed = true;
  globalThis.__firstTimings = {
    connect_ms: first.connect_ms,
    open_ms: open.ms,
    list_procedures_ms: listed.ms,
    binary_session_ms: session.ms,
    cold_score_ms: coldScore.ms,
    cold_feature_ms: coldFeature.ms,
    warm_score_ms: warmScore.ms,
    warm_feature_ms: warmFeature.ms,
    graph_ms: graph.ms,
    close_snapshot_ms: closeWithSnapshot.ms,
  };
} finally {
  if (!firstClosed) {
    try { await tool(first.client, "close_binary"); } catch {}
  }
  await first.client.close();
}

const snapshotStat = await stat(snapshotPath);
const second = await connect("snapshot");
let snapshotOpen;
let snapshotScore;
let snapshotFeature;
let snapshotSession;
try {
  snapshotOpen = await timed(() => tool(second.client, "open_binary", {
    path: targetPath,
    provider_id: "ghidra",
    snapshot_path: snapshotPath,
  }));
  snapshotSession = await timed(() => tool(second.client, "binary_session"));
  snapshotScore = await timed(() => tool(second.client, "analyze_function", { procedure: scoreAddress }));
  snapshotFeature = await timed(() => tool(second.client, "analyze_function", { procedure: featureAddress }));
  await tool(second.client, "close_binary");
} finally {
  await second.client.close();
}

const score = dossierFacts(coldScore.value);
const feature = dossierFacts(coldFeature.value);
const scorePseudo = score.pseudocode;
const featurePseudo = feature.pseudocode;
const atScore = procedures.find((item) => flatNorm(item.address) === scoreAddress);
const atFeature = procedures.find((item) => flatNorm(item.address) === featureAddress);
assert.ok(atScore, "stripped procedure inventory omitted score address");
assert.ok(atFeature, "stripped procedure inventory omitted feature address");

const strippedNamesAbsent =
  atScore.name !== "score_record" &&
  atFeature.name !== "feature_gate" &&
  !procedures.some((item) => item.name === "score_record" || item.name === "feature_gate");

const scoreFacts = {
  multiplier_7: /\*\s*7\b/u.test(scorePseudo),
  add_3: /\+\s*3(?:U)?\b/u.test(scorePseudo),
  xor_42: /(\^\s*0x2a\b|\^\s*42\b)/iu.test(scorePseudo),
};
const featureFacts = {
  mode_7: /(==\s*7\b|7\s*==)/u.test(featurePseudo),
  add_11: /(\+\s*0xb\b|\+\s*11\b)/iu.test(featurePseudo),
  calls_score_address: hasCallee(coldFeature.value, scoreAddress),
};
const groundTruthPass =
  strippedNamesAbsent &&
  Object.values(scoreFacts).every(Boolean) &&
  Object.values(featureFacts).every(Boolean);

const selectedTools = fullTools.filter((item) => selectedNames.includes(item.name));
const missingSelectedTools = selectedNames.filter(
  (name) => !selectedTools.some((item) => item.name === name),
);
const fullSchemaBytes = Buffer.byteLength(JSON.stringify(fullTools), "utf8");
const selectedSchemaBytes = Buffer.byteLength(JSON.stringify(selectedTools), "utf8");
const schemaRatio = fullSchemaBytes === 0 ? null : selectedSchemaBytes / fullSchemaBytes;

const coldFunctionTotal = coldScore.ms + coldFeature.ms;
const warmTotal = warmScore.ms + warmFeature.ms;
const coldSessionAnalysisTotal =
  globalThis.__firstTimings.open_ms +
  globalThis.__firstTimings.list_procedures_ms +
  globalThis.__firstTimings.binary_session_ms +
  coldFunctionTotal;
const snapshotFunctionTotal = snapshotScore.ms + snapshotFeature.ms;
const snapshotAnalysisTotal =
  snapshotOpen.ms + snapshotSession.ms + snapshotFunctionTotal;
const oneShotTotal =
  Number.isFinite(oneShotScoreMs) && Number.isFinite(oneShotFeatureMs)
    ? oneShotScoreMs + oneShotFeatureMs
    : null;
const reduction = (baseline, candidate) =>
  baseline === null || baseline <= 0 ? null : ((baseline - candidate) / baseline) * 100;

const report = {
  schema: "p2p-rea-admission-canary-02-result/1",
  target: {
    path: targetPath,
    score_address: scoreAddress,
    feature_address: featureAddress,
    stripped_names_absent: strippedNamesAbsent,
  },
  mcp_catalog: {
    full_tool_count: fullTools.length,
    full_schema_bytes: fullSchemaBytes,
    selected_tool_count: selectedTools.length,
    selected_schema_bytes: selectedSchemaBytes,
    selected_schema_ratio: schemaRatio,
    selected_tool_names: selectedTools.map((item) => item.name).sort(),
    missing_selected_tools: missingSelectedTools,
    selected_schema_pass: missingSelectedTools.length === 0 && schemaRatio !== null && schemaRatio <= 0.25,
  },
  persistent: {
    timings_ms: globalThis.__firstTimings,
    cold_function_total_ms: coldFunctionTotal,
    cold_session_analysis_total_ms: coldSessionAnalysisTotal,
    warm_function_total_ms: warmTotal,
    warm_reduction_vs_cold_session_pct: reduction(coldSessionAnalysisTotal, warmTotal),
    one_shot_score_ms: Number.isFinite(oneShotScoreMs) ? oneShotScoreMs : null,
    one_shot_feature_ms: Number.isFinite(oneShotFeatureMs) ? oneShotFeatureMs : null,
    one_shot_total_ms: oneShotTotal,
    warm_reduction_vs_one_shot_pct: reduction(oneShotTotal, warmTotal),
  },
  snapshot: {
    size_bytes: snapshotStat.size,
    connect_ms: second.connect_ms,
    open_ms: snapshotOpen.ms,
    binary_session_ms: snapshotSession.ms,
    score_ms: snapshotScore.ms,
    feature_ms: snapshotFeature.ms,
    function_total_ms: snapshotFunctionTotal,
    analysis_total_ms: snapshotAnalysisTotal,
    reduction_vs_cold_session_pct: reduction(coldSessionAnalysisTotal, snapshotAnalysisTotal),
  },
  correctness: {
    ground_truth_pass: groundTruthPass,
    score_facts: scoreFacts,
    feature_facts: featureFacts,
    feature_graph_contains_score_address:
      JSON.stringify(graph.value).toLowerCase().includes(scoreAddress.toLowerCase()),
    score_limitations_count: score.limitations.length,
    feature_limitations_count: feature.limitations.length,
    limitations_preserved: score.limitations.length > 0 && feature.limitations.length > 0,
    stripped_score_name: atScore.name,
    stripped_feature_name: atFeature.name,
    score_pseudocode: scorePseudo,
    feature_pseudocode: featurePseudo,
  },
  decision_inputs: {
    persistent_material_improvement: warmTotal <= 0.5 * coldSessionAnalysisTotal,
    snapshot_material_improvement: snapshotAnalysisTotal <= 0.5 * coldSessionAnalysisTotal,
    selected_tool_surface_materially_smaller:
      missingSelectedTools.length === 0 && schemaRatio !== null && schemaRatio <= 0.25,
    actual_agent_token_measurement: "BLOCKED_NOT_RUN_NO_AUTHORIZED_AGENT_RUNTIME_OR_CREDENTIAL",
    offline_schema_bytes_are_model_tokens: false,
  },
};
await writeFile(outPath, JSON.stringify(report, null, 2) + "\n", { mode: 0o600 });
process.stdout.write(JSON.stringify(report, null, 2) + "\n");
