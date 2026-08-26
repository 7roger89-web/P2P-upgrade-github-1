# P2P-GOVREC02 Governance Source Anchor Contract Correction Actual Status

Title: P2P-GOVREC02 Governance Source Anchor Contract Correction
Date: 2026-08-26
Status: P2-B Complete / P3 Ready
Companion plan: `docs/plans/2026-08-26-p2p-govrec02-source-anchor-contract/2026-08-26-p2p-govrec02-source-anchor-contract-plan.md`
Companion evidence: `docs/plans/2026-08-26-p2p-govrec02-source-anchor-contract/2026-08-26-p2p-govrec02-source-anchor-contract-evidence.md`
Companion benchmark: `docs/plans/2026-08-26-p2p-govrec02-source-anchor-contract/2026-08-26-p2p-govrec02-source-anchor-contract-benchmark.md`

## Purpose

This file records the real current state after the P1-B dynamic validator and P2-A focused behavior-test slices. The Owner resolved the prior semantics ambiguity by selecting promoted implementation source anchor semantics.

## Freshness / Refresh Rules

P0 is the baseline before implementation. This file must be refreshed after every GOVREC02 slice and before the next phase when its status assumptions change.

## Scope

Target scope:

- Active governance authority projection and its existing development-control validator.
- Dynamic Git identity/ancestry observation at the valid linked-worktree boundary.
- Direct GOVREC01/GOVREC02 tests and exact final evidence.

Out of scope:

- Root invalid `.git` administrative metadata and all unrelated dirty owner paths.
- Official `.19` artifact, historical approval/report bytes, `.74` release/promotion state, provider/Manus/Council/SFI01/Manus R2/vendor/project surfaces, and all remote writes.

## Relationship / Impact Evidence

| Unit / File / Surface | File Detail Evidence | Related File Count | Relationship Summary | Impact Note |
|-----------------------|----------------------|--------------------|----------------------|-------------|
| `governance/development-control.json` | `E0-P0A-GRAPH5` | 2 inbound | active authority projection consumed by governance/report surfaces | low graph scope; high governance consequence |
| `scripts/p2p_development_control.py` | refreshed Anvien graph at `9e8bced...` | 1 inbound / 132 local / 18 flows | validator, status, lineage mutation helpers, and CLI | high file risk; `_validate_source_anchor` CRITICAL impact |
| `tests/test_p2p_govrec01_reconciliation.py` | `E0-P0A-GRAPH4` | 7 outbound / 16 local | direct authority, drift, lock, and doctor regression tests | high test-surface risk |
| historical approval/receipt/report files | direct source inspection | preserve-only | external subject/report/source identity evidence | do not rewrite provenance |

## Status Rules

| Status | Meaning | Allowed next action |
|--------|---------|---------------------|
| `correct` | Already behaves as required. | Preserve. |
| `partial` | Some required behavior exists, but gaps remain. | Change only missing parts. |
| `wrong` | Current contract conflicts with the Owner-selected semantics. | Replace narrowly. |
| `missing` | Required behavior does not exist. | Implement only the missing piece. |
| `unbound` | Surface exists but is not wired to the real source/contract. | Bind to the real source. |
| `fake-or-stub` | Placeholder or indirect evidence is treated as real. | Remove false claim. |
| `blocked` | Authority/evidence is unclear. | Stop. |

## Current Status Matrix

| Unit | Current State | Required State | Status | Relationship Count | Evidence | Next Plan Decision |
|------|---------------|----------------|--------|--------------------|----------|--------------------|
| Active authority field | `promoted_source_anchor` now records explicit Git anchor semantics; dynamic observations are intentionally not persisted | one explicit anchor object with no active legacy duplicate | correct | 2 inbound | `E0-P0A-AUTH1..E0-P0A-AUTH2`, `E1-P1A-CONTRACT1` | preserve in P1-B |
| Static authority validator | validates canonical source refs/trust boundary and explicit anchor semantics; dynamic Git observation is not yet wired | static anchor shape, type, policy, artifact, and self-reference validation | correct | 1 inbound / 17 flows | `E0-P0A-SRC1`, `E0-P0A-GRAPH2`, `E1-P1A-CONTRACT2` | preserve; continue P1-B |
| Dynamic Git boundary | resolves anchor commit/tree and observes HEAD/origin-main at real checkout boundary | explicit equal/descendant/diverged evaluation against anchor; Git-less package boundary remains static | bound-correct | 9 affected processes | `E1-P1B-GIT1..E1-P1B-GIT2`, refreshed Anvien impact | preserve in P2/P3 |
| GOVREC02 focused tests | 11 tests cover active contract, topology simulation, and fail-closed reason codes | positive and fail-closed anchor behavior tests | correct | new focused suite | `E2-P2A-TEST1..E2-P2A-TEST2` | preserve |
| GOVREC01 focused tests | legacy snapshot regression remains green after contract correction | no regression to GOVREC01 reconciliation facts | correct | 9 tests | closure evidence | preserve |
| Source-anchor / external-receipt boundary | committed anchor is reconciliation input; approval subject/report hashes and existing source-binding remain separate external identity surfaces | no second authority/receipt system and no self-referential candidate identity | correct | 2 existing machinery paths | `E2-P2B-DOC1..E2-P2B-DOC2` | preserve in P3 |
| Historical `.19` artifact and receipts | exact historical authority preserved | unchanged historical evidence | correct | preserve-only | `E0-P0A-AUTH3` | preserve-only |
| Current Council status | historical/current boundary already explicit | remain `FALSE / NOT_PROVEN` | correct | preserve-only | `E0-P0A-SCOPE1` | preserve-only |
| Root `.git` and unrelated owner dirty state | root admin metadata invalid; 1,127 target-worktree dirty entries are unrelated owner/line-ending state | untouched | preserve-only | out of scope | `E0-P0A-CHK1` | do not touch |

## Status Refresh Log

| Refresh | Date | Repo Basis | Changed Scope | Status Changes | Evidence | Next Phase Update |
|---------|------|------------|----------------|----------------|----------|-------------------|
| R0 | 2026-08-26 | valid linked worktree at `ad5ea25...`, GOVREC01 anchor ambiguity resolved by Owner | full GOVREC02 scope | initial classification: wrong/partial/missing/correct/preserve-only | `E0-P0A-CHK1..E0-P0A-SCOPE1` | P0 complete; proceed P1-A |
| R1 | 2026-08-26 | after P1-A static anchor contract implementation | authority JSON and static validator | active field `wrong -> correct`; static validator `partial -> correct`; dynamic Git boundary remains `missing` | `E1-P1A-CONTRACT1..E1-P1A-CONTRACT2` | proceed P1-B; dynamic checks must remain separate |
| R2 | 2026-08-26 | after P1-B dynamic validator implementation | real linked worktree CLI and Git-less package boundary | dynamic boundary `missing -> bound-correct`; current checkout `HEAD_DESCENDS_FROM_ANCHOR`, origin/main `ORIGIN_MAIN_EQUALS_ANCHOR`; anchor commit/tree verified | `E1-P1B-GIT1..E1-P1B-GIT2` | proceed P2-A; no remote mutation |
| R3 | 2026-08-26 | after P2-A focused behavior tests | GOVREC02/GOVREC01/development-control tests | focused behavior status `partial -> correct`; 11/11 GOVREC02, 9/9 GOVREC01, 21 development-control with 2 expected skips | `E2-P2A-TEST1..E2-P2A-TEST2` | proceed P2-B receipt/documentation boundary |
| R4 | 2026-08-26 | after P2-B source/receipt boundary inspection | active search, approval schema/receipt, package source binding | receipt boundary `unbound -> correct`; anchor remains committed reconciliation input, external subject/source identity remains existing machinery, no duplicate system | `E2-P2B-DOC1..E2-P2B-DOC2` | proceed P3 final gates |

## Phase Touch Map

| Unit / File / Surface | Plan-Relevant Relationship File | Relationship to Target | Plan Item | Touch Mode | Evidence | Constraint |
|-----------------------|---------------------------------|------------------------|-----------|------------|----------|------------|
| `governance/development-control.json` | `scripts/p2p_development_control.py` | source-of-truth / validator consumer | P1-A | edit | `E0-P0A-GRAPH2`, `E0-P0A-GRAPH5` | one active authority object; preserve historical refs |
| `scripts/p2p_development_control.py` | `tests/test_p2p_development_control.py`, `scripts/package_release.py` | validator / package consumer | P1-A/P1-B | edit | `E0-P0A-GRAPH2..E0-P0A-GRAPH3` | retain Git-less static package validation |
| `tests/test_p2p_govrec01_reconciliation.py` | `scripts/p2p_development_control.py`, `scripts/p2p_governance.py` | behavior test | P2-A | preserve/edit regression | `E0-P0A-GRAPH4`, closure evidence | test behavior, not only spelling |
| `tests/test_p2p_govrec02_source_anchor.py` | `scripts/p2p_development_control.py` | focused contract/lineage behavior test | P2-A | edit | `E2-P2A-TEST1..E2-P2A-TEST2` | use existing Git objects/injected observations; no ref mutation |
| historical approvals/reports | none | historical evidence | all | preserve-only | `E0-P0A-AUTH3` | no retroactive rewrite |
| runtime lock/drift policy | `scripts/p2p_governance.py` | generated integrity gate | P3-C | regenerate/validate only | `E0-P0A-SRC1` | use existing generator; no exclusions |
| root `.git`, owner dirty paths, external projects | none | unrelated owner/admin state | all | do-not-touch | `E0-P0A-CHK1` | no cleanup or repair |

## Detailed Findings

### Active source authority projection

Current state:

The active field is named `promoted_source_anchor`, points to the observed certification ref `origin/main`, and records commit/tree `2a71410...` / `3e6ab12...`. Dynamic validation now treats that pair as the implementation authority anchor while separately observing current HEAD and origin/main; a descendant candidate is valid and divergence fails closed.

Required state:

```text
authority.promoted_source_anchor = exact promoted implementation source used for reconciliation
observed_head = dynamic Git HEAD
observed_origin_main = dynamic refs/remotes/origin/main
lineage_policy = CURRENT_OR_CANDIDATE_HEAD_MUST_EQUAL_OR_DESCEND_FROM_ANCHOR
```

Evidence:

- `E0-P0A-AUTH1`: current field is semantically ambiguous.
- `E0-P0A-AUTH2`: Owner explicitly selected anchor semantics.
- `E0-P0A-SRC1`: existing validator is not wired to the field.

Relationship and impact:

- Related file count: 2 inbound in Anvien projection.
- Relationship summary: JSON is source-of-truth for a validator/report boundary.
- Impact note: low graph count but material governance consequence.

Classification:

`wrong` under the newly selected contract; the snapshot values themselves remain correct anchor values.

Allowed next action:

Implement the explicit anchor object and narrow validator extension in P1.

Forbidden next action:

Do not preserve two active fields, equate anchor to latest HEAD, or encode the candidate's own SHA.

## Next Phase Status Decisions

| Plan Item | Actual Status Finding | Required Status / Next-Action Update |
|-----------|-----------------------|--------------------------------------|
| P1-A | active authority key was wrong/ambiguous; static validation was partial | complete: explicit anchor object and static contract |
| P1-B | dynamic Git relationship was missing | complete: bind real Git checkout observations; no latest-head equality requirement |
| P2-A | tests lacked positive/negative lineage behavior | complete: add behavior matrix after production behavior |
| P2-B | receipt boundary exists historically but was not documented for this contract | complete: document without creating a second receipt system |
| P3 | current baseline gates were green in GOVREC01 but exact final GOVREC02 review is not run | rerun all required gates and fresh Supervisor on final HEAD |

## Implementation Gate

- [x] Target scope is listed in Current Status Matrix.
- [x] Each target unit has a status.
- [x] Each status has evidence IDs.
- [x] Each target file has relationship count evidence where applicable.
- [x] Phase Touch Map lists plan-relevant relationship files.
- [x] Phase Touch Map defines touch mode for every affected unit.
- [x] Correct parts are marked preserve-only.
- [x] Partial, missing, and wrong parts have exact next actions.
- [x] Unrelated blockers are recorded and excluded.
- [x] Next phase status assumptions and work steps are updated.
- [x] Status Refresh Log has an R0 baseline row.
- [x] Affected rows refreshed after implementation slices.
- [x] Later phase assumptions refreshed after implementation slices.

## Final P0 Decision

- [ ] P0 actual-status incomplete. Implementation is blocked.
- [x] P0 complete. Next phase status, next action, and work steps must be updated before implementation.
- [ ] P0 complete. Target scope is preserve-only.
- [ ] P0 complete. Implementation is blocked by missing authority or evidence.

Decision note:

The Owner has resolved the GOVREC01 ambiguity in favor of anchor semantics. The valid linked worktree, current source objects, Anvien graph, and affected-surface map are known. P1 may implement the smallest explicit anchor contract; all protected promotion/release/external actions remain forbidden.

P1-A refresh note:

The active projection and static contract are explicit and tested; checkpoint `9e8bced18387bf786fbd6ed306acce83ad911e9d` records that slice.

P1-B/P2-A refresh note:

The real linked-worktree validator now proves anchor commit/tree identity and separate HEAD/origin-main lineage. Focused simulations prove BEFORE equality, descendant candidate/post-promotion validity, and divergent-head rejection without changing refs. P2-B must now record the external receipt boundary and active-consumer search before final gates.

P2-B refresh note:

Existing approval/source-binding machinery remains the external identity boundary: the committed anchor is not an approval receipt, and no candidate's own future SHA is inserted into its governance file. Active positive consumer search is clean; remaining legacy literals are explicit rejection tests/guards or historical provenance.
