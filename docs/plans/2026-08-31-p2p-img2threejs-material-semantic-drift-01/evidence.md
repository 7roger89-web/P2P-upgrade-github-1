# P2P-IMG2THREEJS-MATERIAL-SEMANTIC-DRIFT-01 — Material Semantic Drift Normalization

## Metadata

- Date: `2026-08-31`
- Workstream: `P2P-IMG2THREEJS-MATERIAL-SEMANTIC-DRIFT-01`
- Repository: `7roger89-web/P2P-upgrade-github-1`
- Fresh main fetch: `40334bff7f078a903702f76ba2412fdb157fce92` — matches
  `EXPECTED_BASE_MAIN_SHA` exactly (main had NOT moved; no STOP to Control
  Tower required).
- Mode: ONE narrow semantic-material-normalization fix to the material
  snapshot classifier. NOT a `version` one-field repair; the full known PR39
  production material drift inventory is closed. No material support
  expansion, no projected-key change, no factory/upstream/Game/capability
  change.

## Production drift inventory (authoritative)

Material type: `MeshPhysicalMaterial`. Live smoke vs `new MeshPhysicalMaterial()`
baseline under pinned three `r169`:

| key | live | base | semantic class |
| --- | --- | --- | --- |
| `version` | `1` | `0` | A. runtime bookkeeping counter (bumped by `material.needsUpdate = true`) |
| `defines` | `{STANDARD:"",PHYSICAL:""}` | same content, distinct record | B. value-equivalent runtime default |
| `color` | non-white | white | D. SUPPORTED PROJECTED APPEARANCE |
| `roughness` | `0.75` | `1` | D. SUPPORTED PROJECTED APPEARANCE |
| `envMapRotation` | `Euler(0,0,0,"XYZ")` | same, distinct Euler | B. value-equivalent runtime default |
| `envMapIntensity` | `0.8` | `1` | C. inactive companion (live `envMap = null`) |
| `clearcoatRoughness` | `0.25` | `0` | C. inactive companion (live `clearcoat = 0`) |
| `iridescenceThicknessRange` | `[100,400]` | same, distinct array | B. value-equivalent runtime default |
| `sheenColor` | white | black | C. inactive companion (live `sheen = 0`) |

No transmission / clearcoat activation / texture map / emissive /
transparency / alphaTest / side / flatShading / vertexColors drift is present.

## Root cause — CONFIRMED

`img2threejs_material_snapshot.mjs` compares each live material own-property to
a freshly constructed baseline. For real (non-runtime-test) materials, three
allocates per-instance objects whose *identity* always differs even when the
*content* is three's own runtime default:

- `Material.version` starts at `0` and is incremented as a pure invalidation
  counter (bumped to `1` whenever anything calls `needsUpdate = true`). Zero
  appearance content; the old numeric path flagged `1 !== 0` as drift.
- `defines` is a record three allocates in the material constructor
  (`{"STANDARD":"","PHYSICAL":""}` for Physical); live and baseline are two
  distinct objects with identical content.
- `envMapRotation` is a per-instance `THREE.Euler` defaulting to
  `(0,0,0,"XYZ")`; identity differs, content identical.
- `iridescenceThicknessRange` is a per-instance `[100, 400]` array; identity
  differs, content identical.
- `envMapIntensity`, `clearcoatRoughness`, `sheenColor` carry non-default
  *companion* values in production, but each controlling feature is provably
  inactive (`envMap === null`, `clearcoat === 0`, `sheen === 0`), so they have
  no rendered effect.

The generic `value !== base -> drift` classifier reported all nine as drift.
Post-normalization the true appearance drift is exactly:

```json
[["color","color"],["roughness",0.75]]
```

## Bounded fix — `img2threejs_material_snapshot.mjs` only

Narrow per-property semantic classifiers added in the existing comparison
loop. There is NO generic deep-equality engine, NO new projected key, NO new
public ignore list / escape flag.

### A. Runtime bookkeeping — `version`

- Ignored for appearance ONLY when BOTH the live value and the constructor
  baseline satisfy: `typeof === "number" && Number.isSafeInteger(v) && v >= 0`
  (finite non-negative safe integer — `0` baseline and any live counter are
  valid runtime bookkeeping).
- Any malformed value (`NaN`, `±Infinity`, negative, fractional, non-number,
  beyond `MAX_SAFE_INTEGER`) fails closed hard with code
  `MATERIAL_VERSION_INVALID`.
- `version` is NOT added to `PROJECTED_MATERIAL_KEYS`.

### B. Value-equivalent runtime defaults — exact narrow semantic equality

- `defines` → `sameDefines`: BOTH sides must be plain records
  (`Object.prototype` or `null` prototype; never arrays/Maps/class
  instances); the EXACT own-key universe must match (strings AND symbols via
  `Reflect.ownKeys`); every value must be a safe primitive (string, finite
  number, boolean — `NaN` rejected) and `Object.is`-equal. Any content
  difference → `["defines","object"]` drift (fail-closed downstream).
- `envMapRotation` → `sameEuler`: BOTH sides must be Euler-like
  (`isEuler === true`) with finite x/y/z and a valid rotation order
  (`XYZ|YXZ|ZXY|ZYX|YZX|XZY`); x/y/z `Object.is`-exact and order identical.
  Different angle/order/NaN/non-Euler → `["envMapRotation","object"]` drift.
- `iridescenceThicknessRange` → `sameIridescenceThicknessRange`: BOTH sides
  must be real (non-typed) length-2 arrays with two finite entries,
  element-wise `Object.is`-exact. Different/malformed range →
  `["iridescenceThicknessRange","object"]` drift.

### C. Inactive appearance companions — proven-inactive only

- `envMapIntensity`: a non-default value is ignored ONLY when `envMap` is
  `null`/`undefined` AND the intensity is finite. An active envMap is handled
  fail-closed: a texture slot is rejected as `["envMap","texture"]` by the
  pre-existing texture gate and the intensity then rides in as numeric drift;
  a non-null non-texture slot leaves `envMapIntensity` as ordinary numeric
  drift. `NaN` intensity → `MATERIAL_NONFINITE:envMapIntensity`.
- `clearcoatRoughness`: ignored ONLY when `clearcoat === 0` (and the value is
  finite). `clearcoat > 0` leaves `clearcoat` as unsupported-feature drift
  and `clearcoatRoughness` as numeric drift — both fail closed.
  `NaN` companion → `MATERIAL_NONFINITE:clearcoatRoughness`.
- `sheenColor`: ignored ONLY when `sheen === 0` (the inactive-companion skip
  runs for the color path only; a texture color slot hits the pre-existing
  texture gate first and still drifts). `sheen > 0` keeps `sheen` as
  unsupported-feature drift and `sheenColor` as `["sheenColor","color"]`
  drift — both fail closed.

### D. Projected appearance — preserved, not suppressed

`color` and `roughness` are untouched: they remain ordinary drift that flows
through the existing projected material path. The exact positive-fixture
post-normalization drift is asserted to be
`[["color","color"],["roughness",0.75]]` (order-sensitive).

## Invariants — verified unchanged

- `PROJECTED_MATERIAL_KEYS = {color, opacity, metalness, roughness}` —
  asserted in tests; none of the seven normalized keys is a member.
- `SUPPORTED_MATERIAL_TYPES` unchanged — no material support expansion.
- `img2threejs_adapter.py` UNCHANGED (correct ownership is the snapshot's
  semantic classification; verified by git diff).
- `img2threejs_generator_metadata.mjs` and generator metadata boundary
  UNCHANGED.
- Arbitrary/non-generator `userData` remains fail-closed (empty-plain-record
  special case untouched).
- Active transmission / clearcoat / sheen / iridescence / textures / emissive
  / non-default attenuationDistance remain fail-closed.
- Default-`Infinity` attenuationDistance rule and NaN-never-default rule
  untouched.
- Strict fixtures, pinned upstream, three r169 pin, factory SHA binding,
  target-scale contract, world-matrix bake, static GLB standardizer, Game
  Truyện, capability activation — all untouched.

## Files changed

- `.p2p/system/p2p_capabilities/img2threejs_material_snapshot.mjs` (fix)
- `.p2p/system/p2p_capabilities/tests/img2threejs_material_snapshot.node_test.mjs`
  (faithful r169 fake surface — `version`/`defines`/`envMap`/`envMapRotation`/
  `envMapIntensity`/`clearcoatRoughness`/`sheenColor`/
  `iridescenceThicknessRange` — plus focused regression tests; no production
  fixture altered)
- this evidence document.

No projection-seam code change was required; seam-level behavior was
re-proven instead (below).

## Test results

```
node --test .p2p/system/p2p_capabilities/tests/*.node_test.mjs
# tests 62   # pass 62   # fail 0
  (img2threejs_material_snapshot: 32 — 16 prior + 16 new semantic-drift)
  (img2threejs_generator_metadata + img2threejs_static_projection_harness: 30)

python3 -m unittest (sys.path=.p2p/system)
  p2p_capabilities.tests.test_img2threejs_static_projection
  p2p_capabilities.tests.test_static_glb_standardizer
  -> Ran 46 tests — OK
```

Focused new coverage:

1. full production inventory material → drift is EXACTLY
   `[["color","color"],["roughness",0.75]]`;
2. version: `0/1/42/MAX_SAFE_INTEGER` ignored; NaN/±Infinity/-1/1.5/"1"/null/
   {}/true/MAX_SAFE_INTEGER+1 → `MATERIAL_VERSION_INVALID`;
3. defines: identical-content fresh record default-equivalent; changed value /
   extra key / missing key / nested-object value / symbol key / array / class
   instance → drift;
4. envMapRotation: equal fresh Euler default-equivalent; rotated angle /
   changed order / NaN component / plain object → drift;
5. iridescenceThicknessRange: equal fresh `[100,400]` default-equivalent;
   changed min/max / wrong length / NaN element / non-numeric / typed array →
   drift;
6. envMapIntensity: `0.8` + `envMap=null` → no drift; active texture envMap →
   `envMap` texture drift AND `envMapIntensity` numeric drift; non-null
   non-texture slot → `envMapIntensity` drift; NaN → non-finite reject;
7. clearcoatRoughness: `0.25` + `clearcoat=0` → no drift; `clearcoat=1.0` →
   `clearcoat` + `clearcoatRoughness` drift; NaN → non-finite reject;
8. sheenColor: white + `sheen=0` → no drift; `sheen=1.0` → `sheen` +
   `["sheenColor","color"]` drift; texture slot with `sheen=0` → texture drift;
9. prior arbitrary userData / transmission / clearcoat / non-finite / texture
   negative cases remain green;
10. seam proof (Python, `img2threejs_adapter._static_material`): the exact
    post-normalization drift projects with `color=[0.5,0.55,0.6]`,
    `roughness=0.75` via `physical_to_standard` narrowing; and any of the
    seven normalized keys, had it re-entered drift, still raises
    `UNSUPPORTED_MATERIAL_FEATURE:<key>` — fail-closed at the seam.

  EXTERNAL_IMG2THREEJS_RUNTIME_PROVEN=NO
  (node tests use bounded r169-shaped fakes; production runtime smoke against
   the pinned three r169 checkout belongs to the Owner-side verified profile.)

## Terminal report

```
WORKSTREAM=P2P-IMG2THREEJS-MATERIAL-SEMANTIC-DRIFT-01
BASE_MAIN_SHA=40334bff7f078a903702f76ba2412fdb157fce92 (matches expected; main unmoved)
FULL_DRIFT_INVENTORY_COVERED=YES
EXPECTED_POSITIVE_POST_NORMALIZATION_DRIFT=[["color","color"],["roughness",0.75]]
VERSION_BOOKKEEPING_RULE=ignore iff live AND base are finite non-negative safe integers; malformed -> MATERIAL_VERSION_INVALID (fail closed)
DEFINES_SEMANTIC_EQUALITY=both plain records (Object.prototype/null proto), exact Reflect.ownKeys universe, Object.is-equal string/finite-number/boolean values; else drift
ENVMAP_ROTATION_SEMANTIC_EQUALITY=both isEuler, finite x/y/z Object.is-exact, identical valid order; else drift
IRIDESCENCE_RANGE_SEMANTIC_EQUALITY=both real length-2 arrays, two finite Object.is-exact entries; else drift
INACTIVE_ENVMAP_INTENSITY_RULE=ignore iff envMap null/undefined AND value finite; active envMap -> texture+numeric drift fail closed
INACTIVE_CLEARCOAT_ROUGHNESS_RULE=ignore iff clearcoat===0 AND value finite; clearcoat>0 -> clearcoat+companion drift fail closed
INACTIVE_SHEEN_COLOR_RULE=ignore iff sheen===0 (color path; texture gate precedes); sheen>0 -> sheen+["sheenColor","color"] drift fail closed
COLOR_PROJECTED_PRESERVED=YES
ROUGHNESS_PROJECTED_PRESERVED=YES
ACTIVE_ENVMAP_FAIL_CLOSED=YES
ACTIVE_CLEARCOAT_FAIL_CLOSED=YES
ACTIVE_SHEEN_FAIL_CLOSED=YES
GENERIC_USERDATA_INVARIANT_PRESERVED=YES
MATERIAL_SUPPORT_EXPANDED=NO
PROJECTED_MATERIAL_KEYS_CHANGED=NO
FIXTURE_CHANGED=NO
UPSTREAM_CHANGED=NO
GAME_REPO_CHANGED=NO
CAPABILITY_ACTIVATED=NO
OVER_ENGINEERING_CHECK=PASS
NEXT_STEP=INDEPENDENT_SUPERVISOR
```
