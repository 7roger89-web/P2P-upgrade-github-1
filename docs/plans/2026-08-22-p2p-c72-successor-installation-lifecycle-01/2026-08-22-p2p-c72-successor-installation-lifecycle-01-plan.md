# P2P C72 Successor Installation Lifecycle 01 Plan

## Metadata

- Date: `2026-08-22`
- Status: `PASS_WITH_DISCLOSURES / P2P_INSTALLATION_LIFECYCLE_SUCCESSOR_CANDIDATE_VERIFIED`
- Plan: `docs/plans/2026-08-22-p2p-c72-successor-installation-lifecycle-01/2026-08-22-p2p-c72-successor-installation-lifecycle-01-plan.md`
- Evidence: `docs/plans/2026-08-22-p2p-c72-successor-installation-lifecycle-01/2026-08-22-p2p-c72-successor-installation-lifecycle-01-evidence.md`
- Benchmark: `docs/plans/2026-08-22-p2p-c72-successor-installation-lifecycle-01/2026-08-22-p2p-c72-successor-installation-lifecycle-01-benchmark.md`
- Actual status: `docs/plans/2026-08-22-p2p-c72-successor-installation-lifecycle-01/2026-08-22-p2p-c72-successor-installation-lifecycle-01-actual-status.md`

## Goal

Build the minimum new successor from the clean canonical-reconciliation lineage that makes normal installed-project adoption produce and validate a canonical `.p2p/project-pin.json`, resolves project-eval initialization only where the repository contract requires it, and creates exactly one new durably sealed candidate without modifying `.72`, changing official `.19`, merging Manus C43, implementing AERG, or promoting.

## Rules

- Complete P0 actual status before implementation work.
- Preserve `.72` byte-for-byte and preserve historical records append-only.
- Do not merge or copy `p2p-controlled-execution-hardening-01`.
- Do not implement AERG, Large Goal, new routers, or unrelated framework work.
- Use the existing pin schema and one normal lifecycle; no handwritten pin fixtures.
- Do not weaken Doctor, drift, eval, approval, or promotion gates.
- Commit every verified implementation slice; run Anvien change detection before each implementation commit.
- Mint exactly one new version and seal it immediately; never remint the published version.
- No approval finalization, promotion, merge to `origin/main`, deployment, credentials, or authoritative project mutation.

## Problem

Independent review proved `.72` non-promotable because the exact installed distribution did not create `.p2p/project-pin.json`. The source repository contains historical pin tooling, but the durable `.72` package did not contain a normal packaged producer. The successor must close that exact lifecycle gap with the smallest canonical implementation and prove it through a fresh package-only install.

## Scope

- clean successor branch from `origin/codex/p2p-canonical-lineage-repair-01`;
- canonical pin schema, producer, installer/adoption wiring, readers and fail-closed checks;
- project-eval initialization only if the installed distribution contract requires it;
- direct tests for install, pin identity, stale/malformed pin, mutation blocking, eval setup, Doctor, and packaging;
- derived current governance regeneration after source freeze;
- one successor artifact, immediate durable seal, fresh remote-derived verification, technical `p2p_gate.py prepare`, and branch push.

## Non-Goals

Manus C43, Controlled Execution Hardening, AERG, Large Goal, new framework/router, official promotion, `origin/main` mutation, historical approval rewriting, public release/deployment, and authoritative Game Truyện/Gia Phả/Logistics mutation or installation.

## Requirements

- Official authority remains `origin/main`; official baseline remains `8.4.7-C-codex.19` with SHA `3a9ee51321e1f5e40e35ce73eb90727cddb571a672aa095d16d76af2feb03dd8`.
- `.72` remains `VALID_UNPROMOTED_NONPROMOTABLE_CANDIDATE` with SHA `70613080d2ddbb92a52d2d79186e125439ec7f5ba8a6fa87bda9208d1b39d872`.
- Successor version is derived from the canonical version policy and is not `.41`, `.46`, `.47`, `.48`, `.71`, or `.72`.
- Pin schema, required fields, creation/update/invalidation semantics are recovered from existing contracts before editing.
- Packaged distribution contains the actual pin producer; source-tree-only tooling cannot satisfy acceptance.
- Missing/wrong/stale/malformed pin and permission denial fail closed.
- Project-eval lifecycle is either verified as normal distribution/adoption initialization or honestly classified as project-owned and proven through the repository-defined disposable setup.
- Before mint: source worktree clean, full source commit/tree/object binding verified.
- Archive inventory/checksum/safety counts are all zero-defect and exact.
- Fresh install/adoption/eval/Doctor, MAP-BEFORE-WORK, regression, provider neutrality, and actual technical prepare pass; approval remains pending only.

## Acceptance Criteria

- `PROJECT_PIN_PRODUCER` is packaged and writes the canonical schema through the normal beginner-first lifecycle.
- Fresh package-only install yields a valid pin with exact version, artifact SHA, project binding, installation class, source binding, Doctor state, and provenance.
- All required negative pin/mutation cases block.
- `PROJECT_EVAL_NORMAL_LIFECYCLE=VERIFIED`, `PROJECT_LOCAL_DOCTOR=HEALTHY`, `STRICT_INSTALLED_DOCTOR=HEALTHY`.
- `DRIFT_GATE=PASS`, `P2P_GATE_PREPARE=PASS`, approval state is pending/pre-owner only.
- Exactly one new durable candidate exists, two independent hashes match, and fresh remote-derived worktree confirms byte identity.
- `NEW_UNEXPLAINED_FAILURES=0`, `MANUS_C43_PARALLEL_LANE_MERGED=NO`, `AERG_STATUS=ACCEPTED_PLANNED_NOT_IMPLEMENTED_IN_THIS_SUCCESSOR`.

## Checklist

- [x] P0-A: Complete actual status before implementation work.
  - Goal: establish clean-lineage, contract, version, pin, eval, and sibling-lane reality.
  - Work Steps: inspect current refs and `.72`; read adoption/Doctor/pin/eval/gate contracts; run Anvien refresh, file-detail, and impact for intended surfaces; classify all touch modes and update downstream slices.
  - Implementation Gate: actual-status has evidence IDs for every target and a final P0 decision.
  - Acceptance: no implementation starts on an unproven producer, schema, or version assumption.

### P1: Recover and implement the minimal installed lifecycle

- Phase Goal: bind one canonical pin producer to the real package install/adoption path and close its fail-closed invariant family.
- Phase Boundary:
  - In scope: pin schema/producer, installer/adoption wiring, readers/validation, direct lifecycle tests.
  - Out of scope: packaging mint, governance history, Manus C43, AERG, promotion.
  - Dependencies: P0 complete; exact source lineage identified.
- Phase Implementation Rule: implement `P1-A`, verify and commit; refresh status; then implement `P1-B`, verify and commit.
- Ordered Slice List:
  - P1-A: Pin contract and producer wiring.
  - P1-B: Fail-closed pin/adoption regression matrix.

- [x] P1-A: Pin contract and producer wiring
  - Goal: make the canonical installed distribution create the existing project pin exactly once at the canonical lifecycle point.
  - Scope Boundary:
    - Editable: minimal installer/adoption helper and package inclusion lists, plus direct contract tests.
    - Inspect-only: `.72` ZIP, historical reports, Manus C43 lane.
    - Preserve-only: `.19` authority and existing readers unless wiring requires a surgical fix.
    - Out of scope: new pin schema, runtime redesign, project auto-upgrade.
  - Non-Goals: source-only helper success or test-created JSON.
  - Pre-flight Questions:
    - Data source: lifecycle contract, existing `p2p_safe_installer.py`/`p2p_install_release.py`, Doctor and `project_context.py`.
    - Display permission: N/A; local installation evidence only.
    - DB read flow: N/A.
    - DB write flow: project-local `.p2p/project-pin.json` through the normal installer/adoption path.
    - Render location: installed project `.p2p` and package reports.
    - UI behavior flow: N/A; beginner CLI/PowerShell install flow.
    - Docker runtime: N/A; no application UI.
    - Playwright target: N/A.
    - Behavior test: fresh package install -> producer -> pin validation -> Doctor.
    - Cleanup/quarantine: repo-local disposable pilots only.
    - External side effects: none beyond branch-local files.
    - N/A notes: no authoritative project or external provider.
  - Work Steps:
    1. Recover schema, creation point, update/invalidation semantics and all sibling readers; run Anvien file-detail/impact before editing.
       - UI flow check: N/A; verify beginner command path instead.
       - DB/data flow check: verify project fingerprint and candidate identity are computed from canonical inputs.
       - Render location check: source helper, `install.ps1`/`install.sh`, package manifest.
       - Evidence target: `E0-P0A-CONTRACT1`, `E0-P0A-IMPACT1`.
    2. Implement the smallest producer and package it through the existing distribution contract; add direct happy/failure tests.
       - UI flow check: N/A.
       - DB/data flow check: verify pin write is atomic/local and exact identity-bound.
       - Render location check: installed package contains producer and no source checkout dependency.
       - Evidence target: `E1-P1A-PRODUCER1`, `E1-P1A-PACKAGE1`, `E1-P1A-TEST1`.
  - Implementation Gate:
    - Anvien impact/file-detail evidence identifies the exact invariant family and no conflicting authority.
    - Canonical schema is existing and source-bound; no new competing pin format.
  - Acceptance:
    - Source: producer is one normal lifecycle path and packaged.
    - Runtime/UI: fresh package-only install creates the pin without manual JSON.
    - DB/data: pin fields bind exact candidate/project/source/health identity.
    - Behavior test: lifecycle happy path and producer absence/source-tree independence pass.
    - Cleanup/quarantine: only disposable project state is mutated.
    - Evidence IDs: `E1-P1A-PRODUCER1..E1-P1A-TEST1`.
    - Actual-status rows refreshed: producer, installer, package membership.
  - Evidence Targets: schema map, producer path, package membership, fresh normal install.
  - Actual-status Update: `missing/unbound -> correct` only after package-only fresh evidence.
  - Commit Boundary: one focused implementation/test commit after acceptance.

- [x] P1-B: Fail-closed pin/adoption regression matrix
  - Goal: prove wrong, missing, stale, malformed, and permission-denied pin states cannot authorize mutation.
  - Scope Boundary:
    - Editable: direct tests and minimal validation wiring required by existing readers.
    - Inspect-only: unrelated runtime capabilities and historical fixtures.
    - Preserve-only: MAP-BEFORE-WORK semantics already verified in `.72`.
    - Out of scope: new authorization features or authority widening.
  - Non-Goals: claiming live Manus or external project proof.
  - Pre-flight Questions:
    - Data source: existing project context/pin readers and mutation gate tests.
    - Display permission: N/A.
    - DB read flow: N/A.
    - DB write flow: disposable filesystem only.
    - Render location: test evidence and installed project state.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: six required fail-closed cases plus authorized valid case.
    - Cleanup/quarantine: isolated temp project per test.
    - External side effects: none.
    - N/A notes: no authoritative project.
  - Work Steps:
    1. Add/run direct behavior tests for missing, wrong SHA, wrong version, wrong fingerprint, stale/malformed pin, and permission denial.
       - UI flow check: N/A.
       - DB/data flow check: mutation remains absent when gate blocks.
       - Render location check: test results under repo-local `.tmp` and evidence ledger.
       - Evidence target: `E1-P1B-NEG1..E1-P1B-NEG6`.
    2. Run focused installer, project-context, MAP-BEFORE-WORK, and Doctor suites; refresh status.
       - UI flow check: N/A.
       - DB/data flow check: valid pin allows only bounded authorized path.
       - Render location check: no authoritative paths touched.
       - Evidence target: `E1-P1B-RUNTIME1`.
  - Implementation Gate: P1-A producer passes and no fallback writer exists.
  - Acceptance:
    - Source: all sibling readers use the same canonical schema.
    - Runtime/UI: valid case works; all required invalid cases block.
    - DB/data: zero unauthorized mutation in negative cases.
    - Behavior test: exact named matrix passes.
    - Cleanup/quarantine: disposable state isolated and removed/preserved only as evidence.
    - Evidence IDs: `E1-P1B-NEG1..E1-P1B-RUNTIME1`.
    - Actual-status rows refreshed: pin validation and mutation gate.
  - Evidence Targets: negative matrix, Doctor, MAP-BEFORE-WORK, permission gate.
  - Actual-status Update: fail-closed family becomes `correct` only after direct runtime tests.
  - Commit Boundary: separate focused regression commit.

### P2: Resolve eval lifecycle and current governance

- Phase Goal: prove project-eval normal lifecycle, freeze material source, and regenerate only current derived governance.
- Phase Boundary:
  - In scope: eval initialization contract, source freeze, Live Specs/current technical evidence.
  - Out of scope: historical approval rewrite, `.72` mutation, final approval.
  - Dependencies: P1 complete.

- [x] P2-A: Project-eval lifecycle closure
  - Goal: classify and implement only the repository-defined project-eval initialization required by installed use.
  - Scope Boundary:
    - Editable: minimal adoption/eval initialization and direct eval tests if contract requires.
    - Inspect-only: arbitrary fixture creation and unrelated eval frameworks.
    - Preserve-only: project-owned eval semantics where contract says owner-created.
    - Out of scope: synthetic PASS or hidden source checkout dependency.
  - Non-Goals: inventing project metrics.
  - Pre-flight Questions:
    - Data source: `project-eval.template.json`, `p2p_eval.py`, `p2p_gate.py`, install/adoption docs.
    - Display permission: N/A.
    - DB read/write flow: disposable project files only.
    - Render location: `.p2p/evals` and gate evidence.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: normal installed lifecycle -> suite/owner setup -> eval PASS.
    - Cleanup/quarantine: fresh disposable pilot.
    - External side effects: none.
    - N/A notes: if project-owned, document normal owner setup without source repo.
  - Work Steps:
    1. Classify suite ownership and run repository-defined normal setup.
       - UI flow check: N/A.
       - DB/data flow check: suite is local and disposable.
       - Render location check: installed system and project eval paths.
       - Evidence target: `E2-P2A-CLASS1`.
    2. Run eval validation/gate and update only required lifecycle code/tests.
       - UI flow check: N/A.
       - DB/data flow check: no hidden or arbitrary case injection.
       - Render location check: evidence under `.tmp`/reports.
       - Evidence target: `E2-P2A-EVAL1`.
  - Implementation Gate: contract classification is explicit and source-tree independence is proven.
  - Acceptance:
    - Source: eval status is honest and repository-defined.
    - Runtime/UI: installed normal flow reaches eval gate.
    - DB/data: disposable-only eval state.
    - Behavior test: eval PASS or exact contract blocker.
    - Cleanup/quarantine: no authoritative mutation.
    - Evidence IDs: `E2-P2A-CLASS1`, `E2-P2A-EVAL1`.
    - Actual-status rows refreshed: project-eval lifecycle.
  - Evidence Targets: ownership classification, normal setup, eval PASS.
  - Actual-status Update: `missing -> correct` only with normal installed evidence.
  - Commit Boundary: separate eval lifecycle commit if code changes; otherwise evidence-only checkpoint.

- [x] P2-B: Source freeze and derived governance reconciliation
  - Goal: commit all material source, verify provenance, and rebuild current derived governance surfaces without historical mutation.
  - Scope Boundary:
    - Editable: current derived Live Specs/lock/technical preview/candidate binding per canonical commands.
    - Inspect-only: historical approvals/reports and `.72`.
    - Preserve-only: official `.19` authority and historical lineage.
    - Out of scope: approval/finalization/promotion.
  - Non-Goals: making old approval match the new candidate by editing it.
  - Pre-flight Questions:
    - Data source: FACT_LEDGER and current canonical governance commands.
    - Display permission: N/A.
    - DB read/write flow: N/A.
    - DB write flow: derived JSON only.
    - Render location: governance current-state and reports.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: source freeze, drift, provenance, and historical hash comparison.
    - Cleanup/quarantine: repo-local logs only.
    - External side effects: none until authorized push.
    - N/A notes: no user project.
  - Work Steps:
    1. Commit material source, run source/tree/object binding and Anvien detect-changes.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: commit/evidence paths.
       - Evidence target: `E2-P2B-SOURCE1`.
    2. Run canonical derived governance commands, then drift gate and historical immutability checks.
       - UI flow check: N/A.
       - DB/data flow check: generated projections only.
       - Render location check: candidate subject exact new successor.
       - Evidence target: `E2-P2B-DRIFT1`.
  - Implementation Gate: material source is committed and source tree is clean.
  - Acceptance:
    - Source: full 40-char commit/tree and object binding verified.
    - Runtime/UI: N/A.
    - DB/data: no historical record changed.
    - Behavior test: drift PASS.
    - Cleanup/quarantine: temporary logs repo-local.
    - Evidence IDs: `E2-P2B-SOURCE1`, `E2-P2B-DRIFT1`.
    - Actual-status rows refreshed: source provenance and governance drift.
  - Evidence Targets: source binding, Anvien changes, derived hashes, drift PASS.
  - Actual-status Update: source/governance becomes `correct` only after exact subject-bound evidence.
  - Commit Boundary: one derived-governance checkpoint after drift PASS.

### P3: Mint, seal, install, prepare, and deliver

- Phase Goal: create one new candidate, seal it immediately, validate it from a fresh remote-derived worktree, and push only the successor branch.
- Phase Boundary:
  - In scope: version selection, package, inventory, seal, fresh install/adoption/eval/Doctor, negative matrix, regression, prepare, push.
  - Out of scope: approval, promotion, main merge, deployment.
  - Dependencies: P2 complete; source clean and drift PASS.

- [x] P3-A: Mint exactly one successor and durable seal
  - Goal: produce one new version and preserve exact bytes in Git.
  - Scope Boundary:
    - Editable: candidate metadata, packaging evidence, durable artifact path.
    - Inspect-only: `.72` and historical candidates.
    - Preserve-only: official `.19` and source history.
    - Out of scope: remint same version.
  - Non-Goals: public release or promotion.
  - Pre-flight Questions:
    - Data source: canonical version policy, source commit/tree, distribution contract.
    - Display permission: N/A.
    - DB read/write flow: N/A.
    - DB write flow: artifact/evidence files only.
    - Render location: `reports/candidates/` and seal report.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: package inventory/checksum and two independent hashes.
    - Cleanup/quarantine: no alternate candidate copies after publication.
    - External side effects: Git branch only.
    - N/A notes: no external release.
  - Work Steps:
    1. Derive unused version, freeze source, mint one candidate, verify inventory/checksum.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: exact candidate path and metadata.
       - Evidence target: `E3-P3A-MINT1`.
    2. Seal immediately, commit artifact, and verify from fresh remote-derived worktree.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: durable path, SHA, remote proof.
       - Evidence target: `E3-P3A-SEAL1`.
  - Implementation Gate: source commit/tree/object binding verified; no source dirt.
  - Acceptance:
    - Source: candidate binds exact source commit/tree.
    - Runtime/UI: N/A.
    - DB/data: N/A.
    - Behavior test: inventory/checksum/safety all pass.
    - Cleanup/quarantine: one published candidate only.
    - Evidence IDs: `E3-P3A-MINT1`, `E3-P3A-SEAL1`.
    - Actual-status rows refreshed: candidate identity and durable seal.
  - Evidence Targets: version rationale, artifact identity, inventory, seal, remote proof.
  - Actual-status Update: candidate becomes `bound-correct` only after fresh remote verification.
  - Commit Boundary: mint/seal commit, followed by separate post-seal evidence commit if required.

- [x] P3-B: Fresh adoption, regression, technical prepare, and branch delivery
  - Goal: prove the successor is technically gate-ready while remaining unpromoted.
  - Scope Boundary:
    - Editable: disposable pilot state and evidence reports.
    - Inspect-only: published artifact bytes and main.
    - Preserve-only: historical records.
    - Out of scope: final approval/promotion.
  - Non-Goals: claiming Manus live execution or AERG.
  - Pre-flight Questions:
    - Data source: durable successor and fresh remote-derived checkout.
    - Display permission: N/A.
    - DB read/write flow: disposable pilot only.
    - DB write flow: project-local `.p2p` evidence only.
    - Render location: reports and branch evidence.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: install/adoption/eval/Doctor, MAP-BEFORE-WORK, regression, prepare.
    - Cleanup/quarantine: repo-local disposable pilots.
    - External side effects: push successor branch only.
    - N/A notes: Manus no credentials; no authoritative projects.
  - Work Steps:
    1. Run fresh package-only install, adoption, eval, strict Doctor, MAP-BEFORE-WORK and negative matrix.
       - UI flow check: N/A.
       - DB/data flow check: verify pin and no unauthorized mutation.
       - Render location check: pilot evidence.
       - Evidence target: `E3-P3B-PILOT1`.
    2. Run regression/security/provider-neutral checks and exact `p2p_gate.py prepare`.
       - UI flow check: N/A.
       - DB/data flow check: authoritative mutation counters remain zero.
       - Render location check: technical report and pending approval state.
       - Evidence target: `E3-P3B-GATE1`.
    3. Run detect-changes, commit evidence, push branch, and verify remote head from a fresh worktree.
       - UI flow check: N/A.
       - DB/data flow check: no authoritative writes.
       - Render location check: local/remote match.
       - Evidence target: `E3-P3B-PUSH1`.
  - Implementation Gate: durable candidate and fresh remote seal proof exist.
  - Acceptance:
    - Source: no post-mint material dirt.
    - Runtime/UI: N/A.
    - DB/data: authoritative mutation `0`.
    - Behavior test: technical prepare PASS with approval pending.
    - Cleanup/quarantine: pilots repo-local and disposable.
    - Evidence IDs: `E3-P3B-PILOT1`, `E3-P3B-GATE1`, `E3-P3B-PUSH1`.
    - Actual-status rows refreshed: all final gates and branch delivery.
  - Evidence Targets: full suite counts, pilot pin/eval/Doctor, negative matrix, prepare, push.
  - Actual-status Update: final PASS only if every required gate is verified.
  - Commit Boundary: final evidence commit; no merge or promotion.

- [x] Pn-A: Call supervisor for the implemented-plan acceptance loop.
  - Goal: independently review the complete successor candidate and exact evidence.
  - Work Steps: create coder report, run supervisor review, fix only explicit rejection, rerun review.
  - Implementation Gate: all required phases complete or exact blocker recorded.
  - Acceptance: supervisor passes or records a precise allowed terminal blocker.
- [x] Pn-B: Remove dead work created during this plan.
  - Goal: retain only required source, candidate, evidence, and plan artifacts.
  - Work Steps: inspect disposable outputs and plan-created files; remove only dead disposable work; preserve evidence.
  - Implementation Gate: no `.72`/main/authoritative mutation.
  - Acceptance: final diff contains no rejected implementation artifact.
- [x] Pn-C: Close the plan.
  - Goal: record final validation, detect-changes, commits, remote match, and exact verdict.
  - Work Steps: update ledgers, verify final hashes, run supervisor, push only successor branch, stop.
  - Implementation Gate: Pn-A and Pn-B pass or exact blocker recorded.
  - Acceptance: final evidence is traceable and no promotion occurred.

## Risk Notes

- The highest risk is accidentally treating the source-only helper or a fixture as the installed distribution capability; acceptance must use only the durable packaged candidate.
- Existing governance drift may expose a policy defect; never rewrite historical approval records to force a PASS.
- Windows path length and line-ending behavior may affect test harnesses; record same-environment limitations without altering product semantics.
- Live Manus is optional and must remain honestly `NOT_RUN / NO_CREDENTIALS` when unavailable.
