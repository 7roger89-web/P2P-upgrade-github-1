import json
import unittest
from decimal import Decimal
from pathlib import Path

from src.validation_pipeline import compare_quotes_validated


FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "pilots"
    / "logistics-quote-comparison"
    / "fixtures"
    / "synthetic-validated-quote-set-02.json"
)


class ValidatedGoldenFixtureTests(unittest.TestCase):
    def test_full_validated_pipeline_preserves_evidence_and_ranking(self):
        data = json.loads(FIXTURE.read_text(encoding="utf-8"))
        result = compare_quotes_validated(data["quotes"], data["context"])
        expected = data["expected"]

        self.assertIsNone(result["decision_warning"])
        self.assertTrue(result["validated_pipeline"])
        self.assertTrue(result["comparison_basis"]["fx_applied"])
        self.assertEqual(result["required_charge_codes"], expected["required_charge_codes"])
        self.assertTrue(all(not row["unresolved_missing_codes"] for row in result["coverage_matrix"]))

        actual_ranking = [
            (item["quote_id"], Decimal(item["total"]))
            for item in result["ranking"]
        ]
        expected_ranking = [
            (item["quote_id"], Decimal(item["total"]))
            for item in expected["ranking"]
        ]
        self.assertEqual(actual_ranking, expected_ranking)

        fx_audit = next(item for item in result["fx_audit"] if item["quote_id"] == expected["fx_quote_id"])
        self.assertEqual(len(fx_audit["conversions"]), 1)
        conversion = fx_audit["conversions"][0]
        self.assertEqual(conversion["from"], expected["fx_from"])
        self.assertEqual(conversion["to"], expected["fx_to"])
        self.assertEqual(Decimal(conversion["converted_amount"]), Decimal(expected["fx_converted_amount"]))

        percentage_audit = next(
            item for item in result["percentage_audit"]
            if item["quote_id"] == expected["percentage_quote_id"]
        )
        resolution = next(
            item for item in percentage_audit["resolutions"]
            if item["line_id"] == expected["percentage_line_id"]
        )
        self.assertEqual(Decimal(resolution["base_total"]), Decimal(expected["percentage_base_total"]))
        self.assertEqual(Decimal(resolution["resolved_total"]), Decimal(expected["percentage_resolved_total"]))

        route_alias = next(
            item for item in result["route_alias_audit"]
            if item["quote_id"] == expected["aliased_quote_id"]
        )
        origin_alias = next(item for item in route_alias["resolutions"] if item["field"] == "origin")
        self.assertEqual(origin_alias["raw"], expected["aliased_origin_raw"])
        self.assertEqual(origin_alias["canonical"], expected["aliased_origin_canonical"])

        val_a = next(item for item in result["semantic_audit"] if item["quote_id"] == "VAL-A")
        self.assertEqual([item["line"] for item in val_a["optional_excluded"]], [5])


if __name__ == "__main__":
    unittest.main()
