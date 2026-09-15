# Graphiti + Opik + loop engineering — P2P adoption decision

Date: 2026-09-15
Status: `RESEARCH_DECISION_WITH_BOUNDED_OPIK_PILOT`
Runtime authority: `NONE`
Canonical operating authority remains `P2P-OPERATIONS-NOTEBOOK.md`.

## Decision

P2P adopts the useful observability seam from Opik as an **opt-in local Hermes
pilot**, keeps Hindsight as the current optional Hermes memory path, and does
**not** add Graphiti as a second default memory system.

```text
HINDSIGHT = OPTIONAL_MEMORY_PROVIDER
OPIK = OPTIONAL_OBSERVABILITY_ONLY
GRAPHITI = RESEARCH_ONLY_SPECIALIST_TEMPORAL_KG
OPIK_TRACE != P2P_EVIDENCE_AUTHORITY
OPIK_OBSERVABILITY != CONTROL_PLANE
HINDSIGHT_RECALL != DURABLE_PROJECT_TRUTH
GRAPHITI_GRAPH != DURABLE_PROJECT_TRUTH
```

No Opik self-host stack is added. No ClickHouse, MySQL, Redis, MinIO,
Kubernetes, second dashboard authority, or second control plane is created.
The pilot targets Opik Cloud only and is disabled by default.

## Why Opik is the useful missing piece

Hermes already has two distinct observability surfaces:

1. native OTLP operational telemetry for gateway/cron lifecycle and health; and
2. documented plugin hooks around LLM calls, provider requests, tools,
   subagents and session lifecycle.

The pinned Hermes runtime (`nousresearch/hermes-agent:v2026.9.14`) deliberately
keeps its native OTLP exporter content-free. It does not represent the full
agent trajectory with prompts/tool inputs/results. Therefore routing native
OTLP directly into an LLM observability backend would prove health telemetry,
not full agent tracing.

The bounded P2P integration uses the documented plugin-hook seam instead. The
observer buffers one turn locally and emits a finalized Opik trace after the
turn finishes. It does not monkey-patch Hermes core and does not add any
model-visible tool.

Relevant upstream surfaces:

- Hermes plugin/hooks documentation:
  https://hermes-agent.nousresearch.com/docs/user-guide/features/hooks
- Hermes plugin developer documentation:
  https://hermes-agent.nousresearch.com/docs/developer-guide/plugins
- Opik low-level Python trace/span API:
  https://www.comet.com/docs/opik/tracing/advanced/log_traces
- Opik Python SDK reference:
  https://www.comet.com/docs/opik/python-sdk-reference/Opik.html
- Opik SDK configuration:
  https://www.comet.com/docs/opik/tracing/advanced/sdk_configuration

Pinned pilot SDK: `opik==2.2.59`.

## Privacy boundary

Safe default:

```text
P2P_ENABLE_OPIK=NO
P2P_OPIK_CAPTURE_CONTENT=NO
OPIK_ANALYTICS_ENABLE=false
```

When enabled with content capture still `NO`, exported data is restricted to
operational metadata such as model/provider/tool names, timing, status, token
usage and opaque SHA-256-derived correlation identifiers. Raw session/turn/tool
request identifiers are not exported.

These content classes are excluded by default:

- user prompts/messages;
- assistant responses;
- provider request/response bodies;
- tool arguments and results;
- subagent goals and summaries;
- error-message bodies.

`P2P_OPIK_CAPTURE_CONTENT=YES` is a separate privacy-sensitive Owner Gate. The
implementation bounds captured fields and never enables this gate by default.

Opik SDK usage analytics is forced off for the pilot. The guard also rejects a
custom ingestion URL: this slice is specifically a reviewed Opik Cloud pilot,
not a generic exfiltration endpoint.

## Hot-path and failure semantics

Observer callbacks on pre/post model/tool/subagent events only mutate bounded
in-process state. They do not synchronously write a remote trace for each hot
path event.

At terminal turn completion the observer creates already-finalized trace/span
records with both start and end times. This avoids the create-then-immediate-
update race documented for batching clients. Opik remains best-effort:
observer errors are logged and never become Hermes task failure or acceptance
authority.

A bounded emitted-turn cache and unfinished-turn buffer prevent unbounded
process growth. Session finalization performs a best-effort two-second SDK
flush.

## Why Graphiti is not installed

Graphiti is a credible temporal knowledge-graph system and is useful when the
product needs first-class changing facts, entity relationships, provenance and
historical validity. That capability is not rejected.

It is not installed in this slice because P2P/Hermes already has an optional
Hindsight memory path and adding Graphiti now would introduce overlapping
memory authority plus graph-database/LLM-extraction infrastructure before a
representative P2P case proves the need.

Re-open a Graphiti implementation only when all are true:

1. a representative P2P workflow has a temporal/entity/provenance retrieval
   failure that Hindsight plus durable project state cannot satisfy cleanly;
2. Graphiti beats the current path on that representative case with measured
   retrieval quality/cost/latency evidence;
3. durable truth/provenance authority remains outside the memory graph;
4. the integration does not create a competing default memory/control plane.

Upstream: https://github.com/getzep/graphiti

## Loop-engineering assimilation check

No new `LOOP_CONTRACT` framework is added to the Supreme Law in this slice.
Fresh review found the proposed principles already represented by existing
canonical rules, including:

- `SIMPLEST_USEFUL_PATH_TO_COMPLETION`;
- `REAL_STATE_AND_EVIDENCE_OVERRIDE_ASSUMPTIONS`;
- `RECOVER_ADAPTIVELY; DO_NOT_ENTER_SPECULATIVE_FIX_LOOPS`;
- `STOP_WHEN_EVIDENCE_SUFFICIENT` / Rule 12 minimum-sufficient work;
- prompt-alignment requirements for explicit evidence and stop conditions;
- task-contract fidelity and representative real-scenario proof;
- Owner Gate / authority boundaries;
- existing Hindsight rule that memory recall is not durable project truth.

Duplicating those ideas under a fresh named framework would violate the same
anti-overengineering and no-parallel-authority principles they are meant to
strengthen. The runtime pilot therefore adds only the missing observability
capability.

## Acceptance for this pilot slice

```text
OPIK_PLUGIN_DISABLED_BY_DEFAULT = PASS_REQUIRED
METADATA_ONLY_BY_DEFAULT = PASS_REQUIRED
RAW_CONTENT_NOT_EXPORTED_IN_DEFAULT_TEST = PASS_REQUIRED
HOT_PATH_REMOTE_WRITE_BEFORE_TURN_END = ZERO_REQUIRED
FAILED_TURN_TERMINAL_TRACE = PASS_REQUIRED
OPIK_SDK_EXACT_VERSION = 2.2.59_REQUIRED
SELF_HOST_OPIK_INFRA_ADDED = NO_REQUIRED
GRAPHITI_RUNTIME_ADDED = NO_REQUIRED
HINDSIGHT_DEFAULT_AUTHORITY_CHANGED = NO_REQUIRED
PRODUCTION_DEPLOYMENT = NOT_AUTHORIZED_BY_THIS_SLICE
REAL_OPIK_SECRET = NOT_CREATED_OR_STORED_BY_THIS_SLICE
```

The real Cloud round-trip remains a separate Owner Gate because it requires a
real external credential and sends telemetry to an external service. Until
that gate is explicitly exercised, this slice can prove code/build/privacy
contracts but must not claim `LIVE_OPIK_TRACE=PASS`.
