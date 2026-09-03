# Video Director Spec Capability Catalog

Status: CANDIDATE — awaiting Owner merge gate
Date: 2026-09-03
Workstream: P2P-VIDEO-CAPABILITY-INTEGRATION-01
Owner authorization: GitHub Issue #71 (`7roger89-web/P2P-upgrade-github-1`)
Registry identity: `video.prompt.director_spec` (exactly one new capability)

## 1. What this catalog is

This is the knowledge catalog for **one** bounded P2P capability:

`video.prompt.director_spec` — `TYPE=KNOWLEDGE_SOURCE`, `SEMANTIC_KIND=SKILL`,
`INVOCATION_CLASS=MODEL_ROUTABLE`, `TRUST_LEVEL=PURE_DATA`, `STATUS=ACTIVE`.

It transforms

```
USER IDEA + CANONICAL REFERENCES + ACTION + STYLE / WORLD INTENT + CAMERA INTENT
```

into a reusable, provider-neutral **master video-direction specification**, and then
projects that master spec down into **one short provider-specific prompt**.

It is prompt-direction knowledge. It does not render video.

## 2. Explicit reuse (no second system)

| Existing P2P surface | Reused for | Duplicated? |
| --- | --- | --- |
| `.p2p/system/p2p_capabilities/capabilities.json` | the one and only capability registry — one entry appended | NO |
| `p2p_uiux.router` / `routing.classify_capabilities` | the one and only router — triggers/negative-triggers only | NO |
| `p2p-visual-reference-pack/1` (`docs/p2p-development/capability-catalog/game-asset-forge/visual-reference-pack.schema.json`) | character multi-view reference vocabulary (`full_body_front`, `full_body_three_quarter`, `full_body_side`, `full_body_back`, `face_front`, `face_three_quarter`) | NO — referenced, never re-declared |
| `governance/research-adoption-ledger.json` | durable research provenance for all seven audited repositories | NO |
| `docs/p2p-development/capability-catalog/` layout | catalog directory convention | NO |

No new router, registry, orchestrator, database, server, daemon, queue, workflow
framework, backend runtime, provider API client, or model weight was created.

## 3. Responsibility boundaries preserved

| Capability | Owns | Must NOT absorb |
| --- | --- | --- |
| `visual.gpt_image_2_style_library` | **IMAGE** prompt construction / style library | generic AI-video direction. Unchanged by this goal. |
| `media.whiteboard_animation` | whiteboard / storyboard / SRT animation production | generic AI-video director prompts. Unchanged by this goal. |
| `p2p-visual-reference-pack/1` | character multi-view reference vocabulary | a second character-reference schema. Reused by reference only. |
| `video.prompt.director_spec` (new) | provider-neutral master video-direction spec + short provider projection | image styling, whiteboard production, video rendering, provider APIs |

Routing separation is enforced mechanically by `TRIGGERS` / `NEGATIVE_TRIGGERS` on
the new registry entry only. No existing registry entry was edited.

## 4. Files in this catalog

| File | Role |
| --- | --- |
| `README.md` | this bounded scope and reuse declaration |
| `director-spec-protocol.md` | the capability contract: 12-field master spec, reference binding, consistency taxonomy, shot/timeline knowledge, provider projection, shot chaining, post-production lessons, non-goals |
| `research-derived-reference.md` | bounded **derived** reference to the seven audited repositories with exact pins, licences, and CC-BY-4.0 attribution. Not a copy of any upstream file. |

Deliberately absent: no `capability-catalog.json`, no `*.schema.json`, no typed
validator, no Python module. The existing P2P capability format does not
mechanically require any of them for a `PURE_DATA` knowledge source, and
`ANTI_OVER_ENGINEERING` forbids adding them without proven necessity.

## 5. What is explicitly NOT here (deferred to future goals)

These are recorded as future **Video Studio artifacts**, not capabilities:

- `character_bible`, `world_bible`, `style_bible`, `shot_spec`, `continuity`
  as separate executable capabilities — rejected for now; they become artifacts
  only if real project use proves the need.
- P2P VIDEO STUDIO bootstrap — not started by this goal.
- Provider profile data (prompt budget, reference-image support, first/last-frame
  support, duration and aspect-ratio controls, marker syntax) — **no verified
  current profile data exists**, so every profile field is declared
  `UNKNOWN_UNTIL_VERIFIED_PROFILE`. No numeric prompt-length constant is
  hard-coded anywhere in P2P for Arena, DesignArena, Seedance, Kling, Wan, or any
  other provider.
- Wan2.2 / VACE / ReCamMaster / MoneyPrinterTurbo runtime — knowledge only, never
  installed, never vendored, never wrapped. MoneyPrinterTurbo's accepted treatment
  is `POST_PRODUCTION_REFERENCE` + `FUTURE_BACKEND` (`RA-EXT-076`); Wan2.2's is
  `MODEL_ADAPTER_CANDIDATE` + `FUTURE_BACKEND` (`RA-EXT-072`).
- Shot chaining execution and any video generation.

## 6. Owner gates carried forward

- `API credentials` = **OWNER GATE**
- `paid video generation` = **OWNER GATE**
- `infrastructure / runtime commitment` = **OWNER GATE**
- `merge of this branch` = **OWNER GATE** (this goal does not merge)
