import json
import unittest
from pathlib import Path

from src.concierge_engine import compare_quotes


class SyntheticQuoteFixtureTests(unittest.TestCase):
    def test_fixture_ranking_and_exclusion_are_stable(self):
        fixture_path = (
            Path(__file__).resolve().parents[1]
            / "pilots"
            / "logistics-quote-comparison"
            / "fixtures"
            / "synthetic-quote-set-01.json"
        )
        data = json.loads(fixture_path.read_text(encoding="utf-8"))
        result = compare_quotes(data["quotes"], data["context"])

        self.assertEqual(
            [(item["quote_id"], item["total"]) for item in result["ranking"]],
            [(item["quote_id"], item["total"]) for item in data["expected"]["ranking"]],
        )
        self.assertEqual(result["required_charge_codes"], data["expected"]["required_charge_codes"])
        self.assertTrue(all(not row["unresolved_missing_codes"] for row in result["coverage_matrix"]))
        self.assertFalse(result["comparison_basis"]["fx_applied"])
        self.assertEqual(result["excluded"][0]["quote_id"], data["expected"]["excluded"]["quote_id"])
        self.assertIn(data["expected"]["excluded"]["reason"], result["excluded"][0]["reasons"])


if __name__ == "__main__":
    unittest.main()
