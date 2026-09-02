# Supervisor Report: P2P MPFB2 GLB Skin Validation 01

Verdict: PASS

## Metadata

- Report file: `reports/supervisor/rp_supervisor_260902_085526_by_gpt-5-codex_p2p-mpfb2-glb-skin-validation-01.md`
- Review time: `260902 085526 +07:00`
- Reviewer: `gpt-5-codex`
- Repo/project: `7roger89-web/P2P-upgrade-github-1`
- Scope reviewed: Issue 55 candidate from canonical main through the bounded GLB source/test fix, exact existing-artifact gate, and one pre-spawn runtime stop
- Claim reviewed: the first `GLB_skeleton: index invalid` blocker is correctly resolved without artifact mutation, while a different runtime-integrity blocker is reported without retry or repair
- Authority used: current user request, repository `AGENTS.md`, Issue 55 plan/ledgers, Khronos glTF 2.0 schema/spec, source diff, focused tests, exact Oak artifact, and fresh Anvien evidence
- Related artifacts: coder report, Issue 55 plan/evidence/benchmark/actual-status, exact Oak GLB/provenance, runtime manifest, and candidate commits

## Executive Summary

- Problem: the validator indexed `skin.get("skeleton")` unconditionally, so an omitted optional glTF property became `None` and failed as `GLB_skeleton: index invalid`.
- Decision: the bounded structural claim passes. The source distinguishes omitted from explicit values, keeps fail-closed explicit validation, retains rooted hierarchy/connectivity, and the exact Oak artifact validates with no byte/hash mutation.
- Required outcome: accept the bounded GLB validator/test result. The full real MPFB2 continuation remains blocked before spawn by the existing provisioning-root hash mismatch; this is the terminal Issue 55 result, not a hidden PASS.

## Source-Level Clearance Notes

- `.p2p/system/p2p_capabilities/glb_validator.py:137-174`: clear for the reviewed GLB invariant. Lines 137-140 retain required non-empty joint and range checks. Lines 141-149 distinguish property presence, retain `_index` for present values, derive one root for omission, and reject a non-root/multiple-root hierarchy. Lines 151-174 retain connected traversal and JOINTS_0/WEIGHTS_0 accessor/component/normalization checks. No second validator or artifact postprocessor exists.
- `tests/test_p2p_game_truyen_mpfb_adapter_01.py:87-110,577-640`: clear for direct regression coverage. A private sentinel preserves omitted-vs-null distinction; the existing explicit valid skeleton test remains; direct null/negative/out-of-range/non-integer and empty/invalid-joint cases fail closed.
- `.p2p/system/p2p_capabilities/mpfb_adapter.py`, `mpfb_blender_entrypoint.py`, `windows_network_isolation.py`, `asset_provenance.py`, and `character_recipe.py`: clear and preserved. The candidate diff contains no changes to these production surfaces.
- Existing Oak artifact and Game Truyen boundary: clear and preserved. Oak bytes/hash were unchanged during P2-A; the one P2-B attempt failed before process spawn and did not access Game Truyen.

## Evidence Checked

Passed:

- Fresh canonical fetch bound `main` to `c8f4449977987a3288717f9a462dae8967f7246d` and tree `c8ce1ec46ed3399341b38817c5b138604fee1ac2`.
- Direct binary JSON-chunk inspection of `Oak.glb` found `SKIN_COUNT=1`, `SKIN_0_HAS_SKELETON_PROPERTY=False`, raw value `ABSENT`, `SKIN_0_JOINT_COUNT=53`, `NODE_COUNT=55`, and `SKIN_REFERENCING_NODES=53:0`.
- Independent artifact checks found all joints in range and scene-reachable, one coherent inferred root `52`, valid `inverseBindMatrices=46` with `MAT4` count `53`, and valid paired `JOINTS_0`/`WEIGHTS_0` accessors.
- Khronos source confirms `skin.joints` is required, `skin.skeleton` is optional, explicit skeleton values are glTF IDs, and common-root/ancestor semantics apply when present.
- Pre-fix candidate reproduction was exact: `GLB_skeleton: index invalid`.
- Focused `GlbValidationTests` rerun passed `6/6` methods, including all requested subcases. Capability/test `compileall` and `git diff --check` passed.
- Candidate validation of the exact existing Oak returned `STRUCTURALLY_VALID`; provenance/recipe/hash checks passed; artifact size `9,093,808` and SHA-256 `5f96f86fbfd4cdc01201e767b0383807ac5e2a7a6365252aee568a91a949c0c4` were unchanged.
- Fresh Anvien capability-subtree review: `glb_validator.py` has 55 current symbols, 21 local relationships, one linked validation flow, and the `_validate_mesh_skin` impact is LOW with one directly affected file/process. The full package graph's hidden `.p2p` omission is recorded as a limitation, not treated as proof of no relationships.
- Candidate diff from canonical contains exactly the validator, direct test, Issue 55 plan/ledgers, coder report, and notes log. Preserved runtime/security source diff count is `0`.

Failed:

- The one permitted real continuation did not reach execution. `build_execution_plan()` failed closed before firewall setup and `Popen` with `MPFB_PROVISIONING_ROOT_HASH_MISMATCH`: computed `10ebf09a8b425f6e1081f9624ccf9365e471522b01527820e89d27b20de705bf`, manifest-recorded `f6907ef03674ddc995e8b0fdd988e9a003cad61df0d4f707e2a7aaeda4d4e788`.
- This failure is a separate existing-runtime integrity blocker. It is not attributed to the GLB source fix and was not repaired.

Not run:

- No second real runtime attempt, runtime-root reconciliation, reinstall, GLB regeneration, exporter change, firewall setup, or new downstream repair was run after the pre-spawn blocker.
- No broad regression suite, browser QA, visual acceptance, release, deployment, merge, or promotion was claimed.

Verification freshness: fresh/current for the candidate source, exact artifact, focused tests, Anvien graph, and one runtime preflight attempt. Historical Issue 52 evidence was used only as context and was superseded for the skeleton-property classification by the current JSON-chunk parse.

## Invariant Closure

- affected invariant: glTF skin structural validation and the intentional P2P rooted-skeleton policy.
- sibling surfaces checked: `_validate_mesh_skin`, `validate_glb_output`, direct `GlbValidationTests`, recipe/provenance dependencies, adapter caller, Blender entrypoint, firewall helper, exact Oak output, runtime manifest, and Game Truyen boundary.
- residual unverified same-invariant surfaces: none for the Issue 55 GLB structural invariant. The later real runtime is not silently accepted; it is blocked by the separately reported provisioning-root integrity mismatch.

## Overall Evaluation

The bounded implementation is accepted. It fixes the real validator defect without weakening required joints, explicit-index fail-closed behavior, or rooted hierarchy checks, and it proves the fix against the exact existing Oak GLB. The end-to-end terminal status remains `P2P_MPFB2_GLB_SKIN_NEXT_BLOCKER_FOUND` because the only allowed real continuation stopped before spawn on an existing MPFB2 provisioning-root mismatch. The evidence does not support a full runtime PASS.
