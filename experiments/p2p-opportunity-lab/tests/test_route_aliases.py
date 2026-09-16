import unittest

from src.concierge_engine import compare_quotes


def quote(qid, origin):
    return {
        "quote_id": qid,
        "provider": qid,
        "currency": "USD",
        "route": {"origin": origin, "destination": "Hai Phong"},
        "equipment": "40HC",
        "charges": [
            {"name": "Freight", "amount": 1000, "basis": "PER_CONTAINER", "source_ref": f"{qid}:1"},
            {"name": "THC", "amount": 100, "basis": "PER_SHIPMENT", "source_ref": f"{qid}:2"},
        ],
    }


class RouteAliasTests(unittest.TestCase):
    def test_evidenced_location_alias_restores_comparability(self):
        result = compare_quotes(
            [quote("A", "Shanghai"), quote("B", "CNSHA")],
            {
                "containers": 1,
                "shipments": 1,
                "location_aliases": {
                    "CNSHA": {"canonical": "SHANGHAI", "source_ref": "UNLOCODE:CNSHA"}
                },
            },
        )
        self.assertEqual(len(result["ranking"]), 2)
        self.assertEqual(result["comparison_basis"]["route"]["origin"], "SHANGHAI")
        self.assertEqual(result["route_alias_audit"][0]["quote_id"], "B")
        self.assertEqual(
            result["route_alias_audit"][0]["resolutions"][0]["source_ref"],
            "UNLOCODE:CNSHA",
        )

    def test_alias_without_source_does_not_merge_routes(self):
        result = compare_quotes(
            [quote("A", "Shanghai"), quote("B", "CNSHA")],
            {
                "containers": 1,
                "shipments": 1,
                "location_aliases": {
                    "CNSHA": {"canonical": "SHANGHAI", "source_ref": ""}
                },
            },
        )
        self.assertEqual(len(result["ranking"]), 1)
        self.assertEqual(result["route_alias_audit"], [])
        self.assertIn("ROUTE_MISMATCH", result["excluded"][0]["reasons"])


if __name__ == "__main__":
    unittest.main()
