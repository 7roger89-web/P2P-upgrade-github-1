# Minimal Live Execution & Telemetry Boundary for Real Context-Efficiency Actual Status

Title: Minimal Live Execution & Telemetry Boundary for Real Context-Efficiency
Date: 2026-08-14
Status: Blocked
Companion plan: `docs/plans/2026-08-14-minimal-live-execution-telemetry-boundary/2026-08-14-minimal-live-execution-telemetry-boundary-plan.md`
Companion evidence: `docs/plans/2026-08-14-minimal-live-execution-telemetry-boundary/2026-08-14-minimal-live-execution-telemetry-boundary-evidence.md`
Companion benchmark: `docs/plans/2026-08-14-minimal-live-execution-telemetry-boundary/2026-08-14-minimal-live-execution-telemetry-boundary-benchmark.md`

## Purpose

This file records current reality before any implementation. The central gate is whether exact .15 and .16-r2 conditions have distinct supported executable behavior and whether the host exposes an official live execution boundary.

## Freshness / Refresh Rules

P0 is a current-state classification. If source or host behavior changes, refresh this file before P1. No implementation may begin from a stale classification.

## Scope

Target scope:

- canonical suite and proxy evidence;
- `scripts/p2p_eval.py`, runtime helper roles, candidate artifacts, and host execution surfaces;
- possible minimal adapter/receipt boundary;
- isolation, provenance, security, stale receipt, and canonical checks.

Out of scope:

- all new context-efficient behavior, durable orchestration, providers, user projects, and release promotion.

## Relationship / Impact Evidence

No production edit is authorized until P0 proves distinct executable A/B behavior. Relationship counts below are evidence targets to refresh with Anvien before any edit.

| Unit / File / Surface | File Detail Evidence | Related File Count | Relationship Summary | Impact Note |
|-----------------------|----------------------|--------------------|----------------------|-------------|
| `scripts/p2p_eval.py` | E1-P1A-BOUNDARY1; E1-P1A-ANVIEN1 | 2 related files; 175 symbols; 51 local relationships; 24 linked flows; 4 inbound refs; 832 unresolved | local validator/runner/recorder | inspect-only; high-risk file; no edit authorized |
| `.p2p/evals/2026-08-14-context-efficiency-ab-proxy-suite.json` | E0-P0A-CANON1 | N/A | canonical proxy metadata | preserve-only |
| `.p2p/evals/fixtures/2026-08-14-context-efficiency-cases.json` | E0-P0A-CANON1 | N/A | frozen fixture | preserve-only |
| `.codex/config.toml` and host hooks | E1-P1A-HOST1 | not indexed by Anvien; direct source inspection | supported host lifecycle/identity surface | inspect-only |
| official .15 / candidate .16-r2 artifacts | E0-P0A-BASE1; E0-P0A-CAND1; E1-P1A-ZIP1 | N/A | immutable release identities; 10 differing ZIP entries, with evaluator/runtime sources unchanged except helper/workflow metadata | preserve-only |

## Status Rules

| Status | Meaning | Allowed next action |
|--------|---------|---------------------|
| `correct` | Already behaves as required. | Preserve. |
| `partial` | Some required behavior exists, but gaps remain. | Edit only the proven gap. |
| `wrong` | Current behavior conflicts with the requirement. | Record and fix only under authority. |
| `missing` | Required behavior does not exist. | Implement only if explicitly authorized and safe. |
| `unbound` | Surface exists but is not wired to the real flow. | Bind only when real source exists. |
| `fake-or-stub` | Proxy/demo is being treated as live. | Keep proxy-only; never certify. |
| `blocked` | Required authority or behavior is unavailable. | Stop. |

## Current Status Matrix

| Unit | Current State | Required State | Status | Relationship Count | Evidence | Next Plan Decision |
|------|---------------|----------------|--------|--------------------|----------|--------------------|
| Existing canonical suite | 12 scenarios, 48 proxy trials, fixed A/B labels | unchanged proxy source of truth | correct | N/A | E0-P0A-CANON1; E0-P0A-HISTORY1 | preserve |
| Proxy execution path | local deterministic subprocess/contract runner | must remain non-live | correct/fake-or-stub for live claims | 2 related files; 2 impacted processes | E0-P0A-HISTORY1; E1-P1A-BOUNDARY1; E1-P1A-ANVIEN1 | preserve and label |
| Condition A | metadata label; exact .15 live adapter not proven | callable .15-bound live path | blocked/unbound | N/A | E1-P1A-A1; E1-P1A-HOST1 | stop unless proven |
| Condition B | candidate label; no distinct .16-r2 executable behavior found | callable distinct candidate path | missing/blocked | N/A | E1-P1A-B1; E1-P1A-ZIP1; E1-P1A-SEARCH1 | `BLOCKED_CONDITION_B_NOT_IMPLEMENTED` |
| Independent variable | no proven executable A/B difference | identifiable strategy difference | blocked | N/A | E1-P1A-DIFF1; E1-P1A-ZIP1 | stop |
| Host execution authority | no supported callable condition-switching provider executor found | official live host path | blocked | N/A | E1-P1A-HOST1 | stop |
| Receipt/telemetry boundary | not implemented | only after A and B are eligible | blocked by dependency | N/A | E1-P1A-TELEMETRY1 | do not create fake receipt |
| Permissions/security | no measurement expansion | unchanged | correct | N/A | E1-P1A-SECURITY1 | preserve |
| Canonical identities/quorum | eight identities, denominator 8 | unchanged | correct | N/A | E1-P1A-SECURITY1 | preserve |

## Status Refresh Log

| Refresh | Date | Repo Basis | Changed Scope | Status Changes | Evidence | Next Phase Update |
|---------|------|------------|----------------|----------------|----------|-------------------|
| R0 | 2026-08-14 | current development checkout, artifacts, host surface | live boundary eligibility | initial proxy-only, missing B, and missing host boundary classification | E0-P0A-*; E1-P1A-* | P1 is blocked unless fresh proof changes B status |
| R1 | 2026-08-14 | fresh Anvien graph, current checkout, exact .15/.16-r2 ZIP contents, host surface | distinct candidate and live boundary verification | confirmed B absent as an executable context-efficient behavior; confirmed no supported live A/B executor or authoritative per-trial telemetry | E1-P1A-ANVIEN1; E1-P1A-ZIP1; E1-P1A-SEARCH1; E1-P1A-HOST1 | stop; supervisor review only |

## Phase Touch Map

| Unit / File / Surface | Plan-Relevant Relationship File | Relationship to Target | Plan Item | Touch Mode | Evidence | Constraint |
|-----------------------|---------------------------------|------------------------|-----------|------------|----------|------------|
| `scripts/p2p_eval.py` | canonical suite and tests | local runner/validator | P1-A | inspect-only | E1-P1A-BOUNDARY1 | no live claim from proxy code |
| canonical suite | frozen fixture/evidence | benchmark source of truth | P1-A | preserve-only | E0-P0A-CANON1 | no second suite |
| candidate artifact | runtime/source manifest | candidate identity | P1-A | preserve-only | E0-P0A-CAND1 | no overwrite or promotion |
| host surface | `.codex/config.toml`, supported host tools | execution authority | P1-A | inspect-only/block | E1-P1A-HOST1 | no private API or scraping |

## Detailed Findings

### Fresh source and artifact comparison

The fresh Anvien graph was rebuilt successfully at `2026-08-14T02:49:18Z`. `scripts/p2p_eval.py` file detail reports 175 symbols, 4 inbound references, 51 local relationships, 24 linked flows, 2 related files, 832 unresolved references, and high risk. Upstream impact reports 15 contained/affected symbols and 2 process hits, so no production edit was authorized after P0 failed.

The official ZIP hashes were rechecked:

- .15: `af4d63a882dabfde20ac237574590ec584ee2944bc4cdc30b6a07bf7f681e195`
- .16-r2: `410572d73aa06dadbd8fe1da068fe217eabeb7efc11cf35fc9576c750a4ee8cf`

The ZIP contents differ in exactly 10 entries. The executable comparison is decisive: `scripts/p2p_eval.py` has the same entry length (55,110 bytes) and SHA-256 `2116874e44de34bf5ff5b226d97761e8a01171fe2caca6e4b068d161e1123d08` in both artifacts; `runtime/scripts/p2p_router.py`, `runtime/scripts/p2p_uiux_eval.py`, and `runtime/scripts/p2p_host_identity_hook.py` also have identical entry hashes. The only source-code difference among the relevant workflow surfaces is `scripts/p2p_workflow.py`, whose candidate changes add transient-path filtering, helper CLI probing, and development/portable/installed helper ownership checks (`helper_path_is_transient`, `helper_supports_project_eval`, and `eval_helper_candidates`); they do not add a live executor, condition switch, provider call, or context-efficient execution strategy.

The selected packaged sources contain no `execute_live_trial`, `runtime_task_execution`, `host_execution_id`, `provider_route`, `input_tokens`, `cached_input_tokens`, `output_tokens`, `total_tokens`, or `trial_receipt` implementation. The current suite's `runtime_task_execution=false` remains metadata describing the proxy boundary, not an executable switch.

### Local proxy boundary

The current evaluator defines `_case_command` at `scripts/p2p_eval.py:550-631`, invokes local commands with `subprocess.run` at `scripts/p2p_eval.py:653-661`, and writes deterministic local evidence at `scripts/p2p_eval.py:671-701`. Its `--variant` option at `scripts/p2p_eval.py:1139` selects baseline/P2P metadata, while `--model`, `--surface`, and `--environment-id` at `scripts/p2p_eval.py:1143-1145` default to local-runner labels. This is a supported local proxy evaluation path, not proof of a real Codex host/provider task.

### Host authority boundary

The allow-listed hook at `.p2p/system/scripts/p2p_host_identity_hook.py:77-118` records only official host identity/lifecycle fields such as session, turn, agent, permission mode, model, working directory, and source. Its contract explicitly discards prompt, transcript, assistant-message, tool, environment, and secret-like fields (`:80-83`), and the hook is configured only for the optional `p2p_aesthetica` subagent in `.codex/config.toml:8-14`. No supported host surface in this repository provides a callable A/B condition switch, provider execution receipt, or authoritative per-trial token/cache/cost telemetry.

### Stop decision

The candidate's helper-boundary changes are not an executable Condition B. The supported local evaluator cannot be relabeled live, and no public host/provider execution boundary is available for exact .15/.16-r2 isolation. The valid terminal decision remains `BLOCKED_CONDITION_B_NOT_IMPLEMENTED`; no live receipt or dry-run may be manufactured.

### Independent supervisor closure

The independent supervisor report at `reports/supervisor/rp_supervisor_260814_100021_by_gpt-5-codex_minimal-live-execution-telemetry-boundary.md` (SHA-256 `5bd5cf9dc0fce5f41f20fa72b5b8079b9808ce2f3d881b85289f79edbb8168f`) accepts the bounded blocker with one `PASS` verdict. It explicitly does not certify live execution, A/B quality, telemetry completeness, token savings, or release readiness.

### Condition B

Current state:

The candidate label exists in benchmark metadata, but current .16-r2 evidence does not show a distinct context-efficient execution behavior callable by the supported runtime.

Required state:

```text
Condition B must execute the same task through a real, distinct candidate behavior bound to .16-r2.
```

Evidence:

- E0-P0A-HISTORY1: existing trials are proxy-only.
- E1-P1A-B1: no distinct executable B behavior identified.
- E1-P1A-DIFF1: no independent variable can be proven.

Relationship and impact:

- Related file count: N/A for the absent candidate behavior; no edit is authorized.
- Relationship summary: metadata and local helper only.
- Impact note: blocked.

Classification:

missing/blocked.

Allowed next action:

Stop with `BLOCKED_CONDITION_B_NOT_IMPLEMENTED`; identify the smallest future behavioral primitive only.

Forbidden next action:

Do not implement an entire Context-Efficiency architecture or label the same proxy path as B.

### Live host execution

Current state:

The supported host surface does not currently expose a proven callable condition-switching provider executor or authoritative live receipt path for this repository.

Required state:

```text
A and B must run through a supported host/model path and produce independently verifiable execution evidence.
```

Evidence:

- E1-P1A-BOUNDARY1: helper source is local/proxy execution.
- E1-P1A-HOST1: supported host authority is not bound.

Relationship and impact:

- Related file count: N/A for external host authority.
- Relationship summary: host surface is inspect-only.
- Impact note: blocked.

Classification:

blocked.

Allowed next action:

Revisit under a separately authorized host-boundary goal after B exists.

Forbidden next action:

Do not use private AgentControl, reverse-engineered RPC, patched binaries, credentials, or UI scraping.

## Next Phase Status Decisions

| Plan Item | Actual Status Finding | Required Status / Next-Action Update |
|-----------|-----------------------|--------------------------------------|
| P1-A | Condition B is not proven as a distinct executable behavior; host live path is not proven | block before source edit; return `BLOCKED_CONDITION_B_NOT_IMPLEMENTED` |
| Pn-A | Supervisor must review the blocker and no-overreach claim | review the current evidence package |
| Pn-B/Pn-C | No adapter or receipt artifact was created | close as blocked; preserve all historical proxy/release artifacts |

## Implementation Gate

- [x] Target scope is listed in Current Status Matrix.
- [x] Each current target has a status and evidence ID.
- [x] Fresh Anvien relationship counts are complete for the inspected production edit target; no edit target is authorized because P0 is blocked.
- [x] Phase Touch Map defines preserve/inspect/block modes.
- [x] Correct and preserve-only surfaces are identified.
- [x] Missing/unbound/fake-or-stub/blocked surfaces have exact next actions.
- [x] Blocker and no-architecture rule are recorded.
- [x] R0 refresh row exists.
- [x] Fresh Anvien graph, file detail, and impact evidence were refreshed before confirming that no production edit is authorized.

## Final P0 Decision

- [ ] P0 actual-status incomplete. Implementation is blocked.
- [ ] P0 complete. Next phase can proceed unchanged.
- [ ] P0 complete. Next phase status, next action, or work steps must be updated before implementation.
- [ ] P0 complete. Target scope is preserve-only.
- [x] P0 complete. Implementation is blocked because distinct executable Condition B and supported live host execution are not proven.

Decision note:

P0 is complete. The existing suite and proxy helper are real local evaluation infrastructure, but they are not live host/model execution. The candidate label does not establish a distinct B behavior. The only valid action in this Goal is to stop before production edits with `BLOCKED_CONDITION_B_NOT_IMPLEMENTED`.
