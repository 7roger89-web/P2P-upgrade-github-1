import json
import unittest
from copy import deepcopy
from pathlib import Path

from src.validation_pipeline import compare_quotes_validated


FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "pilots"
    / "logistics-quote-comparison"
    / "fixtures"
    / "synthetic-validated-quote-set-02.json"
)


class DirtyCommercialAdversarialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.clean = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def _run(self, mutator):
        data = deepcopy(self.clean)
        mutator(data)
        return compare_quotes_validated(data["quotes"], data["context"])

    def test_expired_quote_is_not_ranked_as_current_offer(self):
        def mutate(data):
            val_a = next(q for q in data["quotes"] if q["quote_id"] == "VAL-A")
            val_a["valid_to"] = "2026-09-15"

        result = self._run(mutate)

        self.assertEqual(
            [(item["quote_id"], item["total"]) for item in result["ranking"]],
            [("VAL-B", "1940")],
        )
        expired = next(item for item in result["excluded"] if item["quote_id"] == "VAL-A")
        self.assertIn("EXPIRED", expired["reasons"])
        self.assertEqual(result["decision_warning"], "INSUFFICIENT_COMPLETE_COMPARABLE_QUOTES")

    def test_malformed_validity_date_is_excluded_not_guessed(self):
        def mutate(data):
            val_a = next(q for q in data["quotes"] if q["quote_id"] == "VAL-A")
            val_a["valid_to"] = "30/09/2026"

        result = self._run(mutate)

        malformed = next(item for item in result["excluded"] if item["quote_id"] == "VAL-A")
        self.assertIn("INVALID_VALIDITY_DATE", malformed["reasons"])
        self.assertEqual(
            [(item["quote_id"], item["total"]) for item in result["ranking"]],
            [("VAL-B", "1940")],
        )
        self.assertEqual(result["decision_warning"], "INSUFFICIENT_COMPLETE_COMPARABLE_QUOTES")

    def test_unresolved_subject_to_term_makes_quote_unrankable(self):
        def mutate(data):
            val_a = next(q for q in data["quotes"] if q["quote_id"] == "VAL-A")
            val_a["conditions"] = [
                {
                    "text": "Subject to carrier space and final approval",
                    "source_ref": "a:p1:term1",
                    "resolved": False,
                }
            ]

        result = self._run(mutate)

        self.assertEqual(
            [(item["quote_id"], item["total"]) for item in result["ranking"]],
            [("VAL-B", "1940")],
        )
        val_a = next(item for item in result["priced_quotes"] if item["quote_id"] == "VAL-A")
        self.assertFalse(val_a["complete"])
        self.assertEqual(len(val_a["unresolved_conditions"]), 1)
        self.assertIn("Subject to carrier space", val_a["unresolved_conditions"][0]["text"])
        self.assertEqual(result["decision_warning"], "INSUFFICIENT_COMPLETE_COMPARABLE_QUOTES")

    def test_claimed_resolution_without_evidence_stays_unresolved(self):
        def mutate(data):
            val_a = next(q for q in data["quotes"] if q["quote_id"] == "VAL-A")
            val_a["conditions"] = [
                {
                    "text": "Subject to carrier space and final approval",
                    "source_ref": "a:p1:term1",
                    "resolved": True,
                    "resolution_source_ref": "",
                    "resolution_note": "sales said it should be okay",
                }
            ]

        result = self._run(mutate)

        self.assertEqual(
            [(item["quote_id"], item["total"]) for item in result["ranking"]],
            [("VAL-B", "1940")],
        )
        val_a = next(item for item in result["priced_quotes"] if item["quote_id"] == "VAL-A")
        self.assertFalse(val_a["complete"])
        self.assertEqual(len(val_a["resolved_conditions"]), 0)
        self.assertEqual(len(val_a["unresolved_conditions"]), 1)
        self.assertEqual(result["decision_warning"], "INSUFFICIENT_COMPLETE_COMPARABLE_QUOTES")


if __name__ == "__main__":
    unittest.main()
