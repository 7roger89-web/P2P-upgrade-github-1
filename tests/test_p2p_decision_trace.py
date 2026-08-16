from __future__ import annotations

import sys
import json
import shutil
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import p2p_decision_trace_eval as evaluator  # noqa: E402
import p2p_workflow  # noqa: E402


class P2PDecisionTraceTests(unittest.TestCase):
    def test_dt1_to_dt24_behavioral_certification_passes(self) -> None:
        result = evaluator.run_evaluation(REPO_ROOT)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["case_count"], 24)
        self.assertEqual(result["pass_count"], 24)
        self.assertTrue(result["baseline_gap_confirmed"])
        self.assertTrue(result["environment_isolation"]["protected_hashes_unchanged"])
        self.assertEqual(result["canonical_safety"]["denominator"], 8)
        self.assertEqual(result["canonical_safety"]["full_quorum"], "8/8")
        self.assertFalse(result["canonical_safety"]["aesthetica_canonical"])
        self.assertNotIn("chain_of_thought", str(result).lower())

    def test_material_workflow_auto_captures_and_exposes_why(self) -> None:
        with tempfile.TemporaryDirectory(prefix="p2p-native-trace-workflow-") as raw:
            project = Path(raw) / "project"
            shutil.copytree(REPO_ROOT / "tests" / "fixtures" / "new-project", project)
            result = p2p_workflow.run_workflow(
                project,
                "Choose the architecture for this project and preserve the existing governance boundaries.",
                package_hint=str(REPO_ROOT),
                acceptance=True,
            )
            self.assertEqual(result["status"], "PASS")
            self.assertTrue(result["decision_trace"]["captured"])
            trace_module = p2p_workflow.decision_trace_api(project, str(REPO_ROOT))
            self.assertIsNotNone(trace_module)
            query = trace_module.query_trace(project, decision_id=result["decision_trace"]["decision_id"])
            self.assertEqual(query["status"], "PASS")
            self.assertIn("P2P chọn cách này vì", query["beginner_why"])
            status = json.loads((project / ".p2p" / "state" / "project-status.json").read_text(encoding="utf-8"))
            self.assertEqual(status["decision_trace_refs"], [result["decision_trace"]["decision_id"]])
            report = (project / result["report_markdown"]).read_text(encoding="utf-8")
            self.assertIn("P2P WHY:", report)

    def test_relationship_states_are_explicit(self) -> None:
        import sys
        sys.path.insert(0, str(REPO_ROOT / ".p2p" / "system"))
        from p2p_capabilities import decision_trace as trace  # noqa: E402

        self.assertEqual(trace.make_trace(decision_id="R-S", decision_type="OTHER_MATERIAL", outcome="x", decision_basis={"summary": "x"}, relationship="SUPPORTS")["RELATIONSHIP"], "SUPPORTS")
        self.assertEqual(trace.make_trace(decision_id="R-C", decision_type="OTHER_MATERIAL", outcome="x", decision_basis={"summary": "x"}, relationship="CONTRADICTS")["RELATIONSHIP"], "CONTRADICTS")
        self.assertEqual(trace.make_trace(decision_id="R-U", decision_type="OTHER_MATERIAL", outcome="x", decision_basis={"summary": "x"})["RELATIONSHIP"], "UNKNOWN")

    def test_policy_references_normalize_resolve_and_fail_honestly(self) -> None:
        import sys
        sys.path.insert(0, str(REPO_ROOT / ".p2p" / "system"))
        from p2p_capabilities import decision_trace as trace  # noqa: E402

        with tempfile.TemporaryDirectory(prefix="p2p-policy-reference-normalization-") as raw:
            project = Path(raw) / "project"
            governance = project / ".p2p" / "system" / "governance"
            governance.mkdir(parents=True)
            (governance / "fact-ledger.json").write_text('{"claims": []}\n', encoding="utf-8")
            (governance / "approval-policy.json").write_text('{}\n', encoding="utf-8")
            (governance / "drift-policy.json").write_text('{}\n', encoding="utf-8")

            value = trace.make_trace(
                decision_id="D-POLICY-NORMALIZATION",
                decision_type="GOVERNANCE",
                outcome="use governed policy",
                decision_basis={"summary": "use exact governed policy references"},
                policy_refs=["approval-policy.json", r"governance\drift-policy.json"],
            )
            self.assertEqual(
                value["POLICY_REFS"],
                ["governance/approval-policy.json", "governance/drift-policy.json"],
            )
            trace.append_trace(project, value)
            resolved = trace.query_trace(project, decision_id="D-POLICY-NORMALIZATION")
            policy_links = resolved["results"][0]["links"]["POLICY_REFS"]
            self.assertEqual([item["STATUS"] for item in policy_links], ["PRESENT", "PRESENT"])
            self.assertEqual(resolved["status"], "PASS")
            self.assertNotIn(str(project), json.dumps(resolved, ensure_ascii=False))

            legacy = trace.make_trace(
                decision_id="D-POLICY-LEGACY",
                decision_type="GOVERNANCE",
                outcome="legacy policy",
                decision_basis={"summary": "read an older trace"},
            )
            legacy["POLICY_REFS"] = ["approval-policy.json"]
            legacy["INTEGRITY_METADATA"] = trace._integrity(legacy)
            trace.append_trace(project, legacy)
            legacy_result = trace.query_trace(project, decision_id="D-POLICY-LEGACY")
            self.assertEqual(legacy_result["results"][0]["links"]["POLICY_REFS"][0]["STATUS"], "PRESENT")
            self.assertEqual(
                legacy_result["results"][0]["links"]["POLICY_REFS"][0]["NORMALIZED_REF"],
                "governance/approval-policy.json",
            )

            invalid = trace.make_trace(
                decision_id="D-POLICY-INVALID",
                decision_type="GOVERNANCE",
                outcome="invalid policy reference",
                decision_basis={"summary": "keep missing evidence visible"},
                policy_refs=["governance/does-not-exist.json"],
            )
            trace.append_trace(project, invalid)
            invalid_result = trace.query_trace(project, decision_id="D-POLICY-INVALID")
            invalid_link = invalid_result["results"][0]["links"]["POLICY_REFS"][0]
            self.assertEqual(invalid_link["STATUS"], "MISSING_REFERENCE")
            self.assertEqual(invalid_result["status"], "PARTIAL")

            with self.assertRaises(trace.DecisionTraceError):
                trace.make_trace(
                    decision_id="D-POLICY-ABSOLUTE",
                    decision_type="GOVERNANCE",
                    outcome="unsafe policy reference",
                    decision_basis={"summary": "reject machine path"},
                    policy_refs=[str((governance / "approval-policy.json").resolve())],
                )


if __name__ == "__main__":
    unittest.main()
