from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import p2p_gepa_canary as gepa  # noqa: E402


def run(run_id: str, score: float, *, status: str = "pass", unexpected_writes: int = 0, **extra):
    return {
        "run_id": run_id,
        "status": status,
        "model": "fixture-model",
        "surface": "fixture-surface",
        "environment_id": "fixture-env",
        "run_at": "2026-10-07T00:00:00+00:00",
        "score": score,
        "evidence": f".p2p/evals/runs/{run_id}.json",
        "evidence_sha256": "0" * 64,
        "unexpected_writes": unexpected_writes,
        "notes": "deterministic fixture",
        **extra,
    }


def suite(*, baseline: float = 0.5, candidate: float = 0.5):
    cases = []
    for index in range(1, 6):
        case_id = f"case-{index}"
        cases.append(
            {
                "case_id": case_id,
                "class": "frequent",
                "title": f"Case {index}",
                "task": f"Task {index}",
                "fixture": f".p2p/evals/fixtures/{case_id}.json",
                "fixture_sha256": "1" * 64,
                "tags": ["gepa-canary"],
                "checks": [
                    {
                        "check_id": "observable",
                        "grader": "deterministic",
                        "weight": 1,
                        "criterion": "Observable result matches the frozen expectation.",
                    }
                ],
                "baseline_runs": [
                    run(f"baseline-1-{case_id}", baseline),
                    run(f"baseline-2-{case_id}", baseline),
                ],
                "p2p_runs": [
                    run(f"p2p-1-{case_id}", candidate),
                    run(f"p2p-2-{case_id}", candidate),
                ],
            }
        )
    return {
        "schema_version": "p2p-codex-project-eval/2",
        "project": "gepa-canary-fixture",
        "policy": {
            "minimum_cases": 5,
            "minimum_trials_per_variant": 2,
            "minimum_p2p_pass_rate": 0.8,
            "maximum_mean_regression": 0.0,
            "maximum_case_regressions": 0,
            "maximum_score_spread": 0.25,
            "blocked_cases_allowed": False,
        },
        "comparison_contract": {
            "same_input": True,
            "same_environment": True,
            "isolate_runs": True,
            "record_model_and_surface": True,
            "leakage_check": True,
            "criteria_defined_before_runs": True,
            "frozen_fixtures": True,
            "no_cross_run_memory": True,
        },
        "cases": cases,
    }


class P2PGepaCanaryTests(unittest.TestCase):
    def test_missing_trials_requires_evidence(self):
        value = suite()
        value["cases"][0]["p2p_runs"] = []
        result = gepa.evaluate(value)
        self.assertEqual(result["verdict"], "EVIDENCE_REQUIRED")
        self.assertIn("INSUFFICIENT_TRIALS:case-1", result["reason_codes"])

    def test_case_regression_rejects_candidate(self):
        value = suite(baseline=0.8, candidate=0.9)
        value["cases"][2]["p2p_runs"][0]["score"] = 0.1
        value["cases"][2]["p2p_runs"][1]["score"] = 0.1
        result = gepa.evaluate(value)
        self.assertEqual(result["verdict"], "REJECT")
        self.assertIn("CASE_REGRESSION:case-3", result["reason_codes"])

    def test_equal_candidate_has_no_material_improvement(self):
        result = gepa.evaluate(suite(baseline=0.8, candidate=0.8))
        self.assertEqual(result["verdict"], "REJECT")
        self.assertEqual(result["reason_codes"], ["NO_MATERIAL_IMPROVEMENT"])

    def test_clear_non_regressing_quality_improvement_continues_canary(self):
        result = gepa.evaluate(suite(baseline=0.5, candidate=0.9))
        self.assertEqual(result["verdict"], "CONTINUE_CANARY")
        self.assertEqual(result["reason_codes"], ["PARETO_IMPROVEMENT:quality"])

    def test_absent_optional_metrics_are_not_fabricated(self):
        result = gepa.evaluate(suite(baseline=0.5, candidate=0.9))
        self.assertEqual(result["verdict"], "CONTINUE_CANARY")
        self.assertEqual(set(result["observed_dimensions"]), {"quality"})
        self.assertEqual(
            result["not_observed_dimensions"],
            ["cost", "latency_ms", "token_proxy"],
        )

    def test_partial_optional_metric_requires_comparable_evidence(self):
        value = suite(baseline=0.5, candidate=0.9)
        for case in value["cases"]:
            for item in case["baseline_runs"]:
                item["cost"] = 1.0
        result = gepa.evaluate(value)
        self.assertEqual(result["verdict"], "EVIDENCE_REQUIRED")
        self.assertEqual(result["reason_codes"], ["INCOMPARABLE_OPTIONAL_DIMENSION:cost"])

    def test_unexpected_candidate_write_is_hard_reject(self):
        value = suite(baseline=0.5, candidate=0.9)
        value["cases"][0]["p2p_runs"][0]["unexpected_writes"] = 1
        result = gepa.evaluate(value)
        self.assertEqual(result["verdict"], "REJECT")
        self.assertIn("UNEXPECTED_WRITE:case-1", result["reason_codes"])

    def test_evaluate_file_keeps_missing_evidence_fail_closed(self):
        value = suite(baseline=0.5, candidate=0.9)
        with tempfile.TemporaryDirectory(prefix="p2p-gepa-canary-") as raw:
            project = Path(raw)
            path = project / ".p2p" / "evals" / "suite.json"
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            result = gepa.evaluate_file(path)
        self.assertEqual(result["verdict"], "EVIDENCE_REQUIRED")
        self.assertEqual(result["reason_codes"], ["EVIDENCE_INTEGRITY_OR_COMPARABILITY_FAILED"])


if __name__ == "__main__":
    unittest.main()
