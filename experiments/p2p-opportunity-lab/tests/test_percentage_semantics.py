import unittest

from src.percentage_semantics import resolve_percentage_charges


def quote(charges):
    return {
        "quote_id": "Q",
        "currency": "USD",
        "charges": charges,
    }


class PercentageSemanticsTests(unittest.TestCase):
    def test_percentage_of_freight_resolves_to_fixed_contribution(self):
        resolved, audit = resolve_percentage_charges(quote([
            {"line_id": "F", "name": "Freight", "amount": 1000, "basis": "PER_SHIPMENT", "source_ref": "p:1"},
            {"line_id": "BAF", "name": "BAF", "percentage_rate": 5, "percentage_of_line_ids": ["F"], "basis": "UNKNOWN", "source_ref": "p:2"},
        ]), {"shipments": 1})
        self.assertEqual(audit["status"], "READY")
        self.assertEqual(resolved["charges"][1]["amount"], "50")
        self.assertEqual(resolved["charges"][1]["basis"], "PER_SHIPMENT")

    def test_percentage_uses_quantity_adjusted_base_total(self):
        resolved, audit = resolve_percentage_charges(quote([
            {"line_id": "F", "name": "Freight", "amount": 500, "basis": "PER_CONTAINER", "source_ref": "p:1"},
            {"line_id": "PSS", "name": "PSS", "percentage_rate": 5, "percentage_of_line_ids": ["F"], "source_ref": "p:2"},
        ]), {"shipments": 1, "containers": 2})
        self.assertEqual(audit["resolutions"][0]["base_total"], "1000")
        self.assertEqual(resolved["charges"][1]["amount"], "50")

    def test_percentage_can_reference_multiple_named_lines(self):
        resolved, audit = resolve_percentage_charges(quote([
            {"line_id": "F", "name": "Freight", "amount": 1000, "basis": "PER_SHIPMENT", "source_ref": "p:1"},
            {"line_id": "THC", "name": "THC", "amount": 100, "basis": "PER_SHIPMENT", "source_ref": "p:2"},
            {"line_id": "SUR", "name": "Surcharge", "percentage_rate": 5, "percentage_of_line_ids": ["F", "THC"], "source_ref": "p:3"},
        ]), {"shipments": 1})
        self.assertEqual(audit["resolutions"][0]["base_total"], "1100")
        self.assertEqual(resolved["charges"][2]["amount"], "55")

    def test_missing_base_line_blocks_resolution(self):
        _, audit = resolve_percentage_charges(quote([
            {"line_id": "SUR", "name": "Surcharge", "percentage_rate": 5, "percentage_of_line_ids": ["MISSING"], "source_ref": "p:3"},
        ]), {"shipments": 1})
        self.assertEqual(audit["status"], "BLOCKED")
        self.assertIn("unknown percentage base line_id", audit["errors"][0]["reason"])

    def test_percentage_cannot_reference_another_percentage(self):
        _, audit = resolve_percentage_charges(quote([
            {"line_id": "P1", "name": "P1", "percentage_rate": 5, "percentage_of_line_ids": ["F"], "source_ref": "p:1"},
            {"line_id": "F", "name": "Freight", "amount": 1000, "basis": "PER_SHIPMENT", "source_ref": "p:f"},
            {"line_id": "P2", "name": "P2", "percentage_rate": 2, "percentage_of_line_ids": ["P1"], "source_ref": "p:2"},
        ]), {"shipments": 1})
        self.assertEqual(audit["status"], "BLOCKED")
        self.assertTrue(any("cannot be used as another percentage base" in x.get("reason", "") for x in audit["errors"]))


if __name__ == "__main__":
    unittest.main()
