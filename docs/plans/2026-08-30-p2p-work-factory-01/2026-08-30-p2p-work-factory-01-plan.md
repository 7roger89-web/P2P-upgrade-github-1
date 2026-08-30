# Plan — P2P-WORK-FACTORY-01: minimum durable multi-executor work-item and handoff flow

## Goal

Implement the smallest durable flow:

```
GOAL -> WORK_ITEM -> EXECUTION_LANE -> RETURN_PACKET -> INTEGRATION_QUEUE -> VERIFY -> OWNER_GATE
```

Two non-overlapping fixture work items assigned to different executors must be able to
start from explicit base identity, return independent result packets, retain provenance,
enter an integration queue without ambiguity, and preserve Owner/review gates.

## Reused seams (no new ontology, no second Control Tower, no new store)

| Flow step        | Existing seam reused                                                                 |
| ---------------- | ------------------------------------------------------------------------------------ |
| GOAL             | explicit `PROJECT` + `WORKSTREAM` binding on the work item (no goal system invented) |
| WORK_ITEM        | durable identity registered as events in the existing `.p2p/state/execution-ledger.jsonl` via the existing ledger writer (`p2p_workflow.append_event`, same surface the Control Tower uses) |
| EXECUTION_LANE   | executor = existing Control Tower host lane (`normalize_host`); CT session registered through `ControlTower.start_session` |
| RETURN_PACKET    | existing `ControlTowerReturnPacket` / `ControlTower.ingest_response` (binding check, idempotent replay, stale-base reconciliation) |
| INTEGRATION_QUEUE| deterministic replay projection of the same execution ledger (like `ControlTower.snapshot`) |
| VERIFY           | pure fail-closed projection; never executes a protected action                        |
| OWNER_GATE       | carried through from the packet's existing `OWNER_GATE` field; never resolved here    |

## New (minimum glue only)

- `.p2p/system/p2p_capabilities/work_item_handoff.py`
  - `WorkItem` minimum durable identity: `WORK_ITEM_ID, PROJECT, WORKSTREAM,
    BASE_SHA, BASE_TREE, EXECUTOR, SCOPE, DEPENDENCIES, EXPECTED_OUTPUT,
    SESSION_ID` + runtime `CANDIDATE_SHA, CANDIDATE_TREE, VERDICT, NEXT_GATE`.
  - Three event types in the existing ledger: `WORK_ITEM_REGISTERED`,
    `WORK_ITEM_LANE_STARTED`, `WORK_ITEM_RETURN`.
  - `WorkItemHandoff` coordinator: `register_work_item`, `start_lane`,
    `ingest_return`, `integration_queue`, `verify_integration_queue`.
  - Fail-closed detection: duplicate/conflicting work-item identity,
    ambiguous project/workstream binding, stale base, missing candidate
    identity, scope overlap, orphan returns, lane-order violations, cycles.
- `scripts/p2p_work_item.py` — thin foreground CLI (register / lane / return / queue / verify).
- `tests/test_p2p_work_item_handoff.py` — focused acceptance tests (two parallel
  fixtures, owner-gate preservation, conflict/stale/ambiguous fail-safe cases, CLI smoke).

## Explicitly out of scope

No generic scheduler, no worker pool, no new ontology, no second Control Tower,
no new authority framework, no Fast Path redesign, no MPFB/TMPGC/Game Truyen,
no Execution Host, no merge/promote/release/deploy.

## Verification

- `python3 -m unittest tests.test_p2p_work_item_handoff -v` (new, focused).
- Adjacent shared suites stay green: `test_p2p_control_tower_durable`,
  `test_p2p_control_tower_session_handoff`, `test_p2p_task_state`,
  `test_p2p_parallel_execution`.
