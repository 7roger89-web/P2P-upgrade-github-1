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


class ProjectAgentsPromptPreflightTests(unittest.TestCase):
    def test_control_tower_prompt_has_one_law_hierarchy_and_project_preflight(self):
        binding = SessionBinding(
            session_id="agents-preflight-test",
            host="CLAUDE",
            goal_id="P2P-PROMPT-AGENTS",
            goal="Project AGENTS prompt preflight",
        )
        with tempfile.TemporaryDirectory() as directory:
            contextual = control_tower._contextual_task_for_session(
                Path(directory),
                binding,
                "Perform one bounded project task.",
                worktree="/tmp/project",
                branch="test/agents-preflight",
                canonical_base_sha="a" * 64,
                canonical_base_tree="b" * 64,
                acceptance_criteria=(
                    "read project AGENTS.md before substantive work when present",
                ),
            )
        prompt = build_execution_prompt(
            binding,
            contextual,
            worktree="/tmp/project",
            branch="test/agents-preflight",
            canonical_base_sha="a" * 64,
            canonical_base_tree="b" * 64,
            acceptance_criteria=(
                "read project AGENTS.md before substantive work when present",
            ),
        )

        self.assertIn("P2P_SUPREME_LAW_PREFLIGHT", prompt)
        self.assertIn("TASK_CONTRACT_AND_ACCEPTANCE_FIDELITY", prompt)
        self.assertIn("EXECUTOR_INPUT_FORMAT_AND_ARTIFACT_TRANSPORT_FIDELITY", prompt)
        self.assertIn("LAW_AUTHORITY=ONE", prompt)
        self.assertIn("P2P_LAW_PREFLIGHT=read root AGENTS.md when present", prompt)
        self.assertIn("P2P_LAW_SOURCE", prompt)
        self.assertIn("never fake a read", prompt)
        self.assertIn("OE_GATE=", prompt)
        self.assertIn("Không bị over engineering chứ?", prompt)
        for marker in (
            "SIMPLER_PATH",
            "MATERIAL_PROGRESS",
            "NECESSITY",
            "CORE_BEFORE_SUPPORT",
            "SMALLER_VERIFIABLE_SLICE",
            "DO_IT|SKIP_IT|DEFER_UNTIL_NEEDED",
        ):
            self.assertIn(marker, prompt)

        # Old standalone preflight text is no longer inflated into the nine-law
        # capsule for the foreground Control Tower runtime.
        self.assertNotIn("PROJECT_AGENT_INSTRUCTIONS_PREFLIGHT", control_tower._handoff.SUPREME_LAW_CAPSULE)
        self.assertNotIn("P2P_RUNTIME_PROMPT_SERIALIZATION_CONTRACT", control_tower._handoff.SUPREME_LAW_CAPSULE)
        self.assertLessEqual(len(prompt), control_tower.PROMPT_GUARD_CHARS)


if __name__ == "__main__":
    unittest.main()
