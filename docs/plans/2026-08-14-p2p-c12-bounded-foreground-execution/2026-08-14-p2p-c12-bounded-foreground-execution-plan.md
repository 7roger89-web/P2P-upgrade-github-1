# P2P-C12 Bounded Foreground Task Execution Controller Plan

## Metadata

- Date: `2026-08-14`
- Status: `BLOCKED / technical gates PASS; workflow helper closure blocker`
- Plan: `docs/plans/2026-08-14-p2p-c12-bounded-foreground-execution/2026-08-14-p2p-c12-bounded-foreground-execution-plan.md`
- Evidence: `docs/plans/2026-08-14-p2p-c12-bounded-foreground-execution/2026-08-14-p2p-c12-bounded-foreground-execution-evidence.md`
- Benchmark: `docs/plans/2026-08-14-p2p-c12-bounded-foreground-execution/2026-08-14-p2p-c12-bounded-foreground-execution-benchmark.md`
- Actual status: `docs/plans/2026-08-14-p2p-c12-bounded-foreground-execution/2026-08-14-p2p-c12-bounded-foreground-execution-actual-status.md`

## Goal

Implement the smallest standard-library-only bounded foreground execution
controller that consumes the C11 durable task projection and executes at most
one `READY` task through an explicit direct path. The controller must preflight
permissions, capabilities, context, scope, and control-plane health; create a
durable execution intent; enforce a finite budget; perform one bounded direct
action; verify independently from current evidence; and transition the task
only when the existing C11 completion contract passes.

Interruption must leave an observable non-DONE state and a recoverable
checkpoint. A fresh process may resume only by rechecking current artifacts and
running a read-only verifier; it must never infer process survival or fabricate
completion. The controller is a foreground control-plane adapter, not an
agent, scheduler, queue, worker pool, daemon, provider, or second ledger.

## Rules

- Complete P0 actual status before implementation work.
- Update each checklist item immediately when it is completed.
- Record evidence and benchmarkable measurements as they are produced.
- Use repo-local `.tmp/` for temporary roots, logs, and package inspection.
- Use Anvien graph evidence before editing existing functions and report HIGH or
  CRITICAL blast-radius warnings without treating them as an edit prohibition.
- Run `anvien detect-changes` before every implementation checkpoint; this
  workspace has no `.git`, so record that limitation and do not initialize Git.
- Use only the Python standard library; do not install dependencies or enable
  network, hooks, proxying, connectors, or cloud memory.
- Preserve C10 evidence, context, trust, decision-trace, and permission
  contracts. C11 remains the durable source of task state.
- Keep one existing execution ledger. New execution facts are references and
  safe summaries appended through the existing ledger boundary.
- Do not add an executor agent or canonical identity. Canonical identities stay
  exactly eight; `p2p_aesthetica` stays optional and noncanonical.
- Do not rerun or repair C08/C09. C09 remains
  `BLOCKED / EVENT_EVIDENCE_UNAVAILABLE` and no host identity is fabricated.
- Do not overwrite official `8.4.7-C-codex.15`, prior candidates, the
  immutable baseline, or user projects. Promotion and release approval are out
  of scope.
- A failed control plane, permission denial, owner gate, scope violation,
  stale evidence, or missing required capability fails closed. It cannot spawn
  a worker or trigger unbounded retry.

## Problem

C11 can persist a task graph, deterministically identify a safe next task,
preflight gates, checkpoint an active task, and classify resume state. It does
not yet provide the bounded foreground boundary that turns one ready task into
an explicit intent, direct action receipt, independent verification, and safe
state transition. The missing boundary must be narrow enough that “the agent
said it finished” is never confused with evidence that the task finished.

## Scope

- Add one controller module under
  `.p2p/system/p2p_capabilities/` that composes C11 task state with existing
  context, evidence, permission, capability, trust, decision-trace, and ledger
  contracts.
- Add one thin CLI adapter under `scripts/` exposing `select`, `preflight`,
  `run`, and `resume` for an explicit built-in direct action/verifier only.
- Add focused controller tests in an isolated test root, including BFE1-BFE40,
  structural X1-X26, beginner E1-E10, interruption/resume, and negative gates.
- Wire the new runtime module and CLI into package inventory and foundation
  doctor checks without changing version or promoting an artifact.
- Run focused, full, governance, security, capability, doctor, drift, and
  package/lifecycle checks, then create a new immutable candidate only if the
  technical gates pass.
- Write the evidence, benchmark, actual-status, coder, and supervisor reports.

## Non-Goals

- No scheduler, queue, lease, heartbeat, daemon, background execution,
  process keepalive, worker pool, parallelism, delegation, swarm, or child
  task creation.
- No model/provider/agent selection, token/cost accounting, automatic
  capability installation, network access, arbitrary shell execution, or
  external communication.
- No second task database, result store, evidence store, decision trace, or
  ledger.
- No modification to C10 semantics, C09 evidence, C08 status, canonical
  denominator, protected release artifacts, or user projects.
- No general rollback engine. Resume is a bounded read-only recheck path; it
  does not claim that a prior process survived.

## Requirements

- Select at most one deterministic `READY` task from the C11 plan.
- Refuse selection when an `ACTIVE` task exists, a dependency is incomplete,
  a blocker or owner decision is pending, or preflight is not `PASS`.
- Record a serializable execution intent containing task/goal/plan/project
  binding, direct strategy, scope/non-scope, required refs, verifier plan,
  owner gate, and a finite budget. It must reject agent/model/provider/thread
  identity fields.
- Enforce declared path scope, non-scope exclusions, action count, retry count,
  wall-clock bound, no network, no child/delegated work, and no destructive
  operation without an explicit owner gate.
- Persist intent and checkpoint before mutation. Persist a receipt and
  post-action checkpoint before verification. Use the existing ledger for
  safe decision references.
- Retry only explicitly transient direct-action failures and only within the
  finite budget; never retry permission, owner, scope, stale-evidence,
  capability, or control-plane failures.
- Call verification independently from the action result. Output text alone
  cannot satisfy C10 evidence requirements.
- Mark `DONE` only through C11 completion with current bound evidence and a
  candidate-state fingerprint. Verification failure leaves the task active or
  blocked with a checkpoint.
- Resume from a fresh process by classifying current state and, at most, running
  a read-only verifier. Resume never auto-starts, mutates, or marks DONE from
  a historical output.
- Return beginner-readable results with explicit `automatic_start: false`,
  `background_execution: false`, `parallel_execution: false`, and
  `delegation_status: DEFERRED_NOT_CERTIFIED`.

## Acceptance Criteria

- BFE1-BFE40 pass and map to source, focused tests, and observable state or
  receipt evidence.
- Structural X1-X26 pass: no hidden scheduler, queue, worker, process,
  delegation, identity, second ledger, arbitrary egress, or protected-path
  mutation surface.
- Beginner E1-E10 pass, including a no-technical-setup owner message,
  honest blocked/failed/needs-recheck results, and clear next steps.
- C10 and C11 focused regressions pass; C09 remains blocked and C08 is not
  rerun.
- Full regression, governance, security, capability, doctor, drift, and
  package/lifecycle checks pass, or one exact technical blocker is recorded.
- Existing official and candidate artifacts remain unchanged. A new candidate
  is separately labelled, hashed, and not promoted.
- Supervisor review is `PASS`, or the task terminal state is `BLOCKED`/`REJECT`
  with the exact failed gate.

## Checklist

- [x] P0-A: Complete actual status before implementation.
  - Goal: map C10/C11 contracts, current controller gap, package boundary,
    protected artifacts, canonical registry, C09/C08 status, and graph impact.
  - Evidence: `E0-P0-SPEC`, `E0-P0-C11`, `E0-P0-GRAPH`, `E0-P0-IMPACT`,
    `E0-P0-ARTIFACTS`, `E0-P0-LIMITS`.
  - Decision: proceed with a new controller module and thin CLI; preserve C10,
    C11, C09, C08, and existing candidates.

### P1: Foreground controller kernel

- Phase Goal: implement the direct intent, budget, scope, receipt, preflight,
  action, verification, and interruption boundary.
- Phase Boundary:
  - In scope: new foreground controller module and its focused tests; a small
    public C11 event adapter only if needed to append safe references through
    the existing ledger.
  - Inspect-only: C10 evidence/context/trust/decision-trace modules and C11
    task-state contracts before any edit.
  - Preserve-only: C09/C08, official artifacts, existing candidates, and
    unrelated runtime modules.
- Phase Implementation Rule: complete P1-A, run focused QA and Anvien checks,
  update status, then continue to P1-B and P1-C.

- [x] P1-A: Add immutable execution intent, finite budget, scope guard, and
  direct runtime receipt types.
  - Work Steps:
    1. Define `ExecutionBudget`, `ExecutionIntent`, action/verification result,
       and safe serialization schemas with no identity fields.
    2. Define a path-scoped `ExecutionRuntime` with read, hash, bounded write,
       action counting, and no shell/network/child APIs.
    3. Define immutable intent/checkpoint/receipt persistence under the project
       `.p2p/state/foreground-executions/` boundary.
  - Implementation Gate: new code is standard-library-only, no forbidden
    runtime symbol or second store is introduced, and direct tests prove scope
    and budget rejection.
  - Evidence Targets: `E1-P1A-INTENT`, `E1-P1A-SCOPE`, `E1-P1A-TEST`.
  - Actual-status Update: controller surface `missing -> partial -> bound-correct`.

- [x] P1-B: Add selection, preflight, action execution, bounded retry, and
  independent verification.
  - Work Steps:
    1. Select one C11 `next_safe_task` and reject competing ACTIVE work.
    2. Map C11 preflight plus control-plane health to explicit fail-closed
       statuses and beginner messages.
    3. Persist intent/checkpoint, transition `READY -> ACTIVE`, run one direct
       action within budget, store a receipt/checkpoint, and run a separate
       verifier.
    4. Complete through C11 only with current EvidenceClaim-bound evidence;
       preserve ACTIVE/BLOCKED/NEEDS_RECHECK on all failed verification paths.
  - Implementation Gate: every material action is preceded by persisted intent
    and every DONE path contains independent current evidence.
  - Evidence Targets: `E1-P1B-SELECT`, `E1-P1B-PREFLIGHT`,
    `E1-P1B-VERIFY`, `E1-P1B-TEST`.
  - Actual-status Update: selection/preflight/verification rows are
    `bound-correct` from focused direct evidence.

- [x] P1-C: Add interruption and fresh-process resume.
  - Work Steps:
    1. Persist an interruption-safe checkpoint after direct action and before
       verification, retaining non-DONE state.
    2. Load and classify current state with C11 resume helpers and current
       hashes/evidence; never assume process survival.
    3. Allow only a read-only verifier on `SAFE_TO_RESUME` or `NEEDS_RECHECK`;
       mark DONE only after fresh proof.
  - Implementation Gate: missing/stale bindings remain UNKNOWN or
    NEEDS_RECHECK and cannot unlock dependents.
  - Evidence Targets: `E1-P1C-INTERRUPT`, `E1-P1C-RESUME`, `E1-P1C-TEST`.
  - Actual-status Update: interruption/resume row is `bound-correct` from
    the fresh-process trial.

### P2: CLI and package boundary

- Phase Goal: expose one beginner-readable explicit foreground path and make
  the runtime package/doctor inventory complete.
- Phase Boundary:
  - In scope: new `scripts/p2p_foreground_execution.py`, direct CLI tests,
    `scripts/package_release.py`, `scripts/doctor.py`, and package tests.
  - Out of scope: workflow helper redesign, C09/C08, release promotion, and
    arbitrary user-supplied code execution.

- [x] P2-A: Add thin CLI `select`, `preflight`, `run`, and `resume` commands.
  - Acceptance: CLI delegates to the controller, supports only the bounded
    built-in direct action/verifier, emits honest status fields, and has no
    technical setup question in beginner output.
  - Evidence Targets: `E2-P2A-CLI`, `E2-P2A-BEGINNER`, `E2-P2A-TEST`.

- [x] P2-B: Wire package inventory and doctor checks.
  - Acceptance: source packaging copies the new module/CLI; doctor checks both
    paths; package tests and lifecycle inspection show them in the expected
    runtime boundary; version and existing artifacts remain unchanged.
  - Evidence Targets: `E2-P2B-PACKAGE`, `E2-P2B-DOCTOR`, `E2-P2B-TEST`.

### P3: BFE, structural, beginner, and regression evaluation

- Phase Goal: prove behavior, negative paths, structural boundaries, beginner
  communication, and preservation guarantees.
- Phase Boundary: tests/evals and validation only; no production feature
  expansion after the controller contract is closed.

- [x] P3-A: Add focused BFE1-BFE40 and X1-X26 tests.
  - Include selection/preflight/intent/scope/budget/retry/control-plane/direct
    path/delegation/ACTIVE/checkpoint/mutation/verification/DONE/failure/
    interruption/resume/owner-gate/project-boundary cases.
  - Include structural scans for no scheduler, queue, worker, background,
    process survival, arbitrary egress, identity coupling, second ledger, and
    canonical changes.
  - Evidence Targets: `E3-P3A-BFE`, `E3-P3A-STRUCTURAL`.

- [x] P3-B: Add beginner E1-E10 and preservation tests.
  - Verify recommendation/consequence messages, safe owner gate, blocked and
    failed verification summaries, optional capability fallback, and no
    technical installation questions.
  - Recheck C10/C11, canonical 8/8, optional AESTHETICA, C09 blocked, C08 not
    rerun, and project-state versus chat-history separation.
  - Evidence Targets: `E3-P3B-BEGINNER`, `E3-P3B-PRESERVE`.

### P4: Final gates, candidate, supervisor, and closure

- Phase Goal: run all required technical gates, create a new candidate only if
  allowed, obtain an independent supervisor verdict, and stop at PASS,
  BLOCKED, or REJECT.
- Phase Boundary: no promotion, approval execution, deployment, or optional
  hardening after a PASS.

- [x] P4-A: Run focused/full regression and technical gates.
  - Run full build, focused tests, full unit suite, project eval, capability
    doctor, governance/security/drift, and package/lifecycle checks. Keep all
    logs under `.tmp/` and record each result immediately.
  - Evidence Targets: `E4-P4A-REGRESSION`, `E4-P4A-GATES`.

- [x] P4-B: Create a new immutable candidate if all technical gates pass.
  - Record candidate label, embedded version, absolute path, and SHA-256
    separately. Never overwrite official `.15`, existing candidates, or the
    C11 candidate; do not run approval/promotion.
  - Evidence Targets: `E4-P4B-CANDIDATE`, `E4-P4B-HASH`.

- [x] P4-C: Run Supervisor review and cleanup.
  - Supervisor must inspect source, diff, tests, artifacts, and reports and
    return exactly PASS or REJECT. Remove only dead plan-created temporary
    outputs; retain required evidence and candidate artifacts.
  - Evidence Targets: `E4-P4C-SUPERVISOR`, `E4-P4C-CLEANUP`.

- [x] P4-D: Close plan and workflow state.
  - Refresh evidence/benchmark/status, run change detection (record no-Git
    limitation), run the bounded workflow only after implementation evidence,
    and report the exact terminal state.
  - Evidence Targets: `E4-P4D-CLOSURE`.

## Risk Notes

- The unpacked source workspace has no `.git`; Anvien can analyze with
  `--skip-git`, but a real diff/commit checkpoint may remain unavailable.
- The helper `scripts/p2p_workflow.py plan` timed out while scanning this large
  unpacked tree. This is recorded as an orchestration limitation, not used as
  evidence of controller behavior, and will not be retried indefinitely.
- Existing Anvien graphs have unresolved references and high-risk hotspots;
  source inspection plus direct behavioral tests remain necessary.
- Package/doctor functions have non-uniform blast radius (package functions
  LOW; doctor foundation-path function CRITICAL), so those edits stay narrow
  and receive focused regression coverage.
- C09 remains `BLOCKED / EVENT_EVIDENCE_UNAVAILABLE`; no C12 result can change
  that status or manufacture host identity.

## Final terminal state

Technical implementation and validation: `PASS`.

Final r7 candidate: `p2p-c12-candidate-8.4.7-C-codex.15-r7.zip`, embedded
version `8.4.7-C-codex.15`, SHA-256
`939f918875f57906112fcb50f7e145ef15187cbe29ae50c4cc15dd888709c522`.
It was rebuilt after the protected runtime-lock refresh; r6 and r5 remain
preserved immutable candidates.
The final owner-gate correction durably records missing mutation permission as
C11 `WAITING_OWNER` before any action; candidate r5 is superseded.

Overall workflow terminal state: `BLOCKED` at the Goal Contract linter because
the single implementation request also contained an independent verification
objective. The C09 project-status projection remains `BLOCKED`, and C08/C09
were not rerun.
