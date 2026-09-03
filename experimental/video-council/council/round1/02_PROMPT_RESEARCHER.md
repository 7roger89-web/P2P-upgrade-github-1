# ROUND 1 — 02 PROMPT_RESEARCHER (source: awesome-seedance-prompts)

## Grounding
Corpus snapshot in README + data/posts.json: 300 posts, 191 source accounts, 144 with the full
prompt text, models covered Seedance 2.5 (233), 2.0 (63), Seedance (4), last refreshed
2026-09-03. This is an empirical record of what people actually posted and what shipped —
not a methodology. I report observed practice only.

## Observed patterns relevant to GOLDEN_VIDEO_001
- Prompts that circulate with the clip are typically one dense paragraph, not a form. Subject,
  wardrobe, environment, light, then camera, then a single action verb.
- The highest-view items are single-idea clips: one subject, one movement, one payoff.
  Multi-event prompts are markedly rarer in the with-prompt subset.
- Camera language in the corpus is plain-English shorthand ("slow push in", "tracking shot",
  "crane up"), not numeric trajectories.
- Model attribution matters: the corpus is overwhelmingly Seedance 2.5, so 2.5-era reference
  slot syntax is the safe assumption, and 2.0-era prompts should not be copied verbatim.
- Only 144/300 posts include the prompt; the rest are visual evidence only. Do not infer
  prompt text from a clip.

## CHARACTER_REFERENCE_REQUIREMENTS
Corpus practice: wardrobe and hair are respecified **in the prompt text every time**, even when
a reference image is attached. Recommend a fixed 12–20 word character clause reused verbatim.

## WORLD_REFERENCE_REQUIREMENTS
Environment described with 3–5 concrete nouns plus one weather/light phrase. Long environment
paragraphs correlate with generic output in the corpus.

## KEYFRAME_REQUIREMENTS
ABSTAIN on production mechanics. Observation only: clips whose prompts name a specific opening
composition read as more deliberate.

## SHOT_COUNT / SHOT_DURATION
Corpus is dominated by single-shot clips in the 5–10s band. For a 4-shot piece, keep each shot
independently postable as a standalone clip — that is the shape the corpus rewards.

## CAMERA_STRATEGY
Use the corpus's plain camera vocabulary; one camera phrase per prompt.

## MOTION_STRATEGY
One action verb per prompt. Chained actions ("walks, then draws, then turns") are the most
common failure shape visible in the collection.

## CONTINUITY_STRATEGY
Verbatim clause reuse across prompts — copy-paste the subject clause, change only the beat.

## ARENA_PROMPT_STRATEGY
One paragraph, ~60–110 words, order: subject+wardrobe → environment → light → camera → action.
Negative/ban content kept short; the corpus rarely shows long negative lists.

## DESIGNARENA_PROMPT_STRATEGY
Same subject clause, verbatim, with "still frame, no motion blur" and an explicit composition
noun. Reuse of the identical clause across stills and video is the observable consistency trick.

## WHICH_REPOS_REQUIRE_RUNTIME
None. `scripts/` in my source only rebuilds the list; irrelevant here.

## WHICH_REPOS_ARE_REFERENCE_ONLY
awesome-seedance-prompts — reference-only.

## RISKS
- Corpus bias: it records what got posted, not what worked on the first try. Survivorship.
- Views ≠ prompt quality; the most-watched items are announcements and stunts.
- Copying a 2.0-era prompt into a 2.5 workflow will misuse the reference slots.
- Xianxia/wuxia is thinly represented — low confidence transferring style-specific phrasing.

## ONE_NEXT_ACTION
Extract the with-prompt subset that contains a walking hero / approach-to-a-city composition and
lift only the camera and light phrasing from it into the shot table.
