# ZaoFu Audit Findings: Area Group 7 — WORKSPACE/WORKTREE ISOLATION & CONTEXT PACKAGING

## 1. Workspace & Worktree Isolation

### Implementation Details
ZaoFu implements workspace and worktree isolation primarily through git worktrees, managed by the `WorkdirManager` and `TaskWorkspaceManager` classes. The `WorkdirManager` class, located in `src/zf/runtime/workdirs.py`, is responsible for preparing and removing worktrees for different roles such as writers and readers. It utilizes git commands like `git worktree add` and `git worktree remove` to manage these workspaces. Writers are assigned dedicated branches based on their instance IDs, while readers receive detached HEAD worktrees.

The `TaskWorkspaceManager` class in `src/zf/runtime/task_workspaces.py` manages task-specific workspaces. It ensures that these workspaces are created as git worktrees and tracks their metadata, including information stored in `meta.json`.

### Key Implementation Semantics
The core semantic of this implementation is strict isolation. Each role or task is allocated its own directory, which is physically separated from the main project repository but shares the same underlying `.git` object database. This allows for concurrent operations without interference.

The lifecycle of these worktrees is tightly coupled with the roles they serve. Worktrees are created when a role is instantiated and are removed when the role is retired. Before removal, the system performs checks for uncommitted changes to prevent accidental data loss. Additionally, a `pre-push` hook is installed in writer worktrees to enforce local-only push policies if the system is configured with `remote_policy=local_only`.

### Coupling & Boundaries
The workspace management system depends heavily on the git command-line tool, standard filesystem operations, and the role or task configuration. It is utilized by agent sessions, the task execution engine, and the context delivery system to provide isolated environments for agents to work in.

### Maturity Signals
The implementation appears mature, as tests are present in the `tests/` directory, and documentation exists in the `docs/` directory, specifically under `docs/runbooks` and `docs/design`. The mechanism is extensively used throughout the codebase for task execution and context isolation.

### Provider Neutrality
This component is provider-neutral. The worktree isolation mechanism relies entirely on git and standard filesystem operations, making it completely independent of any specific LLM provider or external service.

## 2. Context Packaging & Briefing

### Implementation Details
Context packaging for fresh-context workers and the preparation of briefing contents for child tasks are handled by several key modules within the runtime directory. The `ContextRef` class and the `write_context_manifest` function in `src/zf/runtime/context_manifest.py` generate a manifest for each dispatch. This manifest includes both `context.jsonl` and `context.md` files, explicitly listing the files and context provided to the worker.

The delivery of context is managed by functions in `src/zf/runtime/context_delivery.py`, which organize context into sections such as goals, plans, and contracts. Furthermore, functions in `src/zf/runtime/briefing_hydration.py`, such as `render_run_contract_context` and `evaluate_instruction_hydration`, ensure that the run contract context and required references are correctly hydrated and present in the briefing instructions. Finally, `src/zf/runtime/briefing_metrics.py` calculates and stores metrics about the briefing, including byte counts, token estimates, and section sizes.

### Key Implementation Semantics
A crucial semantic of the context packaging system is the generation of a context manifest by the kernel at dispatch time. This manifest explicitly lists what the worker was loaded with, serving as a valuable debugging tool to answer the question of whether the worker actually had the required specification.

Context is organized into distinct sections, including `goal_objective_and_claims`, `task_contract_and_scope`, and `plan_package_and_task_map`. The system also performs hydration validation by checking if required references from the run contract are present in the instructions. Depending on the strictness configuration, missing references may result in warnings or block execution entirely.

### Coupling & Boundaries
The context packaging system depends on the run contract configuration, the state directory structure, and the task dispatch mechanism. It is actively used by worker agents, debugging tools, and audit systems to ensure that agents receive the correct context for their tasks.

### Maturity Signals
The system demonstrates maturity through its comprehensive implementation of context manifests and hydration validation. Tests are present in the repository, and the context delivery and briefing mechanisms are documented in the design docs. It is a core component of the multi-agent task execution architecture.

### Provider Neutrality
This component is provider-neutral. Context packaging and briefing focus on organizing and delivering information to agents, operating independently of the underlying LLM provider.
