# Coder Report — P2P Game Truyen MPFB Runtime 01

## Result

The two requested implementation blockers are closed at the code-contract
level. The parent now targets a dedicated bounded Blender entrypoint and gates
spawn behind an exact-path Windows Defender Firewall outbound rule lifecycle.
The implementation is ready for exact-subject Supervisor review. Blender and
MPFB2 execution remain explicitly NOT_RUN.

## Invariant family map

| Family | Source of truth | Preserved / changed surface |
|---|---|---|
| Recipe and job binding | `character_recipe.py`, parent adapter | strict workspace-relative recipe/job paths; recipe hash rechecked before spawn |
| MPFB pin and asset rights | exact MPFB2 snapshot, core-asset manifest, `asset_provenance.py` | 2.0.17 SHA/tree and six-key manifest, `CORE_CC0_ONLY`, CC0 core assets only |
| Supported Blender-side API | exact pinned MPFB2 source inspection | `mpfb.register`, `HumanService.create_human`, `add_builtin_rig("game_engine")`, `set_character_skin("GAMEENGINE")` |
| Process boundary | parent adapter and Windows isolation helper | `shell=False`, minimal env, exact entrypoint, timeout/tree kill, pre-spawn isolation, cleanup on all paths |
| Output and provenance | `glb_validator.py`, `asset_provenance.py` | exactly one GLB plus exactly one recipe/GLB-bound sidecar; undeclared output fails closed |
| Project boundary | user task and AGENTS.md | no Blender/MPFB2 execution, no Game Truyen modification, no promotion/release |

## Implemented slices

### Dedicated Blender body

- Added `.p2p/system/p2p_capabilities/mpfb_blender_entrypoint.py`.
- It explicitly binds the checked-in `.p2p/system` package root before any
  parent capability import, so a Blender launch from the per-job workspace
  cannot accidentally resolve a different `p2p_capabilities` package.
- It accepts one strict bounded argument shape after Blender's `--` marker;
  unknown flags, duplicate flags, positional values, arbitrary script paths,
  `--python-expr`, and `-c` are rejected.
- It revalidates the recipe, job identity, exact MPFB pin, root hash, and the
  six-key manifest including every declared `core_assets` hash/license entry.
- It maps the recipe's five proportion values only when they are representable
  by the inspected MPFB2 macro API; unsupported values fail closed instead of
  being silently approximated.
- It uses the inspected API sequence:
  `mpfb.register()` -> `HumanService.create_human(...)` ->
  `HumanService.add_builtin_rig(..., "game_engine", import_weights=True)` ->
  `HumanService.set_character_skin(..., skin_type="GAMEENGINE")`.
- It calls Blender's native `bpy.ops.export_scene.gltf` for exactly one GLB,
  then writes exactly one validated provenance sidecar. Hair/clothing entries
  remain rights-bound declarations; no unsupported or implicit asset API is
  invented.

### Windows process/network boundary

- Added `windows_network_isolation.py`.
- The mechanism is an exact executable-path-bound Windows Defender Firewall
  outbound program block, created with `netsh.exe` and verified with
  `Get-NetFirewallProfile`, `Get-NetFirewallRule`, and
  `Get-NetFirewallApplicationFilter`.
- It requires Administrator and enabled Windows Defender Firewall profiles.
  Rule collisions, path mismatches, disabled profiles, command failure, or
  verification failure fail closed. The helper also rechecks symlink/reparse
  status at its own executable boundary, covering the plan-to-spawn TOCTOU
  interval.
- A context-managed lease is created and verified before `Popen`; release is
  attempted after success, command failure, timeout, and setup failure. Cleanup
  failure is surfaced rather than hidden. Receipt fields bind identity,
  executable, mechanism, privilege, setup, enforcement, and cleanup results.
- No live firewall rule was created during this workstream.

### Parent integration

- `mpfb_adapter.py` now binds the dedicated entrypoint, validates the manifest
  and output root before spawn, rechecks recipe/manifest hashes, enters the
  isolation context before `Popen`, and propagates the enforcement receipt.
- Existing shell, environment, containment, reparse, timeout, process-tree,
  output, rights, and `ADAPTER_PASS != EXECUTION_PASS != VISUAL_PASS`
  boundaries remain in force.

## Focused verification

- `python -m unittest tests.test_p2p_game_truyen_mpfb_adapter_01`: **30/30
  PASS**. Tests use synthetic recipes/assets, fake Blender/MPFB boundaries,
  and mocked Windows command lifecycles only.
- Targeted `python -m py_compile` for parent, Blender entrypoint, Windows
  helper, and focused test: **PASS**.
- Full `python -m compileall -q .p2p/system/p2p_capabilities tests`: **PASS**;
  compile-only, no Blender/MPFB2 execution.
- `git diff --check`: **PASS**.
- Fresh Anvien graph refresh after implementation: 1,078 files scanned, 191
  parsed code files, 0 parse failures, 47,300 nodes, 54,620 relationships.
  The hidden `.p2p` source remains outside reliable file-detail/symbol-impact
  coverage; that limitation is recorded and is not treated as zero blast
  radius.
- Anvien change detection is required and recorded before the candidate
  commit; it is not substituted by the focused tests.

## Explicit non-claims

- `BLENDER_INSTALLED=NO`.
- `MPFB_EXECUTED=NO`.
- `GLB_CREATED=NO`.
- No Golden Character, visual proof, Game Truyen change, promotion, release,
  deployment, push, or live network-isolation activation occurred.
- This report claims implementation readiness only. It is not actual Blender
  execution proof, execution-pass proof, visual-pass proof, or owner approval.

## Handoff

Run a fresh exact-subject Supervisor review after the candidate commit. The
review subject must bind to the candidate SHA/tree and must preserve
`ACTUAL_EXECUTION_PROVEN=NO` and `CANONICAL_PROMOTED=NO`.
