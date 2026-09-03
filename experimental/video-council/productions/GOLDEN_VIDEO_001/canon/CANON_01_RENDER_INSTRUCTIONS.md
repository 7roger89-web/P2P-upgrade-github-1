# CANON_01 — RENDER GATE INSTRUCTIONS
CHARACTER_ID=CANON_01 · PRODUCTION=GOLDEN_VIDEO_001
STAGE: one image, one review. Nothing else is authorised by this file.

## THE RULE THAT MATTERS MOST
**Generate exactly ONE image first.**
**Do NOT generate variants, batches, seeds or alternates until that first image has been
reviewed and recorded in CANON_01_REVIEW_SHEET.md.**
A batch of four "options" is how a production quietly ends up with four different characters.
One image → one review → then either freeze it or fix one named thing and regenerate one image.

---

## 1. WHAT TO USE

| Purpose | Source | Exact location |
|---|---|---|
| Positive prompt | CANON_01_SPEC.md | **§10 IMAGE_GENERATION_PROMPT** — the single indented block |
| Negative prompt | CANON_01_SPEC.md | **§10 → NEGATIVE_CONSTRAINTS** — the block directly under it |
| Identity wording | CANON_01_TOKEN_FREEZE.md | authoritative; never paraphrase |
| Review | CANON_01_REVIEW_SHEET.md | fill in after the render |

Copy both blocks **verbatim**. Do not summarise, reorder, translate, or "improve" them.
Do not add style keywords, artist names, quality spam ("masterpiece, 8k, trending"), or LoRA/style
tags. The spec already carries the style definition.

Output settings: **2:3 portrait, high resolution**, single image, no upscaler pass, no face-fix
pass on the first render (those hide whether the base image is actually correct).
Record the seed if the tool exposes one — a frozen canon needs a reproducible seed.

## 2. THE AUTHORITATIVE VISUAL CANON (restated)
Any conflict with an older document is resolved in favour of this list.

- **IDENTITY** — young adult male xianxia cultivator, 22–26; oval face, high cheekbones, defined
  jaw; almond danfeng eyes, dark amber-brown irises; straight-swept dark brows; narrow straight
  nose; medium-thin closed lips; fair warm-toned matte skin; no scars, no facial hair.
  Expression: composed, quietly confident, not smiling.
- **HAIR** — long near-black glossy hair to mid-back, half-up in a smooth topknot held by **one**
  slim pale-jade ring, two thin face-framing strands. No other ornaments.
- **BODY** — tall slim athletic, eight heads tall, moderate shoulders, narrow waist, long clean
  limbs, elegant long-fingered hands, upright relaxed posture.
- **COSTUME** — three-layer ivory-white cultivation robe (inner under-robe, floor-length
  crossed-front main robe, sheer pale over-robe); collar crossing **RIGHT over LEFT**; wide long
  sleeves; gold-thread cloud-scroll embroidery on **cuffs and lower hem only**; woven gold belt
  with a small centre clasp and two ivory sash ties on the left; low white cloth boots;
  light silk in long vertical folds. No armour, cape, hood or jewellery.
- **WEAPON** — **one** straight double-edged golden jian. Blade ≈ shoulder-to-floor length with a
  shallow central fuller; small plain flat gold crescent guard; charcoal cord diamond-wrapped grip
  over gold; plain round gold pommel with **one** short pale tassel; faint steady warm-gold inner
  glow along the fuller and edges. Empty scabbard on the **LEFT hip**; sword drawn in the **right
  hand**, point down at ~30°, clear of the body and the face.
- **STYLE** — high-end cinematic xianxia key art; photoreal materials with a slight painterly
  finish; silk as silk, gold as brushed metal, blade as polished steel; high texture detail;
  restrained warm-neutral grade. Not anime, not cartoon, not 3D-toy.
- **CAMERA** — full body head to boots, nothing cropped; chest-height level camera; front
  three-quarter ~20° off axis with the face near-frontal; 85mm portrait feel, no distortion.
- **BACKGROUND** — flat neutral mid-grey studio backdrop, soft even gradient, nothing else.
- **POSE** — neutral heroic standing, weight on both feet, left arm relaxed, right arm lowered
  holding the jian point-down. No action posing.

**Absolute:** no horizontal mirroring of the result, ever. A flip reverses the collar and moves
the sword to the wrong hip, breaking two identity tokens at once.

## 3. THE THREE RECONCILED OVERRIDES (restated)
CANON-01 supersedes PRODUCTION_PLAN.md §1/§3 on exactly these points:

| # | Item | Superseded (old plan) | Authoritative (CANON-01) |
|---|---|---|---|
| 1 | Robe | pale blue-grey hanfu | **white-and-gold cultivation robe** |
| 2 | Sword | plain non-glowing golden jian | **golden jian with a faint controlled inner glow** |
| 3 | Framing | 3/4 upper body, 16:9 | **full body, 2:3 portrait** (identity plate only) |

Still binding from the original plan: long dark hair · collar right-over-left · scabbard on the
LEFT hip · no mirroring. The 1280×720 / 16:9 / 24fps envelope continues to govern shot keyframes
and clips — CANON-01 is an identity plate, not a shot, and its portrait aspect does not propagate.

## 4. PROCEDURE
1. Copy §10 prompt + NEGATIVE_CONSTRAINTS verbatim into the image tool.
2. Set 2:3 portrait, high resolution. Generate **ONE** image. Record the seed.
3. Save it inside this `canon/` directory as `CANON_01_v1.png` (v2, v3… on later attempts).
4. Open CANON_01_REVIEW_SHEET.md and score all 13 checks against the image.
5. **STOP.** Either the canon is frozen or exactly one thing is fixed and one new image is made.

## 5. NOT AUTHORISED BY THIS GATE
No video. No storyboard. No shot keyframes. No environment or city art. No character variants,
outfit variants, expression sheets or turnarounds. No new council round. No software installs,
no model weights, no paid APIs. No changes to P2P core.
