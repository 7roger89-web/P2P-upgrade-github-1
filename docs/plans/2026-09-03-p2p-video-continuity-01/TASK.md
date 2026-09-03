# P2P VIDEO CONTINUITY FOUNDATION — TASK

Issue: #72
Branch: `issue-72-p2p-video-continuity`
Execution lane: STANDARD
Scope: development-plane candidate only; no merge/promotion/deploy

## Outcome

Implement the minimum provider-neutral P2P foundation needed for consistency-controlled AI-video production before any standalone Video Studio project is bootstrapped.

The design must work even when Arena Video / DesignArena use random video models. Consistency must live outside the renderer in canonical assets, approved keyframes, shot state and continuity checks.

## Research inputs

Review upstream evidence as needed, but do not vendor/import whole frameworks merely because they exist:

1. `jacobye2017-afk/jacob-ye-seedance-prompt`
2. `opensource-works/awesome-seedance-prompts`
3. `Wan-Video/Wan2.2`
4. `ali-vilab/VACE`
5. `KlingAIResearch/ReCamMaster`
6. `divolleggett/awesome-character-consistency`
7. `harry0703/MoneyPrinterTurbo`

Research reference already identified by Owner:

`SEEDANCE-2.5-SOLO-SKYDIVE-LIVE-TV-JP-01`

Use its production-spec structure as research evidence only: identity, scene, performance, camera, physics, timeline, audio, speech, continuity, negative constraints.

## Mandatory preflight

Before editing:

1. Read repository orientation and applicable capability-foundation specs.
2. Inspect current capability manifest and nearby capability patterns.
3. Search current P2P surfaces for overlap before creating anything.
4. Classify each proposed surface as `NEW`, `PARTIAL_OVERLAP`, `ALREADY_EXISTS`, or `NOT_NEEDED`.
5. Reuse the existing P2P router/capability foundation. Never create another router/registry/orchestrator.

## Minimum concepts to support

### 1. Video director specification

Provider-neutral structured production specification capable of representing at minimum:

- canonical reference pointers
- identity constraints
- character/world/style constraints
- shot duration / timeline
- action / actor performance
- camera framing / movement / lens intent where applicable
- lighting
- physics
- dialogue / audio
- continuity state
- negative constraints
- provider projection hints

Do not assume the final capability ID must be `video.prompt.director_spec`; reuse an existing equivalent if present.

### 2. Canonical visual consistency contract

Must distinguish at minimum:

- identity / face
- hair
- body proportions
- costume
- prop / weapon
- environment
- visual style
- image consistency
- temporal video consistency
- shot-to-shot continuity

### 3. Performance bible

Represent provider-neutral behavioral continuity such as:

- movement style
- gesture amplitude
- action tempo
- body posture tendencies
- camera feel / inertia conventions
- other bounded performance cues justified by evidence

Do not turn this into an animation engine.

### 4. Canonical keyframe + re-anchor semantics

Preferred conceptual flow:

`CANONICAL ASSETS -> APPROVED START KEYFRAME -> RANDOM VIDEO MODEL(S) -> CANDIDATE TAKES -> CONTINUITY QA -> BEST TAKE -> LAST GOOD FRAME -> CANONICAL RE-ANCHOR -> NEXT APPROVED KEYFRAME`

Critical rule:

A raw final frame containing drift must never automatically become canonical input for the next shot.

### 5. Continuity gate

Before a candidate shot can propagate state to the next shot, evaluate at minimum:

- identity
- hair/body
- costume
- prop/weapon
- environment/style
- expected start state
- expected end state
- action/camera continuity

A failed shot cannot become the source of truth for downstream shots.

Keep this as a compact contract/evaluation surface; do not build a broad vision-QA platform in this task.

### 6. Provider prompt projection

Support the concept:

`LARGE CANONICAL MASTER SPEC -> SHORT PROVIDER-SPECIFIC SHOT PROMPT`

Provider prompt limits must be profile/config data, not hard-coded architectural constants. Avoid duplicating the entire master spec per shot.

Arena/DesignArena are initially experimental/random candidate renderers, not canonical production backends.

Random model selection should be represented as best-of-N candidate rendering rather than assumed model continuity.

### 7. Knowledge/backend classification

For every research source decide the minimum treatment:

- executable capability
- knowledge source/reference
- prompt corpus
- backend/model-adapter candidate
- post-production reference
- defer/reject

Prefer knowledge/reference treatment over executable code when code is not required.

### 8. MoneyPrinterTurbo boundary

Extract only useful architecture lessons now:

- script/material/narration/subtitle/music/render stages
- agent execution contract
- credential hygiene
- paid-generation Owner Gate
- bounded retry/recovery
- final artifact return

Do not install or vendor MoneyPrinterTurbo in this task unless a present requirement makes it mechanically necessary; default is DEFER.

## Explicit non-goals / forbidden expansion

Do NOT:

- install Wan2.2
- install VACE
- install ReCamMaster
- install ComfyUI
- install MoneyPrinterTurbo
- download model weights
- add paid video APIs
- add credentials/secrets
- add database/server/daemon/job queue
- create another router/registry/orchestrator
- create a broad video framework
- create a standalone `p2p-video-studio` repo/project yet
- deploy anything
- merge or promote anything
- generate paid video
- build large generic benchmarks

## Implementation guidance

Follow current P2P capability patterns and upstream-first policy.

If a small provider-neutral adapted skill/capability is justified, keep it on-demand and route-selected only. If knowledge artifacts are sufficient, do not manufacture executable code.

Do not import upstream examples/assets/reference media unless they are necessary, licensed, and justified.

Use focused tests only for the contracts actually added or changed.

STOP when acceptance evidence is sufficient.

## Acceptance criteria

1. Existing P2P overlap is explicitly reconciled.
2. Minimum video-director / continuity capability or equivalent is implemented only where justified.
3. Canonical asset, performance-bible, keyframe/re-anchor, and continuity-gate semantics are represented without a new orchestration framework.
4. Provider projection can express prompt-limited Arena/DesignArena targets without copying a full master spec into every shot.
5. Random Arena/DesignArena model selection is treated as candidate/best-of-N rendering, not stable provider identity.
6. Knowledge-only sources stay knowledge-only when runtime adoption is unnecessary.
7. Focused validation passes.
8. No runtime model stack, paid API, secret, infrastructure, merge, promotion, or deploy is introduced.

## Required final report

Return exactly these fields plus concise evidence:

`VIDEO_RESEARCH_RECONCILED=`

`P2P_EXISTING_OVERLAP=`

`NEW_P2P_CAPABILITIES=`

`KNOWLEDGE_REFERENCES=`

`VIDEO_DIRECTOR_SPEC_STATUS=`

`CANONICAL_ASSET_STATUS=`

`PERFORMANCE_BIBLE_STATUS=`

`KEYFRAME_REANCHOR_STATUS=`

`CONTINUITY_GATE_STATUS=`

`PROVIDER_PROJECTION_STATUS=`

`ARENA_DESIGNARENA_TREATMENT=`

`MONEYPRINTERTURBO_TREATMENT=`

`VALIDATION_STATUS=`

`CANDIDATE_SHA=`

`VIDEO_STUDIO_READY_TO_BOOTSTRAP=YES/NO`

`OWNER_GATE_REQUIRED=YES/NO`

`OVER_ENGINEERING_STATUS=`

`CONTROL_TOWER_RETURN_PACKET=`

Explicitly answer: `Không bị over engineering chứ?`
