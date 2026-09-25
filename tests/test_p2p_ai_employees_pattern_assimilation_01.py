"""Invariant checks for P2P_AI_EMPLOYEES_PATTERN_ASSIMILATION_01.

Locks durable governance outcomes, not prose wording:
pin, unique ledger records, RESEARCHED vs DEFERRED, empty capability ids,
re-entry conjuncts, no cadence runtime/capability, JSON-over-projection.
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / "docs" / "p2p-development" / "research" / "P2P-AI-EMPLOYEES-PATTERN-ASSIMILATION-01.md"
LEDGER = ROOT / "governance" / "research-adoption-ledger.json"
PROJECTION = ROOT / "docs" / "RESEARCH-ADOPTION-LEDGER.md"

UPSTREAM_COMMIT = "edffe8f4afea467818988ce3ce9332e6d832e5ed"

RECORD_REQUIRED_FIELDS = (
    "research_id",
    "source_name",
    "source_type",
    "source_reference",
    "source_version_or_commit",
    "provenance_status",
    "research_summary",
    "selected_ideas",
    "rejected_ideas",
    "p2p_translation",
    "capability_family",
    "canonical_capability_ids",
    "status",
    "evidence_pointers",
    "dependencies",
    "roadmap_slot",
    "owner_decision_status",
    "last_reviewed_at",
    "notes",
)

EXPECTED_CLASSES = {
    "A": "ALREADY_COVERED",
    "B": "KEEP",
    "C": "DEFER_UNTIL_NEEDED",
    "D": "DEFER_UNTIL_NEEDED",
    "E": "ADAPT",
    "F": "ALREADY_COVERED",
    "G": "ALREADY_COVERED",
    "H": "ALREADY_COVERED",
    "I": "ALREADY_COVERED",
    "J": "KEEP",
    "K": "ALREADY_COVERED",
    "L": "ADAPT",
    "M": "KEEP",
    "N": "ALREADY_COVERED",
    "O": "KEEP",
}


def load_ledger():
    return json.loads(LEDGER.read_text(encoding="utf-8"))


def record(ledger, research_id):
    matches = [r for r in ledger["records"] if r.get("research_id") == research_id]
    if len(matches) != 1:
        return None
    return matches[0]


class AdoptionInvariants(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.study = STUDY.read_text(encoding="utf-8")
        cls.ledger = load_ledger()
        cls.projection = PROJECTION.read_text(encoding="utf-8")

    def test_upstream_pin_is_recorded(self):
        self.assertTrue(STUDY.is_file())
        self.assertIn(UPSTREAM_COMMIT, self.study)
        rec = record(self.ledger, "RA-EXT-100")
        self.assertIsNotNone(rec)
        self.assertIn(UPSTREAM_COMMIT, rec["source_version_or_commit"])
        self.assertIn("MIT", rec["provenance_status"])
        self.assertIn("markfulton/ai-employees", rec["source_reference"])

    def test_ledger_records_exist_once_with_required_fields(self):
        ids = [r.get("research_id") for r in self.ledger["records"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(ids.count("RA-EXT-100"), 1)
        self.assertEqual(ids.count("RA-EXT-101"), 1)
        for research_id in ("RA-EXT-100", "RA-EXT-101"):
            rec = record(self.ledger, research_id)
            for field in RECORD_REQUIRED_FIELDS:
                self.assertIn(field, rec)
            self.assertIn(rec["status"], self.ledger["status_vocabulary"])
            self.assertEqual(rec["canonical_capability_ids"], [])

    def test_study_complete_is_researched_candidate_is_deferred(self):
        self.assertEqual(record(self.ledger, "RA-EXT-100")["status"], "RESEARCHED")
        self.assertEqual(record(self.ledger, "RA-EXT-101")["status"], "DEFERRED")
        self.assertRegex(self.projection, r"RA-EXT-100\b.*\bRESEARCHED\b")
        self.assertRegex(self.projection, r"RA-EXT-101\b.*\bDEFERRED\b")

    def test_pattern_matrix_classifications_are_present(self):
        # Structural: each letter appears in the matrix table with its class.
        for letter, klass in EXPECTED_CLASSES.items():
            row = re.compile(
                rf"^\|\s*{letter}\s*\|.+\|\s*{klass}\s*\|",
                re.MULTILINE,
            )
            self.assertRegex(self.study, row, letter)

    def test_re_entry_trigger_has_four_conjuncts(self):
        rec = record(self.ledger, "RA-EXT-101")
        notes = rec["notes"]
        self.assertIn("RE_ENTRY_TRIGGER", notes)
        for token in ("PERIOD form", "firing source", "expires_at", "local-clock"):
            self.assertIn(token, notes)
        self.assertIn("SPECIFIED_NOT_IMPLEMENTED", rec["provenance_status"])

    def test_json_ledger_is_declared_authority(self):
        self.assertIn("the JSON wins", self.projection)
        self.assertIn(UPSTREAM_COMMIT, self.projection)
        self.assertIn("RA-EXT-100", self.projection)
        self.assertIn("RA-EXT-101", self.projection)

    def test_no_cadence_runtime_or_capability_minted(self):
        capabilities = ROOT / ".p2p" / "system" / "p2p_capabilities"
        offenders = [
            p.name
            for p in capabilities.glob("*.py")
            if re.search(r"(recurring|routine|cadence|period_key|schedule_guard)", p.name, re.I)
        ]
        self.assertEqual(offenders, [])
        registry = json.loads((capabilities / "capabilities.json").read_text(encoding="utf-8"))
        minted = [
            c.get("CAPABILITY_ID")
            for c in registry["capabilities"]
            if re.search(r"(recurring.routine|cadence.identity|period_key)", json.dumps(c), re.I)
        ]
        self.assertEqual(minted, [])


if __name__ == "__main__":
    unittest.main()
