# Cinematique → P2P Video Lab research reference

Status: `RESEARCHED / REFERENCE_ONLY`
Adoption: `NOT_ADOPTED`
Vendoring: `NO`
License/reuse status: `UNVERIFIED_FOR_BULK_REUSE`
Recorded: `2026-09-10`
Source: https://vvsvs.pro/cinematique

## Why this is here

Cinematique is a public cinematography reference that organizes 150+ named filmmaking techniques across camera work, lighting, composition, editing, storytelling, visual effects, genres and styles. It is useful to P2P Video Lab primarily as a **director-language reference**, not as a prompt library to copy wholesale.

The durable P2P lesson is:

> `STORY_INTENT -> CINEMATIC_DIRECTION -> MODEL_SPECIFIC_GENERATION_PROMPT`

Do not collapse these layers into one giant prompt.

## P2P value

Potentially useful ideas to research further:

- named camera grammar instead of vague terms such as “cinematic”;
- explicit framing, camera travel, direction, speed and subject lock;
- composition as an intentional control surface;
- motivated lighting and visual-weight decisions;
- editing/storytelling techniques as shot-planning primitives;
- rejection criteria for unwanted camera, face, costume or continuity drift;
- model-neutral direction first, then adaptation to the actual image/video model.

This is relevant to P2P Video Lab because the hard problem is not merely generating an attractive frame. The harder capability is producing shots that belong to the same scene, preserve subject/world continuity, and express a deliberate narrative purpose.

## Proposed minimal vertical slice

Do **not** ingest all 150+ techniques first. Start with roughly 20 techniques that directly affect shot generation and continuity:

- establishing shot
- master shot
- medium shot
- close-up
- POV
- dolly / tracking
- push-in / pull-out
- pan
- tilt
- rack focus
- handheld
- motivated lighting
- back/side lighting
- negative space
- leading lines
- visual weight
- match cut
- cross-cutting
- montage
- reveal / concealment staging

Exact names and final set should be revalidated against the live source before implementation.

## Candidate Director Intent shape

This is a research sketch, **not yet a canonical schema**:

```text
NARRATIVE_PURPOSE
SUBJECT
FRAMING
CAMERA_POSITION
CAMERA_MOVEMENT
LENS_OR_DEPTH_CUE
COMPOSITION
LIGHTING
SUBJECT_MOTION
ENVIRONMENT_MOTION
CONTINUITY_CONSTRAINTS
REJECTION_CRITERIA
```

Example concept:

```text
NARRATIVE_PURPOSE = reveal authority
FRAMING = medium-long -> medium close-up
CAMERA_MOVEMENT = slow push-in
COMPOSITION = centered + strong leading lines
LIGHTING = motivated side/back light
SUBJECT_MOTION = slow advance
CONTINUITY_CONSTRAINTS = face/costume/environment identity fixed
REJECTION_CRITERIA = random orbit, random zoom, face drift, costume drift
```

A future model adapter may translate this intent into Veo/Kling/Seedance/Wan/image-model-specific instructions. The provider-specific prompt is downstream output, not the source of truth.

## Provenance and copyright boundary

Treat Cinematique as **external provenance, not P2P authority**.

Until a clear reuse license for the full corpus is verified:

- do not scrape or mirror the entire site into the repository;
- do not vendor its prompt corpus;
- do not copy long technique descriptions verbatim;
- store source links and P2P-authored abstractions instead;
- independently document cinematography concepts using lawful/public knowledge when they become P2P capabilities.

If future implementation needs exact source text, licensing/provenance must be checked first.

## Future research questions

1. Which cinematic controls are reliably understood by each target video model rather than merely sounding plausible in text?
2. Which controls improve **continuity across adjacent shots**, not only single-shot beauty?
3. Which techniques can be represented provider-neutrally and which require model-specific syntax/control inputs?
4. Can Director Intent become a small reusable layer before prompt generation without becoming another competing router/schema universe?
5. What is the smallest real P2P Video Lab scene that can test this against the current generation pipeline?

## Acceptance for any future adoption

Do not call this a P2P capability merely because the vocabulary is documented. Adoption requires a real scene test showing measurable improvement in shot planning/generation or continuity versus the current baseline.

If evidence is sufficient, stop. Do not build a cinema ontology, dedicated database, second router, 150-technique registry, or new agent population just because the source contains many categories.

## Anti-overengineering gate

Before expanding this reference:

1. Is there a simpler way to achieve the same Video Lab outcome?
2. Does the added step create meaningful capability, evidence or progress?
3. If the step is removed, does a success condition actually become impossible?
4. Are we solving the core video capability, or optimizing supporting infrastructure before the capability works?

One bad answer means reduce scope.
