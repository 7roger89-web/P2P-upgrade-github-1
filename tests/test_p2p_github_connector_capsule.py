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


class GitHubConnectorCapsulePropagationTests(unittest.TestCase):
    def _prompt(self, task: str) -> str:
        binding = SessionBinding(
            session_id="github-capsule-propagation",
            host="CODEX",
            goal_id="P2P-GITHUB-CONNECTOR-PROPAGATION",
            goal="Bounded GitHub task",
        )
        with tempfile.TemporaryDirectory() as directory:
            contextual = control_tower._contextual_task_for_session(
                Path(directory),
                binding,
                task,
            )
        return build_execution_prompt(binding, contextual)

    def test_github_guidance_is_present_for_github_work(self):
        prompt = self._prompt("Review GitHub PR, branch, repository and exact HEAD before merge.")

        self.assertIn("GITHUB_GUIDANCE=", prompt)
        self.assertIn("EXECUTOR_GITHUB_ACCESS != OWNER_GITHUB_CONNECTOR_STATUS", prompt)
        self.assertIn("direct repo/PR/HEAD evidence wins", prompt)
        self.assertIn("do not infer account breakage from one unavailable session", prompt)
        self.assertLessEqual(len(prompt), control_tower.PROMPT_GUARD_CHARS)

    def test_github_guidance_is_not_global_supreme_law(self):
        ordinary = self._prompt("Analyze shipment totals and report discrepancies.")
        self.assertNotIn("GITHUB_GUIDANCE=", ordinary)
        self.assertNotIn(
            "EXECUTOR_GITHUB_ACCESS != OWNER_GITHUB_CONNECTOR_STATUS",
            control_tower._handoff.SUPREME_LAW_CAPSULE,
        )
        lines = tuple(
            line for line in control_tower._handoff.SUPREME_LAW_CAPSULE.splitlines() if line.strip()
        )
        self.assertEqual(9, len(lines))

    def test_full_connector_rules_remain_in_canonical_notebook(self):
        notebook = (
            REPO_ROOT / "docs" / "p2p-development" / "P2P-OPERATIONS-NOTEBOOK.md"
        ).read_text(encoding="utf-8")
        for marker in (
            "EXECUTOR_GITHUB_ACCESS=UNAVAILABLE_IN_THIS_SESSION",
            "OWNER_GITHUB_CONNECTOR_STATUS=NOT_PROVEN_BROKEN",
            "REPO_SCOPE_BROKEN",
            "AUTH_CONNECTION_BROKEN",
            "PROVIDER_OUTAGE",
        ):
            self.assertIn(marker, notebook)


if __name__ == "__main__":
    unittest.main()
