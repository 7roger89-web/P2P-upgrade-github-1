# ZaoFu Audit Findings: Area Group 6 — Codex & Claude Code Integration

## 1. Codex Integration
ZaoFu implements a deep and mature integration with OpenAI Codex. The integration is primarily handled through the `src/zf/runtime/codex_hooks.py` and `src/zf/runtime/codex_session_ownership.py` modules.

### Implementation Details
- **Hooks**: The `src/zf/runtime/codex_hooks.py` file defines a set of hooks that interface directly with the Codex environment. These hooks are used to manage the lifecycle of Codex sessions, handle tool execution, and process streaming responses.
- **Session Ownership**: The `src/zf/runtime/codex_session_ownership.py` file manages the ownership and lifecycle of Codex sessions. It ensures that sessions are properly initialized, maintained, and terminated, preventing resource leaks and ensuring secure execution.
- **Provider Features**: The integration exercises several Codex features, including tool execution, streaming responses, and stop conditions. This allows ZaoFu to handle complex, long-running tasks efficiently.

### Coupling and Boundaries
- The Codex integration is tightly coupled with the ZaoFu state machine and event system. It depends on the `src/zf/core/statemachine` module to manage task execution and the `src/zf/core/events` module to log and process events.
- Other modules, such as `src/zf/runtime/agent_live.py` and `src/zf/runtime/backend.py`, depend on the Codex integration to execute tasks and manage agent sessions.

### Maturity Signals
- The Codex integration is well-tested and used in end-to-end (e2e) tests. Documentation in `docs/manual` and `docs/design` provides detailed guidance on how to use and configure the integration.

## 2. Claude Code Integration
ZaoFu also integrates with Claude Code, providing an alternative backend for code generation and execution.

### Implementation Details
- **Presence**: The integration with Claude Code is present in the codebase, primarily managed through the `src/zf/runtime/contract_authority.py` module.
- **Provider Features**: The integration exercises Claude Code's capabilities, including code generation and execution. However, the depth of the integration is not as extensive as that of Codex.

### Coupling and Boundaries
- The Claude Code integration is coupled with the ZaoFu contract authority system. It depends on the `src/zf/core/task` module to manage task contracts and the `src/zf/core/verification` module to verify execution results.

### Maturity Signals
- The Claude Code integration is less mature compared to the Codex integration. While it is documented in `docs/manual`, it is not as extensively tested or used in e2e tests.

## 3. Provider Neutrality
The integration with both Codex and Claude Code demonstrates a mixed approach to provider neutrality. While the Codex integration is deep and specific, the overall architecture of ZaoFu is designed to be provider-neutral, allowing for the integration of multiple backends.

## Key Classes and Functions
- `src/zf/runtime/codex_hooks.py`: Defines hooks for interfacing with the Codex environment.
- `src/zf/runtime/codex_session_ownership.py`: Manages the ownership and lifecycle of Codex sessions.
- `src/zf/runtime/contract_authority.py`: Manages the integration with Claude Code.

## Summary
ZaoFu implements a deep and mature integration with OpenAI Codex, utilizing hooks and session ownership to manage task execution and resource management. The integration exercises several Codex features, including tool execution, streaming responses, and stop conditions. The integration with Claude Code is present but less extensive, primarily managed through the contract authority system. The overall architecture of ZaoFu is designed to be provider-neutral, allowing for the integration of multiple backends.
