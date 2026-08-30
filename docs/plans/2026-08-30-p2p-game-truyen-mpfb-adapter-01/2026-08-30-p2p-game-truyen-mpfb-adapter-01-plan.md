# P2P Game Truyen MPFB Adapter 01 Plan

## Metadata

- Date: `2026-08-30`
- Status: `P1/P2-A complete; P2-B Supervisor review pending`
- Plan: `docs/plans/2026-08-30-p2p-game-truyen-mpfb-adapter-01/2026-08-30-p2p-game-truyen-mpfb-adapter-01-plan.md`
- Evidence: `docs/plans/2026-08-30-p2p-game-truyen-mpfb-adapter-01/2026-08-30-p2p-game-truyen-mpfb-adapter-01-evidence.md`
- Benchmark: `docs/plans/2026-08-30-p2p-game-truyen-mpfb-adapter-01/2026-08-30-p2p-game-truyen-mpfb-adapter-01-benchmark.md`
- Actual status: `docs/plans/2026-08-30-p2p-game-truyen-mpfb-adapter-01/2026-08-30-p2p-game-truyen-mpfb-adapter-01-actual-status.md`

## Goal

Implement the minimum P2P-owned, fail-closed execution adapter contract for the
selected MPFB2 2.0.17 -> built-in GameEngine rig/skin -> Blender glTF 2.0 ->
GLB -> Three.js GLTFLoader lane. The lane must define and validate recipes,
asset rights provenance, bounded invocation semantics, and GLB structural
outputs without installing or executing Blender/MPFB2 and without modifying
Game Truyen.

## Rules

- Complete P0 actual status before implementation work.
- Update each checklist item immediately when it is completed.
- Record evidence as work completes.
- Record benchmarkable counts or measurements when they are taken.
- Update later phase status assumptions, next actions, and work steps when actual-status evidence changes the repo state.
- After completing a phase or implementation slice and refreshing `actual-status.md`, update the next affected phase's work steps as needed to match the latest repo reality, while preserving that phase's original goal, scope, acceptance criteria, and major phase order.
- Run Anvien detect-changes before every implementation-slice commit when implementation work was performed.
- For this non-UI adapter lane, validate changed behavior at its nearest real boundary; no Game Truyen runtime or browser QA is authorized.
- Do not run Docker or substitute a dev server for the explicitly non-runtime, non-UI lane.
- Keep the standard planner structure. These detail rules only make phase checklist items concrete enough to implement safely.
- Every implementation phase must be decomposed into multiple implementation slices that are as small as practical.
- Hidden fallback is forbidden. Invalid recipes, rights gaps, unsafe paths, missing outputs, and unproven execution must fail closed.
- Tests use temporary in-repo roots and synthetic GLB fixtures only; they must not mutate release ZIPs, v5, immutable baseline, or user projects.
- Do not install or execute Blender/MPFB2, generate a Golden Character, modify Game Truyen, promote, release, deploy, or publish.

## Problem

The existing Asset Forge catalog maps broad character generation to
`game.character.generate`, but its MPFB2 candidate is stale and records no exact
release/tree, code-versus-asset license split, or core-asset-only policy. P2P
has no bounded recipe schema, provenance validator, Blender command contract,
or structural GLB validator for this selected lane. The existing img2threejs
adapter is a sibling security precedent and must remain unchanged.

## Scope

- Fresh canonical `origin/main` binding and exact MPFB2 v2.0.17 provenance.
- One P2P-side MPFB adapter module with command construction, containment,
  minimal environment, network-deny declaration, timeout/process-tree contract,
  and execution refusal unless separately authorized.
- One allowlisted parametric recipe validator with unknown-key rejection.
- One asset provenance validator and schema for CORE_CC0-only inputs.
- One GLB/glTF 2.0 structural validator and provenance/output binding.
- Existing Asset Forge catalog, existing `game.character.generate` metadata,
  and selective projection pointers only; no new registry/router/projection.
- Focused unit tests and evidence/report artifacts.

## Non-Goals

- Blender/MPFB2 installation, provisioning, or execution.
- Golden Character generation or six-view image reconstruction.
- Game Truyen source, assets, runtime, Character Lab, or browser changes.
- Reopening or comparing replacement character stacks.
- Third-party asset clearance; third-party assets remain denied by default.
- New registry, router, projection engine, generic shell executor, or release.
- Visual match, execution pass, browser GLTFLoader pass, animation quality, or
  production readiness claims.

## Requirements

- Exact MPFB2 v2.0.17 commit/tree and GPLv3 code / CC0 1.0 core-asset split.
- `VISUAL_REFERENCE_PACK` remains review-only and is not an executable input.
- `PARAMETRIC_CHARACTER_RECIPE` is machine-readable, allowlisted, and rejects
  unknown keys, unsafe asset identifiers, and undeclared assets.
- Every referenced asset has ASSET_ID, SOURCE, LICENSE, SHA256, COMMERCIAL_USE,
  DERIVATIVE_USE, and REDISTRIBUTION fields.
- `CORE_CC0_ONLY` is enforced; unmanifested third-party and custom assets fail.
- Blender invocation is explicit, background-only, uses one allowlisted P2P
  entrypoint, `shell=False`, explicit output root, bounded job workspace,
  symlink/reparse rejection, minimal environment, no inherited secrets, network
  deny contract, timeout, process-tree termination, and undeclared-output fail.
- Required output is `<character_id>.glb` plus
  `<character_id>.asset-provenance.json`.
- GLB validation requires glTF 2.0, scene, mesh, skin, JOINTS_0, WEIGHTS_0,
  rooted skeleton, GameEngine rig expectation, and embedded/hash-bound resources.
- Projection is selective and reuses `game.character.generate`, existing router,
  existing registry, and existing project/profile metadata.

## Acceptance Criteria

- Fresh-main SHA/tree and MPFB release SHA/tree are recorded and independently
  reproducible from Git metadata.
- Focused tests prove happy and fail-closed paths for recipe, rights, path,
  argv, environment, timeout contract, GLB structure, and projection metadata.
- No Blender/MPFB process ran, no Game Truyen path changed, and no upstream
  source was vendored.
- Compile/parse and `git diff --check` pass; affected Anvien change detection
  is captured before each implementation checkpoint.
- One clean bounded candidate is frozen and independently reviewed by Supervisor
  against the exact candidate subject. Technical readiness remains separate from
  Owner approval/promotion.

## Checklist

- [x] P0-A: Complete actual status before implementation work.
  - Goal: establish the real current state and exact external binding.
  - Work Steps: verify fresh canonical main, inspect existing catalog/registry/router/projection seams, resolve MPFB2 tag to commit/tree/license files, inspect sibling adapter security behavior, and record every target surface as correct, partial, missing, or blocked.
  - Implementation Gate: `actual-status.md` contains baseline evidence IDs, relationship counts where Anvien can resolve them, the invariant family map, and a downstream decision before any production edit.
  - Acceptance: P0 is complete with no unresolved authority conflict; implementation is allowed only for the bounded P1 slices below.

### P1: Bounded adapter contract implementation

- Phase Goal: create the smallest P2P-side executable contract and structural validators without external execution.
- Phase Boundary:
  - In scope: recipe/provenance/GLB validators and MPFB command-plan adapter.
  - Out of scope: actual Blender/MPFB runtime, Game Truyen, browser QA, provisioning, and promotion.
  - Dependencies: fresh-main and MPFB exact binding from P0; existing registry and catalog remain the authority.
- Phase Implementation Rule: do not implement `P1` directly. Implement `P1-A`, verify it, record evidence, refresh actual-status, commit when required, then continue to `P1-B`.
- Ordered Slice List:
  - P1-A: Recipe, asset provenance, and pinned binding contracts
  - P1-B: Bounded Blender command-plan and process policy
  - P1-C: GLB structural/output validation

- [x] P1-A: Recipe, asset provenance, and pinned binding contracts
  - Goal: define the machine-readable character recipe and enforce core CC0 provenance without treating images as executable input.
  - Scope Boundary:
    - Editable: new recipe/provenance modules and schema/fixture files; selected existing catalog/registry metadata only after impact evidence.
    - Inspect-only: visual reference packs, Game Truyen, existing img2threejs source, external MPFB audit checkout.
    - Preserve-only: existing router, canonical identities, registry architecture, and prior img2threejs security semantics.
    - Out of scope: any asset download, vendor snapshot, Blender/MPFB execution, or output generation.
  - Non-Goals: no image parser, automatic reconstruction, third-party asset approval, or Game Truyen projection write.
  - Pre-flight Questions:
    - Data source: existing Asset Forge catalog plus exact MPFB LICENSE files and user-provided selected stack.
    - Display permission: N/A; no UI is changed.
    - DB read flow: N/A; validators consume explicit JSON mappings/files.
    - DB write flow: N/A; only isolated test artifacts may be created.
    - Render location: N/A; no UI/render.
    - UI behavior flow: N/A; this is a non-UI contract.
    - Docker runtime: N/A; no app/runtime change and Docker is not authorized.
    - Playwright target: N/A; no browser claim is made.
    - Behavior test: valid recipe -> normalized validated recipe; invalid/unknown/third-party recipe -> explicit rejection.
    - Cleanup/quarantine: all temporary roots are under repo-local `.tmp`; tests use `TemporaryDirectory` under that root and remove/quarantine outputs.
    - External side effects: none; upstream audit is read-only metadata/source inspection.
    - N/A notes: visual reference pack is represented only as a non-executable contract note.
  - Work Steps:
    1. Add the recipe schema/constants and validator with exact allowlists for character_id, body/proportions, base, material, hair, clothing, rig, scale, export, and asset references.
       - UI flow check: N/A; prove no UI surface is touched.
       - DB/data flow check: prove input mapping -> validator -> normalized immutable mapping and no persistent external write.
       - Render location check: N/A; prove no renderer is invoked.
       - Mini QA for each completed implementation slice (MUST)
          For Codex: When Mini QA must use plugins
            - Browser: Control the in-app browser
            - Chrome: Control the user's real Chrome browser
            - Computer Use: Control Windows apps or installed artifacts when mini QA requires real app interaction outside a browser.
            - Playwright: use as an automation arm for browser actions, control sweeps, screenshots, videos, traces, and reports.
          For Claude or other agents:
            - Use the equivalent browser, Chrome/session, or computer-control capability exposed by that agent/runtime or Playwright-like capability available in that environment.
       - Evidence target: focused recipe tests and schema parse/hash evidence.
    2. Add provenance records/schema and update only the existing MPFB catalog/registry metadata to point at the pinned external binding and selective adapter contract.
       - UI flow check: N/A; verify existing project/profile routing remains the only projection surface.
       - DB/data flow check: prove catalog/registry parse and canonical identity/quorum count are unchanged.
       - Render location check: N/A.
       - Mini QA for each completed implementation slice (MUST)
          For Codex: When Mini QA must use plugins
            - Browser: Control the in-app browser
            - Chrome: Control the user's real Chrome browser
            - Computer Use: Control Windows apps or installed artifacts when mini QA requires real app interaction outside a browser.
            - Playwright: use as an automation arm for browser actions, control sweeps, screenshots, videos, traces, and reports.
          For Claude or other agents:
            - Use the equivalent browser, Chrome/session, or computer-control capability exposed by that agent/runtime or Playwright-like capability available in that environment.
       - Evidence target: catalog/registry tests, exact upstream metadata, and no-new-registry proof.
  - Implementation Gate:
    - Before editing target files, run the relevant Anvien impact/file-detail command for files, symbols, routes, tools, or contracts touched by this slice, and record the evidence IDs.
    - P0 actual status is complete; exact MPFB binding and core-asset license evidence are recorded.
  - Acceptance:
    - Source: new validators are dependency-free, deterministic, and do not import Blender/MPFB.
    - Runtime/UI: N/A; no runtime/UI is claimed.
    - DB/data: registry remains valid with canonical denominator 8 and no new registry/router.
    - Behavior test: valid and invalid recipe/provenance cases pass expected outcomes.
    - Cleanup/quarantine: test roots stay within repo-local `.tmp` and are cleaned.
    - Evidence IDs: `E1-P1A-SRC1..E1-P1A-TEST1`.
    - Actual-status rows refreshed: recipe, provenance, catalog binding, registry preservation.
  - Evidence Targets: source lines, exact hashes, focused test output, and diff scope.
  - Actual-status Update: mark recipe/provenance `missing -> correct`; catalog/registry `partial -> bound-correct` only after tests pass.
  - Commit Boundary: commit after this slice when acceptance passes.

- [x] P1-B: Bounded Blender command-plan and process policy
  - Goal: define an allowlisted, network-denied, containment-bound Blender invocation that refuses execution by default in this lane.
  - Scope Boundary:
    - Editable: new adapter module and direct tests.
    - Inspect-only: existing img2threejs adapter and host/projection modules.
    - Preserve-only: existing adapter semantics and canonical execution architecture.
    - Out of scope: process invocation in this task, provisioning, install, network enablement, and Game Truyen.
  - Non-Goals: no generic shell, arbitrary Python file, implicit download, or real subprocess.
  - Pre-flight Questions:
    - Data source: validated recipe/provenance plus explicit preprovisioned absolute Blender/MPFB roots.
    - Display permission: N/A.
    - DB read flow: N/A.
    - DB write flow: N/A; bounded job workspace only.
    - Render location: N/A.
    - UI behavior flow: N/A.
    - Docker runtime: N/A; no runtime change.
    - Playwright target: N/A.
    - Behavior test: plan -> exact argv/env/policy; unauthorized execute -> refusal; unsafe workspace/path -> refusal.
    - Cleanup/quarantine: isolated job workspace under repo-local `.tmp`, no output outside explicit root.
    - External side effects: no process starts; fake runner tests only inspect contract semantics.
    - N/A notes: timeout/process-tree behavior is tested through injected fake process semantics, not a Blender run.
  - Work Steps:
    1. Implement explicit command-plan creation with `--background`, one allowlisted P2P entrypoint, `--`, recipe path, explicit output root, and fixed policy fields.
       - UI flow check: N/A.
       - DB/data flow check: prove plan input -> argv/env mapping and no persisted state mutation.
       - Render location check: N/A.
       - Mini QA for each completed implementation slice (MUST)
          For Codex: When Mini QA must use plugins
            - Browser: Control the in-app browser
            - Chrome: Control the user's real Chrome browser
            - Computer Use: Control Windows apps or installed artifacts when mini QA requires real app interaction outside a browser.
            - Playwright: use as an automation arm for browser actions, control sweeps, screenshots, videos, traces, and reports.
          For Claude or other agents:
            - Use the equivalent browser, Chrome/session, or computer-control capability exposed by that agent/runtime or Playwright-like capability available in that environment.
       - Evidence target: exact argv, `shell=False`, minimal env, no-secret inheritance, network-deny tests.
    2. Add default-deny authorization, timeout/process-tree termination contract, output declaration checks, and explicit receipts that distinguish planned/blocked from executed.
       - UI flow check: N/A.
       - DB/data flow check: prove unauthorized execution returns blocked without spawning or writing.
       - Render location check: N/A.
       - Mini QA for each completed implementation slice (MUST)
          For Codex: When Mini QA must use plugins
            - Browser: Control the in-app browser
            - Chrome: Control the user's real Chrome browser
            - Computer Use: Control Windows apps or installed artifacts when mini QA requires real app interaction outside a browser.
            - Playwright: use as an automation arm for browser actions, control sweeps, screenshots, videos, traces, and reports.
          For Claude or other agents:
            - Use the equivalent browser, Chrome/session, or computer-control capability exposed by that agent/runtime or Playwright-like capability available in that environment.
       - Evidence target: no-process execution refusal and fake-runner timeout semantics.
  - Implementation Gate:
    - Before editing target files, run the relevant Anvien impact/file-detail command for files, symbols, routes, tools, or contracts touched by this slice, and record the evidence IDs.
    - The adapter cannot be reached through a generic registry/router path and default authorization is false.
  - Acceptance:
    - Source: no shell string, unrestricted Python entrypoint, inherited secret, or network enablement exists.
    - Runtime/UI: N/A; real Blender/MPFB execution remains not run.
    - DB/data: no external persistence or project mutation.
    - Behavior test: plan construction and unauthorized/unsafe/timeout paths pass.
    - Cleanup/quarantine: no test artifact escapes repo-local `.tmp`.
    - Evidence IDs: `E1-P1B-SRC1..E1-P1B-TEST1`.
    - Actual-status rows refreshed: adapter command policy and execution authority.
  - Evidence Targets: source inspection, focused security tests, compile output, and no-execution proof.
  - Actual-status Update: mark adapter contract `missing -> correct`; execution authorization remains `blocked/not authorized` by design.
  - Commit Boundary: commit after this slice when acceptance passes.

- [x] P1-C: GLB structural/output validation
  - Goal: refuse structurally incomplete GLB/provenance outputs while proving only adapter output readiness.
  - Scope Boundary:
    - Editable: new GLB/output validator and synthetic fixture tests.
    - Inspect-only: Three.js/GLTFLoader boundary and Game Truyen.
    - Preserve-only: downstream runtime ownership and no Game Truyen source change.
    - Out of scope: browser loading, visual QA, animation QA, and generated character assets.
  - Non-Goals: no claim of visual resemblance or actual MPFB export.
  - Pre-flight Questions:
    - Data source: synthetic GLB fixtures following the glTF 2.0 binary container contract and validated provenance.
    - Display permission: N/A.
    - DB read flow: N/A.
    - DB write flow: N/A; fixture files only.
    - Render location: N/A.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A; Three.js smoke is future and unauthorized.
    - Behavior test: valid structural fixture -> pass; missing scene/skin/attributes/root/resources -> fail closed.
    - Cleanup/quarantine: all synthetic fixtures are temporary or test-local and are not shipped assets.
    - External side effects: none.
    - N/A notes: independent GLTFLoader/browser validation is explicitly future.
  - Work Steps:
    1. Implement GLB chunk/header/JSON validation and structural traversal for scene, mesh, skin, JOINTS_0, WEIGHTS_0, and rooted skeleton.
       - UI flow check: N/A.
       - DB/data flow check: prove GLB bytes -> parser -> structural result with no mutation.
       - Render location check: N/A.
       - Mini QA for each completed implementation slice (MUST)
          For Codex: When Mini QA must use plugins
            - Browser: Control the in-app browser
            - Chrome: Control the user's real Chrome browser
            - Computer Use: Control Windows apps or installed artifacts when mini QA requires real app interaction outside a browser.
            - Playwright: use as an automation arm for browser actions, control sweeps, screenshots, videos, traces, and reports.
          For Claude or other agents:
            - Use the equivalent browser, Chrome/session, or computer-control capability exposed by that agent/runtime or Playwright-like capability available in that environment.
       - Evidence target: positive and one-defect-per-required-structure tests.
    2. Bind output filename, GLB SHA256, provenance SHA256, GameEngine rig expectation, and embedded/hash-bound resources; add future Three.js boundary metadata without touching Game Truyen.
       - UI flow check: N/A.
       - DB/data flow check: prove output validator consumes explicit files and never writes project state.
       - Render location check: N/A.
       - Mini QA for each completed implementation slice (MUST)
          For Codex: When Mini QA must use plugins
            - Browser: Control the in-app browser
            - Chrome: Control the user's real Chrome browser
            - Computer Use: Control Windows apps or installed artifacts when mini QA requires real app interaction outside a browser.
            - Playwright: use as an automation arm for browser actions, control sweeps, screenshots, videos, traces, and reports.
          For Claude or other agents:
            - Use the equivalent browser, Chrome/session, or computer-control capability exposed by that agent/runtime or Playwright-like capability available in that environment.
       - Evidence target: output contract tests, no Game Truyen diff, and downstream claim boundary.
  - Implementation Gate:
    - Before editing target files, run the relevant Anvien impact/file-detail command for files, symbols, routes, tools, or contracts touched by this slice, and record the evidence IDs.
    - P1-A and P1-B have passed and actual-status rows are refreshed.
  - Acceptance:
    - Source: parser is bounded and dependency-free.
    - Runtime/UI: N/A; no GLTFLoader/browser execution.
    - DB/data: no project mutation.
    - Behavior test: complete structure passes; each required omission fails closed.
    - Cleanup/quarantine: synthetic fixtures are contained and removed/quarantined.
    - Evidence IDs: `E1-P1C-SRC1..E1-P1C-TEST1`.
    - Actual-status rows refreshed: GLB structural contract and downstream boundary.
  - Evidence Targets: parser source, fixture results, exact hashes, and Game Truyen unchanged proof.
  - Actual-status Update: mark output validation `missing -> correct`; downstream runtime proof remains `not authorized/not run`.
  - Commit Boundary: commit after this slice when acceptance passes.

### P2: Catalog/projection evidence and independent closure

- Phase Goal: align existing P2P catalog/projection metadata and package exact evidence without creating a second architecture.
- Phase Boundary:
  - In scope: existing catalog/registry pointers, contract docs, evidence/report artifacts, focused tests.
  - Out of scope: promotion, release, deployment, Game Truyen, and live forge execution.
  - Dependencies: all P1 slices complete.
- Phase Implementation Rule: do not implement `P2` directly. Implement `P2-A`, verify it, record evidence, refresh actual-status, commit when required, then continue to P2-B.
- Ordered Slice List:
  - P2-A: Selective projection/catalog reconciliation and focused closure tests
  - P2-B: Exact-subject Supervisor review and owner-gate handoff

- [x] P2-A: Selective projection/catalog reconciliation and focused closure tests
  - Goal: expose the adapter through the existing `game.character.generate` projection metadata while preserving one registry/router/projection architecture.
  - Scope Boundary:
    - Editable: only selected catalog/registry/protocol/test/report files required by this lane.
    - Inspect-only: existing routing implementation and project profile surfaces unless tests prove a metadata pointer is required.
    - Preserve-only: canonical identities, quorum, existing img2threejs record, and all Game Truyen files.
    - Out of scope: any promotion or external execution.
  - Non-Goals: no activation, install, or visual validation.
  - Pre-flight Questions:
    - Data source: existing P2P Asset Forge catalog and registry.
    - Display permission: N/A.
    - DB read flow: N/A.
    - DB write flow: N/A.
    - Render location: N/A.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: existing router/catalog discovery -> selected metadata only; no second registry/router.
    - Cleanup/quarantine: no persistent test mutation outside isolated roots.
    - External side effects: none.
    - N/A notes: Owner approval and runtime execution remain absent.
  - Work Steps:
    1. Run focused catalog/registry/projection tests and add only the direct assertions needed for MPFB pin, rights, projection metadata, and readiness distinctions.
       - UI flow check: N/A.
       - DB/data flow check: prove catalog -> existing registry/router reads only.
       - Render location check: N/A.
       - Mini QA for each completed implementation slice (MUST)
          For Codex: When Mini QA must use plugins
            - Browser: Control the in-app browser
            - Chrome: Control the user's real Chrome browser
            - Computer Use: Control Windows apps or installed artifacts when mini QA requires real app interaction outside a browser.
            - Playwright: use as an automation arm for browser actions, control sweeps, screenshots, videos, traces, and reports.
          For Claude or other agents:
            - Use the equivalent browser, Chrome/session, or computer-control capability exposed by that agent/runtime or Playwright-like capability available in that environment.
       - Evidence target: focused tests, Anvien detect-changes, compile, and diff check.
  - Implementation Gate:
    - Before editing target files, run the relevant Anvien impact/file-detail command for files, symbols, routes, tools, or contracts touched by this slice, and record the evidence IDs.
    - P1 status is refreshed and no shared runtime surface requires broad regression.
  - Acceptance:
    - Source: metadata is selective and references existing catalog/router/registry only.
    - Runtime/UI: N/A; no project runtime.
    - DB/data: no persistent external mutation.
    - Behavior test: projection discovery and no-duplication assertions pass.
    - Cleanup/quarantine: isolated tests clean.
    - Evidence IDs: `E2-P2A-SRC1..E2-P2A-TEST1`.
    - Actual-status rows refreshed: projection readiness and Game Truyen isolation.
  - Evidence Targets: tests, change detection, compile, diff, and exact candidate identity.
  - Actual-status Update: mark projection `missing -> ready-selective`; keep execution/visual/G1 claims not run.
  - Commit Boundary: commit after this slice when acceptance passes.

- [ ] P2-B: Exact-subject Supervisor review and owner-gate handoff
  - Goal: independently review the frozen candidate against all requested boundaries and stop at Owner gate.
  - Scope Boundary:
    - Editable: review report and evidence only; no code repair during Supervisor review.
    - Inspect-only: exact candidate subject, source, tests, reports, hashes, and external binding.
    - Preserve-only: candidate implementation and no Game Truyen mutation.
    - Out of scope: approval execution, promotion, release, deployment, and forge execution.
  - Non-Goals: no visual or downstream runtime PASS.
  - Pre-flight Questions:
    - Data source: exact candidate SHA/tree and upstream MPFB SHA/tree.
    - Display permission: N/A.
    - DB read flow: N/A.
    - DB write flow: N/A.
    - Render location: N/A.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: exact-subject independent source/test/evidence sweep.
    - Cleanup/quarantine: report artifacts stay in repo-local reports.
    - External side effects: no approval/promotion action.
    - N/A notes: Supervisor must explicitly confirm no Blender/MPFB execution.
  - Work Steps:
    1. Call Supervisor to inspect the exact candidate and write PASS or REJECT report; if REJECT, return only the failed implementation slice for a separate fix/review round.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: N/A.
       - Mini QA for each completed implementation slice (MUST)
          For Codex: When Mini QA must use plugins
            - Browser: Control the in-app browser
            - Chrome: Control the user's real Chrome browser
            - Computer Use: Control Windows apps or installed artifacts when mini QA requires real app interaction outside a browser.
            - Playwright: use as an automation arm for browser actions, control sweeps, screenshots, videos, traces, and reports.
          For Claude or other agents:
            - Use the equivalent browser, Chrome/session, or computer-control capability exposed by that agent/runtime or Playwright-like capability available in that environment.
       - Evidence target: Supervisor report bound to candidate SHA/tree.
  - Implementation Gate:
    - All P1/P2-A acceptance evidence is present and candidate identity is frozen.
  - Acceptance:
    - Source: Supervisor independently verifies exact source and boundaries.
    - Runtime/UI: Supervisor confirms no runtime/visual claim was made.
    - DB/data: Supervisor confirms no Game Truyen/project mutation.
    - Behavior test: Supervisor confirms focused tests are direct and current.
    - Cleanup/quarantine: worktree and reports are auditable.
    - Evidence IDs: `E2-P2B-REVIEW1`.
    - Actual-status rows refreshed: candidate review and terminal verdict.
  - Evidence Targets: exact-subject Supervisor report and owner-gate handoff.
  - Actual-status Update: `ready-selective -> READY_FOR_OWNER_GATE` only after Supervisor PASS; never mark canonical promoted.
  - Commit Boundary: review artifacts are committed separately only if required by the review workflow.

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
    1. Run the required final validation for the accepted scope, including full build before final runtime validation. For app/runtime scopes, full build must include Docker image/container build.
    2. Start the real built Docker/container runtime for app/runtime validation. If Docker cannot be built or started, record the blocker and do not substitute a host dev server.
    3. Validate public runtime or UI-facing changes with browser or Playwright evidence against the real built Docker/container runtime. Playwright evidence must include Docker build/run or compose command, container/service name, exposed URL, Playwright command, and screenshot/trace/result.
    4. Regenerate generated outputs if source-of-truth changes require it.
    5. Run Anvien detect-changes before commit when implementation work was performed.
    6. Record final validation, detect-changes, benchmark, and commit evidence.
    7. Commit the completed scope and verify the worktree state.
  - Implementation Gate: Pn-A and Pn-B must pass or record blockers.
  - Acceptance: final evidence is recorded, required commits exist, and the worktree state is known.

## Risk Notes

- The original requested path has an incomplete `.git`; the candidate must remain in the fresh isolated worktree derived from the verified canonical clone.
- MPFB2 exact binding is external and not vendored. A future provisioning process must separately verify Blender, MPFB2, and core assets before any execution.
- GPLv3 applies to MPFB tool code; the upstream LICENSE.md explicitly separates bundled CC0 assets and does not claim control over MPFB output. This lane records provenance and does not provide legal advice.
- `ADAPTER_PASS`, `EXECUTION_PASS`, `VISUAL_MATCH_PASS`, and `GOLDEN_CHARACTER_PASS` are independent claims.
- The only final implementation verdict allowed here is `P2P_GAME_TRUYEN_MPFB_ADAPTER_01_READY_FOR_OWNER_GATE` after exact Supervisor PASS; otherwise report `REJECTED` or `BLOCKED` honestly.
