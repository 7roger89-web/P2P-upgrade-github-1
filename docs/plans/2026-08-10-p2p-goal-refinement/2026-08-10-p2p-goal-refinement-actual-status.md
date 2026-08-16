# P2P Goal subsystem refinement Actual Status

Title: P2P Goal subsystem refinement
Date: 2026-08-10
Status: PASS — focused Goal refinement complete; supervisor accepted.
Companion plan: `docs/plans/2026-08-10-p2p-goal-refinement/2026-08-10-p2p-goal-refinement-plan.md`
Companion evidence: `docs/plans/2026-08-10-p2p-goal-refinement/2026-08-10-p2p-goal-refinement-evidence.md`
Companion benchmark: `docs/plans/2026-08-10-p2p-goal-refinement/2026-08-10-p2p-goal-refinement-benchmark.md`

## Purpose

This file records current Goal subsystem reality before the focused refinement. It is a living status record; implementation updates affected rows and appends refresh evidence.

## Freshness / Refresh Rules

The previous reusable-project-workflow state is the baseline. Only the Goal eligibility/linter/discipline gaps named by the new request are editable. Existing passing governance/workflow surfaces remain preserve-only.

## Scope

Target scope:

- Goal eligibility classification and bounded interpretation.
- Goal Contract verification oracles and linter.
- mandatory/supporting/optional/out-of-scope classification.
- work type, exploration budget, iteration/mutation discipline, and capsule/ledger persistence.
- normal entry guidance and direct behavior tests.

Out of scope:

- existing bootstrap/eval/FACT/Live/Approval/Drift/Quorum implementations;
- application projects, network/hooks/connectors, release, deployment, and real host quorum;
- immutable `source/8.4.6-C/` baseline.

## Relationship / Impact Evidence

Anvien was queried for the target but the package is not registered; related-file counts are unavailable from graph tooling. Local source/test inspection is the fallback.

| Unit / File / Surface | File Detail Evidence | Related File Count | Relationship Summary | Impact Note |
|---|---|---:|---|---|
| `scripts/p2p_workflow.py` | `E0-P0A-SRC1`, `E0-P0A-ANV1` | unavailable | Goal contract/dispatcher, state writer, capsule and ledger producer | high within Goal invariant |
| `.agents/skills/p2p/SKILL.md` | `E0-P0A-SRC1`, `E0-P0A-ANV1` | unavailable | natural-language entry routing and output contract | medium |
| `tests/test_p2p_workflow.py` | `E0-P0A-SRC1` | unavailable | existing workflow regression coverage | high validation sibling |
| `tests/test_p2p_goal_subsystem.py` | `E0-P0A-BOUND1` | new | planned ten-case Goal behavior coverage | editable |
| existing governance/eval/quorum/doctor/installer files | `E0-P0A-GATE1` | unavailable | already-PASS control surfaces consumed by helper | preserve-only |

## Status Rules

| Status | Meaning | Allowed next action |
|---|---|---|
| `correct` | Already behaves as required. | Preserve. |
| `partial` | Some required behavior exists, but gaps remain. | Edit only missing Goal behavior. |
| `missing` | Required behavior does not exist. | Implement only that behavior. |
| `blocked` | Required evidence or authority is unavailable. | Record blocker; do not guess. |

## Current Status Matrix

| Unit | Current State | Required State | Status | Relationship Count | Evidence | Next Plan Decision |
|---|---|---|---|---:|---|---|
| Goal eligibility | Helper now exposes exact four-way preflight classification | `DIRECT TASK` / `PLAN FIRST` / `GOAL` / `SEPARATE GOALS` before Goal creation | correct | unavailable | `E1-P1A-CODE1`, `E1-P1A-TEST1` | preserve; run P2 |
| Bounded interpretation | Vague/open-ended requests produce bounded PLAN FIRST reason and measurable next action | explicit bounded PLAN FIRST/direct result with reason and measurable next action | correct | unavailable | `E1-P1A-CODE1`, `E1-P1A-TEST1` | preserve; run P2 |
| Verification oracle/linter | Five mandatory criteria have structured oracles; malformed oracle fails closed | every mandatory criterion has concrete verification method before autonomous execution | correct | unavailable | `E1-P1A-CODE2`, `E1-P1A-TEST2` | preserve; run P2 |
| Mandatory/optional/out-of-scope | Contract and classifier persist four item classes | four explicit item classes; optional/backlog cannot block PASS | correct | unavailable | `E1-P1A-CODE2`, `E1-P1A-TEST1` | preserve; run P2 |
| Work type/exploration | Work type, primary/alternative/speculative limits, and failure reason policy persist | explicit work type, one primary lane, max one justified alternative, failed approach record | correct | unavailable | `E1-P1A-CODE3`, `E1-P1B-TEST1` | preserve; run P2 |
| Iteration/mutation | Approach recorder writes failures to ledger; update classifier rejects silent expansion | baseline/failure/one focused change/affected verify and four mutation classes | correct | unavailable | `E1-P1A-CODE3`, `E1-P1B-CODE1`, `E1-P1B-TEST1` | preserve; run P2 |
| Capsule/status | Generated capsule/status include criteria, evidence, bottleneck, lane, failures, backlog, approval, terminal | include criteria, satisfied evidence, bottleneck, work type, lane, failures, backlog, approval, terminal | correct | unavailable | `E1-P1B-CODE2`, `E1-P1B-TEST1` | preserve; run P2 |
| Beginner entry | Main skill and CLI expose classification/linter before long-running work | natural-language flow internally decides direct/plan/goal/separate | correct | unavailable | `E1-P1B-CODE1`, `E1-P1B-CLI1` | preserve; run P2 |
| Existing workflow/governance | previous acceptance, doctor, drift, source and eight agents PASS | unchanged and reused | correct | unavailable | `E0-P0A-GATE1` | preserve-only |

## Status Refresh Log

| Refresh | Date | Repo Basis | Changed Scope | Status Changes | Evidence | Next Phase Update |
|---|---|---|---|---|---|---|
| R0 | 2026-08-10 | focused refinement baseline after prior workflow PASS | Goal decision/linter/discipline only | eligibility/optional/work-type/mutation missing; oracle/capsule/entry partial; existing workflow/governance correct | `E0-P0A-SRC1`, `E0-P0A-GATE1`, `E0-P0A-ANV1` | implement P1-A then P1-B; preserve correct rows |
| R1 | 2026-08-10 | P1-A/P1-B code, tests, CLI smoke | Goal eligibility, oracle lint, work policy, mutation, capsule, and guidance changed partial/missing -> correct; package gates still pending | `E1-P1A-CODE1`, `E1-P1A-CODE2`, `E1-P1A-CODE3`, `E1-P1A-TEST1`, `E1-P1A-TEST2`, `E1-P1B-CODE1`, `E1-P1B-CODE2`, `E1-P1B-TEST1`, `E1-P1B-TEST2`, `E1-P1B-CLI1` | run P2 acceptance/doctor/drift then supervisor |
| R2 | 2026-08-10 | P2 tests, acceptance, package doctor, fresh install, and drift | 17 tests PASS; ten Goal cases PASS; fresh installed classify/run/doctor PASS; package doctor/drift PASS; supervisor pending | `E2-P2A-TEST1`, `E2-P2A-ACCEPT1`, `E2-P2A-FRESH1`, `E2-P2A-FRESH2`, `E2-P2A-PACKAGE1`, `E2-P2A-DRIFT1`, `E2-P2A-LOCK1` | supervisor review and closure |
| R3 | 2026-08-10 | supervisor source review and closure gate | supervisor PASS; final syntax/tests/acceptance/fresh smoke PASS; final lock, doctor, and drift refreshed after this record | `E3-SUPERVISOR1`, `E3-TEST1`, `E3-ACCEPT1`, `E3-FRESH1`, `E3-GATES1`, `E3-LOCK1`, `E3-SCOPE1` | complete; no further Goal hardening |

## Phase Touch Map

| Unit / File / Surface | Plan-Relevant Relationship File | Relationship to Target | Plan Item | Touch Mode | Evidence | Constraint |
|---|---|---|---|---|---|---|
| `scripts/p2p_workflow.py` | `.p2p/state/` schemas and reports | source-of-truth/consumer | P1-A/P1-B | edit | `E0-P0A-SRC1` | additive fields; keep existing commands/terminal states |
| `.agents/skills/p2p/SKILL.md` | `AGENTS.md` | entry guidance/authority | P1-B | edit | `E0-P0A-SRC1` | route internally; no new user technical burden |
| `tests/test_p2p_workflow.py` | `scripts/p2p_workflow.py` | regression test | P1-B/P2-A | preserve/validate | `E0-P0A-GATE1` | existing 4 tests must remain PASS |
| `tests/test_p2p_goal_subsystem.py` | `scripts/p2p_workflow.py` | behavior tests | P1-B | edit | `E0-P0A-BOUND1` | safe temp fixtures only |
| governance/eval/quorum/doctor/install/source | helper/entry | preserve-only consumers | P2-A | preserve/validate | `E0-P0A-GATE1` | no redesign or duplicate control |

## Detailed Findings

### Goal eligibility and linter

Current state:

The current helper can bound vague objectives but creates the same Goal-oriented workflow for all requests. Completion criteria do not require a structured verification oracle, so an autonomous run could begin with only free-form evidence text.

Required state:

```text
Classify first; compile one bounded contract; fail closed when a mandatory criterion lacks a concrete verification oracle.
```

Evidence:

- `E0-P0A-SRC1`: direct source inspection of current helper/entry/tests.
- `E0-P0A-ANV1`: target unavailable in Anvien; local fallback is required.

Relationship and impact:

- Related file count: unavailable.
- Relationship summary: helper is the source of Goal contract and runtime state; main skill is its entry guidance.
- Impact note: high within this invariant, but no impact on existing governance semantics.

Classification:

partial/missing.

Allowed next action:

Implement P1-A/P1-B only.

Forbidden next action:

Do not rewrite already-PASS bootstrap/eval/governance/quorum/doctor or create a second ledger/gate.

### Existing passing workflow and governance

Current state: previous acceptance, doctor, drift, source 152/152, eight agent identities, and existing evidence reuse are PASS.

Required state: remain unchanged and be consumed by the refined Goal path.

Classification: correct / preserve-only.

## Next Phase Status Decisions

| Plan Item | Actual Status Finding | Required Status / Next-Action Update |
|---|---|---|
| P1-A | eligibility and linter are missing/partial | implement only Goal decision/oracle/policy fields |
| P1-B | capsule/entry/mutation wiring is incomplete | wire new fields and add ten behavior tests after P1-A |
| P2-A | existing gates are correct | run after refinement; do not redesign gates |

## Implementation Gate

- [x] Target scope is listed in Current Status Matrix.
- [x] Each target unit has a status.
- [x] Each status has evidence IDs.
- [x] Target relationship counts are recorded as unavailable with Anvien fallback evidence.
- [x] Phase Touch Map defines touch mode for relevant surfaces.
- [x] Correct parts are preserve-only.
- [x] Partial/missing parts have exact next actions.
- [x] No blocker prevents the focused implementation; Anvien unavailability is a tooling fallback, not a Goal blocker.
- [x] Status Refresh Log has an R0 baseline row.
- [x] Next phase assumptions reflect the current evidence.

## Final gate status

- [x] 17 combined unit tests PASS.
- [x] Ten Goal acceptance cases PASS.
- [x] New/existing project workflow fixtures PASS.
- [x] Package doctor PASS; fresh installed doctor/classify/run PASS.
- [x] Runtime lock PASS (182 protected files); drift PASS.
- [x] Supervisor review PASS and final closure recorded.

## Final Closure

- Supervisor: `PASS`; report path: `reports/supervisor/rp_supervisor_260810_164500_by_gpt-5-codex_goal-subsystem-refinement.md`.
- Executable evidence: syntax parse PASS; 17/17 tests PASS; ten Goal cases PASS; existing workflow fixtures PASS; fresh installed doctor/classify/run PASS.
- Final protected-runtime lock, package doctor, and drift refresh PASS; their results are recorded as `E3-LOCK1` and `E3-GATES1`.
- Anvien target registration is unavailable, so local source/runtime evidence is the declared fallback. No Git metadata exists; no commit is claimed.
- No duplicate Goal or governance subsystem was introduced; existing workflow, Eval, FACT_LEDGER, Live Specs, Approval, Drift, Quorum, and Execution Ledger surfaces remain preserve-only.

## Final P0 Decision

- [ ] P0 actual-status incomplete. Implementation is blocked.
- [x] P0 complete. Next phase status, next action, and work steps must be updated before implementation.
- [ ] P0 complete. Target scope is preserve-only.
- [ ] P0 complete. Implementation is blocked by missing authority or evidence.

Decision note:

The previous workflow is correct and protected. The new refinement has a narrow, evidenced gap in Goal decision/lint/discipline. Proceed with P1-A, then P1-B, without changing already-PASS governance or project workflow gates.
