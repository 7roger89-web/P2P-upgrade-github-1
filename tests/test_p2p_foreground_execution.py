from __future__ import annotations

import ast
import json
import importlib.util
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = REPO_ROOT / ".p2p" / "system"
if str(SYSTEM_ROOT) not in sys.path:
    sys.path.insert(0, str(SYSTEM_ROOT))

from p2p_capabilities.evidence import EvidenceClaim  # noqa: E402
from p2p_capabilities.foreground_execution import (  # noqa: E402
    ExecutionBudget,
    ExecutionIntent,
    ExecutionRuntime,
    ForegroundExecutionController,
    ForegroundExecutionError,
    ForegroundPermissionError,
    ForegroundScopeError,
    _permission_binding,
    _workspace_binding,
    _workspace_snapshot,
)
from p2p_capabilities import fw06_operational_resilience as fw06  # noqa: E402
from p2p_capabilities.task_state import TaskPlan, TaskStateStore  # noqa: E402


NOW = "2026-08-14T16:00:00+00:00"


def goal(goal_id: str = "goal-foreground-test") -> dict[str, object]:
    return {
        "goal_id": goal_id,
        "scope": ["output.txt", "notes/*.txt"],
        "out_of_scope": ["scheduler", "background worker", ".p2p/state"],
        "completion_criteria": [{"criterion_id": "criterion-foreground", "description": "direct result is verified"}],
    }


def task(task_id: str = "one", **extra: object) -> dict[str, object]:
    return {
        "task_id": task_id,
        "title": f"Foreground {task_id}",
        "purpose": "Perform one bounded direct action and verify it.",
        "scope": ["output.txt", "notes/*.txt"],
        "acceptance_requirements": [f"acceptance-{task_id}"],
        "required_evidence": [f"evidence-{task_id}"],
        **extra,
    }


def claim(task_id: str = "one", *, fingerprint: str = "a" * 64, status: str = "VERIFIED") -> EvidenceClaim:
    reference = f"evidence-{task_id}"
    return EvidenceClaim(
        claim="The independent read-only verifier confirmed the scoped artifact.",
        required_evidence=(reference,),
        actual_evidence=(
            {
                "source": "tests/test_p2p_foreground_execution.py",
                "evidence_ref": reference,
                "origin": "RUNTIME_EVIDENCE",
                "observed_at": NOW,
                "freshness": "CURRENT",
                "scope": ["output.txt"],
                "source_binding": "foreground-test",
                "fingerprint": fingerprint,
            },
        ),
        status=status,
    )


def healthy() -> dict[str, object]:
    return {
        "state": "HEALTHY",
        "states": {
            "INSTALLED": True,
            "DISCOVERED": True,
            "ELIGIBLE": True,
            "RESOLVED": True,
            "EXECUTABLE": True,
            "HEALTHY": True,
        },
        "profile_presence_is_runtime_proof": False,
    }


class ForegroundExecutionTests(unittest.TestCase):
    @staticmethod
    def write_permission() -> dict[str, dict[str, str]]:
        return {"WRITE": {"status": "GRANTED", "source_ref": "permission/foreground-test"}}

    def mutation_task(self) -> dict[str, object]:
        return task(permission_needs=["WRITE"])

    def make_controller(self, root: Path, *, task_specs: list[dict[str, object]] | None = None, goal_id: str = "goal-foreground-test") -> ForegroundExecutionController:
        plan = TaskPlan.from_goal(goal(goal_id), task_specs or [task()], now=NOW)
        TaskStateStore(root).initialize(plan, at=NOW)
        return ForegroundExecutionController(root)

    def mutation_intent(self, root: Path, controller: ForegroundExecutionController, *, lease_id: str = "") -> ExecutionIntent:
        plan = controller.store.require()
        task_record = plan.tasks["one"]
        workspace = _workspace_binding(root)
        baseline = _workspace_snapshot(root)
        return controller._build_intent(
            plan,
            task_record,
            action_name="test-mutation",
            budget=ExecutionBudget(allow_mutation=True),
            verification_plan={"mode": "TEST"},
            owner_gate={"status": "APPROVED", "source_ref": "owner/test"},
            baseline_binding=baseline,
            candidate_binding=baseline,
            workspace_binding=workspace,
            permission_binding=_permission_binding(task_record, self.write_permission()),
            lease_id=lease_id,
        )

    def test_selects_one_ready_task_and_reports_direct_contract(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT / ".tmp", prefix="p2p-c12-select-") as raw:
            controller = self.make_controller(Path(raw))
            selected = controller.select()
            self.assertEqual(selected["status"], "SELECTED")
            self.assertEqual(selected["task_id"], "one")
            self.assertFalse(selected["automatic_start"])
            self.assertFalse(selected["background_execution"])
            self.assertEqual(selected["execution_strategy"], "DIRECT")
            self.assertEqual(selected["delegated_children"], 0)

    def test_preflight_denied_capability_blocks_without_action(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT / ".tmp", prefix="p2p-c12-preflight-") as raw:
            root = Path(raw)
            controller = self.make_controller(root, task_specs=[task(required_capabilities=["cap-x"])])
            calls: list[str] = []

            result = controller.execute(lambda runtime: calls.append("action"), lambda runtime: {"status": "VERIFIED", "evidence_claims": [claim()]})
            self.assertEqual(result["status"], "BLOCKED")
            self.assertEqual(calls, [])
            self.assertEqual(TaskStateStore(root).require().tasks["one"].status, "BLOCKED")

    def test_stale_context_blocks_before_the_direct_path(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT / ".tmp", prefix="p2p-c12-context-") as raw:
            root = Path(raw)
            controller = self.make_controller(root, task_specs=[task(context_refs=["context/one"])])
            calls: list[str] = []
            result = controller.execute(
                lambda runtime: calls.append("action"),
                lambda runtime: {"status": "VERIFIED", "evidence_claims": [claim()]},
                context_state={"context/one": {"status": "STALE"}},
            )
            self.assertEqual(result["status"], "BLOCKED")
            self.assertEqual(calls, [])

    def test_missing_optional_capability_does_not_block_safe_fallback(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT / ".tmp", prefix="p2p-c12-optional-") as raw:
            controller = self.make_controller(Path(raw), task_specs=[task(optional_capabilities=["optional-cap"])])
            result = controller.preflight()
            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["optional_capabilities_unavailable"], ["optional-cap"])

    def test_owner_gate_is_required_before_scoped_mutation(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT / ".tmp", prefix="p2p-c12-owner-") as raw:
            root = Path(raw)
            controller = self.make_controller(root)
            calls: list[str] = []
            result = controller.execute(
                lambda runtime: calls.append("action"),
                lambda runtime: {"status": "VERIFIED", "evidence_claims": [claim()]},
                budget=ExecutionBudget(allow_mutation=True),
            )
            self.assertEqual(result["status"], "WAITING_OWNER")
            self.assertEqual(calls, [])
            self.assertTrue(result["owner_question"]["options"])
            self.assertEqual(result["task_status"], "WAITING_OWNER")
            owner_decision = TaskStateStore(root).require().tasks["one"].owner_decision
            self.assertEqual(TaskStateStore(root).require().tasks["one"].status, "WAITING_OWNER")
            self.assertIsNotNone(owner_decision)
            self.assertEqual(owner_decision["status"], "PENDING")

    def test_direct_success_requires_independent_current_evidence(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT / ".tmp", prefix="p2p-c12-success-") as raw:
            root = Path(raw)
            controller = self.make_controller(root, task_specs=[self.mutation_task()])

            def action(runtime):
                runtime.write_text("output.txt", "bounded result")
                return {"status": "SUCCEEDED", "summary": "direct action returned"}

            def verify(runtime, action_result):
                self.assertEqual(action_result["status"], "SUCCEEDED")
                self.assertEqual(runtime.read_text("output.txt"), "bounded result")
                return {"status": "VERIFIED", "evidence_claims": [claim()], "candidate_state": {"verified": True}}

            result = controller.execute(
                action,
                verify,
                owner_gate={"status": "APPROVED", "source_ref": "owner/test-success"},
                permission_state=self.write_permission(),
                budget=ExecutionBudget(allow_mutation=True),
            )
            self.assertEqual(result["status"], "DONE")
            self.assertEqual(TaskStateStore(root).require().tasks["one"].status, "DONE")
            self.assertTrue(result["intent_ref"].endswith("/intent.json"))
            self.assertGreaterEqual(len(result["receipt_refs"]), 4)
            self.assertNotIn("bounded result", json.dumps(result))
            self.assertFalse(result["output_is_evidence"])
            intent_payload = json.loads((root / result["intent_ref"]).read_text(encoding="utf-8"))
            self.assertEqual(intent_payload["objective"], "Foreground one: Perform one bounded direct action and verify it.")
            self.assertEqual(intent_payload["baseline_binding"], intent_payload["candidate_binding"])
            self.assertEqual(intent_payload["workspace_binding"], _workspace_binding(root))
            self.assertEqual(intent_payload["permission_binding"], _permission_binding(TaskStateStore(root).require().tasks["one"], self.write_permission()))
            self.assertTrue(intent_payload["lease_id"])
            final_receipt = json.loads((root / result["receipt_refs"][-1]).read_text(encoding="utf-8"))
            self.assertEqual(final_receipt["candidate_binding"], _workspace_snapshot(root))
            self.assertEqual(final_receipt["baseline_binding"], intent_payload["baseline_binding"])
            self.assertEqual(final_receipt["workspace_binding"], intent_payload["workspace_binding"])
            lease_rows = [row for row in fw06.read_leases(root) if row.get("lease_id") == intent_payload["lease_id"]]
            self.assertTrue(lease_rows)
            self.assertEqual(lease_rows[-1]["status"], "RELEASED")

    def test_role_name_and_handoff_data_cannot_create_write_permission(self) -> None:
        for label, supplied in (
            ("role", {"p2p_iris": {"status": "GRANTED", "source_ref": "role/p2p_iris"}}),
            ("handoff", {"handoff-1234567890abcdef": {"status": "GRANTED", "source_ref": "handoff/ref"}}),
        ):
            with self.subTest(label=label), tempfile.TemporaryDirectory(dir=REPO_ROOT / ".tmp", prefix=f"p2p-c12-{label}-permission-") as raw:
                root = Path(raw)
                controller = self.make_controller(root, task_specs=[self.mutation_task()])
                calls: list[str] = []
                result = controller.execute(
                    lambda runtime: calls.append("action"),
                    lambda runtime: {"status": "VERIFIED", "evidence_claims": [claim()]},
                    owner_gate={"status": "APPROVED", "source_ref": "owner/test-role-separation"},
                    permission_state=supplied,
                    budget=ExecutionBudget(allow_mutation=True),
                )
                self.assertEqual(result["status"], "WAITING_OWNER")
                self.assertEqual(calls, [])
                self.assertFalse((root / "output.txt").exists())

    def test_mutation_requires_an_explicit_permission_even_with_owner_gate(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT / ".tmp", prefix="p2p-c12-owner-only-") as raw:
            root = Path(raw)
            controller = self.make_controller(root)
            calls: list[str] = []
            result = controller.execute(
                lambda runtime: calls.append("action"),
                lambda runtime: {"status": "VERIFIED", "evidence_claims": [claim()]},
                owner_gate={"status": "APPROVED", "source_ref": "owner/only"},
                budget=ExecutionBudget(allow_mutation=True),
            )
            self.assertEqual(result["status"], "BLOCKED")
            self.assertEqual(result["reason"], "EXPLICIT_MUTATION_PERMISSION_REQUIRED")
            self.assertEqual(calls, [])

    def test_no_write_lease_blocks_the_actual_runtime_mutation_seam(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT / ".tmp", prefix="p2p-c12-no-lease-") as raw:
            root = Path(raw)
            controller = self.make_controller(root, task_specs=[self.mutation_task()])
            runtime = ExecutionRuntime(root, self.mutation_intent(root, controller))
            with self.assertRaisesRegex(ForegroundPermissionError, "WRITE_LEASE_REQUIRED"):
                runtime.write_text("output.txt", "must not write")
            self.assertFalse((root / "output.txt").exists())

    def test_context_or_path_rebinding_cannot_replace_worktree_binding(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT / ".tmp", prefix="p2p-c12-worktree-binding-") as raw:
            root = Path(raw)
            controller = self.make_controller(root, task_specs=[self.mutation_task()])
            intent = self.mutation_intent(root, controller)
            with tempfile.TemporaryDirectory(dir=REPO_ROOT / ".tmp", prefix="p2p-c12-other-worktree-") as other_raw:
                other_root = Path(other_raw)
                runtime = ExecutionRuntime(other_root, intent)
                with self.assertRaisesRegex(ForegroundPermissionError, "WORKSPACE_BINDING_MISMATCH"):
                    runtime.write_text("output.txt", "must not write")
                self.assertFalse((other_root / "output.txt").exists())

    def test_wrong_baseline_blocks_before_any_runtime_write(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT / ".tmp", prefix="p2p-c12-baseline-") as raw:
            root = Path(raw)
            controller = self.make_controller(root, task_specs=[self.mutation_task()])

            def action(runtime):
                (root / "output.txt").write_text("unleased external mutation", encoding="utf-8")
                runtime.write_text("output.txt", "must not overwrite")

            result = controller.execute(
                action,
                lambda runtime: {"status": "VERIFIED", "evidence_claims": [claim()]},
                owner_gate={"status": "APPROVED", "source_ref": "owner/test-baseline"},
                permission_state=self.write_permission(),
                budget=ExecutionBudget(allow_mutation=True),
            )
            self.assertEqual(result["status"], "FAILED")
            self.assertIn("BASELINE_BINDING_MISMATCH", result["reason"])
            self.assertEqual((root / "output.txt").read_text(encoding="utf-8"), "unleased external mutation")

    def test_revoked_and_expired_leases_block_runtime_mutation(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT / ".tmp", prefix="p2p-c12-lease-negative-") as raw:
            root = Path(raw)
            controller = self.make_controller(root, task_specs=[self.mutation_task()])
            workspace = _workspace_binding(root)
            revoked = fw06.acquire_lease(
                root,
                owner_process="test-revoked",
                project_id=workspace,
                goal_id="goal-foreground-test",
                task_id="one",
                ttl_seconds=30,
            )
            revoked_id = str(revoked["lease"]["lease_id"])
            self.assertTrue(fw06.release_lease(root, revoked_id))
            revoked_runtime = ExecutionRuntime(root, self.mutation_intent(root, controller, lease_id=revoked_id))
            with self.assertRaisesRegex(ForegroundPermissionError, "WRITE_LEASE_NOT_ACTIVE"):
                revoked_runtime.write_text("output.txt", "must not write")

        with tempfile.TemporaryDirectory(dir=REPO_ROOT / ".tmp", prefix="p2p-c12-lease-expired-") as raw:
            root = Path(raw)
            controller = self.make_controller(root, task_specs=[self.mutation_task()])
            workspace = _workspace_binding(root)
            expired = fw06.acquire_lease(
                root,
                owner_process="test-expired",
                project_id=workspace,
                goal_id="goal-foreground-test",
                task_id="one",
                ttl_seconds=1,
            )
            expired_id = str(expired["lease"]["lease_id"])
            time.sleep(1.1)
            self.assertIn(expired_id, fw06.expire_leases(root))
            expired_runtime = ExecutionRuntime(root, self.mutation_intent(root, controller, lease_id=expired_id))
            with self.assertRaisesRegex(ForegroundPermissionError, "WRITE_LEASE_NOT_ACTIVE"):
                expired_runtime.write_text("output.txt", "must not write")

    def test_scope_expansion_requires_replan_at_runtime(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT / ".tmp", prefix="p2p-c12-scope-replan-") as raw:
            root = Path(raw)
            controller = self.make_controller(root, task_specs=[self.mutation_task()])
            result = controller.execute(
                lambda runtime: runtime.write_text("unlisted.txt", "must not write"),
                lambda runtime: {"status": "VERIFIED", "evidence_claims": [claim()]},
                owner_gate={"status": "APPROVED", "source_ref": "owner/test-scope-replan"},
                permission_state=self.write_permission(),
                budget=ExecutionBudget(allow_mutation=True),
            )
            self.assertEqual(result["status"], "FAILED")
            self.assertIn("SCOPE_EXPANSION_REQUIRES_REPLAN", result["reason"])
            self.assertFalse((root / "unlisted.txt").exists())

    def test_action_output_alone_cannot_complete(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT / ".tmp", prefix="p2p-c12-no-output-proof-") as raw:
            root = Path(raw)
            controller = self.make_controller(root, task_specs=[self.mutation_task()])

            result = controller.execute(
                lambda runtime: runtime.write_text("output.txt", "changed"),
                lambda runtime: {"status": "VERIFIED", "summary": "the action said done"},
                owner_gate={"status": "APPROVED", "source_ref": "owner/test-output"},
                permission_state=self.write_permission(),
                budget=ExecutionBudget(allow_mutation=True),
            )
            self.assertEqual(result["status"], "VERIFICATION_FAILED")
            self.assertEqual(TaskStateStore(root).require().tasks["one"].status, "ACTIVE")

    def test_scope_and_protected_state_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT / ".tmp", prefix="p2p-c12-scope-") as raw:
            root = Path(raw)
            controller = self.make_controller(root, task_specs=[self.mutation_task()])

            def escape(runtime):
                runtime.write_text("../escape.txt", "no")

            result = controller.execute(
                escape,
                lambda runtime: {"status": "VERIFIED", "evidence_claims": [claim()]},
                owner_gate={"status": "APPROVED", "source_ref": "owner/test-scope"},
                permission_state=self.write_permission(),
                budget=ExecutionBudget(allow_mutation=True),
            )
            self.assertEqual(result["status"], "FAILED")
            self.assertFalse((root.parent / "escape.txt").exists())

    def test_retry_is_finite_and_does_not_retry_mutation(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT / ".tmp", prefix="p2p-c12-retry-") as raw:
            root = Path(raw)
            controller = self.make_controller(root)
            attempts: list[int] = []

            def action(runtime):
                attempts.append(runtime.attempt)
                return {"status": "FAILED", "retryable": True, "summary": "transient direct failure"}

            result = controller.execute(
                action,
                lambda runtime: {"status": "VERIFIED", "evidence_claims": [claim()]},
                budget=ExecutionBudget(max_attempts=3, max_retries=2),
            )
            self.assertEqual(result["status"], "FAILED")
            self.assertEqual(attempts, [1, 2, 3])
            self.assertEqual(TaskStateStore(root).require().tasks["one"].status, "BLOCKED")

    def test_action_count_and_wall_clock_budgets_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT / ".tmp", prefix="p2p-c12-budget-") as raw:
            root = Path(raw)
            controller = self.make_controller(root, task_specs=[self.mutation_task()])
            count_limited = controller.execute(
                lambda runtime: runtime.write_text("output.txt", "too many actions"),
                lambda runtime: {"status": "VERIFIED", "evidence_claims": [claim()]},
                owner_gate={"status": "APPROVED", "source_ref": "owner/test-budget"},
                permission_state=self.write_permission(),
                budget=ExecutionBudget(max_tool_actions=1, allow_mutation=True),
            )
            self.assertEqual(count_limited["status"], "FAILED")

        with tempfile.TemporaryDirectory(dir=REPO_ROOT / ".tmp", prefix="p2p-c12-deadline-") as raw:
            root = Path(raw)
            controller = self.make_controller(root)

            def slow(runtime):
                time.sleep(0.01)
                return {"status": "SUCCEEDED"}

            deadline = controller.execute(slow, lambda runtime: {"status": "VERIFIED", "evidence_claims": [claim()]}, budget=ExecutionBudget(max_wall_clock_seconds=0.001))
            self.assertEqual(deadline["status"], "FAILED")

    def test_interruption_resume_verifies_without_rerunning_action(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT / ".tmp", prefix="p2p-c12-resume-") as raw:
            root = Path(raw)
            controller = self.make_controller(root, task_specs=[self.mutation_task()])
            action_calls: list[str] = []

            def action(runtime):
                action_calls.append("run")
                runtime.write_text("output.txt", "interrupted result")
                runtime.interrupt()

            interrupted = controller.execute(
                action,
                None,
                owner_gate={"status": "APPROVED", "source_ref": "owner/test-resume"},
                permission_state=self.write_permission(),
                budget=ExecutionBudget(allow_mutation=True),
            )
            self.assertEqual(interrupted["status"], "INTERRUPTED")
            self.assertEqual(TaskStateStore(root).require().tasks["one"].status, "ACTIVE")

            def verify(runtime):
                self.assertEqual(runtime.read_text("output.txt"), "interrupted result")
                return {"status": "VERIFIED", "evidence_claims": [claim()]}

            resumed = ForegroundExecutionController(root).resume(verify, permission_state=self.write_permission())
            self.assertEqual(resumed["status"], "DONE")
            self.assertEqual(action_calls, ["run"])
            self.assertEqual(TaskStateStore(root).require().tasks["one"].status, "DONE")
            self.assertEqual(resumed["resume"]["resume_classification"], "NEEDS_RECHECK")

    def test_candidate_mutation_invalidates_the_prior_audit(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT / ".tmp", prefix="p2p-c12-candidate-stale-") as raw:
            root = Path(raw)
            controller = self.make_controller(root, task_specs=[self.mutation_task()])
            interrupted = controller.execute(
                lambda runtime: (runtime.write_text("output.txt", "candidate-one"), runtime.interrupt())[1],
                None,
                owner_gate={"status": "APPROVED", "source_ref": "owner/test-candidate"},
                permission_state=self.write_permission(),
                budget=ExecutionBudget(allow_mutation=True),
            )
            self.assertEqual(interrupted["status"], "INTERRUPTED")
            (root / "output.txt").write_text("candidate-successor", encoding="utf-8")
            resumed = ForegroundExecutionController(root).resume(permission_state=self.write_permission())
            self.assertEqual(resumed["status"], "NEEDS_RECHECK")
            self.assertEqual(resumed["resume"]["resume_classification"], "NEEDS_RECHECK")
            self.assertEqual(TaskStateStore(root).require().tasks["one"].status, "ACTIVE")

    def test_completed_audit_becomes_stale_after_candidate_mutation(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT / ".tmp", prefix="p2p-c12-completed-stale-") as raw:
            root = Path(raw)
            controller = self.make_controller(root, task_specs=[self.mutation_task()])
            completed = controller.execute(
                lambda runtime: runtime.write_text("output.txt", "audited-candidate"),
                lambda runtime: {"status": "VERIFIED", "evidence_claims": [claim()]},
                owner_gate={"status": "APPROVED", "source_ref": "owner/test-completed-stale"},
                permission_state=self.write_permission(),
                budget=ExecutionBudget(allow_mutation=True),
            )
            self.assertEqual(completed["status"], "DONE")
            (root / "output.txt").write_text("successor-candidate", encoding="utf-8")
            stale = ForegroundExecutionController(root).resume()
            self.assertEqual(stale["status"], "STALE")
            self.assertEqual(stale["reason"], "AUDITED_CANDIDATE_STALE")
            self.assertEqual(TaskStateStore(root).require().tasks["one"].status, "DONE")

    def test_resume_never_auto_starts_without_a_read_only_verifier(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT / ".tmp", prefix="p2p-c12-resume-gate-") as raw:
            root = Path(raw)
            controller = self.make_controller(root, task_specs=[self.mutation_task()])
            controller.execute(
                lambda runtime: (runtime.write_text("output.txt", "pending"), runtime.interrupt())[1],
                None,
                owner_gate={"status": "APPROVED", "source_ref": "owner/test-resume-gate"},
                permission_state=self.write_permission(),
                budget=ExecutionBudget(allow_mutation=True),
            )
            resumed = ForegroundExecutionController(root).resume(permission_state=self.write_permission())
            self.assertEqual(resumed["status"], "NEEDS_RECHECK")
            self.assertFalse(resumed["automatic_start"])
            self.assertEqual(TaskStateStore(root).require().tasks["one"].status, "ACTIVE")

    def test_control_plane_partial_ledger_stops_before_action(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT / ".tmp", prefix="p2p-c12-control-plane-") as raw:
            root = Path(raw)
            controller = self.make_controller(root)
            ledger = root / ".p2p" / "state" / "execution-ledger.jsonl"
            ledger.write_text(ledger.read_text(encoding="utf-8") + "{invalid\n", encoding="utf-8")
            calls: list[str] = []
            result = controller.execute(lambda runtime: calls.append("action"), lambda runtime: {"status": "VERIFIED", "evidence_claims": [claim()]})
            self.assertEqual(result["status"], "CONTROL_PLANE_ERROR")
            self.assertEqual(calls, [])

    def test_multiple_active_tasks_are_refused(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT / ".tmp", prefix="p2p-c12-single-active-") as raw:
            root = Path(raw)
            controller = self.make_controller(root, task_specs=[task("one"), task("two")])
            first = controller.store.require().refresh_ready(now=NOW)
            first = first.transition("one", "ACTIVE", now=NOW)
            first = first.transition("two", "ACTIVE", now=NOW)
            controller.store.save(first, event_name="test_invalid_multiple_active", at=NOW)
            result = controller.select()
            self.assertEqual(result["status"], "CONTROL_PLANE_ERROR")
            self.assertIn("MULTIPLE_ACTIVE_TASKS", result["reason"])

    def test_identity_fields_are_not_allowed_in_intent(self) -> None:
        with self.assertRaises(ForegroundExecutionError):
            ExecutionIntent(
                execution_id="fg-12345678",
                task_id="one",
                goal_id="goal-foreground-test",
                plan_hash="a" * 64,
                plan_revision=1,
                project_binding="PROJECT_ROOT_BOUND",
                action_name="direct",
                scope=("output.txt",),
                non_scope=(),
                verification_plan={"agent": "must-not-bind"},
            )

    def test_budget_rejects_network_and_delegation(self) -> None:
        with self.assertRaises(ForegroundExecutionError):
            ExecutionBudget(allow_network=True)
        with self.assertRaises(ForegroundExecutionError):
            ExecutionBudget(max_delegated_children=1)

    def test_artifacts_and_ledger_are_durable_references(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT / ".tmp", prefix="p2p-c12-durable-") as raw:
            root = Path(raw)
            controller = self.make_controller(root, task_specs=[self.mutation_task()])
            result = controller.execute(
                lambda runtime: runtime.write_text("output.txt", "durable"),
                lambda runtime: {"status": "VERIFIED", "evidence_claims": [claim()]},
                owner_gate={"status": "APPROVED", "source_ref": "owner/test-durable"},
                permission_state=self.write_permission(),
                budget=ExecutionBudget(allow_mutation=True),
            )
            self.assertEqual(result["status"], "DONE")
            execution_root = root / ".p2p" / "state" / "foreground-executions" / result["execution_id"]
            self.assertTrue((execution_root / "intent.json").is_file())
            self.assertTrue(list((execution_root / "checkpoints").glob("*.json")))
            self.assertTrue(list((execution_root / "receipts").glob("*.json")))
            events = controller.store.read_events()
            self.assertEqual(events["status"], "PASS")
            serialized = json.dumps(result)
            self.assertNotIn("agent", serialized.lower())
            self.assertNotIn("provider", serialized.lower())
            self.assertNotIn("thread", serialized.lower())

    def test_cli_run_is_thin_and_beginner_readable(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT / ".tmp", prefix="p2p-c12-cli-test-") as raw:
            root = Path(raw)
            (root / "goal.json").write_text(json.dumps({"goal_id": "goal-cli-test", "scope": ["output.txt"], "out_of_scope": ["scheduler"]}), encoding="utf-8")
            (root / "tasks.json").write_text(json.dumps([task(permission_needs=["WRITE"])]), encoding="utf-8")
            (root / "permissions.json").write_text(json.dumps(self.write_permission()), encoding="utf-8")
            init = subprocess.run(
                [sys.executable, str(REPO_ROOT / "scripts" / "p2p_task_state.py"), "--root", str(root), "init", "--goal-contract", "goal.json", "--tasks", "tasks.json"],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(init.returncode, 0, init.stdout + init.stderr)
            run = subprocess.run(
                [
                    sys.executable,
                    str(REPO_ROOT / "scripts" / "p2p_foreground_execution.py"),
                    "--root",
                    str(root),
                    "run",
                    "--action",
                    "write-text",
                    "--path",
                    "output.txt",
                    "--text",
                    "hello from cli",
                    "--allow-mutation",
                    "--owner-source",
                    "owner/cli-test",
                    "--permissions",
                    str(root / "permissions.json"),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            payload = json.loads(run.stdout)
            self.assertEqual(payload["status"], "DONE")
            self.assertFalse(payload["automatic_start"])
            self.assertFalse(payload["background_execution"])

    def test_package_and_doctor_contract_include_controller_paths(self) -> None:
        package_path = REPO_ROOT / "scripts" / "package_release.py"
        spec = importlib.util.spec_from_file_location("p2p_c12_package_release", package_path)
        self.assertIsNotNone(spec)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertIn("scripts/p2p_foreground_execution.py", module.selected_paths(REPO_ROOT))
        self.assertIn("foreground_execution.py", module.FOUNDATION_RUNTIME_MODULES)
        self.assertTrue((module.validate_foundation_runtime(REPO_ROOT) / "p2p_capabilities" / "foreground_execution.py").is_file())

        doctor_source = (REPO_ROOT / "scripts" / "doctor.py").read_text(encoding="utf-8")
        self.assertIn("p2p_capabilities/foreground_execution.py", doctor_source)

    def test_structural_boundary_has_no_scheduler_worker_or_external_executor_surface(self) -> None:
        source_path = SYSTEM_ROOT / "p2p_capabilities" / "foreground_execution.py"
        tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
        forbidden_imports = {"asyncio", "multiprocessing", "socket", "subprocess", "threading", "requests", "httpx"}
        forbidden_names = {"scheduler", "queue", "worker", "spawn", "delegate", "delegation", "process", "thread"}
        imported: set[str] = set()
        defined: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".", 1)[0])
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                defined.add(node.name.lower())
            self.assertFalse(isinstance(node, ast.AsyncFunctionDef), "foreground control must stay synchronous")
        self.assertTrue(imported.isdisjoint(forbidden_imports))
        self.assertTrue(defined.isdisjoint(forbidden_names))
        self.assertFalse((SYSTEM_ROOT / "p2p_capabilities" / "foreground_execution.py").read_text(encoding="utf-8").count("TaskStateStore(") > 1)

        registry = json.loads((SYSTEM_ROOT / "p2p_capabilities" / "capabilities.json").read_text(encoding="utf-8"))
        canonical = [item["CAPABILITY_ID"] for item in registry["capabilities"] if item.get("CANONICAL_QUORUM_MEMBER")]
        self.assertEqual(canonical, ["p2p_iris", "p2p_tecton", "p2p_axiom", "p2p_vector", "p2p_datos", "p2p_anon", "p2p_architecton", "p2p_helios"])
        self.assertEqual(registry.get("canonical_denominator", 8), 8)


if __name__ == "__main__":
    unittest.main()
