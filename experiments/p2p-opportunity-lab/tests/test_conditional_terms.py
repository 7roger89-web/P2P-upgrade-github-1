import unittest

from src.concierge_engine import compare_quotes


def quote(qid):
    return {
        "quote_id": qid,
        "provider": qid,
        "currency": "USD",
        "route": {"origin": "Shanghai", "destination": "Hai Phong"},
        "equipment": "40HC",
        "charges": [
            {"name": "Freight", "amount": 1000, "basis": "PER_CONTAINER", "source_ref": f"{qid}:r1"},
            {"name": "THC", "amount": 100, "basis": "PER_SHIPMENT", "source_ref": f"{qid}:r2"},
        ],
    }


class ConditionalTermsTests(unittest.TestCase):
    def test_unresolved_subject_to_term_blocks_ranking(self):
        a = quote("A")
        b = quote("B")
        b["conditions"] = [
            {"text": "PSS subject to carrier confirmation", "source_ref": "B:terms:1"}
        ]
        result = compare_quotes([a, b], {"containers": 1, "shipments": 1})
        self.assertEqual([item["quote_id"] for item in result["ranking"]], ["A"])
        self.assertFalse(result["priced_quotes"][1]["complete"])
        self.assertEqual(len(result["priced_quotes"][1]["unresolved_conditions"]), 1)

    def test_evidenced_resolution_restores_rankability(self):
        a = quote("A")
        b = quote("B")
        b["conditions"] = [
            {
                "text": "PSS subject to carrier confirmation",
                "source_ref": "B:terms:1",
                "resolved": True,
                "resolution_source_ref": "B:email:2",
                "resolution_note": "Carrier confirmed PSS is included for this validity window.",
            }
        ]
        result = compare_quotes([a, b], {"containers": 1, "shipments": 1})
        self.assertEqual(len(result["ranking"]), 2)
        self.assertTrue(result["priced_quotes"][1]["complete"])
        self.assertEqual(len(result["priced_quotes"][1]["resolved_conditions"]), 1)

    def test_claimed_resolution_without_evidence_stays_unresolved(self):
        a = quote("A")
        b = quote("B")
        b["conditions"] = [
            {
                "text": "Destination charges subject to confirmation",
                "source_ref": "B:terms:2",
                "resolved": True,
                "resolution_source_ref": "",
            }
        ]
        result = compare_quotes([a, b], {"containers": 1, "shipments": 1})
        self.assertFalse(result["priced_quotes"][1]["complete"])
        self.assertEqual(len(result["priced_quotes"][1]["unresolved_conditions"]), 1)


if __name__ == "__main__":
    unittest.main()
