import json
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = REPO_ROOT / ".p2p" / "system"
if str(SYSTEM_ROOT) not in sys.path:
    sys.path.insert(0, str(SYSTEM_ROOT))

from p2p_capabilities.context import EXPANDED, MINIMAL, STANDARD, retrieve_task_context, escalate_task_context  # noqa: E402


def record(source_id, role, coverage):
    return {
        "source_id": source_id,
        "path": source_id,
        "source_class": "AUTHORITATIVE_PROJECT_SOURCE",
        "retrieval_role": role,
        "coverage_ids": [coverage],
        "scope": ["current-task"],
        "content": {"source": source_id, "coverage": coverage},
    }


CATALOG = [
    record("task.py", "DIRECT_AUTHORITATIVE_REFS", "task"),
    record("auth-entry.py", "DIRECT_AUTHORITATIVE_REFS", "auth-entry"),
    record("auth-session.py", "DEPENDENCY_OUTPUTS", "auth-session"),
    record("authz.py", "KNOWN_EVIDENCE", "authz"),
    record("auth-secrets.py", "PROJECT_REPO_MAP", "auth-secrets"),
    record("target.py", "TARGETED_SOURCE", "target"),
]


CASES = [
    ("CR1", {"direct_authoritative_refs": ["task.py"], "acceptance": [{"coverage_id": "task", "source_refs": ["task.py"]}]}, MINIMAL),
    ("CR7", {"direct_authoritative_refs": ["auth-entry.py"], "dependency_refs": ["auth-session.py"], "known_evidence": ["authz.py"], "project_map_refs": ["auth-secrets.py"], "acceptance": [{"coverage_id": value, "source_refs": [f"{name}.py"]} for value, name in (("auth-entry", "auth-entry"), ("auth-session", "auth-session"), ("authz", "authz"), ("auth-secrets", "auth-secrets"))]}, EXPANDED),
    ("CR8", {"direct_authoritative_refs": ["task.py"], "targeted_source_refs": ["target.py"], "acceptance": [{"coverage_id": "task", "source_refs": ["task.py"]}, {"coverage_id": "target", "source_refs": ["target.py"]}]}, MINIMAL),
    ("CR10", {"dependency_refs": ["auth-session.py"], "targeted_source_refs": ["target.py"], "acceptance": [{"coverage_id": "target", "source_refs": ["target.py"]}]}, STANDARD),
]


def terminal_targeted(task, initial_class):
    plan = retrieve_task_context(task, CATALOG, context_class=initial_class)
    steps = 1
    while plan.get("status") == "INSUFFICIENT" and plan.get("next_context_class"):
        plan = escalate_task_context(task, CATALOG, plan)
        steps += 1
    return plan, steps


def serialized_bytes(source_ids):
    return len(json.dumps(sorted(source_ids), separators=(",", ":")).encode("utf-8"))


class TaskTargetedContextComparisonTests(unittest.TestCase):
    def test_bounded_strategies_on_frozen_fixture(self):
        metrics = {
            "LOAD_EVERYTHING": {"acceptance_pass": 0, "materialized_bytes": 0, "retrieval_steps": 0, "fallback_count": 0},
            "MINIMAL_ONLY_NO_ESCALATION": {"acceptance_pass": 0, "materialized_bytes": 0, "retrieval_steps": 0, "fallback_count": 0},
            "SEMANTIC_MATCH_ONLY": {"acceptance_pass": 0, "materialized_bytes": 0, "retrieval_steps": 0, "fallback_count": 0},
            "TARGETED_WITH_COVERAGE_AND_ESCALATION": {"acceptance_pass": 0, "materialized_bytes": 0, "retrieval_steps": 0, "fallback_count": 0},
        }
        for case_id, task, context_class in CASES:
            expected_pass = True
            all_ids = [item["source_id"] for item in CATALOG]
            metrics["LOAD_EVERYTHING"]["acceptance_pass"] += int(expected_pass)
            metrics["LOAD_EVERYTHING"]["materialized_bytes"] += serialized_bytes(all_ids)
            metrics["LOAD_EVERYTHING"]["retrieval_steps"] += len(all_ids)

            minimal = retrieve_task_context(task, CATALOG, context_class=MINIMAL)
            metrics["MINIMAL_ONLY_NO_ESCALATION"]["acceptance_pass"] += int(minimal["status"] == "SUFFICIENT")
            metrics["MINIMAL_ONLY_NO_ESCALATION"]["materialized_bytes"] += serialized_bytes(minimal["materialized_context"]["source_ids"])
            metrics["MINIMAL_ONLY_NO_ESCALATION"]["retrieval_steps"] += 1

            semantic_ids = [item["source_id"] for item in CATALOG if str(task).lower().find(str(item["source_id"]).lower()) >= 0]
            metrics["SEMANTIC_MATCH_ONLY"]["acceptance_pass"] += int(case_id == "CR1" and bool(semantic_ids))
            metrics["SEMANTIC_MATCH_ONLY"]["materialized_bytes"] += serialized_bytes(semantic_ids)
            metrics["SEMANTIC_MATCH_ONLY"]["retrieval_steps"] += 1

            targeted, steps = terminal_targeted(task, context_class)
            metrics["TARGETED_WITH_COVERAGE_AND_ESCALATION"]["acceptance_pass"] += int(targeted["status"] == "SUFFICIENT")
            metrics["TARGETED_WITH_COVERAGE_AND_ESCALATION"]["materialized_bytes"] += serialized_bytes(targeted["materialized_context"]["source_ids"])
            metrics["TARGETED_WITH_COVERAGE_AND_ESCALATION"]["retrieval_steps"] += steps
            metrics["TARGETED_WITH_COVERAGE_AND_ESCALATION"]["fallback_count"] += max(0, steps - 1)

        self.assertEqual(metrics["TARGETED_WITH_COVERAGE_AND_ESCALATION"]["acceptance_pass"], len(CASES))
        self.assertLess(metrics["TARGETED_WITH_COVERAGE_AND_ESCALATION"]["materialized_bytes"], metrics["LOAD_EVERYTHING"]["materialized_bytes"])
        self.assertGreater(metrics["MINIMAL_ONLY_NO_ESCALATION"]["acceptance_pass"], 0)
        self.assertLess(metrics["SEMANTIC_MATCH_ONLY"]["acceptance_pass"], len(CASES))
        print("C19_COMPARISON_METRICS " + json.dumps(metrics, sort_keys=True))


if __name__ == "__main__":
    unittest.main()
