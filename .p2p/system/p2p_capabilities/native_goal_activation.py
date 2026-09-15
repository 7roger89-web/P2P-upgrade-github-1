"""Deterministic, read-only auto-activation gate for host-native ``/goal``.

This module decides whether an already-authoritative P2P GoalPlan/TaskPlan is
large and active enough to benefit from host-native ``/goal``. It never
creates state, launches a host, grants permissions, retries work, or replaces
P2P verification. The decision is derived only from durable P2P state.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Mapping

try:
    from .native_goal_bridge import (
        CLAUDE_CODE,
        CODEX_CLI,
        HOST_KINDS,
        NativeGoalBridgeError,
        build_contract_replay_manifest,
        build_native_goal_projection,
    )
except ImportError:  # Allow direct execution of the installed module path.
    runtime_root = Path(__file__).resolve().parents[1]
    if str(runtime_root) not in sys.path:
        sys.path.insert(0, str(runtime_root))
    from p2p_capabilities.native_goal_bridge import (  # type: ignore[no-redef]
        CLAUDE_CODE,
        CODEX_CLI,
        HOST_KINDS,
        NativeGoalBridgeError,
        build_contract_replay_manifest,
        build_native_goal_projection,
    )

ACTIVATION_SCHEMA = "p2p-native-goal-activation/1"
ACTIVATE = "ACTIVATE_NATIVE_GOAL"
NORMAL = "NORMAL_P2P_PATH"
ACTIVE_GOAL_STATUSES = frozenset({"APPROVED", "IN_PROGRESS"})
TERMINAL_TASK_STATUSES = frozenset({"DONE", "CANCELLED"})


class NativeGoalActivationError(NativeGoalBridgeError):
    """Raised when durable state is malformed or contradictory."""


def _canonical_hash(value: Mapping[str, Any]) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _unwrap_plan(value: Mapping[str, Any], label: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise NativeGoalActivationError(f"{label}_MUST_BE_OBJECT")
    nested = value.get("plan")
    if nested is None:
        return dict(value)
    if not isinstance(nested, Mapping):
        raise NativeGoalActivationError(f"{label}_PLAN_MUST_BE_OBJECT")

    plan = dict(nested)
    if label == "GOAL_STATE":
        if value.get("schema") != "p2p-autopilot-goal/1":
            raise NativeGoalActivationError("GOAL_STATE_SCHEMA_INVALID")
        expected = value.get("goal_hash")
        hash_error = "GOAL_STATE_HASH_MISSING_OR_INVALID"
        mismatch_error = "GOAL_STATE_HASH_MISMATCH"
    elif label == "TASK_STATE":
        if value.get("schema") != "p2p-task-state/1":
            raise NativeGoalActivationError("TASK_STATE_SCHEMA_INVALID")
        expected = value.get("plan_hash")
        hash_error = "TASK_STATE_HASH_MISSING_OR_INVALID"
        mismatch_error = "TASK_STATE_HASH_MISMATCH"
    else:
        raise NativeGoalActivationError("STATE_LABEL_UNSUPPORTED")

    if not isinstance(expected, str) or len(expected) != 64:
        raise NativeGoalActivationError(hash_error)
    if expected.lower() != _canonical_hash(plan):
        raise NativeGoalActivationError(mismatch_error)
    return plan


def detect_host_from_environment(environ: Mapping[str, str] | None = None) -> str | None:
    """Return a host only when the process environment identifies it safely.

    Claude Code exposes stable in-session markers. Codex CLI does not expose
    an equally reliable generic in-session marker, so ``CODEX_HOME`` alone is
    intentionally not treated as proof; a Codex executor should pass its known
    host identity as ``--host codex_cli`` without asking the Owner.
    """

    env = os.environ if environ is None else environ
    if str(env.get("CLAUDECODE", "")).strip() == "1":
        return CLAUDE_CODE
    if str(env.get("CLAUDE_CODE_ENTRYPOINT", "")).strip():
        return CLAUDE_CODE
    return None


def _validated_replay(goal_plan: Mapping[str, Any], task_plan: Mapping[str, Any]) -> dict[str, Any]:
    try:
        return build_contract_replay_manifest(goal_plan, task_plan)
    except NativeGoalBridgeError as exc:
        raise NativeGoalActivationError(str(exc)) from exc


def decide_native_goal_activation(
    host_kind: str,
    goal_state: Mapping[str, Any],
    task_state: Mapping[str, Any],
    *,
    baseline_ref: str | None = None,
) -> dict[str, Any]:
    """Return one deterministic activation decision without mutating state."""

    if host_kind not in HOST_KINDS:
        raise NativeGoalActivationError("HOST_KIND_UNSUPPORTED")

    goal_plan = _unwrap_plan(goal_state, "GOAL_STATE")
    task_plan = _unwrap_plan(task_state, "TASK_STATE")

    # Replay validation is deliberately first: malformed durable state must not
    # be converted into a benign SKIP that hides a control-plane problem.
    replay = _validated_replay(goal_plan, task_plan)

    goal_status = str(goal_plan.get("status", "")).strip().upper()
    plan_lifecycle = str(task_plan.get("plan_lifecycle", "ACTIVE")).strip().upper()
    raw_tasks = task_plan.get("tasks")
    if not isinstance(raw_tasks, list) or not raw_tasks:
        raise NativeGoalActivationError("TASK_PLAN_TASKS_REQUIRED")

    task_statuses = [
        str(task.get("status", "")).strip().upper()
        for task in raw_tasks
        if isinstance(task, Mapping)
    ]
    if len(task_statuses) != len(raw_tasks):
        raise NativeGoalActivationError("TASK_PLAN_TASK_INVALID")
    unfinished_count = sum(status not in TERMINAL_TASK_STATUSES for status in task_statuses)
    task_count = len(raw_tasks)

    common = {
        "schema": ACTIVATION_SCHEMA,
        "host_kind": host_kind,
        "goal_id": replay["goal_id"],
        "goal_status": goal_status,
        "plan_lifecycle": plan_lifecycle,
        "task_count": task_count,
        "unfinished_task_count": unfinished_count,
        "owner_prompt_required": False,
        "state_mutated": False,
        "projection_only": True,
        "native_goal_evaluator_is_acceptance_authority": False,
    }

    if plan_lifecycle != "ACTIVE":
        return {**common, "decision": NORMAL, "reason": f"PLAN_NOT_ACTIVE:{plan_lifecycle}"}
    if goal_status not in ACTIVE_GOAL_STATUSES:
        return {
            **common,
            "decision": NORMAL,
            "reason": f"GOAL_STATUS_NOT_AUTO_ACTIVATABLE:{goal_status or 'MISSING'}",
        }
    if task_count < 2:
        return {**common, "decision": NORMAL, "reason": "SINGLE_TASK_PLAN"}
    if unfinished_count == 0:
        return {**common, "decision": NORMAL, "reason": "ALL_TASKS_TERMINAL"}

    try:
        projection = build_native_goal_projection(
            host_kind,
            goal_plan,
            task_plan,
            baseline_ref=baseline_ref,
        )
    except NativeGoalBridgeError as exc:
        raise NativeGoalActivationError(str(exc)) from exc
    return {
        **common,
        "decision": ACTIVATE,
        "reason": "ACTIVE_MULTI_TASK_P2P_GOAL",
        "command": projection["command"],
        "condition": projection["condition"],
        "host_semantics": projection["host_semantics"],
        "contract_replay": projection["contract_replay"],
    }


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise NativeGoalActivationError(f"JSON_READ_FAILED:{path}:{exc}") from exc
    if not isinstance(value, dict):
        raise NativeGoalActivationError(f"JSON_OBJECT_REQUIRED:{path}")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    parser.add_argument("--host", default="auto", choices=("auto", *HOST_KINDS))
    parser.add_argument("--goal-state", default=".p2p/state/autopilot-goal-state.json")
    parser.add_argument("--task-state", default=".p2p/state/task-state.json")
    parser.add_argument("--baseline")
    parser.add_argument("--format", choices=("json", "command"), default="json")
    args = parser.parse_args()

    host_kind = detect_host_from_environment() if args.host == "auto" else args.host
    if host_kind is None:
        result = {
            "schema": ACTIVATION_SCHEMA,
            "decision": NORMAL,
            "reason": "HOST_NOT_CONFIDENTLY_DETECTED",
            "owner_prompt_required": False,
            "state_mutated": False,
            "projection_only": True,
        }
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
        return 0

    root = Path(args.root).expanduser().resolve()
    try:
        result = decide_native_goal_activation(
            host_kind,
            _read_json(root / args.goal_state),
            _read_json(root / args.task_state),
            baseline_ref=args.baseline,
        )
    except (OSError, NativeGoalActivationError) as exc:
        print(
            json.dumps(
                {
                    "schema": ACTIVATION_SCHEMA,
                    "status": "BLOCKED",
                    "error": str(exc),
                    "owner_prompt_required": False,
                    "state_mutated": False,
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 2

    if args.format == "command":
        if result["decision"] == ACTIVATE:
            print(result["command"])
        else:
            print(f"# P2P_NATIVE_GOAL_SKIP {result['reason']}")
    else:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
