# P2P MPFB2 Addon Init 01 Evidence Ledger

## Metadata

- Date: `2026-09-01`
- Plan: `docs/plans/2026-09-01-p2p-mpfb2-addon-init-01/2026-09-01-p2p-mpfb2-addon-init-01-plan.md`
- Evidence: `docs/plans/2026-09-01-p2p-mpfb2-addon-init-01/2026-09-01-p2p-mpfb2-addon-init-01-evidence.md`
- Benchmark: `docs/plans/2026-09-01-p2p-mpfb2-addon-init-01/2026-09-01-p2p-mpfb2-addon-init-01-benchmark.md`
- Actual status: `docs/plans/2026-09-01-p2p-mpfb2-addon-init-01/2026-09-01-p2p-mpfb2-addon-init-01-actual-status.md`

## Evidence Rules

Use exact IDs and separate source/docs facts, real Blender proof, bounded
implementation, focused checks, artifact validation, and cleanup. A report or
test alone cannot prove the real runtime claim.

## E0 - P0 Evidence

Matching plan item(s): `P0-A`

- `E0-P0A-GIT1`: remote/main and clean branch bind to expected SHA/tree.
- `E0-P0A-RUNTIME1`: existing Blender hash/version, runtime manifest, and MPFB
  pin; five generated caches identified.
- `E0-P0A-MPFB1`: existing MPFB archive hash matches manifest and all 2810
  archive files match provisioned source bytes.
- `E0-P0A-SRC1`: canonical child uses bare `sys.path` import and explicit
  `mpfb.register`; adapter/firewall boundaries are preserve-only.
- `E0-P0A-LOG1`: fresh bare probe reproduces addon/preference failure; prior
  extension probe history is retained as supporting evidence.
- `E0-P0A-GRAPH1`: fresh Anvien analysis: 1109 files scanned, 199 code parsed,
  0 parse failures, 50663 nodes, 58648 relationships.
- `E0-P0A-IMPACT1`: focused test file has 143 local relationships; hidden
  `.p2p` entrypoint file-detail/impact is unavailable and recorded as UNKNOWN.
- `E0-P0A-WORKFLOW1`: P2P workflow inspect/classify returned bounded separate
  objectives; explicit user workstream remains the authority.

## E1 - P1 Evidence

Matching plan item(s): `P1-A`, `P1-B`

- `E1-P1A-SRC1`: pinned manifest id=`mpfb`, type=`add-on`; `get_preference`
  checks `__package__` in `bpy.context.preferences.addons`; `register()` is
  the MPFB initialization entrypoint.
- `E1-P1A-DOC1`: official Blender 4.2 docs/source support local extension
  repositories, `blender_manifest.toml`, `bl_ext.<repo_module>.<id>`, and
  isolated user/portable resources.
- `E1-P1A-RUNTIME1`: bare probe exit 4 with exact
  `The 'mpfb' addon does not exist!?`, `Could not read preference mpfb_user_data`,
  and package-not-an-extension error.
- `E1-P1A-RUNTIME2`: local extension probe exit 0 with
  `MPFB_ADDON_IDENTITY_PRESENT=YES`, `MPFB_GET_PREFERENCE_PASS=YES`,
  `MPFB_REGISTER_PASS=YES`, identity `bl_ext.src.mpfb`, and runtime-local
  resource paths.
- `E1-P1A-DECISION1`: `BOUNDED_SOURCE_FIX`; canonical entrypoint is still
  unbound to the proven extension path.
- `E1-P1B-IMPACT1`: pre-edit Anvien file-detail/impact for hidden entrypoint
  returned not-found/UNKNOWN; focused test file detail returned 143 local
  relationships. This is a scope warning, not zero impact.
- `E1-P1B-SRC1`: frozen bounded entrypoint diff uses local repo discovery,
  refresh, `addon_utils.enable`, real identity/preference checks, and dynamic
  extension service import.
- `E1-P1B-TEST1`: compile/focused test and source-diff checks after edit.
- `E1-P1B-CACHE1`: exact five generated caches quarantined; manifest root hash
  restored to `f6907ef03674ddc995e8b0fdd988e9a003cad61df0d4f707e2a7aaeda4d4e788`.

## E2 - P2 Evidence

Matching plan item(s): `P2-A`, `P2-B`

- `E2-P2A-BIND1`: final candidate SHA/tree, exact MPFB/Blender pins, recipe,
  empty output, and unchanged security source.
- `E2-P2A-ADDON1`: final canonical child identity marker.
- `E2-P2A-ADDON2`: final canonical child preference/register markers.
- `E2-P2B-RUN1`: firewall receipt, child PID, stage output, and logs.
- `E2-P2B-ARTIFACT1`: GLB existence/size/SHA/independent structural result.
- `E2-P2B-ARTIFACT2`: provenance/hash/resource binding result.
- `E2-P2B-CLEAN1`: firewall rule cleanup and absence.
- `E2-P2B-IMMUT1`: Game Truyen fingerprint/mutation NO.
- `E2-P2B-STOP1`: exact first downstream blocker and NOT_RUN fields, if any.

## Closure Evidence

- `E3-P3A-SUP1`: Supervisor report and independent verdict.
- `E3-P3B-CLEAN1`: dead-work review.
- `E3-P3C-CLOSE1`: final commit/branch/PR/detect-changes/terminal packet.

