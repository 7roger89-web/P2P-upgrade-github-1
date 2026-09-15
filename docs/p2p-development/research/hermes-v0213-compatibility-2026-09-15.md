# Hermes v0.21.3 compatibility slice — 2026-09-15

Status: `CANDIDATE_NOT_DEPLOYED`

## Upstream identity

- Repository: `NousResearch/hermes-agent`
- Release: `Hermes Agent v0.21.3 (v2026.9.14)`
- Published: 2026-09-14
- Annotated tag resolves to commit: `345cd2b057a452236de401d3534b8502a7465e8d`
- Official release notes state Docker images build from tag:
  `nousresearch/hermes-agent:v2026.9.14`.

The release specifically includes fixes for duplicate `state.db` writer handles
and remote gateway/dashboard session refresh behavior. P2P therefore stops
following mutable `:latest` and pins this release tag in both Hermes
Dockerfiles.

## Interfaces re-verified from the tagged upstream source

The v2026.9.14 CLI parser still exposes the surfaces consumed by P2P:

- `-z` / `--oneshot`
- `--usage-file`
- `--model`
- `--provider`
- `--toolsets`
- `--in`
- `--ignore-rules`

The hosted compatibility workflow additionally builds the actual P2P
DockHosting source image so the existing `hermes-patches==1.6.1` patch set is
verified against the pinned runtime instead of being assumed compatible.

## TokScale boundary

TokScale's Hermes parser reads `$HERMES_HOME/state.db` read-only. Its required
session-level columns are checked by `scripts/hermes_runtime_compatibility.py`.
The parser also supports `session_model_usage`, but TokScale deliberately
falls back to session totals when the optional per-model schema is absent or
cannot be queried. P2P mirrors that behavior: session-level incompatibility is
a hard failure; optional per-model drift is reported as
`SESSION_TOTALS_FALLBACK`, not promoted into a false global failure.

TokScale remains telemetry only. No public `submit` path is introduced.

## Hindsight boundary

The v2026.9.14 upstream ships the Hindsight memory provider. Upstream defaults
include automatic recall and automatic retain, while local embedded mode can
start a background daemon. Those defaults are wider than the current P2P
memory authority boundary.

P2P therefore adds only a fail-closed example profile:

- `auto_retain=false`
- `auto_recall=false`
- `memory_mode=tools`
- `recall_types=observation`
- low recall budget and bounded token return
- workspace-scoped bank naming

This file is not copied into live Hermes config and contains no secret. Enabling
Hindsight still requires a separate authorized runtime configuration decision
because cloud/local modes introduce credential and/or persistent-service
requirements.

`HINDSIGHT_MEMORY != P2P_TASK_STATE`

`HINDSIGHT_RECALL != FACT_OR_EVIDENCE_AUTHORITY`

## Workspace boundary

Hermes Workspace v2.x can attach to an existing Hermes gateway on `:8642` and
uses the separate Hermes dashboard API on `:9119` for enhanced sessions,
config, skills and jobs. The current P2P DockHosting runtime starts the gateway
only; exposing/operating a dashboard plus Workspace would add a new live
service surface. This slice therefore verifies the Hermes runtime foundation
first and does not silently deploy Workspace.

Workspace remains the preferred candidate UI shell after the gateway/dashboard
auth and service topology are explicitly proven. Its Swarm/Conductor/TaskBoard
surfaces do not inherit P2P Control Tower authority.

## Acceptance for this slice

1. Both Dockerfiles pin `nousresearch/hermes-agent:v2026.9.14`.
2. Existing P2P image builds with `hermes-patches==1.6.1`.
3. Built runtime reports Hermes `0.21.3`.
4. Required CLI flags remain present.
5. A real runtime-created `state.db` satisfies TokScale's session-level schema.
6. Bundled Hindsight provider exists in the built image.
7. Safe Hindsight example stays opt-in and auto-memory-off.
8. No deployment, promotion, new secret, public telemetry submission, Workspace
   service, Hindsight daemon, or second control plane is started by this PR.
