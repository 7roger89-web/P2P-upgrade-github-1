# P2P Canonical Lineage Repair 01 Plan

## Metadata

- Date: `2026-08-21`
- Status: `BLOCKED / REAL_MANUS_SENTINEL_UNAVAILABLE before candidate mint.`
- Plan: `docs/plans/2026-08-21-p2p-canonical-lineage-repair-01/2026-08-21-p2p-canonical-lineage-repair-01-plan.md`
- Evidence: `docs/plans/2026-08-21-p2p-canonical-lineage-repair-01/2026-08-21-p2p-canonical-lineage-repair-01-evidence.md`
- Benchmark: `docs/plans/2026-08-21-p2p-canonical-lineage-repair-01/2026-08-21-p2p-canonical-lineage-repair-01-benchmark.md`
- Actual status: `docs/plans/2026-08-21-p2p-canonical-lineage-repair-01/2026-08-21-p2p-canonical-lineage-repair-01-actual-status.md`

## Goal

Rebuild one clean, source-bound successor candidate from a fresh `origin/main`
checkout while preserving `origin/main` official baseline `.19`, recovering only
verified later P2P implementation, separating release authorities, and stopping
before promotion or merge.

## Rules

- Complete P0 actual status before implementation work.
- The only canonical official authority for this task is `origin/main` at task start.
- Preserve the `.19` official version and exact SHA; candidate identity must never replace official authority.
- Treat `.41`, `.46`, `.47`, `.48`, and `.71` as historical/development inputs only.
- Work only in the fresh worktree and branch created from `origin/main`; preserve the dirty owner checkout.
- Do not mutate or merge `origin/main`; do not tag, deploy, publish, approve, or promote.
- Do not mutate Game Truyện, Gia Phả, Logistics, or any authoritative user project.
- Use Anvien after refresh for file detail, impact, and detect-changes evidence.
- Keep all temporary logs and disposable pilots under repo-local `.tmp/`.
- Keep the source tree clean before candidate mint; generate artifact-only identity/inventory/checksum records in the staging pipeline.
- Update each checklist item immediately when it is completed.
- Record evidence as work completes.
- Record benchmarkable counts or measurements when they are taken.
- Update later phase status assumptions, next actions, and work steps when actual-status evidence changes the repo state.
- After completing a phase or implementation slice and refreshing `actual-status.md`, update the next affected phase's work steps as needed to match the latest repo reality, while preserving that phase's original goal, scope, acceptance criteria, and major phase order.
- Run Anvien detect-changes before every implementation-slice commit when implementation work was performed.
- No Docker or Playwright evidence is applicable: this is a Python package/CLI runtime and no web UI is changed; package-build and disposable-project runtime evidence are required instead.
- Hidden fallback is forbidden; unavailable live Manus transport must be reported as unavailable, never simulated.

## Problem

Independent review established `BLOCKED / MULTIPLE_COMPETING_GOVERNANCE_AUTHORITIES`:
the canonical main line still states official `.19`, while later feature/promotion
refs contain divergent `.41/.46/.47/.48/.71` claims, inconsistent package identity,
missing canonical merge/binding, and incomplete evidence. A clean successor must be
assembled without rewriting that historical truth.

## Scope

- Fresh branch/worktree from exact `origin/main`.
- Recovery matrix for later implementation refs and source commits.
- Material provider-neutral execution, backend/role runtime, Context Intelligence,
  Project Context/Project Map/MAP-BEFORE-WORK, Decision Trace, safe installer/
  rollback, Doctor fixes, planner derivation, FW00-FW06, Manus adapter, and
  capability/governance runtime machinery where verified in source.
- One non-conflicting release authority model with `.19` official baseline.
- Append-only historical reconciliation record.
- One derived successor revision from the existing numeric version policy.
- Candidate packaging, clean-source provenance, disposable install/Doctor/map pilots,
  relevant negative matrix, regression/security/portability checks, and branch push.

## Non-Goals

- Promotion, approval, merge, tag, public release, deployment, or official baseline change.
- Rewriting or deleting historical reports, approvals, candidate records, or artifacts.
- New product features, new Project Context semantics, new router/certification systems,
  new external credentials, live council claims, or authoritative project installation.
- Treating profiles, fixtures, reports, simulations, or synthetic Manus responses as live proof.

## Requirements

- `RECONCILIATION_BASE = origin/main` with recorded commit/tree and clean worktree.
- `CURRENT_OFFICIAL_BASELINE` and `CURRENT_OFFICIAL_SHA256` remain inherited from `origin/main`.
- A machine-readable development capability recovery matrix names source ref, source commit,
  surfaces, dependencies, evidence, canonical-main presence, adoption decision, and rationale.
- Governance, candidate distribution, artifact identity, source binding, inventory, checksum,
  and capability registry surfaces are explicit and non-competing.
- Candidate version is mechanically derived, not manually selected from ambiguous historical ids.
- Candidate artifact is built exactly once after clean source commit; two independent SHA checks agree.
- Manifest/inventory/checksum and archive safety gates are all zero-defect.
- Fresh disposable install is pinned and Doctor is `HEALTHY`, not merely `WARN`.
- Map-before-work proves allowed fresh-map execution and blocked stale/missing/denied cases.
- Manus support remains provider-neutral; native council claims remain the exact bounded status.
- Negative matrix is 26/26 fail-closed, regression has zero new unexplained failures,
  and authoritative project mutation counts are zero.

## Acceptance Criteria

- Terminal verdict is exactly one of the user-authorized labels.
- PASS/PASS_WITH_DISCLOSURES is allowed only if every required gate is independently evidenced.
- On any unmet mandatory gate, stop with the exact matching `BLOCKED / ...` verdict and preserve the evidence.
- If PASS, report exact authority, baseline, successor, artifact, source, inventory, checksum,
  Doctor, map gate, Manus ID/reason, negative matrix, regression, mutation, and promotion fields,
  then return only the requested independent Promotion Readiness Review decision.

## Checklist

- [x] P0-A: Complete actual status before implementation work.
  - Goal: establish repository truth before editing.
  - Work Steps: refresh graph; record clean worktree/base commit/tree; inspect `origin/main` governance/package/runtime; inspect all required later refs; classify material implementation versus stale authority; record Anvien relationship counts and impact warnings; update downstream slices.
  - Implementation Gate: no implementation started before the fresh worktree, graph refresh, authority inspection, and status matrix were recorded.
  - Acceptance: actual status identifies correct, partial, missing/unbound, fake-or-stub, and blocked surfaces with exact evidence IDs and a downstream decision.

### P1: Recover implementation and establish one authority model

- Phase Goal: integrate verified later implementation onto the clean canonical start and remove competing current authority without importing historical claims as official.
- Phase Boundary:
  - In scope: verified source lineage through `bbb5cbbc...`, runtime/capability surfaces, package/governance source metadata, reconciliation matrix/record, source tests and validation helpers.
  - Out of scope: candidate mint, external projects, promotion, merge, tag, deployment, or live Manus credentials.
  - Dependencies: P0-A evidence and clean worktree.
- Phase Implementation Rule: do not implement P1 directly. Implement P1-A, verify it, refresh actual-status, commit; then P1-B, verify it, refresh actual-status, commit.
- Ordered Slice List:
  - P1-A: Integrate verified later runtime/capability implementation.
  - P1-B: Rebuild clean governance/package authority and append reconciliation evidence.

- [x] P1-A: Integrate verified later runtime/capability implementation
  - Goal: recover material implementation from the verified later source lineage while preserving only source code/tests needed for the successor.
  - Scope Boundary:
    - Editable: runtime modules, runtime tests, installer/Doctor/pilot helpers, valid package machinery, and source docs required by those contracts.
    - Inspect-only: promotion approvals, historical candidate ZIPs/reports, fixtures, external project evidence, and later official pointers.
    - Preserve-only: `origin/main` baseline source snapshot, official `.19` evidence, canonical eight-role definitions, and existing protected project paths.
    - Out of scope: external project mutation, official promotion, deployment, and unrelated refactor.
  - Non-Goals: inventing missing live evidence, changing router topology, or upgrading placeholders to implemented status.
  - Pre-flight Questions:
    - Data source: exact commits/ref matrix from P0-A.
    - Display permission: N/A; no UI change.
    - DB read flow: N/A; runtime state uses disposable filesystem roots.
    - DB write flow: only disposable test/pilot roots; no authoritative project.
    - Render location: N/A; CLI/runtime payload and reports.
    - UI behavior flow: N/A; no browser surface.
    - Docker runtime: N/A; no container contract.
    - Playwright target: N/A; no web UI change.
    - Behavior test: targeted runtime tests for each recovered family plus negative cases.
    - Cleanup/quarantine: all pilots/logs under `.tmp/`; verify no authoritative path touched.
    - External side effects: Git branch only; no external service calls except authorized remote push later.
    - N/A notes: live Manus may be unavailable and must remain `NOT_RUN` honestly.
  - Work Steps:
    1. Integrate the coherent implementation lineage through `bbb5cbbc...` using an explicit no-commit merge/content review, then inventory every changed runtime/test surface against the recovery matrix.
       - UI flow check: N/A; verify CLI/runtime trigger -> process -> observable result.
       - DB/data flow check: verify isolated filesystem/state roots and no authoritative project writes.
       - Render location check: verify generated reports/artifacts are under scoped paths.
       - Evidence target: E1-P1A-SRC1, E1-P1A-IMPACT1, E1-P1A-TEST1.
    2. Remove/quarantine stale embedded release artifacts from the candidate distribution path without deleting historical Git truth, and run targeted syntax/import/runtime checks.
       - UI flow check: N/A.
       - DB/data flow check: verify disposable roots only.
       - Render location check: verify no `reports/`, `.tmp/`, or authoritative project surfaces enter the release stage.
       - Evidence target: E1-P1A-SCOPE1, E1-P1A-TEST2.
  - Implementation Gate:
    - Before editing target files, run Anvien file-detail and impact for each source/contract file touched; record exact counts and HIGH/CRITICAL warnings.
    - The selected source ref must be an ancestor of the reviewed later lineage and must not be a promotion-only tip.
  - Acceptance:
    - Source: material runtime modules and tests are present with provenance to listed commits.
    - Runtime/UI: targeted runtime tests pass; N/A for UI.
    - DB/data: disposable-only mutation evidence passes.
    - Behavior test: primary and negative runtime paths pass.
    - Cleanup/quarantine: no authoritative project mutation.
    - Evidence IDs: E1-P1A-SRC1..E1-P1A-TEST2.
    - Actual-status rows refreshed: runtime families transition only where fresh evidence proves them.
  - Evidence Targets: implementation diff, Anvien impact, targeted test outputs, protected-path scan.
  - Actual-status Update: refresh implementation rows and update P1-B assumptions before editing authority.
  - Commit Boundary: commit after acceptance passes.

- [x] P1-B: Rebuild clean governance/package authority and append reconciliation evidence
  - Goal: keep `.19` official while binding the new source candidate to one non-conflicting authority model.
  - Scope Boundary:
    - Editable: `governance/development-control.json`, validator/packager contracts, `manifest/package.json`, runtime version manifests, reconciliation matrix/record, and candidate-stage metadata generation.
    - Inspect-only: historical approval/promotion reports and fixture governance.
    - Preserve-only: official baseline version/SHA/report/approval and historical records.
    - Out of scope: final candidate mint and promotion decision.
  - Non-Goals: treating a candidate hash as official or modifying historical files.
  - Pre-flight Questions:
    - Data source: origin/main official control plus P1-A source tree.
    - Display permission: N/A.
    - DB read flow: N/A.
    - DB write flow: N/A; JSON authority and stage metadata only.
    - Render location: governance/manifest/reports in the reconciliation branch.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: control validator, source-binding, package manifest, and authority separation tests.
    - Cleanup/quarantine: no stale `.41/.46/.47/.48/.71` official pointers in active authority; fixtures remain explicitly non-authoritative.
    - External side effects: none until final branch push.
    - N/A notes: artifact hash is generated in stage after clean source binding; source remains clean at mint.
  - Work Steps:
    1. Derive the next unused numeric revision from all fetched refs and the existing version policy, set one successor source version, preserve `.19` official, and add explicit reconciliation records for `.19/.41/.46/.47/.48/.71`.
       - UI flow check: N/A.
       - DB/data flow check: validate JSON schema/control invariants.
       - Render location check: verify matrix/report paths are branch-local and append-only.
       - Evidence target: E1-P1B-AUTH1, E1-P1B-MATRIX1.
    2. Update package builder to generate candidate distribution manifest, artifact identity, source binding, inventory, and checksum records from a clean committed source into the staging area, without mutating the source worktree.
       - UI flow check: N/A.
       - DB/data flow check: verify staged metadata and source clean check.
       - Render location check: verify distribution include/exclude rules and archive safety.
       - Evidence target: E1-P1B-PKG1, E1-P1B-PKG2.
  - Implementation Gate:
    - Anvien impact/file-detail evidence exists for every changed contract file; official `.19` hashes are mechanically unchanged.
    - Validator accepts the new unpromoted source state but rejects official baseline drift and stale authority promotion.
  - Acceptance:
    - Source: authority files are internally consistent and candidate != official.
    - Runtime/UI: package metadata/runtime manifests agree; N/A for UI.
    - DB/data: N/A; JSON and staged metadata checks pass.
    - Behavior test: authority separation and clean-source package tests pass.
    - Cleanup/quarantine: stale authority is not active; historical records remain intact.
    - Evidence IDs: E1-P1B-AUTH1..E1-P1B-PKG2.
    - Actual-status rows refreshed: authority/package rows transition to correct or remain blocked honestly.
  - Evidence Targets: machine-readable recovery matrix, reconciliation record, control validation, package-builder tests.
  - Actual-status Update: record source commit/tree after the authority slice and update P2 gate assumptions.
  - Commit Boundary: commit after acceptance passes.

### P2: Validate successor gates and mint exactly one candidate

- Phase Goal: prove source/package/runtime safety on disposable roots and mint one immutable successor only after all mandatory gates pass.
- Phase Boundary:
  - In scope: full validation, disposable install/Doctor/map pilots, Manus sentinel classification, A-Z matrix, regression/security/portability, candidate mint, evidence, and branch delivery.
  - Out of scope: promotion, merge, tag, deployment, authoritative project installation, and direct promotion approval.
  - Dependencies: P1-A and P1-B commits, clean source provenance, and accepted authority model.
- Phase Implementation Rule: do not implement P2 directly. Implement P2-A, verify it, refresh actual-status, commit; then P2-B, verify it, refresh actual-status, commit.
- Ordered Slice List:
  - P2-A: Run source/runtime/install/map/manus/negative/regression gates.
  - P2-B: Mint one candidate, verify package integrity, record evidence, and push only the reconciliation branch.

- [x] P2-A: Run source/runtime/install/map/manus/negative/regression gates — blocked before candidate-dependent install/mint because the live Manus sentinel has no existing credential; no credential was requested or fabricated. Local source/runtime and regression suites passed, with the exact blocker recorded in `reports/reconciliation/p2p-canonical-lineage-repair-01-blocker.json`.
  - Goal: prove all mandatory gates against fresh disposable roots before mint.
  - Scope Boundary:
    - Editable: tests/evidence only if required by the already-defined contract; no new feature work.
    - Inspect-only: authoritative project paths and live external identities.
    - Preserve-only: source and authority commits from P1.
    - Out of scope: remediating unrelated historical failures or re-minting versions.
  - Non-Goals: simulating Manus or counting synthetic/profile evidence as live runtime proof.
  - Pre-flight Questions:
    - Data source: clean source commit and candidate-stage builder.
    - Display permission: N/A.
    - DB read flow: disposable project root only.
    - DB write flow: bounded isolated pilot only.
    - Render location: `.tmp/` pilots and reports.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: Doctor, pin, map gate, role, receipt, Manus separation, and negative matrix.
    - Cleanup/quarantine: delete/move only repo-local disposable pilots after fingerprints are recorded.
    - External side effects: live Manus sentinel only if already authenticated; read-only and bounded.
    - N/A notes: authoritative project mutation counts must remain zero.
  - Work Steps:
    1. Build/validate from a fresh extraction or disposable install; assert project pin and `PROJECT_LOCAL_DOCTOR = HEALTHY`.
       - UI flow check: N/A.
       - DB/data flow check: verify install writes only disposable root.
       - Render location check: record logs and evidence under `.tmp/`/reports.
       - Evidence target: E2-P2A-INSTALL1, E2-P2A-DOCTOR1.
    2. Run map-before-work fresh/stale/missing/permission cases, Manus sentinel classification, A-Z 26/26, regression, secret/absolute-path/provider-neutrality/authority widening checks.
       - UI flow check: N/A.
       - DB/data flow check: verify mutation counters and blocked states.
       - Render location check: preserve exact JSON evidence and hashes.
       - Evidence target: E2-P2A-MAP1, E2-P2A-MANUS1, E2-P2A-NEG1, E2-P2A-REG1.
  - Implementation Gate:
    - Source status is clean and all mandatory source/package authority tests pass before runtime pilots.
    - Any unavailable external Manus transport is classified honestly and causes the exact user-authorized blocker if required for PASS.
  - Acceptance:
    - Source: clean source commit/tree verified.
    - Runtime/UI: Doctor HEALTHY; N/A for UI.
    - DB/data: disposable-only mutation and fail-closed map/permission outcomes.
    - Behavior test: required matrix and regression thresholds met.
    - Cleanup/quarantine: no authoritative project writes.
    - Evidence IDs: E2-P2A-INSTALL1..E2-P2A-REG1.
    - Actual-status rows refreshed: every gate row is verified or explicitly blocked.
  - Evidence Targets: install/Doctor/pin, map, Manus, negative, regression, security, and mutation counters.
  - Actual-status Update: record whether P2-B may mint; if any mandatory gate fails, set exact blocker and stop.
  - Commit Boundary: commit only evidence/test updates required before mint; no artifact remint.

- [ ] P2-B: Mint one candidate, verify package integrity, record evidence, and push only the reconciliation branch — not entered because P2-A mandatory Manus evidence is unavailable.
  - Goal: mint exactly one new successor after clean source and package gates, then deliver the branch without promotion.
  - Scope Boundary:
    - Editable: final evidence reports and package-stage artifact output only.
    - Inspect-only: `origin/main`, authoritative projects, and historical reports.
    - Preserve-only: source commit/tree and exact candidate identity after mint.
    - Out of scope: any second mint, overwrite, promotion, merge, tag, or deployment.
  - Non-Goals: changing source after identity publication.
  - Pre-flight Questions:
    - Data source: clean committed source and P2-A gate evidence.
    - Display permission: N/A.
    - DB read flow: N/A.
    - DB write flow: stage/pilot filesystem only.
    - Render location: `.tmp/candidates/` plus append-only branch reports.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: two independent SHA mechanisms, manifest/inventory/checksum verifier.
    - Cleanup/quarantine: preserve exactly one candidate; do not overwrite its version/path.
    - External side effects: push new branch only.
    - N/A notes: no official promotion approval is created.
  - Work Steps:
    1. Mint one candidate to a non-source `.tmp` path, calculate artifact SHA independently twice, extract/verify it, and bind source commit/tree in artifact identity evidence.
       - UI flow check: N/A.
       - DB/data flow check: verify archive members only.
       - Render location check: verify canonical include/exclude rules.
       - Evidence target: E2-P2B-MINT1, E2-P2B-INVENTORY1.
    2. Write final reconciliation report, run change detection, verify branch head, push only the reconciliation branch, and verify local/remote equality.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: report exact paths/hashes.
       - Evidence target: E2-P2B-DELIVERY1, E2-P2B-DELIVERY2.
  - Implementation Gate:
    - `SOURCE_WORKTREE_DIRTY_AT_MINT = FALSE`, source commit/tree objects verified, all package gates pass, and no candidate of the selected revision exists.
  - Acceptance:
    - Source: source commit/tree are full 40-character verified values.
    - Runtime/UI: package verification and fresh extraction pass; N/A for UI.
    - DB/data: inventory/checksum/unsafe path counts are zero.
    - Behavior test: exactly one candidate identity with matching independent hashes.
    - Cleanup/quarantine: no duplicate mint or overwrite.
    - Evidence IDs: E2-P2B-MINT1..E2-P2B-DELIVERY2.
    - Actual-status rows refreshed: candidate and delivery rows closed; promotion remains `NO`.
  - Evidence Targets: candidate identity, manifest/inventory/checksum, branch delivery, terminal report.
  - Actual-status Update: record final candidate identity and terminal verdict.
  - Commit Boundary: commit final reports and evidence before push; do not alter source after mint.

- [ ] Pn-A: Call supervisor for the implemented-plan acceptance loop.
  - Goal: independently review the completed plan work against authority, source, artifact, runtime, evidence, and blockers.
  - Work Steps:
    1. Review the final diff, source, candidate, reports, and validation outputs with Supervisor.
    2. If rejected, record the exact blocker and perform only the authorized corrective slice; never promote.
    3. Re-run the review after any correction.
  - Implementation Gate: all planned phases are complete or explicitly blocked.
  - Acceptance: supervisor PASS or durable blocker; no unsupported completion claim.
- [ ] Pn-B: Remove dead work created during this plan.
  - Goal: keep the branch free of abandoned candidate duplicates, stale temporary files, and rejected generated artifacts.
  - Work Steps:
    1. Review plan-created files, stage outputs, logs, and candidate paths.
    2. Remove only plan-created disposable dead work; preserve historical Git evidence.
    3. Re-run supervisor review for cleanup.
  - Implementation Gate: only plan-created disposable targets are in scope.
  - Acceptance: final status/diff contains no dead plan-created artifact and evidence describes preserved history.
- [ ] Pn-C: Close the plan.
  - Goal: finalize evidence, benchmark, change detection, branch state, and exact terminal verdict.
  - Work Steps:
    1. Run final package/source/runtime verification and record all exact counts.
    2. Run Anvien detect-changes before the final commit.
    3. Commit final reports, verify branch state, and push only the reconciliation branch.
  - Implementation Gate: Pn-A and Pn-B pass or record an explicit blocker.
  - Acceptance: final evidence is current, source/artifact identity is fixed, and no promotion occurred.

## Risk Notes

- Existing later branches contain real runtime improvements mixed with stale governance and candidate artifacts; full-tip merge is unsafe without authority reset.
- The package builder currently mutates source metadata during build; this is a direct clean-source provenance risk and must be closed before mint.
- Existing validator vocabulary is narrower than this corrective task; any extension must remain fail-closed and preserve the official `.19` constants.
- Live Manus availability is external state; no credentials may be requested or fabricated in this task.
- The current owner checkout is dirty; all edits must remain isolated in the new worktree.
