"""Semantic contract tests for RULE 20 executor autonomy routing.

RULE 20 (OWNER_EXECUTOR_SELECTION_AND_AUTONOMOUS_COMPLETION) canonicalizes
one Owner UX across P2P-managed projects: "Tiep tuc cong viec, dung
CatDesk / Arena / Auto". The project Control Tower owns executor routing
and drives the approved mission with EXECUTION_MODE=AUTONOMOUS_UNTIL_TERMINAL.

These checks are deliberately semantic, not giant-string snapshots: they
assert the canonical tokens and intents exist in the right artifacts, while
prose may evolve.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = REPO_ROOT / "docs" / "p2p-development" / "P2P-OPERATIONS-NOTEBOOK.md"
AGENTS = REPO_ROOT / "AGENTS.md"
INSTALL_SOURCE = REPO_ROOT / "docs" / "p2p-development" / "P2P-AGENTS-INSTALL.md"
ARENA_PROTOCOL = REPO_ROOT / "docs" / "ARENA_AGENT_MODE_PROTOCOL.md"

RULE20_HEADING = "RULE 20 — OWNER_EXECUTOR_SELECTION_AND_AUTONOMOUS_COMPLETION"
RULE21_HEADING = "RULE 21 — BEGINNER_PLAIN_LANGUAGE_FIRST"


def _rule20_section(notebook_text: str) -> str:
    start = notebook_text.index("### " + RULE20_HEADING)
    end = notebook_text.index("### " + RULE21_HEADING, start)
    return notebook_text[start:end]


def _rule21_section(notebook_text: str) -> str:
    start = notebook_text.index("### " + RULE21_HEADING)
    end = notebook_text.index("## 4. RULE_ASSIMILATION_GATE_V1", start)
    return notebook_text[start:end]


class ExecutorAutonomyRoutingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.notebook_text = NOTEBOOK.read_text(encoding="utf-8")
        cls.agents_text = AGENTS.read_text(encoding="utf-8")
        cls.install_text = INSTALL_SOURCE.read_text(encoding="utf-8")
        cls.arena_text = ARENA_PROTOCOL.read_text(encoding="utf-8")
        cls.rule20 = _rule20_section(cls.notebook_text)
        cls.rule21 = _rule21_section(cls.notebook_text)
        cls.flat = re.sub(r"\s+", " ", cls.rule20)
        cls.flat21 = re.sub(r"\s+", " ", cls.rule21)

    def test_rule20_exists_in_canonical_notebook(self) -> None:
        self.assertIn("### " + RULE20_HEADING, self.notebook_text)
        self.assertIn("## 3. P2P_BEGINNER_OPERATIONS_UX_V1", self.notebook_text)
        # RULE 20 sits inside the beginner rule set, before the assimilation gate.
        ux_start = self.notebook_text.index("## 3. P2P_BEGINNER_OPERATIONS_UX_V1")
        rule_start = self.notebook_text.index("### " + RULE20_HEADING)
        gate_start = self.notebook_text.index("## 4. RULE_ASSIMILATION_GATE_V1")
        self.assertLess(ux_start, rule_start)
        self.assertLess(rule_start, gate_start)

    def test_digest_law_exposes_new_semantics(self) -> None:
        # Development-repo digest names the new rule and its core semantics.
        self.assertIn("RULE 20 OWNER_EXECUTOR_SELECTION_AND_AUTONOMOUS_COMPLETION",
                      self.agents_text)
        self.assertIn("rules 01-21 in the notebook", self.agents_text)
        self.assertIn("AUTONOMOUS_UNTIL_TERMINAL", self.agents_text)
        # Installed thin entrypoint advertises the extended rule range so a
        # normal installed project discovers RULE 20 via the installed
        # notebook projection (installers copy the full notebook wholesale).
        self.assertIn("RULE 01–21", self.install_text)
        # ... while staying thin: full rule bodies are never copied there.
        self.assertNotIn(RULE20_HEADING, self.install_text)
        self.assertIn("not copied here", self.install_text)

    def test_owner_commands_canonicalized(self) -> None:
        for command in (
            "dùng CatDesk",
            "dùng Arena",
            "dùng Auto",
        ):
            self.assertIn(command, self.rule20, command)
        self.assertIn("Tiếp tục công việc", self.rule20)
        # Natural-language equivalents match by intent, not exact syntax.
        self.assertIn("matched by intent", self.flat)

    def test_control_tower_owns_executor_routing(self) -> None:
        self.assertIn("CONTROL_TOWER_OWNS_EXECUTOR_ROUTING=YES", self.rule20)
        self.assertIn("OWNER_IS_NOT_MESSAGE_BUS=YES", self.rule20)
        for step in (
            "FRESH_CHECK",
            "RECOVER_DURABLE_MISSION_STATE",
            "READ_ACTIVE_SUPREME_LAW",
            "READ_PROJECT_AGENTS_SPEC_STATE",
            "RESOLVE_UNFINISHED_BOUNDED_GOAL",
            "SELECT_OR_CONFIRM_EXECUTOR",
            "CREATE_INTERNAL_EXECUTION_CONTRACT",
            "INVOKE_EXECUTOR_WHEN_DIRECTLY_AVAILABLE",
            "SUPERVISE_EXECUTION",
            "VERIFY_EVIDENCE",
            "CONTINUE_UNTIL_TERMINAL",
        ):
            self.assertIn(step, self.rule20, step)
        self.assertIn("PROMPT_IS_TASK_DELTA", self.rule20)

    def test_autonomous_until_terminal_contract(self) -> None:
        self.assertIn("EXECUTION_MODE=AUTONOMOUS_UNTIL_TERMINAL", self.rule20)
        for terminal in ("MISSION_COMPLETE", "HARD_OWNER_GATE", "HARD_BLOCK"):
            self.assertIn(terminal, self.rule20, terminal)
        self.assertIn("TERMINAL_STATES = MISSION_COMPLETE | HARD_OWNER_GATE | HARD_BLOCK",
                      self.flat)
        for loop_step in (
            "PLAN_MINIMUM_NEXT_STEP",
            "DIAGNOSE",
            "REPAIR",
            "RETEST",
            "CONTINUE automatically",
            "FINAL_VERIFY",
        ):
            self.assertIn(loop_step, self.flat, loop_step)

    def test_intermediate_pass_is_not_mission_complete(self) -> None:
        self.assertIn("INTERMEDIATE_PASS != MISSION_COMPLETE", self.rule20)
        for non_terminal in (
            "subtask PASS",
            "test PASS",
            "one repair",
            "one file completed",
            "one commit completed",
            "one validation-lane PASS",
            "one intermediate goal PASS",
        ):
            self.assertIn(non_terminal, self.flat, non_terminal)
        # No continue-nagging for clear safe in-scope next actions.
        self.assertIn("Do you want me to continue?", self.rule20)

    def test_catdesk_selector_with_direct_invocation(self) -> None:
        self.assertIn("CATDESK_AVAILABLE_IN_CURRENT_CONVERSATION=<YES|NO>", self.rule20)
        self.assertIn("DIRECT invocation is required", self.flat)
        self.assertIn("CONTROL_TOWER=YES", self.rule20)
        self.assertIn("LOCAL_EXECUTION_BACKEND=YES", self.rule20)
        for context_field in (
            "PROJECT",
            "MISSION",
            "LOCAL_REPO",
            "CANONICAL_LAW",
            "DURABLE_BASE",
            "APPROVED_SCOPE",
            "DEFINITION_OF_DONE",
            "VALIDATION_REQUIREMENTS",
            "HARD_OWNER_GATES",
            "RETURN_CONTRACT",
        ):
            self.assertIn(context_field, self.rule20, context_field)

    def test_owner_relay_removed_on_direct_catdesk_path(self) -> None:
        flat = self.flat
        self.assertIn("Do NOT instruct the Owner to open a separate CatDesk chat", flat)
        self.assertIn("Do NOT output a CatDesk relay prompt for the Owner", flat)
        self.assertIn(
            "The Owner is not required to relay CatDesk prompts when direct invocation exists",
            flat)
        self.assertIn("the prompt plumbing", flat)

    def test_catdesk_workspace_and_safe_bootstrap(self) -> None:
        self.assertIn("P2P_WORKSPACE", self.rule20)
        self.assertIn("P2P-upgrade-github-1", self.rule20)
        for bootstrap in (
            "clone if absent",
            "verify remote",
            "require clean worktree",
            "pull --ff-only",
            "never overwrite",
        ):
            self.assertIn(bootstrap, self.flat, bootstrap)
        self.assertIn("GitHub remains durable authority", self.flat)
        # Prohibitions stay explicit.
        for prohibition in (
            "no destructive reset/stash/overwrite",
            "no secret harvesting",
            "no scope expansion",
        ):
            self.assertIn(prohibition, self.flat, prohibition)

    def test_catdesk_unavailable_fails_closed(self) -> None:
        self.assertIn("CATDESK_CAPABILITY_REQUIRED", self.rule20)
        flat = self.flat
        self.assertIn("fail closed", flat)
        self.assertIn("minimum beginner action", flat)
        self.assertIn("Do NOT generate a large relay prompt by default", flat)
        self.assertIn("resumes from durable state", flat)
        self.assertIn("Never claim cross-chat automatic dispatch", flat)

    def test_arena_selector_aligned_with_rule15(self) -> None:
        self.assertIn("ARENA_AGENT_MODE_PROTOCOL.md", self.rule20)
        self.assertIn("extends", self.flat)
        self.assertIn("RULE 15", self.rule20)
        self.assertIn("ARENA_TASK_COMPLETION_DIALOG", self.rule20)
        self.assertIn("does not duplicate it", self.flat)
        self.assertIn("KEEP WORKING", self.rule20)
        # ONE complete packet, not a micro-prompt relay chain.
        self.assertIn("ONE complete Arena execution packet", self.flat)
        # The Arena protocol itself is the session contract; RULE 20 links
        # to it instead of redefining it.
        self.assertIn("P2P_SUPREME_OPERATING_LAW_V1", self.arena_text)

    def test_auto_selector_is_routing_policy(self) -> None:
        self.assertIn("AUTO_IS_ROUTING_POLICY_NOT_EXECUTOR=YES", self.rule20)
        self.assertIn("ACTUALLY AVAILABLE", self.rule20)
        self.assertIn("AUTO must not invent", self.flat)
        self.assertIn("EXECUTOR_SELECTED=<executor>", self.rule20)
        self.assertIn("SELECTION_REASON=<one concise factual reason>", self.rule20)
        for evidence in (
            "task requirements",
            "environment suitability",
            "local repo availability",
            "durable-state accessibility",
            "cost/quota",
        ):
            self.assertIn(evidence, self.flat, evidence)
        # Routing transparency reuses RULE 18; it is referenced, not rebuilt.
        self.assertIn("RULE 18", self.rule20)
        self.assertIn("OWNER_CHALLENGE_SUMMARY", self.rule20)

    def test_no_silent_executor_drift(self) -> None:
        self.assertIn("do not silently", self.flat)
        for field in (
            "EXECUTOR_SWITCH_FROM=",
            "EXECUTOR_SWITCH_TO=",
            "REASON=",
            "DURABLE_CHECKPOINT=",
        ):
            self.assertIn(field, self.rule20, field)

    def test_owner_gates_preserved(self) -> None:
        self.assertIn("does NOT grant blanket authority", self.flat)
        self.assertIn("RULE 11", self.rule20)
        self.assertIn("VALIDATED_PR_AUTO_MERGE_AUTHORITY", self.rule20)
        for gate in (
            "release/promotion",
            "production deploy",
            "production data mutation",
            "destructive deletion",
            "secrets/credentials",
            "major paid spending",
            "hard rollback",
            "force push/reset",
            "external communication",
        ):
            self.assertIn(gate, self.flat, gate)
        self.assertIn("invents no merge policy", self.flat)

    def test_no_new_daemon_or_orchestrator_required(self) -> None:
        flat = self.flat
        self.assertIn("It creates no", flat)
        for forbidden in (
            "daemon",
            "server",
            "orchestration service",
            "agent framework",
            "routing subsystem",
            "persistent background process",
        ):
            self.assertIn(forbidden, flat, forbidden)
        self.assertIn("policy/protocol over existing Control Tower", flat)

    def test_beginner_mnemonic_present(self) -> None:
        flat = self.flat
        self.assertIn("CONTROL TOWER TỰ GỌI CATDESK", flat)
        self.assertIn("OWNER KHÔNG CHUYỂN PROMPT", flat)
        self.assertIn("CONTROL TOWER TỰ CHỌN NGƯỜI LÀM PHÙ HỢP", flat)


    def test_rule21_beginner_plain_language_contract(self) -> None:
        self.assertIn("### " + RULE21_HEADING, self.notebook_text)
        self.assertIn("PLAIN_LANGUAGE_FIRST=YES", self.rule21)
        self.assertIn("RETURN_PACKET != OWNER_EXPLANATION", self.rule21)
        self.assertIn("NOT_RUN != FAIL", self.rule21)
        self.assertIn("NOT_OBSERVED != NO", self.rule21)
        self.assertIn("BLOCKED_BY_ENVIRONMENT != PRODUCT_DEFECT", self.rule21)

    def test_rule21_distinguishes_unverified_from_failed(self) -> None:
        self.assertIn("not verified rather than as observed failures", self.flat21)
        self.assertIn("chưa kiểm tra được vì thiếu công cụ/điều kiện", self.rule21)
        self.assertIn("visual gate failed", self.rule21)

    def test_rule21_reuses_rule09_for_one_action(self) -> None:
        self.assertIn("RULE 09 — ONE_ACTION_NOW_FOR_BEGINNER", self.rule21)
        self.assertIn("instead of creating a second action rule", self.flat21)

    def test_rule21_owner_wording_is_neutral_and_digest_is_exposed(self) -> None:
        self.assertIn("BẠN CẦN LÀM GÌ BÂY GIỜ", self.rule21)
        self.assertNotIn("MÀY CẦN LÀM GÌ BÂY GIỜ", self.rule21)
        self.assertIn("RULE 21 BEGINNER_PLAIN_LANGUAGE_FIRST", self.agents_text)
        self.assertIn("RETURN_PACKET != OWNER_EXPLANATION", self.agents_text)
        self.assertIn("NOT_OBSERVED != NO", self.agents_text)

    def test_rule21_install_entrypoint_stays_thin(self) -> None:
        self.assertIn("RULE 01–21", self.install_text)
        self.assertIn("Owner-facing explanations must be plain-language first", self.install_text)
        self.assertNotIn(RULE21_HEADING, self.install_text)

if __name__ == "__main__":
    unittest.main()
