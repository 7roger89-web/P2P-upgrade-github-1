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
- `E1-P1B-TEST1`: `GlbValidationTests.test_omitted_skeleton_is_accepted_without_normalizing_absence` and the existing valid-present-skeleton test both pass; the omitted fixture asserts the parsed JSON has no `skeleton` key.
- `E1-P1B-TEST2`: `test_explicit_invalid_skeleton_values_fail_closed` passes all four subcases: JSON null, negative index, out-of-range index, and non-integer value, each raising `GLB_skeleton: index invalid`.
- `E1-P1B-TEST3`: `test_empty_or_invalid_joint_indices_fail_closed` passes both subcases: empty joints raises `GLB_SKIN_JOINTS_INVALID`; out-of-range joint raises `GLB_joint: index invalid`.
- `E1-P1B-TEST4`: Focused `GlbValidationTests` run passes `6/6` methods; `compileall` for the capability subtree and focused test passes; `git diff --check` passes; temporary fixture roots are owned by `TemporaryDirectory` and clean on teardown.

## E2 - P2 Evidence

Matching plan item(s): `P2-A`, `P2-B`

- `E2-P2A-ARTIFACT1`: Candidate `validate_glb_output()` run with `load_recipe()` against `D:\AI\P2P_runtime\mpfb2-runtime-01\output\Oak.glb` returned `status=STRUCTURALLY_VALID`, glTF `2.0`, character `Oak`, `scene_reachable_nodes=55`, and the expected GLB SHA-256.
- `E2-P2A-ARTIFACT2`: Artifact bytes and size were compared before and after validation: both hashes are `5f96f86fbfd4cdc01201e767b0383807ac5e2a7a6365252aee568a91a949c0c4`, size `9,093,808`, and `ARTIFACT_MUTATED_DURING_VALIDATION=NO`.
- `E2-P2A-ARTIFACT3`: Candidate validation passed the existing provenance schema, recipe binding, rights/assets binding, and GLB hash binding; output is `PROVENANCE_VALIDATION=PASS`.
- `E2-P2A-ARTIFACT4`: Exact existing-artifact gate is PASS. P2-B is permitted to run exactly once; no Blender execution occurred before this gate.
- `E2-P2B-RUN1`: Preflight bound candidate source `335ca7ad57b2d51ff456af29427143b5f848a112` / tree `448713c171f107cc821f64db948ff4b7eba8f767`, Blender `4.2.23`, MPFB2 `2.0.17`, exact upstream pin/tree, a new absent output root, and zero active Blender processes. Plan construction failed closed before firewall or spawn on `MPFB_PROVISIONING_ROOT_HASH_MISMATCH`.
- `E2-P2B-RUN2`: `REAL_BLENDER_CHILD_PID=NOT_CREATED`; no Blender, MPFB2, character, or export stage marker was produced by the Issue 55 attempt.
- `E2-P2B-RUN3`: `NEW_OUTPUT_PATH=NOT_CREATED`; no new GLB/provenance was created. The existing Oak GLB remains `5f96f86fbfd4cdc01201e767b0383807ac5e2a7a6365252aee568a91a949c0c4`.
- `E2-P2B-RUN4`: Firewall sequence was not reached and no P2P firewall rule was present afterward (`P2P_FIREWALL_RULE_COUNT_AFTER_PRESPAWN_BLOCK=0`); no isolation lease existed to clean up.
- `E2-P2B-RUN5`: The failed pre-spawn attempt did not access Game Truyen and made no protected-project mutation; `GAME_TRUYEN_MUTATIONS=NO`.
- `E2-P2B-RUN6`: First different blocker is `MPFB_PROVISIONING_ROOT_HASH_MISMATCH`: computed root `10ebf09a8b425f6e1081f9624ccf9365e471522b01527820e89d27b20de705bf` versus manifest `f6907ef03674ddc995e8b0fdd988e9a003cad61df0d4f707e2a7aaeda4d4e788`. No retry, runtime-root repair, reinstall, or second fix was performed.

## Closure Evidence

- `E3-P3A-SUP1`: `reports/supervisor/rp_supervisor_260902_085526_by_gpt-5-codex_p2p-mpfb2-glb-skin-validation-01.md` independently reviews the source, focused tests, exact Oak gate, Anvien impact, preserved surfaces, and the pre-spawn runtime blocker; verdict is PASS for the bounded Issue 55 claim and explicitly not full runtime PASS.
- `E3-P3B-CLEAN1`: Final candidate diff contains only `.p2p/system/p2p_capabilities/glb_validator.py`, `tests/test_p2p_game_truyen_mpfb_adapter_01.py`, the Issue 55 plan/ledgers, coder/supervisor reports, and the date notes log. No second validator, exporter workaround, generated GLB, or unrelated runtime/security source remains.
- `E3-P3C-CLOSE1`: Final closure records fresh candidate SHA/tree, detect-changes and diff-scope evidence, focused validation, exact-artifact PASS, the single pre-spawn stop, and the terminal `P2P_MPFB2_GLB_SKIN_NEXT_BLOCKER_FOUND` result. Fresh Anvien compare detection reports 8 candidate files and 7 affected file projections with a high file-risk warning caused by the broad documentation/test topology; direct source scope remains the one validator plus one test file and preserved runtime/security source diff is zero. No PR/promotion is claimed without a separately authorized external publication action.
