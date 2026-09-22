"""Focused policy checks for global community research and model identity inference."""
from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "docs" / "p2p-development" / "P2P-OPERATIONS-NOTEBOOK.md"
AGENTS = ROOT / "AGENTS.md"
INSTALL = ROOT / "docs" / "p2p-development" / "P2P-AGENTS-INSTALL.md"
LEDGER = ROOT / "governance" / "research-adoption-ledger.json"


class GlobalCommunityResearchPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.notebook = NOTEBOOK.read_text(encoding="utf-8")
        cls.agents = AGENTS.read_text(encoding="utf-8")
        cls.install = INSTALL.read_text(encoding="utf-8")
        cls.ledger = json.loads(LEDGER.read_text(encoding="utf-8"))

    def test_global_research_is_adaptive_not_country_whitelist(self):
        for token in (
            "GLOBAL_COMMUNITY_RESEARCH_V1",
            "INTERNET != REDDIT",
            "ENGLISH_WEB != GLOBAL_WEB",
            "COUNTRY_WHITELIST = FORBIDDEN",
            "FORUM_ANECDOTE != AUTHORITATIVE_FACT",
            "Search in local languages when useful",
            "Track independence, not raw link count",
        ):
            self.assertIn(token, self.notebook)

    def test_model_identity_boundary_rejects_self_disclosure_tricks(self):
        for token in (
            "MODEL_IDENTITY_INFERENCE_BOUNDARY_V1",
            "SELF_DISCLOSURE != MODEL_IDENTITY_EVIDENCE",
            "FIRST_LETTER_OR_LAST_LETTER_TRICK != MODEL_IDENTITY_EVIDENCE",
            "OBFUSCATED_SELF_REPORT != MODEL_IDENTITY_EVIDENCE",
            "WRITING_STYLE_GUESS != MODEL_IDENTITY_EVIDENCE",
            "SESSION_QUALITY > GUESSED_MODEL_NAME",
        ):
            self.assertIn(token, self.notebook)

    def test_arena_reference_requires_matching_surface_and_harness(self):
        for token in (
            "AGENT_POOL != DIRECT_SELECTOR",
            "AGENT_POOL != SIDE_BY_SIDE_SELECTOR",
            "REFERENCE_HARNESS_MUST_MATCH_TARGET_HARNESS",
        ):
            self.assertIn(token, self.notebook)

    def test_behavioral_fingerprint_is_bounded_and_uncertain(self):
        self.assertIn("define a CLOSED candidate set", self.notebook)
        self.assertIn("ranked candidate set or family-level estimate with confidence", self.notebook)
        self.assertIn("an `UNKNOWN` option", self.notebook)
        self.assertIn("automatic model switching", self.notebook)
        self.assertIn("Fingerprinting never replaces `MODEL_CANARY_GATE_V1`", self.notebook)

    def test_entrypoints_discover_both_policies(self):
        for text in (self.agents, self.install):
            self.assertIn("GLOBAL_COMMUNITY_RESEARCH_V1", text)
            self.assertIn("MODEL_IDENTITY_INFERENCE_BOUNDARY_V1", text)

    def test_research_adoption_record_is_durable(self):
        record = next((r for r in self.ledger["records"] if r["research_id"] == "RA-EXT-099"), None)
        self.assertIsNotNone(record)
        self.assertEqual(record["status"], "IMPLEMENTED")
        self.assertIn("GLOBAL_COMMUNITY_RESEARCH_V1", record["p2p_translation"])
        self.assertIn("MODEL_IDENTITY_INFERENCE_BOUNDARY_V1", record["p2p_translation"])


if __name__ == "__main__":
    unittest.main()
