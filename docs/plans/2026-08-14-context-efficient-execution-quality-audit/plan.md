# Context-Efficient Execution & Quality Audit — Foundation for Durable Orchestration Plan

## Metadata

- Date: `2026-08-14`
- Status: `blocked`
- Plan: `docs/plans/2026-08-14-context-efficient-execution-quality-audit/plan.md`
- Evidence: `docs/plans/2026-08-14-context-efficient-execution-quality-audit/evidence.md`
- Benchmark: `docs/plans/2026-08-14-context-efficient-execution-quality-audit/benchmark.md`
- Actual status: `docs/plans/2026-08-14-context-efficient-execution-quality-audit/actual-status.md`

## Goal

Determine from runtime evidence whether P2P can reduce execution context, raw
return propagation, duplicate retrieval, unnecessary delegation, and wasted
attempts without reducing correctness, evidence quality, acceptance coverage,
safety, project-state integrity, or beginner usefulness.

The audit is read-only with respect to P2P runtime behavior. Any runtime
change remains a separate, approval-gated follow-up Goal.

## Rules

- Preserve official `8.4.7-C-codex.15` and its ZIP artifact unchanged.
- Do not reopen AESTHETICA research. Preserve primary `p2p-uiux`, optional
  AESTHETICA, canonical count `8`, denominator `8`, and quorum `8/8`.
- Do not build a durable queue, DAG, scheduler, lease system, worker pool,
  daemon, kanban, Code-Impact integration, new router, or meta-agent.
- Use existing FACT_LEDGER, Live Specs, Decision Trace, Execution Ledger,
  Approvals, and Evidence as the only authority chain.
- Never invent token, cache, provider-cost, or model wall-time values.
- A character/byte count is a deterministic serialization proxy only.
- A proxy benchmark cannot certify real worker quality or non-inferiority.
- Use isolated synthetic fixtures and keep App Game Truyện, Logistics, the
  official ZIP, and protected baseline paths preserve-only.

## Problem

The current project has a Goal Contract, CAPSULE, evidence reuse, context
pointer, trust, readiness, approval, no-progress, and Decision Trace surfaces,
but their end-to-end execution binding is incomplete. The local workflow
selects agent metadata without exposing a worker/provider executor. Host-level
token, cache, tool-output, and provider telemetry is not available. The
workflow also prioritizes an installed UI/UX evaluator that does not implement
the `design` interface expected by `p2p_workflow.py`.

## Scope

In scope:

- Official `.15` baseline and current development-source runtime map.
- Goal → routing → capsule/context → executor → evidence → return → state →
  done-check flow.
- Context-waste forensics and telemetry-authority classification.
- Capsule 2.0, Knowledge Delta, capability/readiness/permission/budget
  preflight, intent/permission, effect authority, execution modes, and
  parallelism restraint.
- Twelve frozen synthetic scenarios, two isolated trials per condition, and
  contract-level A/B proxy measurements.
- Current unit, governance, Decision Trace, capability, beginner, secret, and
  eval validation evidence.

Out of scope:

- Any P2P runtime/package implementation or release `8.4.7-C-codex.16`.
- Real provider or child-agent execution unavailable in this host.
- Durable orchestration and external integration.
- App Game Truyện, Logistics, official ZIP, v5 artifact, and user projects.

## Requirements

- Map CE1 and identify actual implementation rather than relying on docs.
- Classify each waste source as MATERIAL_WASTE, MINOR_WASTE,
  EXPECTED_CONTEXT, or UNKNOWN.
- Classify every candidate metric as EXACT_HOST_TELEMETRY,
  EXACT_P2P_TELEMETRY, DETERMINISTIC_PROXY, or UNAVAILABLE/UNKNOWN.
- Evaluate H1–H10 independently and preserve the quality-first rule.
- Execute at least 12 equivalent fixture scenarios with two isolated trials per
  condition where the available runtime permits.
- Keep contract-proxy results visibly separate from real task-quality results.
- Produce an independent supervisor verdict before closure.

## Acceptance Criteria

- CE1–CE12: current flow, waste, telemetry, capsule, delta, preflight,
  authority, modes, and parallelism are evidence-backed.
- CE13: twelve or more frozen scenarios and paired trial records exist.
- CE14–CE16: A/B quality and efficiency are accepted only when quality is
  observed with equivalent acceptance and authoritative metrics.
- CE17–CE22: H1–H10 decisions and adoption boundary are explicit, with no
  second source of truth or forbidden orchestration.
- CE23–CE26: relevant regression, canonical, and security checks are recorded
  with their real PASS/FAIL/BLOCKED status.
- CE27: supervisor produces one explicit PASS or REJECT verdict.
- Overall result is `PASS` only if real A/B quality non-inferiority is proven;
  otherwise it is `BLOCKED` with the exact evidence gap.

## Checklist

- [x] P0-A: Complete actual status before implementation work.
  - Goal: establish the real current state.
  - Work Steps: inspect the runtime, installed capability surfaces, governance,
    tests, official artifact, and graph relationships; record missing or
    unbound surfaces.
  - Implementation Gate: no implementation was started.
  - Acceptance: actual status records the helper mismatch, unavailable host
    telemetry, incomplete worker binding, and protected baseline.

### P1: Runtime and context audit

- Phase Goal: map current execution and identify context/evidence waste.
- Phase Boundary:
  - In scope: workflow, capsule, context pointers, evidence, trace, routing,
    approval, no-progress, and state contracts.
  - Out of scope: changing any runtime contract.
  - Dependencies: current source, specs, Anvien graph, and existing state.
- Phase Implementation Rule: audit-only; no implementation slice is opened.
- Ordered Slice List:
  - P1-A: map the current runtime flow.
  - P1-B: classify waste, telemetry, permissions, and execution modes.

- [x] P1-A: Map the current runtime flow.
  - Goal: trace the actual Goal → DONE path from source.
  - Scope Boundary: inspect-only for `scripts/p2p_workflow.py`,
    `.p2p/system/p2p_capabilities`, governance, and state.
  - Acceptance: flow map and unbound worker/candidate surfaces recorded in
    `evidence.md`.
  - Evidence Targets: `E1-P1A-FLOW1..E1-P1A-FLOW8`.
  - Actual-status Update: capsule is a continuation index; context pointers
    are standalone metadata resolution; workflow does not execute workers.

- [x] P1-B: Perform context-waste and authority forensics.
  - Goal: distinguish observed waste from unknown host behavior.
  - Scope Boundary: inspect-only; no broad security architecture.
  - Acceptance: all twelve waste classes and metric authorities are classified.
  - Evidence Targets: `E1-P1B-WASTE1..E1-P1B-TELEM5`.
  - Actual-status Update: exact P2P state/fingerprint evidence exists, but host
    token/cache/provider/worker telemetry is unavailable.

### P2: Paired benchmark

- Phase Goal: run the smallest honest A/B benchmark that the host can support.
- Phase Boundary:
  - In scope: frozen synthetic C1–C12 fixtures and contract-level A/B shapes.
  - Out of scope: claiming model quality or runtime cost from proxies.
  - Dependencies: p2p-eval schema v2 and two trials per condition.
- Phase Implementation Rule: benchmark artifact only; no runtime edits.
- Ordered Slice List:
  - P2-A: freeze fixtures and execute paired contract proxies.
  - P2-B: perform quality non-inferiority review.

- [x] P2-A: Execute C1–C12 paired contract proxy.
  - Goal: exercise current `.15` contract shape and candidate Capsule/Delta/
    preflight shape using the same isolated inputs.
  - Acceptance: 12 cases × 2 trials × 2 conditions; fixture and evidence SHA-256
    recorded; p2p-eval validate and gate PASS for the proxy artifact.
  - Evidence Targets: `E2-P2A-BENCH1..E2-P2A-BENCH5`.
  - Actual-status Update: 48 proxy trials recorded; Q1–Q12 remain UNKNOWN.

- [ ] P2-B: Complete real A/B quality review.
  - Goal: compare correctness, evidence, acceptance, safety, regression, and
    beginner usefulness on real task outputs.
  - Implementation Gate: requires a host/provider/worker execution surface
    with equivalent access and authoritative telemetry.
  - Acceptance: blinded independent review and non-inferiority result.
  - Status: blocked by missing worker/provider execution and host telemetry.

### P3: Validation and safety

- Phase Goal: validate the untouched baseline and audit artifacts.
- Phase Boundary: no source/runtime changes.
- Dependencies: P1 and P2 records.

- [x] P3-A: Run regression, governance, capability, trace, beginner, eval, and
  secret checks.
  - Acceptance: command outcomes are recorded without converting warnings or
    package failures into PASS.
  - Evidence Targets: `E3-P3A-TEST1..E3-P3A-SECURITY4`.

- [x] P3-B: Confirm canonical safety and protected baseline.
  - Acceptance: exact eight identities, denominator 8, full quorum 8/8,
    AESTHETICA optional/noncanonical, official artifact hash unchanged.
  - Evidence Targets: `E3-P3B-CANON1..E3-P3B-BASELINE3`.

### P4: Closure

- [x] P4-A: Write the audit report and stop at the first honest terminal state.
  - Goal: report PASS/BLOCKED/REJECT with evidence and no optional hardening.
  - Acceptance: supervisor verdict exists; no runtime change or release is
    created.
  - Evidence Targets: `E4-P4A-REPORT1..E4-P4A-SUPERVISOR2`.

## Risk Notes

- The contract proxy has lower serialized context bytes for B, but this is not
  a token measurement and may omit context needed for real correctness.
- Existing `.p2p/evals/suite.json` is a different project-specific UI/UX suite;
  it must not be reused as evidence for this audit.
- `scripts/doctor.py --package .` fails because the development checkout does
  not expose the expected root package payload paths. This is a packaging/source
  layout blocker, not a reason to edit the official artifact.
- No Git repository is present, so no commit/diff claim can be made.
