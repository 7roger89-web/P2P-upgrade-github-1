# P2P native `/goal` auto-activation

Status: implementation slice for deterministic session-continuation selection.

The activation gate is read-only and derives its decision from the existing durable P2P GoalPlan/TaskPlan. It creates no new state, router, scheduler, daemon, permission grant, provider route, or acceptance authority.

## Activation rule

Return `ACTIVATE_NATIVE_GOAL` only when all are true:

- host identity is known as `claude_code` or `codex_cli`;
- Goal status is `APPROVED` or `IN_PROGRESS`;
- TaskPlan lifecycle is `ACTIVE`;
- canonical plan contains at least two tasks;
- at least one task is not terminal.

Otherwise return `NORMAL_P2P_PATH`. `OWNER_GATE`, `BLOCKED`, `BUDGET_BOUNDARY`, `VERIFIED`, terminal goals, closed/superseded plans, and single-task plans never auto-activate native `/goal`.

Canonical durable wrapper hashes are checked before activation. Malformed or contradictory state fails closed.

Claude Code may be identified from stable in-session markers. Codex CLI host identity is supplied by the executor from its known execution surface rather than guessed from weak environment hints such as `CODEX_HOME`.

The returned `/goal` command is still only a projection of P2P authority. P2P task state, evidence and independent verifier remain acceptance authority.
