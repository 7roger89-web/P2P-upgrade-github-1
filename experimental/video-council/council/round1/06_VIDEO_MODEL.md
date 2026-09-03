# ROUND 1 — 06 VIDEO_MODEL (source: Wan2.2)

## Grounding
Wan2.2: MoE architecture for video diffusion (specialised experts across denoising timesteps,
larger capacity at similar compute); curated aesthetic data labelled for lighting, composition,
contrast and colour tone, enabling controllable cinematic style; +65.6% images / +83.2% videos
over Wan2.1; and an open-sourced 5B hybrid **TI2V** model on the Wan2.2-VAE (16×16×4 compression)
supporting text-to-video and image-to-video at **720P, 24fps**, runnable on consumer cards such
as a 4090. Repo ships generate.py, INSTALL.md, requirements*.txt, T2V-A14B / I2V-A14B / TI2V-5B
variants, Diffusers and ComfyUI integrations, and an S2V/CosyVoice speech path.

## Lane finding
Capability envelope only. **No weights are downloaded and generate.py is not run in this task.**

## CHARACTER_REFERENCE_REQUIREMENTS
If a future render uses the I2V/TI2V path, the character reference must be a real image at the
target resolution — 720p-class, correct aspect, sharp face. I2V inherits the input frame's
identity far more reliably than T2V invents it. This is the architectural argument for the
keyframe-first plan the other experts are converging on.

## WORLD_REFERENCE_REQUIREMENTS
Same: world context is best delivered as the first frame rather than as adjectives. The aesthetic
labelling (lighting / composition / contrast / colour tone) means those four axes are worth
naming explicitly in text as well.

## KEYFRAME_REQUIREMENTS
Author keyframes at **1280×720 (16:9), 24fps target**. That is the documented sweet spot of the
open TI2V-5B path and keeps a consumer-GPU render feasible later. Do not author stills at an
aspect the backbone will have to crop.

## SHOT_COUNT / SHOT_DURATION
Feasibility view: short clips per shot are the safe unit. 4 shots × ~5s at 720p/24fps is a
reasonable envelope for the open model class; a single 20s continuous take is not.

## CAMERA_STRATEGY
Supportive note only: Wan2.2's aesthetic labelling covers composition and lighting, so plain
cinematic language ("low wide, golden backlight, slow push-in") lands well. Trajectory control is
not a native text control — agreeing with expert 04 that camera is authored, not computed.

## MOTION_STRATEGY
Complex-motion generalisation improved in 2.2, but a single sustained action per clip remains the
reliable shape. Walking + mist + cloth is well within envelope; combat/flight is not requested.

## CONTINUITY_STRATEGY
Continuity across separate clips is not something the backbone provides. It must come from
identical input keyframes and identical text clauses. Chaining shot N's last frame into shot N+1's
first frame via I2V is the mechanism that actually preserves the world between clips.

## ARENA_PROMPT_STRATEGY
Name the four labelled aesthetic axes explicitly — lighting, composition, contrast, colour tone —
in each prompt, then subject, then one action, then one camera move. Keep the paragraph tight.

## DESIGNARENA_PROMPT_STRATEGY
Stills authored 1280×720, 16:9, with the same four aesthetic axes worded identically to the video
prompt so the still and the clip do not disagree.

## WHICH_REPOS_REQUIRE_RUNTIME
Wan2.2 is the only repo that would ever be the *rendering* runtime — but **not in this task**.
It is future-conditional on a separate, explicitly authorised render task with GPU and weights.

## WHICH_REPOS_ARE_REFERENCE_ONLY
Wan2.2 — reference-only for GOLDEN_VIDEO_001.

## RISKS
- Weight download is multi-tens of GB and is banned here; any plan step that implies it is invalid.
- A14B variants need far more VRAM than TI2V-5B; assuming A14B would silently break feasibility.
- VACE is built on Wan2.1, not 2.2 — cross-version assumptions are unsafe (agrees with 05).
- 720p/24fps is the documented envelope; planning for 1080p invites a late re-plan.
- No native identity lock: without keyframes, a xianxia face will drift shot to shot.

## ONE_NEXT_ACTION
Fix the technical envelope in the plan — 1280×720, 16:9, 24fps, ~5s per shot — so every keyframe
and prompt is authored against it from the start.
