# ROUND 2 — 05 REFERENCE_VIDEO_EDIT — disagreements / risks / corrections

READ: R1 01,02,03,04,06,07.

D1 — vs 03. CONCEDED. My R1 positioned MV2V spot-repair as the continuity safety net. 03 is right
on two counts: it is banned runtime here, and masked regeneration can itself shift identity.
Correction: for GOLDEN_VIDEO_001 the safety net is "re-roll the single shot against the unchanged
canonical references." VACE repair is a future upgrade of that rule, not the rule.

D2 — vs 06. MATERIAL RISK I want recorded explicitly in the plan. VACE ships as Wan2.1-VACE-1.3B /
14B — it is built on Wan2.1. 06's envelope is Wan2.2 TI2V-5B. Anyone who later tries to run a VACE
edit pass over Wan2.2 output on the assumption of a shared stack will hit a version mismatch and a
second full environment. This must be written down now or it will be discovered expensively later.

D3 — vs 04. ACCEPTED. 04's cap on loose framing is correct and I withdraw the Expand-Anything
framing argument for this production. Compose the shot properly; do not compose for a pass that
is out of scope. My remaining request is narrower: keep the stills lossless and uncropped as
delivered, so a future pass has the original.

D4 — vs 01. AGREEMENT, with a note. 01's repair-SOP ("fix the broken window, not the chain") and
my MV2V philosophy are the same principle at two runtime levels. Recommend the plan state it once
as a production rule, then note the two implementations (no-runtime re-roll now, masked edit later).

D5 — vs 02. AGREEMENT on the surface-mismatch point. Reference-slot semantics differ between a
hosted Seedance surface and an open R2V model; the plan should keep the reference *bundle* abstract
(isolated character plate, isolated prop plate, three world plates) and let each surface bind it
its own way.

D6 — vs 07. AGREEMENT. Lossless intermediates, single encode at the end.

RISK I OWN: my repo is the easiest one to accidentally promote from reference to dependency,
because its scripts look immediately runnable. Restate: VACE is REFERENCE-ONLY for this task.
