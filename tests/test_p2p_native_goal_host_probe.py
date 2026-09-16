from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYSTEM = ROOT / ".p2p" / "system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

from p2p_capabilities.native_goal_bridge import CLAUDE_CODE, CODEX_CLI  # noqa: E402
from p2p_capabilities.native_goal_host_probe import (  # noqa: E402
    READY,
    UNAVAILABLE,
    UNKNOWN,
    probe_native_goal_host,
)


def completed(argv, *, stdout="", stderr="", returncode=0):
    return subprocess.CompletedProcess(argv, returncode, stdout=stdout, stderr=stderr)


class TestNativeGoalHostProbe(unittest.TestCase):
    def test_claude_ready_at_minimum_version(self) -> None:
        calls = []

        def runner(argv, **kwargs):
            calls.append(argv)
            return completed(argv, stdout="2.1.139 (Claude Code)")

        result = probe_native_goal_host(
            CLAUDE_CODE, runner=runner, which=lambda name: "/bin/claude"
        )
        self.assertEqual(result["status"], READY)
        self.assertTrue(result["runtime_confirmation_required"])
        self.assertFalse(result["invocation_proven"])
        self.assertEqual(calls, [["/bin/claude", "--version"]])

    def test_claude_too_old_is_unavailable(self) -> None:
        result = probe_native_goal_host(
            CLAUDE_CODE,
            runner=lambda argv, **kwargs: completed(argv, stdout="2.1.138"),
            which=lambda name: "/bin/claude",
        )
        self.assertEqual(result["status"], UNAVAILABLE)
        self.assertEqual(result["reason"], "CLAUDE_VERSION_TOO_OLD")

    def test_claude_missing_is_unavailable_without_launching(self) -> None:
        result = probe_native_goal_host(CLAUDE_CODE, which=lambda name: None)
        self.assertEqual(result["status"], UNAVAILABLE)
        self.assertFalse(result["launched_host"])

    def test_codex_enabled_is_ready(self) -> None:
        result = probe_native_goal_host(
            CODEX_CLI,
            runner=lambda argv, **kwargs: completed(
                argv, stdout="multi_agent false\ngoals enabled\nother true\n"
            ),
            which=lambda name: "/bin/codex",
        )
        self.assertEqual(result["status"], READY)
        self.assertEqual(result["reason"], "CODEX_GOALS_FEATURE_ENABLED")
        self.assertFalse(result["mutated_config"])

    def test_codex_disabled_returns_official_remediation_without_mutation(self) -> None:
        result = probe_native_goal_host(
            CODEX_CLI,
            runner=lambda argv, **kwargs: completed(argv, stdout="goals disabled\n"),
            which=lambda name: "/bin/codex",
        )
        self.assertEqual(result["status"], UNAVAILABLE)
        self.assertEqual(result["remediation_command"], "codex features enable goals")
        self.assertFalse(result["mutated_config"])

    def test_codex_unparseable_state_is_unknown_not_ready(self) -> None:
        result = probe_native_goal_host(
            CODEX_CLI,
            runner=lambda argv, **kwargs: completed(argv, stdout="experimental feature list\n"),
            which=lambda name: "/bin/codex",
        )
        self.assertEqual(result["status"], UNKNOWN)
        self.assertFalse(result["invocation_proven"])

    def test_probe_never_accepts_unknown_host(self) -> None:
        with self.assertRaisesRegex(ValueError, "HOST_KIND_UNSUPPORTED"):
            probe_native_goal_host("arena")


if __name__ == "__main__":
    unittest.main()
