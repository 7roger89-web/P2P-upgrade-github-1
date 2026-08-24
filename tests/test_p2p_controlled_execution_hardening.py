"""Focused C11 binding tests for Controlled Execution hardening."""
from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = REPO_ROOT / ".p2p" / "system"
TEMP_ROOT = REPO_ROOT / ".tmp"
TEMP_ROOT.mkdir(parents=True, exist_ok=True)
if str(SYSTEM_ROOT) not in sys.path:
    sys.path.insert(0, str(SYSTEM_ROOT))

from p2p_capabilities.autopilot_state import (  # noqa: E402
    GoalPlan,
    GoalStateStore,
)
from p2p_capabilities.autopilot_verifier import TaskVerifier  # noqa: E402
from p2p_capabilities.fake_execution_backend import (  # noqa: E402
    FakeDeterministicExecutionBackend,
)
from p2p_capabilities.p2p_fw01_loop import build_fw01_loop  # noqa: E402
from p2p_capabilities.task_state import (  # noqa: E402
    TaskControlPlaneError,
    TaskStateStore,
)


class RaisingBackend:
    def execute(self, contract):
        raise RuntimeError("synthetic executor failure")


class ControlledExecutionHardeningTests(unittest.TestCase):
    def _goal(self) -> GoalPlan:
        return GoalPlan(
            goal_id="goal-controlled-execution",
            goal_version="v1",
            title="Controlled execution hardening",
            purpose="Prove one canonical task graph survives restart.",
            owner_approval_ref="owner-approval-controlled-execution",
            scope=("docs",),
            non_scope=("production",),
            plan_task_ids=("one", "two"),
        )

    def _records(self, root: Path) -> dict[str, dict]:
        common = {
            "goal_id": "goal-controlled-execution",
            "scope": ("docs",),
            "non_scope": ("production",),
            "acceptance_requirements": ("acceptance",),
            "required_evidence": ("evidence",),
            "permission_needs": ("sandboxed-default",),
            "required_capabilities": (),
            "last_preflight": {"status": "PASS"},
            "workspace": str(root),
            "execution_target": "fake-1",
            "expected_output": ("result.txt",),
            "verify_spec": ("default",),
            "input_evidence_pointers": (),
            "skills": (),
            "team": (),
        }
        first = dict(common)
        first.update({
            "task_id": "one",
            "title": "Complete the first bounded task",
            "purpose": "Create the first verified result.",
            "status": "READY",
            "dependencies": (),
        })
        second = dict(common)
        second.update({
            "task_id": "two",
            "title": "Complete the dependent bounded task",
            "purpose": "Create the dependent verified result.",
            "status": "READY",
            "dependencies": ("one",),
        })
        return {"one": first, "two": second}

    def _build(self, root: Path, records: dict[str, dict], *, backend=None):
        execution_backend = backend or FakeDeterministicExecutionBackend()
        if isinstance(execution_backend, FakeDeterministicExecutionBackend):
            execution_backend.set_fixtures({"one": ("PASS",), "two": ("PASS",)})
        verifier = TaskVerifier()
        verifier.set_fixtures({
            "one": ("ACCEPTABLE",),
            "two": ("ACCEPTABLE",),
        })
        return build_fw01_loop(
            root,
            goal_plan=self._goal(),
            task_records=records,
            backend=execution_backend,
            verifier=verifier,
            registry_permissions=("read", "write", "run-tests", "diff"),
            goal_scope="docs",
            execution_targets=("fake-1",),
        )

    def test_restart_uses_canonical_graph_and_preserves_completion(self):
        with tempfile.TemporaryDirectory(
                dir=TEMP_ROOT, prefix="p2p-ce-restart-") as raw:
            root = Path(raw)
            records = self._records(root)
            loop = self._build(root, records)
            self.assertEqual(loop.loop.select_next_safe_task(), "one")

            first_result = loop.loop.step()
            self.assertEqual(first_result["status"], "TASK_DONE_CONTINUE")
            persisted = TaskStateStore(root).require()
            self.assertEqual(persisted.tasks["one"].status, "DONE")
            self.assertEqual(
                persisted.tasks["one"].completion["evidence_refs"],
                ["evidence"],
            )
            self.assertIsNotNone(persisted.tasks["one"].checkpoint)

            changed_session = copy.deepcopy(records)
            changed_session["one"]["status"] = "READY"
            changed_session["two"]["status"] = "READY"
            fresh = self._build(root, changed_session)
            self.assertEqual(fresh.loop.task_plan().tasks["one"].status,
                             "DONE")
            self.assertEqual(fresh.loop.select_next_safe_task(), "two")

    def test_graph_and_execution_descriptor_drift_fail_closed(self):
        with tempfile.TemporaryDirectory(
                dir=TEMP_ROOT, prefix="p2p-ce-drift-") as raw:
            root = Path(raw)
            records = self._records(root)
            self._build(root, records)

            graph_drift = copy.deepcopy(records)
            graph_drift["two"]["dependencies"] = ()
            with self.assertRaisesRegex(RuntimeError,
                                        "TASK_PLAN_IDENTITY_MISMATCH"):
                self._build(root, graph_drift)

            descriptor_drift = copy.deepcopy(records)
            descriptor_drift["one"]["workspace"] = str(root / "other")
            with self.assertRaisesRegex(
                RuntimeError, "TASK_EXECUTION_DESCRIPTOR_MISMATCH"):
                self._build(root, descriptor_drift)

    def test_goal_mismatch_does_not_initialize_task_state(self):
        with tempfile.TemporaryDirectory(
                dir=TEMP_ROOT, prefix="p2p-ce-goal-mismatch-") as raw:
            root = Path(raw)
            records = self._records(root)
            goal = self._goal()
            goal_store = GoalStateStore(root)
            goal_store.initialize(goal)
            goal_store.transition("APPROVED")

            wrong_goal = GoalPlan(
                goal_id="different-goal",
                goal_version=goal.goal_version,
                title=goal.title,
                purpose=goal.purpose,
                owner_approval_ref=goal.owner_approval_ref,
                scope=goal.scope,
                non_scope=goal.non_scope,
                plan_task_ids=goal.plan_task_ids,
            )
            backend = FakeDeterministicExecutionBackend()
            backend.set_fixtures({"one": ("PASS",), "two": ("PASS",)})
            verifier = TaskVerifier()
            verifier.set_fixtures({"one": ("ACCEPTABLE",),
                                   "two": ("ACCEPTABLE",)})
            with self.assertRaisesRegex(RuntimeError, "GOAL_ID_MISMATCH"):
                build_fw01_loop(
                    root,
                    goal_plan=wrong_goal,
                    task_records=records,
                    backend=backend,
                    verifier=verifier,
                    registry_permissions=("read", "write", "run-tests", "diff"),
                    goal_scope="docs",
                    execution_targets=("fake-1",),
                )
            self.assertFalse(
                (root / ".p2p" / "state" / "task-state.json").exists())

    def test_corrupt_task_state_is_not_replaced(self):
        with tempfile.TemporaryDirectory(
                dir=TEMP_ROOT, prefix="p2p-ce-corrupt-") as raw:
            root = Path(raw)
            records = self._records(root)
            self._build(root, records)
            state_path = root / ".p2p" / "state" / "task-state.json"
            payload = json.loads(state_path.read_text(encoding="utf-8"))
            payload["plan_hash"] = "0" * 64
            state_path.write_text(json.dumps(payload), encoding="utf-8")

            with self.assertRaises(TaskControlPlaneError):
                self._build(root, records)
            self.assertEqual(
                json.loads(state_path.read_text(encoding="utf-8"))["plan_hash"],
                "0" * 64,
            )

    def test_executor_exception_releases_slot_and_blocks_canonical_task(self):
        with tempfile.TemporaryDirectory(
                dir=TEMP_ROOT, prefix="p2p-ce-exception-") as raw:
            root = Path(raw)
            records = self._records(root)
            loop = self._build(root, records, backend=RaisingBackend())
            outcome = loop.loop.step()
            self.assertEqual(outcome["status"], "EXECUTOR_EXCEPTION")
            self.assertEqual(loop.loop.budget.usage.active_executions, 0)
            task = TaskStateStore(root).require().tasks["one"]
            self.assertEqual(task.status, "BLOCKED")
            self.assertEqual(task.blocker["reason"], "EXECUTOR_EXCEPTION")
            self.assertIsNotNone(task.checkpoint)
            self.assertEqual(task.checkpoint["recovery_classification"],
                             "UNKNOWN")


if __name__ == "__main__":
    unittest.main()
