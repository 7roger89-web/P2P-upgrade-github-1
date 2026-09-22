"""Focused checks for P2P_AI_EMPLOYEES_PATTERN_ASSIMILATION_01.

Verifies the durable outcome of the AI-Employees pattern-assimilation study:

* the study artifact exists and carries the required over-engineering gate and
  15-pattern KEEP/ADAPT/ALREADY_COVERED/DEFER matrix;
* the rejected-mechanism register is present and includes the authority-boundary
  refusals the task required (no instruction-level guardrails, no second outbound
  authority surface, no ungated self-edit, no local-machine coupling, no new
  P2P agent identities);
* the deferred direction is specified but NOT implemented, and its re-entry
  trigger is recorded;
* the canonical adoption ledger (JSON authority) carries the batch
  ``RA-EXT-100 .. RA-EXT-101`` with conforming records, and no capability or
  runtime surface was minted;
* no second control plane / router / registry / scheduler / state store exists
  as a result of this batch, and no upstream byte was vendored.

Read-only: no network, no external tool execution, no writes.
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
NOTEBOOK = ROOT / "docs" / "p2p-development" / "P2P-OPERATIONS-NOTEBOOK.md"

UPSTREAM_COMMIT = "edffe8f4afea467818988ce3ce9332e6d832e5ed"

# The 15 evaluated patterns and their expected primary classification.
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


def load_ledger():
    return json.loads(LEDGER.read_text(encoding="utf-8"))


def record(ledger, research_id):
    return next((r for r in ledger["records"] if r.get("research_id") == research_id), None)


class StudyArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.study = STUDY.read_text(encoding="utf-8")
        cls.ledger = load_ledger()
        cls.projection = PROJECTION.read_text(encoding="utf-8")
        cls.notebook = NOTEBOOK.read_text(encoding="utf-8")

    # ---------------------------------------------------------------- artifact
    def test_study_artifact_exists_with_required_provenance(self):
        self.assertTrue(STUDY.is_file(), f"missing study artifact: {STUDY}")
        for token in (
            "Task: `P2P_AI_EMPLOYEES_PATTERN_ASSIMILATION_01`",
            "markfulton/ai-employees",
            UPSTREAM_COMMIT,
            "MIT",
            "2026-09-22",
            "REVIEW_DATE",
            "RESEARCH_ONLY_PASS",
        ):
            self.assertIn(token, self.study, f"study is missing {token!r}")

    def test_over_engineering_gate_is_recorded_and_not_ceremonial(self):
        # The gate must carry all five required fields plus a real verdict.
        for token in (
            "Không bị over engineering chứ?",
            "SIMPLER_PATH=",
            "MATERIAL_PROGRESS=",
            "NECESSITY=",
            "CORE_BEFORE_SUPPORT=",
            "SMALLER_VERIFIABLE_SLICE=",
            "OE_VERDICT=DEFER_UNTIL_NEEDED",
        ):
            self.assertIn(token, self.study, f"OE gate is missing {token!r}")
        # A ceremonial pass is invalid: NECESSITY must fail for runtime and the
        # machinery for the gap must NOT have been built.
        self.assertIn("NECESSITY=FAIL for runtime", self.study)
        self.assertIn("NOT implemented", self.study)

    def test_all_fifteen_patterns_are_classified_once(self):
        for letter, expected in EXPECTED_CLASSES.items():
            heading = re.compile(rf"^### {letter}\. .* — {expected}$", re.MULTILINE)
            self.assertRegex(
                self.study,
                heading,
                f"pattern {letter} must have exactly one primary class {expected}",
            )
        for klass in ("KEEP", "ADAPT", "ALREADY_COVERED", "DEFER_UNTIL_NEEDED"):
            self.assertIn(klass, self.study)
        # Each pattern block must answer the required six questions.
        for label in (
            "- **Upstream evidence:**",
            "- **Current P2P equivalent:**",
            "- **Demonstrated P2P gap:**",
        ):
            self.assertGreaterEqual(self.study.count(label), 15, label)

    def test_reject_register_covers_the_authority_boundaries(self):
        for token in (
            "REJECT register",
            "Instruction-level guardrail sufficiency",
            "RELEASES.md` as the authority surface",
            "Ungated routine self-editing",
            "Local-machine and single-harness assumptions",
            "Browser-profile automation as a core capability",
            "eight-employee / sixty-routine role catalogue",
        ):
            self.assertIn(token, self.study, f"reject register is missing {token!r}")

    def test_authority_and_boundary_sections_are_present(self):
        for token in (
            "A routine definition must not widen authority",
            "content is data",
            "ALREADY_COVERED — add nothing.",
            "No\nChief-of-Staff agent was created",
        ):
            self.assertIn(token, self.study, f"boundary statement is missing {token!r}")

    def test_deferred_direction_is_specified_with_a_re_entry_trigger(self):
        for token in (
            "PROVIDER_NEUTRAL_RECURRING_ROUTINE_CONTRACT",
            "Re-entry trigger",
            "RUN | SKIP",
            "never UTC, never a stored timezone",
            "REUSE_EXISTING_P2P > EXTEND_EXISTING_P2P > ADAPTER >",
            "no cron engine",
        ):
            self.assertIn(token, self.study, f"deferred candidate is missing {token!r}")

    def test_study_states_it_added_no_runtime_surface(self):
        for token in (
            "SECOND_CONTROL_PLANE_CREATED=NO",
            "SECOND_ROUTER_CREATED=NO",
            "SECOND_REGISTRY_CREATED=NO",
            "SCHEDULER_DAEMON_CREATED=NO",
            "CANONICAL_8_AGENTS_CHANGED=NO",
            "OWNER_GATES_WEAKENED=NO",
        ):
            self.assertIn(token, self.study, token)

    # ------------------------------------------------------------------ ledger
    def test_adoption_ledger_batch_is_durable_and_conforming(self):
        for research_id in ("RA-EXT-100", "RA-EXT-101"):
            rec = record(self.ledger, research_id)
            self.assertIsNotNone(rec, f"{research_id} is missing from the adoption ledger")
            for field in RECORD_REQUIRED_FIELDS:
                self.assertIn(field, rec, f"{research_id} is missing {field}")
            self.assertIn(rec["status"], self.ledger["status_vocabulary"])
            self.assertEqual(rec["status"], "DEFERRED")
            self.assertEqual(rec["canonical_capability_ids"], [])
            self.assertTrue(rec["evidence_pointers"], research_id)

    def test_ledger_ids_are_unique_and_this_batch_is_the_tail(self):
        ids = [r.get("research_id") for r in self.ledger["records"]]
        self.assertEqual(len(ids), len(set(ids)), "duplicate research_id in the adoption ledger")
        self.assertEqual(ids[-2:], ["RA-EXT-100", "RA-EXT-101"])

    def test_ledger_records_pin_upstream_and_forbid_revendoring(self):
        rec100 = record(self.ledger, "RA-EXT-100")
        self.assertIn(UPSTREAM_COMMIT, rec100["source_version_or_commit"])
        self.assertIn("MIT", rec100["provenance_status"])
        self.assertIn("markfulton/ai-employees", rec100["source_reference"])
        self.assertIn("NO IMPLEMENTATION", rec100["p2p_translation"])
        # The refusal list must carry the authority-boundary items.
        rejected = " ; ".join(rec100["rejected_ideas"]).lower()
        for token in (
            "instruction-level guardrail sufficiency",
            "second outbound-action authority surface",
            "ungated routine self-editing",
            "local-machine",
            "browser",
            "eight-employee",
        ):
            self.assertIn(token.lower(), rejected, token)

    def test_deferred_record_carries_the_re_entry_trigger(self):
        rec101 = record(self.ledger, "RA-EXT-101")
        self.assertEqual(rec101["status"], "DEFERRED")
        for token in ("RE_ENTRY_TRIGGER", "PERIOD form", "firing source", "expires_at", "local-clock"):
            self.assertIn(token, rec101["notes"], token)
        self.assertIn("SPECIFIED_NOT_IMPLEMENTED", rec101["provenance_status"])
        self.assertIn("NOT implemented", rec101["source_version_or_commit"])

    def test_projection_matches_the_ledger_authority(self):
        for token in ("4.7 AI Employees pattern-assimilation batch", "RA-EXT-100", "RA-EXT-101", UPSTREAM_COMMIT):
            self.assertIn(token, self.projection, token)
        # The JSON remains declared authoritative over the projection.
        self.assertIn("the JSON wins", self.projection)

    # ------------------------------------------------------- no new machinery
    def test_no_runtime_module_was_added_for_this_batch(self):
        capabilities = ROOT / ".p2p" / "system" / "p2p_capabilities"
        offenders = [
            p.name
            for p in capabilities.glob("*.py")
            if re.search(r"(recurring|routine|cadence|period_key|schedule_guard)", p.name, re.I)
        ]
        self.assertEqual(offenders, [], f"no runtime module may be created for this batch: {offenders}")
        # No capability registry entry was minted for the batch either.
        registry = json.loads((capabilities / "capabilities.json").read_text(encoding="utf-8"))
        minted = [
            c.get("CAPABILITY_ID")
            for c in registry["capabilities"]
            if re.search(r"(recurring|routine|cadence)", json.dumps(c), re.I)
        ]
        self.assertEqual(minted, [], f"no capability may be minted for this batch: {minted}")

    def test_protocol_used_is_the_canonical_one_not_a_recreation(self):
        for token in ("MODEL_CANARY_GATE_V1", "OWNER_CONTINUATION_GATE_V1", "RULE 14"):
            self.assertIn(token, self.notebook, token)
        self.assertIn("MODEL_CANARY_GATE_V1", self.study)
        self.assertIn("OWNER_CONTINUATION_GATE_V1", self.study)
        self.assertIn("No part of\nthat protocol was bypassed, recreated, or weakened.", self.study)


if __name__ == "__main__":
    unittest.main()
