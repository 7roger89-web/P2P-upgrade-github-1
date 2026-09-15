from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = REPO_ROOT / ".p2p" / "system"
if str(SYSTEM_ROOT) not in sys.path:
    sys.path.insert(0, str(SYSTEM_ROOT))

from p2p_capabilities.control_tower_handoff import (  # noqa: E402
    bind_session,
    build_execution_prompt,
)


class PromptAuthoringDisciplineTests(unittest.TestCase):
    def setUp(self) -> None:
        binding = bind_session(
            session_id="session-prompt-authoring-v1",
            host="CLAUDE",
            goal_id="PROMPT_AUTHORING_V1",
            goal="Write or revise one bounded executor prompt",
        )
        self.prompt = build_execution_prompt(
            binding,
            "Revise the supplied executor prompt without changing its bounded outcome.",
            acceptance_criteria=(
                "preserve known constraints",
                "return one executable revised prompt",
            ),
        )
        self.install_text = (
            REPO_ROOT / "docs" / "p2p-development" / "P2P-AGENTS-INSTALL.md"
        ).read_text(encoding="utf-8")

    def test_runtime_prompt_carries_prompt_authoring_discipline(self) -> None:
        required = (
            "PROMPT_AUTHORING_DISCIPLINE_V1",
            "PROMPT_INPUT_MATURITY",
            "READY_PROMPT",
            "PARTIAL_DRAFT",
            "CLEAR_SIMPLE_REQUEST",
            "AMBIGUOUS_HIGH_IMPACT",
            "CLARIFICATION_DISCIPLINE",
            "DESTINATION_RESOLUTION",
            "CAPABILITY_OVER_FOLKLORE",
            "PROPORTIONAL_PROMPT_COMPLEXITY",
            "NO_PRIVATE_CHAIN_OF_THOUGHT_REQUEST",
            "REVISION_CONTINUITY",
            "OUTPUT_SURFACE_FIDELITY",
            "PROMPT_AUTHORING_STOP",
        )
        for marker in required:
            self.assertIn(marker, self.prompt)

    def test_runtime_discipline_suppresses_interview_loops_and_model_folklore(self) -> None:
        self.assertIn("Never re-ask facts already explicit", self.prompt)
        self.assertIn("After one useful clarification round", self.prompt)
        self.assertIn("Fresh destination capability evidence outranks stale prompting folklore", self.prompt)
        self.assertIn("Do not instruct an executor to reveal private chain-of-thought", self.prompt)
        self.assertIn("return the complete revised prompt", self.prompt)
        self.assertNotIn("Claude likes XML", self.prompt)

    def test_installed_entrypoint_exposes_same_bounded_discipline(self) -> None:
        required = (
            "## Prompt authoring discipline",
            "PROMPT_AUTHORING_DISCIPLINE_V1",
            "READY_PROMPT",
            "AMBIGUOUS_HIGH_IMPACT",
            "Never re-ask facts already explicit",
            "Do not encode model folklore",
            "Never request private chain-of-thought",
            "return the complete revised prompt",
        )
        for marker in required:
            self.assertIn(marker, self.install_text)

    def test_discipline_is_assimilation_not_parallel_framework(self) -> None:
        self.assertIn("not a second prompt framework", self.prompt)
        self.assertIn("not a second prompt framework", self.install_text)
        self.assertIn("Reuse the existing P2P task contract", self.prompt)
        self.assertIn("reuses the existing P2P task contract", self.install_text)


if __name__ == "__main__":
    unittest.main()
