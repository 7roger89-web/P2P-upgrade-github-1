# P2P-IMG2THREEJS-MATERIAL-DEFAULT-NONFINITE-01 — Material Default / Non-finite Bounded Fix

## Metadata

- Date: `2026-08-31`
- Workstream: `P2P-IMG2THREEJS-MATERIAL-DEFAULT-NONFINITE-01`
- Downstream capability: `game.three.asset.static_glb_standardize`
- Fresh main: `1924816f6161bf19574421eb28d5084c40b7970d`
  tree `4a3917909f0dd545e3505b5d5765d548fdc78089`
- Prior local candidate: `39719842dd2728ff4014370c18bd81ad25fe25a4`
  tree `9c594c12999e173137aac6740c00339fc7eed17b` — **NOT recoverable** in this
  workspace's object store (verified: `git cat-file -t` fails, no branch/ref
  contains it, `fsck --unreachable` empty). Recreated from the reviewed fix
  intent against fresh canonical main. No fake SHA is claimed.
- Mode: bounded, scoped material-default remediation only. No redesign, no
  material support expansion, no registry change, no Game Truyện change.

## Root cause

`img2threejs_static_projection_harness.mjs` builds a material snapshot by
iterating a THREE material's own properties and comparing each to the same
class's runtime constructor default (`reference[key]`). For a numeric property
the old comparison order was:

```js
if (!Number.isFinite(value)) fail(`MATERIAL_NONFINITE:${key}`);
if (value !== base) drift.push([key, value]);
```

Because the non-finite check ran **before** the default comparison, a property
whose exact runtime default is `Infinity` — `MeshPhysicalMaterial.attenuationDistance`
at the pinned three `0.169.0` — always tripped `MATERIAL_NONFINITE:attenuationDistance`
on a completely default `MeshPhysicalMaterial`. The bake aborted for a material
that carried no appearance drift, i.e. the seam rejected a legitimate
"all-physical-default" material that the contract should narrow to the canonical
Standard subset.

## Bounded fix

The material snapshot is extracted into a P2P-owned module
`img2threejs_material_snapshot.mjs`, and the numeric branch order is corrected
so that the runtime-default comparison runs **before** the generic non-finite
rejection:

```js
if (typeof value === "number") {
  // 1. runtime-default comparison BEFORE generic non-finite rejection
  if (value === base) continue;              // exact runtime default (may be Infinity)
  // 2. only a non-default value reaches the finite-only rejection
  if (!Number.isFinite(value)) reject(`MATERIAL_NONFINITE:${key}`);
  if (value !== base) drift.push([key, value]);
  continue;
}
```

The property-comparison ordering contract this module now guarantees:

1. runtime-default comparison runs before generic non-finite rejection;
2. an exact runtime default `Infinity` (e.g. `attenuationDistance`) is treated
   as DEFAULT → no drift, no reject;
3. `NaN` is NEVER accepted as a valid default — `NaN !== base` for every base,
   including a NaN base, so it always reaches the finite-only rejection;
4. supported projected numeric fields (color channels, opacity, metalness,
   roughness) remain finite-only;
5. an active / non-default `attenuationDistance` remains fail-closed (recorded
   as drift, then rejected downstream as `UNSUPPORTED_MATERIAL_FEATURE`);
6. active transmission / clearcoat / etc. drift remains fail-closed;
7. no material support expansion (no new material types, no new projected keys;
   `SUPPORTED_MATERIAL_TYPES` and the projected set `{color, opacity, metalness,
   roughness}` are unchanged).

The module is free of `process.exit` and throws an `Error` whose `code` carries
the exact failure code; the harness wraps it and translates a caught code into
its own terminal `P2P_IMG2THREEJS_BAKE_FAIL <code>` line. This keeps the module
unit-testable under Node without a THREE runtime.

## Files changed

- `.p2p/system/p2p_capabilities/img2threejs_material_snapshot.mjs` — **new**;
  standalone material snapshot (runtime-default-first comparison, fail-closed).
- `.p2p/system/p2p_capabilities/img2threejs_static_projection_harness.mjs` —
  import the module, drop the inline snapshot/helpers, wrap thrown codes.
- `.p2p/system/p2p_capabilities/tests/img2threejs_material_snapshot.node_test.mjs`
  — **new**; 11 snapshot-semantics unit tests.
- `.p2p/system/p2p_capabilities/tests/test_img2threejs_static_projection.py` —
  3 new adapter-boundary/default-nonfinite tests (17 → 20, see counts below).
- `docs/plans/2026-08-31-p2p-img2threejs-material-default-nonfinite-01/evidence.md`
  — this file.

No registry change. No capability activation. No Game Truyện change.

## Focused evidence

### 1. Exact runtime-default attenuationDistance → accepted as DEFAULT

- Node snapshot module: `materialSnapshot(new FakePhysicalMaterial())` where the
  physical material's `attenuationDistance` is the runtime default `Infinity`
  and every other physical semantic is at its own default → snapshot succeeds
  with empty drift and no `MATERIAL_NONFINITE` failure.
- Python projection: a `MeshPhysicalMaterial` with `drift=[]` (the corrected
  snapshot's output) narrows to `MeshStandardMaterial` and is accepted by the
  static-GLB standardizer (`STRUCTURALLY_VALID`).

### 2. Finite active attenuationDistance → fail closed

- Node snapshot: `attenuationDistance = 2.5` is recorded as drift
  `["attenuationDistance", 2.5]` (not silently dropped).
- Python projection: `drift=[["attenuationDistance", 2.5]]` →
  `UNSUPPORTED_MATERIAL_FEATURE:attenuationDistance`.

### 3. NaN attenuationDistance → fail closed

- Node snapshot: `attenuationDistance = NaN` → throws
  `MATERIAL_NONFINITE:attenuationDistance` (NaN never equals the `Infinity`
  runtime default, so it is never laundered into a "default").
- Python projection: a `NaN` drift for `attenuationDistance` →
  `UNSUPPORTED_MATERIAL_FEATURE:attenuationDistance`.

### 4. Supported projected field Infinity → fail closed

- Node snapshot: `material.metalness = Infinity` → throws
  `MATERIAL_NONFINITE:metalness` (and `material.opacity = Infinity` →
  `MATERIAL_NONFINITE:opacity`).
- Python projection: `opacity = Infinity` / `roughness = Infinity` →
  `MATERIAL.OPACITY` / `MATERIAL.ROUGHNESS` non-finite rejection.

### 5. Supported projected field NaN → fail closed

- Node snapshot: `material.opacity = NaN` → throws `MATERIAL_NONFINITE:opacity`;
  a non-finite color channel → `MATERIAL_COLOR_NONFINITE`.
- Python projection: `metalness = NaN` → `MATERIAL.METALNESS` non-finite
  rejection; a NaN color channel → `MATERIAL.COLOR[0]` non-finite rejection.

### 6. Existing active transmission / clearcoat / etc → fail closed

- Node snapshot: `transmission = 0.4` and `clearcoat = 1.0` are each recorded as
  drift (never silently dropped).
- Python projection: the same unsupported-feature keys →
  `UNSUPPORTED_MATERIAL_FEATURE`, unchanged from the promoted seam.

## Test counts

```text
node snapshot semantics    = 11/11  (tests/img2threejs_material_snapshot.node_test.mjs)
projection seam suite      = 20/20  (tests/test_img2threejs_static_projection.py)
static GLB standardizer    =  7/7   (tests/test_static_glb_standardizer.py)
BROAD_TESTS_RUN            = NO
```

Projection seam suite moved from a 17/17 baseline to 20/20 with three focused
adapter-boundary tests. Static GLB standardizer 7/7 baseline is unchanged. Only
focused tests needed for the exact candidate were run.

## Scope guards

```text
REGISTRY_CHANGED          = NO
CAPABILITY_ACTIVATED      = NO
GAME_REPO_CHANGED         = NO
MATERIAL_SUPPORT_EXPANDED = NO
OVER_ENGINEERING_CHECK    = PASS
```

## Verdict

```text
STATUS=CANDIDATE (bounded, reviewed-fix scope; not activated)
ATTENUATION_DISTANCE_RUNTIME_DEFAULT=Infinity
FAILURE_ORDER_CAUSE=runtime-default numeric comparison ran after generic non-finite rejection
NONFINITE_DEFAULT_HANDLING_FIXED=YES
SUPPORTED_FIELD_NONFINITE_REJECTION_PRESERVED=YES
ACTIVE_PHYSICAL_FEATURE_FAIL_CLOSED_PRESERVED=YES
EXECUTION_AUTHORIZED=NO
OWNER_GATE_READY=NO
NEXT_STEP=INDEPENDENT_SUPERVISOR
TERMINAL_VERDICT=P2P_IMG2THREEJS_MATERIAL_DEFAULT_NONFINITE_PR_READY
```
