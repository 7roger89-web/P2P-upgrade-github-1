import json
import unittest
from copy import deepcopy
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

    def test_validated_pipeline_is_invariant_to_quote_and_charge_order(self):
        data = json.loads(FIXTURE.read_text(encoding="utf-8"))
        expected = data["expected"]
        permuted_quotes = deepcopy(list(reversed(data["quotes"])))
        for quote in permuted_quotes:
            quote["charges"] = list(reversed(quote["charges"]))

        result = compare_quotes_validated(permuted_quotes, data["context"])

        self.assertIsNone(result["decision_warning"])
        self.assertTrue(result["comparison_basis"]["fx_applied"])
        self.assertEqual(result["required_charge_codes"], expected["required_charge_codes"])
        self.assertTrue(all(not row["unresolved_missing_codes"] for row in result["coverage_matrix"]))
        self.assertEqual(
            [(item["quote_id"], Decimal(item["total"])) for item in result["ranking"]],
            [(item["quote_id"], Decimal(item["total"])) for item in expected["ranking"]],
        )

        fx_audit = next(item for item in result["fx_audit"] if item["quote_id"] == expected["fx_quote_id"])
        self.assertEqual(len(fx_audit["conversions"]), 1)
        self.assertEqual(Decimal(fx_audit["conversions"][0]["converted_amount"]), Decimal(expected["fx_converted_amount"]))

        percentage_audit = next(
            item for item in result["percentage_audit"]
            if item["quote_id"] == expected["percentage_quote_id"]
        )
        resolution = next(
            item for item in percentage_audit["resolutions"]
            if item["line_id"] == expected["percentage_line_id"]
        )
        self.assertEqual(Decimal(resolution["resolved_total"]), Decimal(expected["percentage_resolved_total"]))

        val_a = next(item for item in result["semantic_audit"] if item["quote_id"] == "VAL-A")
        self.assertEqual(len(val_a["optional_excluded"]), 1)
        self.assertEqual(val_a["optional_excluded"][0]["code"], "INSURANCE")


if __name__ == "__main__":
    unittest.main()
