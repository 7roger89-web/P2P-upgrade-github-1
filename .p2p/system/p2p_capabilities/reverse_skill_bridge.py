"""Bounded bridge to the pinned reverse-skill methodology router.

Reverse-Skill is advisory data/code under P2P governance.  This bridge does not
install tools, bootstrap capabilities, register MCP servers, grant target
authorization, execute a target action, or create a second P2P router.

The only executable upstream surface exposed here is the pinned master-route
entrypoint.  P2P chooses the security capability first; Reverse-Skill may then
suggest the PRIMARY methodology skill inside its own package.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from .security_contract import ANALYSIS_LOCAL, authorize_security_execution


REVERSE_SKILL_UPSTREAM_REPO = "zhaoxuya520/reverse-skill"
REVERSE_SKILL_UPSTREAM_COMMIT = "7e2097fd90d25c2f976f6eba26d6c00aa88051df"
REVERSE_SKILL_ROUTE_SCHEMA = "p2p-reverse-skill-route/1"
REVERSE_SKILL_ROUTE_CLASSIFICATION = "NON_AUTHORITATIVE_SECURITY_METHOD_ADVICE"
REVERSE_SKILL_BRIDGE_VERSION = "1.0.0"

_REQUIRED_PATHS = (
    "skills/config/routing.json",
    "skills/MASTER-ROUTING.md",
    "skills/scripts/master-route.sh",
    "skills/scripts/master-route.ps1",
    "skills/scripts/lib/WorkRoot.ps1",
)


class ReverseSkillBridgeError(RuntimeError):
    """Base error for the bounded Reverse-Skill bridge."""


class ReverseSkillUnavailable(ReverseSkillBridgeError):
    """Raised when the optional pinned upstream checkout cannot be used."""


class ReverseSkillProvenanceError(ReverseSkillBridgeError):
    """Raised when the checkout does not match the exact reviewed source."""


class ReverseSkillBoundaryError(ReverseSkillBridgeError):
    """Raised when a request crosses the bridge's read-only/advisory boundary."""


class ReverseSkillExecutionFailed(ReverseSkillBridgeError):
    """Raised when the pinned router itself fails."""


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


def _clean_text(value: Any, field_name: str, *, max_length: int = 4096) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReverseSkillBoundaryError(f"{field_name.upper()}_REQUIRED")
    normalized = value.strip()
    if len(normalized) > max_length:
        raise ReverseSkillBoundaryError(f"{field_name.upper()}_TOO_LONG")
    return normalized


class ReverseSkillBridge:
    """Expose only Reverse-Skill's pinned methodology-selection entrypoint."""

    def __init__(
        self,
        *,
        package_root: str | os.PathLike[str],
        expected_commit: str = REVERSE_SKILL_UPSTREAM_COMMIT,
        runner: Runner | None = None,
        which: Which | None = None,
        platform_name: str | None = None,
    ) -> None:
        self.package_root = Path(package_root).expanduser().resolve()
        self.expected_commit = str(expected_commit).lower().strip()
        if len(self.expected_commit) != 40 or any(
            char not in "0123456789abcdef" for char in self.expected_commit
        ):
            raise ReverseSkillBoundaryError("EXPECTED_COMMIT_INVALID")
        self._runner = runner or _default_runner
        self._which = which or shutil.which
        self._platform_name = (platform_name or os.name).lower()

    def _run(self, argv: tuple[str, ...], *, cwd: Path | None, timeout_seconds: int) -> subprocess.CompletedProcess[str]:
        return self._runner(
            ToolInvocation(
                argv=argv,
                cwd=str(cwd) if cwd is not None else None,
                timeout_seconds=timeout_seconds,
            )
        )

    def verify_checkout(self) -> dict[str, Any]:
        """Verify exact HEAD, clean tracked files, and the router's required shape."""

        if not self.package_root.is_dir():
            raise ReverseSkillUnavailable("REVERSE_SKILL_CHECKOUT_MISSING")
        missing = [
            relative
            for relative in _REQUIRED_PATHS
            if not (self.package_root / relative).is_file()
        ]
        if missing:
            raise ReverseSkillUnavailable(
                "REVERSE_SKILL_REQUIRED_PATH_MISSING:" + ",".join(missing)
            )

        git = self._which("git")
        if not git:
            raise ReverseSkillUnavailable("GIT_NOT_AVAILABLE_FOR_PROVENANCE_CHECK")

        head_result = self._run(
            (git, "-C", str(self.package_root), "rev-parse", "HEAD"),
            cwd=self.package_root,
            timeout_seconds=15,
        )
        if head_result.returncode != 0:
            raise ReverseSkillProvenanceError("UPSTREAM_HEAD_UNVERIFIABLE")
        observed_commit = (head_result.stdout or "").strip().lower()
        if observed_commit != self.expected_commit:
            raise ReverseSkillProvenanceError(
                f"UPSTREAM_COMMIT_MISMATCH:{observed_commit or 'EMPTY'}"
            )

        dirty_result = self._run(
            (
                git,
                "-C",
                str(self.package_root),
                "status",
                "--porcelain=v1",
                "--untracked-files=no",
            ),
            cwd=self.package_root,
            timeout_seconds=15,
        )
        if dirty_result.returncode != 0:
            raise ReverseSkillProvenanceError("UPSTREAM_WORKTREE_UNVERIFIABLE")
        if (dirty_result.stdout or "").strip():
            raise ReverseSkillProvenanceError("UPSTREAM_TRACKED_WORKTREE_DIRTY")

        config_path = self.package_root / "skills" / "config" / "routing.json"
        try:
            config = json.loads(config_path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ReverseSkillProvenanceError("UPSTREAM_ROUTING_JSON_INVALID") from exc
        if (
            not isinstance(config, dict)
            or not isinstance(config.get("routes"), dict)
            or not isinstance(config.get("priority"), list)
            or not config.get("meta", {}).get("fallbackId")
        ):
            raise ReverseSkillProvenanceError("UPSTREAM_ROUTING_CONTRACT_INVALID")

        return {
            "repository": REVERSE_SKILL_UPSTREAM_REPO,
            "expected_commit": self.expected_commit,
            "observed_commit": observed_commit,
            "tracked_worktree_clean": True,
            "routing_json_sha256": _sha256(config_path),
        }

    def _platform_router(self) -> tuple[str, Path, tuple[str, ...]]:
        is_windows = self._platform_name.startswith("win") or self._platform_name == "nt"
        if is_windows:
            shell = self._which("powershell") or self._which("pwsh")
            if not shell:
                raise ReverseSkillUnavailable("POWERSHELL_NOT_AVAILABLE")
            return (
                shell,
                self.package_root / "skills" / "scripts" / "master-route.ps1",
                ("-NoProfile", "-File"),
            )
        shell = self._which("bash")
        if not shell:
            raise ReverseSkillUnavailable("BASH_NOT_AVAILABLE")
        return (
            shell,
            self.package_root / "skills" / "scripts" / "master-route.sh",
            (),
        )

    def build_route_invocation(
        self,
        *,
        task_hint: str,
        project_root: str | os.PathLike[str],
        artifact_dir: str | os.PathLike[str],
        timeout_seconds: int = 30,
    ) -> ToolInvocation:
        """Build the only permitted upstream invocation.

        The route artifact must live outside both the caller project and the
        Reverse-Skill checkout so methodology output cannot silently mutate
        either source tree.
        """

        hint = _clean_text(task_hint, "task_hint", max_length=8000)
        if type(timeout_seconds) is not int or not 1 <= timeout_seconds <= 300:
            raise ReverseSkillBoundaryError("TIMEOUT_OUT_OF_RANGE")

        project = Path(project_root).expanduser().resolve()
        if not project.is_dir():
            raise ReverseSkillBoundaryError("PROJECT_ROOT_NOT_DIRECTORY")

        out_dir = Path(artifact_dir).expanduser().resolve()
        if _is_within(out_dir, project):
            raise ReverseSkillBoundaryError("ARTIFACT_DIR_MUST_BE_OUTSIDE_PROJECT")
        if _is_within(out_dir, self.package_root):
            raise ReverseSkillBoundaryError("ARTIFACT_DIR_MUST_BE_OUTSIDE_UPSTREAM")
        if not out_dir.parent.is_dir():
            raise ReverseSkillBoundaryError("ARTIFACT_PARENT_MISSING")
        if out_dir.exists() and any(out_dir.iterdir()):
            raise ReverseSkillBoundaryError("ARTIFACT_DIR_MUST_BE_EMPTY")

        shell, script, prefix = self._platform_router()
        is_windows = script.suffix.lower() == ".ps1"
        if is_windows:
            argv = (
                shell,
                *prefix,
                str(script),
                "-Hint",
                hint,
                "-ProjectRoot",
                str(project),
                "-OutDir",
                str(out_dir),
            )
        else:
            argv = (
                shell,
                str(script),
                "--hint",
                hint,
                "--project-root",
                str(project),
                "--out-dir",
                str(out_dir),
            )
        return ToolInvocation(argv=argv, cwd=str(self.package_root), timeout_seconds=timeout_seconds)

    def _validate_skill_ref(self, value: str) -> str:
        normalized = _clean_text(value, "skill_ref", max_length=1024).replace("\\", "/")
        if not normalized.startswith("skills/") or ".." in Path(normalized).parts:
            raise ReverseSkillBoundaryError("UPSTREAM_SKILL_REF_ESCAPE")
        resolved = (self.package_root / Path(normalized)).resolve()
        if not _is_within(resolved, self.package_root) or not resolved.is_file():
            raise ReverseSkillBoundaryError("UPSTREAM_SKILL_REF_INVALID")
        return normalized

    def _parse_route_scope(self, path: Path) -> dict[str, Any]:
        try:
            text = path.read_text(encoding="utf-8-sig")
        except OSError as exc:
            raise ReverseSkillExecutionFailed("ROUTE_SCOPE_UNREADABLE") from exc

        fields: dict[str, str] = {}
        wanted = {
            "primary",
            "primary_label",
            "primary_skill",
            "confidence",
            "secondary",
        }
        for line in text.splitlines():
            if not line.startswith("- ") or ":" not in line:
                continue
            key, value = line[2:].split(":", 1)
            key = key.strip()
            if key in wanted:
                fields[key] = value.strip()

        required = {"primary", "primary_label", "primary_skill", "confidence"}
        if not required.issubset(fields):
            raise ReverseSkillExecutionFailed("ROUTE_SCOPE_FIELDS_MISSING")
        if fields["confidence"] not in {"high", "medium", "low"}:
            raise ReverseSkillExecutionFailed("ROUTE_SCOPE_CONFIDENCE_INVALID")

        primary_skill = self._validate_skill_ref(fields["primary_skill"])
        secondary_raw = fields.get("secondary", "(none)")
        secondary: list[str] = []
        if secondary_raw and secondary_raw != "(none)":
            secondary = [
                self._validate_skill_ref(item.strip())
                for item in secondary_raw.split(",")
                if item.strip()
            ]

        return {
            "primary": fields["primary"],
            "primary_label": fields["primary_label"],
            "primary_skill": primary_skill,
            "confidence": fields["confidence"],
            "secondary": secondary,
        }

    @staticmethod
    def _redacted_command(argv: tuple[str, ...]) -> list[str]:
        redacted = list(argv)
        for marker in ("--hint", "-Hint"):
            if marker in redacted:
                index = redacted.index(marker)
                if index + 1 < len(redacted):
                    redacted[index + 1] = "<task_hint>"
        return redacted

    def route(
        self,
        *,
        task_hint: str,
        project_root: str | os.PathLike[str],
        artifact_dir: str | os.PathLike[str],
        timeout_seconds: int = 30,
    ) -> dict[str, Any]:
        """Return non-authoritative methodology advice from the pinned router."""

        provenance = self.verify_checkout()
        security_execution = authorize_security_execution(ANALYSIS_LOCAL)
        if not security_execution["allowed"]:
            raise ReverseSkillBoundaryError("P2P_SECURITY_EXECUTION_BLOCKED")

        invocation = self.build_route_invocation(
            task_hint=task_hint,
            project_root=project_root,
            artifact_dir=artifact_dir,
            timeout_seconds=timeout_seconds,
        )
        result = self._runner(invocation)
        if result.returncode != 0:
            stderr = (result.stderr or "").strip().replace("\n", " ")[:300]
            raise ReverseSkillExecutionFailed(
                f"REVERSE_SKILL_ROUTE_FAILED:{result.returncode}:{stderr}"
            )

        route_path = Path(artifact_dir).expanduser().resolve() / "route-scope.md"
        if not route_path.is_file():
            raise ReverseSkillExecutionFailed("ROUTE_SCOPE_MISSING")
        route = self._parse_route_scope(route_path)

        return {
            "schema": REVERSE_SKILL_ROUTE_SCHEMA,
            "classification": REVERSE_SKILL_ROUTE_CLASSIFICATION,
            "authoritative_state": False,
            "bridge_version": REVERSE_SKILL_BRIDGE_VERSION,
            "p2p_router_authority_unchanged": True,
            "upstream_router_scope": "SUBORDINATE_METHOD_SELECTOR_ONLY",
            "execution_class": ANALYSIS_LOCAL,
            "security_execution": security_execution,
            "provenance": provenance,
            "route": route,
            "artifact": {
                "path": str(route_path),
                "sha256": _sha256(route_path),
                "ephemeral": True,
                "contains_task_hint": True,
            },
            "boundary": {
                "auto_install": False,
                "auto_bootstrap": False,
                "mcp_registration": False,
                "permission_grant": False,
                "case_init": False,
                "target_act": False,
                "network_runtime": False,
            },
            "command": self._redacted_command(invocation.argv),
        }


def _main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the bounded P2P bridge to a pinned local Reverse-Skill checkout."
    )
    parser.add_argument("--upstream-root", required=True)
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--artifact-dir", required=True)
    parser.add_argument("--hint", required=True)
    parser.add_argument("--timeout-seconds", type=int, default=30)
    args = parser.parse_args()

    bridge = ReverseSkillBridge(package_root=args.upstream_root)
    try:
        payload = bridge.route(
            task_hint=args.hint,
            project_root=args.project_root,
            artifact_dir=args.artifact_dir,
            timeout_seconds=args.timeout_seconds,
        )
    except ReverseSkillBridgeError as exc:
        print(json.dumps({"status": "BLOCKED", "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps({"status": "OK", "result": payload}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())


__all__ = [
    "REVERSE_SKILL_BRIDGE_VERSION",
    "REVERSE_SKILL_ROUTE_CLASSIFICATION",
    "REVERSE_SKILL_ROUTE_SCHEMA",
    "REVERSE_SKILL_UPSTREAM_COMMIT",
    "REVERSE_SKILL_UPSTREAM_REPO",
    "ReverseSkillBoundaryError",
    "ReverseSkillBridge",
    "ReverseSkillBridgeError",
    "ReverseSkillExecutionFailed",
    "ReverseSkillProvenanceError",
    "ReverseSkillUnavailable",
    "ToolInvocation",
]
