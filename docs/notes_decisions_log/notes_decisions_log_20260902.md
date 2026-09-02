# Notes and Decisions Log — 2026-09-02

## P2P-MPFB2-GLB-SKIN-VALIDATION-01 / Issue 55

- Fresh canonical main: `c8f4449977987a3288717f9a462dae8967f7246d`; tree `c8ce1ec46ed3399341b38817c5b138604fee1ac2`.
- Exact `Oak.glb` SHA-256 matched `5f96f86fbfd4cdc01201e767b0383807ac5e2a7a6365252aee568a91a949c0c4`.
- Direct JSON chunk proved `skins[0].skeleton` is omitted, not JSON null; joints/hierarchy/accessor/skinning checks passed independently.
- Canonical validator fix accepts omitted optional skeleton, preserves explicit fail-closed validation, and corrects nested-joint overreach while retaining rooted common-root policy.
- Focused GLB structural tests pass `6/6` methods and the exact existing artifact validates `STRUCTURALLY_VALID` without byte/hash mutation.
- One real continuation attempt stopped before spawn at `MPFB_PROVISIONING_ROOT_HASH_MISMATCH` (computed `10ebf09a...`, manifest `f6907ef0...`). No retry or runtime repair was performed.
- Terminal verdict: `P2P_MPFB2_GLB_SKIN_NEXT_BLOCKER_FOUND`.
- Coder report: `reports/coder/rp_coder_260902_085141_by_gpt-5-codex_p2p-mpfb2-glb-skin-validation-01.md`.

## P2P-MPFB2-PROVISIONING-ROOT-DRIFT-01 / Issue 56

- Fresh canonical main: `e7c040d87dacf7b5cfee1e57536edc0b27f5768b`; tree `9649785f0104259bac05b244a2162e2a7321657f`.
- Exact MPFB2 pin: `2.0.17`, release `80919fa4682335c41847f761a4d79dcad4124732`, tree `189a1d6694515ecfbdc40067218c5024389b4e43`; pinned source/assets unchanged.
- Root delta: exactly 526 added `src/**/__pycache__/*.pyc` paths, 0 modified, 0 deleted, 0 unknown; archive recomputed exactly to manifest root `f6907ef03674ddc995e8b0fdd988e9a003cad61df0d4f707e2a7aaeda4d4e788`.
- Bounded fix: `mpfb_adapter.hash_provisioned_root()` excludes only immediate `__pycache__/*.pyc`; source and asset mutations, unknown cache files, and outside-cache `.pyc` remain fail-closed.
- Focused adapter boundary tests: `22/22 PASS`; full native compile exit 0; package doctor governance drift remains pre-existing and out of scope.
- Exactly one real continuation passed with child PID `27548`, firewall setup/enforcement/cleanup PASS, addon identity/preference/register PASS, HumanService/GameEngine rig/skin/export/provenance/GLB validation PASS, Oak GLB SHA `5f96f86fbfd4cdc01201e767b0383807ac5e2a7a6365252aee568a91a949c0c4`.
- Post-run: root hash `f6907ef0...`, 526 generated `.pyc` retained, active Blender `0`, `P2P-MPFB-DENY-*` rule count `0`, Game Truyen HEAD/status unchanged, no reinstall/download/manifest rewrite.
- Candidate source checkpoint: `79d9526b4401fdd6b0e76eef972ec6ec2186430d` / tree `8c22e067ce35e96ac6e59d93f36f372603be9393`.
- Coder report: `reports/coder/rp_coder_260902_103500_by_gpt-5-codex_p2p-mpfb2-provisioning-root-drift-01.md`.
- Supervisor report: `reports/supervisor/rp_supervisor_260902_103800_by_gpt-5-codex_p2p-mpfb2-provisioning-root-drift-01.md`; verdict `PASS` for the bounded ISSUE=56 claim.
- Terminal verdict: `P2P_MPFB2_RUNTIME_SMOKE_PASS`.
