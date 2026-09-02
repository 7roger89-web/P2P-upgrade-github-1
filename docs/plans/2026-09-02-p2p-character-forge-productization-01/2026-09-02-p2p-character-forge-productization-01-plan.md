# P2P Character Forge Productization ISSUE 59 Plan

## Metadata

- Date: `2026-09-02`
- Status: `in_progress`
- Plan: `docs/plans/2026-09-02-p2p-character-forge-productization-01/2026-09-02-p2p-character-forge-productization-01-plan.md`
- Evidence: `docs/plans/2026-09-02-p2p-character-forge-productization-01/2026-09-02-p2p-character-forge-productization-01-evidence.md`
- Benchmark: `docs/plans/2026-09-02-p2p-character-forge-productization-01/2026-09-02-p2p-character-forge-productization-01-benchmark.md`
- Actual status: `docs/plans/2026-09-02-p2p-character-forge-productization-01/2026-09-02-p2p-character-forge-productization-01-actual-status.md`

## Goal

Add one beginner-facing, deterministic productization facade over the already
canonical `game.character.generate` MPFB2 route. The facade must accept a small
JSON-shaped `CharacterRequest`, produce a validated internal `CharacterRecipe`,
delegate to the existing Windows-isolated MPFB2 adapter, and return one concise
`CharacterForgeReceipt` without creating a second router, registry, service, or
character framework.

## Rules

- Complete P0 actual status before implementation work.
- Update each checklist item immediately when it is completed.
- Record evidence as work completes.
- Record benchmarkable counts or measurements when they are taken.
- Update later phase status assumptions, next actions, and work steps when actual-status evidence changes the repo state.
- After completing a phase or implementation slice and refreshing `actual-status.md`, update the next affected phase's work steps as needed to match the latest repo reality, while preserving that phase's original goal, scope, acceptance criteria, and major phase order.
- Run Anvien detect-changes before every implementation-slice commit when implementation work was performed.
- This is a native Windows Blender runtime scope with no Docker or browser target; Docker/Playwright checks are `N/A` and must not be substituted with a UI claim.
- Preserve the exact canonical base `0ee414147ae308ab1f6035d1e7776292752bd8da` and tree `f34719776bee67a731c4049b79165bd3deaa3074`.
- Preserve the existing capability identity `game.character.generate`, single router, routing/selection machinery, MPFB2 adapter, Blender entrypoint, provenance model, GLB validator, and Windows firewall isolation.
- Use only a deterministic structured request at the runtime boundary. Natural-language interpretation remains outside this module.
- Reject unknown request keys and any path, command, network, shell, Blender, MPFB2, manifest, or firewall input from the beginner request.
- Treat exact height, exact age-in-years, long/dark hair, and clothing customization as unsupported unless the existing runtime surface proves and executes them. Do not silently claim them.
- Use only the existing MPFB2 `2.0.17` pin, release `80919fa4682335c41847f761a4d79dcad4124732`, tree `189a1d6694515ecfbdc40067218c5024389b4e43`, and `CORE_CC0_ONLY` policy.
- Run exactly one real product smoke after focused source proof. No reinstall, download, retry, second character, upstream edit, or unrelated subsystem repair.
- One Writer branch and one PR are allowed; do not merge. The PR head is not written into source or a committed self-referential bookkeeping file.
- Supervisor review is independent and read/review-only. Stop at `OWNER_GATE` after Supervisor PASS.

## Problem

The canonical MPFB2 route is runtime-proven through the existing adapter and
Windows isolation, but its caller must currently construct the verbose internal
`p2p-character-recipe/1` document and separately interpret adapter output. The
route has no small beginner request contract, deterministic semantic-to-recipe
projection, or product receipt. The existing internal recipe also contains
hair/clothing asset slots that are not executed by the current Blender entrypoint,
and the entrypoint does not bind a physical `height_m` or exact age-in-years
input. Productization must expose only what the real route can honor.

## Scope

- Add one productization module under `.p2p/system/p2p_capabilities/`.
- Define `CharacterRequest`, `CharacterRecipe`, and `CharacterForgeReceipt`.
- Normalize safe defaults and map supported beginner semantics to the existing
  internal recipe contract.
- Reject unsupported material customizations and runtime-control injection.
- Bind the recipe to `mpfb_adapter.build_execution_plan` and
  `mpfb_adapter.execute_plan` without copying execution/security logic.
- Return and validate a receipt containing capability identity, recipe hash,
  output/provenance paths and hashes/statuses, structural validation, rig/skin,
  runtime, and isolation status.
- Add one focused request/recipe/receipt test module and one request JSON schema.
- Execute one real bounded product smoke using the supplied provisioned runtime.
- Record the plan, evidence, benchmark, coder report, independent Supervisor
  report, and one PR without merge.

## Non-Goals

- No NLP parser or natural-language interpreter.
- No second capability identity, registry, router, selection system, or database.
- No changes to `mpfb_adapter.py`, `mpfb_blender_entrypoint.py`,
  `asset_provenance.py`, `glb_validator.py`, `windows_network_isolation.py`,
  or existing routing/selection code unless a direct productization failure
  proves an existing contract must change.
- No exact physical height support, exact age-in-years visual guarantee, hair
  system, hair color customization, clothing system, visual editor, UI,
  marketplace, combat animation, multi-character generation, OpenMontage,
  img2threejs expansion, or Game Truyen integration.
- No upstream MPFB2 changes, dependency installation, Blender installation,
  network widening, manifest rewriting, runtime repair, or output overwrite.
- No release, deployment, merge, or promotion.

## Requirements

### Beginner request contract

The request schema is `p2p-character-request/1` and accepts only:

- `name` (optional identifier; default `Character`)
- `gender` (optional `male`, `female`, or `neutral`; default `neutral`)
- `age_class` (optional `young`, `adult`, or `old`; default `adult`; this is a
  semantic class, not an exact age in years)
- `build` (optional `default`, `slim`, `average`, or `athletic`; default
  `default`)
- `rig` (optional boolean; default `true`, and `false` fails closed)
- `output_format` (optional `glb`; default `glb`)

The following are explicitly classified as `NOT_CURRENTLY_SUPPORTED` and must
fail closed when supplied: `height_m`, exact `age`, `age_years`, `hair`,
`hair_intent`, `hair_color`, `clothing`, and `clothing_intent`. Runtime paths,
commands, network controls, shell controls, manifest hashes, and arbitrary
unknown keys are rejected as request-contract violations.

### Deterministic recipe projection

The facade must call the existing `character_recipe.validate_recipe` contract.
It may only produce the current internal recipe shape and the existing four
`mpfb2-core:*` asset bindings required by the provisioned manifest. Supported
semantic mappings are explicit and stable:

- `gender` maps to `recipe.body.gender`.
- `age_class` maps to a fixed MPFB macro value: `young=0.35`, `adult=0.45`,
  `old=0.75`.
- `build` maps to fixed current-route macro values: `default=(weight=0.50,
  muscle=0.35)`, `slim=(0.25,0.35)`, `average=(0.50,0.50)`, and
  `athletic=(0.45,0.75)`.
- All five internal proportion values remain `1.0`, because the current
  Blender entrypoint requires a uniform proportion value.
- Rig is always `GAMEENGINE` with `MPFB_BUILT_IN_WEIGHTS`; GLB 2.0 embeds
  resources; scale remains the existing neutral `1.0` default.

These values describe deterministic MPFB macro inputs, not a visual or
anthropometric guarantee beyond the existing route.

### Runtime binding and receipt

The runtime binding is P2P-owned internal context, not request data. It carries
the provisioned workspace/executable and fixed relative MPFB2/manifest locations
needed by the existing adapter. The facade must write one temporary recipe file
inside the managed runtime workspace, call the existing adapter, remove only that
recipe file, preserve the two declared durable output files, and never overwrite
an existing output directory.

The receipt must validate:

- `capability_id == game.character.generate`;
- the normalized recipe SHA-256;
- `<character_id>.glb` and matching provenance sidecar paths;
- GLB SHA-256 and provenance/structural status;
- `GAMEENGINE` rig and `MPFB_BUILT_IN_WEIGHTS` skin status;
- adapter runtime status;
- firewall/isolation cleanup status;
- explicit deferred/unsupported field metadata when applicable.

## Acceptance Criteria

- P0 actual status and invariant family map are complete before source edits.
- Focused tests pass for minimal request, safe defaults, semantic determinism,
  adapter binding, receipt validation, invalid height/type/range, unsupported
  format, false rig, unknown/runtime-control keys, and unsupported customization
  fail-closed behavior.
- A valid request reaches the existing adapter boundary; no duplicate execution
  or security logic is introduced.
- Exactly one real product smoke uses `D:\AI\P2P_runtime\mpfb2-runtime-01`
  without reinstall/download/retry and records all requested runtime flags:
  `REAL_BLENDER_CHILD_SPAWNED=YES`, `REAL_MPFB2_EXECUTED=YES`,
  `CHARACTER_CREATED=YES`, `RIG_PRESENT=YES`, `SKIN_PRESENT=YES`,
  `GLB_STRUCTURALLY_VALID=YES`, `PROVENANCE_VALIDATION=PASS`, and
  `FIREWALL_CLEANUP_PASS=YES`.
- The real product receipt validates and points to exactly one GLB plus one
  provenance sidecar; no receipt file is added to the output directory.
- No Game Truyen path is written or changed.
- The candidate remains one Writer branch, one unmerged PR, with exact head/tree
  recorded only after source/evidence commits are complete.
- One independent Supervisor review returns `PASS`; no unresolved same-scope
  surface remains. The terminal next step is `OWNER_GATE`.

## Checklist

- [x] P0-A: Complete actual status before implementation work.
  - Goal: establish the real current state.
  - Work Steps: reconcile fresh canonical main/tree, inspect the full relevant capability SPEC cluster, inspect the existing registry/routing/selection/recipe/adapter/entrypoint/provenance/validator/test surfaces, inspect closed #46/#52/#55/#56 evidence, inspect the provisioned runtime manifest/result, and classify every shared invariant before editing.
  - Implementation Gate: no implementation or editing starts until `docs/plans/2026-09-02-p2p-character-forge-productization-01/2026-09-02-p2p-character-forge-productization-01-actual-status.md` has a final P0 decision.
  - Acceptance: actual status identifies correct, partial, missing/unbound, fake-or-stub, and blocked surfaces for this scope.

### P1: Beginner contract and existing-route facade

- Phase Goal: implement the smallest deterministic facade and prove it locally without launching Blender.
- Phase Boundary:
  - In scope: request normalization, recipe projection, unsupported-field rejection, runtime-owned binding type, receipt construction/validation, request schema, and focused tests.
  - Out of scope: existing adapter/entrypoint/security changes, UI, NLP, exact height/hair/clothing support, upstream/runtime mutation, real smoke, and Game Truyen.
  - Dependencies: P0 complete; existing `game.character.generate` and canonical MPFB2 route are preserved; Anvien impact evidence is current.
- Phase Implementation Rule: do not implement `P1` directly. Implement `P1-A`, verify it, record evidence, refresh actual-status, commit when required, then continue to `P1-B`.
- Ordered Slice List:
  - P1-A: CharacterRequest normalization and CharacterRecipe projection
  - P1-B: Existing MPFB2 binding and CharacterForgeReceipt

- [x] P1-A: CharacterRequest normalization and CharacterRecipe projection
  - Goal: create the beginner contract and deterministic internal recipe projection without executing any runtime.
  - Scope Boundary:
    - Editable: new `.p2p/system/p2p_capabilities/character_forge.py`, new `character.request.schema.json`, and new focused test module after code is correct.
    - Inspect-only: existing recipe schema and `character_recipe.validate_recipe` implementation, capability registry, routing/selection surfaces, upstream MPFB2 macro source.
    - Preserve-only: existing `character_recipe.py`, adapter, entrypoint, provenance, GLB validator, firewall isolation, runtime root, and Game Truyen.
    - Out of scope: execution binding, receipt, Blender, MPFB2, output files, and external publication.
  - Non-Goals: no NLP, path discovery, command construction, cosmetic support, or runtime-side default guessing.
  - Pre-flight Questions:
    - Data source: existing `character_recipe.py`, recipe schema, current MPFB2 `_macro_detail_dict`, and pinned macro target config.
    - Display permission: N/A; no UI/display surface exists.
    - DB read flow: N/A; no database.
    - DB write flow: N/A; no persistent data.
    - Render location: N/A; no UI render.
    - UI behavior flow: N/A; direct Python contract only.
    - Docker runtime: N/A; native Windows Blender is a later runtime target.
    - Playwright target: N/A; no browser/UI change.
    - Behavior test: mapping input -> normalized request -> validated internal recipe -> stable hash.
    - Cleanup/quarantine: tests use repo-local temporary roots and clean them; no runtime root writes.
    - External side effects: none in this slice.
    - N/A notes: all UI/DB/Docker/Playwright rows are N/A because this is a standard-library Python contract slice.
  - Work Steps:
    1. Implement request parsing, explicit defaults, support classification, and the deterministic recipe mapping; validate the result through the existing recipe validator.
       - UI flow check: N/A; confirm no UI code or natural-language parser is introduced.
       - DB/data flow check: N/A; confirm no persistent write.
       - Render location check: N/A; inspect the module boundary only.
       - Mini QA for each completed implementation slice (MUST): run the focused Python contract tests and inspect output for no runtime spawn.
       - Evidence target: `E1-P1A-SRC1`, `E1-P1A-TEST1`, `E1-P1A-TEST2`.
    2. Add the request JSON schema and direct happy/failure tests only after the behavior is correct.
       - UI flow check: N/A; schema is not a UI.
       - DB/data flow check: N/A.
       - Render location check: N/A.
       - Mini QA for each completed implementation slice (MUST): run the exact focused test module and compile the touched Python.
       - Evidence target: `E1-P1A-SCHEMA1`, `E1-P1A-TEST3`.
  - Implementation Gate:
    - Before editing target files, use the fresh Anvien `file-detail`/impact evidence for the reused contract and high-risk sibling files recorded as `E0-P0A-GRAPH1..E0-P0A-GRAPH5`.
    - No current live Supervisor report assigns a higher-priority repair to this Writer lane.
    - Exact supported/unsupported field classification is recorded in the source docstring and plan before implementation.
  - Acceptance:
    - Source: only the new productization module/schema/tests are introduced; protected existing route files remain unchanged.
    - Runtime/UI: no runtime launch; no UI claim.
    - DB/data: no persistent project/database write.
    - Behavior test: minimal/default/deterministic/fail-closed request tests pass.
    - Cleanup/quarantine: test temporary roots are under repo-local `.tmp` and cleaned.
    - Evidence IDs: `E1-P1A-SRC1..E1-P1A-TEST3`.
    - Actual-status rows refreshed: product facade `missing -> partial`; existing route remains `correct`/preserve-only.
  - Evidence Targets: new contract source, schema alignment, focused test output, compile output, and protected-file diff check.
  - Actual-status Update: mark `CharacterRequest`/`CharacterRecipe` as `bound-correct` for local normalization, while execution/receipt remains `missing` for P1-B.
  - Commit Boundary: commit after this slice when acceptance passes.

- [x] P1-B: Existing MPFB2 binding and CharacterForgeReceipt
  - Goal: bind the normalized recipe to the existing adapter and produce a validated concise receipt without duplicating execution/security logic.
  - Scope Boundary:
    - Editable: the new `character_forge.py` and its focused tests; plan/evidence/actual-status files.
    - Inspect-only: existing adapter/entrypoint/provenance/GLB validator and runtime result contract.
    - Preserve-only: existing registry/routing/selection, firewall, MPFB2 source, and Game Truyen.
    - Out of scope: real runtime execution (P2), UI, persistence, and PR publication.
  - Non-Goals: no second process runner, no output validator copy, no receipt sidecar, and no hidden fallback.
  - Pre-flight Questions:
    - Data source: `mpfb_adapter.build_execution_plan`/`execute_plan`, `asset_provenance`, and `glb_validator` results.
    - Display permission: N/A; receipt is a Python return object.
    - DB read flow: N/A.
    - DB write flow: recipe file is a managed test/runtime input and is deleted; no database.
    - Render location: N/A.
    - UI behavior flow: N/A.
    - Docker runtime: N/A; native Windows runtime remains P2.
    - Playwright target: N/A.
    - Behavior test: normalized request -> adapter call -> mocked observable output -> receipt validation.
    - Cleanup/quarantine: mock binding uses repo-local temporary workspace; facade deletes its generated recipe input and never overwrites output.
    - External side effects: none; adapter call is mocked in this slice.
    - N/A notes: no real child or firewall lease is allowed before P2.
  - Work Steps:
    1. Add P2-owned runtime binding and facade invocation that passes only fixed internal paths/policies to the existing adapter.
       - UI flow check: N/A.
       - DB/data flow check: verify recipe input cleanup and no persistent service/database.
       - Render location check: N/A.
       - Mini QA for each completed implementation slice (MUST): run mocked binding tests and inspect adapter call arguments for exact allowlisted paths/policies.
       - Evidence target: `E1-P1B-SRC1`, `E1-P1B-TEST1`.
    2. Add receipt construction, shape validation, status derivation, and failure-path tests.
       - UI flow check: N/A.
       - DB/data flow check: verify output directory is not overwritten and generated recipe input is cleaned.
       - Render location check: N/A.
       - Mini QA for each completed implementation slice (MUST): run focused tests, compile, and diff-check protected surfaces.
       - Evidence target: `E1-P1B-TEST2`, `E1-P1B-TEST3`.
  - Implementation Gate:
    - Reused symbol impact and file-detail evidence is fresh; no existing high-risk protected file needs editing.
    - P1-A focused tests pass and the actual-status file records the P1-B work step as allowed.
  - Acceptance:
    - Source: facade delegates to the existing adapter and existing validators; no duplicate runtime logic.
    - Runtime/UI: no real child; mocked boundary only.
    - DB/data: managed recipe input is cleaned; no service/database.
    - Behavior test: binding and receipt tests pass, including malformed receipt rejection.
    - Cleanup/quarantine: all test roots are repo-local and cleaned; no runtime root touched.
    - Evidence IDs: `E1-P1B-SRC1..E1-P1B-TEST3`.
    - Actual-status rows refreshed: facade `partial -> bound-correct`; real runtime smoke remains `missing` until P2.
  - Evidence Targets: source delegation, adapter call allowlist, receipt validator, test output, and protected-file diff.
  - Actual-status Update: mark local product surface complete and P2 as the only remaining implementation phase.
  - Commit Boundary: commit after this slice when acceptance passes.

### P2: One real product smoke

- Phase Goal: prove the complete product route once against the existing provisioned Windows runtime.
- Phase Boundary:
  - In scope: one supported male/slim/adult or neutral bounded request, one facade call, one real Blender child, one MPFB2 generation, one GLB/provenance result, structural/provenance checks, isolation cleanup, and receipt capture.
  - Out of scope: retry, second character, runtime repair, installation/download, hair/clothing/height expansion, Game Truyen, UI, and unrelated failure repair.
  - Dependencies: P1-B committed and focused tests pass; runtime manifest/root is current; output target is new and empty; exact candidate source is bound.
- Phase Implementation Rule: do not implement `P2` directly. Implement `P2-A`, verify it, record evidence, refresh actual-status, commit evidence when required, then continue to `P2-B`.
- Ordered Slice List:
  - P2-A: Build and execute exactly one real product route
  - P2-B: Independent artifact/isolation cleanup evidence

- [x] P2-A: Build and execute exactly one real product route
  - Goal: run the facade, not the lower-level adapter alone, exactly once.
  - Scope Boundary:
    - Editable: repo-local `.tmp` smoke runner and evidence files only; no production runtime/security source.
    - Inspect-only: supplied runtime manifest, existing runtime assets, and prior result logs.
    - Preserve-only: runtime MPFB2 root, Blender installation, firewall implementation, Game Truyen, and upstream source.
    - Out of scope: any source repair after a new blocker.
  - Non-Goals: no reinstall/download/retry/second character or cosmetic customization.
  - Pre-flight Questions:
    - Data source: committed facade, runtime manifest, and current provisioned root hash.
    - Display permission: N/A; evidence is log/receipt data.
    - DB read flow: N/A.
    - DB write flow: one managed recipe input and durable two-file output under the supplied runtime root.
    - Render location: N/A.
    - UI behavior flow: N/A.
    - Docker runtime: N/A; this is the documented native Windows Blender runtime.
    - Playwright target: N/A.
    - Behavior test: facade call -> real child -> output -> receipt.
    - Cleanup/quarantine: use a new deterministic output directory; facade removes its generated recipe input; adapter owns firewall/process cleanup.
    - External side effects: exactly one real Blender/MPFB2 process and one isolated output.
    - N/A notes: no UI/browser/DB surfaces exist.
  - Work Steps:
    1. Run the full Python compile/build boundary and confirm the new output directory and recipe path are absent/empty before spawning.
       - UI flow check: N/A.
       - DB/data flow check: verify no existing runtime output is eligible for overwrite.
       - Render location check: N/A.
       - Mini QA for each completed implementation slice (MUST): inspect exact preflight output and stop if any precondition fails.
       - Evidence target: `E2-P2A-BUILD1`, `E2-P2A-PREFLIGHT1`.
    2. Execute exactly one facade call with the bounded supported request and capture child PID, product receipt, child output, output hashes, provenance, and validation result.
       - UI flow check: N/A.
       - DB/data flow check: verify exactly one GLB and one sidecar are created.
       - Render location check: N/A.
       - Mini QA for each completed implementation slice (MUST): inspect the product receipt and stop at the first genuine blocker.
       - Evidence target: `E2-P2A-RUN1`, `E2-P2A-ARTIFACT1`.
  - Implementation Gate:
    - P1-B receipt/focused tests pass; runtime manifest exact pin/root is fresh; output target is not present; explicit one-run authorization is active.
  - Acceptance:
    - Source: no production source changes during smoke.
    - Runtime/UI: facade reaches real Blender/MPFB2 and returns receipt; no UI claim.
    - DB/data: exactly two declared output files and no overwrite.
    - Behavior test: product route reaches observable receipt/artifact.
    - Cleanup/quarantine: recipe input removed; adapter isolation context closes.
    - Evidence IDs: `E2-P2A-BUILD1..E2-P2A-ARTIFACT1`.
    - Actual-status rows refreshed: real product smoke `missing -> correct` only if every required flag is proven; otherwise `blocked` and stop.
  - Evidence Targets: build output, preflight, real child PID/log, receipt, artifact hashes, provenance, structural validation, and no-retry stop.
  - Actual-status Update: record exact output paths/hashes and required terminal flags; do not generalize from the previous Oak smoke.
  - Commit Boundary: commit only the smoke runner/evidence/report artifacts after the single run result is known; do not commit runtime outputs.

- [x] P2-B: Independent artifact/isolation cleanup evidence
  - Goal: independently confirm the output/provenance/GLB receipt and post-run process/firewall state.
  - Scope Boundary:
    - Editable: plan/evidence/report/notes only.
    - Inspect-only: real runtime output, result/logs, source diff, and firewall/process state.
    - Preserve-only: all production/runtime sources and Game Truyen.
    - Out of scope: any fix or rerun.
  - Non-Goals: no output rewriting, validator weakening, firewall changes, or second smoke.
  - Pre-flight Questions:
    - Data source: product receipt, existing validators, runtime logs, filesystem hashes, and OS state.
    - Display permission: N/A.
    - DB read flow: N/A.
    - DB write flow: no writes; evidence only.
    - Render location: N/A.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: receipt -> independent artifact/OS checks.
    - Cleanup/quarantine: preserve durable smoke artifact for evidence; confirm no residual process/rules.
    - External side effects: read-only post-run checks.
    - N/A notes: native Windows evidence replaces browser/Docker evidence.
  - Work Steps:
    1. Recompute GLB/provenance hashes, rerun existing validators, check exact output membership, and compare recipe hash with the receipt.
       - UI flow check: N/A.
       - DB/data flow check: verify two-file output contract.
       - Render location check: N/A.
       - Mini QA for each completed implementation slice (MUST): record fresh independent values.
       - Evidence target: `E2-P2B-ARTIFACT1`.
    2. Check active Blender process count, `P2P-MPFB-DENY-*` rule count, runtime-root hash, and no Game Truyen source mutation; write final evidence.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: N/A.
       - Mini QA for each completed implementation slice (MUST): confirm cleanup and exact one-run stop.
       - Evidence target: `E2-P2B-CLEAN1`, `E2-P2B-STOP1`.
  - Implementation Gate:
    - P2-A produced a receipt or a genuine blocker; do not proceed if any required pass flag is missing.
  - Acceptance:
    - Source: protected production/runtime files remain unchanged.
    - Runtime/UI: independent receipt/artifact/OS evidence agrees.
    - DB/data: no undeclared output.
    - Behavior test: receipt and existing validators agree.
    - Cleanup/quarantine: no process/firewall residue and no retry.
    - Evidence IDs: `E2-P2B-ARTIFACT1..E2-P2B-STOP1`.
    - Actual-status rows refreshed: P2 terminal state is PASS or BLOCKED, never inferred.
  - Evidence Targets: independent artifact and cleanup proof, exact stop boundary, and protected-surface diff.
  - Actual-status Update: set terminal readiness for Supervisor review only after all requested flags are current.
  - Commit Boundary: commit evidence/report only after all checks are recorded.

- [ ] Pn-A: Call supervisor for the implemented-plan acceptance loop.
  - Goal: verify the completed plan work against the accepted plan, actual-status decisions, evidence, benchmark, changed files, generated output, and validation results before closure.
  - Work Steps:
    1. Create one independent Supervisor chat and provide the exact candidate head/tree, scope, source diff, focused tests, real product smoke evidence, and protected-surface checks.
    2. If supervisor fails the work, return to the responsible implementation workflow for the failed scope only; do not fix inside the review.
    3. Re-run Supervisor review after any required correction, with a fresh exact subject.
  - Implementation Gate: all planned implementation phases must be completed or explicitly blocked before this review.
  - Acceptance: Supervisor returns `PASS`, residual same-invariant unverified surfaces are none, and the plan stops at Owner Gate.

- [ ] Pn-B: Remove dead work created during this plan.
  - Goal: ensure the final diff contains only artifacts that still serve the accepted productization scope.
  - Work Steps:
    1. Review production source, tests, schema, plan artifacts, reports, and repo-local smoke helpers created by this plan.
    2. Remove only dead artifacts created by this plan; preserve runtime output and prior evidence needed for the receipt/report.
    3. Verify no duplicate capability, parser, runner, validator, generated receipt sidecar, or unrelated change remains.
  - Implementation Gate: only plan-created artifacts may be removed.
  - Acceptance: final status/diff has no dead plan-created artifacts and the cleanup is recorded.

- [ ] Pn-C: Close the plan.
  - Goal: finish validation, evidence, benchmark, detect-changes, commit, PR, and final status.
  - Work Steps:
    1. Run final focused validation and compile/build evidence; do not run unrelated full suites.
    2. Refresh actual-status/evidence/benchmark and run Anvien detect-changes before the final source/evidence commit.
    3. Verify exact canonical parent, candidate head/tree, one remote branch, one PR, and no merge.
    4. Stop at `OWNER_GATE` after Supervisor PASS.
  - Implementation Gate: Pn-A and Pn-B pass or record a genuine blocker.
  - Acceptance: final evidence is recorded, required commits/PR exist, worktree state is known, and terminal verdict is `P2P_CHARACTER_FORGE_PRODUCTIZATION_READY_FOR_OWNER_GATE` or the exact blocker verdict.

## Risk Notes

- The existing adapter, entrypoint, provenance, validator, firewall, and focused
  test file have high or critical graph warnings. They are preserve-only unless
  direct evidence proves a productization defect; the new facade should avoid
  touching them.
- The supplied runtime is external to the Git candidate. Its manifest/root,
  Blender executable, and MPFB2 pin must be rechecked immediately before the one
  run. A failed precondition means no spawn and `STOP_AT_GENUINE_BLOCKER`.
- MPFB2's current macro route controls normalized age/weight/muscle/gender and
  uniform proportions, not exact meters, exact years, hair styling/color, or
  clothing. The product contract must remain honest about this boundary.
- Existing #56 evidence proves one route, not this new facade. The new smoke must
  prove `CharacterRequest -> CharacterRecipe -> facade -> adapter -> Blender ->
  MPFB2 -> artifact -> receipt` with fresh evidence.
- No Docker or browser evidence is applicable; adding a UI to satisfy a generic
  planner rule would be scope expansion.
