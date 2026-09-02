# P2P-MPFB2 provisioning root drift ISSUE 56 Plan

## Metadata

- Date: `2026-09-02`
- Status: `in_progress`
- Plan: `docs/plans/2026-09-02-p2p-mpfb2-provisioning-root-drift-01/2026-09-02-p2p-mpfb2-provisioning-root-drift-01-plan.md`
- Evidence: `docs/plans/2026-09-02-p2p-mpfb2-provisioning-root-drift-01/2026-09-02-p2p-mpfb2-provisioning-root-drift-01-evidence.md`
- Benchmark: `docs/plans/2026-09-02-p2p-mpfb2-provisioning-root-drift-01/2026-09-02-p2p-mpfb2-provisioning-root-drift-01-benchmark.md`
- Actual status: `docs/plans/2026-09-02-p2p-mpfb2-provisioning-root-drift-01/2026-09-02-p2p-mpfb2-provisioning-root-drift-01-actual-status.md`

## Goal

Resolve only the MPFB2 provisioning-root integrity mismatch for ISSUE=56. Fresh-fetch and bind exact canonical main `e7c040d87dacf7b5cfee1e57536edc0b27f5768b` / tree `9649785f0104259bac05b244a2162e2a7321657f`, inspect every path responsible for the observed runtime drift, protect MPFB2 `2.0.17` / release `80919fa4682335c41847f761a4d79dcad4124732` and CORE_CC0 assets, apply the smallest safe reconciliation, and execute exactly one real continuation in the existing Windows runtime.

## Rules

- Complete P0 actual status before implementation work.
- Update each checklist item immediately when it is completed.
- Record evidence as work completes.
- Record benchmarkable counts or measurements when they are taken.
- Update later phase status assumptions, next actions, and work steps when actual-status evidence changes the repo state.
- After completing a phase or implementation slice and refreshing `actual-status.md`, update the next affected phase's work steps as needed to match the latest repo reality, while preserving that phase's original goal, scope, acceptance criteria, and major phase order.
- Run Anvien detect-changes before every implementation-slice commit when implementation work was performed.
- Do not reinstall, overwrite, or redownload the manifest, Blender, or MPFB2 before the exact delta is known.
- Do not repair the malformed working `.git`; use a fresh canonical clone or isolated checkout and preserve the existing workspace.
- Treat all unclassified extra paths as fail-closed until exact evidence classifies them.
- Do not update the manifest root hash merely to make the observed runtime pass.
- Preserve firewall logic, PR54 addon lifecycle, PR57 GLB validation, Game Truyen, MPFB2 upstream source, and the Blender installation.
- Run the real route only after root integrity is reconciled; stop at the first downstream blocker.
- For app/runtime validation, full build must include Docker image/container build. If Docker is missing or not run, full build is incomplete.
- Keep the standard planner structure. These detail rules only make phase checklist items concrete enough to implement safely.
- Every implementation phase must be decomposed into multiple implementation slices that are as small as practical. A phase is a grouping and ordering container; a slice is the executable implementation unit.
- Do not implement a phase directly. Work starts from a slice ID such as `P1-A`, `P1-B`, or `P2-C`.
- Prefer many narrow slices over one broad slice. A single-slice implementation phase is allowed only when the plan explicitly states why the phase cannot be split further without creating empty or non-executable slices.
- Each implementation slice must include goal, scope boundary, non-goals, pre-flight questions, work steps, implementation gate, acceptance, evidence targets, actual-status update, and commit boundary.
- Hidden fallback is forbidden. Prefer a visible failure over a fallback that hides a broken primary path.
- If source changes are required, focused tests must prove pinned source mutation failure, pinned asset mutation failure, approved deterministic generated-file handling, unknown-extra-file fail-closed behavior, and exact manifest binding.

## Problem

The existing runtime root at `D:\AI\P2P_runtime\mpfb2-runtime-01` was reported with computed hash `10ebf09a8b425f6e1081f9624ccf9365e471522b01527820e89d27b20de705bf`, while the manifest-bound expected root hash is `f6907ef03674ddc995e8b0fdd988e9a003cad61df0d4f707e2a7aaeda4d4e788`. The responsible paths and whether the pinned subject changed are not yet proven. The previous real runtime reached MPFB initialization and stopped later at the known GLB skeleton blocker, so this workstream must not conflate root reconciliation with downstream GLB repair.

## Scope

- Fresh-fetch `origin/main` in a usable clean checkout and verify exact canonical main SHA/tree.
- Inspect the manifest-bound root definition and compute a deterministic path-level comparison against the current runtime root.
- Identify every added, modified, or deleted path responsible for the root mismatch and classify each as `RUNTIME_GENERATED`, `PINNED_SOURCE`, `PINNED_ASSET`, `MANIFEST_METADATA`, or `UNKNOWN`.
- Verify MPFB2 version/release SHA and byte-level integrity of all pinned source and CORE_CC0 assets.
- Decide from evidence among `HASH_SCOPE_DEFECT`, `RUNTIME_CLEANUP_DEFECT`, and `PINNED_RUNTIME_CORRUPTION`.
- Apply only runtime-only deterministic restoration or one bounded source fix at the existing root-hash boundary; preserve all protected surfaces.
- Add/update only the focused tests required when source changes.
- Run exactly one real canonical MPFB2 continuation using the existing Windows runtime, with firewall-before-spawn and cleanup evidence.
- Record issue/PR/candidate/runtime/provenance/hash/validation fields requested by the user.

## Non-Goals

- No Blender or MPFB2 reinstall, download, upgrade, or upstream edit.
- No manifest rewrite without exact path evidence and an authorized bounded source change.
- No generic ignore pattern, disabled hashing, cache manager, second provisioning framework, or arbitrary unknown-file exclusion.
- No firewall, addon lifecycle, GLB validator, rig/skeleton, Game Truyen, release, deployment, or promotion changes.
- No repair of any downstream blocker after the first one reached by the single continuation.

## Requirements

- Canonical subject: main `e7c040d87dacf7b5cfee1e57536edc0b27f5768b`, tree `9649785f0104259bac05b244a2162e2a7321657f`.
- Runtime root: `D:\AI\P2P_runtime\mpfb2-runtime-01`.
- Expected root hash: `f6907ef03674ddc995e8b0fdd988e9a003cad61df0d4f707e2a7aaeda4d4e788`.
- MPFB2 pin: version `2.0.17`, release SHA `80919fa4682335c41847f761a4d79dcad4124732`.
- Root-delta output must include every path, type, classification, evidence, and final count.
- Pinned source/assets must be proved unchanged byte-for-byte or the work must fail closed as corruption.
- Any runtime-only cleanup must use an exact deterministic allowlist derived from observed evidence and must preserve unknown-file failure.
- A source fix must include focused behavior tests and fresh impact/change evidence.
- Runtime result must distinguish root integrity, firewall, Blender child, MPFB addon, character creation, GLB, provenance, cleanup, and first blocker.

## Acceptance Criteria

- Exact canonical main SHA and tree are freshly fetched and independently verified.
- Every root-drift path is listed and classified; no “cache” or disposable label is inferred without evidence.
- `PINNED_SUBJECT_MUTATED=NO`, `PINNED_SOURCE_CHANGED=NO`, and `PINNED_ASSETS_CHANGED=NO`, unless the evidence proves mutation and the terminal result is fail-closed.
- Exactly one of the design-defect classifications is selected from path evidence, or corruption is reported.
- The root hash equals the manifest-bound hash after the smallest safe remediation, without weakening root hashing or broadening the ignore set.
- Focused tests pass when source changes are made; unknown extra files remain fail-closed and manifest binding remains exact.
- Exactly one real continuation is run with the existing runtime and no reinstall. The run stops at the first downstream blocker, if any.
- No Game Truyen files are mutated.
- A coder evidence report and supervisor review artifact are written; final verdict uses one of the two user-specified terminal values.

## Checklist

- [x] P0-A: Complete actual status before implementation work.
  - Goal: establish the real current state of the malformed working checkout, fresh canonical source, manifest contract, runtime root, and known prior runtime boundary.
  - Work Steps: inspect current Git/worktree state without repairing it; fresh-fetch a usable canonical checkout; inspect the manifest/root-hash implementation and relevant runtime entrypoint; inventory current runtime root; record all user-supplied and independently verified facts; classify each target surface and update P1-P3 decisions.
  - Implementation Gate: no implementation or runtime cleanup starts until `2026-09-02-p2p-mpfb2-provisioning-root-drift-01-actual-status.md` has a final P0 decision and exact evidence IDs.
  - Acceptance: actual status identifies correct, partial, missing/unbound, fake-or-stub, and blocked surfaces for this scope, and explicitly states whether P1 should proceed. P0 is complete; P1 evidence selected the exact bounded source-fix path.

### P1: Exact subject, delta, and pinned-byte classification

- Phase Goal: bind the investigation to fresh canonical main and determine the complete root delta without changing the manifest or pinned subject.
- Phase Boundary:
  - In scope: fresh remote fetch, clean checkout, manifest/root-hash code and data inspection, runtime inventory/hash comparison, exact pinned source/asset byte verification, defect classification.
  - Out of scope: source repair, manifest changes, runtime installation, Blender execution, firewall changes, Game Truyen, and downstream GLB repair.
  - Dependencies: P0 complete; current working `.git` remains preserve-only if unusable.
- Phase Implementation Rule: do not implement `P1` directly. Implement `P1-A`, verify it, record evidence, refresh actual-status, commit when required, then continue to `P1-B`.
- Ordered Slice List:
  - P1-A: Fresh canonical subject and manifest-bound root inventory.
  - P1-B: Complete runtime delta and pinned-subject byte audit.

- [x] P1-A: Fresh canonical subject and manifest-bound root inventory
  - Goal: obtain a usable exact-main subject and establish the root-hash scope and runtime inventory from current files.
  - Scope Boundary:
    - Editable: repo-local plan/evidence/status files only.
    - Inspect-only: fresh canonical checkout, manifest, root-hash code, MPFB2 runtime root, existing runtime logs/receipts.
    - Preserve-only: malformed current `.git`, Windows Blender installation, MPFB2 runtime content, Game Truyen, upstream source.
    - Out of scope: any manifest/runtime/source mutation.
  - Non-Goals: no cleanup, no reinstall, no hash rebinding, no Blender spawn.
  - Pre-flight Questions:
    - Data source: remote `origin/main`, fresh clone, manifest-bound runtime root.
    - Display permission: N/A; this is filesystem/runtime evidence, not UI.
    - DB read flow: N/A; no database.
    - DB write flow: N/A; no database.
    - Render location: N/A; no UI.
    - UI behavior flow: N/A; no UI.
    - Docker runtime: N/A for this native Windows Blender runtime; document that the app/runtime plan rule is not applicable to this non-container route.
    - Playwright target: N/A; no browser surface.
    - Behavior test: exact SHA/tree, root-scope manifest binding, and inventory command outputs.
    - Cleanup/quarantine: none in this slice; all runtime paths are preserve-only.
    - External side effects: read-only remote fetch and local clone creation under repo-local `.tmp` only.
    - N/A notes: no product UI, DB, or Docker surface exists in this issue.
  - Work Steps:
    1. Verify the current checkout is unusable as Git and preserve it; create/use a fresh repo-local analysis checkout with `core.autocrlf=false`, fetch `origin/main`, and verify the exact canonical SHA/tree.
       - UI flow check: N/A.
       - DB/data flow check: trace remote ref -> local commit/tree -> inspected source; no DB.
       - Render location check: N/A.
       - Evidence target: E1-P1A-SUBJECT1 and E1-P1A-SUBJECT2.
    2. Locate the manifest-bound root definition, MPFB2 pin declarations, and runtime entrypoint; record the current runtime root inventory and the two root hashes without modifying either subject.
       - UI flow check: N/A.
       - DB/data flow check: trace manifest -> root enumerator -> computed hash and runtime filesystem -> observed hash.
       - Render location check: N/A.
       - Evidence target: E1-P1A-MAP1 and E1-P1A-HASH1.
  - Implementation Gate:
    - Before editing target files, run relevant Anvien file-detail/impact evidence for files selected for a possible later fix; record the evidence IDs.
    - P0 is complete, canonical SHA/tree are exact, and root-scope authority is located.
  - Acceptance:
    - Source: exact canonical source is available and no protected source was edited.
    - Runtime/UI: existing runtime root is inventoried read-only.
    - DB/data: N/A.
    - Behavior test: exact subject and hash computations are independently reproducible.
    - Cleanup/quarantine: no runtime files changed.
    - Evidence IDs: E1-P1A-SUBJECT1..E1-P1A-HASH1.
    - Actual-status rows refreshed: canonical subject, root contract, runtime inventory.
  - Evidence Targets: fresh-fetch output, SHA/tree binding, manifest/root-scope source, pin declarations, runtime hash/inventory.
  - Actual-status Update: mark canonical subject `bound-correct`; keep root mismatch `partial`; update P1-B with exact target paths and no-edit boundary. Completed with exact SHA/tree and root inventory evidence.
  - Commit Boundary: no implementation commit; plan/evidence/status artifacts are committed only if repository authority permits and after change detection.

- [x] P1-B: Complete runtime delta and pinned-subject byte audit
  - Goal: identify every responsible path and prove whether pinned MPFB2 source or CORE_CC0 assets changed.
  - Scope Boundary:
    - Editable: repo-local evidence/status/benchmark artifacts only.
    - Inspect-only: manifest-bound subject and current runtime root, including hidden/generated/state/log/cache/temp paths.
    - Preserve-only: all pinned source/assets and any path not proven disposable by exact evidence.
    - Out of scope: remediation and manifest update.
  - Non-Goals: no generic cache inference, no deleting files, no “repair by recopy” before classification.
  - Pre-flight Questions:
    - Data source: exact root enumeration rules, archive/manifest records, pinned release tree, current runtime bytes.
    - Display permission: N/A.
    - DB read flow: N/A.
    - DB write flow: N/A.
    - Render location: N/A.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: delta map and byte-level source/asset comparison.
    - Cleanup/quarantine: none until classification is complete; if exact duplicate evidence requires quarantine, use repo-local evidence staging and preserve originals.
    - External side effects: none beyond read-only filesystem inspection.
    - N/A notes: runtime filesystem and archive data are the source-of-truth surfaces.
  - Work Steps:
    1. Compute a complete path-level delta with `ADDED`, `MODIFIED`, and `DELETED`, covering `__pycache__`, `.pyc`, extension state, preferences/state, temp, logs, caches, source, and assets; assign only evidence-supported classifications.
       - UI flow check: N/A.
       - DB/data flow check: trace expected manifest path set -> observed runtime path set -> per-path type/classification.
       - Render location check: N/A.
       - Evidence target: E1-P1B-DELTA1.
    2. Verify MPFB2 version/release identity and compare every pinned source and CORE_CC0 asset byte; select the exact defect classification and smallest safe restoration path.
       - UI flow check: N/A.
       - DB/data flow check: trace release pin/archive bytes -> runtime pinned bytes -> SHA result.
       - Render location check: N/A.
       - Evidence target: E1-P1B-PIN1 and E1-P1B-CLASS1.
  - Implementation Gate:
    - No source/runtime edit is permitted until every delta path has a type and classification, and pinned mutation status is explicit.
    - If any pinned byte differs, stop fail-closed with `PINNED_RUNTIME_CORRUPTION=YES` and no manifest rewrite.
  - Acceptance:
    - Source: all pinned source/assets are proven unchanged or corruption is reported.
    - Runtime/UI: complete root delta is recorded.
    - DB/data: N/A.
    - Behavior test: the classification is derived from exact evidence, not filename convention alone.
    - Cleanup/quarantine: no unapproved deletion occurred.
    - Evidence IDs: E1-P1B-DELTA1, E1-P1B-PIN1, E1-P1B-CLASS1.
    - Actual-status rows refreshed: delta inventory, pinned source, pinned assets, selected defect.
  - Evidence Targets: complete delta table, source/asset hash map, version/release proof, selected design-defect and restoration decision.
  - Actual-status Update: update P2 work steps to the exact bounded path; `HASH_SCOPE_DEFECT=YES`, `RUNTIME_CLEANUP_DEFECT=NO`, `PINNED_RUNTIME_CORRUPTION=NO`; proceed to one exact source boundary fix.
  - Commit Boundary: no implementation commit; evidence/status update only.

### P2: Smallest reconciliation and focused proof

- Phase Goal: repair only the proven root-boundary defect and prove the invariant without weakening fail-closed behavior.
- Phase Boundary:
  - In scope: exact runtime cleanup or one bounded source change at the existing root-hash boundary, focused tests if source changes, root hash re-computation.
  - Out of scope: manifest rebinding without proof, generic ignore rules, cache manager, second provisioning framework, protected runtime surfaces.
  - Dependencies: P1 complete and `PINNED_SUBJECT_MUTATED=NO` for any continuation.
- Phase Implementation Rule: do not implement `P2` directly. Implement `P2-A`, verify it, refresh actual-status, commit when required, then continue to `P2-B` only if source changed.
- Ordered Slice List:
  - P2-A: Apply the minimum runtime-only or bounded source reconciliation.
  - P2-B: Focused root-integrity regression proof when source changed.

- [x] P2-A: Apply the minimum runtime-only or bounded source reconciliation
  - Goal: make legitimate execution deterministic without excluding pinned source/assets or unknown files.
  - Scope Boundary:
    - Editable: only exact source files identified by P1-B, or exact generated runtime paths identified by P1-B.
    - Inspect-only: all unrelated provisioning, firewall, addon, validator, and product surfaces.
    - Preserve-only: MPFB2 pinned source/assets, manifest bytes unless an exact source contract requires a bounded update, Blender installation, Game Truyen.
    - Out of scope: downstream route repair.
  - Non-Goals: no broad refactor, no cache subsystem, no generic ignores, no manifest hash replacement.
  - Pre-flight Questions:
    - Data source: P1-B exact delta and selected defect.
    - Display permission: N/A.
    - DB read flow: N/A.
    - DB write flow: N/A.
    - Render location: N/A.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: root verification before/after deterministic execution and unknown-file fail-closed behavior.
    - Cleanup/quarantine: if runtime-only, remove/quarantine only the exact proven generated allowlist and prove pinned bytes unchanged; if source fix, no runtime cleanup beyond test isolation.
    - External side effects: possible local runtime file removal only if P1-B proves it exact and user scope authorizes reconciliation.
    - N/A notes: runtime route is native Windows, not web/UI.
  - Work Steps:
    1. Run Anvien `file-detail` plus impact on each candidate source symbol/file before editing; if runtime-only, record that no source edit is needed and execute only the exact allowlisted restoration.
       - UI flow check: N/A.
       - DB/data flow check: trace hash verifier -> root scope -> runtime path treatment.
       - Render location check: N/A.
       - Evidence target: E2-P2A-IMPACT1 and E2-P2A-FIX1.
    2. Recompute the root hash, recheck pinned source/assets and unknown-extra-file behavior, then run the smallest directly affected focused checks.
       - UI flow check: N/A.
       - DB/data flow check: trace reconciled filesystem/source -> verifier -> exact manifest hash result.
       - Render location check: N/A.
       - Evidence target: E2-P2A-ROOT1 and E2-P2A-BOUNDARY1.
  - Implementation Gate:
    - P1-B proves the exact path and selected defect; Anvien impact/file-detail evidence is fresh for every source symbol/file edited.
    - `PINNED_SUBJECT_MUTATED=NO` is required; otherwise stop.
  - Acceptance:
    - Source: only the bounded existing boundary changed, if any; pinned subject remains fully bound.
    - Runtime/UI: root integrity equals the expected manifest hash.
    - DB/data: N/A.
    - Behavior test: affected root verification passes and unknown files remain fail-closed.
    - Cleanup/quarantine: exact generated paths only, or none for source fix; no protected file removed.
    - Evidence IDs: E2-P2A-IMPACT1, E2-P2A-FIX1, E2-P2A-ROOT1, E2-P2A-BOUNDARY1.
    - Actual-status rows refreshed: remediation, root integrity, pinned subject.
  - Evidence Targets: impact report, diff, root hash after repair, pinned hash recheck, unknown-file negative check, source/runtime test result.
  - Actual-status Update: mark root integrity `correct` after candidate code recomputes the existing runtime to the exact manifest hash; update P2-B/P3 assumptions. Completed with a bounded source fix only.
  - Commit Boundary: if implementation work occurred, run `anvien detect-changes --repo <repo> --scope all`, then one small checkpoint commit for this slice.

- [x] P2-B: Focused root-integrity regression proof when source changed
  - Goal: prove the five required root-binding behaviors and avoid broad unrelated testing.
  - Scope Boundary:
    - Editable: focused tests directly covering the bounded source fix, plus the source fix from P2-A if needed.
    - Inspect-only: unrelated full suite and protected surfaces.
    - Preserve-only: manifest/pinned source/assets and all closed firewall/addon/GLB code.
    - Out of scope: broad regression, runtime downstream route, Game Truyen.
  - Non-Goals: no test-only weakening or removal of negative gates.
  - Pre-flight Questions:
    - Data source: root verifier/manifest and isolated temporary test roots.
    - Display permission: N/A.
    - DB read flow: N/A.
    - DB write flow: N/A.
    - Render location: N/A.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: mutation/fail-close and approved-generated-file/pass cases.
    - Cleanup/quarantine: all temporary test roots under repo-local `.tmp`; deterministic cleanup after each isolated trial.
    - External side effects: none.
    - N/A notes: only applicable if P2-A changes source; otherwise mark this slice N/A with evidence.
  - Work Steps:
    1. Add or update only direct behavior tests for pinned source mutation failure, pinned asset mutation failure, approved deterministic generated files not causing false drift, unknown extra files failing closed, and exact manifest binding.
       - UI flow check: N/A.
       - DB/data flow check: isolated root -> verifier -> pass/fail result.
       - Render location check: N/A.
       - Evidence target: E2-P2B-TEST1.
    2. Run focused tests, compile/build required by the repository, record failures without patching unrelated code, and run change detection before checkpoint commit.
       - UI flow check: N/A.
       - DB/data flow check: N/A beyond test flow.
       - Render location check: N/A.
       - Evidence target: E2-P2B-TEST2 and E2-P2B-DETECT1.
  - Implementation Gate:
    - P2-A source fix exists and only the required focused tests are in scope; all test roots are isolated under repo-local `.tmp`.
  - Acceptance:
    - Source: focused tests encode current behavior, not static shape only.
    - Runtime/UI: N/A.
    - DB/data: N/A.
    - Behavior test: all five required cases pass.
    - Cleanup/quarantine: isolated test roots are cleaned or retained only as evidence under `.tmp`.
    - Evidence IDs: E2-P2B-TEST1, E2-P2B-TEST2, E2-P2B-DETECT1.
    - Actual-status rows refreshed: focused proof and source candidate.
  - Evidence Targets: test paths/line numbers, focused results, compile/build result, change detection, commit SHA/tree.
  - Actual-status Update: mark focused proof `correct` after 22/22 `AdapterBoundaryTests` pass, including all five required cases plus the outside-cache negative; proceed to P3. Package doctor governance drift remains a pre-existing out-of-scope validation failure.
  - Commit Boundary: separate commit from P2-A if tests/source were changed.

### P3: One real canonical MPFB2 continuation

- Phase Goal: execute exactly one existing-runtime continuation after root reconciliation and stop at the first downstream blocker.
- Phase Boundary:
  - In scope: root integrity -> firewall -> Blender -> MPFB2 addon -> create_human -> rig/skin -> GLB export -> provenance -> GLB validation -> cleanup.
  - Out of scope: reinstall/download, retries, second character, firewall/addon/GLB fixes, Game Truyen, release/deployment/promotion.
  - Dependencies: root hash reconciled and pinned subject unchanged; source-focused proof passed when applicable.
- Phase Implementation Rule: execute one run only; do not add a second runtime slice or repair a downstream blocker in this workstream.
- Ordered Slice List:
  - P3-A: Exactly one real canonical continuation and first-blocker report.

- [ ] P3-A: Exactly one real canonical continuation and first-blocker report
  - Goal: prove the post-reconciliation runtime boundary and produce the requested terminal fields.
  - Scope Boundary:
    - Editable: runtime-local logs/receipts/provenance/output only as produced by the existing canonical entrypoint; repo-local evidence/status artifacts.
    - Inspect-only: protected firewall/addon/validator code and Game Truyen.
    - Preserve-only: Blender installation, MPFB2 upstream source, existing closed PR54/PR57 surfaces.
    - Out of scope: any repair after first downstream blocker.
  - Non-Goals: no reinstall, no retry, no force-through, no cleanup beyond the canonical route's own cleanup.
  - Pre-flight Questions:
    - Data source: reconciled runtime, existing canonical entrypoint, exact pinned manifest/provenance.
    - Display permission: N/A.
    - DB read flow: N/A.
    - DB write flow: N/A.
    - Render location: N/A.
    - UI behavior flow: N/A.
    - Docker runtime: N/A; native Blender route.
    - Playwright target: N/A.
    - Behavior test: real process/artifact evidence, not synthetic tests.
    - Cleanup/quarantine: canonical firewall and output cleanup only; record final counts and paths.
    - External side effects: one Windows Blender child and one firewall lifecycle; no network enablement.
    - N/A notes: this is the only execution attempt allowed by the workstream.
  - Work Steps:
    1. Verify root integrity immediately before the run, verify firewall prerequisites, spawn the exact Blender child, and capture addon/create_human/rig/skin/export/provenance events.
       - UI flow check: N/A; Blender is driven by the canonical headless entrypoint.
       - DB/data flow check: recipe/manifest -> Blender/MPFB2 -> output files and provenance.
       - Render location check: N/A.
       - Evidence target: E3-P3A-RUN1.
    2. Independently validate GLB/provenance, clean firewall/output state, record the first blocker if present, and stop.
       - UI flow check: N/A.
       - DB/data flow check: GLB/provenance bytes -> validators -> verdict; cleanup -> zero/expected residuals.
       - Render location check: N/A.
       - Evidence target: E3-P3A-ARTIFACT1 and E3-P3A-CLEAN1.
  - Implementation Gate:
    - P2 acceptance is complete; exact runtime and command are identified; no protected surface has changed.
  - Acceptance:
    - Source: no protected source modified.
    - Runtime/UI: exactly one real run is recorded with each requested stage and first blocker.
    - DB/data: N/A.
    - Behavior test: real route evidence distinguishes each gate and does not claim blocked downstream stages as passed.
    - Cleanup/quarantine: firewall cleanup and output cleanup are verified.
    - Evidence IDs: E3-P3A-RUN1, E3-P3A-ARTIFACT1, E3-P3A-CLEAN1.
    - Actual-status rows refreshed: real runtime execution, artifacts, first blocker, final verdict.
  - Evidence Targets: runtime receipt, child PID/logs, output/sha256, GLB structural/provenance result, cleanup result, Game Truyen fingerprint.
  - Actual-status Update: stop at first blocker; do not add remediation steps for a downstream blocker.
  - Commit Boundary: runtime evidence is not a source commit; write report and status closure only.

- [ ] Pn-A: Call supervisor for the implemented-plan acceptance loop.
  - Goal: verify the completed plan work against the accepted plan, actual-status decisions, evidence, benchmark, changed files, generated output, and validation results before closure.
  - Work Steps:
    1. Call the supervisor skill to review the full completed plan work.
    2. If supervisor fails the work, return to the responsible implementation workflow/skill for the failed scope only.
    3. Re-run supervisor review after the fix.
    4. Repeat until supervisor passes or records a blocker.
  - Implementation Gate: all planned implementation phases must be completed or explicitly blocked before this review.
  - Acceptance: supervisor review passes, or the plan records a blocker with evidence and no closure is performed.
- [ ] Pn-B: Remove dead work created during this plan.
  - Goal: ensure the final diff contains only artifacts that still serve the accepted plan.
  - Work Steps:
    1. Review files, sections, generated output, tests, temp files, and plan artifacts created or modified during this plan.
    2. Remove or rewrite any artifact made obsolete by actual-status findings, user corrections, failed approaches, or phase status updates.
    3. Verify no rejected approach, stale placeholder, unused generated output, or dead helper artifact remains in the final diff.
    4. Call supervisor to review the dead-work cleanup.
    5. If supervisor fails the cleanup, return to the responsible implementation workflow/skill for the failed cleanup scope only, then re-run supervisor review.
  - Implementation Gate: only remove artifacts created by this plan unless the user explicitly approves broader cleanup.
  - Acceptance: final `git diff/status` contains no dead plan-created artifacts, supervisor passes the cleanup, and evidence records what was removed or preserved.
- [ ] Pn-C: Close the plan.
  - Goal: finish validation, evidence, benchmark, detect-changes, commit, and final status.
  - Work Steps:
    1. Run the required final validation for the accepted scope, including full build before final runtime validation. For this native runtime route, record Docker as N/A with reason rather than substituting a dev server.
    2. Regenerate generated outputs if source-of-truth changes require it.
    3. Run Anvien detect-changes before commit when implementation work was performed.
    4. Record final validation, detect-changes, benchmark, and commit evidence.
    5. Commit the completed scope and verify the worktree state.
  - Implementation Gate: Pn-A and Pn-B must pass or record blockers.
  - Acceptance: final evidence is recorded, required commits exist when source changed, and the worktree state is known.

## Risk Notes

- The current working directory may be a malformed Git root; never repair or initialize it as part of this issue.
- Runtime-generated files may be legitimate execution state or may be part of the manifest scope; classification must come from the actual root contract and byte evidence.
- Deleting a path before proving its class could destroy pinned subject evidence; preserve until P1-B closes.
- A source fix can alter root-binding security; require focused negative tests and fresh impact/change evidence.
- Existing memory reports a later GLB skeleton blocker after addon initialization; that is an expected first downstream stop candidate, not permission to edit PR57 or rig output here.
