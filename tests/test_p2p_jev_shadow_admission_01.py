"""Regression checks for P2P_JEV_SHADOW_ADMISSION_01 (Issue #282).

These tests certify only the research harness and frozen admission boundary.
They do not certify Jev provider quality and they never call the network.
"""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
from unittest import mock
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "p2p_jev_shadow_admission.py"
FIXTURE = ROOT / "tests" / "fixtures" / "p2p_jev_shadow_admission_01.json"


def _load_module():
    spec = importlib.util.spec_from_file_location("p2p_jev_shadow_admission", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class JevShadowAdmissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.mod = _load_module()
        cls.fixture = cls.mod.load_fixture()

    def test_fixture_is_frozen_before_live_results_and_bounded(self) -> None:
        self.assertTrue(self.fixture["frozen_before_live_results"])
        self.assertEqual(self.fixture["frozen_against_main"],
                         "577c0eba7578113438e5222eca232015806de5d2")
        self.assertEqual(len(self.fixture["cases"]), 30)
        groups = {case["group"] for case in self.fixture["cases"]}
        self.assertEqual(
            groups,
            {
                "SAFE_READ",
                "REVERSIBLE_MUTATION",
                "CRITICAL",
                "AMBIGUOUS",
                "ADVERSARIAL",
            },
        )
        self.assertEqual(
            self.fixture["authority_boundary"],
            "JEV_OUTPUT_IS_OBSERVATION_ONLY; deterministic P2P policy remains authoritative; no tool execution is permitted by this fixture.",
        )

    def test_deterministic_baseline_matches_all_frozen_cases(self) -> None:
        result = self.mod.validate_deterministic_baseline(self.fixture)
        self.assertEqual(result["status"], "PASS", result)
        self.assertEqual(result["case_count"], 30)
        self.assertEqual(result["mismatches"], [])
        self.assertGreater(result["lane_counts"].get("CRITICAL", 0), 0)
        self.assertGreater(result["lane_counts"].get("STANDARD", 0), 0)
        self.assertGreater(result["lane_counts"].get("FAST", 0), 0)

    def test_provider_state_projection_is_minimal_and_sanitized_by_shape(self) -> None:
        allowed = set(self.mod.ALLOWED_STATE_KEYS)
        for case in self.fixture["cases"]:
            state = self.mod.sanitized_state(case)
            self.assertEqual(set(state), allowed)
            request = self.mod.build_request(self.fixture, case)
            self.assertEqual(set(request), {"model", "state", "questions"})
            self.assertNotIn("baseline", request)
            self.assertNotIn("expected", request)
            self.assertNotIn("source_ref", request)
            self.assertNotIn('"owner_gate":', json.dumps(request).lower())
            self.assertNotIn("api_key", json.dumps(request).lower())

    def test_request_contains_three_atomic_observation_questions(self) -> None:
        request = self.mod.build_request(self.fixture, self.fixture["cases"][0])
        questions = request["questions"]
        self.assertEqual(
            {name: question["type"] for name, question in questions.items()},
            {
                "destructive_intent": "noul",
                "action_class": "choice",
                "ambiguity": "score",
            },
        )
        self.assertEqual(len(questions["ambiguity"]["criteria"]), 5)
        self.assertIn("UNKNOWN", questions["action_class"]["criteria"])

    def test_choice_order_challenge_changes_only_option_order(self) -> None:
        case = self.fixture["cases"][0]
        normal = self.mod.build_request(self.fixture, case)
        reversed_request = self.mod.build_request(
            self.fixture, case, reverse_choice=True
        )
        self.assertEqual(normal["state"], reversed_request["state"])
        self.assertEqual(
            list(normal["questions"]["action_class"]["criteria"]),
            list(reversed(reversed_request["questions"]["action_class"]["criteria"])),
        )
        normal_without_choice = dict(normal["questions"])
        reverse_without_choice = dict(reversed_request["questions"])
        normal_without_choice.pop("action_class")
        reverse_without_choice.pop("action_class")
        self.assertEqual(normal_without_choice, reverse_without_choice)

    def test_rewrap_challenge_is_whitespace_only(self) -> None:
        case = self.fixture["cases"][0]
        normal = self.mod.build_request(self.fixture, case)
        wrapped = self.mod.build_request(self.fixture, case, rewrap=True)
        self.assertEqual(
            normal["state"]["proposal"].split(),
            wrapped["state"]["proposal"].split(),
        )
        for key in ("target", "environment", "note"):
            self.assertEqual(normal["state"][key], wrapped["state"][key])

    def test_live_mode_fails_closed_without_api_key_before_sdk_import(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(
                self.mod.JevShadowAdmissionError,
                r"LIVE_PROVIDER_EVIDENCE_NOT_RUN:TYPESAFE_API_KEY_MISSING",
            ):
                self.mod.run_live(self.fixture)

    def _perfect_live(self):
        rows = []
        for case in self.fixture["cases"]:
            expected = case["expected"]
            destructive = {
                "YES": 0.99,
                "NO": 0.01,
                "UNCERTAIN": 0.50,
            }[expected["destructive_intent"]]
            low, high = expected["ambiguity_score_range"]
            ambiguity = (float(low) + float(high)) / 2.0
            answers = {
                "destructive_intent": {
                    "type": "noul",
                    "noul": destructive,
                },
                "action_class": {
                    "type": "choice",
                    "choice": expected["action_class"],
                    "confidence": 1.0,
                    "probabilities": {expected["action_class"]: 1.0},
                },
                "ambiguity": {
                    "type": "score",
                    "score": ambiguity,
                    "confidence": 1.0,
                    "probabilities": {str(round(ambiguity)): 1.0},
                },
            }
            for variant in ("base", "choice_reversed", "rewrapped"):
                rows.append(
                    {
                        "case_id": case["id"],
                        "variant": variant,
                        "latency_ms": 100.0,
                        "answers": answers,
                    }
                )
        return {
            "schema": "p2p-jev-shadow-live-results/1",
            "task_id": self.fixture["task_id"],
            "permission_effect": "NONE",
            "execution_authority": "DETERMINISTIC_P2P_ONLY",
            "provider_control": "SHADOW_ONLY",
            "results": rows,
            "failures": [],
        }

    def test_perfect_shadow_evidence_can_only_reach_bounded_influence_candidate(self) -> None:
        grade = self.mod.grade_results(self.fixture, self._perfect_live())
        self.assertEqual(grade["verdict"], "CANDIDATE_FOR_BOUNDED_INFLUENCE_TEST")
        self.assertEqual(grade["permission_effect"], "NONE")
        self.assertEqual(grade["production_control"], "FORBIDDEN")
        self.assertTrue(all(grade["checks"].values()), grade)

    def test_critical_destructive_false_negative_forces_reject(self) -> None:
        live = self._perfect_live()
        critical_yes = next(
            case
            for case in self.fixture["cases"]
            if case["expected"]["critical"]
            and case["expected"]["destructive_intent"] == "YES"
        )
        row = next(
            item
            for item in live["results"]
            if item["case_id"] == critical_yes["id"] and item["variant"] == "base"
        )
        row["answers"] = dict(row["answers"])
        row["answers"]["destructive_intent"] = {"type": "noul", "noul": 0.01}
        grade = self.mod.grade_results(self.fixture, live)
        self.assertEqual(grade["verdict"], "REJECT")
        self.assertEqual(
            grade["metrics"]["critical_destructive_false_negatives"], 1
        )

    def test_research_ledger_records_bounded_reopen_without_runtime_admission(self) -> None:
        ledger = json.loads(
            (ROOT / "governance" / "research-adoption-ledger.json").read_text(
                encoding="utf-8"
            )
        )
        matches = [
            record for record in ledger["records"]
            if record.get("research_id") == "RA-EXT-104"
        ]
        self.assertEqual(len(matches), 1)
        record = matches[0]
        self.assertEqual(record["status"], "RESEARCHED")
        self.assertEqual(
            record["owner_decision_status"],
            "OWNER_SELECTED_BOUNDED_SHADOW_PROBE",
        )
        rejected = " ".join(record["rejected_ideas"]).lower()
        self.assertIn("global jev/openjev install", rejected)
        self.assertIn("permission authority", rejected)
        self.assertIn("mcp middleware", rejected)
        self.assertIn("live_provider_evidence_not_run", record["provenance_status"].lower())

    def test_human_projection_and_research_doc_preserve_authority_boundary(self) -> None:
        projection = (
            ROOT / "docs" / "RESEARCH-ADOPTION-LEDGER.md"
        ).read_text(encoding="utf-8")
        research = (
            ROOT / "docs" / "p2p-development" / "research"
            / "P2P-JEV-SHADOW-ADMISSION-01.md"
        ).read_text(encoding="utf-8")
        for marker in (
            "RA-EXT-104",
            "JEV_OBSERVATION != EXECUTION_AUTHORITY",
            "LIVE_PROVIDER_EVIDENCE=NOT_RUN",
        ):
            self.assertIn(marker, research)
        self.assertIn("RA-EXT-104", projection)
        self.assertIn("JEV_OBSERVATION != EXECUTION_AUTHORITY", projection)
        self.assertIn("production MCP", projection)

    def test_fixture_does_not_embed_a_real_secret_value(self) -> None:
        text = FIXTURE.read_text(encoding="utf-8")
        # Semantic words such as "API key" are valid benchmark content; common
        # literal credential forms are not.
        for marker in (
            "sk-",
            "ghp_",
            "github_pat_",
            "BEGIN PRIVATE KEY",
            "mongodb+srv://",
            "postgresql://",
        ):
            self.assertNotIn(marker, text)


if __name__ == "__main__":
    unittest.main()
