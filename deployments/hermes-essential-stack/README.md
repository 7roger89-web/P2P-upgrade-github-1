# P2P Hermes Essential Stack

Status: `LOCAL_OPT_IN_STACK_READY`  
Production / public deployment: `NOT_PERFORMED`

This stack completes the bounded integration path for the five Hermes-adjacent tools reviewed on 2026-09-15 without creating a second P2P control plane.

## What is integrated

| Tool | P2P role | Runtime behavior |
|---|---|---|
| Repomix `1.18.0` | bounded context packer | opt-in `tools` profile; repository mounted read-only; output goes to a disposable volume; token budget required |
| TokScale `4.16.0` | read-only token/cost telemetry | opt-in `tools` profile; Hermes data volume mounted read-only; only `--json`; no `submit` path |
| Hermes Workspace `2.3.0` | local web UI | starts with the default stack; host bind is `127.0.0.1:3000`; HermesWorld link disabled |
| Hindsight | optional non-authoritative memory | bundled Hermes provider; enabling requires an explicit `YES` gate plus API key; safe config keeps `auto_retain=false`, `auto_recall=false`, `memory_mode=tools` |
| Mission Control | not a P2P authority | intentionally absent from runtime compose; P2P already owns task state, approvals, orchestration and governance |

Hard invariants:

```text
THIRD_PARTY_TOOL != P2P_AUTHORITY
TOKSCALE_TELEMETRY != BILLING_TRUTH
HINDSIGHT_RECALL != DURABLE_PROJECT_TRUTH
WORKSPACE_UI != CONTROL_TOWER_AUTHORITY
MISSION_CONTROL != SECOND_CONTROL_PLANE
```

## Pinned upstreams

- Hermes Agent: `v0.21.3`, Docker tag `v2026.9.14`
- Hermes Workspace: `v2.3.0`
- Repomix: `v1.18.0`
- TokScale: `v4.16.0`

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

Before startup you still need to place at least one model-provider key in the generated `.env` (for example `GEMINI_API_KEY`). Do not commit the file.

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

## Hermes Workspace

Workspace connects to the same single Hermes container used by the gateway. Hermes v0.21.3 supervises its dashboard alongside the gateway in that same container. Do **not** run a second Hermes gateway against the same `/opt/data` volume.

Workspace's Swarm/Conductor/Operations surfaces do not acquire P2P authority merely because the UI exposes them. P2P task state, evidence, approvals and Control Tower remain authoritative.

## Mission Control

Mission Control is deliberately **not** a service in this stack. Its task state, approvals, agent orchestration, skills, memory, eval and scheduling surfaces overlap existing P2P authority. Adding it wholesale would create two steering wheels on one bus.

If a future bounded feature is uniquely valuable, integrate that feature read-only behind an adapter and evidence gate. Do not install Mission Control as a second control plane.

## Validation

```bash
python scripts/hermes_essential_stack_guard.py validate
python -m unittest -v tests.test_hermes_essential_stack_guard
```

Hosted CI additionally renders the compose config, builds the real P2P Hermes image, verifies the exact Workspace image tag is pullable, and smoke-checks the pinned Repomix/TokScale package versions.
