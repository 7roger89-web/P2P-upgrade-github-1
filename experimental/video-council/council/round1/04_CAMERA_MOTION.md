# ROUND 1 — 04 CAMERA_MOTION (source: ReCamMaster)

## Grounding
ReCamMaster: "Camera-Controlled Generative Rendering from A Single Video" (ICCV'25 oral).
It re-shoots an **existing** video along a **new camera trajectory**. Repo ships
inference_recammaster.py, train_recammaster.py, vis_cam.py, download_wan2.1.py,
example_test_data, and is built on a Wan2.1 T2V base. The README itself states the open-source
version is a reference implementation and may not match the paper's model, and points users to
a hosted form / Kling for the best version.

## Core lane finding
ReCamMaster is a **post-capture** tool. Its input is a video that already exists. GOLDEN_VIDEO_001
has no footage yet. Therefore ReCamMaster is **not applicable at the current stage**, and cannot
be applicable until a base clip exists. Any plan that puts it before the first render is wrong.

## CHARACTER_REFERENCE_REQUIREMENTS / WORLD_REFERENCE_REQUIREMENTS
ABSTAIN — outside lane.

## KEYFRAME_REQUIREMENTS
Only this: frame keyframes with headroom and lateral margin. Re-camera passes crop into the
existing frustum; a tightly framed original leaves no room for a new trajectory.

## SHOT_COUNT / SHOT_DURATION
ABSTAIN on count. Note: camera-trajectory work is evaluated on short single clips; long takes are
not where this class of method is demonstrated.

## CAMERA_STRATEGY
For this production, camera must be authored **in-prompt at generation time**, not corrected
afterwards. Recommended: one simple, monotonic trajectory per shot (static / lateral dolly /
push-in / crane-up). Reserve ReCamMaster-style re-camera strictly as an optional future pass on a
clip we already like but want a second angle of — e.g. an alternate angle on S3 without
re-rolling the character.

## MOTION_STRATEGY
Keep subject motion and camera motion decoupled and simple: if the camera moves, the subject
walks at constant pace; do not combine a camera move with a subject direction change.

## CONTINUITY_STRATEGY
Consistent screen direction across all shots (left → right). Do not cross the axis. Keep a single
notional focal-length ladder so the space reads as one place.

## ARENA_PROMPT_STRATEGY
One camera phrase per prompt, stated in plain language, placed after the environment and before
the action. No trajectory numbers — that vocabulary belongs to a runtime this task does not use.

## DESIGNARENA_PROMPT_STRATEGY
Keyframes should state the camera height and lens feel ("low wide, 24mm feel") so the still and
the eventual clip agree on perspective.

## WHICH_REPOS_REQUIRE_RUNTIME
None now. ReCamMaster would require Wan2.1 weights + GPU + its own env — explicitly banned by the
brief. Flag it as **future-conditional**, gated on (a) an existing base clip, (b) an explicit new
task authorising weights and GPU.

## WHICH_REPOS_ARE_REFERENCE_ONLY
ReCamMaster — reference-only for GOLDEN_VIDEO_001.

## RISKS
- Planning a re-camera pass into the critical path would block the whole production on a banned
  runtime.
- Re-camera passes can degrade identity; it is a second generative pass over the character.
- Open-source quality caveat is stated by the authors themselves — do not budget on paper results.
- Complex camera moves in-prompt (orbit + push + tilt) are the usual cause of geometry warping.

## ONE_NEXT_ACTION
Lock a one-move-per-shot camera ladder in the shot table and record ReCamMaster as an explicitly
deferred, non-blocking optional pass.
