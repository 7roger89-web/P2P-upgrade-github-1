# ROUND 1 — 07 POST_PRODUCTION (source: MoneyPrinterTurbo)

## Grounding
MoneyPrinterTurbo: all-in-one AI short-video generator — give a topic/keyword, it writes the
script, matches footage, generates subtitles and background music and produces an HD short.
Ships a WebUI, an API, cli.py/main.py, config.example.toml, Docker/Docker-compose (CPU and GPU
variants), Python 3.11+, and a moviepy/ffmpeg-based assembly stack. Its value here is the
**assembly and packaging half**: concat, aspect handling, subtitles, BGM, export.

## Lane finding
Post-production is the only stage in this whole production that is genuinely runnable on CPU with
no weights and no paid API — but it has nothing to assemble yet. It activates after clips exist.

## CHARACTER_REFERENCE_REQUIREMENTS / WORLD_REFERENCE_REQUIREMENTS
ABSTAIN — outside lane.

## KEYFRAME_REQUIREMENTS
One packaging constraint: keyframes should also yield a **thumbnail/cover frame** at the delivery
aspect ratio. Pick the cover at plan time, not after the edit.

## SHOT_COUNT / SHOT_DURATION
Assembly view: 4 clips × 5s = 20s finished, which sits well inside short-form delivery. Ask each
clip to be delivered with ~0.5s of usable head and tail so cuts have room. Frame rate must be
identical across all clips or concat re-encodes and softens the image.

## CAMERA_STRATEGY / MOTION_STRATEGY
ABSTAIN — outside lane. One note: whip-fast camera moves at cut points make the seam obvious;
end shots on settled framing.

## CONTINUITY_STRATEGY
Editorial continuity: fixed 1280×720 / 24fps / same codec for every clip; consistent loudness for
the wind bed and music; a single colour pass applied to the whole timeline rather than per clip.

## ARENA_PROMPT_STRATEGY
ABSTAIN on prompt craft. Request only: no burned-in text, no watermark, no letterboxing inside the
generated frame — subtitles and framing are added in post, not baked by the generator.

## DESIGNARENA_PROMPT_STRATEGY
Also produce a title-card still and a cover frame with clear negative space where a title will sit.

## WHICH_REPOS_REQUIRE_RUNTIME
MoneyPrinterTurbo is the **only candidate runtime repo in the whole council** — CPU/ffmpeg only,
no weights. But it is NOT used at the current stage (no clips exist), and its TTS/LLM/material
features would touch paid APIs and are therefore excluded. If ever used here it is
assembly-only: concat, subtitles, BGM, export.

## WHICH_REPOS_ARE_REFERENCE_ONLY
MoneyPrinterTurbo — reference-only *now*; conditionally runtime later, assembly-only.

## RISKS
- Feature creep: its script/LLM/TTS/stock-footage path would pull in paid APIs and keys — banned.
- Mixed fps or resolution between clips forces a re-encode and visible quality loss.
- Auto-subtitles are unnecessary for a dialogue-free approach sequence; adding them adds a
  dependency for no benefit.
- Installing its full requirements set is a heavier footprint than a sandbox needs; ffmpeg alone
  covers concat/export.

## ONE_NEXT_ACTION
Record the delivery spec now — 1280×720, 24fps, 4×5s, no baked text, cover frame chosen — so all
upstream stages author against it.
