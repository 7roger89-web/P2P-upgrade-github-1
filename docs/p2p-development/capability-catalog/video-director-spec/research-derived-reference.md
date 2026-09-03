# Research-Derived Reference — AI Video Direction

Capability: `video.prompt.director_spec`
Workstream: P2P-VIDEO-CAPABILITY-INTEGRATION-01 (GitHub Issue #71)
Predecessor: P2P-VIDEO-RESEARCH-01 — complete, research-only, no repository mutation.
Durable adoption records: `governance/research-adoption-ledger.json` → `RA-EXT-070` … `RA-EXT-077`
Pins resolved: 2026-09-03 via GitHub repository metadata only.

**Nature of this file.** This is a *bounded derived reference*: the minimum useful
knowledge P2P extracted, in P2P's own words, with exact upstream pins so the
derivation is recoverable. It is **not** a mirror, not a translation, and
not a copy of any upstream file. No upstream `FORMULA.md`, prompt corpus, dataset, checkpoint,
or runtime was copied, vendored, downloaded, or installed.

---

## 1. Attribution notice (CC-BY-4.0 — must be preserved)

```
JACOB YE · SEEDANCE PROMPT
Copyright (c) 2026 Jacob Ye

Licensed under the Creative Commons Attribution 4.0 International
License (CC BY 4.0) — https://creativecommons.org/licenses/by/4.0/

Upstream repository: https://github.com/jacobye2017-afk/jacob-ye-seedance-prompt
Pinned upstream commit: f74d2fcfa803cec4007fdfbeae9cde8831693ee7
Pinned upstream tree:   883377396a8c945d8d1f9ff4a37cde73a9bca6e6
Default branch: master   ·   upstream pushed_at: 2026-08-24T06:18:44Z

The upstream NOTICE file additionally credits these incorporated sources, and that
credit is preserved here unchanged:
  - ByteDance Seedance 2.5 official prompt guide (2026-07-31)
  - Seedance 2.5 production reference by Serge Shima, smixs/visual-skills (CC BY 4.0)
  - MapleShaw/seedance2.0-prompt-skill

P2P treatment: KNOWLEDGE_REFERENCE + PRIMARY_METHOD_PROVENANCE.
Nothing was vendored. Derived concepts below are P2P's own restatement, attributed
to the pinned revision.
```

---

## 2. Repository pins (all seven, metadata-only resolution)

| # | Repository | Pin (commit) | Pin (tree) | Licence at pin | Accepted treatment |
| --- | --- | --- | --- | --- | --- |
| 1 | `https://github.com/jacobye2017-afk/jacob-ye-seedance-prompt` | `f74d2fcfa803cec4007fdfbeae9cde8831693ee7` | `883377396a8c945d8d1f9ff4a37cde73a9bca6e6` | CC-BY-4.0 | `KNOWLEDGE_REFERENCE` + `PRIMARY_METHOD_PROVENANCE`; attribution required; not vendored |
| 2 | `https://github.com/opensource-works/awesome-seedance-prompts` | `5ba05bc9849b4502e282fce329ff7ba741bcca18` | `dc83da241e87d8a95cb980b1241346ef59223a01` | NOASSERTION | `PROMPT_CORPUS` + `BENCHMARK_REFERENCE`; `READ_ONLY`; third-party prompts **not** vendored |
| 3 | `https://github.com/Wan-Video/Wan2.2` | `42bf4cfaa384bc21833865abc2f9e6c0e67233dc` | `553393a92dbf6ffc81250a237523d3415f607a52` | Apache-2.0 | `MODEL_ADAPTER_CANDIDATE` + `FUTURE_BACKEND`; **no** runtime installation |
| 4 | `https://github.com/ali-vilab/VACE` | `48eb44f1c4be87cc65a98bff985a26976841e9f3` | `a54245198942cc85989cc22a68adef248bb09727` | Apache-2.0 | `KNOWLEDGE_REFERENCE`; conditioning/control-slot vocabulary only; **no** runtime installation |
| 5 | `https://github.com/KlingAIResearch/ReCamMaster` | `fcf98bc86e876bb534518cd99e8a65b282f0f16e` | `dc290b5e97f8f2b00da539f3c2459dd73eea2ed5` | MIT | `KNOWLEDGE_REFERENCE`; AI-video camera vocabulary only; `BENCHMARK_ONLY`; **no** runtime installation |
| 6 | `https://github.com/divolleggett/awesome-character-consistency` | `81ec30770ae70ad2602997f258292a4e6bb3e9d6` | `a1c380e033e58e3c16023be944002ee158848676` | NOASSERTION | `KNOWLEDGE_REFERENCE`; consistency taxonomy only |
| 7 | `https://github.com/harry0703/MoneyPrinterTurbo` | `cbbb366393105d5cefc254dc9ed492d43da0711b` | `2f86fab447e1b438b80f6079961d80a79ca0e385` | MIT | `POST_PRODUCTION_REFERENCE` + `FUTURE_BACKEND`; **no** installation |

Eighth reference (not a repository): `SEEDANCE-2.5-SOLO-SKYDIVE-LIVE-TV-JP-01` —
`KNOWLEDGE_REFERENCE` for prompt architecture only; session-derived artifact;
recorded as `RA-EXT-077`.

Licence gate carried forward from the existing P2P asset-forge convention: a
`NOASSERTION` or missing SPDX identifier blocks executable projection. Repositories
2 and 6 are therefore knowledge-only, and repository 2's third-party prompt corpus
is never vendored or redistributed by P2P.

---

## 3. Minimum useful knowledge extracted per source

### 3.1 `jacob-ye-seedance-prompt` — PRIMARY METHOD PROVENANCE

Adopted (restated, not copied):

1. **Director-first, not prompt-first.** The unit of authoring is a shot with a
   stated intention; the prompt is the last artifact produced, assembled from a
   fixed set of sections. → P2P: master spec first, provider projection last
   (protocol §0, §5).
2. **Reference separation with an explicit exclusion declaration.** Scene/world
   references and character references are bound separately, each with a declared
   responsibility and an explicit "what this reference must not contribute". →
   P2P: `REFERENCE SLOT → ADOPT → EXCLUDE` (protocol §2).
3. **One action and one camera move per time window**, with a minimum viable window
   so a move can actually complete. → P2P: `ONE PRINCIPAL CAMERA MOVE PER BEAT`
   as a director rule, explicitly **not** a universal hard validator (protocol §4.2).
4. **Every beat declares a visible end-state.** The end-state is the handoff
   contract to the next beat and the next shot. → P2P: protocol §4.1, §6.
5. **Light in three layers** — source, then behaviour, then colour tone. Unmotivated
   light is the most reliable "generated, not filmed" tell. → P2P: protocol §1 field 5.
6. **Performance written as observable physical signal, not adjective**, with the
   character's intention stated so the movement has a cause. → P2P: protocol §1 field 3.
7. **Two-layer prohibitions** — a global anti-artifact layer plus a scene-specific
   layer with temporal gating ("must not appear before beat N"). → P2P: protocol
   §1 field 11.
8. **Continuity lock statements are repeated per shot and per extension**, and
   costume/prop are specified to a concrete degree (cut, length, closure, material,
   state) because generic descriptions drift. → P2P: protocol §1 fields 1 and 10,
   §2.3.
9. **Identifying features are restated in words even when a reference image is
   bound.** → P2P: protocol §2.4.
10. **Camera move as psychological verb** — the move is chosen for meaning. →
    P2P: protocol §4.3.
11. **Sound as a distinct, marked layer** — music, effects, and dialogue kept
    separable, with an explicit language/dialect declaration for speech. → P2P:
    protocol §1 fields 8 and 9.
12. **Repair by re-cutting, not by full re-run** — a failed tail is replaced by a
    bounded continuation from a known end-state. → P2P: bounded-retry boundary,
    protocol §7.

Explicitly **not** adopted:

- Any provider-specific marker syntax, slot-count budget, or numeric prompt-length
  constant. Upstream documents a recommended working length for **its own** target
  provider; P2P adopts no numeric length constant for any provider (protocol §5.2).
- The provider-specific assembly template as a P2P output format. P2P's master spec
  is provider-neutral; the template belongs to a future provider profile.
- Upstream's provider-compliance and platform-red-line lists — volatile, unverified
  in P2P, and only admissible through the governed Live Specs path.
- The full `FORMULA.md`. This bounded derived reference is sufficient.

### 3.2 `awesome-seedance-prompts` — PROMPT CORPUS / BENCHMARK REFERENCE (READ_ONLY)

Adopted: the *existence and shape* of a community prompt corpus — i.e. that real
prompts in the wild are short, flat, natural-language, frequently unstructured, and
often single-paragraph. That is the empirical reason P2P keeps the master spec
structured but requires a **flattening** projection step.

Not adopted: no prompt text, no gallery entry, no showcase item, no third-party
prompt is copied, vendored, translated, or redistributed. Licence is `NOASSERTION`,
which blocks executable projection under the existing P2P licence gate.

### 3.3 `Wan2.2` — MODEL ADAPTER CANDIDATE / FUTURE BACKEND

Adopted: the *concept* that an open-weight text/image-to-video family exists whose
adapter surface would later need declared inputs (prompt, conditioning images,
duration, resolution/aspect, seed) and declared outputs (artifact path, generation
metadata). Recorded as `MODEL_ADAPTER_CANDIDATE` only.

Not adopted: no clone, no install, no weight download, no dependency, no runtime
commitment. Any future adapter is an `OWNER GATE` (infrastructure/runtime
commitment) and must pass the existing licence and model-weight gates.

### 3.4 `VACE` — KNOWLEDGE REFERENCE (conditioning / control-slot vocabulary)

Adopted: task-level vocabulary for how a video model can be conditioned —
reference-to-video, video-to-video editing, and masked video-to-video editing, with
composed control slots (move / swap / reference / expand / animate). This is where
P2P's conditioning-concept list in protocol §6 gets its shape.

Not adopted: no installation, no inference code, no preprocess tooling, no model
download, no benchmark run.

### 3.5 `ReCamMaster` — KNOWLEDGE REFERENCE (camera vocabulary), BENCHMARK_ONLY

Adopted: the published **basic camera trajectory vocabulary** used as neutral naming
for a principal move — pan left/right, tilt up/down, zoom in/out, translate
up/down with rotation, arc left/right with rotation. Adopted as *words*, so that
"arc to frontal" in protocol §4.3 is unambiguous.

Not adopted: no checkpoint, no dataset, no training or inference code, no
re-capture pipeline. Classified `BENCHMARK_ONLY`: it is a comparison point for what
camera-controlled re-generation could later mean, nothing more.

### 3.6 `awesome-character-consistency` — KNOWLEDGE REFERENCE (consistency taxonomy)

Adopted: the structural insight that character consistency is **not one problem**.
The source separates image identity/consistency material from video consistency
material and from storyboard/agentic workflow material. That separation is the
external corroboration for P2P's required inequality:

```
IMAGE_CONSISTENCY != VIDEO_TEMPORAL_CONSISTENCY != SHOT_TO_SHOT_CONTINUITY
```

P2P's ten-concept taxonomy (protocol §3) is P2P's own enumeration; only the
"these are different problems" insight is taken from this source.

Not adopted: no workflow, no node graph, no hosted-API integration, no paper list
mirroring. Licence is `NOASSERTION` → knowledge only.

### 3.7 `MoneyPrinterTurbo` — POST PRODUCTION REFERENCE / FUTURE BACKEND

Adopted: the post-production stage decomposition
`SCRIPT → MATERIAL → NARRATION → SUBTITLE → MUSIC → RENDER → FINAL ARTIFACT`,
and the operational boundaries that fall out of it — credentials gate, paid-
generation gate, infrastructure gate, bounded retry, "failure is not an advance",
"final output is a durable returned artifact" (protocol §7).

Not adopted: no installation, no vendoring, no wrapper, no Docker/Colab path, no
service integration, no execution.

### 3.8 `SEEDANCE-2.5-SOLO-SKYDIVE-LIVE-TV-JP-01` — KNOWLEDGE REFERENCE (prompt architecture)

Adopted, from prompt architecture only:

- A single high-motion continuous action still benefits from being split into
  beats with distinct camera responsibilities rather than one compound instruction.
- Sustained physical plausibility (free-fall body position, air resistance, cloud
  and ground relative motion) must be stated as explicit physics expectations, not
  left to the model.
- A continuous-action shot needs an explicit **visible end-state**, otherwise the
  generation ends ambiguously and cannot be chained.
- Live/broadcast framing intent (what the "camera operator" is trying to keep in
  frame) is a useful way to express a chase move.

Not adopted: no session artifact is vendored; no claim from it enters P2P as a
verified fact.

---

## 4. Recoverability

Every derived statement above resolves to the pinned commit/tree in section 2 and to
the adoption record in `governance/research-adoption-ledger.json`. Re-opening a
source is required whenever exact current upstream content matters; the pins here
describe what P2P derived from, not what upstream says today.
