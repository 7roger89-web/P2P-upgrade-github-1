# C17 Evaluation Matrix

This matrix records the bounded local evidence for the requested beginner and
structural cases. Tests use isolated repository-local `.tmp` roots. Synthetic
callbacks prove the contract and bounded overlap only; they are not live host
identity evidence.

## Beginner cases P1–P12

| Case | Scenario | Expected | Result / evidence |
|---|---|---|---|
| P1 | Two read-only independent analyses | `PARALLEL` eligible | PASS — `test_independent_ready_pair_is_parallel_and_starts_no_more_than_two` |
| P2 | B depends on A | `SEQUENTIAL` | PASS — `test_dependency_relation_defaults_to_sequential` |
| P3 | Two tasks write the same file | sequential/conflict | PASS — `test_scope_conflict_defaults_to_sequential` |
| P4 | Disjoint paths share package manifest | sequential/conflict | PASS — `test_shared_manifest_resource_defaults_to_sequential` |
| P5 | Two isolated safe artifacts | `PARALLEL` eligible | PASS — independent pair test |
| P6 | One task `WAITING_OWNER` | cannot join | PASS — `test_waiting_owner_task_cannot_join_group` |
| P7 | Identity-required task without identity | cannot join | PASS — `test_identity_required_unknown_task_cannot_join_group` |
| P8 | A succeeds, B fails without mutation | preserve A | PASS — `test_partial_success_is_preserved_without_rescue_child` |
| P9 | B has unknown partial mutation | freeze/recheck | PASS — `test_unknown_mutation_freezes_group_and_cancellation_is_truthful` |
| P10 | Children pass, combined regression fails | group incomplete | PASS — `test_combined_regression_failure_prevents_group_completion` |
| P11 | Beginner knows nothing about coding | no concurrency questions | PASS — CLI no-callback path blocks honestly; no concurrency prompt exists |
| P12 | Three READY independent tasks | at most two | PASS — `test_three_candidates_are_capped_at_two` |

## Structural cases PX1–PX50

| Case | Required invariant | Result / evidence |
|---|---|---|
| PX1 | Official `.19` recovered | PASS — control validation and official hash |
| PX2 | Development lineage gate | PASS — guarded `.15 → .20` reconciliation |
| PX3 | Stale `.15` cannot recur silently | PASS — stale build rejection before side effects |
| PX4 | C11 DAG remains authority | PASS — coordinator uses `TaskStateStore`/`TaskPlan` |
| PX5 | Dependency blocks parallelism | PASS — P2 |
| PX6 | Indirect dependency blocks parallelism | PASS — recursive `_reachable` DAG guard plus C11 graph validation |
| PX7 | Unknown dependency blocks | PASS — C11 invalid dependency guard |
| PX8 | Scope overlap blocks mutation parallelism | PASS — P3 |
| PX9 | Shared singleton resource blocks | PASS — P4 |
| PX10 | READ/READ compatible | PASS — P1 |
| PX11 | READ/WRITE protected | PASS — pair overlap guard |
| PX12 | WRITE/WRITE protected | PASS — P3 |
| PX13 | Value gate supports sequential | PASS — `test_no_material_value_defaults_to_sequential` |
| PX14 | Value gate supports parallel | PASS — P1 |
| PX15 | Maximum parallel children is 2 | PASS — constant and P12 |
| PX16 | No idle worker pool | PASS — short-lived threads only after selection; joined before return |
| PX17 | Each child satisfies C15 | PASS — two C15 controllers per group |
| PX18 | Child permissions are a subset | PASS — C15 subset gate reused |
| PX19 | Aggregate permission safety | PASS — aggregate grants/budgets gate |
| PX20 | Child `DELEGATE=false` | PASS — group result/record and C15 context |
| PX21 | Delegation depth is 1 | PASS — C15 and group constant |
| PX22 | Handoff contexts isolated | PASS — distinct task bindings and context-ref conflict gate |
| PX23 | Distinct execution/result bindings | PASS — persisted group child refs |
| PX24 | Worker output is not evidence | PASS — explicit `worker_output_is_evidence=false` |
| PX25 | Independent verification | PASS — each C15 child verification required |
| PX26 | Combined integration verification | PASS — combined verifier required for mutation groups |
| PX27 | One success/one failure preserved | PASS — P8 |
| PX28 | Unknown mutation freezes continuation | PASS — P9 |
| PX29 | Retry remains bounded | PASS — inherited finite C15 budgets; no unbounded loop |
| PX30 | No third rescue worker | PASS — max-two selection and no rescue path |
| PX31 | Cancellation is truthful | PASS — cancellation status records unavailable/failed/requested/not-needed |
| PX32 | Control-plane failure stays control-plane | PASS — malformed ledger and explicit failure states |
| PX33 | Unknown identity preserved | PASS — C15 `UNKNOWN` is never inferred |
| PX34 | Identity-required failure blocks affected group | PASS — P7 |
| PX35 | No background runtime | PASS — `background_execution=false`, joined foreground threads |
| PX36 | No scheduler/queue | PASS — no scheduler/queue surface introduced |
| PX37 | No remote bridge | PASS — no remote/network execution path |
| PX38 | No worker pool | PASS — no persistent pool; exactly two transient threads |
| PX39 | No automatic 8-agent quorum | PASS — no quorum/runtime identity path |
| PX40 | C10 preserved | PASS — existing ledger/Decision Trace is reused |
| PX41 | C11 preserved | PASS — full regression and shared store |
| PX42 | C12 preserved | PASS — C12 regression suite |
| PX43 | C13/C14 preserved | PASS — full regression and package doctor |
| PX44 | C15 preserved | PASS — C15 regression subset and additive group context |
| PX45 | C16 roadmap/lineage preserved | PASS — durable `.20` reconciliation and C17 provenance |
| PX46 | C08 deferred | PASS — control/status projection |
| PX47 | C09 blocked | PASS — `EVENT_EVIDENCE_UNAVAILABLE` preserved |
| PX48 | Official `.19` immutable | PASS — before/after hash exact |
| PX49 | Canonical count is 8 | PASS — doctor/control 8/8 |
| PX50 | Aesthetica optional/noncanonical | PASS — doctor and capability manifest |

## Result

The matrix supports `PASS / PARALLEL_EXECUTION_FOUNDATION_READY`. It does not
upgrade the separate `LIVE_PARALLEL_EXECUTION_CERTIFIED` field, which remains
`NO / NOT_CERTIFIED` because no supported native host callback/identity receipt
was available.

## Cognitive Economy Addendum Matrix

| Case | Expected policy | Result |
|---|---|---|
| CE1 | tiny independent pair → sequential/direct | PASS |
| CE2 | meaningful independent pair may parallelize | PASS |
| CE3 | duplicated large context → sequential | PASS |
| CE4 | missing acceptance context → `CONTEXT_INSUFFICIENT`, never false parallel PASS | PASS |
| CE5 | worker narrative becomes structured parent delta | PASS |
| CE6 | extensive + tiny does not parallelize merely by readiness | PASS |
| CE7 | independent review can justify extra bounded worker | PASS |
| CE8 | deterministic verification uses no worker | PASS |
| CE9 | lower local context proxy avoids duplicated-large-context overhead | PASS |
| CE10 | result-context dependency escalates | PASS |

The CE matrix evaluates quality-adjusted policy behavior only. It does not
claim a universal optimum, token/cost savings, wall-clock savings, or live host
certification.
