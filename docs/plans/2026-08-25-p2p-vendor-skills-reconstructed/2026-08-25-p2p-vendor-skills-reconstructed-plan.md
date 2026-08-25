# P2P Vendor Skills — Reconstruct Candidate on Valid Git Authority Plan

## Metadata

- Date: `2026-08-25`
- Status: `Owner approval recorded; exact checkpoint unpromoted`
- Plan: `docs/plans/2026-08-25-p2p-vendor-skills-reconstructed/2026-08-25-p2p-vendor-skills-reconstructed-plan.md`
- Evidence: `docs/plans/2026-08-25-p2p-vendor-skills-reconstructed/2026-08-25-p2p-vendor-skills-reconstructed-evidence.md`
- Benchmark: `docs/plans/2026-08-25-p2p-vendor-skills-reconstructed/2026-08-25-p2p-vendor-skills-reconstructed-benchmark.md`
- Actual status: `docs/plans/2026-08-25-p2p-vendor-skills-reconstructed/2026-08-25-p2p-vendor-skills-reconstructed-actual-status.md`

## Goal

Reconstruct the two local vendor-skill integrations from the read-only broken
snapshot onto a fresh valid Git worktree, preserving the verified provider-
neutral baseline and proving the result with differential tests, doctors,
Git diff authority, Anvien change detection, and an independent supervisor
review. The result remains an unpromoted candidate.

## Rules

- Complete P0 actual status before implementation work.
- Update each checklist item immediately when it is completed.
- Record evidence as work completes and keep measured counts in the benchmark ledger.
- The broken root and its `.git` metadata are read-only candidate material.
- Do not initialize, repair, reset, clean, force-remove, or copy Git metadata.
- Do not copy the whole broken snapshot or absorb unrelated owner drift.
- Do not copy profiles/configuration, regenerate canonical role hashes, fabricate
  Aesthetica/runtime evidence, promote, merge, push, release, deploy, or publish.
- Start from `557b502758581812a8845355ed6b426ba75372ec` because current valid Git
  refs and the verified worktree do not prove a newer descendant canonical or
  owner-promoted base for this scope.
- Run Anvien after graph refresh; run file-detail and impact before editing
  functions or shared contracts, and run detect-changes before any checkpoint.
- Full build for this Python/backend slice is `python -m compileall -q
  .p2p/system scripts tests`; browser, Docker, and Playwright evidence are N/A.
- A green direct test is not enough for acceptance; the C35 differential,
  doctor classification, minimal Git scope, and supervisor verdict remain gates.

## Problem

The broken source snapshot contains the intended vendor registry records,
adapter, router projection, and vendor tests, but its root Git authority is
unusable and its full snapshot diverges from the verified baseline in
unrelated runtime/profile/role surfaces. Copying that snapshot wholesale
causes the provider-neutral C35 suite to fail with canonical role-spec hash
errors. The safe unit is therefore the vendor integration seam only.

## Scope

- Verify valid local Git worktree, remote URL, refs, lineage evidence, and the
  explicit reconstruction base.
- Create a new branch/worktree from the verified base with clean pre-change
  status.
- Re-verify the seven supplied broken-root artifact/tree hashes.
- Add the two vendor snapshots byte-for-byte and their manifest-driven adapter.
- Apply only vendor-specific registry records, the existing-router projection,
  and focused/foundation test expectations required by that integration.
- Run C35 before/after, focused tests, compile/build, relevant doctors, Git diff,
  Anvien detect-changes, and an independent supervisor review.
- Create one checkpoint commit only if every user-specified technical gate passes.

## Non-Goals

- Repairing or making claims from the broken root `.git`.
- Reconstructing missing `.codex` profiles/configuration or unrelated source drift.
- Editing `role_contract.py`, `role_verifier.py`, `model.py`, C35 tests, canonical
  role fingerprints, or vendor snapshot content.
- Installing dependencies, invoking external renderers, using network services,
  changing protected governance, merging, promoting, deploying, or releasing.

## Requirements

- The candidate worktree is Git-valid, branch-bound, and clean before edits.
- The base SHA/tree and base reason are recorded; the remote is the supplied
  GitHub URL.
- Canonical identity set remains exactly eight with denominator `8` and full
  quorum `8/8`; vendor skills are ordinary `SKILL` entries and never votes.
- Vendor discovery is metadata-only, lazy, path-safe, hash-bound, offline, and
  permission-free; optional operation dependency failures remain explicit.
- The existing router remains the only router and its current baseline logic is
  preserved outside vendor-specific hunks.
- Vendor tree hashes remain exactly the supplied values.
- C35 is `57/57`, vendor integration is `17/17`, foundation is `28/28`, and
  combined focused evidence is `45/45`.
- Doctor failures are classified as inherited, attributable, environmental,
  optional-expected, or unknown; no failure is hidden or relabeled as PASS.
- The final diff contains only the reconstruction scope and evidence/governance
  files required by this plan.

## Acceptance Criteria

- `RECONSTRUCTION_BASE_SHA` and `RECONSTRUCTION_BASE_REASON` are recorded.
- New worktree shows the expected branch, exact base SHA/tree, supplied remote,
  and clean pre-change status.
- Vendor snapshots match both supplied tree hashes after reconstruction.
- C35 before and after are both `57/57 OK`; no role-hash workaround is present.
- Focused suites are `17/17`, `28/28`, and `45/45`.
- Compile/build succeeds; no attributable doctor blocker remains.
- Git status/diff is valid and narrow; Anvien detect-changes succeeds on the
  valid reconstructed worktree.
- One checkpoint exists only when all technical gates pass; no promotion occurs.
- Supervisor writes exactly one fresh `PASS` or `REJECT` verdict for this new
  candidate, independent of the old broken-root review.

## Checklist

- [x] P0-A: Complete actual status before implementation work.
  - Goal: establish the current authority, baseline, hash, test, doctor, and graph state.
  - Work Steps: inspect the broken root read-only; inspect valid Git refs and remote heads; verify `557b`; create isolated baseline worktrees; run baseline C35 and doctors; record Anvien graph/file-detail limitations.
  - Implementation Gate: the actual-status matrix classifies every editable and preserve-only surface, and the verified base is selected without relying on chat/history.
  - Acceptance: `2026-08-25-p2p-vendor-skills-reconstructed-actual-status.md` is P0 Complete with exact evidence IDs.

### P1: Authority and reconstruction worktree

- Phase Goal: establish a clean, valid Git candidate and freeze the source comparison boundary.
- Phase Boundary:
  - In scope: valid common repository, new branch/worktree, base/ref/tree/remote proof, broken-root hash recheck, Anvien graph refresh.
  - Out of scope: source edits, profile repair, broken-root Git repair, remote writes.
  - Dependencies: P0 evidence and supplied base SHA.
- Phase Implementation Rule: do not implement `P1` directly. Complete `P1-A`, refresh actual-status, then continue to `P1-B`.
- Ordered Slice List:
  - P1-A: Bind clean reconstructed worktree to verified base.
  - P1-B: Complete source/impact comparison for the vendor seam.

- [x] P1-A: Bind clean reconstructed worktree to verified base.
  - Goal: create `codex/p2p-vendor-skills-reconstructed-03` from `557b502…` without using the broken root as a working directory.
  - Scope Boundary:
    - Editable: new worktree metadata managed by valid Git.
    - Inspect-only: broken root, remote refs, existing owner worktrees.
    - Preserve-only: baseline source and all unrelated owner files.
    - Out of scope: Git repair/reset/clean/force removal and remote mutation.
  - Non-Goals: claiming 557b is promoted; changing any source file.
  - Pre-flight Questions:
    - Data source: valid local Git common repository and fresh remote-head inspection.
    - Display permission: N/A; this is a backend/repository task.
    - DB read flow: N/A; no database.
    - DB write flow: N/A; no database.
    - Render location: N/A; no UI.
    - UI behavior flow: N/A; no UI.
    - Docker runtime: N/A; Python source slice has no container contract.
    - Playwright target: N/A; no public UI.
    - Behavior test: exact C35 baseline in a detached clean worktree.
    - Cleanup/quarantine: side-effecting test baseline isolated in `.tmp` worktree.
    - External side effects: none; no push or remote write.
    - N/A notes: evidence is Git/source/test/doctor based.
  - Work Steps:
    1. Verify branch/ref/tree/remote and create the new worktree; record the clean status and exact base.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: N/A.
       - Evidence target: `E0-P0A-AUTH1..E0-P0A-BASE1`.
    2. Recheck supplied broken-root hashes and refresh the valid candidate graph.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: N/A.
       - Evidence target: `E0-P0A-HASH1`, `E0-P0A-ANV1`.
  - Implementation Gate:
    - Base and worktree proof are fresh; broken root remains untouched; baseline C35 is `57/57`.
    - No source edit starts until P0 status and planner files exist.
  - Acceptance:
    - Source: valid branch/worktree and exact base are proven.
    - Runtime/UI: N/A.
    - DB/data: N/A.
    - Behavior test: C35 baseline `57/57 OK`.
    - Cleanup/quarantine: baseline test worktree is separate from candidate.
    - Evidence IDs: `E0-P0A-AUTH1`, `E0-P0A-AUTH2`, `E0-P0A-BASE1`.
    - Actual-status rows refreshed: authority, base, worktree, C35 baseline.
  - Evidence Targets: Git commands, remote refs, hash table, baseline C35 output.
  - Actual-status Update: P1-A complete; P1-B may proceed.
  - Commit Boundary: no implementation commit; source is still unchanged.

- [x] P1-B: Complete source/impact comparison for the vendor seam.
  - Goal: identify exact vendor-specific hunks while preserving the verified baseline's newer logic.
  - Scope Boundary:
    - Editable: none during comparison.
    - Inspect-only: capabilities registry, router, model/foundation tests, candidate adapter/test/tree sources.
    - Preserve-only: role/profile/config/model surfaces and all unrelated baseline files.
    - Out of scope: whole-file replacement of existing baseline files.
  - Non-Goals: normalizing the broken candidate or fixing C35 role hashes.
  - Pre-flight Questions:
    - Data source: fresh diffs and parsed manifest records.
    - Display permission: N/A.
    - DB read flow: N/A.
    - DB write flow: N/A.
    - Render location: N/A.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: focused tests after implementation.
    - Cleanup/quarantine: no generated source files.
    - External side effects: none.
    - N/A notes: Anvien cannot resolve ignored `.p2p` files; record that limitation explicitly.
  - Work Steps:
    1. Run Anvien file-detail/impact attempts for shared router/registry and inspect the source diffs.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: N/A.
       - Evidence target: `E0-P0A-ANV2`, `E1-P1B-SCOPE1`.
    2. Freeze the minimal edit list: new adapter, two registry entries, additive router projection, vendor test, and required foundation expectation updates.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: N/A.
       - Evidence target: `E1-P1B-SCOPE2`.
  - Implementation Gate:
    - Every existing function/shared contract edit has impact evidence or an explicit Anvien not-found limitation; unrelated candidate files are excluded.
  - Acceptance:
    - Source: minimal edit list is recorded before code changes.
    - Runtime/UI: N/A.
    - DB/data: N/A.
    - Behavior test: deferred to P2/P3.
    - Cleanup/quarantine: no source mutation from comparison.
    - Evidence IDs: `E1-P1B-SCOPE1..E1-P1B-SCOPE2`.
    - Actual-status rows refreshed: scope and Anvien evidence.
  - Evidence Targets: diff excerpts, file/symbol impact output, preserve-only list.
  - Actual-status Update: P2 assumes only the frozen vendor surface is editable.
  - Commit Boundary: no commit until implementation slice and gates pass.

### P2: Vendor integration seam

- Phase Goal: reapply only the vendor integration behavior on top of the valid baseline.
- Phase Boundary:
  - In scope: unchanged vendor trees, new adapter, two registry records, additive router projection, focused tests, vendor-specific foundation expectations.
  - Out of scope: role/profile/config/model changes, canonical hash changes, external optional execution.
  - Dependencies: P1-B scope freeze and Anvien impact attempt.
- Phase Implementation Rule: complete `P2-A`, refresh actual-status, then complete `P2-B`.
- Ordered Slice List:
  - P2-A: Add vendor snapshots, adapter, and manifest records.
  - P2-B: Bind vendor readiness/projection to the existing router and tests.

- [x] P2-A: Add vendor snapshots, adapter, and manifest records.
  - Goal: make the two local vendor declarations resolvable without changing canonical or baseline authority.
  - Scope Boundary:
    - Editable: `.p2p/vendor/skill/**` for exact copies, `vendor_skill.py`, and two appended registry records.
    - Inspect-only: vendor source in broken root and baseline model/role files.
    - Preserve-only: all pre-existing registry records and baseline code.
    - Out of scope: vendor content edits, dependency installation, network, credentials.
  - Non-Goals: executing renderers or treating a snapshot as instruction authority.
  - Pre-flight Questions:
    - Data source: supplied broken-root tree and manifest hashes.
    - Display permission: N/A.
    - DB read flow: N/A.
    - DB write flow: N/A.
    - Render location: N/A.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: vendor metadata/load/hash/dependency tests.
    - Cleanup/quarantine: optional operations remain blocked and test clones are temporary under repo `.tmp`.
    - External side effects: no install/network/credential use.
    - N/A notes: the adapter is the only allowed host-code boundary for vendor optional probes.
  - Work Steps:
    1. Copy both vendor trees unchanged and verify tree/entrypoint hashes.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: N/A.
       - Evidence target: `E2-P2A-HASH1`.
    2. Add the adapter and append only the two parsed vendor records to the preserved registry.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: N/A.
       - Evidence target: `E2-P2A-SRC1`.
  - Implementation Gate:
    - Source diff touches no role/profile/config/model surface and registry validation remains valid with canonical `8/8`.
  - Acceptance:
    - Source: adapter and two records are present; existing records are preserved.
    - Runtime/UI: N/A.
    - DB/data: N/A.
    - Behavior test: registry parses and vendor hashes match.
    - Cleanup/quarantine: no optional dependency installation.
    - Evidence IDs: `E2-P2A-HASH1`, `E2-P2A-SRC1`.
    - Actual-status rows refreshed: vendor surfaces become partial/ready for router binding.
  - Evidence Targets: source diff, parsed registry, exact hashes.
  - Actual-status Update: vendor adapter/manifest/tree rows move to implemented pending focused tests.
  - Commit Boundary: one small implementation slice may be committed only after its local acceptance and detect-changes gate.

- [x] P2-B: Bind vendor readiness/projection to the existing router and tests.
  - Goal: route the two vendor skills through the existing foundation router with lazy metadata and fail-closed optional operations.
  - Scope Boundary:
    - Editable: vendor-specific hunks in `router.py`, new vendor integration test, vendor-specific foundation expectation updates.
    - Inspect-only: baseline router behavior outside the additive projection.
    - Preserve-only: C35 test and role/profile/runtime hash surfaces.
    - Out of scope: second router, provider/model selection, optional renderer execution.
  - Non-Goals: changing UIUX/Aesthetica semantics outside vendor projection.
  - Pre-flight Questions:
    - Data source: loaded manifests, local snapshot paths, existing route result.
    - Display permission: N/A.
    - DB read flow: N/A.
    - DB write flow: N/A.
    - Render location: N/A.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: `test_p2p_vendor_skill_integration` and foundation suite.
    - Cleanup/quarantine: hash-mutation clone remains temporary and isolated.
    - External side effects: none.
    - N/A notes: route output is evidence/data, not instruction or permission.
  - Work Steps:
    1. Apply only the import/readiness/result projection hunks to the baseline router.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: N/A.
       - Evidence target: `E2-P2B-SRC1`.
    2. Add/adapt focused tests and update only registry-count/adapter-boundary expectations required by the two new vendor records.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: N/A.
       - Evidence target: `E2-P2B-TEST1`.
  - Implementation Gate:
    - Source inspection shows one router, no external provider strings/install fallback, and no vendor content read during discovery.
  - Acceptance:
    - Source: additive router projection preserves baseline behavior.
    - Runtime/UI: N/A.
    - DB/data: N/A.
    - Behavior test: vendor `17/17`, foundation `28/28`, combined `45/45`.
    - Cleanup/quarantine: optional operations report blocked/NOT_REQUIRED without install.
    - Evidence IDs: `E2-P2B-SRC1`, `E2-P2B-TEST1`.
    - Actual-status rows refreshed: router/vendor integration correct pending full differential.
  - Evidence Targets: source review, focused test output, route/provenance assertions.
  - Actual-status Update: P3 may begin only after focused tests pass.
  - Commit Boundary: commit after P2-B only if local focused gates and detect-changes pass.

### P3: Differential validation and candidate checkpoint

- Phase Goal: prove the reconstruction against the clean base and close or honestly block the candidate.
- Phase Boundary:
  - In scope: build, C35 before/after, focused suites, doctors, Git diff, Anvien detect-changes, report, checkpoint, supervisor review.
  - Out of scope: fixes outside the vendor seam, promotion/merge/push/release/deploy.
  - Dependencies: completed P2 source slice.
- Phase Implementation Rule: complete `P3-A`, refresh actual-status, then complete `P3-B` and supervisor review.
- Ordered Slice List:
  - P3-A: Run full technical differential and classify doctor output.
  - P3-B: Close evidence, detect changes, checkpoint, and supervisor-review the new candidate.

- [x] P3-A: Run full technical differential and classify doctor output.
  - Goal: establish exact before/after behavior and inherited versus attributable failures.
  - Scope Boundary:
    - Editable: evidence ledgers only.
    - Inspect-only: candidate and detached clean baseline worktrees.
    - Preserve-only: source candidate and all vendor trees.
    - Out of scope: role-hash repair or doctor workaround.
  - Non-Goals: turning inherited governance drift into a vendor defect.
  - Pre-flight Questions:
    - Data source: fresh command output from both worktrees.
    - Display permission: N/A.
    - DB read flow: N/A.
    - DB write flow: N/A.
    - Render location: N/A.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: exact required suites and compileall.
    - Cleanup/quarantine: exclude test state side effects from source commit.
    - External side effects: none.
    - N/A notes: doctor package-role mismatch is expected for a development worktree and must be labeled.
  - Work Steps:
    1. Run compileall, C35 after, focused suites, and relevant doctors on candidate and clean base.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: N/A.
       - Evidence target: `E3-P3A-TEST1..E3-P3A-DOCTOR1`.
    2. Compare status and source hashes; classify every doctor difference.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: N/A.
       - Evidence target: `E3-P3A-DIFF1`.
  - Implementation Gate:
    - Required counts are exact; no attributable C35 regression or vendor-tree mutation exists.
  - Acceptance:
    - Source: no unrelated source drift.
    - Runtime/UI: N/A.
    - DB/data: N/A.
    - Behavior test: C35 `57/57`; focused `45/45`.
    - Cleanup/quarantine: test-only state is not checkpointed.
    - Evidence IDs: `E3-P3A-TEST1`, `E3-P3A-DOCTOR1`, `E3-P3A-DIFF1`.
    - Actual-status rows refreshed: technical gates and doctor classification.
  - Evidence Targets: exact outputs and differential table.
  - Actual-status Update: candidate becomes ready for scope/authority review or blocked with a named cause.
  - Commit Boundary: no checkpoint if any required technical gate fails.
  - Result: compileall exit `0`; C35 after reconstruction `57/57 OK`; focused
    vendor/foundation suites `17/17`, `28/28`, combined `45/45`; vendor trees
    unchanged; capability doctor PASS with registry `15` and canonical `8/8`.
    Package role mismatch and development governance drift match the clean-base
    inherited/expected state; no candidate-attributable doctor blocker found.

- [x] P3-B: Close evidence, detect changes, checkpoint, and supervisor-review the new candidate.
  - Goal: establish valid Git/Anvien authority and obtain an independent verdict.
  - Scope Boundary:
    - Editable: plan/evidence/benchmark/status/coder/supervisor reports and one checkpoint commit if gates pass.
    - Inspect-only: broken root and remote.
    - Preserve-only: vendor snapshots and baseline unrelated files.
    - Out of scope: promotion, merge, push, release, deployment, approval execution.
  - Non-Goals: claiming owner approval from technical PASS.
  - Pre-flight Questions:
    - Data source: Git diff, Anvien detect-changes, source review, fresh tests.
    - Display permission: N/A.
    - DB read flow: N/A.
    - DB write flow: N/A.
    - Render location: N/A.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: supervisor re-run against exact candidate SHA.
    - Cleanup/quarantine: dead/unrelated artifacts excluded before commit.
    - External side effects: no remote write.
    - N/A notes: owner gate remains separate from this checkpoint.
  - Work Steps:
    1. Run Git status/diff and Anvien detect-changes; write coder report with invariant/sibling/residual maps.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: N/A.
       - Evidence target: `E3-P3B-GIT1`, `E3-P3B-ANV1`, `E3-P3B-REPORT1`.
    2. If all gates pass, create one checkpoint, record SHA/tree, and run fresh supervisor review; otherwise record BLOCKED/REGRESSION and do not commit.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: N/A.
       - Evidence target: `E3-P3B-COMMIT1`, `E3-P3B-SUP1`.
  - Implementation Gate:
    - All technical gates, source scope, Git diff, and Anvien results are fresh and consistent.
  - Acceptance:
    - Source: final diff is narrow and reviewable.
    - Runtime/UI: N/A.
    - DB/data: N/A.
    - Behavior test: supervisor independently verifies the exact candidate.
    - Cleanup/quarantine: no dead work or untracked test state enters commit.
    - Evidence IDs: `E3-P3B-GIT1..E3-P3B-SUP1`.
    - Actual-status rows refreshed: final candidate state and owner-gate boundary.
  - Evidence Targets: Git diff, Anvien result, commit, coder report, supervisor report.
  - Actual-status Update: close as ready-for-owner-gate, regression, or blocked.
  - Commit Boundary: exactly one checkpoint commit; never merge/promote/push.
  - Current result: Git is valid, the final Anvien alias is unambiguous, and
    `detect-changes --scope all` exited `0`. The exact checkpoint is
    `d29801bd37a53207f81e89eaa295cbef0802b951` / tree
    `27bac22f1f2cba670425a28d050a566916d23265`; the pre-review to checkpoint
    implementation subject is `EXACT_MATCH`. The fresh Supervisor verdict is
    `PASS`, applies to this exact checkpoint, and the current Owner instruction
    records approval. State remains unpromoted.

- [ ] Pn-A: Call the supervisor for the implemented-plan acceptance loop.
  - Goal: independently verify the completed reconstruction against current source and evidence.
  - Work Steps:
    1. Read the new diff/report and rerun the relevant source/test/authority checks.
    2. Write one fresh supervisor report with exactly `PASS` or `REJECT`.
  - Implementation Gate: P3 evidence is complete or explicitly blocked.
  - Acceptance: supervisor verdict is recorded and final verdict maps to the user's allowed values.
- [ ] Pn-B: Remove dead work created during this plan.
  - Goal: ensure only useful plan/report artifacts remain.
  - Work Steps:
    1. Review untracked/changed files and exclude temporary test state and unused copies.
    2. Verify cleanup did not touch the broken root or vendor snapshots.
  - Implementation Gate: only plan-created artifacts are considered for cleanup.
  - Acceptance: final Git status/diff has no dead plan-created artifact.
- [ ] Pn-C: Close the plan.
  - Goal: record final validation, benchmark, detect-changes, checkpoint, and status.
  - Work Steps:
    1. Refresh all ledgers and reports with final hashes and exits.
    2. Verify worktree state and stop at owner gate.
  - Implementation Gate: supervisor has issued its verdict.
  - Acceptance: evidence is complete and no promotion action occurred.

## Risk Notes

- The valid common repository itself has unrelated dirty owner files; do not
  clean or commit them. The new worktree is the only source target.
- The Anvien index may omit ignored/hidden `.p2p` source paths; if file-detail
  or impact is unavailable, record the exact not-found output and use direct
  source diff evidence rather than claiming graph coverage.
- The clean baseline's development doctor has inherited governance drift and
  the package doctor reports a role mismatch; these are differential context,
  not vendor PASS evidence. Any new candidate-only failure is attributable
  until disproven.
- Optional render dependencies and external services remain blocked by design.
- Technical PASS, checkpoint commit, supervisor PASS, Owner approval, and
  promotion are separate states.
