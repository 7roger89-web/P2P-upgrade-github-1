# P2P-GOVREC02 Governance Source Anchor Contract Correction Plan

## Metadata

- Date: `2026-08-26`
- Status: `P1-B Complete / P2-A Complete / P2-B Ready`
- Plan: `docs/plans/2026-08-26-p2p-govrec02-source-anchor-contract/2026-08-26-p2p-govrec02-source-anchor-contract-plan.md`
- Evidence: `docs/plans/2026-08-26-p2p-govrec02-source-anchor-contract/2026-08-26-p2p-govrec02-source-anchor-contract-evidence.md`
- Benchmark: `docs/plans/2026-08-26-p2p-govrec02-source-anchor-contract/2026-08-26-p2p-govrec02-source-anchor-contract-benchmark.md`
- Actual status: `docs/plans/2026-08-26-p2p-govrec02-source-anchor-contract/2026-08-26-p2p-govrec02-source-anchor-contract-actual-status.md`

## Goal

Replace the ambiguous `authority.current_promoted_source` projection with one explicit `authority.promoted_source_anchor` contract. The anchor records the exact promoted implementation source against which the governance reconciliation was evaluated; dynamically observed `HEAD` and `origin/main` remain separate runtime facts. The validator must accept equal/descendant governance overlays, reject divergence and malformed authority, and never require a committed file to contain its own future Git SHA.

## Rules

- Complete and record P0 actual status before implementation.
- Preserve the historical `.19` official artifact, its SHA-256, approval, and reports.
- Preserve the `.74`/GOVREC01 successor as unpromoted; this correction does not promote or release anything.
- Use one existing authority projection. Do not create a second governance subsystem or duplicate authority truth.
- Use `promoted_source_anchor` with explicit semantic type, purpose, observed ref, anchor commit/tree, verification date, and descendant lineage policy.
- Observe current Git state dynamically when validating a real repository. Do not persist `HEAD` or `origin/main` as an implied forever-current value.
- Do not store a candidate's own commit SHA in that candidate's committed governance file.
- Keep `HEAD_EQUALS_ANCHOR`, `HEAD_DESCENDS_FROM_ANCHOR`, and `HEAD_DIVERGED_FROM_ANCHOR` explicit in validation output.
- Keep current-lineage full Council `FALSE / NOT_PROVEN` and do not run providers, Manus, or Council.
- Run Anvien graph refresh before graph queries, file-detail, impact, and detect-changes. Report the CRITICAL impact warning as scope information, not as an edit prohibition.
- Commit each verified implementation slice separately; do not push, merge, promote, release, deploy, or mutate owner worktrees.

## Problem

GOVREC01 added `authority.current_promoted_source` with an `origin/main` ref and a snapshot commit/tree. The repository did not define whether the field meant the latest canonical Git HEAD or a promoted implementation anchor. Existing validation, status, runtime lock, and drift logic accepted a hypothetical `origin/main` advance while leaving the recorded SHA at the prior source. That ambiguity blocked promotion and created a self-reference hazard.

The Owner has now selected anchor semantics. The current anchor is commit `2a71410afd1b29651016ef57a5d2da38938c3f68`, tree `3e6ab12ff78a72c4a3ea2a418e11167a8649aaad`, observed from `origin/main` on `2026-08-26`.

## Scope

- Target worktree: `.tmp/p2p-govrec01-current-authority`.
- Source-of-truth contract: `governance/development-control.json`.
- Validator boundary: `scripts/p2p_development_control.py` and its existing CLI/API callers.
- Direct regression surfaces: `tests/test_p2p_govrec01_reconciliation.py` and focused development-control tests as required.
- Evidence/plan artifacts: this standard four-file plan set plus the required coder and final Supervisor reports.
- Dynamic observations: valid linked-worktree Git `HEAD` and `refs/remotes/origin/main`, with injectable observations for disposable simulation tests.

## Non-Goals

- No push, merge, promotion, release, deployment, tag, or host ACL mutation.
- No provider, Manus, Council, SFI01, Manus R2, vendor-source, project, release-artifact, v5, or immutable-baseline change.
- No recursive commit/hash patching and no weakening of drift or approval gates.
- No new receipt format or replacement for `p2p_approval.py`, `p2p_gate.py`, or existing historical promotion receipts.
- No rewriting of historical GOVREC01/Supervisor reports merely to erase their pre-correction evidence; historical references remain historical and the active authority/tests must use the new field.

## Requirements

1. Rename the active field to `authority.promoted_source_anchor`; no active authority record may retain a competing `current_promoted_source` object.
2. Require explicit fields: `semantic_type`, `purpose`, `observed_ref`, `anchor_commit`, `anchor_tree`, `verified_on`, and `lineage_policy`.
3. Use the exact policy `CURRENT_OR_CANDIDATE_HEAD_MUST_EQUAL_OR_DESCEND_FROM_ANCHOR` for governance-overlay descendants.
4. Validate anchor commit existence and commit/tree binding when a Git repository is available; report `AUTHORITY_ANCHOR_COMMIT_MISSING` or `AUTHORITY_ANCHOR_TREE_MISMATCH` on failure.
5. Validate dynamically observed `HEAD` and `origin/main` independently; reject missing, diverged, unrelated, or invalid Git lineage fail-closed.
6. Reject artifact-shaped or historical-official records as source anchors, malformed anchor objects, legacy ambiguous field names, and policies that require a candidate's own HEAD SHA.
7. Preserve static package/extracted-root validation when no Git repository is available; dynamic checks must activate at the real repository boundary.
8. Add behavior tests for equal anchor, descendant candidate, hypothetical post-promotion, divergent head, missing commit, wrong tree, historical artifact shape, ambiguous legacy field, and self-reference policy.
9. Document the external receipt boundary: committed anchor data is distinct from the final promoted candidate subject SHA/tree held in approval/promotion evidence.

## Acceptance Criteria

- `authority.promoted_source_anchor` is the single active source-anchor truth and has unambiguous anchor semantics.
- The old `current_promoted_source` key is absent from active authority JSON and active tests/consumers; historical reports are explicitly preserved as historical evidence.
- A real candidate whose `HEAD` equals or descends from the anchor validates PASS.
- A hypothetical post-promotion `origin/main` at the corrected candidate while the anchor stays `2a71410...` validates PASS without self-reference.
- A valid commit before the anchor or from a divergent lineage fails closed with an explicit reason code.
- Anchor commit/tree mismatch, missing object, artifact-shaped anchor, malformed policy, and self-reference policy all fail closed.
- Governance drift, development doctor, development-control validate/status, focused GOVREC01/GOVREC02 tests, required regression suites, and compileall pass; current Council remains `FALSE / NOT_PROVEN`.
- A fresh Supervisor review covers the exact final GOVREC02 commit/tree and all post-promotion simulations.
- Terminal status is `P2P_GOVREC02_SOURCE_ANCHOR_CONTRACT_CORRECTED_READY_FOR_OWNER_GATE` only after all gates and the exact final Supervisor PASS.

## Checklist

- [x] P0-A: Complete actual status before implementation work.
  - Goal: establish the exact GOVREC01 worktree, authority gap, graph impact, preserve-only surfaces, and implementation boundary.
  - Work Steps: verify the linked worktree and current refs; inspect the authority record, validator, callers, tests, receipts, and historical docs; refresh Anvien; record file-detail/impact evidence; classify each surface and update downstream slices.
  - Implementation Gate: `2026-08-26-p2p-govrec02-source-anchor-contract-actual-status.md` records P0 complete and authorizes P1 only.
  - Acceptance: current state is classified as partial/wrong where needed, preserve-only historical surfaces are identified, and no unresolved authority choice remains after the Owner anchor decision.

### P1: Implement the explicit source-anchor contract

- Phase Goal: make the active JSON projection and existing validator speak one explicit anchor contract.
- Phase Boundary:
  - In scope: active authority JSON, existing development-control validator, dynamic Git observation helper, direct contract tests.
  - Out of scope: remote state mutation, release/promotion machinery redesign, historical report rewriting, and unrelated governance fields.
  - Dependencies: P0 actual status, Owner anchor decision, fresh Anvien impact evidence.
- Phase Implementation Rule: implement `P1-A`, verify and refresh actual-status, commit; then implement `P1-B`, verify and refresh actual-status, commit.
- Ordered Slice List:
  - P1-A: Replace the ambiguous projection with explicit anchor fields and static validation.
  - P1-B: Add dynamic Git relationship evaluation and fail-closed reason codes.

- [x] P1-A: Replace the ambiguous projection with explicit anchor fields and static validation
  - Goal: establish one clear committed anchor object without requiring a future candidate SHA.
  - Scope Boundary:
    - Editable: `governance/development-control.json`, `scripts/p2p_development_control.py` contract validation surface.
    - Inspect-only: package promotion/approval scripts and historical receipts.
    - Preserve-only: official `.19`, `.74` candidate records, historical reports, runtime lock policy, and owner dirty paths.
    - Out of scope: dynamic Git execution and unrelated current-development validation.
  - Non-Goals: no second authority file, no source-commit rewrite loop, no artifact promotion.
  - Pre-flight Questions:
    - Data source: Owner-selected anchor commit/tree and existing `origin/main` observation.
    - Display permission: governance/read-only projection only; it cannot grant promotion or release permission.
    - DB read flow: N/A; this is a JSON governance projection.
    - DB write flow: N/A; only the requested source-of-truth JSON edit is in scope.
    - Render location: `governance/development-control.json` and validator summaries.
    - UI behavior flow: N/A; CLI/API validation is the observable boundary.
    - Docker runtime: N/A; no application runtime is changed.
    - Playwright target: N/A; no UI surface.
    - Behavior test: malformed/legacy/artifact/self-reference anchor records fail closed; valid anchor parses and validates statically.
    - Cleanup/quarantine: tests use repo-local `.tmp` fixtures and remove them in `finally` blocks.
    - External side effects: none.
    - N/A notes: package verification without `.git` must retain static validation.
  - Work Steps:
    1. Add the explicit anchor object and remove the active legacy key.
       - UI flow check: N/A.
       - DB/data flow check: parse the active JSON and confirm one authority projection only.
       - Render location check: verify existing `development-control.json` consumers remain the only authority surface.
       - Evidence target: `E1-P1A-CONTRACT1`.
    2. Implement static schema/semantic validation and precise reason codes before adding tests.
       - UI flow check: N/A.
       - DB/data flow check: validate field types, semantic type, policy, and artifact/self-reference exclusions.
       - Render location check: validator summary must expose anchor identity without implying latest HEAD.
       - Evidence target: `E1-P1A-CONTRACT2`.
  - Implementation Gate:
    - Anvien file-detail/impact evidence is complete; CRITICAL impact is acknowledged and the edit remains limited to the authority validation family.
    - The active record has no competing authority key and the static contract can be tested without Git.
  - Acceptance:
    - Source: one explicit `promoted_source_anchor` object with required concepts and no active legacy duplicate.
    - Runtime/UI: N/A.
    - DB/data: N/A; JSON authority shape and semantic validation pass.
    - Behavior test: malformed, ambiguous, artifact-shaped, and self-reference policy cases fail closed.
    - Cleanup/quarantine: no fixture or generated state remains outside repo-local `.tmp`.
    - Evidence IDs: `E1-P1A-CONTRACT1..E1-P1A-CONTRACT2`.
    - Actual-status rows refreshed: authority projection and static validator transition to partial/correct as proven.
  - Evidence Targets: contract diff, source review, focused static validator output, path-scoped status.
  - Actual-status Update: append R1 with the exact field/validator transition and update P1-B assumptions.
  - Commit Boundary: commit after this slice when static contract acceptance passes.

- [x] P1-B: Add dynamic Git relationship evaluation and fail-closed reason codes
  - Goal: distinguish recorded anchor, observed `HEAD`, and observed `origin/main` at the real repository boundary.
  - Scope Boundary:
    - Editable: `scripts/p2p_development_control.py`, its direct tests if required.
    - Inspect-only: `scripts/package_release.py`, `scripts/p2p_gate.py`, `scripts/p2p_approval.py`, historical receipts.
    - Preserve-only: runtime lock generation and drift policy.
    - Out of scope: remote mutation and promotion execution.
  - Non-Goals: do not require anchor equality with latest HEAD; do not synthesize remote authority.
  - Pre-flight Questions:
    - Data source: `git rev-parse`, `git merge-base --is-ancestor`, and explicit injected observations for simulation.
    - Display permission: relationship result is diagnostic/validation evidence, not approval.
    - DB read flow: N/A.
    - DB write flow: N/A.
    - Render location: `validate --json`, `status --json`, and returned validation summary.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: anchor equality, descendant, missing object, wrong tree, and divergence.
    - Cleanup/quarantine: disposable Git simulations remain under `.tmp` or use current valid objects without changing refs.
    - External side effects: read-only Git commands only.
    - N/A notes: static package roots skip dynamic checks when no Git object database is present.
  - Work Steps:
    1. Add the dynamic observation boundary and explicit relationship codes.
       - UI flow check: N/A.
       - DB/data flow check: validate anchor commit/tree binding before ancestry evaluation.
       - Render location check: return separate `observed_head`, `observed_origin_main`, and relation fields.
       - Evidence target: `E1-P1B-GIT1`.
    2. Wire real CLI/build validation to the existing validator while preserving static package verification.
       - UI flow check: N/A.
       - DB/data flow check: real linked worktree validates both HEAD and origin/main; no caller can turn divergence into PASS.
       - Render location check: text status remains concise; JSON carries full evidence.
       - Evidence target: `E1-P1B-GIT2`.
  - Implementation Gate:
    - Exact symbol/file impact is reviewed and no new promotion mechanism is introduced.
    - Dynamic checks are optional only at Git-less package boundaries, never silently bypassed at the real checkout boundary.
  - Acceptance:
    - Source: current/candidate HEAD and observed origin/main are separately evaluated against the anchor.
    - Runtime/UI: N/A.
    - DB/data: N/A.
    - Behavior test: equal/descendant PASS; diverged/missing/wrong-tree FAIL CLOSED with stable reason codes.
    - Cleanup/quarantine: no refs, remote files, or canonical main are mutated.
    - Evidence IDs: `E1-P1B-GIT1..E1-P1B-GIT2`.
    - Actual-status rows refreshed: dynamic validator transitions to bound-correct.
  - Evidence Targets: source diff, relation results, static-package compatibility, current-worktree validation.
  - Actual-status Update: append R2 with dynamic relationship and static-package results; update P2 simulation assumptions.
  - Commit Boundary: commit after this slice when dynamic checks pass.

### P2: Prove simulations, regression, and receipt boundary

- Phase Goal: close the behavior contract across positive, negative, historical, and external-receipt boundaries.
- Phase Boundary:
  - In scope: GOVREC02/GOVREC01 tests, disposable topology simulation, active documentation/plan evidence, regression commands.
  - Out of scope: providers, Manus, Council, SFI01, remote writes, and release/promotion.
  - Dependencies: P1-A and P1-B committed and green.
- Phase Implementation Rule: implement `P2-A`, verify and refresh actual-status, commit; then complete `P2-B`, verify and refresh actual-status, commit if source/docs changed.
- Ordered Slice List:
  - P2-A: Add behavior tests for anchor and post-promotion/divergence semantics.
  - P2-B: Align active contract documentation and record external receipt boundary.

- [x] P2-A: Add behavior tests for anchor and post-promotion/divergence semantics
  - Goal: mechanically prove that a promoted candidate may descend from a prior anchor without self-reference, while unrelated lineage fails closed.
  - Scope Boundary:
    - Editable: `tests/test_p2p_govrec02_source_anchor.py` and existing direct validator suites where regression coverage belongs.
    - Inspect-only: production code after P1.
    - Preserve-only: historical reports and official artifact.
    - Out of scope: full repository tests until P3.
  - Non-Goals: no simulated eight-role Council and no fake provider evidence.
  - Pre-flight Questions:
    - Data source: current valid Git objects and copied JSON records.
    - Display permission: tests prove validator behavior only.
    - DB read flow: N/A.
    - DB write flow: N/A.
    - Render location: test assertions and validation JSON.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: required positive/negative matrix from GOVREC02.
    - Cleanup/quarantine: test-local `.tmp`, no ref mutation.
    - External side effects: none.
    - N/A notes: no live host or remote boundary is exercised.
  - Work Steps:
    1. Add tests after the corrected behavior exists for active key, semantic fields, relation codes, and malformed records.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: validation output is the observable result.
       - Evidence target: `E2-P2A-TEST1`.
    2. Add disposable BEFORE/CANDIDATE/HYPOTHETICAL POST-PROMOTION and diverged-head tests.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: assert PASS versus explicit FAIL CLOSED reason codes.
       - Evidence target: `E2-P2A-TEST2`.
  - Implementation Gate:
    - Production validator behavior is complete and tests target behavior, not only field spelling.
  - Acceptance:
    - Source: test suite covers every required GOVREC02 failure/positive category.
    - Runtime/UI: N/A.
    - DB/data: N/A.
    - Behavior test: GOVREC02 and GOVREC01 focused tests PASS.
    - Cleanup/quarantine: all temporary fixtures are cleaned and active refs unchanged.
    - Evidence IDs: `E2-P2A-TEST1..E2-P2A-TEST2`.
    - Actual-status rows refreshed: simulation and regression rows reflect fresh evidence.
  - Evidence Targets: test names, output, mutation audit, exact relation values.
  - Actual-status Update: append R3 and update P2-B/P3 assumptions.
  - Commit Boundary: commit after test matrix acceptance passes.

- [ ] P2-B: Align active contract documentation and record external receipt boundary
  - Goal: document that the committed anchor is reconciliation input while final promoted subject identity remains externally bound by existing approval/receipt machinery.
  - Scope Boundary:
    - Editable: new GOVREC02 plan/evidence/benchmark/actual-status artifacts and active docs only if exact consumers remain after source search.
    - Inspect-only: historical GOVREC01 reports/plans and approval records.
    - Preserve-only: historical evidence bytes, official baseline, and current Council boundary.
    - Out of scope: new approval schema or receipt system.
  - Non-Goals: do not rewrite historical reports to retroactively claim corrected semantics.
  - Pre-flight Questions:
    - Data source: existing approval schema, C41 historical receipts, and source-binding records.
    - Display permission: documentation only; no authorization is granted.
    - DB read flow: N/A.
    - DB write flow: N/A.
    - Render location: active plan/evidence and any exact active consumer discovered by search.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: source search has no active legacy consumer or competing authority field.
    - Cleanup/quarantine: no stale generated docs or unrelated plan artifacts.
    - External side effects: none.
    - N/A notes: historical references remain clearly historical.
  - Work Steps:
    1. Record the source-anchor/receipt distinction and exact evidence in the plan ledger.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: plan/evidence links name source-of-truth versus historical evidence.
       - Evidence target: `E2-P2B-DOC1`.
    2. Search active consumers and preserve historical reports without creating a duplicate truth.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: only `promoted_source_anchor` is active.
       - Evidence target: `E2-P2B-DOC2`.
  - Implementation Gate:
    - No active `current_promoted_source` consumer remains; any retained historical text is labeled by provenance, not used as authority.
  - Acceptance:
    - Source: active docs and tests align with anchor semantics; historical evidence remains unmodified.
    - Runtime/UI: N/A.
    - DB/data: N/A.
    - Behavior test: active consumer search and validation pass.
    - Cleanup/quarantine: no duplicate authority record introduced.
    - Evidence IDs: `E2-P2B-DOC1..E2-P2B-DOC2`.
    - Actual-status rows refreshed: docs/receipt boundary is correct and preserve-only history is recorded.
  - Evidence Targets: receipt schema/records, active search, plan ledger.
  - Actual-status Update: append R4 before final regression.
  - Commit Boundary: commit if active documentation/source changes were made; otherwise record preserve-only evidence.

### P3: Final gates and exact final review

- Phase Goal: run the required regression matrix, verify final exact identity, and obtain fresh Supervisor acceptance before Owner gate.
- Phase Boundary:
  - In scope: required tests, drift, doctor, control validate/status, regression inventory, compileall, exact final identity, Supervisor report.
  - Out of scope: Owner approval execution, promotion, release, deployment, provider/Manus/Council.
  - Dependencies: P2 complete and all implementation-slice commits known.
- Phase Implementation Rule: no source implementation remains after P2; final validation and review are read-only.

- [ ] P3-A: Call supervisor for the implemented-plan acceptance loop.
  - Goal: independently review the exact final GOVREC02 HEAD and the full anchor invariant.
  - Work Steps:
    1. Run all required validation and record commit/tree/parent, anchor, origin/main, simulations, changed paths, and clean subject status.
    2. Apply no fixes during review; if rejected, return to the responsible coder slice, create a separate fix commit, and re-review.
  - Implementation Gate: P1/P2 slices are complete and validation evidence exists.
  - Acceptance: fresh Supervisor PASS with residual same-invariant unverified surfaces `none`, or a bounded blocker is recorded.
- [ ] P3-B: Remove dead work created during this plan.
  - Goal: ensure only live contract, tests, evidence, and required reports remain.
  - Work Steps:
    1. Inspect plan-created artifacts and temporary outputs.
    2. Remove only dead artifacts created by this plan, then re-run targeted status and Supervisor review if necessary.
  - Implementation Gate: no unrelated owner path is selected for cleanup.
  - Acceptance: final diff has no dead plan-created artifacts and evidence records preserved history.
- [ ] P3-C: Close the plan.
  - Goal: record final validation, detect-changes, benchmark, commits, and terminal status.
  - Work Steps:
    1. Run full required non-UI validation and compileall; no Docker/Playwright applies.
    2. Run Anvien detect-changes before the final implementation commit when source changes exist.
    3. Record the final exact identity and stop at Owner Gate.
  - Implementation Gate: P3-A and P3-B pass or record a blocker.
  - Acceptance: evidence is complete, no protected action occurred, and the terminal verdict is honest.

## Risk Notes

- The validator's graph impact is CRITICAL because `validate_control` feeds multiple governance/build paths. Keep the new Git boundary optional for Git-less package verification and fail closed only when a real repository observation is requested.
- The current root has invalid Git administrative metadata and a large pre-existing dirty owner state. Use only the valid linked worktree and preserve unrelated paths.
- Existing runtime-lock hashes cover the active governance JSON and will require the existing deterministic lock/drift path after source changes; do not hand-edit or weaken exclusions.
- Historical reports may retain the old field name as evidence of the pre-correction state. They must not be treated as active authority or rewritten to erase provenance.
- A final Supervisor PASS is technical review only; Owner approval and promotion remain separate and are not performed by this plan.
