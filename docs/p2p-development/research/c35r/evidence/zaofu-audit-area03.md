# Audit Findings: Area Group 3 — Task Identity & Task Contract

## 1. Task Contract Schema & Validation (`src/zf/core/task/schema.py`, `src/zf/core/task/contract_validation.py`)

**What ZaoFu Implements:**
ZaoFu implements a comprehensive `TaskContract` dataclass in `src/zf/core/task/schema.py` that defines the semantic agreement for a task. The contract includes fields for `behavior` (required), `verification` (required), `verification_tiers` (must not be empty, valid tiers are `static`, `runtime`, `e2e`, `manual_evidence`), `scope`, `affected_files`, `owner_role`, `owner_instance`, and various reference identifiers (e.g., `spec_ref`, `plan_ref`, `evidence_contract`).

**Key Implementation Semantics:**
The `TaskContract` is validated in `src/zf/core/task/contract_validation.py`. The validation logic enforces that `behavior` and `verification` are present, `verification_tiers` is non-empty, and contains only valid tiers. It also checks if `owner_role` or `owner_instance` correspond to configured roles in `ZfConfig`. A notable semantic is the handling of `source_precedence_ref` (e.g., `spec_ref`, `source_ref`), which is required if the task targets a "writer" role.

**Coupling/Boundaries:**
The contract validation depends on `ZfConfig` to resolve valid role names and instances. It is consumed by the orchestrator and dispatch logic to ensure tasks are admissible before execution.

**Maturity Signals:**
The schema and validation logic are well-documented with comments explaining historical context (e.g., `#E fix (TR-STATIC-GATE-PER-TASK-OVERRIDE-001)`). Tests are likely present in the `tests/` directory, though not explicitly audited here.

**Provider Neutrality:**
Provider-neutral. The `TaskContract` defines the semantic agreement independent of the underlying LLM provider. The `execution_profile_id` field explicitly mentions "Provider-neutral Task-local execution strategy."

## 2. Task Identity & Lifecycle (`src/zf/core/task/schema.py`, `src/zf/core/task/lifecycle.py`, `src/zf/core/task/store.py`)

**What ZaoFu Implements:**
Tasks are identified by a generated ID (`TASK-<6-char-uuid>`) in `src/zf/core/task/schema.py`. The `Task` dataclass includes fields for `status` (e.g., `backlog`, `in_progress`, `done`, `cancelled`), `priority`, `assigned_to`, `contract`, and `execution_binding`. The lifecycle phase is not stored directly on the `Task` object but is derived from events in `src/zf/core/task/lifecycle.py`.

**Key Implementation Semantics:**
The `Task.status` field conflates business status and lifecycle phase. The actual lifecycle phase (e.g., `design_done`, `build_done`, `review_approved`, `test_passed`, `judge_passed`) is derived from the most recent stage-progress event in `events.jsonl` via `derive_phase()` in `src/zf/core/task/lifecycle.py`. The `TaskStore` in `src/zf/core/task/store.py` manages tasks via `kanban.json`, using Compare-And-Swap (CAS) revisions (`contract_authority_revision`) to prevent stale updates and handle authority fields securely. Terminal tasks (`done`, `cancelled`) are archived to maintain a small active file.

**Coupling/Boundaries:**
The lifecycle derivation depends heavily on the `ZfEvent` stream. The `TaskStore` depends on file I/O utilities (`atomic_write_text`, `locked_path`) for persistence.

**Maturity Signals:**
The use of CAS revisions and event-driven phase derivation indicates a mature, robust design aimed at avoiding schema migration issues and state drift.

**Provider Neutrality:**
Provider-neutral. The identity and lifecycle mechanisms are core to the ZaoFu orchestrator and do not depend on specific provider APIs.

## 3. WIP Enforcement & Kanban Projection (`src/zf/core/task/wip.py`, `src/zf/core/task/kanban_projection.py`)

**What ZaoFu Implements:**
WIP limits are enforced per worker in `src/zf/core/task/wip.py` via the `WipEnforcer` class. It checks if a worker can accept a new task based on their current active tasks (`status == "in_progress"`). Kanban projections are generated in `src/zf/core/task/kanban_projection.py`.

**Key Implementation Semantics:**
`WipEnforcer` uses `latest_dispatched` events to accurately track in-flight tasks, preventing gridlock during reassignments. The `WorkflowProjection` in `kanban_projection.py` synthesizes the latest events to determine the `workflow_phase` (e.g., `plan`, `impl`, `verify`, `judge`, `done`) and generates badges (e.g., `impl gate passed`, `verify failed`) for UI representation.

**Coupling/Boundaries:**
Both depend on `TaskStore` and the event stream. The projection logic maps specific event types to phases and states, tightly coupling it to the defined event vocabulary.

**Maturity Signals:**
The implementation includes backward compatibility checks for fixtures and handles edge cases like role-name vs. instance-id matching in dispatch events.

**Provider Neutrality:**
Provider-neutral. These are internal orchestration mechanisms.

## 4. Typed Call/Return Envelopes & Authority (`src/zf/runtime/call_result_*.py`)

**What ZaoFu Implements:**
ZaoFu uses a strict, ref-backed envelope model for call results in the runtime layer (`src/zf/runtime/call_result_envelope.py`, `call_result_admission.py`, etc.). The `CALL_RESULT_ENVELOPE_SCHEMA` is "call-result-envelope.v1".

**Key Implementation Semantics:**
The envelope contains an `identity` block (including `workflow_run_id`, `operation_id`, `request_hash`, `task_id`, `dispatch_id`), an `execution` block (status, exit code, provider session ID, timestamps), a `control_result` reference (pointing to a sidecar JSON payload), and `artifact_manifest_ref`. The `control_result` is hydrated via `hydrate_sidecar_ref`. The authority model relies on `contract_authority_revision` (generated via SHA256 hash in `src/zf/core/task/authority.py`) to ensure only authorized updates modify the semantic contract.

**Coupling/Boundaries:**
The call result admission depends on `SidecarRef` for payload storage and `WorkflowOperationService` for context. It bridges the gap between provider-specific execution outputs and the ZaoFu semantic kernel.

**Maturity Signals:**
The explicit schema validation (`validate_call_result_envelope`) and canonicalization versioning indicate a highly mature, production-ready integration layer designed for long-horizon reliability.

**Provider Neutrality:**
Mixed. The envelope structure itself is provider-neutral, designed to wrap execution results generically. However, it includes provider-specific fields like `provider_session_id` and `provider_operation_summary_ref` to maintain traces of the underlying LLM execution.
