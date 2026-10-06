import unittest

from src.charge_semantics import compare_quotes_guarded, prepare_quote, scoped_code


def quote(qid, charges):
    return {
        "quote_id": qid,
        "provider": qid,
        "currency": "USD",
        "route": {"origin": "Shanghai", "destination": "Hai Phong"},
        "equipment": "40HC",
        "charges": charges,
    }


class ChargeSemanticsTests(unittest.TestCase):
    def test_scope_is_encoded_into_coverage_code(self):
        prepared, audit = prepare_quote(quote("A", [
            {"name": "THC", "amount": 100, "basis": "PER_SHIPMENT", "scope": "ORIGIN", "source_ref": "a:1"},
        ]))
        self.assertEqual(audit["status"], "READY")
        self.assertEqual(prepared["charges"][0]["name"], "ORIGIN::THC")
        self.assertEqual(scoped_code("THC", "DESTINATION"), "DESTINATION::THC")

    def test_exact_duplicate_priced_charge_blocks(self):
        _, audit = prepare_quote(quote("A", [
            {"name": "THC", "amount": 100, "basis": "PER_SHIPMENT", "scope": "ORIGIN", "source_ref": "a:1"},
            {"name": "Terminal Handling", "amount": 100, "basis": "PER_SHIPMENT", "scope": "ORIGIN", "source_ref": "a:2"},
        ]))
        self.assertEqual(audit["status"], "BLOCKED")
        self.assertEqual(audit["duplicate_groups"][0]["code"], "THC")

    def test_same_code_different_scope_is_not_duplicate(self):
        _, audit = prepare_quote(quote("A", [
            {"name": "THC", "amount": 100, "basis": "PER_SHIPMENT", "scope": "ORIGIN", "source_ref": "a:1"},
            {"name": "THC", "amount": 90, "basis": "PER_SHIPMENT", "scope": "DESTINATION", "source_ref": "a:2"},
        ]))
        self.assertEqual(audit["status"], "READY")
        self.assertEqual(audit["duplicate_groups"], [])

    def test_bundle_expands_coverage_without_double_counting_components(self):
        prepared, audit = prepare_quote(quote("A", [
            {
                "name": "All in",
                "amount": 1100,
                "basis": "PER_SHIPMENT",
                "scope": "MAIN",
                "bundle_includes": ["Freight", "THC", "DOC"],
                "bundle_primary_code": "Freight",
                "source_ref": "a:bundle",
            },
        ]))
        self.assertEqual(audit["status"], "READY")
        names = [item["name"] for item in prepared["charges"]]
        self.assertEqual(names, ["MAIN::FREIGHT", "MAIN::THC", "MAIN::DOC"])
        self.assertFalse(prepared["charges"][0].get("included", False))
        self.assertTrue(prepared["charges"][1]["included"])
        self.assertTrue(prepared["charges"][2]["included"])

    def test_bundle_plus_priced_component_blocks_double_count_risk(self):
        _, audit = prepare_quote(quote("A", [
            {
                "name": "All in",
                "amount": 1100,
                "basis": "PER_SHIPMENT",
                "scope": "MAIN",
                "bundle_includes": ["Freight", "THC"],
                "source_ref": "a:bundle",
            },
            {"name": "THC", "amount": 100, "basis": "PER_SHIPMENT", "scope": "MAIN", "source_ref": "a:thc"},
        ]))
        self.assertEqual(audit["status"], "BLOCKED")
        self.assertTrue(any(x["type"] == "BUNDLE_COMPONENT_DOUBLE_COUNT_RISK" for x in audit["errors"]))

    def test_unselected_optional_charge_is_excluded_from_pricing_and_coverage(self):
        prepared, audit = prepare_quote(quote("A", [
            {"name": "Freight", "amount": 1000, "basis": "PER_SHIPMENT", "source_ref": "a:f"},
            {"name": "Insurance", "amount": 50, "basis": "PER_SHIPMENT", "optional": True, "selected": False, "source_ref": "a:ins"},
        ]))
        self.assertEqual(audit["status"], "READY")
        self.assertEqual(len(prepared["charges"]), 1)
        self.assertEqual(audit["optional_excluded"][0]["code"], "INSURANCE")

    def test_selected_optional_charge_remains_priced(self):
        prepared, audit = prepare_quote(quote("A", [
            {"name": "Freight", "amount": 1000, "basis": "PER_SHIPMENT", "source_ref": "a:f"},
            {"name": "Insurance", "amount": 50, "basis": "PER_SHIPMENT", "optional": True, "selected": True, "source_ref": "a:ins"},
        ]))
        self.assertEqual(audit["status"], "READY")
        self.assertEqual(len(prepared["charges"]), 2)

    def test_optional_charge_requires_explicit_selection(self):
        _, audit = prepare_quote(quote("A", [
            {"name": "Insurance", "amount": 50, "basis": "PER_SHIPMENT", "optional": True, "source_ref": "a:ins"},
        ]))
        self.assertEqual(audit["status"], "BLOCKED")
        self.assertTrue(any(x["type"] == "OPTIONAL_SELECTION_REQUIRED" for x in audit["errors"]))

    def test_guard_blocks_before_ranking_when_semantics_are_unresolved(self):
        bad = quote("A", [
            {"name": "THC", "amount": 100, "basis": "PER_SHIPMENT", "source_ref": "a:1"},
            {"name": "THC", "amount": 100, "basis": "PER_SHIPMENT", "source_ref": "a:2"},
        ])
        good = quote("B", [
            {"name": "THC", "amount": 90, "basis": "PER_SHIPMENT", "source_ref": "b:1"},
        ])
        result = compare_quotes_guarded([bad, good], {"shipments": 1})
        self.assertEqual(result["ranking"], [])
        self.assertEqual(result["decision_warning"], "UNRESOLVED_CHARGE_SEMANTICS")
        self.assertEqual(result["comparison_basis"]["selection_mode"], "SEMANTIC_GUARD_BLOCKED")


if __name__ == "__main__":
    unittest.main()
