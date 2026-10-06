import unittest

from src.validation_pipeline import compare_quotes_validated


def quote(qid, freight, local_amount, local_currency="USD"):
    return {
        "quote_id": qid,
        "provider": qid,
        "currency": "USD",
        "route": {"origin": "Shanghai", "destination": "Hai Phong"},
        "equipment": "40HC",
        "charges": [
            {"line_id": "F", "name": "Freight", "amount": freight, "basis": "PER_SHIPMENT", "scope": "MAIN", "source_ref": f"{qid}:f"},
            {"line_id": "LOCAL", "name": "Local Handling", "amount": local_amount, "basis": "PER_SHIPMENT", "scope": "ORIGIN", "currency": local_currency, "source_ref": f"{qid}:local"},
        ],
    }


class FxValidationPipelineTests(unittest.TestCase):
    def test_fx_resolves_before_core_comparison(self):
        a = quote("A", 1000, 700, "CNY")
        b = quote("B", 995, 100, "USD")
        result = compare_quotes_validated(
            [a, b],
            {
                "shipments": 1,
                "as_of_date": "2026-09-16",
                "fx_rates": [
                    {"from": "CNY", "to": "USD", "rate": "0.14", "source_ref": "fx:bank", "as_of_date": "2026-09-16"}
                ],
            },
        )
        self.assertTrue(result["validated_pipeline"])
        self.assertTrue(result["comparison_basis"]["fx_applied"])
        self.assertEqual(result["ranking"][0]["quote_id"], "B")
        self.assertEqual(result["ranking"][0]["total"], "1095")
        self.assertEqual(result["ranking"][1]["total"], "1098.00")

    def test_missing_fx_rate_blocks_before_percentage_or_ranking(self):
        a = quote("A", 1000, 700, "CNY")
        b = quote("B", 995, 100, "USD")
        result = compare_quotes_validated([a, b], {"shipments": 1})
        self.assertEqual(result["ranking"], [])
        self.assertEqual(result["decision_warning"], "UNRESOLVED_FX_SEMANTICS")
        self.assertEqual(result["comparison_basis"]["selection_mode"], "FX_GUARD_BLOCKED")


if __name__ == "__main__":
    unittest.main()
