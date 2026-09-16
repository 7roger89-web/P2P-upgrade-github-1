import json
import subprocess

import pytest

from p2p_capabilities.code_intelligence_bridge import (
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


def test_bridge_builds_one_shot_json_cli_query() -> None:
    bridge = CodebaseMemoryEvidenceBridge(which=lambda _: "/usr/bin/codebase-memory-mcp")
    invocation = bridge.build_invocation(
        tool="search_graph",
        arguments={"project": "p2p", "name_pattern": ".*Bridge.*", "label": "Function"},
    )

    assert invocation.argv == (
        "codebase-memory-mcp",
        "cli",
        "--quiet",
        "search_graph",
        "--format",
        "json",
    )
    assert json.loads(invocation.stdin_json) == {
        "project": "p2p",
        "name_pattern": ".*Bridge.*",
        "label": "Function",
    }


def test_bridge_rejects_mutating_or_control_plane_tools() -> None:
    bridge = CodebaseMemoryEvidenceBridge()
    for tool in (
        "index_repository",
        "manage_adr",
        "query_graph",
        "config",
        "install",
        "daemon",
    ):
        with pytest.raises(UnsafeCodeIntelligenceRequest):
            bridge.build_invocation(tool=tool, arguments={"project": "p2p"})


def test_bridge_requires_project_and_bounded_timeout() -> None:
    bridge = CodebaseMemoryEvidenceBridge()
    with pytest.raises(UnsafeCodeIntelligenceRequest, match="PROJECT_REQUIRED"):
        bridge.build_invocation(tool="get_architecture", arguments={"project": ""})
    with pytest.raises(UnsafeCodeIntelligenceRequest, match="TIMEOUT_OUT_OF_RANGE"):
        bridge.build_invocation(
            tool="get_architecture",
            arguments={"project": "p2p"},
            timeout_seconds=301,
        )


def test_query_returns_non_authoritative_structural_evidence() -> None:
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

    assert result["classification"] == NON_AUTHORITATIVE_STRUCTURAL_EVIDENCE
    assert result["authoritative_state"] is False
    assert result["standing_process_started_by_bridge"] is False
    assert result["index_created_by_bridge"] is False
    assert result["payload"] == {"functions": 12, "routes": 3}
    assert json.loads(seen["invocation"].stdin_json) == {"project": "p2p"}


def test_query_fails_closed_when_binary_is_missing() -> None:
    bridge = CodebaseMemoryEvidenceBridge(which=lambda _: None)
    with pytest.raises(CodeIntelligenceUnavailable, match="NOT_INSTALLED"):
        bridge.query(tool="get_architecture", arguments={"project": "p2p"})


def test_query_fails_closed_on_invalid_json_or_command_failure() -> None:
    invalid = CodebaseMemoryEvidenceBridge(
        runner=lambda _: _completed("not-json"),
        which=lambda _: "/usr/bin/codebase-memory-mcp",
    )
    with pytest.raises(CodeIntelligenceExecutionFailed, match="JSON_INVALID"):
        invalid.query(tool="get_architecture", arguments={"project": "p2p"})

    failed = CodebaseMemoryEvidenceBridge(
        runner=lambda _: _completed("", returncode=2, stderr="bad request"),
        which=lambda _: "/usr/bin/codebase-memory-mcp",
    )
    with pytest.raises(CodeIntelligenceExecutionFailed, match="COMMAND_FAILED:2"):
        failed.query(tool="trace_path", arguments={"project": "p2p", "function_name": "run"})
