# P2P-PB01 Current Canonical Reconciliation and Installed Contract Fix Plan

## Metadata

- Date: `2026-08-29`
- Status: `P2 Complete; P3-A in progress`
- Plan: `docs/plans/2026-08-29-p2p-pb01-current-reconciled-installed-contract/2026-08-29-p2p-pb01-current-reconciled-installed-contract-plan.md`
- Evidence: `docs/plans/2026-08-29-p2p-pb01-current-reconciled-installed-contract/2026-08-29-p2p-pb01-current-reconciled-installed-contract-evidence.md`
- Benchmark: `docs/plans/2026-08-29-p2p-pb01-current-reconciled-installed-contract/2026-08-29-p2p-pb01-current-reconciled-installed-contract-benchmark.md`
- Actual status: `docs/plans/2026-08-29-p2p-pb01-current-reconciled-installed-contract/2026-08-29-p2p-pb01-current-reconciled-installed-contract-actual-status.md`

## Goal

Create one isolated PB01 candidate from the current official `main`, retain all
current 02A history, carry only the reviewed PB01 implementation delta, and
close the installed-runtime launcher requirement without promotion.

## Rules

- Current official `main` and its tree are the authority for this candidate.
- The old PB01 subject is source/evidence only; it is not promotable.
- Preserve current-main behavior first and never drop or revert 02A paths.
- Keep one existing workflow/router/truth store and existing BG01/EFF01 gates.
- Do not promote, release, deploy, live-activate, or mutate production.
- Do not run broad regression, full repository tests, Anvien, graph/impact, or
  benchmark regeneration; the current user explicitly set that verification
  ceiling.
- Use only the smallest installed contract and focused-test changes required.

## Problem

The old PB01 candidate descends from `9f5b91c9...`, while current official
`main` is `6cc7555246905fce7b2fec1d4e48f5e46bfaf57e` and contains 02A history.
The path comparison is disjoint, so there is no semantic overlap to resolve.
Supervisor also found that `INSTALLED_REQUIRED_FILES` does not require the
installed `scripts/p2p_bootstrap.py` launcher.

## Scope

- Fresh official-main candidate creation under repo-local `.tmp`.
- Controlled carry-forward of `scripts/p2p_bootstrap.py`, its installer/package
  inclusion, and its focused tests.
- Minimal installed-runtime required-file contract correction.
- Focused positive and negative installed-runtime regression proof.
- One independent Supervisor review; candidate remains unpromoted.

## Non-Goals

- No 02A edits, vendor changes, provider/model work, router/workflow redesign,
  release, deployment, remote write, or live runtime action.
- No broad test or graph investigation.

## Requirements

- The new candidate must descend from current official `main`.
- Existing PB01 beginner, discovery, idempotency, path, conflict, BG01, Task,
  ledger, Control Tower, and safety behavior must remain unchanged.
- An installed runtime missing `scripts/p2p_bootstrap.py` must fail closed;
  one containing it must remain valid.
- Current 02A capability/provenance/vendor/test/report paths must remain present.

## Acceptance Criteria

- Fresh candidate base SHA/tree exactly match the freshly verified official main.
- Old PB01/current-main path intersection is recorded as empty.
- Focused PB01 tests and the two installed-launcher cases pass.
- Package/install selection and installed required-file validation agree.
- No duplicate control plane or safety-gate change is introduced.
- One independent Supervisor returns `PASS`; no promotion occurs.

## Checklist

- [x] P0-A: Verify current authority and classify reconciliation scope.
  - Goal: establish fresh official main, old subject identity, path delta, and
    preserve-only 02A boundary before editing.
  - Work Steps: clone official main, verify SHA/tree/status/remote, fetch the old
    subject as an object, compare old PB01 and current-main path deltas, and
    record the matrix in actual-status/evidence.
  - Implementation Gate: current official checkout is clean and the overlap
    result is known.
  - Acceptance: current base is bound, overlap is `0`, and 02A is preserve-only.

### P1: PB01 carry-forward and installed contract repair

- Phase Goal: carry the disjoint reviewed PB01 delta and close only the missing
  installed launcher requirement.
- Phase Boundary:
  - In scope: bootstrap source, package/install lists, focused PB01 tests, and
    the installed required-file tuple.
  - Out of scope: 02A vendor/provenance/test/report paths and all live actions.
  - Dependencies: P0-A current-main and overlap evidence.
- Phase Implementation Rule: implement the carry-forward slice, verify it, then
  implement the one-line contract/test slice and verify it.

- [x] P1-A: Carry forward the PB01 delta without touching 02A.
  - Goal: reproduce the reviewed beginner bootstrap behavior on current main.
  - Scope Boundary:
    - Editable: PB01 source, package/install lists, focused PB01 tests.
    - Inspect-only: current 02A paths and old PB01 source.
    - Preserve-only: existing workflow, BG01, EFF01, governance, and current main.
    - Out of scope: remote writes and release/deployment artifacts.
  - Non-Goals: no mechanical whole-commit overwrite and no second control plane.
  - Pre-flight Questions:
    - Data source: exact old PB01 subject and current official main.
    - Display permission: local source/evidence only; no secrets.
    - DB read/write flow: N/A; isolated filesystem state only.
    - DB write flow: N/A.
    - Render location: N/A; CLI result only.
    - UI behavior flow: N/A; no public UI.
    - Docker runtime: N/A; standard-library CLI.
    - Playwright target: N/A.
    - Behavior test: fresh/reused/installed/ambiguous/conflict/idempotent PB01 cases.
    - Cleanup/quarantine: repo-local isolated candidate only; preserve old roots.
    - External side effects: none.
    - N/A notes: user verification ceiling excludes Anvien and broad suites.
  - Work Steps:
    1. Apply only the disjoint PB01 source/package/install/test delta.
       - UI flow check: N/A.
       - DB/data flow check: isolated filesystem roots only.
       - Render location check: CLI result.
       - Mini QA: run the focused PB01 module.
       - Evidence target: `E1-P1A-CARRY1`.
    2. Inspect the diff to prove all current 02A paths remain untouched.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: N/A.
       - Mini QA: run a focused path-presence check.
       - Evidence target: `E1-P1A-02A1`.
  - Implementation Gate: P0-A is complete and no path overlap exists.
  - Acceptance:
    - Source: PB01 source is present on current-main ancestry.
    - Runtime/UI: N/A.
    - DB/data: no production or user data touched.
    - Behavior test: prior focused PB01 behavior remains green.
    - Cleanup/quarantine: no old candidate mutation.
    - Evidence IDs: `E1-P1A-CARRY1`, `E1-P1A-02A1`.
    - Actual-status rows refreshed: PB01 `partial -> correct` if verified.
    - Result: complete. The five PB01 implementation/package/install/test
      paths were carried forward; the four historical PB01 plan documents and
      all current-main-only 02A paths were not copied.
  - Evidence Targets: `E1-P1A-CARRY1..E1-P1A-02A1`.
  - Actual-status Update: record exact carry-forward paths and 02A preservation.
  - Commit Boundary: commit after the carry-forward slice passes.

- [x] P1-B: Require and reject the installed PB01 launcher correctly.
  - Goal: close the confirmed installed-runtime required-file gap minimally.
  - Scope Boundary:
    - Editable: installed required-file tuple and one focused regression test.
    - Inspect-only: package/install copy lists and source discovery.
    - Preserve-only: all other validation and orchestration behavior.
    - Out of scope: validator redesign and broad tests.
  - Non-Goals: no new runtime layer or installer framework.
  - Pre-flight Questions:
    - Data source: Supervisor finding at old PB01 `scripts/p2p_bootstrap.py`.
    - Display permission: local evidence only.
    - DB read/write flow: N/A.
    - DB write flow: N/A.
    - Render location: N/A.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: valid installed runtime with/without launcher.
    - Cleanup/quarantine: temporary installed roots only.
    - External side effects: none.
    - N/A notes: package/install checks are static and focused.
  - Work Steps:
    1. Add `scripts/p2p_bootstrap.py` to `INSTALLED_REQUIRED_FILES`.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: N/A.
       - Mini QA: compile the changed module.
       - Evidence target: `E1-P1B-FIX1`.
    2. Add positive and negative installed-runtime cases and run them.
       - UI flow check: N/A.
       - DB/data flow check: isolated install roots.
       - Render location check: structured CLI result.
       - Mini QA: focused module rerun.
       - Evidence target: `E2-P2A-INSTALL1`.
  - Implementation Gate: P1-A source carry-forward is present and scoped.
  - Acceptance:
    - Source: tuple requires the launcher.
    - Runtime/UI: N/A.
    - DB/data: isolated roots only.
    - Behavior test: present launcher accepted; missing launcher rejected.
    - Cleanup/quarantine: no user project overwritten.
    - Evidence IDs: `E1-P1B-FIX1`, `E2-P2A-INSTALL1`.
    - Actual-status rows refreshed: installed contract `partial -> correct`.
    - Result: complete. `scripts/p2p_bootstrap.py` is now an installed
      required file; present and missing-launcher outcomes pass.
  - Evidence Targets: `E1-P1B-FIX1`, `E2-P2A-INSTALL1`.
  - Actual-status Update: record both installed-runtime outcomes.
  - Commit Boundary: commit after focused acceptance passes.

### P2: Focused verification and candidate closure

- [x] P2-A: Run the verification ceiling and prepare the candidate packet.
  - Goal: prove only PB01, launcher contract, package/install, overlap, compile,
    and diff boundaries.
  - Work Steps: run focused tests, static package/install checks, compile/diff
    checks, record exact candidate SHA/tree/base, and update evidence.
  - Implementation Gate: P1-A and P1-B pass.
  - Acceptance: all relevant checks pass and no broad suite/Anvien is run.
  - Result: complete. Focused PB01 is 16/16; package/install contract,
    compile, and diff checks pass. Compile emitted one pre-existing unrelated
    `SyntaxWarning` in `tests/test_p2p_live_certification.py` and no error.

- [ ] P3-A: Independent Supervisor review.
  - Goal: independently review current-main ancestry, PB01 acceptance, launcher
    requirement, 02A preservation, single control plane, and no live action.
  - Work Steps: call one fresh Supervisor; do not repair during review.
  - Implementation Gate: P2-A evidence exists.
  - Acceptance: Supervisor `PASS`, or truthful blocker recorded.

- [ ] P3-B: Close the unpromoted candidate.
  - Goal: record final identity, clean worktree, and explicit Owner Gate.
  - Work Steps: inspect diff/status, commit code and evidence checkpoints, and
    stop without promotion.
  - Implementation Gate: P3-A passes.
  - Acceptance: candidate is descended from current main, unpromoted, and ready
    for a separately authorized Owner Gate.

## Risk Notes

- Current 02A history is the primary preservation risk; path intersection is
  recorded as empty and current-main behavior wins.
- The installed launcher tuple is a fail-closed contract boundary; only one
  required-file entry and its direct test should change.
- A technical PASS does not authorize promotion, release, deployment, or live
  activation.
