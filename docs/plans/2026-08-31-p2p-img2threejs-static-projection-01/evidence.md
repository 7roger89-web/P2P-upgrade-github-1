# P2P-IMG2THREEJS-STATIC-PROJECTION-01 — Seam Resolution Evidence

## Metadata

- Date: `2026-08-31`
- Workstream: `P2P-IMG2THREEJS-STATIC-PROJECTION-01`
- Downstream capability: `game.three.asset.static_glb_standardize`
- Fresh main: `1163f69ebbdf33aab7a8c24097b823a8c5823f6a`
  tree `15246cd7a9e4593716e433c8823a2fd7683d5ca2`
- Pinned upstream audit subject: `img2threejs` v1.5.1, commit
  `dede5909be4e494b228c801a55dda47439143932`, tree
  `25bcd4e1f1a487b9a61d69ade257342a3da767e3` (per
  `.p2p/system/p2p_capabilities/img2threejs_adapter.py` and
  `.p2p/vendor/skill/img2threejs-safe-exec-1.5.1/SKILL.md`)
- Mode: repo-side read-only probe; no checkout install, no execution,
  no code or registry change.

## E1 — Source-contract resolution

- `E1-SRC1`: the narrowest existing structured source surface is the
  ObjectSculptSpec JSON (`forge/stage2_spec/new_sculpt_spec.py` emitter,
  `forge/stage2_spec/validate_sculpt_spec.py` gate, already allowlisted
  through the P2P adapter). It carries the component tree, parented
  transforms, materials, and quality/pre-spec structures. No generated
  TypeScript is parsed.
- `E1-SRC2`: the spec does NOT contain baked static mesh data. Geometry is
  a procedural recipe (`primitive`, `geometryDescriptor`,
  `deformationStack`, `edgeTreatment`, SDF/vertex-paint parameters);
  vertex positions and indices exist only after `generate_threejs_factory.py`
  codegen executes against a Three.js runtime. A
  bounded mesh/material JSON projection (the `p2p-static-glb-asset/1`
  input contract: flat numeric `positions`, triangle `indices`) is
  therefore not derivable from the spec by pure data projection.
- Decision: `PROJECTION_SOURCE=NO_SAFE_SOURCE` for a static-projection
  seam that neither parses/compiles generated TypeScript nor runs the
  upstream runtime (both explicitly out of scope).

## E2 — Unit-scale contract probe (fail-closed finding)

All citations are at the pinned v1.5.1 commit above.

- `E2-U1`: `new_sculpt_spec.py` hard-codes component
  `dimensions.units = "relative"` (lines 294, 1978) and
  `imageRegion.units = "normalized"` (line 1941). No `meters`, absolute
  size, or conversion factor is ever emitted.
- `E2-U2`: `validate_sculpt_spec.py` defines no `units` semantics:
  `validate_dimensions` (line 1045) checks numeric fields only; there are
  zero `meters`/absolute-scale validations in the file.
- `E2-U3`: `generate_threejs_factory.py` confirms unit-free scene space:
  vertex-paint regions stay "in the same units as the component's
  measured dimensions" (line ~1612); instance scale is "ABSOLUTE, in the
  parent pivot's local units" and "never multiplied by the parent
  component's own declared [scale]" (lines ~3819-3822) — all in relative
  "world units". Authoring guidance references only approximations
  ("0.02 world-unit seam overlap"; character "HU ~= 0.28 world units"),
  which are stylization heuristics, not a scale contract.
- `E2-U4`: the P2P-side canonical record agrees: the vendor contract
  (`.p2p/vendor/skill/img2threejs-safe-exec-1.5.1/SKILL.md`) documents
  "head-unit measurement" for the character profile and a
  reference-consistency `SCALE_CONSISTENT=YES` field; neither defines a
  relative-unit -> meters mapping for static objects.
- Decision: no authoritative relative->meters scale mapping exists at the
  pinned canon. Per the workstream instruction, no conversion is invented
  (`1 relative unit = 1 meter` is a guess and is prohibited).

## E3 — Consequence for the seam and the composition test

- The standardizer input contract
  (`game.three.asset.static_glb_standardize`, `p2p-static-glb-asset/1`)
  requires `units=meters`, `up_axis=Y`, `transform.space=flat`, and baked
  numeric meshes. An img2threejs spec projection can satisfy none of
  `units`/`meters` (blocked by E2) nor the baked-mesh requirement (blocked
  by E1-SRC2) without redesigning either side.
- No seam module, registry entry, provenance field, or composition test was
  added. Emitting a local fixture that "passes" would manufacture
  representation-level proof of a runtime contract that does not exist —
  prohibited by the evidence law (`CODE_ONLY_PASS != VISUAL_PASS`,
  technical readiness never substitutes for authoritative semantics).
- `game.three.asset.static_glb_standardize` remains
  `img2threejs_seam=MISSING_SEAM` in
  `.p2p/system/p2p_capabilities/capabilities.json`; the record stays
  accurate with this evidence attached.

## Verdict

```text
STATUS=DISCOVERED (no new capability registered)
EXECUTION_AUTHORIZED=NO
RUNTIME_PROVEN=NO
COMPOSITION_TESTED=NO
EXTERNAL_IMG2THREEJS_RUNTIME_PROVEN=NO
FILES_CHANGED=docs/plans/2026-08-31-p2p-img2threejs-static-projection-01/evidence.md
BROAD_TESTS_RUN=NO (no code path changed; static suite baseline 7/7 PASS re-verified on fresh main)
TERMINAL_VERDICT=BLOCKED_UNIT_SCALE_CONTRACT_MISSING
```

## Required Owner-side unblock (either path, not both)

1. `UPSTREAM_UNIT_CONTRACT`: upstream (or an Owner-ratified contract)
   publishes an authoritative absolute-scale mapping for ObjectSculptSpec
   (e.g. a `units:"meters"` dimension mode or a pinned
   `relativeToMeters` factor per profile) at a re-audited commit —
   then the seam can be re-scoped as data-only projection + unit gate.
2. `STATIC_EXPORT_SOURCE`: upstream emits a bounded static mesh artifact
   (baked positions/indices JSON, meters, Y-up) as an allowlisted
   entrypoint — then the seam consumes that export instead of the spec,
   and the composition test becomes meaningful.

Until one exists, the correct composition-testable state of this workstream
is a fail-closed rejection, which the already-promoted standardizer
performs on its own input boundary today (`STATIC_CONVENTION_INVALID`).

---

## E4 — SUPERSESSION: blocked route resolved by Owner-side runtime probe (2026-08-31)

The E1–E3 findings are preserved as accurate for what they examined: the
DATA-ONLY route. They are not retracted. What E1–E3 proved was that no
static projection can be derived from the spec file alone without a
physical-scale contract, and that conclusion stands.

```text
DATA_ONLY_PROJECTION_SOURCE=NO_SAFE_SOURCE
DATA_ONLY_ROUTE=BLOCKED (permanently; do not retry data-only projection)
```

The Owner-side supervisor then executed a disposable runtime feasibility
probe (Node v25.2.1, three@0.169.0, pinned upstream
`dede5909be4e494b228c801a55dda47439143932`, with `--allow-nonstrict` used
only as a test-fixture escape hatch on the probe side). Supervisor return:

```text
RUNTIME_PROBE_VERDICT=P2P_IMG2THREEJS_RUNTIME_STATIC_EXPORT_FEASIBLE
RUNTIME_MATERIALIZATION_SOURCE=PROVEN
WORLD_MATRIX_BAKE_FEASIBLE=YES
Y_UP_RUNTIME_PROVEN=YES
EXPLICIT_PHYSICAL_SCALE_ANCHOR_FEASIBLE=YES
STATIC_STANDARDIZER_COMPOSITION_PROVEN=YES
```

The probe proves the ROUTE, not any production adapter. The blocked
assumptions are superseded only along the replacement route:

1. Geometry: materialized by executing the pinned upstream generator inside
   the existing contained adapter, then baked in the P2P-owned Node harness +
   deterministic Python world-matrix seam (no TypeScript parsing).
2. Units: the absent implicit relative->meters mapping is NOT invented. The
   seam requires an explicit caller anchor
   `TARGET_MAJOR_EXTENT_METERS` applied once to the aggregate
   world-transform-baked bounding box
   (`relative_to_meter_scale = target / baked_relative_major_extent`).
   Missing/invalid anchor, non-positive extent, or empty geometry fail closed.

## E5 — Production seam candidate on PR #33

- Implementation: `.p2p/system/p2p_capabilities/img2threejs_adapter.py`
  extended in place (`bake_static_projection`,
  `verify_static_runtime_profile`, `project_static_asset`) plus the
  P2P-owned contained harness
  `.p2p/system/p2p_capabilities/img2threejs_static_projection_harness.mjs`.
  No new capability ID, registry class, router, provenance store, or Asset
  Forge framework. The operation is recorded on the existing `img2threejs`
  capability as `execution.static_projection` (kind
  `BOUNDED_ADAPTER_OPERATION_NOT_A_NEW_CAPABILITY`); the promoted
  standardizer record keeps its own semantics and only updates
  `img2threejs_seam` to `PROJECTION_CANDIDATE_PR33`.
- Strict quality: production route composes `--strict-quality` validation via
  the existing `_build_argv`; the upstream test-only `--allow-nonstrict`
  hatch is not exposed, accepted, or constructible (asserted by test).
- Containment: per-run workspace directory
  `static-projection/<run-id>/`, fixed generator entrypoints, fixed factory
  and bake paths, argv-only subprocess, `shell=False`, minimal sanitized
  environment (NODE_OPTIONS cleared), bounded timeout and 64 MiB bounded
  output, workspace-relative paths with symlink/reparse rejection retained.
- Runtime profile: exact-pin gate for Node `v25.2.1` and three `0.169.0`
  against the pre-provisioned external runtime; no npm, no bundling, no
  download; wrong/missing/unverified runtime fails closed before any
  generation. Broader compatibility is NOT claimed.
- Static-only: harness rejects skinned meshes, bones, skeletons,
  animations, instanced/line/points/sprite nodes, morph targets,
  non-BufferGeometry, non-finite data; Python re-validates aggregate counters
  and bakes world matrices with duplicate-identity, cycle, and
  missing-parent rejection; output `transform.space=flat` carries no
  hierarchy keys.
- Materials: only the canonical standardizer subset is projected
  (color/opacity/metalness/roughness). Any material property that differs
  from the material class's own runtime default and is not representable by
  the contract (textures, emissive, flat shading, Phong specular/shininess,
  MeshPhysical transmission/thickness/clearcoat/sheen/iridescence/etc.)
  fails closed with `UNSUPPORTED_MATERIAL_FEATURE:<key>`.
  MeshPhysicalMaterial with all-physical-default properties narrows to
  MeshStandardMaterial; equivalence is never silently claimed.
- Responsibility boundary held: the seam emits the normalized projection
  only; GLB writing/validation/provenance stays with
  `game.three.asset.static_glb_standardize` (unchanged).
- Tests: `.p2p/system/p2p_capabilities/tests/test_img2threejs_static_projection.py`
  12/12 PASS, including repo-side composition (bounded synthetic bake-manifest
  fixture -> projection -> standardizer -> validated GLB).
  `test_static_glb_standardizer` remains 7/7; img2threejs exec suite skips
  cleanly without the external checkout; capability-catalog UI suite 35/35.
  Registry `load_registry` valid at 66 entries (no new identity).
- Status: `STATUS=DISCOVERED`-class only (candidate). This sandbox proves no
  external runtime (local Node here is v22.x and is correctly REFUSED by the
  profile gate; the sandbox has no three package).

```text
COMPOSITION_TESTED=YES (repo-side, bounded fixtures)
EXTERNAL_IMG2THREEJS_RUNTIME_PROVEN=NO
PRODUCTION_ADAPTER_RUNTIME_PROVEN=NO
NEXT_RUNTIME_SMOKE=CODEX_WINDOWS_PRODUCTION_ADAPTER_SMOKE
EXECUTION_AUTHORIZED=NO
AUTO_ACTIVATION=NO
```
