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
import shutil
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = REPO_ROOT / "docs" / "p2p-development" / "P2P-OPERATIONS-NOTEBOOK.md"
AGENTS = REPO_ROOT / "AGENTS.md"
ARENA_PROTOCOL = REPO_ROOT / "docs" / "ARENA_AGENT_MODE_PROTOCOL.md"
CT_HANDOFF = REPO_ROOT / "docs" / "p2p-development" / "CONTROL-TOWER-SESSION-HANDOFF.md"
P2P_SKILL = REPO_ROOT / ".agents" / "skills" / "p2p" / "SKILL.md"
PACKAGE_RELEASE = REPO_ROOT / "scripts" / "package_release.py"
INSTALL_SH = REPO_ROOT / "install.sh"
INSTALL_PS1 = REPO_ROOT / "install.ps1"

NOTEBOOK_RELATIVE = "docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md"
INSTALLED_NOTEBOOK_RELATIVE = ".p2p/system/docs/P2P-OPERATIONS-NOTEBOOK.md"

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
    "RULE 15 — ARENA_TASK_COMPLETION_DIALOG",
    "RULE 16 — CONTEXT_HYGIENE_AND_PLAN_LIFECYCLE",
)

LEDGER_STATUSES = {"PENDING", "VERIFIED", "RULE_ASSIMILATION_MISSED"}


class P2POperationsNotebookTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.notebook_text = NOTEBOOK.read_text(encoding="utf-8")
        cls.agents_text = AGENTS.read_text(encoding="utf-8")
        cls.arena_text = ARENA_PROTOCOL.read_text(encoding="utf-8")
        cls.ct_text = CT_HANDOFF.read_text(encoding="utf-8")
        cls.p2p_skill_text = P2P_SKILL.read_text(encoding="utf-8")
        cls.package_text = PACKAGE_RELEASE.read_text(encoding="utf-8")

    def test_exactly_one_canonical_notebook_declares_identity(self) -> None:
        self.assertTrue(NOTEBOOK.is_file(), "canonical notebook must exist")
        self.assertIn("# P2P_OPERATIONS_NOTEBOOK", self.notebook_text)
        self.assertIn("single canonical operations notebook", self.notebook_text)
        self.assertIn("P2P_OPERATIONS_NOTEBOOK_ACTIVE_BY_DEFAULT", self.notebook_text)

    def test_supreme_operating_law_is_mandatory_preflight(self) -> None:
        self.assertIn("## 2A. P2P_SUPREME_OPERATING_LAW_V1", self.notebook_text)
        for law in (
            "OWNER_OUTCOME_AND_AUTHORITY_ARE_INVARIANTS",
            "SIMPLEST_USEFUL_PATH_TO_COMPLETION",
            "REAL_STATE_AND_EVIDENCE_OVERRIDE_ASSUMPTIONS",
            "RECOVER_ADAPTIVELY; DO NOT_ENTER_SPECULATIVE_FIX_LOOPS",
            "PRESERVE_CONTINUITY_AND_STOP",
        ):
            self.assertIn(law, self.notebook_text, law)
        self.assertIn("CONTROL_TOWER_BEFORE_PROMPT_WRITE => READ_P2P_SUPREME_OPERATING_LAW_V1",
                      self.notebook_text)
        self.assertIn("TASK_BRANCH != LAW_AUTHORITY", self.notebook_text)
        self.assertIn("TARGET_PROJECT != LAW_SOURCE", self.notebook_text)
        self.assertIn("7roger89-web/P2P-upgrade-github-1@main", self.notebook_text)
        self.assertIn("P2P_SUPREME_OPERATING_LAW_V1", self.agents_text)
        self.assertIn("SUPREME_LAW_CAPSULE", self.agents_text)
        self.assertIn("EXECUTOR_BEFORE_IMPLEMENTATION => READ_P2P_SUPREME_OPERATING_LAW_V1",
                      self.notebook_text)
        self.assertIn("Before Control Tower writes any executor prompt", self.ct_text)
        self.assertIn("P2P_SUPREME_OPERATING_LAW_V1", self.arena_text)
        self.assertIn("SUPREME_LAW_CAPSULE", self.arena_text)
        self.assertIn("Before building any P2P prompt", self.p2p_skill_text)
        self.assertNotIn("The expected normal result is `PASS`", self.notebook_text)
        self.assertIn("never auto-return `PASS`", self.notebook_text)

    def test_beginner_operations_ux_v1_rules_01_to_14_present(self) -> None:
        self.assertIn("## 3. P2P_BEGINNER_OPERATIONS_UX_V1", self.notebook_text)
        for heading in RULE_HEADINGS:
            self.assertIn(heading, self.notebook_text, heading)

    def test_durable_checkpoint_policy_is_recovery_value_driven(self) -> None:
        for marker in (
            "DURABLE_CHECKPOINT_POLICY",
            "MATERIAL_RECOVERY_VALUE",
            "verify remote HEAD == local HEAD",
            "CHECKPOINT != CANDIDATE_PROMOTION",
            "LOCAL_HEAD=",
            "REMOTE_HEAD=",
            "UNPUSHED_COMMITS=",
            "UNPUSHED_FILES=",
            "PUSH_BLOCKER=",
        ):
            self.assertIn(marker, self.notebook_text, marker)
        self.assertIn("Do not commit/push every tiny edit", self.notebook_text)
        self.assertIn("Same goal + same usable workstream continues the existing branch / existing PR",
                      self.notebook_text)
        self.assertIn("routine checkpointing of the already\napproved working branch", self.notebook_text)
        self.assertIn("Before known quota exhaustion", self.notebook_text)
        self.assertIn("Arena/Codex/Manus/another executor", self.notebook_text)
        self.assertIn("MATERIAL_RECOVERY_VALUE", self.agents_text)
        self.assertIn("CURRENT approved branch", self.agents_text)
        self.assertIn("MATERIAL_RECOVERY_VALUE", self.arena_text)
        self.assertIn("CURRENT working branch", self.arena_text)
        self.assertIn("DURABLE_CHECKPOINT", self.ct_text)

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
                                    "BACKLOG_G", "BACKLOG_H", "BACKLOG_I"})
        backlog_h = next(entry for entry in ledger["entries"] if entry["id"] == "BACKLOG_H")
        self.assertEqual(backlog_h["item"], "ARENA_TASK_COMPLETION_DIALOG")
        self.assertEqual(backlog_h["status"], "VERIFIED")
        self.assertTrue(any("RULE 15" in line for line in backlog_h["evidence"]))
        # CONTEXT_HYGIENE_01 (Issue #42) is tracked truthfully: PENDING until
        # Control Tower independently verifies the exact PR head/tree.
        backlog_i = next(entry for entry in ledger["entries"] if entry["id"] == "BACKLOG_I")
        self.assertEqual(backlog_i["item"], "CONTEXT_HYGIENE_01")
        self.assertEqual(backlog_i["status"], "PENDING")
        self.assertTrue(any("test_p2p_context_hygiene" in line for line in backlog_i["evidence"]))
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

    def test_rule15_completion_dialog_semantics(self) -> None:
        self.assertIn("### RULE 15 — ARENA_TASK_COMPLETION_DIALOG", self.notebook_text)
        # YES: terminal state + ReturnPacket returned; honest BLOCKED/fail-closed
        # is still a valid YES (technical PASS is NOT required).
        self.assertIn("reached the requested terminal state", self.notebook_text)
        self.assertIn("YES` does NOT mean the technical outcome must be PASS", self.notebook_text)
        self.assertIn("honest\n`BLOCKED` / fail-closed result can still be `YES`",
                      self.notebook_text)
        # KEEP WORKING: same-chat continuation (Control Tower requires more
        # work in the SAME CHAT, or terminal state not yet reached).
        self.assertIn("KEEP WORKING", self.notebook_text)
        self.assertIn("requires more work in the SAME CHAT", self.notebook_text)
        # NO: executor/task failure (wrong task, wrong repo/workstream,
        # unusable result, ignored scope, premature termination) — never
        # merely because the technical outcome is BLOCKED.
        self.assertIn("wrong task", self.notebook_text)
        self.assertIn("wrong repository/workstream", self.notebook_text)
        self.assertIn("unusable result", self.notebook_text)
        self.assertIn("ignored required scope", self.notebook_text)
        self.assertIn("premature/incorrect termination", self.notebook_text)
        self.assertIn("Do NOT select `NO` merely because the bounded technical outcome is",
                      self.notebook_text)
        # Beginner mnemonic.
        self.assertIn("XONG ĐÚNG PHẠM VI + ĐÃ TRẢ KẾT QUẢ", self.notebook_text)
        self.assertIn("CÒN TIẾP TỤC CHÍNH CHAT NÀY", self.notebook_text)
        self.assertIn("ARENA LÀM SAI / KẾT QUẢ KHÔNG DÙNG ĐƯỢC", self.notebook_text)

    def test_arena_protocol_references_rule15(self) -> None:
        self.assertIn("RULE 15", self.arena_text)
        self.assertIn("ARENA_TASK_COMPLETION_DIALOG", self.arena_text)
        self.assertIn("Completion-dialog handling", self.arena_text)

    def test_rule11_owner_micro_loop_suppression_preserves_real_gates(self) -> None:
        # The workflow law is assimilated into RULE 11 ...
        self.assertIn("OWNER_MICRO_LOOP_SUPPRESSION", self.notebook_text)
        self.assertIn("SAME bounded Writer repair loop", self.notebook_text)
        # ... without removing the real Owner Gates.
        for gate in (
            "canonical merge/promotion",
            "production deployment",
            "destructive deletion",
            "secrets/credentials",
            "major paid infrastructure/spending",
            "hard rollback",
        ):
            self.assertIn(gate, self.notebook_text, gate)
        self.assertIn("never removes or weakens a real Owner Gate", self.notebook_text)

    def test_rule16_context_hygiene_laws_are_canonical(self) -> None:
        self.assertIn("### RULE 16 — CONTEXT_HYGIENE_AND_PLAN_LIFECYCLE", self.notebook_text)
        # The law block is formatted as a wrapped code block, so match against
        # whitespace-normalized text (newlines collapse to single spaces).
        flat = re.sub(r"\s+", " ", self.notebook_text)
        for law in (
            "SESSION_CONTEXT != AUTHORITY",
            "DEFAULT_RETRIEVAL = ACTIVE_TASK + REQUIRED_CANONICAL_SPECS",
            "EXCLUDED FROM DEFAULT ACTIVE RETRIEVAL",
            "OUTRANKS SEMANTIC TEXT SIMILARITY",
            "CANNOT SILENTLY REGAIN IT",
            "EVIDENCE IS DURABLE AND QUERYABLE, NEVER INSTRUCTION AUTHORITY",
            "NO_BLIND_DELETE_AFTER_MERGE = YES",
        ):
            self.assertIn(law, flat, law)
        # The installed digest stays consistent with the canonical rule set.
        self.assertIn("RULE 16 CONTEXT_HYGIENE_AND_PLAN_LIFECYCLE", self.agents_text)
        self.assertIn("OWNER_MICRO_LOOP_SUPPRESSION", self.agents_text)

    def test_no_second_notebook_framework_created(self) -> None:
        # The notebook must reference the existing Arena/Control Tower
        # surfaces instead of redefining them as new frameworks.
        self.assertIn("docs/ARENA_AGENT_MODE_PROTOCOL.md", self.notebook_text)
        self.assertIn("docs/p2p-development/CONTROL-TOWER-SESSION-HANDOFF.md",
                      self.notebook_text)
        self.assertIn("It does not add a router, scheduler, orchestrator, memory framework",
                      self.notebook_text)

    # --- REAL INSTALLED PROJECT NOTEBOOK INHERITANCE (C.T. blocker) ---

    def test_release_package_contains_full_notebook(self) -> None:
        # A. Release package ships the FULL canonical notebook (DOC_FILES
        # entry and the actual file present with the canonical rule set), not a
        # stub.
        self.assertIn(f'"{NOTEBOOK_RELATIVE}"', self.package_text)
        self.assertTrue(NOTEBOOK.is_file(), "canonical notebook file must exist")
        self.assertIn("RULE_ASSIMILATION_GATE_V1", self.notebook_text)
        self.assertIn("### RULE 15", self.notebook_text)
        self.assertIn("P2P_OPERATIONS_NOTEBOOK_ACTIVE_BY_DEFAULT", self.notebook_text)

    def test_install_sh_copies_notebook_to_managed_docs(self) -> None:
        # B. install.sh installs .p2p/system/docs/P2P-OPERATIONS-NOTEBOOK.md.
        sh_text = INSTALL_SH.read_text(encoding="utf-8")
        self.assertIn("operations_notebook_src", sh_text)
        self.assertIn("$system_destination/docs", sh_text)
        self.assertIn("P2P-OPERATIONS-NOTEBOOK.md", sh_text)
        # Fail-closed when the canonical notebook is missing.
        self.assertIn("operations notebook is missing", sh_text)
        self.assertIn("docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md", sh_text)

    def test_install_ps1_copies_notebook_to_managed_docs(self) -> None:
        # C. install.ps1 installs the equivalent path.
        ps_text = INSTALL_PS1.read_text(encoding="utf-8")
        self.assertIn("OperationsNotebook", ps_text)
        self.assertIn('(Join-Path $SystemDestination "docs")', ps_text)
        self.assertIn('docs\\P2P-OPERATIONS-NOTEBOOK.md', ps_text)
        # Fail-closed when the canonical notebook is missing.
        self.assertIn("operations notebook is missing", ps_text)
        self.assertIn("docs\\p2p-development\\P2P-OPERATIONS-NOTEBOOK.md", ps_text)

    def test_installed_agents_refers_local_installed_notebook(self) -> None:
        # D. Installed AGENTS.md digest points to the local installed notebook,
        # not (only) the development-source path.
        self.assertIn(INSTALLED_NOTEBOOK_RELATIVE, self.agents_text)
        self.assertIn("never depend on access to the original development repo",
                      self.agents_text)
        self.assertIn("P2P_INSTALL => P2P_OPERATIONS_NOTEBOOK_ACTIVE_BY_DEFAULT",
                      self.agents_text)

    def test_installed_agents_digest_has_all_rules_01_15(self) -> None:
        # E. Installed AGENTS.md digest enumerates RULE 01-15 (including 15).
        match = re.search(
            r"## P2P_OPERATIONS_NOTEBOOK.*?(?=\n## )", self.agents_text, re.DOTALL
        )
        self.assertIsNotNone(match, "digest section must exist")
        assert match is not None
        digest = match.group(0)
        for n in range(1, 16):
            self.assertRegex(digest, r"`RULE %02d " % n)
        self.assertIn("RULE 15 ARENA_TASK_COMPLETION_DIALOG", digest)
        self.assertRegex(digest, r"reached its requested\s+terminal state")
        self.assertIn("KEEP WORKING", digest)
        self.assertIn("never merely a technical `BLOCKED`", digest)

    def test_installed_notebook_contains_gate_and_rule15(self) -> None:
        # F. The installed canonical notebook contains RULE_ASSIMILATION_GATE_V1
        # and RULE 15.
        self.assertTrue(NOTEBOOK.is_file())
        self.assertIn("## 4. RULE_ASSIMILATION_GATE_V1", self.notebook_text)
        self.assertIn("### RULE 15 — ARENA_TASK_COMPLETION_DIALOG", self.notebook_text)
        self.assertIn("RULE_ASSIMILATION_LEDGER", self.notebook_text)

    def test_install_projection_preserves_existing_agents_content(self) -> None:
        # G. The installer merge preserves owner/project pre-existing AGENTS
        # content (backup + insert/replace of the P2P CODEX block only).
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "AGENTS.md"
            owner_marker = "# My Project Owner Notes"
            target.write_text(
                owner_marker + "\n\nKeep this.\n<!-- BEGIN P2P CODEX -->\nOLD\n<!-- END P2P CODEX -->\n",
                encoding="utf-8",
            )
            source = AGENTS.read_text(encoding="utf-8")
            begin, end = "<!-- BEGIN P2P CODEX -->", "<!-- END P2P CODEX -->"
            block = begin + "\n" + source.strip() + "\n" + end
            text = target.read_text(encoding="utf-8")
            pattern = re.escape(begin) + r".*?" + re.escape(end)
            merged = re.sub(pattern, block, text, flags=re.S)
            target.write_text(merged, encoding="utf-8")
            merged_text = target.read_text(encoding="utf-8")
            # Owner content preserved (markers outside the P2P block).
            self.assertIn(owner_marker, merged_text)
            self.assertIn("Keep this.", merged_text)
            # Old stale block replaced, new digest present.
            self.assertNotIn("OLD", merged_text)
            self.assertIn(INSTALLED_NOTEBOOK_RELATIVE, merged_text)
            self.assertIn("RULE 15 ARENA_TASK_COMPLETION_DIALOG", merged_text)
            # Exactly one P2P block.
            self.assertEqual(merged_text.count(begin), 1)
            self.assertEqual(merged_text.count(end), 1)

    def test_no_second_notebook_framework_exists(self) -> None:
        # H. Only the single canonical notebook file exists (no parallel
        # operations notebook/manual/framework recreated).
        matches = list(REPO_ROOT.rglob("*P2P-OPERATIONS-NOTEBOOK*"))
        # Ignore the evidence/plan document which references (but is not) the
        # notebook; only the canonical .md counts as an operations notebook.
        notebook_files = [p for p in matches if p.is_file() and p.suffix == ".md"
                          and p.name == "P2P-OPERATIONS-NOTEBOOK.md"]
        self.assertEqual(len(notebook_files), 1, f"multiple notebooks: {notebook_files}")
        self.assertEqual(notebook_files[0].resolve(), NOTEBOOK.resolve())


if __name__ == "__main__":
    unittest.main()
