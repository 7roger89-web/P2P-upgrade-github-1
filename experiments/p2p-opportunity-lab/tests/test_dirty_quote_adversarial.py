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


class DirtyQuoteAdversarialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.clean = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def _run(self, mutator):
        data = deepcopy(self.clean)
        mutator(data)
        return compare_quotes_validated(data["quotes"], data["context"])

    def test_missing_required_charge_cannot_create_false_cheapest_quote(self):
        def mutate(data):
            val_a = next(q for q in data["quotes"] if q["quote_id"] == "VAL-A")
            val_a["charges"] = [
                charge for charge in val_a["charges"] if charge.get("line_id") != "A-DOC"
            ]

        result = self._run(mutate)

        self.assertEqual(
            [(item["quote_id"], item["total"]) for item in result["ranking"]],
            [("VAL-B", "1940")],
        )
        self.assertEqual(result["decision_warning"], "INSUFFICIENT_COMPLETE_COMPARABLE_QUOTES")
        coverage = next(row for row in result["coverage_matrix"] if row["quote_id"] == "VAL-A")
        self.assertEqual(coverage["unresolved_missing_codes"], ["MAIN::DOC"])
        val_a = next(item for item in result["priced_quotes"] if item["quote_id"] == "VAL-A")
        self.assertFalse(val_a["complete"])

    def test_alias_duplicate_freight_is_blocked_before_ranking(self):
        def mutate(data):
            val_a = next(q for q in data["quotes"] if q["quote_id"] == "VAL-A")
            val_a["charges"].append(
                {
                    "line_id": "A-FRT-DUP",
                    "name": "Sea Freight",
                    "amount": 900,
                    "basis": "PER_CONTAINER",
                    "scope": "MAIN",
                    "source_ref": "a:p1:r1-duplicate",
                }
            )

        result = self._run(mutate)

        self.assertEqual(result["ranking"], [])
        self.assertEqual(result["decision_warning"], "UNRESOLVED_CHARGE_SEMANTICS")
        val_a = next(item for item in result["semantic_audit"] if item["quote_id"] == "VAL-A")
        duplicate = next(error for error in val_a["errors"] if error["type"] == "DUPLICATE_PRICED_CHARGE")
        self.assertEqual(duplicate["scope"], "MAIN")
        self.assertEqual(duplicate["code"], "FREIGHT")
        self.assertEqual(duplicate["lines"], [1, 6])

    def test_conflicting_direct_fx_sources_block_instead_of_picking_one(self):
        def mutate(data):
            data["context"]["fx_rates"].append(
                {
                    "from": "CNY",
                    "to": "USD",
                    "rate": "0.141",
                    "source_ref": "fx:alternate:cny-usd",
                    "as_of_date": "2026-09-16",
                }
            )

        result = self._run(mutate)

        self.assertEqual(result["ranking"], [])
        self.assertEqual(result["decision_warning"], "UNRESOLVED_FX_SEMANTICS")
        self.assertTrue(result["excluded"])
        for audit in result["fx_audit"]:
            error_types = {item["type"] for item in audit["errors"]}
            self.assertIn("AMBIGUOUS_FX_RATE", error_types)

    def test_missing_freight_provenance_makes_quote_unrankable(self):
        def mutate(data):
            val_a = next(q for q in data["quotes"] if q["quote_id"] == "VAL-A")
            freight = next(charge for charge in val_a["charges"] if charge.get("line_id") == "A-FRT")
            freight["source_ref"] = ""

        result = self._run(mutate)

        self.assertEqual(
            [(item["quote_id"], item["total"]) for item in result["ranking"]],
            [("VAL-B", "1940")],
        )
        self.assertEqual(result["decision_warning"], "INSUFFICIENT_COMPLETE_COMPARABLE_QUOTES")
        val_a = next(item for item in result["priced_quotes"] if item["quote_id"] == "VAL-A")
        self.assertFalse(val_a["complete"])
        self.assertTrue(any("uncertain extraction/provenance" in warning for warning in val_a["warnings"]))


if __name__ == "__main__":
    unittest.main()
