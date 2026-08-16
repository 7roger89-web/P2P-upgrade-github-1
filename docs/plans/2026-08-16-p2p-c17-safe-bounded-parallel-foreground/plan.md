# P2P-C17 Safe Bounded Parallel Foreground Execution Plan

## Metadata

- Date: `2026-08-16`
- Status: `PASS — C17 foundation ready; cognitive economy evaluated; candidate unpromoted; live parallel execution not certified`
- Plan: `docs/plans/2026-08-16-p2p-c17-safe-bounded-parallel-foreground/plan.md`
- Evidence: `docs/plans/2026-08-16-p2p-c17-safe-bounded-parallel-foreground/evidence.md`
- Benchmark: `docs/plans/2026-08-16-p2p-c17-safe-bounded-parallel-foreground/benchmark.md`
- Actual status: `docs/plans/2026-08-16-p2p-c17-safe-bounded-parallel-foreground/actual-status.md`

## Goal

Implement C17 Safe Bounded Parallel Foreground Execution as a small extension of the existing C11 task DAG, C12 foreground executor, and C15 bounded delegation controller. At most two already-READY, demonstrably independent tasks may run concurrently in one foreground command; uncertainty, conflict, missing identity, unsafe permissions, and control-plane failure remain fail-closed. The source candidate must first be reconciled to the promoted `.19` lineage without replacing or modifying the official `.19` artifact.

## Rules

- Complete P0 actual status before implementation work.
- Update each checklist item immediately when it is completed.
- Record evidence as work completes.
- Record benchmarkable counts or measurements when they are taken.
- Preserve the official `.19` artifact and all C10-C16 source work.
- Keep C12 direct single-task behavior and C15 one-child limits unchanged outside an explicit C17 group context.
- No scheduler, queue, daemon, remote bridge, persistent worker pool, second router, second ledger, or simulated eight-agent quorum.
- Run Anvien impact/file-detail before editing touched symbols and detect-changes before final acceptance; the checkout is not a Git repository, so any unavailable Git evidence must be recorded rather than fabricated.
- This is a Python/runtime package change. UI, DB, Docker, and Playwright checks are `N/A` with a reason; real runtime and package-boundary checks remain required.

## Problem

The current source contains the C10-C16 cumulative foundation and C15 can execute one bounded child, but the development metadata still reports `.15` and is blocked below the promoted `.19` baseline. The foreground path also rejects multiple active tasks by design and has no C17 decision model for dependency independence, read/write scope conflicts, shared resources, aggregate permissions, value, group receipts, partial success, cancellation, or combined verification.

## Scope

- Reconcile active source metadata to an unpromoted `.20` development candidate based exactly on official `.19`, using a controlled, reversible source-of-truth operation.
- Add a C17 bounded parallel coordinator that selects at most two READY tasks and composes existing C15 child execution, handoff, result, evidence, and ledger/Decision Trace mechanisms.
- Add a conservative dependency/scope/resource/value/permission gate, durable group record, distinct child bindings, independent parent verification, combined verification, partial-result and cancellation truth states, bounded retry, and no-grandchild enforcement.
- Add focused structural/behavior tests and package inventory updates; update durable roadmap/state only after evidence is available.

## Non-Goals

- Do not overwrite, rebuild, republish, or promote official `.19`.
- Do not turn the general C11/C12/C15 path into a scheduler or allow multiple unrelated active tasks.
- Do not add background execution, remote execution, queueing, daemon lifecycle, cloud memory, connectors, network permissions, or an eight-agent QUORUM runtime.
- Do not certify live parallel host execution when the current host has no supported native child callback surface.
- Do not change C08 (`DEFERRED`) or C09 (`BLOCKED/EVENT_EVIDENCE_UNAVAILABLE`) states.

## Requirements

1. Recover durable state before edits and prove the source has C10-C16 work.
2. Reconcile all active version surfaces coherently to `.20` while retaining `.19` as immutable official baseline.
3. Recover only existing READY tasks; validate the existing DAG and reject dependency relations in either direction.
4. Reject overlapping read/write/delete scopes and shared mutable/singleton resources; unknown boundaries are not independent.
5. Apply the existing C15 per-child value, preflight, permission-subset, identity, finite-budget, and `DELEGATE=false` rules.
6. Enforce maximum two children, depth one, no grandchildren, aggregate permission safety, and no shared unsafe singleton.
7. Persist a group record linked to the existing ledger/Decision Trace, distinct handoffs, contexts, results, verification, and rollback/cancellation state.
8. Verify each child independently, then verify the combined result when concurrent mutations require it; preserve unrelated partial success.
9. Keep cancellation truthful, freeze on unknown mutation/control-plane failure, and never perform a third rescue retry.
10. Run package/doctor/unit/eval/drift checks and report foundation readiness separately from live certification.

## Acceptance Criteria

- Source metadata is coherent at `.20`, based on the exact official `.19` SHA, and validation/build gates no longer report lineage regression; `.19` ZIP hash is unchanged.
- `MAX_PARALLEL_CHILDREN == 2`, parallelism is foreground-only, and C12/C15 single-child behavior remains covered and passing.
- Independent READY pair can run through two C15 child controllers with distinct group/handoff/result/verification bindings and no shared unsafe resource.
- Dependent, scope-conflicting, resource-conflicting, ambiguous, permission-unsafe, identity-unknown, stale, active-task, and malformed-control cases choose sequential/block/freeze truthfully without starting unsafe work.
- One-child failure does not erase unrelated success; unknown mutation and control-plane failure prevent automatic continuation; no third child or rescue is started.
- C17 structural/evaluation suite passes in isolated repository-local temporary roots; package candidate verifies as an unpacked package; no promotion or release approval is performed.
- Durable roadmap reports `C17 DONE/PASS`, `PARALLEL_EXECUTION_FOUNDATION_READY` separately from `LIVE_PARALLEL_EXECUTION_CERTIFIED = NO`, with C08/C09 preserved.

## Checklist

- [x] P0-A: Complete actual status before implementation work.
  - Goal: establish the real current state.
  - Work Steps: inspect official control, C16 lineage, package metadata, C10-C16 runtime/tests, and Anvien evidence; classify each target.
  - Implementation Gate: completed in `actual-status.md` before source implementation.
  - Acceptance: actual status identifies correct, partial, missing, and blocked surfaces for this scope.

### P1: Lineage reconciliation and source-state gate

- Phase Goal: prove cumulative source continuity and move only active source metadata from stale `.15` to unpromoted `.20` based on exact official `.19`.
- Phase Boundary:
  - In scope: `scripts/p2p_development_control.py`, active package/runtime metadata, governance current-development/roadmap state, lineage tests.
  - Out of scope: official ZIP, historical reports, C08/C09, package promotion.
  - Dependencies: P0 status and exact official hash evidence.
- Phase Implementation Rule: implement `P1-A`, verify and refresh status, then implement `P1-B`.
- Ordered Slice List:
  - P1-A: Add controlled lineage reconciliation and C17 governance transitions.
  - P1-B: Verify coherent metadata, immutable `.19`, and package preflight.

- [x] P1-A: Add controlled lineage reconciliation and C17 governance transitions.
  - Goal: make the source candidate truthful and buildable without overwriting `.19`.
  - Scope Boundary:
    - Editable: development-control validation/reconciliation, active VERSION/manifest surfaces, focused governance tests.
    - Inspect-only: official `.19` ZIP and C10-C16 historical reports.
    - Preserve-only: official artifact/hash, C08/C09 state, canonical identity set.
    - Out of scope: release/promotion/approval.
  - Non-Goals: automatic release, metadata edits outside the active surfaces, or changing historical evidence.
  - Pre-flight Questions:
    - Data source: `governance/development-control.json`, root/package/runtime metadata, C16 reports.
    - Display permission: N/A; this is a local developer/runtime contract.
    - DB read flow: N/A; no database.
    - DB write flow: N/A; durable JSON/manifest files only.
    - Render location: N/A; CLI/runtime reports.
    - UI behavior flow: N/A; no UI.
    - Docker runtime: N/A; no containerized service.
    - Playwright target: N/A; no browser surface.
    - Behavior test: lineage reconciliation and validation tests in `tests/test_p2p_development_control.py`.
    - Cleanup/quarantine: all test mutations under repository-local `.tmp`; no official/user-project paths.
    - External side effects: none; no network/connectors/promotion.
    - N/A notes: package hashes/locks are regenerated only for the unpromoted candidate.
  - Work Steps:
    1. Add the guarded reconciliation operation and explicit `.20`/C17 validation states.
       - UI flow check: N/A, no UI.
       - DB/data flow check: verify atomic metadata writes and rollback on failure.
       - Render location check: verify CLI status output and source metadata agree.
       - Evidence target: `E1-P1A-LINEAGE*` and updated actual-status row.
    2. Update active metadata/state and add tests that reject below-official or incoherent lineage.
       - UI flow check: N/A, no UI.
       - DB/data flow check: validate control and all active version surfaces after reconciliation.
       - Render location check: verify package/runtime version reports.
       - Evidence target: `E1-P1A-TEST*`, official hash comparison, and `E1-P1A-DETECT*`.
  - Implementation Gate:
    - Existing Anvien file-detail/impact evidence covers the control script (medium blast-radius warning) and package builder; rerun focused evidence before any new symbol edit.
    - No candidate is promoted and no official artifact is touched.
  - Acceptance:
    - Source: active metadata is `.20` and based on exact `.19`.
    - Runtime/UI: CLI/runtime version surfaces are coherent; UI N/A.
    - DB/data: control validation PASS; no second state authority.
    - Behavior test: stale below-official and rollback tests pass.
    - Cleanup/quarantine: temporary roots only; official ZIP hash unchanged.
    - Evidence IDs: `E1-P1A-LINEAGE1..E1-P1A-TEST3`.
    - Actual-status rows refreshed: lineage and metadata transition `partial/blocked -> correct for development`.
  - Evidence Targets: `E1-P1A-LINEAGE1`, `E1-P1A-LINEAGE2`, `E1-P1A-TEST1`, `E1-P1A-TEST2`, `E1-P1A-DETECT1`.
  - Actual-status Update: record `.20` reconciliation, exact `.19` ancestry, and preserved artifact evidence.
  - Commit Boundary: commit after acceptance when Git is available; otherwise record no-Git limitation.

- [x] P1-B: Verify coherent metadata, immutable `.19`, and package preflight.
  - Goal: prove the reconciled source passes build lineage checks before C17 runtime changes are accepted.
  - Scope Boundary:
    - Editable: package/release tests only if they encode stale `.15` assumptions.
    - Inspect-only: candidate build output and extracted verification root.
    - Preserve-only: official `.19` ZIP.
    - Out of scope: promotion and final release approval.
  - Non-Goals: embedding a self-referential candidate SHA into its own ZIP.
  - Pre-flight Questions:
    - Data source: package builder and development-control validator.
    - Display permission: N/A.
    - DB read/write: N/A.
    - Render location: package manifest/doctor output.
    - UI behavior: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: package lineage preflight and official hash comparison.
    - Cleanup/quarantine: `.tmp/p2p-c17` only.
    - External side effects: none.
    - N/A notes: candidate remains unpromoted.
  - Work Steps:
    1. Run preflight and, after C17 implementation, build/verify an unpromoted candidate package.
       - UI flow check: N/A.
       - DB/data flow check: verify generated lock/checksum inputs are source-derived.
       - Render location check: verify extracted VERSION/manifest/doctor results.
       - Evidence target: `E1-P1B-PACKAGE1..E1-P1B-PACKAGE3`.
    2. Refresh status and record candidate size/hash without changing official baseline.
       - UI flow check: N/A.
       - DB/data flow check: record candidate hash in source governance after build, not inside its own hash input.
       - Render location check: N/A.
       - Evidence target: `E1-P1B-HASH1`, `E1-P1B-HASH2`.
  - Implementation Gate: package builder lineage check and official hash comparison must pass.
  - Acceptance:
    - Source: no `.15` active version mismatch remains.
    - Runtime/UI: unpacked package doctor PASS; UI N/A.
    - DB/data: no external writes.
    - Behavior test: package tests pass.
    - Cleanup/quarantine: candidate output remains under `.tmp` until evidence is recorded.
    - Evidence IDs: `E1-P1B-PACKAGE1..E1-P1B-HASH2`.
    - Actual-status rows refreshed: package preflight `blocked -> ready`.
  - Evidence Targets: package build/verify/doctor and official SHA comparison.
  - Actual-status Update: note package candidate status and no promotion.
  - Commit Boundary: commit only source/test changes if Git becomes available; do not commit generated candidate ZIP.

### P2: Bounded independent foreground parallel execution

- Phase Goal: select and run at most two independent READY tasks through existing C15 child surfaces with durable, verifiable group state.
- Phase Boundary:
  - In scope: C17 parallel coordinator, C15 parallel-group context extension, task-state atomicity needed for two foreground children, focused tests.
  - Out of scope: C12 default semantics, scheduler/background/remote execution, new ledger/router.
  - Dependencies: P1-A coherent lineage and Anvien impact evidence for C15/task-state files.
- Phase Implementation Rule: implement `P2-A`, verify gates, then `P2-B`.
- Ordered Slice List:
  - P2-A: Add fail-closed independence/value/aggregate-permission decision gate.
  - P2-B: Add bounded foreground execution, group receipts, verification, partial/cancel states.

- [x] P2-A: Add fail-closed independence/value/aggregate-permission decision gate.
  - Goal: deterministically return `PARALLEL`, `SEQUENTIAL`, or `BLOCKED` before either child starts.
  - Scope Boundary:
    - Editable: new C17 runtime module and additive C15 request/context fields only.
    - Inspect-only: C11 DAG authority and C12 direct controller.
    - Preserve-only: C11 state schema semantics and C15 one-child default.
    - Out of scope: child callback execution and combined-result mutation.
  - Non-Goals: speculative prefetch or automatic task creation.
  - Pre-flight Questions:
    - Data source: existing TaskStateStore/TaskPlan plus explicit C17 scope/resource declarations.
    - Display permission: N/A; decision is durable CLI/runtime data.
    - DB read/write: N/A; task ledger is the data boundary.
    - Render location: group decision JSON/ledger event.
    - UI behavior: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: dependency, scope, resource, value, permission, identity, active-task, and max-two cases.
    - Cleanup/quarantine: every fixture uses an isolated `.tmp` root and deletes/quarantines after test.
    - External side effects: callback not invoked in this slice.
    - N/A notes: live host callback unavailable remains `NO` certification.
  - Work Steps:
    1. Implement candidate normalization and deterministic pair selection using DAG relations, scopes/resources, values, and C15 decisions.
       - UI flow check: N/A.
       - DB/data flow check: verify no task ACTIVE mutation before decision completes.
       - Render location check: verify decision rationale and exclusions are inspectable.
       - Evidence target: `E2-P2A-GATE1..E2-P2A-GATE6`.
    2. Add structural tests for fail-closed uncertainty and aggregate bounds.
       - UI flow check: N/A.
       - DB/data flow check: inspect ledger has decision trace but no child result.
       - Render location check: N/A.
       - Evidence target: `E2-P2A-TEST1..E2-P2A-TEST4`.
  - Implementation Gate: run Anvien file-detail/impact for new and changed C15/task-state symbols; high/critical warnings are scope warnings and must be recorded.
  - Acceptance:
    - Source: decision gate is bounded and additive.
    - Runtime/UI: decision output truthful; UI N/A.
    - DB/data: no second ledger; no child starts on blocked decisions.
    - Behavior test: all gate cases pass.
    - Cleanup/quarantine: isolated roots only.
    - Evidence IDs: `E2-P2A-GATE1..E2-P2A-TEST4`.
    - Actual-status rows refreshed: decision gate `missing -> correct`.
  - Evidence Targets: gate outputs, focused unit tests, Anvien impact.
  - Actual-status Update: mark dependency/resource/value gate complete and identify P2-B remaining.
  - Commit Boundary: commit after acceptance when Git exists; otherwise record unavailable.
  - Outcome: `PASS`; the C17 decision surface selects at most two READY tasks, rejects dependency/scope/resource/aggregate conflicts, and defaults to sequential or blocked without starting children.

- [x] P2-B: Add bounded foreground execution, group receipts, verification, partial/cancel states.
  - Goal: execute selected children concurrently in one finite foreground call, using C15 for each child and preserving truthful outcomes.
  - Scope Boundary:
    - Editable: C17 coordinator, additive C15 group context, task-state locking/record-event adapter, package inventory, tests.
    - Inspect-only: official artifact and unrelated C10-C14 runtime.
    - Preserve-only: ordinary C12/C15 single-child paths.
    - Out of scope: background workers, queue, remote bridge, worker-pool lifecycle, eight-thread QUORUM.
  - Non-Goals: claiming live certification without a native supported host surface.
  - Pre-flight Questions:
    - Data source: C17 decision result, C15 handoff/result/verification, existing ledger/Decision Trace.
    - Display permission: N/A; parent-only receipts.
    - DB read/write: N/A; durable JSON/JSONL state.
    - Render location: `.p2p/state/foreground-executions/parallel-groups/<group-id>` and task ledger.
    - UI behavior: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: success, one failure, unknown mutation, control failure, cancellation, retry bound, combined verification, no grandchild.
    - Cleanup/quarantine: test group roots under `.tmp`; candidate package output quarantined.
    - External side effects: only supplied in-process callbacks; no network/remote execution.
    - N/A notes: live probe runs only if a real supported callback surface is present; otherwise record not certified.
  - Work Steps:
    1. Compose two distinct C15 foreground controllers with a short-lived bounded invocation; add atomic store protection for concurrent state transitions.
       - UI flow check: N/A.
       - DB/data flow check: verify group/task/handoff/result/verification bindings and existing ledger events.
       - Render location check: inspect group record after each child completion.
       - Evidence target: `E2-P2B-RUN1..E2-P2B-RUN4`.
    2. Add parent/combined verification, partial success, unknown/control failure, cancellation truth states, and structural no-background checks.
       - UI flow check: N/A.
       - DB/data flow check: verify DONE/NEEDS_RECHECK/BLOCKED/CONTROL_PLANE_FAILURE transitions and no third child.
       - Render location check: N/A.
       - Evidence target: `E2-P2B-VERIFY1..E2-P2B-VERIFY7`.
  - Implementation Gate: preserve C12/C15 baseline tests; no new background/remote/scheduler imports or capabilities.
  - Acceptance:
    - Source: max two and depth one are enforced by code and tests.
    - Runtime/UI: foreground callback concurrency is bounded; UI N/A.
    - DB/data: durable group receipt and existing ledger/Decision Trace are coherent.
    - Behavior test: focused C17 suite and prior C10-C16 tests pass.
    - Cleanup/quarantine: all disposable probe/test state is repo-local and isolated.
    - Evidence IDs: `E2-P2B-RUN1..E2-P2B-VERIFY7`.
    - Actual-status rows refreshed: execution `missing -> correct/partial` and live certification separately `unknown -> NO`.
  - Evidence Targets: concurrency timing/bounded count, group receipts, child and combined verification, failure/cancel tests.
  - Actual-status Update: mark foundation readiness separately from live host certification.
  - Commit Boundary: commit after acceptance when Git exists; otherwise record the no-Git limitation.
  - Outcome: `PASS`; two short-lived foreground C15 controllers share only the explicit group context, persist group/child bindings beside the existing ledger, and preserve partial/unknown/control-plane truth.

### P3: Validation, durable governance, and supervisor closure

- Phase Goal: validate source/package/runtime boundaries, record evidence and metrics, update C17 roadmap state, and obtain a supervisor verdict.
- Phase Boundary:
  - In scope: full Python test suite, package build/verify/doctor, governance validation/drift, structural PX/P eval coverage, reports, roadmap state.
  - Out of scope: release promotion, deployment, external approval, optional hardening after PASS.
  - Dependencies: P1 and P2 accepted or explicitly blocked.
- Phase Implementation Rule: validate `P3-A`, then run `P3-B` supervisor review; stop at PASS/BLOCKED/REJECT.
- Ordered Slice List:
  - P3-A: Run full validation and persist C17 evidence/metrics/state.
  - P3-B: Supervisor review and final cleanup/closure.

- [x] P3-A: Run full validation and persist C17 evidence/metrics/state.
  - Goal: prove the implementation at real package and state boundaries and record C17 terminal state.
  - Scope Boundary: tests, doctor, package candidate, drift, reports, governance JSON; no promotion.
  - Non-Goals: release approval or changing official baseline.
  - Pre-flight Questions: UI/DB/Docker/Playwright are N/A; package/runtime/ledger boundaries are required.
  - Work Steps:
    1. Run focused and full tests, compile/doctor/package verification, governance validation/drift, and Anvien detect-changes.
       - UI/data/render checks: N/A except package/runtime outputs.
       - Evidence target: `E3-P3A-VALIDATE*`, `E3-P3A-DETECT1`.
    2. Update reports, actual status, benchmark ledger, roadmap, and candidate hash without promotion.
       - UI/data/render checks: N/A; verify durable file references and hashes.
       - Evidence target: `E3-P3A-STATE*`, `E3-P3A-HASH1`.
  - Implementation Gate: all required validation commands have explicit PASS/FAIL evidence.
  - Acceptance: C17 `DONE/PASS`, foundation readiness and live certification separated, C08/C09 preserved.
  - Evidence Targets: final test/package/doctor/drift reports and state hash.
  - Actual-status Update: refresh all changed rows and add R-final-pre-supervisor.
  - Commit Boundary: no Git commit is possible in this checkout; record that fact.
  - Outcome: `PASS`; 248/248 repository tests, package build/verify/doctor, source doctor, governance validation/drift, compile, and official hash checks passed.

- [x] P3-B: Supervisor review and final cleanup/closure.
  - Goal: independently review source reality, reports, generated candidate, and plan acceptance.
  - Scope Boundary: review/cleanup only; no new feature expansion.
  - Non-Goals: optional hardening after PASS.
  - Pre-flight Questions: UI/DB/Docker/Playwright N/A; source/evidence/report boundaries required.
  - Work Steps:
    1. Run supervisor skill and resolve only evidenced failures.
       - UI/data/render checks: N/A.
       - Evidence target: `E3-P3B-SUPERVISOR1`.
    2. Remove dead temporary artifacts and close the plan with final status.
       - UI/data/render checks: N/A.
       - Evidence target: `E3-P3B-CLOSE1`.
  - Implementation Gate: P3-A is complete and no unresolved acceptance failure remains.
  - Acceptance: supervisor emits one PASS/REJECT/BLOCKED verdict and the final report is truthful.
  - Evidence Targets: supervisor report, final actual-status/evidence/benchmark.
  - Actual-status Update: add final refresh and closure state.
  - Commit Boundary: none available in no-Git checkout.
  - Outcome: `PASS`; supervisor acceptance is limited to the local C17 foundation. Live host certification and promotion remain explicitly unclaimed.

## Risk Notes

- The official `.19` artifact is immutable and its SHA must be checked before and after all work.
- `task_state.py` has CRITICAL graph impact; touch only the minimum atomicity/event surface and preserve C11 transition invariants.
- C15 and task-state APIs are high-impact; existing tests are mandatory evidence.
- A source metadata reconciliation is a protected lineage action, but it is within this explicitly requested C17 scope and will not promote or publish anything.
- Live parallel execution may remain `NO` because the current host exposes no supported native child callback surface; this is an accurate certification result, not a simulated pass.
- No Git repository exists in the checkout; do not initialize one or claim commits. Record the limitation in evidence and supervisor report.

### P4: Cognitive Economy / Spawn Economy addendum

- Addendum goal: evaluate minimum sufficient context, workers, delegation, and
  coordination overhead for the already-PASS C17 foundation without changing
  its safety contract.
- Scope: quality-adjusted economy gates, CE1–CE10 deterministic fixtures,
  local context proxy evidence, parent/worker/capsule seam verification, and
  durable governance status.
- Explicit non-goals: universal optimization math, token/cost/wall-clock
  claims, adaptive worker/quorum/provider runtime, live certification,
  promotion, or redesign of max-two foreground safety.
- Outcome: `PASS / COGNITIVE_ECONOMY_PARALLEL_ORCHESTRATION_EVALUATED`.
- Original C17 result preserved: `PASS / PARALLEL_EXECUTION_FOUNDATION_READY`.
- Source change: minimal additive economy profile/gate in
  `p2p_capabilities/parallel_execution.py`; old final2 candidate becomes
  historical and a new unpromoted candidate is required.
- Durable evidence: see `cognitive-economy-addendum.md`, CE-focused tests,
  governance provenance, and the refreshed supervisor report.
- Stop rule: stop after bounded evaluation PASS; broader adaptive
  orchestration remains roadmap-only.
