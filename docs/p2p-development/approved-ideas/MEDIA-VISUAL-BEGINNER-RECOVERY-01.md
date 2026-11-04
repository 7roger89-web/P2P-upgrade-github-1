# P2P MEDIA / VISUAL / BEGINNER RECOVERY 01

Status: `DURABLE_RECOVERY_RECORD`

Purpose: recover Owner-approved or materially advanced P2P work that predates the durable approved-ideas backlog, especially image / character / 3D asset / video / voice capability work, and restate the product North Star that P2P is ultimately for a beginner Owner.

This file is a durable backlog/reconciliation record only. It is **not** runtime authority, install permission, execution authorization, release authority, or a replacement for canonical specs / Task State / Operations Notebook. Existing durable subjects must be reconciled, not restarted.

## P2P_BEGINNER_NORTH_STAR_01 — Beginner-first final product goal

`STATUS=EXISTING_CANONICAL_INVARIANT`

The final P2P product is intended to let a beginner operate complex software/project workflows without becoming the manual relay for Git SHAs, agent handoffs, repair loops, test bookkeeping, or infrastructure details.

Durable prior evidence already exists, including PR38 `P2P_BEGINNER_OPERATIONS_UX_V1` and the canonical Operations Notebook. This recovery entry does not create a new UX framework; it prevents the North Star from being diluted as capability count grows.

Required product laws:

```text
BEGINNER_FIRST=YES
ONE_ACTION_NOW=YES
EXPLAIN_SIMPLY=YES
AUTO_RECOMMEND_DEFAULT=YES
OWNER_MICRO_LOOP_SUPPRESSION=YES
TECHNICAL_BOOKKEEPING_HIDDEN_BY_DEFAULT=YES
REAL_OWNER_GATES_ONLY=YES
NO_OWNER_AS_AGENT_RELAY=YES
```

P2P may be technically sophisticated internally, but the Owner-facing surface should remain simple. Internal complexity is justified only when it reduces Owner burden, raises reliability, or safely expands capability.

## GAME_ASSET_FORGE_01 — Existing canonical game/media asset routing foundation

`STATUS=EXISTING_CANONICAL_WORK`

Durable subject: merged PR24 `P2P Game Asset Forge catalog and offline-forge contracts`.

Known durable result:

- audited 19 candidate game-asset toolchains across character / rig / img2threejs / motion / VFX / terrain;
- added/reused selective capability identities rather than installing every tool;
- reused `img2threejs` and `visual.gpt_image_2_style_library`;
- established Asset Forge protocol plus license/model/dataset/security gates;
- no bulk weights/CUDA/PyTorch install as part of the intake.

Continuation law:

```text
REFERENCE -> ROUTE_SELECTION -> REAL_ASSET -> PROJECT_RUNTIME -> DURABLE_EVIDENCE -> VISUAL_COMPARISON
```

Do not restart Asset Forge architecture from chat memory.

## IMG2THREEJS_01 — Production-proven static 3D asset route

`STATUS=PRODUCTION_PROVEN_CLOSED`

The img2threejs static-asset route has already been promoted and independently proven end-to-end. Do not reopen hardening merely because a new visual project wants to use it.

Reuse it as one Asset Forge route when the project/reference fit is appropriate. It is not the only asset route.

## MPFB2_CHARACTER_FORGE_01 — Existing canonical character-generation runtime boundary

`STATUS=EXISTING_CANONICAL_WORK_RUNTIME_NOT_LIVE_PROVEN`

Current canonical main contains `.p2p/system/p2p_capabilities/mpfb_adapter.py` with pinned upstream:

```text
UPSTREAM=https://github.com/makehumancommunity/mpfb2.git
VERSION=2.0.17
RELEASE_SHA=80919fa4682335c41847f761a4d79dcad4124732
RELEASE_TREE=189a1d6694515ecfbdc40067218c5024389b4e43
CODE_LICENSE=GPL-3.0-or-later
CORE_ASSET_LICENSE=CC0-1.0
NETWORK_POLICY=DENY
THIRD_PARTY_ASSET_POLICY=DENY
EXECUTION_AUTHORIZED=False
```

A durable commit (`d661654746f090136f37370f76578ee345b74994`) closed bounded MPFB runtime blockers and is an ancestor of current canonical main. The adapter/runtime boundary exists, but the durable source itself still states that Blender/MPFB execution was not launched in that workstream.

Continuation rule: reconcile current canonical MPFB surfaces and run a separately authorized real runtime smoke before claiming production-proven character generation.

## VISUAL_GPT_IMAGE_2_STYLE_LIBRARY_01 — Existing image/style source

`STATUS=EXISTING_DURABLE_CAPABILITY_RECONCILE_BEFORE_EXPANSION`

Recovered durable evidence: merged Asset Forge PR24 explicitly reused `visual.gpt_image_2_style_library`; prior P2P work treated `awesome-gpt-image-2` as an existing style/reference source.

Do not create a second image-style library merely because the earlier discussion predates this backlog. Before expansion, locate/reconcile the exact current registry/provenance record and reuse it.

This is a style/reference/generation-support capability, not authority over project visual direction. Project references / Visual North Star remain the visual target.

## OPENMONTAGE_01 — Existing video/media vendor intake

`STATUS=HOLD_EXISTING_CANDIDATE`

Pointer only: existing PR31 `P2P-OPENMONTAGE-VENDOR-01` is already durably tracked in the main approved-ideas backlog. It is an AGPL-3.0 reference-only external-runtime vendor intake and must be reconciled rather than restarted.

Video generation/editing/composition work should check this subject before inventing a new OpenMontage workstream.

## REAL_TIME_VOICE_CLONING_01 — Recovered pre-backlog voice capability idea

`STATUS=PENDING_RECONCILIATION`

Prior Owner discussion included `Real-Time-Voice-Cloning` as a possible media/voice pipeline source. Current recovery search did not find a matching dedicated P2P PR/issue/commit subject under that name.

Therefore preserve it as a recovered idea, not an implemented capability.

Future bounded fit work must evaluate current upstream identity/license/security, consent/voice-rights boundaries, local runtime requirements, and whether P2P already has an equivalent voice path. Do not globally install or claim voice-cloning production readiness from this record.

## WHITEBOARD_ANIMATION_01 — Recovered media skill path

`STATUS=PENDING_RECONCILIATION`

Prior sessions used/imported a `media.whiteboard_animation` skill and produced a storyboard-oriented planning flow. No matching canonical P2P GitHub workstream was found in this recovery pass.

Preserve the concept as an external/selective media skill path. Before P2P integration, identify the exact durable skill source, license/provenance, execution boundary, and whether it should remain host-specific or project into a provider-neutral P2P media capability.

## MEDIA / VISUAL capability law

```text
REFERENCE_IS_TARGET
CAPABILITY_IS_ROUTE_NOT_AUTHORITY
AVAILABLE != LOADED != AUTHORIZED != EXECUTED
REAL_ASSET_REQUIRED_FOR_ASSET_CLAIM
PROJECT_RUNTIME_EVIDENCE_REQUIRED_FOR_INTEGRATION_CLAIM
VISUAL_COMPARISON_REQUIRED_FOR_VISUAL_SUCCESS_CLAIM
EXISTING_DURABLE_SUBJECT -> RECONCILE, DO_NOT_RESTART
```

For image/video/game work, P2P should discover the minimum relevant routes, normally compare only a small shortlist, create a real durable output, integrate it into the real project when integration is claimed, and verify against the reference/Visual North Star.

## Recovery follow-up

This recovery record is intentionally broader than one implementation workstream. It exists because several media/visual decisions predated the approved-ideas backlog.

When PR41 is later reconciled with current canonical main, consolidate these IDs into `P2P-APPROVED-IDEAS-BACKLOG.md` without creating a parallel authority store. Until then, this file is the durable pointer preventing loss.
