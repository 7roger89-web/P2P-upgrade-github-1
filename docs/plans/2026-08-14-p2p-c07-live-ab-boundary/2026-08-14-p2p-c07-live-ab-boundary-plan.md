# P2P-C07 Supported Live A/B Context Boundary Plan

## Metadata

- Date: `2026-08-14`
- Status: `complete`
- Plan: `docs/plans/2026-08-14-p2p-c07-live-ab-boundary/2026-08-14-p2p-c07-live-ab-boundary-plan.md`
- Evidence: `docs/plans/2026-08-14-p2p-c07-live-ab-boundary/2026-08-14-p2p-c07-live-ab-boundary-evidence.md`
- Benchmark: `docs/plans/2026-08-14-p2p-c07-live-ab-boundary/2026-08-14-p2p-c07-live-ab-boundary-benchmark.md`
- Actual status: `docs/plans/2026-08-14-p2p-c07-live-ab-boundary/2026-08-14-p2p-c07-live-ab-boundary-actual-status.md`

## Goal

Create the smallest supported boundary that takes the already implemented
`BASELINE_COMPAT` or `CONTEXT_EFFICIENT_V1` context view and submits that exact
payload to a real supported Codex host/model execution. Bind every trial to its
scenario, context mode, context fingerprint, host identity, captured output,
isolated fixture, and telemetry provenance. Stop after paired C1 and one
non-trivial paired dry-run plus independent Supervisor review.

## Rules

- Complete P0 actual status before implementation work.
- Preserve the official `.15` ZIP and existing `.16-r2` ZIP byte-for-byte.
- Build a new unpromoted candidate only when the C06 behavior is absent from
  `.16-r2`; use the existing package/version mechanism and never overwrite an
  existing artifact.
- Use only supported native Codex host/subagent surfaces. No private RPC,
  AgentControl, patched binary, UI scraping, credential interception, or fake
  provider adapter.
- Reuse the existing context builder, host identity receipt hook, Execution
  Ledger, Goal/evidence contracts, and existing eval/doctor/governance gates.
- `runtime_task_execution=true` is valid only with fresh host-owned execution
  evidence and captured live output. Proxy/local deterministic paths remain
  `false`.
- A/B context payloads must differ in their actual constructed data; a mode
  label alone is not a valid independent variable.
- Unknown provider/model/token/cost telemetry is valid only when represented as
  `UNKNOWN` with an explicit authority label. Local byte counts remain
  `LOCAL_SERIALIZATION_PROXY`.
- Use only repository-local `.tmp` roots for temporary extraction, fixtures,
  receipts, and outputs. Never mutate App Game Truyện, Logistics_App_Copy, or a
  user production project.
- The workspace has no `.git`; use artifact SHA-256, source hashes, runtime
  locks, and fixture fingerprints instead of fabricated commits.
- Do not run the full 12-scenario live benchmark or add memory, DAG, scheduler,
  recovery, background execution, or another router/truth system.

## Problem

The reviewed development source now has the deterministic C06 context primitive,
but the immutable `.16-r2` candidate predates it. The existing evaluator is a
local proxy and correctly records `runtime_task_execution=false`. The project
does have a supported native Codex child/subagent surface and an existing
official host identity receipt hook, but no boundary currently connects an
actual C06 payload to a live host execution or captures a safe live receipt.

## Scope

- Inspect and bind C06 source state to a new immutable candidate when required.
- Verify official `.15` and `.16-r2` immutability and isolate A/B roots.
- Add one small live-trial contract around the existing context builder.
- Reuse the existing host identity receipt path and append live trial evidence
  to the existing Execution Ledger rather than creating a second store.
- Capture blinded-safe output artifacts and allow-listed telemetry provenance.
- Run exactly four paired dry-run trials: C1 A/B, then one non-trivial
  canonical scenario A/B.
- Run affected focused tests, full P2P regression, Decision Trace, governance,
  capability, doctor, and secret/lifecycle checks; then request Supervisor review.

## Non-Goals

- No quality, efficiency, token-reduction, cost, or non-inferiority claim.
- No provider API integration or estimation of provider telemetry.
- No release promotion, deployment, publication, or interactive approval.
- No full 12-scenario live certification.
- No mutation of real business projects or protected release artifacts.
- No new database, telemetry truth store, evaluation framework, memory system,
  swarm, scheduler, task DAG, or recursive delegation.

## Requirements

1. The C06 source behavior is bound to immutable state; official `.15` and
   `.16-r2` remain unchanged.
2. A and B resolve to the two existing deterministic context modes and their
   fingerprints are different for each trial.
3. The live boundary validates known scenarios, exact context fingerprints,
   source bindings, fixture fingerprints, artifact state, and execution config.
4. A real supported host receipt and actual output are required before a live
   receipt can set `runtime_task_execution=true`.
5. The receipt contains the requested fields where observable and uses
   `UNKNOWN` for missing provider-owned fields.
6. Output is captured outside the receipt so later blinded X/Y review can use it
   without relying on condition labels.
7. Proxy execution cannot self-promote to live status; stale receipts fail
   closed; secret-looking fields are rejected or omitted.
8. A/B fixture/state/output isolation and no cross-condition memory leakage are
   proven by focused tests.
9. The same profile/route and requested settings are used for A/B pairs, with
   observed settings recorded separately and confounders disclosed.
10. C1 paired live execution and one non-trivial paired live execution both
    succeed before the Goal can pass.

## Acceptance Criteria

- `SUPPORTED_LIVE_AB_BOUNDARY_READY` is proven, or the Goal stops at a named
  real blocker without a fake live receipt.
- Exact candidate version, path, and SHA-256 are recorded when a candidate is
  created; no existing artifact is overwritten or promoted.
- Each live trial proves `scenario -> mode -> context fingerprint -> supplied
  host request -> host execution ID -> captured output`.
- `runtime_task_execution=true` appears only in receipts with fresh supported
  host evidence and output capture.
- Telemetry fields are allow-listed and each has an authority class from
  `HOST`, `PROVIDER`, `LOCAL_MONOTONIC_TIMER`, `DETERMINISTIC_RUNTIME`,
  `LOCAL_PROXY`, or `UNKNOWN`.
- Focused tests, full affected regression, package/lifecycle checks when a
  candidate exists, and an independent Supervisor report are available.

## Checklist

- [x] P0-A: Complete actual status before implementation work.
  - Goal: establish the real C06, artifact, host, proxy, isolation, and
    governance baseline.
  - Work Steps: inspect current source, compare immutable ZIP members, verify
    artifact hashes, inspect supported host receipts/configuration, and record
    all preserve-only, editable, missing, and blocked surfaces.
  - Implementation Gate: actual-status has a final P0 decision and evidence
    IDs; no production implementation begins from assumptions.
  - Acceptance: P0 records `.16-r2` as pre-C06 and identifies the supported
    native host surface plus the missing live boundary.

### P1: Freeze C06 into immutable candidate

- Phase Goal: create a new unpromoted B candidate only if required, without
  changing `.15` or `.16-r2`.
- Phase Boundary:
  - In scope: isolated candidate source copy, canonical version bump, package
    builder, package verification, doctor, drift, and lifecycle fixtures.
  - Out of scope: live trials, release promotion, and user approval.
  - Dependencies: P0 artifact comparison and current C06 source hashes.
- Phase Implementation Rule: implement `P1-A`, verify it, refresh actual-status
  and evidence, then implement `P1-B` only if the candidate is required.
- Ordered Slice List:
  - P1-A: Confirm C06 absence/presence and freeze source binding.
  - P1-B: Build and verify a new immutable candidate in an isolated root.

- [x] P1-A: Confirm C06 absence/presence and freeze source binding.
  - Goal: prove whether `.16-r2` already contains the reviewed C06 behavior.
  - Scope Boundary:
    - Editable: none; inspection-only.
    - Inspect-only: `.p2p/system/p2p_capabilities/context.py`, package runtime,
      official ZIPs, and C06 reports.
    - Preserve-only: `.15`, `.16-r2`, immutable baseline, user projects.
    - Out of scope: source edits and release operations.
  - Non-Goals: no semantic C06 rewrite and no live execution.
  - Pre-flight Questions:
    - Data source: current development source and ZIP members.
    - Display permission: N/A.
    - DB read flow: N/A; file/artifact inspection only.
    - DB write flow: N/A.
    - Render location: N/A.
    - UI behavior flow: N/A.
    - Docker runtime: N/A; no application UI.
    - Playwright target: N/A; no browser surface.
    - Behavior test: hash and source-marker comparison.
    - Cleanup/quarantine: extraction under `.tmp/p2p-c07-artifact-inspection`.
    - External side effects: none.
    - N/A notes: package artifacts are preserve-only.
  - Work Steps:
    1. Compare C06 source markers and hashes in `.15` and `.16-r2`.
       - UI flow check: N/A.
       - DB/data flow check: verify extraction stays under `.tmp`.
       - Render location check: N/A.
       - Evidence target: `E0-P0A-ART1` and `E0-P0A-ART2`.
    2. Record the candidate decision and exact immutable hashes.
       - UI flow check: N/A.
       - DB/data flow check: preserve-only roots unchanged.
       - Render location check: N/A.
       - Evidence target: `E0-P0A-SRC1` and `E0-P0A-HOST1`.
  - Implementation Gate: the package comparison must show whether C06 is
    present; the current evidence shows it is absent from `.16-r2`.
  - Acceptance:
    - Source: current C06 source is identified and `.16-r2` is pre-C06.
    - Runtime/UI: N/A.
    - DB/data: preserve-only artifacts are unchanged.
    - Behavior test: comparison is reproducible from hashes and package paths.
    - Cleanup/quarantine: inspection roots are repository-local temporary data.
    - Evidence IDs: `E0-P0A-SRC1`, `E0-P0A-ART1`, `E0-P0A-ART2`.
    - Actual-status rows refreshed: C06 binding, candidate, baseline, `.16-r2`.
  - Evidence Targets: source hashes, ZIP hashes, package member hashes, and
    immutable-root preservation checks.
  - Actual-status Update: transition candidate from `unknown` to `required`.
  - Commit Boundary: no Git commit; record SHA-256 checkpoint because the
    workspace has no `.git`.

- [x] P1-B: Build and verify the new immutable candidate.
  - Goal: package the exact reviewed C06 source as the next canonical revision.
  - Scope Boundary:
    - Editable: isolated candidate copy under `.tmp` and new artifact path only.
    - Inspect-only: source truth and existing artifacts.
    - Preserve-only: `.15`, `.16-r2`, immutable baseline, user projects.
    - Out of scope: promotion, publication, and source-root version changes.
  - Non-Goals: do not include live-boundary code unless it is already part of
    the reviewed C06 freeze.
  - Pre-flight Questions:
    - Data source: current development source and package builder.
    - Display permission: N/A.
    - DB read flow: N/A.
    - DB write flow: N/A.
    - Render location: N/A.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: package verification and doctor.
    - Cleanup/quarantine: candidate staging remains under repo `.tmp`.
    - External side effects: new unpromoted ZIP only.
    - N/A notes: Windows install lifecycle fixtures are required when supported.
  - Work Steps:
    1. Copy the source into a fresh candidate root, apply only the canonical
       next revision metadata, and build with `scripts/package_release.py`.
       - UI flow check: N/A.
       - DB/data flow check: verify no state/ledger is copied into the package.
       - Render location check: N/A.
       - Evidence target: `E1-P1B-PACK1`.
    2. Verify package inventory, doctor, drift, fresh install, upgrade from
       `.15`, and same-version reinstall using isolated fixtures.
       - UI flow check: N/A.
       - DB/data flow check: verify state isolation and recoverable backups.
       - Render location check: N/A.
       - Evidence target: `E1-P1B-LIFE1`.
  - Implementation Gate: the builder must not overwrite an existing output and
    the candidate content must match current C06 source before packaging.
  - Acceptance:
    - Source: candidate contains exact C06 context behavior.
    - Runtime/UI: doctor and drift pass.
    - DB/data: lifecycle roots are isolated and fixture-safe.
    - Behavior test: package verification passes.
    - Cleanup/quarantine: all staging is inside `.tmp`.
    - Evidence IDs: `E1-P1B-PACK1`, `E1-P1B-LIFE1`.
    - Actual-status rows refreshed: candidate, package, lifecycle.
  - Evidence Targets: candidate version/path/hash, package doctor, drift,
    lifecycle reports, and rollback path.
  - Actual-status Update: transition candidate/package to `bound-correct`.
  - Commit Boundary: no Git commit; retain candidate and hashes as immutable
    checkpoints without promotion.

  - Completion Evidence: `E1-P1B-PACK1` and `E1-P1B-LIFE1` record candidate
    `8.4.7-C-codex.17`, package/doctor/drift PASS, and repository-local fresh,
    `.15` upgrade, and same-version reinstall PASS results.

### P2: Implement the live-trial boundary

- Phase Goal: add the smallest contract that validates C06 payloads, accepts
  supported host evidence, captures output, and writes one safe receipt shape.
- Phase Boundary:
  - In scope: one standard-library live boundary module, direct tests, and
    minimal integration with the existing ledger/host identity receipt.
  - Out of scope: provider APIs, proxy relabeling, new stores, and orchestration.
  - Dependencies: P1 candidate binding and supported native host surface.
- Phase Implementation Rule: implement `P2-A`, verify it, refresh actual-status,
  then implement `P2-B` only for the real host binding and direct tests.
- Ordered Slice List:
  - P2-A: Live contract, receipt schema, provenance, isolation, stale safety.
  - P2-B: Supported native child execution handoff and host-evidence adapter.

- [x] P2-A: Add the live contract and receipt boundary.
  - Goal: enforce mode/fingerprint/scenario/artifact/fixture binding and
    fail-closed live status.
  - Scope Boundary:
    - Editable: new live boundary module and direct tests.
    - Inspect-only: existing context builder, proxy evaluator, ledger helpers.
    - Preserve-only: canonical proxy suite and existing host hook semantics.
    - Out of scope: provider client or model/token estimator.
  - Non-Goals: no real execution claim from local tests.
  - Pre-flight Questions:
    - Data source: actual `build_context_view` output.
    - Display permission: receipt stores metadata/output pointers only.
    - DB read flow: existing JSONL Execution Ledger.
    - DB write flow: append one live-trial event; no second store.
    - Render location: N/A.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: boundary unit/integration tests.
    - Cleanup/quarantine: temporary isolated roots under `.tmp`.
    - External side effects: no network/provider calls.
    - N/A notes: host adapter is injected and separately proven by live dry-run.
  - Work Steps:
    1. Define allow-listed request/receipt/telemetry contracts and binding
       fingerprints from the existing context view and artifact state.
       - UI flow check: N/A.
       - DB/data flow check: prove source/fixture/condition isolation.
       - Render location check: N/A.
       - Evidence target: `E2-P2A-CONTRACT1`.
    2. Implement output capture and proxy/live fail-closed checks with direct
       tests for unknown mode, stale context, secrets, and contamination.
       - UI flow check: N/A.
       - DB/data flow check: prove no output becomes future context/state.
       - Render location check: N/A.
       - Evidence target: `E2-P2A-TEST1`.
  - Implementation Gate: run Anvien file-detail/impact on every existing symbol
    touched; no live flag can be produced without host evidence.
  - Acceptance:
    - Source: contract is standard-library-only and reuses existing truth paths.
    - Runtime/UI: proxy remains false; host evidence is required for true.
    - DB/data: receipt/output isolation and stale binding pass.
    - Behavior test: every listed focused test passes.
    - Cleanup/quarantine: safe roots only.
    - Evidence IDs: `E2-P2A-CONTRACT1`, `E2-P2A-TEST1`.
    - Actual-status rows refreshed: receipt, telemetry, isolation, security.
  - Evidence Targets: source review, Anvien impact, direct tests, and hashes.
  - Actual-status Update: transition live boundary from missing to partial.
  - Commit Boundary: hash checkpoint after verification; no fabricated commit.

  - Completion Evidence: `E2-P2A-CONTRACT1` and `E2-P2A-TEST1` record the
    standard-library boundary, exact receipt fields, provenance map, and six
    focused fail-closed tests.

- [x] P2-B: Bind supported native child execution.
  - Goal: use the current supported Codex child/subagent surface for one worker
    per trial and supply the exact constructed context payload.
  - Scope Boundary:
    - Editable: minimal host-binding helper/config only if required by fresh
      evidence; live receipts and outputs are benchmark artifacts.
    - Inspect-only: Codex host tool contract and existing hook implementation.
    - Preserve-only: no private host internals or hook bypass.
    - Out of scope: recursive delegation and profile proliferation.
  - Non-Goals: no provider telemetry claim from identity alone.
  - Pre-flight Questions:
    - Data source: P2-A request payload and official host receipt.
    - Display permission: read-only bounded worker prompt.
    - DB read flow: existing ledger receipt lookup.
    - DB write flow: live trial event only.
    - Render location: N/A.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: one supported worker with exact host ID and output.
    - Cleanup/quarantine: isolated fixture root per trial.
    - External side effects: native host model execution only.
    - N/A notes: provider/token/cost remain UNKNOWN unless host exposes them.
  - Work Steps:
    1. Prove the host surface can run a bounded worker with the same requested
       profile/settings for both conditions.
       - UI flow check: N/A.
       - DB/data flow check: no worker writes to project fixtures.
       - Render location check: N/A.
       - Evidence target: `E2-P2B-HOST1`.
    2. Feed the exact A/B context payloads through the boundary and bind the
       returned host identity/output to trial receipts.
       - UI flow check: N/A.
       - DB/data flow check: receipt references existing ledger and output file.
       - Render location check: N/A.
       - Evidence target: `E2-P2B-BIND1`.
  - Implementation Gate: supported host evidence is fresh, real, and distinct;
    no self-report or prompt label is accepted as identity proof.
  - Acceptance:
    - Source: adapter records requested versus observed settings separately.
    - Runtime/UI: real host output is captured with `runtime_task_execution=true`.
    - DB/data: A/B roots and outputs do not cross-contaminate.
    - Behavior test: host ID, session/turn when available, and context hash bind.
    - Cleanup/quarantine: no production project mutation.
    - Evidence IDs: `E2-P2B-HOST1`, `E2-P2B-BIND1`.
    - Actual-status rows refreshed: host path, A/B executability, receipts.
  - Evidence Targets: fresh official host receipt, live tool result, request
    fingerprint, output hash, and trial receipt.
  - Actual-status Update: transition live boundary to bound-correct only after
    fresh evidence exists.
  - Commit Boundary: hash checkpoint after the adapter slice; no Git commit.

  - Completion Evidence: `E2-P2B-HOST1` and `E2-P2B-BIND1` record four
    accepted native-host executions, fresh official hook receipts, and the
    exact context/request/output chain. Two completed attempts without hook
    receipts remain disclosed as discarded control-plane failures.

### P3: Run bounded live dry-runs

- Phase Goal: prove the boundary with C1 first, then one non-trivial canonical
  scenario, without quality scoring or full-suite execution.
- Phase Boundary:
  - In scope: C1 A/B and one non-trivial A/B pair, receipts, outputs, timing.
  - Out of scope: all other scenarios, quality scoring, and efficiency claims.
  - Dependencies: P2-A and P2-B PASS.
- Phase Implementation Rule: do not start P3-B until both C1 trials are live,
  captured, and fingerprint-correct.
- Ordered Slice List:
  - P3-A: C1 Tiny configuration edit paired dry-run.
  - P3-B: C7 Accessibility-heavy UI paired dry-run.

- [x] P3-A: C1 paired A/B dry-run.
  - Goal: prove both context modes reach the real host with isolated outputs.
  - Scope Boundary: safe synthetic fixture only; no project mutation.
  - Non-Goals: no score or claim that either mode is better.
  - Pre-flight Questions: same route/profile/settings? exact context differs?
    output isolated? telemetry labeled? yes, or stop with the confounder.
  - Work Steps:
    1. Build C1 A and B views from the same fixture and record distinct hashes.
       - UI flow check: N/A.
       - DB/data flow check: independent roots and no prior output preload.
       - Render location check: N/A.
       - Evidence target: `E3-P3A-CONTEXT1`.
    2. Execute one real worker per condition and finalize receipts/output files.
       - UI flow check: N/A.
       - DB/data flow check: ledger/output pointers resolve inside trial roots.
       - Render location check: N/A.
       - Evidence target: `E3-P3A-LIVE1`.
  - Implementation Gate: both A and B have live host evidence before continuing.
  - Acceptance: two fresh live receipts, two output artifacts, exact mode/hash
    binding, and no contamination.
  - Evidence Targets: C1 A/B receipts, host IDs, output hashes, timer values.
  - Actual-status Update: C1 rows become PASS only from fresh runtime evidence.
  - Commit Boundary: record immutable receipt/output hashes; no Git commit.

  - Completion Evidence: `E3-P3A-CONTEXT1` and `E3-P3A-LIVE1` record distinct
    C1 fingerprints, equal requested execution settings, two live receipts,
    and two isolated output artifacts.

- [x] P3-B: C7 paired non-trivial dry-run.
  - Goal: prove the boundary is not C1-specific using the existing
    accessibility-heavy UI scenario, which exercises a larger acceptance and
    permission context while remaining read-only and non-owner-boundary.
  - Scope Boundary: synthetic C7 fixture only; no C12 owner approval path.
  - Non-Goals: no accessibility quality grade and no A/B superiority claim.
  - Pre-flight Questions: same worker profile/settings? exact C7 context?
    no owner action? output captured? yes, or disclose a confounder.
  - Work Steps:
    1. Build and bind C7 A/B context views with the same fixture fingerprint.
       - UI flow check: worker reviews synthetic UI text only.
       - DB/data flow check: separate A/B roots and output paths.
       - Render location check: N/A.
       - Evidence target: `E3-P3B-CONTEXT1`.
    2. Execute both live trials and capture final receipts and outputs.
       - UI flow check: read-only runtime request.
       - DB/data flow check: no cross-condition preload or writes.
       - Render location check: N/A.
       - Evidence target: `E3-P3B-LIVE1`.
  - Implementation Gate: C1 paired proof is complete and Supervisor has not
    identified a boundary defect requiring a fix.
  - Acceptance: one fresh non-trivial live A/B pair is captured and bound.
  - Evidence Targets: C7 receipts, output pointers, route equality, telemetry.
  - Actual-status Update: non-trivial pair becomes PASS only from live evidence.
  - Commit Boundary: record receipt/output hashes; no Git commit.

  - Completion Evidence: `E3-P3B-CONTEXT1` and `E3-P3B-LIVE1` record the
    accessibility-heavy C7 A/B pair with distinct fingerprints, equal
    requested settings, fresh host receipts, and isolated outputs.

### P4: Regression, evidence, and independent review

- Phase Goal: run affected regression and obtain a separate Supervisor verdict.
- Phase Boundary:
  - In scope: focused tests, full P2P suite, Decision Trace, governance drift,
    capability validation, doctor, secret scans, lifecycle checks if candidate,
    evidence/benchmark/actual-status, and Supervisor review.
  - Out of scope: optional hardening and full live certification.
  - Dependencies: P3 paired dry-runs or a named real blocker.
- Phase Implementation Rule: stop at PASS, BLOCKED, or REJECT after review.
- Ordered Slice List:
  - P4-A: Affected regression and final evidence.
  - P4-B: Supervisor acceptance review and closure.

- [x] P4-A: Run affected regression and close evidence.
  - Goal: prove the live boundary did not weaken existing controls.
  - Scope Boundary: only affected tests/gates and package lifecycle when P1-B ran.
  - Non-Goals: no optional hardening.
  - Pre-flight Questions: full build command, test command, doctor, drift,
    secret scan, and artifact checks are all recorded? yes, or status is not
    ready.
  - Work Steps:
    1. Run direct tests and full regression with logs under `.tmp`.
       - UI flow check: N/A.
       - DB/data flow check: verify temp-root cleanup/quarantine.
       - Render location check: N/A.
       - Evidence target: `E4-P4A-TEST1`.
    2. Run detect-changes, governance/doctor/security/lifecycle gates and
       update the four plan ledgers.
       - UI flow check: N/A.
       - DB/data flow check: confirm ledger remains the only durable event store.
       - Render location check: N/A.
       - Evidence target: `E4-P4A-GATE1`.
  - Implementation Gate: all required focused/live evidence exists and no
    stale receipt is being reused.
  - Acceptance: affected regression passes or one named blocker is recorded;
    evidence contains exact commands/results and no fabricated Git data.
  - Evidence Targets: tests, gate outputs, detect-changes, hashes, and reports.
  - Actual-status Update: refresh every acceptance row before review.
  - Commit Boundary: hash checkpoint; no Git commit because `.git` is absent.
  - Completion Evidence: `E4-P4A-TEST1` and `E4-P4A-GATE1` record focused/full
    regression, Decision Trace, package/build, doctor, lifecycle, governance,
    capability, source-drift, scoped-security, artifact, isolation, and the
    no-Git detect-changes limitation.

- [x] P4-B: Supervisor review and closure.
  - Goal: independently accept or reject the exact supported-live boundary claim.
  - Scope Boundary: current plan, changed files, receipts, outputs, tests,
    artifacts, and reports only.
  - Non-Goals: no fixes inside the Supervisor lane.
  - Pre-flight Questions: source inspected, evidence fresh, invariant siblings
    checked, no residual unverified surface? all must be answered.
  - Work Steps:
    1. Write the coder/evidence handoff report with the Invariant Family Map.
       - UI flow check: N/A.
       - DB/data flow check: state/receipt/output isolation documented.
       - Render location check: N/A.
       - Evidence target: `E4-P4B-REPORT1`.
    2. Invoke Supervisor review and stop at its PASS/REJECT or real blocker.
       - UI flow check: N/A.
       - DB/data flow check: no cleanup beyond plan-created temporary data.
       - Render location check: N/A.
       - Evidence target: `E4-P4B-SUP1`.
  - Implementation Gate: P4-A is complete and all required artifacts are bound.
  - Acceptance: Supervisor report contains exactly one verdict for this scope;
    final project status is PASS, BLOCKED, or REJECT.
  - Evidence Targets: supervisor report, final plan ledgers, and final hashes.
  - Actual-status Update: mark `SUPPORTED_LIVE_AB_BOUNDARY_READY` only on PASS.
  - Commit Boundary: no Git commit; preserve report and artifact hashes.
  - Completion Evidence: `E4-P4B-REPORT1` and `E4-P4B-SUP1`; the independent
    Supervisor report is `PASS` for the bounded C07 claim.

- [x] Pn-A: Call supervisor for the implemented-plan acceptance loop.
  - Goal: independently verify the completed plan and exact boundary claim.
  - Work Steps: review source, receipts, output artifacts, tests, gates, and
    remaining risks; if rejected, return only to the failed implementation slice.
  - Implementation Gate: all planned phases are complete or explicitly blocked.
  - Acceptance: Supervisor PASS or a recorded blocker with no closure claim.
  - Completion Evidence: fresh current-source review and independent receipt,
    artifact, test, gate, and Anvien verification in `E4-P4B-SUP1`.

- [x] Pn-B: Remove dead work created during this plan.
  - Goal: leave no fake receipts, stale placeholders, or unused adapter artifacts.
  - Work Steps: inspect plan-created files, remove only dead plan-created work,
    and re-run the relevant safety check.
  - Implementation Gate: only plan-created artifacts are eligible for removal.
  - Acceptance: final evidence contains no misleading live claim or dead helper.
  - Completion Evidence: no fake receipts or unused adapter artifacts were
    found; two missing-hook attempts remain explicitly discarded, and all
    retained `.tmp` roots are evidence pointers for the bounded run.

- [x] Pn-C: Close the plan.
  - Goal: record final validation, hashes, evidence, benchmark, and terminal status.
  - Work Steps: refresh actual-status, evidence, benchmark, and reports; verify
    final file state and stop at the terminal result.
  - Implementation Gate: Pn-A and Pn-B pass or contain an explicit blocker.
  - Acceptance: the final response is limited to PASS, BLOCKED, or REJECT plus
    the requested numbered report.
  - Completion Evidence: final plan ledgers and fresh Supervisor report record
    terminal `PASS`; no release or additional live scenario is started.

## Risk Notes

- The primary risk is relabeling a local proxy as live; the boundary must
  require a fresh supported host receipt and output.
- The second risk is losing the exact context binding between construction and
  host submission; request fingerprints and stale-binding checks must be
  deterministic.
- Provider-owned telemetry may remain `UNKNOWN`; missing values must never be
  estimated from bytes, words, or local timers.
- A native child may observe the working tree; prompts and fixture roots must be
  explicitly read-only and never target protected business projects.
- If the current host cannot provide a fresh supported child receipt/output,
  stop with the correct failure taxonomy rather than creating a fake adapter.
