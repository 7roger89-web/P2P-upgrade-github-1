import unittest

from src.prospect_bridge import qualify_public_prospect


def good_prospect():
    return {
        "display_name": "Example Logistics Team",
        "source_url": "https://example.com/public-discussion",
        "signal_type": "PAIN",
        "evidence_class": "USER_SAID",
        "signal_text": "We spend hours normalizing supplier quotes by hand.",
        "score_dimensions": {
            "pain_strength": 5,
            "product_fit": 5,
            "timing": 4,
            "public_reachability": 4,
            "evidence_quality": 5,
        },
        "public_channel": "public forum reply",
        "outreach_opener": "Saw your public note about quote normalization...",
    }


class ProspectBridgeTests(unittest.TestCase):
    def test_direct_public_signal_can_enter_primary_shortlist(self):
        result = qualify_public_prospect(good_prospect())
        self.assertEqual(result.stage, "PRIMARY_STRONG")
        self.assertEqual(result.market_evidence["signal"], "PAIN")
        self.assertEqual(result.outreach["mode"], "DRAFT_ONLY")
        self.assertFalse(result.outreach["send_authorized"])

    def test_industry_fit_without_public_signal_is_rejected(self):
        p = good_prospect()
        p["signal_type"] = "POTENTIAL_FIT"
        self.assertEqual(qualify_public_prospect(p).stage, "REJECT")

    def test_missing_public_source_is_rejected(self):
        p = good_prospect()
        p["source_url"] = ""
        self.assertEqual(qualify_public_prospect(p).stage, "REJECT")

    def test_public_pain_never_becomes_money_signal(self):
        result = qualify_public_prospect(good_prospect())
        self.assertNotIn(result.market_evidence["signal"], {"PAYMENT", "WILLINGNESS_TO_PAY"})

    def test_private_or_sensitive_enrichment_is_forbidden(self):
        p = good_prospect()
        p["private_email"] = "person@example.com"
        with self.assertRaisesRegex(ValueError, "private_or_sensitive_enrichment_forbidden"):
            qualify_public_prospect(p)


if __name__ == "__main__":
    unittest.main()
