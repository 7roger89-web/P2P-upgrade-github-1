# Coder Report: P2P-MPFB2-GLB-SKIN-VALIDATION-01

Date: 2026-09-02 08:51:41 +07:00
Role: WRITER_AND_REAL_ARTIFACT_INVESTIGATOR
Repository: `7roger89-web/P2P-upgrade-github-1`
Issue: `55`
Workstream: `P2P-MPFB2-GLB-SKIN-VALIDATION-01`
Base: `c8f4449977987a3288717f9a462dae8967f7246d`
Base tree: `c8ce1ec46ed3399341b38817c5b138604fee1ac2`
Branch: `workstream/p2p-mpfb2-glb-skin-validation-01-candidate`

## Result

The requested first GLB blocker is resolved in the canonical validator. The exact existing Oak GLB is structurally valid after the candidate source fix, without any artifact mutation. Omitted `skin.skeleton` is accepted explicitly; present null, negative, out-of-range, and non-integer values fail closed. Required joints, scene/mesh/skin references, rooted hierarchy/connectivity, JOINTS_0/WEIGHTS_0, accessors, resources, provenance, and output naming remain guarded.

The one permitted real runtime continuation was attempted after the exact-artifact gate and stopped before Blender spawn at a different existing-environment blocker: `MPFB_PROVISIONING_ROOT_HASH_MISMATCH`. No retry, reinstall, runtime-root repair, second GLB fix, or second real run was performed.

## Invariant Family Map

| Family | Authority / SSOT | Sibling surfaces checked | Result |
|---|---|---|---|
| glTF skin structure | Khronos glTF 2.0 skin schema/spec and exact Oak JSON chunk | `glb_validator.py`, direct GLB fixture tests, Oak scene/joint/accessor hierarchy | Omitted optional field handled; explicit invalid values fail closed; Oak passes |
| P2P rooted skeleton | `docs/p2p-development/capability-catalog/protocols/asset-forge-protocol.md` | `_validate_mesh_skin` root selection and connectivity traversal | Intentional rooted policy preserved; accidental rejection of nested joints corrected |
| Mesh/accessor structural validation | Existing `glb_validator.py` contract | joints, node/mesh/skin index checks, primitive attributes, resource checks | Preserved; no unrelated branch removed |
| Provenance/data boundary | `asset_provenance.py`, `character_recipe.py`, existing runtime sidecar | Oak sidecar, normalized recipe, GLB hash | Preserved and exact Oak validation PASS |
| Runtime/security boundary | `mpfb_adapter.py`, `mpfb_blender_entrypoint.py`, `windows_network_isolation.py` | candidate diff and single gated runtime attempt | No source changes; runtime stopped before firewall/spawn on preflight integrity mismatch |
| Product immutability | user stop law | Game Truyen external boundary | No access or mutation |

## Legacy fallback status

No fallback was added. `skin.get("skeleton")` is no longer used to infer whether the property exists. The implementation distinguishes key omission from explicit JSON null and malformed values. No exporter or postprocessor was introduced.

## Files changed

Production source:

- `.p2p/system/p2p_capabilities/glb_validator.py:141-149`

Direct tests:

- `tests/test_p2p_game_truyen_mpfb_adapter_01.py:87-110,577-640`

Workflow evidence:

- `docs/plans/2026-09-02-p2p-mpfb2-glb-skin-validation-01/`
- this coder report

Preserved and unchanged:

- `.p2p/system/p2p_capabilities/windows_network_isolation.py`
- `.p2p/system/p2p_capabilities/mpfb_adapter.py`
- `.p2p/system/p2p_capabilities/mpfb_blender_entrypoint.py`
- `.p2p/system/p2p_capabilities/asset_provenance.py`
- `.p2p/system/p2p_capabilities/character_recipe.py`
- Game Truyen
- `D:\AI\P2P_runtime\mpfb2-runtime-01\output\Oak.glb`

## Source checkpoint

- Plan checkpoint: `e25c1d2`
- Validator checkpoint: `4bcc26a`
- Focused-test checkpoint: `3e4f0e8`
- Exact-artifact gate checkpoint: `335ca7a`
- Candidate HEAD at report time: `335ca7ad57b2d51ff456af29427143b5f848a112`
- Candidate tree at report time: `448713c171f107cc821f64db948ff4b7eba8f767`
- Candidate diff from canonical base contains exactly the validator, direct test, and Issue 55 plan/ledger files.

## Verification evidence

### Canonical and artifact

- Fresh remote fetch: `main = c8f4449977987a3288717f9a462dae8967f7246d`; tree `c8ce1ec46ed3399341b38817c5b138604fee1ac2`.
- Existing artifact: `D:\AI\P2P_runtime\mpfb2-runtime-01\output\Oak.glb`.
- Artifact SHA-256: `5f96f86fbfd4cdc01201e767b0383807ac5e2a7a6365252aee568a91a949c0c4` — exact expected match.
- Direct JSON chunk: `SKIN_COUNT=1`, `SKIN_0_HAS_SKELETON_PROPERTY=False`, `SKIN_0_SKELETON_RAW_VALUE=ABSENT`, `SKIN_0_JOINT_COUNT=53`, `NODE_COUNT=55`, `SKIN_REFERENCING_NODES=53:0`.
- Independent checks: scene reachable nodes `55/55`; every joint index valid and reachable; one inferred joint root `52`; common-root connectivity PASS; `inverseBindMatrices=46` with accessor `MAT4`, count `53`; primitive attributes include a valid `JOINTS_0`/`WEIGHTS_0` pair.
- Khronos glTF 2.0 confirms `joints` required, `skeleton` optional, explicit skeleton IDs non-negative integers, and common-root/ancestor semantics.

### Reproduction and source repair

- Pre-fix direct validator call reproduced `GLB_skeleton: index invalid` against the exact Oak artifact.
- Candidate source at `.p2p/system/p2p_capabilities/glb_validator.py:141-149` uses explicit property-presence branching, derives one root only for omission, retains explicit `_index`, and allows nested joint hierarchy under the preserved rooted policy.
- Candidate direct validation returned `STRUCTURALLY_VALID`, `gltf_version=2.0`, `character_id=Oak`, `scene_reachable_nodes=55`, and the expected hash.
- Anvien capability-subtree `file-detail` and `_validate_mesh_skin` impact were run before editing. The isolated graph reported 54 symbols, 21 local relationships, one linked validation flow, one directly affected source file, and LOW direct blast-radius risk. The full package graph does not index hidden `.p2p` source nodes; this limitation was recorded rather than treated as zero risk.

### Focused tests

- `tests/test_p2p_game_truyen_mpfb_adapter_01.py::GlbValidationTests`: `6/6` methods PASS.
- `test_rigged_glb_requires_glb20_scene_mesh_joints_weights_and_root` covers valid present skeleton PASS.
- `test_omitted_skeleton_is_accepted_without_normalizing_absence` covers omitted property PASS and asserts no `skeleton` key is present in parsed JSON.
- `test_explicit_invalid_skeleton_values_fail_closed` covers explicit `null`, negative, out-of-range, and non-integer values; all fail with `GLB_skeleton: index invalid`.
- `test_empty_or_invalid_joint_indices_fail_closed` covers empty joints and invalid joint index; both fail closed.
- Existing missing JOINTS/resource and hash/output naming tests remain PASS.
- `python -m compileall -q .p2p/system/p2p_capabilities tests/test_p2p_game_truyen_mpfb_adapter_01.py`: PASS.
- `git diff --check`: PASS.
- No broad suite was run after the bounded fix.

### Exact existing-artifact gate

- Candidate validator against the existing exact Oak GLB: PASS.
- `PROVENANCE_VALIDATION=PASS`.
- Artifact hash before/after validation: exact expected SHA both times.
- Artifact size before/after validation: `9,093,808` bytes both times.
- `ARTIFACT_MUTATED_DURING_VALIDATION=NO`.
- `EXISTING_OAK_GLB_VALIDATION=PASS`.

### Single real runtime continuation

- Existing environment bindings passed initial checks: Blender `4.2.23`, MPFB2 `2.0.17`, upstream commit `80919fa4682335c41847f761a4d79dcad4124732`, upstream tree `189a1d6694515ecfbdc40067218c5024389b4e43`, new empty output root, and zero active Blender processes.
- The one canonical adapter continuation failed in `build_execution_plan()` before firewall setup and before `Popen`: `MPFB_PROVISIONING_ROOT_HASH_MISMATCH`.
- Computed MPFB root: `10ebf09a8b425f6e1081f9624ccf9365e471522b01527820e89d27b20de705bf`.
- Recorded manifest root: `f6907ef03674ddc995e8b0fdd988e9a003cad61df0d4f707e2a7aaeda4d4e788`.
- `REAL_BLENDER_CHILD_PID=NOT_CREATED`; no new GLB or sidecar; no firewall lease; P2P firewall rule count afterward `0`.
- Existing Oak hash remained exact; new output root was not created; active Blender process count remained `0`.
- `GAME_TRUYEN_MUTATIONS=NO`.
- Stop law applied: no retry and no repair of this different environment blocker.

## E2E flow

```text
exact Oak JSON -> candidate validator -> STRUCTURALLY_VALID
candidate plan -> existing MPFB root integrity check -> BLOCKED before Popen
```

The GLB structural invariant is closed. The full real runtime claim remains blocked by the existing runtime provisioning manifest/root mismatch.

## Residual unverified surfaces

None for the Issue 55 GLB structural invariant. The later real MPFB2 execution remains explicitly blocked by `MPFB_PROVISIONING_ROOT_HASH_MISMATCH`, which is outside this scope and was not repaired.

## Terminal status

```text
VALIDATOR_DEFECT=YES
ARTIFACT_DEFECT=NO
EXISTING_OAK_GLB_VALIDATION=PASS
REAL_RERUN_EXECUTED=NO
FIRST_DIFFERENT_BLOCKER=MPFB_PROVISIONING_ROOT_HASH_MISMATCH
TERMINAL_VERDICT=P2P_MPFB2_GLB_SKIN_NEXT_BLOCKER_FOUND
```
