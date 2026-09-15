# P2P Hermes Essential Stack

Status: `LOCAL_OPT_IN_STACK_READY`  
Production / public deployment: `NOT_PERFORMED`

This stack completes the bounded integration path for the Hermes-adjacent tools reviewed on 2026-09-15 without creating a second P2P control plane.

## What is integrated

| Tool | P2P role | Runtime behavior |
|---|---|---|
| Repomix `1.18.0` | bounded context packer | opt-in `tools` profile; repository mounted read-only; output goes to a disposable volume; token budget required |
| TokScale `4.16.0` | read-only token/cost telemetry | opt-in `tools` profile; Hermes data volume mounted read-only; only `--json`; no `submit` path |
| Hermes Workspace `2.3.0` | local web UI | built from exact release commit `15fa9cd706f5c04e4db288fb958e21d10fc776da`; host bind is `127.0.0.1:3000`; HermesWorld link disabled |
| Hindsight | optional non-authoritative memory | bundled Hermes provider; enabling requires an explicit `YES` gate plus API key; safe config keeps `auto_retain=false`, `auto_recall=false`, `memory_mode=tools` |
| Opik `2.2.59` | optional non-authoritative observability | local-stack-only hook observer; disabled by default; metadata-only by default; exact SDK pin; Cloud pilot only; no self-host Opik infrastructure |
| GenieX `v0.3.17` | optional local inference provider | **not bundled**; Snapdragon-only host prerequisite; registered as a named Hermes custom provider only after a real `/v1/chat/completions` smoke test; main model is not changed |
| Mission Control | not a P2P authority | intentionally absent from runtime compose; P2P already owns task state, approvals, orchestration and governance |

Hard invariants:

```text
THIRD_PARTY_TOOL != P2P_AUTHORITY
TOKSCALE_TELEMETRY != BILLING_TRUTH
HINDSIGHT_RECALL != DURABLE_PROJECT_TRUTH
OPIK_TRACE != P2P_EVIDENCE_AUTHORITY
OPIK_OBSERVABILITY != CONTROL_TOWER_AUTHORITY
WORKSPACE_UI != CONTROL_TOWER_AUTHORITY
GENIEX_PROVIDER != P2P_EXECUTOR_AUTHORITY
GENIEX_REGISTER != DEFAULT_MODEL_SWITCH
MISSION_CONTROL != SECOND_CONTROL_PLANE
```

## Pinned upstreams

- Hermes Agent: `v0.21.3`, Docker tag `v2026.9.14`
- Hermes Workspace: annotated tag `v2.3.0` resolved to commit `15fa9cd706f5c04e4db288fb958e21d10fc776da`
- Workspace build toolchain: `pnpm 9.15.9`
- Repomix: `v1.18.0`
- TokScale: `v4.16.0`
- Opik Python SDK: `2.2.59`
- GenieX host-side integration target: stable `v0.3.17` (BSD-3-Clause); alpha/newer upstream builds are not silently selected

The Workspace `v2.3.0` GitHub release does **not** currently have a pullable matching GHCR manifest. Its upstream Dockerfile is also no longer reproducible as written because unpinned Corepack now resolves to pnpm 12, whose build-script policy rejects this older release's Electron/esbuild dependency scripts.

P2P therefore uses `Dockerfile.workspace` as a thin build wrapper. It fetches the exact full 40-character release commit, verifies `git rev-parse HEAD`, pins pnpm `9.15.9` for the lockfile-v9-era build, and then runs the upstream application's ordinary `pnpm install --frozen-lockfile` and `pnpm build`. The application source is not patched and there is no fallback to a mutable registry tag.

The Hermes runtime itself is already compatibility-gated by `.github/workflows/hermes-runtime-compatibility.yml`, including the real P2P Docker build, required CLI flags, TokScale-compatible `state.db`, and the bundled Hindsight provider.

## Local startup

From repository root:

```bash
python scripts/hermes_essential_stack_guard.py init
cd deployments/hermes-essential-stack
docker compose up -d
```

Then open:

```text
http://127.0.0.1:3000
```

The bootstrap creates random local secrets and refuses to overwrite an existing `.env` unless `--force` is explicitly supplied. `.env` is already ignored by repository policy.

Before startup you still need to place at least one model-provider key in the generated `.env` (for example `GEMINI_API_KEY`) unless you already have another persisted Hermes provider configured. Do not commit the file.

## Security topology

The host publishes only loopback ports:

- Workspace: `127.0.0.1:3000`
- Hermes API: `127.0.0.1:8642`
- Hermes dashboard: `127.0.0.1:9119`

Inside the Docker network Hermes binds on `0.0.0.0` so Workspace can reach it, therefore the stack requires generated API/dashboard/workspace authentication secrets. This is deliberate defense in depth even though the host-side binds are local-only.

Do not change those host binds to `0.0.0.0` merely to reach the UI from another device. LAN, Tailscale, reverse-proxy, tunnel, or public exposure is a separate infrastructure/security decision and remains an Owner Gate.

## Repomix

Run the bounded packer:

```bash
docker compose --profile tools run --rm repomix
```

The repo is mounted read-only and the packed result lands in the named `repomix-output` volume, outside the target repository. The default token budget is `200000`; adjust `REPOMIX_TOKEN_BUDGET` in `.env` if needed.

The P2P Python bridge remains the programmatic surface and still rejects remote repository mode, arbitrary argv, output inside the target repo, missing token budgets, and disabling security checks.

## TokScale

Read Hermes telemetry:

```bash
docker compose --profile tools run --rm tokscale
```

The Hermes data volume is mounted `:ro`. This stack does not expose TokScale `submit`, login, or leaderboard mutation. Cost output is telemetry, not accounting/billing authority.

## Hindsight

Hindsight is installed in the pinned Hermes runtime but is not activated by default.

To opt in to the cloud provider:

1. Set these two local `.env` values:

```text
P2P_ENABLE_HINDSIGHT=YES
HINDSIGHT_API_KEY=<your key>
```

2. Apply the fail-closed safe profile:

```bash
docker compose --profile hindsight run --rm hindsight-enable
```

This copies `hindsight-p2p-safe.example.json` into persistent Hermes state and sets `memory.provider=hindsight`. The safe profile intentionally keeps automatic retain and recall off. Memory must be invoked through tools and remains non-authoritative context.

Enabling Hindsight with a real secret is an Owner Gate because it introduces an external memory service and persistent data flow. The repository is ready; no secret has been created or stored here.

## Opik observability pilot

Opik is integrated only into this richer local essential stack. The ordinary root-image build keeps `P2P_INSTALL_OPIK=0`; this stack explicitly builds the same image with `P2P_INSTALL_OPIK=1` and the exact `opik==2.2.59` SDK.

The integration uses Hermes' documented plugin observer hooks around provider requests, tools, subagents and turn/session completion. It does **not** replace Hermes' native OTLP health/lifecycle telemetry and it does not add a model-visible tool. Native Hermes OTLP stays the operational health plane; Opik is the optional LLM/agent trace view.

Safe defaults in the generated `.env` are:

```text
P2P_ENABLE_OPIK=NO
P2P_OPIK_CAPTURE_CONTENT=NO
OPIK_URL_OVERRIDE=https://www.comet.com/opik/api
OPIK_API_KEY=
OPIK_WORKSPACE=
OPIK_PROJECT_NAME=p2p-hermes
OPIK_ENVIRONMENT=development
OPIK_ANALYTICS_ENABLE=false
```

With `P2P_OPIK_CAPTURE_CONTENT=NO`, the observer exports only bounded operational metadata such as model/provider/tool names, timing, status, token usage and opaque hashed correlation identifiers. It does **not** export user prompts, assistant responses, provider request/response bodies, tool arguments/results, subagent goals/summaries or error-message bodies.

`P2P_OPIK_CAPTURE_CONTENT=YES` is a separate privacy-sensitive Owner Gate. Do not enable it merely to make traces look richer.

The observer buffers the hot path in memory and creates finalized trace/span records after turn completion. A tracing failure is logged and does not become Hermes execution authority or a false P2P failure. A bounded session-finalize flush is best-effort.

The pilot deliberately rejects arbitrary ingestion URLs and does not add ClickHouse, MySQL, Redis, MinIO, Kubernetes or a second Opik control plane. If self-hosting later becomes a real requirement, evaluate it as a separate infrastructure decision rather than silently expanding this pilot.

To activate the Cloud pilot after the explicit external-secret/privacy Owner Gate, set local `.env` values without committing them:

```text
P2P_ENABLE_OPIK=YES
P2P_OPIK_CAPTURE_CONTENT=NO
OPIK_API_KEY=<your Opik API key>
OPIK_WORKSPACE=<your Opik workspace>
OPIK_PROJECT_NAME=p2p-hermes
```

Then validate before restart:

```bash
python scripts/hermes_essential_stack_guard.py validate
cd deployments/hermes-essential-stack
docker compose up -d --build hermes-agent
```

Until that real credentialed round-trip is performed, repository/CI evidence proves the build, hook contract and privacy defaults only. It must not be reported as `LIVE_OPIK_TRACE=PASS`.

## GenieX local inference

GenieX is integrated **under Hermes**, not as a new P2P backend or router. Hermes already has a native named-custom-provider surface for OpenAI-compatible endpoints, while GenieX exposes `/v1/chat/completions`. Adding a second P2P adapter would duplicate an existing seam for no useful gain.

Upstream facts used by this integration:

- source: `https://github.com/qualcomm/GenieX`
- license: BSD-3-Clause
- pinned stable target: `v0.3.17`
- supported hardware is Qualcomm Snapdragon only: Windows ARM64 Snapdragon X/X Elite, supported Snapdragon Android devices, or supported Qualcomm Linux ARM64 targets
- GenieX can serve an OpenAI-compatible endpoint, normally on port `18181`
- GitHub-hosted P2P CI is **not** Snapdragon device evidence; it can validate the integration contract but cannot certify NPU/GPU/CPU inference on the Owner's machine

### Why registration is bounded

The `geniex-register` profile does four things only:

1. requires the explicit `P2P_ENABLE_GENIEX=YES` gate;
2. requires a local HTTP `/v1` endpoint plus an explicit model id;
3. sends a real chat-completions probe containing both a `system` and `user` message;
4. registers a named Hermes provider `geniex` only if the probe returns a real `choices` result.

It deliberately sets:

```text
providers.geniex.transport=chat_completions
providers.geniex.discover_models=false
```

The explicit model id + disabled discovery is intentional. GenieX has had OpenAI-compatibility regressions where `/v1/models` returned a precision-suffixed id that `/v1/chat/completions` did not accept. Registration therefore trusts the explicit model id that actually passed the chat probe, not a catalog guess.

Registration **does not** modify `model.provider` or `model.default`. GenieX enters Hermes as an optional named provider; it does not hijack the current cloud/default model.

### Host-side prerequisite

Install and run the pinned GenieX release on a supported Snapdragon machine first. Example upstream flow:

```text
geniex pull ai-hub-models/Qwen3-4B-Instruct-2507
geniex serve
```

Use a model whose license and hardware/runtime path are acceptable for your use case. Model licenses are independent from the BSD-3-Clause GenieX runtime license.

The exact URL placed in `GENIEX_BASE_URL` must be reachable **from the Hermes container**. On Docker Desktop a common candidate is:

```text
http://host.docker.internal:18181/v1
```

Do not weaken a local GenieX bind to a public `0.0.0.0` listener merely to make the container reach it. If the local bridge is not reachable, leave registration blocked and fix the local transport deliberately instead of silently widening exposure.

### Register without replacing the current model

Set the generated `.env` values:

```text
P2P_ENABLE_GENIEX=YES
GENIEX_BASE_URL=http://host.docker.internal:18181/v1
GENIEX_MODEL=ai-hub-models/Qwen3-4B-Instruct-2507
```

Then run:

```bash
python scripts/hermes_essential_stack_guard.py validate
cd deployments/hermes-essential-stack
docker compose --profile geniex run --rm geniex-register
```

Expected terminal evidence after the real request succeeds:

```text
GENIEX_CHAT_SMOKE=PASS
GENIEX_PROVIDER_REGISTERED:model=<model-id>:main_model_unchanged=YES
```

After that, GenieX remains opt-in. In an active Hermes session, switch deliberately with the named custom-provider syntax supported by Hermes, for example:

```text
/model custom:geniex:ai-hub-models/Qwen3-4B-Instruct-2507
```

A successful registration proves only the bounded OpenAI-compatible chat route. It does **not** certify full P2P agent/tool execution, large-context reliability, VLM behavior, NPU performance, or long-horizon autonomy. Those capabilities need their own representative device proof before promotion.

### Octopus V4 decision

Nexa/Octopus V4 is **not** integrated into the P2P commercial/runtime path. Its published GGUF model card uses `CC BY-NC 4.0`, so it is suitable for research/non-commercial experiments but is a bad default dependency for a stack that may later be used commercially. The architecture idea (small local routing/function-calling models) remains useful; the model artifact itself stays out of the commercial lane unless its license changes or a separately licensed replacement is selected.

## Hermes Workspace

Workspace connects to the same single Hermes container used by the gateway. Hermes v0.21.3 supervises its dashboard alongside the gateway in that same container. Do **not** run a second Hermes gateway against the same `/opt/data` volume.

Workspace's Swarm/Conductor/Operations surfaces do not acquire P2P authority merely because the UI exposes them. P2P task state, evidence, approvals and Control Tower remain authoritative.

## Mission Control

Mission Control is deliberately **not** a service in this stack. Its task state, approvals, agent orchestration, skills, memory, eval and scheduling surfaces overlap existing P2P authority. Adding it wholesale would create two steering wheels on one bus.

If a future bounded feature is uniquely valuable, integrate that feature read-only behind an adapter and evidence gate. Do not install Mission Control as a second control plane.

## Validation

```bash
python scripts/hermes_essential_stack_guard.py validate
python -m unittest -v tests.test_hermes_essential_stack_guard tests.test_p2p_opik_observer
```

Hosted CI additionally renders the compose config, builds the exact Workspace release source with the pinned wrapper toolchain, smoke-checks the pinned Repomix/TokScale package versions, builds the real P2P Hermes image, verifies exact `opik==2.2.59` importability in that image, proves the metadata-only observer privacy/hook contract, and starts the local-only Hermes + Workspace stack for health verification. Hosted CI validates the GenieX registration contract statically; live GenieX inference remains a Snapdragon-device proof and is never inferred from ordinary GitHub runners. Live Opik Cloud delivery likewise remains unclaimed until the explicit external-credential pilot is run.
