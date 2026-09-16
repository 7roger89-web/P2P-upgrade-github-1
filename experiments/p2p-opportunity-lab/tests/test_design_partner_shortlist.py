import json
import unittest
from pathlib import Path

from src.prospect_bridge import qualify_public_prospect


FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "pilots"
    / "logistics-quote-comparison"
    / "design-partner-shortlist.json"
)


class DesignPartnerShortlistTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_shortlist_has_multiple_direct_public_prospects(self):
        prospects = self.data["prospects"]
        self.assertGreaterEqual(len(prospects), 5)
        for prospect in prospects:
            result = qualify_public_prospect(prospect)
            self.assertEqual(result.stage, prospect["expected_stage"])
            self.assertEqual(result.score, prospect["expected_score"])
            self.assertIsNotNone(result.market_evidence)

    def test_all_primary_outreach_remains_draft_only(self):
        self.assertFalse(self.data["send_authorized"])
        for prospect in self.data["prospects"]:
            result = qualify_public_prospect(prospect)
            self.assertIsNotNone(result.outreach)
            self.assertEqual(result.outreach["mode"], "DRAFT_ONLY")
            self.assertFalse(result.outreach["send_authorized"])

    def test_shortlist_never_manufactures_money_evidence(self):
        for prospect in self.data["prospects"]:
            result = qualify_public_prospect(prospect)
            self.assertNotIn(
                result.market_evidence["signal"],
                {"PAYMENT", "WILLINGNESS_TO_PAY"},
            )
        self.assertEqual(
            self.data["market_gate_effect"],
            "NONE_UNTIL_REAL_BEHAVIOR_OR_MONEY_SIGNAL_IS_OBSERVED",
        )

    def test_competitors_are_not_smuggled_into_customer_shortlist(self):
        excluded = {item["display_name"] for item in self.data["excluded_or_peer_only"]}
        primary = {item["display_name"] for item in self.data["prospects"]}
        self.assertIn("mardingca / QuoteFast", excluded)
        self.assertNotIn("mardingca / QuoteFast", primary)


if __name__ == "__main__":
    unittest.main()
