<!-- RESEARCH_ONLY / NON_CANONICAL / PROPOSAL / NOT_IMPLEMENTATION / NOT_PROMOTED -->

# Hermes Agent Architecture Audit — C32 research notes (source-backed)

Source: NousResearch/hermes-agent, tag `v2026.8.16` (release v0.20.2), commit `df4b65147d7ddd74`, retrieved 2026-08-17. All file/module references below are relative to the extracted tree root (`/home/ubuntu/c32_research/hermes`).

## Verified evidence highlights (grep-confirmed)
- Loop budget guard: `conversation_loop.py:1830` — `while (api_call_count < agent.max_iterations and agent.iteration_budget.remaining > 0) or agent._budget_grace_call:`; parent default `max_iterations=500`, subagent default `delegation.max_iterations=50` (`agent/iteration_budget.py` docstring); thread-safe consume/refund counter.
- Subagent public contract: `agent/subagent_lifecycle.py` — `PUBLIC_CONTRACT_VERSION = 1`; `SubagentState` enum (PENDING→STARTING→RUNNING→SUCCEEDED/FAILED/INTERRUPTED/CANCELLED/UNKNOWN); `SubagentLaunchRequest` with goal (≤16,000 chars), context (≤32,000), role, model, `allowed_toolsets`, `blocked_tools`, `working_directory`, `parent_session_id`, `correlation_id`; HMAC-signed requests (`hmac`), fail-closed on corrupt data.
- ESTOP: `agent/estop.py` — `$HERMES_HOME/ESTOP` sentinel, pause-new-work-only (in-flight never killed), fail-safe on corrupt file; consulted by cron scheduler (`cron/scheduler.py:tick`) and kanban dispatcher.
- Cron persistence: `cron/jobs.py` — jobs in `~/.hermes/cron/jobs.json` with advisory file locking (fcntl/msvcrt), outputs to `~/.hermes/cron/output/{job_id}/{timestamp}.md`.
- Trajectory/session persistence: `agent/trajectory.py`, `agent/moa_trace.py`, `agent/trace_upload.py` — session transcripts as primary durable artifact (JSONL traces), plus `moa_loop.py` (Mixture-of-Agents loop, 2453 lines) and `background_review.py` (1376 lines) post-session review.
- `agent/oneshot.py` — stateless single-call helper outside sessions (title generation, commit messages).
- `context_engine.py` budgeting + `context_compressor.py` (7858 lines, largest) + `conversation_compression.py` (4329) + `prompt_caching.py` + cache boundary/scope modules — compaction, cache boundaries, token counting.

## Tree overview
`agent/` = core Python engine (~220 modules, ~40k LOC in the 20 largest). Key directories: `agent/transports/` (provider runtimes), `agent/monitoring/` (events/telemetry), `agent/verify/` (verification evidence), `agent/lsp/`, `agent/secret_sources/`, `agent/proxy_sources/`. Top-level: `cli.py` (CLI/TUI), `cron/` (scheduler), `acp_adapter/` (Agent Communication Protocol server), `apps/` (desktop installer), `batch_runner.py`, `evals/`, `contribs/`, `docs/`.

## 1. Main agent/execution loop
`agent/conversation_loop.py` (8125 lines) — the heart. Single large `ConversationLoop` class:
- Reads config → builds provider client (adapter selection by `model` + `config`) → `run()` loop with `while True`.
- Message lifecycle per turn: construct messages → call LLM with tool definitions → stream tool calls → execute tools via `ToolExecutor` → append results → decide continue/stop.
- `IterationBudget` (agent/iteration_budget.py, 62 lines) caps `max_iterations` and `max_time_seconds`; loop checks budget before each turn and sets `stop=True` at exhaustion — hard-bounded main loop.
- `kanban_stop.py` / `deadline.py` — goal-level stop triggers (Kanban columns, deadline).
- Events are emitted through `agent/monitoring/emitter.py` at every state transition (loop_start, tool_call_start/end, turn_complete, iteration_budget, error).

## 2. Task/session lifecycle
- `agent/agent_init.py` (2934 lines): bootstrap — config resolution order (project→user→env), session dir creation, resume detection, model metadata fetch, skill loading, memory init.
- Session directory layout (agent/agent_runtime_helpers.py): `~/.hermes/sessions/<id>/` with `messages.jsonl`, `session.json`, tool result files.
- `agent/display.py`: TUI rendering fed by the same event stream as headless consumers.

## 3. Long-running continuation
- Loop is an infinite bounded loop (iteration/time budget) that keeps going while provider returns tool_use; no fixed "max turns" other than budgets. Long sessions survive via message persistence to `messages.jsonl` (append-only) — resumable.
- Resume semantics: session files are read back on startup; `agent/agent_init.py` detects existing session dir and continues instead of starting fresh.

## 4. Planning
- Planning is LLM-native (no separate planner): `system_prompt.py` (large) composes AGENTS.md-informed instructions, task plan expectations, goal tags.
- `agent/coding_context.py` — repo-plan awareness from AGENTS.md.
- No deterministic planner artifact; plan lives in-context.

## 5–6. Delegation/subagents and result return
- `agent/subagent_lifecycle.py` (540 lines): subagent spawn via `spawn_subagent` tool → separate ConversationLoop instance with its own session dir and context window → parent receives compacted `result` + `artifacts` summary; subagent messages.jsonl persists evidence.
- `agent/delegation_context.py` (161 lines): shared context handoff schema.
- `agent/turn_summary.py`: subagent returns a structured summary, not raw transcript.

## 7. Concurrency controls
- `agent/agent_runtime_helpers.py` + transports use asyncio; a global concurrency gate prevents parallel tool executors for unsafe tools (filesystem tools serialized, approval-gated).
- `agent/stream_single_writer.py` — single-writer guarantee on output streams.

## 8. Retry/budget semantics
- `agent/retry_utils.py` (208 lines): bounded exponential retry with max attempts for transient provider errors.
- `agent/turn_retry_state.py`: per-turn retry accounting; `repetition_guard.py` guards against looping tool results.
- `iteration_budget.py`: max_iterations / max_time_seconds hard stops.

## 9–10. Context management and compression
- `agent/context_engine.py` (489 lines): builds per-turn context from skills, memory, AGENTS.md, attachments, tool schemas with token budgets per section.
- `agent/context_compressor.py` (7858 lines): largest module — compaction strategies: summarization, truncation, token counting, model-aware limits, `manual_compression_feedback.py` user feedback, `native_compaction.py` (model-native compact), `conversation_compression.py` (4329 lines) — slide-window + summary retention, `prompt_caching.py`/`prompt_cache_boundary.py`/`prompt_cache_scope.py` — deterministic cache boundaries to reduce cost.
- `command_token_source.py`: caches token estimates.

## 11. Memory
- `agent/memory_manager.py` (1291 lines) + `memory_provider.py`: durable memory store (files under session/user dir), retrieval at context build time, persistence across sessions.

## 12. Skills loading
- `agent/skill_bundles.py`, `skill_commands.py`, `skill_preprocessing.py`, `skill_utils.py`: skills discovered from `.skills/` dirs (project/user/bundled), loaded as injected text + tool hooks; 79 built-in + 114 optional bundled + community skills per topic index.
- Learning loop: `learning_graph.py`, `learning_mutations.py`, `learn_prompt.py` — agent can propose skill improvements from experience (self-improvement claim; persisted to skill files).

## 13. Progressive disclosure
- Context engine budgets each section; file content is offloaded to disk and referenced; tool schemas injected only when relevant (`tool_dispatch_helpers.py`); `subdirectory_hints.py`.

## 14–15. Terminal/shell and file operations
- `agent/tool_executor.py` (2683 lines): registry-dispatched tool execution; shell tool with profile-based restrictions (profiles: full, restricted, blocked), cwd scoping, timeout, interactive gating via approval; file tools with path safety (`file_safety.py`).

## 16. Workspace isolation
- Per-session directories; `runtime_cwd.py` manages working dir; workspace can be bound per invocation; no shared-state between parallel sessions.

## 17. Git/worktree behavior
- Git tools in tool registry (commit, diff, status) operate on the bound repo; no automatic worktree isolation found in core — git tools mutate the bound workspace; commits are agent-produced and require approval per policy.

## 18. Checkpoint/rollback
- No automatic pre-action checkpointing of the filesystem; recovery relies on git by the agent itself and replay from messages.jsonl; `replay_cleanup.py` — replay tooling.

## 19. Browser/web tools
- `agent/browser_provider.py`, `browser_registry.py`, `agent/` supports Playwright-based browser tool (CDP), web search providers (`web_search_provider.py`/registry), MCP-driven browser variants.

## 20. Tool registry
- `agent/tool_executor.py` registration map + per-tool permission gates; `agent/tool_guardrails.py` content guardrails; `message_sanitization.py`.

## 21. MCP
- `agent/transports/hermes_tools_mcp_server.py` — Hermes itself exposes tools via MCP server; client side: MCP tool sources in tool registry (external MCP servers connectable). `acp_adapter/` is a full ACP (Agent Communication Protocol) server.

## 22–24. Provider/model abstraction and switching
- `agent/transports/base.py` — abstract transport; implementations: `anthropic.py`, `chat_completions.py` (OpenAI-compatible incl. OpenRouter), `bedrock.py`, `codex.py`, `codex_responses_adapter.py`, `gemini_native_adapter.py`, `vertex_adapter.py`, `azure_identity_adapter.py`, `plugin_llm.py` (third-party), `lmstudio_reasoning.py`, `relay_llm.py`/`relay_runtime.py` (agentic fallback chain), `moonshot_schema.py`, `relay_tools.py`.
- Selection: config `model` string parsed in `agent_init.py` → `model_metadata.py` routes to transport; provider switch = config edit, no restart of session state loss (context rebuilt from persisted messages).
- `relay_runtime.py` (1622 lines): multi-provider relay with capability-based routing and fallback order — notable: this IS a form of runtime model routing (P2P's C30 invariant warns against implicit routing).

## 25. Authentication boundaries
- Credentials via env vars, credential files (`credential_persistence.py`, `credential_pool.py`, `credential_sources.py`); `agent/secret_sources/` pluggable secret sources; `agent/secret_scope.py`; `ssl_verify.py`/`ssl_guard.py`; secrets never embedded in prompts (`redact.py`).

## 26. Permissions
- Approval system: interactive ask/OnRequest, `--dangerously-skip-permissions`, per-tool permission policy; `agent/tool_guardrails.py`; `acp_adapter/permissions.py`, `edit_approval.py`.

## 27. Headless/CLI execution
- `cli.py` — TUI; headless modes: `-p/--prompt` oneshot (`agent/oneshot.py`), `batch_runner.py` for bulk prompts, cron jobs (`cron/`), ACP adapter (`acp_adapter/`), webhooks (`outbound_webhooks.py`), portal tags.
- Non-interactive mode outputs structured event log consumable programmatically.

## 28. Structured output/events/receipts
- `agent/monitoring/events.py` + `emitter.py` — JSON event stream (tool calls, results, errors, budget); `agent/verify/` — verification evidence artifacts; receipts of runs persisted in session dir.

## 29–30. Failure recovery / interruption
- `agent/error_classifier.py` classifies LLM/tool errors; retry per `retry_utils`; loop continues on recoverable errors; `estop.py` (174 lines) — emergency stop; SIGINT → graceful interruption (`interrupt_compat.py`); `background_review.py` — post-hoc review of sessions.

## 31. Resume semantics
- Session dir + messages.jsonl replay on restart (agent_init detects); transcript is the durable state in Hermes — directly contrasts with P2P invariant "project-state-is-not-chat-history".

## 32. Observability
- `agent/monitoring/`: events emitter, `otlp_exporter.py` (OpenTelemetry), `cron_health.py`, `gateway_health.py` + export; `trace_upload.py` trajectory upload.

## 33. Token/cost measurement
- `agent/usage_pricing.py`, `credits_tracker.py`, `account_usage.py`, `billing_usage.py`, `aux_accounting.py`, `nous_rate_guard.py`, `billing_view.py` — per-token pricing tables, live cost tracking per session and account-wide quota guards.

## 34. Messaging/gateway/background
- Messaging integrations (Telegram/Discord/Slack/etc.) via gateway daemons; `background_review.py`; `agent/background_review.py` reviews closed sessions; portal; apps/desktop.

## 35. Scheduler/cron
- `cron/scheduler.py`, `cron/jobs.py`, `cron/lifecycle_guard.py`, `cron/monitor.py`, `cron/scheduler_provider.py` — cron jobs defined in Hermes config run headless with their own sessions; lifecycle guard prevents duplicate/overlapping runs.

## 36. Safety boundaries
- Approval-on-dangerous-actions; `file_safety.py`; shell profiles; `tool_guardrails.py`; `ssl_guard.py`; `secret_scope.py`; `think_scrubber.py` (removes thinking blocks); permission elevation requires explicit user action; `--dangerously-skip-permissions` exists (notable anti-pattern for P2P).
