# P2P Video Capability Integration 01 — Plan

## Metadata

- Date: `2026-09-03`
- Task ID: `P2P-VIDEO-CAPABILITY-INTEGRATION-01`
- Execution mode: `BOUNDED_CAPABILITY_INTEGRATION`
- GitHub issue: `#71` (`7roger89-web/P2P-upgrade-github-1`)
- Base main SHA: `c1ddc4fdbc3bf6639a5f3e3f171a7fb5c1df6352`
- Branch: `arena/01a0664a-p2p-upgrade-github-1` (Arena session-fixed; the suggested
  name `arena/p2p-video-director-foundation` could not be used because this Arena
  session is bound to one branch)
- Status: `complete / READY_FOR_OWNER_MERGE_GATE`
- Plan: `docs/plans/2026-09-03-p2p-video-capability-integration-01/2026-09-03-p2p-video-capability-integration-01-plan.md`
- Evidence: `docs/plans/2026-09-03-p2p-video-capability-integration-01/2026-09-03-p2p-video-capability-integration-01-evidence.md`
- Benchmark: `N/A` — declared, not silently omitted. This goal performs exactly one
  representative synthetic validation and no measurement campaign. Issue #71
  forbids a benchmark suite, so a benchmark file would be an empty artifact.
- Actual status: `N/A` — declared, not silently omitted. This goal is a single
  implementation slice, not a multi-phase plan, so there is no later phase whose
  assumptions could drift. The pre-change repository state was captured directly in
  the evidence file (`E1`) instead.

## Goal

Integrate the minimum useful AI-video foundation into current P2P before any
standalone P2P VIDEO STUDIO is bootstrapped: exactly one bounded capability,
`video.prompt.director_spec`, expressed in the representation the existing registry
already supports, plus durable research provenance for the seven audited
repositories, plus one representative synthetic validation proving
`USER IDEA -> MASTER DIRECTOR SPEC -> SHORT PROVIDER PROMPT`.

## Authority and closed inputs

`P2P-VIDEO-RESEARCH-01` is complete. The six-repository research is **not** repeated
here. Issue #71 and the research return packet already fix the accepted
classifications; this goal implements and validates them and does not reopen them.
No broad P2P audit was conducted. The surfaces inspected were limited to:
`AGENTS.md`, issue #71, the capability registry and its model contract, the router
conventions, `governance/research-adoption-ledger.json`, the current
`UPSTREAM_PROVENANCE` pattern, `p2p-visual-reference-pack/1`,
`visual.gpt_image_2_style_library`, `media.whiteboard_animation`, and the governed
Live Specs boundary.

## Rules

- Minimum relevant context; minimum sufficient work; anti-over-engineering.
- Verify in proportion to demonstrated risk, not to available effort.
- Stop when the synthetic transformation and focused validation are sufficient.
- Prefer knowledge/reference artifacts over executable code.
- Do not repair unrelated stale documentation or projections unless required for
  this goal to validate.
- One Arena session, one bounded goal, one branch, one pull request. Do not merge.
  Do not deploy. Do not create P2P VIDEO STUDIO.
- No new router, registry, orchestrator, database, server, daemon, queue, or
  generic video/workflow framework.
- No provider API, no video backend runtime, no model weights, no paid generation.
- Do not vendor the `awesome-seedance-prompts` third-party prompt corpus.
- Do not fold responsibility into `visual.gpt_image_2_style_library` or
  `media.whiteboard_animation`.
- Do not create a second character-reference schema; reuse
  `p2p-visual-reference-pack/1`.
- Any source or test temporary output stays below the repository-local `.tmp/`
  path. (This goal produced none; the one-shot mutation scripts were kept outside
  the repository and are not committed.)
- Hidden fallback is forbidden: unverified provider data stays visibly
  `UNKNOWN_UNTIL_VERIFIED_PROFILE`, and absent reference stills stay visibly
  declared rather than being silently substituted.

## Problem

Current canonical P2P has strong image-prompt knowledge
(`visual.gpt_image_2_style_library`), whiteboard/storyboard production
(`media.whiteboard_animation`), and a character multi-view reference vocabulary
(`p2p-visual-reference-pack/1`), but no owner for **AI-video direction**. A user
idea for a moving shot has nowhere to go: nothing turns it into a reusable,
provider-neutral direction spec, and nothing reduces that spec to the short flat
prompt a real video provider actually accepts. The risk of filling that gap
naively is a second router, a video framework, an installed backend, or an
overloaded single camera command that silently drops half of what the user asked
for.

## Design decisions

| # | Decision | Why |
| --- | --- | --- |
| D1 | Exactly one new registry entry: `video.prompt.director_spec` | Issue #71 accepts exactly one bounded capability |
| D2 | `TYPE=KNOWLEDGE_SOURCE`, `SEMANTIC_KIND=SKILL`, `INVOCATION_CLASS=MODEL_ROUTABLE`, `TRUST_LEVEL=PURE_DATA`, `STATUS=ACTIVE` | `KNOWLEDGE_SOURCE + MODEL_ROUTABLE SKILL` is expressible with the registry's existing orthogonal `SEMANTIC_KIND` vocabulary, which exists precisely so no new registry class or second registry is needed. `PURE_DATA` keeps it out of the vendor-skill/host-code surface |
| D3 | No typed schema, no validator framework, no Python module | The existing capability format does not mechanically require any of them for a `PURE_DATA` knowledge source; issue #71 asks for a lightweight 12-field checklist/template |
| D4 | Knowledge lives in `docs/p2p-development/capability-catalog/video-director-spec/` | Follows the existing `ui.design` / `game.three.*` / `game-asset-forge` knowledge-catalog convention exactly |
| D5 | `UPSTREAM_PROVENANCE.mode = P2P_NATIVE_KNOWLEDGE_DERIVATION` | Deliberately not `LOCAL_VENDOR_SNAPSHOT`, so `is_vendor_skill()` returns false and no vendor snapshot, entrypoint hash, or optional dependency surface is implied |
| D6 | Reference binding reuses `p2p-visual-reference-pack/1` view ids verbatim | No second character-reference schema |
| D7 | Canonical symbolic prop gets its own `SYMBOLIC_PROP_REFERENCE` slot | Prop state is a plot event; folding it into the character slot hides drift |
| D8 | Ten-concept consistency taxonomy recorded as knowledge, with the three-way inequality asserted | `IMAGE_CONSISTENCY != VIDEO_TEMPORAL_CONSISTENCY != SHOT_TO_SHOT_CONTINUITY`; no consistency engine |
| D9 | `ONE PRINCIPAL CAMERA MOVE PER BEAT` recorded as a director rule, explicitly not a universal hard validator | Issue #71 forbids a universal validator; a deviation with a recorded reason stays legal |
| D10 | Every provider profile field is `UNKNOWN_UNTIL_VERIFIED_PROFILE`; no numeric prompt-length, duration, or aspect constant anywhere | No verified current profile data exists, and the governed Live Specs path is the only route to runtime-authoritative provider data |
| D11 | Projection flattens to natural-language prose | `accepts_labelled_structured_prompt` is UNKNOWN, so structured input must not be assumed |
| D12 | Shot chaining and MoneyPrinterTurbo post-production recorded as knowledge only | No execution, no install, no vendor, no wrap |
| D13 | Eight append-only adoption records `RA-EXT-070` … `RA-EXT-077` | Seven repositories plus the non-repository skydive reference; `REPOS_REVIEWED` stays 7 |
| D14 | Ledger statuses are `SELECTED` / `RESEARCHED` / `DEFERRED`, never `IMPLEMENTED` / `VERIFIED` / `SHIPPED` | The ledger forbids inferring IMPLEMENTED from a report; the capability exists on a candidate branch only and promotion needs the Owner merge gate |
| D15 | One focused validation module, `tests/test_p2p_video_director_spec.py` | Repo convention is one test module per capability goal; issue #71 forbids a broad new suite |

## Declared bounded-scope deviations

Recorded rather than left silent; full reasoning is in the evidence file and in the
ledger `notes` array.

1. **No `governance/research-intake-ledger.json` append.** Its provenance note
   `PN-001` already references an `RI-008` that is absent from `intake_records`.
   Assigning `RI-008` would create a duplicate-truth conflict with `PN-001`;
   assigning `RI-009` would silently imply `RI-008` exists. Repairing that is out
   of this goal's bounded scope.
2. **No `capability-index.json` / `current-roadmap.md` /
   `p2p-development-roadmap.json` append.** The most recent capability-addition
   precedent (`creative.social.*`, 2026-09-02) added registry, vendor, provenance,
   plan/evidence, and focused-test artifacts with no capability-index or
   development-roadmap record; `capability-index.json` is a declared derived
   projection whose own validator already reports six pre-existing failures on
   main, so regenerating it plus the roadmap record count would be unrelated
   stale-projection repair.
3. **No `governance/runtime-manifest.lock.json` regeneration.** The lock already
   drifts on three governance files at base main
   (`development-control.json`, `project-adoption-lifecycle.md`,
   `research-adoption-ledger.json`). Regenerating it is a release-gated,
   approval-bound step, not a bounded-goal step.
4. **No repair of `docs/RESEARCH-ADOPTION-LEDGER.md` staleness** beyond a bounded
   addendum for the eight new rows. The projection already claims 26 canonical
   entries while the JSON holds 69 at base main; a full regeneration is unrelated
   repair.
5. **Pre-existing vendor snapshot hash drift not repaired.**
   `test_p2p_visual_vendor_integration`, `test_p2p_vendor_skill_integration`,
   `test_p2p_host_skill_projection`, and `test_p2p_manus_skill_package` already fail
   at base main on `VENDOR_SNAPSHOT_HASH_MISMATCH`. Out of scope; the goal proves
   instead that it adds no new failure.
6. **Pre-existing routing over-capture not repaired.** `game.mengto.camera_controls`
   carries a bare `camera` trigger, so it is selected as `SECONDARY` on any request
   containing the word `camera`, including the validation request. Editing an
   existing capability entry is outside this goal's bounded scope; the collision is
   recorded in the evidence file instead.

## Work slices

- **S0 — Preflight and fresh authority check.** Confirm the workspace, fresh-fetch
  `origin`, resolve `origin/main`, confirm it has not moved past the known base SHA,
  read issue #71, inspect only the minimum relevant surfaces.
- **S1 — Baseline capture.** Record the pre-change failing test modules, the
  pre-change framework-validator failures, and the canonical hashes of the artifacts
  this goal must not disturb.
- **S2 — Knowledge artifacts.** Author the bounded catalog: `README.md`,
  `director-spec-protocol.md`, `research-derived-reference.md`.
- **S3 — Registry entry.** Append exactly one capability to `capabilities.json`
  without rewriting any existing entry.
- **S4 — Research ledger.** Append `RA-EXT-070` … `RA-EXT-077` append-only, plus two
  ledger notes recording the append and the bounded-scope deviations.
- **S5 — Focused synthetic validation.** Author the master spec and the single
  provider projection for the issue #71 request, then the one validation module.
- **S6 — Regression proof.** Re-run the whole suite per module and the framework
  validator; prove the failing sets are identical to baseline and the new module is
  green.
- **S7 — Human projection addendum, plan/evidence, commit, one pull request. Do not
  merge.**

## Acceptance criteria

1. Registry valid, canonical denominator still `8`, `full_quorum` still `8/8`,
   capability count exactly `72 -> 73`.
2. `video.prompt.director_spec` is the only `video.*` capability and is
   `KNOWLEDGE_SOURCE` / `MODEL_ROUTABLE` / `PURE_DATA` / `ACTIVE`, not a vendor skill.
3. `visual.gpt_image_2_style_library`, `media.whiteboard_animation`,
   `creative.copywriting`, and `p2p-visual-reference-pack/1` are byte-identical to
   base main.
4. The existing router selects the new capability on a video-direction request and
   never displaces an existing selection; the bare idea sentence does not
   over-capture.
5. The master spec demonstrates all twelve fields; the two-move camera request
   yields at least two camera beats with exactly one principal move each.
6. Every reference slot declares both `ADOPT` and `EXCLUDE`; the character slot
   reuses the six `p2p-visual-reference-pack/1` view ids; the sword has its own slot.
7. All ten consistency concepts are recorded and the three-way inequality is
   asserted in both the protocol and the validation instance.
8. Exactly one provider projection exists, is flat prose, is materially shorter
   than the master spec, records its budget source and its dropped/compressed
   fields, and hard-codes no provider length, duration, or aspect constant.
9. Shot chaining and MoneyPrinterTurbo are knowledge only: no execution, no
   install, no vendor, no wrap, no weights, no paid generation.
10. `RA-EXT-070` … `RA-EXT-077` exist, the 69 historical records and the ledger
    top level are unchanged, all seven repositories carry commit and tree pins, and
    the CC-BY-4.0 attribution, upstream identity, and upstream `NOTICE` credits are
    preserved.
11. No new router, registry, orchestrator, database, server, daemon, queue, schema
    file, or executable module in the capability package.
12. Zero new failing test modules and zero new framework-validator failures versus
    baseline; the new validation module is green.
13. One branch, one pull request, not merged.

## Explicit non-goals

No P2P VIDEO STUDIO. No video generator, renderer, or backend. No provider API. No
model weights. No paid generation. No second router, registry, orchestrator,
database, server, daemon, queue, or generic framework. No separate executable
capabilities for `character_bible`, `world_bible`, `style_bible`, `shot_spec`, or
`continuity`. No vendored third-party prompt corpus. No full `FORMULA.md` copy. No
broad new test suite. No merge, no deploy.
