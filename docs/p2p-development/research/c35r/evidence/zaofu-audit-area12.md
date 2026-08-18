# Audit Findings: Supervisor & Run Manager

## 1. Run Manager

The Run Manager is implemented as a deterministic tick-based recovery and supervision layer. It operates over existing deterministic actuators, deriving state from events and projections, asking the `ControlledActionService` to mutate truth, and recording post-verification events. It does not introduce a second queue or write kernel-managed stores directly.

Key classes and functions include `RunManagerTickResult` (`src/zf/runtime/run_manager.py:217`), a dataclass representing the result of a single tick, tracking actions applied, blocked, failed, repairs accepted/dispatched, etc. The main entry point is `run_manager_tick` (`src/zf/runtime/run_manager.py:255`), which executes a bounded Run Manager observe/decide/act/verify tick. It uses a lock (`run-manager-tick`) to ensure serialization. Additionally, `run_manager_watchdog_tick` (`src/zf/runtime/run_manager_watchdog.py:45`) provides a watchdog mechanism for the Run Manager.

The core semantic of the Run Manager is the serialization of the observe/decide/act/verify loop into one lease-owned tick. It applies deterministic actions, such as recovering unrecorded writer fanout results via the `recover_unrecorded_writer_fanout_results` function from the `zf.runtime.fanout_recovery` module. It also converges unrecoverable escalations through the `escalation_terminal` module. The system is heavily event-driven, relying on events like `run.manager.tick.started`, `run.manager.tick.completed`, `run.manager.action.applied`, and `run.manager.action.failed`.

In terms of coupling and boundaries, the Run Manager depends on the `ControlledActionService` (via `zf.runtime.control_actions`), `EventWriter`, `TaskStore`, `zf.core.config.schema.ZfConfig`, and `zf.core.events.log.EventLog`. It is depended upon by the overall orchestration loop, likely called periodically or on state changes. Crucially, it strictly avoids direct mutation of kernel-managed stores, delegating truth mutations to the `ControlledActionService`.

Extensive tests are present in `tests/test_run_manager.py`, `tests/test_run_manager_watchdog.py`, and others. The assessment of provider neutrality is neutral, as the Run Manager logic relies on internal state, events, and controlled actions without provider-specific hooks or dependencies visible at this layer.

## 2. Supervisor

The Supervisor focuses on control loops, attention mechanisms, and inspection. Key functions include `supervisor_decision_projection` (`src/zf/runtime/supervisor_control_loop.py:121`), which derives decisions from events, particularly `supervisor.decision.recorded`. Another important function is `supervisor_snapshot_ref` (`src/zf/runtime/supervisor_inspection.py:352`), which captures a snapshot reference of the state directory. The `supervisor_attention` module (`src/zf/runtime/supervisor_attention.py`) handles attention events and proposals.

The supervisor tracks routes and outcomes of decisions using capabilities with specific required fields and optional requirements like `owner_approval_required`. It classifies events into failure classes (e.g., `plan_admission`, `semantic_replan`) and intervention classes. The Supervisor depends on `ZfEvent`, `EventWriter`, and `TaskStore`. It is depended upon by the human-in-the-loop mechanisms or automated attention handlers.

Tests for the Supervisor are present in `tests/test_supervisor_attention.py`, `tests/test_supervisor_control_loop.py`, and `tests/test_supervisor_inspection.py`. The provider neutrality is assessed as neutral, as the supervisor logic is generic to the platform's internal events and states.

## 3. Autopilot

The Autopilot is a deterministic proposal runner. It scans existing runtime truth and emits attention proposals. It never mutates task/session truth directly. Key classes include `AutopilotProposal` (`src/zf/runtime/autopilot.py:41`), which represents a proposal with kind, severity, title, reason, and optional action. The main function is `run_autopilot_tick` (`src/zf/runtime/autopilot.py:87`), which scans runtime state and emits proposal events when configured.

The core semantic is that Autopilot v1 is explicitly proposal-only. It writes only `autopilot.proposal.created` events. The function is deterministic over kanban/events inputs plus the current time. It detects blocked tasks and stale tasks based on configuration thresholds like `stale_after_hours` and `failed_event_window_hours`.

The Autopilot depends on `TaskStore`, `EventLog`, and `ZfConfig`. It is depended upon by external systems or human operators that review proposals. Tests are present in `tests/test_autopilot.py`. The provider neutrality is neutral, as it operates purely on internal state and events.

## 4. Control Actions (Recovery & Workflow Replay)

Control actions provide deterministic verbs for recovery and workflow manipulation. The `RecoveryActionsMixin` (`src/zf/runtime/control_actions_recovery.py:32`) provides helper methods for recovery actions. Recovery verbs include `task-requeue`, `child-rebuild`, `stage-retrigger`, `stage-replan-new-generation`, `fanout-aggregate-rebuild`, and `rescan-grant`. The `replay_active_workflow_start` function (`src/zf/runtime/control_actions_workflow_replay.py:14`) handles fail-closed replay for active workflow requests.

The design emphasizes fail-closed behavior where preconditions must be met before an action is applied. If conditions aren't met, the action is rejected. Actions are designed to be idempotent. The replay mechanism checks for active workflow requests and returns the existing invocation without revising an active request.

These actions depend on the `ControlledActionService` base class, `TaskStore`, and `EventWriter`. They are depended upon by the Run Manager and other orchestrators triggering these actions. The provider neutrality is neutral, as these actions manipulate internal task graphs and event streams without provider-specific logic.

## 5. Delivery Cycles & Run Groups

These modules provide read-only projections for delivery tracking. Key functions include `build_delivery_cycles` (`src/zf/runtime/delivery_cycles.py:52`), which returns delivery cycles and autoresearch cycles for `delivery-trace.v1`. The `build_run_groups` function (`src/zf/runtime/delivery_run_groups.py:19`) builds a run-group projection for the Delivery cockpit.

The projections are intentionally read-only, deriving delivery/autoresearch cycles from already-loaded events. They track phases, fanouts, rework, replans, and shipping cycles. These modules depend on `ZfEvent` and `Task`, and are depended upon by UI cockpits or reporting tools. Extensive tests cover these components, such as `test_delivery_trace.py`. The provider neutrality is neutral, as it is purely data aggregation from internal events.

## Summary Table

| Component | Key Files | Provider Neutrality | Core Mechanism |
| :--- | :--- | :--- | :--- |
| Run Manager | `src/zf/runtime/run_manager.py` | Neutral | Deterministic tick-based recovery via observe/decide/act/verify loop. |
| Supervisor | `src/zf/runtime/supervisor_*.py` | Neutral | Attention routing, control loops, and inspection projections. |
| Autopilot | `src/zf/runtime/autopilot.py` | Neutral | Deterministic, proposal-only detection of stale or blocked tasks. |
| Control Actions | `src/zf/runtime/control_actions_*.py` | Neutral | Fail-closed, idempotent deterministic verbs for recovery and replay. |
| Delivery Tracking | `src/zf/runtime/delivery_*.py` | Neutral | Read-only projections for tracking delivery cycles and run groups. |

## Summary
The ZaoFu platform implements a robust, event-driven Supervisor and Run Manager architecture. The Run Manager operates via deterministic, lease-locked ticks that observe state, decide on recovery actions (delegating truth mutations to a `ControlledActionService`), act, and verify. Recovery actions (e.g., `task-requeue`, `child-rebuild`) are strictly fail-closed, requiring preconditions to be met before execution. The Supervisor handles attention routing and control loop projections, while the Autopilot provides a deterministic, proposal-only mechanism for detecting stale or blocked tasks without direct mutation. Delivery cycles and run groups are exposed via read-only projections for tracking. Extensive unit tests cover these components, and the architecture remains strictly provider-neutral, relying entirely on internal events and state projections.
