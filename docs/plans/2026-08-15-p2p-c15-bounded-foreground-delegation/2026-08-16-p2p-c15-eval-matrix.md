# P2P-C15 Evaluation Matrix

The matrix is backed by the real focused C15/C11/C12 runtime tests and the
safe project-style field fixture. It is not a claim of live host identity or
provider/model execution.

| # | Required case | Runtime evidence | Result |
|---:|---|---|---|
| 1 | Trivial task → `DIRECT` | `BoundedDelegationTests.test_direct_is_first_class_when_no_material_value_exists`; field A | PASS |
| 2 | Specialist bounded task → `DELEGATE` | `test_material_value_delegates_only_after_host_surface_is_declared`; field B | PASS |
| 3 | Unclear/missing boundary → no delegation | `test_missing_candidate_state_blocks_before_delegation` | PASS |
| 4 | Owner decision required → blocked | `test_mutating_child_requires_task_need_and_owner_gate` | PASS |
| 5 | Permission mismatch → no delegation | `test_child_permission_and_scope_must_be_subsets` | PASS |
| 6 | Capability/host mismatch → truthful block | `test_material_value_delegates_only_after_host_surface_is_declared` with `host=False` | PASS |
| 7 | Stale evidence/result → reject | `test_stale_candidate_result_is_rejected` | PASS |
| 8 | Incomplete worker result → not `DONE` | `test_delegated_result_requires_parent_verification_before_done`; field C | PASS |
| 9 | Verification failure → reject | `test_failed_verification_prevents_done`; field C | PASS |
| 10 | Worker failure/timeout → bounded recovery | `test_boundary_failure_is_not_retried`, `test_transient_failure_retries_only_within_budget` | PASS |
| 11 | Retry does not hide uncertain mutation | `test_unknown_partial_mutation_stops_without_direct_fallback`, `test_safe_direct_fallback_requires_known_no_mutation` | PASS |
| 12 | No grandchildren | `test_child_cannot_delegate_again`; field E | PASS |
| 13 | No swarm/parallel/background path | `ForegroundExecutionTests.test_structural_boundary_has_no_scheduler_worker_or_external_executor_surface` | PASS |
| 14 | Context package is bounded | `test_handoff_is_minimal_and_structurally_bounded` | PASS |
| 15 | Result/evidence stays linked to durable task | `test_parent_verification_can_complete_existing_c11_task`; field D | PASS |
| 16 | Decision reconstructable from trace | `test_material_strategy_reason_is_recorded_in_existing_decision_trace` | PASS |
| 17 | Interruption/resume preserves owner/task state | `ForegroundExecutionTests.test_interruption_resume_verifies_without_rerunning_action`; field F | PASS |
| 18 | Beginner does not select agent/model | `test_cli_decision_is_thin_and_beginner_readable`, `test_decision_precedes_execution_class_resolution` | PASS |

## Execution Summary

- Focused C15 suite after the fingerprint fix: `24/24 PASS`.
- Affected C15+C11+C12 suite after the fix: `64/64 PASS`.
- Full repository suite after the fix: `218/218 PASS`.
- Field A-F fixture: `all_checks_pass=true`.
- No synthetic host identity, provider/model selection, worker thread, or
  external bridge was used.
