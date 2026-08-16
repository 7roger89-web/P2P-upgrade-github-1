import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = REPO_ROOT / ".p2p" / "system"
if str(SYSTEM_ROOT) not in sys.path:
    sys.path.insert(0, str(SYSTEM_ROOT))

from p2p_capabilities.bounded_delegation import DELEGATE, DIRECT, DelegationRequest, PermissionEnvelope  # noqa: E402
from p2p_capabilities.context import BASELINE_COMPAT, CONTEXT_EFFICIENT_V1, LOCAL_SERIALIZATION_PROXY, build_context_view, context_fingerprint  # noqa: E402
from p2p_capabilities.parallel_execution import (  # noqa: E402
    MAX_PARALLEL_CHILDREN,
    PARALLEL,
    PARALLEL_BLOCKED,
    PARALLEL_LARGE_CONTEXT_BYTES,
    SEQUENTIAL,
    BoundedParallelForegroundController,
    ParallelEconomyProfile,
)
from p2p_capabilities.task_state import TaskPlan, TaskStateStore  # noqa: E402


NOW = "2026-08-16T04:00:00+00:00"


def _goal() -> dict[str, object]:
    return {
        "goal_id": "goal-c17-ce",
        "scope": ["src/a.py", "src/b.py", "src/c.py", "out/a.txt", "out/b.txt", "out/c.txt"],
        "out_of_scope": ["scheduler", ".p2p/state", "release", "remote"],
        "completion_criteria": [{"criterion_id": "criterion-c17-ce", "description": "bounded economy policy is verified"}],
    }


def _task(task_id: str, scope: str, **extra: object) -> dict[str, object]:
    return {
        "task_id": task_id,
        "title": f"C17 CE {task_id}",
        "purpose": "Perform one independent bounded foreground task and return a proposal.",
        "scope": [scope],
        "non_scope": ["scheduler", ".p2p/state", "release", "remote"],
        "acceptance_requirements": [f"acceptance-{task_id}"],
        "required_evidence": [f"evidence-{task_id}"],
        **extra,
    }


def _request(root: Path, task_id: str, *, task_size: str = "MODERATE", value_reasons: tuple[str, ...] = ("CONTEXT_ISOLATION",)) -> DelegationRequest:
    record = TaskStateStore(root).require().tasks[task_id]
    permissions = PermissionEnvelope(grants=("READ",), scope=record.scope)
    return DelegationRequest(
        task=record,
        task_size=task_size,
        value_reasons=value_reasons,
        parent_permissions=permissions,
        child_permissions=permissions,
        child_scope=record.scope,
        read_scopes=record.scope,
        candidate_state={"candidate": "current"},
        host_child_available=True,
    )


def _root(specs: list[dict[str, object]]) -> Path:
    root = Path(tempfile.mkdtemp(prefix="p2p-c17-ce-", dir=REPO_ROOT / ".tmp"))
    TaskStateStore(root).initialize(TaskPlan.from_goal(_goal(), specs, now=NOW), at=NOW)
    return root


def _context_fixture() -> dict[str, object]:
    goal_source = {"goal": "preserve acceptance evidence"}
    history_source = {"history": "historical context that may be deferred"}
    goal_hash = context_fingerprint(goal_source)
    history_hash = context_fingerprint(history_source)
    return {
        "goal_id": "goal-ce-context",
        "task_or_goal": "evaluate bounded context economy",
        "scope": ["current-task"],
        "non_scope": ["remote", "secrets"],
        "acceptance": [{"item_id": "acceptance-main", "value": "acceptance evidence remains present", "required": True}],
        "relevant_facts": [{"item_id": "fact-main", "value": "current project fact", "required": True}],
        "relevant_decisions": [{"item_id": "decision-main", "value": "parent verifies worker proposal", "required": True}],
        "direct_dependencies": [{"item_id": "dependency-main", "value": "dependency is complete", "required": True}],
        "history": [{"item_id": "history-main", "value": history_source["history"], "defer": True, "pointer_id": "pointer-history", "source_binding": "history"}],
        "evidence_pointers": [{
            "pointer_id": "pointer-history",
            "label": "authoritative deferred history",
            "authority": "FACT_LEDGER",
            "scope": ["current-task"],
            "freshness": "CURRENT",
            "provenance": "ce-fixture",
            "content_class": "EVIDENCE",
            "source_binding": "history",
        }],
        "capability_constraints": ["same-tools"],
        "permission_constraints": ["owner approval remains explicit"],
        "source_bindings": [
            {"source_id": "goal", "path": "fixtures/goal.json", "source_hash": goal_hash, "required": True},
            {"source_id": "history", "path": "fixtures/history.json", "source_hash": history_hash},
        ],
        "access_contract": {"tools": ["read"], "source_catalog": "ce-fixture"},
    }


class CognitiveEconomyTests(unittest.TestCase):
    def test_ce1_tiny_independent_pair_uses_sequential_direct_path(self) -> None:
        root = _root([_task("a", "src/a.py"), _task("b", "src/b.py")])
        requests = (_request(root, "a", task_size="TINY"), _request(root, "b", task_size="TINY"))
        decision = BoundedParallelForegroundController(root).decide(requests)
        self.assertEqual(decision["strategy"], SEQUENTIAL)
        self.assertEqual({child["strategy"] for child in decision["child_decisions"].values()}, {DIRECT})

    def test_ce2_meaningful_independent_pair_may_parallelize(self) -> None:
        root = _root([_task("a", "src/a.py"), _task("b", "src/b.py")])
        decision = BoundedParallelForegroundController(root).decide((_request(root, "a"), _request(root, "b")))
        self.assertEqual(decision["strategy"], PARALLEL)
        self.assertEqual(decision["economy_gate"]["mode"], "QUALITY_ADJUSTED_BOUNDED_SIGNALS")

    def test_ce3_duplicate_large_context_is_an_economy_rejection(self) -> None:
        root = _root([_task("a", "src/a.py"), _task("b", "src/b.py")])
        fingerprint = "a" * 64
        profile = {
            task_id: ParallelEconomyProfile(
                expected_work_units=8,
                context_bytes=PARALLEL_LARGE_CONTEXT_BYTES,
                context_fingerprints=(fingerprint,),
                context_proxy_label=LOCAL_SERIALIZATION_PROXY,
            )
            for task_id in ("a", "b")
        }
        decision = BoundedParallelForegroundController(root).decide(
            (_request(root, "a"), _request(root, "b")), economy_profiles=profile
        )
        self.assertEqual(decision["strategy"], SEQUENTIAL)
        self.assertIn("DUPLICATED_CONTEXT_OVERHEAD", decision["pair_rejections"]["a+b"])
        self.assertEqual(decision["reason"], "PARALLEL_ECONOMY_GATE_NOT_SATISFIED")

    def test_ce4_context_insufficient_never_becomes_parallel_pass(self) -> None:
        root = _root([_task("a", "src/a.py"), _task("b", "src/b.py")])
        profiles = {
            "a": ParallelEconomyProfile(context_status="CONTEXT_INSUFFICIENT"),
            "b": ParallelEconomyProfile(),
        }
        decision = BoundedParallelForegroundController(root).decide(
            (_request(root, "a"), _request(root, "b")), economy_profiles=profiles
        )
        self.assertEqual(decision["strategy"], SEQUENTIAL)
        self.assertIn("CONTEXT_INSUFFICIENT", decision["pair_rejections"]["a+b"])
        self.assertFalse(decision["parallel_execution"])

    def test_ce5_worker_output_is_compact_parent_delta(self) -> None:
        root = _root([_task("a", "src/a.py")])
        request = _request(root, "a")

        def child(handoff: dict[str, object]) -> dict[str, object]:
            return {
                "outcome": "SUCCEEDED",
                "candidate_fingerprint": handoff["candidate_fingerprint"],
                "summary": "verbose worker narrative " * 200,
                "work_performed": ["bounded review"],
                "artifact_refs": ["src/a.py"],
                "self_checks": ["scope checked"],
                "unresolved": [],
                "risks": [],
                "recommended_next_step": "parent verifies artifact",
            }

        result = BoundedParallelForegroundController(root).execute((request,), child_executors=child)
        child_result = result["child_results"]["a"].get("child_result", result["child_results"]["a"])
        self.assertLessEqual(len(str(child_result.get("summary", ""))), 8192)
        self.assertIn("artifact_refs", child_result)
        self.assertNotIn("raw_narrative", child_result)
        self.assertFalse(child_result.get("output_is_evidence", False))

    def test_ce6_extensive_plus_tiny_does_not_parallelize_by_readiness(self) -> None:
        root = _root([_task("large", "src/a.py"), _task("tiny", "src/b.py")])
        requests = (_request(root, "large", task_size="LARGE"), _request(root, "tiny", task_size="TINY"))
        decision = BoundedParallelForegroundController(root).decide(requests)
        self.assertEqual(decision["strategy"], SEQUENTIAL)
        self.assertEqual(decision["child_decisions"]["tiny"]["strategy"], DIRECT)

    def test_ce7_independent_review_can_justify_one_extra_worker(self) -> None:
        root = _root([_task("review", "src/a.py"), _task("build", "src/b.py")])
        requests = (
            _request(root, "review", task_size="TINY", value_reasons=("INDEPENDENT_REVIEW",)),
            _request(root, "build", task_size="MODERATE"),
        )
        profiles = {
            "review": ParallelEconomyProfile(expected_work_units=1, handoff_units=2, verification_units=2),
            "build": ParallelEconomyProfile(expected_work_units=1, handoff_units=1, verification_units=1),
        }
        decision = BoundedParallelForegroundController(root).decide(requests, economy_profiles=profiles)
        self.assertEqual(decision["strategy"], PARALLEL)
        self.assertEqual(decision["child_decisions"]["review"]["strategy"], DELEGATE)

    def test_ce8_deterministic_verification_answers_use_no_worker(self) -> None:
        root = _root([_task("a", "src/a.py"), _task("b", "src/b.py")])
        requests = (_request(root, "a", value_reasons=()), _request(root, "b", value_reasons=()))
        decision = BoundedParallelForegroundController(root).decide(requests)
        self.assertEqual(decision["strategy"], SEQUENTIAL)
        self.assertEqual({child["strategy"] for child in decision["child_decisions"].values()}, {DIRECT})

    def test_ce9_local_context_proxy_prefers_lower_overhead_path(self) -> None:
        context = _context_fixture()
        context["history"] = [{"item_id": "history-main", "value": "x" * 100000, "defer": True, "pointer_id": "pointer-history", "source_binding": "history"}]
        baseline = build_context_view(context, BASELINE_COMPAT)
        efficient = build_context_view(context, CONTEXT_EFFICIENT_V1)
        baseline_bytes = baseline["serialized_size"]["bytes"]
        efficient_bytes = efficient["serialized_size"]["bytes"]
        self.assertEqual(baseline["serialized_size"]["label"], LOCAL_SERIALIZATION_PROXY)
        self.assertEqual(efficient["serialized_size"]["label"], LOCAL_SERIALIZATION_PROXY)
        self.assertLess(efficient_bytes, baseline_bytes)
        fingerprint = str(context["source_bindings"][0]["source_hash"])
        root = _root([_task("a", "src/a.py"), _task("b", "src/b.py")])
        requests = (_request(root, "a"), _request(root, "b"))
        baseline_profiles = {
            task_id: ParallelEconomyProfile(context_bytes=max(PARALLEL_LARGE_CONTEXT_BYTES, baseline_bytes), context_fingerprints=(fingerprint,))
            for task_id in ("a", "b")
        }
        efficient_profiles = {
            task_id: ParallelEconomyProfile(context_bytes=efficient_bytes, context_fingerprints=(fingerprint,), context_proxy_label="CONTEXT_POINTER")
            for task_id in ("a", "b")
        }
        controller = BoundedParallelForegroundController(root)
        self.assertEqual(controller.decide(requests, economy_profiles=baseline_profiles)["strategy"], SEQUENTIAL)
        self.assertEqual(controller.decide(requests, economy_profiles=efficient_profiles)["strategy"], PARALLEL)

    def test_ce10_lower_context_with_result_dependency_escalates(self) -> None:
        root = _root([_task("a", "src/a.py"), _task("b", "src/b.py")])
        profiles = {
            "a": ParallelEconomyProfile(context_bytes=32, result_context_dependency=True),
            "b": ParallelEconomyProfile(context_bytes=32),
        }
        decision = BoundedParallelForegroundController(root).decide(
            (_request(root, "a"), _request(root, "b")), economy_profiles=profiles
        )
        self.assertEqual(decision["strategy"], SEQUENTIAL)
        self.assertIn("RESULT_CONTEXT_DEPENDENCY", decision["pair_rejections"]["a+b"])

    def test_spawn_economy_preserves_zero_one_two_worker_outcomes(self) -> None:
        zero_root = _root([_task("a", "src/a.py")])
        zero = BoundedParallelForegroundController(zero_root).decide(())
        self.assertEqual(zero["strategy"], PARALLEL_BLOCKED)
        one_root = _root([_task("a", "src/a.py")])
        one = BoundedParallelForegroundController(one_root).decide((_request(one_root, "a"),))
        self.assertEqual(one["strategy"], SEQUENTIAL)
        two_root = _root([_task("a", "src/a.py"), _task("b", "src/b.py")])
        two = BoundedParallelForegroundController(two_root).decide((_request(two_root, "a"), _request(two_root, "b")))
        self.assertEqual(two["strategy"], PARALLEL)
        self.assertLessEqual(len(two["task_ids"]), MAX_PARALLEL_CHILDREN)

    def test_parent_worker_and_capsule_seams_remain_structured(self) -> None:
        root = _root([_task("a", "src/a.py"), _task("b", "src/b.py")])
        controller = BoundedParallelForegroundController(root)
        decision = controller.decide((_request(root, "a"), _request(root, "b")))
        self.assertIn("economy_profiles", decision)
        self.assertFalse(decision["worker_output_is_evidence"])
        result = controller.execute(
            (_request(root, "a"), _request(root, "b")),
            child_executors=lambda handoff: {"outcome": "SUCCEEDED", "candidate_fingerprint": handoff["candidate_fingerprint"], "work_performed": ["bounded read"]},
            verifiers=lambda result, handoff: {"status": "VERIFIED"},
            combined_verify=lambda children: {"status": "VERIFIED"},
        )
        self.assertEqual(result["strategy"], PARALLEL)
        self.assertFalse(result["worker_output_is_evidence"])
        group = root / ".p2p" / "state" / "foreground-executions" / "parallel-groups" / str(result["parallel_group_id"]) / "group.json"
        persisted = group.read_text(encoding="utf-8")
        self.assertIn("economy_profiles", persisted)
        self.assertIn("combined_verification", persisted)


if __name__ == "__main__":
    unittest.main()
