<!-- RESEARCH_ONLY / NON_CANONICAL / PROPOSAL / NOT_IMPLEMENTATION / NOT_PROMOTED -->

# Deliverable A — Hermes Architecture Map (source-backed)

**Source:** NousResearch/hermes-agent, tag `v2026.8.16` (release v0.20.2), commit `df4b65147d7ddd74dd449f9067aabbca5aef0ec7`, retrieved 2026-08-17T07:41Z. MIT licensed. All locations reference the extracted tree root.

## A.1 System landscape

Hermes Agent is a Python application whose heart is a single large session loop, wrapped by a CLI/TUI, a cron scheduler, an Agent Communication Protocol (ACP) server, a desktop app bootstrap, and messaging gateway daemons. The core engine lives in `agent/` (~220 modules).

| Layer | Modules | Role |
|---|---|---|
| Interface | `cli.py`, TUI rendering | Terminal user interface, slash commands, `-p` oneshot headless mode |
| Core loop | `conversation_loop.py` (8125 ln), `agent_init.py` (2934), `turn_finalizer.py`, `turn_summary.py` | Main agent loop, bootstrap, turn completion |
| LLM interface | `prompt_builder.py` (2452), `chat_completion_helpers.py`, `message_content.py`, `models_dev.py`, `model_metadata.py` | Prompt composition, completion calls, model registry |
| Transports | `agent/transports/` (13 files) | Provider abstraction: Anthropic, chat-completions (OpenAI/OpenRouter-compatible), Bedrock, Codex CLI, Gemini native, Vertex, Azure, LMStudio, plugin LLMs, and **relay** (multi-provider fallback) |
| Tools | `tool_executor.py` (2683), `tool_guardrails.py`, `file_safety.py`, `browser_provider.py`, MCP surfaces | Tool dispatch, permissions, safety, browser, MCP |
| Context | `context_engine.py`, `context_compressor.py` (7858), `conversation_compression.py` (4329), `prompt_caching.py` + boundary/scope, `coding_context.py` | Context assembly, compaction, cache markers, profile budgets |
| Memory & skills | `memory_manager.py` (1291), `skill_bundles.py`, `skill_utils.py`, `skill_preprocessing.py`, `learning_graph.py` | Durable memory, skill discovery/loading, self-improvement learning loop |
| Delegation | `subagent_lifecycle.py` (540), `delegation_context.py`, `moa_loop.py` (2453) | Subagent contract (typed launch, state enum, HMAC), MoA (mixture-of-agents) loop |
| Governance of run | `iteration_budget.py`, `retry_utils.py`, `turn_retry_state.py`, `repetition_guard.py`, `estop.py`, `interrupt_compat.py`, `error_classifier.py` | Budgets, retry, repetition guard, emergency pause, interrupt, error classification |
| Durability | `trajectory.py`, `moa_trace.py`, `trace_upload.py`, session dirs (`messages.jsonl`, `session.json`) | Session transcripts and traces as the durable artifact |
| Observability | `agent/monitoring/emitter.py`, `events.py`, `otlp_exporter.py`, `cron_health.py`, `gateway_health.py` | JSON event stream, OpenTelemetry, health |
| Economics | `usage_pricing.py`, `credits_tracker.py`, `account_usage.py`, `nous_rate_guard.py`, `billing_view.py` | Token/cost accounting, quota guards |
| Scheduling | `cron/{scheduler,jobs,lifecycle_guard,monitor,notepad}.py` | Cron jobs (`jobs.json` + locking), lifecycle guard, monitors |
| Integration | `acp_adapter/` (server, permissions, provenance), `outbound_webhooks.py`, messaging gateways | ACP protocol server, webhooks, messaging |
| Safety | `redact.py`, `secret_scope.py`, `ssl_guard.py`, `think_scrubber.py`, approval system, `--dangerously-skip-permissions` | Secret redaction, SSL, thinking-scrub, approvals |

## A.2 Execution flow

`cli.py -p "<prompt>"` (or interactive TUI) → `agent_init.py` resolves config precedence (project → user → env), creates/opens a session dir, detects resume, loads model metadata → `ConversationLoop.run()`: build messages (`prompt_builder.py` + `context_engine.py` budgets) → streaming completion with tool schemas → `ToolExecutor` dispatches each tool call (approval-gated for dangerous tools; shell tool respects profiles, cwd, timeouts) → results appended → loop continues while budget remains. The loop guard is at `conversation_loop.py:1830`:

> `while (api_call_count < agent.max_iterations and agent.iteration_budget.remaining > 0) or agent._budget_grace_call:`

Parent default `max_iterations=500`; each subagent gets an independent budget (default 50) via `delegation.max_iterations` — so total work across a parent and its subagents can exceed the parent cap. `IterationBudget` is a thread-safe consume/refund counter (`agent/iteration_budget.py`).

## A.3 Headless contract surface (relevant to C30)

Structured input: CLI `-p` goal text + config files; structured output: the monitoring JSON event stream (`agent/monitoring/emitter.py`) covering tool calls, results, errors, budgets; exit status from the CLI process; session identity via session dirs; tool execution via the registry; workspace binding via cwd/session dir; permission configuration via the approval policy; model/provider selection via config `model`; cancellation via SIGINT; bounded execution via injected `max_iterations`; result extraction from final tool results and session artifacts. No public SDK — the CLI + event stream is the machine-usable interface.

## A.4 Durability model (the key divergence from P2P)

Hermes's durable state **is** the session transcript: append-only `messages.jsonl` plus `session.json` in `~/.hermes/sessions/<id>/`. Resume is transcript replay (`agent_init.py` resume detection). Compaction (`conversation_compression.py`) slides a window and retains summaries; `context_compressor.py` implements summarization strategies with hygiene safeguards (cooldown on summary-LLM failures, protected skill names, recovery stubs, anchor indices). This makes long sessions *possible* but makes the transcript the single source of truth — the opposite of P2P's `project-state-is-not-chat-history` invariant.

## A.5 Provider architecture (the other key divergence)

`agent/transports/base.py` defines the transport interface; `model_metadata.py` resolves a config `model` string to a transport. Critically, `agent/relay_llm.py` and `agent/relay_runtime.py` (1622 ln) implement **automatic capability-based provider fallback chains** — an implicit router inside the harness. P2P's C30 invariant `REGISTRY != ROUTER` classifies this as a rejected default, though the underlying transport abstraction is the pattern P2P should keep.

## A.6 Delegation architecture

`agent/subagent_lifecycle.py` exposes a versioned public contract (`PUBLIC_CONTRACT_VERSION = 1`): `SubagentLaunchRequest` (goal ≤16,000 chars, context ≤32,000, role, model, `allowed_toolsets`, `blocked_tools`, `working_directory`, `parent_session_id`, `correlation_id`), HMAC request authentication, a `SubagentState` enum (PENDING→STARTING→RUNNING→SUCCEEDED/FAILED/INTERRUPTED/CANCELLED/UNKNOWN), per-subagent budgets, and compaction-style result summaries (`turn_summary.py`). Subagents run as separate `ConversationLoop` instances in their own session dirs. `moa_loop.py` adds a parallel reference-slot "mixture of agents" pattern with `_RefAccounting` for reference cost tracking.

## A.7 Governance-of-the-run primitives worth adapting

ESTOP (`agent/estop.py`): a `$HERMES_HOME/ESTOP` sentinel file, checked per tick, that pauses **new** work without killing in-flight runs, fails safe on corruption, and is consulted by the cron scheduler and kanban dispatcher — a clean pause-new-work semantic. Cron (`cron/jobs.py`, `lifecycle_guard.py`): file-backed jobs with advisory locking and a lifecycle guard against overlapping dispatch. Error handling (`error_classifier.py` + `retry_utils.py`): classified errors with bounded retry; the loop continues on recoverable errors and surfaces the rest. Cost (`credits_tracker.py`, `usage_pricing.py`): live token-cost tracking feeding quota latches (`nous_rate_guard.py`).

## A.8 Trust posture observations

Credentials are reference-only (`credential_persistence.py`, `credential_sources.py`); `redact.py` scrubs secrets from prompts; `secret_sources/` is a pluggable provider layer; `ssl_guard.py`/`ssl_verify.py` harden transport; `think_scrubber.py` removes thinking blocks. Two tensions matter for P2P: (1) `--dangerously-skip-permissions` shows harness safety is optionally defeatable by a single flag — P2P governance must enforce its gates at the control plane regardless; (2) the harness never sandbox-enforces workspaces — workspace boundaries are convention, not mechanism, so P2P's workspace contract must add its own assumptions.
