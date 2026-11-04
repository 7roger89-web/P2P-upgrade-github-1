from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYSTEM = ROOT / ".p2p" / "system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

from p2p_capabilities.native_goal_bridge import CLAUDE_CODE, CODEX_CLI  # noqa: E402
from p2p_capabilities.native_goal_gate import (  # noqa: E402
    NOT_NEEDED,
    READY_TO_INVOKE,
    UNAVAILABLE,
    evaluate_native_goal_gate,
)


def task(task_id: str, status: str = "READY") -> dict:
    return {
        "task_id": task_id,
        "goal_id": "goal-gate",
        "title": task_id,
        "purpose": task_id,
        "status": status,
        "dependencies": [],
        "scope": ["bounded"],
        "non_scope": ["no deploy"],
        "acceptance_requirements": ["proof"],
        "required_evidence": ["evidence"],
        "permission_needs": [],
        "required_capabilities": [],
        "optional_capabilities": [],
        "context_refs": [],
        "output_refs": [],
        "requirement_refs": [],
        "decision_refs": [],
    }


def goal(status: str = "APPROVED", ids=None) -> dict:
    return {
        "schema": "p2p-autopilot-goal/1",
        "goal_id": "goal-gate",
        "goal_version": "v1",
        "plan_task_ids": ids or ["a", "b"],
        "status": status,
    }


def plan(tasks=None) -> dict:
    return {
        "schema": "p2p-task-plan/1",
        "goal_id": "goal-gate",
        "plan_lifecycle": "ACTIVE",
        "tasks": tasks or [task("a"), task("b")],
    }


class TestNativeGoalGate(unittest.TestCase):
    def test_eligible_and_ready_is_ready_to_invoke_not_invoked(self) -> None:
        result = evaluate_native_goal_gate(
            CLAUDE_CODE,
            goal(),
            plan(),
            probe=lambda host: {
                "status": "READY_TO_INVOKE",
                "host_kind": host,
                "invocation_proven": False,
            },
        )
        self.assertEqual(result["status"], READY_TO_INVOKE)
        self.assertTrue(result["command"].startswith("/goal "))
        self.assertFalse(result["invocation_proven"])
        self.assertTrue(result["host_command_boundary_required"])
        self.assertTrue(result["do_not_launch_nested_host_to_fake_same_session_invocation"])
        self.assertEqual(result["after_host_acceptance_verify_with"], "/goal")
        self.assertEqual(result["receipt_proof_kind"], "CLAUDE_GOAL_STATUS_VIEW")

    def test_codex_uses_codex_status_receipt(self) -> None:
        result = evaluate_native_goal_gate(
            CODEX_CLI,
            goal(),
            plan(),
            probe=lambda host: {"status": "READY_TO_INVOKE", "host_kind": host},
        )
        self.assertEqual(result["status"], READY_TO_INVOKE)
        self.assertEqual(result["receipt_proof_kind"], "CODEX_GOAL_STATUS_VIEW")

    def test_host_unavailable_falls_back_without_claiming_invocation(self) -> None:
        result = evaluate_native_goal_gate(
            CODEX_CLI,
            goal(),
            plan(),
            probe=lambda host: {
                "status": "UNAVAILABLE",
                "host_kind": host,
                "reason": "CODEX_GOALS_DISABLED",
            },
        )
        self.assertEqual(result["status"], UNAVAILABLE)
        self.assertEqual(result["p2p_path"], "NORMAL_P2P_PATH")
        self.assertFalse(result["invocation_proven"])
        self.assertNotIn("command", result)

    def test_single_task_is_not_needed_and_does_not_probe_host(self) -> None:
        probed = []
        result = evaluate_native_goal_gate(
            CLAUDE_CODE,
            goal(ids=["a"]),
            plan([task("a")]),
            probe=lambda host: probed.append(host),
        )
        self.assertEqual(result["status"], NOT_NEEDED)
        self.assertEqual(probed, [])

    def test_owner_gate_is_not_needed(self) -> None:
        result = evaluate_native_goal_gate(
            CLAUDE_CODE,
            goal(status="OWNER_GATE"),
            plan(),
            probe=lambda host: self.fail("host must not be probed for owner-gated goal"),
        )
        self.assertEqual(result["status"], NOT_NEEDED)
        self.assertFalse(result["invocation_proven"])


if __name__ == "__main__":
    unittest.main()
