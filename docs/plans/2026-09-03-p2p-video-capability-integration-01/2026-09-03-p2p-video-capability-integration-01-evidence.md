# P2P Video Capability Integration 01 — Evidence

## Metadata

- Date: `2026-09-03`
- Task ID: `P2P-VIDEO-CAPABILITY-INTEGRATION-01`
- GitHub issue: `#71` (`7roger89-web/P2P-upgrade-github-1`)
- Base main SHA: `c1ddc4fdbc3bf6639a5f3e3f171a7fb5c1df6352`
- Branch: `arena/01a0664a-p2p-upgrade-github-1`
- Plan: `2026-09-03-p2p-video-capability-integration-01-plan.md`
- Evidence: this file
- Benchmark: `N/A` (declared in the plan; issue #71 forbids a benchmark suite)
- Actual status: `N/A` (declared in the plan; single-slice goal, baseline captured in `E1`)

Evidence IDs are stable and phase-scoped so the plan, this file, and later agents can
reference exact proof.

---

## E0 — Preflight and fresh authority check

| Check | Result |
| --- | --- |
| `WORKSPACE_FUNCTIONAL` | `YES` — shell, git, and `gh` all functional in the Arena sandbox |
| Repository access | `git status`, `git log`, `gh issue view 71` all succeeded |
| `git fetch origin --prune` | succeeded |
| `origin/main` resolved | `c1ddc4fdbc3bf6639a5f3e3f171a7fb5c1df6352` |
| `KNOWN_MAIN_SHA_AT_TASK_CREATION` | `c1ddc4fdbc3bf6639a5f3e3f171a7fb5c1df6352` |
| `git rev-list --count <known>..origin/main` | `0` — **origin/main did not move** |
| Consequence | No newly merged capability could own the same responsibility; the known base SHA is used unchanged and no re-basing analysis was required |
| Issue #71 state | `OPEN`, title `P2P-VIDEO-CAPABILITY-INTEGRATION-01: minimal video director foundation` |
| Research repeated? | `NO` — `P2P-VIDEO-RESEARCH-01` accepted as complete; the six-repository audit was not re-run |

Surfaces inspected (minimum relevant context only — no broad audit):
`AGENTS.md`, issue #71, `.p2p/system/p2p_capabilities/capabilities.json`,
`.p2p/system/p2p_capabilities/model.py`,
`.p2p/system/p2p_capabilities/routing.py`,
`.p2p/system/p2p_capabilities/vendor_skill.py`,
`governance/research-adoption-ledger.json`, `governance/research-intake-ledger.json`,
`governance/intake-contract.json`, `governance/p2p-development-roadmap.json`,
`governance/drift-policy.json`, `governance/runtime-manifest.lock.json`,
`governance/live-specs.json` + `live-specs.lock.json`,
`docs/p2p-development/capability-catalog/game-asset-forge/visual-reference-pack.schema.json`,
`docs/p2p-development/capability-ledger/capability-ledger.schema.json`,
`docs/RESEARCH-ADOPTION-LEDGER.md`, `NOTICE.md`,
`docs/plans/2026-09-02-p2p-social-content-skills-01/*`,
`tests/test_p2p_social_content_skills.py`,
`tests/test_p2p_capability_foundation.py`,
`tests/test_p2p_visual_vendor_integration.py`,
`tests/test_p2p_game_toolchain_02a.py`,
`tests/test_p2p_ledger_provenance.py`,
`scripts/validate_p2p_development_framework.py`.

Overlap confirmed against existing responsibilities:

| Existing surface | Overlap found | Action |
| --- | --- | --- |
| `visual.gpt_image_2_style_library` | Owns IMAGE prompt construction only; `camera` is already one of its `NEGATIVE_TRIGGERS` | Preserved byte-identically; new capability prohibited from expanding it |
| `media.whiteboard_animation` | Owns whiteboard/storyboard/SRT production; carries generic triggers `scene`, `animation`, `render` | Preserved byte-identically; new capability prohibited from routing into it |
| `p2p-visual-reference-pack/1` | Owns the six-view character reference vocabulary | Reused verbatim by reference; no second schema created |
| `game.three.cinematic` | Cinematic **camera animation inside a Three.js runtime** — a different responsibility from AI-video prompt direction | No overlap; left untouched |
| `creative.copywriting`, `creative.social.*` | Text/social copy, not video direction | No overlap; left untouched |
| `.agents/skills/p2p/references/legacy/*` | Legacy historical material mentioning video AI vendors | Legacy material is non-authoritative per `AGENTS.md`; not used, not edited |
| Governed Live Specs | Owns runtime-authoritative volatile provider facts | Not touched; provider profile data declared `UNKNOWN_UNTIL_VERIFIED_PROFILE` and routed to that path only |

No existing capability was found to own AI-video direction. Zero contradictions with
the accepted research classifications were found in current canonical P2P, so none
were reopened.

---

## E1 — Pre-change baseline (captured before any mutation)

Command (per module, because `tests/` has no `__init__.py` and `pytest` is absent):

```
for f in tests/test_*.py; do m=$(basename $f .py); \
  timeout 120 python3 -m unittest tests.$m ... ; done
```

- Failing test modules at base main: **31 of 82**
- `test_p2p_capability_foundation`: `Ran 28 tests … FAILED (failures=2)`
  (`test_cf1_model_has_exact_six_classes` asserts `capability_count == 39` while base
  main already holds 72; `test_cf21_no_external_framework_surface`)
- `test_p2p_visual_vendor_integration`: `Ran 10 tests … FAILED (failures=5, errors=3)`
- `test_p2p_vendor_skill_integration`: `Ran 22 tests … FAILED (failures=3, errors=1)`
- `test_p2p_game_toolchain_02a`: `Ran 14 tests … FAILED (failures=3, errors=1)`
- `test_p2p_social_content_skills`: **PASS** (the most recent capability precedent)
- Root cause of the vendor-snapshot family of failures: `VENDOR_SNAPSHOT_HASH_MISMATCH`
  for `gpt-image-2-style-library-9a7b2e9` (observed
  `de9598c1e2a06a3de14b405d28abcb496e058d34d4e876342ad22f8f50761ecb` vs declared
  `29121408bbfdd4994ec4738b6ee181c80ba123cb7554c297e8a07091faddc482`) — pre-existing,
  out of scope
- `scripts/validate_p2p_development_framework.py`: `52/58 checks passed. 6 failed.`
  (`V03-family-registered`, `V05-dep-integrity`, `V06-charter-no-competitor-patterns`,
  `V09-freshness-vocab`, `V12-origin-type-valid`, `V20-pr-lineage-declared`)
- `governance/runtime-manifest.lock.json` governance drift at base main: **3 files**
  (`governance/development-control.json`, `governance/project-adoption-lifecycle.md`,
  `governance/research-adoption-ledger.json`); 28 governance entries matched
- `governance/research-adoption-ledger.json`: `69` records, `RA-EXT-001` … `RA-EXT-069`
- `.p2p/system/p2p_capabilities/capabilities.json`: `72` capabilities
- `docs/p2p-development/capability-ledger/capability-index.json`: `176` records;
  `docs/p2p-development/current-roadmap.md` declares `176 records` (`V15` in sync)

Canonical hashes frozen for the "must not disturb" assertions:

| Artifact (base main) | Canonical SHA-256 |
| --- | --- |
| `visual.gpt_image_2_style_library` registry entry | `81f9394346af72f2b6ce7c910dca12966100ae3499e61d31757063e19962beb4` |
| `media.whiteboard_animation` registry entry | `d451e77538625a681b210e65199bdaf9b0b20ac5425336f0015e505ce5575104` |
| `creative.copywriting` registry entry | `2b1d77e311c36a4df9409597fda636265498e8d65f4b282ab67258d1fe875d5f` |
| `research-adoption-ledger.json` first 69 records | `9318599107e5786b8f134e305d4ddcbe550f98d690d60d872b61fe84855c62b9` |
| `research-adoption-ledger.json` top level (ex-`records`/`notes`) | `23d85912b13543ba6ea01fc4c8a83213ab8a61e4cbad99e02738927f123ed3ec` |
| `visual-reference-pack.schema.json` file bytes | `71ea8fd728705eb57e545188cf272e042893a0d6ebfe72c815ecb3090d78ab83` |

---

## E2 — Upstream pin resolution (metadata only)

Resolved 2026-09-03 through `gh api repos/<owner>/<repo>` and
`gh api repos/<owner>/<repo>/commits/HEAD`. **No repository was cloned, checked out,
vendored, or installed. No model weight, checkpoint, or dataset was downloaded.**
Reading upstream text for knowledge extraction only; the single file read in full
was jacob-ye's `NOTICE` (434 bytes) and `SKILL.md` (3113 bytes), plus heading/section
extractions of `FORMULA.md` and the four `docs/*.md` files, from which a bounded
derived reference was written in P2P's own words.

| Repository | Commit | Tree | Licence | Treatment |
| --- | --- | --- | --- | --- |
| `jacobye2017-afk/jacob-ye-seedance-prompt` | `f74d2fcfa803cec4007fdfbeae9cde8831693ee7` | `883377396a8c945d8d1f9ff4a37cde73a9bca6e6` | CC-BY-4.0 | `KNOWLEDGE_REFERENCE` + `PRIMARY_METHOD_PROVENANCE` |
| `opensource-works/awesome-seedance-prompts` | `5ba05bc9849b4502e282fce329ff7ba741bcca18` | `dc83da241e87d8a95cb980b1241346ef59223a01` | NOASSERTION | `PROMPT_CORPUS` + `BENCHMARK_REFERENCE`, `READ_ONLY` |
| `Wan-Video/Wan2.2` | `42bf4cfaa384bc21833865abc2f9e6c0e67233dc` | `553393a92dbf6ffc81250a237523d3415f607a52` | Apache-2.0 | `MODEL_ADAPTER_CANDIDATE` + `FUTURE_BACKEND` |
| `ali-vilab/VACE` | `48eb44f1c4be87cc65a98bff985a26976841e9f3` | `a54245198942cc85989cc22a68adef248bb09727` | Apache-2.0 | `KNOWLEDGE_REFERENCE`, control-slot vocabulary only |
| `KlingAIResearch/ReCamMaster` | `fcf98bc86e876bb534518cd99e8a65b282f0f16e` | `dc290b5e97f8f2b00da539f3c2459dd73eea2ed5` | MIT | `KNOWLEDGE_REFERENCE`, `BENCHMARK_ONLY`, camera vocabulary only |
| `divolleggett/awesome-character-consistency` | `81ec30770ae70ad2602997f258292a4e6bb3e9d6` | `a1c380e033e58e3c16023be944002ee158848676` | NOASSERTION | `KNOWLEDGE_REFERENCE`, consistency taxonomy only |
| `harry0703/MoneyPrinterTurbo` | `cbbb366393105d5cefc254dc9ed492d43da0711b` | `2f86fab447e1b438b80f6079961d80a79ca0e385` | MIT | `POST_PRODUCTION_REFERENCE` + `FUTURE_BACKEND` |

`SEEDANCE-2.5-SOLO-SKYDIVE-LIVE-TV-JP-01` — session-derived reference artifact, not a
repository, `KNOWLEDGE_REFERENCE` for prompt architecture only. `REPOS_REVIEWED` stays
**7**.

Licence gate applied: `NOASSERTION` blocks executable projection (same gate as the
existing `game-asset-forge` catalog), so repositories 2 and 6 are knowledge-only and
repository 2's third-party prompt corpus is never vendored.

Attribution preserved for jacob-ye in three places: the registry entry
(`UPSTREAM_PROVENANCE.primary_method_provenance.license`), the derived reference
(section 1 notice block), and adoption record `RA-EXT-070`. The upstream `NOTICE`'s
own incorporated-source credits (ByteDance Seedance 2.5 official prompt guide
2026-07-31; Serge Shima / `smixs/visual-skills` CC BY 4.0;
`MapleShaw/seedance2.0-prompt-skill`) are carried through unchanged.

---

## E3 — Implementation: files changed

Modified (3):

| File | Change |
| --- | --- |
| `.p2p/system/p2p_capabilities/capabilities.json` | `72 -> 73` capabilities. Purely additive: `git diff --numstat` reports `428 / 0` — zero deleted lines. `172117 -> 188966` bytes. SHA-256 `4917df7a96ac6c302efad90b4fd647872f2f81a3902fb38e518d7fcdd4afbfad` |
| `governance/research-adoption-ledger.json` | `69 -> 77` records, append-only; `notes` `1 -> 3`. `git diff --numstat` reports `323 / 1`: the single "deletion" is the final pre-existing `notes` string re-emitted with a trailing comma, so no historical content was removed. `106439 -> 132914` bytes. SHA-256 `a9a2a9031212f60e22d527e4055c8ec450a183f817a4ebaa3eb38a0cc86b3956` |
| `docs/RESEARCH-ADOPTION-LEDGER.md` | `+64 / -0`, a bounded addendum (section 7) covering only the eight new records, their provenance notes, and the declared deviations. Sections 1–6 are untouched and their pre-existing staleness is not repaired |

New (5):

| File | Lines | Role |
| --- | --- | --- |
| `docs/p2p-development/capability-catalog/video-director-spec/README.md` | 90 | bounded scope, reuse map, responsibility boundaries, non-goals, owner gates |
| `docs/p2p-development/capability-catalog/video-director-spec/director-spec-protocol.md` | 382 | the capability contract: 12 fields, reference binding, consistency taxonomy, shot/timeline, provider projection, shot chaining, post-production boundaries, prohibited actions, validation contract |
| `docs/p2p-development/capability-catalog/video-director-spec/research-derived-reference.md` | 214 | CC-BY-4.0 attribution notice, all seven pins, minimum derived knowledge per source, explicit non-adoptions |
| `docs/plans/2026-09-03-p2p-video-capability-integration-01/validation/ly-truong-sinh-sword-descent.master-spec.json` | 548 | the master director spec for the issue #71 request |
| `docs/plans/2026-09-03-p2p-video-capability-integration-01/validation/ly-truong-sinh-sword-descent.provider-projection.json` | 119 | the single compact provider projection derived from it |

Plus this plan/evidence pair, and one focused validation module
(`tests/test_p2p_video_director_spec.py`, 882 lines, one class, 16 tests, no
duplicates) and a bounded addendum to the human projection
`docs/RESEARCH-ADOPTION-LEDGER.md`.

**New dependencies: none.** No `requirements.txt`, no `package.json`, no lockfile, no
submodule, no vendored tree. New executable modules added to
`.p2p/system/p2p_capabilities/`: **none** (asserted by `test_02`).

Registry entry classification:

```
CAPABILITY_ID     video.prompt.director_spec
TYPE              KNOWLEDGE_SOURCE          (one of the existing six classes)
SEMANTIC_KIND     SKILL                     (existing orthogonal vocabulary)
INVOCATION_CLASS  MODEL_ROUTABLE
TRUST_LEVEL       PURE_DATA
STATUS            ACTIVE
CANONICAL_QUORUM_MEMBER  false              (denominator stays 8)
OPTIONAL_SPECIALIST      false
is_vendor_skill()        false              (mode is P2P_NATIVE_KNOWLEDGE_DERIVATION)
UPSTREAM_PROVENANCE.dual_classification  ["KNOWLEDGE_SOURCE","MODEL_ROUTABLE_SKILL"]
```

`KNOWLEDGE_SOURCE + MODEL_ROUTABLE SKILL` is expressed with the representation the
registry already supports: `TYPE` carries the six-class contract, and the existing
orthogonal `SEMANTIC_KIND` vocabulary (`SKILL`, `TOOL`, `ADAPTER`, `VENDOR`,
`EXTERNAL_RUNTIME`, `KNOWLEDGE_SOURCE`) carries the skill role. `model.py` documents
that vocabulary as existing precisely so no new registry class or second registry is
created. No new capability architecture was introduced.

---

## E4 — Routing evidence through the existing single router

Router used: `p2p_capabilities.routing.classify_capabilities` via the existing
registry. **No second router was created.** `route["single_router"]` is `true` and
`route["schema"]` is `p2p-capability-route/1`.

Request (issue #71 validation request, capability-named so routing is deterministic):

```
Viết video prompt (video.prompt.director_spec): Tạo cảnh Lý Trường Sinh cưỡi kiếm
lao xuống Thiên Kiếm Thành, giữ nguyên khuôn mặt, trang phục và thanh kiếm; camera
đuổi từ phía sau rồi vòng sang chính diện.
```

Observed:

```
route.selected = ['game.mengto.camera_controls', 'video.prompt.director_spec']
  video.prompt.director_spec   PRIMARY    value=2  pos=['video prompt','video.prompt.director_spec'] neg=[]
  game.mengto.camera_controls  SECONDARY  value=1  pos=['camera']                                    neg=[]
vendor projection selected = ['game.mengto.camera_controls']   (PURE_DATA source is never a vendor skill)
content_loaded = False    permission_grant = False
```

Bare idea sentence without a video-direction signal:

```
route.selected = ['game.mengto.camera_controls']
  video.prompt.director_spec   NOT_APPLICABLE  value=0  pos=[]  neg=[]
```

This is the intended behaviour and is asserted: a bare scene sentence is ambiguous
(it could be prose, a storyboard image, or a game scene), so the capability requires
an explicit video-direction signal and does not over-capture.

**Observed pre-existing routing collision, not repaired (out of scope).**
`game.mengto.camera_controls` carries a bare `camera` trigger, so it is selected
`SECONDARY` on any request containing the word `camera`, including a Vietnamese
AI-video request where it has no business. Repairing it means editing an existing
capability entry, which this bounded goal does not do. Recorded here so the Owner
can decide. `test_05` proves the new capability's triggers never displace an
existing selection on the 13 routing requests already asserted elsewhere in the
suite.

Trigger design: 30 positive triggers (English + Vietnamese), all compound or
capability-named. Bare `video`, bare `camera`, bare `prompt`, bare `shot`, and bare
`sword` were deliberately **not** used as triggers, because `prompt` and `camera`
already appear in asserted routing requests and `sword` appears in
`"Create a Three.js xianxia sword from an approved reference."`. 39 negative
triggers enforce the whiteboard / image-prompt / marketing / install / runtime /
provider-API boundaries.

---

## E5 — Focused synthetic validation (the one representative validation)

Request: exactly the issue #71 sentence. No video render, no API, no benchmark
suite, no second validation case.

### E5.1 USER IDEA -> MASTER DIRECTOR SPEC

`validation/ly-truong-sinh-sword-descent.master-spec.json`
(`spec_id = VDS-VALIDATION-01-LY-TRUONG-SINH-SWORD-DESCENT`, `provider_neutral = true`)

All twelve minimum fields demonstrated (`test_06`):

| Field | Demonstrated |
| --- | --- |
| `identity_constraints` | face, hair, body proportions, costume, single sword — restated in words **and** bound to slots; five consistency concepts locked |
| `scene` | Thiên Kiếm Thành, late afternoon to dusk, broken cloud deck, cultivation-world rules, xianxia painted-cinematic art direction, three-depth parallax cues |
| `actor_performance` | one core action + intention + 4–5 observable physical signals per beat + subtext; `not_adjectives_only = true` |
| `camera` | three beats, one principal move each, framing + lens intent as visible effect + psychological verb + end-state of move per beat |
| `lighting` | three layers: source (high sun + city lantern/forge glow) → behaviour (rake, cloud shadow bands, key rotation across the arc, warm rim) → colour tone (cold blue-grey to amber-bronze, never reversing) |
| `physics` | 7 must-obey + 6 must-not-happen: acceleration then terminal rate, blade loading, continuous airflow on cloth/hair, cloud/ground parallax, atmospheric perspective, no hover |
| `timeline` | three ordered non-overlapping beats covering `0.0–1.0`, each with duration window, actor, framing, move, environment, lighting, physics, dialogue, audio, **visible end-state**, continuity |
| `dialogue` | `NOT_APPLICABLE` with reason (the request specifies no line) **plus** the forward contract: language declaration required, expected `vi`, TTS-friendly phrasing, must not contradict `actor_performance`, marked separately from music/SFX |
| `audio` | music layer declared (with an explicit no-default-music rule), per-beat SFX, ambience/room tone, sound bridge (city ambience leaks forward into BEAT-02) |
| `continuity` | the three concepts locked separately with `sufficient_for_shot_acceptance`/`satisfied_within_one_generation` flags, the three-way inequality asserted and explained for this shot, five global lock statements, sword and costume state ledgers per beat with `state_change_without_stated_cause = PROHIBITED` |
| `negative_constraints` | 10 global + 9 scene-specific, including temporal gating ("gate and wall must NOT be legible before BEAT-03"), move discipline, and output purity |
| `model_specific_projection` | points at the single projection artifact; records direction, lossiness, keep/drop/compress policy, `provider_profile_used = NONE_VERIFIED`, `hard_coded_prompt_length_constant_used = false`, `structured_prompt_assumption = NOT_ASSUMED` |

**Two camera beats, not one overloaded command** (`test_07`). The request contains
two moves — `camera đuổi từ phía sau` (rear chase) and `rồi vòng sang chính diện`
(arc to frontal). The spec authors:

| Beat | Window (fraction) | Principal move | Count |
| --- | --- | --- | --- |
| `BEAT-01` rear chase descent | `0.00–0.40` | `REAR_CHASE_FOLLOW` | 1 |
| `BEAT-02` arc to frontal | `0.40–0.75` | `ARC_TO_FRONTAL` (`ARC_RIGHT_WITH_ROTATION` family) | 1 |
| `BEAT-03` frontal arrival hold | `0.75–1.00` | `LOCKED_OFF_FRONTAL_HOLD` | 1 |

Asserted: `camera_moves_requested = 2`, `len(beats) >= 2`, every beat
`principal_camera_move_count == 1`, moves distinct, chase index `<` arc index,
windows contiguous and covering the shot, `collapsed_into_one_overloaded_command =
false`, and `recorded_deviation = null`. `BEAT-03` exists to carry the chainable
visible end-state and adds no second move to any beat.
`ONE_PRINCIPAL_CAMERA_MOVE_PER_BEAT` is recorded as
`DIRECTOR_RULE_NOT_UNIVERSAL_VALIDATOR`; no validator module exists (asserted).

Reference binding (`test_08`): six slots
(`CHARACTER_REFERENCE`, `COSTUME_REFERENCE`, `SYMBOLIC_PROP_REFERENCE`,
`WORLD_REFERENCE`, `STYLE_REFERENCE`, `PREVIOUS_SHOT_FINAL_FRAME`), **every one**
declaring non-empty `ADOPT` and `EXCLUDE`. `CHARACTER_REFERENCE` adopts
face/hair/body proportions/outfit and excludes source background/unrelated
characters/unrelated props; it binds to `p2p-visual-reference-pack/1` and reuses all
six view ids verbatim (`full_body_front`, `full_body_three_quarter`,
`full_body_side`, `full_body_back`, `face_front`, `face_three_quarter`), asserted
against the schema's own `enum`. The sword — a canonical symbolic prop — receives
its own `SYMBOLIC_PROP_REFERENCE` slot with a stated reason and a per-beat state
ledger. `PREVIOUS_SHOT_FINAL_FRAME` is `NOT_APPLICABLE` (shot 1) but is declared so
shot 2 inherits the contract. No reference stills exist for this synthetic
validation, and that is declared visibly (`instance_available_at_validation = false`)
rather than silently substituted.

Consistency (`test_09`): all ten concepts recorded in the registry provenance and the
protocol; the three inequalities asserted in both the protocol and the instance;
`consistency_engine_built = false`; no executable consistency engine exists.

### E5.2 MASTER DIRECTOR SPEC -> SHORT PROVIDER PROMPT

`validation/ly-truong-sinh-sword-descent.provider-projection.json`
(`projection_number_for_this_validation = 1`)

| Property | Value |
| --- | --- |
| Direction | `CANONICAL_MASTER_SPEC -> SHORT_PROVIDER_SPECIFIC_PROMPT` |
| Master spec mutated? | `false` — it stays provider-neutral |
| Target profile | `UNNAMED_FLAT_PROSE_VIDEO_PROVIDER`, `named_provider = null`, `verified_profile_available = false` |
| All 12 profile fields | `UNKNOWN_UNTIL_VERIFIED_PROFILE` |
| Format decision | `FLAT_NATURAL_LANGUAGE_PROSE`; `marker_syntax_used = NONE`; `field_labels_emitted = false` — because `accepts_labelled_structured_prompt` is UNKNOWN |
| Budget | `SHORT_FORM_FLAT_PROSE_SINGLE_PARAGRAPH_SET`, `budget_source = SUPPLIED_BY_CALLER_FOR_THIS_VALIDATION_ONLY`, `budget_is_a_p2p_constant = false` |
| Prompt length | **1317 characters**, 7 period-terminated sentences, asserted equal to `len(prompt_text)` so it cannot drift |
| Source master spec | 31111 bytes — the projection is materially shorter (asserted) |
| Kept | identity lock, both camera beats in order, light source + colour arc, the reveal-gating prohibition, the visible end-state |
| Dropped | dialogue, three-layer audio detail, taxonomy labels, the slot table, caller-control provenance, chain handoff, non-goals, subtext, window guidelines, psychological-verb annotations |
| Compressed | 3 beats → one ordered sentence chain; 10 global prohibitions → one clause; 9 scene-specific prohibitions → the reveal gate kept explicit; 3 lighting layers → one clause; 7 physics rules → one clause |
| Invented facts | `[]` — `compress_never_invent_respected = true` |
| Reversible | `YES`, every clause maps back to a named master-spec field |
| Provider-side controls | duration `12s` and aspect `2.35:1` are declared as caller-supplied provider controls and asserted **absent from the prompt text** |
| Executed? | `submitted_to_any_provider = false`, `provider_api_called = false`, `credentials_used = false`, `video_rendered = false`, `paid_video_generation_used = false`, `artifact_returned_by_a_provider = null` |

`test_12` additionally regex-scans all five new artifacts for any
`<provider> … (max|limit|characters) … <number>` pattern and finds none, and asserts
the protocol states `No permanent hard-coded prompt-length limit` and
`P2P hard-codes no duration constant`, and the derived reference states
`P2P adopts no numeric length constant for any provider`. No Arena, DesignArena,
Seedance, Kling, Wan, or other provider limit is hard-coded anywhere.

### E5.3 Chain proved

`USER IDEA -> MASTER DIRECTOR SPEC -> SHORT PROVIDER PROMPT` — demonstrated end to
end on one representative request, with no video render, no API call, no dependency
install, and no benchmark suite.

---

## E6 — Governance evidence

### E6.1 Research adoption ledger (append-only)

`governance/research-adoption-ledger.json`, `69 -> 77` records:

| Record | Source | Status | Family | Owner decision |
| --- | --- | --- | --- | --- |
| `RA-EXT-070` | jacob-ye-seedance-prompt | `SELECTED` | `SKILLS_AND_KNOWLEDGE` | `OWNER_SELECTED` |
| `RA-EXT-071` | awesome-seedance-prompts | `RESEARCHED` | `RESEARCH_ONLY_REGISTER` | `REFERENCE_ONLY` |
| `RA-EXT-072` | Wan2.2 | `DEFERRED` | `RESEARCH_ONLY_REGISTER` | `CONDITIONAL` |
| `RA-EXT-073` | VACE | `SELECTED` | `SKILLS_AND_KNOWLEDGE` | `REFERENCE_ONLY` |
| `RA-EXT-074` | ReCamMaster | `SELECTED` | `SKILLS_AND_KNOWLEDGE` | `REFERENCE_ONLY` |
| `RA-EXT-075` | awesome-character-consistency | `SELECTED` | `SKILLS_AND_KNOWLEDGE` | `REFERENCE_ONLY` |
| `RA-EXT-076` | MoneyPrinterTurbo | `DEFERRED` | `RESEARCH_ONLY_REGISTER` | `CONDITIONAL` |
| `RA-EXT-077` | SEEDANCE-2.5-SOLO-SKYDIVE-LIVE-TV-JP-01 | `SELECTED` | `SKILLS_AND_KNOWLEDGE` | `REFERENCE_ONLY` |

- Every status is inside the ledger's own `status_vocabulary`; none is
  `IMPLEMENTED`, `VERIFIED`, or `SHIPPED`, because the ledger forbids inferring
  IMPLEMENTED from a report and the capability exists on a candidate branch only.
- Every record uses exactly the existing 19-field record shape (asserted), cites
  `issue #71`, and lists `selected_ideas`, `rejected_ideas`, `p2p_translation`,
  `evidence_pointers`, and a `DEFERRED` reason where applicable.
- Both `DEFERRED` records carry an explicit reason, satisfying the roadmap
  coverage-gate rule that a deferred selected item must say why.
- Append-only verified two ways: the first 69 records' canonical hash equals the
  frozen base-main hash, and the top level (excluding `records`/`notes`) equals its
  frozen hash, so `generated_at`, `generated_by`, `authority`, `status_vocabulary`,
  `intake_rule`, `baseline_identity`, `rejected_register_summary`, and
  `last_reviewed` are untouched. Every evidence pointer path in the new records is
  asserted to exist.
- `notes` gained two entries: the append record, and the bounded-scope deviation
  declaration (intake ledger, capability-index, roadmap, release lock).

No second research registry was invented; the existing ledger and its existing
vocabulary were used.

### E6.2 Provenance

- `UPSTREAM_PROVENANCE.mode = P2P_NATIVE_KNOWLEDGE_DERIVATION` — deliberately not
  `LOCAL_VENDOR_SNAPSHOT`, so no vendor snapshot, entrypoint hash, or optional
  dependency surface is implied and `is_vendor_skill()` returns `false`.
- All seven commit + tree pins recorded in three places: the registry entry, the
  derived reference, and the adoption records (all three asserted).
- CC-BY-4.0 attribution, upstream repository identity, pinned revision, and the
  upstream `NOTICE`'s own incorporated-source credits preserved (asserted).
- `vendored = false`, `copied_files = []`, and the derived reference states it is
  "not a copy of any upstream file". The full `FORMULA.md` is **not** copied —
  a bounded derived reference is recorded as sufficient, and this is asserted by
  checking that `JACOB SEEDANCE FILM FORMULA` (the upstream document title) does not
  appear in any P2P artifact.
- No third-party prompt corpus vendored: asserted that no path under `.p2p/vendor`
  matches `awesome-seedance`, and that no `video`/`seedance` vendor snapshot
  directory exists.
- `pins_resolved_at = 2026-09-03`; `freshness = CURRENT`;
  `CERTIFIED = P2P-VIDEO-CAPABILITY-INTEGRATION-01`.
- Runtime-authoritative provider data is routed to the existing governed path only
  (`FACT_LEDGER -> Live Specs promotion`); `governance/live-specs.json` and
  `live-specs.lock.json` were **not** touched, so no undeclared live-spec promotion
  occurred.

### E6.3 Owner gates carried forward

`API credentials`, `paid video generation`, `infrastructure/runtime commitment`, and
`merge of this branch` are all declared `OWNER GATE` in the catalog `README.md`, the
protocol section 7/8, the registry `APPROVAL_BOUNDARY`, and adoption records
`RA-EXT-072` / `RA-EXT-076`. `OWNER_GATE_REQUIRED = YES`.

---

## E7 — Validation evidence

### E7.1 Focused validation module

```
python3 -m unittest tests.test_p2p_video_director_spec -v
Ran 16 tests in 0.490s
OK
```

16/16 green: registry boundedness, no-second-system proof, byte-identical
preservation of existing responsibilities, single-router selection, existing-route
non-disturbance, twelve fields, two camera beats, reference binding, consistency
taxonomy, knowledge-only chaining/post-production, single short projection, no
hard-coded provider constant, prompt-text-only execution, append-only ledger with
seven pins, CC-BY-4.0 attribution, base authority.

### E7.2 Regression proof — zero new failures

Same per-module command as `E1`, re-run after the change:

| Measure | Base main | After | Delta |
| --- | --- | --- | --- |
| Failing test modules | 31 | 31 | **0 new** |
| Failing module set (`comm` diff) | — | — | **identical** (no new, none fixed) |
| `test_p2p_capability_foundation` | failures=2 | failures=2 | 0 |
| `test_p2p_visual_vendor_integration` | failures=5, errors=3 | failures=5, errors=3 | 0 |
| `test_p2p_vendor_skill_integration` | failures=3, errors=1 | failures=3, errors=1 | 0 |
| `test_p2p_game_toolchain_02a` | failures=3, errors=1 | failures=3, errors=1 | 0 |
| `test_p2p_social_content_skills` | PASS | PASS | 0 |
| `test_p2p_beginner_routing`, `test_p2p_aesthetica_selective_routing`, `test_p2p_lightweight_fastpath`, `test_p2p_projection_bundle`, `test_p2p_c35_provider_neutral_runtime` | PASS | PASS | 0 |
| `validate_p2p_development_framework.py` | `52/58`, 6 failed | `52/58`, 6 failed | **identical six** (`V03`, `V05`, `V06`, `V09`, `V12`, `V20`) |
| Registry validity | valid | valid | canonical denominator `8`, `full_quorum` `8/8` |
| `V15-roadmap-count-sync` | PASS (176/176) | PASS (176/176) | untouched, because `capability-index.json` was intentionally not appended (declared deviation) |

The 31 pre-existing failing modules are unchanged and unrepaired by design: their
root causes (`VENDOR_SNAPSHOT_HASH_MISMATCH`, a stale `capability_count == 39`
assertion, missing `pytest`, and unrelated governance drift) are out of this goal's
bounded scope, and issue #71 directs that unrelated stale material not be repaired.

### E7.3 Boundary proofs (no execution, no install, no download)

| Boundary | Proof |
| --- | --- |
| `MODEL_WEIGHTS_DOWNLOADED` | `NO` — asserted in registry provenance; no path under `.p2p/vendor` added; no checkpoint/dataset/weight file anywhere in the diff |
| `VIDEO_RUNTIME_INSTALLED` | `NO` — `install_mode = DISABLED`, `dependency_mode = NONE`, no requirements/lockfile/submodule change |
| `PAID_VIDEO_GENERATION_USED` | `NO` — `paid_video_generation_used = false`; projection `submitted_to_any_provider = false` |
| `NEW_ROUTER_CREATED` | `NO` — asserted; `route["single_router"]` remains `true`; `p2p_uiux.router` untouched |
| `NEW_REGISTRY_CREATED` | `NO` — one entry appended to the existing `p2p-capability-registry/1` |
| `NEW_ORCHESTRATOR_CREATED` | `NO` — asserted |
| `NEW_DATABASE_CREATED` / `NEW_SERVER_CREATED` / `NEW_QUEUE_CREATED` | `NO` — asserted; no new executable module in the capability package |
| Network calls made by the change | none — the only network use was `gh api` metadata reads during pin resolution, performed by the agent, not by any committed code |

### E7.4 Runtime side-effect hygiene

Importing `p2p_capabilities` writes `.p2p/system/.p2p/state/adapter_registry.json`
(a pre-existing behaviour shared by every test module in the suite). Those tracked
state files were restored with `git checkout --` after each run, and the final
`git status` shows only the intended two modifications and three new paths. During
this goal one accidental deletion of those two tracked state files occurred while
cleaning the side-effect; both were immediately restored from `HEAD` and verified
byte-identical, and they are not part of the committed change.

---

## E8 — Over-engineering self-check

Every failure condition in the task brief, checked:

| Condition | Created? | Evidence |
| --- | --- | --- |
| Additional video capabilities beyond `video.prompt.director_spec` | NO | `test_02`: `video.*` set == `{video.prompt.director_spec}` |
| Another character-reference schema | NO | `test_03` + `test_08`: `p2p-visual-reference-pack/1` bytes unchanged, view ids reused verbatim, no `*.schema.json` in the new catalog |
| Another router | NO | `test_04`: `single_router` true, `p2p-capability-route/1` |
| Another registry | NO | one entry in the existing registry; `p2p-capability-registry/1` unchanged |
| Another orchestrator | NO | `test_02` |
| Provider API runtime | NO | `provider_api_implemented = false`; `PURE_DATA` |
| Video backend runtime | NO | `video_runtime_installed = false`; Wan2.2 / VACE / ReCamMaster / MoneyPrinterTurbo all `runtime_installed`/`installed`/`wrapped` false |
| Database / queue / daemon / server | NO | `test_02` |
| Generic workflow or video framework | NO | no Python module, no typed schema, no validator framework |
| Downloaded model weights | NO | `model_weights_downloaded = false`, `checkpoint_downloaded = false`, `dataset_downloaded = false` |
| Broad new test suite | NO | one module, 16 focused tests, one class, no duplicates |
| Separate executable capabilities for `character_bible` / `world_bible` / `style_bible` / `shot_spec` / `continuity` | NO | `separate_capabilities_created_for = []`; forbidden ids asserted absent |
| P2P VIDEO STUDIO | NO | `video_studio_created = false` |

Artifact mix: 3 knowledge/reference markdown files (686 lines) + 2 validation data
artifacts (667 lines) + 1 focused test module, versus **zero** new executable
production modules. Knowledge/reference artifacts were preferred over executable
code throughout, as directed.

`OVER_ENGINEERING_STATUS = PASS`

---

## E9 — Closure

- `VIDEO_RESEARCH_RECONCILED = YES` (research not repeated; all seven accepted
  classifications recorded unchanged; no contradictory evidence found in current
  canonical P2P, so none was reopened)
- `VIDEO_DIRECTOR_SPEC_STATUS = VERIFIED_MINIMAL`
- `CONSISTENCY_MODEL_STATUS = VERIFIED_TAXONOMY`
- `PROVIDER_PROJECTION_STATUS = VERIFIED_MINIMAL`
- `SHOT_CHAINING_STATUS = KNOWLEDGE_ONLY`
- `MONEYPRINTERTURBO_TREATMENT = POST_PRODUCTION_REFERENCE/FUTURE_BACKEND`
- `RESEARCH_LEDGER_STATUS = APPENDED_8_RECORDS_APPEND_ONLY`
- `PROVENANCE_STATUS = PINNED_AND_ATTRIBUTED`
- `SYNTHETIC_DIRECTOR_SPEC_VALIDATION = PASS`
- `PROVIDER_PROJECTION_VALIDATION = PASS`
- `VIDEO_STUDIO_READY_TO_BOOTSTRAP = YES` (foundation present; bootstrapping itself
  remains a separate Owner-gated goal)
- `IMPLEMENTATION_STATUS = COMPLETE_ON_CANDIDATE_BRANCH`
- `VALIDATION_STATUS = PASS_16_OF_16_NO_REGRESSION`
- Terminal target: `P2P_VIDEO_CAPABILITY_INTEGRATION_01 = READY_FOR_OWNER_MERGE_GATE`

Stopped here per `STOP_WHEN_EVIDENCE_SUFFICIENT`. No optional hardening, no follow-on
work, no merge, no deploy.

Recommended next action for the Owner merge gate: review the three knowledge
artifacts and the single validation instance, then decide on (a) merge, (b) whether
to repair the `game.mengto.camera_controls` bare-`camera` over-capture, (c) whether
to close the declared bounded-scope deviations (intake ledger `RI` id collision,
`capability-index`/roadmap records, release-lock regeneration, human-projection
staleness), and (d) whether to open a verified provider-profile goal through the
governed Live Specs path before any real video generation is attempted.
