import copy
import json
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = REPO_ROOT / ".p2p" / "system"
if str(SYSTEM_ROOT) not in sys.path:
    sys.path.insert(0, str(SYSTEM_ROOT))

from p2p_capabilities.context import (  # noqa: E402
    CONTEXT_INSUFFICIENT,
    EXPANDED,
    MINIMAL,
    STANDARD,
    LOCAL_SERIALIZATION_PROXY,
    build_knowledge_delta,
    escalate_task_context,
    materialize_task_context,
    retrieve_task_context,
    validate_context_reuse,
)


FIXTURE = REPO_ROOT / "tests" / "fixtures" / "p2p-c19-task-targeted-context.json"


def source(source_id: str, role: str, *, coverage=(), content=None, **extra):
    value = {
        "source_id": source_id,
        "path": source_id,
        "source_class": "AUTHORITATIVE_PROJECT_SOURCE",
        "retrieval_role": role,
        "coverage_ids": list(coverage),
        "scope": ["current-task"],
        "content": content if content is not None else {"source": source_id},
    }
    value.update(extra)
    return value


def direct_task(*refs: str, acceptance_refs=None, purpose="bounded task"):
    return {
        "task_purpose": purpose,
        "scope": ["current-task"],
        "direct_authoritative_refs": list(refs),
        "acceptance": [{"coverage_id": f"acceptance-{index}", "source_refs": [ref], "required": True} for index, ref in enumerate(acceptance_refs or refs)],
    }


class TaskTargetedContextTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_fixture_has_exact_cr1_to_cr20(self):
        self.assertEqual([case["id"] for case in self.cases], [f"CR{index}" for index in range(1, 21)])

    def test_cr1_cr2_cr3_minimal_direct_authority(self):
        catalog = [source("task.py", "DIRECT_AUTHORITATIVE_REFS"), source("module-a.py", "DIRECT_AUTHORITATIVE_REFS"), source("module-b.py", "DIRECT_AUTHORITATIVE_REFS")]
        for refs in (("task.py",), ("task.py",), ("module-a.py", "module-b.py")):
            plan = retrieve_task_context(direct_task(*refs), catalog, context_class=MINIMAL)
            self.assertEqual(plan["status"], "SUFFICIENT")
            self.assertEqual(plan["context_class"], MINIMAL)

    def test_cr4_stale_map_fails_closed(self):
        plan = retrieve_task_context(
            {"project_map_refs": ["repo-map"], "acceptance": [{"coverage_id": "map", "source_refs": ["repo-map"]}]},
            [source("repo-map", "PROJECT_REPO_MAP", freshness="STALE", candidate_binding="candidate-1")],
            context_class=EXPANDED,
            candidate_binding="candidate-1",
        )
        self.assertEqual(plan["status"], "STALE")
        self.assertIn("STALE_INDEX", plan["failure_reasons"])

    def test_cr5_and_cr6_cache_binding_and_hash_rules(self):
        task = direct_task("task.py")
        catalog = [source("task.py", "DIRECT_AUTHORITATIVE_REFS")]
        plan = retrieve_task_context(task, catalog, context_class=MINIMAL, candidate_binding="candidate-1")
        plan["scope"] = ["current-task"]
        reusable = validate_context_reuse(plan, catalog, candidate_binding="candidate-1", required_scope=["current-task"])
        self.assertEqual(reusable["status"], "REUSABLE")
        changed = copy.deepcopy(catalog)
        changed[0]["content"] = {"source": "changed"}
        stale = validate_context_reuse(plan, changed, candidate_binding="candidate-1", required_scope=["current-task"])
        self.assertEqual(stale["status"], "STALE")
        self.assertIn("STALE_SOURCE", stale["reason_codes"])

    def test_cr7_security_coverage_follows_acceptance(self):
        refs = ["auth-entry", "session", "authorization", "secret-handling"]
        catalog = [source(ref, "DIRECT_AUTHORITATIVE_REFS") for ref in refs]
        task = {"context_breadth": "BROAD", "acceptance": [{"coverage_id": ref, "source_refs": [ref]} for ref in refs], "direct_authoritative_refs": refs}
        plan = retrieve_task_context(task, catalog, context_class=EXPANDED)
        self.assertEqual(plan["status"], "SUFFICIENT")
        self.assertEqual(plan["coverage_summary"]["required_coverage_ratio"], 1.0)
        self.assertEqual({item["requirement_state"] for item in plan["coverage"]}, {"REQUIRED"})
        self.assertEqual(plan["coverage_summary"]["counts"]["COVERED"], 4)

    def test_cr8_relevant_source_without_required_area_is_insufficient(self):
        catalog = [source("local.py", "DIRECT_AUTHORITATIVE_REFS"), source("authorization.py", "TARGETED_SOURCE")]
        task = {"direct_authoritative_refs": ["local.py"], "acceptance": [{"coverage_id": "local", "source_refs": ["local.py"]}, {"coverage_id": "authorization", "source_refs": ["authorization.py"]}]}
        plan = retrieve_task_context(task, catalog, context_class=MINIMAL)
        self.assertEqual(plan["status"], "INSUFFICIENT")
        self.assertEqual(plan["next_context_class"], STANDARD)

    def test_cr9_and_cr10_escalation_is_bounded(self):
        task = {"dependency_refs": ["dependency"], "targeted_source_refs": ["target"], "acceptance": [{"coverage_id": "target", "source_refs": ["target"]}]}
        catalog = [source("dependency", "DEPENDENCY_OUTPUTS"), source("target", "TARGETED_SOURCE")]
        minimal = retrieve_task_context(task, catalog, context_class=MINIMAL)
        self.assertEqual(minimal["status"], "INSUFFICIENT")
        standard = escalate_task_context(task, catalog, minimal)
        self.assertEqual(standard["status"], "INSUFFICIENT")
        self.assertEqual(standard["next_context_class"], EXPANDED)
        expanded = escalate_task_context(task, catalog, standard)
        self.assertEqual(expanded["status"], "SUFFICIENT")
        exhausted = escalate_task_context(task, catalog, expanded)
        self.assertEqual(exhausted["context_class"], CONTEXT_INSUFFICIENT)
        self.assertEqual(exhausted["status"], "INSUFFICIENT")

    def test_cr11_cr13_unavailable_or_denied_source_blocks(self):
        for record in (source("unavailable", "DIRECT_AUTHORITATIVE_REFS", readable=False), source("denied", "DIRECT_AUTHORITATIVE_REFS", permission="DENIED")):
            plan = retrieve_task_context(direct_task(record["source_id"]), [record], context_class=MINIMAL)
            self.assertEqual(plan["status"], "BLOCKED")
            self.assertIn("PERMISSION_BLOCKED", plan["failure_reasons"])

    def test_cr12_contradiction_is_preserved(self):
        catalog = [
            source("owner-a", "DIRECT_AUTHORITATIVE_REFS", conflict_group="deployment", content={"value": "A"}),
            source("owner-b", "DIRECT_AUTHORITATIVE_REFS", conflict_group="deployment", content={"value": "B"}),
        ]
        plan = retrieve_task_context(direct_task("owner-a", "owner-b"), catalog, context_class=MINIMAL)
        self.assertEqual(plan["status"], "CONTRADICTED")
        self.assertEqual(plan["contradictions"], ["deployment"])

    def test_cr14_available_context_is_not_materialized_context(self):
        catalog = [source("task.py", "DIRECT_AUTHORITATIVE_REFS")] + [source(f"unrelated-{i}.py", "TARGETED_SOURCE") for i in range(99)]
        plan = retrieve_task_context(direct_task("task.py"), catalog, context_class=MINIMAL)
        materialized = materialize_task_context(plan, catalog, role="WORKER")
        self.assertEqual(plan["available_context"]["count"], 100)
        self.assertEqual(materialized["materialized_context"]["count"], 1)
        self.assertEqual(materialized["permission_expansion"], False)

    def test_cr15_overlapping_workers_can_reuse_same_bounded_materialization(self):
        catalog = [source("shared.py", "DIRECT_AUTHORITATIVE_REFS")]
        plan = retrieve_task_context(direct_task("shared.py"), catalog, context_class=MINIMAL, candidate_binding="candidate")
        first = materialize_task_context(plan, catalog, role="WORKER")
        second = materialize_task_context(plan, catalog, role="WORKER")
        self.assertEqual(first["materialized_context"], second["materialized_context"])
        self.assertEqual(validate_context_reuse(plan, catalog, candidate_binding="candidate", required_scope=["current-task"])["status"], "REUSABLE")

    def test_cr16_routed_design_source_does_not_load_all_faculties(self):
        catalog = [source("design-faculty-spacing", "DIRECT_AUTHORITATIVE_REFS")] + [source(f"faculty-{i}", "TARGETED_SOURCE") for i in range(173)]
        plan = retrieve_task_context(direct_task("design-faculty-spacing", purpose="design intelligence"), catalog, context_class=MINIMAL)
        self.assertEqual(plan["status"], "SUFFICIENT")
        self.assertEqual(plan["materialized_context"]["count"], 1)

    def test_cr17_research_uses_bounded_expanded_order(self):
        catalog = [source("research-direct", "DIRECT_AUTHORITATIVE_REFS"), source("research-evidence", "KNOWN_EVIDENCE"), source("research-map", "PROJECT_REPO_MAP"), source("research-target", "TARGETED_SOURCE")]
        task = {"task_purpose": "research", "direct_authoritative_refs": ["research-direct"], "known_evidence": ["research-evidence"], "project_map_refs": ["research-map"], "targeted_source_refs": ["research-target"], "acceptance": [{"coverage_id": "research", "source_refs": ["research-target"]}]}
        plan = retrieve_task_context(task, catalog, context_class=EXPANDED)
        self.assertEqual(plan["status"], "SUFFICIENT")
        self.assertEqual(plan["retrieval_order"][0], "TASK_CONTRACT")

    def test_cr18_summary_invalidates_after_authoritative_change(self):
        catalog = [source("summary.json", "DIRECT_AUTHORITATIVE_REFS")]
        plan = retrieve_task_context(direct_task("summary.json"), catalog, context_class=MINIMAL)
        catalog[0]["content"] = {"summary": "new"}
        result = validate_context_reuse(plan, catalog, candidate_binding=None, required_scope=["current-task"])
        self.assertEqual(result["status"], "STALE")

    def test_cr19_project_authority_beats_external_source(self):
        catalog = [source("owner-decision", "DIRECT_AUTHORITATIVE_REFS", content={"value": "owner"}), source("web-result", "DIRECT_AUTHORITATIVE_REFS", source_class="EXTERNAL", content={"value": "external"})]
        task = direct_task("owner-decision", "web-result", acceptance_refs=["owner-decision"], purpose="verify project truth")
        plan = retrieve_task_context(task, catalog, context_class=MINIMAL, allow_external=False)
        self.assertEqual(plan["status"], "SUFFICIENT")
        self.assertIn("web-result", {item["source_id"] for item in plan["excluded"]})

    def test_cr20_beginner_request_never_requires_retrieval_questions(self):
        plan = retrieve_task_context(direct_task("task.py", purpose="continue completing the project"), [source("task.py", "DIRECT_AUTHORITATIVE_REFS")], context_class=MINIMAL)
        self.assertEqual(plan["status"], "SUFFICIENT")
        self.assertNotIn("Which files should I read?", json.dumps(plan))

    def test_pointer_and_secret_boundaries_remain_fail_closed(self):
        with self.assertRaises(Exception):
            retrieve_task_context(direct_task("secret.json"), [source("secret.json", "DIRECT_AUTHORITATIVE_REFS", content={"api_token": "no"})], context_class=MINIMAL)

    def test_delta_contains_references_not_transcript(self):
        delta = build_knowledge_delta([source("new.py", "TARGETED_SOURCE")], coverage_updates=[{"coverage_id": "new", "status": "COVERED"}])
        self.assertEqual(delta["schema"], "p2p-knowledge-delta/1")
        self.assertFalse(delta["transcript_included"])
        self.assertIn("source_hash", delta["new_source_bindings"][0])

    def test_local_proxy_is_honestly_labeled(self):
        plan = retrieve_task_context(direct_task("task.py"), [source("task.py", "DIRECT_AUTHORITATIVE_REFS")], context_class=MINIMAL)
        self.assertEqual(plan["local_serialization_proxy"]["label"], LOCAL_SERIALIZATION_PROXY)


if __name__ == "__main__":
    unittest.main()
