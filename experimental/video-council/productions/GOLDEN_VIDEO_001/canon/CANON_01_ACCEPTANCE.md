# CANON_01 — ACCEPTANCE CHECKLIST
CHARACTER_ID=CANON_01 · PRODUCTION=GOLDEN_VIDEO_001

How to use: generate the image from CANON_01_SPEC.md §10, then open it next to
CANON_01_TOKEN_FREEZE.md and answer every line below with PASS or FAIL.
Judge only what you can actually see in the image. If you are unsure, it is a FAIL —
an ambiguous canon poisons every later shot.

## CHECKLIST
```
FACE_IDENTITY_CLEAR=              # face sharp, fully visible, both eyes readable; danfeng eyes,
                                  # straight-swept brows, narrow straight nose all clearly present
HAIR_CLEAR=                       # long to mid-back, half-up topknot, ONE jade ring, 2 face strands
BODY_PROPORTIONS_CLEAR=           # head to boots visible; tall slim athletic, ~8 heads; normal anatomy
COSTUME_FRONT_CLEAR=              # robe front readable; collar visibly crosses RIGHT over LEFT
COSTUME_DETAILS_CLEAR=            # three layers, wide sleeves, gold belt + clasp, cuff & hem
                                  # embroidery, sash ties, boots — all distinguishable
WEAPON_SHAPE_CLEAR=               # straight double-edged jian; fuller, crescent guard, wrapped grip,
                                  # round pommel, ONE tassel all visible
WEAPON_SCALE_CLEAR=               # blade ≈ shoulder-to-floor; whole sword ≈ half his height
NO_DUPLICATE_WEAPON=              # exactly one sword in frame (empty scabbard on left hip is OK)
NO_EXTRA_LIMBS=                   # 2 arms, 2 legs, 1 head, 5 fingers per hand, no fused digits
FACE_UNOBSCURED=                  # nothing crossing the face — no hair, sleeve, blade, shadow, glow
FULL_CHARACTER_READABLE=          # nothing cropped: head, boots and sword point all inside frame
STYLE_MATCH=                      # cinematic xianxia key art, photoreal materials, neutral grey
                                  # backdrop, no anime/cartoon look, no VFX clutter
SUITABLE_FOR_STORYBOARD_DERIVATION=  # sharp, high-res, clean silhouette, usable as the single
                                     # reference for the 4-panel storyboard sheet
```

## CRITICAL_FIELDS
All of these are critical — every field above is critical. There are no optional checks.
A canon that is 90% right produces a character that is 90% right in four different directions.

## CANON_01_APPROVAL_RULE
```
CANON_01_APPROVAL_RULE = PASS only if ALL fields above are PASS.

  any field FAIL  ->  STATUS=REGENERATE
  all fields PASS ->  STATUS=APPROVED_AND_FROZEN
```
Partial acceptance is not permitted. There is no "approved with notes" and no "fix it later in
the storyboard" — the storyboard inherits the flaw and multiplies it across four shots.

On **STATUS=REGENERATE**: change only the prompt lines or negative constraints that address the
specific failed field, then regenerate. Do not redesign the character and do not accept a
different-looking person who happens to score better.

On **STATUS=APPROVED_AND_FROZEN**: record the approved image path and date at the bottom of this
file, and CANON-01 becomes immutable. From that moment, all later visual material must derive from
CANON-01 or from an approved storyboard/keyframe derived from CANON-01. Independent
re-generation of the character for individual shots is forbidden.

## RESULT (fill in after review)
```
IMAGE_PATH=
REVIEW_DATE=
STATUS=            # REGENERATE | APPROVED_AND_FROZEN
```
