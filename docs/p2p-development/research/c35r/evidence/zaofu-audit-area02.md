# Audit Findings: Area Group 2 — Product Controllers & Workflow

## 1. Product Controllers Pattern & Workflow Authority

ZaoFu implements a strict separation between agent recommendations and human execution, particularly in its workflow and product control actions. The system enforces a "token-gated" approval mechanism where human operators must explicitly approve or reject plans and proposals.

*   **Workflow Authority**: The workflow system is heavily governed by `WorkflowNode`, `WorkflowEdge`, and `ReworkRoute` defined in `src/zf/core/workflow/graph.py`. The workflow graph is compiled into canonical stages, ensuring deterministic execution paths.
*   **Product Controllers**: The `ProductActionsMixin` in `src/zf/runtime/control_actions_product.py` handles the creation and management of tasks. It validates payloads strictly, ensuring that required fields like `title` and `task_id` are present.
*   **Plan Approval**: In `src/zf/runtime/control_actions_plan.py`, the `PlanApprovalActionsMixin` explicitly states that "agent 预审只建议、人点按钮 —— actor 恒 operator". This confirms that while agents can suggest plans, the actual approval or rejection (e.g., `plan-approve`, `plan-reject`) must be triggered by a human operator. The events generated (`plan.approved`, `plan.rejected`) are then fed back into the kernel for further processing (e.g., incubation or replan).

## 2. Plan, Proposal, Recovery, and Replay Control Actions

The repository features a comprehensive set of control actions designed to manage the lifecycle of tasks, plans, and proposals, with built-in mechanisms for recovery and replay.

*   **Plan and Proposal Execution**: `src/zf/runtime/control_actions_proposals.py` introduces `ProposalExecutionActionsMixin`, which enforces an exactly-once execution wrapper using `locked_path` and `proposal_execution_gate`. This ensures that proposals are executed atomically and idempotently.
*   **Recovery Actions**: `src/zf/runtime/control_actions_recovery.py` defines `RecoveryActionsMixin`, which includes deterministic recovery verbs like `task-requeue`, `child-rebuild`, and `stage-retrigger`. These actions are designed to fix deadlocked or failed tasks by rebuilding state or resending unprocessed events.
*   **Replay and Resume**: `src/zf/runtime/control_actions_workflow_replay.py` and `src/zf/runtime/control_actions_workflow_resume.py` provide mechanisms to replay active workflow requests or resume from specific checkpoints. The resume action requires a `checkpoint_id` and `safe_resume_action`, ensuring that state transitions are controlled and validated.
*   **Run Control**: `src/zf/runtime/control_actions_run.py` allows for pausing, resuming, and cancelling runs (`run-pause`, `run-resume`, `run-cancel`), maintaining strict state transitions (e.g., a run can only be paused if it is currently running).

## 3. Human/Owner Interventions

Human interventions are seamlessly integrated into the workflow loop through CLI commands and web interfaces, which emit specific events that the kernel processes.

*   **CLI Command Resolution**: `src/zf/runtime/cli_command.py` ensures that workers use the correct CLI command (`ZF_CLI_CMD`), providing a reliable way to interact with the ZaoFu runtime from within project environments.
*   **Operator Intent**: The system infers operator intent and validates payloads before executing actions, ensuring that human inputs are correctly parsed and applied.

## 4. Maturity Signals

The workflow and control action components exhibit a high level of maturity, evidenced by extensive testing and documentation.

*   **Tests**: There is a robust suite of tests covering various aspects of the workflow, including `test_workflow_graph_runtime.py`, `test_workflow_topology.py`, `test_workflow_proposal.py`, and `test_workflow_resume_batch.py`. These tests ensure the correctness and reliability of the workflow execution and control actions.
*   **Documentation**: Comprehensive documentation is available in `docs/manual/`, with specific sections dedicated to workflow operations (e.g., `02-zf-yaml-control-plane.md`, `13-plan-task-map-orchestrator-dispatch.md`) and controlled workflow starts (`controlled-workflow-start.md`).

## 5. Provider Neutrality

The workflow and control action implementations are largely provider-neutral, focusing on the orchestration and execution logic rather than specific AI model interactions. However, there are some provider-specific integrations, particularly with Codex, as seen in `src/zf/core/workflow/runner_policy.py` and `src/zf/core/workflow/topology.py`. These integrations are abstracted through the workflow topology, allowing for some level of abstraction, but the core logic remains tied to specific provider hooks.

**Assessment**: mixed; Codex hooks are deep but backend.py abstracts sessions.
