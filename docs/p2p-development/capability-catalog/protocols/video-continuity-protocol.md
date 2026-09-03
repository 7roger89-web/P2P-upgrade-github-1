# Video Continuity Protocol

Status: CANDIDATE — awaiting a single Golden Video #1 manual pilot before any
Video Studio bootstrap
Date: 2026-09-03
Workstream: P2P-VIDEO-CONTINUITY-01
Parent catalog: `docs/p2p-development/capability-catalog/video-continuity/capability-catalog.json`
Issue: #72

Provider-neutral, renderer-agnostic representation of the minimum needed for
consistency-controlled AI-video production before a standalone Video Studio
project is bootstrapped.

## Preferred law

CANONICAL ASSETS → APPROVED START KEYFRAME → RANDOM VIDEO MODEL(S) (best-of-N)
→ CANDIDATE TAKES → CONTINUITY QA → BEST TAKE → LAST GOOD FRAME → CANONICAL
RE-ANCHOR → NEXT APPROVED KEYFRAME

## Core rule

Consistency lives **outside the renderer** in canonical assets, approved
keyframes, and shot state. A random video renderer (Arena Video /
DesignArena) never owns identity.

1. **A raw final frame containing drift must never automatically become the
   canonical input for the next shot.**
2. **A failed shot cannot become the source of truth for downstream shots.**
3. **Provider prompt limits are profile/config data**, not architecture
   constants.
4. **Continuity QA is manual / external evidence only.** This foundation does
   not inspect image/video media and does not perform automated visual drift
   detection.
5. **Best-of-N is candidate-planning / state semantics only.** This foundation
   does not invoke Arena Video / DesignArena and does not score real takes.

## 1. Video director specification

A provider-neutral structured production specification (schema
`p2p-video-director-spec/1`) capable of representing at minimum:

- canonical reference pointers (`canonical_refs`)
- identity constraints (`identity_constraints`)
- character/world/style constraints (`element_constraints`)
- shot duration / timeline (`timeline_duration_seconds`)
- action / actor performance (`action_performance`)
- camera framing / movement / lens intent (`camera`)
- lighting (`lighting`)
- physics (`physics`)
- dialogue / audio (`dialogue_audio`)
- continuity state (`continuity_state`)
- negative constraints (`negative_constraints`)
- provider projection hints (`provider_projection_hints`)

The spec is an identity-hashable, JSON-safe contract. It is not a rendering
command.

## 2. Canonical visual consistency contract

Schema `p2p-canonical-visual-contract/1`. Distinguishes at minimum:

- identity / face (`identity_face`)
- hair (`hair`)
- body proportions (`body_proportions`)
- costume (`costume`)
- prop / weapon (`prop_weapon`)
- environment (`environment`)
- visual style (`visual_style`)
- image consistency (`image_consistency`)
- temporal video consistency (`temporal_video_consistency`)
- shot-to-shot continuity (`shot_to_shot_continuity`)

The contract is distinct from any prompt. A renderer never re-derives identity;
the canonical anchor is the source of truth.

## 3. Performance bible

Schema `p2p-performance-bible/1`. Bounded provider-neutral behavioral
continuity cues:

- movement style (`movement_style`)
- gesture amplitude (`gesture_amplitude`)
- action tempo (`action_tempo`)
- body posture tendencies (`body_posture_tendencies`)
- camera feel / inertia conventions (`camera_feel_inertia`)
- other bounded performance cues (`cues`)

This is **not** an animation engine.

## 4. Canonical keyframe + re-anchor semantics

Schema `p2p-reanchor-cycle/1`. Preferred flow:

CANONICAL ASSETS → APPROVED START KEYFRAME → RANDOM VIDEO MODEL(S) → CANDIDATE
TAKES → CONTINUITY QA → BEST TAKE → LAST GOOD FRAME → CANONICAL RE-ANCHOR →
NEXT APPROVED KEYFRAME

`safe_to_reanchor` requires `gate_passed` AND `not drift_detected`.
`next_start()` raises `RE_ANCHOR_BLOCKED` for a drifted or un-approved final
frame, so a drifted raw final frame can never seed the next shot.

## 5. Continuity gate

Schema `p2p-continuity-gate/1`. **Manual / external-evidence contract.** A
compact evaluation surface, not a broad vision-QA platform. Before a candidate
propagates state to the next shot, the operator supplies PASS/FAIL-like
evidence per dimension:

- identity
- hair / body
- costume
- prop / weapon
- environment / style
- expected start state
- expected end state
- action / camera continuity

`propagate_allowed` is true only when every dimension passes. The gate does
**not** inspect media and does **not** do automated drift detection
(`inspects_media=False`, `evidence_source=MANUAL_OR_EXTERNAL_EVIDENCE`). A
failed shot cannot become the source of truth for downstream shots.

## 6. Provider prompt projection

Schema `p2p-provider-projection/1`. Concept:
`LARGE CANONICAL MASTER SPEC → SHORT PROVIDER-SPECIFIC SHOT PROMPT`.

Provider prompt limits (`max_prompt_chars`, `accepts_image_reference`,
`forbidden_tokens`) are profile/config data, not architecture constants. The
projection emits a short prompt using canonical pointer references, avoiding
duplicating the whole master spec per shot.

**Priority-aware, no silent raw truncation:**

- Mandatory constraints (anchor/reference, identity, canonical refs, action,
  camera, negative constraints) are always preserved intact.
- If a mandatory constraint cannot fit the provider limit, or uses a
  provider-forbidden token, the projection **fails closed** with an explicit
  reason (`PROVIDER_PROJECTION_FAIL_CLOSED`). It never truncates mid-sentence.
- Optional/compaction fields (tempo, style, scene, lighting, duration) are
  dropped in priority order, never the mandatory constraints.

Arena Video / DesignArena are initially experimental **random/candidate**
renderers, not canonical production backends. Random model selection is
represented as best-of-N candidate **planning** (`p2p-reanchor-cycle` /
`build_candidate_set`), not assumed model continuity and not actual rendering.

## Golden Video #1 pilot

The next proof is a single Golden Path executed manually:
`canonical -> one approved keyframe -> one provider-ready prompt -> manual
Arena/DesignArena render -> manual continuity verdict`.
See `video-continuity/golden-video-01.md` for the concrete executable contract.
Readiness question is only `GOLDEN_VIDEO_01_READY_TO_PILOT=YES/NO`.

## Post-production boundary (MoneyPrinterTurbo)

Extract only architecture lessons now: script/material/narration/subtitle/music
/render stages, agent execution contract, credential hygiene, paid-generation
Owner Gate, bounded retry/recovery, final artifact return. Default is DEFER; do
not install or vendor it. No narration/subtitle/music stage is implemented here
because generation is outside this task's bounded scope.

## Out of scope / not implemented

No video model, framework, weight, paid API, credential, secret, database,
server, daemon, job queue, second router/registry/orchestrator, auto media QA,
renderer API, or standalone Video Studio project is introduced.
