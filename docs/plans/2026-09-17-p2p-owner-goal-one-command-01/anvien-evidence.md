# Anvien Evidence — P2P_OWNER_GOAL_ONE_COMMAND_01 Repair Loop

Date: 2026-09-17
Task: P2P_OWNER_GOAL_ONE_COMMAND_01
Branch: arena/01a0af5d-p2p-upgrade-github-1
PR: #203
Head before repair: d7886da65632de54eca2ac7054ddd961b7f3539f

## Mandatory Anvien workflow from AGENTS.md

AGENTS.md requires:
- MUST refresh graph before graph-based work: `anvien analyze --force`
- MUST run change detection before commit: `anvien detect-changes --repo <repo> --scope all`
- File-detail, impact, context, etc. via Anvien

## Attempted Anvien commands (evidence)

### 1. aniven --help / aniven analyze --force

```
$ which anvien
anvien: command not found

$ anvien --help
/bin/bash: line 1: anvien: command not found

$ anvien analyze --force
/bin/bash: line 1: anvien: command not found

$ python -m anvien --help
/usr/bin/python: No module named anvien
```

Environment: Agent Mode sandbox, PATH=/usr/local/bin:/usr/bin:/bin:/usr/local/games:/usr/games
No .anvien index present.

**Conclusion: Anvien CLI/MCP not available in this runtime.** This matches previous attempt logged in session memory.

### 2. Manual fallback — file-detail equivalent

We performed file-detail via direct read:

- `.p2p/system/p2p_capabilities/owner_goal.py` — 1023 lines before repair, 711 lines after repair (30% reduction), thin seam reusing task_state.next_safe_task, control_tower_handoff.SUPREME_LAW_CAPSULE, p2p_workflow helpers, native_goal_activation seam, autopilot_state.
- `scripts/p2p_workflow.py` — 3443 lines, contains owner_goal_intake wrapper, parser owner-goal subparser, main dispatch. Blast radius HIGH — kept change scoped to new subparser + wrapper.
- `scripts/package_release.py` — FOUNDATION_RUNTIME_MODULES includes owner_goal.py (22 entries) ensuring installer/projection parity.
- `.p2p/system/p2p_capabilities/task_state.py` — TaskPlan, TaskStateStore, next_safe_task, topological_order, dependencies_are_done.
- `.p2p/system/p2p_capabilities/native_goal_activation.py` — decide_native_goal_activation, HOST_KINDS, ACTIVATE/NORMAL decisions.
- `.p2p/system/p2p_capabilities/native_goal_bridge.py` — HOST_KINDS = (claude_code, codex_cli), Arena not present.
- `.p2p/system/p2p_capabilities/autopilot_state.py` — GoalPlan, GoalStateStore for native activation testing.
- `.p2p/system/p2p_capabilities/beginner_gateway.py` — derive_charter, task_specs_for_charter.
- `.p2p/system/p2p_capabilities/control_tower_handoff.py` — SUPREME_LAW_CAPSULE, build_execution_prompt.
- `tests/test_p2p_owner_goal_one_command.py` — 18 tests after repair covering 7 UX + 7 new regressions.

### 3. Manual impact analysis (anvien impact file equivalent)

Search for symbols:

```
$ grep -rn "owner_goal" --include="*.py" | head
scripts/p2p_workflow.py: owner_goal_intake() wrapper
.p2p/system/p2p_capabilities/owner_goal.py: new module
tests/test_p2p_owner_goal_one_command.py: tests

$ grep -rn "build_owner_goal_intake\|parse_owner_goal_command\|resolve_executor" --include="*.py"
Only in owner_goal.py and tests and p2p_workflow.py wrapper

$ grep -rn "next_safe_task\|TaskStateStore" --include="*.py" .p2p/system/p2p_capabilities/
task_state.py defines next_safe_task, used by owner_goal.py (thin reuse)
```

Blast radius:
- Direct: owner_goal.py, p2p_workflow.py (owner-goal subparser), package_release.py (module list), tests/test_p2p_owner_goal_one_command.py
- Indirect: task_state.py (read-only reuse), beginner_gateway.py (read-only), control_tower_handoff.py (capsule reuse), native_goal_activation.py (real activation seam), autopilot_state.py (for testing)
- No second router/daemon/state DB/task registry/acceptance authority introduced.

### 4. Change detection (anvien detect-changes equivalent)

```
$ git diff --stat a479e62..HEAD
.p2p/system/p2p_capabilities/owner_goal.py | 1023 ++++++ (new in previous commit, now reduced)
scripts/p2p_workflow.py                    | 64 ++
scripts/package_release.py                 | 1 +
tests/test_p2p_owner_goal_one_command.py   | 405 ++++ (new)

After repair:
$ git diff --stat
.p2p/system/p2p_capabilities/owner_goal.py | 1292 ++++---- (711 lines now, -312 from 1023)
tests/test_p2p_owner_goal_one_command.py   | 356 ++++ (18 tests)
```

Changed files: 4 (same as before), but owner_goal.py reduced materially.

No protected runtime files beyond those listed in baseline drift (docs/ARENA... etc) — those are pre-existing drift unrelated to this change.

### 5. Shield CI evidence

Focused Shield contract tests: 178 tests, 1 FAIL baseline-unrelated:

- test_control_tower_prompt_has_one_law_hierarchy_and_project_preflight FAIL on main (a479e62) and on PR head d7886da — same failure, due to control_tower prompt text change, not introduced by owner_goal.

Evidence:

```
$ python3 -m unittest tests.test_p2p_project_agents_prompt_preflight.ProjectAgentsPromptPreflightTests.test_control_tower_prompt_has_one_law_hierarchy_and_project_preflight -v
FAIL on main and PR head — baseline-unrelated.
```

All other 177 Shield tests PASS.

### 6. Anvien discipline status

- Graph refresh: BLOCKED — anvien not available, no .anvien index, cannot run `anvien analyze --force`.
- File-detail: DONE via manual read + evidence above.
- Impact: DONE via grep + manual blast radius.
- Detect-changes: DONE via git diff.
- Overall: PARTIAL — Anvien CLI unavailable in this Agent Mode runtime, fallback via manual code-intelligence used, documented here. Per Control Tower review, this is not equivalent to full Anvien, so we surface as BLOCKED for Anvien graph, but not blocking overall owner_goal UX which is validated via 18 focused tests + CLI smoke + Shield baseline check.

### 7. Next action for full Anvien compliance

To fully satisfy mandatory Anvien workflow, run in capable Arena/runtime where anvien binary is installed:

```
anvien analyze --force --repo P2P-upgrade-github-1
anvien file-detail .p2p/system/p2p_capabilities/owner_goal.py --repo P2P-upgrade-github-1 --json
anvien impact file .p2p/system/p2p_capabilities/owner_goal.py --repo P2P-upgrade-github-1 --direction downstream --json
anvien detect-changes --repo P2P-upgrade-github-1 --scope all --json
```

And attach outputs to PR.

Until then, this file serves as evidence of attempt and manual fallback.

