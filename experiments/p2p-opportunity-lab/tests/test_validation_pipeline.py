import unittest

from src.validation_pipeline import compare_quotes_validated


def quote(qid, freight, surcharge_ref="F"):
    return {
        "quote_id": qid,
        "provider": qid,
        "currency": "USD",
        "route": {"origin": "Shanghai", "destination": "Hai Phong"},
        "equipment": "40HC",
        "charges": [
            {"line_id": "F", "name": "Freight", "amount": freight, "basis": "PER_SHIPMENT", "scope": "MAIN", "source_ref": f"{qid}:f"},
            {"line_id": "BAF", "name": "BAF", "percentage_rate": 5, "percentage_of_line_ids": [surcharge_ref], "scope": "MAIN", "source_ref": f"{qid}:baf"},
        ],
    }


class ValidationPipelineTests(unittest.TestCase):
    def test_percentage_is_resolved_before_guarded_comparison(self):
        result = compare_quotes_validated(
            [quote("A", 1000), quote("B", 900)],
            {"shipments": 1},
        )
        self.assertTrue(result["validated_pipeline"])
        self.assertEqual(result["ranking"][0]["quote_id"], "B")
        self.assertEqual(result["ranking"][0]["total"], "945")
        self.assertEqual(result["percentage_audit"][1]["resolutions"][0]["resolved_total"], "45")

    def test_bad_percentage_reference_blocks_before_ranking(self):
        result = compare_quotes_validated(
            [quote("A", 1000, surcharge_ref="MISSING"), quote("B", 900)],
            {"shipments": 1},
        )
        self.assertEqual(result["ranking"], [])
        self.assertEqual(result["decision_warning"], "UNRESOLVED_PERCENTAGE_SEMANTICS")
        self.assertEqual(result["comparison_basis"]["selection_mode"], "PERCENTAGE_GUARD_BLOCKED")


if __name__ == "__main__":
    unittest.main()
