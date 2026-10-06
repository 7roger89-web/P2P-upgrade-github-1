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

    def test_missing_charge_coverage_blocks_false_cheapest_provider(self):
        a = provider("A", 500, 900)
        b = provider("B", 480, 850)
        a["offers"][1]["charges"].append({
            "name": "THC", "amount": 100, "basis": "PER_CONTAINER", "scope": "MAIN", "source_ref": "A:40:thc"
        })
        result = compare_fcl_portfolios([a, b], self.context())
        self.assertEqual([row["quote_set_id"] for row in result["ranking"]], ["A"])
        b_excluded = next(row for row in result["excluded"] if row["quote_set_id"] == "B")
        self.assertIn("COVERAGE_GAP:40HC:MAIN::THC", b_excluded["reasons"])
        self.assertEqual(result["decision_warning"], "INSUFFICIENT_COMPLETE_PROVIDER_PORTFOLIOS")

    def test_evidenced_bundle_restores_equipment_coverage(self):
        a = provider("A", 500, 900)
        b = provider("B", 480, 930)
        a["offers"][1]["charges"].append({
            "name": "THC", "included": True, "basis": "INCLUDED", "scope": "MAIN", "source_ref": "A:40:thc-included"
        })
        b["offers"][1]["charges"] = [{
            "name": "All-in freight",
            "amount": 930,
            "basis": "PER_CONTAINER",
            "scope": "MAIN",
            "source_ref": "B:40:all-in",
            "bundle_includes": ["Freight", "THC"],
            "bundle_primary_code": "Freight",
        }]
        result = compare_fcl_portfolios([a, b], self.context())
        self.assertEqual(len(result["ranking"]), 2)
        self.assertIn("MAIN::THC", result["required_coverage"]["40HC"])

    def test_unresolved_offer_condition_blocks_provider_ranking(self):
        a = provider("A", 500, 900)
        b = provider("B", 480, 850)
        b["offers"][1]["conditions"] = [{
            "text": "subject to PSS confirmation",
            "source_ref": "B:40:terms",
            "resolved": False,
        }]
        result = compare_fcl_portfolios([a, b], self.context())
        self.assertEqual([row["quote_set_id"] for row in result["ranking"]], ["A"])
        b_excluded = next(row for row in result["excluded"] if row["quote_set_id"] == "B")
        self.assertIn("40HC:INCOMPLETE_OFFER", b_excluded["reasons"])

    def test_expired_required_equipment_offer_excludes_provider(self):
        a = provider("A", 500, 900)
        b = provider("B", 480, 850)
        b["offers"][1]["valid_to"] = "2026-08-31"
        result = compare_fcl_portfolios([a, b], self.context())
        self.assertEqual([row["quote_set_id"] for row in result["ranking"]], ["A"])
        b_excluded = next(row for row in result["excluded"] if row["quote_set_id"] == "B")
        self.assertIn("40HC:EXPIRED", b_excluded["reasons"])

    def test_evidenced_portfolio_coverage_resolution_restores_provider(self):
        a = provider("A", 500, 900)
        b = provider("B", 480, 850)
        a["offers"][1]["charges"].append({
            "name": "THC", "amount": 100, "basis": "PER_CONTAINER", "scope": "MAIN", "source_ref": "A:40:thc"
        })
        context = self.context()
        context["portfolio_coverage_resolutions"] = {
            "B": {
                "40HC": {
                    "MAIN::THC": {"status": "INCLUDED", "source_ref": "B:40:terms:thc-included"}
                }
            }
        }
        result = compare_fcl_portfolios([a, b], context)
        self.assertEqual(len(result["ranking"]), 2)
        b_row = next(row for row in result["coverage_matrix"] if row["quote_set_id"] == "B")
        b_40 = next(row for row in b_row["buckets"] if row["bucket"] == "40HC")
        self.assertEqual(b_40["unresolved_missing_codes"], [])
        self.assertEqual(b_40["resolved_missing_codes"][0]["status"], "INCLUDED")


if __name__ == "__main__":
    unittest.main()
