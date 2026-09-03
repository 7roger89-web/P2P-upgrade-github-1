# ROUND 1 — 05 REFERENCE_VIDEO_EDIT (source: VACE)

## Grounding
VACE (ICCV 2025), Tongyi Lab: an all-in-one model for video creation and editing covering
reference-to-video (R2V), video-to-video editing (V2V) and masked video-to-video editing (MV2V),
freely composable — Move-Anything, Swap-Anything, Reference-Anything, Expand-Anything,
Animate-Anything. Released as Wan2.1-VACE-1.3B / 14B plus an LTX variant; repo ships
run_vace_pipeline.sh, run_vace_wan.sh, run_vace_ltx.sh, run_vace_preproccess.sh, a preprocessing
stack, UserGuide.md and VACE-Benchmark.

## Lane finding
VACE is the natural home for two things this brief needs: (1) R2V — driving a clip from a locked
character/world reference, and (2) MV2V — repairing a single region of a shot (e.g. the sword)
without re-rolling the whole clip. Both are **runtime** capabilities requiring checkpoints, which
this task forbids. So my contribution now is *plan shape*, not execution.

## CHARACTER_REFERENCE_REQUIREMENTS
For a future R2V pass the references must be clean-background subject plates: character isolated,
prop isolated. VACE's preprocessing stack expects tidy reference inputs; busy backgrounds leak.
So: character card and prop card on neutral ground — which matches what 01 and 03 already ask for.

## WORLD_REFERENCE_REQUIREMENTS
Keep world plates separate from subject plates so they can be composed as distinct references
rather than one baked image. A composed reference set (subject + prop + environment) is the
input shape R2V wants.

## KEYFRAME_REQUIREMENTS
Keyframes should be produced at the same aspect ratio and resolution intended for the clip, and
kept as lossless stills. Expand-Anything means the frame can be widened later, so do not crop
tight at the still stage.

## SHOT_COUNT / SHOT_DURATION
ABSTAIN on count. Note: editing passes are per-clip, so a 4-clip structure means 4 independent
edit surfaces — that is a feature (localised repair), not a cost.

## CAMERA_STRATEGY
ABSTAIN — expert 04's lane.

## MOTION_STRATEGY
Animate-Anything / Move-Anything can drive subject motion from a reference, but only if a driving
reference exists. None exists here. Motion must therefore be authored in-prompt for the first pass.

## CONTINUITY_STRATEGY
The strongest continuity story available is: one reference set, reused unchanged across all four
R2V calls, plus MV2V spot-repair for any single shot that drifts. Never re-generate a good shot to
fix a bad detail — mask the detail.

## ARENA_PROMPT_STRATEGY
Write prompts so each shot is independently editable: one subject, one action, one clear
foreground/background separation. Ambiguous overlaps (sword crossing the face) make masking hard.

## DESIGNARENA_PROMPT_STRATEGY
Generate the reference plates as isolated subjects on neutral ground, plus one composed
"target look" frame. Isolated plates are the reusable asset; the composed frame is only a target.

## WHICH_REPOS_REQUIRE_RUNTIME
VACE **would** require runtime (weights + GPU + its own requirements) — and is therefore
**excluded** for GOLDEN_VIDEO_001 under the brief's hard constraints. Future-conditional only.

## WHICH_REPOS_ARE_REFERENCE_ONLY
VACE — reference-only for this production.

## RISKS
- Temptation to make VACE a dependency of the plan; that would breach the no-inference constraint.
- VACE-on-Wan2.1 vs the Wan2.2 backbone expert 06 describes: version mismatch is a real
  integration hazard if a later render task tries to use both naively.
- Masked repair still re-generates pixels; identity can shift inside the mask.
- Preprocessing quality dominates output quality; dirty plates produce dirty edits.

## ONE_NEXT_ACTION
Specify the reference-plate set (isolated character, isolated golden jian, three world plates) in
the plan as the single reusable asset bundle, and mark all VACE execution as deferred.
