#!/usr/bin/env python3
"""Assess one P2P Shield control with one mapped provider and emit evidence.

Slice 1 path::

    control contract -> provider mapping -> provider CLI -> scoped evidence
                                                            -> PASS | FAIL | BLOCKED

Rules this file must keep:

- The control contract owns the objective and the PASS/FAIL/BLOCKED semantics.
  The provider mapping file owns provider name, pinned version, source,
  command shape, coverage, limitations, and failure behaviour.
- A provider that cannot be executed, whose version cannot be matched to the
  pinned mapping, that errors, or whose report cannot be read is ``BLOCKED``.
  Provider failure never becomes ``PASS``.
- Evidence always declares the scan scope that actually ran plus the mapped
  provider limitations, so a narrow scan can never be read as full coverage.
- Provider finding values are never copied into evidence; only rule, file,
  line, and commit references are retained so evidence is safe to log.
- The provider runs with the assessment target as its working directory and
  with the environment overrides declared by the mapping. That keeps
  target-local allow/config state in charge of the scan instead of whatever
  directory or variable happened to be set by the caller.

Stdlib only. Exit status is the Shield status, not a boolean:
``0`` PASS, ``10`` FAIL, ``20`` BLOCKED.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

CONTROL_SCHEMA = "p2p-shield-control/1"
MAPPING_SCHEMA = "p2p-shield-provider-mapping/1"
EVIDENCE_SCHEMA = "p2p-shield-evidence/1"

STATUS_PASS = "PASS"
STATUS_FAIL = "FAIL"
STATUS_BLOCKED = "BLOCKED"
EXIT_BY_STATUS = {STATUS_PASS: 0, STATUS_FAIL: 10, STATUS_BLOCKED: 20}

SHIELD_DIR = Path(__file__).resolve().parent
DEFAULT_CONTROL = "SHIELD-SECRET-01"
MAX_FINDING_REFERENCES = 25
DIAGNOSTIC_TAIL_CHARS = 400
UNRESOLVED_TOKEN = re.compile(r"\{[A-Za-z_][A-Za-z0-9_]*\}")

CONTROL_REQUIRED_FIELDS = (
    "schema",
    "control_id",
    "control_version",
    "objective",
    "required_scope",
    "status_semantics",
    "evidence_fields",
)
MAPPING_REQUIRED_FIELDS = (
    "schema",
    "control_id",
    "provider_name",
    "provider_version",
    "source",
    "invocation",
    "coverage",
    "limitations",
    "failure_behavior",
)


class Blocked(Exception):
    """A required provider assessment cannot be relied on. Reason is durable."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_json_object(path: Path, label: str) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise Blocked(f"{label}_MISSING_OR_INVALID:{path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise Blocked(f"{label}_UNREADABLE:{exc}") from exc
    if not isinstance(data, dict):
        raise Blocked(f"{label}_NOT_AN_OBJECT:{path}")
    return data


def _require_fields(document: dict[str, Any], fields: Sequence[str], label: str) -> None:
    missing = [field for field in fields if field not in document]
    if missing:
        raise Blocked(f"{label}_FIELD_MISSING:{','.join(missing)}")


def load_control(shield_dir: Path, control_id: str) -> tuple[dict[str, Any], Path]:
    path = shield_dir / "controls" / f"{control_id}.json"
    control = _load_json_object(path, "CONTROL")
    _require_fields(control, CONTROL_REQUIRED_FIELDS, "CONTROL")
    if control["schema"] != CONTROL_SCHEMA:
        raise Blocked(f"CONTROL_SCHEMA_UNSUPPORTED:{control['schema']}")
    if control["control_id"] != control_id:
        raise Blocked(f"CONTROL_ID_MISMATCH:{control['control_id']}!={control_id}")
    for status in (STATUS_PASS, STATUS_FAIL, STATUS_BLOCKED):
        if not str(control["status_semantics"].get(status, "")).strip():
            raise Blocked(f"CONTROL_STATUS_SEMANTICS_MISSING:{status}")
    if control.get("non_negotiable", {}).get("provider_failure_must_never_become_pass") is not True:
        raise Blocked("CONTROL_FAIL_CLOSED_RULE_ABSENT")
    return control, path


def load_provider_mapping(
    shield_dir: Path, control_id: str, explicit: Path | None
) -> tuple[dict[str, Any], Path]:
    candidates = [explicit] if explicit else sorted((shield_dir / "providers").glob("*.json"))
    matches: list[tuple[Path, dict[str, Any]]] = []
    for candidate in candidates:
        document = _load_json_object(candidate, "PROVIDER_MAPPING")
        if document.get("schema") != MAPPING_SCHEMA:
            continue
        if document.get("control_id") != control_id:
            continue
        matches.append((candidate, document))
    if len(matches) != 1:
        # Exactly one mapping in v0.1: no provider registry, no silent selection.
        raise Blocked(f"PROVIDER_MAPPING_NOT_UNIQUE:{control_id}:matches={len(matches)}")
    path, mapping = matches[0]
    _require_fields(mapping, MAPPING_REQUIRED_FIELDS, "PROVIDER_MAPPING")
    if mapping["failure_behavior"] != STATUS_BLOCKED:
        raise Blocked(f"PROVIDER_FAILURE_BEHAVIOR_UNSUPPORTED:{mapping['failure_behavior']}")
    invocation = mapping["invocation"]
    for field in ("version_argv", "version_expected_exact", "detect_argv", "scan_mode_args"):
        if field not in invocation:
            raise Blocked(f"PROVIDER_INVOCATION_FIELD_MISSING:{field}")
    expected_version = str(invocation["version_expected_exact"]).strip()
    if not re.fullmatch(r"\d+\.\d+\.\d+", expected_version):
        raise Blocked(f"PROVIDER_VERSION_PIN_MALFORMED:{expected_version}")
    return mapping, path


def _resolve_executable(executable: str) -> Path:
    path = Path(executable).expanduser()
    if path.is_dir():
        raise Blocked(f"PROVIDER_EXECUTABLE_IS_A_DIRECTORY:{path}")
    if not path.is_file():
        raise Blocked(f"PROVIDER_EXECUTABLE_MISSING:{path}")
    return path.resolve()


def _substitute(argv: Sequence[str], values: dict[str, str]) -> list[str]:
    resolved = []
    for template in argv:
        token = template
        for key, value in values.items():
            token = token.replace("{" + key + "}", value)
        unresolved = UNRESOLVED_TOKEN.search(token)
        if unresolved:
            raise Blocked(f"PROVIDER_ARGV_UNRESOLVED_TOKEN:{unresolved.group(0)}")
        resolved.append(token)
    if not resolved:
        raise Blocked("PROVIDER_ARGV_EMPTY")
    return resolved


def _work_directory(target: Path) -> Path | None:
    """Run the provider from the assessment target so target-local provider
    state governs the scan instead of whatever directory the caller used."""
    return target if target.is_dir() else None


def _execute(
    argv: list[str],
    timeout: int,
    label: str,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            cwd=str(cwd) if cwd else None,
            env=env,
        )
    except FileNotFoundError as exc:
        raise Blocked(f"PROVIDER_EXECUTABLE_NOT_RUNNABLE:{label}:{exc}") from exc
    except PermissionError as exc:
        raise Blocked(f"PROVIDER_EXECUTABLE_NOT_EXECUTABLE:{label}:{exc}") from exc
    except OSError as exc:
        raise Blocked(f"PROVIDER_SPAWN_FAILED:{label}:{exc}") from exc
    except subprocess.TimeoutExpired as exc:
        raise Blocked(f"PROVIDER_TIMEOUT:{label}:seconds={timeout}") from exc


def _provider_environment(mapping: dict[str, Any]) -> dict[str, str]:
    """Apply the mapping's declared environment overrides to a copy of os.environ.

    A ``null`` value unsets the variable. This keeps provider configuration
    state from being inherited from wherever the assessment happened to run.
    """
    environment = dict(os.environ)
    overrides = mapping["invocation"].get("environment") or {}
    if not isinstance(overrides, dict):
        raise Blocked("PROVIDER_ENVIRONMENT_OVERRIDE_UNSUPPORTED")
    for key, value in overrides.items():
        if value is None:
            environment.pop(key, None)
        else:
            environment[str(key)] = str(value)
    return environment


def _tail(text: str) -> str:
    flat = " ".join(text.split())
    return flat[-DIAGNOSTIC_TAIL_CHARS:] if flat else ""


# Standalone semver token with optional leading 'v'. Word boundaries so that
# "8.18.40" does not satisfy a pin for "8.18.4" and arbitrary trailing text is
# rejected; the extracted version is compared to the pin by exact equality.
_VERSION_TOKEN = re.compile(r"(?<!\S)v?(\d+\.\d+\.\d+)(?!\S)")


def _extract_exact_version(output: str) -> str:
    """Return the exact semver token from provider version output, or ''."""
    flattened = " ".join((output or "").split())
    match = _VERSION_TOKEN.search(flattened)
    return match.group(1) if match else ""


def resolve_provider_version(
    mapping: dict[str, Any],
    executable: Path,
    target: Path,
    timeout: int,
    env: dict[str, str],
) -> tuple[str, subprocess.CompletedProcess[str]]:
    invocation = mapping["invocation"]
    argv = _substitute(
        invocation["version_argv"],
        {"executable": str(executable), "target": str(target)},
    )
    process = _execute(argv, timeout, "version", cwd=_work_directory(target), env=env)
    observed_raw = (process.stdout + "\n" + process.stderr).strip()
    if process.returncode != 0:
        raise Blocked(f"PROVIDER_VERSION_COMMAND_FAILED:rc={process.returncode}")
    expected = str(invocation["version_expected_exact"]).strip()
    observed = _extract_exact_version(observed_raw)
    if observed != expected:
        # A different provider version is a different provider: never silent.
        raise Blocked(
            f"PROVIDER_VERSION_MISMATCH:pinned={expected}:observed={_tail(observed_raw) or 'EMPTY'}"
        )
    return observed, process


def _read_findings(report_path: Path, returncode: int) -> tuple[str, int, str, list[dict[str, Any]]]:
    """Return (status, findings_count, reason, finding_references)."""
    if not report_path.is_file():
        return (
            STATUS_BLOCKED,
            0,
            f"PROVIDER_REPORT_MISSING:rc={returncode} (completed scans must produce a report)",
            [],
        )
    try:
        payload = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise Blocked(f"PROVIDER_REPORT_UNREADABLE:{exc}") from exc
    if payload is None:
        # A null document encodes "no finding objects" for the pinned provider.
        # It still only becomes PASS when the provider also exited cleanly.
        payload = []
    if not isinstance(payload, list):
        raise Blocked(f"PROVIDER_REPORT_SHAPE_UNSUPPORTED:type={type(payload).__name__}")
    findings = [item for item in payload if isinstance(item, dict)]
    if len(findings) != len(payload):
        raise Blocked("PROVIDER_REPORT_SHAPE_UNSUPPORTED:non_object_finding")
    count = len(findings)
    if returncode == 0:
        if count:
            return STATUS_FAIL, count, "PROVIDER_COMPLETED_WITH_FINDINGS", findings
        return STATUS_PASS, 0, "PROVIDER_COMPLETED_WITHOUT_FINDINGS", []
    if count:
        return STATUS_FAIL, count, f"PROVIDER_REPORTED_FINDINGS:rc={returncode}", findings
    # Non-zero exit without established findings (for example a partial scan)
    # cannot be read as a clean result.
    return (
        STATUS_BLOCKED,
        0,
        f"PROVIDER_INCOMPLETE:rc={returncode} (findings not reliably established)",
        [],
    )


def _finding_references(findings: Sequence[dict[str, Any]]) -> list[dict[str, str | int]]:
    references = []
    for finding in findings[:MAX_FINDING_REFERENCES]:
        entry: dict[str, str | int] = {}
        for target, keys in (
            ("rule_id", ("RuleID", "ruleId", "rule")),
            ("file", ("File", "file", "path")),
            ("line", ("StartLine", "startLine", "line")),
            ("commit", ("Commit", "commit")),
        ):
            for key in keys:
                if key in finding:
                    entry[target] = finding[key]
                    break
        references.append(entry)
    return references


NO_GIT_HEAD = "NO_GIT_HEAD"


def resolve_target_ref(target: Path) -> str:
    try:
        process = subprocess.run(
            ["git", "-C", str(target), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return NO_GIT_HEAD
    if process.returncode == 0 and process.stdout.strip():
        return process.stdout.strip()
    return NO_GIT_HEAD


def requires_git_repository(control: dict[str, Any]) -> bool:
    """Whether the control declares git repositories as its applicable target.

    The pinned provider does not fail on a non-repository target: it scans
    nothing and exits cleanly, which would otherwise be recorded as PASS. When
    the control requires a repository, an unresolvable ref is a BLOCKED
    assessment instead of a clean one.
    """
    return control.get("applies_to", {}).get("target_kind") == "git_repository"


def build_evidence(
    *,
    control: dict[str, Any],
    control_path: Path,
    mapping: dict[str, Any],
    mapping_path: Path,
    scan_mode: str,
    target: Path,
    status: str,
    findings_count: int,
    findings: Sequence[dict[str, Any]],
    reason: str,
    target_ref: str,
    provider_version_text: str,
    diagnostics: dict[str, Any],
    reference: str,
) -> dict[str, Any]:
    # A blocked assessment never established its intended coverage; recording
    # the mapped coverage as if it had run would be an overclaim.
    coverage = (
        ["NONE_ESTABLISHED"]
        if status == STATUS_BLOCKED
        else mapping["coverage"].get(scan_mode, ["UNDECLARED"])
    )
    return {
        "schema": EVIDENCE_SCHEMA,
        "control_id": control["control_id"],
        "control_version": control["control_version"],
        "provider": mapping["provider_name"],
        "provider_version": mapping["provider_version"],
        "provider_source": f"{mapping['source'].get('repository', 'UNDECLARED')}@{mapping['source'].get('tag', 'UNDECLARED')}",
        "target": str(target),
        "target_ref": target_ref,
        "timestamp": _utc_timestamp(),
        "status": status,
        "scope": scan_mode,
        "coverage": coverage,
        "findings_count": findings_count,
        "findings": _finding_references(findings),
        "findings_reference_limit": MAX_FINDING_REFERENCES,
        "findings_truncated": findings_count > MAX_FINDING_REFERENCES,
        "limitations": list(mapping["limitations"]) + [
            f"Control objective wider than this scope: {mode} not assessed in this record."
            for mode in control["required_scope"]["required_evidence"]
            if mode != scan_mode
        ],
        "reason": reason,
        "diagnostics": diagnostics,
        "contract_binding": {
            "control_sha256": _sha256_file(control_path),
            "provider_mapping_sha256": _sha256_file(mapping_path),
        },
        "provider_version_observed": provider_version_text,
        "artifact_or_reference": reference,
    }


def assess(
    *,
    shield_dir: Path,
    control_id: str,
    scan_mode: str,
    target: Path,
    executable: str,
    provider_mapping: Path | None,
    timeout: int,
    reference: str,
) -> dict[str, Any]:
    """Run one assessment for one control/scope and return the evidence record."""
    control = control_path = mapping = mapping_path = None
    findings: list[dict[str, Any]] = []
    findings_count = 0
    target_ref = "UNRESOLVED"
    provider_version_text = "UNRESOLVED"
    diagnostics: dict[str, Any] = {"provider_exit_code": None, "provider_stderr_tail": ""}
    try:
        control, control_path = load_control(shield_dir, control_id)
        mapping, mapping_path = load_provider_mapping(shield_dir, control_id, provider_mapping)
        environment = _provider_environment(mapping)
        resolved_executable = _resolve_executable(executable)
        provider_version_text, version_process = resolve_provider_version(
            mapping, resolved_executable, target, timeout, environment
        )
        invocation = mapping["invocation"]
        mode_args = invocation["scan_mode_args"].get(scan_mode)
        if mode_args is None:
            raise Blocked(f"SCAN_MODE_NOT_MAPPED:{scan_mode}")
        if scan_mode not in control["required_scope"]["required_evidence"]:
            raise Blocked(f"SCAN_MODE_NOT_REQUIRED_BY_CONTROL:{scan_mode}")
        target_ref = resolve_target_ref(target)
        if requires_git_repository(control) and target_ref == NO_GIT_HEAD:
            raise Blocked(f"TARGET_NOT_A_GIT_REPOSITORY:{target}")
        with tempfile.TemporaryDirectory(prefix="p2p-shield-run-") as work_dir:
            report_path = Path(work_dir) / "provider-report.json"
            argv = _substitute(
                list(invocation["detect_argv"]) + list(mode_args),
                {
                    "executable": str(resolved_executable),
                    "target": str(target),
                    "report": str(report_path),
                },
            )
            process = _execute(argv, timeout, "detect", cwd=_work_directory(target), env=environment)
            status, findings_count, reason, findings = _read_findings(report_path, process.returncode)
        diagnostics = {
            "provider_exit_code": process.returncode,
            "provider_stderr_tail": _tail(process.stderr),
            "provider_version_exit_code": version_process.returncode,
        }
    except Blocked as exc:
        status, reason = STATUS_BLOCKED, exc.reason
    if control is None or mapping is None or control_path is None or mapping_path is None:
        # Contract resolution failed before an evidence record could be bound.
        return {
            "schema": EVIDENCE_SCHEMA,
            "control_id": control_id,
            "control_version": "UNRESOLVED",
            "provider": "UNRESOLVED",
            "provider_version": "UNRESOLVED",
            "target": str(target),
            "target_ref": NO_GIT_HEAD if target.is_dir() else "TARGET_MISSING",
            "timestamp": _utc_timestamp(),
            "status": STATUS_BLOCKED,
            "scope": scan_mode,
            "coverage": ["NONE_ESTABLISHED"],
            "findings_count": 0,
            "findings": [],
            "limitations": ["No provider assessment completed; no coverage is claimed."],
            "reason": reason,
            "diagnostics": diagnostics,
            "artifact_or_reference": reference,
        }
    return build_evidence(
        control=control,
        control_path=control_path,
        mapping=mapping,
        mapping_path=mapping_path,
        scan_mode=scan_mode,
        target=target,
        status=status,
        findings_count=findings_count,
        findings=findings,
        reason=reason,
        target_ref=target_ref,
        provider_version_text=provider_version_text,
        diagnostics=diagnostics,
        reference=reference,
    )


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--control", default=DEFAULT_CONTROL, help="Shield control id")
    parser.add_argument(
        "--scan-mode",
        required=True,
        help="Provider scan scope to assess, for example git_history_scan or worktree_scan",
    )
    parser.add_argument("--target", required=True, help="Repository or directory to assess")
    parser.add_argument(
        "--executable",
        required=True,
        help="Provider executable path (no PATH lookup, no silent provider substitution)",
    )
    parser.add_argument(
        "--shield-dir",
        default=str(SHIELD_DIR),
        help="Directory holding controls/ and providers/ (defaults to this package)",
    )
    parser.add_argument(
        "--provider-mapping",
        default=None,
        help="Optional explicit provider mapping file instead of the single-mapping default",
    )
    parser.add_argument("--evidence-out", default=None, help="Write the evidence record as JSON here")
    parser.add_argument(
        "--evidence-reference",
        default="UNREFERENCED",
        help="Durable reference stored with the evidence record",
    )
    parser.add_argument("--timeout-seconds", type=int, default=600)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    started = time.monotonic()
    evidence = assess(
        shield_dir=Path(args.shield_dir).resolve(),
        control_id=args.control,
        scan_mode=args.scan_mode,
        target=Path(args.target).resolve(),
        executable=args.executable,
        provider_mapping=Path(args.provider_mapping).resolve() if args.provider_mapping else None,
        timeout=args.timeout_seconds,
        reference=args.evidence_reference,
    )
    serialised = json.dumps(evidence, indent=2, sort_keys=True)
    if args.evidence_out:
        out_path = Path(args.evidence_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(serialised + "\n", encoding="utf-8")
    print(serialised)
    status = evidence.get("status", STATUS_BLOCKED)
    exit_code = EXIT_BY_STATUS.get(status)
    if exit_code is None:
        print(f"SHIELD_STATUS_UNSUPPORTED:{status}", file=sys.stderr)
        return EXIT_BY_STATUS[STATUS_BLOCKED]
    print(
        f"SHIELD_STATUS={status} findings={evidence.get('findings_count', 0)} "
        f"elapsed={time.monotonic() - started:.1f}s",
        file=sys.stderr,
    )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
