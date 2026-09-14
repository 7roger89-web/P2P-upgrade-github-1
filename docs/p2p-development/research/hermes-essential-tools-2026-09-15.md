# Hermes essential-tools adoption review — 2026-09-15

Status: `BOUNDED_BRIDGE_IMPLEMENTED_NOT_RUNTIME_ENABLED`

This review answers one question: which capabilities from Repomix, TokScale,
Hermes Workspace, Hindsight, and Mission Control should P2P actually adopt
without creating a second source of truth or a second control plane?

## P2P boundary

P2P remains authoritative for task contracts, permissions, durable task state,
evidence, governance, promotion and release decisions. Third-party tooling may
supply context artifacts, telemetry, UI, or non-authoritative recall, but it
must not silently become task/governance authority.

`THIRD_PARTY_TOOL != P2P_AUTHORITY`

`TELEMETRY != BILLING_TRUTH`

`MEMORY_RECALL != DURABLE_PROJECT_TRUTH`

`UI_OR_SWARM != CONTROL_TOWER_AUTHORITY`

## Fresh upstream observations

Observed 2026-09-15 from upstream repositories/docs:

- Repomix: https://github.com/yamadashy/repomix — repository packing, token
  accounting/budget controls, include/ignore controls, compression and MCP.
  Security advisories in 2026 make version pinning and a narrow command surface
  mandatory before any deployment use.
- TokScale: https://github.com/junhoyeo/tokscale — JSON usage/cost telemetry
  across coding agents, including Hermes `state.db`; model/monthly JSON views
  are suitable for read-only ingestion. Public `submit` behavior is explicitly
  outside the P2P bridge.
- Hermes Workspace: https://github.com/outsourc-e/hermes-workspace — zero-fork
  web/PWA workspace for Hermes with chat/files/memory/skills/terminal plus
  operations/swarm/conductor surfaces. Useful UI, but those orchestration
  surfaces overlap P2P Control Tower and therefore receive no authority by
  default.
- Hermes Agent / Hindsight provider: https://github.com/NousResearch/hermes-agent
  — current Hermes memory-provider surface includes Hindsight among selectable
  external memory providers. Hindsight may be evaluated as non-authoritative
  recall only; it must not replace Task State, the fact ledger, Git history, or
  evidence authority.
- Mission Control: https://github.com/builderz-labs/mission-control — broad
  self-hosted task/agent/cost/memory/approval/eval control plane. This overlaps
  existing P2P responsibilities heavily and is alpha; wholesale adoption would
  create split authority.

## Adoption matrix

| Tool | Decision now | P2P role | Explicit boundary |
| --- | --- | --- | --- |
| Repomix | `ADOPT_BRIDGE_NOW` | Optional bounded context packer | Local target only; mandatory token budget; output outside target; no arbitrary/remote argv; artifact is ephemeral and non-authoritative |
| TokScale | `ADOPT_BRIDGE_NOW` | Read-only telemetry | JSON views only; never `submit`; prices/cost are telemetry until independently validated; never task authority |
| Hermes Workspace | `DEFER_RUNTIME_ENABLE` | Candidate beginner/UI shell | Chat/files/dashboard may be useful; Swarm/Conductor/Operations do not become P2P task authority; remote exposure requires explicit security review |
| Hindsight | `DEFER_RUNTIME_ENABLE` | Candidate long-term recall cache | Recall can assist context; GitHub/Task State/fact/evidence ledgers win; start with conservative/manual retain rather than uncontrolled auto-retain |
| Mission Control | `REJECT_AS_SECOND_CONTROL_PLANE` | Possible future read-only observability source | No duplicate task ledger, approval system, scheduler, skill registry, or agent authority; only a future adapter if it exposes unique evidence/telemetry P2P actually needs |

## Implemented bounded bridge

`.p2p/system/p2p_capabilities/hermes_tool_bridges.py` adds two optional
stdlib-only bridges. It installs nothing and enables nothing automatically.

### Repomix bridge

The bridge intentionally exposes only:

- a local directory input;
- output path outside the target repository;
- explicit positive token budget;
- supported output style;
- optional compression/include/ignore selectors;
- bounded timeout.

It intentionally exposes no arbitrary extra arguments and no remote-repository
mode. The API also does not expose a way to disable Repomix security scanning.
A successful pack returns size/SHA-256 metadata and is classified
`EPHEMERAL_CONTEXT_ARTIFACT`, never authoritative project state.

### TokScale bridge

The bridge exposes only these read-only JSON shapes:

- `tokscale --json`
- `tokscale models --json`
- `tokscale monthly --json`

There is intentionally no generic command passthrough and therefore no
`tokscale submit` path. Returned data is classified
`TELEMETRY_NON_AUTHORITATIVE`.

## Critical Hermes version-drift gate

Current P2P Hermes evidence and `hermes_adapter.py` are anchored to Hermes
v0.20.2. Current upstream has moved through the v0.21 series, including major
session/state, MCP, delegation and memory changes. At the same time the P2P
DockHosting Dockerfile currently starts from `nousresearch/hermes-agent:latest`.
A reported upstream Docker-image lag also means the `latest` tag cannot be
assumed to equal the latest GitHub release.

Therefore:

`HERMES_RUNTIME_VERSION_UNKNOWN_OR_DRIFTED => DO_NOT_ENABLE_STATE_DB/UI/MEMORY_INTEGRATION`

Before TokScale is wired to a live Hermes `state.db`, or Workspace/Hindsight is
enabled in the P2P Hermes deployment, a separate smallest-sufficient
compatibility slice must:

1. resolve and pin the exact Hermes runtime/image identity;
2. re-probe the P2P Hermes adapter against that exact runtime;
3. verify state/session schema needed by TokScale;
4. verify Workspace gateway/dashboard contract if Workspace is selected;
5. verify Hindsight provider configuration and persistence boundary if Hindsight
   is selected;
6. rerun the existing P2P adapter/security invariants without widening
   permissions or enabling background execution in the headless adapter.

This is a compatibility gate, not permission to deploy, promote, expose a
remote UI, add persistent infrastructure, or create a second control plane.

## OE gate

Would a simpler solution reach the same outcome? Yes: two narrow adapters plus
one compatibility gate are enough. Installing all five tools, adding a new
registry/database/dashboard, or replacing P2P Control Tower would add more
state and authority than the current goal requires.

Stop condition for this slice: bounded Repomix/TokScale bridge code exists,
deterministic tests prove its command boundaries, this adoption decision is
recorded, and no runtime/production deployment has changed.
