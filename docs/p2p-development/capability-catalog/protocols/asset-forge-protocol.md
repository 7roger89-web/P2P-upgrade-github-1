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
