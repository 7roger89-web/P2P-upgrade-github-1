# P2P_AUTO_NATIVE_GOAL_ACTIVATION_01

Implementation evidence summary for review.

- New read-only runtime gate: `.p2p/system/p2p_capabilities/native_goal_activation.py`.
- Activation decision is deterministic from existing GoalPlan/TaskPlan durable state.
- Canonical wrapper shapes with `plan` are supported and their `goal_hash` / `plan_hash` are verified before activation.
- Auto activation requires `APPROVED|IN_PROGRESS`, active TaskPlan, at least two tasks, and unfinished work.
- Owner Gate / blocked / budget boundary / verified / terminal / closed / superseded / single-task cases use the normal P2P path.
- Claude Code environment detection is conservative; Codex executor passes its known host identity rather than guessing from `CODEX_HOME`.
- Returned host-native `/goal` remains projection-only and never replaces P2P verifier/evidence authority.
- Installed and portable entrypoints serialize the auto-activation rule so existing/future P2P-managed executors can apply it without asking the Owner whether to use `/goal`.
- Regression coverage is in `tests/test_p2p_native_goal_activation.py` and the portable projection tests.
