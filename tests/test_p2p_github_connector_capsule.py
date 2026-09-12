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


EXPECTED_GITHUB_CONNECTOR_MARKERS = (
    "EXECUTOR_GITHUB_ACCESS != OWNER_GITHUB_CONNECTOR_STATUS",
    "ONE_FAILED_CALL != GITHUB_CONNECTOR_DISABLED",
    "SESSION_TOOL_UNAVAILABLE != ACCOUNT_CONNECTION_BROKEN",
    "GITHUB_CONNECTOR_STATUS=SESSION_SURFACE_UNAVAILABLE",
    "REPO_SCOPE_BROKEN",
    "AUTH_CONNECTION_BROKEN",
    "PROVIDER_OUTAGE",
    "EXECUTOR_GITHUB_ACCESS=UNAVAILABLE_IN_THIS_SESSION",
    "OWNER_GITHUB_CONNECTOR_STATUS=NOT_PROVEN_BROKEN",
)


class GitHubConnectorCapsulePropagationTests(unittest.TestCase):
    def test_generated_prompt_carries_github_failure_classification(self):
        binding = bind_session(
            session_id="github-capsule-propagation",
            host="CODEX",
            goal_id="P2P-GITHUB-CONNECTOR-PROPAGATION",
            goal="Propagate GitHub connector failure classification",
        )
        prompt = build_execution_prompt(
            binding,
            "Verify generated prompt carries connector failure classification.",
        )

        for marker in EXPECTED_GITHUB_CONNECTOR_MARKERS:
            with self.subTest(marker=marker):
                self.assertIn(marker, prompt)

    def test_capsule_forbids_public_web_as_private_github_proof(self):
        binding = bind_session(
            session_id="github-private-proof",
            host="ARENA",
            goal_id="P2P-GITHUB-CONNECTOR-PROPAGATION",
            goal="Keep private GitHub claims fail-closed",
        )
        prompt = build_execution_prompt(binding, "Check a private PR.")

        self.assertIn(
            "Public web search is not proof of private repository, branch, PR, or HEAD state.",
            prompt,
        )


if __name__ == "__main__":
    unittest.main()
