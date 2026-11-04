import unittest

from src.percentage_semantics import resolve_percentage_charges


def quote(selected_marker):
    optional = {
        "line_id": "INS",
        "name": "Insurance",
        "percentage_rate": 5,
        "percentage_of_line_ids": ["MISSING"],
        "basis": "UNKNOWN",
        "optional": True,
        "source_ref": "q:ins",
    }
    if selected_marker != "OMIT":
        optional["selected"] = selected_marker
    return {
        "quote_id": "Q",
        "currency": "USD",
        "charges": [
            {"line_id": "F", "name": "Freight", "amount": 1000, "basis": "PER_SHIPMENT", "source_ref": "q:f"},
            optional,
        ],
    }


class OptionalPercentageSemanticsTests(unittest.TestCase):
    def test_unselected_optional_percentage_is_deferred_not_resolved(self):
        resolved, audit = resolve_percentage_charges(quote(False), {"shipments": 1})
        self.assertEqual(audit["status"], "READY")
        self.assertEqual(audit["resolutions"], [])
        self.assertEqual(audit["deferred_optional"][0]["selected"], False)
        self.assertIn("percentage_rate", resolved["charges"][1])

    def test_ambiguous_optional_percentage_is_deferred_to_selection_guard(self):
        _, audit = resolve_percentage_charges(quote("OMIT"), {"shipments": 1})
        self.assertEqual(audit["status"], "READY")
        self.assertEqual(audit["deferred_optional"][0]["selected"], None)


if __name__ == "__main__":
    unittest.main()
