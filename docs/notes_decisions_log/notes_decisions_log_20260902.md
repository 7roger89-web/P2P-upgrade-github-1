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
