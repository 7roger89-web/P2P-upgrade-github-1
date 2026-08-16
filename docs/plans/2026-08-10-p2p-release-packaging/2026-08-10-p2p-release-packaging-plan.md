# P2P reusable release packaging Plan

## Metadata

- Date: `2026-08-10`
- Status: `COMPLETE — supervisor PASS`
- Plan: `docs/plans/2026-08-10-p2p-release-packaging/2026-08-10-p2p-release-packaging-plan.md`
- Evidence: `docs/plans/2026-08-10-p2p-release-packaging/2026-08-10-p2p-release-packaging-evidence.md`
- Benchmark: `docs/plans/2026-08-10-p2p-release-packaging/2026-08-10-p2p-release-packaging-benchmark.md`
- Actual status: `docs/plans/2026-08-10-p2p-release-packaging/2026-08-10-p2p-release-packaging-actual-status.md`

## Goal

Finalize the verified P2P development tree as one clean reusable release package,
determine the next release identity from the existing `codex.4` convention, make
installation/upgrade/reinstall state-safe, and prove fresh-project and existing-project
acceptance without reworking the already-PASS Goal subsystem.

## Rules

- Treat the Goal subsystem and existing governance/workflow gates as preserve-only.
- Package only reusable P2P runtime, source-of-truth manifests, required schemas, guides,
  installers, doctor tooling, and release metadata; exclude development state and reports.
- Never overwrite project state with package templates.
- Same-version reinstall and upgrade must be deterministic, backed up, and doctor/drift safe.
- Use the existing package/doctor/manifest/lock tooling; do not introduce a second governance,
  Goal, Eval, Approval, Drift, Quorum, or Ledger system.
- Do not claim real eight-thread runtime or real project-quality eval from safe fixtures.
- No network, hooks, connectors, deployment, external publication, or destructive project reset.
- A release artifact is a protected release action; technical gates must PASS before handoff.

## Problem

The current development tree has the verified reusable workflow but its package scripts archive
the entire development directory, including `.tmp`, reports, plans, and transient outputs. The
installers back up system files but do not clearly identify same-version versus upgrade behavior,
do not expose a package release identity in installed state, and have no explicit safe-state
acceptance fixture for old supported system files plus preserved project state.

## Scope

Editable surfaces:

- `VERSION`, `manifest/package.json`, release notes, and beginner entry guide.
- `scripts/package.ps1`, `scripts/package.sh` for curated distributable contents.
- `install.ps1`, `install.sh` and narrowly scoped installer metadata/state logic.
- focused packaging/installer acceptance tests and safe fixtures under `tests/`.
- this four-file plan/evidence/benchmark/actual-status set and coder/supervisor reports.

Preserve-only surfaces:

- `scripts/p2p_workflow.py` and the completed Goal tests/behavior.
- FACT_LEDGER, Live Specs, Eval, RAG boundary, Approval, Drift, Execution Ledger, quorum,
  doctor internals, and immutable `source/8.4.6-C/` baseline.

## Non-Goals

- No Goal hardening or architecture redesign.
- No changes to FACT_LEDGER/Live Specs/Eval/RAG/Approval/Drift/Execution Ledger architecture.
- No application-project code changes.
- No real external publication or user approval action.
- No cleanup of unrelated historical reports outside the release contents selection.

## Requirements

- Release identity is the next existing convention value: `8.4.6-C-codex.5`, distinguished from `codex.4`.
- Clean package excludes `.tmp`, caches, reports, plan ledgers, experimental scratch, credentials,
  project-specific state, and install backups while retaining all doctor-required runtime sources.
- Package manifest, source inventory, runtime lock, and checksums remain internally consistent.
- Installer distinguishes fresh project, same-version reinstall, supported upgrade, and already
  initialized project without overwriting project FACT/Live Specs/evals/policy/approvals/ledger/
  CAPSULE/status/Goal state.
- Fresh fixture proves beginner natural-language initialization and terminal workflow.
- Existing fixture proves state preservation, system-file upgrade, evidence reuse, doctor, and drift.
- Same-version reinstall proves deterministic non-destructive behavior and no duplicates.
- Concise release notes and one plain-language beginner guide are present in the release.

## Acceptance Criteria

- [x] Release identity is consistently `8.4.6-C-codex.5` in required metadata and notes.
- [x] Clean release artifact contains required runtime and excludes development/project state.
- [x] No Logistics_App_Copy-specific state or credentials are packaged.
- [x] Package doctor, manifest, checksums, inventory, runtime lock, and drift PASS.
- [x] Fresh-project install and beginner workflow PASS.
- [x] Existing-project upgrade preserves all project state and updates only reusable system files.
- [x] Same-version reinstall is deterministic, non-destructive, and duplicate-free.
- [x] Eight agents parse/discover; Goal tests and existing workflow tests remain PASS.
- [x] Beginner guide and concise release notes are complete.
- [x] Final distributable artifact path and hash are recorded.

## Checklist

- [x] P0-A: Complete actual status before implementation work.
  - Goal: classify release identity, package selection, installer safety, and existing gates from the current tree.
  - Work Steps: inspect metadata/conventions; inspect packaging and installers; attempt Anvien; list correct/partial/missing surfaces; update downstream slices.
  - Implementation Gate: actual status has evidence IDs, invariant map, touch modes, and one P0 decision.
  - Acceptance: current gaps are bounded to release packaging/install safety; Goal and governance are preserve-only.

### P1: Release identity and safe distributable contents

- Phase Goal: make the candidate release identifiable and package only reusable runtime contents.
- Phase Boundary:
  - In scope: version metadata, release notes, guide, package scripts, release manifest/checksum inputs.
  - Out of scope: Goal/runtime architecture and project application state.
  - Dependencies: P0-A and existing doctor/manifest tooling.
- Phase Implementation Rule: implement P1-A, verify and refresh status, then P1-B.
- Ordered Slice List:
  - P1-A: bump release identity and author user-facing release notes/guide.
  - P1-B: curate package selection and add release-package integrity checks.

- [x] P1-A: Bump release identity and user-facing release documents.
  - Goal: identify the reusable build as `8.4.6-C-codex.5` without changing baseline identity.
  - Scope Boundary:
    - Editable: `VERSION`, `manifest/package.json`, release-notes file, beginner guide.
    - Inspect-only: source baseline/version history and existing governance metadata.
    - Preserve-only: Goal, governance, and source content.
    - Out of scope: upstream version scheme changes.
  - Non-Goals: no changelog rewrite or development diary.
  - Pre-flight Questions:
    - Data source: current `VERSION`, manifest version, existing release naming.
    - Display permission: package metadata and beginner-facing docs only.
    - DB read/write flow: N/A; file metadata only.
    - Render location: release root and `docs/`.
    - UI behavior flow: N/A; CLI/package consumer reads metadata.
    - Docker runtime: N/A; CLI/package artifact.
    - Playwright target: N/A; no public UI.
    - Behavior test: metadata consistency and release-note/guide presence.
    - Cleanup/quarantine: do not include development reports/plans in release.
    - External side effects: none; no publication.
    - N/A notes: user approval for actual external release is not performed.
  - Work Steps:
    1. Update only required version/release metadata and add concise release notes.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: release root/docs paths resolve in manifest.
       - Evidence target: metadata consistency test.
    2. Update the beginner entry guide to describe fresh and existing project use in three plain-language steps.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: guide path is packaged and manifest-linked.
       - Evidence target: guide content/package inclusion check.
  - Implementation Gate:
    - Before editing, source metadata and release conventions are recorded in `E0-P0A-META1`.
    - No existing version scheme conflict remains.
  - Acceptance:
    - Source: version and manifest agree at `8.4.6-C-codex.5`.
    - Runtime/UI: N/A; docs are readable UTF-8.
    - DB/data: N/A.
    - Behavior test: metadata and guide checks PASS.
    - Cleanup/quarantine: no development-only files are added to the release set.
    - Evidence IDs: `E1-P1A-META1`, `E1-P1A-DOC1`.
    - Actual-status rows refreshed: release identity, guide, metadata.
  - Evidence Targets: version files, manifest, release notes, guide, consistency test.
  - Actual-status Update: `partial -> correct` for release identity/docs.
  - Commit Boundary: no Git metadata; record no-Git exception instead of initializing a repository.

- [x] P1-B: Curate clean package contents and integrity inputs.
  - Goal: produce a deterministic distributable tree without temporary/project-specific state.
  - Scope Boundary:
    - Editable: `scripts/package.ps1`, `scripts/package.sh`, package manifest/package-selection helpers if needed.
    - Inspect-only: source inventory and doctor required paths.
    - Preserve-only: all runtime source content selected for shipping.
    - Out of scope: installer behavior changes in this slice.
  - Non-Goals: no arbitrary cleanup of the development workspace.
  - Pre-flight Questions:
    - Data source: package doctor required files, manifest entrypoints, runtime lock.
    - Display permission: artifact contents only.
    - DB/data flow: N/A; archive file contents.
    - Render location: parent `D:\AI\P2P_dev\` release artifact and `.tmp` staging.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: archive inventory and package doctor.
    - Cleanup/quarantine: staging under `.tmp`; never archive `.tmp`, reports, caches, plans, or backups.
    - External side effects: none; artifact remains local.
    - N/A notes: package contains immutable source needed by doctor and manifests.
  - Work Steps:
    1. Replace whole-tree archive selection with an explicit allowlist of runtime/package paths and release metadata.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: archive root has install scripts and manifest paths.
       - Evidence target: archive inventory and exclusion scan.
    2. Build a uniquely named ZIP, validate its extracted tree with doctor and checksums, and record its hash.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: extracted release runs from a clean path.
       - Evidence target: package artifact and integrity report.
  - Implementation Gate:
    - Explicit allowlist covers all doctor-required paths and excludes development/project state.
    - Anvien fallback is documented because the package is not indexed.
  - Acceptance:
    - Source: package script is deterministic and refuses overwrite.
    - Runtime/UI: clean extracted package doctor PASS.
    - DB/data: no project state or secrets in archive.
    - Behavior test: package inventory and checksum validation PASS.
    - Cleanup/quarantine: staging outputs remain under `.tmp` and are not shipped.
    - Evidence IDs: `E1-P1B-PKG1`, `E1-P1B-PKG2`.
    - Actual-status rows refreshed: package selection, artifact integrity.
  - Evidence Targets: release archive listing, exclusion scan, doctor, manifest/checksum output.
    - Actual-status Update: `partial -> correct` for package builder/integrity.
  - Commit Boundary: no Git checkpoint available; preserve artifact hash and report.

### P2: Installer safety and release acceptance

- Phase Goal: prove the release can be safely installed/upgraded/reinstalled.
- Phase Boundary:
  - In scope: PowerShell and shell installer state logic, safe fixtures, fresh/existing/reinstall tests.
  - Out of scope: real user home modification, external publication, Goal hardening.
  - Dependencies: P1 clean artifact.
- Phase Implementation Rule: implement P2-A, verify fresh; then P2-B existing/reinstall; then closure.
- Ordered Slice List:
  - P2-A: make installer release-aware and state-preserving.
  - P2-B: run fresh/existing/reinstall acceptance against the real package path.

- [x] P2-A: Make installer release-aware and state-preserving.
  - Goal: distinguish fresh, same-version, upgrade, and initialized roots without overwriting project state.
  - Scope Boundary:
    - Editable: `install.ps1`, `install.sh`, narrowly scoped installer metadata/state helpers.
    - Inspect-only: existing `.p2p` project state schemas and package templates.
    - Preserve-only: project FACT/Live/Eval/policy/approval/ledger/CAPSULE/status/Goal state.
    - Out of scope: changing state schema or adding a second migration system.
  - Non-Goals: no destructive reset or hidden fallback.
  - Pre-flight Questions:
    - Data source: package VERSION/manifest and target `.p2p/system` release marker.
    - Display permission: installer summary and backup path.
    - DB read flow: N/A; read JSON/marker files.
    - DB write flow: reusable system files and release marker only; project state preserved.
    - Render location: target `.p2p/system` and `.p2p/install-backups`.
    - UI behavior flow: terminal installer output.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: PowerShell installer fixtures and shell syntax check.
    - Cleanup/quarantine: each test target isolated under `.tmp`; backups retained inside fixture only.
    - External side effects: none outside temporary fixtures.
    - N/A notes: no live user/project installation.
  - Work Steps:
    1. Add a package release marker and classify target state before system-file replacement.
       - UI flow check: installer prints fresh/same-version/upgrade/already-initialized classification.
       - DB/data flow check: state files are not moved or overwritten by system update.
       - Render location check: `.p2p/system/release.json` is authoritative for installer state.
       - Evidence target: fixture marker/state diff.
    2. Preserve or back up only reusable system files/config/instructions while keeping project state in place.
       - UI flow check: backup path is printed and deterministic for each run.
       - DB/data flow check: FACT/Live/Eval/policy/approval/ledger/CAPSULE/status hashes remain unchanged.
       - Render location check: doctor/drift read the new system tree.
       - Evidence target: existing-project preservation assertions.
  - Implementation Gate:
    - Existing installer behavior and project state paths are enumerated before editing.
    - Tests assert no state overwrite and no duplicate governance tree.
  - Acceptance:
    - Source: both installers validate/record release identity and preserve project state.
    - Runtime/UI: real supported installer path succeeds in isolated fixtures.
    - DB/data: state hashes/history preserved.
    - Behavior test: fresh/upgrade/reinstall tests PASS.
    - Cleanup/quarantine: no fixture escapes `.tmp`.
    - Evidence IDs: `E2-P2A-INSTALL1`, `E2-P2A-INSTALL2`.
    - Actual-status rows refreshed: installer state classification and preservation.
  - Evidence Targets: installer source, fixture state snapshots, doctor/drift.
  - Actual-status Update: `partial -> correct` for installer safety.
  - Commit Boundary: no Git checkpoint; record no-Git exception.

- [x] P2-B: Execute fresh, existing-upgrade, and same-version reinstall acceptance.
  - Goal: prove the release is reusable across new and existing projects.
  - Scope Boundary:
    - Editable: safe test fixtures only; no production project state.
    - Inspect-only: extracted artifact and installer outputs.
    - Preserve-only: source package and runtime implementation.
    - Out of scope: external release publication or live user home.
  - Non-Goals: no manual terminal steps in the hypothetical user flow beyond invoking supported installer entrypoint in the fixture harness.
  - Pre-flight Questions:
    - Data source: extracted release ZIP and fixture snapshots.
    - Display permission: N/A.
    - DB read flow: N/A; file/state hashes.
    - DB write flow: fixture installation only.
    - Render location: installed `.p2p/system` and project state.
    - UI behavior flow: CLI natural-language workflow smoke.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: package acceptance runner plus installer fixture tests.
    - Cleanup/quarantine: all fixture roots and extracted artifacts under `.tmp`.
    - External side effects: none.
    - N/A notes: real eight-thread runtime is not required for package acceptance.
  - Work Steps:
    1. Install fresh fixture from the built artifact and run the beginner natural-language workflow through PASS/BLOCKED/REJECT semantics.
       - UI flow check: N/A.
       - DB/data flow check: new project state created, no user intervention beyond request.
       - Render location check: capsule/status/Goal contract/eval paths exist.
       - Evidence target: fresh acceptance report.
    2. Upgrade an existing fixture, repeat same-version install, and compare state/system/inventory snapshots.
       - UI flow check: N/A.
       - DB/data flow check: project state hashes/history preserved; reusable system changes present.
       - Render location check: doctor/drift PASS after each step.
       - Evidence target: upgrade/reinstall preservation report.
  - Implementation Gate:
    - Fresh install has passed before existing/reinstall tests begin.
  - Acceptance:
    - Source: acceptance harness uses real supported package/install paths.
    - Runtime/UI: beginner workflow reaches a correct terminal result.
    - DB/data: all required project-state preservation assertions PASS.
    - Behavior test: fresh, upgrade, and reinstall all PASS.
    - Cleanup/quarantine: `.tmp` only.
    - Evidence IDs: `E2-P2B-FRESH1`, `E2-P2B-UPGRADE1`, `E2-P2B-REINSTALL1`.
    - Actual-status rows refreshed: all release acceptance rows.
  - Evidence Targets: extracted artifact, three fixture reports, doctor/drift/regression.
  - Actual-status Update: all mandatory release rows become `correct`.
  - Commit Boundary: no Git checkpoint; final artifact hash is closure evidence.

- [x] Pn-A: Call supervisor for the implemented-plan acceptance loop.
  - Goal: independently verify release identity, artifact contents, installer safety, and all acceptance evidence.
  - Work Steps: inspect source/artifact; rerun package/fresh/upgrade/reinstall/doctor/drift checks; write PASS/REJECT report.
  - Implementation Gate: P1 and P2 are complete or explicitly blocked.
  - Acceptance: supervisor PASS or evidenced blocker.
- [x] Pn-B: Remove dead work created during this plan.
  - Goal: keep only release artifact, required docs, tests, and audit evidence.
  - Work Steps: inspect `.tmp`/reports/plans and release contents; remove only plan-created dead artifacts from the shipped package; verify exclusions.
  - Implementation Gate: no unrelated user data is touched.
  - Acceptance: artifact excludes dead/transient content and supervisor accepts cleanup.
- [x] Pn-C: Close the plan.
  - Goal: record final artifact/hash, doctor/drift/regression, no-Git exception, and status.
  - Work Steps: run final validation, refresh lock after last protected change, record artifact path/hash, update four plan files and report.
  - Implementation Gate: supervisor PASS and all mandatory acceptance criteria PASS.
  - Acceptance: final response contains exactly the ten requested sections and completion sentence.

## Risk Notes

- Anvien cannot index this package path; local source/runtime evidence is the fallback.
- Windows installer can be tested natively; Linux installer syntax/fixture execution may be limited by host availability.
- Package doctor intentionally retains immutable source/manifests because they are required integrity evidence.
- No Git metadata exists; no repository will be initialized solely for this task.
- Actual user approval/public release is not performed; the local distributable artifact is the deliverable.
