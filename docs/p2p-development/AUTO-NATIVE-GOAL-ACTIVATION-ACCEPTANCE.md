# AUTO-NATIVE-GOAL-ACTIVATION acceptance

Acceptance for this slice:

1. Activation is read-only and derived only from authoritative durable P2P GoalPlan/TaskPlan state.
2. Only active multi-task goals (`APPROVED` or `IN_PROGRESS`, active TaskPlan, >=2 tasks, unfinished work) return `ACTIVATE_NATIVE_GOAL`.
3. Owner gates, blocked/budget/verified/terminal goals, closed/superseded plans, single-task plans, unknown host identity, or completed work do not auto-activate.
4. Canonical durable wrapper hashes are verified before activation; malformed or tampered wrappers fail closed.
5. Claude Code and Codex CLI semantics remain distinct.
6. No new P2P authority, state machine, scheduler, daemon, ledger, permission grant, provider route, promotion, release or deploy is introduced.
7. Installed and portable P2P entrypoints instruct executors to run/apply this gate automatically without asking the Owner whether to use `/goal`.
8. Regression tests cover activation, non-activation, wrapper shape, hash mismatch, malformed state, and conservative host detection.
