from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
for candidate in (REPO_ROOT / "scripts", REPO_ROOT / ".p2p" / "system", REPO_ROOT):
    value = str(candidate)
    if value not in sys.path:
        sys.path.insert(0, value)

import p2p_control_tower as control_tower  # noqa: E402
from p2p_capabilities.control_tower_handoff import SessionBinding, build_execution_prompt  # noqa: E402


class PromptAuthoringDisciplineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.binding = SessionBinding(
            session_id="session-prompt-authoring-v1",
            host="CLAUDE",
            goal_id="PROMPT_AUTHORING_V1",
            goal="Write or revise one bounded executor prompt",
        )
        self.install_text = (
            REPO_ROOT / "docs" / "p2p-development" / "P2P-AGENTS-INSTALL.md"
        ).read_text(encoding="utf-8")

    def _runtime_prompt(self, task: str) -> str:
        with tempfile.TemporaryDirectory() as directory:
            contextual = control_tower._contextual_task_for_session(
                Path(directory),
                self.binding,
                task,
            )
        return build_execution_prompt(self.binding, contextual)

    def test_prompt_authoring_guidance_is_present_only_for_prompt_work(self) -> None:
        prompt = self._runtime_prompt(
            "Revise the supplied executor prompt without changing its bounded outcome."
        )
        ordinary = self._runtime_prompt("Analyze shipment totals and report discrepancies.")

        required = (
            "PROMPT_AUTHORING_DISCIPLINE_V1",
            "PROMPT_INPUT_MATURITY",
            "READY_PROMPT",
            "PARTIAL_DRAFT",
            "CLEAR_SIMPLE_REQUEST",
            "AMBIGUOUS_HIGH_IMPACT",
            "CLARIFICATION_DISCIPLINE",
            "DESTINATION_RESOLUTION",
            "REQUIRED_SKILL_HANDOFF",
            "CAPABILITY_OVER_FOLKLORE",
            "PROPORTIONAL_PROMPT_COMPLEXITY",
            "NO_PRIVATE_CHAIN_OF_THOUGHT_REQUEST",
            "REVISION_CONTINUITY",
            "OUTPUT_SURFACE_FIDELITY",
            "PROMPT_AUTHORING_STOP",
        )
        for marker in required:
            self.assertIn(marker, prompt)
            self.assertNotIn(marker, ordinary)
        self.assertLessEqual(len(prompt), control_tower.PROMPT_GUARD_CHARS)
        self.assertLessEqual(len(ordinary), control_tower.PROMPT_GUARD_CHARS)

    def test_installed_entrypoint_keeps_full_human_readable_discipline(self) -> None:
        required = (
            "## Prompt authoring discipline",
            "PROMPT_AUTHORING_DISCIPLINE_V1",
            "READY_PROMPT",
            "AMBIGUOUS_HIGH_IMPACT",
            "Never re-ask facts already explicit",
            "Do not encode model folklore",
            "Never request private chain-of-thought",
            "return the complete revised prompt",
            "REQUIRED_SKILLS=<ids>",
        )
        for marker in required:
            self.assertIn(marker, self.install_text)

    def test_discipline_is_context_not_parallel_law(self) -> None:
        prompt = self._runtime_prompt("Improve this delegation prompt for Arena.")
        self.assertIn("PROMPT_AUTHORING_DISCIPLINE_V1", prompt)
        self.assertIn("LAW_AUTHORITY=ONE", prompt)
        self.assertIn("not independent laws", prompt)
        self.assertIn("not a second prompt framework", self.install_text)
        self.assertNotIn("PROMPT_AUTHORING_DISCIPLINE_V1", control_tower._handoff.SUPREME_LAW_CAPSULE)


if __name__ == "__main__":
    unittest.main()
