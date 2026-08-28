# P2P-EFF01 Execution Efficiency Canonicalization Plan

## Metadata

- Date: `2026-08-28`
- Status: `P2-C Complete`
- Plan: `docs/plans/2026-08-28-p2p-eff01-execution-efficiency-canonicalization/2026-08-28-p2p-eff01-execution-efficiency-canonicalization-plan.md`
- Evidence: `docs/plans/2026-08-28-p2p-eff01-execution-efficiency-canonicalization/2026-08-28-p2p-eff01-execution-efficiency-canonicalization-evidence.md`
- Benchmark: `docs/plans/2026-08-28-p2p-eff01-execution-efficiency-canonicalization/2026-08-28-p2p-eff01-execution-efficiency-canonicalization-benchmark.md`
- Actual status: `docs/plans/2026-08-28-p2p-eff01-execution-efficiency-canonicalization/2026-08-28-p2p-eff01-execution-efficiency-canonicalization-actual-status.md`

## Goal

Wire `MINIMUM_SUFFICIENT_WORK` and `RISK_PROPORTIONAL_EXECUTION` into the existing C18 `orchestration_policy.py` contract with four fail-closed execution lanes (`FAST`, `STANDARD`, `STRICT`, `CRITICAL`), preserving the existing worker/context/reasoning/verification policy and all authority, provenance, quorum, and approval boundaries.

## Rules

- Complete P0 actual status before implementation work.
- Update each checklist item immediately when it is completed.
- Record evidence as work completes.
- Record benchmarkable counts or measurements when they are taken.
- Update later phase status assumptions, next actions, and work steps when actual-status evidence changes the repo state.
- Run Anvien detect-changes before every implementation-slice commit when implementation work was performed.
- This is a non-UI, standard-library-only runtime policy change; no Docker or Playwright runtime applies.
- Use the lowest safe lane. Escalate only for material mutation, blast-radius, dependency, security/production/authority, or acceptance-evidence signals.
- Do not create a second router, orchestration engine, truth store, skill system, or provider/model resolver.
- Preserve canonical identities, denominator `8`, full quorum `8/8`, approval, fail-closed CRITICAL predicates, and unpromoted candidate boundaries.
- Do not modify the broken source root; implementation occurs only in the isolated candidate worktree.
- Stop at the lowest test ceiling that proves acceptance; broad/full regression requires an explicit material-risk justification.

## Problem

The existing C18 policy derives bounded worker, context, reasoning, and verification requirements, but it does not express the execution-efficiency contract at the canonical policy boundary. As a result, read-only closure can inherit implementation ceremony, small fixes can inherit broad validation, and high-risk promotion/destructive predicates lack a single lane projection while existing governance remains authoritative.

## Scope

- Extend the existing `TaskProfile` vocabulary only as needed to represent execution materiality and evidence sufficiency.
- Add deterministic lane selection and inspectable policy projections to `.p2p/system/p2p_capabilities/orchestration_policy.py`.
- Add direct acceptance tests for FAST, STANDARD, STRICT, CRITICAL, baseline-failure, JIT-skill, test-ceiling, safety, and stop-rule behavior.
- Refresh plan evidence and produce an isolated, unpromoted commit candidate.

## Non-Goals

- No new router, orchestrator, scheduler, worker executor, skill registry, truth store, provider/model routing, quorum change, release, deployment, live activation, force push, or promotion.
- No changes to individual skill files, existing context/selection consumers, package release artifacts, runtime locks, or verified historical baselines unless a fresh acceptance failure proves the root policy cannot enforce the contract.
- No broad regression unless a material dependency or safety finding requires it.

## Requirements

- Lanes are exactly `FAST`, `STANDARD`, `STRICT`, and `CRITICAL`.
- Default is the lowest safe lane; FAST is valid for read-only, no-mutation, targeted-evidence closure.
- STANDARD covers focused source mutation; STRICT covers registry/runtime changes, material blast radius, unclear acceptance dependency paths, or insufficient targeted evidence; CRITICAL covers security/production/promotion/destructive/owner-authority predicates.
- JIT skill projection must never request `coder` without code mutation, `debugging` without an unexplained material failure, `qa` without a testing/evidence need, or `supervisor` outside terminal independent/high-risk gates by default.
- Validation selection follows `acceptance-specific -> directly affected module -> dependency-neighbor -> broad/full regression`, stopping at the first sufficient level.
- Baseline/pre-existing/out-of-scope unrelated failures are recorded and classified without investigation or lane escalation when they do not invalidate acceptance, affect the dependency path, or create safety/security/authority risk.
- Once acceptance is proven, optional checks are disabled and the policy emits a terminal stop decision.

## Acceptance Criteria

- Cases A-F in the request pass as executable tests against the canonical policy.
- Existing AO1-AO20 and affected C18 consumer tests remain passing.
- Existing canonical governance, permission, provenance, quorum, and CRITICAL fail-closed behavior remains unchanged.
- Candidate SHA/tree are exact and bound to the isolated branch; no promotion/deployment/live activation/force push occurs.
- Supervisor review returns exactly `PASS` or records a truthful blocker.

## Checklist

- [x] P0-A: Complete actual status before implementation work.
  - Goal: establish the real current state and exact mutation boundary.
  - Work Steps: verify live remote/current canonical SHA, isolate from the dirty canonical clone, inspect the existing C18 policy and consumers, record Anvien freshness/limitations, and update downstream phase decisions.
  - Implementation Gate: actual-status contains classifications, evidence IDs, touch modes, and a P0 decision.
  - Acceptance: target policy is `partial`, consumers are preserve-only, and the candidate is safe to edit.

### P1: Implement the canonical execution-efficiency projection

- Phase Goal: add the smallest policy-root behavior and executable contract tests.
- Phase Boundary:
  - In scope: one existing policy module and one direct test module.
  - Out of scope: skill files, routers, executors, governance promotion, packaging, and unrelated regressions.
  - Dependencies: verified `origin/main` candidate base, existing C18 `TaskProfile` vocabulary, existing consumer compatibility.
- Phase Implementation Rule: do not implement `P1` directly. Implement `P1-A`, verify it, record evidence, refresh actual-status, commit when required, then continue to `P1-B`.
- Ordered Slice List:
  - P1-A: Add four-lane policy and JIT/test/stop projections.
  - P1-B: Add the P2P-EFF01 executable acceptance matrix.

- [x] P1-A: Add four-lane policy and JIT/test/stop projections
  - Goal: make lane selection, escalation evidence, JIT skills, test ceiling, baseline handling, and terminal stop behavior deterministic at the existing policy root.
  - Scope Boundary:
    - Editable: `.p2p/system/p2p_capabilities/orchestration_policy.py`.
    - Inspect-only: `.p2p/system/p2p_capabilities/context.py`, `.p2p/system/p2p_capabilities/selection_risk.py`, `scripts/package_release.py`, existing C18 fixtures/tests, and governance/approval surfaces.
    - Preserve-only: existing worker/context/reasoning/verification decisions, canonical router, quorum, owner/approval, provenance, and fail-closed controls.
    - Out of scope: all individual skills, provider/model resolution, execution callbacks, release locks, and promotion.
  - Non-Goals: no new execution framework or runtime side effects.
  - Pre-flight Questions:
    - Data source: existing validated `TaskProfile` plus explicit materiality/evidence flags.
    - Display permission: output is inspectable policy data and cannot grant permission or approval.
    - DB read flow: N/A; pure in-memory policy.
    - DB write flow: N/A; no persistence.
    - Render location: N/A; consumed as structured policy output.
    - UI behavior flow: N/A; no UI surface.
    - Docker runtime: N/A; standard-library Python module.
    - Playwright target: N/A; no public UI/runtime change.
    - Behavior test: direct `derive_requirement` assertions.
    - Cleanup/quarantine: no persistent test state; use repo-local `.tmp` only for logs if needed.
    - External side effects: none.
    - N/A notes: policy does not execute skills or tests; it only selects bounded requirements.
  - Work Steps:
    1. Add lane/materiality vocabulary and deterministic lowest-safe-lane selection while preserving old profile defaults and output fields.
       - UI flow check: N/A; prove structured caller output.
       - DB/data flow check: N/A; prove no writes or truth-store path.
       - Render location check: N/A; prove output remains policy data.
       - Evidence target: source diff, import/compile check, and lane truth-table assertions in P1-B.
    2. Add JIT skill, validation ceiling, baseline-failure, safety-invariant, and terminal-stop projections without invoking any skill or broad test runner.
       - UI flow check: N/A; prove no UI route is created.
       - DB/data flow check: N/A; prove no persistence/permission mutation.
       - Render location check: N/A; prove explicit structured fields and no hidden fallback.
       - Evidence target: direct A-F behavior tests and existing C18 regression.
  - Implementation Gate:
    - P0 actual status is complete.
    - Existing consumers are confirmed unaffected by additive output/defaults.
    - The target policy is the only production file needed for the requested root behavior.
  - Acceptance:
    - Source: four lanes and both named principles are defined in the existing policy module.
    - Runtime/UI: N/A; pure policy result is deterministic.
    - DB/data: no writes, permission expansion, or authority mutation.
    - Behavior test: P1-B covers all required lanes and boundaries.
    - Cleanup/quarantine: no candidate-created transient files in the tracked diff.
  - Evidence IDs: `E1-P1A-SRC1`, `E1-P1A-IMPL1`.
    - Actual-status rows refreshed: policy `partial -> correct`; consumers remain `correct/preserve-only`.
  - Evidence Targets: `E1-P1A-SRC1..E1-P1A-IMPL1`.
  - Actual-status Update: record the implementation transition and update P1-B assumptions from the actual exported contract.
  - Commit Boundary: commit after source compile and focused policy smoke pass.

- [x] P1-B: Add the P2P-EFF01 executable acceptance matrix
  - Goal: prove cases A-F and prevent regression to ceremony-driven escalation.
  - Scope Boundary:
    - Editable: `tests/test_p2p_eff01_execution_efficiency.py`.
    - Inspect-only: existing `tests/test_p2p_adaptive_orchestration.py` and consumer tests.
    - Preserve-only: existing AO1-AO20 fixture semantics.
    - Out of scope: broad test-suite rewrites and unrelated baseline repair.
  - Non-Goals: no synthetic eight-agent quorum, no test-only second policy implementation, no mutation of release/user paths.
  - Pre-flight Questions:
    - Data source: frozen in-test profiles and actual `derive_requirement` output.
    - Display permission: assertions inspect policy data only.
    - DB read/write flow: N/A; isolated pure calls.
    - Render location: N/A.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: `python -m unittest tests.test_p2p_eff01_execution_efficiency -v`.
    - Cleanup/quarantine: no writes outside Python test process.
    - External side effects: none.
    - N/A notes: no acceptance-specific app runtime exists for this pure module.
  - Work Steps:
    1. Encode Cases A-C with exact lane, JIT skill, validation-ceiling, and no-unjustified-full-regression assertions.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: N/A.
       - Evidence target: `E1-P1B-TEST1`.
    2. Encode Cases D-F with critical preservation, baseline classification, optional-check suppression, and no-skill-escalation assertions.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: N/A.
       - Evidence target: `E1-P1B-TEST2`.
  - Implementation Gate:
    - P1-A source behavior is implemented and directly importable.
    - Tests assert observable policy outputs, not source markers alone.
  - Acceptance:
    - Source: test calls canonical `derive_requirement`.
    - Runtime/UI: N/A.
    - DB/data: N/A; no mutation.
    - Behavior test: Cases A-F pass.
    - Cleanup/quarantine: test process leaves no tracked or protected mutations.
    - Evidence IDs: `E1-P1B-TEST1`, `E1-P1B-TEST2`.
    - Actual-status rows refreshed: acceptance matrix `missing -> bound-correct`.
  - Evidence Targets: `E1-P1B-TEST1..E1-P1B-TEST2`.
  - Actual-status Update: record exact case coverage and any baseline failures without opening a new workstream.
  - Commit Boundary: commit after the focused acceptance matrix passes.

### P2: Verify, supervise, and close

- [x] P2-A: Run the lowest sufficient validation ceiling
  - Goal: compile the affected Python runtime, run focused EFF01 tests, and run directly affected C18/consumer tests only if the source change requires them.
  - Work Steps:
    1. Run `python -m compileall -q .p2p/system scripts tests` and the focused EFF01 suite.
    2. Run `tests.test_p2p_adaptive_orchestration` and only directly affected policy consumer tests; classify inherited failures as baseline when the request rule permits.
    3. Run Anvien detect-changes before the implementation checkpoint/closure commit.
  - Implementation Gate: P1-A and P1-B are complete.
  - Acceptance: focused and directly affected validation proves the contract; no broad/full regression is run without a material justification. PASS for EFF01, with one compile-only baseline warning recorded.

- [x] P2-B: Supervisor acceptance review
  - Goal: independently verify source, exact diff, tests, safety boundaries, candidate identity, and the requested terminal packet.
  - Work Steps:
    1. Review the final source and reports against the user request and current candidate SHA/tree.
    2. Verify no promotion, deployment, live activation, force push, or hidden skill mutation occurred.
    3. Record exactly `PASS` or a truthful blocker in the supervisor report.
  - Implementation Gate: P2-A evidence and detect-changes are current.
  - Acceptance: supervisor returns `PASS`, with no residual same-invariant unverified surface, or records `REJECT` with exact remediation. PASS recorded in the Supervisor report.

- [x] P2-C: Close and stop
  - Goal: write the final evidence/report packet and stop at the owner gate.
  - Work Steps:
    1. Refresh actual-status, evidence, and benchmark ledgers with final hashes and validation results.
    2. Verify candidate SHA/tree and clean subject scope; do not push or promote.
    3. Emit the required terminal verdict and stop all optional checks.
  - Implementation Gate: P2-A and P2-B pass or record a blocker.
  - Acceptance: final packet contains all requested fields and `OWNER_GATE_REQUIRED: YES`; no promotion, deployment, live activation, or force push occurred.

## Risk Notes

- The target hidden `.p2p` file is not uniquely available to Anvien's duplicate local registry; direct source and focused runtime evidence are required and the limitation must remain explicit.
- The target policy has many consumers and package inventory relationships; this is a high blast-radius warning, not permission to widen the patch.
- Existing governance/runtime-lock state and dirty owner worktrees are preserve-only; candidate readiness is distinct from promotion/release authority.
- The policy must never turn a lane choice into permission, approval, quorum, or live-host certification.
