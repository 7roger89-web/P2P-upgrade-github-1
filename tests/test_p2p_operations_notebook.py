"""Structural validation for the canonical P2P operations notebook.

P2P_OPERATIONS_NOTEBOOK is the single canonical operations-memory artifact
for P2P-installed projects. These checks are deliberately structural and
lightweight: exactly one canonical notebook, the beginner rule set, the
rule-assimilation gate with its machine-readable ledger, install inheritance
through the AGENTS.md entrypoint, and Arena/Control Tower linkage.
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = REPO_ROOT / "docs" / "p2p-development" / "P2P-OPERATIONS-NOTEBOOK.md"
AGENTS = REPO_ROOT / "AGENTS.md"
ARENA_PROTOCOL = REPO_ROOT / "docs" / "ARENA_AGENT_MODE_PROTOCOL.md"
CT_HANDOFF = REPO_ROOT / "docs" / "p2p-development" / "CONTROL-TOWER-SESSION-HANDOFF.md"
PACKAGE_RELEASE = REPO_ROOT / "scripts" / "package_release.py"

NOTEBOOK_RELATIVE = "docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md"

RULE_HEADINGS = (
    "RULE 01 — EXPLICIT_DESTINATION",
    "RULE 02 — CHAT_TITLE_REQUIRED",
    "RULE 03 — SAME_CHAT_MUST_NAME_CHAT",
    "RULE 04 — GITHUB_IS_DURABLE_CHECKPOINT",
    "RULE 05 — SESSION_OR_QUOTA_RECOVERY",
    "RULE 06 — NO_DUPLICATE_PR",
    "RULE 07 — WRITER_BOUNDARY",
    "RULE 08 — INDEPENDENT_SUPERVISOR",
    "RULE 09 — ONE_ACTION_NOW_FOR_BEGINNER",
    "RULE 10 — SUCCESS_SIGNAL_AND_RETURN",
    "RULE 11 — OWNER_GATE_ONLY_WHEN_REAL",
    "RULE 12 — MINIMUM_SUFFICIENT_WORK",
    "RULE 13 — CONTROL_TOWER_STATE_RESPONSIBILITY",
    "RULE 14 — OVER_ENGINEERING_CHECK",
)

LEDGER_STATUSES = {"PENDING", "VERIFIED", "RULE_ASSIMILATION_MISSED"}


class P2POperationsNotebookTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.notebook_text = NOTEBOOK.read_text(encoding="utf-8")
        cls.agents_text = AGENTS.read_text(encoding="utf-8")
        cls.arena_text = ARENA_PROTOCOL.read_text(encoding="utf-8")
        cls.ct_text = CT_HANDOFF.read_text(encoding="utf-8")
        cls.package_text = PACKAGE_RELEASE.read_text(encoding="utf-8")

    def test_exactly_one_canonical_notebook_declares_identity(self) -> None:
        self.assertTrue(NOTEBOOK.is_file(), "canonical notebook must exist")
        self.assertIn("# P2P_OPERATIONS_NOTEBOOK", self.notebook_text)
        self.assertIn("single canonical operations notebook", self.notebook_text)
        self.assertIn("P2P_OPERATIONS_NOTEBOOK_ACTIVE_BY_DEFAULT", self.notebook_text)

    def test_beginner_operations_ux_v1_rules_01_to_14_present(self) -> None:
        self.assertIn("## 3. P2P_BEGINNER_OPERATIONS_UX_V1", self.notebook_text)
        for heading in RULE_HEADINGS:
            self.assertIn(heading, self.notebook_text, heading)

    def test_rule_assimilation_gate_v1_present_with_status_vocabulary(self) -> None:
        self.assertIn("## 4. RULE_ASSIMILATION_GATE_V1", self.notebook_text)
        self.assertIn("RULE_ASSIMILATION_STATUS=PENDING", self.notebook_text)
        self.assertIn("RULE_ASSIMILATION_STATUS=VERIFIED", self.notebook_text)
        self.assertIn("RULE_ASSIMILATION_MISSED", self.notebook_text)
        self.assertIn("RULE_ASSIMILATED=YES", self.notebook_text)

    def test_machine_readable_ledger_is_valid_and_truthful(self) -> None:
        match = re.search(r"```json\n(.*?)\n```", self.notebook_text, re.DOTALL)
        self.assertIsNotNone(match, "machine-readable ledger must exist")
        assert match is not None
        ledger = json.loads(match.group(1))
        self.assertEqual(ledger["schema"], "p2p-rule-assimilation-ledger/1")
        self.assertEqual(ledger["gate"], "RULE_ASSIMILATION_GATE_V1")
        ids = [entry["id"] for entry in ledger["entries"]]
        self.assertEqual(set(ids), {"BACKLOG_A", "BACKLOG_B", "BACKLOG_C",
                                    "BACKLOG_D", "BACKLOG_E", "BACKLOG_F",
                                    "BACKLOG_G"})
        for entry in ledger["entries"]:
            self.assertIn(entry["status"], LEDGER_STATUSES, entry["id"])
            self.assertIsInstance(entry["evidence"], list)
            self.assertTrue(entry["evidence"], entry["id"])

    def test_install_inheritance_through_agents_md_entrypoint(self) -> None:
        # install.sh / install.ps1 project package AGENTS.md into every
        # installed project as the BEGIN/END P2P CODEX block; the digest in
        # that block must declare the notebook and the rule sets.
        self.assertIn("## P2P_OPERATIONS_NOTEBOOK (install-inherited operations memory)",
                      self.agents_text)
        self.assertIn("P2P_INSTALL => P2P_OPERATIONS_NOTEBOOK_ACTIVE_BY_DEFAULT",
                      self.agents_text)
        self.assertIn(NOTEBOOK_RELATIVE, self.agents_text)
        self.assertIn("RULE_ASSIMILATION_GATE_V1", self.agents_text)

    def test_arena_protocol_discovers_notebook(self) -> None:
        self.assertIn("## 11. P2P operations notebook discovery", self.arena_text)
        self.assertIn(NOTEBOOK_RELATIVE, self.arena_text)
        self.assertIn("P2P_OPERATIONS_NOTEBOOK", self.arena_text)

    def test_control_tower_handoff_discovers_notebook(self) -> None:
        self.assertIn("P2P operations notebook", self.ct_text)
        self.assertIn(NOTEBOOK_RELATIVE, self.ct_text)
        self.assertIn("P2P_BEGINNER_OPERATIONS_UX_V1", self.ct_text)
        self.assertIn("RULE_ASSIMILATION_GATE_V1", self.ct_text)

    def test_release_projection_includes_notebook(self) -> None:
        self.assertIn(f'"{NOTEBOOK_RELATIVE}"', self.package_text)

    def test_no_second_notebook_framework_created(self) -> None:
        # The notebook must reference the existing Arena/Control Tower
        # surfaces instead of redefining them as new frameworks.
        self.assertIn("docs/ARENA_AGENT_MODE_PROTOCOL.md", self.notebook_text)
        self.assertIn("docs/p2p-development/CONTROL-TOWER-SESSION-HANDOFF.md",
                      self.notebook_text)
        self.assertIn("It does not add a router, scheduler, orchestrator, memory framework",
                      self.notebook_text)


if __name__ == "__main__":
    unittest.main()
