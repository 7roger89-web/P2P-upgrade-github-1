# P2P-C06 Minimal Executable Context-Efficient Behavioral Primitive Actual Status

Title: P2P-C06 Minimal Executable Context-Efficient Behavioral Primitive
Date: 2026-08-14
Status: EXECUTABLE_BEHAVIOR_READY_FOR_LIVE_AB
Companion plan: `docs/plans/2026-08-14-p2p-c06-context-delivery-primitive/2026-08-14-p2p-c06-context-delivery-primitive-plan.md`
Companion evidence: `docs/plans/2026-08-14-p2p-c06-context-delivery-primitive/2026-08-14-p2p-c06-context-delivery-primitive-evidence.md`
Companion benchmark: `docs/plans/2026-08-14-p2p-c06-context-delivery-primitive/2026-08-14-p2p-c06-context-delivery-primitive-benchmark.md`

## Purpose

This file records the real current state before implementation. The Goal is authorized to implement only the smallest context-delivery primitive because prior evidence proves the historical A/B labels are not executable behavior.

## Freshness / Refresh Rules

P0 is the baseline before code edits. Refresh this file after each implementation slice and before the next phase. Preserve the prior blocker and artifact hashes unless fresh source/evidence changes them.

## Scope

Target scope:

- current workflow context assembly and serialization path;
- existing context-pointer capability and authoritative source/pointer semantics;
- explicit mode selection, safe minimal view, manifest/fingerprint, freshness, and workflow observability;
- focused C1-C12 behavior tests and affected regression/governance checks.

Out of scope:

- live host/provider execution, token/cost/quality measurement, release promotion, `.15`, `.16-r2`, historical source snapshots, new memory/orchestration, delegation, and UI/database/Docker surfaces.

## Relationship / Impact Evidence

| Unit / File / Surface | File Detail Evidence | Related File Count | Relationship Summary | Impact Note |
|-----------------------|----------------------|--------------------|----------------------|-------------|
| `scripts/p2p_workflow.py` | `E0-P0A-GRAPH1` | 4 listed related files; 267 symbols; 40 inbound refs; 46 linked flows | goal/bootstrap/evidence/ledger/trace/report/capsule/status orchestrator | HIGH scope warning; edit narrow and verify all sibling writers |
| `.p2p/system/p2p_capabilities/context.py` | `E0-P0A-GRAPH2` | 1 indexed file; 21 symbols; 20 local relationships; no linked flows/tests | existing pointer metadata, relevance, freshness resolver | LOW upstream impact; direct capability extension |
| `tests/test_p2p_capability_foundation.py` | direct source inspection plus main graph | 1 test file; existing context-pointer/canonical capability tests | direct behavior regression surface | edit only with focused new tests |
| `tests/test_p2p_workflow.py` | main graph file detail | 1 test file plus workflow siblings | bounded workflow/default/helper-role regression surface | edit only with explicit mode tests |
| `.p2p/state/*`, governance, Decision Trace | direct source/evidence inspection | existing state consumers | source-of-truth/evidence projections | preserve semantics; no second store |
| official `.15` and existing `.16-r2` artifacts | `E0-P0A-BASE1`, `E0-P0A-CAND1` | preserve-only | immutable release identity | do-not-touch |

## Status Rules

| Status | Meaning | Allowed next action |
|--------|---------|---------------------|
| `correct` | Already behaves as required. | Preserve. Add evidence or tests only if needed. |
| `partial` | Some required behavior exists, but it does not fully satisfy the requirement. | Change only the missing parts. |
| `wrong` | Current behavior or contract conflicts with the requirement. | Replace only the exact conflicting behavior. |
| `missing` | Required behavior does not exist. | Implement the missing piece only. |
| `unbound` | Surface exists but is not wired to the real flow. | Bind to the real source only. |
| `fake-or-stub` | Proxy/demo is being used as real behavior. | Keep it proxy-only and make the boundary explicit. |
| `blocked` | Required authority or evidence is unavailable. | Stop. Do not invent authority. |

## Current Status Matrix

| Unit | Current State | Required State | Status | Relationship Count | Evidence | Next Plan Decision |
|------|---------------|----------------|--------|--------------------|----------|--------------------|
| Current workflow context path | Goal/inspection -> explicit selector -> deterministic view/manifest -> bootstrap/evidence -> ledger -> optional trace -> report -> CAPSULE -> status | evidenced and bound to the existing workflow path | correct/bound | 4 related workflow files; 46 linked flows | E0-P0A-FLOW1..E0-P0A-FLOW5, E1-P1B-WIRE1, E1-P1B-OBS1 | preserve; validate closure |
| Existing context pointer resolver | metadata relevance/scope/freshness plus source binding and authoritative resolution | reusable pointer/source binding for compact view | correct | 1 file; 20 local relationships | E0-P0A-FLOW4, E0-P0A-GRAPH2, E1-P1A-SAFETY2 | preserve |
| Baseline context mode | explicit `BASELINE_COMPAT`; default selector; complete structured view | current structured workflow compatibility wrapper | correct | N/A | E1-P1A-CONTEXT1, E1-P1A-CONTEXT2, E2-P2A-SCENARIO1 | preserve default |
| Context-efficient mode | explicit `CONTEXT_EFFICIENT_V1`; required/direct preload plus deterministic pointer/defer | experimental, off by default, structurally distinct | correct/executable | N/A | E1-P1A-SAFETY1, E2-P2A-SCENARIO1..E2-P2A-SCENARIO12 | no live A/B claim |
| Source/evidence access | Goal/evidence/policy/profile/eval/status/ledger sources are hash-bound with identical A/B source bindings/access contract | same legitimate access with different preload | correct/bound | N/A | E1-P1A-CONTEXT3, E1-P1B-OBS2 | preserve |
| Required acceptance/security/owner/dependency facts | top-level acceptance/constraints plus required/direct categories are shared; unsafe omission raises | required facts always included or fail closed | correct | N/A | E1-P1A-SAFETY1, E2-P2A-NEGATIVE1, E2-P2A-NEGATIVE6 | preserve |
| Contradiction handling | conflict groups are retained together in B | preserve conflict/provenance and pointers | correct | N/A | E1-P1A-SAFETY1, E2-P2A-SCENARIO9 | preserve |
| Freshness/stale binding | source hashes/fingerprint are emitted; changed authoritative content rejects resolution | stale view rejected | correct | N/A | E1-P1A-SAFETY2, E2-P2A-NEGATIVE3 | preserve |
| Observation metadata | run result, run/verification/terminal ledger events, report, status, and CAPSULE expose mode/fingerprint/manifest/size proxy | future receipt-ready fields | correct/bound | N/A | E1-P1B-WIRE1, E1-P1B-OBS1, E1-P1B-OBS2 | preserve; no provider fields |
| Regression/governance closure | 95-test discovery, DT1-DT24, governance drift, canonical foundation, and doctor-role checks pass; development doctor retains one unrelated placeholder-doc scan failure | bounded regression/security/governance evidence recorded without release claim | correct with known out-of-scope baseline warning | N/A | E2-P2B-REGRESSION1..E2-P2B-REGRESSION8, Supervisor report | preserve boundary; no unrelated cleanup |
| Agent selection/quorum | canonical registry is eight/8/8 and current workflow does not change it | exactly unchanged, no extra agents | correct/preserve-only | existing capability coverage | E0-P0A-HISTORY1; existing capability tests | test P2-A/P2-B |
| Existing `.15` / `.16-r2` artifacts | hashes supplied and preserve-only | unchanged | correct/preserve-only | N/A | E0-P0A-BASE1, E0-P0A-CAND1 | never edit/package |
| Host live executor/telemetry | prior supervisor found no supported A/B host executor or authoritative telemetry; this implementation adds no adapter | not required for this Goal | blocked/out of scope | N/A | E0-P0A-HISTORY1, E1-P1B-OBS1 | stop before live benchmark |
| Git checkpoint/detect-changes | workspace has no `.git` | truthful limitation report | blocked process capability | N/A | E0-P0A-GIT1 | record failure; do not fabricate commit |

## Status Refresh Log

| Refresh | Date | Repo Basis | Changed Scope | Status Changes | Evidence | Next Phase Update |
|---------|------|------------|---------------|----------------|----------|-------------------|
| R0 | 2026-08-14 | fresh Anvien main/system indexes, source inspection, prior supervisor blocker, artifact hashes | P0 baseline | confirmed no executable A/B; current pointer resolver is partial/unbound; workflow context path evidenced | E0-P0A-FLOW1..E0-P0A-GIT1 | P1-A may implement pure primitive; P1-B wires it; live A/B remains blocked |
| R1 | 2026-08-14 | implementation source plus focused C1-C12 and workflow receipt tests | P1-A, P1-B, P2-A | two executable modes, default baseline, deterministic pointer/defer view, stale/security guards, workflow receipts, same agent/quorum behavior | E1-P1A-CONTEXT1..E1-P1B-OBS2, E2-P2A-SCENARIO1..E2-P2A-NEGATIVE6 | P2-B regression/governance/doctor/detect-changes closure; live A/B remains blocked |
| R2 | 2026-08-14 | final source review, 95-test full discovery, DT1-DT24, governance drift, final lock/artifact hashes, fresh Anvien, Supervisor PASS | P2-B, Pn-A, Pn-B, Pn-C | closure complete; bounded primitive accepted as executable behavior ready for future live A/B | E2-P2B-REGRESSION1..E2-P2B-REGRESSION8, Supervisor report | stop; no live A/B, release, or performance claim |

## Phase Touch Map

| Unit / File / Surface | Plan-Relevant Relationship File | Relationship to Target | Plan Item | Touch Mode | Evidence | Constraint |
|-----------------------|---------------------------------|------------------------|-----------|------------|----------|------------|
| `.p2p/system/p2p_capabilities/context.py` | `tests/test_p2p_capability_foundation.py` | context-pointer capability / direct tests | P1-A | edit | E0-P0A-GRAPH2 | no new store or retrieval subsystem |
| `scripts/p2p_workflow.py` | `tests/test_p2p_workflow.py`, `.p2p/state/*` | workflow producer / state projections | P1-B | edit | E0-P0A-GRAPH1 | preserve agent count, evidence, trace, capsule semantics |
| `tests/test_p2p_capability_foundation.py` | `.p2p/system/p2p_capabilities/context.py` | direct behavior regression | P2-A | edit | E0-P0A-GRAPH2 | add behavior tests after code |
| `tests/test_p2p_workflow.py` | `scripts/p2p_workflow.py` | workflow trigger/output behavior | P2-A | edit | E0-P0A-GRAPH1 | default and explicit mode coverage |
| `governance/*`, `scripts/p2p_governance.py`, `scripts/p2p_decision_trace.py` | workflow and runtime state | validation-only sibling surfaces | P2-B | validate-only | E0-P0A-FLOW1, E0-P0A-HISTORY1 | no governance weakening |
| `.15`, `.16-r2`, `source/8.4.6-C`, `.tmp/*` | none | historical/protected artifacts | all | do-not-touch | E0-P0A-BASE1, E0-P0A-CAND1 | no overwrite, promotion, or source fallback |

## Detailed Findings

### Current workflow context path

Current state:

`main` invokes `run_workflow`; `run_workflow` reads request/project state/snapshot, builds or reuses Goal Contract, bootstraps state/eval, calculates evidence reuse and criteria, appends the Execution Ledger, optionally captures Decision Trace, writes report and CAPSULE, and writes project status. This is the real current flow. It is not currently a context-mode executor.

Required state:

```text
structured source input -> explicit mode selector -> deterministic context view
-> manifest/fingerprint -> existing workflow/evidence projections
```

Evidence:

- `E0-P0A-FLOW1`: source-level flow recovery.
- `E0-P0A-FLOW4`: existing pointer helper only resolves metadata/freshness.
- `E0-P0A-HISTORY1`: prior A/B blocker.

Relationship and impact:

- Related file count: 4 listed by main Anvien file detail for the workflow; 46 linked flows.
- Relationship summary: high fan-in orchestration with state/report/trace/capsule consumers.
- Impact note: HIGH warning; edit only explicit mode construction/metadata and test all sibling writers.

Classification:

partial/unbound; historical B is fake-or-stub for any executable claim.

Allowed next action:

Implement P1-A pure context primitive, then P1-B workflow binding.

Forbidden next action:

Do not relabel the proxy suite as live A/B, create a live adapter, or add memory/orchestration.

## Next Phase Status Decisions

| Plan Item | Actual Status Finding | Required Status / Next-Action Update |
|-----------|-----------------------|--------------------------------------|
| P1-A | Pure deterministic two-mode view, pointer binding, stale rejection, and safety tests pass | complete; preserve primitive and continue regression closure |
| P1-B | Workflow API/CLI selection and report/status/ledger/CAPSULE receipt metadata are bound; isolated A/B workflow tests pass with unchanged quorum | complete; verify closure surfaces |
| P2-A | C1-C12 structured scenarios and negative safety tests pass; measurements remain local serialization proxies | complete; no quality/token/cost inference |
| P2-B | Full regression, DT1-DT24, governance drift, canonical/quorum checks, protected artifact re-hash, and fresh Anvien evidence complete; package doctor has one unrelated preserved placeholder-doc warning; Git is unavailable | complete with explicit warning/process limitation; no release claim |
| Pn-A | Fresh Supervisor source/evidence review PASSes the bounded claim | complete; report is durable |
| Pn-B | No unrelated product cleanup was added; fixture-copy guards safely ignore generated cache directories; reports/plan/evidence are the only durable plan outputs | complete |
| Pn-C | Plan, actual-status, evidence, benchmark, coder report, Supervisor report, hashes, and terminal result agree | complete; stop after PASS |

## Implementation Gate

- [x] Target scope is listed in Current Status Matrix.
- [x] Each target unit has a status.
- [x] Each status has evidence IDs.
- [x] Each target file has relationship count evidence from Anvien when applicable; hidden `.p2p` source was separately indexed as `p2p-system`.
- [x] Phase Touch Map lists plan-relevant relationship files and touch modes.
- [x] Correct parts are preserve-only.
- [x] Partial/missing/unbound/fake-or-stub/blocked parts have exact next actions.
- [x] Blockers are recorded.
- [x] Next phase status assumptions and work steps were updated from P0 evidence.
- [x] Status Refresh Log has an R0 baseline row.
- [x] If implementation has started, affected rows have been refreshed from latest evidence.

## Final P0 Decision

- [ ] P0 actual-status incomplete. Implementation is blocked.
- [ ] P0 complete. Next phase can proceed unchanged.
- [x] P0 complete. Next phase status, next action, or work steps must be updated before implementation.
- [ ] P0 complete. Target scope is preserve-only.
- [ ] P0 complete. Implementation is blocked by missing authority or evidence.

Decision note:

P0 is complete. Existing source and prior supervisor evidence establish the precise gap: the workflow has a real current context path, but no executable A/B context construction. The smallest safe next action is a pure deterministic view and narrow workflow observability. The live benchmark, host telemetry, release, and all larger architecture remain blocked/out of scope.

## Current Implementation Decision

P1-A, P1-B, P2-A, P2-B, and the closure loop are complete: the two modes are executable, baseline is the only default, B is a deterministic pointer/defer view, source bindings/fingerprints are fail-closed, and the bounded workflow exposes observation metadata without changing agent selection, quorum, permissions, or acceptance. Fresh Supervisor review PASSed the bounded claim. The terminal result is `EXECUTABLE_BEHAVIOR_READY_FOR_LIVE_AB`; no live A/B or token/quality/cost result is implied. The development doctor’s preserved placeholder-doc scan and the workspace’s missing Git metadata remain explicitly recorded limitations, not hidden PASS claims.
