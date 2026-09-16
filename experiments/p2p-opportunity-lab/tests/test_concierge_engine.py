import unittest

from src.concierge_engine import compare_quotes, normalize_quote, price_quote


def quote(qid, currency="USD", equipment="40HC", charges=None):
    return {
        "quote_id": qid,
        "provider": qid,
        "currency": currency,
        "route": {"origin": "Shanghai", "destination": "Hai Phong"},
        "equipment": equipment,
        "charges": charges or [
            {"name": "Ocean Freight", "amount": 1000, "basis": "PER_CONTAINER", "source_ref": "p1:r3"},
            {"name": "THC", "amount": 100, "basis": "PER_SHIPMENT", "source_ref": "p1:r4"},
        ],
    }


class ConciergeEngineTests(unittest.TestCase):
    def test_per_container_math_and_ranking(self):
        result = compare_quotes(
            [
                quote("A"),
                quote("B", charges=[
                    {"name": "Ocean Freight", "amount": 900, "basis": "PER_CONTAINER", "source_ref": "p2:r1"},
                    {"name": "THC", "amount": 150, "basis": "PER_SHIPMENT", "source_ref": "p2:r2"},
                ]),
            ],
            {"containers": 2, "shipments": 1, "bl_count": 1, "weight_kg": 0, "cbm": 0},
        )
        self.assertEqual(result["ranking"][0]["quote_id"], "B")
        self.assertEqual(result["ranking"][0]["total"], "1950")

    def test_unknown_basis_blocks_ranking_for_that_quote(self):
        bad = quote("B", charges=[
            {"name": "Mystery fee", "amount": 20, "basis": "UNKNOWN", "source_ref": "p2:r9"}
        ])
        result = compare_quotes([quote("A"), bad], {"containers": 1, "shipments": 1})
        self.assertEqual(len(result["ranking"]), 0)
        self.assertFalse(result["priced_quotes"][1]["complete"])

    def test_currency_mismatch_excluded_no_silent_fx(self):
        result = compare_quotes([quote("A"), quote("B", currency="CNY")], {"containers": 1, "shipments": 1})
        self.assertEqual(result["excluded"][0]["reasons"], ["CURRENCY_MISMATCH"])
        self.assertFalse(result["comparison_basis"]["fx_applied"])

    def test_missing_source_ref_marks_uncertain(self):
        q = quote("A", charges=[{"name": "THC", "amount": 100, "basis": "PER_SHIPMENT"}])
        normalized = normalize_quote(q)
        self.assertTrue(normalized["charges"][0]["uncertain"])
        priced = price_quote(normalized, {"shipments": 1})
        self.assertFalse(priced["complete"])

    def test_included_charge_contributes_zero_and_preserves_audit(self):
        q = quote("A", charges=[
            {"name": "DOC", "included": True, "basis": "INCLUDED", "source_ref": "p1:r5"},
            {"name": "Freight", "amount": 1000, "basis": "PER_SHIPMENT", "source_ref": "p1:r1"},
        ])
        priced = price_quote(normalize_quote(q), {"shipments": 1})
        self.assertEqual(priced["total"], "1000")
        self.assertEqual(priced["audit"][0]["status"], "INCLUDED")

    def test_missing_charge_blocks_false_cheapest_ranking(self):
        full = quote("A", charges=[
            {"name": "Freight", "amount": 1000, "basis": "PER_SHIPMENT", "source_ref": "a:1"},
            {"name": "THC", "amount": 100, "basis": "PER_SHIPMENT", "source_ref": "a:2"},
            {"name": "DOC", "amount": 50, "basis": "PER_BL", "source_ref": "a:3"},
        ])
        deceptively_low = quote("B", charges=[
            {"name": "Freight", "amount": 900, "basis": "PER_SHIPMENT", "source_ref": "b:1"},
            {"name": "THC", "amount": 100, "basis": "PER_SHIPMENT", "source_ref": "b:2"},
        ])
        result = compare_quotes([full, deceptively_low], {"shipments": 1, "bl_count": 1})
        self.assertEqual(result["ranking"][0]["quote_id"], "A")
        self.assertEqual(result["priced_quotes"][1]["coverage_gaps"], ["DOC"])
        self.assertFalse(result["priced_quotes"][1]["complete"])
        self.assertEqual(result["decision_warning"], "INSUFFICIENT_COMPLETE_COMPARABLE_QUOTES")

    def test_evidenced_coverage_resolution_can_restore_comparability(self):
        a = quote("A", charges=[
            {"name": "Freight", "amount": 1000, "basis": "PER_SHIPMENT", "source_ref": "a:1"},
            {"name": "DOC", "amount": 50, "basis": "PER_BL", "source_ref": "a:2"},
        ])
        b = quote("B", charges=[
            {"name": "Freight", "amount": 900, "basis": "PER_SHIPMENT", "source_ref": "b:1"},
        ])
        context = {
            "shipments": 1,
            "bl_count": 1,
            "coverage_resolutions": {
                "B": {"DOC": {"status": "INCLUDED", "source_ref": "b:terms:doc-included"}}
            },
        }
        result = compare_quotes([a, b], context)
        self.assertEqual([x["quote_id"] for x in result["ranking"]], ["B", "A"])
        self.assertEqual(result["priced_quotes"][1]["coverage_gaps"], [])
        self.assertEqual(result["priced_quotes"][1]["coverage_resolutions"][0]["status"], "INCLUDED")

    def test_unproven_coverage_resolution_does_not_restore_comparability(self):
        a = quote("A", charges=[
            {"name": "Freight", "amount": 1000, "basis": "PER_SHIPMENT", "source_ref": "a:1"},
            {"name": "PSS", "amount": 80, "basis": "PER_SHIPMENT", "source_ref": "a:2"},
        ])
        b = quote("B", charges=[
            {"name": "Freight", "amount": 900, "basis": "PER_SHIPMENT", "source_ref": "b:1"},
        ])
        result = compare_quotes(
            [a, b],
            {
                "shipments": 1,
                "coverage_resolutions": {
                    "B": {"PSS": {"status": "NOT_APPLICABLE", "source_ref": ""}}
                },
            },
        )
        self.assertEqual(result["priced_quotes"][1]["coverage_gaps"], ["PSS"])
        self.assertFalse(result["priced_quotes"][1]["complete"])


if __name__ == "__main__":
    unittest.main()
