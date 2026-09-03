# ROUND 1 — 01 DIRECTOR (source: jacob-ye-seedance-prompt)

## Grounding
FORMULA.md V3.0: the ten questions (WORLD / ACTOR / CAMERA / LIGHT / MOTION / PERFORMANCE /
EMOTION / CONTINUITY / ANTI-AI / SOUND); the assembly order
`[参考素材声明] + [一句话总纲] + [全局设定] + [时间轴剧情] + [全局尾部]`;
the binding rules "≥3s per window, one core action + one camera move per window,
duration/aspect set in the UI, never in the prompt"; scene/actor reference separation;
Subject Profile; four-part breathing feel; two-layer ANTI-AI ban list; per-shot end state.
docs/: material-discipline (what to attach and what to delete per segment), repair-sop
(fix one shot, do not re-run the whole chain), post-production, voice-continuity.

## CHARACTER_REFERENCE_REQUIREMENTS
One Subject Profile for 剑客 (working name YE_JIAN):
- 1 face/upper-body card, neutral light, 3/4 angle — appearance + hair + robe only.
- 1 full-body card, same robe, sword sheathed at hip — silhouette + costume authority.
- 1 prop card: the golden jian alone on neutral ground (fixed prop, per FORMULA 1.2).
- Explicit exclusion line per card: "不采用图片背景" / "不得持有他人道具".
- Bindings are written one-by-one. Merged binding ("图1到图3分别定义…") is forbidden.

## WORLD_REFERENCE_REQUIREMENTS
Scene cards must contain **zero humans** — no passers-by, shadows, reflections, statues,
posters, mannequins, blurred human silhouettes (FORMULA 1.1 hard list).
- W1 mountain road / mist, low sun.
- W2 city wall + gate at middle distance.
- W3 gate-front detail: banners, lanterns, stone.
Binding: "场景对应@图片N，仅参考场景、构图、光线、色调、天气、建筑与道具，不采用任何人物。"

## KEYFRAME_REQUIREMENTS
Keyframes are stills, not video: 3 world cards + 2 character cards + 1 prop card = 6 stills,
plus one 4-panel storyboard sheet showing the shot order. Golden-hour key from screen-left,
mist as the fill, sword as the only specular hit. Light described in three layers
(source → behaviour → tone).

## SHOT_COUNT / SHOT_DURATION
4 shots × 5s = 20s. Rationale: ≥3s minimum per window; 4 windows is the smallest count that
carries approach → arrival without a montage. One core action + one camera move each.
S1 wide, figure enters frame on the ridge. S2 tracking three-quarter back, sword at hip.
S3 medium-close, face lifts, city reflected in the blade. S4 wide from behind, gate ahead.

## CAMERA_STRATEGY
One lens, one move per window. S1 static wide 24mm. S2 slow lateral dolly 35mm.
S3 slow push-in 50mm. S4 slow crane-up 24mm. No move stacking.

## MOTION_STRATEGY
Breathing feel, four elements per shot: environment micro-motion (mist drift, banner flutter),
character micro-motion (robe hem, breath, blink), camera micro-motion (hand-held float ≤2%),
sound micro-motion (wind bed). Walk pace stays constant across shots.

## CONTINUITY_STRATEGY
Global tail block, repeated verbatim in every shot prompt: same face, same hair tie, same robe
colour and wear, sword always on the LEFT hip, same time of day, same weather, same walking
direction (screen left → right). Each shot ends with an explicit **end state** which is the
first line of the next shot's setup. Damage repair follows repair-sop: re-roll the single
broken window, never the chain.

## ARENA_PROMPT_STRATEGY
Per shot, assemble in fixed order: reference declaration (each card bound individually with its
exclusion) → one-sentence premise → global setting → timeline beats with `<sfx>` `{dialogue}`
`(music)` markers → global tail (continuity lock + scene-specific ANTI-AI ban + clean-video
declaration). No duration or aspect ratio inside the prompt text.
ANTI-AI global: no extra fingers, no floating feet, no sword clipping the robe, no duplicated
character, no modern objects, no text/watermark. Scene-specific: no crowds at the gate, no
second sword, no glow trails before beat 3.

## DESIGNARENA_PROMPT_STRATEGY
Still-image surface produces the 6 cards + storyboard sheet. Character cards: neutral studio
light, flat background, no environment storytelling. World cards: the human-exclusion list is
pasted into the negative side. Prop card: single object, orthographic-ish, neutral grey.
Storyboard sheet: 4 ordered panels, same character in all four (this is the handoff artefact
to expert 03).

## WHICH_REPOS_REQUIRE_RUNTIME
None from my lane. jacob-ye-seedance-prompt is a methodology/skill document.

## WHICH_REPOS_ARE_REFERENCE_ONLY
jacob-ye-seedance-prompt — reference-only, permanently.

## RISKS
- Xianxia robes + long hair are the classic drift surface; costume detail must be frozen in text
  as well as in the reference card.
- Sword side-flip (left hip → right hip) between shots is the most likely continuity break.
- Over-writing motion when a video reference is attached — text and reference will fight.
- Prompt bloat: ten questions answered verbosely produces an unusable wall of text.

## ONE_NEXT_ACTION
Write the 4-shot script table (beat, action, camera, light, end state) and get it approved
before any prompt or card is generated — script first, always.
