import unittest

from src.portfolio_semantics import compare_fcl_portfolios


def provider(name, freight20, freight40, shared_doc=50):
    return {
        "quote_set_id": name,
        "provider": name,
        "currency": "USD",
        "route": {"origin": "Shanghai", "destination": "Hai Phong"},
        "shared_charges": [
            {"name": "DOC", "amount": shared_doc, "basis": "PER_BL", "scope": "MAIN", "source_ref": f"{name}:doc"}
        ],
        "offers": [
            {
                "offer_id": "20",
                "equipment": "20GP",
                "charges": [
                    {"name": "Freight", "amount": freight20, "basis": "PER_CONTAINER", "scope": "MAIN", "source_ref": f"{name}:20"}
                ],
            },
            {
                "offer_id": "40",
                "equipment": "40HQ",
                "charges": [
                    {"name": "Freight", "amount": freight40, "basis": "PER_CONTAINER", "scope": "MAIN", "source_ref": f"{name}:40"}
                ],
            },
        ],
    }


class PortfolioSemanticsTests(unittest.TestCase):
    def context(self):
        return {
            "route": {"origin": "Shanghai", "destination": "Hai Phong"},
            "currency": "USD",
            "equipment_requirements": {"20GP": 2, "40HC": 1},
            "shipments": 1,
            "bl_count": 1,
            "as_of_date": "2026-09-16",
        }

    def test_multi_equipment_portfolio_ranks_total_quote(self):
        a = provider("A", 500, 900)
        b = provider("B", 480, 950)
        result = compare_fcl_portfolios([a, b], self.context())
        self.assertEqual(result["ranking"][0]["quote_set_id"], "A")
        self.assertEqual(result["ranking"][0]["total"], "1950")
        self.assertEqual(result["ranking"][1]["total"], "1960")

    def test_missing_required_equipment_excludes_provider(self):
        a = provider("A", 500, 900)
        b = provider("B", 480, 950)
        b["offers"] = [b["offers"][0]]
        result = compare_fcl_portfolios([a, b], self.context())
        self.assertEqual(len(result["ranking"]), 1)
        self.assertIn("MISSING_EQUIPMENT:40HC", result["excluded"][0]["reasons"])

    def test_duplicate_offer_for_same_canonical_equipment_is_ambiguous(self):
        a = provider("A", 500, 900)
        b = provider("B", 480, 950)
        b["offers"].append({
            "offer_id": "40b",
            "equipment": "40HC",
            "charges": [
                {"name": "Freight", "amount": 930, "basis": "PER_CONTAINER", "scope": "MAIN", "source_ref": "B:40b"}
            ],
        })
        result = compare_fcl_portfolios([a, b], self.context())
        self.assertIn("AMBIGUOUS_EQUIPMENT_OFFER:40HC", result["excluded"][0]["reasons"])

    def test_per_shipment_charge_inside_equipment_offer_is_blocked(self):
        a = provider("A", 500, 900)
        b = provider("B", 480, 950)
        b["offers"][0]["charges"].append({
            "name": "DOC",
            "amount": 50,
            "basis": "PER_SHIPMENT",
            "scope": "MAIN",
            "source_ref": "B:bad-doc",
        })
        result = compare_fcl_portfolios([a, b], self.context())
        reasons = result["excluded"][0]["reasons"]
        self.assertTrue(any("unsupported basis PER_SHIPMENT" in item for item in reasons))

    def test_equipment_aliases_in_requirements_are_combined(self):
        context = self.context()
        context["equipment_requirements"] = {"40HQ": 1, "40HC": 1}
        a = provider("A", 500, 900)
        b = provider("B", 480, 950)
        result = compare_fcl_portfolios([a, b], context)
        self.assertEqual(result["requirements"], {"40HC": 2})
        self.assertEqual(result["ranking"][0]["total"], "1850")


if __name__ == "__main__":
    unittest.main()
