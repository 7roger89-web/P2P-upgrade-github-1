"""Regression contract for the Roger UI/UX lean-workflow integration.

This test is intentionally safe before activation:
- it always protects the single-authority architecture;
- it validates the durable integration packet;
- once the unique lean-workflow marker appears in p2p-uiux, the full marker
  contract becomes mandatory.
"""

from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
UIUX = REPO_ROOT / ".agents" / "skills" / "p2p-uiux" / "SKILL.md"
PARALLEL = REPO_ROOT / ".agents" / "skills" / "roger-ui-ux"
PACKET = REPO_ROOT / "docs" / "p2p-development" / "ROGER-UI-UX-V1-INTEGRATION.md"

ACTIVATION_MARKER = (
    "PROJECT TRUTH -> USER JOB -> INFORMATION PRIORITY -> REUSE -> "
    "LAYOUT DECISION -> IMPLEMENT -> RENDER -> VERIFY"
)


class P2PUIUXLeanWorkflowContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.uiux = UIUX.read_text(encoding="utf-8")
        cls.packet = PACKET.read_text(encoding="utf-8")

    def test_existing_p2p_uiux_remains_the_only_p2p_uiux_authority(self) -> None:
        self.assertTrue(UIUX.is_file())
        self.assertFalse(
            PARALLEL.exists(),
            "Do not create a parallel roger-ui-ux authority inside P2P.",
        )
        self.assertIn("P2P_PARALLEL_UIUX_SKILL=NO", self.packet)
        self.assertIn("P2P_INTEGRATION_TARGET=existing p2p-uiux", self.packet)

    def test_integration_packet_preserves_existing_runtime_boundaries(self) -> None:
        for marker in (
            "SOURCE_REVIEW != RUNTIME_VISUAL_REVIEW",
            "provider-neutral browser capability classification",
            "read-only review safety",
            "Aesthetica as optional/noncanonical",
            "eight-member canonical governance denominator",
            "RUNTIME_CONTRACT_PRESERVE=YES",
        ):
            self.assertIn(marker, self.packet, marker)

    def test_integration_packet_contains_the_lean_workflow_contract(self) -> None:
        for marker in (
            "UI_AUDIT=<stack>",
            "ARRIVE=<why the user comes here>",
            "DECIDE=<what they inspect or compare>",
            "ACT=<primary action or next operational step>",
            "EXCEPTIONS=<states that materially change the decision>",
            "BUILD",
            "REDESIGN",
            "AUDIT",
            "SYSTEM",
            "VISUAL_REGRESSION",
            ACTIVATION_MARKER,
            "existing project component",
            "Minimum Owner Gate",
            "attention and action outrank decoration",
            "Design-system restraint",
        ):
            self.assertIn(marker, self.packet, marker)

    def test_once_activated_the_skill_must_contain_the_complete_contract(self) -> None:
        if ACTIVATION_MARKER not in self.uiux:
            self.skipTest("Lean workflow integration is documented but not active yet.")

        for marker in (
            "UI_AUDIT=<stack>",
            "ARRIVE=<why the user comes here>",
            "DECIDE=<what they inspect or compare>",
            "ACT=<primary action or next operational step>",
            "EXCEPTIONS=<states that materially change the decision>",
            "BUILD",
            "REDESIGN",
            "AUDIT",
            "SYSTEM",
            "VISUAL_REGRESSION",
            "existing project component",
            "Owner Gate",
            "attention and action outrank decoration",
        ):
            self.assertIn(marker, self.uiux, marker)

        # Existing evidence/safety boundaries must survive the integration.
        for marker in (
            "SOURCE_REVIEW",
            "RUNTIME_VISUAL_REVIEW",
            "RUNTIME_UI_REVIEW_REQUIRED=YES",
            "CLICK_CAPABILITY != WRITE_AUTHORITY",
            "CHROME_DEVTOOLS_MCP",
            "PLAYWRIGHT",
            "HOST_BROWSER",
            "p2p_aesthetica",
        ):
            self.assertIn(marker, self.uiux, marker)


if __name__ == "__main__":
    unittest.main()
