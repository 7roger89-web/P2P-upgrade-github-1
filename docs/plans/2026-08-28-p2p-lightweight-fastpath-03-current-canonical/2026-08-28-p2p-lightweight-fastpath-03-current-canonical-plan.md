# P2P-LIGHTWEIGHT-FASTPATH-03 Current-Canonical Reconciliation and Clean Verification Plan

## Metadata

- Date: `2026-08-28`
- Status: `P2-A/P2-B/P2-C complete; candidate stopped at Owner gate`
- Plan: `docs/plans/2026-08-28-p2p-lightweight-fastpath-03-current-canonical/2026-08-28-p2p-lightweight-fastpath-03-current-canonical-plan.md`
- Evidence: `docs/plans/2026-08-28-p2p-lightweight-fastpath-03-current-canonical/2026-08-28-p2p-lightweight-fastpath-03-current-canonical-evidence.md`
- Benchmark: `docs/plans/2026-08-28-p2p-lightweight-fastpath-03-current-canonical/2026-08-28-p2p-lightweight-fastpath-03-current-canonical-benchmark.md`
- Actual status: `docs/plans/2026-08-28-p2p-lightweight-fastpath-03-current-canonical/2026-08-28-p2p-lightweight-fastpath-03-current-canonical-actual-status.md`

## Goal

Reconcile the FASTPATH-02 workflow bridge against current `origin/main`, reuse the already-promoted EFF01 C18 policy behavior, and produce a new clean isolated candidate only for the minimum C18/C19 workflow wiring that is still absent. Validate the seven required scenarios from a non-`.tmp` path and stop at the Owner gate without promotion or merge.

## Rules

- Complete P0 actual status before implementation work.
- Treat current remote `origin/main` as the authority; do not infer it from the old candidate or a dirty Owner checkout.
- Reuse current EFF01 execution lanes, JIT skill projection, test ceilings, proportional verification, and stop behavior; do not duplicate them in workflow code.
- Keep `.p2p/system/p2p_capabilities/orchestration_policy.py`, `context.py`, routing, quorum, governance, Owner state, and EFF01 tests preserve-only unless fresh evidence proves a contract defect.
- Use only the existing single router, existing C18 `derive_requirement`, and existing C19 retrieval/escalation primitives.
- Do not repair, reset, clean, stash, delete, rebase, merge, promote, push, deploy, or modify the Owner dirty canonical checkout.
- Keep all verification logs under the candidate's repo-local `.tmp` directory.
- Run Anvien analysis before graph queries, file-detail/impact before editing, and detect-changes before implementation commits.
- For this non-UI Python seam, full build is `python -m compileall -q .p2p/system scripts tests`; Docker and Playwright are not applicable.
- A clean candidate status is mandatory. If unrelated line-ending/tooling noise appears, create a correctly configured fresh candidate rather than normalizing or deleting it.

## Problem

FASTPATH-02 was implemented against the pre-EFF01 base and left a dirty `.tmp` candidate. Current canonical main now contains EFF01 commits that materially extend C18 with four execution lanes, JIT skill projection, validation ceilings, and stop rules. Current `scripts/p2p_workflow.py` still lacks the task-to-C18 bridge and only has an earlier C19 adapter without bounded escalation/result exposure. A clean semantic replay is required; a mechanical patch replay could duplicate or bypass EFF01 behavior.

## Scope

- Verify current live `origin/main` SHA/tree, ancestry, intervening commits, and EFF01 status.
- Reconcile every FASTPATH-02 source change against current canonical behavior.
- Edit only `scripts/p2p_workflow.py` for the workflow bridge and add one focused behavior test file for FASTPATH-03.
- Reuse current C18 fields including `source_mutation`, `runtime_change`, `acceptance_requires_testing`, `owner_gate`, and current lane/test-ceiling projections.
- Strengthen the existing workflow C19 adapter with explicit required-source bindings and one bounded escalation through `escalate_task_context`.
- Emit inspectable orchestration/context/verification metadata through existing workflow result, manifest, ledger, and status surfaces.
- Produce candidate-only plan/evidence/benchmark/status/report artifacts required by the project workflow and bind them to the candidate commit.

## Non-Goals

- No edit to canonical `D:\AI\P2P_dev\P2P-canonical-runtime-01` or the incomplete source root.
- No change to current C18 policy, C19 primitive, router, quorum denominator, governance, permissions, provider/model resolution, worker executor, Prompt Composer, `/quick-prompt`, Control Tower, or game-specific subsystem.
- No EFF01 reimplementation, second test ceiling, second escalation engine, load-everything fallback, or new worker framework.
- No automatic external/upstream integration, promotion, merge, push, deploy, or release.
- No broad full-repository suite without a new material failure that justifies it.

## Requirements

- Current `origin/main` is read directly and its tree/ancestry are recorded.
- The four EFF01 commits between `230769...` and current main are classified, including exact touched paths.
- FASTPATH-02 changes are classified as `STILL_REQUIRED`, `ALREADY_PRESENT`, `SUPERSEDED`, `CONFLICTING`, or `STALE`.
- Prompt composition and read-only transformation select C18 `DIRECT`, `MINIMAL`, `LOW`, `DETERMINISTIC`, zero delegated workers, no default quorum/council, and a narrow verification surface.
- Local implementation maps to the current C18 mutation/test signals and one existing worker role.
- System design remains architecture/high-reasoning and is not classified as trivial composition.
- High-impact architecture and external upstream integration remain Owner/high-risk fail-closed.
- Insufficient context invokes at most one current C19 tier escalation and never loads everything.
- Existing explicit full quorum behavior remains `8/8` and is not lowered.
- Candidate status after commit contains only intentional candidate state.

## Acceptance Criteria

- Seven-scenario matrix passes on current canonical lineage: prompt, transformation, implementation, system design, high-impact architecture, upstream integration, and insufficient context.
- Current EFF01 focused tests, C18/C19 tests, workflow tests, smallest relevant neighboring regression set, and both formerly path-sensitive tests pass from a non-`.tmp` path, except any newly evidenced unrelated limitation is recorded explicitly.
- `git diff --check` and Python compile/static validation pass.
- Candidate commit/tree are exact and based on current `origin/main`; no Owner state is changed.
- Independent Supervisor review returns exactly `PASS` if governance requires it, or the plan records the explicit reason it was not required.
- Final verdict is one of the three task-approved FASTPATH-03 values and never `PROMOTED`.

## Checklist

- [x] P0-A: Complete current-canonical actual status and reconciliation preflight.
  - Goal: establish live authority, EFF01 lineage, old-candidate delta, clean candidate boundary, and the exact remaining work.
  - Work Steps: verify live `ls-remote`; inspect current canonical refs/tree/ancestry; inspect intervening EFF01 commits and current source/specs; compare FASTPATH-02 paths and behavior; create a correctly configured neutral candidate; refresh Anvien; run baseline focused tests and record status.
  - Implementation Gate: actual-status has evidence IDs, impact/file-detail evidence, classifications, and a P0 decision before source editing.
  - Acceptance: current EFF01 policy is preserve-only/correct, workflow bridge is partial/unbound, candidate status is clean, and P1 is limited to the missing bridge plus focused tests.

### P1: Replay only the missing current-canonical workflow bridge

- Phase Goal: connect existing workflow classification to current C18 and C19 primitives without changing either primitive.
- Phase Boundary:
  - In scope: `scripts/p2p_workflow.py` and one direct FASTPATH-03 test file.
  - Out of scope: C18 policy module, C19 context module, router/quorum, executor, governance, release, promotion, and unrelated tests.
  - Dependencies: P0 current-main reconciliation, clean candidate, current C18 EFF01 API, current C19 API.
- Phase Implementation Rule: do not implement P1 directly. Implement P1-A, verify and commit it, refresh actual-status, then implement P1-B and verify/commit it.
- Ordered Slice List:
  - P1-A: Add the minimum current-C18/C19 workflow adapter.
  - P1-B: Add focused current-canonical FASTPATH-03 behavior tests.

- [x] P1-A: Add the minimum current-C18/C19 workflow adapter
  - Goal: make the existing workflow derive one current C18 requirement, use C19 targeted retrieval with one bounded escalation, and expose proportional metadata without duplicating EFF01 policy.
  - Scope Boundary:
    - Editable: `scripts/p2p_workflow.py`.
    - Inspect-only: `.p2p/system/p2p_capabilities/orchestration_policy.py`, `.p2p/system/p2p_capabilities/context.py`, routing/quorum, EFF01 tests, current workflow consumers.
    - Preserve-only: current C18 lane/JIT/test-ceiling logic, C19 primitive, canonical eight identities, full quorum, governance and Owner boundaries.
    - Out of scope: worker execution, external I/O, host runtime, release and promotion.
  - Non-Goals: no second policy, second router, second retriever, or fake worker execution.
  - Pre-flight Questions:
    - Data source: request/inspection signals mapped to current `TaskProfile` fields.
    - Display permission: structured workflow metadata only; no permission or approval grant.
    - DB read flow: N/A; existing filesystem state only.
    - DB write flow: N/A for production code; workflow's existing project-state writes remain unchanged.
    - Render location: existing result/status/ledger/context-manifest surfaces.
    - UI behavior flow: N/A; CLI/Python workflow seam.
    - Docker runtime: N/A; standard-library Python change.
    - Playwright target: N/A; no public UI behavior.
    - Behavior test: direct workflow fixture calls plus current C18/C19 regression tests.
    - Cleanup/quarantine: all workflow fixture state remains under repo-local `.tmp` test parents.
    - External side effects: none; `allow_external=False` is explicit.
    - N/A notes: no actual worker executor exists in this workflow; selection metadata must remain honest.
  - Work Steps:
    1. Add the workflow-to-C18 bridge and map current EFF01 materiality/test signals without editing policy code.
       - UI flow check: N/A; verify structured result.
       - DB/data flow check: N/A; verify no new persistent authority source.
       - Render location check: N/A; result/contract surfaces only.
       - Mini QA: run compile and direct C18 bridge smoke after the edit.
       - Evidence target: source lines, current C18 output, and Anvien impact evidence.
    2. Extend the existing C19 adapter with explicit required bindings, one escalation ceiling, and fail-closed invalid retrieval handling; add result/ledger/manifest projection helpers.
       - UI flow check: N/A.
       - DB/data flow check: verify required source IDs are not silently intersected away.
       - Render location check: N/A.
       - Mini QA: run direct C19 insufficiency/escalation and workflow fixture checks.
       - Evidence target: C19 status/coverage/escalation outputs and diff check.
  - Implementation Gate:
    - P0 is complete.
    - Existing current EFF01 API is confirmed additive and the FASTPATH-02 policy edits are classified as already present/superseded.
    - Anvien file-detail/impact evidence for the high-fan-in workflow is recorded.
  - Acceptance:
    - Source: workflow calls current `derive_requirement`, `retrieve_task_context`, and `escalate_task_context`; no new policy/router.
    - Runtime/UI: N/A.
    - DB/data: required bindings fail closed; no load-all fallback.
    - Behavior test: direct smoke and C19 edge checks pass.
    - Cleanup/quarantine: only intended source changes are staged.
    - Evidence IDs: `E1-P1A-SRC1`, `E1-P1A-IMPL1`, `E1-P1A-TEST1`.
    - Actual-status rows refreshed: workflow adapter `partial -> bound-correct`; C18/C19 primitives remain preserve-only.
  - Evidence Targets: `E1-P1A-SRC1..E1-P1A-TEST1`.
  - Actual-status Update: append R1 with source status transition and current C18/C19 compatibility result.
  - Commit Boundary: commit after direct smoke, compile, and diff check.

- [x] P1-B: Add focused current-canonical FASTPATH-03 behavior tests
  - Goal: prove the seven required scenarios against the current C18/C19 runtime, including EFF01 lane/test-ceiling reuse and fail-closed boundaries.
  - Scope Boundary:
    - Editable: `tests/test_p2p_lightweight_fastpath.py`.
    - Inspect-only: current EFF01 policy tests, frozen C18/C19 tests, and workflow tests.
    - Preserve-only: existing C18/C19 fixtures and current EFF01 acceptance matrix.
    - Out of scope: broad test rewrites and unrelated baseline failures.
  - Non-Goals: no test-local policy implementation, no simulated quorum, no production state mutation.
  - Pre-flight Questions:
    - Data source: actual imported workflow and current C18/C19 modules.
    - Display permission: assertions only.
    - DB read/write flow: N/A; isolated fixture roots.
    - Render location: N/A.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: `python -m unittest tests.test_p2p_lightweight_fastpath -v`.
    - Cleanup/quarantine: fixture roots under repo-local `.tmp`; no tracked state writes.
    - External side effects: none.
    - N/A notes: test uses non-`.tmp` candidate checkout but temporary project fixtures remain repo-local as required.
  - Work Steps:
    1. Add direct C18 bridge assertions for prompt, transformation, implementation, design, high-impact, upstream, explicit quorum, and current EFF01 lane/JIT/test-ceiling fields.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: N/A.
       - Mini QA: focused suite immediately after adding behavior tests.
       - Evidence target: `E1-P1B-TEST1`.
    2. Add direct C19 missing-binding, one-escalation, ceiling, and workflow receipt/ledger assertions.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: N/A.
       - Mini QA: rerun focused suite and compile.
       - Evidence target: `E1-P1B-TEST2`.
  - Implementation Gate:
    - P1-A source behavior is present and direct smoke passes.
    - Tests call the actual current policy/context modules through workflow seams.
  - Acceptance:
    - Source: focused test imports current workflow and C18/C19, not a copied policy.
    - Runtime/UI: N/A.
    - DB/data: fixtures do not touch Owner/release paths.
    - Behavior test: all FASTPATH-03 focused cases pass.
    - Cleanup/quarantine: candidate tracked status lists only intended files before commit.
    - Evidence IDs: `E1-P1B-TEST1`, `E1-P1B-TEST2`.
    - Actual-status rows refreshed: test coverage `missing -> bound-correct`.
  - Evidence Targets: `E1-P1B-TEST1..E1-P1B-TEST2`.
  - Actual-status Update: append R2 with exact focused count and any failure classification.
  - Commit Boundary: commit after focused tests pass and detect-changes is run.

### P2: Proportional current-canonical verification

- [x] P2-A: Run the proportional validation ceiling
  - Goal: verify source and behavior at the smallest level that proves the workflow seam.
  - Work Steps: run focused FASTPATH suite; current EFF01/C18/C19 suites; relevant workflow tests; smallest routing/context neighbors; both previous path-sensitive tests outside `.tmp`; compile; diff check; record any failure with exact test and reason.
  - Implementation Gate: P1-A and P1-B committed; candidate path is neutral and status is intentional-only.
  - Acceptance: required validation commands and path-sensitive checks pass, or a concrete unrelated limitation is recorded without broad expansion.

- [x] P2-B: Independent Supervisor review when required by current governance
  - Goal: independently review current lineage, no EFF01 duplication, seven-scenario behavior, high-risk protection, bounded context, and candidate cleanliness.
  - Work Steps: inspect final source/diff first; check reports and fresh validation; verify no Owner mutation or promotion; write exactly `PASS` or `REJECT` in the Supervisor report.
  - Implementation Gate: P2-A evidence and detect-changes are current.
  - Acceptance: Supervisor report exists if required and returns `PASS`, or the plan records a truthful governance reason it was not required.

- [x] P2-C: Close the candidate at the Owner gate
  - Goal: bind final SHA/tree, files, cleanliness, limitations, and terminal verdict.
  - Work Steps: refresh actual-status/evidence/benchmark; run final status/diff identity checks; commit only intended artifacts; confirm canonical remains untouched; stop without promotion.
  - Implementation Gate: P2-A and P2-B pass or record an explicit limitation.
  - Acceptance: final report has all 18 requested items, exact candidate identity, clean status, and one approved FASTPATH-03 terminal verdict.

### Final closure

- P2-A proportional validation passed: focused FASTPATH `18/18`, current EFF01/C18/C19/foundation `61/61`, workflow/path-sensitive `8/8`, compile/static checks, diff check, and fresh Anvien analysis.
- P2-B Supervisor review passed in `reports/supervisor/rp_supervisor_260828_194313_by_gpt-5-codex_p2p-lightweight-fastpath-03.md`.
- P2-C closes the isolated candidate at the Owner gate. The implementation checkpoint is `82d6bffc9c6e596d2b8270679db1a7ee2fc80ee6` with tree `1011ccf931445e5f645de2ec56cc7509c871a87a`; the final closure checkpoint is the commit containing this evidence update.
- No promotion, merge, push, deploy, Owner approval, or canonical checkout mutation occurred.

## Risk Notes

- `scripts/p2p_workflow.py` has high Anvien fan-in and many unresolved graph references; this is a scope warning, not permission to widen the patch.
- The hidden `.p2p` policy/context files may not resolve uniquely in Anvien's duplicate registry; direct source and behavior evidence remain required.
- EFF01 is current canonical behavior. Duplicating its lanes, JIT selection, or test ceilings would create policy drift and is forbidden.
- The workflow still has no worker executor; selected worker counts are honest route metadata, not live execution proof.
- The canonical Owner checkout remains dirty and is preserve-only. Candidate technical readiness is not Owner approval, promotion, release, or deployment authority.
