# Minimal Live Execution & Telemetry Boundary for Real Context-Efficiency A/B Plan

## Metadata

- Date: `2026-08-14`
- Status: `blocked`
- Plan: `docs/plans/2026-08-14-minimal-live-execution-telemetry-boundary/2026-08-14-minimal-live-execution-telemetry-boundary-plan.md`
- Evidence: `docs/plans/2026-08-14-minimal-live-execution-telemetry-boundary/2026-08-14-minimal-live-execution-telemetry-boundary-evidence.md`
- Benchmark: `docs/plans/2026-08-14-minimal-live-execution-telemetry-boundary/2026-08-14-minimal-live-execution-telemetry-boundary-benchmark.md`
- Actual status: `docs/plans/2026-08-14-minimal-live-execution-telemetry-boundary/2026-08-14-minimal-live-execution-telemetry-boundary-actual-status.md`

## Goal

Determine whether the existing development project already contains a supported way to execute the canonical benchmark live, and, only if both conditions are genuinely distinct and callable, add the smallest observation boundary that emits honest machine-readable trial receipts. This Goal does not certify context efficiency and must stop if Condition B is not implemented.

## Rules

- Complete P0 actual status before implementation work.
- Use only supported local/runtime/host surfaces; never private RPC, binary patching, credential interception, UI scraping, or fabricated provider receipts.
- Condition A must bind to official .15 and Condition B must bind to the exact .16-r2 candidate artifact and distinct behavior.
- The existing 12-scenario suite and 48 proxy trials remain unchanged and proxy-only.
- No full benchmark in this Goal; dry-run only on C1 and one non-trivial scenario if eligible.
- `runtime_task_execution=true` is valid only for genuine host/model execution and cannot be set by the proxy path.
- Capture allow-listed telemetry with provenance; unavailable values are `UNKNOWN`.
- Do not implement Capsule 2.0, Knowledge Delta, memory, DAG, queue, lease, recovery, scheduler, parallel orchestration, additional routers, agents, or model economy layers.
- Preserve existing Execution Ledger, Decision Trace, Evidence, fixture isolation, role boundaries, intent/permission separation, and canonical 8/8 quorum.
- If .16-r2 has no distinct executable Condition B, stop with `BLOCKED_CONDITION_B_NOT_IMPLEMENTED` and do not invent it.
- If only proxy execution is available, stop; do not relabel it live.
- Update each checklist item immediately when completed or blocked.
- Run Anvien impact/file-detail before any production edit and detect-changes before any implementation commit.

## Problem

The previous benchmark Goal proved that the current canonical suite is proxy-only: `runtime_task_execution=false`, `provider_called=false`, and `quality_claim_allowed=false`. The current task asks for the smallest supported live observation boundary, but the candidate may contain no real context-efficient execution behavior yet. Building an adapter around two metadata labels would create invalid evidence.

## Scope

- Recover the live/proxy boundary and supported host execution path.
- Inspect official .15 and .16-r2 artifact contents and source/runtime role ownership.
- Prove or disprove a distinct executable Condition B before coding.
- If eligible, implement one minimal live adapter and receipt schema, with exact A/B binding, isolation, provenance, allow-listed output capture, failure taxonomy, stale receipt rejection, and existing ledger/evidence references.
- Run only dry-run C1 and one non-trivial scenario, without quality scoring.
- Validate security, path isolation, helper roles, canonical 8/8, and supervisor review.

## Non-Goals

- No full 12-scenario benchmark or quality conclusion.
- No new context-efficient behavior if .16-r2 lacks it.
- No provider integration, hidden host APIs, additional orchestration, or release promotion.
- No mutation of official .15, .16-r2, App Game Truyện, or user projects.

## Requirements

1. Document the local Python/proxy versus real host/model boundary.
2. Prove callable A and B conditions or stop with the specified blocker.
3. Bind A to .15 SHA-256 and B to .16-r2 SHA-256.
4. Prove the independent variable is real, not a prompt/label difference.
5. Use an allow-listed receipt with telemetry provenance and existing evidence/ledger references.
6. Preserve fixture and cross-condition isolation.
7. Represent failures and interruption states without treating them as success.
8. Reject stale receipts when bindings change.
9. Keep unsupported telemetry UNKNOWN and never label proxies as provider values.
10. Do not run the full benchmark after the boundary Goal.

## Acceptance Criteria

- P0 actual status is complete and current.
- Live/proxy semantics are documented from source/runtime evidence.
- Either dry-run A and B both pass with `runtime_task_execution=true` and capturable outputs, or the Goal stops with `BLOCKED_CONDITION_B_NOT_IMPLEMENTED` / another evidence-backed blocker.
- No source change is made when Condition B is absent or only metadata/proxy semantics exist.
- Any implemented boundary has isolated receipts, stale binding checks, provenance, security filtering, helper-role safety, and existing ledger/evidence integration.
- No full benchmark, quality scoring, candidate promotion, or new architecture occurs.
- Supervisor gives exactly one independent `PASS` or `REJECT` verdict.

## Checklist

- [x] P0-A: Complete actual status before implementation work.
  - Goal: establish whether supported live A/B execution and a distinct candidate behavior exist.
  - Work Steps: inspect current instructions, prior blocker evidence, canonical suite, helper source, package artifacts, candidate/runtime manifests, host/tool surface, and Anvien graph; classify every target as correct, partial, missing, unbound, fake-or-stub, or blocked; update P1 from evidence.
  - Implementation Gate: no source edit or dry-run until actual status records A/B executability, candidate distinction, host authority, and touch modes.
  - Acceptance: actual status contains exact evidence IDs and a final P0 decision. **Completed:** distinct executable B behavior and a supported live host boundary are not proven; implementation is blocked.

### P1: Minimal live boundary or evidence-backed stop

- Phase Goal: add only the minimum observation boundary if the required existing behaviors and supported host path exist; otherwise stop without implementation.
- Phase Boundary:
  - In scope: live/proxy semantic boundary, A/B binding, receipt/telemetry contract, isolation, output capture, stale/failure handling, C1 plus one non-trivial dry-run, and validation.
  - Out of scope: new Context-Efficiency behavior, full benchmark, quality scoring, orchestration architecture, and release promotion.
  - Dependencies: P0 actual status proves distinct executable A and B and supported host execution.
- Phase Implementation Rule: do not implement `P1` directly. Execute `P1-A` only after P0 passes the implementation gate; if B is absent, mark P1 blocked and stop.
- Ordered Slice List:
  - P1-A: Implement and validate the minimal live adapter/receipt boundary, or record the hard stop without editing.
  - P1-B: remove (no second implementation slice is authorized in this Goal).

- [x] P1-A: Implement and validate the minimal live adapter/receipt boundary, or record the hard stop without editing.
  - Goal: produce genuine A/B dry-run evidence or a truthful blocker.
  - Scope Boundary:
    - Editable: only the smallest existing eval/runtime boundary proven necessary by P0; audit ledgers and tests.
    - Inspect-only: official/candidate artifacts, host configuration, existing state/ledger/evidence, and protected project files.
    - Preserve-only: canonical suite/fixtures, .15, .16-r2, App Game Truyện, role ownership, permissions, and eight identities.
    - Out of scope: all future architecture and full benchmark execution.
  - Non-Goals: no new behavior for Condition B; no hidden host access; no proxy relabeling.
  - Pre-flight Questions:
    - Data source: supported host/runtime execution and existing frozen fixture.
    - Display permission: N/A; no UI change.
    - DB read flow: N/A; no application database.
    - DB write flow: existing isolated evidence/ledger references only.
    - Render location: N/A.
    - UI behavior flow: N/A.
    - Docker runtime: N/A unless P0 proves the actual supported path requires it.
    - Playwright target: N/A.
    - Behavior test: dry-run receipt and boundary tests.
    - Cleanup/quarantine: temporary isolated roots inside the repository only; no release/user roots.
    - External side effects: none beyond already-authorized host execution if proven supported.
    - N/A notes: missing Condition B is a hard stop.
  - Work Steps:
    1. Prove live/proxy semantics, exact A/B resolution, candidate distinction, and supported host execution before touching code.
       - UI flow check: N/A.
       - DB/data flow check: verify fixture/evidence isolation.
       - Render location check: N/A.
       - Mini QA for each completed implementation slice (MUST): command/runtime boundary checks; no UI slice.
       - Evidence target: `E0-P0A-*` and `E1-P1A-*`.
    2. If eligible, implement the smallest adapter and run only C1 plus one non-trivial dry-run; if not eligible, record `BLOCKED_CONDITION_B_NOT_IMPLEMENTED` and do not edit production source.
       - UI flow check: N/A.
       - DB/data flow check: verify no cross-condition writes or fixture inheritance.
       - Render location check: N/A.
       - Mini QA for each completed implementation slice (MUST): receipt, stale-binding, secret-filter, and role-isolation checks.
       - Evidence target: dry-run receipts or blocker proof.
  - Implementation Gate:
    - Before editing any production symbol, run current Anvien file-detail and impact evidence.
    - Both A and B must be distinct, callable, supported, and bound to exact artifacts.
    - If any gate fails, do not edit or run fake trials.
  - Acceptance:
    - Source: only minimal boundary code is changed if authorized.
    - Runtime/UI: A and B dry-runs prove genuine live execution, or the plan is blocked with no false receipt.
    - DB/data: isolated state and no protected mutation.
    - Behavior test: proxy path cannot claim live execution; live path must produce receipt proof.
    - Cleanup/quarantine: all temporary roots are inside the repository and isolated.
    - Evidence IDs: `E0-P0A-*`, `E1-P1A-*`, and supervisor report.
    - Actual-status rows refreshed: A, B, receipt, telemetry, isolation, release impact.
  - Evidence Targets: source/runtime map, artifact hashes, host authority, adapter source, receipt schema, dry-run outputs, test results, security scan, and supervisor verdict.
  - Actual-status Update: preserve correct proxy/role controls; transition missing B or missing host authority to `blocked` with exact next action.
  - Commit Boundary: no commit if blocked; if implementation occurs, commit only after validation and detect-changes.
  - Actual outcome: blocked before implementation with `BLOCKED_CONDITION_B_NOT_IMPLEMENTED`; no adapter, receipt, live dry-run, or runtime source edit was created.
- [x] Pn-A: Call supervisor for the completed or blocked-plan acceptance loop.
  - Goal: independently verify live/proxy semantics, condition bindings, telemetry honesty, isolation, security, and scope discipline.
  - Work Steps:
    1. Review current source, plan, actual status, evidence, benchmark, tests, and any receipts.
    2. Verify that no proxy was relabeled live and that B is genuinely distinct.
    3. If review fails, return only to the authorized implementation scope or record the blocker; do not expand architecture.
  - Implementation Gate: P1 is complete or explicitly blocked.
  - Acceptance: supervisor report contains exactly one `PASS` or `REJECT` verdict.
  - Actual outcome: supervisor report accepts the bounded blocker as `PASS`; it does not certify live execution or efficiency.
- [x] Pn-B: Remove dead work created during this plan.
  - Goal: remove fake receipts, placeholder metrics, duplicate suites, or unused adapter artifacts created by this Goal.
  - Work Steps: inspect plan-created files, preserve historical proxy evidence, remove only dead artifacts from this Goal, and verify no source-of-truth duplication remains.
  - Implementation Gate: only plan-created artifacts may be removed.
  - Acceptance: final scope contains no misleading live claim or dead implementation.
  - Actual outcome: no adapter, receipt, placeholder telemetry, duplicate suite, or dead runtime artifact was created; historical proxy evidence remains explicitly proxy-only.
- [x] Pn-C: Close the plan.
  - Goal: record final validation, files changed, release impact, and terminal status.
  - Work Steps: run relevant tests/scans, run detect-changes if source changed, record artifact hashes, update all ledgers, and verify worktree state.
  - Implementation Gate: supervisor review passes or records the blocker.
  - Acceptance: PASS only with eligible dry-runs; otherwise BLOCKED with exact blocker and no promotion.
  - Actual outcome: closed as `BLOCKED_CONDITION_B_NOT_IMPLEMENTED`; no promotion or release candidate was created.

## Risk Notes

- The highest risk is creating a receipt that looks live while wrapping a local proxy. The implementation gate forbids this.
- The second risk is inventing Condition B because the candidate currently contains only helper-boundary changes. The explicit stop code prevents this.
- Host/provider telemetry may remain UNKNOWN even after a valid boundary; this is acceptable when provenance is explicit.
- Any change to execution behavior contaminates the later efficiency experiment and must be separately classified.
