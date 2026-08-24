# P2P AERG Expired-Evidence Fail-Closed Repair Plan

## Metadata

- Date: `2026-08-24`
- Status: `P0 Complete / P1-A red checkpoint / P1-B pending`
- Plan: `Docs/plans/2026-08-24-p2p-aerg-stale-evidence-repair/2026-08-24-p2p-aerg-stale-evidence-repair-plan.md`
- Evidence: `Docs/plans/2026-08-24-p2p-aerg-stale-evidence-repair/2026-08-24-p2p-aerg-stale-evidence-repair-evidence.md`
- Benchmark: `Docs/plans/2026-08-24-p2p-aerg-stale-evidence-repair/2026-08-24-p2p-aerg-stale-evidence-repair-benchmark.md`
- Actual status: `Docs/plans/2026-08-24-p2p-aerg-stale-evidence-repair/2026-08-24-p2p-aerg-stale-evidence-repair-actual-status.md`

## Goal

Repair the confirmed AERG freshness defect so age-expired and explicit
`STALE` evidence produce `decision=STALE`, preserve outward `status` and
`freshness` semantics, and cannot allow a QualityIntelligence checkpoint.

## Rules

- This is a narrow production semantic repair, not feature expansion.
- User-required tests-first ordering overrides the generic coder ordering:
  add failing discriminating freshness tests before editing production code.
- Preserve contradiction precedence: `CONTRADICTED > SUBJECT_MISMATCH > STALE > INSUFFICIENT > SUPPORTED`.
- Do not reopen the closed no-mutation repair.
- Do not modify QI or FW01 source unless fresh repaired evidence proves their
  contracts defective.
- Preserve `.19`, `.74`, CPT01-R2, RF01, C43, governance, owner authority,
  release, deployment, and host boundaries.
- Do not run Supervisor review, independent verification, Owner approval,
  promotion, release, deployment, or another Goal in this task.
- Use repo-local `.tmp` only for temporary verification artifacts.
- Run Anvien impact/file-detail before editing and detect-changes before each
  implementation commit.

## Problem

`aerg_engine.py` records `EVIDENCE_EXPIRED` and `EVIDENCE_NOT_CURRENT` but does
not append a `STALE` decision. Decision aggregation therefore falls through to
`SUPPORTED`, serializes `VERIFIED/CURRENT`, and can make QI return
`QUALITY_VERIFIED` with `checkpoint_allowed=True`.

## Scope

- Production: `.p2p/system/p2p_capabilities/aerg_engine.py`, smallest decision
  aggregation change required by the current contract.
- Tests: `.p2p/system/p2p_capabilities/tests/test_aerg_reconciliation.py`,
  explicit age-expiry, explicit stale, stale-plus-contradiction, fresh happy
  path, and QI-boundary assertions.
- Evidence: this plan set, coder report, current notes decision log, and
  exact repair checkpoint.

## Non-Goals

- No AERGResult redesign, new state machine, freshness subsystem, QI rewrite,
  FW01 redesign, scheduler, queue, database, persistence authority, or release
  gate.
- No changes to `aerg_model.py`, `quality_intelligence.py`, or
  `p2p_fw01_loop.py` unless a fresh failing integration test proves necessity.
- No independent verification or Supervisor acceptance in this lane.

## Requirements

1. Age-only expired evidence returns exact `decision=STALE` and
   `freshness=STALE`, with `EVIDENCE_EXPIRED` preserved.
2. Explicit `freshness=STALE` returns exact `decision=STALE` and
   `freshness=STALE`, with `EVIDENCE_NOT_CURRENT` preserved.
3. Stale plus material contradiction returns `CONTRADICTED`.
4. Current mechanically valid evidence remains `SUPPORTED`.
5. Actual stale AERG output maps through current QI to a non-checkpointing
   state with `STALE_EVIDENCE`.
6. Existing claim, provenance, subject, contradiction, authority, provider
   neutrality, QI, FW01, C43, RF01, and protected-state invariants remain
   intact.

## Acceptance Criteria

- Tests fail before the production edit for the new stale cases.
- The smallest production change makes all new cases pass without changing QI
  or FW01 source.
- Fresh direct probes show the five required cases exactly.
- Focused AERG, freshness-specific, reconstructed A-Z, QI, FW01, full
  capability, C43, RF01, compile, and framework classification evidence is
  recorded.
- `NEW_FAILURE = 0` relative to the known inherited framework debt.
- Independent REJECT report remains unchanged.
- Final terminal state is exactly
  `P2P_AERG_STALE_EVIDENCE_REPAIR_READY_FOR_SUPERVISOR_REVIEW`.

## Checklist

- [x] P0-A: Complete actual status before implementation work.
  - Goal: classify the confirmed defect and all sibling surfaces.
  - Work Steps: read the user defect report, open REJECT report, read the
    relevant SPECs, inspect source, run pre-repair probes, inspect Git, and
    refresh Anvien.
  - Implementation Gate: `actual-status.md` records the wrong freshness path,
    unaffected QI/FW01 boundaries, and evidence IDs.
  - Acceptance: P0 status is complete and downstream slices are bounded.

### P1: Test-first freshness repair

- Phase Goal: add discriminating failing tests, then make the smallest
  production decision-aggregation correction.
- Phase Boundary:
  - In scope: AERG freshness decisions and tests for the five required cases.
  - Out of scope: QI/FW01 source, architecture, governance, release/host.
  - Dependencies: P0 actual status and fresh Anvien impact limitation.
- Phase Implementation Rule: implement `P1-A`, run the intentionally failing
  tests, commit that test checkpoint; then implement `P1-B`, verify, and commit.
- Ordered Slice List:
  - P1-A: Add failing freshness and QI-boundary assertions.
  - P1-B: Add the minimal AERG stale decision derivation.
  - P1-C: Prove QI/FW01 source is unaffected and preserve closed invariants.

- [x] P1-A: Add failing freshness and QI-boundary assertions.
  - Goal: encode exact stale outcomes before production editing.
  - Scope Boundary:
    - Editable: AERG reconciliation test file only.
    - Inspect-only: AERG production, QI, FW01, governance, prior reports.
    - Preserve-only: no-mutation assertions and existing A-Z cases.
    - Out of scope: production source and all protected state.
  - Non-Goals: no test weakening or replacement of existing cases.
  - Pre-flight Questions:
    - Data source: structured `EvidenceObservation` fixtures; no external data.
    - Display permission: N/A; no UI.
    - DB read/write flow: N/A; in-memory engine only.
    - Render location: N/A; Python result contract.
    - UI behavior flow: N/A; no UI.
    - Docker runtime: N/A; offline Python capability tests.
    - Playwright target: N/A; no UI/runtime surface.
    - Behavior test: five exact AERG/QI outcomes.
    - Cleanup/quarantine: test-created temporary state remains under test
      harness cleanup; no repository target is mutated.
    - External side effects: none.
    - N/A notes: this is a library contract repair.
  - Work Steps:
    1. Add age-only and explicit-stale tests asserting exact `STALE` decision,
       result freshness, and reason.
       - UI flow check: N/A.
       - DB/data flow check: in-memory observation only.
       - Render location check: result object and serialized contract.
       - Evidence target: `E1-P1A-RED1` and test output.
    2. Add stale-plus-contradiction, fresh-happy-path, and actual-QI-boundary
       assertions while retaining no-mutation assertions.
       - UI flow check: N/A.
       - DB/data flow check: existing QI callable only.
       - Render location check: QI verdict/checkpoint fields.
       - Evidence target: `E1-P1A-RED2`.
  - Implementation Gate: tests are added only after source inspection and
    Anvien impact/file-detail limitation is recorded; production remains
    untouched until the tests demonstrate the old failure.
  - Acceptance:
    - Source: only the test file changes.
    - Runtime/UI: N/A.
    - DB/data: no persistent writes.
    - Behavior test: new tests fail for the known pre-repair behavior.
    - Cleanup/quarantine: no repository state mutation.
    - Evidence IDs: `E1-P1A-RED1..E1-P1A-RED2`.
    - Actual-status rows refreshed: AERG freshness `wrong` remains until P1-B.
  - Evidence Targets: failing test output, exact diff, current test hash.
  - Actual-status Update: `missing freshness tests -> explicit failing tests`.
  - Commit Boundary: commit test-only red checkpoint before production edit.
  - Result: `17` tests ran; the `5` new discriminating assertions exposed `4`
    expected pre-repair failures and left production source untouched. The
    test-only checkpoint is ready before P1-B editing.

- [ ] P1-B: Add the minimal AERG stale decision derivation.
  - Goal: make stale freshness fail closed without changing the state model.
  - Scope Boundary:
    - Editable: `aerg_engine.py` decision aggregation only.
    - Inspect-only: QI/FW01 source and existing model contracts.
    - Preserve-only: contradiction precedence and no-mutation behavior.
    - Out of scope: all other production files and governance.
  - Non-Goals: no new subsystem, abstraction, queue, persistence, or QI fix.
  - Pre-flight Questions: all non-Python/UI/DB items are N/A; direct runtime
    probes and nearest-boundary tests are the authoritative behavior check.
  - Work Steps:
    1. Derive/append `STALE` when freshness is `STALE` and no stronger
       contradiction exists, preserving existing precedence.
       - UI/DB/render checks: N/A; result contract only.
       - Evidence target: `E1-P1B-SRC1` and `E1-P1B-GREEN1`.
    2. Run focused tests, direct five-case probe, and compile boundary; inspect
       diff and hashes.
       - UI/DB/render checks: N/A.
       - Evidence target: `E1-P1B-RUN1..E1-P1B-RUN3`.
  - Implementation Gate: P1-A red evidence exists; only the smallest source
    branch needed to close the current invariant may be edited.
  - Acceptance:
    - Source: stale is a decision and serialization remains `STALE`.
    - Behavior test: all five new cases pass; old no-mutation cases pass.
    - Evidence IDs: `E1-P1B-SRC1`, `E1-P1B-GREEN1..E1-P1B-GREEN3`.
    - Actual-status rows refreshed: AERG freshness `wrong -> correct`.
  - Evidence Targets: source diff, direct before/after output, hashes.
  - Actual-status Update: record production fix and exact checkpoint.
  - Commit Boundary: commit production repair after fresh focused verification.

- [ ] P1-C: Prove QI/FW01 and sibling invariants unaffected.
  - Goal: close the freshness invariant across the existing integration seam.
  - Scope Boundary:
    - Editable: none unless a fresh failing test proves required.
    - Inspect-only: QI, FW01, model serialization, existing A-Z and authority tests.
    - Preserve-only: QI/FW01 source and all protected state.
    - Out of scope: redesign or integration topology changes.
  - Non-Goals: no QI/FW01 source edit.
  - Pre-flight Questions: no UI/DB/Docker/Playwright surface applies.
  - Work Steps:
    1. Verify actual stale AERG output maps to non-checkpointing QI.
       - Evidence target: `E1-P1C-QI1`.
    2. Verify FW01 post-execution seam receives the repaired result without
       source change and closed AERG invariants still pass.
       - Evidence target: `E1-P1C-FW1`.
  - Implementation Gate: P1-B focused tests pass and source diff is surgical.
  - Acceptance: QI/FW01 source unchanged and direct integration is correct.
  - Evidence Targets: QI mapping, FW01 source/order, no-mutation/provider/
    authority regression output.
  - Actual-status Update: sibling surfaces `bound-correct / preserve-only`.
  - Commit Boundary: include only if a needed P1-C change is proven; otherwise
    attach evidence to the P1-B repair checkpoint.

### P2: Fresh regression and protected-state validation

- Phase Goal: establish no new failures and preserve development-plane state.
- Phase Boundary:
  - In scope: fresh AERG/QI/FW01/full/C43/RF01/compile/validator checks.
  - Out of scope: inherited validator repair and any host/promotion action.
- [ ] P2-A: Run focused and reconstructed behavioral validation.
  - Goal: prove direct five-case semantics, A-Z coverage, QI boundary, and
    no-mutation preservation.
  - Work Steps: run focused AERG, freshness-specific, reconstructed A-Z, QI,
    FW01, and direct probes; record exact results.
  - Implementation Gate: P1-B checkpoint exists.
  - Acceptance: all required behavior passes and `NEW_FAILURE=0`.
  - Evidence Targets: `E2-P2A-RUN1..E2-P2A-RUN5`.
  - Commit Boundary: no source commit; evidence follows the repair commit.

- [ ] P2-B: Run full regressions, compile, and protected-state checks.
  - Goal: confirm no sibling or boundary regression.
  - Work Steps: run full capability, C43, RF01 orientation/packaging, compile,
    framework validator, Git diff/status, and governance readback.
  - Implementation Gate: P2-A passes.
  - Acceptance: required suites pass; inherited debt remains honestly listed;
    protected state is unchanged.
  - Evidence Targets: `E2-P2B-RUN1..E2-P2B-RUN5`.
  - Commit Boundary: no source commit; evidence follows the repair commit.

### P3: Evidence and handoff

- [ ] P3-A: Write coder evidence and stop at Supervisor-ready state.
  - Goal: create fresh repair evidence, hashes, report, and notes-log entry.
  - Work Steps: refresh plan evidence/benchmark/actual-status, write the coder
    report, update today's notes decision log, run detect-changes, commit the
    report/doc evidence separately, and verify current status.
  - Implementation Gate: P2 acceptance evidence is complete.
  - Acceptance: exact terminal state is
    `P2P_AERG_STALE_EVIDENCE_REPAIR_READY_FOR_SUPERVISOR_REVIEW`.
  - Non-Goals: do not call Supervisor or independent verification.

## Risk Notes

- The principal risk is precedence regression: stale evidence must not mask a
  stronger contradiction. The new test explicitly covers stale plus mutation or
  status contradiction.
- The hidden `.p2p/system` path is outside the Anvien file projection; direct
  source/test evidence is required and will be reported honestly.
- The worktree is dirty with unrelated owner changes; only scoped files may be
  staged, and no cleanup/reset is authorized.
