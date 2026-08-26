# P2P-GOVREC01 Current Governance Authority Reconciliation Plan

## Metadata

- Date: `2026-08-26`
- Status: `P0 Complete; implementation in progress`
- Plan: `docs/plans/2026-08-26-p2p-govrec01-current-governance-authority/2026-08-26-p2p-govrec01-current-governance-authority-plan.md`
- Evidence: `docs/plans/2026-08-26-p2p-govrec01-current-governance-authority/2026-08-26-p2p-govrec01-current-governance-authority-evidence.md`
- Benchmark: `docs/plans/2026-08-26-p2p-govrec01-current-governance-authority/2026-08-26-p2p-govrec01-current-governance-authority-benchmark.md`
- Actual status: `docs/plans/2026-08-26-p2p-govrec01-current-governance-authority/2026-08-26-p2p-govrec01-current-governance-authority-actual-status.md`

## Goal

Reconcile the current governance authority of the promoted `origin/main` source with the historical `.19` artifact authority and the unpromoted `.74` development successor, then close the smallest existing drift, Council-wording, edge-case-index, and cross-platform doctor defects without promoting, releasing, deploying, invoking providers, or invoking a Council.

## Rules

- Complete P0 actual status before implementation work.
- Preserve the historical `.19` artifact and all historical C36 evidence unchanged.
- Treat `origin/main=2a71410afd1b29651016ef57a5d2da38938c3f68`, tree `3e6ab12ff78a72c4a3ea2a418e11167a8649aaad`, and baseline ancestor `af02170ac7ba180900ca78beb26a2972d80c73b6` as the current supplied source authority.
- Keep `.74` as an unpromoted development successor; do not turn it into current or official release authority.
- Classify every runtime-lock finding before changing the existing lock. No wildcard, mass whitelist, suppression, gate weakening, stale-identity substitution, or parallel governance system is allowed.
- Historical single-host Council evidence remains historical. Current-lineage full Council remains `FALSE` / `NOT_PROVEN` until fresh exact current-head evidence exists.
- Do not run Manus, external providers, Council roles, remote writes, promotion, release, deployment, or production mutation.
- Update each checklist item immediately when it is completed.
- Record evidence as work completes and run Anvien change detection before implementation commits.
- This is a governance/CLI/documentation scope: UI, database, Docker, and browser validation are `N/A` with explicit reasons.
- Run a full Python/build-equivalent validation before final acceptance: `compileall`, required focused suites, specified regression gates, governance drift, and development doctor.

## Problem

The promoted current source has moved past the `.74` runtime-manifest lock, while `development-control.json` still presents `.19` as the only authority and `.74` as the active successor. The current source therefore has an authority representation gap, not evidence that the source is defective. The same snapshot contains historical `LIVE_COUNCIL_8_OF_8` wording beside current `NOT_PROVEN` wording, no dedicated canonical edge-case index, a stale drift test expectation, and a Windows subprocess decoder failure that obscures the real drift verdict.

## Scope

- Record current promoted source authority separately from the historical `.19` official artifact baseline.
- Recompute and classify the exact runtime lock delta against current promoted `origin/main`.
- Regenerate only the existing `governance/runtime-manifest.lock.json` through `scripts/p2p_governance.py lock-runtime` after classification.
- Make canonical/projection Council language distinguish `HISTORICAL_SINGLE_HOST_LIVE_COUNCIL_8_OF_8=TRUE` from `CURRENT_LINEAGE_FULL_COUNCIL_LIVE_PROVEN=FALSE`.
- Add `reports/Edge-Case/QA+EDGE_CASE_TEST_PLAN.md` at the closest native reports location, mapping required edge-case families and live-evidence slots.
- Repair the existing `scripts/doctor.py` governance-helper subprocess boundary with explicit UTF-8 child output and strict fail-closed decoding.
- Add/adjust tests for authority separation, lock identity and additions, Council historical/current separation, and malformed helper output.
- Produce fresh reports, final exact-head identity, and a separate fresh Supervisor review of the final candidate.

## Non-Goals

- No change to the `.19` artifact, its SHA-256, its promotion report, or its approval record.
- No promotion of `.74` or this branch; no release ZIP, tag, merge, push, deploy, or host ACL mutation.
- No Council/provider/Manus execution and no fabricated live evidence.
- No new router, test framework, database, browser harness, Docker image, or parallel governance ledger.
- No cleanup of unrelated dirty worktrees or repair of the broken root `.git` container.
- No changes to SFI01, vendor skill package, Manus R2, or unrelated project repositories.

## Requirements

### Invariant family map

| Family | Invariant | Proof boundary |
|---|---|---|
| A1 Authority/lineage | `.19` historical artifact remains immutable; current promoted main is represented separately; `.74` remains unpromoted | `development-control.json`, exact Git identity, unchanged historical refs |
| A2 Drift/generation | Every added/changed protected path is explained by current promoted source truth; lock is regenerated by the existing deterministic command | drift report, path classification matrix, lock identity test |
| A3 Council epistemics | Historical C36 fact is preserved; current-lineage full Council is not upgraded from historical or C43 smoke evidence | roadmap, research ledger, capability ledger, negative tests |
| A4 Edge cases | retry, duplicate, stale, partial, quorum, host failure, resume/recovery, and process interruption each have an owner/evidence slot | canonical edge-case index |
| A5 Decoder safety | Child helper output is explicitly UTF-8 and malformed bytes fail closed without reader-thread exceptions or swallowed failures | doctor tests and development doctor |
| A6 Boundary/regression | No provider/Council/remote mutation; specified gates stay green or their inherited blockers are reported honestly | command receipts, diff, Supervisor exact-head review |

## Acceptance Criteria

- Terminal status is `P2P_GOVREC01_CURRENT_GOVERNANCE_AUTHORITY_RECONCILED_READY_FOR_OWNER_GATE` only if drift, development doctor, focused tests, required regression gates, compileall, and fresh exact-head Supervisor review all pass.
- `.19` remains `PROMOTED_VERIFIED` historical official artifact authority with the original SHA-256 and approval reference unchanged.
- Current promoted `origin/main` exact commit/tree/base is represented as a separate source-authority projection and explicitly does not grant release/promotion authority.
- `.74` remains `ACTIVE_UNPROMOTED` / `SEALED_UNPROMOTED` and is not relabeled as official or current Council proof.
- Runtime lock contains the current promoted protected path set and no new wildcard/suppression rule; all 6 additions and 11 changed files have a recorded classification.
- Canonical Council records state historical single-host evidence separately from current-lineage full Council, with current status false/not proven.
- The edge-case index exists at `reports/Edge-Case/QA+EDGE_CASE_TEST_PLAN.md` and contains all required families plus live evidence slots.
- The doctor decoder fix is strict and deterministic: valid UTF-8 helper output passes/fails from helper status; malformed stdout/stderr fails closed.
- No protected historical artifact, provider, Council, root Git admin, or unrelated owner worktree is changed.

## Checklist

- [x] P0-A: Complete actual status before implementation work.
  - Goal: establish the real current state.
  - Work Steps: inspect source-of-truth files, classify each surface, record blocked or missing pieces, and update later phase status assumptions, next actions, and work steps from evidence.
  - Implementation Gate: no implementation or editing starts until `2026-08-26-p2p-govrec01-current-governance-authority-actual-status.md` has a final P0 decision.
  - Acceptance: actual status identifies correct, partial, missing/unbound, fake-or-stub, and blocked surfaces for this scope.

### P1: Authority and protected-runtime drift reconciliation

- Phase Goal: express current promoted main authority using the existing governance projection and make the existing runtime lock match the exact current promoted source after path-by-path classification.
- Phase Boundary:
  - In scope: `governance/development-control.json`, `governance/runtime-manifest.lock.json`, drift reports/tests, exact Git identity.
  - Out of scope: `.19` artifact mutation, `.74` promotion, release lifecycle, remote authority writes, and drift-policy wildcard changes.
  - Dependencies: P0 exact authority and baseline drift reproduction.
- Phase Implementation Rule: do not implement `P1` directly. Implement `P1-A`, verify it, record evidence, refresh actual-status, commit when required, then continue to `P1-B`.
- Ordered Slice List:
  - P1-A: Bind current promoted source authority without replacing `.19` or `.74` records.
  - P1-B: Reconcile the deterministic runtime lock and exact path classification.

- [ ] P1-A: Bind current promoted source authority without replacing historical or unpromoted records
  - Goal: add the smallest field under the existing `authority` projection for current promoted `origin/main` source truth.
  - Scope Boundary:
    - Editable: `governance/development-control.json` and its direct governance tests if required.
    - Inspect-only: `.19` reports/artifact, current `.74` candidate record, canonical checkout refs, PREPILOT receipts.
    - Preserve-only: `official_baseline`, `candidate_identity_binding`, historical reports, and owner worktrees.
    - Out of scope: replacing official baseline, changing VERSION, minting/releasing `.74`, or claiming current Council proof.
  - Non-Goals: no new authority file or parallel source of truth.
  - Pre-flight Questions:
    - Data source: exact local promoted `origin/main` commit/tree/parent supplied and verified in canonical checkout.
    - Display permission: governance/read-only metadata only; it cannot grant release or promotion permission.
    - DB read flow: N/A; no database.
    - DB write flow: N/A; no database.
    - Render location: JSON authority projection and downstream reports.
    - UI behavior flow: N/A; no UI surface.
    - Docker runtime: N/A; no app/container runtime.
    - Playwright target: N/A; no browser-facing change.
    - Behavior test: exact commit/tree/base and `.19`/`.74` separation tests.
    - Cleanup/quarantine: isolated candidate worktree only; no owner worktree cleanup.
    - External side effects: none; no remote or provider call.
    - N/A notes: this is a local governance projection change.
  - Work Steps:
    1. Compare exact Git identity and existing authority records; insert only the current promoted source projection.
       - UI flow check: N/A; inspect JSON consumer flow instead.
       - DB/data flow check: verify JSON parse and existing validator consumers.
       - Render location check: verify `development-control.json` is the existing canonical source named by current-roadmap projections.
       - Mini QA: run JSON parse, `p2p_development_control.py status`, and focused authority tests.
       - Evidence target: `E1-P1A-AUTH1..E1-P1A-AUTH4`.
    2. Confirm the historical `.19` and unpromoted `.74` rows remain byte/semantic-equivalent except for the new separate projection.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: verify no derived document silently becomes source authority.
       - Mini QA: run diff inspection and exact-field assertions.
       - Evidence target: `E1-P1A-AUTH5..E1-P1A-AUTH7`.
  - Implementation Gate:
    - Before editing, Anvien file-detail and impact evidence for `governance/development-control.json` is recorded (`E0-P0A-GRAPH1`, `E0-P0A-IMPACT1`).
    - No current promoted source is represented by filename, stale `.74` artifact, or historical report alone.
  - Acceptance:
    - Source: current commit/tree/parent and scope are explicit; `.19` and `.74` statuses are unchanged.
    - Runtime/UI: N/A.
    - DB/data: JSON validates and existing development-control validator passes.
    - Behavior test: authority separation and stale-authority negative cases pass.
    - Cleanup/quarantine: only candidate worktree changed.
    - Evidence IDs: `E1-P1A-AUTH1..E1-P1A-AUTH7`.
    - Actual-status rows refreshed: authority rows and next P1-B lock assumptions.
  - Evidence Targets: exact Git identity, JSON diff, validator/test output.
  - Actual-status Update: `partial -> correct` for authority representation; retain `.74` as unpromoted and `.19` as historical official.
  - Commit Boundary: commit after slice acceptance.

- [ ] P1-B: Reconcile the deterministic runtime lock and exact path classification
  - Goal: close only authorized promoted evolution and generated lock state.
  - Scope Boundary:
    - Editable: `governance/runtime-manifest.lock.json`, drift classification tests/evidence.
    - Inspect-only: commit history for every added/changed path and drift policy.
    - Preserve-only: wildcard/exclusion policy and historical evidence.
    - Out of scope: adding broad policy exceptions or deleting files to make drift pass.
  - Non-Goals: no runtime feature work.
  - Pre-flight Questions:
    - Data source: current promoted tree and deterministic `runtime_manifest()` output.
    - Display permission: lock is an integrity gate, not an approval record.
    - DB read flow: N/A.
    - DB write flow: N/A.
    - Render location: runtime lock and drift report.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: added/changed path rejection and lock identity tests.
    - Cleanup/quarantine: no extra generated files outside the candidate worktree.
    - External side effects: none.
    - N/A notes: lock regeneration is the existing supported command.
  - Work Steps:
    1. Record all 6 added and 11 changed files as `AUTHORIZED_PROMOTED_EVOLUTION` or another evidence-backed class; record expected generated state separately.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: report/table only.
       - Mini QA: inspect each path's introduction/last-change commit and compare current tree.
       - Evidence target: `E1-P1B-DRIFT1..E1-P1B-DRIFT17`.
    2. Run `scripts/p2p_governance.py lock-runtime` with a GOVREC01 reason, then run direct drift and assert no path policy was broadened.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: `runtime-manifest.lock.json` only.
       - Mini QA: direct drift, lock identity negative test, `git diff --check`.
       - Evidence target: `E1-P1B-LOCK1..E1-P1B-LOCK4`.
  - Implementation Gate:
    - Anvien impact is not required for JSON-only lock regeneration; the existing deterministic generator must be used.
    - Fail closed if any path remains `UNEXPLAINED_DRIFT` or if a policy wildcard/suppression changes.
  - Acceptance:
    - Source: lock protected-file set equals current runtime manifest exactly.
    - Runtime/UI: direct governance drift PASS; UI N/A.
    - DB/data: N/A.
    - Behavior test: unauthorized file/change and changed-lock-identity cases reject.
    - Cleanup/quarantine: no stale generated lock copies.
    - Evidence IDs: `E1-P1B-DRIFT1..E1-P1B-LOCK4`.
    - Actual-status rows refreshed: drift goes to `correct` only after direct PASS.
  - Evidence Targets: path matrix, lock hash/count, direct drift JSON, negative tests.
  - Actual-status Update: `wrong/partial -> correct` only for explained protected drift; preserve fail-closed behavior.
  - Commit Boundary: commit after slice acceptance.

### P2: Council semantics and edge-case index

- Phase Goal: remove ambiguity between historical live Council evidence and current-lineage proof, and add the missing canonical edge-case index.
- Phase Boundary:
  - In scope: canonical governance/ledger/projection wording and `reports/Edge-Case/QA+EDGE_CASE_TEST_PLAN.md`.
  - Out of scope: historical report rewrites, live Council execution, provider calls, and new test frameworks.
  - Dependencies: P1 authority and drift lock are reconciled.
- Phase Implementation Rule: implement `P2-A` then `P2-B`; preserve all historical evidence.
- Ordered Slice List:
  - P2-A: Reconcile historical/current Council wording across canonical projections.
  - P2-B: Add the canonical edge-case test-plan/index with live evidence slots.

- [ ] P2-A: Reconcile historical/current Council wording across canonical projections
  - Goal: preserve C36 historical fact while making current lineage status explicitly false/not proven.
  - Scope Boundary:
    - Editable: `governance/p2p-development-roadmap.json`, `governance/research-adoption-ledger.json`, capability-ledger canonical record, and active human-readable projections that currently blur status.
    - Inspect-only: C36 receipts/reports and C43 smoke receipts.
    - Preserve-only: historical source evidence and exact C36 fact.
    - Out of scope: any live run or upgrade of C36/C43.
  - Non-Goals: no deletion of `LIVE_COUNCIL_8_OF_8` historical vocabulary.
  - Pre-flight Questions:
    - Data source: C36 historical exact receipts plus current-head capability/role state.
    - Display permission: projections may display status but cannot promote evidence.
    - DB read flow: N/A.
    - DB write flow: N/A.
    - Render location: governance JSON, roadmap, capability ledger, framework projections.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: historical/current negative assertions.
    - Cleanup/quarantine: retain historical report paths unchanged.
    - External side effects: none.
    - N/A notes: document-only governance semantics.
  - Work Steps:
    1. Add explicit historical/current fields or wording at each canonical surface without changing C36 facts.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: confirm each projection names its source and status.
       - Mini QA: JSON parse, targeted `rg`, semantic negative tests.
       - Evidence target: `E2-P2A-COUNCIL1..E2-P2A-COUNCIL5`.
    2. Verify C43 current smoke remains a bounded one-role/not-quorum result and cannot be used to derive full Council proof.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: C43 record and active projection.
       - Mini QA: exact negative tests and historical receipt hash checks.
       - Evidence target: `E2-P2A-COUNCIL6..E2-P2A-COUNCIL8`.
  - Implementation Gate:
    - Anvien file-detail/impact for any edited code contract is recorded; JSON/docs remain projection edits.
    - No historical evidence file is rewritten.
  - Acceptance:
    - Source: historical true and current false/not-proven are separate and machine-checkable.
    - Runtime/UI: N/A.
    - DB/data: N/A.
    - Behavior test: C36-to-current upgrade is rejected.
    - Cleanup/quarantine: historical receipts unchanged.
    - Evidence IDs: `E2-P2A-COUNCIL1..E2-P2A-COUNCIL8`.
    - Actual-status rows refreshed: Council semantics `partial -> correct`.
  - Evidence Targets: changed-path diff, exact historical field, current negative test.
  - Actual-status Update: preserve historical fact; current status remains `NOT_PROVEN`.
  - Commit Boundary: commit after slice acceptance.

- [ ] P2-B: Add canonical edge-case index with live evidence slots
  - Goal: provide one native, auditable index for edge-case coverage and future independent evidence.
  - Scope Boundary:
    - Editable: `reports/Edge-Case/QA+EDGE_CASE_TEST_PLAN.md`.
    - Inspect-only: existing edge-case skills/tests/reports.
    - Preserve-only: existing framework and tests.
    - Out of scope: implementing a new test runner or claiming live proof.
  - Non-Goals: no fabricated receipt or PASS state.
  - Pre-flight Questions:
    - Data source: existing engine/governance edge-case contracts and reports.
    - Display permission: report/index only; `UNKNOWN` and `NOT_PROVEN` remain valid.
    - DB read flow: N/A.
    - DB write flow: N/A.
    - Render location: reports/Edge-Case.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: document completeness/slot inventory.
    - Cleanup/quarantine: no generated test artifacts.
    - External side effects: none.
    - N/A notes: index-only slice.
  - Work Steps:
    1. Map retry, duplicate, stale, partial, quorum, host failure, resume/recovery, and process interruption to current contract/test/evidence locations.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: report tables and evidence-slot identifiers.
       - Mini QA: required-family checker and `git diff --check`.
       - Evidence target: `E2-P2B-EDGE1..E2-P2B-EDGE3`.
    2. Mark every live/independent evidence slot `UNKNOWN` until a fresh receipt exists.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: slot status and owner/action columns.
       - Mini QA: no slot is silently marked PASS.
       - Evidence target: `E2-P2B-EDGE4..E2-P2B-EDGE5`.
  - Implementation Gate: use the closest native report location; no new framework.
  - Acceptance:
    - Source: all required families and live slots are present.
    - Runtime/UI: N/A.
    - DB/data: N/A.
    - Behavior test: completeness checker passes and no live proof is fabricated.
    - Cleanup/quarantine: only the intended report is added.
    - Evidence IDs: `E2-P2B-EDGE1..E2-P2B-EDGE5`.
    - Actual-status rows refreshed: missing index -> correct.
  - Evidence Targets: report path/hash and completeness output.
  - Actual-status Update: edge index `missing -> correct`; evidence slots remain `UNKNOWN`.
  - Commit Boundary: commit after slice acceptance.

### P3: Deterministic doctor decoder and fail-closed tests

- Phase Goal: make the existing governance-helper subprocess boundary cross-platform and fail closed for malformed output.
- Phase Boundary:
  - In scope: `scripts/doctor.py`, focused doctor/drift tests, and no unrelated subprocess paths.
  - Out of scope: changing governance verdicts, swallowing errors, or weakening drift.
  - Dependencies: P1 direct drift is understood; P2 terminology does not alter runtime behavior.
- Phase Implementation Rule: implement `P3-A`, verify, commit, then `P3-B` if test-only hardening is still needed.
- Ordered Slice List:
  - P3-A: Explicit UTF-8 child environment and strict byte decoding.
  - P3-B: Malformed-output and valid-output regression coverage.

- [ ] P3-A: Explicit UTF-8 child environment and strict byte decoding
  - Goal: remove Windows reader-thread decode noise while preserving fail-closed behavior.
  - Scope Boundary:
    - Editable: `scripts/doctor.py` governance-helper call only.
    - Inspect-only: other subprocess calls.
    - Preserve-only: nonzero helper status and report failure semantics.
    - Out of scope: changing `p2p_governance.py` drift logic.
  - Non-Goals: no `errors='replace'`, no default-text encoding, no silent success.
  - Pre-flight Questions:
    - Data source: helper stdout/stderr bytes.
    - Display permission: diagnostic text only.
    - DB read flow: N/A.
    - DB write flow: N/A.
    - Render location: doctor JSON report.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: valid UTF-8 and malformed bytes.
    - Cleanup/quarantine: temporary test roots only.
    - External side effects: none.
    - N/A notes: CLI-only change.
  - Work Steps:
    1. Change only `check_governance` helper capture to bytes, pass explicit UTF-8 child environment, and decode strictly with a diagnostic failure path.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: `governance-drift` report row.
       - Mini QA: focused unit tests plus direct doctor reproduction.
       - Evidence target: `E3-P3A-DECODER1..E3-P3A-DECODER4`.
    2. Confirm helper nonzero still reports real drift details and malformed output cannot pass.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: fail row retains decoder/helper detail.
       - Mini QA: test malformed stdout, malformed stderr, and nonzero valid UTF-8.
       - Evidence target: `E3-P3A-DECODER5..E3-P3A-DECODER7`.
  - Implementation Gate:
    - `anvien file-detail scripts/doctor.py` and `anvien impact symbol check_governance` are recorded before editing (`E0-P0A-GRAPH2`, `E0-P0A-IMPACT2`).
    - High blast-radius warning is acknowledged; edit remains one helper boundary.
  - Acceptance:
    - Source: no implicit text decoder remains on this helper path.
    - Runtime/UI: development doctor returns JSON without reader-thread traceback.
    - DB/data: N/A.
    - Behavior test: malformed output fails closed; valid output honors return code.
    - Cleanup/quarantine: temporary fixtures cleaned by tests.
    - Evidence IDs: `E3-P3A-DECODER1..E3-P3A-DECODER7`.
    - Actual-status rows refreshed: decoder `wrong -> correct`.
  - Evidence Targets: diff, focused test results, doctor output.
  - Actual-status Update: update P4 assumptions from actual doctor result.
  - Commit Boundary: commit after slice acceptance.

- [ ] P3-B: Malformed-output and valid-output regression coverage
  - Goal: lock the decoder safety contract in existing unittest style.
  - Scope Boundary:
    - Editable: focused test module and stale drift-test expectations only where current policy evidence proves them stale.
    - Inspect-only: product runtime.
    - Preserve-only: all existing gate assertions and historical failure classifications.
    - Out of scope: lowering thresholds or deleting failing cases.
  - Non-Goals: no synthetic Council/provider evidence.
  - Pre-flight Questions:
    - Data source: mocked subprocess bytes at the doctor boundary plus current policy fixture.
    - Display permission: test-only.
    - DB read flow: N/A.
    - DB write flow: N/A.
    - Render location: unittest output.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: exact rejection assertions.
    - Cleanup/quarantine: `TemporaryDirectory`/mock cleanup.
    - External side effects: none.
    - N/A notes: test-only.
  - Work Steps:
    1. Update the stale drift fixture counts only to the currently measured policy/reference counts and add negative tests for unauthorized additions, lock identity, stale authority, and Council upgrade.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: test assertions.
       - Mini QA: focused unittest modules.
       - Evidence target: `E3-P3B-TEST1..E3-P3B-TEST5`.
    2. Run all focused gates and compare failures against the frozen prepilot baseline; do not mask inherited failures.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: reports only.
       - Mini QA: pytest/unittest commands and compileall.
       - Evidence target: `E3-P3B-TEST6..E3-P3B-TEST8`.
  - Implementation Gate: test edits must assert behavior/contract, not static text only.
  - Acceptance:
    - Source: tests reject each prohibited governance shortcut.
    - Runtime/UI: N/A.
    - DB/data: N/A.
    - Behavior test: focused suite passes.
    - Cleanup/quarantine: no persistent fixture mutation.
    - Evidence IDs: `E3-P3B-TEST1..E3-P3B-TEST8`.
    - Actual-status rows refreshed: test coverage `partial -> correct`.
  - Evidence Targets: focused test receipt and regression comparison.
  - Actual-status Update: refresh final validation matrix.
  - Commit Boundary: commit after slice acceptance.

### P4: Validation, fresh exact-head Supervisor review, and handoff

- Phase Goal: prove the final local candidate exactly, report residual limits honestly, and stop at Owner Gate.
- Phase Boundary:
  - In scope: full specified validations, reports, change detection, local commits, exact-head Supervisor review.
  - Out of scope: user approval execution, promotion, release, deployment, remote writes, and provider/Council calls.
  - Dependencies: all prior slices pass.
- Ordered Slice List:
  - P4-A: Full validation and evidence closure.
  - P4-B: Fresh exact-head Supervisor review and final local handoff.

- [ ] P4-A: Full validation and evidence closure
  - Goal: run every required gate and record exact counts/statuses.
  - Scope Boundary:
    - Editable: evidence/report/plan status files only.
    - Inspect-only: final source and generated lock after validation.
    - Preserve-only: all implementation commits and historical reports.
    - Out of scope: optional hardening after PASS.
  - Non-Goals: no release artifact.
  - Pre-flight Questions:
    - Data source: candidate worktree and existing test/gate commands.
    - Display permission: local evidence only.
    - DB read flow: N/A.
    - DB write flow: N/A.
    - Render location: reports/coder and reports/reconciliation.
    - UI behavior flow: N/A.
    - Docker runtime: N/A, no app/runtime scope.
    - Playwright target: N/A.
    - Behavior test: all specified suites and negative checks.
    - Cleanup/quarantine: retain only plan/evidence/report artifacts; no unrelated cleanup.
    - External side effects: none.
    - N/A notes: local-only validation.
  - Work Steps:
    1. Run compileall, drift, doctor, Vendor 22/22, Host Projection 30/30, Manus package 8/8, Foundation 28/28, C35 57/57, C43 9/9, and relevant regressions.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: command receipts in evidence.
       - Mini QA: inspect exit codes and counts, not logs alone.
       - Evidence target: `E4-P4A-GATE1..E4-P4A-GATE12`.
    2. Run Anvien detect-changes, diff check, status, exact identity, and report residual remote-authority limitations.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: coder report and actual-status closure.
       - Mini QA: exact tree/hash/parent/base and no provider/Council process evidence.
       - Evidence target: `E4-P4A-CLOSE1..E4-P4A-CLOSE5`.
  - Implementation Gate: no final closure until all mandatory gates are known.
  - Acceptance:
    - Source: final candidate is clean and hashes are recorded.
    - Runtime/UI: required CLI gates pass; no UI claim.
    - DB/data: N/A.
    - Behavior test: full specified suite/regressions are green or an explicit terminal block is recorded.
    - Cleanup/quarantine: no dead plan-created artifact.
    - Evidence IDs: `E4-P4A-GATE1..E4-P4A-CLOSE5`.
    - Actual-status rows refreshed: final matrix.
  - Evidence Targets: all command receipts, final hashes, change detection.
  - Actual-status Update: closure readiness or exact blocker.
  - Commit Boundary: commit evidence/status only when necessary; no source changes after final validation without rerun.

- [ ] P4-B: Fresh exact-head Supervisor review and final local handoff
  - Goal: obtain one fresh independent-style review of the exact final candidate head.
  - Scope Boundary:
    - Editable: Supervisor report only during review; no repair in review phase.
    - Inspect-only: exact final tree, parent, baseline, path diff, reports, tests, lock, authority fields.
    - Preserve-only: all previous review reports and historical C36/.19 evidence.
    - Out of scope: promotion/release/approval execution.
  - Non-Goals: no claim that PREPILOT `03a9e4` was reviewed; that object is not available in this authority checkout.
  - Pre-flight Questions:
    - Data source: exact final candidate commit/tree and fresh validation receipts.
    - Display permission: review verdict only.
    - DB read flow: N/A.
    - DB write flow: N/A.
    - Render location: `reports/supervisor/`.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: Supervisor rechecks source before tests.
    - Cleanup/quarantine: no review-time repair.
    - External side effects: none.
    - N/A notes: exact-head review is local and read-only.
  - Work Steps:
    1. Review source truth, diff, gates, invariant families, and residual scope at the exact final head.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: Supervisor report.
       - Mini QA: one verdict only, PASS or REJECT.
       - Evidence target: `E4-P4B-SUP1..E4-P4B-SUP6`.
  - Implementation Gate: if the exact head changes, the review is invalidated and must rerun.
  - Acceptance:
    - Source: report names exact reviewed commit/tree/parent/base and path diff.
    - Runtime/UI: no unsupported UI claim.
    - DB/data: N/A.
    - Behavior test: Supervisor PASS required for READY terminal status.
    - Cleanup/quarantine: review report is the only review artifact.
    - Evidence IDs: `E4-P4B-SUP1..E4-P4B-SUP6`.
    - Actual-status rows refreshed: final review state.
  - Evidence Targets: fresh Supervisor report and final handoff.
  - Actual-status Update: `PASS` -> Owner Gate; `REJECT` -> exact repair slice only.
  - Commit Boundary: final local commit before review; no commit during review.

- [ ] Pn-A: Call supervisor for the implemented-plan acceptance loop.
  - Goal: verify the completed plan work against the accepted plan, actual-status decisions, evidence, benchmark, changed files, generated output, and validation results before closure.
  - Work Steps:
    1. Run the fresh exact-head Supervisor review described in P4-B.
    2. If it rejects, return only to the responsible implementation slice and rerun affected gates.
  - Implementation Gate: all planned implementation phases are completed or explicitly blocked.
  - Acceptance: Supervisor PASS, or a precise blocker with no false closure.
- [ ] Pn-B: Remove dead work created during this plan.
  - Goal: ensure the final diff contains only accepted plan artifacts.
  - Work Steps: inspect diff/status, remove only plan-created dead artifacts, rerun diff check, and record preserved owner data.
  - Implementation Gate: no unrelated cleanup.
  - Acceptance: no stale placeholder or dead generated artifact remains.
- [ ] Pn-C: Close the plan.
  - Goal: finish validation, evidence, benchmark, detect-changes, commit, and final status.
  - Work Steps: run final validation, record exact identity, record Supervisor report, commit locally, and stop at Owner Gate.
  - Implementation Gate: Pn-A and Pn-B pass or record blockers.
  - Acceptance: terminal status is one of the user-specified GOVREC01 outcomes.

## Risk Notes

- The root snapshot has an invalid `.git` admin container; do not repair it or infer authority from it.
- The direct remote is private/credential-limited; local exact `origin/main` evidence is usable for this candidate, but remote ACL/promotion authority remains unproven.
- The candidate worktree starts clean but the shared repository contains dirty owner worktrees; every non-target worktree is preserve-only.
- Anvien reports `scripts/doctor.py` as high blast-radius with 3 inbound files, 78 local relationships, 14 linked flows, and unresolved analyzer references; the decoder edit must remain one bounded helper boundary.
- A green structural/configured quorum (`8/8`) is not live Council proof. Current full Council remains `FALSE` / `NOT_PROVEN`.
- If any protected path cannot be justified as current promoted evolution or expected generated state, stop with `P2P_GOVREC01_BLOCKED_UNEXPLAINED_PROTECTED_DRIFT`.
