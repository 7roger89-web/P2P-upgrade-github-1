# P2P-IMG2THREEJS-MATERIAL-DEFAULT-USERDATA-01 — Empty Default `userData` Bounded Fix

## Metadata

- Date: `2026-08-31`
- Workstream: `P2P-IMG2THREEJS-MATERIAL-DEFAULT-USERDATA-01`
- Downstream capability: `game.three.asset.static_glb_standardize` (via the
  `img2threejs.static_projection` seam)
- Fresh main: `c1481ef7450113d6f7980fb2360991626200c9e6`
  tree `6c8321bbe089e1c37d552fcce8d139cf51096378` (matches expected)
- Mode: bounded, fail-closed material-boundary fix for the actual production
  smoke only. No module-resolution revisit (PR35 is proven), no material
  support expansion, no registry change, no Game Truyện change.

## Proven production blocker

```
material type: MeshPhysicalMaterial
attenuationDistance: Infinity  (classification: RUNTIME_DEFAULT)
first projection blocker: UNSUPPORTED_MATERIAL_FEATURE:userData
```

## Root cause — CONFIRMED

`img2threejs_material_snapshot.mjs` iterates a THREE material's own
properties and compares each live value to a freshly constructed baseline
`new material.constructor()` (`reference[key]`).

Pinned three `0.169.0` (`r169`) `src/materials/Material.js` constructor:

```js
this.userData = {};
```

Every material instance allocates its **own** empty plain record at
construction. Therefore:

| value | baseline |
| --- | --- |
| `{}` (live material's own instance) | `{}` (baseline instance's own record) |

- `Object.keys(material)` includes `"userData"` (own, enumerable).
- `value !== base` is `true` **only because object identity differs** (both
  records are empty and plain).
- Previous generic object comparison therefore emitted
  `drift: [["userData", "object"]]` for a completely inert default material.
- `bake_static_projection` → `_static_material` sees `userData` outside the
  projected key set → `UNSUPPORTED_MATERIAL_FEATURE:userData`.

```
ROOT_CAUSE_CONFIRMED=YES
USERDATA_RUNTIME_VALUE={}          (fresh empty plain object, instance-owned)
USERDATA_BASELINE_VALUE={}         (fresh empty plain object, baseline-owned)
USERDATA_DEFAULT_EQUIVALENT=YES    (appearance semantics identical; identity differs)
```

This is a special-case runtime-default metadata comparison, not a material
support expansion.

## Bounded fix

`img2threejs_material_snapshot.mjs` — special-case `key === "userData"` only:

- accepted as DEFAULT / no drift **only when both** the runtime value and the
  constructor baseline are plain record-like objects (`Object.prototype` or
  `null` prototype; not arrays/Maps/class instances) **and both are empty**
  (`Reflect.ownKeys(...).length === 0`, so symbol/non-enumerable keys also
  fail closed).
- distinct object identity alone never creates drift for two empty default
  userData records.
- non-empty or non-plain userData remains fail-closed drift
  (`["userData", "object"]` → downstream `UNSUPPORTED_MATERIAL_FEATURE:userData`).

No change to:

- `PROJECTED_MATERIAL_KEYS` — still `{color, opacity, metalness, roughness}`;
  `userData` is NOT projected.
- static GLB output contract — no `userData` field is emitted.
- generic object handling for every other property — no broad
  JSON.stringify/deep-equality rule.
- adapter, harness, standardizer, registry, activation, pins, or PR35 wiring.

## Focused evidence

### 1. Two separately allocated empty default userData objects → no drift

```js
const material = new FakeStandardMaterial();
material.userData = {};                       // distinct identity from baseline
materialSnapshot(material).drift              // []
```

### 2. Default MeshPhysicalMaterial — attenuationDistance=Infinity + empty
userData → snapshot drift empty
(covered by `default-Infinity attenuationDistance ...` test with a reallocated
empty userData; drift is `[]`, no `userData` entry).

### 3. Non-empty runtime userData while baseline empty → drift (fail-closed)

```js
material.userData = { customTag: "unique-id" };
materialSnapshot(material).drift              // [["userData", "object"]]
bake_static_projection(...)                   // UNSUPPORTED_MATERIAL_FEATURE:userData
```

### 4/5. Active transmission / clearcoat → still recorded as drift (fail-closed)

Existing snapshot tests remain green (`transmission = 0.4`, `clearcoat = 1.0`).

### 6. NaN attenuationDistance → still hard reject

`MATERIAL_NONFINITE:attenuationDistance` (snapshot) and
`UNSUPPORTED_MATERIAL_FEATURE:attenuationDistance` (projection) — unchanged.

### 7. non-default -Infinity attenuationDistance → still hard reject

New snapshot test: `MATERIAL_NONFINITE:attenuationDistance`.

### 8. default Infinity attenuationDistance → still passes

Existing snapshot test (`drift: []`) and existing seam test
(`physical_to_standard` narrowing) remain green.

### 9. bake_static_projection accepts corrected snapshot (drift=[]) and
narrows MeshPhysicalMaterial → MeshStandardMaterial
(new seam test; output satisfies `validate_static_glb_output`,
`STRUCTURALLY_VALID`).

### 10. bake_static_projection rejects non-empty userData drift
(seam test → `UNSUPPORTED_MATERIAL_FEATURE:userData`).

## Test counts

```text
node snapshot semantics    = 15/15  (tests/img2threejs_material_snapshot.node_test.mjs)
projection seam suite      = 30/30  (tests/test_img2threejs_static_projection.py)
static GLB standardizer    =  7/7   (tests/test_static_glb_standardizer.py)
BROAD_TESTS_RUN            = NO
```

Projection seam suite went 28/28 → 30/30 with the two focused
`MaterialDefaultUserDataTests` adapter-boundary tests. Static GLB
standardizer 7/7 baseline unchanged.

## Scope guards

```text
MATERIAL_SUPPORT_EXPANDED      = NO
PROJECTED_MATERIAL_KEYS_CHANGED= NO
STATIC_GLB_CONTRACT_CHANGED    = NO
REGISTRY_CHANGED               = NO
CAPABILITY_ACTIVATED           = NO
GAME_REPO_CHANGED              = NO
PR35_RUNTIME_WIRING_PRESERVED  = YES
OVER_ENGINEERING_CHECK         = PASS
```

## Verdict

```text
STATUS=CANDIDATE (bounded, fail-closed; not activated)
DEFAULT_EMPTY_USERDATA_CLASSIFICATION = DEFAULT (no drift)
NONEMPTY_USERDATA_FAIL_CLOSED         = YES
EXECUTION_AUTHORIZED                  = NO
NEXT_STEP=INDEPENDENT_SUPERVISOR
TERMINAL_VERDICT=P2P_IMG2THREEJS_MATERIAL_DEFAULT_USERDATA_PR_READY
```
