# P2P-MPFB2-GLB-SKIN-VALIDATION-01 Plan

## Metadata

- Date: `2026-09-02`
- Status: `in_progress`
- Plan: `docs/plans/2026-09-02-p2p-mpfb2-glb-skin-validation-01/2026-09-02-p2p-mpfb2-glb-skin-validation-01-plan.md`
- Evidence: `docs/plans/2026-09-02-p2p-mpfb2-glb-skin-validation-01/2026-09-02-p2p-mpfb2-glb-skin-validation-01-evidence.md`
- Benchmark: `docs/plans/2026-09-02-p2p-mpfb2-glb-skin-validation-01/2026-09-02-p2p-mpfb2-glb-skin-validation-01-benchmark.md`
- Actual status: `docs/plans/2026-09-02-p2p-mpfb2-glb-skin-validation-01/2026-09-02-p2p-mpfb2-glb-skin-validation-01-actual-status.md`

## Goal

Resolve only the first downstream structural blocker `GLB_skeleton: index invalid` for the exact existing Oak GLB. Accept an omitted optional `skin.skeleton` property while preserving explicit-index fail-closed behavior, required joints validation, the intentional P2P rooted-skeleton policy, accessor validation, mesh skinning validation, provenance, and all previously proven MPFB2/firewall/Game Truyen boundaries.

## Rules

- Complete P0 actual status before implementation work.
- Fresh-fetch and bind all work to canonical main `c8f4449977987a3288717f9a462dae8967f7246d` and tree `c8ce1ec46ed3399341b38817c5b138604fee1ac2`.
- Inspect `D:\AI\P2P_runtime\mpfb2-runtime-01\output\Oak.glb` first and require SHA-256 `5f96f86fbfd4cdc01201e767b0383807ac5e2a7a6365252aee568a91a949c0c4` before any runtime rerun.
- Do not regenerate, mutate, standardize, post-process, or replace the existing GLB for the initial proof.
- `skin.joints` remains required, non-empty, unique, and range-checked. `skin.skeleton` remains optional. An explicit null or invalid value fails closed.
- Preserve the existing stronger P2P rooted-skeleton rule because the Asset Forge Protocol intentionally requires a rooted skeleton. When `skeleton` is omitted, derive the unique joint root only for that policy check; do not invent or write an artifact field.
- Change only the existing structural validator and directly affected tests. Do not add a second validator or exporter workaround.
- Do not change `windows_network_isolation.py`, MPFB2 addon lifecycle, `addon_utils.enable` binding, MPFB2 pin/version, adapter security boundary, provenance model, Game Truyen, or the existing artifact.
- Run exactly one canonical real MPFB2 runtime rerun, and only after exact existing-artifact validation passes. Stop at full PASS or the first different genuine downstream blocker; do not fix that blocker in this task.
- Update each checklist item immediately when it is completed.
- Record evidence as work completes.
- Record benchmarkable counts or measurements when they are taken.
- Update later phase status assumptions, next actions, and work steps when actual-status evidence changes the repo state.
- Run Anvien detect-changes before every implementation-slice commit when implementation work was performed.
- For this non-UI Python validator slice, Docker and Playwright are N/A: no public service, browser surface, or container build is part of the requested invariant.
- Keep the standard planner structure. These detail rules only make phase checklist items concrete enough to implement safely.
- Every implementation phase is decomposed into narrow slices; a phase is not implemented directly.
- Hidden fallback is forbidden. An omitted optional field is handled explicitly, while explicit malformed values remain visible failures.
- Tests use repo-local temporary roots and never write the existing runtime artifact or any protected project path.

## Problem

The exact existing Oak GLB is a valid glTF 2.0 container with one skin, 53 joints, 55 reachable nodes, a valid inverse-bind-matrix accessor, and paired JOINTS_0/WEIGHTS_0 attributes. Its JSON chunk omits `skins[0].skeleton`. The canonical validator currently calls `_index(skin.get("skeleton"), ...)`, converting omission into `None` and raising `GLB_skeleton: index invalid`. This conflates an absent optional property with an invalid present property and blocks the artifact before the already-proven downstream runtime can continue.

## Scope

- Fresh canonical source fetch and exact base/tree binding.
- Direct binary JSON-chunk inspection and independent structural checks of the existing Oak GLB.
- `.p2p/system/p2p_capabilities/glb_validator.py`, limited to optional `skeleton` handling inside the existing mesh/skin validator.
- `tests/test_p2p_game_truyen_mpfb_adapter_01.py`, limited to direct structural regression cases for omitted, valid, null, negative, out-of-range, non-integer skeleton values and joints failures.
- Repo-local plan, evidence, benchmark, actual-status, coder, and supervisor reports required by project workflow.
- Exact existing-artifact validation, followed by at most one real rerun through the existing Blender/MPFB2 runtime if the preconditions pass.

## Non-Goals

- No GLB mutation, regeneration, export postprocessor, second validator, or artifact repair.
- No change to the Blender entrypoint, MPFB2 addon lifecycle, adapter, firewall/isolation, pin/version, provenance, or runtime security boundary.
- No Game Truyen access or mutation.
- No broad regression suite, hardening, visual/browser QA, Three.js integration, or repair of a later downstream blocker.
- No release, deployment, merge, force push, or promotion inference from technical PASS.

## Requirements

- Record exact artifact fields: `SKIN_COUNT`, skeleton property presence, raw value classification, joint count/indices, node count, and skin-referencing nodes.
- Distinguish property absent, property present with JSON null, and property present with an invalid integer.
- Reconcile against glTF 2.0: `joints` is required and non-empty; `skeleton` is optional; an explicit skeleton is a non-negative node index and must satisfy the glTF hierarchy rule.
- Preserve the intentional P2P rooted-skeleton rule from `asset-forge-protocol.md`: all listed joints must have one common root/ancestor and be connected under it. For omission, infer only the unique joint root needed to check this invariant.
- Preserve valid skin references, scene reachability, joint index checks, inverse-bind-matrix checks, JOINTS_n/WEIGHTS_n pairing, accessor checks, resources, provenance, and output naming.
- Focused tests must cover both acceptance and fail-closed cases named by the workstream.
- The exact existing Oak GLB must validate after the source fix without changing its bytes or hash.

## Acceptance Criteria

- Canonical base and tree match the supplied values, with no source drift before the candidate change.
- Artifact SHA-256 matches the expected value and direct parsing proves `skeleton` is absent, not null.
- `VALIDATOR_DEFECT=YES` and `ARTIFACT_DEFECT=NO` are supported by direct source and artifact evidence, unless fresh evidence disproves that classification.
- Omitted skeleton passes only when the preserved rooted-joint hierarchy is coherent; valid explicit skeleton passes; null, negative, out-of-range, and non-integer explicit values fail closed.
- Empty or invalid joints remain rejected, and accessor/mesh/scene checks remain intact.
- `EXISTING_OAK_GLB_VALIDATION=PASS` is recorded before any rerun.
- At most one real rerun executes through firewall -> Blender -> MPFB2 -> character -> GLB -> provenance -> structural validation -> cleanup. Any different downstream blocker stops the task without a second fix.
- Game Truyen mutations are `NO`; preserved firewall/addon/provenance surfaces remain unchanged.
- A focused coder report and independent supervisor report exist, and candidate SHA/tree plus PR metadata are recorded if external candidate publication is authorized by the exact workflow state.

## Checklist

- [x] P0-A: Complete actual status before implementation work.
  - Goal: establish the real current state from fresh canonical, artifact, source, spec, and impact evidence.
  - Work Steps: verify canonical fetch and tree; hash and parse Oak.glb directly; run the current validator with the normalized recipe; read the glTF and P2P contracts; inspect the validator/test surfaces; record Anvien file-detail and impact evidence; classify artifact versus validator defect; update downstream slice assumptions.
  - Implementation Gate: `2026-09-02-p2p-mpfb2-glb-skin-validation-01-actual-status.md` has a completed P0 decision with evidence IDs, and no implementation has started.
  - Acceptance: current status distinguishes correct/preserve-only artifact and runtime boundaries from the wrong validator behavior and the partial test matrix.

### P1: Surgical validator contract repair and direct regression coverage

- Phase Goal: repair only optional-skeleton interpretation and encode the required pass/fail matrix without weakening the existing structural invariant family.
- Phase Boundary:
  - In scope: the existing `_validate_mesh_skin` implementation and directly affected GLB structural tests.
  - Out of scope: artifact bytes, exporter/runtime code, firewall, addon lifecycle, provenance, Game Truyen, broad tests, and later downstream blockers.
  - Dependencies: P0 evidence proves omitted `skeleton`, valid joint hierarchy, validator defect, and target file ownership.
- Phase Implementation Rule: do not implement `P1` directly. Implement `P1-A`, verify it, record evidence, refresh actual-status, commit when required, then continue to `P1-B`.
- Ordered Slice List:
  - P1-A: Make optional `skin.skeleton` handling explicit in the canonical structural validator.
  - P1-B: Add the narrow skeleton/joints structural regression matrix.

- [x] P1-A: Make optional `skin.skeleton` handling explicit in the canonical structural validator.
  - Goal: accept omission of the optional property while preserving explicit range checks and the rooted-skeleton policy.
  - Scope Boundary:
    - Editable: `.p2p/system/p2p_capabilities/glb_validator.py`, only `_validate_mesh_skin` logic needed for skeleton-root selection.
    - Inspect-only: `asset_provenance.py`, `character_recipe.py`, `mpfb_adapter.py`, `mpfb_blender_entrypoint.py`, `windows_network_isolation.py`, protocol/spec files, and runtime artifact.
    - Preserve-only: all existing scene, mesh, skin, joint, accessor, resource, provenance, and output-name checks outside the selected branch.
    - Out of scope: exporter changes, artifact mutation, runtime changes, firewall changes, and Game Truyen.
  - Non-Goals: do not relax explicit null or malformed values; do not remove rooted hierarchy checking; do not create a helper validator or normalize JSON omission into null.
  - Pre-flight Questions:
    - Data source: canonical validator source plus direct Oak JSON chunk; no database.
    - Display permission: N/A; no UI.
    - DB read flow: N/A; no database.
    - DB write flow: N/A; no database.
    - Render location: N/A; no UI render.
    - UI behavior flow: N/A; this is a Python structural boundary.
    - Docker runtime: N/A; no public/container runtime exists for this slice.
    - Playwright target: N/A; no browser surface.
    - Behavior test: direct `validate_glb_output` and focused temporary GLB fixtures.
    - Cleanup/quarantine: test fixtures use repo-local `TemporaryDirectory`; the existing Oak output is read-only until the permitted rerun.
    - External side effects: none in this slice; no network or subprocess.
    - N/A notes: evidence is source, direct parser, unit behavior, and exact artifact validation.
  - Work Steps:
    1. Use the existing presence test (`"skeleton" in skin`) to separate omission from explicit values, retain `_index` for every present value, and derive the unique joint root only when omission is present.
       - UI flow check: N/A; no UI.
       - DB/data flow check: verify the parsed skin mapping is not mutated and no artifact write occurs.
       - Render location check: N/A; no render.
       - Mini QA for each completed implementation slice (MUST): direct Python import/compile and the smallest structural regression command; no browser plugin is applicable.
       - Evidence target: source diff and focused behavior output proving absent/explicit branches.
    2. Re-read the changed function and compare the branch against glTF/P2P hierarchy requirements before testing.
       - UI flow check: N/A; no UI.
       - DB/data flow check: confirm all existing joints, accessor, mesh, and scene checks remain textually and behaviorally present.
       - Render location check: N/A; no render.
       - Mini QA for each completed implementation slice (MUST): `py_compile` plus the direct pre-fix reproduction/retest path.
       - Evidence target: line-level source inspection and no unrelated changed files.
  - Implementation Gate:
    - Before editing, Anvien file-detail and impact evidence for `glb_validator.py` and the focused test file are recorded.
    - P0 artifact evidence proves a valid omitted optional field and coherent inferred root.
    - The edit can be expressed within the existing `_validate_mesh_skin` branch without changing unrelated surfaces.
  - Acceptance:
    - Source: omission is accepted explicitly; present invalid values fail closed; existing rooted hierarchy and structural checks remain.
    - Runtime/UI: N/A; exact runtime validation is P2-A.
    - DB/data: no persistent data writes.
    - Behavior test: focused tests in P1-B pass.
    - Cleanup/quarantine: no generated/artifact files changed.
    - Evidence IDs: `E1-P1A-SRC1..E1-P1A-SRC4`.
    - Actual-status rows refreshed: validator `wrong -> partial/fixed-candidate`; artifact remains `correct/preserve-only`.
  - Evidence Targets: changed source lines, `py_compile`, focused regression result, diff scope, and Anvien detect-changes.
  - Actual-status Update: record the source branch and preserve-only sibling surfaces before beginning P1-B.
  - Commit Boundary: commit after P1-A acceptance if the source-only batch is verified.

- [x] P1-B: Add the narrow skeleton/joints structural regression matrix.
  - Goal: prove omitted and valid skeleton acceptance and fail-closed handling for all directly requested invalid cases.
  - Scope Boundary:
    - Editable: `tests/test_p2p_game_truyen_mpfb_adapter_01.py`, only the GLB fixture/test helpers and `GlbValidationTests` cases.
    - Inspect-only: canonical validator, provenance/recipe helpers, existing adapter/firewall tests, and runtime artifact.
    - Preserve-only: all unrelated adapter, addon, firewall, provenance, and projection tests.
    - Out of scope: broad regression or changes to production code beyond P1-A.
  - Non-Goals: do not test or change later GLB semantics not required by this issue; do not mutate the real Oak artifact.
  - Pre-flight Questions:
    - Data source: temporary in-memory/document fixtures serialized to repo-local temporary files.
    - Display permission: N/A; no UI.
    - DB read flow: N/A; no database.
    - DB write flow: N/A; no database.
    - Render location: N/A; no UI.
    - UI behavior flow: N/A; direct validator behavior.
    - Docker runtime: N/A; no container boundary.
    - Playwright target: N/A; no browser.
    - Behavior test: `GlbValidationTests` pass/fail cases with `validate_glb_output`.
    - Cleanup/quarantine: test `TemporaryDirectory` under the repository; all fixture files disappear after each test.
    - External side effects: none.
    - N/A notes: no persistent state or external process is touched.
  - Work Steps:
    1. Extend only the existing fixture helper to represent omitted, valid, null, negative, out-of-range, non-integer, empty-joint, and invalid-joint documents.
       - UI flow check: N/A; no UI.
       - DB/data flow check: assert fixture-only writes stay under the test temporary directory.
       - Render location check: N/A; no render.
       - Mini QA for each completed implementation slice (MUST): run the focused `GlbValidationTests` class immediately.
       - Evidence target: test names, fixture behavior, and fail-closed reason codes.
    2. Retain the existing valid explicit-skeleton and missing-attribute/resource tests, then run compile and the directly affected test classes.
       - UI flow check: N/A; no UI.
       - DB/data flow check: no real runtime artifact or protected path is used.
       - Render location check: N/A; no render.
       - Mini QA for each completed implementation slice (MUST): focused unittest/pytest output and `git diff --check`.
       - Evidence target: complete focused matrix and unchanged sibling test behavior.
  - Implementation Gate:
    - P1-A source behavior is present and no test is written to encode `None` as omission.
    - Each requested pass/fail case maps to an observable validator result.
  - Acceptance:
    - Source: only directly affected tests/helpers change.
    - Runtime/UI: N/A; runtime is P2.
    - DB/data: temporary fixture isolation passes.
    - Behavior test: omitted and valid explicit skeleton pass; null, negative, out-of-range, non-integer, empty joints, and invalid joint fail closed; existing direct structural tests remain.
    - Cleanup/quarantine: temporary roots are cleaned.
    - Evidence IDs: `E1-P1B-TEST1..E1-P1B-TEST4`.
    - Actual-status rows refreshed: focused test matrix `partial -> complete`.
  - Evidence Targets: test output, source/test line references, compile/diff checks, and detect-changes.
  - Actual-status Update: record the verified matrix and advance P2-A only if P1 is fully accepted.
  - Commit Boundary: commit after P1-B acceptance as the focused-test checkpoint.

### P2: Exact artifact revalidation and one real runtime continuation

- Phase Goal: prove the source candidate against the exact existing Oak artifact first, then perform at most one canonical real rerun if the first gate is clean.
- Phase Boundary:
  - In scope: read-only exact artifact validation, provenance/hash confirmation, one existing-environment runtime rerun, cleanup and stop-law evidence.
  - Out of scope: any second source repair, new validator, new artifact generation before P2-A, Game Truyen, broad QA, release, or promotion.
  - Dependencies: P1-A and P1-B focused source/test checkpoints pass.
- Phase Implementation Rule: do not implement `P2` directly. Execute P2-A, refresh status, then execute P2-B only if its gate is satisfied.
- Ordered Slice List:
  - P2-A: Validate the exact existing Oak GLB with the candidate source.
  - P2-B: Run exactly one canonical real MPFB2 continuation and stop at the first different blocker.

- [x] P2-A: Validate the exact existing Oak GLB with the candidate source.
  - Goal: demonstrate `EXISTING_OAK_GLB_VALIDATION=PASS` without changing existing GLB bytes.
  - Scope Boundary:
    - Editable: repo-local evidence/actual-status ledgers only.
    - Inspect-only: exact external runtime artifact, sidecar, recipe, candidate validator, provenance, and preserved runtime sources.
    - Preserve-only: all runtime directories and all existing GLB bytes.
    - Out of scope: Blender/MPFB2 rerun until this gate passes.
  - Non-Goals: do not regenerate or rewrite Oak.glb; do not treat the validation result as proof of visual quality or browser integration.
  - Pre-flight Questions:
    - Data source: exact Oak GLB, sidecar, recipe, and candidate source.
    - Display permission: N/A; no UI.
    - DB read flow: N/A; no database.
    - DB write flow: N/A; evidence only.
    - Render location: N/A; no render.
    - UI behavior flow: N/A; direct validator call.
    - Docker runtime: N/A; existing Blender runtime is not a container.
    - Playwright target: N/A; no browser in this structural gate.
    - Behavior test: direct `validate_glb_output` call with `load_recipe`.
    - Cleanup/quarantine: no artifact mutation; hashes before and after must match.
    - External side effects: none; no Blender or network.
    - N/A notes: record all required structural fields and provenance status.
  - Work Steps:
    1. Run the candidate validator against the existing exact Oak GLB and normalized recipe/sidecar, recording the result and unchanged hash.
       - UI flow check: N/A; no UI.
       - DB/data flow check: compare exact artifact hash/size before and after.
       - Render location check: N/A; no render.
       - Mini QA for each completed implementation slice (MUST): direct real-artifact validator invocation.
       - Evidence target: `EXISTING_OAK_GLB_VALIDATION`, provenance, hash, and no-write proof.
    2. Stop immediately if any structural error other than the optional-skeleton blocker remains; otherwise refresh actual-status for P2-B.
       - UI flow check: N/A; no UI.
       - DB/data flow check: verify no sidecar/recipe/artifact changes.
       - Render location check: N/A; no render.
       - Mini QA for each completed implementation slice (MUST): independent JSON-chunk structural check and exact output inventory.
       - Evidence target: full structural matrix and explicit rerun gate decision.
  - Implementation Gate:
    - P1 focused tests pass, candidate source is committed, and the exact Oak hash matches the expected value.
    - No pre-existing or new structural blocker besides the proven optional omission remains.
  - Acceptance:
    - Source: candidate validator is the one invoked.
    - Runtime/UI: N/A; no rerun yet.
    - DB/data: external artifact remains byte-identical.
    - Behavior test: `EXISTING_OAK_GLB_VALIDATION=PASS`.
    - Cleanup/quarantine: no runtime cleanup needed; no writes occurred.
    - Evidence IDs: `E2-P2A-ARTIFACT1..E2-P2A-ARTIFACT4`.
    - Actual-status rows refreshed: exact artifact validation `blocked -> pass-gate`.
  - Evidence Targets: direct output, before/after hash, structural checks, and rerun authorization decision.
  - Actual-status Update: mark P2-B runnable only if every P2-A gate passes.
  - Commit Boundary: no source commit; ledger refresh is recorded with the next implementation checkpoint.

- [ ] P2-B: Run exactly one canonical real MPFB2 continuation and stop at the first different blocker.
  - Goal: continue the existing real sequence once after validator proof and capture honest end-to-end evidence.
  - Scope Boundary:
    - Editable: repo-local evidence/actual-status/coder report; runtime output may be produced only by the authorized single rerun.
    - Inspect-only: existing Blender/MPFB2 environment, adapter, entrypoint, firewall, provenance, and Game Truyen boundary.
    - Preserve-only: `windows_network_isolation.py`, addon lifecycle, pin/version, adapter security boundary, provenance model, Game Truyen.
    - Out of scope: any fix after the first new blocker, reinstall, second rerun, visual/browser QA, release, or promotion.
  - Non-Goals: do not claim full PASS if a different downstream blocker appears; do not hide cleanup failure or substitute synthetic output.
  - Pre-flight Questions:
    - Data source: existing runtime manifest, exact recipe, existing Blender/MPFB2 installation, runtime logs, output, sidecar.
    - Display permission: N/A; no UI acceptance claim.
    - DB read flow: N/A; no database.
    - DB write flow: runtime-local output only, bounded by existing adapter cleanup.
    - Render location: N/A; visual quality is not claimed.
    - UI behavior flow: N/A; no browser flow.
    - Docker runtime: N/A; existing Windows/Blender process is the canonical runtime.
    - Playwright target: N/A; no browser claim is in scope.
    - Behavior test: exactly one real runtime sequence through firewall -> Blender -> MPFB2 -> character -> GLB -> provenance -> structural validation -> cleanup.
    - Cleanup/quarantine: require firewall cleanup and undeclared-output cleanup evidence; preserve exact runtime receipt.
    - External side effects: one authorized local Blender subprocess and its bounded runtime-local output; no reinstall or external publication during the rerun.
    - N/A notes: stop at first different downstream blocker.
  - Work Steps:
    1. Rebind the existing runtime manifest, exact recipe, output root, Blender executable, MPFB2 pin, and security boundary immediately before the one spawn.
       - UI flow check: N/A; no UI.
       - DB/data flow check: verify output inventory is empty/clean according to the existing adapter contract before spawn.
       - Render location check: N/A; no render claim.
       - Mini QA for each completed implementation slice (MUST): inspect exact preflight/receipt markers.
       - Evidence target: firewall setup/order, Blender/MPFB2 identity, recipe/output bindings.
    2. Execute once, validate provenance and GLB structure, then clean up on every exit path; stop at full PASS or the first different blocker.
       - UI flow check: N/A; no UI.
       - DB/data flow check: capture output path/hash/sidecar and cleanup receipt without touching Game Truyen.
       - Render location check: N/A; no visual QA.
       - Mini QA for each completed implementation slice (MUST): inspect final runtime receipt, output inventory, firewall rule count, and Game Truyen fingerprint.
       - Evidence target: `REAL_RERUN_EXECUTED`, new output/provenance/hash, structural result, firewall sequence/cleanup, and stop verdict.
  - Implementation Gate:
    - P2-A is PASS and exact source/artifact hashes are bound.
    - Existing firewall/addon/adapter surfaces are unchanged and the runtime manifest is valid.
    - This is the one and only permitted real rerun for this workstream.
  - Acceptance:
    - Source: no runtime/security source changes.
    - Runtime/UI: one real sequence is evidenced; no browser claim.
    - DB/data: runtime-local output/provenance are hash-bound and cleanup is recorded.
    - Behavior test: full PASS or first genuine next blocker is recorded exactly.
    - Cleanup/quarantine: firewall cleanup and output cleanup pass, or the run is reported blocked.
    - Evidence IDs: `E2-P2B-RUN1..E2-P2B-RUN6`.
    - Actual-status rows refreshed: runtime `blocked -> pass` or `blocked -> next-blocker-found`.
  - Evidence Targets: runtime manifest, process receipt/logs, output/provenance checks, firewall receipt, cleanup, immutability fingerprint, and stop-law verdict.
  - Actual-status Update: record no second attempt and no remediation for any new blocker.
  - Commit Boundary: commit final evidence/report updates only after the single rerun and detect-changes review.

- [ ] Pn-A: Call supervisor for the implemented-plan acceptance loop.
  - Goal: independently verify the completed plan work against the exact artifact, source diff, focused tests, runtime receipt, stop law, and preserved boundaries.
  - Work Steps:
    1. Call the supervisor skill to review the full completed plan work.
    2. If supervisor fails the work, return only to the responsible implementation slice; do not broaden scope or rerun MPFB2 automatically.
    3. Re-run supervisor review after any required bounded correction.
    4. Repeat until supervisor passes or records a real blocker.
  - Implementation Gate: all runnable planned slices are completed or explicitly blocked with evidence.
  - Acceptance: supervisor review passes, or the plan records a blocker with no false closure.
- [ ] Pn-B: Remove dead work created during this plan.
  - Goal: ensure the final candidate contains only the validator fix, direct tests, required ledgers/reports, and evidence that still serves Issue 55.
  - Work Steps:
    1. Review the final diff/status and remove only dead artifacts created by this plan.
    2. Preserve rejected evidence and the exact existing-artifact proof; do not delete runtime history or unrelated owner work.
    3. Call supervisor to review cleanup.
  - Implementation Gate: only plan-created dead work is considered; no broad cleanup.
  - Acceptance: no second validator, exporter workaround, stale placeholder, or unrelated source change remains.
- [ ] Pn-C: Close the plan.
  - Goal: finish validation, evidence, benchmark, detect-changes, commit, and final status without converting technical PASS into approval/promotion.
  - Work Steps:
    1. Run final non-UI compile and focused validation required for this scope.
    2. Record exact candidate SHA/tree, report links, and any PR metadata only after the candidate subject is fixed.
    3. Run Anvien detect-changes before the implementation commit/closure commit.
    4. Record final evidence, benchmark measurements, and worktree state.
    5. Commit the completed scope and verify the worktree state.
  - Implementation Gate: Pn-A and Pn-B pass or record blockers.
  - Acceptance: final evidence is recorded, the worktree/subject is known, and the terminal verdict is either `P2_MPFB2_GLB_SKIN_VALIDATION_PASS` or `P2P_MPFB2_GLB_SKIN_NEXT_BLOCKER_FOUND`.

## Risk Notes

- The full repository root supplied to the task is not a valid Git checkout; all source work is isolated in a fresh canonical clone/worktree. The owner snapshot is not repaired or mutated.
- Anvien does not index the hidden `.p2p` source when run at the full package root, so the capability subtree is analyzed separately with a custom repository registration; the evidence records that limitation rather than treating missing links as zero risk.
- The existing GLB is external to the source repository and must remain hash-bound. Any hash drift before P2-A blocks the run.
- The P2P rooted-skeleton rule is stronger than the optional glTF `skeleton` property. It is retained intentionally and is checked using the hierarchy when the field is omitted.
- A real rerun may expose a new downstream blocker. The stop law forbids fixing it in Issue 55.
