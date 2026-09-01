# Coder Report: P2P-MPFB2-ADDON-INIT-01

Date: 2026-09-01
Role: WRITER_AND_REAL_RUNTIME_EXECUTOR
Repository: `7roger89-web/P2P-upgrade-github-1`
Issue: `52`
Base: `b65948b00ed2a8969fed70ab59f68b5d9b53858d`
Branch: `workstream/p2p-mpfb2-addon-init-01-final`

## Result

The addon-initialization blocker is closed by one bounded source fix. A real
Blender 4.2.23 child loaded the existing pinned MPFB2 2.0.17 source through
Blender's local extension lifecycle and passed the identity, preference, and
registration gates. The one-character route then reached native GLB export and
stopped at the first new downstream structural-validation blocker:
`GLB_skeleton: index invalid` because `skins[0].skeleton` is `null`.

This report does not claim full route acceptance. No second blocker was fixed,
no retry was made, and no unrelated surface was widened.

## Invariant Family Map

| Family | Existing contract | Change / evidence |
|---|---|---|
| Security | Firewall profile normalization, exact DisplayName/rule count, outbound BLOCK, executable binding, verify-before-Popen, cleanup | Preserved; real smoke spawned only after setup/verification and ended with rule count `0`. |
| Data | Exact MPFB pin/root hash and provenance-bound GLB | Preserved; existing source hash matched after deterministic `.pyc` quarantine; sidecar recipe/GLB/hash validation passed. |
| Boundary | Parent adapter owns child process and post-child validation | Preserved; only child addon loading changed. |
| Lifecycle | Blender must own addon identity and registration before MPFB preference/service access | Fixed with local extension repo discovery/addition, refresh, and `addon_utils.enable(..., default_set=True, persistent=False)`. |
| Provenance | One neutral character and exact sidecar binding | Native `Oak.glb` plus sidecar created; provenance validation passed. |
| Immutability | Game Truyen and Owner checkout remain untouched | Game Truyen fingerprint unchanged; Owner root with invalid `.git` untouched. |

## Files and source checkpoint

Production mutation is limited to:

- `.p2p/system/p2p_capabilities/mpfb_blender_entrypoint.py`

Plan/evidence/benchmark/status ledgers and this report are documentation
artifacts. `mpfb_adapter.py` and `windows_network_isolation.py` were not
changed. Pinned MPFB2 upstream source was not edited. Blender was not
reinstalled and no second MPFB2 download was made.

Source checkpoint before documentation closure:

- commit: `0e3cc85d3b8ea599a1918be91873d1ef17ba14b1`
- tree: `e77c8e45f5c1771bf1fc47f8b3bdc27e4d431d90`

## Verification

- `py_compile`: PASS.
- `compileall` for affected capability/test roots: PASS.
- Directly affected focused classes: `35/35 PASS`.
- Full affected module: `42/43`; the only failure was the pre-existing
  projection assertion `expected 65, observed 67`, not changed or used as
  evidence against this bounded fix.
- Anvien fresh graph: `1109` scanned, `199` parsed, `0` parse failures. The
  hidden `.p2p` entrypoint is not represented as a graph file node, so its
  file-detail/impact result is `UNKNOWN`, not zero blast radius. Change
  detection identified one changed production file in the equivalent analyzed
  candidate.

## Real runtime evidence

- Real Blender child PID: `10540`.
- `MPFB_ADDON_IDENTITY_PRESENT=YES`.
- `MPFB_GET_PREFERENCE_PASS=YES`.
- `MPFB_REGISTER_PASS=YES`.
- MPFB initialization finished; HumanService path reached game-engine rig and
  skin material creation; native glTF export started and finished.
- Output: `Oak.glb`, `9093808` bytes,
  SHA-256 `5f96f86fbfd4cdc01201e767b0383807ac5e2a7a6365252aee568a91a949c0c4`.
- Provenance sidecar: `1488` bytes,
  SHA-256 `d5d50b0bea9dfb096762e566211df4db62be1ed1f7bb47473919a5f9f672f7b7`;
  schema, recipe binding, CORE_CC0 asset binding, and GLB hash all PASS.
- Structural result: `GLB_skeleton: index invalid`; independent inspection
  found one skin with `skeleton=null`.
- Firewall cleanup: exact rule count `0` after the exception.
- Game Truyen before/after fingerprint unchanged:
  `31c994cc0c53758f15260db71b7a6c4b52554a6d15b298402fba2db31cb7555d`.

## E2E status

Addon initialization: PASS.

Full one-character route: BLOCKED at the first new downstream structural
validator error. GLB repair, validator repair, retry, additional characters,
benchmarks, broad regression, and hardening are explicitly not run.

## Handoff

Ready for supervisor review of the bounded addon-init claim and truthful stop
at the first downstream blocker.
