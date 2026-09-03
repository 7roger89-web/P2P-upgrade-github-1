# CANON_01 — REVIEW SHEET
CHARACTER_ID=CANON_01 · PRODUCTION=GOLDEN_VIDEO_001
Fill this in with the rendered image open beside CANON_01_TOKEN_FREEZE.md.
One sheet per rendered image. Copy the block below for attempt v2, v3, … if needed.

```
IMAGE_FILE=            # e.g. CANON_01_v1.png
SEED=
REVIEW_DATE=
REVIEWER=
```

## RULES FOR SCORING
- Write only `PASS` or `FAIL`. Nothing else.
- Judge only what you can actually see. **If you are unsure, it is FAIL.**
- All 13 checks are critical. There are no optional fields and no "approved with notes".
- Do not excuse a flaw because it "can be fixed in the storyboard" — the storyboard inherits it
  and multiplies it across four shots.

## CHECKLIST
```
FACE_IDENTITY_CLEAR=                 # sharp, both eyes readable; danfeng eyes + straight-swept
                                     # brows + narrow straight nose all clearly present
HAIR_CLEAR=                          # long to mid-back, half-up topknot, ONE jade ring, 2 face strands
BODY_PROPORTIONS_CLEAR=              # head to boots visible; tall slim athletic ~8 heads; normal anatomy
COSTUME_FRONT_CLEAR=                 # robe front readable; collar visibly crosses RIGHT over LEFT
COSTUME_DETAILS_CLEAR=               # three layers, wide sleeves, gold belt + clasp, cuff & hem
                                     # embroidery, sash ties, boots — all distinguishable
WEAPON_SHAPE_CLEAR=                  # straight double-edged jian; fuller, crescent guard, wrapped
                                     # grip, round pommel, ONE tassel all visible
WEAPON_SCALE_CLEAR=                  # blade ≈ shoulder-to-floor; whole sword ≈ half his height
NO_DUPLICATE_WEAPON=                 # exactly one sword (an empty scabbard on the left hip is OK)
NO_EXTRA_LIMBS=                      # 2 arms, 2 legs, 1 head, 5 fingers per hand, no fused digits
FACE_UNOBSCURED=                     # nothing crossing the face — hair, sleeve, blade, shadow, glow
FULL_CHARACTER_READABLE=             # nothing cropped: head, boots, sword point all inside frame
STYLE_MATCH=                         # cinematic xianxia key art, photoreal materials, neutral grey
                                     # backdrop, no anime/cartoon, no VFX clutter
SUITABLE_FOR_STORYBOARD_DERIVATION=  # sharp, high-res, clean silhouette, usable as the single
                                     # reference for the 4-panel storyboard sheet
```

## VERDICT
```
ALL_THIRTEEN_PASS=          # YES / NO

STATUS=                     # APPROVED_AND_FROZEN  (only if ALL_THIRTEEN_PASS=YES)
                            # REGENERATE           (if any single field is FAIL)
```

## FAILURE_REASON
Only if STATUS=REGENERATE. Name the failed field(s) and describe what you actually see, in one
line each. Be concrete — "hair is wrong" is not actionable; "hair ends at the shoulders, spec
requires mid-back" is.
```
FAILED_FIELDS=
WHAT_WENT_WRONG=
```

## REVISION_NOTES_FOR_REGEN
Only if STATUS=REGENERATE. The smallest possible change that addresses the named failure.
```
PROMPT_LINE_TO_ADJUST=       # which line of SPEC §10 to strengthen (do not rewrite the prompt)
NEGATIVE_TERMS_TO_ADD=       # e.g. "shoulder-length hair, bob cut"
SEED_STRATEGY=               # keep same seed (targeted fix) | new seed (composition failure)
EVERYTHING_ELSE=UNCHANGED
```
Regeneration rules:
- Change only what the failure requires. Do not redesign the character.
- Do not accept a different-looking person who merely scores better — that is a new character,
  not a fixed one.
- Generate **ONE** image per attempt, then fill in a fresh copy of this sheet.
- Persistent failure on the same field after 3 attempts means the spec wording is at fault, not
  the model: fix CANON_01_SPEC.md, note it here, and continue.

## ON APPROVAL
If STATUS=APPROVED_AND_FROZEN:
1. Record `IMAGE_FILE` and `SEED` above — they are now production assets.
2. CANON-01 is immutable. No further character generation is permitted.
3. All later material must derive from CANON-01, or from a storyboard/keyframe derived from
   CANON-01. Independent re-generation of the character per shot is forbidden.
4. Next stage (a separate task, not authorised here): the 4-panel storyboard sheet.
