# UI / Game UI / Three.js Capability Catalog

Status: CANDIDATE — awaiting Owner gate
Date: 2026-08-29
Parent: `P2P-CAPABILITY-FOUNDATION-ARCHITECTURE-SPEC.md`
Workstream: P2P-GAME-UI-CAP-01

## Purpose

Cross-project reusable capability catalog for UI/UX, frontend, game UI, Three.js/R3F production, design-system workflows, visual authoring, and visual QA. Uses project-profile-based selective activation.

## Architecture Alignment

This catalog **extends** the existing P2P capability foundation:

- `capabilities.json` — canonical capability registry (extended with new entries)
- `research-adoption-ledger.json` — durable research record (extended with RA-EXT-032..049)
- `p2p_uiux/router.py` — the only router (no second router created)
- `p2p_capabilities/domain.py` — optional project domain model (unchanged)
- `project-profile-routing.json` — new routing rules for project profiles

## Files

| File | Purpose |
|---|---|
| `capability-catalog.json` | Structured candidate catalog with provenance, classification, project-profile applicability |
| `project-profile-routing.json` | Project profile → capability routing rules |
| `../protocols/ui-design-protocol.md` | Reusable UI design workflow protocol |
| `../protocols/game-ui-protocol.md` | Reusable game UI/HUD protocol |
| `../protocols/threejs-visual-protocol.md` | Reusable Three.js visual QA protocol |
| `../bootstrap-projection.md` | Bootstrap/projection guidance for new projects |

## Key Invariants

1. **Repository != Capability** — One capability may reference multiple upstream sources.
2. **AVAILABLE_FOR_PROJECT_SELECTION != INSTALLED_GLOBALLY** — Catalog entries are not globally installed.
3. **COMPONENT_FOUNDATION != VISUAL_DIRECTION** — A component library supplies primitives, not product identity.
4. **CODE_PASS != VISUAL_PASS** — Code correctness does not prove visual correctness.
5. **SANDBOX_ARTIFACT != OWNER_VISIBLE_EVIDENCE** — Visual evidence must be durable and accessible.
6. **WORLD/GAME_VIEW = VISUALLY_PRIMARY** — The game world is the star, not the chrome.
7. **GPU_TIER = HEURISTIC** — Never authoritative device capability.
8. **game.three.visual != game.three.spatial_query != game.three.navigation** — Orthogonal concerns.
9. **THREEJS_GAME does not automatically receive R3F-only capabilities.**
10. **WEB_APP does not receive game capabilities by default.**

## Candidate Summary

| ID | Source | Classification | Domain(s) |
|---|---|---|---|
| CAND-GAME-UI-001 | openai/plugins | PATTERN_ONLY | game.ui, ui.frontend |
| CAND-GAME-UI-002 | shadcn-ui/ui | ACCEPT | ui.design_system, ui.frontend |
| CAND-GAME-UI-003 | motiondivision/motion | ACCEPT | ui.motion |
| CAND-GAME-UI-004 | storybookjs/storybook | ACCEPT | ui.component_lab |
| CAND-GAME-UI-005 | gkjohnson/three-mesh-bvh | ACCEPT | game.three.spatial_query |
| CAND-GAME-UI-006 | call-me-sensei/toonlab | CONDITIONAL | game.three.visual |
| CAND-GAME-UI-007 | theatre-js/theatre | CONDITIONAL (LICENSE SPLIT) | game.three.cinematic |
| CAND-GAME-UI-008 | donmccurdy/three-pathfinding | ACCEPT | game.three.navigation |
| CAND-GAME-UI-009 | pmndrs/detect-gpu | CONDITIONAL | game.three.adaptive_quality |
| CAND-GAME-UI-010 | Mojang/ore-ui | CONDITIONAL | ui.game_hud |
| CAND-GAME-UI-011 | pmndrs/uikit | CONDITIONAL | ui.spatial |
| CAND-GAME-UI-012 | hmans/composer-suite | CONDITIONAL | game.three.scene_authoring |
| CAND-GAME-UI-013 | Penpot MCP | SECURITY_GATED | ui.penpot_bridge |
| CAND-GAME-UI-014 | keiththomas1/threespace | RESEARCH_ONLY | game.three.scene_authoring |
| CAND-GAME-UI-015 | pmndrs/triplex | LICENSE_GATED | game.three.scene_authoring |
| CAND-GAME-UI-016 | YG3-ai/Capsule | RESEARCH_ONLY | game.three.scene_authoring |
| CAND-GAME-UI-017 | prnthh/react-three-game | LICENSE_GATED | game.three.scene_authoring |
| CAND-GAME-UI-018 | threejsassets/game-hud | REFERENCE_ONLY | ui.game_hud |

## Classification Counts

| Classification | Count |
|---|---|
| ACCEPT | 5 |
| CONDITIONAL | 6 |
| PATTERN_ONLY | 1 |
| REFERENCE_ONLY | 1 |
| RESEARCH_ONLY | 2 |
| LICENSE_GATED | 2 |
| SECURITY_GATED | 1 |
| REJECT | 0 |

## Required Disclaimer

Implemented against sealed .74 NONCANONICAL DEVELOPMENT BASE. Official canonical baseline remains .19. Release/promotion authority remains deferred.
