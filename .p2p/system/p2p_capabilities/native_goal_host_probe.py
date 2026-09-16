"""Conservative host capability probe for P2P native ``/goal`` use.

This module does not enable features, launch a second host, or claim that a
slash command was invoked.  It answers only whether the local CLI surface is
ready enough for P2P to attempt the existing host-native ``/goal`` command.
Actual invocation remains a host/session action and requires an invocation
receipt before P2P may claim that native goal mode was used.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Sequence

try:
    from .native_goal_bridge import CLAUDE_CODE, CODEX_CLI, HOST_KINDS
except ImportError:  # Support direct execution from the installed module path.
    runtime_root = Path(__file__).resolve().parents[1]
    if str(runtime_root) not in sys.path:
        sys.path.insert(0, str(runtime_root))
    from p2p_capabilities.native_goal_bridge import CLAUDE_CODE, CODEX_CLI, HOST_KINDS  # type: ignore[no-redef]

PROBE_SCHEMA = "p2p-native-goal-host-probe/1"
READY = "READY_TO_INVOKE"
UNAVAILABLE = "UNAVAILABLE"
UNKNOWN = "UNKNOWN"
MIN_CLAUDE_CODE_VERSION = (2, 1, 139)

_VERSION_RE = re.compile(r"(?<!\d)(\d+)\.(\d+)\.(\d+)(?!\d)")
_CODEX_GOALS_RE = re.compile(
    r"^\s*goals\b.*?\b(enabled|disabled|true|false|on|off)\b",
    re.IGNORECASE | re.MULTILINE,
)

Runner = Callable[..., subprocess.CompletedProcess[str]]
Which = Callable[[str], str | None]


def _run(
    argv: Sequence[str],
    *,
    runner: Runner = subprocess.run,
    timeout: float = 8.0,
) -> subprocess.CompletedProcess[str]:
    return runner(
        list(argv),
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def _version(text: str) -> tuple[int, int, int] | None:
    match = _VERSION_RE.search(text)
    if match is None:
        return None
    return tuple(int(part) for part in match.groups())  # type: ignore[return-value]


def _base(host_kind: str) -> dict[str, Any]:
    return {
        "schema": PROBE_SCHEMA,
        "host_kind": host_kind,
        "mutated_config": False,
        "launched_host": False,
        "invocation_proven": False,
        "owner_prompt_required": False,
    }


def _probe_claude(
    *, runner: Runner = subprocess.run, which: Which = shutil.which
) -> dict[str, Any]:
    base = _base(CLAUDE_CODE)
    binary = which("claude")
    if not binary:
        return {**base, "status": UNAVAILABLE, "reason": "CLAUDE_CLI_NOT_FOUND"}
    try:
        completed = _run((binary, "--version"), runner=runner)
    except (OSError, subprocess.SubprocessError) as exc:
        return {
            **base,
            "status": UNKNOWN,
            "reason": "CLAUDE_VERSION_PROBE_FAILED",
            "error_class": type(exc).__name__,
        }
    output = "\n".join((completed.stdout or "", completed.stderr or ""))
    version = _version(output)
    if completed.returncode != 0 or version is None:
        return {**base, "status": UNKNOWN, "reason": "CLAUDE_VERSION_UNVERIFIED"}
    version_text = ".".join(str(part) for part in version)
    if version < MIN_CLAUDE_CODE_VERSION:
        return {
            **base,
            "status": UNAVAILABLE,
            "reason": "CLAUDE_VERSION_TOO_OLD",
            "observed_version": version_text,
            "minimum_version": "2.1.139",
        }
    return {
        **base,
        "status": READY,
        "reason": "CLAUDE_CLI_VERSION_SUPPORTS_GOAL",
        "observed_version": version_text,
        "minimum_version": "2.1.139",
        "runtime_confirmation_required": True,
        "runtime_limitations": [
            "workspace trust must already be accepted",
            "managed hook policy must permit /goal",
        ],
    }


def _probe_codex(
    *, runner: Runner = subprocess.run, which: Which = shutil.which
) -> dict[str, Any]:
    base = _base(CODEX_CLI)
    binary = which("codex")
    if not binary:
        return {**base, "status": UNAVAILABLE, "reason": "CODEX_CLI_NOT_FOUND"}
    try:
        completed = _run((binary, "features", "list"), runner=runner)
    except (OSError, subprocess.SubprocessError) as exc:
        return {
            **base,
            "status": UNKNOWN,
            "reason": "CODEX_FEATURE_PROBE_FAILED",
            "error_class": type(exc).__name__,
        }
    output = "\n".join((completed.stdout or "", completed.stderr or ""))
    if completed.returncode != 0:
        return {**base, "status": UNKNOWN, "reason": "CODEX_FEATURE_LIST_FAILED"}
    match = _CODEX_GOALS_RE.search(output)
    if match is None:
        return {
            **base,
            "status": UNKNOWN,
            "reason": "CODEX_GOALS_STATE_UNVERIFIED",
            "remediation_command": "codex features enable goals",
        }
    enabled = match.group(1).lower() in {"enabled", "true", "on"}
    if not enabled:
        return {
            **base,
            "status": UNAVAILABLE,
            "reason": "CODEX_GOALS_DISABLED",
            "remediation_command": "codex features enable goals",
        }
    return {
        **base,
        "status": READY,
        "reason": "CODEX_GOALS_FEATURE_ENABLED",
        "runtime_confirmation_required": True,
    }


def probe_native_goal_host(
    host_kind: str,
    *,
    runner: Runner = subprocess.run,
    which: Which = shutil.which,
) -> dict[str, Any]:
    """Probe one supported host without mutating configuration or launching it."""

    if host_kind not in HOST_KINDS:
        raise ValueError("HOST_KIND_UNSUPPORTED")
    if host_kind == CLAUDE_CODE:
        return _probe_claude(runner=runner, which=which)
    return _probe_codex(runner=runner, which=which)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", required=True, choices=HOST_KINDS)
    args = parser.parse_args(argv)
    result = probe_native_goal_host(args.host)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0 if result["status"] == READY else 1


if __name__ == "__main__":
    raise SystemExit(main())
