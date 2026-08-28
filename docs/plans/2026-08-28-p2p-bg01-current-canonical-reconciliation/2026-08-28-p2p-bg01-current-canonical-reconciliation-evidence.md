# P2P-BG01 Current-Canonical Reconciliation Evidence Ledger

## Metadata

- Date: 2026-08-28
- Plan: docs/plans/2026-08-28-p2p-bg01-current-canonical-reconciliation/2026-08-28-p2p-bg01-current-canonical-reconciliation-plan.md
- Evidence: docs/plans/2026-08-28-p2p-bg01-current-canonical-reconciliation/2026-08-28-p2p-bg01-current-canonical-reconciliation-evidence.md
- Benchmark: docs/plans/2026-08-28-p2p-bg01-current-canonical-reconciliation/2026-08-28-p2p-bg01-current-canonical-reconciliation-benchmark.md
- Actual status: docs/plans/2026-08-28-p2p-bg01-current-canonical-reconciliation/2026-08-28-p2p-bg01-current-canonical-reconciliation-actual-status.md

## Evidence Rules

Evidence must identify the exact candidate source, observable behavior, focused command result, and current safety boundary. No technical PASS is treated as Owner approval or promotion authority.

## E0 - P0 Evidence

Matching plan item(s): P0-A

- E0-P0A-ID1: Fresh git ls-remote against the official origin returned 34ece1d1b804d0b794c56d51acba649b2d4a88c5 for refs/heads/main. Clean source worktree worktrees/p2p-lightweight-fastpath-03-final returned the same HEAD and tree b3f541df0ba2215a4d752e67aa3672a22e242acb with zero status lines.
- E0-P0A-ID2: P2P-canonical-runtime-01 remains at 28a85bc6 with 42734b3c tree and 1133 dirty status lines; it was not used as authority or mutation target.
- E0-P0A-ID3: Old BG01 candidate is 86def9330ab343f345a365529bf39687c768de9c with tree 470aa76876ed468aaaf35b5abfa6dec063848827 and direct parent 28a85bc6; it is dirty/evidence-only.
- E0-P0A-SRC1: Current canonical scripts/p2p_workflow.py contains the existing C18/C19 lightweight-fastpath seams; old BG01 adds capability_api, beginner_entrypoint, beginner_public_result, and CLI dispatch around the same workflow file.
- E0-P0A-SRC2: Old BG01 changes are beginner_gateway.py added, test_p2p_bg01_beginner_gateway.py added, and scripts/p2p_workflow.py modified. Current canonical has no beginner_gateway.py or BG01 focused test.
- E0-P0A-SRC3: Current canonical contains tests/test_p2p_lightweight_fastpath.py and the current workflow implementation from 82d6bffc followed by 34ece1d1. These are preserve-only and directly affected by the shared workflow path.
- E0-P0A-SPEC1: Read the full relevant capability foundation, routing/readiness, context-pointer, execution/evidence, trust/data-instruction, project-domain, and decision-trace specifications. They require one router, existing state/evidence/approval authority, progressive disclosure, fail-closed safety, and no competing truth store.

## E1 - P1 Evidence

Matching plan item(s): P1-A, P1-B, P1-C

- E1-P1A-SRC1: Added .p2p/system/p2p_capabilities/beginner_gateway.py from the old BG01 source checkpoint through apply_patch. The module is a pure bounded charter/projection layer and calls existing C18 derive_requirement only; it does not execute, select providers, grant permissions, or persist state.
- E1-P1A-TEST1: Added tests/test_p2p_bg01_beginner_gateway.py with eight acceptance tests covering Vietnamese new-project intake, English existing-project improvement, material ambiguity, hidden/default and advanced projections, recovery reuse, conflicting state, protected input, and empty input.
- E1-P1B-SRC1: Added capability_api, _beginner_decision_charter, beginner_entrypoint, and beginner_public_result to scripts/p2p_workflow.py. The entrypoint binds existing write_goal, TaskStateStore, Control Tower next_safe_session, and execution-ledger event surfaces. build_goal_contract receives package_hint and continues to use current C18/C19 policy.
- E1-P1B-DIFF1: CLI adds only the existing parser/main seam named beginner and its render path. No change was made to orchestration_policy.py, context.py, task_state.py, control_tower_handoff.py, or tests/test_p2p_lightweight_fastpath.py.
- E1-P1C-COMPILE1: python -m py_compile scripts/p2p_workflow.py .p2p/system/p2p_capabilities/beginner_gateway.py tests/test_p2p_bg01_beginner_gateway.py returned exit 0.
- E1-P1C-TEST1: python -X utf8 tests/test_p2p_bg01_beginner_gateway.py returned 8/8 PASS; python -X utf8 tests/test_p2p_workflow.py returned 7/7 PASS; python -X utf8 tests/test_p2p_lightweight_fastpath.py returned 18/18 PASS; python -X utf8 tests/test_p2p_eff01_execution_efficiency.py returned 7/7 PASS.
- E1-P1C-ID1: The candidate remains based on 34ece1d1 / b3f541df. The source-worktree 34ece1d worktree and official remote main were not modified. The first workflow run from a .tmp candidate path exposed an existing transient-path test assumption; the same candidate worktree was moved outside .tmp, not recreated, and the workflow test passed 7/7.
- E1-P1C-SAFETY1: Focused tests prove automatic_start remains false, protected input does not authorize execution, existing task state is not overwritten, recovery reuses existing state, and no new router/orchestrator/provider/truth-store file was introduced.

## Closure Evidence

- E2-PnA-SUP1: Independent read-only Supervisor review passed. The report confirms the current-canonical base, empty preserve-only path matches for the fastpath/policy/state surfaces, BG01 acceptance coverage, and no duplicate authority. Anvien was not run because the user explicitly prohibited it.
- E2-PnB-DIFF1: Candidate status and changed-path review found only the bounded BG01 gateway/test, one surgical `scripts/p2p_workflow.py` seam, and candidate-only plan/evidence/report artifacts. No dead implementation, replacement candidate, or transient test artifact remains.
- E2-PnC-ID1: Implementation checkpoint is `1012428798ed43027d24ba57b7551321ee5e15fe` with tree `84a612c17f413df5e967f4a3dad7a8d01f286ea2`, parent `f735d437473ecb158d472928dc2454a0c7a56967`, and current canonical base `34ece1d1b804d0b794c56d51acba649b2d4a88c5` as an ancestor. The final evidence-only closure commit is the new candidate subject reported after commit verification.
- E2-PnC-TEST1: Reused focused results remain BG01 `8/8`, direct workflow `7/7`, lightweight-fastpath `18/18`, EFF01 `7/7`, and targeted compile PASS; no test was rerun during report closure.
- E2-PnC-BOUNDARY1: `OWNER_APPROVAL_REUSABLE=NO`, `OWNER_GATE_REQUIRED=YES`, and `CANONICAL_PROMOTED=NO`. No canonical checkout, remote main, deployment, or live runtime was changed.
