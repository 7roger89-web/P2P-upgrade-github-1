# P2P-BG01 Current-Canonical Reconciliation Plan

## Metadata

- Date: 2026-08-28
- Status: complete - ready for Owner gate
- Plan: docs/plans/2026-08-28-p2p-bg01-current-canonical-reconciliation/2026-08-28-p2p-bg01-current-canonical-reconciliation-plan.md
- Evidence: docs/plans/2026-08-28-p2p-bg01-current-canonical-reconciliation/2026-08-28-p2p-bg01-current-canonical-reconciliation-evidence.md
- Benchmark: docs/plans/2026-08-28-p2p-bg01-current-canonical-reconciliation/2026-08-28-p2p-bg01-current-canonical-reconciliation-benchmark.md
- Actual status: docs/plans/2026-08-28-p2p-bg01-current-canonical-reconciliation/2026-08-28-p2p-bg01-current-canonical-reconciliation-actual-status.md

## Goal

Create one new isolated candidate from current canonical 34ece1d1, reconcile the old BG01 product-intake intent into the current lightweight-fastpath workflow without mechanically replacing current workflow code, and stop at a fresh Owner gate.

## Rules

- Complete P0 actual status before implementation work.
- Preserve current canonical lightweight-fastpath behavior.
- Reuse the existing router, Goal Contract, Task State, Control Tower, Execution Ledger, and existing policy seams.
- Do not create a second router, orchestrator, provider layer, truth store, or certification system.
- Keep automatic_start false and protected actions fail closed.
- Run only the user-authorized focused validation matrix.
- Do not run Anvien, full repository regression, promotion, push, deployment, or live activation.
- Record evidence and measured counts as work completes.
- Use a separate checkpoint commit for each verified implementation slice.

## Problem

The approved BG01 candidate 86def933 was based on 28a85bc and cannot be promoted because current canonical main advanced through the lightweight-fastpath commits 82d6bffc and 34ece1d. The current canonical workflow has a materially overlapping scripts/p2p_workflow.py implementation, so the old script must be semantically reconciled rather than copied over it.

## Scope

In scope:

- New candidate based exactly on current canonical 34ece1d1 / b3f541df.
- Porting the old BG01 gateway module and focused product-behavior tests where valid.
- Integrating one bounded Beginner entrypoint into the existing workflow and CLI.
- Preserving and testing current lightweight-fastpath behavior.
- Reusing current state, recovery, policy, and safety surfaces.

Out of scope:

- Changes to canonical checkout or remote main.
- Promotion, push, deployment, live activation, release, or Owner approval.
- HOST01, SKILL01, EXEC01, REC01, COUNCIL01, provider installation, or new orchestration.
- Reimplementation of current C18/C19/lightweight-fastpath policy.
- Full repository regression or Anvien.

## Requirements

- Ordinary Vietnamese and English requests enter in BEGINNER mode.
- New versus existing project state is inferred from request and project evidence.
- Only material ambiguity produces a product-level question.
- The internal charter contains outcome, type, state, criteria, constraints, workstreams, and safe next action.
- Default output hides technical implementation detail; Advanced output preserves it.
- Beginner statuses remain ĐANG LÀM, ĐÃ XONG, and CẦN BẠN QUYẾT ĐỊNH.
- Durable state is written through the existing Goal Contract, Task State, Control Tower, and Execution Ledger.
- No execution starts automatically.
- Existing Owner, security, production, promotion, provenance, rollback, and fail-closed boundaries remain unchanged.

## Acceptance Criteria

1. Vietnamese new-project intake passes through Beginner mode.
2. Existing-project improvement is recognized without a technical question.
3. A concise structured charter is generated and bound to existing durable state.
4. Material ambiguity produces one beginner-facing product question.
5. Technical detail is hidden by default and available only through Advanced projection.
6. Current lightweight-fastpath focused tests remain green.
7. Relevant EFF01 and safety smoke checks remain green.
8. The final candidate has exact base 34ece1d1, a clean state, and no promotion action.

## Checklist

- [x] P0-A: Complete actual status before implementation work.
  - Goal: bind the target to current canonical evidence.
  - Work Steps: verify current remote SHA/tree, inspect the clean current-canonical worktree, inspect the old BG01 delta, classify the shared workflow path, and record preserve-only surfaces.
  - Implementation Gate: actual-status has current lineage, target status, evidence IDs, and a downstream decision.
  - Acceptance: current canonical is exact and clean in the source worktree; old BG01 is evidence-only; implementation scope is narrow.

### P1: Reconcile and verify the isolated candidate

- Phase Goal: integrate BG01 into current canonical while preserving fastpath.
- Phase Boundary:
  - In scope: beginner gateway module, existing workflow bridge, CLI entrypoint, focused tests, and candidate evidence.
  - Out of scope: canonical/remote writes, policy rewrites, new orchestration, and unrelated cleanup.
  - Dependencies: P0 current status, old BG01 source checkpoint, current fastpath source, and existing C18/C19 contracts.
- Phase Implementation Rule: implement P1-A, verify and checkpoint it; then implement P1-B, verify and checkpoint it; finish with P1-C focused validation.
- Ordered Slice List:
  - P1-A: Add the non-overlapping BG01 gateway and focused behavior tests.
  - P1-B: Bind one BG01 entrypoint into the current workflow and CLI without replacing fastpath.
  - P1-C: Run the focused reconciliation validation matrix.

- [x] P1-A: Add the non-overlapping BG01 gateway and focused behavior tests
  - Goal: preserve the old gateway contract in new files that do not overlap current canonical source.
  - Scope Boundary:
    - Editable: .p2p/system/p2p_capabilities/beginner_gateway.py and tests/test_p2p_bg01_beginner_gateway.py.
    - Inspect-only: current C18/C19 modules, current fastpath tests, and old BG01 script integration.
    - Preserve-only: current canonical workflow and all safety/governance files.
    - Out of scope: router/policy changes and test expansion beyond BG01 behavior.
  - Non-Goals: no host start, provider selection, package installation, or external side effect.
  - Pre-flight Questions:
    - Data source: owner request plus existing project inspection.
    - Display permission: beginner projection by default; advanced only on explicit request.
    - DB read flow: N/A; project-local JSON/task state only.
    - DB write flow: N/A; state binding is performed in P1-B through existing stores.
    - Render location: existing workflow CLI output.
    - UI behavior flow: CLI request to structured beginner projection.
    - Docker runtime: N/A; Python CLI scope has no container runtime.
    - Playwright target: N/A; no UI surface.
    - Behavior test: test_p2p_bg01_beginner_gateway.py.
    - Cleanup/quarantine: every test uses a temporary directory under candidate .tmp.
    - External side effects: none.
    - N/A notes: source is local standard-library runtime.
  - Work Steps:
    1. Add the old BG01 gateway module through apply_patch and verify its public contract.
       - UI flow check: N/A; verify public projection shape.
       - DB/data flow check: verify no persistence is performed by the pure gateway.
       - Render location check: verify render_beginner remains product-language only.
       - Evidence target: E1-P1A-SRC1 and E1-P1A-TEST1.
    2. Add focused tests for Vietnamese, English, existing-project, ambiguity, projection, safety, and empty input behavior.
       - UI flow check: N/A; CLI and callable entrypoint are the user boundary.
       - DB/data flow check: temporary roots only.
       - Render location check: verify no technical fields appear in default projection.
       - Evidence target: E1-P1A-TEST2.
  - Implementation Gate:
    - Current candidate is clean at 34ece1d and target files are absent.
    - Old BG01 files are read-only evidence/source material.
    - No current fastpath file is overwritten.
  - Acceptance:
    - Source: gateway module matches the bounded old contract.
    - Runtime/UI: N/A; public projection is verifiable through callable/CLI tests.
    - DB/data: temporary state only and no gateway-side persistent write.
    - Behavior test: focused gateway tests pass.
    - Cleanup/quarantine: temporary roots are isolated and removed by context managers.
    - Evidence IDs: E1-P1A-SRC1, E1-P1A-TEST1, E1-P1A-TEST2.
    - Actual-status rows refreshed: gateway missing -> present; focused tests missing -> present.
  - Evidence Targets: new-file content, import check, focused test result, and diff scope.
  - Actual-status Update: record new gateway/test files and preserve-only current fastpath.
  - Commit Boundary: checkpoint after focused tests pass.

- [x] P1-B: Bind one BG01 entrypoint into the current workflow and CLI without replacing fastpath
  - Goal: make the new gateway usable while reusing current policy and durable state.
  - Scope Boundary:
    - Editable: scripts/p2p_workflow.py only at the smallest loader, entrypoint, projection, CLI, and integration seams.
    - Inspect-only: .p2p/system/p2p_capabilities/orchestration_policy.py, context.py, task_state.py, control_tower_handoff.py, and current fastpath tests.
    - Preserve-only: current C18/C19 policy implementation and all existing fastpath branches.
    - Out of scope: second router/orchestrator/provider/truth store, policy duplication, and unrelated refactors.
  - Non-Goals: no automatic execution, no live worker execution, and no canonical mutation.
  - Pre-flight Questions:
    - Data source: existing inspect_project plus gateway charter.
    - Display permission: beginner_public_result default; advanced=True only when requested.
    - DB read flow: existing Goal Contract and TaskStateStore.
    - DB write flow: existing write_goal, TaskStateStore.initialize/record_event, and Control Tower recommendation.
    - Render location: existing parser/main beginner command and existing result surfaces.
    - UI behavior flow: request -> inspect -> charter -> existing state binding -> safe projection.
    - Docker runtime: N/A; no web/container boundary.
    - Playwright target: N/A.
    - Behavior test: BG01 tests plus directly affected workflow tests.
    - Cleanup/quarantine: tests use temporary project roots; candidate evidence remains isolated.
    - External side effects: no network/provider/host action.
    - N/A notes: current fastpath selection remains delegated to C18.
  - Work Steps:
    1. Add the minimal capability loader and BG01 entrypoint around existing workflow helpers.
       - UI flow check: N/A; CLI projection is the user-visible boundary.
       - DB/data flow check: verify existing state is reused and conflicting state is not overwritten.
       - Render location check: verify existing lightweight result fields remain unchanged.
       - Evidence target: E1-P1B-SRC1 and E1-P1B-TEST1.
    2. Add only the beginner CLI dispatch and public projection binding.
       - UI flow check: verify default and advanced output paths.
       - DB/data flow check: verify automatic_start remains false and recovery uses existing Control Tower.
       - Render location check: verify technical details are absent by default.
       - Evidence target: E1-P1B-TEST2 and E1-P1B-DIFF1.
  - Implementation Gate:
    - P1-A checkpoint passes.
    - Current fastpath functions remain present and their existing tests are not edited unless a direct compatibility assertion is required.
    - The BG01 integration has no new state authority.
  - Acceptance:
    - Source: one bounded entrypoint calls existing state/policy surfaces.
    - Runtime/UI: CLI beginner request returns a structured product response.
    - DB/data: Goal Contract, Task State, and ledger references are existing surfaces.
    - Behavior test: BG01 and directly affected workflow tests pass.
    - Cleanup/quarantine: no test state escapes temporary roots.
    - Evidence IDs: E1-P1B-SRC1, E1-P1B-TEST1, E1-P1B-TEST2, E1-P1B-DIFF1.
    - Actual-status rows refreshed: workflow seam partial -> bound-correct; fastpath preserve-only remains correct.
  - Evidence Targets: semantic diff, focused workflow tests, and fastpath-preservation result.
  - Actual-status Update: record the exact integration seam and unchanged fastpath surfaces.
  - Commit Boundary: checkpoint after directly affected tests pass.

- [x] P1-C: Run the focused reconciliation validation matrix
  - Goal: close BG01 acceptance, fastpath preservation, and relevant EFF01 safety evidence.
  - Scope Boundary:
    - Editable: none; validation-only.
    - Inspect-only: changed source, focused tests, current fastpath tests, and EFF01 smoke tests.
    - Preserve-only: canonical and remote authority.
    - Out of scope: full regression, Anvien, promotion, and deployment.
  - Non-Goals: no broad baseline investigation.
  - Pre-flight Questions:
    - Data source: candidate checkout.
    - Display permission: evidence remains internal to candidate report.
    - DB read flow: temporary test roots only.
    - DB write flow: N/A beyond test quarantine.
    - Render location: test output and candidate report.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: BG01, directly affected workflow, lightweight-fastpath, and EFF01 smoke.
    - Cleanup/quarantine: confirm no persistent test output in candidate.
    - External side effects: none.
    - N/A notes: no Anvien per explicit user boundary.
  - Work Steps:
    1. Run exactly the focused test commands and record pass counts.
       - UI flow check: N/A.
       - DB/data flow check: inspect temporary-root cleanup.
       - Render location check: inspect CLI JSON/text assertions.
       - Evidence target: E1-P1C-TEST1.
    2. Verify exact candidate base/tree, source diff, fastpath markers, and clean state.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: N/A.
       - Evidence target: E1-P1C-ID1 and E1-P1C-SAFETY1.
  - Implementation Gate:
    - P1-B checkpoint exists and no required focused test is skipped.
  - Acceptance:
    - Source: changed files are limited to BG01 and the bounded workflow seam.
    - Runtime/UI: N/A.
    - DB/data: state safety assertions pass.
    - Behavior test: all user-authorized focused groups pass.
    - Cleanup/quarantine: candidate has no accidental test artifacts.
    - Evidence IDs: E1-P1C-TEST1, E1-P1C-ID1, E1-P1C-SAFETY1.
    - Actual-status rows refreshed: all acceptance rows are correct or explicitly blocked.
  - Evidence Targets: focused results, identity, safety, and status.
  - Actual-status Update: mark P1 complete only if all required focused evidence passes.
  - Commit Boundary: no extra implementation commit; retain P1-B checkpoint as final source checkpoint.

- [x] Pn-A: Call supervisor for the implemented-plan acceptance loop.
  - Goal: independently review the completed candidate and evidence.
  - Work Steps: call the supervisor skill once after P1; if it rejects, stop at the responsible correction boundary.
  - Implementation Gate: P1 is complete or explicitly blocked.
  - Acceptance: supervisor result is recorded without promoting or deploying.
  - Actual Result: independent review recorded `PASS` in `reports/supervisor/rp_supervisor_260828_215128_by_gpt-5-codex_p2p-bg01-current-canonical-reconciliation.md`.

- [x] Pn-B: Remove dead work created during this plan.
  - Goal: ensure only accepted candidate artifacts remain.
  - Work Steps: inspect status/diff and remove only plan-created dead artifacts; do not touch old candidate or canonical.
  - Implementation Gate: no unrelated files are in scope.
  - Acceptance: final candidate diff has no dead work.
  - Actual Result: only the bounded BG01 source/test, surgical workflow seam, and candidate-only evidence artifacts remain; no duplicate candidate or transient test artifact remains.

- [x] Pn-C: Close the plan.
  - Goal: record final identity, focused validation, candidate commit/tree, and Owner gate boundary.
  - Work Steps: update evidence/benchmark/actual-status, perform final read-only identity checks, and commit the candidate evidence if needed.
  - Implementation Gate: Pn-A and Pn-B pass or have explicit blockers.
  - Acceptance: exact new candidate SHA/tree and no promotion are reported.
  - Actual Result: source checkpoint is `1012428798ed43027d24ba57b7551321ee5e15fe` / `84a612c17f413df5e967f4a3dad7a8d01f286ea2`; final closure commit identity is verified and returned after the evidence-only close.

## Risk Notes

- scripts/p2p_workflow.py is high fan-in and is the only material overlap; changes must stay surgical.
- The old candidate is dirty/evidence-only and must not be used as a working base.
- Current canonical checkout used as source must remain untouched.
- No live host/provider/quorum claim is made by this candidate.
