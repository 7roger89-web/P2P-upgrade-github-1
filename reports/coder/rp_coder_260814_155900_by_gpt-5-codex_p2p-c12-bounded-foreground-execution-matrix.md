# Coder Report: P2P-C12 BFE / Structural / Beginner Evaluation Matrix

Status: READY FOR INDEPENDENT REVIEW

## Scope and Evidence

- Controller: `.p2p/system/p2p_capabilities/foreground_execution.py`.
- CLI: `scripts/p2p_foreground_execution.py`.
- Tests: `tests/test_p2p_foreground_execution.py`.
- Focused result at this checkpoint: 20/20 PASS in 1.153 seconds.
- C11/C06 preservation slice: 36/36 PASS in 1.077 seconds.
- Final full suite after the owner-gate source change: 159/159 PASS in
  94.719 seconds.
- No browser/Playwright target exists: this is an offline standard-library
  Python control-plane and CLI boundary.

## BFE1-BFE40

| ID | Invariant | Evidence | Result |
|---|---|---|---|
| BFE1 | Select a deterministic task | `test_selects_one_ready_task...` | PASS |
| BFE2 | Only READY is executable | selection/preflight tests | PASS |
| BFE3 | One direct task per run | selection result + `test_multiple_active_tasks...` | PASS |
| BFE4 | Dependency readiness preserved | C11 task-state regression | PASS |
| BFE5 | Capability preflight before action | `test_preflight_denied_capability...` | PASS |
| BFE6 | Permission/owner preflight before action | `test_owner_gate_is_required...` + durable `WAITING_OWNER` assertion | PASS |
| BFE7 | Stale context blocks | `test_stale_context_blocks...` | PASS |
| BFE8 | Optional capability is fallback-only | `test_missing_optional_capability...` | PASS |
| BFE9 | Intent exists before mutation | durable artifact test | PASS |
| BFE10 | Intent binds goal/task/plan | intent schema and receipt inspection | PASS |
| BFE11 | Intent rejects agent/model/provider/thread | `test_identity_fields...` | PASS |
| BFE12 | Scope is explicit | `test_scope_and_protected_state...` | PASS |
| BFE13 | Non-scope wins | path guard and protected-path assertions | PASS |
| BFE14 | Action count is finite | `test_action_count_and_wall_clock...` | PASS |
| BFE15 | Wall-clock budget is finite | same budget test | PASS |
| BFE16 | Retry count is finite | `test_retry_is_finite...` | PASS |
| BFE17 | Permission failures are not retried | owner/capability preflight tests | PASS |
| BFE18 | Control-plane failure stops | `test_control_plane_partial_ledger...` | PASS |
| BFE19 | Direct path only | direct success + CLI subprocess test | PASS |
| BFE20 | No parallel execution | structural AST test / result flags | PASS |
| BFE21 | No delegation | budget rejection / structural AST test | PASS |
| BFE22 | Rigor is not delegation | controller uses verifier callback, no child surface | PASS |
| BFE23 | ACTIVE starts after preflight | success and blocked-state tests | PASS |
| BFE24 | Pre-action checkpoint persists | receipt/checkpoint artifact test | PASS |
| BFE25 | Mutation is explicit | owner-gate mutation test | PASS |
| BFE26 | Action receipt is not evidence | action-output-only test | PASS |
| BFE27 | Verification is independent | success verifier + C10 completion | PASS |
| BFE28 | DONE requires current evidence | `test_direct_success...` | PASS |
| BFE29 | Failed verification is non-DONE | `test_action_output_alone...` | PASS |
| BFE30 | Interrupted action is non-DONE | `test_interruption_resume...` | PASS |
| BFE31 | Checkpoint records next safe step | persisted checkpoint inspection | PASS |
| BFE32 | Resume uses current bindings | `test_interruption_resume...` | PASS |
| BFE33 | Resume never auto-starts | `test_resume_never_auto_starts...` | PASS |
| BFE34 | Resume does not rerun action | action-call assertion | PASS |
| BFE35 | Resume verifier is read-only | runtime read-only mode + resume test | PASS |
| BFE36 | Project state is source of truth | fresh controller/store reload | PASS |
| BFE37 | Existing ledger remains the trace | `read_events()` durable test | PASS |
| BFE38 | C10 evidence contract is reused | C11/C10 regression and claim binding | PASS |
| BFE39 | C11 state contract is preserved | 36/36 C11/C06 regression | PASS |
| BFE40 | Package/lifecycle boundary is complete | candidate r7 package verify/doctor PASS | PASS |

## Structural X1-X26

| ID | Boundary check | Evidence | Result |
|---|---|---|---|
| X1 | No scheduler symbol | AST function/class scan | PASS |
| X2 | No queue symbol | AST/import scan | PASS |
| X3 | No lease/heartbeat runtime | source inspection | PASS |
| X4 | No worker/child process | AST/import scan | PASS |
| X5 | No parallel/async path | no async/import; fixed result flags | PASS |
| X6 | No background execution | intent/receipt/result false fields | PASS |
| X7 | No process survival claim | intent/receipt/result false fields | PASS |
| X8 | No delegation/agent children | zero-child budget and AST scan | PASS |
| X9 | No model/provider selection | identity rejection and source inspection | PASS |
| X10 | No token/cost budget | finite action/time/output only | PASS |
| X11 | No network import | AST/import scan | PASS |
| X12 | No arbitrary shell/process API | AST/import scan; CLI fixed actions | PASS |
| X13 | No capability installation | C11 preflight is observational | PASS |
| X14 | No permission auto-grant | owner gate and C11 permission contract | PASS |
| X15 | No second ledger | existing `TaskStateStore` ledger only | PASS |
| X16 | No second database | JSON projection plus execution refs only | PASS |
| X17 | No raw action output in receipt | receipt stores bounded summary only | PASS |
| X18 | No raw evidence in trace | C10 refs/fingerprints only | PASS |
| X19 | No identity coupling | intent identity rejection | PASS |
| X20 | Canonical count stays 8 | capability doctor + registry test | PASS |
| X21 | AESTHETICA stays optional | capability doctor + C11 test | PASS |
| X22 | Protected paths fail closed | path guard test | PASS |
| X23 | No delete/destructive API | runtime exposes read/hash/write only | PASS |
| X24 | No unbounded retry | budget/retry test | PASS |
| X25 | C09 host identity unchanged | C11 preservation test/project status | PASS |
| X26 | C08 not rerun | workflow/status preservation evidence | PASS |

## Beginner E1-E10

| ID | Beginner behavior | Evidence | Result |
|---|---|---|---|
| E1 | CLI help names one direct bounded action | CLI `--help` | PASS |
| E2 | Owner request has two concrete options | owner-gate result | PASS |
| E3 | Recommendation and consequence are visible | owner-gate result | PASS |
| E4 | No package/runtime/MCP setup question | CLI output assertions | PASS |
| E5 | Blocked capability has a plain reason | preflight result | PASS |
| E6 | Failed verification explains why it is not DONE | no-output-proof test | PASS |
| E7 | Interrupted task tells user to recheck | checkpoint `next_safe_step` | PASS |
| E8 | Resume result is honest about no auto-start | resume test | PASS |
| E9 | Successful output is separate from evidence | `output_is_evidence: false` | PASS |
| E10 | CLI works from portable and installed layouts | portable candidate smoke + focused CLI test | PASS |

## Preservation and Limits

- C09 remains `BLOCKED / EVENT_EVIDENCE_UNAVAILABLE`; no host identity was
  claimed and no C09/C08 run was started.
- Canonical identities remain the exact eight; AESTHETICA is optional and not
  counted.
- The source workspace has no `.git`; Anvien `detect-changes` returned Git
  exit 129. SHA-256 snapshots are recorded for the new source/test files and
  no Git repository was initialized.
- Final candidate r7 (built after the runtime-lock refresh): `.tmp/p2p-c12/candidates/p2p-c12-candidate-8.4.7-C-codex.15-r7.zip`,
  package version `8.4.7-C-codex.15`, SHA-256
  `939f918875f57906112fcb50f7e145ef15187cbe29ae50c4cc15dd888709c522`,
  size `2,446,508` bytes;
  package verification and package doctor both PASS.
- Candidate r6 is superseded by r7 only because r7 was rebuilt after the
  protected runtime-lock refresh; the owner-gate correction remains present.
- Candidate r5 is superseded by r6 because r6 adds durable C11
  `WAITING_OWNER` persistence for the explicit mutation owner gate.
- The bounded workflow helper was run once for the implementation request and
  stopped BLOCKED because its Goal Contract linter classified “implement and
  verify” as separate objectives. The preserved project projection remains
  C09 `BLOCKED`; this orchestration limitation does not invalidate the direct
  controller evidence above.
