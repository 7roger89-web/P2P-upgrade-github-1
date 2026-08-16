# P2P-C16 Durable Development Roadmap and Release Lineage Foundation Plan

## Metadata

- Date: `2026-08-16`
- Status: `in_progress`
- Plan: `docs/plans/2026-08-16-p2p-c16-roadmap-lineage/2026-08-16-p2p-c16-roadmap-lineage-plan.md`
- Evidence: `docs/plans/2026-08-16-p2p-c16-roadmap-lineage/2026-08-16-p2p-c16-roadmap-lineage-evidence.md`
- Benchmark: `docs/plans/2026-08-16-p2p-c16-roadmap-lineage/2026-08-16-p2p-c16-roadmap-lineage-benchmark.md`
- Actual status: `docs/plans/2026-08-16-p2p-c16-roadmap-lineage/2026-08-16-p2p-c16-roadmap-lineage-actual-status.md`

## Goal

Make the existing P2P project state authoritative for fresh-session recovery and make release packaging reject a development source that silently regresses below the promoted `8.4.7-C-codex.19` baseline. The implementation remains a compact extension of existing governance/project state; it does not promote C16, certify live delegation, or start C17.

## Rules

- Complete P0 actual status before implementation work.
- Update each checklist item immediately when it is completed.
- Record evidence as work completes.
- Record benchmarkable counts or measurements when they are taken.
- Update later phase status assumptions, next actions, and work steps when actual-status evidence changes the repo state.
- After completing a phase or implementation slice and refreshing `actual-status.md`, update the next affected phase's work steps as needed to match the latest repo reality, while preserving that phase's original goal, scope, acceptance criteria, and major phase order.
- Run Anvien detect-changes before every implementation-slice checkpoint when implementation work was performed; the repository has no `.git`, so record the exact exit-129 limitation instead of initializing Git.
- This is a local Python/governance change; browser, Playwright, and Docker evidence are not applicable unless the implementation unexpectedly adds a public runtime.
- Every implementation phase is decomposed into narrow slices. Work starts from a slice ID and stops after the requested C16 boundary is verified.
- Hidden fallback is forbidden. An absent, malformed, conflicting, or stale lineage record must fail closed with an explicit reason.
- Tests use temporary project/state/artifact roots and never mutate official `.19`, prior release ZIPs, immutable baseline sources, or user projects.
- No network, hooks, proxy, connectors, external provider, dependency installation, promotion, release, deployment, parallelism, background queue, scheduler, or remote operator is introduced.
- No second router, agent, ledger, FACT authority, certification system, or large project-management subsystem is introduced.
- Existing FACT_LEDGER, Live Specs, Goal/eval contracts, Execution Ledger, Decision Trace, approval, drift, doctor, installer, and rollback controls remain authoritative; the new control record references them rather than copying them.
- All SPEC/docs changes are UTF-8 without BOM.

## Problem

The promoted official artifact is `8.4.7-C-codex.19` with SHA-256 `3a9ee51321e1f5e40e35ce73eb90727cddb571a672aa095d16d76af2feb03dd8`, but the development checkout and the C15 candidate still embed `.15`. The current packager validates only the checkout `VERSION` against `manifest/package.json`, so it can produce a clean-looking candidate whose ancestry is below the official baseline. Roadmap, capability state, research decisions, and C15's foundation/live-certification split are spread across reports and chat-bound context instead of one compact durable recovery surface.

## Scope

- Add one versioned development-control record under the existing `governance/` authority, with explicit official baseline, lineage policy, capability/Goal status, roadmap, provenance, architectural invariant references, research decisions, and beginner status projection inputs.
- Add a standard-library-only loader/validator/status/mutation CLI in `scripts/p2p_development_control.py` and package it through the existing release allowlist.
- Integrate the existing release builder with explicit baseline/lineage validation before any build-side writes; filename numbering is never authority.
- Record the C15 drift root cause and the exact unpromoted candidate lineage without changing C15 implementation or the official `.19` ZIP.
- Add focused behavioral tests for R1-R18 and run affected C10-C15, governance, doctor, security, package, and full regression checks.
- Create/update C16 plan, evidence, benchmark, actual-status, coder, and supervisor artifacts.

## Non-Goals

- Do not promote the C15 or C16 candidate.
- Do not change the official `.19` artifact or rewrite C15 implementation.
- Do not implement C17 safe bounded parallel execution, adaptive orchestration, remote/control bridge, live delegation certification, controlled continuation, worker pools, scheduler, background queue, or remote operator.
- Do not rebuild all earlier capabilities, replace project-status/goal/ledger/FACT/Decision Trace authority, vendor external research repositories, or create a permanent project-management subsystem.
- Do not claim C08 or C09 as complete; do not infer identity from generic delegation.

## Requirements

- Official baseline is explicit and hash-bound; promotion and approval references are retained.
- Each material candidate record contains `based_on_official_version`, `based_on_official_sha`, `development_goal`, `candidate_version/label`, `candidate_sha`, `embedded_version`, and `promotion_status`.
- The C15 candidate is recorded as unpromoted `.15` with its supplied SHA and `LINEAGE_REGRESSION_BLOCKED` status.
- The drift root cause is recorded as `RELEASE_BASELINE_NOT_PROPAGATED`, with contributing stale packager input/development metadata evidence.
- Roadmap statuses are limited to `DONE`, `ACTIVE`, `PLANNED`, `DEFERRED`, `BLOCKED`, and `REJECTED`; unknown status mutation fails safely and each mutation records what/why/evidence/when.
- C08 is `DEFERRED`; C09 is `BLOCKED / EVENT_EVIDENCE_UNAVAILABLE`.
- C15 records `BOUNDED_DELEGATION_FOUNDATION_READY=YES` and `LIVE_DELEGATION_CERTIFIED=NO` separately.
- Design Intelligence `.19` has 174 faculties as metadata design cognition; `p2p-uiux` is primary and Aesthetica is optional/noncanonical.
- Canonical identities remain exactly eight with denominator 8 and full quorum `8/8`.
- Packager rejects a current source/candidate version below `.19` unless an explicitly enabled historical-maintenance workflow exists; the default is disabled.
- A fresh process can load and render the status without chat transcript input.

## Acceptance Criteria

- `python scripts/p2p_development_control.py validate --root .` returns `PASS` for the committed control record.
- `python scripts/p2p_development_control.py status --root . --json` deterministically returns official `.19`, C10-C15 completion, C09 blocked, C08 deferred, C16 active, and the next candidate direction.
- Roadmap mutation on a temporary copy appends provenance and rejects unknown status.
- A temporary source with explicit `.18` ancestry is rejected by package lineage validation before build-side mutation; a filename-only `.19` claim is not accepted.
- Existing historical release verification remains compatible when its archive predates the new control record; the official `.19` hash remains unchanged.
- Focused C16 tests cover R1-R18, and affected existing tests plus full unittest regression pass or record a real blocker.
- `scripts/doctor.py`, governance drift/security checks, and package control validation remain available; no promotion or C17 work begins.

## Checklist

- [x] P0-A: Complete actual status before implementation work.
  - Goal: establish the real current state.
  - Work Steps: inspect VERSION/runtime VERSION/manifest, governance/release records, Goal/state/ledger, C14/C15 evidence, package builder/doctor, and Anvien graph/impact; classify each target and update downstream slices.
  - Implementation Gate: no implementation starts until the actual-status file has a final P0 decision.
  - Acceptance: current baseline, drift evidence, related-file counts, preserve-only surfaces, and editable surfaces are recorded with exact evidence IDs.

### P1: Durable development-control record and fresh-session projection

- Phase Goal: create one compact, validated governance record and a deterministic status surface that references existing P2P authority.
- Phase Boundary:
  - In scope: `governance/development-control.json`, `scripts/p2p_development_control.py`, focused control-record tests, roadmap provenance mutation.
  - Out of scope: package promotion, C15 implementation, `.p2p/state/project-status.json` rewrite, new ledger/router/agent, external research downloads.
  - Dependencies: P0 evidence; existing governance, Goal, evidence, Decision Trace, and canonical identity contracts.
- Phase Implementation Rule: do not implement `P1` directly. Implement `P1-A`, verify it, record evidence, refresh actual-status, checkpoint if possible, then continue to `P1-B`.
- Ordered Slice List:
  - P1-A: Define and validate the compact control record.
  - P1-B: Add fresh-session status projection and provenance-safe roadmap mutation.

- [x] P1-A: Define and validate the compact control record.
  - Goal: make official baseline, lineage schema, capabilities, roadmap, research decisions, invariants, and provenance machine-readable without duplicating source contents.
  - Scope Boundary:
    - Editable: new `governance/development-control.json` and new validator module.
    - Inspect-only: existing FACT_LEDGER, Live Specs, Goal/state, Execution Ledger, Decision Trace, release/approval reports, C10-C15 implementation.
    - Preserve-only: official `.19`, C15 candidate, prior artifacts, canonical profiles.
    - Out of scope: package builder integration and any runtime capability change.
  - Non-Goals: no automatic promotion, no upstream refresh, no candidate rebuild, no new persistent ledger.
  - Pre-flight Questions:
    - Data source: user C16 brief plus existing local reports/records; no network.
    - Display permission: read-only status projection; owner approval remains external for protected actions.
    - DB read flow: N/A; JSON governance record is the existing project-local control boundary.
    - DB write flow: N/A; atomic file write only for explicit roadmap mutation.
    - Render location: CLI JSON/plain-text output.
    - UI behavior flow: N/A; no public UI.
    - Docker runtime: N/A; no app/runtime service.
    - Playwright target: N/A; no browser surface.
    - Behavior test: load/validate control record and reject malformed/unknown values.
    - Cleanup/quarantine: all mutation tests use repo-local temporary copies.
    - External side effects: none.
    - N/A notes: no database, queue, worker, or remote bridge is in scope.
  - Work Steps:
    1. Add the versioned control JSON with explicit baseline/hash/approval references, C08-C15 state, C16 roadmap, original foundation families, research registry, Superlearn principles, and invariant references.
       - UI flow check: N/A; CLI is the user-visible boundary.
       - DB/data flow check: control JSON -> validator -> structured result.
       - Render location check: control record remains source; projections are derived.
       - Mini QA for each completed implementation slice (MUST): run the control validator and inspect deterministic JSON output.
       - Evidence target: `E1-P1A-CONTROL1`, `E1-P1A-TEST1`.
    2. Implement schema/invariant validation with exact canonical eight and fail-closed enums.
       - UI flow check: N/A.
       - DB/data flow check: malformed record -> explicit validation error, no write.
       - Render location check: no copied policy text; only safe references.
       - Mini QA for each completed implementation slice (MUST): run positive and malformed temporary fixtures.
       - Evidence target: `E1-P1A-TEST2`, `E1-P1A-ANVIEN1`.
  - Implementation Gate:
    - Before editing target files, the recorded Anvien file-detail/impact evidence must be current for the package/test siblings and the new control module must have a narrow ownership boundary.
    - No source authority conflict remains unresolved.
  - Acceptance:
    - Source: control JSON and validator agree on `.19`, exact SHA, C08/C09/C15, roadmap enums, research decisions, and canonical eight.
    - Runtime/UI: CLI validation returns `PASS` and malformed fixtures fail closed.
    - DB/data: N/A; file reads/writes are atomic and isolated.
    - Behavior test: R1-R9 and R15-R18 pass at the nearest real boundary.
    - Cleanup/quarantine: temporary fixtures are under `.tmp` or test-managed temporary roots and removed.
    - Evidence IDs: `E1-P1A-CONTROL1..E1-P1A-ANVIEN1`.
    - Actual-status rows refreshed: control record, research registry, invariants, and canonical count.
  - Evidence Targets: source review, validator output, focused tests, Anvien refresh.
  - Actual-status Update: `missing -> correct` for durable control record; preserve existing governance/ledger surfaces.
  - Commit Boundary: checkpoint after this slice if Git becomes available; otherwise record no-Git limitation. Current evidence: no `.git` is present.

- [x] P1-B: Add fresh-session status projection and provenance-safe roadmap mutation.
  - Goal: allow a new process to recover current status and record roadmap changes without chat history.
  - Scope Boundary:
    - Editable: `scripts/p2p_development_control.py`, focused tests, control record mutation history.
    - Inspect-only: existing workflow/goal state and notes log.
    - Preserve-only: existing `.p2p/state/project-status.json`, Execution Ledger, Decision Trace.
    - Out of scope: workflow orchestration changes and autonomous next-goal planning.
  - Non-Goals: no background watcher, scheduler, continuation loop, or owner approval inference.
  - Pre-flight Questions:
    - Data source: control record plus referenced existing state paths.
    - Display permission: safe beginner surface only.
    - DB read flow: N/A.
    - DB write flow: explicit roadmap mutation writes one atomic control record and appends one provenance entry.
    - Render location: `status` command plain text/JSON.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: new process status recovery; mutation provenance; unknown status failure.
    - Cleanup/quarantine: temporary copies only.
    - External side effects: none.
    - N/A notes: next-goal selection is a deterministic candidate list, not an autonomous planner.
  - Work Steps:
    1. Implement deterministic `status` projection with official/completed/blocked/deferred/current/likely-next fields.
       - UI flow check: CLI output is the user-facing surface.
       - DB/data flow check: fresh process reads only the control record and safe references.
       - Render location check: no stale cached status is authoritative.
       - Mini QA for each completed implementation slice (MUST): invoke CLI from a fresh Python process and compare JSON.
       - Evidence target: `E1-P1B-STATUS1`.
    2. Implement explicit roadmap mutation with status enum validation and provenance (`what_changed`, `why`, `evidence`, `when`).
       - UI flow check: CLI returns changed item and new status.
       - DB/data flow check: invalid status causes no write; valid status preserves history.
       - Render location check: status projection reflects the new source value.
       - Mini QA for each completed implementation slice (MUST): temporary-copy mutation and rollback-by-discard only.
       - Evidence target: `E1-P1B-MUTATION1`, `E1-P1B-TEST1`.
  - Implementation Gate:
    - P1-A validation passes and existing state remains untouched except explicit control-record test copies.
  - Acceptance:
    - Source: projection/mutation is read-only by default and atomic when explicitly requested.
    - Runtime/UI: fresh-session status contains the required beginner surface.
    - DB/data: mutation history is append-only within the control record.
    - Behavior test: R10, R14, R15, R16 pass.
    - Cleanup/quarantine: no test writes the official artifact or root state.
    - Evidence IDs: `E1-P1B-STATUS1..E1-P1B-TEST1`.
    - Actual-status rows refreshed: fresh-session recovery and roadmap provenance.
  - Evidence Targets: CLI output, temporary mutation diff, focused tests.
  - Actual-status Update: `missing -> correct` for fresh-session status surface.
  - Commit Boundary: checkpoint after this slice if possible; record detect-changes result. Current evidence: no `.git` is present.

### P2: Lineage fail-closed packaging boundary

- Phase Goal: make future material packaging consult explicit baseline/lineage state before any build-side mutation.
- Phase Boundary:
  - In scope: `scripts/package_release.py`, package allowlist/manifest entrypoint if needed, package lineage tests.
  - Out of scope: changing current VERSION to a promoted release, modifying old artifacts, or promoting a candidate.
  - Dependencies: P1 validated control record and source/packager drift evidence.
- Phase Implementation Rule: implement `P2-A`, verify fail/pass fixtures, refresh actual-status, then implement `P2-B`.
- Ordered Slice List:
  - P2-A: Integrate explicit lineage validation before build writes.
  - P2-B: Add packaging regression tests and historical-artifact compatibility checks.

- [x] P2-A: Integrate explicit lineage validation before build writes.
  - Goal: reject stale source ancestry and filename-only authority while preserving historical `verify` compatibility.
  - Scope Boundary:
    - Editable: `scripts/package_release.py`, package script allowlist, manifest entrypoint metadata only if required.
    - Inspect-only: existing release files, C14 approval/gate reports, official `.19` ZIP.
    - Preserve-only: all existing candidate ZIPs and official `.19`.
    - Out of scope: release promotion and installer behavior changes.
  - Non-Goals: no automatic VERSION propagation and no mutation of the C15 artifact.
  - Pre-flight Questions:
    - Data source: explicit governance control record, root VERSION, manifest version.
    - Display permission: package error must expose a safe reason/code.
    - DB read flow: N/A.
    - DB write flow: lineage validation precedes runtime-lock/checksum/stage writes.
    - Render location: package builder JSON/error output.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: stale `.18`/`.15` rejection and explicit `.20` acceptance fixture.
    - Cleanup/quarantine: output paths are fresh temporary repo-local targets.
    - External side effects: none; official ZIP is read-only verification target.
    - N/A notes: no installer state transition is changed.
  - Work Steps:
    1. Call control validation immediately after package version resolution and before lock/checksum/staging writes.
       - UI flow check: N/A.
       - DB/data flow check: source version + manifest + control lineage -> allow/block.
       - Render location check: error identifies explicit lineage reason, not filename inference.
       - Mini QA for each completed implementation slice (MUST): run a stale fixture and confirm no output artifact is created.
       - Evidence target: `E2-P2A-SRC1`, `E2-P2A-BLOCK1`.
    2. Keep historical extracted artifacts verifiable when no control record is embedded, while validating new embedded records when present.
       - UI flow check: N/A.
       - DB/data flow check: optional historical control -> compatibility path; embedded control -> strict validation.
       - Render location check: release manifest remains hash-based; filenames remain labels only.
       - Mini QA for each completed implementation slice (MUST): verify the supplied `.19` ZIP and a temporary new package shape.
       - Evidence target: `E2-P2A-COMPAT1`.
  - Implementation Gate:
    - P1 control validation passes; package source file impact remains scoped; no official path is an output target.
  - Acceptance:
    - Source: validation is fail-closed and occurs before side effects.
    - Runtime/UI: stale package command returns explicit `LINEAGE_REGRESSION`/`SOURCE_VERSION_STALE`.
    - DB/data: no output/checksum/runtime-lock mutation occurs on blocked build.
    - Behavior test: R11-R13 and R17 pass.
    - Cleanup/quarantine: only temporary fixture outputs are created.
    - Evidence IDs: `E2-P2A-SRC1..E2-P2A-COMPAT1`.
    - Actual-status rows refreshed: package boundary and official immutability.
  - Evidence Targets: source diff, stale-build output, no-write assertion, historical verify output.
  - Actual-status Update: `partial -> correct` for lineage guard; current root remains intentionally `STALE_BLOCKED`.
  - Commit Boundary: checkpoint after slice; no Git commit claim because `.git` remains absent.

- [x] P2-B: Add packaging regression tests and historical-artifact compatibility checks.
  - Goal: cover R11-R13/R17 and prevent future packager regressions without changing existing lifecycle contracts.
  - Scope Boundary:
    - Editable: new `tests/test_p2p_development_control.py` and/or narrow additions to `tests/test_p2p_release_packaging.py`.
    - Inspect-only: all previous package/install tests and artifact paths.
    - Preserve-only: C15 candidate and official `.19` bytes.
    - Out of scope: full package rebuild/promotion.
  - Non-Goals: no test that treats a filename as release authority.
  - Pre-flight Questions:
    - Data source: temporary copied control/source roots and existing artifact hashes.
    - Display permission: test outputs are local evidence.
    - DB read flow: N/A.
    - DB write flow: temporary roots only.
    - Render location: unittest results and report.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: trigger -> validator/packager -> observable PASS/BLOCK.
    - Cleanup/quarantine: `TemporaryDirectory`/repo-local `.tmp` only.
    - External side effects: none.
    - N/A notes: no network/provider.
  - Work Steps:
    1. Add R1-R18 behavioral tests with temporary isolated records and fresh-process subprocess checks where relevant.
       - UI flow check: N/A.
       - DB/data flow check: file-state transitions only.
       - Render location check: CLI JSON/plain-text is asserted.
       - Mini QA for each completed implementation slice (MUST): focused unittest invocation.
       - Evidence target: `E2-P2B-TEST1`.
    2. Run affected C15/C14/package/governance/doctor/security tests and full unittest discovery; record exact failures and scope.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: reports only.
       - Mini QA for each completed implementation slice (MUST): full build boundary check and regression commands.
       - Evidence target: `E2-P2B-REG1`, `E2-P2B-PROTECT1`.
  - Implementation Gate:
    - P2-A stale and historical compatibility behavior is proven before expanding regression coverage.
  - Acceptance:
    - Source: direct tests exist for every new control/packaging surface.
    - Runtime/UI: focused and affected test suites pass.
    - DB/data: protected artifacts remain byte-identical.
    - Behavior test: R1-R18 all have named PASS results.
    - Cleanup/quarantine: test roots are cleaned; no root candidate is overwritten.
    - Evidence IDs: `E2-P2B-TEST1..E2-P2B-PROTECT1`.
    - Actual-status rows refreshed: all C16 acceptance rows.
  - Evidence Targets: unittest output, package/doctor/governance/security results, hash recheck.
  - Actual-status Update: focused controls move to `correct`; unrelated earlier capabilities remain preserve-only.
  - Commit Boundary: checkpoint after verified tests; no Git commit claim because `.git` remains absent.

### P3: Evidence, regression, and closure

- Phase Goal: document the result, refresh affected governance/runtime evidence, obtain an independent supervisor verdict, and stop at C16.
- Phase Boundary:
  - In scope: plan/evidence/benchmark/actual-status refresh, coder report, notes log, governance lock/drift/doctor/security checks, supervisor review.
  - Out of scope: optional hardening, C17, promotion, release publication, or new research.
  - Dependencies: P1/P2 slices complete or explicitly blocked.
- Phase Implementation Rule: complete `P3-A`, then supervisor `P3-B`; do not continue after PASS.
- Ordered Slice List:
  - P3-A: Run closure checks and write evidence.
  - P3-B: Supervisor acceptance and terminal stop.

- [x] P3-A: Run closure checks and write evidence.
  - Goal: prove the full C16 claim with current source, tests, governance, and protected-hash evidence.
  - Scope Boundary:
    - Editable: plan companion files, coder report, notes log, generated runtime lock if affected.
    - Inspect-only: implementation source and official artifacts after tests.
    - Preserve-only: official `.19`, prior candidates, source baseline, user projects.
    - Out of scope: any additional implementation after acceptance criteria pass.
  - Non-Goals: no release gate finalization and no user approval request for promotion.
  - Pre-flight Questions:
    - Data source: fresh commands and current files.
    - Display permission: local reports only.
    - DB read flow: N/A.
    - DB write flow: evidence/report files only.
    - Render location: `docs/plans`, `reports/coder`, `reports/supervisor`, notes log.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: all required commands and named R tests.
    - Cleanup/quarantine: retain only required evidence; no material deletion.
    - External side effects: none.
    - N/A notes: Git detect-changes limitation is recorded.
  - Work Steps:
    1. Run focused/full checks, doctor, security scan, governance drift, and official/candidate hash checks; write evidence and benchmark rows.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: reports link to exact output.
       - Mini QA for each completed implementation slice (MUST): inspect report/source alignment.
       - Evidence target: `E3-P3A-REG1..E3-P3A-PROTECT1`.
  - Implementation Gate:
    - All mandatory implementation acceptance items are either PASS or have one explicit blocker.
  - Acceptance:
    - Source: reports match current diff and invariant family map.
    - Runtime/UI: affected commands are fresh and reproducible.
    - DB/data: no protected artifact changes.
    - Behavior test: closure evidence identifies all R1-R18 results.
    - Cleanup/quarantine: no dead plan-created helper/report remains.
    - Evidence IDs: `E3-P3A-REG1..E3-P3A-PROTECT1`.
    - Actual-status rows refreshed: final status and stop rule.
  - Evidence Targets: coder report, notes log, plan ledgers, runtime/drift/doctor outputs.
  - Actual-status Update: current C16 status becomes `PASS` after final supervisor acceptance; see `E3-P3B-SUP1`.
  - Commit Boundary: final checkpoint if Git is available; otherwise report no commit.

- [x] P3-B: Call supervisor for the implemented-plan acceptance loop.
  - Goal: independently verify official baseline authority, drift root cause, lineage guard, roadmap durability, provenance, preserved roadmap/invariants, no promotion/C17 creep, canonical 8, and artifact immutability.
  - Work Steps:
    1. Call the supervisor skill to review the completed plan work and current worktree/source.
    2. If rejected, return only the failed scope to coder, re-verify, and resubmit.
    3. If passed, mark the plan terminal and stop without starting C17.
  - Implementation Gate: P1/P2/P3-A are complete or explicitly blocked with evidence.
  - Acceptance: supervisor report is `PASS`, residual same-invariant unverified surfaces are none, and final status is `DURABLE_DEVELOPMENT_ROADMAP_AND_LINEAGE_READY`.

- [x] P3-C: Close the plan.
  - Goal: finish evidence, benchmark, detect-changes, and final status without release promotion.
  - Work Steps:
    1. Refresh all companion files and record final validation.
    2. Run Anvien detect-changes; if Git exit 129 persists, record the limitation and do not initialize Git.
    3. Verify worktree/filesystem state and stop.
  - Implementation Gate: P3-B passes or a real blocker is recorded.
  - Acceptance: plan is terminal, required reports exist, official `.19` is unchanged, and no C17 work begins. Final result: `DURABLE_DEVELOPMENT_ROADMAP_AND_LINEAGE_READY — YES`.

## Risk Notes

- The current development checkout is `.15`; the intended outcome is a truthful packaging block until an explicitly lineage-bound future candidate is prepared. This is not a reason to rewrite C15 or to promote `.19` again.
- The new governance record must remain a compact reference projection; it must not copy full Goal/status/ledger/FACT content or become a second authority.
- Existing historical artifacts predate the control record. Compatibility validation must be optional for old archives while new packages with the record are strict.
- Anvien reports HIGH file risk and the workspace has no Git; these are scope/evidence constraints, not reasons to broaden or simulate work.
- The final result is `PASS` only for roadmap/lineage readiness; it does not certify live delegation, parallelism, remote control, or release readiness.
