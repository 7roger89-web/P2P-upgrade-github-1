"""Native-first bridge for optional external code-structure evidence.

P2P already has a canonical native code-impact evidence contract in
``quality_intelligence.py`` based on stdlib AST/import analysis. That native
path remains first choice. This bridge exists only for a *documented residual
gap* that native analysis cannot establish well enough, for example a
cross-language call path or a richer semantic/architecture query.

The bridge intentionally does not install, configure, index, watch, daemonize,
serve UI, manage ADRs, or grant authority to codebase-memory-mcp. It can query
an already-existing local index through the upstream one-shot CLI mode and
returns non-authoritative supplemental structural evidence.

Upstream research pin for this contract:
DeusData/codebase-memory-mcp v0.11.0
commit 8972ea69c6ad94b1ef1d4ffbf0a92d78d2db1798

P2P project files, native impact evidence, tests, task state, FACT/evidence and
canonical governance remain authoritative. External graph output is evidence
candidate only.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from typing import Any, Callable, Mapping


NON_AUTHORITATIVE_STRUCTURAL_EVIDENCE = "NON_AUTHORITATIVE_STRUCTURAL_EVIDENCE"
NATIVE_FIRST_FALLBACK = "NATIVE_FIRST_FALLBACK"
UPSTREAM_RESEARCH_PIN = "DeusData/codebase-memory-mcp@8972ea69c6ad94b1ef1d4ffbf0a92d78d2db1798"
DEFAULT_BINARY = "codebase-memory-mcp"
MAX_OUTPUT_BYTES = 2_000_000
MIN_NATIVE_GAP_REASON_CHARS = 12

# Only query surfaces that can add structural/impact evidence beyond the
# existing native contract. Deliberately absent: install, update, config,
# index_repository, manage_adr, daemon, UI and arbitrary Cypher.
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
    native_gap_reason: str


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


def _validated_gap_reason(native_gap_reason: str) -> str:
    reason = str(native_gap_reason or "").strip()
    if len(reason) < MIN_NATIVE_GAP_REASON_CHARS:
        raise UnsafeCodeIntelligenceRequest("CODE_INTEL_NATIVE_GAP_REASON_REQUIRED")
    return reason


class CodebaseMemoryEvidenceBridge:
    """Query an existing external index only after native evidence is insufficient.

    ``quality_intelligence.affected_surface`` and related native code-impact
    evidence are the default. The caller must state the concrete residual gap
    before this bridge can build or execute an external query. This keeps the
    external graph a supplemental evidence provider rather than a competing
    index/truth authority.

    The bridge never calls ``index_repository``; provisioning/index creation
    remains an explicit external setup decision rather than a side effect of
    verification.
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
        native_gap_reason: str,
        timeout_seconds: int = 60,
    ) -> CodeIntelligenceInvocation:
        gap_reason = _validated_gap_reason(native_gap_reason)
        if tool not in READ_ONLY_TOOLS:
            raise UnsafeCodeIntelligenceRequest(f"CODE_INTEL_TOOL_NOT_ALLOWED:{tool}")
        if not isinstance(arguments, Mapping) or not arguments:
            raise UnsafeCodeIntelligenceRequest("CODE_INTEL_ARGUMENTS_REQUIRED")
        project = arguments.get("project")
        if not isinstance(project, str) or not project.strip():
            raise UnsafeCodeIntelligenceRequest("CODE_INTEL_PROJECT_REQUIRED")
        if not isinstance(timeout_seconds, int) or not 1 <= timeout_seconds <= 300:
            raise UnsafeCodeIntelligenceRequest("CODE_INTEL_TIMEOUT_OUT_OF_RANGE")

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
        return CodeIntelligenceInvocation(argv, stdin_json, timeout_seconds, gap_reason)

    def query(
        self,
        *,
        tool: str,
        arguments: Mapping[str, Any],
        native_gap_reason: str,
        timeout_seconds: int = 60,
    ) -> dict[str, Any]:
        if not self._which(self.binary):
            raise CodeIntelligenceUnavailable("CODEBASE_MEMORY_MCP_NOT_INSTALLED")

        invocation = self.build_invocation(
            tool=tool,
            arguments=arguments,
            native_gap_reason=native_gap_reason,
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
            "activation_policy": NATIVE_FIRST_FALLBACK,
            "native_gap_reason": invocation.native_gap_reason,
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
