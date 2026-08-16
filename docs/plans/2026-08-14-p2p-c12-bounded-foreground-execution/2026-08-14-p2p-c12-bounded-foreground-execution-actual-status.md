# P2P-C12 Bounded Foreground Task Execution Controller Actual Status

## Metadata

- Date: `2026-08-14`
- Status: `BLOCKED / technical implementation complete; workflow helper closure blocked`
- Plan: `docs/plans/2026-08-14-p2p-c12-bounded-foreground-execution/2026-08-14-p2p-c12-bounded-foreground-execution-plan.md`
- Evidence: `docs/plans/2026-08-14-p2p-c12-bounded-foreground-execution/2026-08-14-p2p-c12-bounded-foreground-execution-evidence.md`
- Last checked: `2026-08-14`

## P0 Decision

`PASS TO IMPLEMENTATION`.

The repository has a usable C11 durable task foundation and the existing C10
evidence/context/trust/decision-trace boundaries needed by a foreground
controller. The missing capability is specifically the direct execution
intent/action/verification boundary. A new additive controller and thin CLI
are in scope. No existing C10/C11 guarantee, C09/C08 status, canonical
identity, official artifact, or prior candidate is to be changed.

## Current-State Matrix

| Surface | Current status | Source/evidence | C12 decision |
|---|---|---|---|
| Goal Contract/workflow state | correct/reused | `.p2p/state/goal-contract.json`, workflow inspect/classify/bootstrap | reuse |
| C10 evidence binding | bound-correct/preserve | `.p2p/system/p2p_capabilities/evidence.py`, execution-evidence spec | reuse |
| C10 context pointers | bound-correct/preserve | `.p2p/system/p2p_capabilities/context.py` | reuse |
| C10 trust boundary | bound-correct/preserve | `.p2p/system/p2p_capabilities/trust.py` | reuse |
| C10 Decision Trace | bound-correct/preserve | `.p2p/system/p2p_capabilities/decision_trace.py` and existing ledger | reuse |
| C11 task contract | bound-correct | `.p2p/system/p2p_capabilities/task_state.py` | consume |
| C11 selection/preflight | bound-correct | `next_safe_task`, `TaskStateStore.preflight` | consume |
| C11 checkpoint/resume | bound-correct/preserve | `checkpoint_task`, `classify_resume`, `resume_summary` | consume |
| Generic foreground controller | bound-correct | `.p2p/system/p2p_capabilities/foreground_execution.py`; 20 focused tests | preserve contract |
| Direct intent/budget/scope | bound-correct | `ExecutionIntent`, `ExecutionBudget`, `ExecutionRuntime` | preserve contract |
| Action receipt + independent verify | bound-correct | immutable receipts/checkpoints + C10 completion | preserve contract |
| Fresh-process resume action | bound-correct | controller `resume`, interruption test, portable smoke | preserve read-only resume |
| State CLI | correct/preserve + C12 additive | `scripts/p2p_foreground_execution.py` | preserve old CLI |
| Package inventory | bound-correct | `scripts/package_release.py`, candidate r7 | preserve version |
| Foundation doctor | bound-correct | `scripts/doctor.py`, package doctor PASS | preserve canonical contract |
| Canonical registry | correct 8/8 | capability registry/spec | preserve |
| AESTHETICA | optional/noncanonical | foundation spec/registry | preserve |
| C09 | blocked | `EVENT_EVIDENCE_UNAVAILABLE` reports/status | do not rerun |
| C08 | deferred | project status/workflow records | do not rerun |
| Official/candidate artifacts | preserve-only | artifact hashes in E0-P0-ARTIFACTS | never overwrite |
| Git/change checkpoints | unavailable | no `.git`; Anvien `--skip-git` works | record limitation |

## Authority and Ownership Map

| Concern | Existing authority | C12 writer | C12 reader |
|---|---|---|---|
| Goal/requirement | Goal Contract | none | intent/task binding |
| Task state | C11 `TaskStateStore` | controller through public C11 API | controller/CLI |
| Evidence | C10 EvidenceClaim/source refs | verifier supplies current refs | C11 completion/controller |
| Context | C10 ContextPointer | none | preflight/verifier |
| Permission | existing policy/owner decision | none; requests gate | preflight |
| Capability readiness | registry/readiness contracts | none; optional fallback only | preflight |
| Decision trace | existing execution ledger | safe intent/action/verify refs | reports/CLI |
| Execution artifacts | project `.p2p/state` boundary | intent/checkpoint/receipt refs | resume/controller |
| Identity | canonical registry | none | structural preservation test |

## Anvien and Blast-Radius Evidence

- Root graph was refreshed with `anvien analyze . --force --skip-git` and
  repo-local exclusions. It reports 12,707 nodes and 14,434 relationships.
- System graph was refreshed with `anvien analyze .p2p/system --force --skip-git`.
  It reports 5,499 nodes and 7,015 relationships.
- C11 task-state file is a HIGH hotspot because it is shared by many flows; it
  is preserve-only unless a minimal public event adapter is technically
  unavoidable.
- Package validation/copy functions are LOW impact with one direct impact each.
- Doctor `_foundation_required_paths` is CRITICAL with two direct impacts and
  eight affected processes; only append the two exact required paths and run
  doctor/package regressions immediately afterward.
- The missing controller is additive, so it avoids changing the high-risk C11
  state kernel by default.

## Detailed Findings

1. C11 already enforces `READY`/`ACTIVE`/`DONE` invariants and requires
   preflight PASS for gated execution. The controller must not duplicate or
   weaken those checks.
2. C11 checkpoint fields can represent pending verification and current state
   fingerprints; C12 adds an execution-specific immutable receipt around them.
3. The C06 `live_execution.py` module is a specialized read-only context trial
   harness and must not be repurposed as a generic executor.
4. C10 `EvidenceClaim` requires current, source-bound, fingerprinted evidence;
   an action result or stdout line cannot be used as a DONE proof.
5. Context pointers are metadata and cannot grant permission. Trust rejects
   retrieved/tool/model content as authority.
6. The existing ledger is the only event/decision trace boundary. C12 may add
   safe references but not a second ledger.
7. No existing module provides a scheduler, queue, worker, or background path
   that C12 needs; all such mechanisms remain explicitly out of scope.

## Work Status

| Phase | Status | Next action |
|---|---|---|
| P0 actual status | complete | begin P1-A implementation |
| P1 controller kernel | complete | focused C12 suite 16/16 |
| P2 CLI/package | complete | candidate r4 + package/doctor PASS |
| P3 evaluations | complete | BFE 40/40, structural 26/26, beginner 10/10, preservation PASS |
| P4 gates/candidate/supervisor | complete | technical gates PASS; Supervisor PASS; workflow closure BLOCKED |

## Open Risks and Controls

- Risk: shared C11 state kernel blast radius. Control: new module first; only
  edit C11 after fresh Anvien impact and a direct need is demonstrated.
- Risk: package doctor CRITICAL impact. Control: exact path additions only and
  immediate package/doctor regression.
- Risk: no Git. Control: never initialize Git; report detect-changes limitation.
- Risk: stale C09 projection in historical project status. Control: preserve
  C09 blocked status and do not silently rewrite it.
- Risk: plan helper timeout. Control: use the manually completed plan and direct
  evidence files; do not treat helper timeout as runtime failure.

## P0 Checklist

- [x] Read the attached C12 request.
- [x] Load P2P, planner, coder, and supervisor guidance.
- [x] Inspect/classify/bootstrap the project Goal Contract.
- [x] Read the relevant C10/C11/SPEC cluster.
- [x] Refresh Anvien graphs with the correct no-Git mode.
- [x] Run file-detail and impact analysis before existing-function edits.
- [x] Record protected artifact hashes and C09/C08 preservation rules.
- [x] Complete this P0 status before implementation.

## Implementation Evidence Checkpoint

- P1 controller kernel: complete; no existing C11 state-kernel edit was needed.
- P2 CLI/package: complete; module exported from the capability package, root
  CLI resolves both installed `.p2p/system` and portable `runtime` layouts.
- Protected runtime lock: refreshed after the owner-gate correction with
  `lock-runtime`; subsequent development doctor and drift both PASS.
- Final focused suite: 20/20 PASS in 1.153 seconds; C11/C06 slice: 36/36 PASS
  in 1.077 seconds; full unittest run: 159/159 PASS in 94.719 seconds.
- Candidate r7: `p2p-c12-candidate-8.4.7-C-codex.15-r7.zip`, package version
  `8.4.7-C-codex.15`, size `2,446,508` bytes, SHA-256
  `939f918875f57906112fcb50f7e145ef15187cbe29ae50c4cc15dd888709c522`.
- r7 was built after the protected runtime lock was refreshed; r6 and r5 are
  preserved as superseded immutable candidates.
- The final owner-gate correction persists a missing mutation decision as C11
  `WAITING_OWNER` and does not invoke the action; r5 is superseded.
- C09 remains blocked and C08 was not rerun.
- The final workflow-helper run stopped `BLOCKED` because its Goal Contract
  linter classified the combined implementation/verification request as
  separate objectives. The helper wrote a C12 projection; the preserved
  project-status request was restored to the existing C09 `BLOCKED` projection
  and the affected C09 state test passed again. No C08/C09 execution was run.

## Terminal Condition for This Plan

All technical evidence exists, all technical gates pass, the current Supervisor
report is PASS, and candidate r7 is separately identified without promotion.
The overall plan remains `BLOCKED` at the workflow-helper closure gate named
above; no runtime or governance failure was found.
