"""Bounded read-only bridge for optional codebase structural evidence.

The bridge intentionally does not install, configure, index, watch, daemonize,
serve UI, manage ADRs, or grant authority to codebase-memory-mcp. It can query
an already-existing local index through the upstream one-shot CLI mode and
returns non-authoritative structural evidence for P2P Evidence-First review.

Upstream research pin for this contract:
DeusData/codebase-memory-mcp v0.11.0
commit 8972ea69c6ad94b1ef1d4ffbf0a92d78d2db1798

P2P project files, tests, task state, FACT/evidence and canonical governance
remain authoritative. External graph output is evidence candidate only.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from typing import Any, Callable, Mapping


NON_AUTHORITATIVE_STRUCTURAL_EVIDENCE = "NON_AUTHORITATIVE_STRUCTURAL_EVIDENCE"
UPSTREAM_RESEARCH_PIN = "DeusData/codebase-memory-mcp@8972ea69c6ad94b1ef1d4ffbf0a92d78d2db1798"
DEFAULT_BINARY = "codebase-memory-mcp"
MAX_OUTPUT_BYTES = 2_000_000

# Only query surfaces that are useful for structural/impact evidence and are
# documented as query/analysis operations. Deliberately absent: install,
# update, config, index_repository, manage_adr, daemon, UI and arbitrary Cypher.
READ_ONLY_TOOLS = frozenset(
    {
        "get_architecture",
        "search_graph",
        "trace_path",
    }
)


class CodeIntelligenceBridgeError(RuntimeError):
    """Base failure for the optional structural-evidence bridge."""


class CodeIntelligenceUnavailable(CodeIntelligenceBridgeError):
    """Raised when the optional upstream binary is not installed."""


class UnsafeCodeIntelligenceRequest(CodeIntelligenceBridgeError):
    """Raised when a request exceeds the bounded read-only surface."""


class CodeIntelligenceExecutionFailed(CodeIntelligenceBridgeError):
    """Raised when the upstream command fails or returns invalid evidence."""


@dataclass(frozen=True)
class CodeIntelligenceInvocation:
    argv: tuple[str, ...]
    stdin_json: str
    timeout_seconds: int


Runner = Callable[[CodeIntelligenceInvocation], subprocess.CompletedProcess[str]]
Which = Callable[[str], str | None]


def _default_runner(invocation: CodeIntelligenceInvocation) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(invocation.argv),
        input=invocation.stdin_json,
        capture_output=True,
        text=True,
        timeout=invocation.timeout_seconds,
        check=False,
    )


def _json_size(value: Any) -> int:
    return len(json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))


class CodebaseMemoryEvidenceBridge:
    """Query an existing codebase-memory-mcp index without gaining authority.

    The upstream README documents one-shot CLI mode as independent from its
    standing coordination daemon. P2P uses only that shape here. The bridge
    never calls ``index_repository``; provisioning/index creation remains an
    explicit external setup decision rather than a side effect of verification.
    """

    def __init__(
        self,
        *,
        binary: str = DEFAULT_BINARY,
        runner: Runner | None = None,
        which: Which | None = None,
    ) -> None:
        self.binary = binary
        self._runner = runner or _default_runner
        self._which = which or shutil.which

    def build_invocation(
        self,
        *,
        tool: str,
        arguments: Mapping[str, Any],
        timeout_seconds: int = 60,
    ) -> CodeIntelligenceInvocation:
        if tool not in READ_ONLY_TOOLS:
            raise UnsafeCodeIntelligenceRequest(f"CODE_INTEL_TOOL_NOT_ALLOWED:{tool}")
        if not isinstance(arguments, Mapping) or not arguments:
            raise UnsafeCodeIntelligenceRequest("CODE_INTEL_ARGUMENTS_REQUIRED")
        project = arguments.get("project")
        if not isinstance(project, str) or not project.strip():
            raise UnsafeCodeIntelligenceRequest("CODE_INTEL_PROJECT_REQUIRED")
        if not isinstance(timeout_seconds, int) or not 1 <= timeout_seconds <= 300:
            raise UnsafeCodeIntelligenceRequest("CODE_INTEL_TIMEOUT_OUT_OF_RANGE")

        # P2P never needs megabytes of request parameters. This also prevents a
        # caller from abusing the bridge as a generic payload transport.
        payload = dict(arguments)
        if _json_size(payload) > 64_000:
            raise UnsafeCodeIntelligenceRequest("CODE_INTEL_ARGUMENTS_TOO_LARGE")

        stdin_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        argv = (
            self.binary,
            "cli",
            "--quiet",
            tool,
            "--format",
            "json",
        )
        return CodeIntelligenceInvocation(argv, stdin_json, timeout_seconds)

    def query(
        self,
        *,
        tool: str,
        arguments: Mapping[str, Any],
        timeout_seconds: int = 60,
    ) -> dict[str, Any]:
        if not self._which(self.binary):
            raise CodeIntelligenceUnavailable("CODEBASE_MEMORY_MCP_NOT_INSTALLED")

        invocation = self.build_invocation(
            tool=tool,
            arguments=arguments,
            timeout_seconds=timeout_seconds,
        )
        result = self._runner(invocation)
        if result.returncode != 0:
            stderr = (result.stderr or "").strip()[:500]
            raise CodeIntelligenceExecutionFailed(
                f"CODE_INTEL_COMMAND_FAILED:{result.returncode}:{stderr}"
            )

        stdout = result.stdout or ""
        if len(stdout.encode("utf-8")) > MAX_OUTPUT_BYTES:
            raise CodeIntelligenceExecutionFailed("CODE_INTEL_OUTPUT_TOO_LARGE")
        try:
            payload = json.loads(stdout)
        except json.JSONDecodeError as exc:
            raise CodeIntelligenceExecutionFailed("CODE_INTEL_JSON_INVALID") from exc

        return {
            "classification": NON_AUTHORITATIVE_STRUCTURAL_EVIDENCE,
            "authoritative_state": False,
            "source": "codebase-memory-mcp-cli",
            "upstream_research_pin": UPSTREAM_RESEARCH_PIN,
            "tool": tool,
            "project": str(arguments["project"]),
            "payload": payload,
            "command": list(invocation.argv),
            "standing_process_started_by_bridge": False,
            "index_created_by_bridge": False,
        }
