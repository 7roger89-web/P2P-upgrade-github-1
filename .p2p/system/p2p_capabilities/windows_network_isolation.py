"""Fail-closed Windows outbound isolation for one exact executable path.

This module deliberately uses the Windows Defender Firewall program-rule
boundary.  Proxy variables and Blender flags are not an isolation mechanism.
The caller must hold the privilege required to create and remove firewall
rules; inability to prove the rule is active is an error and must prevent the
child process from being spawned.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Final


MECHANISM: Final = "WINDOWS_DEFENDER_FIREWALL_PROGRAM_OUTBOUND_BLOCK"
PRIVILEGE_REQUIRED: Final = "Administrator"
_RULE_PREFIX: Final = "P2P-MPFB-DENY-"
_REPARSE_POINT: Final = 0x400


class NetworkIsolationError(RuntimeError):
    """Raised when process network denial cannot be established or released."""


@dataclass
class NetworkIsolationReceipt:
    identity: str
    mechanism: str
    executable_path: str
    rule_name: str
    platform: str
    privilege_required: str
    setup_result: str = "NOT_STARTED"
    enforcement_result: str = "NOT_VERIFIED"
    cleanup_result: str = "NOT_STARTED"
    rule_created: bool = False

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def _returncode(result: object) -> int:
    value = getattr(result, "returncode", None)
    return value if isinstance(value, int) else 1


def _runner_call(runner: Callable[..., object], command: list[str]) -> object:
    try:
        return runner(
            command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
            shell=False,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise NetworkIsolationError("NETWORK_ISOLATION_COMMAND_UNAVAILABLE") from exc


def _powershell(runner: Callable[..., object], script: str) -> object:
    return _runner_call(
        runner,
        [
            "powershell.exe",
            "-NoLogo",
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "RemoteSigned",
            "-Command",
            script,
        ],
    )


def _netsh(runner: Callable[..., object], *arguments: str) -> object:
    return _runner_call(runner, ["netsh.exe", "advfirewall", "firewall", *arguments])


def _powershell_json(result: object, error_code: str) -> object:
    if _returncode(result) != 0:
        raise NetworkIsolationError(error_code)
    try:
        return json.loads(getattr(result, "stdout", ""))
    except (TypeError, json.JSONDecodeError) as exc:
        raise NetworkIsolationError(error_code) from exc


def _profile_enabled(value: object) -> bool:
    """Return True only when PowerShell reported one firewall profile enabled.

    The pre-spawn probe expands ``Enabled`` from every ``Get-NetFirewallProfile``
    result into compressed JSON, where the CIM boolean arrives either as the
    JSON boolean ``true`` or as the integer ``1`` (real Windows hosts were
    observed emitting ``[1,1,1]``).  Only those two decoded values count as
    enabled.  The check is deliberately type-strict rather than truthiness-based:
    ``0``, ``2``, ``-1``, ``1.0``, ``"1"``, ``"true"``, ``null``, and any object
    fail closed, because a value this parser cannot read as an explicit enabled
    state must never unlock outbound isolation.
    """
    if value is True:
        return True
    return type(value) is int and value == 1


def _reparse_point(path: Path) -> bool:
    try:
        attributes = int(getattr(os.stat(path, follow_symlinks=False), "st_file_attributes", 0))
    except OSError:
        return False
    return bool(attributes & _REPARSE_POINT)


def _validate_executable(executable_path: str | Path) -> Path:
    candidate = Path(executable_path)
    if os.name != "nt":
        raise NetworkIsolationError("WINDOWS_NETWORK_ISOLATION_UNAVAILABLE")
    if candidate.is_symlink() or _reparse_point(candidate):
        raise NetworkIsolationError("BLENDER_SYMLINK_OR_REPARSE")
    try:
        resolved = candidate.resolve(strict=True)
    except OSError as exc:
        raise NetworkIsolationError("BLENDER_EXECUTABLE_UNAVAILABLE") from exc
    if resolved.is_symlink() or _reparse_point(resolved) or not resolved.is_file():
        raise NetworkIsolationError("BLENDER_EXECUTABLE_INVALID")
    return resolved


def _identity(executable: Path, job_identity: str) -> str:
    material = f"{executable.as_posix()}\x00{job_identity}".encode("utf-8")
    return hashlib.sha256(material).hexdigest()[:32]


class NetworkIsolationLease:
    """Context manager that owns one uniquely named firewall rule."""

    def __init__(
        self,
        executable_path: str | Path,
        job_identity: str,
        *,
        platform_name: str | None = None,
        runner: Callable[..., object] = subprocess.run,
    ) -> None:
        self.executable_path = _validate_executable(executable_path)
        self.platform_name = platform_name or os.name
        if self.platform_name != "nt":
            raise NetworkIsolationError("WINDOWS_NETWORK_ISOLATION_UNAVAILABLE")
        self.runner = runner
        self.identity = _identity(self.executable_path, job_identity)
        self.rule_name = _RULE_PREFIX + self.identity
        self.receipt = NetworkIsolationReceipt(
            identity=self.identity,
            mechanism=MECHANISM,
            executable_path=self.executable_path.as_posix(),
            rule_name=self.rule_name,
            platform=self.platform_name,
            privilege_required=PRIVILEGE_REQUIRED,
        )

    def __enter__(self) -> "NetworkIsolationLease":
        self._setup()
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> bool:
        self.release()
        return False

    def _setup(self) -> None:
        try:
            profiles = _powershell(
                self.runner,
                "@(Get-NetFirewallProfile -All | Select-Object -ExpandProperty Enabled) | ConvertTo-Json -Compress",
            )
            enabled = _powershell_json(profiles, "NETWORK_ISOLATION_FIREWALL_PROFILE_CHECK_FAILED")
            if (
                not isinstance(enabled, list)
                or len(enabled) != 3
                or any(not _profile_enabled(item) for item in enabled)
            ):
                raise NetworkIsolationError("NETWORK_ISOLATION_FIREWALL_DISABLED")

            existing = _netsh(self.runner, "show", "rule", f"name={self.rule_name}")
            if _returncode(existing) == 0:
                raise NetworkIsolationError("NETWORK_ISOLATION_RULE_ID_COLLISION")

            added = _netsh(
                self.runner,
                "add",
                "rule",
                f"name={self.rule_name}",
                "dir=out",
                "action=block",
                "enable=yes",
                "profile=any",
                f"program={self.executable_path}",
            )
            if _returncode(added) != 0:
                raise NetworkIsolationError("NETWORK_ISOLATION_RULE_CREATE_FAILED")
            self.receipt.rule_created = True

            # netsh rules are addressed by their display-name surface: the
            # legacy -Name parameter queries InstanceID, which does not match
            # the netsh rule name, so canonical verification must use the
            # exact -DisplayName surface.  The result is forced to an array
            # and must contain exactly one rule; the returned DisplayName is
            # re-compared exactly in Python below, so the query surface alone
            # is never trusted.
            script = (
                "$rules = @(Get-NetFirewallRule -DisplayName '"
                + self.rule_name
                + "' -ErrorAction Stop); "
                "if ($rules.Count -ne 1) { throw 'P2P_RULE_DISPLAYNAME_NOT_EXACTLY_ONE' }; "
                "$rule = $rules[0]; "
                "$app = $rule | Get-NetFirewallApplicationFilter -ErrorAction Stop; "
                "[pscustomobject]@{DisplayName=[string]$rule.DisplayName;Enabled=[bool]$rule.Enabled;"
                "Direction=[string]$rule.Direction;Action=[string]$rule.Action;"
                "Program=[string]$app.Program} | ConvertTo-Json -Compress"
            )
            verified = _powershell_json(
                _powershell(self.runner, script),
                "NETWORK_ISOLATION_RULE_VERIFY_FAILED",
            )
            if not isinstance(verified, dict):
                raise NetworkIsolationError("NETWORK_ISOLATION_RULE_VERIFY_FAILED")
            program = str(verified.get("Program", ""))
            if (
                verified.get("DisplayName") != self.rule_name
                or verified.get("Enabled") is not True
                or str(verified.get("Direction", "")).casefold() != "outbound"
                or str(verified.get("Action", "")).casefold() != "block"
                or Path(program).resolve() != self.executable_path
            ):
                raise NetworkIsolationError("NETWORK_ISOLATION_RULE_NOT_EXACT")
            self.receipt.setup_result = "PASS"
            self.receipt.enforcement_result = "PASS"
        except NetworkIsolationError:
            self.receipt.setup_result = "FAIL"
            try:
                if self.receipt.rule_created:
                    self._delete_rule()
            except NetworkIsolationError as cleanup_error:
                self.receipt.cleanup_result = "FAIL"
                raise NetworkIsolationError("NETWORK_ISOLATION_SETUP_AND_CLEANUP_FAILED") from cleanup_error
            raise
        except (OSError, ValueError, TypeError) as exc:
            self.receipt.setup_result = "FAIL"
            raise NetworkIsolationError("NETWORK_ISOLATION_SETUP_FAILED") from exc

    def _delete_rule(self) -> None:
        deleted = _netsh(self.runner, "delete", "rule", f"name={self.rule_name}")
        if _returncode(deleted) != 0:
            raise NetworkIsolationError("NETWORK_ISOLATION_RULE_DELETE_FAILED")
        remaining = _netsh(self.runner, "show", "rule", f"name={self.rule_name}")
        if _returncode(remaining) == 0:
            raise NetworkIsolationError("NETWORK_ISOLATION_RULE_REMAINS")
        self.receipt.rule_created = False

    def release(self) -> None:
        if self.receipt.cleanup_result == "PASS":
            return
        if not self.receipt.rule_created:
            self.receipt.cleanup_result = "NOT_REQUIRED"
            return
        try:
            self._delete_rule()
        except NetworkIsolationError:
            self.receipt.cleanup_result = "FAIL"
            raise
        self.receipt.cleanup_result = "PASS"


def create_network_isolation(
    executable_path: str | Path,
    job_identity: str,
    *,
    platform_name: str | None = None,
    runner: Callable[..., object] = subprocess.run,
) -> NetworkIsolationLease:
    """Create, but do not activate, a Windows firewall isolation lease."""

    return NetworkIsolationLease(
        executable_path,
        job_identity,
        platform_name=platform_name,
        runner=runner,
    )


__all__ = [
    "MECHANISM",
    "NetworkIsolationError",
    "NetworkIsolationLease",
    "NetworkIsolationReceipt",
    "PRIVILEGE_REQUIRED",
    "create_network_isolation",
]
