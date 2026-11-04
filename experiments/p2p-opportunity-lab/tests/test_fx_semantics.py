import unittest

from src.fx_semantics import resolve_fx


def quote(charges):
    return {"quote_id": "Q", "currency": "USD", "charges": charges}


def context():
    return {
        "as_of_date": "2026-09-16",
        "fx_rates": [
            {"from": "CNY", "to": "USD", "rate": "0.14", "source_ref": "fx:bank:2026-09-16", "as_of_date": "2026-09-16"}
        ],
    }


class FxSemanticsTests(unittest.TestCase):
    def test_direct_rate_converts_amount_and_preserves_audit(self):
        resolved, audit = resolve_fx(quote([
            {"line_id": "LOCAL", "name": "Local", "amount": 700, "basis": "PER_SHIPMENT", "currency": "CNY", "source_ref": "q:1"}
        ]), context())
        self.assertEqual(audit["status"], "READY")
        self.assertEqual(resolved["charges"][0]["amount"], "98.00")
        self.assertEqual(resolved["charges"][0]["currency"], "USD")
        self.assertEqual(audit["conversions"][0]["source_ref"], "fx:bank:2026-09-16")

    def test_minimum_amount_is_converted_with_same_rate(self):
        resolved, _ = resolve_fx(quote([
            {"name": "Handling", "amount": 1, "minimum_amount": 500, "basis": "PER_CBM", "currency": "CNY", "source_ref": "q:2"}
        ]), context())
        self.assertEqual(resolved["charges"][0]["minimum_amount"], "70.00")

    def test_missing_direct_rate_blocks(self):
        _, audit = resolve_fx(quote([
            {"name": "Local", "amount": 700, "basis": "PER_SHIPMENT", "currency": "VND", "source_ref": "q:3"}
        ]), context())
        self.assertEqual(audit["status"], "BLOCKED")
        self.assertEqual(audit["errors"][0]["type"], "FX_RATE_REQUIRED")

    def test_rate_without_source_is_not_accepted(self):
        ctx = {"fx_rates": [{"from": "CNY", "to": "USD", "rate": 0.14, "as_of_date": "2026-09-16"}]}
        _, audit = resolve_fx(quote([
            {"name": "Local", "amount": 700, "basis": "PER_SHIPMENT", "currency": "CNY", "source_ref": "q:4"}
        ]), ctx)
        self.assertEqual(audit["status"], "BLOCKED")
        self.assertTrue(any(x["type"] == "FX_SOURCE_REQUIRED" for x in audit["errors"]))

    def test_future_rate_is_rejected_against_comparison_date(self):
        ctx = {
            "as_of_date": "2026-09-16",
            "fx_rates": [{"from": "CNY", "to": "USD", "rate": 0.14, "source_ref": "fx:future", "as_of_date": "2026-09-17"}],
        }
        _, audit = resolve_fx(quote([
            {"name": "Local", "amount": 700, "basis": "PER_SHIPMENT", "currency": "CNY", "source_ref": "q:5"}
        ]), ctx)
        self.assertEqual(audit["status"], "BLOCKED")
        self.assertTrue(any(x["type"] == "FX_RATE_FROM_FUTURE" for x in audit["errors"]))

    def test_unselected_optional_cross_currency_addon_does_not_require_fx(self):
        resolved, audit = resolve_fx(quote([
            {"name": "Insurance", "amount": 700, "basis": "PER_SHIPMENT", "currency": "VND", "optional": True, "selected": False, "source_ref": "q:6"}
        ]), context())
        self.assertEqual(audit["status"], "READY")
        self.assertEqual(audit["conversions"], [])
        self.assertEqual(resolved["charges"][0]["currency"], "VND")


if __name__ == "__main__":
    unittest.main()
