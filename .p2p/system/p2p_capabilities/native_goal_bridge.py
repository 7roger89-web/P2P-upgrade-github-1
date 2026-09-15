"""Read-only projection from canonical P2P goal/task state to host-native /goal.

Adopts only Supergoal's useful host-native goal pattern. Canonical P2P
GoalPlan/TaskPlan and independent verifier evidence remain authoritative.
No parallel state, process, retry policy, permission change, or provider route
is created here.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Mapping

BRIDGE_SCHEMA = "p2p-native-goal-projection/1"
REPLAY_SCHEMA = "p2p-contract-replay-manifest/1"
CLAUDE_CODE = "claude_code"
CODEX_CLI = "codex_cli"
HOST_KINDS = (CLAUDE_CODE, CODEX_CLI)
_GOAL_MAX_CHARS = 4000
_GIT_OID_RE = re.compile(r"^[0-9a-f]{40}$")
_PACKAGED_WORKTREE_COMMAND = (
    "python .agents/skills/p2p/scripts/p2p_native_goal.py worktree summary"
)

_TASK_REPLAY_FIELDS = (
    "task_id",
    "goal_id",
    "title",
    "purpose",
    "dependencies",
    "scope",
    "non_scope",
    "acceptance_requirements",
    "required_evidence",
    "permission_needs",
    "required_capabilities",
    "optional_capabilities",
    "context_refs",
    "output_refs",
    "requirement_refs",
    "decision_refs",
)
_LIST_FIELDS = {
    "dependencies",
    "scope",
    "non_scope",
    "acceptance_requirements",
    "required_evidence",
    "permission_needs",
    "required_capabilities",
    "optional_capabilities",
    "context_refs",
    "output_refs",
    "requirement_refs",
    "decision_refs",
}
_REQUIRED_LIST_FIELDS = {"scope", "acceptance_requirements", "required_evidence"}

_HOST_SEMANTICS: dict[str, dict[str, Any]] = {
    CLAUDE_CODE: {
        "native_command": "/goal",
        "documented_semantics": "EVALUATOR_DRIVEN_SESSION_LOOP",
        "automatic_turn_continuation_documented": True,
        "separate_completion_evaluator_documented": True,
        "evaluator_observation_scope": "TRANSCRIPT_ONLY",
    },
    CODEX_CLI: {
        "native_command": "/goal",
        "documented_semantics": "PERSISTENT_ACTIVE_CHAT_OBJECTIVE",
        "automatic_turn_continuation_documented": False,
        "separate_completion_evaluator_documented": False,
        "evaluator_observation_scope": "NOT_CLAIMED",
    },
}


class NativeGoalBridgeError(ValueError):
    """Raised when a native-goal projection would drift from P2P authority."""


def _required_text(value: Any, field: str, *, max_length: int = 4096) -> str:
    if not isinstance(value, str):
        raise NativeGoalBridgeError(f"{field.upper()}_INVALID")
    text = value.strip()
    if not text or len(text) > max_length:
        raise NativeGoalBridgeError(f"{field.upper()}_INVALID")
    return text


def _unique_text_list(value: Any, field: str, *, required: bool = False) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise NativeGoalBridgeError(f"{field.upper()}_MUST_BE_LIST")
    items = tuple(_required_text(item, field, max_length=2048) for item in value)
    if required and not items:
        raise NativeGoalBridgeError(f"{field.upper()}_REQUIRED")
    if len(items) != len(set(items)):
        raise NativeGoalBridgeError(f"{field.upper()}_MUST_BE_UNIQUE")
    return items


def _canonical_hash(value: Mapping[str, Any]) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _goal_identity(goal_plan: Mapping[str, Any]) -> tuple[str, str, tuple[str, ...]]:
    if not isinstance(goal_plan, Mapping):
        raise NativeGoalBridgeError("GOAL_PLAN_MUST_BE_OBJECT")
    goal_id = _required_text(goal_plan.get("goal_id"), "goal_id", max_length=128)
    goal_version = _required_text(goal_plan.get("goal_version"), "goal_version", max_length=32)
    task_order = _unique_text_list(
        goal_plan.get("plan_task_ids"), "plan_task_ids", required=True
    )
    return goal_id, goal_version, task_order


def _task_records(task_plan: Mapping[str, Any], goal_id: str) -> dict[str, Mapping[str, Any]]:
    if not isinstance(task_plan, Mapping):
        raise NativeGoalBridgeError("TASK_PLAN_MUST_BE_OBJECT")
    if _required_text(task_plan.get("goal_id"), "task_plan.goal_id", max_length=128) != goal_id:
        raise NativeGoalBridgeError("TASK_PLAN_GOAL_MISMATCH")
    raw_tasks = task_plan.get("tasks")
    if not isinstance(raw_tasks, list) or not raw_tasks:
        raise NativeGoalBridgeError("TASK_PLAN_TASKS_REQUIRED")
    tasks: dict[str, Mapping[str, Any]] = {}
    for raw in raw_tasks:
        if not isinstance(raw, Mapping):
            raise NativeGoalBridgeError("TASK_PLAN_TASK_INVALID")
        task_id = _required_text(raw.get("task_id"), "task_id", max_length=128)
        if _required_text(raw.get("goal_id"), "task.goal_id", max_length=128) != goal_id:
            raise NativeGoalBridgeError(f"TASK_GOAL_MISMATCH:{task_id}")
        if task_id in tasks:
            raise NativeGoalBridgeError(f"TASK_ID_DUPLICATE:{task_id}")
        tasks[task_id] = raw
    return tasks


def build_contract_replay_manifest(
    goal_plan: Mapping[str, Any], task_plan: Mapping[str, Any]
) -> dict[str, Any]:
    """Project original task contracts for final replay without new authority."""

    goal_id, goal_version, task_order = _goal_identity(goal_plan)
    tasks = _task_records(task_plan, goal_id)
    if set(task_order) != set(tasks):
        raise NativeGoalBridgeError("GOAL_TASK_SET_MISMATCH")

    replay_tasks: list[dict[str, Any]] = []
    for task_id in task_order:
        source = tasks[task_id]
        immutable: dict[str, Any] = {}
        for field in _TASK_REPLAY_FIELDS:
            value = source.get(field)
            if field in _LIST_FIELDS:
                value = list(
                    _unique_text_list(
                        value or [],
                        f"{task_id}.{field}",
                        required=field in _REQUIRED_LIST_FIELDS,
                    )
                )
            else:
                value = _required_text(value, f"{task_id}.{field}", max_length=8192)
            immutable[field] = value
        replay_tasks.append(
            {
                "task_id": task_id,
                "contract_fingerprint": _canonical_hash(immutable),
                "scope": immutable["scope"],
                "non_scope": immutable["non_scope"],
                "acceptance_requirements": immutable["acceptance_requirements"],
                "required_evidence": immutable["required_evidence"],
                "permission_needs": immutable["permission_needs"],
            }
        )

    manifest = {
        "schema": REPLAY_SCHEMA,
        "goal_id": goal_id,
        "goal_version": goal_version,
        "task_order": list(task_order),
        "tasks": replay_tasks,
        "authority_refs": [
            ".p2p/state/autopilot-goal-state.json",
            ".p2p/state/task-state.json",
            ".p2p/state/goal-contract.json",
        ],
        "completion_authority": "P2P_TASK_STATE_PLUS_INDEPENDENT_VERIFIER_EVIDENCE",
        "native_goal_evaluator_is_authority": False,
        "recovery_policy": "P2P_ADAPTIVE_FAILURE_CLASSIFICATION",
        "fixed_retry_hard_stop": None,
        "projection_only": True,
    }
    manifest["manifest_fingerprint"] = _canonical_hash(manifest)
    return manifest


def _validate_baseline_ref(value: str | None) -> str | None:
    if value is None:
        return None
    text = value.strip().lower()
    if not _GIT_OID_RE.fullmatch(text):
        raise NativeGoalBridgeError("BASELINE_REF_MUST_BE_FULL_GIT_COMMIT_OID")
    return text


def build_native_goal_projection(
    host_kind: str,
    goal_plan: Mapping[str, Any],
    task_plan: Mapping[str, Any],
    *,
    baseline_ref: str | None = None,
) -> dict[str, Any]:
    """Return one ready-to-paste host-native `/goal` command."""

    if host_kind not in HOST_KINDS:
        raise NativeGoalBridgeError("HOST_KIND_UNSUPPORTED")
    baseline = _validate_baseline_ref(baseline_ref)
    replay = build_contract_replay_manifest(goal_plan, task_plan)
    goal_id = replay["goal_id"]
    task_count = len(replay["task_order"])

    clauses = [
        f"Complete P2P goal {goal_id} using only canonical P2P goal/task state ({task_count} tasks).",
        "Reload durable task state before each task; obey each task's original scope, non-scope, permissions, acceptance requirements, and required evidence.",
        "Use the existing P2P verifier/evidence authority: executor DONE/PASS and this native /goal evaluator are not acceptance authority.",
        "Before declaring completion, replay every original task contract and surface the P2P verifier/evidence result and durable refs in the transcript.",
    ]
    if baseline is not None:
        clauses.append(
            f"Re-check the complete working tree against baseline {baseline} with "
            f"`{_PACKAGED_WORKTREE_COMMAND} --baseline {baseline}` and surface the JSON result."
        )
    clauses.extend(
        [
            "Completion holds only when canonical goal state is GOAL_DONE and every canonical task is DONE with independent current evidence.",
            "On Owner Gate/BLOCKED or failures, follow P2P adaptive failure classification; do not use a fixed retry count, widen scope, grant permissions, promote, release, or deploy.",
        ]
    )
    condition = " ".join(clauses)
    if len(condition) > _GOAL_MAX_CHARS:
        raise NativeGoalBridgeError("NATIVE_GOAL_CONDITION_TOO_LONG")

    semantics = dict(_HOST_SEMANTICS[host_kind])
    return {
        "schema": BRIDGE_SCHEMA,
        "host_kind": host_kind,
        "condition": condition,
        "command": f"{semantics['native_command']} {condition}",
        "condition_chars": len(condition),
        "host_semantics": semantics,
        "contract_replay": replay,
        "state_authority_created": False,
        "background_process_created": False,
        "permission_mode_changed": False,
        "native_goal_evaluator_is_acceptance_authority": False,
    }
