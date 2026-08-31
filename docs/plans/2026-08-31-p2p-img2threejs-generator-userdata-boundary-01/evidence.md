# P2P-IMG2THREEJS-GENERATOR-USERDATA-BOUNDARY-01 — Generator-Owned `Material.userData` Separation

## Metadata

- Date: `2026-08-31`
- Workstream: `P2P-IMG2THREEJS-GENERATOR-USERDATA-BOUNDARY-01`
- Downstream capability: `game.three.asset.static_glb_standardize` (via the
  `img2threejs.static_projection` seam)
- Fresh main: `cbf26b4d5380656743eddbbdc55c4924cd09ce36`
  tree `d75d33a83488c99d168b5ade9b2f319ef3477ab2` (matches expected; main has
  NOT advanced past PR37)
- Mode: bounded generator-metadata separation at the verified
  generator/harness boundary. No material architecture reopening, no material
  support expansion, no registry change, no pin change, no Game Truyện change.

## Proven production blocker

After PR37, the production smoke still terminated at:

```
UNSUPPORTED_MATERIAL_FEATURE:userData
```

with every earlier stage green (strict fixture validation, verified Three
`r169` runtime, factory generation, Object3D creation,
`MeshPhysicalMaterial` creation, default `attenuationDistance=Infinity`
classified `RUNTIME_DEFAULT`, empty `userData` classified `DEFAULT`).

## Root cause — CONFIRMED

The verified generated factory itself populates `Material.userData`.

Read directly from the pinned upstream generator at the exact pinned identity
(`.p2p/vendor/skill/img2threejs-safe-exec-1.5.1` contract:
`UPSTREAM_SHA=dede5909be4e494b228c801a55dda47439143932`,
`UPSTREAM_TREE=25bcd4e1f1a487b9a61d69ade257342a3da767e3` — both re-verified
against the fetched object), file
`forge/stage3_build/generate_threejs_factory.py`, inside
`createSculptMaterial`, lines 3387–3394:

```js
material.userData.sculptMaterial = spec;
material.userData.proceduralMapsIndependent = true;
material.userData.pbrConstraints = { albedoRange: [30, 240], binaryMetalness: true, f0Range: [0.02, 1], iorRange: [1, 2.5] };
material.userData.pbrTextureSource = textures?.source ?? 'flat-fallback';
material.userData.referencePbr = spec.referencePbr ?? null;
material.userData.referenceMaterialId = spec.referenceMaterialId ?? spec.materialReference?.profileId ?? null;
material.userData.materialEvidence = spec.materialEvidence ?? null;
material.userData.validationViews = spec.materialReference?.validationViews ?? [];
```

These eight assignments are **unconditional** inside `createSculptMaterial`
— there is no branch within it that omits them — and every material produced
through `createSculptMaterial` (called at lines 3457 and 3502) therefore
carries non-empty `userData` with exactly the eight keys the smoke observed.
The proven positive production route uses `createSculptMaterial` for its
materials. The generator additionally contains an inline
`?? new THREE.MeshStandardMaterial({ color: 0x888888 })` fallback for
unresolved material references (lines 3504 and 3817); that path may exist,
and it does not invalidate this root cause: a fallback material carries the
freshly allocated empty `userData` that PR37 already classifies as DEFAULT,
and it does not carry the eight generator keys. The classifier treats it
exactly like any other default material — `separateGeneratorMaterialMetadata`
returns `present: false`, nothing is detached, and the generic rule applies.

Therefore the positive fixture legitimately produces non-empty `userData`, and
PR37's generic rule — any arbitrary/non-empty `userData` reaching
`img2threejs_material_snapshot.mjs` is fail-closed drift, which
`_static_material` turns into `UNSUPPORTED_MATERIAL_FEATURE:userData` — is
**correct** and correctly fired.

```
ROOT_CAUSE_CONFIRMED=YES
ROOT_CAUSE=VERIFIED_GENERATOR_POPULATES_MATERIAL_USERDATA
GENERATOR_KEY_UNIVERSE_MATCHES_OBSERVED=YES   (8/8 exact)
GENERATOR_ASSIGNMENTS_CONDITIONAL=NO          (unconditional in createSculptMaterial)
```

## Architectural boundary

`img2threejs_material_snapshot.mjs` is **byte-for-byte unchanged**
(`git diff` against `cbf26b4` is empty). It remains the generic
appearance-snapshot authority with its invariant intact:

- two default-equivalent empty plain `userData` records → `DEFAULT`
- ANY arbitrary/non-empty `userData` reaching it → drift → fail closed

No generic `userData` support was added and `userData` was NOT added to
`PROJECTED_MATERIAL_KEYS` (still `{color, opacity, metalness, roughness}`).

The separation is implemented at the verified generator/harness boundary
instead, which is the only place that knows the factory came from the pinned
verified generator entrypoint:

- NEW `img2threejs_generator_metadata.mjs` — the narrowly scoped classifier.
- `img2threejs_static_projection_harness.mjs` — applies it in
  `snapshotMaterial`, strictly **before** `materialSnapshot`, and records the
  bake attestation.

## Generator-metadata classifier

`GENERATOR_NON_APPEARANCE_METADATA` is returned only when ALL hold:

- **A** `userData` is a plain record (`Object.prototype` or `null` prototype;
  not array/Map/Set/class instance/Date/typed array).
- **B** Every own key (via `Reflect.ownKeys`) is in the verified pinned
  generator key universe. An unknown additional key fails closed. A subset of
  the universe is accepted (rule B is "every own key is expected").
- **C** No symbol key and no non-enumerable/accessor property can bypass:
  `Reflect.ownKeys` + `Object.getOwnPropertyDescriptor` cover symbols and
  non-enumerables, and `safeLabel` sanitises any key embedded in a fail code
  so no key value can forge an extra `P2P_IMG2THREEJS_BAKE_FAIL` stdout line.
- **D** Every value is inert bounded JSON-like data: `null`, boolean, string,
  finite number, array, plain record. Rejected: function, bigint, symbol,
  `undefined`, `NaN`, `±Infinity`, class instances, Map/Set, prototype-exotic
  values, cycles (explicit `Set`-based ancestor detection), depth > 16,
  node count > 16384, string > 65536.

Bounds are small and are a safety net, not a serialization framework. Note
that the `NaN`/`Infinity` rejection is load-bearing, not theoretical:
`json_literal` in the pinned generator is a bare `json.dumps`, which emits
`NaN`/`Infinity` as live JS identifiers, so a non-finite spec value would
really arrive in `userData`.

No narrowly justified variant of the data contract was needed — the real
pinned generator metadata is a `json.dumps` literal of the strict-validated
spec, which is shallow, acyclic, and inert by construction.

## Separate, do not launder

On a classifier pass only:

- classification `GENERATOR_NON_APPEARANCE_METADATA`
- `userData` is detached (replaced with an empty plain record) so the generic
  snapshot provably never observes it, and `restore()` puts the original back
  so the live material is not left silently mutated
- the exact sorted key list is attested in the bake manifest

Why this cannot launder appearance: `userData.sculptMaterial` **describes**
the authored spec; it is not the live appearance. The same
`createSculptMaterial` also sets the live properties (`color`, `roughness`,
`metalness`, `transmission`, `clearcoat`, `sheen`, `iridescence`,
`attenuationDistance`, texture slots, `emissive`, …). Those are still
snapshotted and still fail closed. If the spec declared `transmission: 0.4`,
the live `material.transmission` is `0.4` and the projection still rejects —
proven by test at both the module and the harness level.

Bake attestation (new bake-manifest field, bound by the existing
`factory_sha256` → `BAKE_FACTORY_BINDING_MISMATCH` gate):

```json
"generator_material_metadata": { "present": true, "keys": ["materialEvidence", "pbrConstraints", "pbrTextureSource", "proceduralMapsIndependent", "referenceMaterialId", "referencePbr", "sculptMaterial", "validationViews"] }
```

The field never enters the static GLB material contract; asserted by test that
the serialized projected asset contains none of the eight keys, no `userData`,
and no `generator_material_metadata`, and that the material surface stays
exactly `{type, color, opacity, metalness, roughness}`.

## Focused evidence

| # | Requirement | Where | Result |
| --- | --- | --- | --- |
| 1 | standalone `materialSnapshot` still rejects arbitrary non-empty `userData` | node (generator-metadata suite) | PASS |
| 2 | verified-generator metadata separated before `materialSnapshot`; default appearance material passes | node ×2 (module + harness process) | PASS |
| 3 | separation records bake attestation | node (real harness subprocess) | PASS |
| 4 | arbitrary `{customTag:"x"}` fails closed | node ×2 (module + harness) | PASS |
| 5 | expected keys + one unknown key fails closed | node ×2 (module + harness) | PASS |
| 6 | symbol/hidden/non-plain/cyclic/non-finite fails closed | node ×2 (module + harness, 9 harness cases) | PASS |
| 7 | active transmission still fails | node ×2 + python seam | PASS |
| 8 | active clearcoat still fails | node ×2 + python seam | PASS |
| 9 | default `Infinity` remains PASS | node ×2 (module + harness) | PASS |
| 10 | factory SHA binding still enforced | python (match → PROJECTED; mismatch → `BAKE_FACTORY_BINDING_MISMATCH`) | PASS |

Representative fail-closed codes observed on the real harness stdout:

```
P2P_IMG2THREEJS_BAKE_FAIL GENERATOR_MATERIAL_METADATA_UNKNOWN_KEY:customTag
P2P_IMG2THREEJS_BAKE_FAIL GENERATOR_MATERIAL_METADATA_NOT_PLAIN_RECORD
P2P_IMG2THREEJS_BAKE_FAIL GENERATOR_MATERIAL_METADATA_UNKNOWN_KEY:SYMBOL
P2P_IMG2THREEJS_BAKE_FAIL GENERATOR_MATERIAL_METADATA_HIDDEN_KEY:materialEvidence
P2P_IMG2THREEJS_BAKE_FAIL GENERATOR_MATERIAL_METADATA_CYCLIC
P2P_IMG2THREEJS_BAKE_FAIL GENERATOR_MATERIAL_METADATA_NON_INERT_VALUE:sculptMaterial
```

## Supervisor delta — restore-before-terminal-fail (FIX_PR39_USERDATA_RESTORE_BEFORE_TERMINAL_FAIL)

Finding (REJECT — USERDATA_RESTORE_SEMANTICS): in `snapshotMaterial()`, a
`materialSnapshot` failure was translated by calling `fail()` directly from
the `catch`. `fail()` calls `process.exit(1)`, which terminates Node
synchronously, so the enclosing `finally` never ran and `separation.restore()`
was skipped — a material could be left with its generator `userData` detached
when a terminal failure followed.

Fix (control flow only): the `catch` now CAPTURES the failure
(`error.code` when present, else `MATERIAL_SNAPSHOT_FAILED`); the `finally`
restores on every path; the captured failure is translated through `fail()`
AFTER the `finally`. The success path is unchanged (`return snapshot`). No
change to `img2threejs_material_snapshot.mjs`, `img2threejs_adapter.py`, the
metadata key universe, `PROJECTED_MATERIAL_KEYS`, material support, the
factory SHA binding, the scale/world-bake contracts, the Three pin, the
fixture, or the attestation format.

Regression proof (5 tests appended to the projection-harness node suite, run
against the REAL harness process with an instrumented `userData` setter that
logs every `DETACH:<i>` / `RESTORE:<i>` assignment):

| Case | Observed |
| --- | --- |
| success, valid generator metadata | `DETACH:0`, `RESTORE:0`, manifest written, exit 0 |
| coded terminal fail (`attenuationDistance=NaN`, valid generator metadata) | `DETACH:0`, `RESTORE:0` BEFORE `P2P_IMG2THREEJS_BAKE_FAIL MATERIAL_NONFINITE:attenuationDistance`, exit 1, no manifest |
| uncoded `materialSnapshot` exception | `DETACH:0`, `RESTORE:0` BEFORE `MATERIAL_SNAPSHOT_FAILED`, exit 1 |
| classifier rejection (`customTag`) | no `DETACH`/`RESTORE` at all — rejection throws before any mutation, nothing to restore, fail-closed code unchanged |
| two materials, second fails terminally | `DETACH:0`, `RESTORE:0`, `DETACH:1`, `RESTORE:1` BEFORE the terminal fail — per-mesh restoration including the failing mesh |

Mutation check: re-introducing the defective ordering (`fail()` inside
`catch`) against the fixed suite fails exactly the three restore-before-
terminal-fail tests (10/13 pass); with the fix, 13/13 pass. Evidence
wording for the `createSculptMaterial` universality claim corrected in the
Root cause section above and in both file headers (fallback
`?? new THREE.MeshStandardMaterial(...)` path acknowledged).

## Appearance safety preserved

| Behaviour | Result |
| --- | --- |
| default `attenuationDistance=Infinity` → runtime default | PASS (no drift, nothing non-finite leaks) |
| `NaN` → reject | PASS (`MATERIAL_NONFINITE:attenuationDistance`) |
| non-default `±Infinity` → reject | PASS (`MATERIAL_NONFINITE:attenuationDistance`) |
| active finite `attenuationDistance` → unsupported drift | PASS |
| active transmission → unsupported | PASS |
| active clearcoat → unsupported | PASS |
| textures / emissive / other unsupported features | PASS (unchanged rules) |
| `MeshPhysicalMaterial` narrowing only after all drift cleared | PASS |

## Test counts

```text
material snapshot node      = 16/16  (unchanged file; pristine-base baseline is also 16/16)
generator metadata node     = 17/17  (NEW)
projection harness node     = 13/13  (NEW; real harness subprocess; 8 base + 5 restore-delta tests)
projection seam python      = 39/39  (baseline 30/30, +9)
static GLB standardizer     =  7/7   (code untouched; run only as a downstream guard)
BROAD_TESTS_RUN             = NO
```

Note on a prior count: PR37's evidence file records the material snapshot node
suite as `15/15`. The file at `cbf26b4` actually contains 16 `test()`
invocations and passes 16/16 both at the pristine base and now. The number in
this document is the measured one.

## Scope guards

```text
MATERIAL_SNAPSHOT_GENERIC_INVARIANT_PRESERVED = YES (file byte-identical to cbf26b4)
PROJECTED_MATERIAL_KEYS_CHANGED               = NO
STATIC_GLB_CONTRACT_CHANGED                   = NO
MATERIAL_SUPPORT_EXPANDED                     = NO
UPSTREAM_CHANGED                              = NO
FIXTURE_CHANGED                               = NO
THREE_VERSION_OR_RUNTIME_PIN_CHANGED          = NO
PR35_THREE_RESOLUTION_CHANGED                 = NO
TARGET_MAJOR_EXTENT_METERS_CONTRACT_CHANGED   = NO
WORLD_MATRIX_BAKE_CHANGED                     = NO
GAME_REPO_CHANGED                             = NO
REGISTRY_CHANGED                              = NO
CAPABILITY_ACTIVATED                          = NO
DEPENDENCIES_INSTALLED                        = NO
BLENDER_RUN                                   = NO
GOLDEN_WEAPON_RUN                             = NO
WINDOWS_PRODUCTION_SMOKE_RUN                  = NO
MERGED                                        = NO
PUBLIC_ESCAPE_HATCH_ADDED                     = NO
```

## Files changed

```text
M  .p2p/system/p2p_capabilities/img2threejs_static_projection_harness.mjs
M  .p2p/system/p2p_capabilities/tests/test_img2threejs_static_projection.py
A  .p2p/system/p2p_capabilities/img2threejs_generator_metadata.mjs
A  .p2p/system/p2p_capabilities/tests/img2threejs_generator_metadata.node_test.mjs
A  .p2p/system/p2p_capabilities/tests/img2threejs_static_projection_harness.node_test.mjs
```

Untouched, verified by empty diff against `cbf26b4`:
`img2threejs_material_snapshot.mjs`, `img2threejs_adapter.py`,
`static_glb_standardizer.py`, `.p2p/vendor/skill/**`.

## Verdict

```text
STATUS=CANDIDATE (bounded, fail-closed; not activated)
GENERATOR_MATERIAL_METADATA_CLASSIFICATION = GENERATOR_NON_APPEARANCE_METADATA
ARBITRARY_NONEMPTY_USERDATA_FAIL_CLOSED    = YES
EXECUTION_AUTHORIZED                       = NO
NEXT_STEP=INDEPENDENT_SUPERVISOR
TERMINAL_VERDICT=P2P_IMG2THREEJS_GENERATOR_USERDATA_BOUNDARY_PR_READY
```
