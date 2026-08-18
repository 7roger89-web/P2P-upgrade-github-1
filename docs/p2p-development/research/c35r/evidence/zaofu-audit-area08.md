# ZaoFu Audit Findings: Area Group 8 — STATE PERSISTENCE, APPEND-ONLY EVENTS & STATE STORES

## 1. Event Model & Append-Only Event Store

**What ZaoFu actually implements:**
ZaoFu implements an append-only event store centered around the `ZfEvent` dataclass (`src/zf/core/events/model.py:ZfEvent`). Events are serialized as JSON lines. The core writer logic is encapsulated in `EventWriter` (`src/zf/core/events/writer.py:EventWriter`), which handles appending events, enriching them with causation and correlation IDs, and executing projectors. The event log is segmented into JSONL files (e.g., `events.jsonl`) located in the `.zf` directory, managed by `EventLog` and `segments` (`src/zf/core/events/segments.py`).

**Key implementation semantics:**
The event store enforces an append-only nature where events are strictly added to JSONL files. Deduplication is handled via an in-memory bounded ID set (`BoundedIdSet` in `src/zf/core/events/dedupe.py`) to prevent processing the same event twice within a session. The `EventWriter` automatically enriches events with `causation_id` (pointing to the parent event) and `correlation_id` (for tracing across related events). If not explicitly provided, these are inferred from the latest task event or the writer's default correlation ID. Events also trigger "projectors" (`src/zf/core/events/projectors.py:EventProjector`), which are handlers that update derived state (e.g., fanout manifests, stage reports) without blocking the event append. The `BoundedIdSet` uses an `OrderedDict` to maintain insertion order and evicts the oldest entries when the size exceeds 50,000, preventing unbounded memory growth.

**Coupling/boundaries:**
The event system depends on `ZfConfig`, `EventLog`, and `ProjectorRunner`. It is heavily depended upon by the `Orchestrator`, `Workflow` runners, `Agent` hooks, `Discriminator` (GAN) logic, and CLI tools (e.g., `zf workflow audit`).

**Maturity signals:**
Extensive tests exist, including `test_writer_contract_handoff.py`, `test_writer_fanout_admission.py`, `test_writer_fanout_runtime.py`, and `test_writer_task_map_fallback.py`. The system is deeply integrated into the runtime and CLI, and is referenced in design docs (e.g., doc 140, doc 26, doc 39).

**Provider Neutrality:**
Mixed. While the core event model and writer are provider-neutral, there are specific provider hooks integrated (e.g., `claude.hook.*`, `codex.hook.*` in `src/zf/core/events/known_types.py`), indicating tight integration with specific LLM providers for session capture and rollout events.

## 2. State Persistence & Atomic IO

**What ZaoFu actually implements:**
State persistence is managed through atomic file writes and POSIX advisory file locks. The core components are `atomic_write_text` (`src/zf/core/state/atomic_io.py:atomic_write_text`), `FileLock` (`src/zf/core/state/locks.py:FileLock`), and `locked_path` (`src/zf/core/state/locks.py:locked_path`). State is stored in various formats (YAML, JSON) within the `.zf` directory (e.g., `session.yaml`, `kanban.json`, `task-attempts.json`).

**Key implementation semantics:**
The `atomic_write_text` function writes to a temporary sibling file (e.g., `file.tmp`) and then uses `os.replace` to atomically swap it with the target file. This prevents partial writes on crashes. The `FileLock` class uses `fcntl.flock` for exclusive locking, supporting timeouts and polling intervals. The `locked_path` context manager acquires the lock for the duration of a block, while `locked_read_modify_write` ensures safe concurrent access to state files. Additionally, the `GitState` dataclass (`src/zf/core/state/git_state.py:GitState`) captures the repository's state (branch, head, dirty files, last commit message) at a specific point in time.

**Coupling/boundaries:**
The state persistence layer depends on `pathlib`, `fcntl`, and `tempfile`. It is depended upon by `SessionStore`, `TaskAttemptStore`, `OperatorSessionRegistry`, and `RoleSessionRegistry`.

**Maturity signals:**
Tests for state management and workdirs exist (e.g., `test_workdirs.py`, `test_worker_state_events.py`). The system is fundamental to the platform's operation and is documented as part of the deterministic kernel rule (keeping subprocesses out of core).

**Provider Neutrality:**
Neutral. The atomic IO and locking mechanisms are entirely provider-neutral, relying on standard POSIX APIs.

## 3. Session & Role State Management

**What ZaoFu actually implements:**
Session state is managed through several registries and stores. The `SessionStore` (`src/zf/core/state/session.py:SessionStore`) manages `.zf/session.yaml`, tracking worker states, session IDs, and the latest event offset. The `TaskAttemptStore` (`src/zf/core/state/task_attempts.py:TaskAttemptStore`) persists task attempts, managing identity (via SHA256 digests), leases, and statuses. The `RoleSessionRegistry` (`src/zf/core/state/role_sessions.py`) manages role-specific sessions, including Codex rollout JSONL parsing and session rotation. The `OperatorSessionRegistry` (`src/zf/core/state/operator_sessions.py:OperatorSessionRegistry`) tracks operator-to-target bindings (e.g., Feishu threads, CLI PIDs).

**Key implementation semantics:**
The `TaskAttemptStore` uses deterministic IDs generated by hashing run ID, task ID, and dispatch ID. It enforces schema versions (`task-attempt.v1`) and identity versions (`TASK_ATTEMPT_IDENTITY_ROLE_V1`, `TASK_ATTEMPT_IDENTITY_OPERATION_V2`). The `RoleSessionRegistry` parses Codex rollout files, matching them to the project's root to prevent cross-contamination. It handles session rotation by incrementing a counter and reseeding a UUID5. The `OperatorSessionRegistry` stores bindings in YAML, mapping opaque operator session IDs to targets. The registry supports binding, resolving, unbinding, and listing all active bindings.

**Coupling/boundaries:**
The session management layer depends on `yaml`, `json`, `hashlib`, and `uuid`. It is depended upon by the `Orchestrator`, `Statemachine`, `CLI` commands, and `Web Server`.

**Maturity signals:**
Tests exist for worker state events and workflow state breadcrumbs (`test_worker_state_events.py`, `test_workflow_state_breadcrumb.py`). The system is actively used in end-to-end scenarios and referenced in design docs regarding session management and task lifecycle.

**Provider Neutrality:**
Mixed. The core session management (session store, task attempts, operator sessions) is provider-neutral. However, the `RoleSessionRegistry` has specific logic for parsing Codex rollout files (`codex` provider), making it provider-specific in that context.
