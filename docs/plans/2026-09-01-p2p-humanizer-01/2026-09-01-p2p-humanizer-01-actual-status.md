# P2P-HUMANIZER-01 Actual Status

Title: P2P-HUMANIZER-01
Date: 2026-09-02
Status: R4 Complete — reconciled candidate pending one independent Supervisor
Companion plan: `docs/plans/2026-09-01-p2p-humanizer-01/2026-09-01-p2p-humanizer-01-plan.md`
Companion evidence: `docs/plans/2026-09-01-p2p-humanizer-01/2026-09-01-p2p-humanizer-01-evidence.md`
Companion benchmark: `docs/plans/2026-09-01-p2p-humanizer-01/2026-09-01-p2p-humanizer-01-benchmark.md`

## Purpose

This file records the current state after the bounded main-branch
reconciliation. R0-R3 remain historical checkpoints; R4 is the active status
for the candidate and does not replace the evidence ledger.

## Freshness / Refresh Rules

This file is living current-state evidence. R0 is the baseline before
implementation. After each implementation slice, affected rows and the
refresh log must be updated before the next slice starts.

## Scope

Target scope:

- exact upstream audit for `blader/humanizer`;
- one two-file local vendor snapshot;
- one `creative.prose.humanize` registry record;
- focused Issue #51 fixtures/tests and writer handoff evidence.

Out of scope:

- parent unpacked workspace Git metadata;
- existing `creative.copywriting` content and semantics;
- existing vendor loader/router/model/host projection production code;
- release ZIP/v5/immutable baseline/user projects;
- upstream execution/install, providers, UI, database, merge to `main`,
  deployment, promotion, and Owner approval execution.

## Relationship / Impact Evidence

| Unit / File / Surface | File Detail Evidence | Related File Count | Relationship Summary | Impact Note |
|-----------------------|----------------------|--------------------|----------------------|-------------|
| `.p2p/system/p2p_capabilities/capabilities.json` | `E0-P0A-GRAPH1` plus source inspection | N/A: hidden static path not projected by current Anvien file-detail | Registry source consumed by `load_registry` and existing routing/vendor projection | high scope warning; targeted single-record edit |
| `.p2p/system/p2p_capabilities/vendor_skill.py` | `E0-P0A-ADAPTER1`, Anvien hidden-path not-found result | N/A: hidden path not projected | Generic source owner for discovery/load/hash/readiness | high scope warning; preserve-only |
| `tests/test_p2p_vendor_skill_integration.py` | `E0-P0A-GRAPH1` | 39 local relationships; 41 symbols | Existing direct behavior tests for the reusable vendor loader | high scope warning; inspect-only |
| `.p2p/vendor/skill/xiaoma-durex-copywriter-main` | `E0-P0A-REG1` | N/A static vendor tree | Existing marketing-only capability snapshot | preserve-only; no semantic broadening |
| upstream detached `blader/humanizer` checkout | `E0-P0A-UP1` | N/A external inspect-only tree | Exact source/provenance/license input | inspect-only; never mutate |
| new Humanizer vendor root/manifest/tests | `E0-P0A-SCOPE1` | missing before implementation | Required Issue #51 surfaces | edit only in P1 slices |

## Status Rules

| Status | Meaning | Allowed next action |
|--------|---------|---------------------|
| `correct` | Already behaves as required. | Preserve. Add evidence or tests only if needed. |
| `partial` | Some required behavior exists, but gaps remain. | Change only the missing parts. Preserve correct parts. |
| `wrong` | Current behavior, source, or contract is incorrect. | Replace with required behavior. Record the exact reason. |
| `missing` | Required behavior, source, or contract does not exist. | Implement the missing piece only. |
| `unbound` | Surface exists but is not wired to the real source, flow, or contract. | Bind to the real source only. Preserve approved surface. |
| `fake-or-stub` | Prototype, demo, mock, fallback, or placeholder data is being used as real behavior. | Remove fake behavior or replace it with an approved truthful state. |
| `blocked` | Source, authority, contract, or required evidence is unclear. | Stop. Do not implement until resolved. |

## Current Status Matrix

| Unit | Current State | Required State | Status | Relationship Count | Evidence | Next Plan Decision |
|------|---------------|----------------|--------|--------------------|----------|--------------------|
| fresh P2P clone / `origin/main` | Fresh fetch verified canonical `main`; existing Writer branch now contains it through a non-rewriting merge. Exact current SHA/tree remain external review-time bindings. | clean authoritative base | correct | N/A | `E3-RECON1`, `E3-RECON2` | preserve; fetch again before review |
| existing `creative.copywriting` | Marketing/double-semantic snapshot; one unique record, with current canonical-main semantics preserved | remain marketing-only, no duplicate | correct | N/A | `E0-P0A-REG1`, `E3-RECON3` | preserve-only |
| Content Studio social capabilities | `creative.social.voice_profile`, `.post`, `.hook`, `.content_matrix`, and `.post_format` remain exact current-main records and projections | preserve Issue #60 semantics; Voice Profile is not Humanizer | correct | N/A | `E3-RECON3`, `E3-RECON4` | preserve-only |
| existing `vendor_skill.py` + single router | Generic metadata/JIT loader and one router already exist | reuse existing boundary | correct | N/A hidden path | `E0-P0A-ADAPTER1` | preserve-only in P1-A/B |
| upstream Humanizer subject | Detached exact commit/tree, not yet vendored | exact source audit record | correct | N/A | `E0-P0A-UP1` | inspect-only input to P1-A |
| Humanizer vendor snapshot | exact P2P root contains only `SKILL.md` + `LICENSE`, byte-identical to upstream | exactly `SKILL.md` + `LICENSE` | correct | N/A | `E1-P1A-SRC1`, `E1-P1A-HASH1` | preserve-only; P1-B may test it |
| Humanizer registry manifest | one valid `creative.prose.humanize` record, explicit/on-demand, 2.11.2 provenance | one noncanonical `SKILL` record, explicit/on-demand | correct | N/A hidden path | `E1-P1A-REG1`, `E1-P1A-ROUTE1` | preserve-only; P1-B may test it |
| focused Humanizer fixture/test surface | `tests/test_p2p_humanizer_integration.py` and four fixture pairs; direct module passes 9/9; Anvien reports 33 symbols/24 local relationships | A-G focused behavior/value tests | correct | 24 local relationships | `E1-P1B-TEST1..E1-P1B-TEST8`, `E1-P1B-GRAPH1` | preserve; run final detect |
| wider legacy suite | 104 tests: 97 pass, 7 baseline failures | no new Humanizer regressions; unrelated failures remain disclosed | partial | per test surfaces | `E0-P0A-BASE1` | do not broaden scope; rerun nearest checks |
| plan/evidence/benchmark/actual-status | newly created P0 standard set | living evidence updated per slice | correct | N/A | `E0-P0A-SCOPE1` | preserve and refresh |
| release/promotion/Owner gate | not executed | remain unexecuted | correct | N/A | `E0-P0A-SCOPE1`, `E3-RECON6` | stop at Owner Gate after one Supervisor PASS |

## Status Refresh Log

| Refresh | Date | Repo Basis | Changed Scope | Status Changes | Evidence | Next Phase Update |
|---------|------|------------|----------------|----------------|----------|-------------------|
| R0 | 2026-09-01 | fresh fetched `origin/main` before implementation | full Issue #51 target family | existing surfaces correct; Humanizer snapshot/manifest/tests missing; wider suite partial from baseline failures | `E0-P0A-GIT1`, `E0-P0A-UP1`, `E0-P0A-REG1`, `E0-P0A-ADAPTER1`, `E0-P0A-GRAPH1`, `E0-P0A-BASE1`, `E0-P0A-SCOPE1` | P1-A adds only exact two files + one record; P1-B adds fixtures/tests after production acceptance |
| R1 | 2026-09-01 | after P1-A exact snapshot/registry smoke | Humanizer vendor root and manifest | Humanizer snapshot `missing -> correct`; manifest `missing -> correct`; focused tests remain missing | `E1-P1A-SRC1`, `E1-P1A-REG1`, `E1-P1A-HASH1`, `E1-P1A-ROUTE1`, `E1-P1A-ROUTE2` | P1-B proceeds with fixtures/tests only; no production adapter/router edits |
| R2 | 2026-09-01 | after P1-B corrected focused module and graph refresh | Humanizer fixture/test surface | focused tests `missing -> correct`; exact production surfaces remain correct; graph detail now known | `E1-P1B-TEST1`, `E1-P1B-TEST2`, `E1-P1B-TEST3`, `E1-P1B-TEST4`, `E1-P1B-TEST5`, `E1-P1B-TEST6`, `E1-P1B-TEST7`, `E1-P1B-TEST8`, `E1-P1B-GRAPH1`, `E1-P1B-BUILD1`, `E1-P1B-GLOBAL1`, `E1-P1B-GLOBAL2`, `E1-P1B-RETRY1`, `E0-P0A-REBASE1` | final remote main is now bound; rerun nearest checks after rebase, then push only exact candidate |
| R3 | 2026-09-01 | after Writer push and PR creation | branch/PR handoff | one branch and one draft PR now exist; remote head/tree match local candidate; independent Supervisor remains pending | `E2-P2C-PR1` | stop Writer lane; independent Supervisor reviews exact PR subject; no merge/promotion |
| R4 | 2026-09-02 | fresh fetch of `origin/main` and PR #53, then non-rewriting merge into the existing branch | current-main reconciliation, direct Content Studio conflict, and stale evidence cleanup | current main is present; five social records are preserved; one direct social-test assertion now permits the separately registered Humanizer; focused/adjacent suite passes 73/73; one Supervisor remains pending | `E3-RECON1`–`E3-RECON7` | push the stable branch once, run exactly one independent Supervisor, then stop at Owner Gate on PASS |

## Phase Touch Map

| Unit / File / Surface | Plan-Relevant Relationship File | Relationship to Target | Plan Item | Touch Mode | Evidence | Constraint |
|-----------------------|---------------------------------|------------------------|-----------|------------|----------|------------|
| `capabilities.json` | `p2p_capabilities.model.load_registry` | source-of-truth / consumer | P1-A | edit | `E0-P0A-REG1` | one unique ID; preserve canonical 8/8 |
| `capabilities.json` | `p2p_capabilities.routing.classify_capabilities` | routing consumer | P1-A | validate-only | `E0-P0A-ADAPTER1` | explicit/on-demand; no global default |
| `capabilities.json` | `p2p_capabilities.vendor_skill` | vendor metadata/load consumer | P1-A | validate-only | `E0-P0A-ADAPTER1` | no code branch or dependency install |
| existing creative vendor root | `creative.copywriting` manifest | sibling capability | P1-A | preserve-only | `E0-P0A-REG1` | do not merge marketing and humanization semantics |
| Humanizer vendor root | upstream detached checkout | exact source input | P1-A | edit | `E0-P0A-UP1` | exactly `SKILL.md` and `LICENSE` |
| focused test module/fixtures | existing vendor loader/router | behavior test | P1-B | edit | `E0-P0A-SCOPE1` | no production rewrite engine; temp writes under `.tmp` |
| release artifacts / user projects | package/release/user paths | preserve-only target | P1-A/P1-B | do-not-touch | `E0-P0A-SCOPE1` | no release rebuild, install, merge, or promotion |

## Detailed Findings

### Existing creative.copywriting

Current state:

The current registry contains exactly one `creative.copywriting` record. It is
described and triggered for advertising/marketing copy, explicitly excludes
technical documentation, summaries, translation, legal, and unrelated writing,
and points to its own local snapshot. It is not a general prose-humanization
contract.

Required state:

```text
creative.copywriting remains singular, marketing-only, and unchanged.
Humanizer receives a distinct semantic ID because its domain is editing prose,
voice calibration, and protected Markdown file mode rather than ad copy.
```

Evidence:

- `E0-P0A-REG1`: current manifest inventory and existing record.
- `E0-P0A-SCOPE1`: reconciliation decision and forbidden duplicate paths.

Relationship and impact:

- Related file count: N/A for hidden JSON; existing vendor test suite covers the reusable adapter.
- Relationship summary: sibling registry record and vendor snapshot; no shared content source.
- Impact note: high scope warning; preserve-only.

Classification:

`correct`

Allowed next action:

Preserve the record and add a distinct humanization capability only if the
focused routing tests demonstrate non-overlap.

Forbidden next action:

Do not rename, broaden, duplicate, or route Humanizer through marketing-copy
triggers.

### Existing vendor boundary

Current state:

`p2p_capabilities.vendor_skill` already performs safe repository-relative
vendor discovery, exact snapshot/entrypoint hash checks, metadata-only
discovery, selected entrypoint loading, explicit declared context loading, and
no permission/network grant. It does not install or execute optional
dependencies for a no-dependency Markdown skill.

Required state:

```text
Reuse this generic adapter. No new production module or runtime subsystem.
```

Evidence:

- `E0-P0A-ADAPTER1`: source inspection and existing vendor tests.
- `E0-P0A-GRAPH1`: existing direct test relationship inventory.

Relationship and impact:

- Related file count: hidden production path not projected by current Anvien.
- Relationship summary: loader/router consumer family.
- Impact note: high scope warning; preserve-only and validate through public functions.

Classification:

`correct`

Allowed next action:

Add a manifest record that satisfies the existing generic loader.

Forbidden next action:

Do not add a humanizer-specific branch, prompt engine, provider, subprocess,
or global activation path.

### Humanizer candidate surfaces

Current state:

The exact upstream source is audited but no P2P snapshot, manifest record, or
focused tests exist in the fresh main checkout.

Required state:

```text
One exact two-file snapshot and one explicit/on-demand registry record are
loaded through the existing route/loader. Focused fixtures prove value and
protected-content preservation without claiming live model certification.
```

Evidence:

- `E0-P0A-UP1`: exact upstream commit/tree/version/license/hash.
- `E0-P0A-SCOPE1`: missing-to-editable classification and verify matrix.

Relationship and impact:

- Related file count: N/A before creation.
- Relationship summary: new data snapshot + existing registry/loader consumers.
- Impact note: targeted new surface; preserve all existing siblings.

Classification:

`missing`

Allowed next action:

Implement P1-A, then P1-B only after exact source and manifest validation pass.

Forbidden next action:

Do not vendor unrelated upstream content or implement a rewrite engine.

### Current-main reconciliation

The current canonical main contains the five Issue #60 Content Studio
capabilities. Their registry objects and vendored projections are preserved
unchanged in the candidate. The social test's old assertion that Humanizer was
absent was a direct conflict with the requested downstream relationship; it
was narrowed to the five-social-capability inventory while the existing
Voice Profile/Humanizer separation checks remain intact. No production router,
registry engine, pipeline, or authorization surface was added.

## Next Phase Status Decisions

| Plan Item | Actual Status Finding | Required Status / Next-Action Update |
|-----------|-----------------------|--------------------------------------|
| P1-A | Humanizer source is exact and audited; P2P snapshot/manifest now pass exact smoke | preserve the two files and one record; keep loader/router/copywriting preserve-only |
| P1-B | Focused module now has 9/9 passing cases; P1-A production surfaces are correct; wider baseline remains partial with seven unrelated failures | preserve focused surface; run final compile/build-equivalent and detect-changes; do not use the stale wider failures as Humanizer proof |
| P2-A | Reconciled PR #53 is stable and the focused/adjacent suite passes; no independent review has run in this lane | run exactly one independent Supervisor; PASS stops at Owner Gate, REJECT stops at a genuine blocker |
| P2-B | Stale candidate head/tree claims were removed from committed notes/evidence/report; generated Anvien line-ending churn was excluded | complete; do not create an evidence-binding commit loop |
| P2-C | Final Writer checks are recorded after the reconciliation merge and cleanup commit | keep Owner approval, merge to `main`, release, and promotion unexecuted |

## Implementation Gate

- [x] Target scope is listed in Current Status Matrix.
- [x] Each target unit has a status.
- [x] Each status has evidence IDs.
- [x] Each target file has relationship count evidence from `file-detail` when applicable, or the Anvien hidden-path limitation is recorded.
- [x] Phase Touch Map lists plan-relevant relationship files that can affect the current phase/slice.
- [x] Phase Touch Map defines touch mode for every plan-relevant relationship unit that may be affected.
- [x] Correct parts are marked preserve-only.
- [x] Partial, missing, wrong, unbound, and fake-or-stub parts have exact next actions.
- [x] Blockers are recorded, if any.
- [x] Next phase status assumptions, next action, and work steps have been updated from this status file when needed.
- [x] Status Refresh Log has an R0 baseline row.
- [x] If implementation has started, affected Current Status Matrix rows have been refreshed from latest evidence.
- [x] If refreshed statuses changed next work, only the stale next-phase status assumptions, next action, or work steps have been updated before the next phase.

## Final P0 Decision

Choose one:

- [ ] P0 actual-status incomplete. Implementation is blocked.
- [ ] P0 complete. Next phase can proceed unchanged.
- [x] P0 complete. Next phase status, next action, or work steps must be updated before implementation.
- [ ] P0 complete. Target scope is preserve-only.
- [ ] P0 complete. Implementation is blocked by missing authority or evidence.

Decision note:

P0 is complete. Current authority supports a distinct `creative.prose.humanize`
record because `creative.copywriting` is marketing-only. The next phase is
narrowed to exact two-file vendoring plus one manifest entry, followed by
focused route/load/value tests. No production adapter or router edit is
authorized by the evidence.
