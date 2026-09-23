"""Invariant checks for P2P_DOMAIN_CAPABILITY_ADMISSION_01 (Issue #245).

Locks durable governance outcomes, not prose wording:

- `DOMAIN_CAPABILITY_ADMISSION_V1` is ONE bounded subsection under canonical
  RULE 19 and creates no new top-level numbered rule;
- the required canonical invariants and authority-boundary examples exist;
- the Rule Assimilation ledger carries `VERIFIED` only after independent
  Control Tower verification of the exact Writer head;
- the research-adoption ledger is append/reconcile only: history preserved,
  RA-EXT-102 present exactly once, no runtime capability minted;
- the existing portable projector carries the new canonical source identity,
  is idempotent on a second run, and preserves project-specific AGENTS.md
  content.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "docs" / "p2p-development" / "P2P-OPERATIONS-NOTEBOOK.md"
RESEARCH_LEDGER = ROOT / "governance" / "research-adoption-ledger.json"
RESEARCH_PROJECTION = ROOT / "docs" / "RESEARCH-ADOPTION-LEDGER.md"
INSTALL_SOURCE = ROOT / "docs" / "p2p-development" / "P2P-AGENTS-INSTALL.md"
CAPABILITIES = ROOT / ".p2p" / "system" / "p2p_capabilities"
SCRIPTS = ROOT / "scripts"

SUBSECTION = "#### DOMAIN_CAPABILITY_ADMISSION_V1"
RULE19 = "### RULE 19 — REALITY_FIRST_CAPABILITY_PROBE"
RULE20 = "### RULE 20 — OWNER_EXECUTOR_SELECTION_AND_AUTONOMOUS_COMPLETION"

REQUIRED_INVARIANTS = (
    "CROSS_DOMAIN_SUCCESS != TARGET_DOMAIN_PROOF",
    "NEW_COMPLEX_CAPABILITY => CHEAP_CREDIBLE_BASELINE_FIRST",
    "EVALUATION_SET => FREEZE_BEFORE_RESULT_WHEN_RESULT_CAN_BIAS_THE_TEST",
    "PROMOTION_CRITERIA => PREDECLARE_BEFORE_FINAL_RESULT",
    "CAN_RUN != WORKS_FOR_TARGET_TASK != MATERIALLY_BETTER_THAN_CURRENT_PATH "
    "!= WORTH_COMPLEXITY != READY_FOR_PRODUCT_CONTROL",
    "UNPROVEN_MODEL_OR_PROVIDER => OBSERVE_BEFORE_CONTROL_WHEN_CONTROL_HAS_MATERIAL_RISK",
    "ROUTING_OR_CLASSIFICATION_SIGNAL != DOMAIN_TRUTH_AUTHORITY",
    "ABSTAIN_OR_UNKNOWN => VALID_OUTCOME_WHEN_EVIDENCE_IS_INSUFFICIENT",
    "TRUTHFUL_UNKNOWN > UNSUPPORTED_CONFIDENT_GUESS",
)

AUTHORITY_BOUNDARY_EXAMPLES = (
    "ROUTER_CLASSIFIES_PAYMENT_QUERY != PAYMENT_IS_SETTLED",
    "ROUTER_CLASSIFIES_LEGAL_HISTORY != LAW_IS_CURRENT",
    "ROUTER_CLASSIFIES_BAZI_DUNG_THAN != DUNG_THAN_IS_X",
    "ROUTER_CLASSIFIES_GENEALOGY_RELATION_QUERY != PERSON_A_IS_PARENT_OF_PERSON_B",
)

SELECTED_IDEAS = (
    "CROSS_DOMAIN_SUCCESS != TARGET_DOMAIN_PROOF",
    "NEW_COMPLEX_CAPABILITY => CHEAP_CREDIBLE_BASELINE_FIRST",
    "PROMOTION_CRITERIA => PREDECLARE_BEFORE_FINAL_RESULT",
    "UNPROVEN_MODEL_OR_PROVIDER => OBSERVE_BEFORE_CONTROL_WHEN_CONTROL_HAS_MATERIAL_RISK",
    "ROUTING_OR_CLASSIFICATION_SIGNAL != DOMAIN_TRUTH_AUTHORITY",
    "ABSTAIN_OR_UNKNOWN => VALID_OUTCOME_WHEN_EVIDENCE_IS_INSUFFICIENT",
    "TRUTHFUL_UNKNOWN > UNSUPPORTED_CONFIDENT_GUESS",
)

REJECTED_IDEAS = (
    "upstream benchmark as target-domain proof",
    "cross-domain extrapolation",
    "runtime success",
    "global OpenJev install",
    "domain truth authority",
)

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


def _flatten(text: str) -> str:
    """Collapse whitespace so wrapped code blocks match their logical line."""
    return re.sub(r"\s+", " ", text)


class DomainCapabilityAdmissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.notebook = NOTEBOOK.read_text(encoding="utf-8")
        cls.ledger = json.loads(RESEARCH_LEDGER.read_text(encoding="utf-8"))
        cls.projection = RESEARCH_PROJECTION.read_text(encoding="utf-8")
        cls.install_source = INSTALL_SOURCE.read_text(encoding="utf-8")

    def _ledger_record(self, research_id: str) -> dict:
        matches = [r for r in self.ledger["records"] if r.get("research_id") == research_id]
        self.assertEqual(len(matches), 1, f"{research_id} must exist exactly once")
        return matches[0]

    # --- canonical placement ------------------------------------------------

    def test_subsection_exists_under_rule19_only(self) -> None:
        self.assertIn(SUBSECTION, self.notebook)
        self.assertLess(self.notebook.index(RULE19), self.notebook.index(SUBSECTION))
        self.assertLess(self.notebook.index(SUBSECTION), self.notebook.index(RULE20))
        # Level 4 = subsection. A level-3 heading would be a new numbered rule.
        # (Match anchored at line start: "#### X" contains "### X" as a substring.)
        self.assertIsNone(
            re.search(r"^### DOMAIN_CAPABILITY_ADMISSION_V1\b", self.notebook, re.M)
        )
        self.assertIsNotNone(
            re.search(r"^#### DOMAIN_CAPABILITY_ADMISSION_V1\b", self.notebook, re.M)
        )

    def test_no_new_top_level_numbered_rule_created(self) -> None:
        numbers = sorted(int(n) for n in re.findall(r"^### RULE (\d+) —", self.notebook, re.M))
        self.assertEqual(numbers, list(range(1, 22)), "top-level rule set must remain RULE 01-21")
        self.assertNotIn("### RULE 22", self.notebook)

    def test_required_canonical_invariants_are_present(self) -> None:
        flat = _flatten(self.notebook)
        for law in REQUIRED_INVARIANTS:
            self.assertIn(law, flat, law)

    def test_authority_boundary_examples_are_preserved(self) -> None:
        flat = _flatten(self.notebook)
        for example in AUTHORITY_BOUNDARY_EXAMPLES:
            self.assertIn(example, flat, example)

    def test_subsection_declares_no_second_framework(self) -> None:
        start = self.notebook.index(SUBSECTION)
        end = self.notebook.index(RULE20)
        section = self.notebook[start:end]
        for token in (
            "no second framework",
            "registry",
            "smallest representative probe",
        ):
            self.assertIn(token, section, token)
        # Proportionality: no mandatory broad benchmark ceremony.
        self.assertIn("no mandatory broad benchmark ceremony", _flatten(section))

    # --- rule assimilation ledger ------------------------------------------

    def test_assimilation_ledger_carries_verified_entry_after_control_tower_review(self) -> None:
        match = re.search(r"```json\n(.*?)\n```", self.notebook, re.DOTALL)
        self.assertIsNotNone(match, "machine-readable ledger must exist")
        assert match is not None
        ledger = json.loads(match.group(1))
        entries = {e["id"]: e for e in ledger["entries"]}
        self.assertIn("BACKLOG_J", entries)
        entry = entries["BACKLOG_J"]
        self.assertEqual(entry["item"], "DOMAIN_CAPABILITY_ADMISSION_V1")
        # Control Tower independently verified PR #246 Writer head d14b5e89...
        # in comment 5793604664 before this post-verification status flip.
        self.assertEqual(entry["status"], "VERIFIED")
        self.assertTrue(entry["evidence"], "evidence list must be non-empty")
        joined = " ".join(entry["evidence"])
        self.assertIn("DOMAIN_CAPABILITY_ADMISSION_V1", joined)
        self.assertIn("Issue #245", joined)
        self.assertIn("tests/test_p2p_domain_capability_admission_01.py", joined)

    # --- research adoption ledger (append/reconcile only) -------------------

    def test_research_record_exists_once_with_required_fields(self) -> None:
        ids = [r.get("research_id") for r in self.ledger["records"]]
        self.assertEqual(len(ids), len(set(ids)), "duplicate research_id in ledger")
        self.assertEqual(ids.count("RA-EXT-102"), 1)
        # History preserved: the previous tail record is untouched and earlier.
        self.assertIn("RA-EXT-101", ids)
        self.assertLess(ids.index("RA-EXT-101"), ids.index("RA-EXT-102"))
        record = self._ledger_record("RA-EXT-102")
        for field in RECORD_REQUIRED_FIELDS:
            self.assertIn(field, record, field)
        self.assertIn(record["status"], self.ledger["status_vocabulary"])
        # No runtime capability was minted by this governance delta.
        self.assertEqual(record["canonical_capability_ids"], [])

    def test_research_record_carries_selected_and_rejected_lessons(self) -> None:
        record = self._ledger_record("RA-EXT-102")
        selected = " ".join(record["selected_ideas"])
        for idea in SELECTED_IDEAS:
            self.assertIn(idea, selected, idea)
        rejected = " ".join(record["rejected_ideas"]).lower()
        for idea in REJECTED_IDEAS:
            self.assertIn(idea.lower(), rejected, idea)
        self.assertIn("RULE 19", record["p2p_translation"])
        self.assertIn("no new top-level numbered rule", record["p2p_translation"])

    def test_json_ledger_declared_authority_over_projection(self) -> None:
        self.assertIn("the JSON wins", self.projection)
        self.assertIn("RA-EXT-102", self.projection)

    def test_no_runtime_capability_or_service_minted(self) -> None:
        offenders = [
            p.name
            for p in CAPABILITIES.glob("*.py")
            if re.search(r"(admission|benchmark|baseline_probe|capability_registry)", p.name, re.I)
        ]
        self.assertEqual(offenders, [], f"unexpected runtime modules: {offenders}")
        registry = json.loads((CAPABILITIES / "capabilities.json").read_text(encoding="utf-8"))
        minted = [
            c.get("CAPABILITY_ID")
            for c in registry["capabilities"]
            if re.search(r"(domain.capability.admission|admission_v1)", json.dumps(c), re.I)
        ]
        self.assertEqual(minted, [], f"unexpected capability minted: {minted}")

    def test_thin_install_entrypoint_still_thin_and_mentions_subsection(self) -> None:
        # Inheritance discovery: the thin entrypoint names the new RULE 19 body
        # it does not copy, and stays thin (no full rule body).
        self.assertIn("DOMAIN_CAPABILITY_ADMISSION_V1", self.install_source)
        self.assertNotIn(SUBSECTION, self.install_source)
        self.assertNotIn("OWNER_OUTCOME_AND_AUTHORITY_ARE_INVARIANTS", self.install_source)

    # --- portable projection inheritance ------------------------------------

    def test_portable_projection_carries_new_source_identity_and_is_idempotent(self) -> None:
        sys.path.insert(0, str(SCRIPTS))
        import p2p_portable_law_projection as projector

        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            project.mkdir()
            (project / "AGENTS.md").write_text(
                "# Project Specific Rules\n\nKeep this content.\n", encoding="utf-8"
            )

            first = projector.project_law(ROOT, project)
            self.assertEqual(first["status"], "PASS")
            portable = project / ".p2p" / "portable" / "P2P-OPERATIONS-NOTEBOOK.md"
            self.assertTrue(portable.is_file())

            text = portable.read_text(encoding="utf-8")
            # New canonical source identity: projection header + carried body.
            self.assertIn("P2P_PORTABLE_LAW_PROJECTION=YES", text)
            self.assertIn("DOMAIN_CAPABILITY_ADMISSION_V1", text)
            expected_sha = hashlib.sha256(NOTEBOOK.read_bytes()).hexdigest()
            self.assertIn(f"SOURCE_CONTENT_SHA256={expected_sha}", text)

            agents1 = (project / "AGENTS.md").read_bytes()
            portable1 = portable.read_bytes()
            agents_text = agents1.decode("utf-8")
            # Project-specific AGENTS content preserved; exactly one managed block.
            self.assertTrue(agents_text.startswith("# Project Specific Rules"))
            self.assertIn("Keep this content.", agents_text)
            self.assertEqual(agents_text.count("<!-- BEGIN P2P PORTABLE LAW -->"), 1)

            # Second projection/sync run is a byte-identical no-op.
            second = projector.project_law(ROOT, project)
            self.assertEqual(second["status"], "PASS")
            self.assertEqual((project / "AGENTS.md").read_bytes(), agents1)
            self.assertEqual(portable.read_bytes(), portable1)
            self.assertEqual(
                projector.project_law(ROOT, project, check=True)["status"], "PASS"
            )


if __name__ == "__main__":
    unittest.main()
