# P2P-GOVREC01 Current Governance Authority Reconciliation Actual Status

Title: P2P-GOVREC01 Current Governance Authority Reconciliation
Date: 2026-08-26
Status: P0 Complete / implementation in progress
Companion plan: `docs/plans/2026-08-26-p2p-govrec01-current-governance-authority/2026-08-26-p2p-govrec01-current-governance-authority-plan.md`
Companion evidence: `docs/plans/2026-08-26-p2p-govrec01-current-governance-authority/2026-08-26-p2p-govrec01-current-governance-authority-evidence.md`
Companion benchmark: `docs/plans/2026-08-26-p2p-govrec01-current-governance-authority/2026-08-26-p2p-govrec01-current-governance-authority-benchmark.md`

## Purpose

This is the P0 gate and living current-state record. It classifies the exact current candidate before implementation and will be refreshed after every implementation slice. It does not replace the evidence ledger.

## Freshness / Refresh Rules

P0 is based on the exact candidate worktree at promoted `2a71410…`. Refresh after each slice, before the next phase, and before final Supervisor review. Do not copy status from the dirty root snapshot, `.74` candidate reports, historical `.19` artifact, or PREPILOT exact-head claims without rechecking the current candidate.

## Scope

Target scope:

- Current authority projection, runtime-manifest drift, historical/current Council semantics, edge-case index, doctor decoder, and their tests/reports.

Out of scope:

- `.19` artifact mutation, `.74` promotion, release/deploy/push, providers, Manus, Council execution, production projects, and root Git-admin repair.

## Relationship / Impact Evidence

| Unit / File / Surface | File Detail Evidence | Related File Count | Relationship Summary | Impact Note |
|---|---|---:|---|---|
| `governance/development-control.json` | `E0-P0A-GRAPH3` | 2 inbound | README and prior coder report import the authority projection | low scope warning; source-of-truth semantics |
| `governance/runtime-manifest.lock.json` | `E0-P0A-GRAPH4` | 0 graph symbols | deterministic generated lock consumed by drift helper | low scope warning; regenerate only |
| `scripts/doctor.py::check_governance` | `E0-P0A-GRAPH2`, `E0-P0A-IMPACT1` | 3 inbound / 78 local / 14 flows | doctor main and helper flows consume the subprocess boundary | high scope warning; bounded one-function edit |
| `scripts/p2p_governance.py` | `E0-P0A-GRAPH5` | source helper and test consumer | runtime manifest/drift implementation | high scope warning; inspect-only unless blocked |
| `tests/test_p2p_governance_drift.py` | `E0-P0A-IMPACT2` | 2 outbound / 1 local | calls `scan_volatile`; current count assertions are stale | high test-contract warning |
| Council canonical projections | `E0-P0A-GRAPH6` | low/derived-doc relationships | roadmap, ledger, capability and human-readable projections | low/medium document scope |
| `reports/Edge-Case/QA+EDGE_CASE_TEST_PLAN.md` | missing at P0 | 0 | required native evidence index is absent | missing; add P2-B |

## Status Rules

| Status | Meaning | Allowed next action |
|---|---|---|
| `correct` | Already behaves as required. | Preserve and test. |
| `partial` | Some required behavior exists, but gaps remain. | Change only missing part. |
| `wrong` | Current behavior or contract is incorrect. | Replace narrowly and prove. |
| `missing` | Required surface does not exist. | Implement only the missing piece. |
| `unbound` | Surface exists but is not wired to the real source. | Bind to the real source only. |
| `fake-or-stub` | Prototype/mock/placeholder is treated as real. | Remove false claim; preserve UNKNOWN. |
| `blocked` | Authority/evidence is unclear. | Stop. |

## Current Status Matrix

| Unit | Current State | Required State | Status | Relationship Count | Evidence | Next Plan Decision |
|---|---|---|---|---:|---|---|
| Historical `.19` official artifact | `PROMOTED_VERIFIED`, exact artifact SHA and approval preserved | immutable historical official evidence | correct | n/a | `E0-P0A-AUTH3` | preserve-only |
| Current promoted `origin/main` | exact commit `2a71410…`, tree `3e6ab12…`, parent/base `af02170…` is now separately projected under `authority.current_promoted_source`; release authority remains deferred | separate current promoted source authority, not release authority | correct | 2 inbound in authority file | `E0-P0A-AUTH1`, `E0-P0A-GRAPH3`, `E1-P1A-AUTH1..7` | proceed P1-B |
| `.74` successor | `ACTIVE_UNPROMOTED` / `SEALED_UNPROMOTED` record exists | remain unpromoted and separate | correct | n/a | `E0-P0A-AUTH3` | preserve-only |
| Protected runtime lock | lock has 1,172 files; current manifest has 1,178; six additions and eleven changed hashes | exact current promoted manifest after classification | wrong | generated | `E0-P0A-DRIFT1..2` | edit P1-B |
| Drift policy | current schema/patterns/exclusions are intact; no need for wildcard expansion | unchanged fail-closed policy | correct | generated | `E0-P0A-DRIFT2` | preserve-only |
| Historical C36 Council evidence | genuine historical single-host 8/8 evidence exists in retained reports | remain historical, exact and immutable | correct | derived | `E0-P0A-SCOPE1` | preserve-only |
| Current-lineage Council proof | current source has configured 8/8 structure and bounded C43 smoke, not a full current round-trip | `FALSE` / `NOT_PROVEN` until fresh exact evidence | partial | derived | prepilot council audit, `E0-P0A-AUTH1` | edit P2-A |
| Active Council projections | historical `LIVE_COUNCIL_8_OF_8` wording appears beside current not-proven wording | explicit historical/current distinction | wrong | derived | `E0-P0A-SCOPE1` | edit P2-A |
| Edge-case index | no canonical `reports/Edge-Case/QA+EDGE_CASE_TEST_PLAN.md` | required family map and live evidence slots | missing | n/a | `E0-P0A-SCOPE1` | edit P2-B |
| `doctor.py` governance subprocess | default text reader emits Windows UTF-8 decoder traceback before JSON; underlying drift remains fail | explicit UTF-8 strict boundary, malformed output fail closed | wrong | 3 inbound / 78 local / 14 flows | `E0-P0A-DOCTOR1`, `E0-P0A-GRAPH2`, `E0-P0A-IMPACT1` | edit P3-A |
| Drift test fixture | asserts 10 scoped paths/35 refs against current 38-entry policy and current measured references | current policy truth plus negative governance tests | wrong | 2 outbound | `E0-P0A-TEST1`, `E0-P0A-IMPACT2` | edit P3-B |
| Provider/Manus/Council execution | not run | remain not run | correct | n/a | `E0-P0A-SCOPE1` | preserve-only |
| Root Git admin / dirty owner worktrees | root `.git` invalid; owner worktrees dirty and out of scope | untouched | correct | n/a | root recovery report and `E0-P0A-AUTH2` | preserve-only |

## Status Refresh Log

| Refresh | Date | Repo Basis | Changed Scope | Status Changes | Evidence | Next Phase Update |
|---|---|---|---|---|---|---|
| R0 | 2026-08-26 | exact promoted `2a71410…` candidate before implementation | full GOVREC01 scope | initial classifications recorded | `E0-P0A-AUTH1..E0-P0A-SCOPE1` | P1-A/P1-B are executable; P2/P3 remain dependent |
| R1 | 2026-08-26 | after P1-A authority projection edit | authority projection | `partial -> correct`; existing control fixture errors remain assigned to P3-B | `E1-P1A-AUTH1..7` | proceed P1-B; do not treat fixture errors as authority PASS |
| R1b | 2026-08-26 | after P1-B implementation commit | runtime lock/drift | pending | pending | update P2 from fresh drift output |
| R2 | 2026-08-26 | after P2-A/P2-B implementation commit | Council semantics and edge index | pending | pending | update P3/P4 |
| R3 | 2026-08-26 | after P3-A/P3-B implementation commit | doctor and tests | pending | pending | update P4 final gates |

## Phase Touch Map

| Unit / File / Surface | Plan-Relevant Relationship File | Relationship to Target | Plan Item | Touch Mode | Evidence | Constraint |
|---|---|---|---|---|---|---|
| `governance/development-control.json` | `README.md` | source-of-truth consumer | P1-A | edit | `E0-P0A-GRAPH3` | keep `.19` and `.74` records intact |
| `governance/runtime-manifest.lock.json` | `scripts/p2p_governance.py` | generated output | P1-B | regenerate | `E0-P0A-DRIFT2` | existing lock command only |
| `scripts/doctor.py` | `tests/test_p2p_doctor_roles.py`, `main` | shared CLI helper boundary | P3-A | edit | `E0-P0A-GRAPH2`, `E0-P0A-IMPACT1` | no other subprocess path |
| `tests/test_p2p_governance_drift.py` | `scripts/p2p_governance.py::scan_volatile` | behavior test consumer | P3-B | edit | `E0-P0A-IMPACT2` | no threshold weakening |
| Council canonical projections | C36/C43 reports | historical evidence source | P2-A | edit projections; preserve reports | `E0-P0A-SCOPE1` | no current live claim |
| `reports/Edge-Case/QA+EDGE_CASE_TEST_PLAN.md` | existing edge-case skills/tests | evidence index | P2-B | edit/add | `E0-P0A-SCOPE1` | no new framework |
| `.19` artifact and reports | none | historical reference | all | do-not-touch | `E0-P0A-AUTH3` | immutable |
| dirty owner worktrees/root `.git` | none | owner data/admin state | all | do-not-touch | `E0-P0A-AUTH2` | no cleanup or repair |

## Detailed Findings

### Authority and lineage

Current state:

The exact promoted source is known mechanically in the canonical checkout, but the existing development-control authority projection has only the `.19` artifact and `.74` development records. This is a representation gap, not permission to replace the official artifact or promote `.74`.

Required state:

```text
official_baseline = historical .19 PROMOTED_VERIFIED
current_promoted_source = origin/main @ 2a71410, tree 3e6ab12, base af02170
current_development = .74 ACTIVE_UNPROMOTED
```

Evidence:

- `E0-P0A-AUTH1`: exact promoted source identity.
- `E0-P0A-AUTH3`: existing `.19`/`.74` records.

Relationship and impact:

- Related file count: 2 inbound to the authority JSON.
- Relationship summary: README and prior coder report import the authority projection.
- Impact note: low graph risk but high governance consequence.

Classification:

`partial`

Allowed next action:

Add a separate current promoted source projection under the existing authority surface.

Forbidden next action:

Replace `.19`, relabel `.74`, infer authority from filename, or create a second authority system.

### Protected runtime drift

Current state:

The runtime lock was generated before current promoted main's six additions and eleven changed files. The policy is unchanged and virtual hashes already match.

Required state:

```text
Every delta has an evidence-backed classification, then the existing deterministic lock generator produces an exact current manifest.
```

Evidence:

- `E0-P0A-DRIFT1..E0-P0A-DRIFT3`.

Relationship and impact:

- Related file count: generated lock consumed by the drift helper.
- Relationship summary: protected-path hash projection.
- Impact note: integrity gate; no whitelist expansion allowed.

Classification:

`wrong` until P1-B closes it; then `correct` only after direct PASS.

Allowed next action:

Classify each path and regenerate through `lock-runtime`.

Forbidden next action:

Delete files, add wildcard exclusions, suppress output, or accept unexplained drift.

### Council semantics

Current state:

Historical C36 single-host 8/8 evidence exists, while current C43/current-head evidence does not establish a full current Council round-trip. Active projections use ambiguous `LIVE_COUNCIL_8_OF_8` wording.

Required state:

```text
HISTORICAL_SINGLE_HOST_LIVE_COUNCIL_8_OF_8 = TRUE
CURRENT_LINEAGE_FULL_COUNCIL_LIVE_PROVEN = FALSE
CURRENT_LINEAGE_FULL_COUNCIL_STATUS = NOT_PROVEN
```

Evidence:

- prepilot council audit facts and `E0-P0A-SCOPE1`.

Relationship and impact:

- Related file count: derived governance/projection surfaces.
- Relationship summary: roadmap and capability records consume historical evidence.
- Impact note: semantic/document risk; no live runtime change.

Classification:

`wrong` wording / `partial` evidence projection.

Allowed next action:

Clarify active projections and add negative assertions.

Forbidden next action:

Upgrade current Council from C36, C43 smoke, profiles, configured quorum, or logs.

## Next Phase Status Decisions

| Plan Item | Actual Status Finding | Required Status / Next-Action Update |
|---|---|---|
| P1-A | current promoted source is now separately projected; `.19` and `.74` remain separated | complete; proceed P1-B |
| P1-B | all 17 runtime deltas are explainable candidates but lock is stale | keep P1-B; block on any unexplained path |
| P2-A | active wording blurs historical/current Council | keep P2-A; preserve all historical reports |
| P2-B | dedicated edge-case index is absent | keep P2-B add-only |
| P3-A | doctor reader-thread decode failure is reproduced | keep P3-A bounded strict decoder fix |
| P3-B | drift test expectation is stale; no gate weakening allowed | update current measured assertions and add negative tests |
| P4 | no final gates run yet | remain pending until P1-P3 pass |

## Implementation Gate

- [x] Target scope is listed in Current Status Matrix.
- [x] Each target unit has a status.
- [x] Each status has evidence IDs.
- [x] Target code file has relationship/impact evidence from Anvien.
- [x] Phase Touch Map lists plan-relevant relationship files and touch modes.
- [x] Correct parts are marked preserve-only.
- [x] Partial, missing, wrong, unbound, and fake-or-stub parts have exact next actions.
- [x] Blockers are recorded where applicable.
- [x] Next phase status assumptions and next actions are updated from P0 evidence.
- [x] Status Refresh Log has an R0 baseline row.
- [ ] Affected rows refreshed after each implementation slice.

## Final P0 Decision

- [ ] P0 actual-status incomplete. Implementation is blocked.
- [x] P0 complete. Next phase status, next action, or work steps must be updated before implementation.
- [ ] P0 complete. Target scope is preserve-only.
- [ ] P0 complete. Implementation is blocked by missing authority or evidence.

Decision note:

P0 is complete because the exact supplied promoted source, historical `.19`, unpromoted `.74`, current lock delta, Council evidence boundary, missing edge index, Anvien graph state, and doctor decoder failure are all identified. Implementation may proceed in the ordered slices, but any newly discovered protected drift without a path-specific authority explanation must terminally block the task.
