# Coder Report — P2P Game Truyen MPFB Adapter 01

## Scope

This report covers the bounded P2P adapter contract for the already-selected
MPFB2 2.0.17 -> built-in GameEngine rig/skin -> Blender glTF 2.0 -> GLB lane.
It adds no character asset, no Game Truyen source, no Blender/MPFB2 runtime,
and no replacement-stack research.

## Invariant family map

| Family | Source of truth | Evidence |
|---|---|---|
| Existing capability identity and projection | `capabilities.json`, Asset Forge catalog, existing profile routing | `E1-P1A-SRC3`, `E2-P2A-SRC1` |
| Recipe input boundary | `character_recipe.py` and checked-in recipe/reference schemas | `E1-P1A-SRC1`, `E1-P1A-TEST1` |
| Asset rights and provenance | `asset_provenance.py`, output manifest schema | `E1-P1A-SRC2`, `E1-P1A-TEST1` |
| Pinned local forge invocation | `mpfb_adapter.py` and provisioning manifest contract | `E1-P1B-SRC1`, `E1-P1B-TEST1` |
| Output structure and resource binding | `glb_validator.py` and provenance manifest | `E1-P1C-SRC1`, `E1-P1C-TEST1` |
| Canonical P2P safety boundary | existing registry/router/projection; sibling img2threejs adapter preserved | `E0-P0A-SRC2`, `E0-P0A-SRC3`, `E2-P2A-SRC1` |

## Implemented changes

- Added strict, dependency-free parametric recipe validation. Unknown keys,
  image fields, invalid identifiers, unsupported rig/skin settings, and
  undeclared asset references fail closed.
- Added exact six-view visual-reference validation as a separate non-executable
  contract.
- Added core-CC0-only asset provenance validation with exact SHA256 and rights
  fields. Third-party and user-custom assets remain rejected.
- Bound the existing MPFB candidate and `game.character.generate` identity to
  MPFB2 v2.0.17, exact release commit/tree, GPL-3.0-or-later tool code, and
  CC0-1.0 core assets.
- Added a command-plan adapter that requires a local hash-verified provisioning
  manifest, explicit `--background` Blender argv, one exact P2P entrypoint,
  path/symlink containment, minimal environment, network deny, timeout, fixed
  process-tree termination, and exact output declarations.
- Added structural GLB 2.0 validation for scene, mesh, skin, `JOINTS_0`,
  `WEIGHTS_0`, rooted skeleton, output/provenance/recipe hashes, and embedded
  or hash-bound resources.
- Added only selective metadata to the existing catalog/registry/projection.
  No second registry, router, projection, executor, or Game Truyen change was
  introduced.

## Verification

- `python -m py_compile` on all four new modules: PASS.
- Focused adapter plus existing Asset Forge tests: `28/28` and `9/9` PASS.
- Registry validation: `65` capabilities, canonical denominator `8`: PASS.
- `git diff --check`: PASS.
- Fresh Anvien analysis: `1071` files scanned, `191` parsed code files,
  `0` parse failures, `54193` relationships. The new test file is parsed with
  `59` symbols and `44` local relationships; Anvien reports a high scope
  warning for the test file, not a prohibition.
- Anvien change detection was run before the implementation checkpoint. Its
  semantic graph reports the targeted catalog/protocol changes and no affected
  runtime process; untracked new files are covered by compile and direct tests.

## Explicit non-claims

- No Blender or MPFB2 installation, provisioning, or execution occurred.
- No Golden Character was generated; six-view reference is not automatic
  MPFB2 reconstruction.
- No Three.js `GLTFLoader`, Character Lab, browser, or visual-match test ran.
- Adapter readiness is not execution-pass, visual-match-pass, or Golden
  Character-pass.
- `execution_authorized` remains false and no promotion/release/deployment was
  attempted.

## Handoff

The bounded implementation is ready for an independent exact-subject
Supervisor review. The review must bind its verdict to the final candidate
SHA/tree and retain the Owner gate, execution-denied, and downstream-future-only
boundaries.
