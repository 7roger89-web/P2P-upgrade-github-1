# P2P-C11 Durable Task State and Minimal Dependency Graph Foundation Plan

## Metadata

- Date: `2026-08-14`
- Status: `complete`
- Plan: `docs/plans/2026-08-14-p2p-c11-durable-task-foundation/2026-08-14-p2p-c11-durable-task-foundation-plan.md`
- Evidence: `docs/plans/2026-08-14-p2p-c11-durable-task-foundation/2026-08-14-p2p-c11-durable-task-foundation-evidence.md`
- Benchmark: `docs/plans/2026-08-14-p2p-c11-durable-task-foundation/2026-08-14-p2p-c11-durable-task-foundation-benchmark.md`
- Actual status: `docs/plans/2026-08-14-p2p-c11-durable-task-foundation/2026-08-14-p2p-c11-durable-task-foundation-actual-status.md`

## Goal

Implement the smallest standard-library-only durable task foundation that can
turn an existing P2P Goal into a bounded, dependency-aware task plan and
reconstruct safe continuation state from project artifacts after interruption.
The foundation must reuse the existing Goal Contract, FACT_LEDGER/Live Specs,
EvidenceClaim, Context pointers, Decision Trace, approvals, and append-only
Execution Ledger without creating a second truth store or any autonomous
runtime.

## Rules

- Complete P0 actual status before implementation work.
- Update each checklist item immediately when it is completed.
- Record evidence as work completes.
- Record benchmarkable counts or measurements when they are taken.
- Update later phase status assumptions, next actions, and work steps when actual-status evidence changes the repo state.
- Run Anvien detect-changes before every implementation-slice commit when implementation work was performed; the workspace has no `.git`, so the limitation must remain explicit if the command cannot produce a diff.
- For public runtime or UI-facing changes, validate the real user-visible runtime with browser or Playwright evidence. This scope is offline Python state/runtime work; browser evidence is N/A.
- All temporary test/build outputs stay under the repo-local `.tmp/` tree and all test project roots are isolated temporary roots.
- Do not install external frameworks or dependencies.
- Do not create a scheduler, queue, lease, heartbeat, daemon, worker pool, agent delegation, background retry, or autonomous process.
- Do not add a canonical agent, change the canonical denominator, rerun C08, or alter C09 evidence.
- Do not overwrite official `.15` or any existing candidate artifact; no promotion or release approval is performed.
- Task identity is independent of agent/model/provider/thread identity; lineage is UNKNOWN unless actual host evidence exists.
- A failed control plane is classified and surfaced; it never causes product-agent spawning or unbounded retry.

## Problem

The repository already persists Goal Contracts, project status, execution
events, decision traces, context/evidence references, approvals, and capsules,
but no current runtime contract represents individual work items or their
dependencies. As a result, a new chat can recover a Goal and historical
evidence but cannot deterministically answer which task is ready, blocked,
owner-gated, evidence-complete, or safe to resume. The implementation must
close that gap without duplicating existing authority or turning durable state
into background execution.

## Scope

- Add one task-state contract module under `.p2p/system/p2p_capabilities/`.
- Add one narrow CLI adapter under `scripts/` for validate/save/resume/next-task inspection.
- Persist the current task projection under the existing `.p2p/state/` boundary and append task transition/plan-revision references to the existing `execution-ledger.jsonl`.
- Represent one stable logical owner per Goal without adding an agent.
- Validate task IDs, references, self-dependencies, cycles, state transitions, acceptance evidence, stale evidence, owner decisions, capability readiness, permission authority, plan revisions, interruption classification, direct dependency handoff, and safe next-task selection.
- Add focused behavioral tests and beginner scenarios in isolated temporary roots.
- Run the affected existing suite, full unit suite, capability/decision/evidence/governance/security/doctor checks, and package lifecycle checks when the runtime source is packaged.

## Non-Goals

- No background execution, scheduler, queue, lease, heartbeat, due date, daemon, webhook runtime, worker claim, automatic retry service, rollback engine, or cross-machine continuation.
- No agent pool, parallel spawning, grandchildren, swarm, automatic model/provider selection, or task-to-agent identity coupling.
- No CAPSULE 2.0, Knowledge Delta 2.0, Memory Loadout, CodeGraph, DeepSeek Harness, Semantica runtime, vector database, or full memory graph.
- No routing redesign, AESTHETICA policy change, model/provider change, C08 rerun, C09 investigation, host identity claim, Live Specs promotion, release, deploy, or publish.
- No second task database, workflow database, ledger, or competing evidence/fact/decision store.

## Requirements

- Use the existing Goal ID and existing evidence/decision/context reference vocabulary.
- Persist a minimal task contract containing task/goal identity, purpose, state, dependencies, scope/non-scope, acceptance, required evidence, permission/capability needs, context/source refs, outputs, blockers, owner decisions, timestamps, and completion refs.
- Validate the seven task states `PLANNED`, `READY`, `ACTIVE`, `BLOCKED`, `WAITING_OWNER`, `DONE`, and `CANCELLED` with deterministic fail-closed transitions.
- Treat `DONE` as acceptance plus current scoped evidence; retain historical completion provenance when evidence becomes stale and prevent downstream unlock.
- Reject invalid references, self-dependencies, cycles, `READY` with incomplete dependencies, `DONE` without evidence, unresolved owner gates, denied permissions, missing required capabilities, and cancellation used as dependency satisfaction.
- Preserve requirement -> task -> evidence and decision -> task references without copying evidence payloads.
- Support progressive plan revision with structured rationale, evidence refs, decision refs, immutable completed history, and no speculative microtask explosion.
- Select the next task by dependency readiness, effective evidence status, owner gate, permission, capability, blocker, and deterministic tie-break—not text order alone.
- Provide a plain-language owner question with two or three concrete options and consequence/approval metadata.
- Reconstruct current Goal, owner, last completed task, active/incomplete task, blockers, next safe task, evidence refs, pending owner decision, and interruption classification without the old chat transcript.
- Keep active-at-interruption tasks non-DONE; classify them as `DONE`, `SAFE_TO_RESUME`, `NEEDS_RECHECK`, `BLOCKED`, or `UNKNOWN` only from available evidence.
- Return only direct dependency handoff fields: outcome, artifact refs, evidence refs, material decision/constraint refs, and unresolved risk.
- Keep logical owner, canonical identities, and optional AESTHETICA policy separate; canonical count stays 8 and denominator stays 8.

## Acceptance Criteria

- DTF1-DTF4: existing architecture is mapped; one logical owner is durable; the task contract exists; Task != Agent is enforced.
- DTF5-DTF9: dependency validation, cycle rejection, state transitions, current evidence, and stale-evidence gating pass.
- DTF10-DTF16: requirement/evidence, decision/task, progressive plan, deterministic selection, capability, permission, and owner gates pass.
- DTF17-DTF21: beginner owner message, interruption safety, fresh reconstruction, direct handoff, and project-state/chat-history separation pass.
- DTF22-DTF27: rigor/delegation, bounded control-plane failure, no scheduler, C10 preservation, C09 UNKNOWN, and no second truth store pass.
- DTF28-DTF35: focused tests, beginner evals, regression/governance/security, canonical safety, and immutable artifact preservation pass.
- DTF36: an independent Supervisor review accepts the complete claim with no residual same-invariant surface unverified.

## Checklist

- [x] P0-A: Complete actual status before implementation work.
  - Goal: establish the real current state of Goal, evidence, decision, context, approval, ledger, capsule, task, and resume surfaces.
  - Work Steps: inspect the current C10 plan/evidence, full relevant `docs/SPEC` cluster, `.p2p/state` artifacts, runtime modules, existing tests, Anvien file-detail/impact summaries, canonical registry, and protected artifact metadata; classify each surface; record the exact missing task/resume gap; update all later slice status assumptions from that evidence.
  - Implementation Gate: no runtime or test implementation edits start until the P0 actual-status file has a completed decision and the evidence ledger contains exact P0 IDs.
  - Acceptance: every target surface is classified as correct, partial, missing, preserve-only, or blocked with a source-of-truth, writer, reader, durability, transition, evidence, permission, and resume note.

### P1: Core task contract, graph, gates, and planning

- Phase Goal: create a pure structured task foundation that is safe before persistence is wired.
- Phase Boundary:
  - In scope: `.p2p/system/p2p_capabilities/task_state.py` and its direct unit tests only.
  - Out of scope: scheduler/execution workers, modifications to canonical routing, C09/C08, release artifacts, and unrelated existing modules.
  - Dependencies: P0 complete; existing EvidenceClaim/Context/Decision Trace contracts remain preserve-only dependencies.
- Phase Implementation Rule: do not implement `P1` directly. Implement `P1-A`, verify it, record evidence, refresh actual-status, commit when required, then continue to `P1-B` and `P1-C`.
- Ordered Slice List:
  - P1-A: Add minimal task records, logical owner, graph validation, and state transition kernel.
  - P1-B: Add evidence-backed completion, capability/permission preflight, owner gates, and beginner prompt.
  - P1-C: Add deterministic plan generation, progressive revision provenance, next-task selection, and direct handoff.

- [x] P1-A: Add the minimal task contract and dependency/state kernel.
  - Goal: represent bounded work without introducing agents or execution runtime.
  - Scope Boundary:
    - Editable: new `.p2p/system/p2p_capabilities/task_state.py` and direct test file only.
    - Inspect-only: existing Goal Contract, project-status, EvidenceClaim, Context, Decision Trace, capability registry, and canonical registry.
    - Preserve-only: `.p2p/state/execution-ledger.jsonl`, FACT_LEDGER, Live Specs, C09/C08 artifacts, and all existing runtime modules.
    - Out of scope: persistence adapter, CLI, scheduler, agent pool, worker lineage, and package promotion.
  - Non-Goals: no automatic decomposition from prose, no model call, no task executor, no queue/lease/heartbeat, and no task identity fields for agent/model/provider/thread.
  - Pre-flight Questions:
    - Data source: existing Goal ID and structured task specs supplied by the planner.
    - Display permission: N/A; this slice is a data contract.
    - DB read flow: N/A; no database.
    - DB write flow: N/A; persistence is P2-A.
    - Render location: N/A; API/CLI output is P2-C.
    - UI behavior flow: N/A; no UI.
    - Docker runtime: N/A; offline standard-library module.
    - Playwright target: N/A; no public UI.
    - Behavior test: unique IDs, valid refs, self-dependency, cycle rejection, independent tasks, state transition rejection, and Task != Agent.
    - Cleanup/quarantine: tests use repo-local `.tmp` temporary roots and delete/quarantine them through `TemporaryDirectory`.
    - External side effects: none.
    - N/A notes: all persistent/evidence/owner behavior is covered by later slices.
  - Work Steps:
    1. Define immutable task/owner/plan dataclasses, allowed states, safe serialization, and explicit identity-field rejection.
       - UI flow check: N/A; contract-only.
       - DB/data flow check: validate object -> deterministic mapping; no write.
       - Render location check: N/A.
       - Mini QA for each completed implementation slice (MUST): run focused unit tests against the new module.
       - Evidence target: `E1-P1A-CONTRACT1` and `E1-P1A-TEST1`.
    2. Implement dependency reference validation, cycle detection, topological readiness helpers, and deterministic transition table.
       - UI flow check: N/A.
       - DB/data flow check: graph validation rejects invalid/silent repair paths.
       - Render location check: N/A.
       - Mini QA for each completed implementation slice (MUST): run graph/state tests including cancellation and downstream gating.
       - Evidence target: `E1-P1A-GRAPH1` and `E1-P1A-TEST2`.
  - Implementation Gate:
    - Before editing target files, Anvien freshness is current and related existing surfaces are recorded in P0; no existing function is edited in this slice.
    - New code must use standard-library imports only and expose no scheduler/worker/delegation symbol.
  - Acceptance:
    - Source: task contract and graph functions are self-contained and reject unknown task identity fields.
    - Runtime/UI: N/A.
    - DB/data: no DB or second ledger created.
    - Behavior test: T1-T5, T15-T17 pass.
    - Cleanup/quarantine: temporary roots remain isolated.
    - Evidence IDs: `E1-P1A-CONTRACT1`, `E1-P1A-GRAPH1`, `E1-P1A-TEST1`, `E1-P1A-TEST2`.
    - Actual-status rows refreshed: task contract, dependency graph, state machine.
  - Evidence Targets: source inspection, focused tests, Anvien parse/detail after the new file exists.
  - Actual-status Update: `missing -> partial` for the task contract and graph until later persistence/gate slices close the full foundation.
  - Commit Boundary: commit after this slice when acceptance passes; no `.git` exists, so record the failed detect-changes limitation rather than initializing Git.

- [x] P1-B: Add evidence, capability, permission, and owner gates.
  - Goal: make executable and DONE states fail closed using existing C10 semantics.
  - Scope Boundary:
    - Editable: the new task module and direct tests only.
    - Inspect-only: existing EvidenceClaim/evaluate_done, trust/capability registry, approval policy, and Decision Trace.
    - Preserve-only: existing evidence payloads and approval records.
    - Out of scope: changing C10 evidence.py/trust.py or implementing actual host capability execution.
  - Non-Goals: no blanket Goal permission, no self-approval, no fake capability, no automatic install, and no infinite retry.
  - Pre-flight Questions:
    - Data source: EvidenceClaim objects, caller-supplied capability readiness, granted permission mapping, and owner decision record.
    - Display permission: N/A.
    - DB read flow: N/A.
    - DB write flow: N/A; P2-A records safe refs/events.
    - Render location: plain-language owner prompt returned by the API.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: DONE without evidence, stale evidence, missing required/optional capability, denied permission, and owner gate persistence.
    - Cleanup/quarantine: isolated temporary state only.
    - External side effects: none.
    - N/A notes: actual user approval remains outside this development test.
  - Work Steps:
    1. Bind task completion to acceptance requirements, required evidence refs, EvidenceClaim effective status, and candidate-state fingerprint.
       - UI flow check: N/A.
       - DB/data flow check: acceptance -> evidence refs -> current candidate fingerprint.
       - Render location check: N/A.
       - Mini QA for each completed implementation slice (MUST): focused DONE/stale tests.
       - Evidence target: `E1-P1B-EVID1` and `E1-P1B-TEST1`.
    2. Implement capability/permission preflight and durable owner decision data with beginner-facing options.
       - UI flow check: N/A; message contract only.
       - DB/data flow check: missing required capability/permission becomes BLOCKED; unresolved owner choice becomes WAITING_OWNER.
       - Render location check: `beginner_owner_message()` output.
       - Mini QA for each completed implementation slice (MUST): gate tests and plain-language assertions.
       - Evidence target: `E1-P1B-GATE1` and `E1-P1B-TEST2`.
  - Implementation Gate:
    - Existing EvidenceClaim and permission contracts are inspected and imported/referenced without weakening them.
    - Every gate has an explicit fail-closed reason and no hidden fallback.
  - Acceptance:
    - Source: gate functions store references/fingerprints, never raw evidence payloads or secrets.
    - Runtime/UI: beginner owner message contains concrete options, recommendation, and consequence without technical setup vocabulary.
    - DB/data: N/A until P2-A; no second store added.
    - Behavior test: T6-T10 and B4-B7 pass.
    - Cleanup/quarantine: isolated temporary state only.
    - Evidence IDs: `E1-P1B-EVID1`, `E1-P1B-GATE1`, `E1-P1B-TEST1`, `E1-P1B-TEST2`.
    - Actual-status rows refreshed: evidence binding, capability/permission preflight, owner gate.
  - Evidence Targets: direct source/test evidence and existing C10 regression tests.
  - Actual-status Update: evidence/permission/capability rows remain `bound-correct` in existing modules; new task gates become `bound-correct` for the task boundary.
  - Commit Boundary: commit after this slice when acceptance passes.

- [x] P1-C: Add planning, provenance, selection, and direct handoff contracts.
  - Goal: turn a Goal into a bounded plan and identify the next safe task deterministically.
  - Scope Boundary:
    - Editable: the new task module and direct tests only.
    - Inspect-only: Goal Contract work plan, Decision Trace reference contract, Context pointers, and existing execution ledger.
    - Preserve-only: completed historical task facts and decision/evidence payloads.
    - Out of scope: worker delegation, parallel execution, model selection, and automatic planner inference from prose.
  - Non-Goals: no general workflow language, no hidden chain-of-thought, and no speculative future microtasks.
  - Pre-flight Questions:
    - Data source: Goal Contract plus bounded structured task specs.
    - Display permission: N/A.
    - DB read flow: N/A.
    - DB write flow: plan revision events are P2-A.
    - Render location: deterministic selection/handoff mappings.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: requirement/task/evidence refs, decision/task refs, progressive revision, next-task selection, and direct handoff.
    - Cleanup/quarantine: isolated temporary state only.
    - External side effects: none.
    - N/A notes: persistence and fresh reconstruction are later.
  - Work Steps:
    1. Add bounded `plan_from_goal`, revision provenance, and completed-history protection.
       - UI flow check: N/A.
       - DB/data flow check: Goal requirement refs -> tasks -> evidence refs; revisions keep completed tasks immutable.
       - Render location check: N/A.
       - Mini QA for each completed implementation slice (MUST): plan and provenance tests.
       - Evidence target: `E1-P1C-PLAN1` and `E1-P1C-TEST1`.
    2. Add effective readiness, deterministic `next_safe_task`, and direct dependency handoff.
       - UI flow check: N/A.
       - DB/data flow check: dependency status/gates -> selection; handoff contains only direct refs.
       - Render location check: N/A.
       - Mini QA for each completed implementation slice (MUST): selection/handoff tests.
       - Evidence target: `E1-P1C-SELECT1` and `E1-P1C-TEST2`.
  - Implementation Gate:
    - Completed tasks cannot be rewritten by plan revision; dependency readiness always uses effective current evidence.
    - No task field or function may create or select an agent.
  - Acceptance:
    - Source: bounded plan/revision/selection/handoff contracts are deterministic.
    - Runtime/UI: N/A.
    - DB/data: no persistence yet.
    - Behavior test: T12-T14, T16-T17, B2-B5, and B9 pass.
    - Cleanup/quarantine: isolated temporary state only.
    - Evidence IDs: `E1-P1C-PLAN1`, `E1-P1C-SELECT1`, `E1-P1C-TEST1`, `E1-P1C-TEST2`.
    - Actual-status rows refreshed: planning, selection, direct handoff.
  - Evidence Targets: source/test output and bounded API contract inspection.
  - Actual-status Update: task planning surface becomes `partial` until persisted and reconstructed in P2.
  - Commit Boundary: commit after this slice when acceptance passes.

### P2: Durable projection, ledger references, interruption, and CLI

- Phase Goal: persist task projection in the existing project state boundary and recover it without chat memory.
- Phase Boundary:
  - In scope: task-state store, append-only task events in existing Execution Ledger, interruption/resume reconstruction, and narrow CLI adapter.
  - Out of scope: changes to existing ledger/Decision Trace implementation, scheduler, process supervision, and release promotion.
  - Dependencies: P1 task contract kernel is verified.
- Phase Implementation Rule: implement `P2-A`, verify and refresh status, then `P2-B` and `P2-C`; do not implement the phase as one broad edit.
- Ordered Slice List:
  - P2-A: Persist current projection and append task/plan reference events to the existing ledger.
  - P2-B: Reconstruct and classify interruption/resume state without fabricating completion.
  - P2-C: Add a standard-library CLI adapter for validate/plan/resume/next/handoff inspection.

- [x] P2-A: Persist the task projection and append task events to the existing ledger.
  - Goal: durable state survives the session while preserving one authoritative event store.
  - Scope Boundary:
    - Editable: new task module store functions and `scripts/p2p_task_state.py` only.
    - Inspect-only: existing `.p2p/state/project-status.json`, `.p2p/state/execution-ledger.jsonl`, `p2p_workflow.py` atomic-write conventions, and Decision Trace reader.
    - Preserve-only: existing ledger lines and all protected artifacts.
    - Out of scope: project-status schema rewrite, event-sourcing migration, and background writer.
  - Non-Goals: no TaskDB/SQLite/database, no second ledger, no silent repair of malformed state.
  - Pre-flight Questions:
    - Data source: TaskPlan projection plus existing state path and ledger path.
    - Display permission: N/A.
    - DB read flow: JSON projection read; no DB.
    - DB write flow: atomic task-state projection write plus append-only event to existing execution ledger.
    - Render location: CLI JSON/Markdown output later in P2-C.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: save/load, hash/reference integrity, append events, no second ledger, protected-root rejection, malformed-state classification.
    - Cleanup/quarantine: temp project roots under repo `.tmp`; no release or user roots.
    - External side effects: only test-local file writes.
    - N/A notes: no external network or package install.
  - Work Steps:
    1. Add safe project-state path validation, atomic projection save/load, schema/version and plan hash.
       - UI flow check: N/A.
       - DB/data flow check: save -> read in a fresh object -> validate same plan.
       - Render location check: N/A.
       - Mini QA for each completed implementation slice (MUST): isolated persistence tests.
       - Evidence target: `E2-P2A-STORE1` and `E2-P2A-TEST1`.
    2. Append structured task transition/plan-revision references to `execution-ledger.jsonl` and preserve old lines.
       - UI flow check: N/A.
       - DB/data flow check: existing ledger -> additive task event -> Decision Trace remains readable.
       - Render location check: N/A.
       - Mini QA for each completed implementation slice (MUST): ledger continuity and no-second-store tests.
       - Evidence target: `E2-P2A-LEDGER1` and `E2-P2A-TEST2`.
  - Implementation Gate:
    - The store writes only `.p2p/state/task-state.json` and the existing execution ledger under the supplied project root.
    - Protected roots are explicit and rejected before writes; malformed state raises a bounded control-plane failure.
  - Acceptance:
    - Source: persistence uses standard library and atomic writes; no task DB or new ledger.
    - Runtime/UI: N/A.
    - DB/data: fresh load reconstructs the same current projection and event references.
    - Behavior test: T8, T14, T21, T25 and control-plane failure tests pass.
    - Cleanup/quarantine: protected targets are never mutated.
    - Evidence IDs: `E2-P2A-STORE1`, `E2-P2A-LEDGER1`, `E2-P2A-TEST1`, `E2-P2A-TEST2`.
    - Actual-status rows refreshed: durable state, event history, second-store boundary.
  - Evidence Targets: source inspection, isolated persistence tests, ledger/Decision Trace regression.
  - Actual-status Update: task state and history become `bound-correct` for the existing state boundary.
  - Commit Boundary: commit after this slice when acceptance passes.

- [x] P2-B: Add interruption classification and deterministic resume reconstruction.
  - Goal: recover safe continuation state from artifacts, never from old chat or process survival.
  - Scope Boundary:
    - Editable: new task module and direct tests.
    - Inspect-only: existing CAPSULE, project-status, context manifests, execution ledger, and C09 host-lineage evidence.
    - Preserve-only: historical active/DONE facts and C09 UNKNOWN status.
    - Out of scope: automatic rollback, lease recovery, cross-machine continuation, background retry, and host identity inference.
  - Non-Goals: no claim that an active process survived; no automatic DONE from an ACTIVE task.
  - Pre-flight Questions:
    - Data source: persisted task projection plus current evidence/capability/permission snapshots supplied at resume.
    - Display permission: N/A.
    - DB read flow: fresh state load and bounded event read.
    - DB write flow: optional explicit checkpoint event only; resume inspection is read-only.
    - Render location: `resume_summary()` JSON/Markdown mapping.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: interrupted ACTIVE task classifications, fresh next action, pending owner decision, stale evidence, and C09 UNKNOWN.
    - Cleanup/quarantine: isolated temporary project/state roots.
    - External side effects: none during reconstruction.
    - N/A notes: no live host trial.
  - Work Steps:
    1. Store minimal checkpoint/output/context/evidence references and classify ACTIVE tasks as DONE, SAFE_TO_RESUME, NEEDS_RECHECK, BLOCKED, or UNKNOWN from supplied evidence.
       - UI flow check: N/A.
       - DB/data flow check: active projection -> classification; raw ACTIVE is not rewritten to DONE without current proof.
       - Render location check: N/A.
       - Mini QA for each completed implementation slice (MUST): interruption tests.
       - Evidence target: `E2-P2B-INTERRUPT1` and `E2-P2B-TEST1`.
    2. Reconstruct Goal/owner/completion/blocker/next-task/evidence/owner-gate summary without reading chat history.
       - UI flow check: N/A.
       - DB/data flow check: new process reads only project artifacts and current snapshots.
       - Render location check: N/A.
       - Mini QA for each completed implementation slice (MUST): fresh-process reconstruction test.
       - Evidence target: `E2-P2B-RESUME1` and `E2-P2B-TEST2`.
  - Implementation Gate:
    - Resume output explicitly reports `background_execution=false` and `process_survived=false`.
    - Missing evidence yields UNKNOWN/NEEDS_RECHECK and does not unlock downstream work.
  - Acceptance:
    - Source: resume is read-only and deterministic.
    - Runtime/UI: beginner-facing summary is understandable and technical setup is absent.
    - DB/data: state reload is independent of chat transcript.
    - Behavior test: T7, T11-T13, T18 and B1, B4, B5, B9, B10 pass.
    - Cleanup/quarantine: no protected state mutation.
    - Evidence IDs: `E2-P2B-INTERRUPT1`, `E2-P2B-RESUME1`, `E2-P2B-TEST1`, `E2-P2B-TEST2`.
    - Actual-status rows refreshed: interruption/resume and project-state boundary.
  - Evidence Targets: fresh-process test and C09/canonical registry checks.
  - Actual-status Update: resume surface becomes `bound-correct` for durable-state scope; host lineage remains `UNKNOWN` where unavailable.
  - Commit Boundary: commit after this slice when acceptance passes.

- [x] P2-C: Add the narrow CLI adapter.
  - Goal: make the durable contract inspectable by a future beginner workflow without adding a daemon or router.
  - Scope Boundary:
    - Editable: new `scripts/p2p_task_state.py` and direct CLI tests.
    - Inspect-only: existing CLI conventions and package source inventory.
    - Preserve-only: all existing commands and release artifacts.
    - Out of scope: automatic task execution and modifying the main workflow helper.
  - Non-Goals: no CLI that spawns agents, installs capabilities, or performs protected actions.
  - Pre-flight Questions:
    - Data source: task-state JSON and supplied structured task plan/evidence snapshots.
    - Display permission: read-only project state.
    - DB read flow: JSON/JSONL read only.
    - DB write flow: explicit `save` only under `.p2p/state`.
    - Render location: stdout JSON and concise plain-language resume output.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: CLI help, validate, resume, and next-task output.
    - Cleanup/quarantine: isolated temp roots.
    - External side effects: local state only when explicitly requested.
    - N/A notes: no network.
  - Work Steps:
    1. Expose `validate`, `resume`, `next`, and `handoff` read paths plus explicit `save`/`plan` structured input paths.
       - UI flow check: N/A.
       - DB/data flow check: CLI -> TaskStateStore -> observable JSON/result.
       - Render location check: stdout.
       - Mini QA for each completed implementation slice (MUST): subprocess CLI tests.
       - Evidence target: `E2-P2C-CLI1` and `E2-P2C-TEST1`.
    2. Confirm help/output never claims background execution or technical setup requirements.
       - UI flow check: N/A.
       - DB/data flow check: read-only output does not mutate state.
       - Render location check: stdout.
       - Mini QA for each completed implementation slice (MUST): output assertions.
       - Evidence target: `E2-P2C-BEGINNER1` and `E2-P2C-TEST2`.
  - Implementation Gate:
    - CLI is a thin adapter over the new module; no duplicate state logic.
    - All mutations remain explicit and path-scoped.
  - Acceptance:
    - Source: no scheduler/worker/agent/permission escalation path.
    - Runtime/UI: CLI output is plain language and honest about durable state only.
    - DB/data: no new state store beyond `task-state.json` projection and existing ledger.
    - Behavior test: B1, B6-B8, B10 and CLI tests pass.
    - Cleanup/quarantine: subprocess tests use repo-local isolated roots.
    - Evidence IDs: `E2-P2C-CLI1`, `E2-P2C-BEGINNER1`, `E2-P2C-TEST1`, `E2-P2C-TEST2`.
    - Actual-status rows refreshed: inspectable runtime boundary.
  - Evidence Targets: CLI subprocess output and static scope scan.
  - Actual-status Update: CLI surface becomes `correct` for read/explicit-save scope.
  - Commit Boundary: commit after this slice when acceptance passes.

### P3: Focused C11 evaluation and regression

- Phase Goal: prove the full C11 invariant family with structural, behavioral, beginner, and preservation checks.
- Phase Boundary:
  - In scope: new focused tests/eval fixture and existing affected suite execution.
  - Out of scope: weakening old tests, changing C10/C09 behavior, and new runtime features.
  - Dependencies: P1/P2 verified.
- Phase Implementation Rule: implement `P3-A` focused tests, verify, then `P3-B` evaluation/regression evidence.
- Ordered Slice List:
  - P3-A: Add direct task-state unit and interruption/resume tests.
  - P3-B: Add beginner behavioral matrix and canonical/C09/security preservation assertions.

- [x] P3-A: Add focused task-state tests for T1-T18.
  - Goal: directly test every new contract surface and failure path.
  - Scope Boundary:
    - Editable: `tests/test_p2p_task_state.py` and optional repo-local eval fixture only.
    - Inspect-only: task module and existing regression tests.
    - Preserve-only: old tests and protected paths.
    - Out of scope: test-only bypasses or production changes driven by static assertions.
  - Non-Goals: no mocked proof in place of trigger -> state -> observable result.
  - Pre-flight Questions:
    - Data source: temporary Goal/task/evidence/permission/capability fixtures.
    - Display permission: N/A.
    - DB read flow: temp JSON/JSONL state.
    - DB write flow: test-local store only.
    - Render location: unittest output and evidence report.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: T1-T18.
    - Cleanup/quarantine: `TemporaryDirectory(dir=repo/.tmp)` and protected-root assertions.
    - External side effects: none.
    - N/A notes: no external service.
  - Work Steps:
    1. Implement direct behavior tests for graph, state, evidence, gates, planning, persistence, resume, and handoff.
       - UI flow check: N/A.
       - DB/data flow check: each test observes the stored/reconstructed result.
       - Render location check: N/A.
       - Mini QA for each completed implementation slice (MUST): focused unittest command.
       - Evidence target: `E3-P3A-TEST1`.
    2. Add negative tests for corrupt state, stale evidence, cancellation, fake agent identity, and protected paths.
       - UI flow check: N/A.
       - DB/data flow check: failure is explicit and fail-closed.
       - Render location check: N/A.
       - Mini QA for each completed implementation slice (MUST): focused negative command.
       - Evidence target: `E3-P3A-TEST2`.
  - Implementation Gate:
    - Tests use isolated roots and no release/v5/user-project mutation targets.
    - Tests prove behavior rather than source-marker existence.
  - Acceptance:
    - Source: direct test file exists for each new public surface.
    - Runtime/UI: N/A.
    - DB/data: isolated save/load/reconstruct loop passes.
    - Behavior test: T1-T18 pass with at least two isolated trials for the restart/resume fixture.
    - Cleanup/quarantine: temp roots cleaned.
    - Evidence IDs: `E3-P3A-TEST1`, `E3-P3A-TEST2`.
    - Actual-status rows refreshed: focused test coverage.
  - Evidence Targets: unittest output, isolated trial count, protected-path assertions.
  - Actual-status Update: structural and restart/resume test rows become `correct` when fresh output passes.
  - Commit Boundary: commit after this slice when acceptance passes.

- [x] P3-B: Add beginner B1-B10 and canonical/C09 preservation checks.
  - Goal: demonstrate beginner-first behavior and preserve C10/C09/canonical safety.
  - Scope Boundary:
    - Editable: focused test/eval files only.
    - Inspect-only: canonical `capabilities.json`, C09 reports, C10 evidence/decision trace tests, and existing governance files.
    - Preserve-only: all identities and artifacts.
    - Out of scope: C08/C09 investigation, host identity retries, release changes.
  - Non-Goals: no simulated agent voices or identity receipts.
  - Pre-flight Questions:
    - Data source: task plan fixtures, existing canonical registry, C09 status artifact.
    - Display permission: N/A.
    - DB read flow: temp state read.
    - DB write flow: no protected writes.
    - Render location: beginner messages and eval JSON/Markdown.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: B1-B10 and T19-T20.
    - Cleanup/quarantine: isolated roots.
    - External side effects: none.
    - N/A notes: no host runtime evidence is fabricated.
  - Work Steps:
    1. Run the beginner matrix including owner gate, optional capability, interrupted task, and no-technical-question cases.
       - UI flow check: N/A; text behavior contract.
       - DB/data flow check: fresh artifact reconstruction drives the message.
       - Render location check: test output.
       - Mini QA for each completed implementation slice (MUST): beginner test command.
       - Evidence target: `E3-P3B-BEGINNER1`.
    2. Assert canonical count/denominator, AESTHETICA optional status, C09 UNKNOWN, and no background/scheduler claim.
       - UI flow check: N/A.
       - DB/data flow check: registry/report reads only.
       - Render location check: test output.
       - Mini QA for each completed implementation slice (MUST): preservation command.
       - Evidence target: `E3-P3B-PRESERVE1`.
  - Implementation Gate:
    - Existing C10/C09 evidence is referenced, not rewritten.
    - No test claims official host identity or background execution.
  - Acceptance:
    - Source: behavior fixture and assertions are traceable.
    - Runtime/UI: B1-B10 output is beginner-safe.
    - DB/data: no protected mutation.
    - Behavior test: B1-B10 and T19-T20 pass.
    - Cleanup/quarantine: isolated roots cleaned.
    - Evidence IDs: `E3-P3B-BEGINNER1`, `E3-P3B-PRESERVE1`.
    - Actual-status rows refreshed: beginner behavior and canonical/C09 preservation.
  - Evidence Targets: eval JSON/Markdown, canonical registry read, C09 report read, full unit suite.
  - Actual-status Update: beginner and preservation rows become `correct` when fresh evidence passes.
  - Commit Boundary: commit after this slice when acceptance passes.

### P4: Final gates, package lifecycle, supervisor, and closure

- Phase Goal: verify affected/full regression and report exact release impact without promotion.
- Phase Boundary:
  - In scope: full build/test/doctor/governance/security/drift/package checks, candidate creation if required, supervisor review, cleanup, and final report.
  - Out of scope: promotion, approval execution, deployment, and optional hardening after PASS.
  - Dependencies: all implementation/test slices pass.
- Phase Implementation Rule: final checks are evidence work; after PASS, stop at the requested terminal state.
- Ordered Slice List:
  - P4-A: Run full validation and package/lifecycle gates, preserving old artifacts.
  - P4-B: Supervisor review and dead-work cleanup.

- [x] P4-A: Run final validation and package/lifecycle checks.
  - Goal: prove DTF28-DTF35 and record candidate/embedded version accurately.
  - Scope Boundary:
    - Editable: plan/evidence/benchmark/status/report artifacts only; package output must be a new immutable candidate if the canonical packaging command is used.
    - Inspect-only: all runtime source after implementation.
    - Preserve-only: official `.15`, `.16-r2`, `.17`, `.18`, `.20`, C08/C09 artifacts, immutable baseline, and user projects.
    - Out of scope: promotion/release approval.
  - Non-Goals: no replacing existing candidates and no package claim beyond measured output.
  - Pre-flight Questions:
    - Data source: current source tree, tests, governance and package scripts.
    - Display permission: N/A.
    - DB read flow: N/A.
    - DB write flow: candidate output only if required.
    - Render location: reports/plan ledgers and package manifest.
    - UI behavior flow: N/A.
    - Docker runtime: N/A; no app runtime.
    - Playwright target: N/A.
    - Behavior test: focused suite, full suite, doctor, governance drift, security scan, lifecycle/package verify.
    - Cleanup/quarantine: all logs under `.tmp`; no overwrite of prior candidates.
    - External side effects: none.
    - N/A notes: release approval is not requested.
  - Work Steps:
    1. Run focused tests, full unit suite, Decision Trace, capability foundation, beginner, governance, security, doctor, and drift checks.
       - UI flow check: N/A.
       - DB/data flow check: existing state/ledger/evidence gates remain passing.
       - Render location check: `.tmp` logs and evidence ledger.
       - Mini QA for each completed implementation slice (MUST): record every result immediately.
       - Evidence target: `E4-P4A-TEST1` and `E4-P4A-GATE1`.
    2. If runtime source packaging is affected and all technical gates pass, create a new candidate without promotion and record label, embedded version, path, and SHA-256 separately; otherwise record the real package blocker.
       - UI flow check: N/A.
       - DB/data flow check: package inventory/lifecycle verification.
       - Render location check: package manifest and report.
       - Mini QA for each completed implementation slice (MUST): package verify/doctor/lifecycle.
       - Evidence target: `E4-P4A-PACK1` and `E4-P4A-HASH1`.
  - Implementation Gate:
    - No candidate is created until affected tests and technical gates pass.
    - No promotion/approval command is run.
  - Acceptance:
    - Source: final source inventory/doctor sees new task module and CLI correctly.
    - Runtime/UI: N/A.
    - DB/data: existing state/ledger and C10 evidence/permission contracts remain intact.
    - Behavior test: full required matrix passes or a real blocker is recorded.
    - Cleanup/quarantine: previous artifacts unchanged.
    - Evidence IDs: `E4-P4A-TEST1`, `E4-P4A-GATE1`, `E4-P4A-PACK1`, `E4-P4A-HASH1`.
    - Actual-status rows refreshed: final validation and package lifecycle.
  - Evidence Targets: command outputs, hashes, package/lifecycle reports, final artifact inventory.
  - Actual-status Update: all in-scope rows move to `correct` only when independently evidenced; C09 remains `blocked/UNKNOWN` and Git detect-changes remains a workspace limitation if unchanged.
  - Commit Boundary: record the final checkpoint; do not initialize Git or overwrite artifacts.

- [x] P4-B: Call supervisor for the implemented-plan acceptance loop.
  - Goal: independently review the complete C11 claim against source, evidence, invariants, and scope.
  - Work Steps:
    1. Call the supervisor skill to review the architecture map, new files, tests, state behavior, package/lifecycle evidence, and exact C09/canonical/artifact claims.
    2. If supervisor rejects, return only to the failed implementation slice, make a separate fix, re-run its focused evidence, and request a fresh review.
    3. Accept only when no same-invariant surface remains unverified.
  - Implementation Gate: all prior slices are complete or have an evidence-backed blocker.
  - Acceptance: an independent Supervisor report is PASS, or the plan is BLOCKED/REJECT with one exact reason and no closure claim.

- [x] P4-C: Remove dead work created during this plan.
  - Goal: ensure only active source, tests, plan, evidence, benchmark, status, report, and required candidate artifacts remain.
  - Work Steps:
    1. Inspect plan-created files and `.tmp` outputs; remove only dead artifacts created by this plan using recoverable/local cleanup.
    2. Preserve all historical C09/C10 evidence and prior candidates.
    3. Record cleanup evidence and confirm no rejected implementation remains.
  - Implementation Gate: Supervisor review has either passed or named the exact cleanup scope.
  - Acceptance: no dead production source remains; intermediate package-check and smoke outputs are explicitly retained under repo-local `.tmp` as non-release evidence, while the immutable candidate is preserved.

- [x] P4-D: Close the plan.
  - Goal: finish evidence, benchmark, actual-status, workflow report, and terminal status.
  - Work Steps:
    1. Refresh all status rows and checklist items from final evidence.
    2. Run Anvien detect-changes before any final implementation checkpoint and record the no-`.git` limitation if applicable.
    3. Run the bounded workflow `run` only after actual implementation evidence exists; stop at PASS/BLOCKED/REJECT.
    4. Write the final beginner-facing report with candidate label versus embedded version separated.
  - Implementation Gate: supervisor verdict and all required evidence are present.
  - Acceptance: final status is exactly `PASS`, `BLOCKED`, or `REJECT`; no optional work begins after terminal state.

## Risk Notes

- The workspace is not a Git repository; Anvien change detection and commit checkpoints may remain unavailable. Report this honestly and do not initialize Git.
- Existing `.p2p/state/project-status.json` still contains the prior C09 Goal projection while the workflow helper created a new C11 Goal Contract; this mismatch must be surfaced and resolved only through the existing workflow/status path, not by silently rewriting C09 evidence.
- Existing runtime Anvien coverage is partial/high-risk with unresolved parser references; preserve source inspection and direct behavioral tests as the primary proof.
- C09 host identity remains `BLOCKED / EVENT_EVIDENCE_UNAVAILABLE`; no task-state result may upgrade it.
- Runtime-source packaging may require a new candidate artifact, but no promotion or final user approval is authorized by this task.
