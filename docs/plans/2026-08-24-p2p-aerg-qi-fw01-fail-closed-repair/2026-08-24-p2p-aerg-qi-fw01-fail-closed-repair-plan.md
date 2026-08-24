# P2P AERG QI/FW01 Fail-Closed Repair Plan

## Metadata

- Date: `2026-08-24`
- Status: `ready_for_supervisor_review_handoff` (same Goal; post-review contract-mismatch repair complete)
- Plan: `docs/plans/2026-08-24-p2p-aerg-qi-fw01-fail-closed-repair/2026-08-24-p2p-aerg-qi-fw01-fail-closed-repair-plan.md`
- Evidence: `docs/plans/2026-08-24-p2p-aerg-qi-fw01-fail-closed-repair/2026-08-24-p2p-aerg-qi-fw01-fail-closed-repair-evidence.md`
- Benchmark: `docs/plans/2026-08-24-p2p-aerg-qi-fw01-fail-closed-repair/2026-08-24-p2p-aerg-qi-fw01-fail-closed-repair-benchmark.md`
- Actual status: `docs/plans/2026-08-24-p2p-aerg-qi-fw01-fail-closed-repair/2026-08-24-p2p-aerg-qi-fw01-fail-closed-repair-actual-status.md`

## Goal

Close the two confirmed fail-open paths in the development-source AERG quality boundary: required QI evaluations must not treat non-proof states as verified, and the FW01 compatibility seam must not discard an actual unsafe AERG result before checkpointing. Preserve the existing AERG engine/model semantics, current QI path, FW01 behavior for fresh evidence, protected state, and audit history.

## Rules

- Complete P0 actual status before implementation work.
- Test-first is explicit for this repair: add RED tests and commit them before production edits.
- Production repair is limited to `.p2p/system/p2p_capabilities/quality_intelligence.py` and `.p2p/system/p2p_capabilities/p2p_fw01_loop.py` unless a mechanical necessity is proven.
- Preserve correct AERG engine/model behavior and do not create a second QI engine, freshness subsystem, verifier, router, scheduler, queue, database, promotion path, or release path.
- Use actual AERG/FW01 runtime paths in behavior tests; compatibility shape must not weaken evidence semantics.
- Preserve owner-dirty files and all prior reports. Do not run Owner approval, Supervisor review, promotion, release, deployment, or host mutation.
- Run Anvien detect-changes before every implementation-slice commit; disclose hidden-path graph limitations rather than inferring low impact.
- Record evidence and measured counts as they are produced. The final state is a handoff for Supervisor review, not Supervisor review itself.

## Problem

`build_quality_verdict()` currently lets required result values such as `STALE`, `EXPIRED`, `WARN`, and `UNKNOWN` fall through to `QUALITY_VERIFIED` and `checkpoint_allowed=True`. Separately, `Fw01Loop.step()` omits `aerg_result` for a compatibility QI callable that has no such parameter, then trusts that callable's affirmative checkpoint result. An actual stale AERG observation can therefore be persisted as `VERIFIED`/`CHECKPOINTED`.

## Scope

- Add direct QI matrix coverage for proof, failure, non-proof, and unknown required-evaluation statuses while preserving optional-evaluation distinction.
- Add real FW01 step-path compatibility coverage for fresh and unsafe AERG results.
- Correct QI required-status classification with a small fail-closed semantic classifier.
- Add a narrow FW01 post-QI safety clamp that requires the actual AERG result to be supported, verified, current, subject-bound, provenance-bound, and contract-supporting before a checkpoint can be accepted.
- Run focused, integration, full capability, C43/RF01, compile, validator, protected-state, and audit-history checks.

## Non-Goals

- No AERG engine/model redesign or freshness rule change.
- No new QI subsystem, state machine, database, scheduler, queue, router, verifier, promotion/release/deployment path, or host/GitHub action.
- No repair of the seven inherited framework validator classes.
- No changes to `.19`, `.74`, CPT01-R2, RF01, C43, `promotion.allowed`, release/deployment artifacts, GitHub host state, Owner authority, or prior REJECT reports.
- No Supervisor review, independent verification, Owner approval, promotion, release, deployment, or new Goal.

## Requirements

- Required proof statuses remain accepted only for current contract equivalents such as `PASS`, `VERIFIED`, and `VERIFIED_IMPLEMENTED`.
- `STALE`, `EXPIRED`, `WARN`, `WARNING`, `UNKNOWN`, `NOT_RUN`, `NOT_AVAILABLE`, `UNAVAILABLE`, `SKIPPED`, `INCOMPLETE`, and unrecognized required statuses must fail closed.
- Optional informational evaluations remain non-blocking unless the existing contract already marks them required.
- The compatibility callable may omit `aerg_result`, but it may not remove the actual AERG safety boundary.
- AERG `SUPPORTED` alone is insufficient for FW01 checkpointing: the actual result must also be `VERIFIED`, `CURRENT`, subject-bound, provenance-bound, and explicitly support the existing contract.
- Contradiction precedence and stale observability remain intact; current QI mappings remain intact for stale, contradicted, subject-mismatch, and insufficient AERG results.

## Acceptance Criteria

- RED tests fail on the current `6e531896` subject before production edits and are committed separately.
- After repair, all new QI/FW01 tests pass, fresh evidence still checkpoints through the compatibility seam, and unsafe AERG states cannot produce `QUALITY_VERIFIED`, `checkpoint_allowed=True`, `VERIFIED`, or `CHECKPOINTED`.
- AERG focused/freshness/A-Z plus freshness extensions, QI, FW01, full capability, C43/RF01, compile, and validator checks have fresh results recorded.
- `NEW_TEST_FAILURES=0`, `NEW_RUNTIME_FINDINGS=0` within this invariant, and `NEW_VALIDATOR_FAILURE_CLASSES=0`; validator remains an explicit 52/59 with exactly seven inherited classes.
- Protected state and prior REJECT history are unchanged.
- Coder report, problem report, notes-log links, evidence, benchmark, and actual-status refreshes are committed; final terminal for this continuation is `P2P_AERG_FW01_QI_STATUS_CONTRACT_REPAIR_READY_FOR_SUPERVISOR_REVIEW` only if all required gates pass.

## Checklist

- [x] P0-A: Complete actual status before implementation work.
  - Goal: establish the real current state and the exact bounded repair subject.
  - Work Steps: refresh Anvien; inspect current Git subject/ancestry, source paths, report-only separation, protected state, and relevant SPECs; classify the QI and FW01 surfaces.
  - Implementation Gate: current HEAD, scope, production/report separation, and known graph limitation are recorded in actual-status.
  - Acceptance: P0 actual-status is complete and permits only the two bounded production repairs.

### P1: RED reproduction and QI required-status boundary

- Phase Goal: create executable regressions that prove the generic required-evaluation bypass before production edits, then correct only the QI classification.
- Phase Boundary:
  - In scope: QI required-evaluation status matrix and its direct tests.
  - Out of scope: FW01 production repair, AERG engine/model changes, optional-evaluation semantics.
  - Dependencies: P0 actual-status; current QI source and test contract.
- Phase Implementation Rule: implement P1-A RED tests and commit them; then implement P1-B production correction and commit it separately.
- Ordered Slice List:
  - P1-A: Add and run RED QI non-proof-status matrix.
  - P1-B: Add narrow fail-closed required-status classification.

- [x] P1-A: Add and run RED QI non-proof-status matrix
  - Goal: prove that required non-proof and unknown statuses currently reach the unsafe verified branch.
  - Scope Boundary:
    - Editable: `.p2p/system/p2p_capabilities/tests/test_aerg_qi_fw01_fail_closed.py`.
    - Inspect-only: `quality_intelligence.py`, AERG engine/model, protected state.
    - Preserve-only: existing QI tests and all unrelated tests.
    - Out of scope: production source edits.
  - Non-Goals: no test-only bypass, no artificial AERG state for the compatibility integration case, no production changes.
  - Pre-flight Questions:
    - Data source: real `build_quality_verdict()` and real required-evaluation input shape.
    - Display permission: N/A; no UI.
    - DB read flow: N/A; QI is in-memory.
    - DB write flow: N/A; only isolated FW01 test artifacts are quarantined under repo `.tmp`.
    - Render location: N/A; structured verdict and checkpoint JSON.
    - UI behavior flow: N/A; Python runtime boundary.
    - Docker runtime: N/A; no public app/runtime change.
    - Playwright target: N/A; no browser surface.
    - Behavior test: required status matrix plus real FW01 compatibility step path.
    - Cleanup/quarantine: repo-local `.tmp` Git worktrees removed through `git worktree remove --force` in test cleanup.
    - External side effects: none.
    - N/A notes: no release/deployment/host action.
  - Work Steps:
    1. Add a direct required-status matrix covering proof, failure, STALE, EXPIRED, WARN/WARNING, UNKNOWN, NOT_RUN, unavailable variants, SKIPPED, INCOMPLETE, and an unrecognized value; assert the requested fail-closed properties.
       - UI flow check: N/A.
       - DB/data flow check: verdict fields are the observable data boundary.
       - Render location check: N/A.
       - Evidence target: E1-P1A-TEST1.
    2. Add the compatibility-signature QI callable test with real FW01 step execution and actual stale AERG observation; run before production edits and retain the failing result.
       - UI flow check: N/A.
       - DB/data flow check: inspect isolated FW01 checkpoint JSON and returned status.
       - Render location check: N/A.
       - Evidence target: E1-P1A-RED1.
  - Implementation Gate:
    - Anvien impact/file-detail evidence for the new test boundary is recorded; no production file is edited before the RED command fails.
  - Acceptance:
    - Source: only the new test file is added in this slice.
    - Runtime/UI: N/A.
    - DB/data: isolated worktree artifacts are cleaned.
    - Behavior test: targeted test command fails on the known current bypass.
    - Cleanup/quarantine: no test worktree remains after cleanup.
    - Evidence IDs: E1-P1A-TEST1, E1-P1A-RED1.
    - Actual-status rows refreshed: QI generic required-evaluation surface remains `wrong` pending P1-B.
  - Evidence Targets: RED output, exact failing assertions, test file hash, cleanup proof.
  - Actual-status Update: classify test coverage as bound and the production QI surface as still wrong until P1-B.
  - Commit Boundary: separate RED checkpoint commit before any production edit.

- [x] P1-B: Add narrow fail-closed required-status classification
  - Goal: classify required evaluation results as proof, known failure, known non-proof, unavailable, or unknown without changing optional semantics.
  - Scope Boundary:
    - Editable: `.p2p/system/p2p_capabilities/quality_intelligence.py`.
    - Inspect-only: QI callers, AERG engine/model, FW01.
    - Preserve-only: existing AERG mapping and current proof/failure vocabulary.
    - Out of scope: FW01 clamp and framework validator debt.
  - Non-Goals: no second QI engine or new persistence/state machine.
  - Pre-flight Questions:
    - Data source: required evaluation mapping and declaration.
    - Display permission: N/A.
    - DB read flow: N/A.
    - DB write flow: N/A.
    - Render location: returned quality verdict.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: RED matrix becomes green; existing QI suite remains green.
    - Cleanup/quarantine: N/A.
    - External side effects: none.
    - N/A notes: no public runtime.
  - Work Steps:
    1. Refresh source/impact evidence and implement the smallest classifier inside the existing required-evaluation loop; fail closed for unknown values.
       - UI flow check: N/A.
       - DB/data flow check: verdict fields only.
       - Render location check: N/A.
       - Evidence target: E1-P1B-SRC1.
    2. Run the new matrix and full QI tests; inspect diff for optional distinction and no AERG engine/model changes.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: N/A.
       - Evidence target: E1-P1B-TEST1.
  - Implementation Gate:
    - P1-A RED checkpoint exists; Anvien file-detail/impact limitation is recorded; only the QI target is editable in this slice.
  - Acceptance:
    - Source: required non-proof and unknown statuses cannot reach `QUALITY_VERIFIED`.
    - Runtime/UI: N/A.
    - DB/data: N/A.
    - Behavior test: new matrix and QI suite pass.
    - Cleanup/quarantine: N/A.
    - Evidence IDs: E1-P1B-SRC1, E1-P1B-TEST1.
    - Actual-status rows refreshed: QI generic required-evaluation surface transitions `wrong -> correct`.
  - Evidence Targets: production diff, targeted and regression test outputs, detect-changes result.
  - Actual-status Update: refresh QI classification and preserve sibling surfaces.
  - Commit Boundary: separate QI repair commit after detect-changes.

### P2: FW01 compatibility safety boundary

- Phase Goal: ensure compatibility API shape cannot erase the actual AERG safety result before checkpoint persistence, while fresh evidence remains usable.
- Phase Boundary:
  - In scope: FW01 post-execution AERG/QI/checkpoint seam and integration tests.
  - Out of scope: AERG engine/model, generic QI classification already handled in P1, protected state.
  - Dependencies: P1 RED/repair commits and current FW01 source.
- Phase Implementation Rule: implement P2-A compatibility RED coverage and commit it; then implement P2-B clamp and commit it separately.
- Ordered Slice List:
  - P2-A: Add and run RED FW01 compatibility matrix.
  - P2-B: Add narrow actual-AERG safety clamp.

- [x] P2-A: Add and run RED FW01 compatibility matrix
  - Goal: execute the real FW01 step path with a QI callable lacking `aerg_result` and prove stale AERG can currently be checkpointed unsafely.
  - Scope Boundary:
    - Editable: the new repair test file only.
    - Inspect-only: `p2p_fw01_loop.py`, current QI, AERG engine/model.
    - Preserve-only: existing FW01 tests and helper behavior.
    - Out of scope: production source.
  - Non-Goals: no compatibility API redesign.
  - Pre-flight Questions:
    - Data source: real FW01 isolated Git worktree and actual AERG result.
    - Display permission: N/A.
    - DB read flow: durable `.p2p/fw01.json` checkpoint read.
    - DB write flow: isolated test worktree only.
    - Render location: returned step result and checkpoint JSON.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: fresh compatibility path allowed; stale and unsafe AERG paths blocked.
    - Cleanup/quarantine: repo-local worktree cleanup in `finally`.
    - External side effects: none.
    - N/A notes: no host state.
  - Work Steps:
    1. Add fresh and stale real-step cases with a no-`aerg_result` compatibility callable; assert current stale case fails RED and fresh case remains a candidate for allowed behavior.
       - UI flow check: N/A.
       - DB/data flow check: inspect returned status plus durable checkpoint fields.
       - Render location check: N/A.
       - Evidence target: E2-P2A-RED1.
    2. Add direct unsafe AERG-result cases for contradiction, subject mismatch, and insufficient evidence at the same safety boundary, using actual AERG result shapes.
       - UI flow check: N/A.
       - DB/data flow check: checkpoint must not contain `VERIFIED`/`CHECKPOINTED`.
       - Render location check: N/A.
       - Evidence target: E2-P2A-TEST1.
  - Implementation Gate:
    - P1 repair is committed; no FW01 production edit occurs before the compatibility RED case fails.
  - Acceptance:
    - Source: only tests added.
    - Runtime/UI: N/A.
    - DB/data: isolated worktrees cleaned.
    - Behavior test: stale compatibility case fails before P2-B.
    - Cleanup/quarantine: no test worktree remains.
    - Evidence IDs: E2-P2A-RED1, E2-P2A-TEST1.
    - Actual-status rows refreshed: FW01 compatibility seam remains `wrong` pending P2-B.
  - Evidence Targets: real step output, checkpoint JSON, test hash, cleanup proof.
  - Actual-status Update: preserve current QI path and mark FW01 compatibility seam as wrong until clamp repair.
  - Commit Boundary: separate FW01 RED checkpoint commit if not included in P1-A; otherwise retain one clearly scoped RED checkpoint.

- [x] P2-B: Add narrow actual-AERG safety clamp
  - Goal: require the actual AERG result to prove current supported evidence before accepting any compatibility QI checkpoint.
  - Scope Boundary:
    - Editable: `.p2p/system/p2p_capabilities/p2p_fw01_loop.py`.
    - Inspect-only: QI classifier, AERG engine/model, checkpoint serializer.
    - Preserve-only: current QI path and fresh execution behavior.
    - Out of scope: new verifier/state machine or unrelated FW01 behavior.
  - Non-Goals: no duplicate QI engine; no compatibility parameter removal.
  - Pre-flight Questions:
    - Data source: actual `_fw04_aerg_result` produced by the current FW01 path.
    - Display permission: N/A.
    - DB read flow: checkpoint is the observable persistence boundary.
    - DB write flow: existing FW01 state writer only.
    - Render location: existing quality/checkpoint fields.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: compatibility fresh allow and unsafe block matrix.
    - Cleanup/quarantine: existing test cleanup.
    - External side effects: none.
    - N/A notes: no release/runtime host.
  - Work Steps:
    1. Re-run Anvien file/impact checks, then add a narrow clamp after QI verdict construction and before checkpoint gating, reusing current failure vocabulary and preserving contradiction/stale details.
       - UI flow check: N/A.
       - DB/data flow check: checkpoint gate consumes clamped verdict.
       - Render location check: N/A.
       - Evidence target: E2-P2B-SRC1.
    2. Run compatibility matrix, existing FW01 tests, QI/AERG focused tests, and inspect changed-file scope.
       - UI flow check: N/A.
       - DB/data flow check: returned status and durable checkpoint remain fail-closed.
       - Render location check: N/A.
       - Evidence target: E2-P2B-TEST1.
  - Implementation Gate:
    - P2-A RED checkpoint exists; actual AERG safe predicate and failure mapping are derived from current source before editing.
  - Acceptance:
    - Source: only FW01 seam logic changes.
    - Runtime/UI: N/A.
    - DB/data: fresh compatibility checkpoint remains normal; unsafe AERG cannot be verified/checkpointed.
    - Behavior test: matrix and FW01 suite pass.
    - Cleanup/quarantine: all test worktrees removed.
    - Evidence IDs: E2-P2B-SRC1, E2-P2B-TEST1.
    - Actual-status rows refreshed: FW01 compatibility seam transitions `wrong -> correct`.
  - Evidence Targets: source diff, runtime matrix, checkpoint JSON, detect-changes result.
  - Actual-status Update: record exact safety predicate and preserve-only siblings.
  - Commit Boundary: separate FW01 repair commit after detect-changes.

### P3: Regression, audit preservation, and handoff

- Phase Goal: prove no new failures in the requested bounded invariant, preserve inherited debt and protected state, and prepare the coder handoff.
- Phase Boundary:
  - In scope: fresh required suites, validator classification, protected-state/audit checks, evidence/report artifacts.
  - Out of scope: Supervisor review and Owner actions explicitly forbidden by the user.
  - Dependencies: P1-B and P2-B repair commits.
- Phase Implementation Rule: run validation, update evidence/actual-status/benchmark/report artifacts, and stop at handoff.
- Ordered Slice List:
  - P3-A: Run final regressions and preservation checks.
  - P3-B: Write coder/problem reports and handoff terminal.

- [x] P3-A: Run final regressions and preservation checks
  - Goal: establish fresh test, compile, validator, protected-state, and audit-history evidence.
  - Scope Boundary:
    - Editable: evidence/benchmark/actual-status report artifacts only.
    - Inspect-only: all source and protected paths.
    - Preserve-only: seven inherited validator failures, prior REJECT reports, `.19`/`.74`/CPT01-R2/RF01/C43/host state.
    - Out of scope: repairs to inherited validator debt.
  - Non-Goals: no whole-framework PASS claim.
  - Pre-flight Questions:
    - Data source: fresh commands and Git/source re-derivation.
    - Display permission: N/A.
    - DB read flow: protected JSON/report inspection only.
    - DB write flow: report artifacts only.
    - Render location: evidence ledgers and coder handoff.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: required regression list from the user brief.
    - Cleanup/quarantine: remove only plan-created temporary worktrees.
    - External side effects: none.
    - N/A notes: no Supervisor/Owner/host actions.
  - Work Steps:
    1. Run focused AERG/freshness/A-Z+2/QI/FW01 and then full capability, C43/RF01, compile, and validator commands; record exact counts and exit codes.
       - UI flow check: N/A.
       - DB/data flow check: protected state read-only.
       - Render location check: N/A.
       - Evidence target: E3-P3A-TEST1.
    2. Re-derive protected state, prior REJECT immutability, production/report separation, and final scoped diff; run Anvien detect-changes before final artifact commit.
       - UI flow check: N/A.
       - DB/data flow check: no protected mutation.
       - Render location check: N/A.
       - Evidence target: E3-P3A-PROOF1.
  - Implementation Gate:
    - P1/P2 repair commits exist and no unresolved same-invariant runtime finding remains.
  - Acceptance:
    - Source: production diff is only the two intended files.
    - Runtime/UI: N/A.
    - DB/data: protected state unchanged.
    - Behavior test: NEW failures are zero within scope; validator remains seven inherited failures.
    - Cleanup/quarantine: plan-created temporary outputs are removed or explicitly retained as evidence-only.
    - Evidence IDs: E3-P3A-TEST1, E3-P3A-PROOF1.
    - Actual-status rows refreshed: all repaired surfaces correct; external validator debt inherited.
  - Evidence Targets: regression table, hashes, protected-state proof, detect-changes.
  - Actual-status Update: final classifications and handoff readiness.
  - Commit Boundary: report/evidence commit only after all required validation passes.

- [x] P3-B: Write coder/problem reports and handoff terminal
  - Goal: provide a precise repair handoff without performing the forbidden review/approval actions.
  - Scope Boundary:
    - Editable: `reports/coder/`, `reports/problem/`, `docs/notes_decisions_log/`, and this plan’s evidence/benchmark/actual-status files.
    - Inspect-only: production source and protected state.
    - Preserve-only: all prior reports and audit history.
    - Out of scope: Supervisor report or independent-verification report.
  - Non-Goals: no acceptance claim beyond ready-for-Supervisor-review.
  - Pre-flight Questions:
    - Data source: completed evidence ledgers and fresh final commands.
    - Display permission: N/A.
    - DB read flow: N/A.
    - DB write flow: report artifacts only.
    - Render location: coder/problem reports and notes link.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: report references exact tests and outputs.
    - Cleanup/quarantine: no new temporary state.
    - External side effects: none.
    - N/A notes: terminal stops before Supervisor/Owner.
  - Work Steps:
    1. Refresh actual-status, evidence, and benchmark with final hashes/counts and link the coder/problem reports in today’s notes log.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: report artifacts.
       - Evidence target: E3-P3B-REPORT1.
    2. Verify final status and emit only `P2P_AERG_QI_FW01_FAIL_CLOSED_REPAIR_READY_FOR_SUPERVISOR_REVIEW` when criteria are met; otherwise emit a precise blocked/rejected terminal.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: final handoff message.
       - Evidence target: E3-P3B-HANDOFF1.
  - Implementation Gate:
    - All required validation and preservation checks are complete; no report overwrites a prior artifact.
  - Acceptance:
    - Source: no new production edits.
    - Runtime/UI: N/A.
    - DB/data: protected state unchanged.
    - Behavior test: report accurately reflects results.
    - Cleanup/quarantine: no untracked plan temp state.
    - Evidence IDs: E3-P3B-REPORT1, E3-P3B-HANDOFF1.
    - Actual-status rows refreshed: final handoff state recorded.
  - Evidence Targets: coder report, problem report, notes link, final status.
  - Actual-status Update: mark plan ready for the explicitly separate Supervisor lane.
  - Commit Boundary: final artifact commit; do not run Supervisor review.

### P4: FW01/QI execution-status contract mismatch continuation

- Phase Goal: restore the legitimate fresh FW01 checkpoint without widening QI's canonical execution vocabulary or weakening any fail-closed boundary.
- Phase Boundary:
  - In scope: source/spec/caller re-derivation, one real FW01-to-production-QI RED test, one narrow FW01 status projection if proven necessary, conservative mapping tests, and bounded regression/handoff artifacts.
  - Out of scope: AERG engine/model changes, QI allowlist expansion, compatibility safety-clamp redesign, Supervisor review, independent verification, Owner approval, promotion, release, deployment, and a new Goal.
  - Dependency: prior P1/P2 repair commits and the current independent REJECT are preserved audit inputs, not authority.
- Phase Implementation Rule: test-first RED commit, then the minimum contract-owner production commit, then fresh regression and handoff artifacts.
- Ordered Slice List:
  - P4-A: bind canonical execution/loop vocabulary and commit the real production-path RED test.
  - P4-B: project only proven successful FW01 loop state to QI's canonical execution status; prove negative mappings remain non-success.
  - P4-C: rerun bounded regressions, preserve protected/audit state, and hand off for a separate Supervisor review.

- [x] P4-A: Bind vocabulary and add RED fresh-checkpoint regression
  - Goal: prove the current real production FW01 -> AERG -> QI path produces `QUALITY_VERIFIED` with `checkpoint_allowed=False` and durable `QUALITY_REVIEW/BLOCKED` solely because raw `TASK_DONE_CONTINUE` enters QI.
  - Scope Boundary:
    - Editable: bounded regression test only.
    - Inspect-only: QI, FW01, backend/host execution contracts, AutoPilot loop vocabulary, callers, and relevant SPECs.
    - Preserve-only: AERG engine/model, prior REJECT reports, protected state, and the existing fail-closed compatibility seam.
  - Acceptance: source evidence proves `SUCCESS` is QI's checkpoint execution token and `TASK_DONE_CONTINUE` is a loop/control-flow result; the RED test fails before production edit and is committed separately.
  - Evidence Targets: `E4-P4A-SRC1`, `E4-P4A-RED1`.
  - Commit Boundary: test-only RED commit.

- [x] P4-B: Apply the narrow FW01 projection and falsify unsafe mappings
  - Goal: normalize only the proven successful completed-execution path to QI's canonical `SUCCESS`; failed, blocked, not-run, unknown, and unrecognized states must not normalize to `SUCCESS`.
  - Scope Boundary:
    - Editable: `.p2p/system/p2p_capabilities/p2p_fw01_loop.py` and bounded regression assertions only if mechanically required.
    - Preserve-only: `quality_intelligence.py`, `aerg_engine.py`, `aerg_model.py`, and the existing `_clamp_quality_verdict_to_aerg` safety boundary.
  - Acceptance: fresh real FW01 path persists `VERIFIED/CHECKPOINTED`; all unsafe AERG/required-status/compatibility cases remain blocked; no blanket `TASK_* -> SUCCESS` mapping exists.
  - Evidence Targets: `E4-P4B-SRC1`, `E4-P4B-TEST1`.
  - Commit Boundary: narrow production repair commit, followed by a separate coverage commit if needed.

- [x] P4-C: Regress, preserve, and hand off
  - Goal: establish no new test/runtime/validator failure class, preserve protected/audit state, and stop at the exact requested handoff terminal.
  - Scope Boundary:
    - Editable: plan/evidence/benchmark/actual-status, coder/problem report, and notes-log artifacts only.
    - Inspect-only: all protected and external-host state.
    - Out of scope: Supervisor/independent verification, Owner approval, promotion, release, deployment, and host mutation.
  - Acceptance: required suites are freshly rerun and interpreted; `NEW_TEST_FAILURES=0`, `NEW_RUNTIME_FINDINGS=0`, `NEW_VALIDATOR_FAILURE_CLASSES=0`; prior REJECT history and owner-dirty files are preserved.
  - Evidence Targets: `E4-P4C-TEST1`, `E4-P4C-PROOF1`, `E4-P4C-HANDOFF1`.
  - Commit Boundary: final report/evidence commit only after all required checks pass.

## Risk Notes

- The repository has extensive pre-existing owner-dirty changes; all changes must be staged by exact path and checked against the pre-repair status.
- Anvien’s indexed registry has duplicate names and its file projection does not resolve hidden `.p2p/system` target files; direct Git/source/runtime evidence is required and this limitation must remain visible.
- Compatibility callables may return incomplete or malformed verdict mappings; the FW01 clamp must fail closed without inventing a second state machine.
- The full capability suite is long-running; communicate bounded progress and preserve exact exit codes.
- The seven validator failures are inherited framework debt and must not be reclassified as new or repaired in this scope.

## Final Handoff State

- Source/test subject before documentation artifacts: `a716a5066db4b213af8ef44a392afbf0e4329ce6` on `codex/p2p-post74-development-01`.
- Production repair commits for this continuation: `66657b3` (FW01 projection to canonical QI execution status); `quality_intelligence.py`, `aerg_engine.py`, and `aerg_model.py` are unchanged for this continuation.
- Test commits for this continuation: `36f6877` (real-path RED), `c4c5fc9` (unsafe mapping falsification), `a716a50` (test-fixture contract corrections).
- Prior production repair commits remain preserved: `ce641d6` (QI required-status classifier), `cbf7af9` (FW01 AERG safety clamp and fresh-observation ordering).
- Full capability result: `362 tests`, `OK`, `6 skipped`, exit `0`; the unqualified Windows runner's nine decoding errors were classified as invocation-only and were not counted as product failures after the authoritative UTF-8 rerun.
- Current terminal: `P2P_AERG_FW01_QI_STATUS_CONTRACT_REPAIR_READY_FOR_SUPERVISOR_REVIEW`.
- The final documentation/report commit is a descendant of the source/test subject and contains no production source. Supervisor review, independent verification, Owner approval, promotion, release, deployment, and host mutation remain unperformed and out of scope.
