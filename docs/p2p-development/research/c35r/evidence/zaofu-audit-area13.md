# Audit Findings: Bounded Retry, Recovery, Replay & Idempotence

## 1. Bounded Retry & Recovery Mechanics
**Implementation:** ZaoFu implements a sophisticated bounded retry and recovery mechanism primarily within `src/zf/runtime/canonical_recovery.py` and `src/zf/core/statemachine/loop.py`. The `LoopStateMachine` (`src/zf/core/statemachine/loop.py`) defines the lifecycle of an iteration, allowing transitions from `failed` to `recovering`, and then back to `running` or `failed`. This provides a foundational state machine for managing recovery loops.
**Key Classes/Functions:**
- `src/zf/core/statemachine/loop.py:LoopStateMachine`: Manages the iteration lifecycle, including `recovering` states.
- `src/zf/runtime/canonical_recovery.py:RecoverySeries`: Represents a series of recovery attempts for a specific task and contract revision.
- `src/zf/runtime/canonical_recovery.py:rework_dispatch_count`: Counts valid dispatches to enforce retry bounds.
- `src/zf/runtime/canonical_recovery.py:build_rework_cap_payload`: Constructs the payload for a retry attempt, including the `max_attempts` and `retry_count`.
**Semantics:** The system enforces strict retry bounds by tracking the number of failures and dispatches for a specific recovery series. The `rework_dispatch_count` function ensures that the number of retries does not exceed the `max_attempts` configured for the task. The `build_rework_cap_payload` function injects `retry_count` and `max_attempts` into the event payload, making the retry bounds explicit to the downstream processing logic.
**Coupling/Boundaries:** The recovery mechanics are tightly coupled with the event system (`zf.core.events.model.ZfEvent`) to track failures and dispatches. They depend on the state machine to manage transitions and are consumed by the orchestration layer to decide whether to retry or escalate.
**Maturity Signals:** The presence of extensive test coverage (e.g., `tests/test_rework_cap.py`, `tests/test_task_attempt_recovery.py`) and integration tests (`tests/integration/test_pane_crash_recovery.py`) indicates a high level of maturity. The logic is heavily tested against various failure scenarios.
**Provider Neutrality:** The core retry and recovery logic in `canonical_recovery.py` and `loop.py` is provider-neutral. It operates on abstract events and state transitions without assuming a specific underlying execution environment.

## 2. Replay Mechanics & Idempotence
**Implementation:** Idempotence and replay mechanics are handled by deduplicating events and tracking unique identities within the recovery series. The `canonical_recovery.py` module uses event identities (e.g., `result_event_id`, `source_event_id`, `causation_id`) to ensure that the same failure is not retried multiple times.
**Key Classes/Functions:**
- `src/zf/runtime/canonical_recovery.py:valid_series_failures`: Filters events to count valid semantic failures, explicitly ignoring events marked as `replay` or `stale`.
- `src/zf/runtime/attempt_handoff_reducer.py:reduce_attempt_handoffs`: Reduces a sequence of events to determine the current state of an attempt, ensuring that only unique and relevant events are processed.
**Semantics:** The system achieves idempotence by checking event payloads for `replay` or `stale` flags and deduplicating based on event identities. The `valid_series_failures` function ensures that only distinct, non-superseded failures are counted towards the retry limit. The `attempt_handoff_reducer` processes events to determine the current state of a task attempt, ignoring redundant or superseded handoffs.
**Coupling/Boundaries:** These mechanics are deeply integrated with the event log system. They rely on the accurate recording of event IDs and causation chains to function correctly.
**Maturity Signals:** The extensive test suite for recovery scenarios (e.g., `tests/test_recovery_delta.py`, `tests/test_fanout_recovery_runtime.py`) demonstrates that idempotence and replay mechanics are well-validated.
**Provider Neutrality:** The idempotence logic is provider-neutral, as it relies solely on the abstract event model and event IDs, independent of the specific provider executing the task.

## 3. Rework Evidence Requirements
**Implementation:** The system requires explicit evidence of failures to trigger and guide the rework process. The `candidate_rework.py` module classifies failures and generates rework messages based on the actual output of failing checks.
**Key Classes/Functions:**
- `src/zf/runtime/candidate_rework.py:candidate_quality_failure_message`: Extracts actual error messages (stdout/stderr) from failing quality gate checks to provide concrete evidence for rework.
- `src/zf/runtime/candidate_rework.py:quarantine_candidate_from_plan`: Generates a bug candidate (issue) when the rework cap is exhausted, carrying the findings as evidence.
**Semantics:** Instead of simply retrying on any failure, ZaoFu mandates that failures provide actionable evidence. The `candidate_quality_failure_message` function ensures that the rework process receives the specific error output (e.g., "Cannot find module '../lib/task-store'") rather than just the command that failed. This prevents the system from blindly guessing and exhausting the rework cap. When the cap is reached, the `quarantine_candidate_from_plan` function creates a formal issue (bug candidate) with the unresolved findings, ensuring that failures are not silently dropped.
**Coupling/Boundaries:** This logic is coupled with the verification and quality gate systems. It depends on the output of these checks to generate rework messages and issues.
**Maturity Signals:** The presence of tests like `tests/test_rework_triage.py` and `tests/test_rework_fingerprint_counting.py` indicates that the rework evidence requirements are well-defined and tested.
**Provider Neutrality:** The rework evidence logic is largely provider-neutral, as it focuses on the abstract verification results and event payloads rather than provider-specific execution details. However, some specific error parsing (e.g., npm errors) hints at awareness of the underlying execution environment.

## 4. State Machine Loop Semantics
**Implementation:** The state machines in `src/zf/core/statemachine/` (`task.py`, `loop.py`, `session.py`, `worker.py`) provide the pure transition logic for various aspects of the system.
**Key Classes/Functions:**
- `src/zf/core/statemachine/task.py:TaskStateMachine`: Manages the lifecycle of a task (e.g., `backlog` -> `in_progress` -> `review` -> `testing` -> `done`).
- `src/zf/core/statemachine/loop.py:LoopStateMachine`: Manages the lifecycle of an iteration loop, including `recovering` states.
**Semantics:** The state machines enforce strict transition rules. For example, a task can only transition from `failed` to `recovering` or `terminated`. A loop can transition from `recovering` back to `running` or `failed`. This ensures that the system progresses in a controlled and predictable manner.
**Coupling/Boundaries:** The state machines are isolated modules with no external I/O dependencies, making them easy to test and reason about. They are consumed by the orchestration layer to manage the flow of execution.
**Maturity Signals:** The simplicity and isolation of the state machines, along with the extensive test coverage in the surrounding modules, suggest a mature and well-thought-out design.
**Provider Neutrality:** The state machines are entirely provider-neutral, operating purely on abstract states and transitions.
