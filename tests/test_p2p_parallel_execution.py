from __future__ import annotations

import json
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = REPO_ROOT / ".p2p" / "system"
if str(SYSTEM_ROOT) not in sys.path:
    sys.path.insert(0, str(SYSTEM_ROOT))

from p2p_capabilities.bounded_delegation import DelegationRequest, PermissionEnvelope  # noqa: E402
from p2p_capabilities.evidence import EvidenceClaim  # noqa: E402
from p2p_capabilities.parallel_execution import (  # noqa: E402
    MAX_PARALLEL_CHILDREN,
    PARALLEL,
    PARALLEL_BLOCKED,
    SEQUENTIAL,
    BoundedParallelForegroundController,
    ParallelTaskContract,
)
from p2p_capabilities.task_state import TaskPlan, TaskStateStore  # noqa: E402


NOW = "2026-08-16T04:00:00+00:00"


def goal() -> dict[str, object]:
    return {
        "goal_id": "goal-c17-test",
        "scope": ["src/a.py", "src/b.py", "src/c.py", "out/a.txt", "out/b.txt", "out/c.txt"],
        "out_of_scope": ["scheduler", ".p2p/state", "release", "remote"],
        "completion_criteria": [{"criterion_id": "criterion-c17", "description": "bounded pair is independently verified"}],
    }


def task(task_id: str, scope: str, **extra: object) -> dict[str, object]:
    return {
        "task_id": task_id,
        "title": f"C17 {task_id}",
        "purpose": "Perform one independent bounded foreground task and return a proposal.",
        "scope": [scope],
        "non_scope": ["scheduler", ".p2p/state", "release", "remote"],
        "acceptance_requirements": [f"acceptance-{task_id}"],
        "required_evidence": [f"evidence-{task_id}"],
        **extra,
    }


def claim(task_id: str) -> EvidenceClaim:
    return EvidenceClaim(
        claim=f"Parent verified {task_id} current state.",
        required_evidence=(f"evidence-{task_id}",),
        actual_evidence=(
            {
                "source": "tests/test_p2p_parallel_execution.py",
                "evidence_ref": f"evidence-{task_id}",
                "origin": "RUNTIME_EVIDENCE",
                "observed_at": NOW,
                "freshness": "CURRENT",
                "scope": [f"src/{task_id}.py"],
                "source_binding": "c17-test",
                "fingerprint": "c" * 64,
            },
        ),
        status="VERIFIED",
    )


class ParallelExecutionTests(unittest.TestCase):
    def make_root(self, specs: list[dict[str, object]]) -> Path:
        raw = tempfile.mkdtemp(prefix="p2p-c17-parallel-", dir=REPO_ROOT / ".tmp")
        root = Path(raw)
        TaskStateStore(root).initialize(TaskPlan.from_goal(goal(), specs, now=NOW), at=NOW)
        return root

    def request(self, root: Path, task_id: str, *, value: bool = True, host: bool = True, mutation: bool = False, **extra: object) -> DelegationRequest:
        task_record = TaskStateStore(root).require().tasks[task_id]
        grants = ("READ", "WRITE") if mutation else ("READ",)
        permissions = PermissionEnvelope(grants=grants, scope=task_record.scope)
        values: dict[str, object] = {
            "task_size": "MODERATE",
            "value_reasons": ("CONTEXT_ISOLATION",) if value else (),
            "parent_permissions": permissions,
            "child_permissions": permissions if mutation else PermissionEnvelope(grants=("READ",), scope=task_record.scope),
            "child_scope": task_record.scope,
            "read_scopes": () if mutation else task_record.scope,
            "write_scopes": task_record.scope if mutation else (),
            "candidate_state": {"candidate": "current"},
            "host_child_available": host,
        }
        if mutation:
            values["owner_gate"] = {"status": "APPROVED", "evidence_ref": "c17-test-owner-gate"}
            values["permission_state"] = {"WRITE": {"status": "GRANTED", "source_ref": "c17-test-owner-gate"}}
        values.update(extra)
        return DelegationRequest(task=task_record, **values)

    @staticmethod
    def child(handoff: dict[str, object]) -> dict[str, object]:
        return {
            "outcome": "SUCCEEDED",
            "candidate_fingerprint": handoff["candidate_fingerprint"],
            "mutation_state": "KNOWN_NONE",
            "work_performed": ["bounded read-only review"],
        }

    @staticmethod
    def verify(result: dict[str, object], handoff: dict[str, object]) -> dict[str, object]:
        return {
            "status": "VERIFIED",
            "evidence_claims": [claim(str(handoff["task_id"]))],
            "candidate_state": {"candidate_fingerprint": handoff["candidate_fingerprint"], "verified": True},
        }

    def test_independent_ready_pair_is_parallel_and_starts_no_more_than_two(self) -> None:
        root = self.make_root([task("a", "src/a.py"), task("b", "src/b.py")])
        controller = BoundedParallelForegroundController(root)
        requests = (self.request(root, "a"), self.request(root, "b"))
        decision = controller.decide(requests)
        self.assertEqual(decision["strategy"], PARALLEL)
        self.assertEqual(decision["task_ids"], ["a", "b"])
        active = 0
        peak = 0
        guard = threading.Lock()

        def child(handoff: dict[str, object]) -> dict[str, object]:
            nonlocal active, peak
            with guard:
                active += 1
                peak = max(peak, active)
            # Keep the overlap window generous enough for a deterministic
            # foreground-concurrency assertion on a busy Windows host.
            time.sleep(0.10)
            with guard:
                active -= 1
            return self.child(handoff)

        result = controller.execute(requests, child_executors=child, verifiers=self.verify, combined_verify=lambda children: {"status": "VERIFIED"})
        self.assertEqual(result["status"], "DONE", result)
        self.assertEqual(result["strategy"], PARALLEL)
        self.assertLessEqual(peak, MAX_PARALLEL_CHILDREN)
        self.assertEqual(peak, 2)
        self.assertFalse(result["worker_output_is_evidence"])
        group = root / ".p2p" / "state" / "foreground-executions" / "parallel-groups" / str(result["parallel_group_id"]) / "group.json"
        persisted = json.loads(group.read_text(encoding="utf-8"))
        self.assertEqual(set(persisted["task_ids"]), {"a", "b"})
        self.assertNotEqual(persisted["children"]["a"]["handoff_ref"], persisted["children"]["b"]["handoff_ref"])
        self.assertEqual(TaskStateStore(root).require().tasks["a"].status, "DONE")
        self.assertEqual(TaskStateStore(root).require().tasks["b"].status, "DONE")

    def test_dependency_relation_defaults_to_sequential(self) -> None:
        root = self.make_root([task("a", "src/a.py"), task("b", "src/b.py", dependencies=["a"])])
        result = BoundedParallelForegroundController(root).decide((self.request(root, "a"), self.request(root, "b")))
        self.assertEqual(result["strategy"], SEQUENTIAL)
        self.assertIn("DEPENDENCY_NOT_DONE", result["excluded_task_ids"]["b"])

    def test_scope_conflict_defaults_to_sequential(self) -> None:
        ready_write = {"status": "PASS"}
        root = self.make_root([task("a", "out/shared.txt", permission_needs=["WRITE"], status="READY", last_preflight=ready_write), task("b", "out/shared.txt", permission_needs=["WRITE"], status="READY", last_preflight=ready_write)])
        requests = (self.request(root, "a", mutation=True), self.request(root, "b", mutation=True))
        result = BoundedParallelForegroundController(root).decide(requests)
        self.assertEqual(result["strategy"], SEQUENTIAL)
        reasons = next(iter(result["pair_rejections"].values()))
        self.assertTrue(any("WRITE_SCOPE_CONFLICT" in item for item in reasons))

    def test_shared_manifest_resource_defaults_to_sequential(self) -> None:
        root = self.make_root([task("a", "src/a.py"), task("b", "src/b.py")])
        requests = (self.request(root, "a"), self.request(root, "b"))
        contracts = {
            "a": ParallelTaskContract(task_id="a", read_scopes=("src/a.py",), shared_resources=("manifest/package.json",)),
            "b": ParallelTaskContract(task_id="b", read_scopes=("src/b.py",), shared_resources=("manifest/package.json",)),
        }
        result = BoundedParallelForegroundController(root).decide(requests, task_contracts=contracts)
        self.assertEqual(result["strategy"], SEQUENTIAL)
        self.assertIn("SHARED_RESOURCE_CONFLICT", next(iter(result["pair_rejections"].values())))

    def test_waiting_owner_task_cannot_join_group(self) -> None:
        root = self.make_root([task("a", "src/a.py", status="WAITING_OWNER", owner_decision={"status": "PENDING", "question": "owner approval"}), task("b", "src/b.py")])
        result = BoundedParallelForegroundController(root).decide((self.request(root, "a"), self.request(root, "b")))
        self.assertEqual(result["strategy"], SEQUENTIAL)
        self.assertEqual(result["excluded_task_ids"]["a"], "TASK_NOT_READY:WAITING_OWNER")

    def test_identity_required_unknown_task_cannot_join_group(self) -> None:
        root = self.make_root([task("a", "src/a.py"), task("b", "src/b.py")])
        requests = (self.request(root, "a", identity_required=True, required_identity="p2p_iris"), self.request(root, "b"))
        result = BoundedParallelForegroundController(root).decide(requests)
        self.assertEqual(result["strategy"], SEQUENTIAL)
        self.assertIn("IDENTITY_REQUIRED_BUT_UNVERIFIED", result["excluded_task_ids"]["a"])

    def test_no_material_value_defaults_to_sequential(self) -> None:
        root = self.make_root([task("a", "src/a.py"), task("b", "src/b.py")])
        result = BoundedParallelForegroundController(root).decide((self.request(root, "a", value=False), self.request(root, "b", value=False)))
        self.assertEqual(result["strategy"], SEQUENTIAL)
        self.assertEqual(len(result["task_ids"]), 1)

    def test_combined_regression_failure_prevents_group_completion(self) -> None:
        root = self.make_root([task("a", "src/a.py"), task("b", "src/b.py")])
        requests = (self.request(root, "a"), self.request(root, "b"))
        result = BoundedParallelForegroundController(root).execute(
            requests,
            child_executors=self.child,
            verifiers=self.verify,
            combined_verify=lambda children: {"status": "FAILED", "summary": "combined regression"},
        )
        self.assertEqual(result["status"], "NEEDS_RECHECK")
        self.assertEqual(result["combined_verification"]["status"], "FAILED")

    def test_three_candidates_are_capped_at_two(self) -> None:
        root = self.make_root([task("a", "src/a.py"), task("b", "src/b.py"), task("c", "src/c.py")])
        result = BoundedParallelForegroundController(root).decide(tuple(self.request(root, item) for item in ("a", "b", "c")))
        self.assertEqual(result["strategy"], PARALLEL)
        self.assertEqual(len(result["task_ids"]), MAX_PARALLEL_CHILDREN)
        self.assertNotIn("c", result["task_ids"])

    def test_missing_combined_verifier_blocks_mutation_before_start(self) -> None:
        ready_write = {"status": "PASS"}
        root = self.make_root([task("a", "src/a.py", permission_needs=["WRITE"], status="READY", last_preflight=ready_write), task("b", "src/b.py", permission_needs=["WRITE"], status="READY", last_preflight=ready_write)])
        requests = (self.request(root, "a", mutation=True), self.request(root, "b", mutation=True))
        calls: list[str] = []
        result = BoundedParallelForegroundController(root).execute(requests, child_executors=lambda handoff: calls.append(str(handoff["task_id"])))
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["reason"], "COMBINED_VERIFIER_REQUIRED_FOR_MUTATION_GROUP")
        self.assertEqual(calls, [])

    def test_partial_success_is_preserved_without_rescue_child(self) -> None:
        root = self.make_root([task("a", "src/a.py"), task("b", "src/b.py")])
        calls: list[str] = []

        def child(handoff: dict[str, object]) -> dict[str, object]:
            calls.append(str(handoff["task_id"]))
            if handoff["task_id"] == "b":
                return {"outcome": "FAILED", "candidate_fingerprint": handoff["candidate_fingerprint"], "summary": "known no mutation failure"}
            return self.child(handoff)

        result = BoundedParallelForegroundController(root).execute(
            (self.request(root, "a"), self.request(root, "b")),
            child_executors=child,
            verifiers=self.verify,
            combined_verify=lambda children: {"status": "VERIFIED"},
        )
        self.assertEqual(result["status"], "PARTIAL", result)
        self.assertEqual(set(calls), {"a", "b"})
        self.assertEqual(result["children"]["a"]["status"], "DONE")
        self.assertNotEqual(result["children"]["b"]["status"], "DONE")
        self.assertEqual(len(calls), 2)

    def test_unknown_mutation_freezes_group_and_cancellation_is_truthful(self) -> None:
        root = self.make_root([task("a", "src/a.py"), task("b", "src/b.py")])
        cancelled: list[str] = []

        def child(handoff: dict[str, object]) -> dict[str, object]:
            if handoff["task_id"] == "a":
                return {"outcome": "INTERRUPTED", "candidate_fingerprint": handoff["candidate_fingerprint"], "mutation_state": "UNKNOWN", "mutation_performed": True}
            time.sleep(0.02)
            return self.child(handoff)

        result = BoundedParallelForegroundController(root).execute(
            (self.request(root, "a"), self.request(root, "b")),
            child_executors=child,
            verifiers=self.verify,
            combined_verify=lambda children: {"status": "VERIFIED"},
            cancellation_callbacks=lambda value: cancelled.append(str(value["task_id"])) or {"status": "REQUESTED"},
        )
        self.assertEqual(result["status"], "UNKNOWN")
        self.assertIn(result["cancellation"]["status"], {"REQUESTED", "NOT_NEEDED", "UNAVAILABLE"})
        self.assertLessEqual(len(cancelled), 1)
        self.assertEqual(len(result["task_ids"]), 2)

    def test_malformed_ledger_blocks_before_callbacks(self) -> None:
        root = self.make_root([task("a", "src/a.py"), task("b", "src/b.py")])
        ledger = root / ".p2p" / "state" / "execution-ledger.jsonl"
        ledger.write_text(ledger.read_text(encoding="utf-8") + "{invalid\n", encoding="utf-8")
        calls: list[str] = []
        result = BoundedParallelForegroundController(root).execute((self.request(root, "a"), self.request(root, "b")), child_executors=lambda handoff: calls.append(str(handoff["task_id"])))
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn("CONTROL_PLANE_TASK_LEDGER_PARTIAL", result["reason"])
        self.assertEqual(calls, [])

    def test_cli_surface_reports_no_simulated_child(self) -> None:
        root = self.make_root([task("a", "src/a.py"), task("b", "src/b.py")])
        request_file = root / "requests.json"
        request_file.write_text(json.dumps([{"task_id": "a", "value_reasons": ["CONTEXT_ISOLATION"], "candidate_state": {"candidate": "current"}}, {"task_id": "b", "value_reasons": ["CONTEXT_ISOLATION"], "candidate_state": {"candidate": "current"}}]), encoding="utf-8")
        import subprocess

        result = subprocess.run([sys.executable, str(REPO_ROOT / "scripts" / "p2p_parallel.py"), "--root", str(root), "--requests", str(request_file), "run"], capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "BLOCKED")
        self.assertFalse(payload["parallel_execution"])


if __name__ == "__main__":
    unittest.main()
