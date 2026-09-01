# Notes and Decisions Log — 2026-09-01

Workstream: `P2P-MPFB2-ADDON-INIT-01`
Repository: `7roger89-web/P2P-upgrade-github-1`
Issue: `52`

## Decisions

1. Fresh subject was bound to canonical main
   `b65948b00ed2a8969fed70ab59f68b5d9b53858d` in a clean branch/worktree.
   The supplied Owner checkout has an invalid `.git` and was not repaired or
   modified.
2. Existing Blender 4.2.23 and MPFB2 2.0.17 pin
   `80919fa4682335c41847f761a4d79dcad4124732` were reused. The provisioned
   MPFB2 bytes matched the existing pinned archive after only quarantining five
   generated `.pyc` files; no reinstall, upstream edit, or second download.
3. Blender 4.2's supported local extension repository was selected. The
   canonical child now enables `bl_ext.src.mpfb` through
   `addon_utils.enable(..., default_set=True, persistent=False)`, allowing
   Blender to create the real addon preference identity and invoke
   `mpfb.register()` through its lifecycle.
4. The remediation is `BOUNDED_SOURCE_FIX`, limited to
   `.p2p/system/p2p_capabilities/mpfb_blender_entrypoint.py`. Firewall,
   adapter, network-deny, and cleanup code remain unchanged.
5. The real smoke passed addon identity/preference/registration and reached
   native export. It stopped at the first new downstream error
   `GLB_skeleton: index invalid` (`skins[0].skeleton=null`). No second fix or
   retry is authorized in this workstream.

## Evidence anchors

- Source checkpoint: `0e3cc85d3b8ea599a1918be91873d1ef17ba14b1`.
- Real markers: `MPFB_ADDON_IDENTITY_PRESENT=YES`,
  `MPFB_GET_PREFERENCE_PASS=YES`, `MPFB_REGISTER_PASS=YES`.
- Real child PID: `10540`.
- Provenance validation: `PASS`.
- Firewall post-cleanup count: `0`.
- Game Truyen mutation: `NO`; before/after fingerprint unchanged.
- Detailed packet: `reports/coder/rp_coder_260901_183100_by_gpt-5-codex_p2p-mpfb2-addon-init-01.md`.

## Closure state

Addon-init scope is technically ready for supervisor review. The terminal
workstream verdict remains `P2P_MPFB2_ADDON_INIT_NEXT_BLOCKER_FOUND` because
the first downstream GLB structural blocker is real and deliberately
unrepaired.
