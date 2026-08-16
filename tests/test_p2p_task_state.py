from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = REPO_ROOT / ".p2p" / "system"
if str(SYSTEM_ROOT) not in sys.path:
    sys.path.insert(0, str(SYSTEM_ROOT))

from p2p_capabilities.evidence import EvidenceClaim  # noqa: E402
from p2p_capabilities.task_state import (  # noqa: E402
    TaskContractError,
    TaskEvidenceError,
    TaskGraphError,
    TaskGateError,
    TaskPlan,
    TaskStateStore,
    TaskControlPlaneError,
    TaskTransitionError,
    beginner_owner_message,
    checkpoint_task,
    classify_resume,
    complete_task,
    dependency_handoff,
    next_safe_task,
    preflight_task,
    request_owner_decision,
    resolve_owner_decision,
)


NOW = "2026-08-14T14:00:00+00:00"
READY_NOW = "2026-08-14T14:01:00+00:00"
FINGERPRINT_A = "a" * 64
FINGERPRINT_B = "b" * 64


def goal(goal_id: str = "goal-test") -> dict[str, object]:
    return {
        "goal_id": goal_id,
        "scope": ["bounded task-state foundation"],
        "out_of_scope": ["scheduler", "background worker"],
        "completion_criteria": [{"criterion_id": "criterion-state", "description": "state is durable"}],
    }


def task(task_id: str, *, dependencies: list[str] | None = None, evidence: str | None = None, **extra: object) -> dict[str, object]:
    return {
        "task_id": task_id,
        "title": f"Task {task_id}",
        "purpose": f"Bounded purpose for {task_id}",
        "dependencies": dependencies or [],
        "acceptance_requirements": [f"acceptance-{task_id}"],
        "required_evidence": [evidence or f"evidence-{task_id}"],
        **extra,
    }


def valid_evidence(reference: str = "evidence-one", fingerprint: str = FINGERPRINT_A, *, status: str = "VERIFIED", freshness: str = "CURRENT") -> EvidenceClaim:
    return EvidenceClaim(
        claim="The bounded task result is independently checked.",
        required_evidence=(reference,),
        actual_evidence=(
            {
                "source": "tests/test_p2p_task_state.py",
                "evidence_ref": reference,
                "origin": "RUNTIME_EVIDENCE",
                "observed_at": NOW,
                "freshness": freshness,
                "scope": ["task-state"],
                "source_binding": "focused-test",
                "fingerprint": fingerprint,
            },
        ),
        status=status,
    )


def healthy_readiness() -> dict[str, object]:
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


class P2PTaskStateTests(unittest.TestCase):
    def make_plan(self, specs: list[dict[str, object]], *, goal_id: str = "goal-test") -> TaskPlan:
        return TaskPlan.from_goal(goal(goal_id), specs, now=NOW)

    def test_contract_graph_and_identity_boundary(self) -> None:
        plan = self.make_plan([task("one"), task("two", dependencies=["one"])])
        self.assertEqual(plan.topological_order(), ("one", "two"))
        self.assertEqual(plan.plan_revision, 1)
        self.assertEqual(len(plan.plan_revisions), 1)
        with self.assertRaises(TaskGraphError):
            self.make_plan([task("one", dependencies=["two"]), task("two", dependencies=["one"])])
        with self.assertRaises(TaskContractError):
            self.make_plan([dict(task("one"), agent_id="must-not-be-task-state")])

    def test_done_requires_current_bound_evidence_and_no_raw_state(self) -> None:
        plan = self.make_plan([task("one", evidence="evidence-one")]).refresh_ready(now=READY_NOW)
        plan = plan.transition("one", "ACTIVE", now=READY_NOW)
        plan = complete_task(plan, "one", [valid_evidence()], {"observed": "pass"}, now="2026-08-14T14:02:00+00:00")
        self.assertEqual(plan.tasks["one"].status, "DONE")
        self.assertNotIn("observed", json.dumps(plan.tasks["one"].completion))
        with self.assertRaises(TaskEvidenceError):
            complete_task(
                self.make_plan([task("one", evidence="evidence-one")]).refresh_ready(now=READY_NOW).transition("one", "ACTIVE", now=READY_NOW),
                "one",
                [valid_evidence(status="CONTRADICTED")],
                {"observed": "contradiction"},
                now="2026-08-14T14:02:00+00:00",
            )
        with self.assertRaises(TaskEvidenceError):
            complete_task(
                self.make_plan([task("one", evidence="evidence-one")]).refresh_ready(now=READY_NOW).transition("one", "ACTIVE", now=READY_NOW),
                "one",
                [valid_evidence(reference="other-evidence")],
                {"observed": "missing required evidence"},
                now="2026-08-14T14:02:00+00:00",
            )

    def test_capability_permission_and_owner_gates_are_fail_closed(self) -> None:
        plan = self.make_plan([task("gated", required_capabilities=["cap-x"], permission_needs=["write-scope"])])
        blocked, blocked_result = preflight_task(plan, "gated", now=NOW)
        self.assertEqual(blocked_result["status"], "BLOCKED")
        self.assertEqual(blocked.tasks["gated"].status, "BLOCKED")

        waiting, waiting_result = preflight_task(
            plan,
            "gated",
            capability_readiness={"cap-x": healthy_readiness()},
            permission_state={},
            now=NOW,
        )
        self.assertEqual(waiting_result["status"], "WAITING_OWNER")
        self.assertEqual(waiting.tasks["gated"].status, "WAITING_OWNER")
        owner_prompt = beginner_owner_message(waiting, "gated")
        self.assertEqual(len(owner_prompt["options"]), 2)
        self.assertTrue(owner_prompt["recommendation"])
        self.assertFalse(owner_prompt["approval_metadata"]["auto_grant_permissions"])
        resolved = resolve_owner_decision(waiting, "gated", approved=True, answer="Approved only for this bounded task", decision_refs=["decision/gated"], now=READY_NOW)
        self.assertEqual(resolved.tasks["gated"].status, "PLANNED")
        ready, result = preflight_task(
            resolved,
            "gated",
            capability_readiness={"cap-x": healthy_readiness()},
            permission_state={"write-scope": {"status": "APPROVED", "source_ref": "owner/decision/gated"}},
            now="2026-08-14T14:02:00+00:00",
        )
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(ready.tasks["gated"].status, "READY")
        self.assertEqual(next_safe_task(ready).task_id, "gated")

    def test_revision_checkpoint_resume_and_handoff_preserve_provenance(self) -> None:
        plan = self.make_plan([task("one", evidence="evidence-one"), task("two", dependencies=["one"], evidence="evidence-two")])
        plan = plan.refresh_ready(now=READY_NOW).transition("one", "ACTIVE", now=READY_NOW)
        plan = complete_task(plan, "one", [valid_evidence()], {"state": "one-done"}, now="2026-08-14T14:02:00+00:00")
        with self.assertRaises(TaskContractError):
            plan.revise({"one": {"purpose": "Rewrite completed history"}}, reason="Attempt to rewrite completed task", now="2026-08-14T14:02:30+00:00")
        handoff = dependency_handoff(plan, "one")
        self.assertEqual(handoff["downstream_tasks"][0]["task_id"], "two")
        plan = plan.refresh_ready(now="2026-08-14T14:03:00+00:00")
        self.assertEqual(plan.tasks["two"].status, "READY")
        plan = checkpoint_task(
            plan,
            "two",
            {
                "checkpoint_ref": "checkpoint/two",
                "state_fingerprint": FINGERPRINT_B,
                "recovery_classification": "SAFE_TO_RESUME",
                "next_safe_step": "Inspect the next bounded action",
                "captured_at": "2026-08-14T14:04:00+00:00",
            },
            now="2026-08-14T14:04:00+00:00",
        )
        self.assertEqual(classify_resume(plan.tasks["two"], current_state_fingerprint=FINGERPRINT_B)["resume_classification"], "SAFE_TO_RESUME")
        self.assertEqual(classify_resume(plan.tasks["two"], current_state_fingerprint=FINGERPRINT_A)["resume_classification"], "NEEDS_RECHECK")
        revised = plan.revise({"two": {"purpose": "Clarified bounded handoff"}}, source_refs=["docs/SPEC/P2P-DECISION-TRACE-SPEC.md"], reason="Clarify continuation evidence", now="2026-08-14T14:05:00+00:00")
        self.assertEqual(revised.plan_revision, 2)
        self.assertEqual(len(revised.plan_revisions), 2)

    def test_t1_unique_task_ids_fail_closed(self) -> None:
        with self.assertRaises(TaskContractError):
            self.make_plan([task("duplicate"), task("duplicate")])

    def test_t4_cycles_are_rejected_explicitly(self) -> None:
        with self.assertRaises(TaskGraphError):
            self.make_plan([task("one", dependencies=["two"]), task("two", dependencies=["one"])])

    def test_t2_invalid_dependency_reference_fails_closed(self) -> None:
        with self.assertRaises(TaskGraphError):
            self.make_plan([task("one", dependencies=["missing"])])

    def test_t3_self_dependency_fails_closed(self) -> None:
        with self.assertRaises(TaskGraphError):
            self.make_plan([task("one", dependencies=["one"])])

    def test_t5_incomplete_dependency_cannot_become_ready(self) -> None:
        plan = self.make_plan([task("one"), task("two", dependencies=["one"])])
        plan = plan.refresh_ready(now=READY_NOW)
        self.assertEqual(plan.tasks["one"].status, "READY")
        self.assertEqual(plan.tasks["two"].status, "PLANNED")
        with self.assertRaises(TaskTransitionError):
            plan.transition("two", "READY", now=READY_NOW)

    def test_t7_stale_evidence_cannot_complete_task(self) -> None:
        plan = self.make_plan([task("one")]).refresh_ready(now=READY_NOW).transition("one", "ACTIVE", now=READY_NOW)
        with self.assertRaises(TaskEvidenceError):
            complete_task(plan, "one", [valid_evidence(freshness="STALE")], {"state": "stale"}, now="2026-08-14T14:02:00+00:00")

    def test_t11_interrupted_active_task_never_becomes_done(self) -> None:
        plan = self.make_plan([task("one")]).refresh_ready(now=READY_NOW).transition("one", "ACTIVE", now=READY_NOW)
        checkpointed = checkpoint_task(
            plan,
            "one",
            {
                "checkpoint_ref": "checkpoint/one-active",
                "state_fingerprint": FINGERPRINT_A,
                "recovery_classification": "SAFE_TO_RESUME",
                "next_safe_step": "Recheck the bounded action",
                "captured_at": "2026-08-14T14:02:00+00:00",
            },
            now="2026-08-14T14:02:00+00:00",
        )
        self.assertEqual(checkpointed.tasks["one"].status, "ACTIVE")
        self.assertIsNone(checkpointed.tasks["one"].completion)

    def test_t12_missing_checkpoint_is_unknown(self) -> None:
        plan = self.make_plan([task("one")]).refresh_ready(now=READY_NOW).transition("one", "ACTIVE", now=READY_NOW)
        self.assertEqual(classify_resume(plan.tasks["one"]) ["resume_classification"], "UNKNOWN")

    def test_t14_revision_keeps_completed_history_immutable(self) -> None:
        plan = self.make_plan([task("one")]).refresh_ready(now=READY_NOW).transition("one", "ACTIVE", now=READY_NOW)
        plan = complete_task(plan, "one", [valid_evidence()], {"state": "done"}, now="2026-08-14T14:02:00+00:00")
        with self.assertRaises(TaskContractError):
            plan.revise({"one": {"title": "Rewrite completed task"}}, reason="Invalid history rewrite", now="2026-08-14T14:03:00+00:00")

    def test_t15_cancelled_dependency_does_not_unlock_downstream(self) -> None:
        plan = self.make_plan([task("one"), task("two", dependencies=["one"])])
        cancelled = plan.transition("one", "CANCELLED", now=READY_NOW)
        self.assertFalse(cancelled.dependencies_are_done("two"))
        self.assertEqual(cancelled.refresh_ready(now="2026-08-14T14:02:00+00:00").tasks["two"].status, "PLANNED")

    def test_t17_handoff_never_creates_worker_or_auto_start(self) -> None:
        plan = self.make_plan([task("one")]).refresh_ready(now=READY_NOW).transition("one", "ACTIVE", now=READY_NOW)
        plan = complete_task(plan, "one", [valid_evidence()], {"state": "done"}, now="2026-08-14T14:02:00+00:00")
        handoff = dependency_handoff(plan, "one")
        self.assertFalse(handoff["automatic_start"])
        self.assertNotIn("agent", json.dumps(handoff).lower())

    def test_t18_c09_blocked_identity_state_remains_unknown(self) -> None:
        project_status = json.loads((REPO_ROOT / ".p2p" / "state" / "project-status.json").read_text(encoding="utf-8"))
        self.assertEqual(project_status.get("terminal_state"), "BLOCKED")
        self.assertIn("P2P-C09", project_status.get("current_request", ""))
        self.assertIn("do not rerun c08", project_status.get("current_request", "").lower())

    def test_t19_canonical_count_remains_eight(self) -> None:
        registry = json.loads((SYSTEM_ROOT / "p2p_capabilities" / "capabilities.json").read_text(encoding="utf-8"))
        canonical = [item["CAPABILITY_ID"] for item in registry["capabilities"] if item.get("CANONICAL_QUORUM_MEMBER")]
        self.assertEqual(len(canonical), 8)
        self.assertEqual(registry.get("canonical_denominator", 8), 8)

    def test_t20_aesthetica_is_optional_and_noncanonical(self) -> None:
        registry = json.loads((SYSTEM_ROOT / "p2p_capabilities" / "capabilities.json").read_text(encoding="utf-8"))
        aesthetica = next(item for item in registry["capabilities"] if item.get("CAPABILITY_ID") == "p2p_aesthetica")
        self.assertTrue(aesthetica.get("OPTIONAL_SPECIALIST"))
        self.assertFalse(aesthetica.get("CANONICAL_QUORUM_MEMBER"))

    def test_store_is_atomic_durable_and_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT / ".tmp", prefix="p2p-c11-store-") as raw:
            project = Path(raw)
            plan = self.make_plan([task("one")], goal_id="goal-store")
            store = TaskStateStore(project)
            store.initialize(plan, at=NOW)
            ready = store.require().refresh_ready(now=READY_NOW)
            store.save(ready, event_name="task_ready_refresh", at=READY_NOW)
            reloaded = TaskStateStore(project).load()
            self.assertIsNotNone(reloaded)
            self.assertEqual(reloaded.tasks["one"].status, "READY")
            events = store.read_events()
            self.assertEqual(events["status"], "PASS")
            self.assertGreaterEqual(len(events["events"]), 2)
            self.assertTrue((project / ".p2p" / "state" / "task-state.json").is_file())
            self.assertTrue((project / ".p2p" / "state" / "execution-ledger.jsonl").is_file())
            state_path = project / ".p2p" / "state" / "task-state.json"
            state_path.write_text("{broken", encoding="utf-8")
            with self.assertRaises(TaskControlPlaneError):
                TaskStateStore(project).load()

    def test_cli_init_and_show_use_project_local_state(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT / ".tmp", prefix="p2p-c11-cli-") as raw:
            project = Path(raw)
            state = project / ".p2p" / "state"
            state.mkdir(parents=True)
            (state / "goal-contract.json").write_text(json.dumps(goal("goal-cli")), encoding="utf-8")
            tasks = project / "tasks.json"
            tasks.write_text(json.dumps([task("one")]), encoding="utf-8")
            command = [sys.executable, str(REPO_ROOT / "scripts" / "p2p_task_state.py"), "--root", str(project), "init", "--tasks", str(tasks)]
            result = subprocess.run(command, capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            show = subprocess.run([sys.executable, str(REPO_ROOT / "scripts" / "p2p_task_state.py"), "--root", str(project), "show"], capture_output=True, text=True, check=False)
            self.assertEqual(show.returncode, 0, show.stderr + show.stdout)
            payload = json.loads(show.stdout)
            self.assertEqual(payload["goal_id"], "goal-cli")
            self.assertFalse(payload["automatic_start"])
            tasks.write_text(json.dumps([task("one"), "malformed-task-entry"]), encoding="utf-8")
            malformed = subprocess.run(command, capture_output=True, text=True, check=False)
            self.assertEqual(malformed.returncode, 2)
            self.assertIn("TASK_INPUT_ENTRY_MUST_BE_OBJECT", malformed.stdout)


if __name__ == "__main__":
    unittest.main()
