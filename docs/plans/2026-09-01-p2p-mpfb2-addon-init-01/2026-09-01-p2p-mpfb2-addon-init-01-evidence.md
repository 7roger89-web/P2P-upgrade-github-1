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

### P1/P2 execution evidence details

- `E1-P1A-SRC1`: MPFB2 `blender_manifest.toml` declares `id = "mpfb"` and
  `type = "add-on"`; `get_preference()` uses `__package__` as the
  `bpy.context.preferences.addons` key; `register()` initializes preferences,
  services, and contextual information. Blender 4.2 `addon_utils` documents
  extension namespaces as `bl_ext.<repo_module>.<package>` and its `enable()`
  implementation invokes `mod.register()` after `default_set=True` creates the
  addon preference entry.
- `E1-P1A-DOC1`: official Blender 4.2 references used were the [4.2 command
  line environment/extension documentation](https://docs.blender.org/manual/en/4.2/advanced/command_line/arguments.html),
  [4.2 extension development setup](https://developer.blender.org/docs/handbook/extensions/addon_dev_setup/),
  and [4.2 Python API release notes](https://developer.blender.org/docs/release_notes/4.2/python_api/).
  These support `BLENDER_USER_*`, portable resources, local extension
  repositories, `blender_manifest.toml`, and the extension package model.
- `E1-P1A-RUNTIME1`: the existing runtime's bare probe, with a fresh offline
  Blender process, exited `4` and printed the exact addon-missing,
  preference-missing, and package-not-an-extension errors.
- `E1-P1A-RUNTIME2`: the dedicated extension probe, extended only with truth
  markers, exited `0` in local isolated resources and printed
  `MPFB_ADDON_IDENTITY_PRESENT=YES`, `MPFB_GET_PREFERENCE_PASS=YES`, and
  `MPFB_REGISTER_PASS=YES`; actual module/package and addon key were
  `bl_ext.src.mpfb`, with `online_access=false`. A portable-folder run repeated
  the same PASS and kept config/scripts/extensions beside Blender.
- `E1-P1A-DECISION1`: `BOUNDED_SOURCE_FIX`; runtime-only cannot fix the
  canonical bare import. The source fix changes only the child MPFB loading
  and service import path.
- `E1-P1B-SRC1`: commit `0e3cc85d3b8ea599a1918be91873d1ef17ba14b1` changes only
  `.p2p/system/p2p_capabilities/mpfb_blender_entrypoint.py` in production code:
  local repo discovery/addition, refresh, `addon_utils.enable`, identity and
  preference gates, and dynamic extension service import.
- `E1-P1B-TEST1`: directly affected classes
  `AdapterBoundaryTests`, `GlbValidationTests`, and `NetworkIsolationTests`
  passed `35/35`; `py_compile`, `compileall`, and `git diff --check` passed.
  The full 43-test module has one unrelated projection assertion failure
  (`expected 65, observed 67`) and was not changed.
- `E1-P1B-CACHE1`: exactly five generated `.pyc` files were moved to the
  runtime-local quarantine after archive comparison; root hash then matched the
  manifest and `PYC_COUNT=0`.
- `E2-P2A-BIND1`: final child plan bound the existing Blender executable hash
  `e2b4d2ccbfb7a33b0bb1abb1b7a08ebca3b5a745e73960d5a2decc0b9579b715`, exact
  MPFB pin, recipe `Oak`, and empty output before spawn.
- `E2-P2A-ADDON1`: real canonical child PID `10540` printed
  `MPFB_ADDON_IDENTITY_PRESENT=YES`.
- `E2-P2A-ADDON2`: the same child printed
  `MPFB_GET_PREFERENCE_PASS=YES` and `MPFB_REGISTER_PASS=YES` before
  `HumanService`/export messages. Registration is backed by Blender's
  `addon_utils.enable()` lifecycle, not a fabricated or duplicate call.
- `E2-P2B-RUN1`: the real child printed MPFB initialization finished,
  `Creating game engine skin material`, and native glTF export start/finish;
  the adapter reached structural validation, so firewall setup/verification
  passed before `Popen` and the child returned successfully.
- `E2-P2B-ARTIFACT1`: exactly `Oak.glb` and the sidecar were present. GLB size
  `9093808` bytes, SHA-256
  `5f96f86fbfd4cdc01201e767b0383807ac5e2a7a6365252aee568a91a949c0c4`.
  Header is glTF version 2 with 55 nodes, 1 skin, and 1 mesh, but the skin's
  `skeleton` field is `null`; the validator stopped at
  `GLB_skeleton: index invalid`.
- `E2-P2B-ARTIFACT2`: sidecar size `1488` bytes, SHA-256
  `d5d50b0bea9dfb096762e566211df4db62be1ed1f7bb47473919a5f9f672f7b7`;
  schema, CORE_CC0 asset binding, recipe binding, and GLB hash all validated.
  `PROVENANCE_VALIDATION=PASS`.
- `E2-P2B-CLEAN1`: after the structural-validation exception unwound, exact
  P2P firewall rule count was `0`; cleanup did not mask the structural error.
- `E2-P2B-IMMUT1`: Game Truyen status fingerprint remained
  `31c994cc0c53758f15260db71b7a6c4b52554a6d15b298402fba2db31cb7555d`; no
  Game Truyen files were accessed or changed by the runtime runner.
- `E2-P2B-STOP1`: terminal downstream blocker is
  `GLB_skeleton: index invalid`; no rig/validator repair, retry, second
  character, or unrelated test was performed.

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

- `E3-P3A-SUP1`: supervisor report
  `reports/supervisor/rp_supervisor_260901_184112_by_gpt-5-codex_p2p-mpfb2-addon-init-01.md`;
  PASS is limited to the bounded addon-init claim and stop-law evidence.
- `E3-P3B-CLEAN1`: dead-work review found no unneeded plan-created
  implementation artifact. Retained files are the plan, ledgers, coder report,
  supervisor report, and runtime-local evidence requested by this workstream.
- `E3-P3C-CLOSE1`: fresh origin/main remained the exact canonical base;
  branch `workstream/p2p-mpfb2-addon-init-01-final` was pushed non-force and
  PR #54 was created at
  `https://github.com/7roger89-web/P2P-upgrade-github-1/pull/54`. The PR is
  open and unmerged. The closure-only documentation update does not alter the
  production source or the reviewed runtime result; final HEAD/tree are
  emitted in the terminal return packet.
