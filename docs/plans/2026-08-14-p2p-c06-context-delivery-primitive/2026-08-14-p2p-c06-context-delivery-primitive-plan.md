# P2P-C06 Minimal Executable Context-Efficient Behavioral Primitive Plan

## Metadata

- Date: `2026-08-14`
- Status: `complete`
- Plan: `docs/plans/2026-08-14-p2p-c06-context-delivery-primitive/2026-08-14-p2p-c06-context-delivery-primitive-plan.md`
- Evidence: `docs/plans/2026-08-14-p2p-c06-context-delivery-primitive/2026-08-14-p2p-c06-context-delivery-primitive-evidence.md`
- Benchmark: `docs/plans/2026-08-14-p2p-c06-context-delivery-primitive/2026-08-14-p2p-c06-context-delivery-primitive-benchmark.md`
- Actual status: `docs/plans/2026-08-14-p2p-c06-context-delivery-primitive/2026-08-14-p2p-c06-context-delivery-primitive-actual-status.md`

## Goal

Create the smallest deterministic executable context-delivery primitive that exposes exactly `BASELINE_COMPAT` and experimental `CONTEXT_EFFICIENT_V1`, keeps the normal default baseline-compatible, preserves the same legitimate sources/tools/permissions/acceptance, and emits enough manifest/fingerprint metadata for a later live host boundary to identify the selected mode. This Goal prepares a future live A/B; it does not certify tokens, cost, speed, quality, or provider execution.

## Rules

- Complete P0 actual status before implementation work.
- Update each checklist item immediately when it is completed.
- Record evidence as work completes.
- Record benchmarkable counts or measurements when they are taken.
- Update later phase status assumptions, next actions, and work steps when actual-status evidence changes the repo state.
- Run Anvien detect-changes before every implementation-slice commit when implementation work was performed.
- Keep Anvien HIGH warnings as scope warnings, not edit prohibitions; preserve the narrow invariant family.
- Keep all temporary logs under repository-local `.tmp/`.
- Do not modify the official `.15` artifact or existing `.16-r2` artifact.
- Do not enable network, hooks, proxying, connectors, PXPIPE, or external host execution.
- Do not create a second truth store, memory subsystem, scheduler, DAG, worker pool, router, or live telemetry adapter.
- Do not run the live A/B benchmark in this Goal.
- Use `LOCAL_SERIALIZATION_PROXY` only for deterministic byte-size observations; never call it tokens, usage, cost, savings, or provider evidence.
- Preserve canonical identities exactly: eight agents, denominator 8, full quorum 8/8; Aesthetica remains optional and noncanonical.
- This is a Python package/runtime change, so UI, Docker, database, and Playwright checks are N/A with reasons recorded in evidence.

## Problem

The current P2P path assembles Goal Contract, project inspection, bootstrap/eval state, evidence reuse, ledger events, optional Decision Trace, report, and CAPSULE state, but it has no executable context mode. `CURRENT_15_EXECUTION_CONTRACT` and `CANDIDATE_CONTEXT_EFFICIENT_CONTRACT` are only metadata in the historical proxy suite. The existing `.p2p/system/p2p_capabilities/context.py` resolves pointer metadata and freshness but does not build a task-start view or bind that view to the workflow.

## Scope

- Recover and record the current context flow from the actual source.
- Extend the existing context capability module with deterministic mode selection, safe context views, source/pointer bindings, fingerprints, freshness validation, and local serialization-proxy metadata.
- Wire the selected mode through the bounded workflow's explicit CLI/API, ledger, report, status, and CAPSULE references.
- Add focused behavior tests for the 12 canonical scenarios and all required safety/fairness/default/fail-closed invariants.
- Run affected regression, governance, Decision Trace, capability, secret, doctor, and package checks without promoting or packaging a release.

## Non-Goals

- No CAPSULE 2.0, Knowledge Delta 2.0, Memory Loadout, Memory Hub, CodeGraph, Task DAG, scheduler, lease, recovery engine, delegation, agent-count change, provider switch, host executor, token telemetry, or live A/B.
- No irreversible summarization and no LLM-based compression.
- No change to the canonical eval truth system; the 12-scenario fixture is a focused local behavioral suite only.
- No quality, token, cost, speed, or non-inferiority claim.

## Requirements

1. `BASELINE_COMPAT` is the default and represents the current workflow's complete structured context contract; any exact `.15` parity limitation is explicit.
2. `CONTEXT_EFFICIENT_V1` is explicit, deterministic, experimental, off by default, and structurally smaller for fixtures with deferred unrelated detail.
3. Both modes retain the same source catalog, permission/capability constraints, acceptance requirements, required facts, direct dependency contracts, and authoritative pointers.
4. Relevance is driven by auditable item metadata/links and fails closed on ambiguous required information; it is never model confidence.
5. Conflicts remain conflicts with provenance; stale bindings reject old views; pointers resolve to authoritative source entries.
6. Manifests contain mode, included/deferred categories, source/pointer bindings, relevant source hashes, context fingerprint, and a `LOCAL_SERIALIZATION_PROXY` byte count without secrets.
7. Normal workflow behavior and agent selection remain baseline-compatible; unknown modes fail closed.

## Acceptance Criteria

CB1 current context flow is evidenced; CB2/CB3 executable A/B modes exist; CB4 selection is deterministic; CB5 default remains baseline; CB6 B is experimental/off by default; CB7 payloads differ; CB8 legitimate source access is equal; CB9 acceptance is retained; CB10 security/permission constraints are retained; CB11 owner gates are retained; CB12 conflicts are preserved; CB13 dependencies are represented; CB14 omitted detail remains pointer-reachable; CB15 construction is deterministic; CB16 manifest/fingerprint exists; CB17 stale bindings reject; CB18 size is proxy-labeled; CB19 no provider/token/cost claim; CB20-CB26 no new memory/orchestration/delegation/agents and existing evidence systems are reused; CB27 focused tests pass; CB28 regression passes; CB29 governance/security passes; CB30 canonical count is 8; CB31 quorum is 8/8; CB32 existing artifacts are unchanged; CB33 independent Supervisor passes.

## Checklist

- [x] P0-A: Complete actual status before implementation work.
  - Goal: establish the real current state.
  - Work Steps: inspect the workflow, pointer resolver, ledger/evidence/trace/capsule surfaces, prior blocker reports, exact artifact hashes, and Anvien impact; classify each surface and record downstream decisions.
  - Implementation Gate: `2026-08-14-p2p-c06-context-delivery-primitive-actual-status.md` has a completed P0 decision and no implementation started before it.
  - Acceptance: actual status identifies current flow, missing executable B, editable surfaces, preserve-only artifacts, and the no-live-A/B stop rule.

### P1: Context primitive and explicit workflow selection

- Phase Goal: create one small context-view contract and make the workflow emit the selected mode/fingerprint/manifest reference without changing orchestration.
- Phase Boundary:
  - In scope: `.p2p/system/p2p_capabilities/context.py`, `scripts/p2p_workflow.py`, direct unit tests for the new contract.
  - Out of scope: provider/host execution, agents, routing, package release, historical source snapshot, `.15`, `.16-r2`, and live telemetry.
  - Dependencies: P0 evidence; existing `ContextPointer`, `Execution Ledger`, Decision Trace, Goal Contract, evidence, and CAPSULE contracts.
- Phase Implementation Rule: do not implement `P1` directly. Implement `P1-A`, verify it, record evidence, refresh actual-status, then implement `P1-B`.
- Ordered Slice List:
  - P1-A: implement the pure deterministic two-mode context view and safety helpers.
  - P1-B: wire explicit mode selection and observation metadata into the bounded workflow.

- [x] P1-A: Implement the pure deterministic two-mode context view.
  - Goal: make A and B real executable behavior while preserving required information and authoritative reachability.
  - Scope Boundary:
    - Editable: `.p2p/system/p2p_capabilities/context.py` and its direct focused tests.
    - Inspect-only: existing evidence/Decision Trace/CAPSULE semantics and historical `.15`/`.16-r2` sources.
    - Preserve-only: canonical capability registry, agent identities, permissions, governance, and artifacts.
    - Out of scope: retrieval database, summarizer, scheduler, delegation, provider, and host adapter.
  - Non-Goals: no model call, no irreversible compaction, no hidden access restriction.
  - Pre-flight Questions:
    - Data source: existing structured Goal/inspection/evidence/dependency input mappings.
    - Display permission: no user-facing display; machine-readable evidence metadata only.
    - DB read flow: N/A; no database is introduced.
    - DB write flow: N/A; no database is introduced.
    - Render location: N/A; Python return object and JSON evidence.
    - UI behavior flow: N/A; non-UI package runtime.
    - Docker runtime: N/A; no app/runtime container exists for this package surface.
    - Playwright target: N/A; no UI change.
    - Behavior test: direct mode/view/freshness/pointer tests prove trigger -> build -> observable payload.
    - Cleanup/quarantine: tests use temporary project/source mappings only; no persistent user data.
    - External side effects: none.
    - N/A notes: context construction is pure except caller-owned manifest persistence.
  - Work Steps:
    1. Add the exact mode constants, fail-closed selector, canonical serializer/fingerprint, safe-source-binding checks, and required-field safety rules.
       - UI flow check: N/A.
       - DB/data flow check: verify source bindings and constraints are preserved without secret fields.
       - Render location check: verify returned manifest/view fields and deterministic ordering.
       - Mini QA: run focused Python tests immediately after the slice.
       - Evidence target: `E1-P1A-CONTEXT1..E1-P1A-CONTEXT4`.
    2. Add B's deterministic include/defer rules, conflict preservation, pointer resolution, and stale-binding rejection while keeping A as the baseline-compatible complete view.
       - UI flow check: N/A.
       - DB/data flow check: verify authoritative source lookup and changed-hash rejection.
       - Render location check: verify A/B fingerprints and proxy byte sizes are observable.
       - Mini QA: run focused tests including C7/C9/C10/C11/C12 fixtures.
       - Evidence target: `E1-P1A-SAFETY1..E1-P1A-SAFETY5`.
  - Implementation Gate:
    - Before editing, Anvien file-detail/impact for `p2p_capabilities/context.py` is fresh; current separate system index reports 21 symbols, 20 local relationships, one related file, and LOW blast-radius impact for the existing pointer surface.
    - Required facts must be represented by explicit metadata or the builder must fail closed; no model confidence selection is allowed.
  - Acceptance:
    - Source: exactly two accepted mode values and no silent fallback.
    - Runtime/UI: N/A; pure package behavior.
    - DB/data: pointers bind to authoritative sources and stale hashes reject.
    - Behavior test: A/B fingerprints differ where fixture detail is deferrable; required fields and conflicts remain.
    - Cleanup/quarantine: temporary test roots are isolated and removed by the test harness.
    - Evidence IDs: `E1-P1A-CONTEXT1..E1-P1A-SAFETY5`.
    - Actual-status rows refreshed: context primitive, pointer resolver, source-bound freshness.
  - Evidence Targets: source diff, focused test output, Anvien pre-edit detail/impact, and deterministic sample manifest.
  - Actual-status Update: transition context primitive from partial/unbound to executable-but-not-yet-wired; keep historical artifacts preserve-only.
  - Commit Boundary: commit after this slice when acceptance passes; Git is unavailable in this unpacked workspace, so record the exact limitation instead of fabricating a hash.

- [x] P1-B: Wire explicit selection and observation metadata into the bounded workflow.
  - Goal: ensure a future live boundary can prove which mode executed without changing task requirements, tools, permissions, or agent count.
  - Scope Boundary:
    - Editable: `scripts/p2p_workflow.py` and direct workflow tests; existing report/capsule/status/ledger files only through their current writers.
    - Inspect-only: host identity hook, provider/telemetry surfaces, release scripts, historical proxy suite.
    - Preserve-only: `.15`, `.16-r2`, canonical 8, governance policy, and existing helper role/path safety.
    - Out of scope: full live receipt adapter and provider token fields.
  - Non-Goals: no new workflow branch, worker, router, or persistent truth store.
  - Pre-flight Questions:
    - Data source: current Goal Contract, project status, inspection, trusted evidence, and policy mappings.
    - Display permission: selected mode is evidence metadata, not user configuration for normal use.
    - DB read flow: N/A.
    - DB write flow: existing report/ledger/status/capsule paths only.
    - Render location: run result, `run_started`/verification/terminal ledger metadata, report JSON, status, and capsule pointer.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: CLI/API explicit mode plus default and unknown-mode tests.
    - Cleanup/quarantine: tests run against temporary projects.
    - External side effects: local state writes only within the project.
    - N/A notes: existing Decision Trace remains additive and authoritative; no new trace system.
  - Work Steps:
    1. Add an optional explicit `context_mode` argument and CLI option with baseline default and fail-closed invalid input.
       - UI flow check: N/A.
       - DB/data flow check: same existing source set and agent selection for both modes.
       - Render location check: mode appears in result and ledger metadata.
       - Mini QA: run workflow focused tests and default acceptance fixture.
       - Evidence target: `E1-P1B-WIRE1..E1-P1B-WIRE3`.
    2. Persist the manifest/fingerprint as report evidence and reference it from status/CAPSULE/future receipt fields without duplicating source truth.
       - UI flow check: N/A.
       - DB/data flow check: verify only existing evidence/state paths are used.
       - Render location check: verify `context_mode`, `context_fingerprint`, and `context_manifest_pointer` are machine-readable.
       - Mini QA: run workflow, Decision Trace, and helper-role regressions.
       - Evidence target: `E1-P1B-OBS1..E1-P1B-OBS4`.
  - Implementation Gate:
    - Before editing, `scripts/p2p_workflow.py` Anvien file-detail/impact is fresh; it is HIGH due 267 symbols/40 inbound refs/46 linked flows, so the edit remains narrow and all sibling state writers are checked.
    - The existing default path must produce `BASELINE_COMPAT` and the same selected agents/quorum as before.
  - Acceptance:
    - Source: mode selection is explicit and deterministic.
    - Runtime/UI: N/A; CLI/API and local evidence runtime only.
    - DB/data: no new persistence authority and no permission expansion.
    - Behavior test: default, explicit A, explicit B, invalid mode, and no-agent-change tests pass.
    - Cleanup/quarantine: no test artifacts remain outside repo-local temporary roots.
    - Evidence IDs: `E1-P1B-WIRE1..E1-P1B-OBS4`.
    - Actual-status rows refreshed: workflow binding, default isolation, future receipt fields.
  - Evidence Targets: workflow diff, CLI/API outputs, ledger/report/status/capsule inspection, and focused test output.
  - Actual-status Update: transition mode selection and observability from unbound to bound-correct; keep live host execution blocked/out of scope.
  - Commit Boundary: commit after this slice when acceptance passes; record no-Git limitation if applicable.

### P2: Scenario safety and regression closure

- Phase Goal: demonstrate real A/B structural difference across the canonical C1-C12 fixture shape while preserving required facts, fairness, security, and canonical governance.
- Phase Boundary:
  - In scope: new direct tests, focused fixture data, full Python regression, governance/Decision Trace/capability/secret/doctor checks.
  - Out of scope: provider/model A/B, live task quality, token/cost claims, release packaging, and artifact promotion.
  - Dependencies: P1-A and P1-B acceptance.
- Phase Implementation Rule: implement `P2-A` focused tests first, then `P2-B` regression/evidence closure; do not run live A/B.
- Ordered Slice List:
  - P2-A: add and pass the 12-scenario executable context-behavior suite.
  - P2-B: run affected regression/governance/security/doctor checks and record bounded results.

- [x] P2-A: Add and pass the 12-scenario executable context-behavior suite.
  - Goal: prove the primitive is not a label and does not become smaller by dropping required information.
  - Scope Boundary: direct tests and fixture mappings only; no provider or host calls.
  - Non-Goals: no quality certification or token measurement.
  - Pre-flight Questions: data/source flow is deterministic in-memory structured input; UI/DB/Docker/Playwright are N/A; cleanup is test-harness temporary roots.
  - Work Steps:
    1. Cover C1-C12 with assertions for A/B fingerprints, size proxy, acceptance, constraints, owner gate, contradictions, optional capability, resume state, dependencies, and pointer reachability.
    2. Add negative tests for invalid mode, secrets, path leakage, stale binding, ambiguous required data, and attempted permission/agent expansion.
  - Implementation Gate: P1 mode/view API is available and baseline tests remain green.
  - Acceptance: focused suite passes, no live/provider flags are asserted, and every required safety invariant has a direct behavior test.
  - Evidence Targets: `E2-P2A-SCENARIO1..E2-P2A-SCENARIO12` and `E2-P2A-NEGATIVE1..E2-P2A-NEGATIVE6`.
  - Actual-status Update: scenario suite transitions B from executable-only to behaviorally evidenced; quality/efficiency remain unknown.
  - Commit Boundary: commit after focused suite passes; record no-Git limitation if applicable.

- [x] P2-B: Regression, governance, security, and closure evidence.
  - Goal: verify the change does not regress helper roles, Decision Trace, capability registry, canonical quorum, or protected artifact boundaries.
  - Scope Boundary: existing tests/checks and evidence files; no release candidate.
  - Non-Goals: no package rebuild or promotion.
  - Pre-flight Questions: source/tests/ledger/governance are the authority; UI/DB/Docker/Playwright are N/A.
  - Work Steps:
    1. Run focused tests, full unittest discovery, governance drift/Decision Trace/capability checks, targeted secret scan, doctor/lifecycle checks where affected, and `anvien detect-changes --scope all`.
    2. Record exact artifacts/hashes, report the no-Git boundary, update evidence/benchmark/actual-status, and prepare the coder/supervisor reports.
  - Implementation Gate: P2-A passes and no required field was removed from B.
  - Acceptance: all run checks are recorded as PASS, BLOCKED, or NOT_APPLICABLE with reasons; no live A/B or release claim is made; supervisor independently PASSes the bounded primitive claim.
  - Evidence Targets: `E2-P2B-REGRESSION1..E2-P2B-REGRESSION8` and closure evidence.
  - Actual-status Update: all CB1-CB33 are evaluated; terminal state is PASS only for executable behavior readiness, otherwise BLOCKED/REJECT with the exact first unmet criterion.
  - Commit Boundary: final checkpoint is required by repository policy but cannot be created without Git metadata; record that as a process limitation.

- [x] Pn-A: Call supervisor for the implemented-plan acceptance loop.
  - Goal: independently verify the genuine A/B behavior, baseline compatibility, fairness, safety, staleness, experimental isolation, no feature bloat, security, and canonical safety.
  - Work Steps: provide the coder report, plan/evidence/benchmark/actual-status, source diff/files, focused/full command outputs, and exact artifact hashes; accept only a fresh supervisor PASS.
  - Implementation Gate: all implementation slices and required checks are complete or explicitly blocked.
  - Acceptance: supervisor PASSes the exact bounded claim; no quality/efficiency overclaim is accepted.

- [x] Pn-B: Remove dead work created during this plan.
  - Goal: ensure only accepted primitive, tests, reports, and plan evidence remain.
  - Work Steps: inspect changed files and temporary outputs; remove only plan-created dead artifacts; re-run targeted checks; record any non-removable no-Git limitation.
  - Implementation Gate: no unrelated cleanup is included.
  - Acceptance: no dead helper/fixture/report remains and supervisor sees no residual same-invariant gap.

- [x] Pn-C: Close the plan.
  - Goal: finish validation, evidence, benchmark, detect-changes, and final status.
  - Work Steps: run required Python full regression and governance checks; do not run Docker/Playwright because this is non-UI package work; record final evidence and exact candidate artifact preservation.
  - Implementation Gate: Pn-A and Pn-B pass or record a real blocker.
  - Acceptance: plan status, actual-status, evidence, benchmark, coder report, supervisor report, and final user handoff agree; stop immediately after PASS/BLOCKED/REJECT.

## Risk Notes

- `scripts/p2p_workflow.py` has a HIGH graph scope warning; changes must remain limited to context-mode construction/wiring and be covered by direct workflow tests.
- Exact behavioral equivalence with official `.15` is not assumed; the compatibility limitation must remain explicit unless deterministic fixture evidence proves more.
- The existing workspace has no `.git`; commit/detect-changes semantics requiring Git cannot be claimed as PASS and must be recorded as `NOT_APPLICABLE`/blocked process evidence.
- The development checkout contains historical `.tmp` and documentation material; helper-role/path safety and targeted secret scans must avoid treating preserved examples as new runtime facts.
- The result is `EXECUTABLE_BEHAVIOR_READY_FOR_LIVE_AB` only if the bounded primitive and its safety checks pass. It is never `TOKEN_SAVINGS_CERTIFIED`, `QUALITY_NON_INFERIOR`, `CHEAPER`, or `FASTER`.
