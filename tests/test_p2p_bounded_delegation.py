from __future__ import annotations

import json
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = REPO_ROOT / ".p2p" / "system"
if str(SYSTEM_ROOT) not in sys.path:
    sys.path.insert(0, str(SYSTEM_ROOT))

from p2p_capabilities.bounded_delegation import (  # noqa: E402
    BLOCKED,
    DELEGATE,
    DIRECT,
    UNKNOWN_IDENTITY,
    BoundedDelegationController,
    CodexHostAdapter,
    DelegationBudget,
    DelegationRequest,
    PermissionEnvelope,
    scope_is_subset,
)
from scripts.p2p_host_identity_hook import append_receipt  # noqa: E402
from p2p_capabilities.decision_trace import read_trace_records  # noqa: E402
from p2p_capabilities.evidence import EvidenceClaim  # noqa: E402
from p2p_capabilities.task_state import TaskPlan, TaskStateStore  # noqa: E402


NOW = "2026-08-15T16:00:00+00:00"


def goal(goal_id: str = "goal-c15-test") -> dict[str, object]:
    return {
        "goal_id": goal_id,
        "scope": ["src/*.py", "output.txt"],
        "out_of_scope": ["scheduler", ".p2p/state", "release"],
        "completion_criteria": [{"criterion_id": "criterion-c15", "description": "delegated result is independently verified"}],
    }


def task(task_id: str = "one", **extra: object) -> dict[str, object]:
    return {
        "task_id": task_id,
        "title": f"C15 {task_id}",
        "purpose": "Perform one bounded task and return a proposal for parent verification.",
        "scope": ["src/*.py", "output.txt"],
        "non_scope": ["scheduler", ".p2p/state", "release"],
        "acceptance_requirements": [f"acceptance-{task_id}"],
        "required_evidence": [f"evidence-{task_id}"],
        **extra,
    }


def evidence(task_id: str = "one") -> EvidenceClaim:
    reference = f"evidence-{task_id}"
    return EvidenceClaim(
        claim="The parent independently confirmed the current candidate state.",
        required_evidence=(reference,),
        actual_evidence=(
            {
                "source": "tests/test_p2p_bounded_delegation.py",
                "evidence_ref": reference,
                "origin": "RUNTIME_EVIDENCE",
                "observed_at": NOW,
                "freshness": "CURRENT",
                "scope": ["src/main.py"],
                "source_binding": "c15-test",
                "fingerprint": "a" * 64,
            },
        ),
        status="VERIFIED",
    )


class BoundedDelegationTests(unittest.TestCase):
    def make_controller(self, root: Path, *, task_specs: list[dict[str, object]] | None = None) -> BoundedDelegationController:
        plan = TaskPlan.from_goal(goal(), task_specs or [task()], now=NOW)
        TaskStateStore(root).initialize(plan, at=NOW)
        return BoundedDelegationController(root)

    @staticmethod
    def candidate() -> dict[str, str]:
        return {"candidate": "current", "source": "disposable-c15-fixture"}

    def request(self, controller: BoundedDelegationController, *, host: bool = True, **overrides: object) -> DelegationRequest:
        values: dict[str, object] = {
            "task_size": "MODERATE",
            "value_reasons": ("CONTEXT_ISOLATION",),
            "candidate_state": self.candidate(),
            "host_child_available": host,
            "parent_permissions": PermissionEnvelope(grants=("READ", "WRITE"), scope=("src/*.py", "output.txt")),
            "child_permissions": PermissionEnvelope(grants=("READ",), scope=("src/main.py",)),
        }
        values.update(overrides)
        return controller.request(**values)

    def test_direct_is_first_class_when_no_material_value_exists(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT / ".tmp", prefix="p2p-c15-direct-") as raw:
            controller = self.make_controller(Path(raw))
            decision = controller.decide(task_id="one")
            self.assertEqual(decision["strategy"], DIRECT)
            self.assertEqual(decision["decision"], DIRECT)
            self.assertEqual(decision["model_profile_resolution"], "NOT_REQUESTED")
            self.assertEqual(decision["execution_selection_order"][:2], ["TASK", "DELEGATION_STRATEGY"])

    def test_material_value_delegates_only_after_host_surface_is_declared(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT / ".tmp", prefix="p2p-c15-value-") as raw:
            controller = self.make_controller(Path(raw))
            blocked = controller.decide(self.request(controller, host=False))
            self.assertEqual(blocked["strategy"], BLOCKED)
            self.assertEqual(blocked["reason"], "DELEGATED_EXECUTION_UNAVAILABLE")
            delegated = controller.decide(self.request(controller, host=True))
            self.assertEqual(delegated["strategy"], DELEGATE)
            self.assertEqual(delegated["model_profile_resolution"], "NOT_REQUESTED")

    def test_material_strategy_reason_is_recorded_in_existing_decision_trace(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT / ".tmp", prefix="p2p-c15-trace-") as raw:
            root = Path(raw)
            controller = self.make_controller(root)
            decision = controller.decide(self.request(controller))
            self.assertTrue(decision["decision_trace_ref"].startswith("D-C15-"))
            records = read_trace_records(root)
            self.assertEqual(records["status"], "PASS")
            self.assertEqual(len(records["records"]), 1)
            trace = records["records"][0]["trace"]
            self.assertEqual(trace["DECISION_TYPE"], "GOVERNANCE")
            self.assertIn("DELEGATE", trace["OUTCOME"])

    def test_decision_precedes_execution_class_resolution(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT / ".tmp", prefix="p2p-c15-order-") as raw:
            controller = self.make_controller(Path(raw))
            decision = controller.decide(self.request(controller, requested_execution_class="HOST_DEFAULT"))
            self.assertEqual(decision["strategy"], DELEGATE)
            self.assertNotIn("model_id", json.dumps(decision).lower())
            self.assertNotIn("provider", json.dumps(decision).lower())
            self.assertIn("EXECUTION_CLASS_IF_NEEDED", decision["execution_selection_order"])

    def test_child_permission_and_scope_must_be_subsets(self) -> None:
        self.assertTrue(scope_is_subset(("src/main.py",), ("src/*.py",)))
        self.assertFalse(scope_is_subset(("tests/main.py",), ("src/*.py",)))
        with tempfile.TemporaryDirectory(dir=REPO_ROOT / ".tmp", prefix="p2p-c15-subset-") as raw:
            controller = self.make_controller(Path(raw))
            request = self.request(
                controller,
                child_permissions=PermissionEnvelope(grants=("NETWORK",), scope=("src/main.py",)),
            )
            decision = controller.decide(request)
            self.assertEqual(decision["strategy"], BLOCKED)
            self.assertIn("CHILD_PERMISSION", decision["reason"])

    def test_identity_unknown_is_allowed_when_not_acceptance_material(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT / ".tmp", prefix="p2p-c15-unknown-") as raw:
            controller = self.make_controller(Path(raw))
            decision = controller.decide(self.request(controller, observed_identity=UNKNOWN_IDENTITY))
            self.assertEqual(decision["strategy"], DELEGATE)
            self.assertEqual(decision["rationale"]["observed_identity"], UNKNOWN_IDENTITY)

    def test_missing_candidate_state_blocks_before_delegation(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT / ".tmp", prefix="p2p-c15-unclear-boundary-") as raw:
            controller = self.make_controller(Path(raw))
            decision = controller.decide(self.request(controller, candidate_state=None))
            self.assertEqual(decision["strategy"], BLOCKED)
            self.assertEqual(decision["reason"], "CANDIDATE_STATE_UNKNOWN")

    def test_identity_required_blocks_without_host_proof(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT / ".tmp", prefix="p2p-c15-identity-") as raw:
            controller = self.make_controller(Path(raw))
            decision = controller.decide(self.request(controller, identity_required=True, required_identity="p2p_iris"))
            self.assertEqual(decision["strategy"], BLOCKED)
            self.assertEqual(decision["reason"], "IDENTITY_REQUIRED_BUT_UNVERIFIED")

    def test_handoff_fingerprint_changes_with_candidate_state(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT / ".tmp", prefix="p2p-c15-fingerprint-") as raw:
            controller = self.make_controller(Path(raw))
            first = self.request(controller, candidate_state={"candidate": "one"})
            second = self.request(controller, candidate_state={"candidate": "two"})
            self.assertNotEqual(first.candidate_fingerprint, second.candidate_fingerprint)
            first_handoff = controller.execute(first, child_executor=lambda handoff: {"outcome": "FAILED", "candidate_fingerprint": handoff["candidate_fingerprint"], "summary": "stop"})
            self.assertIn("handoff", first_handoff)
            self.assertNotEqual(first_handoff["handoff"]["fingerprint"], second.candidate_fingerprint)

    def test_handoff_fingerprint_is_stable_when_only_handoff_id_changes(self) -> None:
        def capture(root: Path) -> str:
            controller = self.make_controller(root)
            request = self.request(controller, candidate_state={"candidate": "same"})
            seen: dict[str, str] = {}

            def child_executor(handoff: dict[str, object]) -> dict[str, object]:
                seen["fingerprint"] = str(handoff["fingerprint"])
                return {
                    "outcome": "FAILED",
                    "candidate_fingerprint": handoff["candidate_fingerprint"],
                    "summary": "disposable stop",
                }

            controller.execute(request, child_executor=child_executor)
            return seen["fingerprint"]

        with tempfile.TemporaryDirectory(dir=REPO_ROOT / ".tmp", prefix="p2p-c15-fingerprint-a-") as first_raw:
            with tempfile.TemporaryDirectory(dir=REPO_ROOT / ".tmp", prefix="p2p-c15-fingerprint-b-") as second_raw:
                self.assertEqual(capture(Path(first_raw)), capture(Path(second_raw)))

    def test_mutating_child_requires_task_need_and_owner_gate(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT / ".tmp", prefix="p2p-c15-owner-gate-") as raw:
            controller = self.make_controller(Path(raw), task_specs=[task(permission_needs=["WRITE"])])
            request = self.request(
                controller,
                task_id="one",
                child_permissions=PermissionEnvelope(grants=("WRITE",), scope=("src/main.py",)),
                permission_state={"WRITE": {"status": "GRANTED", "source_ref": "c15-test"}},
                owner_gate=None,
            )
            decision = controller.decide(request)
            self.assertEqual(decision["strategy"], BLOCKED)
            self.assertEqual(decision["reason"], "OWNER_GATE_UNRESOLVED")

    def test_delegated_result_requires_parent_verification_before_done(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT / ".tmp", prefix="p2p-c15-verify-") as raw:
            root = Path(raw)
            controller = self.make_controller(root)

            def child(handoff: dict[str, object]) -> dict[str, object]:
                return {
                    "handoff_id": handoff["handoff_id"],
                    "task_id": handoff["task_id"],
                    "outcome": "SUCCEEDED",
                    "candidate_fingerprint": handoff["candidate_fingerprint"],
                    "observed_identity": UNKNOWN_IDENTITY,
                    "identity_authority": "UNKNOWN",
                    "mutation_state": "KNOWN_NONE",
                }

            result = controller.execute(self.request(controller), child_executor=child)
            self.assertEqual(result["status"], "NEEDS_RECHECK")
            self.assertEqual(TaskStateStore(root).require().tasks["one"].status, "ACTIVE")

    def test_parent_verification_can_complete_existing_c11_task(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT / ".tmp", prefix="p2p-c15-done-") as raw:
            root = Path(raw)
            controller = self.make_controller(root)

            def child(handoff: dict[str, object]) -> dict[str, object]:
                return {
                    "handoff_id": handoff["handoff_id"],
                    "task_id": handoff["task_id"],
                    "outcome": "SUCCEEDED",
                    "candidate_fingerprint": handoff["candidate_fingerprint"],
                    "observed_identity": UNKNOWN_IDENTITY,
                    "identity_authority": "UNKNOWN",
                    "mutation_state": "KNOWN_NONE",
                    "work_performed": ["read-only review"],
                }

            def verify(result: dict[str, object], handoff: dict[str, object]) -> dict[str, object]:
                self.assertTrue(result["proposal_only"])
                return {
                    "status": "VERIFIED",
                    "summary": "parent current-state verification",
                    "evidence_claims": [evidence()],
                    "candidate_state": {"candidate_fingerprint": handoff["candidate_fingerprint"], "verified": True},
                }

            completed = controller.execute(self.request(controller), child_executor=child, verify=verify)
            self.assertEqual(completed["status"], "DONE")
            self.assertEqual(completed["strategy"], DELEGATE)
            self.assertEqual(TaskStateStore(root).require().tasks["one"].status, "DONE")
            self.assertTrue((root / completed["handoff_ref"]).is_file())
            serialized = json.dumps(completed)
            self.assertNotIn("api_key", serialized.lower())
            self.assertNotIn("worker_id", serialized.lower())
            self.assertFalse(completed["output_is_evidence"])

    def test_failed_verification_prevents_done(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT / ".tmp", prefix="p2p-c15-failed-verify-") as raw:
            root = Path(raw)
            controller = self.make_controller(root)
            result = controller.execute(
                self.request(controller),
                child_executor=lambda handoff: {"outcome": "SUCCEEDED", "candidate_fingerprint": handoff["candidate_fingerprint"]},
                verify=lambda result, handoff: {"status": "FAILED", "summary": "current evidence contradicted"},
            )
            self.assertEqual(result["status"], "VERIFICATION_FAILED")
            self.assertEqual(TaskStateStore(root).require().tasks["one"].status, "ACTIVE")

    def test_unknown_partial_mutation_stops_without_direct_fallback(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT / ".tmp", prefix="p2p-c15-unknown-mutation-") as raw:
            root = Path(raw)
            controller = self.make_controller(root)
            direct_calls: list[str] = []
            result = controller.execute(
                self.request(controller, allow_direct_fallback=True),
                child_executor=lambda handoff: {"outcome": "FAILED", "candidate_fingerprint": handoff["candidate_fingerprint"], "mutation_state": "UNKNOWN", "mutation_performed": True},
                direct_action=lambda runtime: direct_calls.append("direct"),
                direct_verify=lambda runtime, action: {"status": "VERIFIED", "evidence_claims": [evidence()]},
            )
            self.assertEqual(result["status"], "UNKNOWN")
            self.assertEqual(direct_calls, [])
            self.assertEqual(TaskStateStore(root).require().tasks["one"].status, "ACTIVE")

    def test_transient_failure_retries_only_within_budget(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT / ".tmp", prefix="p2p-c15-retry-") as raw:
            root = Path(raw)
            controller = self.make_controller(root)
            attempts: list[int] = []

            def child(handoff: dict[str, object]) -> dict[str, object]:
                attempts.append(len(attempts) + 1)
                if len(attempts) == 1:
                    return {"outcome": "FAILED", "candidate_fingerprint": handoff["candidate_fingerprint"], "retryable": True, "summary": "transient child tool failure"}
                return {"outcome": "SUCCEEDED", "candidate_fingerprint": handoff["candidate_fingerprint"]}

            result = controller.execute(
                self.request(controller, budget=DelegationBudget(max_attempts=2, max_retries=1)),
                child_executor=child,
                verify=lambda result, handoff: {"status": "VERIFIED", "evidence_claims": [evidence()], "candidate_state": {"candidate_fingerprint": handoff["candidate_fingerprint"]}},
            )
            self.assertEqual(result["status"], "DONE")
            self.assertEqual(attempts, [1, 2])

    def test_boundary_failure_is_not_retried(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT / ".tmp", prefix="p2p-c15-boundary-") as raw:
            controller = self.make_controller(Path(raw))
            calls: list[int] = []

            def child(handoff: dict[str, object]) -> dict[str, object]:
                calls.append(1)
                return {"outcome": "FAILED", "candidate_fingerprint": handoff["candidate_fingerprint"], "retryable": True, "summary": "PERMISSION_DENIED"}

            result = controller.execute(
                self.request(controller, budget=DelegationBudget(max_attempts=3, max_retries=2)),
                child_executor=child,
            )
            self.assertEqual(result["status"], "FAILED")
            self.assertEqual(calls, [1])

    def test_safe_direct_fallback_requires_known_no_mutation(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT / ".tmp", prefix="p2p-c15-fallback-") as raw:
            root = Path(raw)
            controller = self.make_controller(root)
            direct_calls: list[str] = []

            def direct(runtime: object) -> dict[str, object]:
                direct_calls.append("direct")
                return {"status": "SUCCEEDED"}

            result = controller.execute(
                self.request(controller, allow_direct_fallback=True),
                child_executor=lambda handoff: {"outcome": "FAILED", "candidate_fingerprint": handoff["candidate_fingerprint"], "summary": "bounded child unavailable after start"},
                direct_action=direct,
                direct_verify=lambda runtime, action: {"status": "VERIFIED", "evidence_claims": [evidence()]},
            )
            self.assertEqual(result["strategy"], DIRECT, result)
            self.assertEqual(result["status"], "DONE")
            self.assertEqual(direct_calls, ["direct"])

    def test_stale_candidate_result_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT / ".tmp", prefix="p2p-c15-stale-") as raw:
            root = Path(raw)
            controller = self.make_controller(root)
            result = controller.execute(
                self.request(controller),
                child_executor=lambda handoff: {"outcome": "SUCCEEDED", "candidate_fingerprint": "b" * 64},
                verify=lambda result, handoff: {"status": "VERIFIED", "evidence_claims": [evidence()], "candidate_state": {"candidate_fingerprint": handoff["candidate_fingerprint"]}},
            )
            self.assertEqual(result["status"], "STALE_HANDOFF")
            self.assertEqual(TaskStateStore(root).require().tasks["one"].status, "ACTIVE")

    def test_child_cannot_delegate_again(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT / ".tmp", prefix="p2p-c15-grandchild-") as raw:
            controller = self.make_controller(Path(raw))
            result = controller.execute(
                self.request(controller),
                child_executor=lambda handoff: {"outcome": "SUCCEEDED", "candidate_fingerprint": handoff["candidate_fingerprint"], "child_delegation_allowed": True},
            )
            self.assertEqual(result["status"], "CONTROL_PLANE_ERROR")
            self.assertEqual(result["reason"], "CHILD_DELEGATION_FORBIDDEN")

    def test_control_plane_corruption_stops_before_child(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT / ".tmp", prefix="p2p-c15-control-") as raw:
            root = Path(raw)
            controller = self.make_controller(root)
            request = self.request(controller)
            ledger = root / ".p2p" / "state" / "execution-ledger.jsonl"
            ledger.write_text(ledger.read_text(encoding="utf-8") + "{invalid\n", encoding="utf-8")
            calls: list[str] = []
            result = controller.execute(request, child_executor=lambda handoff: calls.append("child"))
            self.assertEqual(result["status"], "CONTROL_PLANE_ERROR")
            self.assertEqual(calls, [])

    def test_handoff_is_minimal_and_structurally_bounded(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT / ".tmp", prefix="p2p-c15-contract-") as raw:
            controller = self.make_controller(Path(raw))
            result = controller.execute(
                self.request(controller),
                child_executor=lambda handoff: {"outcome": "FAILED", "candidate_fingerprint": handoff["candidate_fingerprint"]},
            )
            handoff = result["handoff"]
            self.assertEqual(handoff["max_depth"], 1)
            self.assertEqual(handoff["child_count"], 1)
            self.assertFalse(handoff["child_delegation_allowed"])
            self.assertNotIn("candidate", handoff)
            self.assertNotIn("transcript", handoff)
            self.assertNotIn("api_key", json.dumps(handoff).lower())
            self.assertIn("verification_expectations", handoff)

    def test_cli_decision_is_thin_and_beginner_readable(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT / ".tmp", prefix="p2p-c15-cli-") as raw:
            root = Path(raw)
            (root / "goal.json").write_text(json.dumps(goal("goal-cli-c15")), encoding="utf-8")
            (root / "tasks.json").write_text(json.dumps([task()]), encoding="utf-8")
            init = __import__("subprocess").run(
                [sys.executable, str(REPO_ROOT / "scripts" / "p2p_task_state.py"), "--root", str(root), "init", "--goal-contract", "goal.json", "--tasks", "tasks.json"],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(init.returncode, 0, init.stdout + init.stderr)
            decision = __import__("subprocess").run(
                [sys.executable, str(REPO_ROOT / "scripts" / "p2p_delegation.py"), "--root", str(root), "decide", "--task-id", "one"],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(decision.returncode, 0, decision.stdout + decision.stderr)
            payload = json.loads(decision.stdout)
            self.assertEqual(payload["strategy"], DIRECT)
            self.assertEqual(payload["model_profile_resolution"], "NOT_REQUESTED")

    def test_package_and_doctor_inventory_include_c15_surfaces(self) -> None:
        package_path = REPO_ROOT / "scripts" / "package_release.py"
        package_spec = importlib.util.spec_from_file_location("c15_package_release", package_path)
        self.assertIsNotNone(package_spec)
        assert package_spec is not None and package_spec.loader is not None
        package = importlib.util.module_from_spec(package_spec)
        package_spec.loader.exec_module(package)
        self.assertIn("scripts/p2p_delegation.py", package.selected_paths(REPO_ROOT))
        self.assertIn("bounded_delegation.py", package.FOUNDATION_RUNTIME_MODULES)

        doctor_path = REPO_ROOT / "scripts" / "doctor.py"
        doctor_spec = importlib.util.spec_from_file_location("c15_doctor", doctor_path)
        self.assertIsNotNone(doctor_spec)
        assert doctor_spec is not None and doctor_spec.loader is not None
        doctor = importlib.util.module_from_spec(doctor_spec)
        doctor_spec.loader.exec_module(doctor)
        required = doctor._foundation_required_paths(REPO_ROOT / ".p2p" / "system")
        self.assertIn("p2p_capabilities/bounded_delegation.py", required)

    def test_host_adapter_requires_fresh_official_receipt_and_preserves_provenance(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT / ".tmp", prefix="p2p-c15-host-adapter-") as raw:
            root = Path(raw)
            controller = self.make_controller(root)
            request = self.request(controller)

            def host_executor(package: dict[str, object], context: dict[str, object]) -> dict[str, object]:
                handoff = package["handoff"]
                assert isinstance(handoff, dict)
                append_receipt(
                    {
                        "schema": "p2p-host-subagent-identity/1",
                        "event": "SubagentStart",
                        "timestamp": NOW,
                        "session_id": "session-c15-test",
                        "turn_id": "turn-c15-test",
                        "agent_id": "agent-c15-test",
                        "agent_type": "default",
                        "permission_mode": "READ_ONLY",
                        "model": "host-test",
                        "cwd": str(root),
                        "source": "codex_official_hook",
                    },
                    root / ".p2p" / "state" / "execution-ledger.jsonl",
                )
                return {
                    "execution_source": "codex_official_host",
                    "execution_completed": True,
                    "host_execution_id": "agent-c15-test",
                    "session_id": "session-c15-test",
                    "turn_id": "turn-c15-test",
                    "child_count": 0,
                    "delegation_depth": 0,
                    "output": "read-only host proposal",
                    "worker_result": {
                        "outcome": "SUCCEEDED",
                        "candidate_fingerprint": handoff["candidate_fingerprint"],
                        "mutation_state": "KNOWN_NONE",
                        "work_performed": ["read-only host inspection"],
                    },
                }

            adapter = CodexHostAdapter(root, host_executor)
            result = controller.execute(
                request,
                child_executor=adapter,
                verify=lambda child, handoff: {
                    "status": "VERIFIED",
                    "evidence_claims": [evidence()],
                    "candidate_state": {"candidate_fingerprint": handoff["candidate_fingerprint"]},
                },
            )
            self.assertEqual(result["status"], "DONE", result)
            self.assertEqual(result["decision"]["plan_hash"], result["handoff"]["plan_hash"])
            child = result["child_result"]
            self.assertFalse(child["output_is_evidence"])
            self.assertTrue(child["proposal_only"])
            self.assertEqual(child["RAW_HOST_RECEIPT"]["agent_id"], "agent-c15-test")
            self.assertEqual(child["NORMALIZED_C15_RECEIPT"]["handoff_id"], result["handoff"]["handoff_id"])
            self.assertEqual(child["NORMALIZED_C15_RECEIPT"]["plan_hash"], result["handoff"]["plan_hash"])

    def test_host_adapter_fails_closed_without_fresh_receipt(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT / ".tmp", prefix="p2p-c15-host-missing-receipt-") as raw:
            root = Path(raw)
            controller = self.make_controller(root)
            request = self.request(controller)
            calls: list[str] = []

            def host_executor(package: dict[str, object], context: dict[str, object]) -> dict[str, object]:
                calls.append("invoked")
                handoff = package["handoff"]
                assert isinstance(handoff, dict)
                return {
                    "execution_source": "codex_official_host",
                    "execution_completed": True,
                    "host_execution_id": "agent-without-receipt",
                    "child_count": 0,
                    "delegation_depth": 0,
                    "worker_result": {"outcome": "SUCCEEDED", "candidate_fingerprint": handoff["candidate_fingerprint"]},
                }

            result = controller.execute(request, child_executor=CodexHostAdapter(root, host_executor))
            self.assertEqual(result["status"], "CONTROL_PLANE_ERROR")
            self.assertIn("HOST_RECEIPT_MISSING_OR_UNBOUND", result["reason"])
            self.assertEqual(calls, ["invoked"])
            self.assertNotEqual(TaskStateStore(root).require().tasks["one"].status, "DONE")


if __name__ == "__main__":
    unittest.main()
