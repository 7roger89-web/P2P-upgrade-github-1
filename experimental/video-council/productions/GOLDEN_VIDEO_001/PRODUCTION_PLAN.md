# GOLDEN_VIDEO_001 — EXECUTABLE PRODUCTION PLAN
STATUS: APPROVED BY COUNCIL (rounds 1–3 complete, council closed)
STAGE: pre-keyframe. **Nothing has been rendered. No keyframe generated yet.**
LOGLINE: one consistent xianxia male cultivator with a golden sword approaching a fantasy city.

TECHNICAL ENVELOPE (single, non-negotiable): 1280×720, 16:9, 24fps.
Per shot: author 144 frames (6.0s), deliver 120 frames (5.0s) on the timeline.
Finished length: 4 × 5s = 20s.

---

## 1. CHARACTER_REFERENCE_REQUIREMENTS
ONE canonical identity image is the single source of truth. Everything else derives from it.

- **CANON-01** — canonical identity image: male xianxia cultivator, 3/4 upper body, neutral even
  light, flat neutral background, face unobstructed, hair fully visible, golden jian visible.
- **CHAR-PLATE-A** — full body, derived from CANON-01, neutral ground, sword on LEFT hip.
- **PROP-01** — the golden jian alone, neutral grey ground, derived from CANON-01's sword.
  The sword is identity-bearing: fixed blade length, hilt wrap, guard shape, pommel.

FROZEN TOKEN LIST (copied verbatim into every prompt, never paraphrased):
> long black hair, half-up in a jade ring; pale blue-grey hanfu robe, collar crossing
> right-over-left; dark grey sash; straight golden jian with a plain guard, worn on the left hip.

RULES
- No independent re-generation of the character, ever.
- No horizontal mirroring at any stage (flip swaps the hip and the collar cross).
- Verify every generated frame against CANON-01, never against the previous shot.

## 2. WORLD_REFERENCE_REQUIREMENTS
Three world plates, each containing **zero human presence** — no figures, passers-by, shadows,
reflections, statues, posters, mannequins or blurred human silhouettes.
- **WORLD-01** mountain ridge road, drifting mist, low golden sun from screen left.
- **WORLD-02** fantasy city wall and main gate at middle distance, pagoda silhouettes behind.
- **WORLD-03** gate-front detail: banners, hanging lanterns, weathered stone.
World plates are bound separately from character plates — one binding per plate, each with its
own exclusion clause. Merged bindings are forbidden.

## 3. KEYFRAME_REQUIREMENTS
Ordered, and this order is the continuity spine:
1. CANON-01 (canonical identity image).
2. **STORY-SHEET-01** — one 4-panel storyboard sheet, produced in a SINGLE pass, same character
   in all four ordered panels, reading as one continuous shot list.
3. **KF-S1..KF-S4** — four per-shot keyframes derived from STORY-SHEET-01 (not independently
   prompted), each authored at 1280×720 / 16:9, lossless, uncropped, ~10% compositional margin.
4. **COVER-01** — cover/thumbnail frame taken from an existing locked keyframe, with negative
   space for a title. Not a separate character generation.
Total keyframe artefacts: 1 canonical + 1 storyboard sheet + 4 shot keyframes + 2 plates
(CHAR-PLATE-A, PROP-01) + 3 world plates. No baked text, no watermark, no letterboxing.

## 4. SHOT_COUNT
**4 shots.** Smallest count that carries approach → arrival without a montage; every extra shot
is an extra identity-drift surface.

## 5. SHOT_DURATION
**5.0s delivered per shot** (120 frames @24fps), authored at 144 frames. ≥3s minimum per window
is satisfied with margin. One core action and one camera move per shot.

## 6. CAMERA_STRATEGY
One lens, one move, decelerating to rest before every cut. Screen direction is left → right in all
four shots; the axis is never crossed.

| Shot | Framing | Lens feel | Move |
|---|---|---|---|
| S1 | wide, ridge, figure enters frame | 24mm | static |
| S2 | three-quarter back, tracking | 35mm | slow lateral dolly |
| S3 | medium-close, face lifts, city on the blade | 50mm | slow push-in |
| S4 | wide from behind, gate ahead | 24mm | slow push-in, locked horizon (crane-up = optional alternate) |

Camera is authored in-prompt in plain cinematic language. No numeric trajectories.
No re-camera correction pass in the critical path.

## 7. MOTION_STRATEGY
One sustained action per shot; walking pace constant across all four. Camera motion and subject
motion never change at the same time. Four-part breathing feel in every shot:
environment micro-motion (mist drift, banner flutter) · character micro-motion (robe hem, breath,
blink) · camera micro-motion (≤2% float) · sound micro-motion (wind bed).
Excluded: rapid head turns, hair blowing across the face, full-body occlusion, combat, flight,
glow trails — all identity-destroying.

## 8. CONTINUITY_STRATEGY
1. **Reference lock** — CANON-01 re-attached to every generation; frozen token list copied verbatim.
2. **Keyframe lock** — no shot is authored text-only (no T2V). Every shot starts from its keyframe.
3. **Chaining** — shot N's end state is the written first line of shot N+1's setup; where an
   image-to-video path is used, shot N's last frame seeds shot N+1.
4. **Fixed tail block** — identical in all four prompts: same face, same hair ring, same robe
   colour and wear, sword always LEFT hip, same time of day, same weather, same walking direction.
5. **No mirroring, no reversal**, in generation or in edit.
6. **Repair rule** — re-roll the single broken shot against unchanged references. Never re-run the
   chain. (Masked repair is a future upgrade, not a dependency.)
7. **Verification gate** — every frame compared to CANON-01 before the shot is accepted.

## 9. ARENA_PROMPT_STRATEGY  *(video-generation prompt surface — primary: Seedance-shaped)*
Per shot, one tight paragraph of ~90 words in fixed order:
`subject + frozen token list → environment → light (source → behaviour → tone) → one camera
phrase → one action verb`, followed by the **fixed tail block** (continuity lock + ANTI-AI ban +
clean-video declaration), identical across all four shots.
- References declared individually, each with its own exclusion clause; merged bindings forbidden.
- Duration and aspect ratio never appear in prompt text (set in the UI / CLI).
- ANTI-AI global ban: extra fingers, floating feet, sword clipping the robe, duplicated character,
  modern objects, text or watermark. Scene-specific ban: crowds at the gate, a second sword,
  glow trails, any human figure in world plates.
- A Wan2.2-shaped variant is recorded for a possible future local path; it names the four labelled
  aesthetic axes (lighting, composition, contrast, colour tone) and passes resolution/frames as CLI
  arguments. It is a variant, not a second envelope.
- Re-roll budget: assume 2–3 attempts per shot; posted-prompt corpora show only successes.

## 10. DESIGNARENA_PROMPT_STRATEGY  *(still / keyframe / reference-image prompt surface)*
Two authored passes only, everything else derived:
- **Pass A** — CANON-01: neutral studio light, flat background, no environmental storytelling,
  "still frame, no motion blur", explicit composition noun.
- **Pass B** — STORY-SHEET-01: 4 ordered panels, same character in all four, one generation.
Derived outputs: CHAR-PLATE-A, PROP-01, KF-S1..S4, COVER-01.
World plates use the human-exclusion list as an explicit negative. All stills 1280×720 / 16:9,
lossless, same wording of the light/tone description as the corresponding video prompt so the still
and the clip do not disagree. Explicitly forbidden instruction: "generate a new version of the
character."

## 11. WHICH_REPOS_REQUIRE_RUNTIME
**None. Zero repositories are executed for GOLDEN_VIDEO_001.**
Future-conditional only, each gated behind a separate, explicitly authorised task:
| Repo | Condition to become runtime |
|---|---|
| Wan2.2 | authorised render task + GPU + weights (TI2V-5B, 720p@24fps envelope) |
| VACE | authorised edit task; note it is built on Wan2.1, a different generation |
| ReCamMaster | requires an existing base clip + Wan2.1 weights + GPU; authors state the open version underperforms the paper |
| MoneyPrinterTurbo | CPU/ffmpeg assembly only, once clips exist; script/LLM/TTS/stock-material paths excluded |

## 12. WHICH_REPOS_ARE_REFERENCE_ONLY
All seven, for this production:
jacob-ye-seedance-prompt (permanently — methodology) · awesome-seedance-prompts (permanently —
corpus) · awesome-character-consistency (permanently — curated list) · ReCamMaster · VACE ·
Wan2.2 · MoneyPrinterTurbo.

## 13. RISKS
| # | Risk | Owner | Mitigation in this plan |
|---|---|---|---|
| R1 | Face drift between wide S1 and close S3 | 03 | CANON-01 lock, keyframe-first, verification gate |
| R2 | Golden jian geometry drift | 03 | PROP-01 derived, sword treated as identity-bearing |
| R3 | Mirroring swaps hip and collar | 03/04/07 | absolute no-flip / no-reversal rule |
| R4 | Prompt bloat degrades output | 01 | ten questions answered in the shot table, not the prompt |
| R5 | Corpus survivorship bias | 02 | explicit 2–3 re-roll budget per shot |
| R6 | Seedance vs Wan2.2 surface confusion | 02/06 | two prompt variants, one asset envelope |
| R7 | Wan2.1 (VACE/ReCamMaster) vs Wan2.2 version mismatch | 05/06 | recorded now; any combined pipeline is two environments |
| R8 | ReCamMaster scope creep into critical path | 04 | marked OUT, non-blocking optional future pass |
| R9 | MoneyPrinterTurbo feature creep to paid APIs | 07 | allowed subset = concat/aspect/BGM/export; ffmpeg sufficient |
| R10 | Accidental promotion of a reference repo to a dependency | 05 | §11/§12 are binding; sources/ is git-ignored |
| R11 | No automated identity verification exists | 03 | manual gate against CANON-01 defined as a required step |

## 14. ONE_NEXT_ACTION
**Generate CANON-01 — the single canonical identity image of the xianxia cultivator with the
golden jian — and freeze its token list in writing. Nothing else starts until it is approved.**

---
COUNCIL CLOSED. No further rounds. No render authorised by this plan.
