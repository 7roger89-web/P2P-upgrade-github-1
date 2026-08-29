# P2P img2threejs safe execution contract

This is a P2P-authored selective projection contract. It is not a copy of the
upstream repository and it is not permission to execute arbitrary upstream
code. The upstream checkout remains external, exact-pinned, and must be bound
through the P2P adapter before any command is launched.

## Identity and provenance

- `UPSTREAM_REPOSITORY`: `https://github.com/img2threejs/img2threejs.git`
- `UPSTREAM_VERSION`: `1.5.1`
- `UPSTREAM_SHA`: `dede5909be4e494b228c801a55dda47439143932`
- `UPSTREAM_TREE`: `25bcd4e1f1a487b9a61d69ade257342a3da767e3`
- `LICENSE`: `Apache-2.0`
- `PROJECTION_MODE`: `SELECTIVE_ON_DEMAND`
- `VENDOR_MODE`: `P2P_CONTRACT_ONLY; UPSTREAM_SOURCE_EXTERNAL`

The adapter must verify the exact commit, tree, required entrypoints, and a
clean ordinary Git worktree before invocation. A floating upstream `main`, a
different tree, missing source, or drifted entrypoint is a hard failure.

## When to use / when not to use

Use this capability for a bounded image/reference-grounded procedural Three.js
reconstruction workflow, especially when a project needs a deterministic local
spec, staged geometry/code generation, or a later Character Lab / Asset Lab
protocol.

Do not use it for neural image-to-mesh claims, automatic production animation,
unbounded web or CS2 metadata intake, arbitrary vision/plugin execution,
provider installation, deployment, or visual acceptance without a real browser
runtime and durable evidence. Use the existing P2P router; this contract never
creates a second router, council, orchestrator, or certification system.

## Execution boundary

Only the following upstream entrypoints are adapter-allowlisted:

1. `forge/state.py`
2. `forge/next.py`
3. `forge/stage1_intake/probe_image.py`
4. `forge/stage2_spec/validate_sculpt_spec.py`
5. `forge/stage3_build/generate_threejs_factory.py`

The following remain denied, even though they exist upstream:

- `forge/stage1_intake/fetch_cs2_metadata.py`
- `forge/stage1_intake/material_region_analysis.py`
- `forge/stage1_intake/run_vision_adapter.py`
- every unlisted script, plugin, renderer, installer, or subprocess route

The adapter contract is:

- `NETWORK_POLICY=DENY` by default;
- `CS2_METADATA_NETWORK=DISABLED` for Thiên Hạ;
- remote reference URLs are rejected;
- state, reference, spec, temporary files, generated output, and evidence stay
  below the declared reconstruction workspace;
- identifiers are restricted to safe ASCII names and reject separators, `..`,
  absolute paths, and root escape;
- subprocesses use an explicit argv list, `shell=False`, stdin closed, a bounded
  timeout, and a minimal environment without inherited secrets;
- `--allow-nonstrict` is not exposed by the adapter;
- no shell command may be derived from reference metadata;
- missing capability, pin mismatch, dirty source, output escape, and policy
  override all fail closed.

The upstream CS2 intake has an unrestricted URL path and the material-region
route has insufficient identifier/path containment. Those routes are not
patched into an apparent safe state; they are denied before invocation.

## Character protocol: THIEN-HA-3D-02

The future Golden Character route accepts a consistent reference pack of up to
six preferred views:

1. front full body;
2. 3/4 full body;
3. side full body;
4. back full body;
5. face front close-up;
6. face 3/4 close-up.

The `CHARACTER_REFERENCE_CONTRACT` must record:

- `IDENTITY_CONSISTENT=YES`;
- `BODY_PROPORTIONS_CONSISTENT=YES`;
- `CLOTHING_CONSISTENT=YES`;
- `SCALE_CONSISTENT=YES`;
- view identity, source provenance, and unresolved ambiguity for every supplied
  image.

Multiple views are reference/evidence constraints. They do not imply that the
current upstream performs mature automatic six-view fusion.

The minimum reusable character contract is:

```text
CHARACTER_BODY
SKELETON
ATTACHMENT_SOCKETS_OR_BONES
APPEARANCE_MANIFEST
ANIMATION_STATE_CONTRACT
INDEPENDENT_VISUAL_LAYERS
SAVE_COMPATIBLE_APPEARANCE_DESCRIPTOR
SAFE_MISSING_LAYER_FALLBACK
CHARACTER_LAB
```

Where technically appropriate, `INDEPENDENT_VISUAL_LAYERS` keep robe, hair,
weapon, cloak, and accessories separable. This is a future protocol, not the
implementation of the Thiên Hạ character system.

The first Golden Character objective is only:

```text
REFERENCE
-> RECONSTRUCTION
-> ACTUAL BROWSER RENDER
-> VISUAL COMPARISON
-> ACCEPTABLE CHARACTER QUALITY
```

Complete outfit persistence and animation are not prerequisites for that first
visual proof.

## Character maturity limits

The pinned v1.5.x material supports a character/hybrid route with anatomy and
head-unit measurement, facial landmarks, component-derived skeleton data,
SkinnedMesh/geodesic-skinning-related contracts, pivots/sockets/attachments,
character review gates, hair guidance, resumable state, and a browser/render
evidence loop where independently verified at the source boundary.

These claims do not mean a complete production animation stack:

- `FULL_PRODUCTION_AUTO_RIG=NOT_PROVEN`
- `GENERAL_AUTO_RIG=NOT_CLAIMED`
- `MIXAMO_COMPATIBILITY=NOT_CURRENT_BASELINE`
- `FACIAL_RIG_COMPLETE=NOT_CURRENT_BASELINE`
- `PRODUCTION_ANIMATION_PIPELINE=NOT_PROVEN`

## Asset Forge protocol: THIEN-HA-3D-04

Golden Weapon / Asset Forge is a separate hard-surface/object route and does
not depend on unfinished character animation work:

```text
IMAGEGEN_OR_CURATED_REFERENCE
-> ASSET_REFERENCE_CONTRACT
-> DETAIL_INVENTORY
-> PROJECTION_OR_GEOMETRY_RECONSTRUCTION
-> COMPONENT_HIERARCHY
-> PIVOTS_SOCKETS_COLLIDERS
-> BROWSER_ASSET_LAB
-> VISUAL_QA
-> GAME_INTEGRATION
```

Character and hard-surface maturity must be reported separately. A code
generation pass is not a weapon visual-quality claim.

## Browser Lab and Arena evidence law

`CODE_ONLY_PASS != VISUAL_PASS`.

Future Character Lab / Asset Lab acceptance must include a deterministic,
loadable subject; orbit/camera inspection; applicable front, 3/4, side, and
back views; reference-versus-render comparison; socket/attachment inspection
when relevant; console-error check; visible missing-layer fallback; and durable
screenshots. A screenshot is evidence of a rendered state, not automatic proof
of acceptable quality; the comparison and reviewer result must remain linked.

The Arena evidence chain is:

```text
actual browser/runtime
-> screenshot
-> durable candidate-branch file
-> PR inline image
-> URL pinned to exact candidate SHA
-> Owner-visible on mobile
```

Future generated Arena prompts must make routing explicit:

```text
DESTINATION=ARENA AI
SESSION_ACTION=CONTINUE_CURRENT_SESSION | START_NEW_SESSION
SESSION_GOAL=<bounded goal>
PR_EXPECTATION=<explicit evidence/PR expectation>
```

`GOLDEN_CHARACTER_READY_FOR_FUTURE_EXECUTION=YES` and
`GOLDEN_WEAPON_READY_FOR_FUTURE_EXECUTION=YES` mean protocol/routing readiness
only. Visual acceptance remains `NOT_PROVEN` until the future project runtime
produces the required independent evidence.

## Projection and return contract

Project only this contract, exact provenance pointers, adapter instructions,
protocol fields, bootstrap/read-order hooks, and evidence requirements. Do not
copy the full P2P runtime or the upstream repository into a target project.

Every future execution return must include the exact upstream SHA/tree, adapter
entrypoint, reconstruction-workspace-relative output, network-used flag,
shell-used flag, and redacted stdout/stderr hashes. It must distinguish:

- local technical execution;
- browser/runtime proof;
- visual QA result;
- Owner-visible Arena evidence;
- Owner approval or promotion.

Technical readiness never authorizes promotion, release, deployment, or live
activation.
