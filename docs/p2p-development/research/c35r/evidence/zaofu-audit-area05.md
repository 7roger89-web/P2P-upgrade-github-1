# Audit Findings: Area Group 5 — WORKER/SESSION IDENTITY & PROVIDER ABSTRACTION

## 1. WORKER/SESSION IDENTITY & OUTPUT MANAGEMENT

ZaoFu implements a robust identity and state management system for agent sessions. The core identity model is defined in `src/zf/runtime/agent_session_stream.py:AgentSessionIdentity`, which captures `run_id`, `thread_id`, `source`, `actor`, `task_id`, `provider`, `backend`, and `provider_session_id`. The `src/zf/runtime/agent_session_output.py` module manages the output of agent sessions, storing large outputs as sidecar files to avoid bloating the main event ledger. It uses a strict artifact contract (`apply_agent_output_contract`, `write_agent_output_artifact`, `read_agent_output_artifact`) to verify and read these outputs. The `src/zf/runtime/agent_mailbox.py` module implements a state machine for agent communication (`agent.message.sent`, `agent.message.delivered`, `agent.message.read`, `agent.message.failed`), tracking message state across the system. The `src/zf/runtime/agent_view_runtime.py` handles the runtime view of agents, including autoscaling logic (`_next_autoscale_instance_id`, `_is_autoscaled_instance`, `_worker_idle`) and workdir management (`_prepare_autoscale_spawn_cwd`). The `src/zf/runtime/assignment_route.py` module maps event logs to assignment routes, determining the stage of a task (`assignment.intent.proposed`, `squad_synthesis`, `workflow_requested`, `task.dispatched`).

The key implementation semantics reveal a unified identity model for all agent interactions, linking runs to tasks, threads, and specific provider sessions. Agent Session Output enforces a `RAW_OUTPUT_SCHEMA_VERSION` and stores large text outputs in a structured `artifacts/` directory with metadata sidecars (JSON) containing SHA256 hashes and line counts, preventing the main event log from becoming unwieldy. The Agent Mailbox uses an append-only state machine to track message delivery, ignoring illegal state transitions. The Agent View Runtime implements logic to spawn autoscaled instances (`-auto-` suffix), check worker idle states, and prepare workdirectories (including git worktrees) for these instances. The Assignment Route synthesizes a sequence of events into a single route object, determining the current stage of a task assignment.

| Module | Key Classes/Functions | Purpose |
|--------|-----------------------|---------|
| `agent_session_stream.py` | `AgentSessionIdentity`, `AgentSessionStreamEmitter` | Defines unified identity model and emits session events |
| `agent_session_output.py` | `apply_agent_output_contract`, `write_agent_output_artifact`, `read_agent_output_artifact` | Manages large text outputs as sidecar artifacts with verification |
| `agent_mailbox.py` | `fold_mailbox`, `undelivered` | Tracks message delivery state via append-only state machine |
| `agent_view_runtime.py` | `_next_autoscale_instance_id`, `_worker_idle` | Handles agent autoscaling, idle checks, and workdir preparation |
| `assignment_route.py` | `_route_stage`, `_stage_label` | Maps event logs to assignment routes and determines task stages |

This system depends on `zf.core.events.model.ZfEvent`, `zf.core.events.writer.EventWriter`, `zf.core.security.redaction`, and `zf.runtime.provider_usage`. It is used by the core runtime orchestrator, agent sessions, and channel bridges (like the Feishu integration). Extensive tests exist, including `test_agent_session_output.py`, `test_backend_session_reader.py`, and `test_backend_adapters.py`, and the system is actively used in end-to-end scenarios (as referenced in comments like "B-1203-06 R-1 (2026-04-21 mixed-e2e)"). The area is provider-neutral; the identity model abstracts the underlying provider by storing both `provider` and `backend` fields, while the output management and mailbox state machines are entirely decoupled from specific LLM providers.

## 2. PROVIDER ABSTRACTION LAYER & BACKENDS

ZaoFu provides a highly structured provider abstraction layer in `src/zf/runtime/backend.py`. It defines an abstract base class `BackendAdapter` and concrete adapters for specific providers: `ClaudeCodeAdapter` and `CodexAdapter`. A `BackendCapabilities` dataclass declaratively describes the features supported by each backend (e.g., `per_turn_hook`, `native_resume`, `context_usage_reader`, `stream_json`). The `src/zf/runtime/backend_session_reader.py` module provides backend-specific readers (`ClaudeSessionReader`, `CodexSessionReader`) to parse session logs from disk and extract usage reports (`UsageReport`).

The key implementation semantics show that `BackendAdapter` defines the contract for spawning agents via CLI commands (`build_command`), detecting readiness (`ready_pattern`), clearing context (`clear_command`), and exposing capabilities (`capabilities`). The `ClaudeCodeAdapter` spawns the Claude Code CLI, handling permissions (`--dangerously-skip-permissions` or `--allowedTools`), session resumption (`--session-id` or `--resume`), and context usage reading. The `CodexAdapter` spawns the Codex CLI in interactive TUI mode within a tmux pane, using `--dangerously-bypass-approvals-and-sandbox` and handling resume via the `resume <uuid>` command. It relies on tmux `send-keys` for prompts and observes the session file to cache the UUID. `BackendCapabilities` serves as a central matrix preventing hardcoded `if backend == "codex"` checks throughout the codebase. `BackendSessionReader` parses JSONL session logs to extract token usage, context windows, and rate limits, normalizing them into a unified `UsageReport`.

| Component | Key Classes/Functions | Purpose |
|-----------|-----------------------|---------|
| `backend.py` | `BackendAdapter`, `ClaudeCodeAdapter`, `CodexAdapter`, `BackendCapabilities` | Abstracts provider CLI spawning, readiness detection, and capability declarations |
| `backend_session_reader.py` | `ClaudeSessionReader`, `CodexSessionReader`, `UsageReport` | Parses session logs to extract token usage and context metrics |

This system depends on `zf.core.config.schema.RoleConfig`, `zf.core.events.model.ZfEvent`, and `zf.core.events.writer.EventWriter`. It is used by the `SpawnCoordinator`, runtime manager, and agent view for dispatching tasks, recovering sessions, and reporting metrics. Comprehensive test coverage exists for backend adapters (`test_backend_adapters.py`, `test_backend_adapters_resume.py`, `test_backend_capability_matrix.py`, `test_runtime_backend.py`), with detailed comments referencing specific testing runs and edge cases (e.g., Codex's `›` prompt rendering delay). The runtime is provider-neutral; the `BackendAdapter` and `BackendCapabilities` abstractions allow ZaoFu to support multiple LLM providers (Codex, Claude Code) and easily add new ones without modifying the core orchestration logic.

## 3. INTEGRATIONS (FEISHU)

The `src/zf/integrations/feishu/` directory contains a comprehensive integration with Feishu (Lark), including modules for agent conversations (`agent_conversation.py`), bot credentials (`bot_credentials.py`), bridge watching (`bridge_watch.py`), and various UI cards for displaying task states (`channel_progress_card.py`, `delivery_card.py`, `stream_card.py`).

The key implementation semantics reveal that Agent Conversation maps Feishu channel members to agent identities (`provider_agent`), assigning specific permission profiles and backend routing. Bot Credentials manages Feishu app IDs and secrets, supporting different purposes (e.g., `run_manager`, `kanban_agent`, `default`) and falling back to default credentials if purpose-specific ones are missing. Bridge Watch monitors the Feishu provider session, ensuring that turns resume the previous provider session. Stream Card renders provider-specific information (like `provider` or `backend`) in the Feishu UI.

| Module | Key Functions/Classes | Purpose |
|--------|-----------------------|---------|
| `agent_conversation.py` | `_conversation_backend`, `_stable_channel_id` | Maps Feishu channel members to agent identities and routing |
| `bot_credentials.py` | `credential_for_purpose`, `transport_for_purpose` | Manages Feishu app credentials with fallback support |
| `bridge_watch.py` | `bridge_watch` (implied) | Monitors provider sessions to ensure turn resumption |
| `stream_card.py` | `StreamCard` (implied) | Renders provider-specific information in the Feishu UI |

This system depends on `zf.core.events.writer.EventWriter` and `zf.web.operator_contract`, and is used by the Feishu gateway and routing mechanisms. The large number of files (48 files) indicates a deep integration, with specific handling for edge cases like invalid provider plans (`plan_repair.py`) and provider app locks (`single_instance.py`). The area is mixed; while the integration interacts with the Feishu platform, it abstracts the underlying LLM provider by using the `provider` and `backend` fields passed from the core runtime, maintaining compatibility with ZaoFu's provider-neutral design.
