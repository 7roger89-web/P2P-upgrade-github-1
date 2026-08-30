# P2P-FASTPATH-WIRE-01 — fast-path seam wiring evidence

## Scope

Wire the already-computed C18 execution-lane and minimum-sufficient-work
decision through the existing workflow result/ledger/report exposure seam.
No new router, ontology, context system, council, or workflow framework was
created. The change is additive read-only metadata.

- `FRESH_MAIN_SHA` = `d661654746f090136f37370f76578ee345b74994` (matches expected)
- `FRESH_MAIN_TREE` = `92895a93a560221bdcd4664992ab16a4e8ec8cb4`

## Existing seams reused (not created)

- `.p2p/system/p2p_capabilities/orchestration_policy.py` already computes
  `execution_lane` (FAST/STANDARD/STRICT/CRITICAL), `execution_policy`
  (`minimum_sufficient_work` / `risk_proportional_execution`), `test_ceiling`
  (`selected_level`, `broad_full_regression`), and `stop_rule` (`stop_after`).
- `scripts/p2p_workflow.py` already bridges request → C18 profile
  (`derive_orchestration_requirement`), C19 context
  (`task_targeted_context_metadata`), agent selection (`select_agents`), and
  result exposure (`orchestration_result_fields`, `verification_surface_for`).

## Gap that was closed

The policy computed the lane / minimum-sufficient / stop-rule decision, but the
workflow result-exposure seam dropped those fields. Downstream (`run_workflow`
result, execution ledger, beginner report) could not see the proportional route
the policy had already selected. Two existing functions now forward the existing
values.

## Before / after (same requests, same policy)

| Request | worker_strategy | execution_lane (before) | execution_lane (after) | test_ceiling_level (after) | broad_full_regression | proportional_route |
|---|---|---|---|---|---|---|
| Prompt composition (low-risk) | DIRECT | not surfaced | FAST | TARGETED_EVIDENCE | false | true |
| Local implementation | ONE_WORKER | not surfaced | STANDARD | DIRECTLY_AFFECTED_MODULE | false | true |
| High-impact prod arch + deploy | BLOCKED | not surfaced | CRITICAL | BROAD_FULL_REGRESSION | true | false |

Before: `orchestration_result_fields` / `verification_surface_for` did not
expose `execution_lane`, `minimum_sufficient_work`, `test_ceiling_level`,
`broad_full_regression`, or `stop_after`. After: all are surfaced from the
already-computed policy output.

## Low-risk fast path (materially lower overhead)

For the prompt-composition fixture the surfaced route is FAST /
DIRECT / MINIMAL context / DETERMINISTIC verification / stop after
`TARGETED_EVIDENCE`, `broad_controls_entered=false` — no council, no quorum, no
broad regression, minimum context (1 source, 0 escalations).

## High-risk gates preserved

The high-impact production-architecture-with-deployment fixture still resolves
to CRITICAL lane, `worker_strategy=BLOCKED`, `verification_class=HIGH_RISK`,
`broad_full_regression=true`, `proportional_route=false`, and the run reports an
Owner decision requirement. Owner gates, evidence requirements, and
security/release discipline are unchanged.

## Focused tests

`python3 -m unittest tests.test_p2p_lightweight_fastpath` — 21/21 PASS
(18 preserved + 3 new lane/stop-rule surfacing tests).

Adjacent shared-file suites (no regression):
- `tests.test_p2p_workflow` — 7/7 PASS
- `tests.test_p2p_eff01_execution_efficiency` — 7/7 PASS
- `tests.test_p2p_projection_bundle` — 17/17 PASS

Out of scope / pre-existing: `tests.test_p2p_game_toolchain_02a` has 2
failures + 1 error at the unmodified baseline (fixture hash mismatches); not
caused by this change and not in scope for this workstream.
