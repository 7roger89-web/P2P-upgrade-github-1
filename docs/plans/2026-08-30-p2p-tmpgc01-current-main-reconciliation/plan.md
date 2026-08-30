# P2P-TMPGC01 Current Main Reconciliation Plan

## Metadata

- Date: `2026-08-30`
- Status: `complete; READY_FOR_OWNER_REVIEW`
- Plan: `docs/plans/2026-08-30-p2p-tmpgc01-current-main-reconciliation/plan.md`
- Evidence: `docs/plans/2026-08-30-p2p-tmpgc01-current-main-reconciliation/evidence.md`
- Benchmark: `docs/plans/2026-08-30-p2p-tmpgc01-current-main-reconciliation/benchmark.md`
- Actual status: `docs/plans/2026-08-30-p2p-tmpgc01-current-main-reconciliation/actual-status.md`

## Goal

Reconcile the already-reviewed TMPGC01 implementation onto fresh canonical
`origin/main` at `d661654746f090136f37370f76578ee345b74994`, preserving that main
tree and changing only the TMPGC invariant family. Freeze one new exact,
unpromoted candidate SHA/tree. This plan authorizes no push, promotion, delete,
scheduling activation, or unrelated P2P work.

## Rules

- Work only in the isolated repo-local worktree created from fresh `origin/main`.
- Preserve the dirty owner checkout and all current-main paths not in the TMPGC family.
- Use the supplied reviewed candidate `dab3e858dcace307f4bd77fdb43145df70e75da2`
  / tree `d9ab934f16a9517dccee3e847362795ec66f719b` as implementation evidence,
  never as current authority.
- Retain `ACTIVE`, `CANDIDATE`, `OWNER_GATE`, `ROLLBACK_REQUIRED`, `UNKNOWN`,
  `DIRTY`, `DEPENDENCY`, and `EVIDENCE_NOT_DURABLE` as KEEP conditions.
- Retain lifecycle `ACTIVE -> COMPLETE -> DISPOSABLE -> DELETED`.
- Retain dry-run default and disabled physical delete, legacy delete, schedule
  activation, and automatic GC.
- If source context differs materially from the reviewed semantics, stop and
  report rather than redesigning TMPGC.
- Run only current-main preservation, focused TMPGC/invariant checks, and
  compile/static checks for changed Python files.
- Run Anvien where available; if its native/index runtime remains unavailable,
  use direct Git/source/AST evidence and record the limitation.

## Problem

Fresh canonical main does not contain the reviewed TMPGC source, policy, or
focused test surface. The previous candidate also contains unrelated lineage
and evidence artifacts, so the reconciliation must select only the TMPGC
implementation family instead of merging the whole historical candidate.

## Scope

The scoped implementation family is:

- `.p2p/system/p2p_capabilities/fw06_operational_resilience.py`: additive
  TMPGC lifecycle, classification, audit, lease serialization, and delete
  safety extension over the existing FW06 seam.
- `scripts/p2p_tmp_gc.py`: dry-run-default CLI and owner-gated schedule preview.
- `scripts/p2p_live_certification.py`: existing C27 reconciliation sibling;
  carry only the reviewed TMPGC guard/delegation changes if a real diff exists.
- `governance/p2p-tmp-gc-policy.json`: TMPGC policy contract.
- `tests/test_p2p_tmp_gc.py`: focused behavior and fail-closed regressions.
- Reconciliation plan/evidence/benchmark/status and the final review report.

## Non-Goals

No redesign; no broad merge; no MPFB, Fast Path, Arena, Game Truyen, or
unrelated P2P surfaces; no deletion run; no scheduling activation; no automatic
GC; no push, promotion, release, deployment, or canonical-main mutation.

## Requirements

- Fresh `origin/main` must bind exactly to the expected SHA and record its tree.
- The resulting candidate must descend from fresh main and contain no unrelated
  historical candidate paths.
- Final deletion authorization must remain inside the existing serialized FW06
  critical section, with final revalidation, audit, filesystem result, lifecycle
  update, and lease release fail-closed.
- Audit validation must retain semantic identity and ordering checks, including
  `prior_lifecycle == lifecycle_from`.
- Focused tests must prove both safe KEEP behavior and the reviewed deletion
  lifecycle/serialization boundary.

## Acceptance Criteria

- Fresh main SHA/tree and ancestry are recorded from the fresh clone/worktree.
- Only the five scoped source/policy/test paths plus this reconciliation's
  bounded process artifacts are changed.
- `git diff` proves all fresh-main paths outside the scope are preserved.
- Focused TMPGC tests and changed-file compile/static checks pass.
- No physical filesystem deletion, schedule activation, auto-GC, push, or
  promotion occurs.
- Exact candidate SHA/tree is frozen and handed to Supervisor/Owner review;
  canonical promotion remains `NO`.

## Checklist

- [x] P0-A: Complete actual status before implementation work.
  - Goal: bind the fresh base, previous exact candidate, scope, and tooling limits.
  - Work Steps: fresh-fetch canonical main; record SHA/tree; inspect exact
    candidate objects, source/test paths, current-main presence, owner-checkout
    safety, and Anvien availability; update actual status before code changes.
  - Implementation Gate: fresh SHA/tree, source authority, scoped files, and
    no material semantic conflict are recorded.
  - Acceptance: `actual-status.md` contains the completed P0 matrix and decision.

### P1: Selective TMPGC implementation reconciliation

- Phase Goal: carry only the reviewed TMPGC functionality onto fresh main and
  then prove its focused behavior.
- Phase Boundary:
  - In scope: the five scoped TMPGC family paths and bounded plan evidence.
  - Out of scope: every unrelated current-main or historical-candidate path.
  - Dependencies: completed P0, exact fresh SHA/tree, exact previous candidate
    source blobs, and no material conflict.
- Phase Implementation Rule: execute `P1-A`, verify and commit it, then execute
  `P1-B`; never merge the whole previous candidate.
- Ordered Slice List:
  - P1-A: Apply exact reviewed TMPGC source/policy/CLI delta.
  - P1-B: Add reviewed focused tests and run the bounded validation matrix.

- [x] P1-A: Apply exact reviewed TMPGC source/policy/CLI delta
  - Goal: add the production TMPGC behavior while preserving current FW06/C27
    baseline semantics.
  - Scope Boundary:
    - Editable: `fw06_operational_resilience.py`, `scripts/p2p_tmp_gc.py`,
      `scripts/p2p_live_certification.py`, `governance/p2p-tmp-gc-policy.json`.
    - Inspect-only: current-main MPFB/Fast Path/Arena/Game Truyen and unrelated
      FW06 consumers.
    - Preserve-only: all fresh-main files outside the TMPGC family.
    - Out of scope: tests, deletion runs, scheduling activation, and promotion.
  - Non-Goals: no new cleanup authority, router, scheduler, fallback, or
    redesign.
  - Pre-flight Questions:
    - Data source: reviewed candidate blobs and fresh-main baseline.
    - Display permission: N/A; this is a local Python CLI/runtime contract.
    - DB read flow: N/A; state is repo-local JSON/JSONL.
    - DB write flow: N/A; no authoritative project state is touched.
    - Render location: N/A; CLI/result records only.
    - UI behavior flow: N/A; no UI change.
    - Docker runtime: N/A; no service/container is changed.
    - Playwright target: N/A; no browser surface.
    - Behavior test: deferred to P1-B after source implementation.
    - Cleanup/quarantine: all probe roots remain under the isolated worktree
      `.tmp`; no historical workspace is deleted.
    - External side effects: no push, promotion, scheduling, or physical delete.
    - N/A notes: current-main preservation is checked by exact Git diff.
  - Work Steps:
    1. Compare the reviewed source delta against fresh-main blobs and assert
       that no genuine conflict changes reviewed semantics.
       - UI flow check: N/A; CLI/runtime scope.
       - DB/data flow check: verify state paths remain repo-local and fail-closed.
       - Render location check: N/A; record source symbol locations.
       - Evidence target: E1-P1A-SRC1..E1-P1A-SRC4.
    2. Apply only the selected source/policy/CLI delta and inspect the resulting
       diff for unrelated paths before staging.
       - UI flow check: N/A; no UI.
       - DB/data flow check: verify KEEP protections and disabled actions remain.
       - Render location check: N/A; inspect CLI output contract source.
       - Evidence target: E1-P1A-DIFF1..E1-P1A-DIFF3.
  - Implementation Gate:
    - Direct source/AST fallback is permitted only because Anvien refresh and
      narrowed refresh both failed in the isolated worktree; no index repair.
    - The exact reviewed functional delta must apply without semantic conflict.
  - Acceptance:
    - Source: all selected TMPGC production/policy paths are present.
    - Runtime/UI: N/A; no UI/runtime server.
    - DB/data: no external or authoritative project data is changed.
    - Behavior test: deferred to P1-B.
    - Cleanup/quarantine: no physical deletion performed.
    - Evidence IDs: E1-P1A-SRC1..E1-P1A-DIFF3.
    - Actual-status rows refreshed: FW06/CLI/policy transition to partial-awaiting-tests.
  - Evidence Targets: source diff, exact path allowlist, semantic invariant scan.
  - Actual-status Update: refreshed after source commit; exact source blobs
    match the supplied reviewed candidate and no material reconciliation
    conflict was found.
  - Commit Boundary: commit this verified source/policy slice before tests.

- [x] P1-B: Add reviewed focused tests and run bounded validation
  - Goal: carry the focused regression suite after behavior exists and verify
    the full TMPGC invariant family at the authorized ceiling.
  - Scope Boundary:
    - Editable: `tests/test_p2p_tmp_gc.py` and bounded evidence files.
    - Inspect-only: FW06/C27 sibling consumers and current-main preservation.
    - Preserve-only: all unrelated test suites and source paths.
    - Out of scope: broad regression, release, deployment, and live action.
  - Non-Goals: no test-only redesign or unrelated cleanup.
  - Pre-flight Questions:
    - Data source: isolated temporary test roots only.
    - Display permission: N/A.
    - DB read flow: N/A; JSON/JSONL filesystem state only.
    - DB write flow: temporary roots only; quarantine after tests.
    - Render location: N/A.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: `tests/test_p2p_tmp_gc.py` focused selectors and full file.
    - Cleanup/quarantine: test-created roots are repo-local and disposable;
      do not remove historical candidate workspaces.
    - External side effects: none.
    - N/A notes: compile/static checks replace UI/browser checks.
  - Work Steps:
    1. Add the exact reviewed focused test file after source behavior is present.
       - UI flow check: N/A.
       - DB/data flow check: assert pytest roots are isolated.
       - Render location check: N/A.
       - Evidence target: E1-P1B-TEST1.
    2. Run focused lifecycle, audit, TOCTOU/serialization, C27 seam, CLI,
       compile, diff-check, and current-main-preservation commands.
       - UI flow check: N/A.
       - DB/data flow check: assert zero physical deletes outside test roots.
       - Render location check: N/A.
       - Evidence target: E1-P1B-TEST2..E1-P1B-TEST7.
  - Implementation Gate: source slice is committed and changed-source import/
    compile succeeds before test files are added.
  - Acceptance:
    - Source: focused tests bind to the exact reviewed semantics.
    - Runtime/UI: N/A.
    - DB/data: isolated roots only; physical delete gate remains disabled by default.
    - Behavior test: focused suite passes.
    - Cleanup/quarantine: no historical or owner workspace is deleted.
    - Evidence IDs: E1-P1B-TEST1..E1-P1B-TEST7.
    - Actual-status rows refreshed: all TMPGC family rows become verified-awaiting-review.
  - Evidence Targets: test output, compile output, diff check, exact path inventory.
  - Actual-status Update: focused suite, compile, AST/JSON/static, and diff
    checks passed; exact candidate commit remains the only review subject.
  - Commit Boundary: commit the tested suite and bounded evidence before review.

- [x] P2-A: Call supervisor for exact-candidate acceptance
  - Goal: independently review the frozen exact subject and distinguish technical
    readiness from Owner approval and promotion.
  - Work Steps: inspect exact source/diff first; verify the invariant family and
    focused outputs; write the Supervisor report; reject if any same-invariant
    surface or exact-subject proof is missing.
  - Implementation Gate: P1-A and P1-B are committed and exact SHA/tree are bound.
  - Acceptance: Supervisor PASS for the exact functional subject; no promotion
    is run. Report: `reports/supervisor/rp_supervisor_260830_044500_by_gpt-5-codex_p2p-tmpgc01-current-main-reconciliation.md`.

- [x] P2-B: Close plan evidence and exact candidate handoff
  - Goal: record final SHA/tree, status, safety counters, and explicit no-push/no-
    promotion boundary.
  - Work Steps: run detect-changes if available, verify final diff/path allowlist,
    update all four plan ledgers, and freeze the exact candidate identity.
  - Implementation Gate: P2-A concluded PASS and no semantic materiality stop
    exists.
  - Acceptance: final handoff contains `CANONICAL_PROMOTED=NO` and the
    requested terminal verdict string. The final closure commit is evidence-
    only and must preserve the functional candidate blobs.

## Risk Notes

- FW06 is a shared contract with a high scope warning; only the reviewed additive
  TMPGC sections may be carried forward.
- The current main commit is not available in the previous candidate object store;
  exact comparison is therefore performed in the fresh clone/worktree.
- Anvien native graph refresh is currently unavailable due a process crash and
  `lbug_database_init failed`; direct source/AST/Git evidence is recorded instead.
- Any mismatch in lifecycle, protection, audit, or delete serialization semantics
  is a hard STOP, not a reconciliation choice.
