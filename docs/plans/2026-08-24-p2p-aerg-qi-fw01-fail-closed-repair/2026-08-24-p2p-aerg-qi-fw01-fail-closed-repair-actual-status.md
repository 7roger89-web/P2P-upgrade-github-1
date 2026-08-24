# P2P AERG QI/FW01 Fail-Closed Repair Actual Status

Title: P2P AERG QI/FW01 Fail-Closed Repair
Date: 2026-08-24
Status: P3 Complete — Ready for Supervisor Review
Companion plan: `docs/plans/2026-08-24-p2p-aerg-qi-fw01-fail-closed-repair/2026-08-24-p2p-aerg-qi-fw01-fail-closed-repair-plan.md`
Companion evidence: `docs/plans/2026-08-24-p2p-aerg-qi-fw01-fail-closed-repair/2026-08-24-p2p-aerg-qi-fw01-fail-closed-repair-evidence.md`
Companion benchmark: `docs/plans/2026-08-24-p2p-aerg-qi-fw01-fail-closed-repair/2026-08-24-p2p-aerg-qi-fw01-fail-closed-repair-benchmark.md`

## Purpose

This is the living current-state record before and during the bounded repair. It distinguishes confirmed wrong behavior from preserve-only correct behavior and records the Anvien graph boundary honestly.

## Freshness / Refresh Rules

Refresh after each implementation slice, before the next phase, and before final handoff. Preserve the R0 baseline and append transitions; do not rewrite prior classifications without a refresh entry.

## Scope

Target scope:

- `.p2p/system/p2p_capabilities/quality_intelligence.py`
- `.p2p/system/p2p_capabilities/p2p_fw01_loop.py`
- bounded regression tests and evidence/report artifacts for this repair

Out of scope:

- AERG engine/model repair, governance/candidate/release/deployment paths, `.19`, `.74`, CPT01-R2, RF01, C43, host/GitHub state, Owner authority, promotion, release, deployment, Supervisor review, independent verification, and Owner approval

## Relationship / Impact Evidence

Anvien refreshed the current Git worktree successfully. The index contains duplicate `P2P-upgrade-github-1` names and its file projection does not resolve hidden `.p2p/system` target files or their symbols; exact `file-detail`/symbol-impact commands returned not found/ambiguous. Direct source/runtime evidence is therefore required for the target relationship decision.

| Unit / File / Surface | File Detail Evidence | Related File Count | Relationship Summary | Impact Note |
|-----------------------|----------------------|--------------------|----------------------|-------------|
| `quality_intelligence.py::build_quality_verdict` | `E0-P0A-GRAPH1` | unavailable: hidden path not projected | direct QI caller and tests inspected from source | unknown graph risk; narrow function edit |
| `p2p_fw01_loop.py::Fw01Loop.step` | `E0-P0A-GRAPH1` | unavailable: hidden path not projected | real FW01 step consumes QI verdict and persists checkpoint | unknown graph risk; narrow seam edit |
| `aerg_engine.py`, `aerg_model.py` | `E0-P0A-SRC1` | preserve-only; no planned edit | actual AERG source/model input and serialization | preserve; no edit unless mechanical necessity |

## Status Rules

| Status | Meaning | Allowed next action |
|--------|---------|---------------------|
| `correct` | Already satisfies the required behavior. | Preserve and regress. |
| `partial` | Some required behavior exists but a gap remains. | Change only the missing part. |
| `wrong` | Current behavior violates the invariant. | Add RED proof, then narrow repair. |
| `missing` | Required behavior does not exist. | Implement only the missing piece. |
| `unbound` | Existing surface is not bound to the real contract. | Bind only to the real source. |
| `fake-or-stub` | Placeholder/mock is treated as real behavior. | Remove or make the state truthful. |
| `blocked` | Authority, source, or evidence is unclear. | Stop and report the blocker. |

## Current Status Matrix

| Unit | Current State | Required State | Status | Relationship Count | Evidence | Next Plan Decision |
|------|---------------|----------------|--------|--------------------|----------|--------------------|
| AERG engine freshness/aggregation | Current source preserves stale/contradiction semantics and fresh path | stale/contradiction closed with observable freshness | correct | preserve-only | E0-P0A-SRC1 | preserve through P1/P2 |
| AERG model serialization | Current result serialization preserves decision/status/freshness | serialized stale truth remains stale | correct | preserve-only | E0-P0A-SRC1 | preserve through P1/P2 |
| QI actual AERG-result mapping | Current stale/contradicted/scope-mismatch/insufficient mapping exists | actual AERG results remain fail-closed | correct | unavailable in graph | E0-P0A-SRC1 | preserve and regress |
| QI generic required-evaluation classification | explicit proof allowlist; non-proof and unknown required statuses block | only explicit proof statuses may verify; all non-proof/unknown block | correct | unavailable in graph | E1-P1B-SRC1, E1-P1B-TEST1 | preserve optional semantics |
| FW01 current QI seam | Current callable with `aerg_result` blocks stale AERG | current path remains fail-closed | correct | unavailable in graph | E0-P0A-SRC1 | preserve and regress |
| FW01 compatibility seam | Post-QI clamp independently requires actual safe/current/bound/contract-supporting AERG result | compatibility shape cannot weaken AERG safety | correct | unavailable in graph | E2-P2B-SRC1, E2-P2B-TEST1 | preserve fresh compatibility behavior |
| Protected governance/candidate/release state | `.19` promoted, `.74` sealed/unpromoted, promotion false, CPT01-R2 host blocked | unchanged | correct | preserve-only | E0-P0A-STATE1 | do not touch |
| Prior independent REJECT reports | current and prior REJECT artifacts exist and are unchanged | immutable audit history | correct | preserve-only | E0-P0A-REPORT1 | do not touch |
| Framework validator | 52/59 with seven named inherited failures | same seven inherited failures; no whole-framework PASS | correct as inherited debt | preserve-only | E0-P0A-STATE1 | do not repair; recheck P3 |

Final status at handoff (appended after the R0/R1 classifications above):

| Unit | Final State | Required State | Status | Evidence | Handoff Constraint |
|------|-------------|----------------|--------|----------|-------------------|
| QI generic required-evaluation classification | Explicit proof allowlist; non-proof and unknown required statuses block | only explicit proof statuses may verify; all non-proof/unknown block | correct | E1-P1B-SRC1, E1-P1B-TEST1 | preserve optional distinction |
| FW01 compatibility seam | Post-QI clamp requires actual safe/current/bound/contract-supporting AERG result | compatibility shape cannot weaken AERG safety | correct | E2-P2B-SRC1, E2-P2B-TEST1 | preserve fresh compatibility behavior |
| AERG engine/model and serialization | unchanged source; stale/contradiction truth remains observable | preserve existing semantics | correct/preserve-only | E3-P3A-PROOF1 | no sibling edits |
| Protected governance and audit history | unchanged protected state and prior REJECT reports | immutable in this task | correct/preserve-only | E3-P3A-PROOF1 | no Supervisor/Owner/host action |

## Status Refresh Log

| Refresh | Date | Repo Basis | Changed Scope | Status Changes | Evidence | Next Phase Update |
|---------|------|------------|----------------|----------------|----------|-------------------|
| R0 | 2026-08-24 | current HEAD `6e531896` before repair | QI/FW01/AERG sibling boundary | QI generic path `wrong`; FW01 compatibility path `wrong`; AERG engine/model/current QI/protected state `correct` or preserve-only | E0-P0A-GIT1..E0-P0A-STATE1 | proceed to RED tests; keep production scope to two files |
| R1 | 2026-08-24 | `ce641d6` after QI repair | QI required-status classifier | generic QI path `wrong -> correct`; current AERG mapping preserved; optional semantics preserved | E1-P1B-SRC1, E1-P1B-TEST1 | proceed to FW01 repair; no sibling edits |
| R2 | 2026-08-24 | `0910b18` after FW01/test repair and final regressions | QI/FW01 boundary and protected/audit scope | FW01 compatibility path `wrong -> correct`; all repaired surfaces correct; seven validator classes remain inherited | E2-P2B-SRC1, E2-P2B-TEST1, E3-P3A-TEST1, E3-P3A-PROOF1 | hand off for separate Supervisor review; no approval/promotion |

## Phase Touch Map

| Unit / File / Surface | Plan-Relevant Relationship File | Relationship to Target | Plan Item | Touch Mode | Evidence | Constraint |
|-----------------------|---------------------------------|------------------------|-----------|------------|----------|------------|
| QI required classifier | `test_aerg_qi_fw01_fail_closed.py` | behavior test | P1-A/P1-B | edit test then edit source | E0-P0A-SRC1 | unknown status fails closed |
| FW01 compatibility seam | `test_aerg_qi_fw01_fail_closed.py` | real runtime integration test | P2-A/P2-B | edit test then edit source | E0-P0A-SRC1 | actual AERG result remains authoritative |
| `aerg_engine.py` | QI/FW01 consumers | source-of-truth evidence producer | P1/P2 | preserve-only | E0-P0A-SRC1 | no repair unless mechanically required |
| `aerg_model.py` | QI/FW01 consumer input serialization | serialization boundary | P1/P2 | preserve-only | E0-P0A-SRC1 | stale truth must remain observable |
| `.19`/`.74`/CPT01-R2/governance | reports/evidence | protected state | P3 | do-not-touch | E0-P0A-STATE1 | no promotion/host action |
| prior REJECT reports | coder/problem handoff | audit history | P3 | preserve-only | E0-P0A-REPORT1 | no overwrite or deletion |

## Detailed Findings

The two subsections below preserve the R0 pre-repair defect descriptions for
audit continuity. The current status is recorded in the final-status table and
R1/R2 refresh rows above.

### QI generic required-evaluation classification

Current state:

The required loop recognizes only explicit failure strings and unavailable values. Other required values fall through to `QUALITY_VERIFIED` when execution is `SUCCESS` and other gates are known.

Required state:

```text
Only explicit current proof statuses may satisfy a required evaluation. Known non-proof and unknown statuses must add a blocking failure and prevent checkpointing. Optional evaluations retain existing informational behavior.
```

Evidence:

- `E0-P0A-SRC1`: current QI source lines 717-727 show the fall-through.
- `E0-P0A-SPEC1`: execution/evidence contract requires stale/missing/conflicting evidence to remain incomplete/contradicted.

Relationship and impact:

- Related file count: unavailable through hidden path projection.
- Relationship summary: QI verdict is consumed by FW01 and other capability tests.
- Impact note: unknown graph risk; source and runtime regression are mandatory.

Classification:

`wrong`

Allowed next action:

P1-A RED test, then P1-B narrow classifier in the existing loop.

Forbidden next action:

Do not add a second QI engine, alter optional semantics, or repair unrelated validator debt.

### FW01 compatibility seam

Current state:

FW01 conditionally omits `aerg_result` for compatibility callables based on signature inspection and accepts their returned checkpoint decision. This permits an actual stale AERG result to be checkpointed as verified.

Required state:

```text
The compatibility callable may omit the parameter, but FW01 must independently require an actual safe/current/supported AERG result before checkpoint acceptance.
```

Evidence:

- `E0-P0A-SRC1`: current FW01 source lines 926-937 omit the result and lines 969-1013 persist the unchecked verdict.
- `E0-P0A-SPEC1`: compatibility must not weaken existing evidence/authority semantics.

Relationship and impact:

- Related file count: unavailable through hidden path projection.
- Relationship summary: real `Fw01Loop.step()` flows through durable observation, AERG, QI, and checkpoint persistence.
- Impact note: unknown graph risk; real isolated worktree step tests are mandatory.

Classification:

`wrong`

Allowed next action:

P2-A RED integration test, then P2-B narrow semantic clamp before checkpoint gating.

Forbidden next action:

Do not redesign compatibility API, add a second verifier, or make the clamp a hidden promotion/release gate.

## Next Phase Status Decisions

| Plan Item | Actual Status Finding | Required Status / Next-Action Update |
|-----------|-----------------------|--------------------------------------|
| P1-A | QI required-status path is wrong but directly testable | add RED matrix before production edit |
| P1-B | QI current AERG mapping is correct; generic classifier is wrong | edit only the classifier after RED commit |
| P2-A | FW01 current path is correct; compatibility path is wrong | add real step-path RED case before FW01 edit |
| P2-B | actual AERG safety predicate is not enforced after compatibility dispatch | add narrow clamp, preserve current QI path |
| P3 | protected/audit state is preserve-only; validator debt inherited | validate and hand off; no Supervisor/Owner action |

## Implementation Gate

- [x] Target scope is listed in Current Status Matrix.
- [x] Each target unit has a status.
- [x] Each status has evidence IDs.
- [x] Each target file has relationship-count evidence or an explicit Anvien limitation.
- [x] Phase Touch Map lists plan-relevant relationship surfaces.
- [x] Phase Touch Map defines touch mode for each affected unit.
- [x] Correct parts are preserve-only.
- [x] Wrong parts have exact RED-then-repair actions.
- [x] Blockers are recorded: Anvien hidden-path projection limitation only; direct source/runtime evidence remains available.
- [x] Next phase status assumptions and actions are updated from P0.
- [x] Status Refresh Log has an R0 baseline row.
- [x] Affected rows refreshed after implementation slices.

## Final P0 Decision

- [ ] P0 actual-status incomplete. Implementation is blocked.
- [x] P0 complete. Next phase status, next action, and work steps are explicit.
- [ ] P0 complete. Target scope is preserve-only.
- [ ] P0 complete. Implementation is blocked by missing authority or evidence.

Decision note:

P0 is complete. The current branch/subject is unambiguous, the defect is bounded to two existing production seams, and the required evidence path is available through direct source and isolated runtime tests. Anvien graph resolution is incomplete for hidden target files, so no low-blast-radius claim is made; the repair remains narrow by plan and source inspection.
