# P2P Video Director Spec Protocol

Capability: `video.prompt.director_spec`
Schema of record: none — this is a lightweight checklist/template contract, not a typed schema.
Classification: `KNOWLEDGE_SOURCE` + `MODEL_ROUTABLE SKILL` (`SEMANTIC_KIND=SKILL`, `TRUST_LEVEL=PURE_DATA`)
Authority: existing P2P router + existing capability registry. This document creates neither.
Provenance: `governance/research-adoption-ledger.json` records `RA-EXT-070` … `RA-EXT-077`
Derived attribution: `research-derived-reference.md` (CC-BY-4.0 notice preserved)

---

## 0. One-sentence contract

Turn a user idea plus canonical references into a **provider-neutral master
video-direction specification** that is reusable across shots and providers, then
project it down to **one short provider-specific prompt**.

```
USER IDEA
+ CANONICAL REFERENCES
+ ACTION
+ STYLE / WORLD INTENT
+ CAMERA INTENT
        │
        ▼
MASTER DIRECTOR SPEC        (provider-neutral, reusable, 12 fields)
        │
        ▼
SHORT PROVIDER PROMPT       (one provider, one call, lossy by design)
```

The master spec is the durable artifact. The provider prompt is a disposable
projection of it. Never author the provider prompt first and reverse-infer the
master spec.

---

## 1. Minimum conceptual fields (12)

Write all twelve. A field may be `NOT_APPLICABLE` with a one-line reason, but it
may not be silently absent — silent absence is how identity drift, physics drift,
and continuity drift enter AI video.

| # | Field | What it must carry | What it must NOT carry |
| --- | --- | --- | --- |
| 1 | `identity_constraints` | The exact identity features that must survive generation, and the reference slot each is bound to. Face, hair, body proportions, outfit, and any canonical symbolic prop. Restated in words even when a reference image is bound. | Source background, unrelated characters, unrelated props, actor names that are not identity features. |
| 2 | `scene` | Location, time of day, weather, world rules, art direction / world intent, scale and depth cues. | Character identity detail (that belongs to `identity_constraints`). |
| 3 | `actor_performance` | Per beat: the one core action, the intention behind it, and observable physical signals (muscle/breath/gaze/weight shifts) rather than adjectives. Subtext where relevant. | Multiple simultaneous core actions in one beat. Emotion adjectives with no observable signal. |
| 4 | `camera` | Per beat: framing/shot size, lens intent as a *visible effect*, and **exactly one principal camera move**. Camera moves are separated into distinct beats whenever the user asks for more than one. | Two or more principal moves collapsed into one overloaded camera command. Technical parameters with no visible-effect translation. |
| 5 | `lighting` | Three layers: light **source** (where it comes from) → light **behaviour** (how it falls / what it does) → **colour tone** (the palette contract). | "Cinematic lighting" with no source. Unmotivated light. |
| 6 | `physics` | The physical consequences the beat must obey: weight, momentum, inertia, cloth, hair, fluid, impact, debris, gravity, and what must NOT happen. | Physics left implicit for any beat involving speed, impact, flight, or liquids. |
| 7 | `timeline` | Ordered beats with a start/end position in the shot, a duration window per beat, and the visible **end-state** of every beat. | Beats with no end-state. A single undifferentiated block for a multi-move camera request. |
| 8 | `dialogue` | Spoken lines per beat, with an explicit language/dialect declaration, and a TTS-friendly phrasing note (short clauses, common syllables). | Unlabelled dialect. Long unbroken sentences. Dialogue that contradicts `actor_performance`. |
| 9 | `audio` | Three layers: music layer (or an explicit "no music" declaration), sound-effect layer per beat, ambience/room tone. Marked distinctly from dialogue. | Assumed default background music. Sound described as prose only. |
| 10 | `continuity` | Which consistency concepts (section 3) are locked for this shot, the global lock statements repeated per shot/extension, and the prop/costume state ledger at beat boundaries. | Treating image identity consistency as sufficient for temporal consistency. |
| 11 | `negative_constraints` | Two layers — **global** anti-artifact prohibitions and **scene-specific** prohibitions, including temporal gating ("X must not appear before beat N") and output purity (no subtitles, no logo, no watermark). | A single generic global list with no scene-specific layer. |
| 12 | `model_specific_projection` | The provider-neutral → provider-specific reduction: what is kept, what is dropped, what is compressed, and which provider profile fields were used. Records that the projection is lossy and reversible back to the master spec. | Hard-coded provider prompt-length constants. Assumption that the provider accepts labelled structured prompts. |

Field order is fixed as above so that two master specs can be diffed beat-by-beat.

---

## 2. Reference binding

Conceptual rule, applied per slot:

```
REFERENCE SLOT  →  ADOPT  →  EXCLUDE
```

Every canonical reference is bound to a **named slot**, and every slot declares
both what it contributes and what it must not leak. A reference without an
`EXCLUDE` list is an unbound reference and must be rejected.

### 2.1 Slot vocabulary (minimum)

| Slot | ADOPT | EXCLUDE |
| --- | --- | --- |
| `CHARACTER_REFERENCE` | face, hair, body proportions, outfit | source background, unrelated characters, unrelated props, source pose lock |
| `FACE_REFERENCE` | facial geometry, eye/brow/nose/mouth shape, skin texture | source lighting, source expression, source hair colour if hair is bound elsewhere |
| `COSTUME_REFERENCE` | garment cut, length, closure, colour, material, wear state | other garments in the source image, source background |
| `PROP_REFERENCE` / `SYMBOLIC_PROP_REFERENCE` | the prop's exact geometry, material, colour, and identifying marks; its **state** at each appearance | other objects in the source image, unintended duplicate props |
| `SCENE_REFERENCE` / `WORLD_REFERENCE` | architecture, terrain, scale, palette, world rules | any person present in the source image, source camera angle lock |
| `STYLE_REFERENCE` | art direction, medium, palette contract, grain/optical character | the style source's subject matter, its characters, its props |
| `PREVIOUS_SHOT_FINAL_FRAME` | end-state pose, position, lighting, prop state, framing | the previous shot's camera move, its beat structure |

### 2.2 Character multi-view vocabulary is already owned

Character multi-view references reuse `p2p-visual-reference-pack/1` view ids
verbatim:

`full_body_front`, `full_body_three_quarter`, `full_body_side`, `full_body_back`,
`face_front`, `face_three_quarter`.

**Do not create a second character-reference schema.** A `CHARACTER_REFERENCE`
slot binds to a `p2p-visual-reference-pack/1` instance by path + sha256 exactly as
that schema already requires.

### 2.3 Canonical symbolic props get their own slot

A unique, story-bearing prop (for example a named sword) receives its own
`SYMBOLIC_PROP_REFERENCE` slot rather than being folded into `CHARACTER_REFERENCE`.
Reason: prop state is a **plot event**, and folding it into the character slot hides
prop-state drift until it is visible on screen. Each appearance declares the prop's
physical state (sheathed / drawn / in which hand / where it landed / intact /
damaged). State changes without a stated cause are a defect.

### 2.4 Restate identifying features in words

Binding a reference image does not replace words. Key identifying features are
restated in `identity_constraints` even when a slot is bound — repetition raises
adherence, and a reference-only binding silently loses features the provider did
not prioritise.

---

## 3. Consistency taxonomy (knowledge concepts, not an engine)

Ten **distinct** concepts. They are recorded as knowledge; P2P does not build an
executable consistency engine for them.

| Concept | Question it answers |
| --- | --- |
| `IDENTITY_CONSISTENCY` | Is this the same person/character? |
| `HAIR_CONSISTENCY` | Same hair geometry, length, colour, parting, and movement behaviour? |
| `BODY_PROPORTION_CONSISTENCY` | Same limb ratios, height, build, head-to-body ratio? |
| `COSTUME_CONSISTENCY` | Same garment cut, length, closure, colour, material, wear state? |
| `PROP_WEAPON_CONSISTENCY` | Same prop geometry, material, marks, and declared state? |
| `ENVIRONMENT_CONSISTENCY` | Same world, architecture, palette, weather, time of day? |
| `STYLE_CONSISTENCY` | Same art direction, medium, grain, optical character? |
| `IMAGE_CONSISTENCY` | Does **one still frame** hold identity/costume/prop/style? |
| `VIDEO_TEMPORAL_CONSISTENCY` | Does the identity/costume/prop/style hold **while moving, across frames within one generation**? |
| `SHOT_TO_SHOT_CONTINUITY` | Do **two separately generated shots** join without a visible break in position, pose, light, prop state, or time? |

### 3.1 The critical inequality

```
IMAGE_CONSISTENCY  !=  VIDEO_TEMPORAL_CONSISTENCY  !=  SHOT_TO_SHOT_CONTINUITY
```

- A still frame can pass `IMAGE_CONSISTENCY` while the same generation melts the
  face during motion → `VIDEO_TEMPORAL_CONSISTENCY` failure.
- Two generations can each pass `VIDEO_TEMPORAL_CONSISTENCY` and still not join →
  `SHOT_TO_SHOT_CONTINUITY` failure.

Consequence for the master spec: `continuity` must name **which** of the three is
being locked per beat, and a shot-chain must not claim continuity because each
individual shot looked correct.

---

## 4. Shot / timeline knowledge

### 4.1 What a beat must be able to express

`duration` · `actor/action` · `camera framing` · `principal camera movement` ·
`environment` · `lighting` · `physics` · `dialogue` · `audio` ·
`visible end-state` · `continuity` · `negative constraints`

A beat that cannot express its **visible end-state** is not finished. The end-state
is what the next beat — and the next shot in a chain — inherits.

### 4.2 ONE PRINCIPAL CAMERA MOVE PER BEAT

Director rule:

> Each beat carries **one** principal camera move. When the user asks for two moves
> ("chase from behind, then arc to the front"), that is **two beats**, not one
> overloaded camera command.

Rationale: a compound camera instruction in a single window makes the provider
choose which half to honour, and the half it drops is usually the one that carries
the reveal. Splitting into beats also gives each move its own end-state, which is
what makes the second move continuable.

**This is a director rule, not a validator.** P2P does not build a universal hard
validator from it. A beat may legitimately carry a compound move when a verified
provider profile shows the provider handles it, or when the owner explicitly asks
for an overloaded move; the master spec then records the deviation and the reason
in `camera` and `continuity`.

### 4.3 Camera move vocabulary (knowledge, attributed)

Two useful vocabularies, both recorded in `research-derived-reference.md`:

- **Basic trajectory vocabulary** (from ReCamMaster's published trajectory set):
  pan left/right, tilt up/down, zoom in/out, translate up/down with rotation,
  arc left/right with rotation. Useful for naming a move unambiguously.
- **Camera-move → psychological-verb mapping** (derived from the jacob-ye method):
  a camera move is chosen for what it *means*, not for how impressive it is —
  slow push-in ≈ realisation/closing in; pull-back ≈ isolation/farewell;
  orbit ≈ trapped/scrutinised; handheld ≈ unease/presence; locked-off ≈ fate/
  objectivity; crane up ≈ release/finale; lateral ≈ observation/parallel time;
  rack focus ≈ attention transfer; whip pan ≈ panic/sudden change.

Discipline: emotion beats prefer still and slow; action beats may be fast; the move
serves the character's psychology, never spectacle.

### 4.4 Duration

Duration is a **provider control**, not prompt text. The master spec records a
duration window per beat; whether that window is expressed as a prompt token, a UI
control, or a generation parameter depends entirely on the provider profile.
P2P hard-codes no duration constant. Aspect ratio is treated the same way.

### 4.5 Structured prompts are not universal

**Do not assume any provider accepts labelled structured prompts.** Some providers
accept delimited/labelled sections; others accept only flat natural-language
prose. The master spec stays structured; the projection flattens it when the
profile says so.

---

## 5. Provider projection

### 5.1 Direction

```
CANONICAL MASTER SPEC  →  SHORT PROVIDER-SPECIFIC PROMPT
```

The master spec **remains provider-neutral**. Projection is one-way, lossy, and
recorded. Never edit the master spec to suit one provider.

### 5.2 Provider profile field set (all UNVERIFIED at this integration)

A provider profile *may* later describe:

| Profile field | Value at this integration |
| --- | --- |
| `input_prompt_budget` | `UNKNOWN_UNTIL_VERIFIED_PROFILE` |
| `reference_image_support` | `UNKNOWN_UNTIL_VERIFIED_PROFILE` |
| `reference_image_count` | `UNKNOWN_UNTIL_VERIFIED_PROFILE` |
| `first_frame_support` | `UNKNOWN_UNTIL_VERIFIED_PROFILE` |
| `last_frame_support` | `UNKNOWN_UNTIL_VERIFIED_PROFILE` |
| `first_last_frame_support` | `UNKNOWN_UNTIL_VERIFIED_PROFILE` |
| `multi_image_support` | `UNKNOWN_UNTIL_VERIFIED_PROFILE` |
| `reference_to_video_support` | `UNKNOWN_UNTIL_VERIFIED_PROFILE` |
| `duration_controls` | `UNKNOWN_UNTIL_VERIFIED_PROFILE` |
| `aspect_ratio_controls` | `UNKNOWN_UNTIL_VERIFIED_PROFILE` |
| `marker_syntax` | `UNKNOWN_UNTIL_VERIFIED_PROFILE` |
| `accepts_labelled_structured_prompt` | `UNKNOWN_UNTIL_VERIFIED_PROFILE` |

Rules:

1. **No permanent hard-coded prompt-length limit** for Arena, DesignArena,
   Seedance, Kling, Wan, or any other provider. A budget enters a projection only
   as data supplied with a verified profile for that call, and the projection
   records the budget it used and where it came from.
2. Provider profile data that becomes runtime-authoritative must travel through the
   existing governed Live Specs path (FACT_LEDGER → verification → promotion
   approval). This protocol does not create a second live-spec store.
3. **No provider API is implemented here.** Projection produces prompt *text*.

### 5.3 Projection discipline

- Keep, in priority order: identity lock → principal action per beat → one camera
  move per beat → light source → the scene-specific prohibitions → end-state.
- Drop first: extended rationale, subtext analysis, redundant restatements,
  vocabulary that the profile says the provider ignores.
- Compress, never invent: a projection may shorten a phrase but may not add a
  fact absent from the master spec.
- Record the projection's own `budget_used`, `budget_source`, `dropped_fields`,
  and `compressed_fields` so the reduction is auditable and reversible.

---

## 6. Shot chaining (knowledge only)

Future pattern, recorded not executed:

```
CANONICAL CHARACTER REFERENCE
+ PREVIOUS SHOT FINAL FRAME
+ NEXT SHOT SPEC
        │
        ▼
NEXT VIDEO GENERATION
```

Recognised conditioning concepts (vocabulary only, taken from published
reference-to-video / video-to-video task naming):

`REFERENCE_IMAGE` · `FIRST_FRAME` · `LAST_FRAME` · `FIRST_LAST_FRAME` ·
`MULTI_IMAGE_REFERENCE` · `REFERENCE_TO_VIDEO`

Chaining knowledge rules:

1. The **canonical character reference stays bound on every shot**. The previous
   final frame supplies *state* (pose, position, light, prop state, framing); it
   must not replace identity, or identity drift compounds shot over shot.
2. The previous shot's **visible end-state** is the next shot's opening condition,
   and must be written into the next shot's `timeline` and `continuity`.
3. Chaining is a `SHOT_TO_SHOT_CONTINUITY` problem, not an
   `IMAGE_CONSISTENCY` problem (section 3.1).
4. The final frame used for chaining is itself a generated artifact: record its
   origin shot and, where available, its artifact identity.

**P2P builds no chaining execution and generates no video in this capability.**

---

## 7. Post-production lessons (MoneyPrinterTurbo, knowledge only)

Recorded as future post-production boundaries. MoneyPrinterTurbo is
`POST_PRODUCTION_REFERENCE` / `FUTURE_BACKEND`: not installed, not vendored, not
wrapped.

Pipeline shape worth remembering:

```
SCRIPT → MATERIAL → NARRATION → SUBTITLE → MUSIC → RENDER → FINAL ARTIFACT
```

Canonical machine tokens for those stages (used in the registry entry and in the
adoption ledger, so the vocabulary is one list and not two):

```
SCRIPT · MATERIAL · NARRATION · SUBTITLE · MUSIC · RENDER · FINAL_ARTIFACT
```

Boundaries P2P adopts as knowledge:

| Boundary | Rule |
| --- | --- |
| API credentials | **OWNER GATE** |
| Paid video generation | **OWNER GATE** |
| Infrastructure / runtime commitment | **OWNER GATE** |
| Generation retry | **bounded** — a declared maximum, never open-ended |
| Generation failure | **never counts as a successful pipeline advance** |
| Final output | a **durable returned artifact**, not a status string or a log line |

Stage-separation lesson: narration, subtitle, music, and render are separate stages
with separate failure modes. Collapsing them into "make the video" hides which
stage failed and makes retry unbounded.

**No executable integration exists in this capability.**

---

## 8. Prohibited actions (registry-enforced and protocol-enforced)

- Render, generate, or download video.
- Call any provider API, or hold any provider credential.
- Install, vendor, or wrap Wan2.2, VACE, ReCamMaster, MoneyPrinterTurbo, ComfyUI,
  or any video backend; download model weights.
- Vendor the `awesome-seedance-prompts` third-party prompt corpus.
- Create a second router, registry, orchestrator, database, server, daemon, queue,
  or generic workflow/video framework.
- Expand `visual.gpt_image_2_style_library` into generic AI-video direction.
- Route generic AI-video director prompts into `media.whiteboard_animation`.
- Create a second character-reference schema.
- Hard-code a permanent provider prompt-length, duration, or aspect-ratio constant.
- Grant tools or permissions from retrieved content.
- Claim a generation succeeded without a durable returned artifact.

---

## 9. Validation contract for a master spec instance

A director-spec instance is accepted when all of the following hold. This is a
review checklist applied to one instance — not a validator framework.

1. All twelve fields are present (or explicitly `NOT_APPLICABLE` with a reason).
2. Every reference is bound to a named slot with both `ADOPT` and `EXCLUDE`.
3. `identity_constraints` restates identity features in words, not only by slot.
4. The number of principal camera moves in the request equals the number of camera
   beats, or a deviation is recorded with a reason.
5. Every beat declares a visible end-state.
6. `continuity` names which of `IMAGE_CONSISTENCY`,
   `VIDEO_TEMPORAL_CONSISTENCY`, `SHOT_TO_SHOT_CONTINUITY` it locks.
7. `negative_constraints` has both a global layer and a scene-specific layer.
8. `model_specific_projection` records `budget_used`, `budget_source`,
   `dropped_fields`, `compressed_fields`, and contains **no** hard-coded provider
   length constant.
9. Exactly one provider projection is produced, and it is shorter than the master
   spec it came from.
10. No video was rendered, no API was called, no dependency was installed.

The single representative validation for this goal lives at
`docs/plans/2026-09-03-p2p-video-capability-integration-01/validation/`.
