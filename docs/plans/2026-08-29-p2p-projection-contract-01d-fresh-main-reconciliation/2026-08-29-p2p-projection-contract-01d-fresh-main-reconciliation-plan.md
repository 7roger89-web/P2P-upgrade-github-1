# P2P Projection Contract 01D Fresh-Main Reconciliation Plan

## Metadata

- Date: `2026-08-29`
- Status: `in_progress`
- Plan: `docs/plans/2026-08-29-p2p-projection-contract-01d-fresh-main-reconciliation/2026-08-29-p2p-projection-contract-01d-fresh-main-reconciliation-plan.md`
- Evidence: `docs/plans/2026-08-29-p2p-projection-contract-01d-fresh-main-reconciliation/2026-08-29-p2p-projection-contract-01d-fresh-main-reconciliation-evidence.md`
- Benchmark: `docs/plans/2026-08-29-p2p-projection-contract-01d-fresh-main-reconciliation/2026-08-29-p2p-projection-contract-01d-fresh-main-reconciliation-benchmark.md`
- Actual status: `docs/plans/2026-08-29-p2p-projection-contract-01d-fresh-main-reconciliation/2026-08-29-p2p-projection-contract-01d-fresh-main-reconciliation-actual-status.md`

## Goal

Reconcile the exact Supervisor-reviewed 01C projection-only contract onto the
fresh canonical remote/main at `1c84bc41421dcbe502d40b71fead5022231d0541`,
preserve every compatible SEC01 change, freeze a new exact candidate, obtain
one focused independent Supervisor PASS for that exact SHA/tree, and perform
one normal fast-forward push only if fresh remote/main remains an ancestor.

## Rules

- Complete P0 actual status before implementation work.
- Update each checklist item immediately when it is completed.
- Record evidence as work completes.
- Record benchmarkable counts or measurements when they are taken.
- Use semantic reconciliation from fresh main; do not rebase, cherry-pick the
  old chain, merge, squash, force-push, rebuild, or create a replacement.
- Preserve the current SEC01 capability/security surfaces and all current-main
  AUTO/workflow/execution-efficiency behavior.
- Candidate freeze is the last candidate mutation. No report, evidence,
  Supervisor, decision-log, or closure commit may follow the frozen subject.
- Run Anvien detect-changes before implementation-slice commits when the
  graph runtime is available. Anvien analysis failed in P0 because the
  isolated disk filled while writing `relations.csv`; record that limitation.
- This is a Python contract/library change with no UI, DB, Docker, provider,
  or external-runtime action. Those checks are N/A with evidence.

## Problem

The previously reviewed candidate is based on `bc686845...`, while fresh
remote/main is `1c84bc...` with three intervening canonical SEC01 commits.
Promoting the old candidate would drop those commits and violate normal
fast-forward topology. The projection contract must be carried forward
without restoring older assumptions or expanding architecture.

## Scope

- Fresh direct fetch and exact SHA/tree authority checks.
- Actual diff and semantic classification of all commits after
  `bc686845fbb5817e50958d91e0d382a72c219b78`.
- Projection-only v2 pin/readiness/materialization behavior already reviewed
  in 01C, reconciled onto fresh main.
- Existing pure host projection, capability registry, C18, C19, FASTPATH,
  AUTO, workflow, and SEC01 surfaces preserved and focused-tested.
- A new projection contract test/spec and planner artifacts committed before
  exact candidate freeze.
- Exact focused Supervisor review, post-review immutability, one conditional
  normal FF push, and fresh post-promotion verification.

## Non-Goals

- No Thiên Hạ projection or mutation.
- No owner checkout, old 01C workspace, unrelated worktree, or user-project
  mutation.
- No new router, registry, context engine, council, transaction engine,
  deployment framework, provider, secret, binary, or runtime installation.
- No img2threejs execution/registration, Tripo activation, network provider
  call, game code, Arena task, or broad unrelated test suite.
- No automatic reconciliation loop after post-review remote drift.

## Requirements

- v1 remains backward compatible; v2 supports exactly `PACKAGED_RUNTIME` and
  `PROJECTION_ONLY`.
- Projection-only readiness is valid without `.p2p/system` and never claims
  executable capability readiness.
- Pure plan remains read-only; one bounded materializer writes only declared
  project-local managed host paths using deterministic hashes, safe collision
  handling, symlink/traversal rejection, atomic writes, bounded rollback, and
  pin-last finalization.
- Existing current-main SEC01 implementation and registry additions remain
  byte/behavior compatible unless a direct import requires an additive change.
- Exact candidate SHA/tree, lineage, focused validation, Supervisor verdict,
  and post-fetch remote equality are recorded.

## Acceptance Criteria

- Fresh main authority is `1c84bc41421dcbe502d40b71fead5022231d0541` /
  `a11a44b676401d8a424db8ed05632c8d22952d26` unless a later fresh fetch proves
  otherwise.
- Each post-base commit has a path-and-semantics classification; no
  `CONFLICTING` or dropped canonical change remains.
- Focused tests pass for projection/security, pin lifecycle negatives, C18,
  C19, FASTPATH, host projection, AUTO, workflow, compile/static validation,
  and `git diff --check`.
- Exact final subject is frozen, independently reviewed as PASS, and remains
  unchanged before promotion.
- Promotion is exactly one normal non-force FF push; post-fetch remote SHA/tree
  exactly equals the reviewed candidate and isolated status is clean.
- IMG2THREEJS execution, Tripo/provider calls, secrets, Thiên Hạ mutations,
  and Owner-worktree mutations remain zero.

## Checklist

- [x] P0-A: Complete actual status before implementation work.
  - Goal: establish fresh remote authority, current tree, post-base commit set,
    relevant SPEC/source state, protected boundaries, and Anvien availability.
  - Work Steps: fetch direct remote, inspect exact SHA/tree and actual diffs,
    read the relevant SPEC cluster and reviewed 01C source, populate the
    matrix and evidence ledger.
  - Implementation Gate: no production edit before actual-status P0 decision.
  - Acceptance: actual status identifies missing/partial/preserve-only and
    blocked tooling surfaces with exact evidence IDs.

### P1: Semantic reconciliation onto fresh current main

- Phase Goal: add only the reviewed projection contract surfaces required on
  fresh main while preserving SEC01 and current execution behavior.
- Phase Boundary:
  - In scope: `project_pin.py`, `project_context.py`, new bounded
    `project_materialization.py`, projection SPEC, and focused contract tests.
  - Out of scope: SEC01 implementation redesign, registry/router replacement,
    reports/old plans, Owner or Thiên Hạ state, and external runtime actions.
  - Dependencies: P0 fresh authority and source/spec review are complete.
- Phase Implementation Rule: do not implement P1 directly. Implement P1-A,
  verify it, refresh actual-status, then P1-B and its evidence.
- Ordered Slice List:
  - P1-A: Reconcile v2 pin/readiness and bounded materializer.
  - P1-B: Add projection contract SPEC and behavior/security tests.

- [ ] P1-A: Reconcile v2 pin/readiness and bounded materializer
  - Goal: carry forward the exact reviewed implementation semantics onto fresh
    main without touching SEC01 paths.
  - Scope Boundary:
    - Editable: the two existing project surfaces and one new materializer.
    - Inspect-only: SEC01 capability model/registry/security adapter/policy.
    - Preserve-only: host projection, C18/C19, FASTPATH, AUTO, workflow,
      Owner/Thiên Hạ paths.
    - Out of scope: architecture expansion and runtime/deployment behavior.
  - Non-Goals: no code copied by blind old-chain replay; no provider/runtime
    claims; no unbounded rollback.
  - Pre-flight Questions:
    - Data source: reviewed 01C source plus current-main files and SPEC cluster.
    - Display permission: N/A; library contract, no UI.
    - DB read flow: N/A; no database.
    - DB write flow: N/A; filesystem writes are the contract under test.
    - Render location: N/A; no UI render.
    - UI behavior flow: N/A; direct Python caller/materializer flow.
    - Docker runtime: N/A; no app runtime.
    - Playwright target: N/A; no browser surface.
    - Behavior test: projection contract and pin lifecycle/security tests.
    - Cleanup/quarantine: all test roots are temporary under repo `.tmp`.
    - External side effects: none; no network/process/provider in materializer.
    - N/A notes: compile/static and direct unittest are the nearest boundary.
  - Work Steps:
    1. Inspect current-main and reviewed-01C diffs, then apply the smallest
       coherent source changes with the reviewed v1/v2 boundary intact.
       - UI flow check: N/A, direct library API is the observable boundary.
       - DB/data flow check: verify pin/filesystem bytes and hashes.
       - Render location check: N/A.
       - Evidence target: `E1-P1A-SRC1..E1-P1A-SRC6`.
    2. Run focused source-level import/compile checks and inspect diff before
       committing the slice; refresh actual status.
       - UI flow check: N/A.
       - DB/data flow check: verify no SEC01 path was overwritten.
       - Render location check: N/A.
       - Evidence target: `E1-P1A-VAL1..E1-P1A-VAL3`.
  - Implementation Gate:
    - Run Anvien file-detail and impact for edited production files if the
      index is available; otherwise retain the P0 disk failure as explicit
      unavailable evidence and use direct diff/import analysis.
    - Preserve current-main SEC01 files byte-for-byte unless an import boundary
      requires an additive compatibility edit.
  - Acceptance:
    - Source: v1 path preserved; v2 modes and safety invariants are explicit.
    - Runtime/UI: N/A; no UI/runtime claim.
    - DB/data: pin-last and managed-file hash binding are source-verifiable.
    - Behavior test: source import/compile and direct contract smoke checks.
    - Cleanup/quarantine: no persistent test target outside `.tmp`.
    - Evidence IDs: `E1-P1A-SRC1..E1-P1A-VAL3`.
    - Actual-status rows refreshed: project pin/context/materializer.
  - Evidence Targets: source diffs, current-main preservation diff, import and
    compile output, and candidate status.
  - Actual-status Update: `partial/missing -> implemented, awaiting focused
    behavioral validation`.
  - Commit Boundary: commit after source acceptance and detect-changes if
    Anvien becomes available; otherwise record unavailable and commit locally.

- [ ] P1-B: Add projection contract SPEC and behavior/security tests
  - Goal: prove the reconciled contract at the nearest real Python boundary.
  - Scope Boundary:
    - Editable: one projection SPEC and one focused test module plus planner
      evidence updates needed before freeze.
    - Inspect-only: current SEC01 tests and C18/C19/AUTO/workflow tests.
    - Preserve-only: all current-main implementation outside projection seam.
    - Out of scope: broad suite and external integrations.
  - Non-Goals: no test-only weakening, mocks presented as provider evidence,
    or runtime-copy behavior.
  - Pre-flight Questions:
    - Data source: public project pin/materializer APIs and pure host plan.
    - Display permission: N/A.
    - DB read/write flow: N/A.
    - Render location/UI flow: N/A.
    - Docker/Playwright: N/A.
    - Behavior test: all required positive and negative security cases.
    - Cleanup/quarantine: isolated temporary project roots; no repo target.
    - External side effects: no providers, network, secrets, or subprocesses.
    - N/A notes: test fixtures may use temporary symlinks when supported.
  - Work Steps:
    1. Add the contract SPEC and focused test module after P1-A source is
       behaviorally coherent.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: N/A.
       - Evidence target: `E1-P1B-SRC1..E1-P1B-SRC3`.
    2. Run projection/security and lifecycle tests; update evidence/status.
       - UI flow check: N/A.
       - DB/data flow check: assert isolated pin/file state after success,
         failure, rerun, tamper, and rollback.
       - Render location check: N/A.
       - Evidence target: `E1-P1B-TEST1..E1-P1B-TEST4`.
  - Implementation Gate: focused test module must prove behavior, not file
    existence; no test may target a protected checkout.
  - Acceptance:
    - Source: SPEC and tests bind exact v1/v2/path/ownership/rollback rules.
    - Runtime/UI: N/A.
    - DB/data: isolated filesystem invariants pass.
    - Behavior test: projection/security and pin lifecycle negatives pass.
    - Cleanup/quarantine: temporary roots are removed by context managers.
    - Evidence IDs: `E1-P1B-SRC1..E1-P1B-TEST4`.
    - Actual-status rows refreshed: SPEC/test/materializer readiness.
  - Evidence Targets: unittest counts/output, negative reason codes, and
    post-test isolated-root status.
  - Actual-status Update: `missing -> present and tested`.
  - Commit Boundary: commit after tests pass and change detection evidence is
    recorded; this is before exact candidate freeze.

### P2: Focused validation and exact freeze

- Phase Goal: validate only affected boundaries, record exact candidate
  identity, and stop all candidate mutation after freeze.
- Phase Boundary:
  - In scope: projection/security, pin lifecycle, C18, C19, FASTPATH, host
    projection, AUTO, workflow, compile/static, diff check, exact identity.
  - Out of scope: Council, giant unrelated suite, reports committed to tree,
    and any implementation change after freeze.
  - Dependencies: P1 slices complete.
- Ordered Slice List:
  - P2-A: Run focused validation and freeze final candidate SHA/tree.
  - P2-B: Focused exact-subject Supervisor review and immutability check.

- [ ] P2-A: Run focused validation and freeze final candidate SHA/tree
  - Goal: establish all promotion-critical evidence on a clean exact subject.
  - Scope Boundary: affected Python modules/tests and git identity only.
  - Work Steps: run required modules separately, compile/static validation,
    `git diff --check`, verify invariant fields, commit intended code/spec/test
    changes, record final SHA/tree, and freeze.
  - Implementation Gate: all material failures stop promotion; no broad suite
    without a recorded invariant-based reason.
  - Acceptance: every required result is PASS, candidate clean, exact SHA/tree
    recorded, and external capability counters remain zero.
  - Evidence Targets: `E2-P2A-TEST1..E2-P2A-ID3`.
  - Actual-status Update: all required projection rows become `correct` only
    after behavioral evidence.
  - Commit Boundary: final candidate commit is the last candidate mutation.

- [ ] P2-B: Focused exact-subject Supervisor review and immutability check
  - Goal: obtain exactly one independent Supervisor PASS against frozen SHA and
    tree, then prove no source/spec/test/candidate mutation.
  - Scope Boundary: exact candidate, reconciliation diff, tests/evidence, and
    candidate cleanliness; no code changes after review starts.
  - Work Steps: create Supervisor request/report outside candidate tree, verify
    exact values and post-review hashes/status, and stop on REJECT.
  - Implementation Gate: no candidate mutation or second review subject.
  - Acceptance: exact Supervisor PASS and unchanged candidate SHA/tree.
  - Evidence Targets: `E2-P2B-SUP1..E2-P2B-IMM4`.
  - Actual-status Update: candidate becomes `reviewed/frozen`.
  - Commit Boundary: no post-review candidate commit is allowed.

### P3: Conditional promotion and post-fetch proof

- Phase Goal: promote only when fresh remote/main is an ancestor of the exact
  reviewed candidate and then verify the exact remote result.
- Phase Boundary:
  - In scope: fresh fetch, merge-base/ancestry/FF checks, one normal push,
    fresh post-promotion fetch and clean status.
  - Out of scope: reconciliation loop, merge/rebase/squash/cherry-pick/force
    push, reports/evidence commit, and follow-on projects.
  - Dependencies: P2-B PASS and no post-review mutation.
- [ ] P3-A: Fresh pre-promotion check, one FF push, and post-fetch verification
  - Goal: perform the authorized external mutation only under all gates.
  - Work Steps: fetch direct remote, compare SHA/tree/ancestry, fast-forward
    isolated main exactly, push once non-force, fetch again, verify equality
    and clean status.
  - Acceptance: promotion verified or exact drift block reported; no fallback.
  - Evidence Targets: `E3-P3A-REMOTE1..E3-P3A-REMOTE6`.

## Risk Notes

- Remote drift after review is a hard stop unless exact reviewed candidate is
  still a direct FF descendant; no second reconciliation in this task.
- Anvien graph evidence is unavailable if disk pressure recurs; this affects
  tooling confidence only and cannot be converted to PASS.
- Existing SEC01 changes touch capability registry/orchestration surfaces; a
  semantic preservation diff is mandatory even though paths do not overlap.
- The exact candidate identity, not equivalent contents or a later report,
  controls promotion.
