from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYSTEM = ROOT / ".p2p" / "system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

from p2p_capabilities.native_goal_activation import (  # noqa: E402
    ACTIVATE,
    NORMAL,
    CLAUDE_CODE,
    CODEX_CLI,
    NativeGoalActivationError,
    decide_native_goal_activation,
    detect_host_from_environment,
)


def task(task_id: str, *, status: str = "READY", dependency: str | None = None) -> dict:
    return {
        "task_id": task_id,
        "goal_id": "goal-auto-native",
        "title": f"Title {task_id}",
        "purpose": f"Purpose {task_id}",
        "status": status,
        "dependencies": [dependency] if dependency else [],
        "scope": [f"scope:{task_id}"],
        "non_scope": [f"non-scope:{task_id}"],
        "acceptance_requirements": [f"accept:{task_id}"],
        "required_evidence": [f"evidence:{task_id}"],
        "permission_needs": ["sandboxed-default"],
        "required_capabilities": [],
        "optional_capabilities": [],
        "context_refs": [],
        "output_refs": [],
        "requirement_refs": [],
        "decision_refs": [],
    }


def goal_plan(*, status: str = "APPROVED", task_ids: list[str] | None = None) -> dict:
    ids = task_ids or ["task-a", "task-b"]
    return {
        "schema": "p2p-autopilot-goal/1",
        "goal_id": "goal-auto-native",
        "goal_version": "v1",
        "plan_task_ids": ids,
        "status": status,
    }


def task_plan(tasks: list[dict] | None = None, *, lifecycle: str = "ACTIVE") -> dict:
    return {
        "schema": "p2p-task-plan/1",
        "goal_id": "goal-auto-native",
        "plan_lifecycle": lifecycle,
        "tasks": tasks or [task("task-a"), task("task-b", dependency="task-a")],
    }


class TestNativeGoalAutoActivation(unittest.TestCase):
    def test_active_multi_task_goal_auto_activates_claude(self) -> None:
        result = decide_native_goal_activation(CLAUDE_CODE, goal_plan(), task_plan())
        self.assertEqual(result["decision"], ACTIVATE)
        self.assertEqual(result["reason"], "ACTIVE_MULTI_TASK_P2P_GOAL")
        self.assertTrue(result["command"].startswith("/goal "))
        self.assertFalse(result["owner_prompt_required"])
        self.assertFalse(result["state_mutated"])
        self.assertTrue(result["host_semantics"]["automatic_turn_continuation_documented"])

    def test_real_durable_wrapper_shape_is_unwrapped(self) -> None:
        wrapped_goal = {
            "schema": "p2p-autopilot-goal/1",
            "plan": goal_plan(status="IN_PROGRESS"),
            "goal_hash": "ignored-by-read-only-projection",
        }
        wrapped_tasks = {
            "schema": "p2p-task-state/1",
            "plan": task_plan(),
            "plan_hash": "ignored-by-read-only-projection",
        }
        result = decide_native_goal_activation(CLAUDE_CODE, wrapped_goal, wrapped_tasks)
        self.assertEqual(result["decision"], ACTIVATE)
        self.assertEqual(result["goal_status"], "IN_PROGRESS")
        self.assertEqual(result["task_count"], 2)

    def test_single_task_plan_stays_on_normal_p2p_path(self) -> None:
        one = task("task-a")
        result = decide_native_goal_activation(
            CLAUDE_CODE,
            goal_plan(task_ids=["task-a"]),
            task_plan([one]),
        )
        self.assertEqual(result["decision"], NORMAL)
        self.assertEqual(result["reason"], "SINGLE_TASK_PLAN")
        self.assertNotIn("command", result)

    def test_owner_gate_and_terminal_goal_do_not_auto_activate(self) -> None:
        for status in ("OWNER_GATE", "BLOCKED", "BUDGET_BOUNDARY", "VERIFIED", "GOAL_DONE", "TERMINAL", "CANCELLED", "PLANNED"):
            with self.subTest(status=status):
                result = decide_native_goal_activation(CLAUDE_CODE, goal_plan(status=status), task_plan())
                self.assertEqual(result["decision"], NORMAL)
                self.assertTrue(result["reason"].startswith("GOAL_STATUS_NOT_AUTO_ACTIVATABLE:"))

    def test_closed_or_superseded_plan_does_not_auto_activate(self) -> None:
        for lifecycle in ("CLOSED", "SUPERSEDED"):
            with self.subTest(lifecycle=lifecycle):
                result = decide_native_goal_activation(CLAUDE_CODE, goal_plan(), task_plan(lifecycle=lifecycle))
                self.assertEqual(result["decision"], NORMAL)
                self.assertEqual(result["reason"], f"PLAN_NOT_ACTIVE:{lifecycle}")

    def test_codex_activates_without_inventing_claude_continuation(self) -> None:
        result = decide_native_goal_activation(CODEX_CLI, goal_plan(), task_plan())
        self.assertEqual(result["decision"], ACTIVATE)
        self.assertFalse(result["host_semantics"]["automatic_turn_continuation_documented"])
        self.assertFalse(result["host_semantics"]["separate_completion_evaluator_documented"])

    def test_all_terminal_tasks_do_not_activate(self) -> None:
        tasks = [task("task-a", status="DONE"), task("task-b", status="CANCELLED")]
        result = decide_native_goal_activation(CLAUDE_CODE, goal_plan(), task_plan(tasks))
        self.assertEqual(result["decision"], NORMAL)
        self.assertEqual(result["reason"], "ALL_TASKS_TERMINAL")

    def test_malformed_state_fails_closed(self) -> None:
        malformed = task_plan()
        malformed["tasks"][0].pop("required_evidence")
        with self.assertRaises(NativeGoalActivationError):
            decide_native_goal_activation(CLAUDE_CODE, goal_plan(), malformed)

    def test_environment_detection_is_conservative(self) -> None:
        self.assertEqual(detect_host_from_environment({"CLAUDECODE": "1"}), CLAUDE_CODE)
        self.assertEqual(detect_host_from_environment({"CLAUDE_CODE_ENTRYPOINT": "cli"}), CLAUDE_CODE)
        self.assertIsNone(detect_host_from_environment({"CODEX_HOME": "/tmp/codex"}))
        self.assertIsNone(detect_host_from_environment({}))


if __name__ == "__main__":
    unittest.main()
