# Asset Forge Protocol

Status: CANDIDATE — awaiting Owner gate
Date: 2026-08-29
Workstream: P2P-GAME-ASSET-FORGE-01
Parent catalog: `docs/p2p-development/capability-catalog/game-asset-forge/capability-catalog.json`

## Preferred law

REFERENCE → OFFLINE ASSET FORGE → DURABLE ASSET → STANDARDIZATION → OPTIMIZATION → PROJECT REPOSITORY → LIGHTWEIGHT GAME RUNTIME → ACTUAL BROWSER QA

Durable outputs only: GLB, GLTF, VRM, TEXTURES, ANIMATION_CLIPS, BAKED VFX DATA.

Heavy AI generation systems belong in OFFLINE ASSET FORGE, not inside the shipped web/mobile game.

## Distinct stages (must not collapse)

GENERATION != RIGGING != SKINNING != RUNTIME != MOTION != EXPRESSION

## Character pipeline

IMAGEGEN_REFERENCE (`visual.gpt_image_2_style_library`)
→ CHARACTER_MESH_GENERATION (`game.character.generate`)
→ RIG/SKIN (`game.character.rig`)
→ VRM_OR_GLTF_STANDARDIZATION
→ MOTION/EXPRESSION (`game.animation.motion_forge`, `game.character.expression`)
→ CHARACTER_LAB
→ THREEJS_RUNTIME (`game.character.runtime` / three-vrm)
→ ACTUAL_BROWSER_VISUAL_QA (`game.majid.threejs_qa_release`)

CODE_PASS != VISUAL_PASS. SANDBOX_ARTIFACT != OWNER_VISIBLE_EVIDENCE.

## Weapon / prop pipeline

IMAGEGEN_REFERENCE → IMG2THREEJS_OR_APPROVED_RECONSTRUCTION (`img2threejs`)
→ COMPONENT_HIERARCHY → MATERIAL → PIVOT/SOCKET/COLLIDER → ASSET_LAB
→ OPTIMIZATION (`game.mengto.performance`) → GAME_INTEGRATION (`game.mengto.hybrid_assets`)

Do not alter img2threejs security semantics: deny network, allowlisted entrypoints, no CS2 metadata, no Mixamo auto-rig, no arbitrary plugin execution.

## Animation pipeline

ACTION_SPEC → APPROVED_MOTION_SOURCE → MOTION_QA → RETARGET → BAKE → ANIMATION_CLIP → GAME_STATE_MACHINE

kimodo and MoMask are CONDITIONAL. They are not approved before owner gate.

## VFX pipeline

SKILL_SPEC → PARTICLE_OR_SHADER_AUTHORING → VFX_LAB → PERFORMANCE_GATE → GAME_INTEGRATION

Evaluate particles (`game.vfx.particles`), shaders (`game.vfx.shader`), editor tooling, and runtime dependencies separately.

## Terrain / environment

Separate TERRAIN_GEOMETRY, VEGETATION/INSTANCING, MATERIALS, ATMOSPHERE, WEATHER, AUTHORED_LANDMARKS.

Procedural Three.js is appropriate for terrain, layout, weather, shaders, VFX, simple geometry, instancing, runtime composition.

Procedural primitives are NOT the default final-asset pipeline for hero characters, faces, hair, complex clothing, monsters, signature weapons/architecture, facial expressions, or production animation.

## Project routing

Profiles: WEB_APP, MOBILE_APP, 2D_GAME, THREEJS_GAME, R3F_GAME.

Asset Forge capabilities normally route to THREEJS_GAME and R3F_GAME only.

Default: OPTIONAL, GOAL_BASED, PROJECT_SELECTIVE. No global activation.

## Arena consumption

PROJECT GOAL → P2P SELECTS MINIMUM CAPABILITIES → PROJECT PROJECTION → ARENA RECEIVES CONTRACT → OFFLINE ASSET FORGE IF NEEDED → FINAL ASSET ENTERS GAME REPO → ARENA INTEGRATES RUNTIME → ACTUAL BROWSER QA

Reuse existing router, registry, projection, and profile system. Do not create a second ontology.

## Selected MPFB2 character adapter contract

For the already-selected Character Forge stack, `game.character.generate` is
the existing P2P capability surface. The bounded adapter binds MPFB2 `2.0.17`
to release commit `80919fa4682335c41847f761a4d79dcad4124732` and source tree
`189a1d6694515ecfbdc40067218c5024389b4e43`. It does not add a registry,
router, projection system, or generic shell executor.

The executable input is a strict `p2p-character-recipe/1` JSON recipe. The
six-view `p2p-visual-reference-pack/1` is supervised visual reference only:
full-body front, full-body 3/4, full-body side, full-body back, face front,
and face 3/4. Reference images inform authoring and review; they are not
automatic MPFB2 reconstruction input and are not passed to the forge command.
Unknown recipe keys are rejected.

The first lane is `CORE_CC0_ONLY`. MPFB2 tool code is GPL-3.0-or-later while
the bundled MPFB2 core graphical assets are CC0-1.0. Those are separate legal
objects: the P2P adapter does not vendor or redistribute MPFB2 source into
Game Truyện, and exported GLB provenance records the upstream boundary without
asserting GPL control over the generated character asset. Any MPFB2 tool
redistribution remains subject to its GPL obligations. Third-party assets are
denied by default; a user-supplied custom asset requires a separate rights
gate and manifest.

The eventual invocation is a preprovisioned, hash-verified local Blender
background process with one allowlisted P2P entrypoint, explicit per-job
workspace and output root, path and symlink containment, minimal environment,
no inherited secrets, network denied, bounded timeout, process-tree
termination, and fail-closed undeclared-output detection. Provisioning is a
separate process from forge execution. This adapter lane performs no Blender,
MPFB2, Golden Character, or Game Truyện execution.

The required durable output is `<character_id>.glb` plus
`<character_id>.asset-provenance.json`. Structural validation requires glTF
2.0, a scene-reachable mesh, skin, `JOINTS_0`, `WEIGHTS_0`, rooted skeleton,
GameEngine rig provenance, and embedded or hash-bound resources. A future
downstream smoke may independently parse the GLB, load it with Three.js
`GLTFLoader`, check skeleton/skin presence, exercise Character Lab, and then
run browser QA. None of those downstream or visual claims are made here.
