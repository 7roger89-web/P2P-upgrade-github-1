"""Deterministic checks for P2P_EXTERNAL_CAPABILITY_ASSIMILATION_20260917_01.

Verifies the assimilated interaction-polish mechanics inside the existing
UI-taste-skill redesign surface (all projection copies byte-identical) and the
durable research-adoption-ledger records RA-EXT-072..RA-EXT-081. Read-only:
this test never executes external tools and never registers MCP servers.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

SKILL_RELATIVE = Path("skills") / "redesign-skill" / "SKILL.md"
SKILL_COPIES = [
    REPO_ROOT / ".agents" / "skills" / "UI-taste-skill" / SKILL_RELATIVE,
    REPO_ROOT / ".claude" / "skills" / "UI-taste-skill" / SKILL_RELATIVE,
    REPO_ROOT / ".p2p" / "system" / ".agents" / "skills" / "UI-taste-skill" / SKILL_RELATIVE,
]

LEDGER_PATH = REPO_ROOT / "governance" / "research-adoption-ledger.json"
LEDGER_MD_PATH = REPO_ROOT / "docs" / "RESEARCH-ADOPTION-LEDGER.md"

BATCH_IDS = [f"RA-EXT-{n:03d}" for n in range(72, 82)]

ASSIMILATED_MARKERS = [
    "Interaction Polish Gate",
    "Interruptible by default",
    "CSS transitions",
    "transition-property",
    "Restrain motion by frequency",
    "Concentric border radius",
    "outer = inner + padding",
    "Match icon stroke to text weight",
    "44×44px",
    "40×40px",
    "tabular-nums",
    "State walk verification",
    "10% speed",
    "Polish review output",
    "Not verified",
    "jakubkrehel/make-interfaces-feel-better",
    "35545ea",
    "MIT",
    "RA-EXT-072",
]

REQUIRED_RECORD_FIELDS = [
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
    "status",
    "evidence_pointers",
    "last_reviewed_at",
]


class InteractionPolishGateContentTests(unittest.TestCase):
    """The assimilated mechanics must be present in the canonical copy."""

    @classmethod
    def setUpClass(cls):
        cls.text = SKILL_COPIES[0].read_text(encoding="utf-8")

    def test_assimilated_markers_present(self):
        missing = [m for m in ASSIMILATED_MARKERS if m not in self.text]
        self.assertEqual(missing, [], f"missing assimilated markers: {missing}")

    def test_constants_are_framed_as_heuristics_not_laws(self):
        self.assertIn("working heuristics and defaults, not universal laws", self.text)

    def test_no_second_styling_system(self):
        collapsed = " ".join(self.text.split())
        self.assertIn("never introduce a second styling system", collapsed)

    def test_existing_audit_sections_preserved(self):
        for section in (
            "## Design Audit",
            "## Upgrade Techniques",
            "## Fix Priority",
            "## Rules",
        ):
            self.assertIn(section, self.text, f"existing section lost: {section}")

    def test_projection_copies_byte_identical(self):
        canonical = SKILL_COPIES[0].read_bytes()
        for copy in SKILL_COPIES[1:]:
            self.assertTrue(copy.is_file(), f"missing projection copy: {copy}")
            self.assertEqual(
                copy.read_bytes(),
                canonical,
                f"projection copy diverged from canonical: {copy}",
            )

    def test_skill_manifest_per_file_hash_matches_content(self):
        import hashlib

        expected = "sha256:" + hashlib.sha256(SKILL_COPIES[0].read_bytes()).hexdigest()
        manifests = [
            REPO_ROOT / ".agents" / "skills" / ".agents-skill-manifest.json",
            REPO_ROOT / ".claude" / "skills" / ".claude-skill-manifest.json",
            REPO_ROOT / ".p2p" / "system" / ".agents" / "skills" / ".agents-skill-manifest.json",
        ]
        for mf in manifests:
            data = json.loads(mf.read_text(encoding="utf-8"))
            entry = data["skills"]["UI-taste-skill"]["files"]["skills/redesign-skill/SKILL.md"]
            self.assertEqual(entry, expected, f"stale manifest hash in {mf}")


class ResearchAdoptionLedgerBatchTests(unittest.TestCase):
    """The ten assessment records must be durable, unique, and valid."""

    @classmethod
    def setUpClass(cls):
        cls.ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
        cls.records = {r["research_id"]: r for r in cls.ledger["records"]}
        cls.vocab = set(cls.ledger["status_vocabulary"])

    def test_no_duplicate_research_ids(self):
        ids = [r["research_id"] for r in self.ledger["records"]]
        self.assertEqual(len(ids), len(set(ids)), "duplicate research_id in ledger")

    def test_batch_records_present_exactly_once(self):
        for rid in BATCH_IDS:
            self.assertIn(rid, self.records, f"missing ledger record: {rid}")

    def test_batch_statuses_use_ledger_vocabulary(self):
        for rid in BATCH_IDS:
            status = self.records[rid]["status"]
            self.assertIn(status, self.vocab, f"{rid} status {status!r} not in vocabulary")

    def test_batch_records_provenance_complete(self):
        for rid in BATCH_IDS:
            record = self.records[rid]
            for field in REQUIRED_RECORD_FIELDS:
                self.assertIn(field, record, f"{rid} missing field {field}")
            self.assertTrue(record["source_reference"].startswith("https://github.com/"))
            self.assertTrue(record["source_version_or_commit"].strip())
            self.assertTrue(record["research_summary"].strip())

    def test_licenses_recorded_per_repo(self):
        for rid in BATCH_IDS:
            blob = json.dumps(self.records[rid]).lower()
            self.assertTrue(
                "mit" in blob or "apache-2.0" in blob or "rights-unspecified" in blob,
                f"{rid} has no license/rights statement",
            )

    def test_assimilated_record_points_at_existing_skill_surface(self):
        record = self.records["RA-EXT-072"]
        self.assertEqual(record["status"], "IMPLEMENTED")
        pointers = " ".join(record["evidence_pointers"])
        self.assertIn("redesign-skill/SKILL.md", pointers)
        self.assertIn("CONCEPT_ADAPTED_NOT_VENDORED", record["provenance_status"])

    def test_no_parallel_infrastructure_records(self):
        for rid in BATCH_IDS:
            translation = self.records[rid]["p2p_translation"]
            self.assertNotIn("new orchestration", translation.lower())
        self.assertEqual(
            self.records["RA-EXT-074"]["status"],
            "DEFERRED",
            "oh-my-hermes must not be adopted as an operating layer",
        )

    def test_ledger_md_projection_documents_batch(self):
        text = LEDGER_MD_PATH.read_text(encoding="utf-8")
        for rid in BATCH_IDS:
            self.assertIn(rid, text, f"md projection missing {rid}")


if __name__ == "__main__":
    unittest.main()
