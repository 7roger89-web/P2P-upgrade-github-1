import unittest

from src.portfolio_validation_pipeline import compare_fcl_portfolios_validated


def provider(name, freight20, freight40, local_amount, local_currency="USD"):
    return {
        "quote_set_id": name,
        "provider": name,
        "currency": "USD",
        "route": {"origin": "Shanghai", "destination": "Hai Phong"},
        "shared_charges": [
            {"line_id": "LOCAL", "name": "Local Handling", "amount": local_amount, "basis": "PER_SHIPMENT", "scope": "ORIGIN", "currency": local_currency, "source_ref": f"{name}:local"}
        ],
        "offers": [
            {"offer_id": "20", "equipment": "20GP", "charges": [
                {"line_id": "F20", "name": "Freight", "amount": freight20, "basis": "PER_CONTAINER", "scope": "MAIN", "source_ref": f"{name}:20"}
            ]},
            {"offer_id": "40", "equipment": "40HC", "charges": [
                {"line_id": "F40", "name": "Freight", "amount": freight40, "basis": "PER_CONTAINER", "scope": "MAIN", "source_ref": f"{name}:40"}
            ]},
        ],
    }


def context():
    return {
        "route": {"origin": "Shanghai", "destination": "Hai Phong"},
        "currency": "USD",
        "equipment_requirements": {"20GP": 2, "40HC": 1},
        "shipments": 1,
        "bl_count": 1,
        "as_of_date": "2026-09-16",
        "fx_rates": [
            {"from": "CNY", "to": "USD", "rate": "0.14", "source_ref": "fx:bank", "as_of_date": "2026-09-16"}
        ],
    }


class FxPortfolioValidationPipelineTests(unittest.TestCase):
    def test_shared_cross_currency_charge_is_converted_once(self):
        a = provider("A", 500, 900, 700, "CNY")
        b = provider("B", 500, 900, 100, "USD")
        result = compare_fcl_portfolios_validated([a, b], context())
        self.assertTrue(result["fx_applied"])
        a_row = next(x for x in result["portfolios"] if x["quote_set_id"] == "A")
        self.assertEqual(a_row["shared_priced"]["total"], "98.00")
        self.assertEqual(result["ranking"][0]["quote_set_id"], "A")

    def test_provider_missing_required_fx_is_excluded_only_for_that_provider(self):
        a = provider("A", 500, 900, 700, "VND")
        b = provider("B", 500, 900, 100, "USD")
        result = compare_fcl_portfolios_validated([a, b], context())
        self.assertEqual([x["quote_set_id"] for x in result["ranking"]], ["B"])
        a_excluded = next(x for x in result["excluded"] if x["quote_set_id"] == "A")
        self.assertTrue(any("SHARED:FX:FX_RATE_REQUIRED" in reason for reason in a_excluded["reasons"]))


if __name__ == "__main__":
    unittest.main()
