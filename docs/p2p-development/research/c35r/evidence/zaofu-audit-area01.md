# Audit Findings: Area Group 1 — DETERMINISTIC KERNEL & ORCHESTRATOR

## 1. What ZaoFu Actually Implements

ZaoFu implements a highly deterministic, event-driven state machine architecture for managing tasks, workers, and sessions. The core of this system is located in `src/zf/core/statemachine/` and `src/zf/runtime/`.

ZaoFu utilizes pure transition logic without I/O in `src/zf/core/statemachine/`. The `task.py` file defines the `TaskStateMachine` with states like `backlog`, `in_progress`, `review`, `testing`, `blocked`, `done`, and `cancelled`. The `worker.py` file defines the `WorkerStateMachine` with states like `idle`, `working`, `refreshing`, `blocked`, `crashed`, and `stopping`. The `session.py` file defines the `SessionStateMachine` with states like `created`, `bootstrapping`, `active`, `degraded`, `shutdown_requested`, and `stopped`. Finally, the `loop.py` file defines the `LoopStateMachine` with states like `starting`, `running`, `waiting`, `paused`, `recovering`, `completed`, `failed`, and `terminated`.

The `src/zf/core/reactor/` directory contains the `EventActionRegistry` (`registry.py`) which manages event handlers. It supports both built-in Python handlers and YAML-declared actions such as `emit`, `log`, and `noop`.

In `src/zf/runtime/action_orchestrator.py`, the `ControlledActionOrchestrator` wraps deterministic action handlers with attempt and result events, providing a stable result envelope for Web/API callers and replay tooling.

Additionally, `src/zf/runtime/agent_live.py` contains the `project_agent_live` function, which tracks task and worker states based on events such as `task.assigned`, `dev.build.done`, and `worker.heartbeat`.

## 2. Key Implementation Semantics

The system enforces strict transition rules through deterministic state machines. For example, a Task cannot transition directly from `backlog` to `done`; it must progress through `in_progress`, `review`, and `testing`.

The architecture relies heavily on an event-driven model. Actions are triggered by events, and the `EventActionRegistry` routes these events to appropriate handlers.

The `ControlledActionOrchestrator` ensures that actions are executed in a controlled manner. It records execution boundaries and adds a stable result envelope, which is crucial for replayability and debugging.

Furthermore, the reactor supports YAML-declared side effects, allowing for custom event handling without the need to modify the underlying Python code.

## 3. Coupling and Boundaries

The state machines are pure logic modules that do not perform I/O, making them highly decoupled from the underlying storage or execution environments. They depend only on the `InvalidTransition` exception defined in `task.py`.

The `EventActionRegistry` acts as a bridge between the core event system and higher-level orchestration logic. It depends on `zf.core.events.log.EventLog` and `zf.core.events.model.ZfEvent`.

The `ControlledActionOrchestrator` depends on `zf.core.events.EventWriter` and `zf.core.events.ZfEvent`. It is tightly coupled to the event writing mechanism but remains independent of the specific business logic of the actions it orchestrates.

The `project_agent_live` function is a projection layer that consumes events to build a real-time view of the system state. It depends on `zf.core.cost.tracker.CostTracker` and `zf.core.events.log.EventLog`.

## 4. Maturity Signals

The state machines are well-defined with clear transition tables, and the code is clean, following good object-oriented practices.

The `EventActionRegistry` is designed to be extensible and supports both built-in and YAML-declared handlers, indicating a mature and flexible design.

The `ControlledActionOrchestrator` provides a robust mechanism for tracking action attempts and results, which is essential for debugging and replayability.

The `project_agent_live` function provides a clear, real-time view of the system state, which is highly valuable for monitoring and operations.

## 5. Provider Neutrality

The audited areas are largely provider-neutral. The state machines, reactor, and orchestrator are designed to be independent of specific cloud providers or execution environments. They rely on generic concepts like events, actions, and state transitions rather than provider-specific APIs.
