# ROUND 1 — 03 CHARACTER_CONSISTENCY (source: awesome-character-consistency)

## Grounding
The list's stated core principle: "lock identity in a reference first, then reuse that reference
everywhere. Re-prompting each shot from scratch is what causes drift."
Worked example: generate ONE storyboard image containing the character across ordered panels,
then feed the whole storyboard into a reference-to-video model as a single request, telling it
to read the panels as one continuous shot list — the character carries through with no per-shot
re-rolling. Sections: image identity adapters (IP-Adapter, InstantID, PhotoMaker, PuLID,
ConsistentID), video consistency, storyboard/agentic workflows, ComfyUI, hosted APIs, papers.

## CHARACTER_REFERENCE_REQUIREMENTS
1. ONE canonical identity image of the cultivator — face unobstructed, hair fully visible,
   even light, no strong colour cast. This is the single source of truth; everything else derives.
2. Derived views generated *from* that image (not re-prompted independently): 3/4, profile,
   full body, back view with sword.
3. The golden jian is an identity-bearing prop, not scenery: fixed length, fixed hilt wrap,
   fixed pommel, fixed guard shape. Prop drift reads as character drift.
4. Freeze a written identity token list (hair tie, collar cross direction, sash colour, scar/none)
   and never paraphrase it.

## WORLD_REFERENCE_REQUIREMENTS
Out of my lane for design, but one constraint: world references must be free of any human figure,
or an adapter will pick up the wrong identity. Keep world locking separate from identity locking.

## KEYFRAME_REQUIREMENTS
**The critical artefact is a single storyboard sheet** containing the same character in all four
ordered panels, produced in ONE generation pass. Four separately generated keyframes are the
drift mechanism this list exists to warn about. If per-shot stills are needed, they must be
derived from the storyboard sheet, not independently prompted.

## SHOT_COUNT / SHOT_DURATION
Prefer the smallest shot count that tells the beat — every additional shot is an additional drift
opportunity. 4 panels is at the comfortable edge of one storyboard sheet. Duration: ABSTAIN.

## CAMERA_STRATEGY
Constraint only: avoid full 180° identity-revealing turns and extreme close-ups on unlocked detail
(hands, sword engraving) unless that detail is in the reference.

## MOTION_STRATEGY
Low-amplitude motion preserves identity. Rapid head turns, hair-covering wind, and full-body
occlusion are where faces are re-invented.

## CONTINUITY_STRATEGY
Reference-first, one lock, reused everywhere:
- one identity image → one storyboard sheet → one reference-to-video request per shot,
  always re-attaching the same identity image;
- never re-prompt a shot from text alone;
- verify identity between shots by comparison against the canonical image, not against the
  previous shot (error accumulates if you chain comparisons).

## ARENA_PROMPT_STRATEGY
Every video prompt re-attaches the canonical identity reference and repeats the frozen token
list verbatim. Prompt describes the *beat*, the reference carries the *person*.

## DESIGNARENA_PROMPT_STRATEGY
Two passes only: (a) canonical identity image, (b) the 4-panel storyboard sheet seeded/anchored
on (a). Everything else derives. Explicitly forbid "generate a new version of the character".

## WHICH_REPOS_REQUIRE_RUNTIME
None. My source is a curated list; it contains no executable pipeline. The tools it *links* to
(IP-Adapter, InstantID, ComfyUI, hosted APIs) are out of scope for this task — several are
weight-downloading or paid-API, both banned by the brief.

## WHICH_REPOS_ARE_REFERENCE_ONLY
awesome-character-consistency — reference-only.

## RISKS
- Highest-probability failure for this brief: face drift between S1 wide and S3 medium-close.
- Second: golden sword geometry drift (hilt/pommel changes shot to shot).
- Third: robe layering/collar direction flipping — very common on hanfu.
- Mirroring: a horizontally flipped shot silently swaps the sword hip and the collar cross.
- Attempting to fix drift by adding more descriptive text usually increases it.

## ONE_NEXT_ACTION
Produce the ONE canonical identity image of the cultivator + golden jian, and freeze its token
list in writing, before any storyboard or shot prompt exists.
