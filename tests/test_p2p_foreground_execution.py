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
    ForegroundExecutionController,
    ForegroundExecutionError,
    ForegroundScopeError,
)
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
    def make_controller(self, root: Path, *, task_specs: list[dict[str, object]] | None = None, goal_id: str = "goal-foreground-test") -> ForegroundExecutionController:
        plan = TaskPlan.from_goal(goal(goal_id), task_specs or [task()], now=NOW)
        TaskStateStore(root).initialize(plan, at=NOW)
        return ForegroundExecutionController(root)

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
            controller = self.make_controller(root)

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
                budget=ExecutionBudget(allow_mutation=True),
            )
            self.assertEqual(result["status"], "DONE")
            self.assertEqual(TaskStateStore(root).require().tasks["one"].status, "DONE")
            self.assertTrue(result["intent_ref"].endswith("/intent.json"))
            self.assertGreaterEqual(len(result["receipt_refs"]), 4)
            self.assertNotIn("bounded result", json.dumps(result))
            self.assertFalse(result["output_is_evidence"])

    def test_action_output_alone_cannot_complete(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT / ".tmp", prefix="p2p-c12-no-output-proof-") as raw:
            root = Path(raw)
            controller = self.make_controller(root)

            result = controller.execute(
                lambda runtime: runtime.write_text("output.txt", "changed"),
                lambda runtime: {"status": "VERIFIED", "summary": "the action said done"},
                owner_gate={"status": "APPROVED", "source_ref": "owner/test-output"},
                budget=ExecutionBudget(allow_mutation=True),
            )
            self.assertEqual(result["status"], "VERIFICATION_FAILED")
            self.assertEqual(TaskStateStore(root).require().tasks["one"].status, "ACTIVE")

    def test_scope_and_protected_state_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT / ".tmp", prefix="p2p-c12-scope-") as raw:
            root = Path(raw)
            controller = self.make_controller(root)

            def escape(runtime):
                runtime.write_text("../escape.txt", "no")

            result = controller.execute(
                escape,
                lambda runtime: {"status": "VERIFIED", "evidence_claims": [claim()]},
                owner_gate={"status": "APPROVED", "source_ref": "owner/test-scope"},
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
            controller = self.make_controller(root)
            count_limited = controller.execute(
                lambda runtime: runtime.write_text("output.txt", "too many actions"),
                lambda runtime: {"status": "VERIFIED", "evidence_claims": [claim()]},
                owner_gate={"status": "APPROVED", "source_ref": "owner/test-budget"},
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
            controller = self.make_controller(root)
            action_calls: list[str] = []

            def action(runtime):
                action_calls.append("run")
                runtime.write_text("output.txt", "interrupted result")
                runtime.interrupt()

            interrupted = controller.execute(
                action,
                None,
                owner_gate={"status": "APPROVED", "source_ref": "owner/test-resume"},
                budget=ExecutionBudget(allow_mutation=True),
            )
            self.assertEqual(interrupted["status"], "INTERRUPTED")
            self.assertEqual(TaskStateStore(root).require().tasks["one"].status, "ACTIVE")

            def verify(runtime):
                self.assertEqual(runtime.read_text("output.txt"), "interrupted result")
                return {"status": "VERIFIED", "evidence_claims": [claim()]}

            resumed = ForegroundExecutionController(root).resume(verify)
            self.assertEqual(resumed["status"], "DONE")
            self.assertEqual(action_calls, ["run"])
            self.assertEqual(TaskStateStore(root).require().tasks["one"].status, "DONE")
            self.assertEqual(resumed["resume"]["resume_classification"], "NEEDS_RECHECK")

    def test_resume_never_auto_starts_without_a_read_only_verifier(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT / ".tmp", prefix="p2p-c12-resume-gate-") as raw:
            root = Path(raw)
            controller = self.make_controller(root)
            controller.execute(
                lambda runtime: (runtime.write_text("output.txt", "pending"), runtime.interrupt())[1],
                None,
                owner_gate={"status": "APPROVED", "source_ref": "owner/test-resume-gate"},
                budget=ExecutionBudget(allow_mutation=True),
            )
            resumed = ForegroundExecutionController(root).resume()
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
            controller = self.make_controller(root)
            result = controller.execute(
                lambda runtime: runtime.write_text("output.txt", "durable"),
                lambda runtime: {"status": "VERIFIED", "evidence_claims": [claim()]},
                owner_gate={"status": "APPROVED", "source_ref": "owner/test-durable"},
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
            (root / "tasks.json").write_text(json.dumps([task()]), encoding="utf-8")
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
