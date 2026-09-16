from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SYSTEM_ROOT = os.path.join(REPO_ROOT, ".p2p", "system")
if SYSTEM_ROOT not in sys.path:
    sys.path.insert(0, SYSTEM_ROOT)

from p2p_capabilities.code_intelligence_bridge import (  # noqa: E402
    CodeIntelligenceExecutionFailed,
    CodeIntelligenceUnavailable,
    CodebaseMemoryEvidenceBridge,
    NON_AUTHORITATIVE_STRUCTURAL_EVIDENCE,
    UnsafeCodeIntelligenceRequest,
)


def _completed(stdout: str, *, returncode: int = 0, stderr: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(
        args=["codebase-memory-mcp"],
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
    )


class CodeIntelligenceBridgeTests(unittest.TestCase):
    def test_bridge_builds_one_shot_json_cli_query(self) -> None:
        bridge = CodebaseMemoryEvidenceBridge(which=lambda _: "/usr/bin/codebase-memory-mcp")
        invocation = bridge.build_invocation(
            tool="search_graph",
            arguments={"project": "p2p", "name_pattern": ".*Bridge.*", "label": "Function"},
        )

        self.assertEqual(
            invocation.argv,
            (
                "codebase-memory-mcp",
                "cli",
                "--quiet",
                "search_graph",
                "--format",
                "json",
            ),
        )
        self.assertEqual(
            json.loads(invocation.stdin_json),
            {"project": "p2p", "name_pattern": ".*Bridge.*", "label": "Function"},
        )

    def test_bridge_rejects_mutating_or_control_plane_tools(self) -> None:
        bridge = CodebaseMemoryEvidenceBridge()
        for tool in (
            "index_repository",
            "manage_adr",
            "query_graph",
            "config",
            "install",
            "daemon",
        ):
            with self.subTest(tool=tool):
                with self.assertRaises(UnsafeCodeIntelligenceRequest):
                    bridge.build_invocation(tool=tool, arguments={"project": "p2p"})

    def test_bridge_requires_project_and_bounded_timeout(self) -> None:
        bridge = CodebaseMemoryEvidenceBridge()
        with self.assertRaisesRegex(UnsafeCodeIntelligenceRequest, "PROJECT_REQUIRED"):
            bridge.build_invocation(tool="get_architecture", arguments={"project": ""})
        with self.assertRaisesRegex(UnsafeCodeIntelligenceRequest, "TIMEOUT_OUT_OF_RANGE"):
            bridge.build_invocation(
                tool="get_architecture",
                arguments={"project": "p2p"},
                timeout_seconds=301,
            )

    def test_query_returns_non_authoritative_structural_evidence(self) -> None:
        seen = {}

        def runner(invocation):
            seen["invocation"] = invocation
            return _completed('{"functions":12,"routes":3}')

        bridge = CodebaseMemoryEvidenceBridge(
            runner=runner,
            which=lambda _: "/usr/bin/codebase-memory-mcp",
        )
        result = bridge.query(
            tool="get_architecture",
            arguments={"project": "p2p"},
        )

        self.assertEqual(result["classification"], NON_AUTHORITATIVE_STRUCTURAL_EVIDENCE)
        self.assertIs(result["authoritative_state"], False)
        self.assertIs(result["standing_process_started_by_bridge"], False)
        self.assertIs(result["index_created_by_bridge"], False)
        self.assertEqual(result["payload"], {"functions": 12, "routes": 3})
        self.assertEqual(json.loads(seen["invocation"].stdin_json), {"project": "p2p"})

    def test_query_fails_closed_when_binary_is_missing(self) -> None:
        bridge = CodebaseMemoryEvidenceBridge(which=lambda _: None)
        with self.assertRaisesRegex(CodeIntelligenceUnavailable, "NOT_INSTALLED"):
            bridge.query(tool="get_architecture", arguments={"project": "p2p"})

    def test_query_fails_closed_on_invalid_json_or_command_failure(self) -> None:
        invalid = CodebaseMemoryEvidenceBridge(
            runner=lambda _: _completed("not-json"),
            which=lambda _: "/usr/bin/codebase-memory-mcp",
        )
        with self.assertRaisesRegex(CodeIntelligenceExecutionFailed, "JSON_INVALID"):
            invalid.query(tool="get_architecture", arguments={"project": "p2p"})

        failed = CodebaseMemoryEvidenceBridge(
            runner=lambda _: _completed("", returncode=2, stderr="bad request"),
            which=lambda _: "/usr/bin/codebase-memory-mcp",
        )
        with self.assertRaisesRegex(CodeIntelligenceExecutionFailed, "COMMAND_FAILED:2"):
            failed.query(
                tool="trace_path",
                arguments={"project": "p2p", "function_name": "run"},
            )


if __name__ == "__main__":
    unittest.main()
