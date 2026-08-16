# P2P Goal subsystem refinement Plan

## Metadata

- Date: `2026-08-10`
- Status: `complete; supervisor-pass`
- Plan: `docs/plans/2026-08-10-p2p-goal-refinement/2026-08-10-p2p-goal-refinement-plan.md`
- Evidence: `docs/plans/2026-08-10-p2p-goal-refinement/2026-08-10-p2p-goal-refinement-evidence.md`
- Benchmark: `docs/plans/2026-08-10-p2p-goal-refinement/2026-08-10-p2p-goal-refinement-benchmark.md`
- Actual status: `docs/plans/2026-08-10-p2p-goal-refinement/2026-08-10-p2p-goal-refinement-actual-status.md`

## Goal

Perform one focused refinement of the existing Goal subsystem so P2P first decides whether a request is `DIRECT TASK`, `PLAN FIRST`, `GOAL`, or `SEPARATE GOALS`; lints every long-running Goal for measurable verification oracles; bounds work type, exploration, mutation, and stop behavior; and persists enough capsule state for safe resumption.

## Rules

- Complete P0 actual status before implementation work.
- Preserve the already-PASS reusable-project workflow, project bootstrap, eval, governance, adaptive quorum, evidence reuse, doctor, drift, and source baseline.
- Add only missing or partial Goal behavior required by the attached refinement request and its ten acceptance cases.
- Do not introduce another FACT, Eval, RAG, Approval, Drift, Quorum, or Execution Ledger system.
- Keep the normal user path natural-language driven; helper commands are internal implementation surfaces.
- A long-running Goal cannot enter autonomous execution while a mandatory criterion lacks a verification oracle.
- Optional/backlog items never block PASS; PASS stops immediately.
- No Docker, Playwright, database, or public UI work applies to this CLI/state-only scope.

## Problem

The completed workflow already creates bounded contracts and terminal reports, but it currently creates a Goal for every workflow request, lacks an explicit eligibility classification, treats completion evidence as free-form strings rather than per-criterion verification oracles, and does not persist work type, exploration lanes, failed approaches, or mid-Goal mutation classification in the capsule/ledger.

## Scope

Editable:

- `scripts/p2p_workflow.py` for eligibility, linter, work classification, exploration policy, mutation classification, and capsule/ledger state.
- `.agents/skills/p2p/SKILL.md` for the normal entry routing language.
- `tests/test_p2p_goal_subsystem.py` for direct behavior coverage of all ten acceptance cases.
- This plan/evidence/benchmark/actual-status set and coder/supervisor reports.

Preserve-only:

- Existing bootstrap/eval/governance/approval/drift/quorum helpers and schemas.
- `source/8.4.6-C/` and its 152-file immutable baseline.
- Existing eight named agent profiles and existing workflow regression tests.

## Non-Goals

- No broad P2P architecture review or new skill/plugin.
- No redesign of components already passing the previous Goal.
- No real project-quality eval trials or host-level eight-agent runtime claim.
- No application-code changes, network, hooks, connectors, release, or deployment.

## Requirements

- Eligibility returns exactly one of `DIRECT TASK`, `PLAN FIRST`, `GOAL`, `SEPARATE GOALS` with a reason and bounded next action.
- Vague and open-ended requests receive a bounded measurable interpretation before long-running work; independent objectives are separated.
- Every mandatory completion criterion includes a concrete verification oracle and linter result; subjective language alone is invalid.
- Work items are classified as `MANDATORY FOR GOAL`, `SUPPORTING`, `OPTIONAL / BACKLOG`, or `OUT OF SCOPE`.
- Work type is `AI-BOUND`, `TOOL-BOUND`, or `MIXED`; exploration defaults to one primary lane and at most one evidence-justified alternative.
- Failed approaches and mutation classes (`CONTEXT UPDATE`, `CONSTRAINT UPDATE`, `ACCEPTANCE UPDATE`, `NEW OBJECTIVE`) are recorded without silent Goal expansion.
- Capsules persist criteria, satisfied criteria, evidence reuse, bottleneck, work type, active lane, failed approaches, backlog, approval, and terminal state.
- Genuine BLOCKED output contains exactly one decision/action; optional backlog and further research never cause BLOCKED.

## Acceptance Criteria

- [ ] Eligibility gate distinguishes all four request classes and does not force `/goal` for direct work.
- [ ] PLAN FIRST is selected for ambiguous/open-ended work and compiles a bounded acceptance interpretation.
- [ ] Clear long-running work becomes GOAL with one primary objective.
- [ ] Every mandatory criterion has a verification oracle and passes the Goal Linter before autonomous execution.
- [ ] Mandatory/supporting/optional/backlog/out-of-scope classification is persisted and optional work cannot block PASS.
- [ ] AI/tool/mixed classification and bounded exploration policy are persisted.
- [ ] Failed approach and mid-Goal mutation records are explicit; new objectives do not silently expand the active Goal.
- [ ] Existing evidence reuse and PASS stop behavior remain correct.
- [ ] Capsule supports resumption without full rediscovery.
- [ ] Ten safe Goal acceptance cases pass, plus existing workflow tests, package doctor, and drift.

## Checklist

- [x] P0-A: Complete actual status before implementation work.
  - Goal: classify the existing Goal subsystem and preserve already-correct surfaces.
  - Work Steps: inspect the current helper, entry skill, tests, capsule/state schema, and governance references; record Anvien availability and local fallback; update downstream slice assumptions.
  - Implementation Gate: actual status contains evidence IDs, an invariant-family map, touch modes, and a P0 decision.
  - Acceptance: every requested Goal behavior is marked correct, partial, or missing with a bounded next action.

### P1: Goal decision and execution discipline

- Phase Goal: close the Goal eligibility/linter contract and persist bounded execution state without changing existing governance semantics.
- Phase Boundary:
  - In scope: helper contract/runtime fields, normal entry wording, direct behavior tests.
  - Out of scope: existing package governance and unrelated application work.
  - Dependencies: P0 status, existing `p2p_workflow.py` and current regression tests.
- Phase Implementation Rule: implement `P1-A`, verify and refresh status, then implement `P1-B`.
- Ordered Slice List:
  - P1-A: eligibility, Goal Linter, work-item classification, work type, and exploration/mutation helpers.
  - P1-B: runtime/CLI/capsule/ledger wiring and ten acceptance tests.

- [x] P1-A: Add Goal eligibility, linter, work classification, and bounded policy.
  - Goal: make the Goal decision explicit and reject unlinted open-ended execution.
  - Scope Boundary:
    - Editable: `scripts/p2p_workflow.py` pure classifiers, contract construction, linter fields, and policy state.
    - Inspect-only: existing eval/governance/quorum/capsule schemas.
    - Preserve-only: source baseline, existing gate helpers, existing workflow behavior.
    - Out of scope: new governance or agent identities.
  - Non-Goals: no full runtime orchestration or user-facing wording changes beyond the required routing contract.
  - Pre-flight Questions:
    - Data source: natural-language request plus local project inspection and existing `.p2p` state.
    - Display permission: internal Goal state only; no new user data surface.
    - DB read flow: N/A; filesystem state only.
    - DB write flow: N/A; atomic JSON/JSONL project state only.
    - Render location: Goal Contract JSON and helper output.
    - UI behavior flow: N/A; Codex natural-language entry invokes the helper.
    - Docker runtime: N/A; no app/runtime surface.
    - Playwright target: N/A; no browser surface.
    - Behavior test: direct pure-function and contract tests for all four eligibility classes and linter failure.
    - Cleanup/quarantine: tests use temporary directories; no persistent fixture writes.
    - External side effects: none.
    - N/A notes: no DB, UI, browser, Docker, network, or external communication.
  - Work Steps:
    1. Add deterministic eligibility and bounded interpretation rules, including separate-objective detection.
       - UI flow check: N/A; verify natural-language entry classification.
       - DB/data flow check: verify inspection evidence is the only input besides the request.
       - Render location check: verify classification and reason are returned in inspect/plan output.
       - Evidence target: `E1-P1A-CODE1`, `E1-P1A-TEST1`.
    2. Add Goal Linter/oracle schema, mandatory/supporting/optional/out-of-scope labels, work type, exploration budget, and mutation classifiers.
       - UI flow check: N/A.
       - DB/data flow check: verify every mandatory criterion has a non-placeholder oracle and failure is fail-closed.
       - Render location check: verify contract JSON exposes linter and policy decisions.
       - Evidence target: `E1-P1A-CODE2`, `E1-P1A-TEST2`.
  - Implementation Gate:
    - Anvien target analysis is attempted and its unregistered-repository fallback is recorded.
    - Existing contract fields remain compatible; new fields are additive.
    - No existing PASS path is rewritten beyond eligibility/linter integration.
  - Acceptance:
    - Source: pure functions and schema fields exist with no placeholder or subjective-only oracle.
    - Runtime/UI: N/A; helper contract output is the observable runtime.
    - DB/data: N/A; temporary filesystem contract/state is valid JSON.
    - Behavior test: vague/open-ended/clear/separate requests classify correctly; invalid oracle blocks linter.
    - Cleanup/quarantine: temporary test roots are cleaned by context managers.
    - Evidence IDs: `E1-P1A-CODE1`, `E1-P1A-CODE2`, `E1-P1A-TEST1`, `E1-P1A-TEST2`.
    - Actual-status rows refreshed: eligibility, linter, work policy, and mutation rows.
  - Evidence Targets: source inspection, direct behavior tests, and UTF-8/no-BOM check.
  - Actual-status Update: partial/missing Goal rows become correct or remain explicitly blocked only when evidence requires a user decision.
  - Commit Boundary: no Git checkpoint is possible because the package is not a Git worktree; record this exception.

- [x] P1-B: Wire runtime state, entry guidance, capsule, ledger, and ten acceptance cases.
  - Goal: make one natural-language workflow apply the new decision/linter/policy and leave resumable evidence.
  - Scope Boundary:
    - Editable: `scripts/p2p_workflow.py`, `.agents/skills/p2p/SKILL.md`, `tests/test_p2p_goal_subsystem.py`.
    - Inspect-only: existing project workflow regression tests and governance helpers.
    - Preserve-only: package doctor, installers, manifest, eval, approval, drift, and source baseline.
    - Out of scope: application projects and full quorum runtime.
  - Non-Goals: no second acceptance harness; use the same helper and project-local state.
  - Pre-flight Questions:
    - Data source: current contract/status/trusted evidence plus new user input.
    - Display permission: beginner report remains compact; detailed fields stay in state.
    - DB read flow: N/A.
    - DB write flow: atomic status/capsule and append-only ledger updates.
    - Render location: `.p2p/state/project-status.json`, `.p2p/state/capsules/`, reports, and ledger.
    - UI behavior flow: N/A; normal Codex app invocation is the user-visible trigger.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: ten acceptance tests plus existing four workflow tests.
    - Cleanup/quarantine: temporary fixture roots only.
    - External side effects: none.
    - N/A notes: CLI/state-only refinement.
  - Work Steps:
    1. Wire eligibility and linter into inspect/plan/run and classify mid-Goal input without silently mutating the active Goal.
       - UI flow check: N/A; verify beginner-facing result includes one decision when required.
       - DB/data flow check: verify mutation records are append-only and new objectives are separate/backlog.
       - Render location check: verify report/capsule references the active Goal and mutation state.
       - Evidence target: `E1-P1B-CODE1`, `E1-P1B-TEST1`.
    2. Expand capsule/ledger state and update entry guidance; run all ten safe cases and preserve previous workflow tests.
       - UI flow check: N/A.
       - DB/data flow check: verify PASS/optional backlog, BLOCKED/exact decision, and reuse state survive reload.
       - Render location check: verify compact report remains five-section beginner format.
       - Evidence target: `E1-P1B-CODE2`, `E1-P1B-TEST2`.
  - Implementation Gate:
    - Existing workflow tests remain valid before the new acceptance suite is considered complete.
    - Capsule fields reference authoritative artifacts rather than copying reports.
  - Acceptance:
    - Source: runtime wires the new contract/policy fields on all helper entrypoints.
    - Runtime/UI: installed helper output remains UTF-8 and beginner-friendly.
    - DB/data: N/A; state files and JSONL ledger persist expected fields.
    - Behavior test: ten named cases pass with exact classifications and stop semantics.
    - Cleanup/quarantine: no fixture residue outside `.tmp`.
    - Evidence IDs: `E1-P1B-CODE1`, `E1-P1B-CODE2`, `E1-P1B-TEST1`, `E1-P1B-TEST2`.
    - Actual-status rows refreshed: all Goal subsystem rows.
  - Evidence Targets: ten-case test output, existing regression output, capsule/ledger inspection, and installed smoke.
  - Actual-status Update: all required Goal rows become correct; prior PASS governance rows remain preserve-only.
  - Commit Boundary: no Git checkpoint; record no-`.git` exception.

### P2: Acceptance and gates

- Phase Goal: prove the focused Goal behavior and preserve package/runtime gates.
- Phase Boundary:
  - In scope: ten safe acceptance cases, existing regression, package doctor, drift, lock refresh.
  - Out of scope: real project eval trials, live eight-agent runtime, release.
  - Dependencies: P1-A and P1-B.
- [x] P2-A: Run all acceptance and regression gates.
  - Goal: demonstrate the full Goal decision/linter/discipline invariant.
  - Work Steps: run compile, new ten-case tests, existing tests, package doctor, runtime drift, and final lock refresh; record evidence and benchmarks.
  - Implementation Gate: no stale Goal docs or placeholder oracle remains.
  - Acceptance: ten cases PASS; existing tests, doctor, drift PASS; no duplicate subsystem introduced.

- [x] Pn-A: Call supervisor for the implemented-plan acceptance loop.
  - Goal: independently verify the focused Goal refinement.
  - Work Steps: read supervisor skill, inspect source/report, rerun targeted checks, and write PASS/REJECT report.
  - Implementation Gate: P1/P2 complete or explicitly blocked.
  - Acceptance: supervisor PASS or an evidenced blocker.
  - Evidence: `reports/supervisor/rp_supervisor_260810_164500_by_gpt-5-codex_goal-subsystem-refinement.md`.
- [x] Pn-B: Remove dead work created during this plan.
  - Goal: retain only useful refinement artifacts.
  - Work Steps: inspect new tests/docs/reports/temp outputs and remove only plan-created dead artifacts.
  - Implementation Gate: cleanup does not touch unrelated user data.
  - Acceptance: no stale placeholder/dead helper artifact remains.
  - Evidence: generated fixture bytecode was quarantined only under `.tmp/`; no source fixture or unrelated file was removed.
- [x] Pn-C: Close the plan.
  - Goal: record final evidence, benchmark, lock, and status.
  - Work Steps: run final validation, record no-Git exception, refresh lock after final protected changes, and update all four plan files.
  - Implementation Gate: supervisor PASS and final drift PASS.
  - Acceptance: final response contains only the requested six sections and exact completion sentence.
  - Evidence: `E3-SUPERVISOR1`, `E3-TEST1`, `E3-ACCEPT1`, `E3-FRESH1`, `E3-GATES1`, `E3-LOCK1`, `E3-SCOPE1`.

## Closure

- Supervisor verdict: `PASS`; source/runtime review found no residual Goal invariant gap within the requested package scope.
- Final executable evidence: syntax parse PASS, 17/17 tests PASS, ten Goal cases PASS, existing workflow fixtures PASS, fresh installed doctor/classify/run PASS.
- Final package evidence: doctor PASS, runtime drift PASS after the closure lock refresh, and protected-runtime lock PASS.
- Anvien target registration remained unavailable; local source, tests, installer, doctor, acceptance, drift, and lock evidence are the documented fallback.
- No Git metadata exists in the package; no repository was initialized and no checkpoint commit is claimed.
- No duplicate Goal, governance, Eval, Approval, Drift, Quorum, or Execution Ledger subsystem was introduced.

## Risk Notes

- The package is an unpacked directory without Git metadata; checkpoints are recorded as unavailable rather than creating a repository.
- The ten acceptance cases are deterministic Goal behavior fixtures, not a real project-quality eval or live eight-thread runtime proof.
- Natural-language classification is bounded heuristics; genuine product/business ambiguity remains the only valid user decision path.
