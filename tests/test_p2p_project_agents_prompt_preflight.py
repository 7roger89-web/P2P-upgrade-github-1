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


class ProjectAgentsPromptPreflightTests(unittest.TestCase):
    def test_generated_prompt_requires_project_agents_preflight(self):
        binding = bind_session(
            session_id="agents-preflight-test",
            host="CLAUDE",
            goal_id="P2P-PROMPT-AGENTS",
            goal="Project AGENTS prompt preflight",
        )
        prompt = build_execution_prompt(
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

        self.assertIn("PROJECT_AGENT_INSTRUCTIONS_PREFLIGHT", prompt)
        self.assertIn("repository-root AGENTS.md", prompt)
        self.assertIn(
            "Treat AGENTS.md as project-specific instructions subordinate to the valid P2P Supreme Law source.",
            prompt,
        )
        self.assertIn(
            "Do not claim AGENTS.md was read unless it actually was.",
            prompt,
        )
        self.assertIn("P2P_SUPREME_LAW_PREFLIGHT", prompt)
        self.assertIn("TASK_CONTRACT_AND_ACCEPTANCE_FIDELITY", prompt)
        self.assertIn("EXECUTOR_INPUT_FORMAT_AND_ARTIFACT_TRANSPORT_FIDELITY", prompt)

        # Runtime-generated prompts must serialize the law-source and OE gates
        # themselves; the executor must not need chat memory to infer them.
        self.assertIn("P2P_RUNTIME_PROMPT_SERIALIZATION_CONTRACT", prompt)
        self.assertIn("P2P_LAW_PREFLIGHT", prompt)
        self.assertIn("P2P_LAW_SOURCE=<actual source>", prompt)
        self.assertIn("OE_GATE", prompt)
        self.assertIn("Không bị over engineering chứ?", prompt)
        self.assertIn("SIMPLER_PATH", prompt)
        self.assertIn("MATERIAL_PROGRESS", prompt)
        self.assertIn("NECESSITY", prompt)
        self.assertIn("CORE_BEFORE_SUPPORT", prompt)
        self.assertIn("SMALLER_VERIFIABLE_SLICE", prompt)
        self.assertIn("OE_VERDICT=DO_IT|SKIP_IT|DEFER_UNTIL_NEEDED", prompt)


if __name__ == "__main__":
    unittest.main()
