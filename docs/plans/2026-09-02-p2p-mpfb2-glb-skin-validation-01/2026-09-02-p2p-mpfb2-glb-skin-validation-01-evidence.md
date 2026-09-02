# P2P-MPFB2-GLB-SKIN-VALIDATION-01 Evidence Ledger

## Metadata

- Date: `2026-09-02`
- Plan: `docs/plans/2026-09-02-p2p-mpfb2-glb-skin-validation-01/2026-09-02-p2p-mpfb2-glb-skin-validation-01-plan.md`
- Evidence: `docs/plans/2026-09-02-p2p-mpfb2-glb-skin-validation-01/2026-09-02-p2p-mpfb2-glb-skin-validation-01-evidence.md`
- Benchmark: `docs/plans/2026-09-02-p2p-mpfb2-glb-skin-validation-01/2026-09-02-p2p-mpfb2-glb-skin-validation-01-benchmark.md`
- Actual status: `docs/plans/2026-09-02-p2p-mpfb2-glb-skin-validation-01/2026-09-02-p2p-mpfb2-glb-skin-validation-01-actual-status.md`

## Evidence Rules

The evidence file explains why the work is known to be correct.

- Evidence is fresh, exact-subject, and tied to a command, source line, artifact, or runtime receipt.
- Direct artifact parsing is independent of the canonical validator.
- A test PASS does not replace source inspection, artifact hash binding, or runtime proof.
- Existing historical reports are context only; current artifact/source evidence controls Issue 55.
- All temporary test roots remain under the repository; the real Oak GLB and Game Truyen are preserve-only until the permitted rerun.

### Evidence ID Naming

Evidence IDs use the required phase-scoped format:

```text
E<phase>-<item>-<kind><n>
```

## E0 - P0 Evidence

Matching plan item(s): `P0-A`

- `E0-P0A-REMOTE1`: Fresh fetch from `https://github.com/7roger89-web/P2P-upgrade-github-1.git` resolved `main` to `c8f4449977987a3288717f9a462dae8967f7246d`; `HEAD^{tree}` is `c8ce1ec46ed3399341b38817c5b138604fee1ac2`.
- `E0-P0A-ARTIFACT1`: `D:\AI\P2P_runtime\mpfb2-runtime-01\output\Oak.glb` exists, has 9,093,808 bytes, and SHA-256 `5f96f86fbfd4cdc01201e767b0383807ac5e2a7a6365252aee568a91a949c0c4`.
- `E0-P0A-ARTIFACT2`: Direct GLB header/chunk parse found glTF container version 2, matching declared/actual length, one skin, 53 joints, 55 nodes, and only `nodes[53].skin = 0`.
- `E0-P0A-ARTIFACT3`: Direct JSON distinction is conclusive: `skins[0]` has no `skeleton` key; raw classification is `ABSENT`, not JSON `null` and not an invalid integer.
- `E0-P0A-ARTIFACT4`: Independent structural checks pass for required/non-empty/range-valid joints, 55/55 scene reachability, reachable joints, valid skin reference, one inferred joint root `52`, common-root connectivity, `inverseBindMatrices=46` with `MAT4` count 53, and valid `JOINTS_0`/`WEIGHTS_0` accessors.
- `E0-P0A-SPEC1`: Khronos glTF 2.0 specification and `skin.schema.json` establish that `joints` is required, `skeleton` is optional, and an explicit skeleton must be a valid node ID satisfying the common-root/ancestor rule. `inverseBindMatrices` count is greater than or equal to joints and type `MAT4`.
- `E0-P0A-CONTRACT1`: The local Asset Forge Protocol intentionally requires a rooted skeleton in the P2P character adapter contract; this is preserved as a policy check, not mistaken for a requirement that the optional glTF property be present.
- `E0-P0A-SRC1`: Canonical source `.p2p/system/p2p_capabilities/glb_validator.py:137-143` requires non-empty joints, then unconditionally calls `_index(skin.get("skeleton"), ...)`, proving omission is treated as an invalid value.
- `E0-P0A-SRC2`: Existing `.p2p/system/p2p_capabilities/glb_validator.py:145-156` performs rooted connectivity from the selected skeleton and must remain active; P1-A will select an inferred root only for omitted-property cases.
- `E0-P0A-SRC3`: Existing `.p2p/system/p2p_capabilities/glb_validator.py:158-174` retains primitive attribute/accessor/component/normalization checks; no weakening is authorized.
- `E0-P0A-REPRO1`: Current validator invocation with `character_recipe.load_recipe()` reproduces `GlbStructuralError: GLB_skeleton: index invalid` against the exact existing Oak GLB.
- `E0-P0A-GRAPH1`: Anvien fresh package analysis completed with 1,118 files scanned and zero parse failures; hidden `.p2p` capability code was not exposed as a package file node.
- `E0-P0A-GRAPH2`: Separate Anvien capability-subtree analysis completed with 127 files scanned and 125 parsed; `file-detail glb_validator.py` reports 54 symbols, 21 local relationships, one linked validation flow, and zero related file rows in that isolated projection.
- `E0-P0A-IMPACT1`: Anvien impact on `_validate_mesh_skin` reports one directly affected source file and one validation process with LOW blast-radius risk in the capability-subtree graph; source file risk remains high and the hidden import boundary is recorded as an analyzer limitation.
- `E0-P0A-TESTGRAPH1`: Anvien `file-detail` for `tests/test_p2p_game_truyen_mpfb_adapter_01.py` reports 139 symbols and 143 local relationships; existing test coverage has an explicit skeleton pass but no omitted/null/invalid skeleton matrix.
- `E0-P0A-HISTORY1`: The prior Issue 52 supervisor report is consumed as a historical pointer only. It correctly stopped before repair but called the field `null`; current direct parsing supersedes that stale classification and proves omission.
- `E0-P0A-WORKFLOW1`: `scripts/p2p_workflow.py inspect` classifies Issue 55 as a bounded `DIRECT TASK` with no Goal required; no setup question or scope expansion was made.

## E1 - P1 Evidence

Matching plan item(s): `P1-A`, `P1-B`

- `E1-P1A-SRC1`: `.p2p/system/p2p_capabilities/glb_validator.py:141-149` now distinguishes key presence from omission, uses `_index` for every present skeleton value, derives exactly one joint root for omission, and retains the existing connected-subgraph check.
- `E1-P1A-SRC2`: `py_compile` passed for `glb_validator.py`; direct candidate invocation with the normalized existing Oak recipe returned `STRUCTURALLY_VALID` with `scene_reachable_nodes=55` and the expected Oak hash.
- `E1-P1A-SRC3`: Source inspection confirms `GLB_SKIN_JOINTS_INVALID`, all node/mesh/skin/joint index checks, `GLB_skeleton_child` traversal, JOINTS_0/WEIGHTS_0 accessor/component checks, and resource validation remain present and unchanged outside the selected branch.
- `E1-P1A-SRC4`: Fresh Anvien detect-changes on the capability subtree reports exactly one changed file, the validator hunk at lines 141-148, LOW changed-file risk, and no changed symbols or affected process files; `git diff --check` passed.
- `E1-P1B-TEST1`: Pending omitted-skeleton and valid-present-skeleton PASS cases.
- `E1-P1B-TEST2`: Pending explicit null, negative, out-of-range, and non-integer FAIL cases.
- `E1-P1B-TEST3`: Pending empty-joints and invalid-joint FAIL cases.
- `E1-P1B-TEST4`: Pending focused compile/test/diff result and temporary-root cleanup proof.

## E2 - P2 Evidence

Matching plan item(s): `P2-A`, `P2-B`

- `E2-P2A-ARTIFACT1`: Pending exact candidate validator run against existing Oak.glb.
- `E2-P2A-ARTIFACT2`: Pending unchanged Oak.glb size and SHA-256 after validation.
- `E2-P2A-ARTIFACT3`: Pending exact provenance and recipe/hash validation result.
- `E2-P2A-ARTIFACT4`: Pending explicit gate decision for the one permitted real rerun.
- `E2-P2B-RUN1`: Pending preflight bindings and firewall-before-spawn receipt.
- `E2-P2B-RUN2`: Pending Blender/MPFB2/character/export stage markers.
- `E2-P2B-RUN3`: Pending new GLB/provenance/hash and structural result.
- `E2-P2B-RUN4`: Pending firewall cleanup and output cleanup result.
- `E2-P2B-RUN5`: Pending Game Truyen immutability fingerprint.
- `E2-P2B-RUN6`: Pending full-PASS or first-different-blocker stop verdict; no second fix.

## Closure Evidence

- `E3-P3A-SUP1`: Pending independent supervisor report for Issue 55.
- `E3-P3B-CLEAN1`: Pending dead-work review and final diff scope.
- `E3-P3C-CLOSE1`: Pending final candidate SHA/tree, detect-changes output, commit, and PR metadata if published.
