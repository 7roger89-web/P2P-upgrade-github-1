# Real Context-Efficiency A/B Benchmark & Quality Non-Inferiority Certification Plan

## Metadata

- Date: `2026-08-14`
- Status: `blocked`
- Plan: `docs/plans/2026-08-14-real-context-efficiency-ab-quality-noninferiority/2026-08-14-real-context-efficiency-ab-quality-noninferiority-plan.md`
- Evidence: `docs/plans/2026-08-14-real-context-efficiency-ab-quality-noninferiority/2026-08-14-real-context-efficiency-ab-quality-noninferiority-evidence.md`
- Benchmark: `docs/plans/2026-08-14-real-context-efficiency-ab-quality-noninferiority/2026-08-14-real-context-efficiency-ab-quality-noninferiority-benchmark.md`
- Actual status: `docs/plans/2026-08-14-real-context-efficiency-ab-quality-noninferiority/2026-08-14-real-context-efficiency-ab-quality-noninferiority-actual-status.md`

## Goal

Determine whether the existing P2P context-efficiency candidate can be compared with the official .15 execution contract using genuine paired Codex host/provider task execution, while preserving quality, evidence, safety, and project-state integrity. This is measurement only. If two executable conditions are not present and observable, the plan must stop as `BLOCKED` without fabricating A/B results or adding architecture.

## Rules

- Complete P0 actual status before implementation work.
- Reuse the existing canonical 12-scenario benchmark and its frozen fixtures; do not create a second suite.
- Do not count proxy or synthetic trials as real benchmark evidence.
- Every scored trial must prove `runtime_task_execution=true` and record its execution identity and acceptance evidence.
- Keep the task, fixture, permissions, network availability, acceptance criteria, and maximum technical capability equivalent across A and B.
- Record only host/provider telemetry that is actually exposed. Use `UNKNOWN` for unavailable token, cache, cost, provider, timing, context, or operation measurements.
- Define the quality rubric and non-inferiority margin before examining aggregate results.
- Do not implement Capsule 2.0, Knowledge Delta 2.0, Memory Hub, CodeGraph, DAG, scheduler, leases, worker pool, router, meta-agent, or new evidence memory.
- If minimal instrumentation materially changes runtime behavior, classify the experiment contaminated and stop.
- Preserve INTENT != PERMISSION and READ != WRITE != LOG != PERSIST != EGRESS.
- Preserve exactly eight canonical identities and quorum denominator 8.
- No package promotion, release, deployment, external communication, or mutation of App Game Truyện.
- Update each checklist item immediately when completed or blocked.
- Record evidence and measured values as work completes.
- Run Anvien detect-changes only if implementation work occurs; this plan is expected to be audit-only.

## Problem

The existing 12-scenario/48-trial evidence is explicitly a deterministic proxy suite with `runtime_task_execution=false`. It proves evaluator contract integrity but does not prove live model quality, token or cache savings, provider cost, wall-clock improvement, or real delegation behavior. The new claim requires a genuine A/B execution path, and the repository may not contain two runnable conditions or host telemetry access sufficient to support that claim.

## Scope

- Recover the canonical benchmark definition, conditions, fixture/evidence hashes, and prior limitations.
- Inspect the actual evaluation helper and runtime surfaces for a live A/B executor.
- Inspect current Codex host tool authority for real task execution and per-trial telemetry.
- Define the fixed quality rubric, pre-registered non-inferiority margin, paired-trial protocol, confounder policy, and failure taxonomy.
- Execute the existing 12 scenarios only if both conditions are genuinely executable and equivalent.
- Report per-scenario and aggregate quality/efficiency results with UNKNOWN values where necessary.
- Review capability preflight, bounded retries, logical integration ownership, context loadout, handoff, compaction/resume, freshness, requirement/evidence linkage, and security boundaries as observed.

## Non-Goals

- No runtime behavior change unless a minimal, non-material observation fix is proven necessary.
- No new context contract, worker return contract, memory system, scheduler, queue, DAG, agent, router, or provider integration.
- No synthetic substitution for live trials.
- No use of prior proxy numbers as live token/cost/time evidence.
- No changes to official .15, candidate .16-r2, release artifacts, immutable baselines, or user projects.

## Requirements

1. Recover the exact canonical scenario IDs and task classes.
2. Verify Condition A and Condition B are separately executable; otherwise stop `BLOCKED` before trials.
3. Use paired, isolated execution with identical task inputs and capabilities.
4. Record model/provider confounding rather than hiding it.
5. Use a fixed 0–4 rubric: Q1 correctness, Q2 requirement coverage, Q3 evidence quality, Q4 integration awareness, Q5 regression awareness, Q6 feasibility, Q7 scope discipline, Q8 unsupported-claim avoidance, Q9 residual-risk identification, Q10 beginner usefulness.
6. Pre-register non-inferiority as B aggregate mean >= A aggregate mean - 0.25 points on the 0–4 mean, with no critical acceptance or safety failure. This threshold is not applied if no real trials run.
7. Report main-context effects separately from total-system effects.
8. Keep historical proxy evidence labeled historical and non-live.
9. Produce an independent supervisor verdict that reviews the blocker or result without treating the proposed optimization as self-certifying.

## Acceptance Criteria

- P0 actual status is complete and evidence-backed.
- The canonical suite and exact 12 scenarios are recovered without duplication.
- Executability of both conditions is proven or the plan stops `BLOCKED`.
- No fake A/B or invented telemetry is present.
- If real trials run, all 12 scenarios have paired evidence and per-scenario quality/efficiency records; otherwise all 12 are explicitly marked not executed with the same blocker.
- Quality scoring and non-inferiority threshold were fixed before aggregate results.
- Capability, budget, failure, freshness, permission, and canonical quorum checks are reported.
- No source/runtime changes occur unless separately justified and classified for contamination.
- Supervisor report gives exactly one independent `PASS` or `REJECT` verdict on the benchmark claim or blocker.

## Checklist

- [x] P0-A: Complete actual status before implementation work.
  - Goal: establish whether the canonical suite, two executable conditions, host execution path, and telemetry authority exist in the current repository and host.
  - Work Steps: inspect the attached Goal, applicable instructions, canonical suite metadata, fixture/evidence hashes, evaluation helper commands, runtime execution markers, and available host tools; classify every relevant surface; update later phase decisions from evidence.
  - Implementation Gate: no runtime editing or benchmark trial begins until actual status records the condition-executability decision and the available telemetry authority.
  - Acceptance: actual status identifies the canonical suite, A/B condition state, live-execution state, telemetry state, and any hard blocker with exact evidence IDs.

### P1: Real paired benchmark eligibility and execution

- Phase Goal: run the existing 12-scenario paired benchmark only when the repository and host can execute both conditions without material instrumentation or confounding.
- Phase Boundary:
  - In scope: condition/runtime eligibility, host capability inspection, fixed rubric, paired execution if eligible, honest telemetry, quality review, and aggregate classification.
  - Out of scope: new runtime architecture, prompt/context redesign, new workers/routers, release promotion, and user-project mutation.
  - Dependencies: completed P0 actual status; exact candidate binding; available host/provider execution surface.
- Phase Implementation Rule: do not implement `P1` directly. Perform only the audit slice below; if eligibility fails, mark P1 blocked and do not create a substitute runner.
- Ordered Slice List:
  - P1-A: Verify executable conditions and telemetry authority; execute or hard-stop the canonical paired benchmark.
  - P1-B: remove (no second implementation slice is valid after a hard-stop; any instrumentation would be a separate contaminated experiment).

- [x] P1-A: Verify executable conditions and telemetry authority; execute or hard-stop the canonical paired benchmark.
  - Goal: obtain real paired evidence or a defensible `BLOCKED` result.
  - Scope Boundary:
    - Editable: audit-plan evidence artifacts only; no runtime source.
    - Inspect-only: `scripts/p2p_eval.py`, `.p2p/evals/`, runtime contracts, host/tool surface, candidate metadata, and prior reports.
    - Preserve-only: official .15, candidate .16-r2, frozen fixtures, canonical suite, source-of-truth state, permissions, and eight-agent identity set.
    - Out of scope: all new runtime architecture and all user projects.
  - Non-Goals: no Capsule 2.0, Knowledge Delta implementation, Memory Hub, scheduler, agent swarm, provider integration, or synthetic live-trial substitute.
  - Pre-flight Questions:
    - Data source: canonical suite, frozen fixture, current source/runtime, and host tool metadata.
    - Display permission: not applicable; report only evidence already within task scope.
    - DB read flow: N/A; no application database is touched.
    - DB write flow: N/A; only isolated audit artifacts may be written.
    - Render location: N/A; no UI is changed.
    - UI behavior flow: N/A; C6/C7 are fixture scenarios, not product UI mutation.
    - Docker runtime: N/A; this is not an app-runtime change.
    - Playwright target: N/A; no UI/runtime claim is being implemented.
    - Behavior test: `p2p_eval.py validate`/`gate` are contract checks, not live execution proof.
    - Cleanup/quarantine: preserve-only canonical inputs; audit files are confined to this plan directory and reports.
    - External side effects: none; no network/provider invocation unless an already-authorized real benchmark surface exists.
    - N/A notes: a missing live A/B executor is a hard stop, not permission to create one.
  - Work Steps:
    1. Recover the exact canonical suite, scenarios, conditions, hashes, and prior proxy limitations; inspect the helper implementation and host capability surface.
       - UI flow check: N/A; record why.
       - DB/data flow check: verify isolated fixture/evidence paths and no protected project mutation.
       - Render location check: N/A; evidence goes to the plan ledger and supervisor report.
       - Mini QA for each completed implementation slice (MUST): no implementation slice; perform command-level validation and supervisor review instead.
       - Evidence target: `E0-P0A-*` and `E1-P1A-*` source/command/authority records.
    2. If and only if both conditions are live and equivalent, execute the canonical paired trials, score blinded outputs with the fixed rubric, decode identities after scoring, and calculate only compatible metrics; otherwise record `BLOCKED` and mark every scenario not executed.
       - UI flow check: N/A; no UI surface is changed.
       - DB/data flow check: verify start/end isolated state and evidence hashes for every real trial if any.
       - Render location check: N/A; use benchmark ledger for measurements and evidence ledger for validation.
       - Mini QA for each completed implementation slice (MUST): no source implementation; independent review is the required quality control.
       - Evidence target: per-scenario records, telemetry authority table, quality rubric, non-inferiority calculation if eligible, or hard-stop proof if blocked.
  - Implementation Gate:
    - Before editing any runtime target, Anvien impact/file-detail evidence would be required; no runtime target is authorized by this plan.
    - Both A and B must be genuinely executable, `runtime_task_execution=true` must be provable, and observation must not require material behavior change.
    - If any gate fails, do not run fake trials; classify P1 `BLOCKED`.
  - Acceptance:
    - Source: the helper/runtime inspection proves the condition state and no forbidden architecture was added.
    - Runtime/UI: all scored trials are real host execution, or none are counted and the blocker is explicit.
    - DB/data: no protected fixture, state, release, or user-project mutation.
    - Behavior test: existing eval contract validation may pass but cannot substitute for runtime evidence.
    - Cleanup/quarantine: audit artifacts remain isolated under this plan/report scope.
    - Evidence IDs: `E0-P0A-*`, `E1-P1A-*`, and supervisor report.
    - Actual-status rows refreshed: canonical suite, A/B executability, telemetry, trial state, release impact.
  - Evidence Targets: canonical suite JSON, fixture/evidence hashes, helper source/help output, runtime markers, host capability inventory, candidate identity, validation output, and supervisor review.
  - Actual-status Update: transition any proxy-only or missing live-execution surfaces to `fake-or-stub`, `missing`, or `blocked` as proven; preserve correct canonical and safety surfaces.
  - Commit Boundary: no implementation commit; audit artifacts may be recorded without promoting or changing runtime source.
- [x] Pn-A: Call supervisor for the completed or blocked-plan acceptance loop.
  - Goal: independently verify that the benchmark claim is accepted only to the extent proven, and that a hard stop was not bypassed.
  - Work Steps:
    1. Review the attached Goal, plan, actual status, evidence, benchmark ledger, source/runtime inspection, and current artifacts.
    2. Verify the condition-executability and `runtime_task_execution` claim independently.
    3. If the supervisor finds an evidence or scope defect, correct only the audit record and re-review; do not implement runtime behavior under the review.
  - Implementation Gate: P1 is completed or explicitly blocked and all required evidence is present.
    - Acceptance: supervisor report contains exactly one `PASS` or `REJECT` verdict and states whether certification is possible.
- [x] Pn-B: Remove dead work created during this plan.
  - Goal: ensure the final audit contains no fake trials, placeholder metrics, duplicate suite, or misleading live claims.
  - Work Steps:
    1. Inspect plan-created files and any output created during this goal.
    2. Remove only dead artifacts created by this plan; preserve historical canonical evidence and protected release files.
    3. Verify no invented token, cache, cost, provider, timing, or trial result remains.
  - Implementation Gate: only plan-created artifacts may be removed; canonical and baseline artifacts are preserve-only.
    - Acceptance: final audit package contains only current evidence, explicit UNKNOWNs, and historical references labeled as such; no dead trial or placeholder artifact was created.
- [x] Pn-C: Close the plan.
  - Goal: record final evidence, benchmark status, supervisor result, worktree state, and release impact.
  - Work Steps:
    1. Run the relevant validation commands for the audit artifacts and canonical suite.
    2. Do not substitute build or proxy validation for live A/B proof.
    3. Record files changed, security/canonical checks, supervisor report, and final blocked/pass status.
  - Implementation Gate: Pn-A and Pn-B pass or record the hard blocker.
  - Acceptance: final status is `PASS` only with real paired evidence; otherwise `BLOCKED` with no false certification. Current status: `BLOCKED` because P1's executable-condition gate failed.

## Risk Notes

- The principal risk is mistaking a valid proxy evaluator for a live model/provider execution path. The stop rule prevents this.
- Host/provider token, cache, cost, wall-time, and child-agent telemetry may be unavailable; these remain UNKNOWN.
- Any attempt to add instrumentation that alters prompts, routing, retrieval, delegation, or state would contaminate the experiment and must be stopped and classified.
- Prior PASS evidence for .15 or .16-r2 is historical and cannot prove live A/B behavior after candidate changes.
- No user decision is required to accept an honest BLOCKED result; a future goal may need to add an explicitly approved, minimally invasive observation surface before rerunning.
