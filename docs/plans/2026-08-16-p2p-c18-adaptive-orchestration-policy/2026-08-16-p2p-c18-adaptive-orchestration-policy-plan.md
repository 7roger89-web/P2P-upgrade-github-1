# C18 Adaptive Orchestration Policy Foundation Plan

## Metadata

- Date: `2026-08-16`
- Status: `P0 Complete`
- Plan: `docs/plans/2026-08-16-p2p-c18-adaptive-orchestration-policy/2026-08-16-p2p-c18-adaptive-orchestration-policy-plan.md`
- Evidence: `docs/plans/2026-08-16-p2p-c18-adaptive-orchestration-policy/2026-08-16-p2p-c18-adaptive-orchestration-policy-evidence.md`
- Benchmark: `docs/plans/2026-08-16-p2p-c18-adaptive-orchestration-policy/2026-08-16-p2p-c18-adaptive-orchestration-policy-benchmark.md`
- Actual status: `docs/plans/2026-08-16-p2p-c18-adaptive-orchestration-policy/2026-08-16-p2p-c18-adaptive-orchestration-policy-actual-status.md`

## Goal

Create an evidence-backed, deterministic, provider-neutral foundation that derives the minimum sufficient orchestration requirement for a bounded task across worker strategy, context class, reasoning class, and verification class, without changing the canonical router, provider/model resolution, quorum, or live-host certification boundaries.

## Rules

- Recover durable state before interpreting chat content.
- Complete P0 actual status before implementation.
- Reuse C06, C10, C11, C12, C15, C17, Design Intelligence, Decision Trace, Capsule, and governance authorities; do not create duplicates.
- Use deterministic gates and a small decision table; no universal weighted score.
- Never select more than two delegated workers.
- Keep `DIRECT` as the explicit zero-delegated-worker path.
- Treat provider/model selection as deferred live-data resolution.
- Record local serialized-byte values only as `LOCAL_SERIALIZATION_PROXY`.
- Run Anvien impact/file-detail before editing existing symbols and detect-changes before any implementation commit.
- Preserve official `.19`, the C17 `.20` candidate, C08/C09, canonical eight identities, and AESTHETICA boundaries.
- Stop at `PASS`, `BLOCKED`, or `REJECT`; do not begin C19.

## Problem

C15 and C17 already provide bounded direct, delegated, sequential, and parallel execution primitives, but no single auditable policy currently derives the abstract requirement before provider/model resolution. Without that policy, a beginner-facing continuation flow cannot choose the smallest sufficient context, worker count, reasoning requirement, and verification burden from task evidence.

## Scope

- Recover and classify existing adaptive surfaces.
- Add one small pure policy module if the gap remains confirmed.
- Add frozen AO1-AO20 fixtures and deterministic tests, including naive-policy comparison and quality non-regression assertions.
- Bind the module into package selection and durable C18 roadmap provenance.
- Build and verify a new unpromoted candidate only if runtime source changes are required.

## Non-Goals

- Provider/model optimizer, pricing or token telemetry, online self-tuning, reinforcement learning, adaptive quorum, swarm execution, background autonomy, remote bridge, new cache/RAG/repo graph, Capsule 3, live delegation/parallel certification, or promotion of any candidate.

## Acceptance Criteria

- AO1-AO20 deterministic fixtures pass with expected abstract requirements.
- Naive alternatives are compared only on the frozen fixture set; no universal superiority claim is made.
- Policy provenance explains the selected path and blocked conditions without hidden reasoning.
- Quality/evidence/permission/owner gates are never weakened.
- Existing C15/C17 tests and affected regression gates remain passing.
- If source changes exist, candidate lineage remains based on official `.19`, official SHA is unchanged, C17 candidate SHA remains preserved, and the new candidate is unpromoted.
- Supervisor review returns exactly `PASS` or a documented `REJECT`/blocker.

## Checklist

- [x] P0-A: Recover durable state and classify all existing adaptive surfaces.
  - Acceptance: `actual-status.md` contains evidence-backed classifications and downstream decisions.

### P1: Implement and evaluate the minimum policy

- Phase Goal: add only the missing abstract policy and controlled evaluation.
- Phase Boundary:
  - In scope: one runtime module, frozen AO fixtures, tests, package inventory, policy evidence.
  - Out of scope: changing existing router/executors or adding provider/model logic.
- Ordered Slice List:
  - P1-A: Add provider-neutral orchestration policy module.
  - P1-B: Add AO1-AO20 fixture matrix, naive comparison, and tests.
  - P1-C: Bind package inventory and durable C18 governance provenance.

- [x] P1-A: Add provider-neutral orchestration policy module
  - Goal: derive `worker_strategy`, `context_class`, `reasoning_class`, and `verification_class` from a compact validated task profile.
  - Scope Boundary:
    - Editable: `.p2p/system/p2p_capabilities/orchestration_policy.py`.
    - Inspect-only: C06 context, C10 evidence/permissions, C11 task state, C12 budgets, C15 delegation, C17 parallel economy, Decision Trace, provider seams.
    - Preserve-only: existing router and execution controllers.
    - Out of scope: provider/model resolution and runtime execution.
  - Pre-flight Questions:
    - Data source: structured task profile only.
    - Display permission: policy output is audit data, not an owner bypass.
    - DB/data flow: N/A; pure function with no persistence.
    - UI flow: N/A; beginner-facing caller remains unchanged.
    - Docker/runtime: N/A; offline Python runtime.
    - Behavior test: AO fixture assertions and provenance validation.
    - Cleanup/quarantine: tests use repo-local `.tmp` only where needed.
    - External side effects: none.
  - Work Steps:
    1. Implement validated profile dimensions and ordered deterministic gates.
       - Evidence target: source inspection and focused unit tests.
    2. Emit abstract requirement, explicit reason codes, seam references, and provider/model deferred status.
       - Evidence target: provenance assertions with no private-reasoning fields.
  - Implementation Gate: new file only; no existing function/class edit required.
  - Acceptance: policy is deterministic, bounded to `DIRECT`/`ONE_WORKER`/`TWO_WORKERS`/`BLOCKED`, and provider-neutral.
  - Actual-status Update: `missing -> correct` for the abstract adaptive policy surface.
  - Commit Boundary: commit after focused acceptance when repository commit tooling is available; otherwise record no-git state.

- [x] P1-B: Add AO1-AO20 fixture matrix, naive comparison, and tests
  - Goal: prove the policy on the required controlled cases and compare against naive alternatives without claiming universal optimality.
  - Scope Boundary:
    - Editable: `tests/fixtures/p2p-c18-adaptive-orchestration.json`, `tests/test_p2p_adaptive_orchestration.py`.
    - Inspect-only: existing C15/C17 fixtures and tests.
    - Out of scope: live host execution and real model telemetry.
  - Work Steps:
    1. Freeze 20 isolated cases with expected abstract outputs and gate notes.
    2. Run policy, naive-policy, provenance, provider-boundary, owner-gate, quorum, and quality non-regression assertions.
  - Implementation Gate: tests must exercise behavior, not only constants.
  - Acceptance: all AO cases pass; no extra worker path exceeds two; deterministic verifier is preferred where sufficient.
  - Actual-status Update: `unbound -> bound-correct` for controlled adaptive evaluation.
  - Commit Boundary: commit after focused acceptance.

- [x] P1-C: Bind package inventory and durable C18 governance provenance
  - Goal: ensure the new runtime module is packaged and the development-control projection records exactly what C18 proves and does not prove.
  - Scope Boundary:
    - Editable: `scripts/package_release.py`, `governance/development-control.json`, C18 plan/evidence/benchmark/status files.
    - Inspect-only: official `.19` artifact and C17 candidate artifact.
    - Preserve-only: release approval and promotion records.
  - Work Steps:
    1. Add only the new module to foundation runtime inventory after impact evidence.
    2. Record C18 roadmap status, provenance, candidate ancestry, and future seams.
  - Implementation Gate: package/lifecycle gates and lineage checks must be prepared before candidate build.
  - Acceptance: package selection includes the module; official `.19` and C17 SHA remain exact; no promotion occurs.
  - Actual-status Update: governance and packaging rows refreshed.
  - Commit Boundary: commit after governance/package source validation.

### P2: Verify, supervise, and close

- [x] P2-A: Run focused and affected regression gates
  - Run AO tests, C17 cognitive economy/parallel, C15 delegation, C12 execution, C11 task state, C10 evidence/permissions, C13/Design Intelligence, Decision Trace, governance, doctor, and security/secret checks.
  - Build a new unpromoted candidate only if required by changed runtime source; record package hash.

- [x] P2-B: Supervisor acceptance review
  - Review source, actual-status, evidence, benchmark, governance, lineage, and all C18 boundaries independently.
  - Acceptance: supervisor report is `PASS`; otherwise record the blocker and stop.

- [x] P2-C: Close and stop
  - Update all four plan artifacts, final durable state, execution ledger/workflow report, and final status.
  - Do not start C19 or promote automatically.

## Risk Notes

- Packaging and lifecycle have a high/critical blast-radius warning because the manifest inventory feeds multiple flows; change is a one-entry additive edit and receives full package verification.
- The policy may be overfit to synthetic fixtures; results are bounded evidence only, not a universal optimizer proof.
- Host delegation and parallel execution remain `NOT_CERTIFIED` because no native host receipt is available.
- Official `.19` and the C17 candidate are protected from overwrite.
