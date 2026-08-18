# Area Group 4: Task Graph & Dependencies

## 1. Task Graph & Dependency Representation

ZaoFu implements task dependencies through a Directed Acyclic Graph (DAG) representation within its workflow specifications. The system translates legacy workflow definitions and safe Generic Workflow specifications into a canonical stage representation that enforces strict dependency constraints.

**Implementation Evidence:**
The workflow specification relies on `src/zf/core/workflow/workflow_kind.py:WorkflowKindCompilation` and the `_translate_legacy_workflow_kind` function to process tasks that declare dependencies via a specific `dependencies` key. To ensure structural integrity, `src/zf/core/workflow/generic_workflow.py:_validate_dag` performs a depth-first search to validate that the workflow definition does not contain cycles, raising a `GenericWorkflowError` if one is detected. At the schema level, `src/zf/core/task/schema.py:Task` includes a `parent_task_id` field, indicating hierarchical task relationships. Furthermore, `src/zf/core/workflow/generic_workflow_catalog.py` defines `DEPENDENCY_BARRIER_EVENT` and `DEPENDENCY_BARRIER_BLOCKED_EVENT` to manage multi-dependency joins.

**Key Implementation Semantics:**
Dependencies are resolved by name, and the system enforces a strict DAG structure. When a task has a single dependency, its trigger is automatically set to the success event of that dependency (formatted as `{dependency}.completed`). For tasks with multiple dependencies, a dependency barrier is created, requiring all specified dependency success events to be satisfied before the task can proceed. Additionally, `src/zf/runtime/channel_question_graph.py` manages question dependencies by validating identity, dependency existence, and acyclicity, utilizing a `depends_on` field to reference other question IDs.

## 2. Fanout and Parallel Child Tasks

ZaoFu supports the parallel execution of child tasks through a robust fanout mechanism. This allows a single parent task to spawn multiple child tasks that can execute concurrently, enabling complex, multi-agent workflows.

**Implementation Evidence:**
The fanout configuration is handled in `src/zf/core/workflow/workflow_kind.py`, which processes the `fanout` key in task definitions and requires either `roles` or `fromTaskMap`. Based on the configuration, the system assigns specific topologies, such as `fanout_reader` (when roles are specified) or `fanout_writer_scoped` (when a task map is used). At runtime, `src/zf/runtime/delivery_run_groups.py` manages these fanout runs by creating `delivery-run-group.v1` schemas with `children` fields to track parallel tasks. To handle errors gracefully, `src/zf/runtime/writer_fanout_dependency_failure.py` implements deterministic dependency-failure closure, ensuring that queued descendants are failed if an upstream dependency fails.

**Key Implementation Semantics:**
The fanout mechanism supports two primary types: `fanout_reader`, which spawns child tasks based on specified roles, and `fanout_writer_scoped`, which spawns child tasks based on a task map. The joining of results from these parallel tasks is controlled by an `aggregate` configuration within the fanout definition. This aggregate specifies the execution mode (such as `wait_for_all` or `candidate_integration`), as well as the specific `child_success_event` and `child_failure_event` that dictate how the parallel execution concludes.

## 3. Coupling and Boundaries

The task graph system is deeply coupled with the workflow configuration (`workflow.dag`) and the underlying event system, which triggers tasks based on dependency completion. The deterministic kernel, orchestrator, and runtime execution engines depend heavily on the resolved task graph to schedule and execute tasks correctly. The `WorkflowKindCompilation` serves as a critical boundary, translating high-level workflow specifications into canonical stage dictionaries that the execution engine can process without needing to understand the original syntax.

## 4. Maturity Signals

The system exhibits strong maturity signals, particularly in its testing and documentation. There are extensive end-to-end tests for the fanout mechanism, most notably the 322KB `tests/test_writer_fanout_runtime.py` file and the detailed `tests/e2e/feishu-ai-native-loop-e2e-plan.md`. The system is actively used in production scenarios and includes clear, deterministic handling of failure cases, such as dependency failure closure. The codebase is further enriched with detailed comments explaining the translation of legacy workflows to canonical stages and the handling of fanout aggregates.

## 5. Provider Neutrality

The task graph and dependency resolution mechanisms are assessed as provider-neutral. This is because the core logic and fanout mechanics are implemented at the workflow level in `src/zf/core/workflow` and operate independently of specific external providers. While there are provider-specific integrations, such as Feishu, the fundamental graph logic remains abstracted from these external dependencies.
