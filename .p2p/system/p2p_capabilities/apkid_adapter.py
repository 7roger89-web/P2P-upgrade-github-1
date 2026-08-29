"""Bounded, local-only APKiD proof adapter.

The adapter owns the sole external-process boundary for this proof. It accepts
one explicit local APK, invokes an already-installed APKiD executable through
an argument list, and returns normalized evidence. It never installs a tool,
opens a network connection, touches a device/emulator, or writes the APK.
"""

from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Callable

from .backend_contract import AdapterHealthState, BackendAdapterIdentity
from .security_contract import (
    SAFE_READONLY,
    NormalizedSecurityEvidence,
    NormalizedSecurityFinding,
    SecurityArtifactIdentity,
)


APKID_CAPABILITY_ID = "android.protection.detect"
APKID_ADAPTER_ID = "apkid-minimal-adapter"
APKID_ADAPTER_VERSION = "1.0.0"
DEFAULT_TIMEOUT_SECONDS = 60

_CATEGORY_PATTERNS = (
    ("PACKER", re.compile(r"^\s*(?:\[\+\]\s*)?Packers?\s*:\s*(?P<value>.*?)\s*$", re.IGNORECASE)),
    ("PROTECTOR", re.compile(r"^\s*(?:\[\+\]\s*)?Protectors?\s*:\s*(?P<value>.*?)\s*$", re.IGNORECASE)),
    ("COMPILER", re.compile(r"^\s*(?:\[\+\]\s*)?Compiler\s*:\s*(?P<value>.*?)\s*$", re.IGNORECASE)),
    ("OBFUSCATOR", re.compile(r"^\s*(?:\[\+\]\s*)?Obfuscators?\s*:\s*(?P<value>.*?)\s*$", re.IGNORECASE)),
)
_EMPTY_LABELS = frozenset({"", "none", "unknown", "n/a", "na", "-", "not detected"})

Runner = Callable[..., subprocess.CompletedProcess[str]]


def _stream_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def _output_ref(text: str) -> str:
    return "apkid-output-sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _labels(value: str) -> tuple[str, ...]:
    labels = []
    for item in re.split(r"[,;]", value):
        normalized = item.strip()
        if normalized.lower() not in _EMPTY_LABELS:
            labels.append(normalized)
    return tuple(dict.fromkeys(labels))


def normalize_apkid_output(output: str) -> tuple[NormalizedSecurityFinding, ...]:
    """Parse only APKiD's supported category lines; preserve raw evidence by hash."""

    text = _stream_text(output)
    reference = _output_ref(text)
    findings: list[NormalizedSecurityFinding] = []
    for line in text.splitlines():
        for category, pattern in _CATEGORY_PATTERNS:
            match = pattern.match(line)
            if not match:
                continue
            for label in _labels(match.group("value")):
                findings.append(
                    NormalizedSecurityFinding(
                        category=category,
                        label=label,
                        evidence_refs=(reference,),
                        confidence="UNKNOWN",
                        semantic_label=label,
                    )
                )
            break
    return tuple(findings)


class ApkidAdapter:
    """Minimal APKiD CLI adapter for explicit local APK artifacts."""

    def __init__(
        self,
        *,
        executable: str | Path = "apkid",
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
        runner: Runner | None = None,
    ) -> None:
        self._executable = str(executable)
        if type(timeout_seconds) is not int or timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be a positive integer")
        self._timeout_seconds = timeout_seconds
        self._runner = runner or subprocess.run

    def identity(self) -> BackendAdapterIdentity:
        return BackendAdapterIdentity(
            adapter_id=APKID_ADAPTER_ID,
            adapter_version=APKID_ADAPTER_VERSION,
            adapter_state="ADAPTER_IMPLEMENTED",
            provider_identity="APKiD external CLI",
            protocol="LOCAL_CLI_ARGV",
            toolset_capabilities=(APKID_CAPABILITY_ID,),
            workspace_binding="EXPLICIT_LOCAL_APK",
            environment_binding="NO_NETWORK_NO_DEVICE_NO_MUTATION",
        )

    def _binary_path(self) -> str | None:
        candidate = Path(self._executable)
        if candidate.is_absolute() or candidate.parent != Path("."):
            if candidate.is_file():
                return str(candidate.resolve())
            return None
        return shutil.which(self._executable)

    def dependency_status(self) -> dict[str, Any]:
        binary = self._binary_path()
        return {
            "dependency": "APKiD",
            "executable": binary,
            "status": "AVAILABLE" if binary else "UNAVAILABLE",
            "install_mode": "DISABLED",
            "auto_install": False,
            "network_runtime": False,
            "credentials": False,
        }

    def health(self) -> AdapterHealthState:
        dependency = self.dependency_status()
        available = dependency["status"] == "AVAILABLE"
        return AdapterHealthState(
            healthy=available,
            auth_state="NO_CREDENTIALS",
            auth_state_after="NO_CREDENTIALS",
            availability="AVAILABLE" if available else "UNAVAILABLE",
            freshness="CURRENT",
        )

    @staticmethod
    def _local_apk(path: str | Path) -> Path | None:
        raw = str(path)
        if "://" in raw or raw.startswith(("\\\\", "//")) or not raw.strip():
            return None
        source = Path(raw)
        if source.is_symlink():
            return None
        try:
            resolved = source.resolve(strict=True)
        except (OSError, RuntimeError):
            return None
        if not resolved.is_file() or resolved.suffix.lower() != ".apk":
            return None
        return resolved

    @staticmethod
    def _result(
        *,
        status: str,
        artifact: SecurityArtifactIdentity | None,
        backend_identity: BackendAdapterIdentity,
        findings: tuple[NormalizedSecurityFinding, ...] = (),
        evidence_refs: tuple[str, ...] = (),
        error_code: str | None = None,
        uncertainty_state: str = "NONE",
        mutation_observed: bool = False,
    ) -> NormalizedSecurityEvidence:
        return NormalizedSecurityEvidence(
            capability_id=APKID_CAPABILITY_ID,
            status=status,
            artifact_identity=artifact,
            backend_identity=backend_identity.to_dict(),
            findings=findings,
            evidence_refs=evidence_refs,
            uncertainty_state=uncertainty_state,
            execution_class=SAFE_READONLY,
            error_code=error_code,
            mutation_observed=mutation_observed,
            external_interaction=False,
        )

    def analyze(self, apk_path: str | Path) -> NormalizedSecurityEvidence:
        """Analyze one local APK without mutating or contacting another target."""

        identity = self.identity()
        source = self._local_apk(apk_path)
        if source is None:
            return self._result(
                status="REJECTED",
                artifact=None,
                backend_identity=identity,
                evidence_refs=("target:local-apk-required",),
                error_code="LOCAL_APK_REQUIRED",
                uncertainty_state="UNKNOWN",
            )

        artifact = SecurityArtifactIdentity.from_path(source)
        before_stat = source.stat()
        dependency = self.dependency_status()
        if dependency["status"] != "AVAILABLE":
            return self._result(
                status="UNAVAILABLE",
                artifact=artifact,
                backend_identity=identity,
                evidence_refs=("dependency:apkid:unavailable",),
                error_code="DEPENDENCY_UNAVAILABLE",
                uncertainty_state="UNKNOWN",
            )

        command = [str(dependency["executable"]), str(source)]
        try:
            process = self._runner(
                command,
                capture_output=True,
                text=True,
                cwd=str(source.parent),
                timeout=self._timeout_seconds,
                check=False,
            )
            stdout = _stream_text(getattr(process, "stdout", ""))
            stderr = _stream_text(getattr(process, "stderr", ""))
            exit_code = int(getattr(process, "returncode", 0))
        except subprocess.TimeoutExpired as exc:
            stdout = _stream_text(getattr(exc, "stdout", ""))
            stderr = _stream_text(getattr(exc, "stderr", ""))
            exit_code = -1
            combined = stdout + stderr
            return self._post_run_boundary(
                source=source,
                before=artifact,
                before_stat=before_stat,
                backend_identity=identity,
                status="UNKNOWN",
                evidence_refs=(_output_ref(combined),),
                error_code="APKID_TIMEOUT",
                uncertainty_state="UNKNOWN",
            )
        except OSError:
            return self._post_run_boundary(
                source=source,
                before=artifact,
                before_stat=before_stat,
                backend_identity=identity,
                status="UNAVAILABLE",
                evidence_refs=("dependency:apkid:process-unavailable",),
                error_code="DEPENDENCY_UNAVAILABLE",
                uncertainty_state="UNKNOWN",
            )

        combined = stdout + ("\n" + stderr if stderr else "")
        output_reference = _output_ref(combined)
        if exit_code != 0:
            return self._post_run_boundary(
                source=source,
                before=artifact,
                before_stat=before_stat,
                backend_identity=identity,
                status="UNKNOWN",
                evidence_refs=(output_reference,),
                error_code="APKID_NONZERO_EXIT",
                uncertainty_state="UNKNOWN",
            )

        findings = normalize_apkid_output(combined)
        return self._post_run_boundary(
            source=source,
            before=artifact,
            before_stat=before_stat,
            backend_identity=identity,
            status="VERIFIED",
            findings=findings,
            evidence_refs=(output_reference,),
        )

    def _post_run_boundary(
        self,
        *,
        source: Path,
        before: SecurityArtifactIdentity,
        before_stat: Any,
        backend_identity: BackendAdapterIdentity,
        status: str,
        findings: tuple[NormalizedSecurityFinding, ...] = (),
        evidence_refs: tuple[str, ...] = (),
        error_code: str | None = None,
        uncertainty_state: str = "NONE",
    ) -> NormalizedSecurityEvidence:
        try:
            after = SecurityArtifactIdentity.from_path(source)
            after_stat = source.stat()
        except (OSError, ValueError):
            return self._result(
                status="REJECTED",
                artifact=before,
                backend_identity=backend_identity,
                findings=findings,
                evidence_refs=evidence_refs,
                error_code="ARTIFACT_UNAVAILABLE_AFTER_ANALYSIS",
                uncertainty_state="UNKNOWN",
                mutation_observed=True,
            )
        mutated = (
            after.sha256 != before.sha256
            or after.size_bytes != before.size_bytes
            or after_stat.st_mtime_ns != before_stat.st_mtime_ns
        )
        if mutated:
            return self._result(
                status="REJECTED",
                artifact=after,
                backend_identity=backend_identity,
                findings=(),
                evidence_refs=evidence_refs,
                error_code="ARTIFACT_MUTATED_DURING_ANALYSIS",
                uncertainty_state="CONTRADICTED",
                mutation_observed=True,
            )
        return self._result(
            status=status,
            artifact=before,
            backend_identity=backend_identity,
            findings=findings,
            evidence_refs=evidence_refs,
            error_code=error_code,
            uncertainty_state=uncertainty_state,
        )

    def execute(self, apk_path: str | Path) -> NormalizedSecurityEvidence:
        """Adapter-pattern alias; it performs the same bounded local analysis."""

        return self.analyze(apk_path)


__all__ = [
    "APKID_ADAPTER_ID",
    "APKID_ADAPTER_VERSION",
    "APKID_CAPABILITY_ID",
    "ApkidAdapter",
    "normalize_apkid_output",
]
