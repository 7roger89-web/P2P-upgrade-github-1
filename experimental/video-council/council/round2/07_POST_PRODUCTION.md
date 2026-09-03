# ROUND 2 — 07 POST_PRODUCTION — disagreements / risks / corrections

READ: R1 01,02,03,04,05,06.

D1 — vs 06. ACCEPTED, and it corrects me. Handles must be specified in frames: author 144 frames
per shot at 24fps (6.0s) and cut to 120 frames (5.0s) on the timeline. That gives 12 frames of
head and tail without eating 01's required end state.

D2 — vs 01. RESOLVED. 01's objection was that padding must not consume the end state. With the
frame spec above, the 5s of content is intact and the handles are additional. No remaining conflict.

D3 — vs 03/04. ACCEPTED as a binding edit rule: no horizontal flip and no clip reversal at any
point in the edit. I will also not use a mirrored "reaction" trick to bridge a cut.

D4 — vs 05. AGREEMENT. Lossless intermediates, one final encode. Concretely: keep per-shot masters
as delivered, assemble without re-encoding where possible, single H.264/MP4 export at the end.

D5 — vs my own R1 and the brief. SELF-CORRECTION AND A RISK. My source is an end-to-end generator
with LLM script writing, TTS, stock-footage matching and API keys in config.toml. Almost all of
that is out of bounds here. The plan must name the allowed subset explicitly — concat, aspect,
BGM, export — and state that its script/TTS/material/LLM paths are excluded. Otherwise the repo's
own defaults will pull the production toward paid APIs.

D6 — vs 02. AGREEMENT on no baked text. Any title or credit is a timeline layer over the cover
frame, never generated into the image.

RISK I OWN: I am the only repo that *could* run here, which makes me the most likely place for the
"just install it" temptation. Recommendation: for a 4-clip 20s assembly, plain ffmpeg is sufficient
and MoneyPrinterTurbo stays reference-only. Promote it to runtime only if subtitles/BGM/batch
export actually become requirements.
