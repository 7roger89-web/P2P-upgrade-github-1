"""Bounded bridges for optional Hermes-adjacent tools used by P2P.

These bridges intentionally do *not* make third-party tools authoritative P2P
state. Repomix may create an ephemeral context artifact outside the target
workspace. TokScale is read-only telemetry. Neither bridge installs software,
changes provider/model routing, starts a daemon, submits public data, or gains
permissions beyond the caller's existing process permissions.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


NON_AUTHORITATIVE_TELEMETRY = "TELEMETRY_NON_AUTHORITATIVE"
EPHEMERAL_CONTEXT_ARTIFACT = "EPHEMERAL_CONTEXT_ARTIFACT"


class HermesToolBridgeError(RuntimeError):
    """Base failure for an optional external-tool bridge."""


class ExternalToolUnavailable(HermesToolBridgeError):
    """Raised when an optional external binary is not installed."""


class ExternalToolExecutionFailed(HermesToolBridgeError):
    """Raised when an external tool returns a non-zero exit status."""


class UnsafeBridgeRequest(HermesToolBridgeError):
    """Raised when a request would violate P2P bridge boundaries."""


@dataclass(frozen=True)
class ToolInvocation:
    argv: tuple[str, ...]
    cwd: str | None
    timeout_seconds: int


Runner = Callable[[ToolInvocation], subprocess.CompletedProcess[str]]
Which = Callable[[str], str | None]


def _default_runner(invocation: ToolInvocation) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(invocation.argv),
        cwd=invocation.cwd,
        capture_output=True,
        text=True,
        timeout=invocation.timeout_seconds,
        check=False,
    )


def _is_within(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class RepomixContextBridge:
    """Create a bounded, local Repomix context artifact.

    The bridge exposes only a narrow safe command surface. In particular it has
    no remote-repository option, no arbitrary extra argv, and no way to disable
    Repomix's default secret/security scanning from this API.
    """

    _STYLES = {"markdown", "xml", "json", "plain"}

    def __init__(
        self,
        *,
        binary: str = "repomix",
        runner: Runner | None = None,
        which: Which | None = None,
    ) -> None:
        self.binary = binary
        self._runner = runner or _default_runner
        self._which = which or shutil.which

    def build_invocation(
        self,
        *,
        root: str | os.PathLike[str],
        output_path: str | os.PathLike[str],
        token_budget: int,
        style: str = "markdown",
        compress: bool = False,
        include: tuple[str, ...] = (),
        ignore: tuple[str, ...] = (),
        timeout_seconds: int = 180,
    ) -> ToolInvocation:
        if not isinstance(token_budget, int) or token_budget <= 0:
            raise UnsafeBridgeRequest("REPOMIX_TOKEN_BUDGET_REQUIRED")
        if style not in self._STYLES:
            raise UnsafeBridgeRequest("REPOMIX_STYLE_UNSUPPORTED")
        if not isinstance(timeout_seconds, int) or not 1 <= timeout_seconds <= 3600:
            raise UnsafeBridgeRequest("REPOMIX_TIMEOUT_OUT_OF_RANGE")

        root_path = Path(root).expanduser().resolve()
        output = Path(output_path).expanduser().resolve()
        if not root_path.is_dir():
            raise UnsafeBridgeRequest("REPOMIX_ROOT_NOT_DIRECTORY")
        if _is_within(output, root_path):
            raise UnsafeBridgeRequest("REPOMIX_OUTPUT_MUST_BE_OUTSIDE_TARGET")
        if not output.parent.is_dir():
            raise UnsafeBridgeRequest("REPOMIX_OUTPUT_PARENT_MISSING")

        argv: list[str] = [
            self.binary,
            str(root_path),
            "--output",
            str(output),
            "--style",
            style,
            "--token-budget",
            str(token_budget),
        ]
        if compress:
            argv.append("--compress")
        if include:
            argv.extend(("--include", ",".join(include)))
        if ignore:
            argv.extend(("--ignore", ",".join(ignore)))
        return ToolInvocation(tuple(argv), None, timeout_seconds)

    def pack(self, **kwargs: Any) -> dict[str, Any]:
        if not self._which(self.binary):
            raise ExternalToolUnavailable("REPOMIX_NOT_INSTALLED")
        invocation = self.build_invocation(**kwargs)
        result = self._runner(invocation)
        if result.returncode != 0:
            raise ExternalToolExecutionFailed(
                f"REPOMIX_FAILED:{result.returncode}:{(result.stderr or '').strip()[:500]}"
            )
        output = Path(invocation.argv[invocation.argv.index("--output") + 1])
        if not output.is_file():
            raise ExternalToolExecutionFailed("REPOMIX_OUTPUT_MISSING")
        return {
            "classification": EPHEMERAL_CONTEXT_ARTIFACT,
            "authoritative_state": False,
            "path": str(output),
            "byte_size": output.stat().st_size,
            "sha256": _sha256(output),
            "command": list(invocation.argv),
        }


class TokScaleTelemetryBridge:
    """Read TokScale JSON telemetry without public submission or mutation."""

    _SCOPES: dict[str, tuple[str, ...]] = {
        "summary": (),
        "models": ("models",),
        "monthly": ("monthly",),
    }

    def __init__(
        self,
        *,
        binary: str = "tokscale",
        runner: Runner | None = None,
        which: Which | None = None,
    ) -> None:
        self.binary = binary
        self._runner = runner or _default_runner
        self._which = which or shutil.which

    def build_invocation(
        self,
        *,
        scope: str = "summary",
        timeout_seconds: int = 60,
    ) -> ToolInvocation:
        if scope not in self._SCOPES:
            raise UnsafeBridgeRequest("TOKSCALE_SCOPE_UNSUPPORTED")
        if not isinstance(timeout_seconds, int) or not 1 <= timeout_seconds <= 600:
            raise UnsafeBridgeRequest("TOKSCALE_TIMEOUT_OUT_OF_RANGE")
        argv = (self.binary, *self._SCOPES[scope], "--json")
        return ToolInvocation(tuple(argv), None, timeout_seconds)

    def snapshot(self, *, scope: str = "summary", timeout_seconds: int = 60) -> dict[str, Any]:
        if not self._which(self.binary):
            raise ExternalToolUnavailable("TOKSCALE_NOT_INSTALLED")
        invocation = self.build_invocation(scope=scope, timeout_seconds=timeout_seconds)
        result = self._runner(invocation)
        if result.returncode != 0:
            raise ExternalToolExecutionFailed(
                f"TOKSCALE_FAILED:{result.returncode}:{(result.stderr or '').strip()[:500]}"
            )
        try:
            payload = json.loads(result.stdout or "")
        except json.JSONDecodeError as exc:
            raise ExternalToolExecutionFailed("TOKSCALE_JSON_INVALID") from exc
        return {
            "classification": NON_AUTHORITATIVE_TELEMETRY,
            "authoritative_state": False,
            "scope": scope,
            "payload": payload,
            "command": list(invocation.argv),
        }
