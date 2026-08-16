# P2P-C14 Design Intelligence Release Readiness & Portable Project Integration Plan

## Metadata

- Date: `2026-08-15`
- Status: `READY_FOR_OWNER_RELEASE_APPROVAL` (technical gates PASS; owner approval still pending)
- Plan: `docs/plans/2026-08-15-p2p-c14-design-intelligence-release-readiness/2026-08-15-p2p-c14-design-intelligence-release-readiness-plan.md`
- Evidence: `docs/plans/2026-08-15-p2p-c14-design-intelligence-release-readiness/2026-08-15-p2p-c14-design-intelligence-release-readiness-evidence.md`
- Benchmark: `docs/plans/2026-08-15-p2p-c14-design-intelligence-release-readiness/2026-08-15-p2p-c14-design-intelligence-release-readiness-benchmark.md`
- Actual status: `docs/plans/2026-08-15-p2p-c14-design-intelligence-release-readiness/2026-08-15-p2p-c14-design-intelligence-release-readiness-actual-status.md`

## Goal

Turn the integrated C10-C13 development source into one technically verified,
portable, immutable Design Intelligence release candidate, without promoting
it or mutating protected user projects. Stop at `PASS`, `BLOCKED`, or `REJECT`.

## Rules

- Complete P0 actual status before implementation work.
- Treat the C13 development-source PASS as scoped evidence, not release proof.
- Preserve C09 `BLOCKED / EVENT_EVIDENCE_UNAVAILABLE` and C08 `DEFERRED`.
- Preserve the exact canonical eight identities, denominator `8`, and full quorum `8/8`.
- Keep `p2p-uiux` as the only UI/UX router; NUI faculties remain metadata, never agents.
- Keep `p2p_aesthetica` optional and noncanonical; live execution is not required.
- Keep C10 as evidence/Decision Trace authority, C11 as durable task-state authority,
  and C12 as foreground execution authority. Do not create parallel stores or runners.
- Keep the NUI snapshot thin, offline, provenance-bound, MIT-attributed, and body-lazy.
- Use only repo-local disposable roots under `.tmp/`; do not use or mutate Logistics,
  App Game Truyen, the official `.15` artifact, prior candidates, the immutable baseline,
  or the release ZIP/v5 targets.
- Do not enable network, hooks, proxying, connectors, delegation, workers, scheduler,
  daemon, queue, lease, or background UI critique.
- Run Anvien `file-detail` and impact before editing production symbols/files and
  `detect-changes` before any implementation commit. The workspace has no Git metadata;
  record that limitation instead of fabricating a commit.
- Record evidence and benchmarkable inventory counts as each gate completes.

## Problem

C13 proves the Design Intelligence foundation in the development source, but it did
not prove a clean portable install, independence from the P2P development checkout,
upgrade/reinstall lifecycle, a full-root secret scan, release-candidate version
consistency, or closure of the workflow-helper timeout. The release candidate must
close or honestly classify those gates without widening the Design Intelligence scope.

## Scope

- Recover and verify one source tree containing C10-C13.
- Verify C13 registry/provenance, license attribution, faculty count/body loading,
  sole-router discovery, optional-specialist policy, render/evidence truthfulness,
  and C10/C11/C12 projection boundaries.
- Classify the workflow-helper timeout and perform at most one minimum bounded retry
  when safe.
- Run the strongest supported full-root secret scan and distinguish real findings from
  placeholders, fixtures, and documentation examples using canonical scanner semantics.
- Prepare a new isolated candidate source copy, align the next valid release version
  through the existing package/version contract, build a new immutable ZIP, and verify
  its manifest, checksums, doctor, drift, provenance, and inventory.
- Run clean fresh-install, `.15` upgrade, same-version reinstall, no-development-source
  dependency, non-UI dormancy, beginner UI request, installed Logistics-like fixture,
  installed consumer contrast, and truthful render-state checks.
- Run focused C13, C12, C11, C10, p2p-uiux, AESTHETICA, full-suite, governance,
  doctor, package, lifecycle, and security validations that are applicable.

## Non-Goals

- No Logistics redesign or mutation.
- No App Game Truyen mutation.
- No browser/Docker UI render certification; C14 only verifies the render capability
  contract and deterministic installed-package behavior.
- No live NUI fetch, NUI MCP/server/plugin, full faculty-body vendor, or auto-update.
- No C08 rerun, C09 reopening, host identity fabrication, eight-thread QUORUM claim,
  worker delegation, parallel execution, background runtime, or new router/store.
- No external publication, merge, release promotion, or owner approval inference.

## Requirements

1. `C10-C13` are verified in the same authoritative development source.
2. NUI provenance includes upstream repository, commit, MIT license, registry source,
   graph/version fingerprint, and P2P adaptation status without network runtime needs.
3. The local registry validates exactly `174` faculties, retains graph breadth, and
   loads `0` faculty bodies by default.
4. Installed discovery exposes `p2p-uiux` and Design Intelligence without beginner
   configuration, NUI installation, faculty selection, or AESTHETICA selection.
5. Optional AESTHETICA remains `optional_specialist=true` and
   `canonical_quorum_member=false` and never changes `8/8` governance.
6. The helper timeout is classified as one of the allowed root-cause classes and its
   release impact follows existing canonical release policy.
7. The candidate contains all required runtime surfaces and excludes `.tmp`, reports,
   caches, test output, credentials, and raw upstream material not required at runtime.
8. Candidate `VERSION`, manifest/package metadata, runtime manifest, doctor output,
   artifact name, and release records are mutually consistent.
9. Fresh install, `.15` upgrade, same-version reinstall, and installed-runtime
   isolation pass without duplicate capability/router/state/evidence systems.
10. Non-UI requests remain dormant; beginner UI requests route through the existing
    router and select relevant design metadata without user faculty/agent selection.
11. Missing render evidence never reports UI completion; compile, generator output,
    automated accessibility checks, and critique remain distinct evidence classes.

## Acceptance Criteria

- All mandatory DIR1-DIR40 conditions in the supplied C14 request are either PASS or
  are recorded as a real release-blocking condition with exact evidence.
- The candidate is new, immutable, hash-recorded, unpromoted, and internally versioned.
- The installed runtime works when the development checkout is treated as unavailable.
- The independent Supervisor report is PASS for the full C14 claim, or the final state
  is `BLOCKED` with no owner approval request.
- If all release gates pass, stop at `READY_FOR_OWNER_RELEASE_APPROVAL`; do not promote.

## Checklist

- [x] P0-A: Complete actual status before implementation work.
  - Goal: classify every release-relevant surface from current source and evidence.
  - Work Steps: inspect C13 ledgers/reports, refresh Anvien evidence, inspect metadata,
    identify preserve-only/inspect-only/editable surfaces, and record helper/security/
    version/lifecycle blockers.
  - Implementation Gate: actual-status has evidence IDs, relationship counts, touch
    modes, and a downstream decision for every target surface.
  - Acceptance: P0 is complete and the next phase reflects current reality.

### P1: Integrated source and release-gate closure

- Phase Goal: verify the source invariant family and close only evidence-backed gaps.
- Phase Boundary:
  - In scope: C10-C13 runtime, provenance, registry, doctor, helper, secret scan,
    version-contract inspection, and focused regression surfaces.
  - Out of scope: candidate promotion, user projects, C08/C09, UI redesign, delegation.
  - Dependencies: P0 actual status, fresh Anvien graph, C13 PASS evidence.
- Phase Implementation Rule: implement slices in order; preserve correct C13 code and
  refresh actual-status before moving to the next slice.
- Ordered Slice List:
  - P1-A: Reconcile integrated source, provenance, policy, and helper/security evidence.
  - P1-B: Apply only verified release-critical source/metadata correction, if required.

- [x] P1-A: Reconcile integrated source, provenance, policy, and helper/security evidence.
  - Goal: prove the C10-C13 invariant family and classify known non-C13 blockers.
  - Scope Boundary:
    - Editable: plan/evidence/status ledgers only unless a release-critical defect is proven.
    - Inspect-only: `.p2p/system/p2p_uiux`, C10/C11/C12 modules, manifests, installers,
      package builder, governance, C13 fixtures/reports.
    - Preserve-only: correct C13 code, C09/C08 state, canonical profiles, prior artifacts.
    - Out of scope: all external app paths and release promotion.
  - Non-Goals: no speculative refactor or helper redesign.
  - Pre-flight Questions:
    - Data source: C13 local registry and existing governance/runtime metadata.
    - Display permission: no user-facing UI surface; internal evidence only.
    - DB read flow: N/A; package has no product DB.
    - DB write flow: N/A; only repo-local ledgers may be updated.
    - Render location: deterministic render-state contract only.
    - UI behavior flow: installed CLI/router fixture, not browser UI.
    - Docker runtime: N/A; no public container contract exists.
    - Playwright target: N/A; user explicitly excludes live browser proof.
    - Behavior test: focused C13 and lifecycle tests.
    - Cleanup/quarantine: all temporary output under `.tmp/p2p-c14-*`.
    - External side effects: none; no network or publication.
    - N/A notes: helper timeout is evidence, not a reason to alter Design Intelligence.
  - Work Steps:
    1. Inspect C10-C13 source, provenance, registry, capabilities, installers, package
       builder, and current reports; record source/impact evidence.
       - UI flow check: N/A; CLI/package boundary only.
       - DB/data flow check: verify no second store and no network dependency.
       - Render location check: verify all four render states remain explicit.
       - Evidence target: `E1-P1A-SRC1..E1-P1A-SRC8`.
    2. Run the canonical helper linter/goal path once more only if the preflight shows
       it is safe and bounded; run the full-root secret scan without weakening rules.
       - UI flow check: N/A.
       - DB/data flow check: verify scanner skips only its canonical safe exclusions.
       - Render location check: N/A.
       - Evidence target: `E1-P1A-HELPER1..E1-P1A-SEC1`.
  - Implementation Gate:
    - No production edit is allowed unless a concrete failed invariant is identified.
    - Record Anvien file-detail/impact IDs before any symbol/file edit.
  - Acceptance:
    - Source: integrated source and C13 provenance are current and correct.
    - Runtime/UI: installed discovery and render boundary remain truthful.
    - DB/data: no parallel state/evidence/truth store is found.
    - Behavior test: helper/security outcomes are reproducible and classified.
    - Cleanup/quarantine: no temporary output is treated as runtime input.
    - Evidence IDs: `E1-P1A-*`.
    - Actual-status rows refreshed: integrated source, helper, secret scan, provenance.
  - Evidence Targets: source paths, Anvien summaries, helper run, scanner output.
  - Actual-status Update: mark correct surfaces preserve-only; classify unresolved gates.
  - Commit Boundary: no code commit unless P1-B changes production source.

- [x] P1-B: Apply only verified release-critical source/metadata correction, if required.
  - Goal: close a concrete package/lifecycle defect found in P1-A without changing C13 design.
  - Scope Boundary:
    - Editable: the smallest proven source/packaging metadata or helper contract files.
    - Inspect-only: all unaffected C10/C11/C12/design surfaces.
    - Preserve-only: NUI snapshot, router architecture, canonical identities, external paths.
    - Out of scope: new features, redesign, parallelism, background behavior.
  - Non-Goals: no change merely to make a gate green.
  - Pre-flight Questions:
    - Data source: failed gate output and authority docs.
    - Display permission: N/A.
    - DB read/write: N/A.
    - Render location: N/A unless a render contract regression is found.
    - UI behavior flow: installed CLI only.
    - Docker/Playwright: N/A.
    - Behavior test: direct regression for the failed contract before/after correction.
    - Cleanup/quarantine: candidate changes remain in isolated source copy until proven.
    - External side effects: none.
    - N/A notes: if no defect is proven, mark this slice preserve-only and continue.
  - Work Steps:
    1. Run Anvien impact/file-detail for each exact target and implement the smallest
       correction with a direct behavioral regression.
       - UI flow check: N/A; CLI/package behavior only.
       - DB/data flow check: verify existing stores remain the only authorities.
       - Render location check: verify no completion claim is widened.
       - Evidence target: `E1-P1B-FIX1..E1-P1B-TEST2`.
    2. Run focused verification, refresh actual-status, and run detect-changes before
       the checkpoint commit when the workspace can provide one.
       - UI flow check: N/A.
       - DB/data flow check: verify no state duplication.
       - Render location check: N/A.
       - Evidence target: `E1-P1B-CHECK1..E1-P1B-CHANGE1`.
  - Implementation Gate:
    - A failed release invariant and its exact authority must be recorded first.
  - Acceptance:
    - Source and direct regression close the failed invariant without unrelated edits.
    - Evidence and actual-status are refreshed; a missing Git hash is recorded honestly.
    - Evidence IDs: `E1-P1B-*`.
  - Evidence Targets: focused diff, direct test, change detection, coder report if edited.
  - Actual-status Update: transition only the corrected row(s); preserve all others.
  - Commit Boundary: checkpoint commit when Git metadata is available; otherwise no fake hash.

### P2: Immutable candidate construction and package contract

- Phase Goal: build a new candidate from an isolated source copy and verify the package boundary.
- Phase Boundary:
  - In scope: candidate version, package inventory, provenance/license inclusion, checksums,
    release manifest, package doctor, drift, rollback artifact.
  - Out of scope: promotion and user-project installation.
  - Dependencies: P1 source/gate status PASS or non-release-blocking classification.
- Ordered Slice List:
  - P2-A: Prepare isolated candidate source and consistent next version markers.
  - P2-B: Build, verify, scan, and inventory the immutable candidate.

- [x] P2-A: Prepare isolated candidate source and consistent next version markers.
  - Goal: select the next valid version from the existing canonical release mechanism,
    never overwrite root `.15` or prior candidates, and align all candidate markers.
  - Scope Boundary:
    - Editable: isolated `.tmp/p2p-c14-candidate-source` copy and its version metadata.
    - Inspect-only: root source and prior artifacts.
    - Preserve-only: official `.15`, `.16-r2`, `.17`, `.18`, `.20`, C11/C12/C13 artifacts.
    - Out of scope: root version mutation before owner approval.
  - Non-Goals: no invented version scheme.
  - Pre-flight Questions:
    - Data source: `scripts/package_release.py`, current VERSION/manifest contract, prior artifact inventory.
    - Display permission: N/A.
    - DB read/write: N/A.
    - Render location: N/A.
    - UI behavior flow: N/A.
    - Docker/Playwright: N/A.
    - Behavior test: package version consistency assertions.
    - Cleanup/quarantine: source copy remains under `.tmp`; no root overwrite.
    - External side effects: none.
    - N/A notes: candidate version must be reported separately from embedded version.
  - Work Steps:
    1. Determine the collision-free next revision through the package builder/artifact
       naming contract and record the decision as FACT/INFERENCE with evidence.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: N/A.
       - Evidence target: `E2-P2A-VERSION1..E2-P2A-VERSION3`.
    2. Copy only the development-source inputs needed by the canonical builder into the
       repo-local candidate root and align VERSION, manifest, runtime manifest, and notes.
       - UI flow check: N/A.
       - DB/data flow check: verify no development state is copied into runtime payload.
       - Render location check: N/A.
       - Evidence target: `E2-P2A-COPY1..E2-P2A-COPY3`.
  - Implementation Gate:
    - Exact candidate path is new, validated inside the repo, and all protected artifacts
      have pre-change hashes recorded.
  - Acceptance:
    - All candidate version-bearing files agree and root/protected artifacts are unchanged.
    - Evidence IDs: `E2-P2A-*`.
  - Evidence Targets: version table, hash table, candidate-source inventory.
  - Actual-status Update: candidate metadata transitions to bound-correct.
  - Commit Boundary: candidate artifacts are not source commits.

- [x] P2-B: Build, verify, scan, and inventory the immutable candidate.
  - Goal: produce one new ZIP with a manifest/checksum hash and no unsafe/transient payload.
  - Scope Boundary:
    - Editable: new `.tmp/p2p-c14-candidate*.zip`, extracted verify root, release evidence.
    - Inspect-only: package source and protected historical artifacts.
    - Preserve-only: root `.15` and all prior artifacts.
    - Out of scope: promotion, publication, external communication.
  - Non-Goals: no full NUI vendor.
  - Pre-flight Questions:
    - Data source: canonical package builder and doctor.
    - Display permission: N/A.
    - DB read/write: N/A.
    - Render location: packaged state contract only.
    - UI behavior flow: installed CLI tests later in P3.
    - Docker/Playwright: N/A.
    - Behavior test: package verify/doctor/drift/secret scan.
    - Cleanup/quarantine: extracted verify root is disposable and repo-local.
    - External side effects: none.
    - N/A notes: record file counts and hashes, not claims of real UI quality.
  - Work Steps:
    1. Run package build from the isolated source, extract it, run package verify,
       development/portable doctor as applicable, and governance drift.
       - UI flow check: N/A.
       - DB/data flow check: verify only one runtime state/evidence path is packaged.
       - Render location check: verify four render states are present in runtime code.
       - Evidence target: `E2-P2B-PACK1..E2-P2B-PACK4`.
    2. Inspect release inventory for required C10-C13 files, provenance/license, and
       excluded `.tmp`/reports/cache/credential/upstream-body material; run secret scan.
       - UI flow check: N/A.
       - DB/data flow check: verify registry is local and no network fetch path is required.
       - Render location check: N/A.
       - Evidence target: `E2-P2B-INVENTORY1..E2-P2B-SEC1`.
  - Implementation Gate:
    - Package build and source metadata checks must pass before lifecycle testing.
  - Acceptance:
    - New candidate, manifest, checksum, package doctor, drift, and security evidence pass.
    - Evidence IDs: `E2-P2B-*`.
  - Evidence Targets: artifact path/hash/version/inventory/doctor/drift/secret outputs.
  - Actual-status Update: package inventory and candidate rows refreshed.
  - Commit Boundary: no source commit for generated candidate ZIP.

### P3: Portable install and lifecycle isolation

- Phase Goal: prove the candidate installs and upgrades in disposable projects without P2P_dev dependency.
- Phase Boundary:
  - In scope: fresh install, `.15` upgrade, same-version reinstall, protected-state preservation,
    capability/registry discovery, no dev-source imports, no duplicate router/state/hooks.
  - Out of scope: real Logistics/App Game Truyen, browser rendering, promotion.
  - Dependencies: P2-B candidate PASS.
- Ordered Slice List:
  - P3-A: Fresh install and development-source independence.
  - P3-B: Upgrade and same-version reinstall idempotence.

- [x] P3-A: Fresh install and development-source independence.
  - Goal: install the candidate into a clean fixture and prove local runtime discovery.
  - Scope Boundary:
    - Editable: disposable `.tmp/p2p-c14-fresh-project` only.
    - Inspect-only: candidate ZIP/extracted package.
    - Preserve-only: source checkout and external projects.
    - Out of scope: any user project.
  - Non-Goals: no UI redesign or browser proof.
  - Pre-flight Questions:
    - Data source: installed `.p2p/system` and candidate package.
    - Display permission: N/A.
    - DB read/write: inspect file/state preservation only.
    - Render location: CLI capability state.
    - UI behavior flow: `p2p_uiux` CLI/router.
    - Docker/Playwright: N/A.
    - Behavior test: fresh installer, doctor, UIUX discovery, registry import.
    - Cleanup/quarantine: disposable project under `.tmp` only.
    - External side effects: none.
    - N/A notes: temporarily rename/isolate dev checkout only when safely possible.
  - Work Steps:
    1. Install using the supported installer, run installed doctor and UI/UX capability
       discovery, inspect registry/provenance, and capture import origins.
       - UI flow check: CLI trigger -> router -> Design Intelligence profile.
       - DB/data flow check: no second task/evidence store.
       - Render location check: unavailable/unknown states remain truthful.
       - Evidence target: `E3-P3A-INSTALL1..E3-P3A-DISCOVERY3`.
    2. Run the same invocation with development-source paths unavailable or blocked and
       fail if imports/data resolve outside the fixture.
       - UI flow check: installed CLI remains discoverable.
       - DB/data flow check: local registry only.
       - Render location check: no UI DONE claim without render evidence.
       - Evidence target: `E3-P3A-ISOLATION1..E3-P3A-RENDER1`.
  - Implementation Gate: candidate package and installer are already verified.
  - Acceptance: fresh install/doctor/discovery/isolation all pass.
  - Evidence Targets: installer output, installed paths, import origins, hashes.
  - Actual-status Update: fresh install and independence rows refreshed.
  - Commit Boundary: lifecycle fixtures are not committed unless plan evidence requires it.

- [x] P3-B: Upgrade and same-version reinstall idempotence.
  - Goal: prove `.15` state preservation, candidate upgrade, and same-version safety.
  - Scope Boundary:
    - Editable: disposable `.tmp/p2p-c14-upgrade-project` and reinstall fixture.
    - Inspect-only: official `.15` package and candidate.
    - Preserve-only: official artifact and all external paths.
    - Out of scope: production upgrade.
  - Non-Goals: no destructive cleanup outside disposable roots.
  - Pre-flight Questions: same as P3-A, with existing state snapshots and backup inventory.
  - Work Steps:
    1. Install official `.15`, seed only contract-allowed fixture state, upgrade with the
       new candidate, and verify state, identities, router count, evidence/task store,
       Design Intelligence discovery, and doctor.
       - UI flow check: installed CLI discovery before/after upgrade.
       - DB/data flow check: state preservation and no duplicate stores.
       - Render location check: contract remains truthful.
       - Evidence target: `E3-P3B-UPGRADE1..E3-P3B-UPGRADE3`.
    2. Reinstall the same candidate version and verify idempotence, backups, hooks,
       registry, capability count, and task/evidence state.
       - UI flow check: discovery remains stable.
       - DB/data flow check: no duplicate state/hook/capability.
       - Render location check: N/A.
       - Evidence target: `E3-P3B-REINSTALL1..E3-P3B-REINSTALL3`.
  - Implementation Gate: fresh install passed and protected snapshots exist.
  - Acceptance: upgrade and reinstall lifecycle pass without mutation outside fixtures.
  - Evidence Targets: lifecycle JSON/MD, doctor, state hash comparison.
  - Actual-status Update: lifecycle rows refreshed.
  - Commit Boundary: no source commit for disposable fixtures.

### P4: Installed behavior, regressions, governance, and supervisor

- Phase Goal: verify installed routing/quiet behavior and complete all applicable release gates.
- Phase Boundary:
  - In scope: non-UI dormancy, beginner UI request, installed Logistics-like/consumer fixtures,
    render claim boundary, focused/full regression, governance/security/package/lifecycle checks.
  - Out of scope: real UI render, external projects, owner approval execution.
  - Dependencies: P3 lifecycle PASS.
- Ordered Slice List:
  - P4-A: Installed deterministic behavior and claim-boundary checks.
  - P4-B: Full regression, governance, package/lifecycle closure, and supervisor review.

- [x] P4-A: Installed deterministic behavior and claim-boundary checks.
  - Goal: prove task-aware routing and honest evidence semantics from installed package.
  - Scope Boundary: synthetic fixtures only; no product mutation.
  - Work Steps:
    1. Run a non-UI request and verify Design Intelligence stays dormant with zero body load.
       Run the beginner UI sentence and verify p2p-uiux/profile/faculty selection without
       asking the user to choose a faculty or agent.
       - UI flow check: request -> sole router -> profile/route result.
       - DB/data flow check: no task store write outside C11 projection.
       - Render location check: no render evidence is invented.
       - Evidence target: `E4-P4A-ROUTE1..E4-P4A-DORMANT2`.
    2. Run installed synthetic Logistics-like and consumer/story-game fixtures, compare
       selected faculty graph breadth and task-aware divergence, and check render/DONE claims.
       - UI flow check: two contrasting fixture routes.
       - DB/data flow check: no NUI truth store.
       - Render location check: all four states and compile/critique/accessibility boundaries.
       - Evidence target: `E4-P4A-FIXTURE1..E4-P4A-BOUNDARY3`.
  - Implementation Gate: installed runtime is isolated and lifecycle-safe.
  - Acceptance: all deterministic installed behavior cases pass with truthful limits.
  - Evidence Targets: installed CLI JSON, route/profile counts, render status outputs.
  - Actual-status Update: behavior/claim-boundary rows refreshed.
  - Commit Boundary: no source commit for fixtures.

- [x] P4-B: Full regression, governance, package/lifecycle closure, and supervisor review.
  - Goal: close the C14 evidence family and obtain an independent verdict.
  - Scope Boundary: current source, candidate, fixtures, reports, and ledgers only.
  - Work Steps:
    1. Run C13 focused tests/evals, C12 foreground, C11 task state, C10 evidence/permission,
       p2p-uiux/AESTHETICA, full P2P suite, Decision Trace, governance drift, doctors,
       package verify, lifecycle, and canonical security scans.
       - UI flow check: installed CLI only.
       - DB/data flow check: existing stores/ledgers only.
       - Render location check: no browser claim.
       - Evidence target: `E4-P4B-TEST1..E4-P4B-GOV1`.
    2. Run Supervisor review over source, candidate, lifecycle, isolation, fixtures,
       version, license, C08/C09, canonical safety, and release-gate correctness.
       - UI flow check: N/A.
       - DB/data flow check: invariant closure review.
       - Render location check: review truthful boundary.
       - Evidence target: `E4-P4B-SUP1`.
  - Implementation Gate: all required checks are current or explicitly blocked.
  - Acceptance: Supervisor PASS or exact release blocker; no owner approval if blocked.
  - Evidence Targets: final C14 report, supervisor report, actual-status/benchmark closure.
  - Actual-status Update: all DIR rows receive PASS/BLOCKED/REJECT status.
  - Commit Boundary: no promotion; no commit hash fabricated.

- [x] P5-A: Call supervisor for the implemented-plan acceptance loop.
  - Goal: independently verify the full completed C14 claim.
  - Work Steps: call Supervisor, fix only a rejected invariant in a separate coder slice,
    rerun affected gates, and review again.
  - Implementation Gate: P1-P4 complete or explicitly blocked.
  - Acceptance: Supervisor PASS or durable blocker recorded.
- [x] P5-B: Remove dead work created during this plan.
  - Goal: keep only useful plan/evidence/candidate artifacts.
  - Work Steps: inspect diff/status and plan-created files; remove only plan-created dead
    artifacts; review cleanup independently.
  - Implementation Gate: no protected artifact is a cleanup target.
  - Acceptance: no stale candidate/temporary artifact is represented as runtime or release.
- [x] P5-C: Close the plan.
  - Goal: record final evidence, benchmark, technical report, and stop at the correct gate.
  - Work Steps: refresh actual-status, record hashes, run detect-changes if applicable,
    write final beginner-facing summary, and if PASS prepare—but do not execute—the
    hash-bound owner approval request.
  - Implementation Gate: P5-A/P5-B pass or record blockers.
  - Acceptance: final state is exactly `PASS`, `BLOCKED`, or `REJECT`.

## Risk Notes

- The workflow helper already timed out during C13 after 184 seconds; one bounded retry
  is allowed only after cause classification. A repeated timeout remains `WORKFLOW_HELPER_BLOCKED`.
- Full-root scanning may be slow because the development source contains large historical
  and state-heavy material. A timeout is not a PASS; the release impact must follow the
  existing canonical policy.
- The workspace is not a Git repository. Commit/change-detection evidence may be blocked,
  but no identity or hash may be fabricated.
- Root version markers remain `.15` until the candidate source copy is made. Candidate
  version choice must be supported by the existing package contract and artifact inventory,
  not by an arbitrary filename.
- No candidate is promoted automatically. If all technical gates pass, the only remaining
  action is explicit owner approval bound to the exact candidate and technical report hashes.

## Final Closure (2026-08-15)

- Technical result: `PASS`; final stop state: `READY_FOR_OWNER_RELEASE_APPROVAL`.
- Candidate: `.tmp/p2p-c14-final/P2P-8.4.7-C-Codex-Edition-v19.zip`, embedded version
  `8.4.7-C-codex.19`, `406` content files, `407` checksums, SHA-256
  `3a9ee51321e1f5e40e35ce73eb90727cddb571a672aa095d16d76af2feb03dd8`.
- Exact official `.15` rollback: `D:\AI\P2P_dev\P2P-8.4.7-C-Codex-Edition-v15.zip`,
  SHA-256 `af4d63a882dabfde20ac237574590ec584ee2944bc4cdc30b6a07bf7f681e195`.
- Technical gate: `reports`/approval artifacts under
  `.tmp/p2p-c14-final/gate-official15/`; status `PASS`, approval request `PENDING`.
- Owner approval is not inferred and no promote/finalize/merge/publish action was run.
- C09 remains `BLOCKED`; C08 remains `DEFERRED`; external projects and protected artifacts
  remain untouched. Browser/Docker/real Logistics rendering and live eight-thread QUORUM
  remain outside the claim.
