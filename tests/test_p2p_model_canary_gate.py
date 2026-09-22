"""Focused structural checks for MODEL_CANARY_GATE_V1.

The gate is policy over existing RULE 19 and existing Arena/DesignArena
surfaces. It must not grow into a second router, benchmark service, or model
identity detector.
"""

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "docs" / "p2p-development" / "P2P-OPERATIONS-NOTEBOOK.md"
ARENA = ROOT / "docs" / "ARENA_AGENT_MODE_PROTOCOL.md"
DESIGN = ROOT / "docs" / "p2p-development" / "DESIGNARENA-EXECUTION-PLAYBOOK.md"
AGENTS = ROOT / "AGENTS.md"
INSTALL = ROOT / "docs" / "p2p-development" / "P2P-AGENTS-INSTALL.md"


class ModelCanaryGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.notebook = NOTEBOOK.read_text(encoding="utf-8")
        cls.arena = ARENA.read_text(encoding="utf-8")
        cls.design = DESIGN.read_text(encoding="utf-8")
        cls.agents = AGENTS.read_text(encoding="utf-8")
        cls.install = INSTALL.read_text(encoding="utf-8")

    def test_gate_is_subordinate_to_existing_reality_first_rule(self):
        self.assertIn("### RULE 19 — REALITY_FIRST_CAPABILITY_PROBE", self.notebook)
        self.assertIn("#### MODEL_CANARY_GATE_V1", self.notebook)
        self.assertIn("bounded application of RULE 19", self.notebook)
        self.assertIn("must not create a new router, benchmark", self.notebook)

    def test_canary_measures_session_not_hidden_model_identity(self):
        self.assertIn("SESSION_QUALITY != MODEL_IDENTITY", self.notebook)
        self.assertIn("model identity", self.arena.lower())
        self.assertIn("MODEL_IDENTITY=UNKNOWN", self.arena)
        self.assertIn("never infers model/provider/reasoning level", self.arena)
        self.assertIn("never asks the tested Arena session to grade itself", self.arena)

    def test_gate_is_risk_proportional_and_anti_reroll_gambling(self):
        self.assertIn("Default to FAST_CANARY: ONE task-representative probe only", self.notebook)
        self.assertIn("REAL_TASK_FIRST_SLICE = CANARY", self.notebook)
        self.assertIn("second or third tiny probe only", self.notebook)
        self.assertIn("Skip the gate for low-risk/mechanical work", self.notebook)
        self.assertIn("one evidence-justified fresh-session reroll", self.arena)
        self.assertIn("do not\nreroll repeatedly to gamble", self.arena)

    def test_fast_canary_has_simple_keep_limit_reroll_contract(self):
        for token in (
            "FAST_CANARY_V1",
            "CANARY_RESULT=GREEN | YELLOW | RED",
            "TOOL_HALLUCINATION=YES | NO",
            "UNNECESSARY_SCOPE=YES | NO",
            "NEXT=CONTINUE_REAL_TASK | LIMIT_TASK | REROLL_OR_SWITCH",
        ):
            self.assertIn(token, self.notebook)
            self.assertIn(token, self.arena)
        self.assertIn("continue the real task immediately in the same session", self.arena)

    def test_pelican_is_not_a_general_model_ranking(self):
        self.assertIn("FIXED_PELICAN_PROMPT != MODEL_RANKING", self.notebook)
        self.assertIn("Randomize the animal/vehicle pair", self.notebook)
        self.assertIn("Không chạy \"bồ nông đạp xe\" trước mỗi tournament", self.design)

    def test_designarena_uses_blind_real_prompt_tournament(self):
        for token in (
            "DESIGNARENA_TOURNAMENT_IS_SELECTION_GATE=YES",
            "FOUR_MODELS_SAME_PROMPT=YES",
            "BLIND_OUTPUT_FIRST=YES",
            "GUESS_MODEL_BEFORE_VOTE=NO",
            "SEPARATE_PELICAN_CANARY_BEFORE_REAL_PROMPT=NO",
        ):
            self.assertIn(token, self.design)
        self.assertIn("acceptance matrix", self.design)
        self.assertIn("không suy model", self.design)

    def test_installed_and_development_entrypoints_discover_gate(self):
        self.assertIn("MODEL_CANARY_GATE_V1", self.agents)
        self.assertIn("MODEL_CANARY_GATE_V1", self.install)


if __name__ == "__main__":
    unittest.main()
