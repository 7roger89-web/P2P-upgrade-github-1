# P2P-C11 Durable Task State and Minimal Dependency Graph Foundation Actual Status

Title: P2P-C11 Durable Task State and Minimal Dependency Graph Foundation
Date: 2026-08-14
Status: PASS — bounded C11 foundation ready; workflow-helper plan/run remains a separately reported timeout limitation
Companion plan: `docs/plans/2026-08-14-p2p-c11-durable-task-foundation/2026-08-14-p2p-c11-durable-task-foundation-plan.md`
Companion evidence: `docs/plans/2026-08-14-p2p-c11-durable-task-foundation/2026-08-14-p2p-c11-durable-task-foundation-evidence.md`
Companion benchmark: `docs/plans/2026-08-14-p2p-c11-durable-task-foundation/2026-08-14-p2p-c11-durable-task-foundation-benchmark.md`

## Purpose

This living file records the C11 baseline, implementation refreshes, and final
status. It separates existing authority and correct C10/C09 behavior from the
additive task-state surface. It does not replace the Goal Contract, project
status, FACT_LEDGER, Live Specs, Decision Trace, approvals, or Execution Ledger.

## Freshness / Refresh Rules

Refresh after every implementation slice and before each next phase. Preserve
historical status transitions in the log; do not silently rewrite completed
task or decision history.

## Scope

Target scope: minimal durable task contract, dependency/state kernel, evidence/
capability/permission/owner gates, deterministic planning/selection, task-state
projection, interruption/resume reconstruction, direct handoff, CLI inspection,
focused tests, and affected regression.

Out of scope: scheduler/background execution, worker delegation/parallelism,
new agents/router/model/provider, second truth store, C08/C09 investigation,
Live Specs promotion, release approval, and protected prior artifacts.

## Relationship / Impact Evidence

| Unit / File / Surface | File Detail Evidence | Related File Count | Relationship Summary | Impact Note |
|-----------------------|----------------------|--------------------|----------------------|-------------|
| `scripts/p2p_workflow.py` | `E0-P0A-IMPACT1` | 5 directly listed related files; 50 linked flows | existing Goal/bootstrap/plan/run owner | high scope warning; inspect-only to avoid changing a 288-symbol high-fan-in surface |
| `.p2p/system/p2p_capabilities/evidence.py` | `E0-P0A-IMPACT1` | 1 file in runtime graph; 35 symbols | existing C10 EvidenceClaim/evaluate_done | preserve-only; task module consumes contract |
| `.p2p/system/p2p_capabilities/context.py` | `E0-P0A-IMPACT1` | runtime graph preserve-only | existing context pointer/source hash binding | preserve-only; task stores refs only |
| `.p2p/system/p2p_capabilities/decision_trace.py` | `E0-P0A-IMPACT1` | runtime graph preserve-only | typed trace projection over existing ledger | preserve-only; task events are additive references |
| `.p2p/state/goal-contract.json` | `E0-P0A-STATE1` | project-state artifact | current C11 Goal Contract written by workflow helper | preserve as Goal authority; task plan references Goal ID |
| `.p2p/state/project-status.json` | `E0-P0A-STATE1` | project-state artifact | existing status projection still names prior C09 Goal | partial/stale projection; do not rewrite C09 evidence; use existing workflow/status path |
| `.p2p/state/execution-ledger.jsonl` | `E0-P0A-SRC1` | existing single event store | workflow/Decision Trace/evidence events | preserve and append task references only |
| `governance/fact-ledger.json`, `governance/live-specs.json` | `E0-P0A-SRC1` | protected governance sources | canonical fact/runtime projections | correct, preserve-only |
| approvals / approval policy | `E0-P0A-SRC1` | protected governance sources | owner/governance authority | correct, preserve-only |
| context manifests / pointers | `E0-P0A-SPEC1` | existing state/report artifacts | source/freshness/scope references | correct, preserve-only |
| CAPSULE artifacts | `E0-P0A-STATE1` | existing capsule files | cross-session summary aids | partial for C11; task state must not depend on chat/capsule memory |
| task/work-item concepts | `E0-P0A-TASK1` | 0 durable task runtime surfaces | no task contract/graph/state machine found | missing; implement additive module |
| interruption/resume state | `E0-P0A-TASK1` | 0 task resume surfaces | no task-specific interruption classification/next-task reconstruction | missing; implement additive module |
| canonical identities / AESTHETICA | `E0-P0A-CANON1` | existing registry/spec | exact canonical 8/8 and optional specialist | correct, preserve-only |
| official/candidate artifacts | `E0-P0A-ART1` | protected external artifact paths | `.15` official; `.20` unpromoted | correct, preserve-only |

## Status Rules

| Status | Meaning | Allowed next action |
|--------|---------|---------------------|
| `correct` | Existing behavior meets the C11 preservation boundary. | Preserve and regression-check. |
| `partial` | Existing state exists but is not sufficient for the C11 task contract. | Add only the missing task/resume bridge. |
| `missing` | Required task/resume behavior does not exist. | Implement the additive surface. |
| `blocked` | External evidence/authority is unavailable. | Preserve and report; do not infer. |

## Current Status Matrix

| Unit | Current State | Required State | Status | Relationship Count | Evidence | Next Plan Decision |
|------|---------------|----------------|--------|--------------------|----------|--------------------|
| Goal Contract | C11 Goal Contract exists under `.p2p/state/goal-contract.json`; the plan constructor binds its Goal ID, scope, non-scope, and criteria refs | task plan references the existing Goal ID and requirements | bound-correct | 1 state artifact + task plan | `E0-P0A-STATE1`, `E1-P1C-PLAN1` | use explicit task specs through the new CLI/API |
| Project status | current projection still names prior C09 Goal and terminal BLOCKED | C11 task state must not overwrite C09 evidence; final workflow may update project projection through existing path | partial / preserve-only | 1 state artifact | `E0-P0A-STATE1`, `E0-P0A-C091` | use existing workflow path; no direct C09 rewrite |
| FACT_LEDGER / Live Specs | canonical fact source and deterministic projection | unchanged | correct | protected | `E0-P0A-SRC1`, `E0-P0A-SPEC1` | preserve-only |
| Approval / governance | existing policy/approval/drift controls | task gates reference granted authority, never grant it | correct | protected | `E0-P0A-SRC1` | preserve-only |
| EvidenceClaim / done check | C10 bound evidence requires safe provenance, current/fresh state, scope, and fingerprint | task DONE must bind to this contract plus candidate fingerprint | bound-correct / preserve-only | runtime file | `E0-P0A-SRC1`, `E0-P0A-SPEC1` | consume in P1-B |
| Context pointers | source-bound, freshness-aware, permission-independent pointers | task stores authoritative pointer refs only | correct / preserve-only | runtime/state | `E0-P0A-SPEC1` | consume in P2 |
| Decision Trace / Execution Ledger | append-only trace projection over existing ledger | task/plan changes reference affected task IDs without new ledger | correct / preserve-only | existing single ledger | `E0-P0A-SRC1`, `E0-P0A-SPEC1` | append additive task events in P2-A |
| Existing CAPSULE | task/profile capsules remain chat/session summaries | durable task projection reconstructs without capsule/chat | partial / preserve-only | existing capsules + independent task state | `E0-P0A-STATE1`, `E2-P2B-RESUME1` | keep CAPSULE non-authoritative |
| Task contract / dependency graph | additive typed task/owner/plan kernel is present and validated | minimal typed task/graph/state contract | bound-correct | 1 runtime module | `E1-P1A-CONTRACT1`, `E1-P1A-GRAPH1` | preserve additive boundary |
| Evidence/permission/capability/owner task gates | task-level preflight and owner decision state fail closed | fail-closed preflight and owner state | bound-correct | 1 runtime module | `E1-P1B-EVID1`, `E1-P1B-GATE1` | no grant/install fallback |
| Planning/selection/handoff | bounded plan revisions, deterministic selector, and direct handoff are present | deterministic plan/next task/direct handoff | bound-correct | 1 runtime module | `E1-P1C-PLAN1`, `E1-P1C-SELECT1` | no microtask explosion or worker delegation |
| Durable task projection/resume | atomic `.p2p/state/task-state.json` adapter and additive existing-ledger events are present; main checkout is not implicitly initialized | `.p2p/state/task-state.json` + existing ledger refs + fresh reconstruction | bound-correct | 1 runtime module + 2 isolated reconstruction paths | `E2-P2A-STORE1`, `E2-P2A-LEDGER1`, `E2-P2B-RESUME1` | explicit CLI/API initialization only |
| C09 host lineage | no fresh official host identity evidence | remain UNKNOWN/BLOCKED | blocked | preserve-only | `E0-P0A-C091` | do not touch |
| Canonical identities | exact eight, denominator 8, AESTHETICA optional | unchanged | correct | protected | `E0-P0A-CANON1` | preserve-only |
| Candidate artifacts | `.15` official; `.20` unpromoted; new C11 candidate is separate and unpromoted | preserve; new C11 candidate only if gates pass | correct | protected + `.tmp` candidate | `E0-P0A-ART1`, `E4-P4A-HASH1` | no promotion/release approval |
| Git checkpoint | no `.git` directory | honest detect-changes limitation | blocked | N/A | `E0-P0A-GIT1` | do not initialize Git |

## Status Refresh Log

| Refresh | Date | Repo Basis | Changed Scope | Status Changes | Evidence | Next Phase Update |
|---------|------|------------|----------------|----------------|----------|-------------------|
| R0 | 2026-08-14 | C10 evidence map, full relevant SPEC cluster, current state and Anvien refresh | full C11 baseline | task/graph/resume missing; existing authority correct; project status partial/stale; C09 blocked | `E0-P0A-SRC1`..`E0-P0A-GIT1` | P1 additive module only; P2 existing state/ledger bridge; no existing function edits |
| R1 | 2026-08-14 | additive runtime/CLI implementation and focused checks | P1/P2 | task contract, gates, planning, projection, resume, and CLI become bound-correct; C09/C08 unchanged | `E1-*`, `E2-*` | add 20-case structural matrix and run full regression |
| R2 | 2026-08-14 | 20-case structural matrix, full suite, gates, package check | P3/P4 | focused 20/20; full 139/139; all required gates PASS; candidate created with embedded `.15` | `E3-*`, `E4-P4A-*` | supervisor review, cleanup, final status |
| R3 | 2026-08-14 | Supervisor source/invariant review and final Anvien refresh | closure | Supervisor PASS; root graph 334/33/12707/14434; Git diff remains unavailable; helper plan/run timeout remains explicit | `E4-P4B-SUP1`, `E4-P4C-CLEAN1`, `E4-P4D-CLOSE1` | stop; do not begin execution orchestration |

## Phase Touch Map

| Unit / File / Surface | Plan-Relevant Relationship File | Relationship to Target | Plan Item | Touch Mode | Evidence | Constraint |
|-----------------------|---------------------------------|------------------------|-----------|------------|----------|------------|
| `.p2p/system/p2p_capabilities/task_state.py` | `tests/test_p2p_task_state.py` | new source/direct behavior test | P1-A/P1-B/P1-C/P2-A/P2-B | edit | `E0-P0A-TASK1` | standard library; no agent/scheduler/second ledger |
| `scripts/p2p_task_state.py` | `tests/test_p2p_task_state.py` | thin CLI adapter | P2-C | edit | `E0-P0A-TASK1` | no duplicate state logic; explicit local writes only |
| `.p2p/state/task-state.json` | `.p2p/state/goal-contract.json` | task projection references Goal ID | P2-A | generate/write | `E0-P0A-STATE1` | existing state boundary; no TaskDB |
| `.p2p/state/execution-ledger.jsonl` | `.p2p/system/p2p_capabilities/decision_trace.py` | additive task/plan event refs | P2-A | append-only | `E0-P0A-SPEC1` | preserve existing ledger; no second ledger |
| `.p2p/state/project-status.json` | `scripts/p2p_workflow.py` | existing status writer/reader | all | preserve-only/inspect-only | `E0-P0A-IMPACT1` | do not silently rewrite C09 projection |
| `evidence.py`, `context.py`, `decision_trace.py`, `trust.py` | new task module | existing contracts consumed by reference | P1/P2 | preserve-only | `E0-P0A-IMPACT1`, `E0-P0A-SPEC1` | no C10 weakening |
| FACT_LEDGER/Live Specs/approval/canonical registry | task module/tests | existing governance source | all | preserve-only/validate-only | `E0-P0A-SRC1`, `E0-P0A-CANON1` | no promotion or identity change |
| official/candidate packages, v5/baseline/user paths | package/tests | protected targets | P4 | do-not-touch/validate-only | `E0-P0A-ART1` | reject mutation targets |

## Detailed Findings

### Existing Goal and project state

Current state: the workflow helper and Goal Contract persist bounded Goal,
project, evidence, capsule, and ledger artifacts. The newly created C11 Goal
Contract is present, while the current project-status projection still names
the preceding C09 Goal. That is a real projection mismatch, not permission to
rewrite C09 history.

Required state: task state references the existing Goal and remains additive;
the existing workflow/status path owns any project-status update.

Evidence: `E0-P0A-STATE1`, `E0-P0A-IMPACT1`, `E0-P0A-C091`.

Classification: `partial / preserve-only`.

Allowed next action: implement task projection and record the mismatch in
resume/report output until the existing workflow updates it.

Forbidden next action: overwrite C09 status/evidence or create a parallel Goal
authority.

### Task and resume foundation

Current state: the additive task module, state machine, graph validator,
owner-gate state, next-task selector, direct handoff, interruption classifier,
and fresh-process reconstruction adapter are implemented.

Required state: one additive task module plus explicit `.p2p/state/task-state.json`
projection and additive events in the existing Execution Ledger.

Evidence: `E1-*`, `E2-*`, `E3-P3A-TEST1`, and `E4-P4A-PACK1`.

Classification: `bound-correct` for the C11 task boundary.

Allowed next action: use the explicit foreground CLI/API to initialize and
inspect a Goal-scoped task plan; a later Goal may add bounded execution only
after separate approval/evidence.

Forbidden next action: create TaskDB/TaskGraphDB/workflow.sqlite, scheduler,
agent pool, queue, worker delegation, or background process.

### Protected authority and identity

Current state: C10 fact/evidence/permission guarantees, Decision Trace, C09
UNKNOWN, canonical 8/8, and AESTHETICA optional status are existing correct or
blocked facts.

Required state: unchanged; task state references these systems and never
promotes content, grants permission, or infers host identity.

Evidence: `E0-P0A-SRC1`, `E0-P0A-SPEC1`, `E0-P0A-C091`, `E0-P0A-CANON1`.

Classification: `correct / preserve-only` (C09 specifically `blocked`).

Allowed next action: consume and regression-check.

Forbidden next action: C08 rerun, C09 host investigation, canonical identity
fabrication, AESTHETICA quorum inclusion, or C10 contract weakening.

## Next Phase Status Decisions

| Plan Item | Actual Status Finding | Required Status / Next-Action Update |
|-----------|-----------------------|--------------------------------------|
| P1-A | Additive task contract/graph/state kernel is implemented and focused | preserve contract; no existing authority edits |
| P1-B | Evidence, capability, permission, and owner gates are bound-correct | preserve C10 semantics; no grant/install fallback |
| P1-C | Plan revision, selection, and direct handoff are deterministic | use bounded structured plans; no prose microtask explosion |
| P2-A | Atomic task projection and existing-ledger references pass isolated tests | initialize explicitly; keep one ledger |
| P2-B | Checkpoint/resume classifications reconstruct without chat and never auto-start | use UNKNOWN/NEEDS_RECHECK when proof is absent |
| P2-C | Foreground CLI is packaged and works from checkout/installed runtime layout | no background claims |
| P3 | 20 structural tests and full regression pass | preserve C09/C08/canonical boundaries |
| P4 | Technical gates, candidate lifecycle, and Supervisor review pass | stop at C11 PASS; no promotion or execution orchestration |

## Implementation Gate

- [x] Target scope is listed in Current Status Matrix.
- [x] Each target unit has a status and exact evidence IDs.
- [x] Existing authority writers/readers/durability/source-of-truth boundaries are mapped.
- [x] Existing task/resume gap is explicit.
- [x] Target file relationship evidence and impact warnings are recorded.
- [x] Phase Touch Map defines edit/preserve-only/do-not-touch boundaries.
- [x] Correct and blocked parts have exact next actions.
- [x] Status Refresh Log has an R0 baseline row.
- [x] Later phase status assumptions, next actions, and work steps were updated from P0 findings.

## Final P0 Decision

- [ ] P0 actual-status incomplete. Implementation is blocked.
- [x] P0 complete. Next phase status, next action, and work steps must follow the additive task-module boundary above.
- [ ] P0 complete. Target scope is preserve-only.
- [ ] P0 complete. Implementation is blocked by missing authority or evidence.

Decision note: the R0 project contained a strong C10 authority/evidence/
permission foundation and an existing append-only ledger, but no durable task
foundation. The completed C11 implementation adds only the missing task
projection under `.p2p/state`, reference-only integration with existing
authority, and fresh-process reconstruction tests. C09/C08 and protected
artifacts remain outside the touch boundary; the helper plan/run timeout and
no-Git checkpoint limitation are reported rather than converted into claims.
