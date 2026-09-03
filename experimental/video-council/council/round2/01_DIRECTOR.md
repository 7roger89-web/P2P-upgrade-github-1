# ROUND 2 — 01 DIRECTOR — disagreements / risks / corrections

READ: R1 02,03,04,05,06,07.

D1 — vs 02 (60–110 word single paragraph). MATERIAL DISAGREEMENT, partly conceded.
The corpus shape is a *single-shot* shape. A 4-shot piece with a hard continuity lock cannot
carry its ban list and end-state in 110 words. Compromise: the **body** of each prompt stays
corpus-shaped and tight (~90 words); the continuity lock + ANTI-AI tail is a fixed appended
block reused verbatim across all four shots. Tight where it matters, locked where it must be.

D2 — vs 03 (one storyboard sheet replaces separate keyframes). ACCEPTED, and it corrects me.
My R1 asked for 6 stills + a storyboard sheet, which implies independent character generations.
Correction: the canonical identity image comes first, the 4-panel sheet is derived from it, and
per-shot stills are derived from the sheet. The sheet is the continuity spine, not an extra.

D3 — vs 06 (specify 1280×720/24fps in the plan). ACCEPTED for the plan, REJECTED for the prompt.
My source is explicit that duration and aspect are set in the generation UI and must never appear
inside the prompt text. So: envelope lives in the plan and the delivery spec, not in prompt bodies.

D4 — vs 04. AGREEMENT, reinforcing. Camera is authored per window, one move per window; a
re-camera pass is not in the critical path. My "one lens one move" rule and 04's ladder are the
same rule from two sources.

D5 — vs 05. CAUTION. VACE's MV2V repair and my repair-SOP agree in spirit ("fix the broken
window, never re-run the chain"), but VACE repair is banned runtime here. The plan must state the
repair rule as a *method* with a no-runtime fallback: re-roll the single shot with the same
references, not a masked edit.

D6 — vs 07. MINOR CORRECTION. 07 wants ~0.5s head/tail per clip. My rule is ≥3s per window with
an explicit end state; head/tail padding must not eat the end state. Resolve by asking for 5s of
usable action plus padding, i.e. author the shot as 5s of content, not 5s including handles.

RISK I OWN: prompt bloat. If the ten questions are answered verbosely in the prompt rather than in
the script table, output degrades. The answers belong in the shot table; the prompt gets the
distillation.
