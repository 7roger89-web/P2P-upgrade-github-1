# P2P Game Truyen MPFB Adapter 01 Evidence Ledger

## Metadata

- Date: `2026-08-30`
- Plan: `docs/plans/2026-08-30-p2p-game-truyen-mpfb-adapter-01/2026-08-30-p2p-game-truyen-mpfb-adapter-01-plan.md`
- Evidence: `docs/plans/2026-08-30-p2p-game-truyen-mpfb-adapter-01/2026-08-30-p2p-game-truyen-mpfb-adapter-01-evidence.md`
- Benchmark: `docs/plans/2026-08-30-p2p-game-truyen-mpfb-adapter-01/2026-08-30-p2p-game-truyen-mpfb-adapter-01-benchmark.md`
- Actual status: `docs/plans/2026-08-30-p2p-game-truyen-mpfb-adapter-01/2026-08-30-p2p-game-truyen-mpfb-adapter-01-actual-status.md`

## Evidence Rules

The evidence file explains why the work is known to be correct. Evidence is
fresh, exact-subject-bound, and distinguishes source inspection, focused tests,
static contract proof, and absent runtime execution. Tests and reports are not
authority by themselves; the user scope, repository rules, and selected stack
are authority.

### Evidence ID Naming

Use stable, phase-scoped evidence IDs in the format `E<phase>-<item>-<kind><n>`.
No evidence ID is reused for a different fact.

## E0 - P0 Evidence

Matching plan item(s): `P0-A`

- `E0-P0A-GIT1`: fresh fetch from the real P2P remote resolved `origin/main` to SHA `7763ded3476b51acc09bccdfc6cb0c1720f28ba2` and tree `6a4f7dba5ffb86a6e5da6659ba3a0ae09b1a443b`.
- `E0-P0A-GIT2`: the user-requested root has incomplete `.git` metadata and was not used as authority; isolated worktree is derived from the fresh canonical clone.
- `E0-P0A-UP1`: MPFB2 tag `v2.0.17` resolved read-only to commit `80919fa4682335c41847f761a4d79dcad4124732` and tree `189a1d6694515ecfbdc40067218c5024389b4e43`.
- `E0-P0A-UP2`: MPFB `LICENSE.md`, `LICENSE.CODE.md`, and `LICENSE.ASSETS.md` separate GPLv3 code from CC0 1.0 bundled assets and describe output provenance.
- `E0-P0A-SRC1`: existing Asset Forge catalog contains CAND-ASSET-FORGE-002 for MPFB2 but with stale commit/license metadata.
- `E0-P0A-SRC2`: existing registry contains `game.character.generate` as the single selected capability identity; canonical registry validation reports denominator 8 and no second registry/router.
- `E0-P0A-SRC3`: existing `img2threejs_adapter.py` is a preserve-only sibling security precedent; it denies network, uses `shell=False`, bounds paths, and is not modified by this lane.
- `E0-P0A-GRAPH1`: Anvien refreshed the isolated worktree and reported `files=1063`, `parsed_code=190`, `failed=0`, `relationships=53748`; `tests/test_p2p_game_asset_forge_01.py` resolved with 10 local relationships and high scope warning. Hidden `.p2p` file-detail queries were not projected, so those source files are verified by direct inspection plus focused tests.

## E1 - P1 Evidence

Matching plan item(s): `P1-A`, `P1-B`, `P1-C`

- `E1-P1A-SRC1`: `character.recipe.schema.json`, `visual-reference-pack.schema.json`, and `asset-provenance.schema.json` define closed JSON object shapes; executable recipe and six-view visual reference are separate schemas.
- `E1-P1A-SRC2`: `character_recipe.py` recursively rejects unknown keys and image-like recipe fields; `asset_provenance.py` requires exact per-asset identity, source, license, SHA256, commercial/derivative/redistribution fields, and rejects non-`mpfb2-core:` assets.
- `E1-P1A-SRC3`: candidate `CAND-ASSET-FORGE-002` and existing `game.character.generate` metadata now bind MPFB2 v2.0.17 to release SHA `80919fa4682335c41847f761a4d79dcad4124732`, tree `189a1d6694515ecfbdc40067218c5024389b4e43`, code GPL-3.0-or-later, core assets CC0-1.0, and third-party deny-by-default.
- `E1-P1A-TEST1`: recipe/provenance tests pass for valid core assets, unknown fields, visual-reference separation, third-party rejection, custom-asset rejection, and exact recipe asset binding.
- `E1-P1B-SRC1`: `mpfb_adapter.py` constructs one explicit `blender --background --python <exact-entrypoint> -- ...` argv, uses repo-local per-job paths, validates a pinned local provisioning manifest and deterministic provisioned-root hash, and exposes no generic shell/Python route.
- `E1-P1B-TEST1`: adapter tests pass for network deny, traversal, symlink/reparse rejection, minimal environment/no secret inheritance, authorization refusal without `Popen`, output declaration, and fixed shell-free process-tree termination semantics.
- `E1-P1C-SRC1`: `glb_validator.py` parses GLB v2 headers/chunks, walks a scene-reachable mesh/skin, checks `JOINTS_0`/`WEIGHTS_0`, rooted joints, embedded or provenance-bound resources, output naming, and GLB/provenance/recipe hashes.
- `E1-P1C-TEST1`: synthetic GLB tests pass for complete structure, missing joints, unbound external resources, and hash mismatch; no Blender/MPFB process or Game Truyen path was used.

## E2 - P2 Evidence

Matching plan item(s): `P2-A`, `P2-B`

- `E2-P2A-SRC1`: the existing `game.character.generate` capability and existing THREEJS_GAME/R3F_GAME projection remain the only selected surfaces; no second registry, router, or projection was added.
- `E2-P2A-TEST1`: focused adapter plus existing Asset Forge catalog tests pass: 28 tests, registry validation 65 capabilities and canonical quorum denominator 8.
- `E2-P2A-GRAPH1`: after refresh, Anvien reports 1071 files scanned, 191 parsed code files, 0 parse failures, 54175 relationships; new focused test file resolves with 59 symbols and 44 local relationships, high scope warning only.
- `E2-P2A-BOUNDARY1`: Three.js GLTFLoader/Character Lab/browser smoke remains future-only and unauthorized; adapter readiness is not execution, visual-match, or Golden Character readiness.

## Closure Evidence

Final detect-changes, compile, focused tests, diff check, candidate SHA/tree,
worktree state, and independent Supervisor report will be appended here.
