import unittest

from src.portfolio_validation_pipeline import compare_fcl_portfolios_validated


def provider(name, freight20, freight40, doc=50, baf_rate=5, bad_ref=False):
    base_ref = "MISSING" if bad_ref else "F20"
    return {
        "quote_set_id": name,
        "provider": name,
        "currency": "USD",
        "route": {"origin": "Shanghai", "destination": "Hai Phong"},
        "shared_charges": [
            {"line_id": "DOC", "name": "DOC", "amount": doc, "basis": "PER_BL", "scope": "MAIN", "source_ref": f"{name}:doc"}
        ],
        "offers": [
            {
                "offer_id": "20",
                "equipment": "20GP",
                "charges": [
                    {"line_id": "F20", "name": "Freight", "amount": freight20, "basis": "PER_CONTAINER", "scope": "MAIN", "source_ref": f"{name}:20:f"},
                    {"line_id": "BAF20", "name": "BAF", "percentage_rate": baf_rate, "percentage_of_line_ids": [base_ref], "basis": "UNKNOWN", "scope": "MAIN", "source_ref": f"{name}:20:baf"},
                ],
            },
            {
                "offer_id": "40",
                "equipment": "40HQ",
                "charges": [
                    {"line_id": "F40", "name": "Freight", "amount": freight40, "basis": "PER_CONTAINER", "scope": "MAIN", "source_ref": f"{name}:40:f"}
                ],
            },
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
    }


class PortfolioValidationPipelineTests(unittest.TestCase):
    def test_offer_percentage_respects_required_container_quantity(self):
        a = provider("A", 500, 900, doc=50)
        b = provider("B", 480, 950, doc=50)
        result = compare_fcl_portfolios_validated([a, b], context())
        self.assertTrue(result["validated_portfolio_pipeline"])
        self.assertEqual(result["ranking"][0]["quote_set_id"], "A")
        self.assertEqual(result["ranking"][0]["total"], "2000")
        self.assertEqual(result["ranking"][1]["total"], "2008")
        a_audit = next(x for x in result["percentage_audit"] if x["quote_set_id"] == "A")
        offer20 = next(x for x in a_audit["offers"] if x["equipment"] == "20GP")
        self.assertEqual(offer20["audit"]["resolutions"][0]["base_total"], "1000")
        self.assertEqual(offer20["audit"]["resolutions"][0]["resolved_total"], "50")

    def test_shared_percentage_is_priced_once_per_provider(self):
        a = provider("A", 500, 900, doc=100, baf_rate=0)
        b = provider("B", 500, 900, doc=80, baf_rate=0)
        for item in (a, b):
            doc_line = item["shared_charges"][0]
            item["shared_charges"].append({
                "line_id": "ADMIN",
                "name": "Admin Surcharge",
                "percentage_rate": 10,
                "percentage_of_line_ids": ["DOC"],
                "basis": "UNKNOWN",
                "scope": "MAIN",
                "source_ref": f"{item['quote_set_id']}:admin",
            })
        result = compare_fcl_portfolios_validated([a, b], context())
        a_portfolio = next(x for x in result["portfolios"] if x["quote_set_id"] == "A")
        b_portfolio = next(x for x in result["portfolios"] if x["quote_set_id"] == "B")
        self.assertEqual(a_portfolio["shared_priced"]["total"], "110")
        self.assertEqual(b_portfolio["shared_priced"]["total"], "88")

    def test_bad_named_percentage_base_excludes_provider(self):
        a = provider("A", 500, 900)
        b = provider("B", 480, 850, bad_ref=True)
        result = compare_fcl_portfolios_validated([a, b], context())
        self.assertEqual([x["quote_set_id"] for x in result["ranking"]], ["A"])
        b_excluded = next(x for x in result["excluded"] if x["quote_set_id"] == "B")
        self.assertTrue(any("PERCENTAGE_RESOLUTION_FAILED" in reason for reason in b_excluded["reasons"]))
        b_audit = next(x for x in result["percentage_audit"] if x["quote_set_id"] == "B")
        self.assertEqual(b_audit["status"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()
