# P2P AERG/FW01 Compatibility Verdict Shape Repair Plan

## Metadata

- Date: 2026-08-24
- Status: implementation complete; ready for Supervisor review
- Plan: docs/plans/2026-08-24-aerg-fw01-compatibility-verdict-shape-repair/2026-08-24-aerg-fw01-compatibility-verdict-shape-repair-plan.md
- Evidence: docs/plans/2026-08-24-aerg-fw01-compatibility-verdict-shape-repair/2026-08-24-aerg-fw01-compatibility-verdict-shape-repair-evidence.md
- Benchmark: docs/plans/2026-08-24-aerg-fw01-compatibility-verdict-shape-repair/2026-08-24-aerg-fw01-compatibility-verdict-shape-repair-benchmark.md
- Actual status: docs/plans/2026-08-24-aerg-fw01-compatibility-verdict-shape-repair/2026-08-24-aerg-fw01-compatibility-verdict-shape-repair-actual-status.md

## Goal

Close the malformed legacy compatibility-QI verdict boundary in FW01 so only a contract-valid QI verdict with literal boolean checkpoint permission, canonical verified quality status, safe actual AERG evidence, and the existing execution requirements can persist VERIFIED / CHECKPOINTED.

## Rules

- Complete P0 actual status before implementation work.
- Follow the user-required test-first sequence: add the real-loop RED regression, run it against the rejected subject, commit RED separately, then implement and commit the narrow production repair.
- Change only the assigned invariant family; do not modify AERG core or canonical QI unless evidence proves the contract itself wrong.
- Preserve TASK_DONE_CONTINUE as FW01 loop state and SUCCESS as QI execution outcome.
- Preserve existing fail-closed statuses, provenance, serialization, aggregation, compatibility, and protected-state boundaries.
- Run Anvien detect-changes before each implementation commit.
- Record evidence and benchmarkable counts as they are produced.
- Do not promote, release, deploy, request Owner approval, or start another Goal.

## Problem

A legacy compatibility QI callable that omits aerg_result can return malformed values. With quality_status=QUALITY_VERIFIED, checkpoint_allowed="yes", and quality_failures="not-a-sequence", current FW01 accepts the truthy string and persists VERIFIED / CHECKPOINTED even though the compatibility verdict is not contract-valid.

## Scope

- Add real FW01-loop regressions for malformed verdict shapes and types, valid fresh compatibility, valid blocked compatibility, and unsafe actual-AERG controls.
- Add one narrow FW01 verdict-shape/type predicate or validator at the existing compatibility/checkpoint seam.
- Require mapping shape, recognized canonical quality status, literal bool checkpoint_allowed, and canonical quality_failures container before checkpoint authorization.
- Keep actual AERG clamp authoritative.
- Run the required focused, full UTF-8, C43/RF01, compile, and validator observations.
- Create coder report and update the plan evidence/actual-status/benchmark ledgers.

## Non-Goals

- No changes to aerg_engine.py, aerg_model.py, or quality_intelligence.py.
- No QI vocabulary expansion and no TASK_DONE_CONTINUE addition to QI.
- No new schema framework, dependency, state machine, checkpoint manager, router, scheduler, queue, database, or policy DSL.
- No Windows encoding repair.
- No Owner approval, promotion, release, deployment, GitHub host mutation, or protected-state change.
- No Supervisor review in this implementation turn.

## Requirements

1. Reproduce the exact malformed compatibility output through the real FW01 path before production editing.
2. Commit the RED regression separately.
3. Make the smallest production change in p2p_fw01_loop.py.
4. Accept only the current real QI verdict contract types: mapping/object with canonical quality_status string, bool checkpoint_allowed, and the current QI tuple quality_failures container; malformed or missing fields fail closed.
5. Require canonical QUALITY_VERIFIED and checkpoint_allowed is True together; safe actual AERG and existing execution requirements remain required.
6. Keep canonical QI execution_status=SUCCESS and FW01 output TASK_DONE_CONTINUE.
7. Preserve all listed unsafe and provenance invariants.
8. Verify durable .p2p/fw01.json state, not transient objects only.

## Acceptance Criteria

- Exact malformed output is RED before repair and BLOCKED after repair.
- None, empty mapping, empty list, string, missing fields, null/unknown status, non-boolean truthy values, and malformed failure containers all persist QUALITY_REVIEW / BLOCKED.
- Valid fresh compatibility persists VERIFIED / CHECKPOINTED.
- Valid false/blocked compatibility remains QUALITY_REVIEW / BLOCKED.
- Stale, contradicted, subject-mismatch, and insufficient actual AERG remain blocked even with affirmative compatibility output.
- SUCCESS remains QI execution outcome and TASK_DONE_CONTINUE remains FW01 loop state.
- AERG core and QI canonical source files are unchanged.
- Required regressions produce NEW_TEST_FAILURES=0, NEW_RUNTIME_FINDINGS=0, and NEW_VALIDATOR_FAILURE_CLASSES=0.
- Validator remains 52/59 with only inherited V01, V03, V05, V09, V06, V12, V20.
- Protected/audit state and all prior reports remain unchanged.
- A coder handoff report exists; Supervisor review is the next state.

## Checklist

- [x] P0-A: Complete actual status before implementation work.
  - Goal: classify the rejected subject and all sibling surfaces.
  - Work Steps: bind Git, inspect the prior reject, read the execution/evaluation specs, inspect FW01/QI/AERG source and Anvien evidence, and record the exact pre-fix runtime.
  - Implementation Gate: actual-status.md records P0 evidence and permits P1-A.
  - Acceptance: FW01 compatibility seam is partial/wrong, canonical QI and AERG are preserve-only, and no authority conflict remains.

### P1: Test-first malformed verdict closure

- Phase Goal: encode the full malformed compatibility invariant against the rejected subject before touching production.
- Phase Boundary:
  - In scope: real FW01 compatibility callable tests and durable checkpoint assertions.
  - Out of scope: production source and canonical AERG/QI changes.
  - Dependencies: P0 actual status, current HEAD, isolated repo-local test worktrees.
- Phase Implementation Rule: implement P1-A, verify RED, refresh actual-status, run detect-changes, and commit the RED test before P1-B.
- Ordered Slice List:
  - P1-A: Add malformed compatibility matrix and controls.
  - P1-B: Commit the reproducible RED test checkpoint.

- [x] P1-A: Add malformed compatibility matrix and controls
  - Goal: prove exact pre-fix behavior and define post-fix durable outcomes.
  - Scope Boundary:
    - Editable: tests/test_aerg_qi_fw01_fail_closed.py or the smallest existing FW01 test surface.
    - Inspect-only: p2p_fw01_loop.py, quality_intelligence.py, AERG modules, checkpoint store.
    - Preserve-only: AERG/QI source, governance, reports, protected state.
    - Out of scope: production repair and unrelated test cleanup.
  - Non-Goals: no fake loop, no artificial AERG object, no transient-only assertions.
  - Pre-flight Questions:
    - Data source: actual FW01 step and actual AERG result in an isolated Git worktree.
    - Display permission: N/A; no UI.
    - DB read flow: durable .p2p/fw01.json read after step.
    - DB write flow: real FW01 checkpoint writer only.
    - Render location: N/A; runtime JSON checkpoint is the observable result.
    - UI behavior flow: N/A.
    - Docker runtime: N/A; Python capability runtime.
    - Playwright target: N/A.
    - Behavior test: legacy callable omits aerg_result and returns each matrix shape.
    - Cleanup/quarantine: repo-local .tmp worktrees removed after each case.
    - External side effects: none.
    - N/A notes: no host, release, or deployment action.
  - Work Steps:
    1. Add the exact malformed verdict regression and matrix cases.
       - UI flow check: N/A.
       - DB/data flow check: assert durable checkpoint state.
       - Render location check: N/A.
       - Evidence target: E1-P1A-RED1.
    2. Run focused test against current rejected subject and record the expected RED failure.
       - UI flow check: N/A.
       - DB/data flow check: verify current malformed output reaches VERIFIED / CHECKPOINTED.
       - Render location check: N/A.
       - Evidence target: E1-P1A-RED2.
  - Implementation Gate:
    - Anvien file/impact evidence is recorded or its hidden-path limitation is explicitly recorded.
    - Exact pre-fix fail-open is reproduced with actual AERG and durable state.
  - Acceptance:
    - Source: no production file changed.
    - Runtime/UI: N/A.
    - DB/data: exact pre-fix durable VERIFIED / CHECKPOINTED captured.
    - Behavior test: RED is reproducible.
    - Cleanup/quarantine: all temporary worktrees removed.
    - Evidence IDs: E1-P1A-RED1, E1-P1A-RED2.
    - Actual-status rows refreshed: FW01 compatibility remains wrong pending P1-B.
  - Evidence Targets: exact test name, command, failure, durable JSON, and clean temporary-worktree state.
  - Actual-status Update: add R1 showing test coverage missing -> bound RED coverage.
  - Commit Boundary: no commit until RED evidence is captured; then commit separately in P1-B.

- [x] P1-B: Commit the reproducible RED test checkpoint
  - Goal: preserve the test-first checkpoint as an auditable commit.
  - Scope Boundary:
    - Editable: only the new test file changes.
    - Inspect-only: all production and protected files.
    - Preserve-only: existing prior commits and reports.
    - Out of scope: production repair.
  - Non-Goals: do not make the RED test pass in this slice.
  - Pre-flight Questions:
    - Data source: current Git subject and real loop.
    - Display permission: N/A.
    - DB read flow: durable checkpoint assertion.
    - DB write flow: test-isolated FW01 writer.
    - Render location: N/A.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: malformed compatibility matrix.
    - Cleanup/quarantine: repo-local isolated worktrees.
    - External side effects: no external writes.
    - N/A notes: commit is local and traceable.
  - Work Steps:
    1. Run Anvien detect-changes and inspect only intended test diff.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: N/A.
       - Evidence target: E1-P1B-CHANGES1.
    2. Commit the RED test with the focused command and failure summary.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: N/A.
       - Evidence target: E1-P1B-COMMIT1.
  - Implementation Gate:
    - RED test is independently reproducible and no production path was edited.
  - Acceptance:
    - Source: test-only commit.
    - Runtime/UI: N/A.
    - DB/data: RED durable behavior recorded.
    - Behavior test: expected failure is present.
    - Cleanup/quarantine: clean isolated worktrees.
    - Evidence IDs: E1-P1B-CHANGES1, E1-P1B-COMMIT1.
    - Actual-status rows refreshed: test coverage bound, production still wrong.
  - Evidence Targets: commit hash, diff scope, RED output.
  - Actual-status Update: append test-only commit and keep FW01 status wrong.
  - Commit Boundary: commit the RED test separately.

### P2: Narrow FW01 production repair and closure

- Phase Goal: validate compatibility verdict shape/types at the existing checkpoint seam without changing AERG/QI architecture.
- Phase Boundary:
  - In scope: p2p_fw01_loop.py validator/predicate and its direct runtime tests.
  - Out of scope: AERG core, QI canonical contract, governance/protected state.
  - Dependencies: committed P1 RED test.
- Phase Implementation Rule: implement P2-A, run focused green/negative controls, refresh status, detect changes, and commit; then run P2-B full regression.
- Ordered Slice List:
  - P2-A: Add narrow FW01 verdict-shape/type validation.
  - P2-B: Run full regression and prepare coder handoff.

- [x] P2-A: Add narrow FW01 verdict-shape/type validation
  - Goal: make malformed compatibility output fail closed while preserving fresh valid behavior.
  - Scope Boundary:
    - Editable: p2p_fw01_loop.py only.
    - Inspect-only: QI return contract, AERG modules, checkpoint store, tests.
    - Preserve-only: all protected/audit files and prior reports.
    - Out of scope: new schema framework or changes to QI/AERG.
  - Non-Goals: no general compatibility framework, no new state.
  - Pre-flight Questions:
    - Data source: actual QI return contract and existing FW01 clamp.
    - Display permission: N/A.
    - DB read flow: durable fw01 checkpoint.
    - DB write flow: existing checkpoint method.
    - Render location: N/A.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: malformed matrix plus fresh/unsafe controls.
    - Cleanup/quarantine: repo-local temporary worktrees.
    - External side effects: none.
    - N/A notes: compile/test only.
  - Work Steps:
    1. Inspect Anvien impact/file-detail result and source lines, then implement the smallest predicate that validates mapping, canonical quality_status, literal bool checkpoint_allowed, and current quality_failures container.
       - UI flow check: N/A.
       - DB/data flow check: checkpoint authorization boundary.
       - Render location check: N/A.
       - Evidence target: E2-P2A-SRC1.
    2. Run focused matrix, fresh valid, and unsafe AERG controls; ensure QI still receives SUCCESS and FW01 returns TASK_DONE_CONTINUE.
       - UI flow check: N/A.
       - DB/data flow check: all durable states.
       - Render location check: N/A.
       - Evidence target: E2-P2A-RUNTIME1.
  - Implementation Gate:
    - P1 RED test commit exists.
    - Accepted field types are derived from current real QI return contract; no new schema framework.
  - Acceptance:
    - Source: only FW01 seam changes.
    - Runtime/UI: N/A.
    - DB/data: malformed -> QUALITY_REVIEW / BLOCKED; valid fresh -> VERIFIED / CHECKPOINTED.
    - Behavior test: all matrix and unsafe controls pass.
    - Cleanup/quarantine: isolated worktrees removed.
    - Evidence IDs: E2-P2A-SRC1, E2-P2A-RUNTIME1.
    - Actual-status rows refreshed: FW01 wrong -> correct for focused scope.
  - Evidence Targets: source diff, direct runtime results, durable checkpoint results.
  - Actual-status Update: append R2 after focused green.
  - Commit Boundary: one production repair commit after focused acceptance and detect-changes.

- [x] P2-B: Full regression and coder handoff
  - Goal: prove no sibling invariant regression and prepare Supervisor review.
  - Scope Boundary:
    - Editable: coder report, plan ledgers, notes decision log; no further production edits unless focused regression fails.
    - Inspect-only: all source and protected state.
    - Preserve-only: prior reports and protected governance.
    - Out of scope: Supervisor review and Owner actions.
  - Non-Goals: no opportunistic encoding repair.
  - Pre-flight Questions:
    - Data source: current HEAD and fresh test output.
    - Display permission: N/A.
    - DB read flow: durable FW01 JSON.
    - DB write flow: isolated test roots only.
    - Render location: N/A.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: full required matrix.
    - Cleanup/quarantine: repo-local temp worktrees and probe files.
    - External side effects: none.
    - N/A notes: no UI, Docker, or host proof.
  - Work Steps:
    1. Run focused, AERG/QI/FW01, AERG, freshness, QI, FW01, A-Z, full UTF-8, C43/RF01, compile, and validator observation.
       - UI flow check: N/A.
       - DB/data flow check: durable unsafe/fresh states.
       - Render location check: N/A.
       - Evidence target: E2-P2B-REG1.
    2. Run detect-changes, verify protected/audit state, update ledgers and coder report, and hand off READY_FOR_SUPERVISOR_REVIEW.
       - UI flow check: N/A.
       - DB/data flow check: protected state unchanged.
       - Render location check: N/A.
       - Evidence target: E2-P2B-HANDOFF1.
  - Implementation Gate:
    - Focused production repair commit passes.
  - Acceptance:
    - Source: production diff only p2p_fw01_loop.py plus intended tests/docs.
    - Runtime/UI: N/A.
    - DB/data: durable checkpoint semantics closed.
    - Behavior test: NEW_TEST_FAILURES=0, NEW_RUNTIME_FINDINGS=0, NEW_VALIDATOR_FAILURE_CLASSES=0.
    - Cleanup/quarantine: no temporary probe/worktree residue.
    - Evidence IDs: E2-P2B-REG1, E2-P2B-HANDOFF1.
    - Actual-status rows refreshed: FW01 compatibility correct; remaining Supervisor review pending.
  - Evidence Targets: regression table, detect-changes output, report path, commit hashes, protected-state proof.
  - Actual-status Update: append R3 closure/handoff state.
  - Commit Boundary: separate report/ledger commit if required; no Supervisor verdict claimed.

- [ ] Pn-A: Call supervisor for the implemented-plan acceptance loop.
  - Goal: verify the completed plan work against current source, tests, reports, commits, and protected boundaries.
  - Work Steps:
    1. Call Supervisor review for the exact repair subject.
    2. If rejected, return only to this scope.
    3. Re-run Supervisor after any repair.
  - Implementation Gate: P1 and P2 complete.
  - Acceptance: Supervisor passes or records a precise blocker; no Owner/promotion action.

- [ ] Pn-B: Remove dead work created during this plan.
  - Goal: leave only useful plan/report/test artifacts.
  - Work Steps: inspect and remove only temporary probe artifacts created by this plan, then verify status.
  - Implementation Gate: no production or owner files are targeted.
  - Acceptance: no dead plan-created probe remains.

- [ ] Pn-C: Close the plan.
  - Goal: record final evidence, detect-changes, commits, and known next state.
  - Work Steps: update ledgers and coder report; do not claim Supervisor/Owner acceptance.
  - Implementation Gate: Pn-A is complete or explicitly pending Supervisor.
  - Acceptance: handoff is traceable and state is known.

## Risk Notes

- Compatibility callables are intentionally flexible at signature level; validating result semantics must not remove the legacy signature path.
- Truthiness coercion is the primary safety risk; literal bool and canonical status checks must be explicit.
- Existing AERG clamp must remain authoritative for unsafe actual AERG results.
- The broad worktree is owner-dirty; only the exact target test/source paths may be edited.
- Anvien hidden-path impact lookup may remain unavailable; direct Git/source/runtime evidence must be recorded.
- Ordinary Windows cp1252 test errors are inherited harness portability evidence and are out of scope.

## Implementation closure

- RED test-only commit: `1b22745527fb31e6299a65cc631f14ab4c754502`.
- Production repair commit: `6c1746d6716bcfe9042ae82b37bf319eda50ea1a`.
- Current HEAD: docs/report-only descendant of executable repair subject
  `6c1746d6716bcfe9042ae82b37bf319eda50ea1a`; bind the exact tip with Git at
  handoff.
- Current terminal: `P2P_AERG_COMPAT_VERDICT_SHAPE_REPAIR_READY_FOR_SUPERVISOR_REVIEW`.
- Supervisor review, independent verification, Owner approval, promotion,
  release, deployment, and host mutation remain pending/forbidden in this
  implementation turn.
