"""Small, fail-closed boundary for supported P2P live context trials.

The context builder remains pure and does not know about hosts, providers, or
trial output.  This module is the development-source adapter around it.  It
accepts a fully constructed context view, verifies that the view can be
reconstructed from the source input, and keeps live status behind two pieces
of host-owned evidence: a completed supported-host result and a matching
identity receipt in the existing Execution Ledger.

This is intentionally not a provider client, scheduler, memory store, or
second evidence ledger.  It is not included in the frozen C06 candidate
artifact; the candidate supplies the immutable context runtime binding used by
the trial harness.
"""

from __future__ import annotations

import hashlib
import json
import re
import time
import uuid
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

from .context import (
    BASELINE_COMPAT,
    CONTEXT_EFFICIENT_V1,
    CONTEXT_MANIFEST_SCHEMA,
    CONTEXT_VIEW_SCHEMA,
    LOCAL_SERIALIZATION_PROXY,
    build_context_view,
    context_fingerprint,
    validate_context_bindings,
)
from scripts.p2p_host_identity_hook import (
    HOST_SOURCE as HOST_IDENTITY_SOURCE,
    host_agent_class,
    is_supported_host_agent_type,
    validate_receipt as validate_host_identity_receipt,
)


LIVE_TRIAL_SCHEMA = "p2p-live-context-trial/1"
LIVE_REQUEST_SCHEMA = "p2p-live-host-request/1"
LIVE_RECEIPT_SCHEMA = "p2p-live-context-receipt/1"
LIVE_LEDGER_EVENT = "live_context_trial_receipt"
EXECUTION_LEDGER_SCHEMA = "p2p-execution-event/1"
HOST_IDENTITY_SCHEMA = "p2p-host-subagent-identity/1"
HOST_EXECUTION_SOURCE = "codex_official_host"
LOCAL_PROXY_SOURCE = "LOCAL_PROXY"
ROUTE_OBSERVATION_SCHEMA = "p2p-route-host-observation/1"
HOST_DEFAULT_EXECUTOR_CLASS = "HOST_DEFAULT / GENERIC"
CUSTOM_PROFILE_EXECUTOR_CLASS = "CUSTOM_PROFILE"
PERMISSION_ACTIONS = (
    "READ",
    "WRITE",
    "DELETE",
    "EXECUTE",
    "LOG",
    "PERSIST",
    "EGRESS",
    "NETWORK",
    "SECRET_ACCESS",
    "DELEGATE",
    "RELEASE",
    "OWNER_APPROVAL",
)
READ_ONLY_PERMISSION_ENVELOPE = {action: action == "READ" for action in PERMISSION_ACTIONS}
HOST_READ_ONLY_PERMISSION_MODES = {"READ_ONLY", "READ_ONLY_CONTEXT_TRIAL"}

CONDITION_MODES = {"A": BASELINE_COMPAT, "B": CONTEXT_EFFICIENT_V1}
SUPPORTED_SCENARIOS = tuple(f"C{index}" for index in range(1, 13))
TELEMETRY_AUTHORITIES = {
    "HOST",
    "PROVIDER",
    "LOCAL_MONOTONIC_TIMER",
    "DETERMINISTIC_RUNTIME",
    "LOCAL_PROXY",
    "UNKNOWN",
}

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_TRIAL_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_MAX_STRING_LENGTH = 4096
_SECRET_KEY_RE = re.compile(
    r"(?:secret|token|password|credential|api[_-]?key|private[_-]?key|access[_-]?key|authorization|env[_-]?vars|environment[_-]?variables)",
    re.IGNORECASE,
)
_SECRET_VALUE_RE = re.compile(
    r"(?:api[_-]?key|password|token|secret|authorization|private[_-]?key)\s*[:=]\s*[^\s,;]+|sk-[A-Za-z0-9_-]{16,}",
    re.IGNORECASE,
)
_HOST_RECEIPT_FIELDS = {
    "schema",
    "event",
    "timestamp",
    "session_id",
    "turn_id",
    "agent_id",
    "agent_type",
    "permission_mode",
    "model",
    "cwd",
    "source",
}
_ROUTE_OBSERVATION_FIELDS = {
    "schema",
    "logical_route",
    "logical_capability",
    "supporting_capabilities",
    "requested_profile_if_any",
    "executor_class",
}


class LiveExecutionError(ValueError):
    """Base error for a rejected or incomplete live trial."""


class LiveBindingError(LiveExecutionError):
    """Raised when a context, artifact, request, or receipt binding fails."""


class LiveIsolationError(LiveExecutionError):
    """Raised when a trial root is unsafe or has already been used."""


class LiveHostEvidenceError(LiveExecutionError):
    """Raised when supported host evidence is absent or cannot prove execution."""


def _canonical_bytes(value: Any) -> bytes:
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise LiveBindingError(f"LIVE_JSON_UNSERIALIZABLE: {exc}") from exc


def _value_fingerprint(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
    except OSError as exc:
        raise LiveBindingError(f"ARTIFACT_READ_FAILED: {path}") from exc
    return digest.hexdigest()


def _assert_sha256(value: Any, field: str) -> str:
    text = str(value or "").lower()
    if not _SHA256_RE.fullmatch(text):
        raise LiveBindingError(f"{field}_INVALID")
    return text


def _assert_safe_value(value: Any, path: str = "value") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            permission_action_key = path.endswith(".permission_envelope") and key_text in PERMISSION_ACTIONS
            if _SECRET_KEY_RE.search(key_text) and not permission_action_key:
                raise LiveBindingError(f"SECRET_FIELD_FORBIDDEN: {path}.{key_text}")
            _assert_safe_value(child, f"{path}.{key_text}")
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            _assert_safe_value(child, f"{path}[{index}]")
    elif isinstance(value, str) and _SECRET_VALUE_RE.search(value):
        raise LiveBindingError(f"SECRET_VALUE_FORBIDDEN: {path}")


def _assert_trial_id(value: Any) -> str:
    text = str(value or "")
    if not _TRIAL_ID_RE.fullmatch(text):
        raise LiveBindingError("TRIAL_ID_INVALID")
    return text


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _parse_timestamp(value: Any) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise LiveHostEvidenceError("HOST_TIMESTAMP_MISSING")
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise LiveHostEvidenceError("HOST_TIMESTAMP_INVALID") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _relative_path(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError as exc:
        raise LiveBindingError(f"PATH_OUTSIDE_PROJECT: {path}") from exc


def _write_new_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
    except FileExistsError as exc:
        raise LiveIsolationError(f"REFUSING_TO_OVERWRITE: {path}") from exc


def _write_new_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(value)
    except FileExistsError as exc:
        raise LiveIsolationError(f"REFUSING_TO_OVERWRITE: {path}") from exc


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        raise LiveBindingError(f"REQUEST_READ_FAILED: {path}") from exc
    if not isinstance(value, dict):
        raise LiveBindingError("REQUEST_MUST_BE_OBJECT")
    return value


def _project_root(root: str | Path) -> Path:
    path = Path(root).expanduser().resolve()
    if not path.is_dir() or not (path / ".p2p").is_dir() or not (path / ".codex" / "config.toml").is_file():
        raise LiveIsolationError("PROJECT_ROOT_NOT_SUPPORTED")
    return path


def _new_trial_root(trial_root: str | Path, project_root: Path) -> tuple[Path, str]:
    root, relative = _trial_root_location(trial_root, project_root)
    root.parent.mkdir(parents=True, exist_ok=True)
    try:
        root.mkdir()
    except FileExistsError as exc:
        raise LiveIsolationError("TRIAL_ROOT_MUST_BE_NEW") from exc
    return root, relative


def _trial_root_location(trial_root: str | Path, project_root: Path) -> tuple[Path, str]:
    root = Path(trial_root).expanduser().resolve()
    project = project_root.resolve()
    try:
        relative = root.relative_to(project)
    except ValueError as exc:
        raise LiveIsolationError("TRIAL_ROOT_OUTSIDE_PROJECT") from exc
    if ".tmp" not in {part.casefold() for part in relative.parts}:
        raise LiveIsolationError("TRIAL_ROOT_MUST_BE_UNDER_REPOSITORY_TMP")
    if root == project or root.exists():
        raise LiveIsolationError("TRIAL_ROOT_MUST_BE_NEW")
    return root, relative.as_posix()


def default_execution_request(profile: str = "p2p_aesthetica") -> dict[str, Any]:
    """Return the fixed requested settings used for both conditions."""

    return {
        "profile": profile,
        "model": "HOST_DEFAULT",
        "provider": "UNKNOWN",
        "reasoning_effort": "INHERIT",
        "service_tier": "INHERIT",
        "permission_mode": "READ_ONLY",
        "network_policy": "NO_NETWORK_REQUESTED",
        "delegation_policy": "NO_CHILDREN",
        "max_workers": 1,
        "task_mode": "READ_ONLY_CONTEXT_TRIAL",
        "permission_envelope": dict(READ_ONLY_PERMISSION_ENVELOPE),
    }


def _validate_permission_envelope(value: Any) -> dict[str, bool]:
    if not isinstance(value, Mapping) or set(value) != set(PERMISSION_ACTIONS):
        raise LiveBindingError("PERMISSION_ENVELOPE_FIELDS_INVALID")
    if any(not isinstance(value[action], bool) for action in PERMISSION_ACTIONS):
        raise LiveBindingError("PERMISSION_ENVELOPE_VALUES_INVALID")
    if value["READ"] is not True or any(value[action] for action in PERMISSION_ACTIONS if action != "READ"):
        raise LiveBindingError("PERMISSION_ENVELOPE_NOT_READ_ONLY")
    return {action: bool(value[action]) for action in PERMISSION_ACTIONS}


def _validate_execution_request(value: Mapping[str, Any]) -> dict[str, Any]:
    _assert_safe_value(value, "requested_execution")
    allowed = set(default_execution_request())
    if set(value) != allowed:
        raise LiveBindingError("REQUESTED_EXECUTION_FIELDS_INVALID")
    result = {str(key): value[key] for key in value}
    if not isinstance(result["profile"], str) or not result["profile"].strip():
        raise LiveBindingError("REQUESTED_PROFILE_REQUIRED")
    if not is_supported_host_agent_type(result["profile"]):
        raise LiveBindingError("REQUESTED_PROFILE_UNSUPPORTED")
    fixed_values = {
        "model": "HOST_DEFAULT",
        "provider": "UNKNOWN",
        "reasoning_effort": "INHERIT",
        "service_tier": "INHERIT",
        "permission_mode": "READ_ONLY",
        "network_policy": "NO_NETWORK_REQUESTED",
        "delegation_policy": "NO_CHILDREN",
        "task_mode": "READ_ONLY_CONTEXT_TRIAL",
    }
    for field, expected in fixed_values.items():
        if result.get(field) != expected:
            raise LiveBindingError(f"REQUESTED_{field.upper()}_INVALID")
    if result["max_workers"] != 1 or result["delegation_policy"] != "NO_CHILDREN":
        raise LiveBindingError("REQUESTED_DELEGATION_BOUNDARY_INVALID")
    result["permission_envelope"] = _validate_permission_envelope(result["permission_envelope"])
    return result


def _default_guardrails() -> dict[str, Any]:
    return {
        "runtime_task_execution_requires_official_host": True,
        "proxy_cannot_promote": True,
        "no_recursive_delegation": True,
        "output_is_not_context": True,
        "permission_scope": "SUPPLIED_CONTEXT_ONLY",
        "control_plane_persistence": "EXISTING_TRIAL_AND_EXECUTION_LEDGER",
    }


def _validate_guardrails(value: Any) -> dict[str, Any]:
    expected = _default_guardrails()
    if not isinstance(value, Mapping) or dict(value) != expected:
        raise LiveBindingError("GUARDRAILS_INVALID")
    return expected


def default_route_observation(profile: str) -> dict[str, Any]:
    """Return backward-compatible route metadata for legacy callers."""

    requested_profile = None if profile == "default" else profile
    executor_class = HOST_DEFAULT_EXECUTOR_CLASS if profile == "default" else CUSTOM_PROFILE_EXECUTOR_CLASS
    return {
        "schema": ROUTE_OBSERVATION_SCHEMA,
        "logical_route": "legacy-live-context",
        "logical_capability": None,
        "supporting_capabilities": [],
        "requested_profile_if_any": requested_profile,
        "executor_class": executor_class,
    }


def _validate_route_observation(value: Mapping[str, Any] | None, profile: str) -> dict[str, Any]:
    route = default_route_observation(profile) if value is None else dict(value)
    _assert_safe_value(route, "route_observation")
    if set(route) != _ROUTE_OBSERVATION_FIELDS:
        raise LiveBindingError("ROUTE_OBSERVATION_FIELDS_INVALID")
    if route.get("schema") != ROUTE_OBSERVATION_SCHEMA:
        raise LiveBindingError("ROUTE_OBSERVATION_SCHEMA_INVALID")
    logical_route = route.get("logical_route")
    if not isinstance(logical_route, str) or not logical_route.strip() or len(logical_route) > _MAX_STRING_LENGTH:
        raise LiveBindingError("LOGICAL_ROUTE_INVALID")
    logical_capability = route.get("logical_capability")
    if logical_capability is not None and (
        not isinstance(logical_capability, str) or not logical_capability.strip() or len(logical_capability) > _MAX_STRING_LENGTH
    ):
        raise LiveBindingError("LOGICAL_CAPABILITY_INVALID")
    supporting = route.get("supporting_capabilities")
    if not isinstance(supporting, list) or any(
        not isinstance(item, str) or not item.strip() or len(item) > _MAX_STRING_LENGTH for item in supporting
    ):
        raise LiveBindingError("SUPPORTING_CAPABILITIES_INVALID")
    requested_profile = route.get("requested_profile_if_any")
    if requested_profile is not None and not is_supported_host_agent_type(requested_profile):
        raise LiveBindingError("REQUESTED_PROFILE_UNSUPPORTED")
    executor_class = route.get("executor_class")
    if executor_class not in {HOST_DEFAULT_EXECUTOR_CLASS, CUSTOM_PROFILE_EXECUTOR_CLASS}:
        raise LiveBindingError("REQUESTED_EXECUTOR_CLASS_INVALID")
    if executor_class == HOST_DEFAULT_EXECUTOR_CLASS:
        if profile != "default" or requested_profile is not None:
            raise LiveBindingError("HOST_DEFAULT_ROUTE_PROFILE_MISMATCH")
    elif requested_profile != profile:
        raise LiveBindingError("CUSTOM_ROUTE_PROFILE_MISMATCH")
    return route


def _validate_artifact_binding(value: Mapping[str, Any]) -> dict[str, Any]:
    _assert_safe_value(value, "artifact_binding")
    required = {"package_version", "artifact_path", "artifact_sha256"}
    if not required.issubset(value):
        raise LiveBindingError("ARTIFACT_BINDING_INCOMPLETE")
    artifact_path = Path(str(value["artifact_path"])).expanduser().resolve()
    if not artifact_path.is_file():
        raise LiveBindingError("ARTIFACT_NOT_FOUND")
    expected = _assert_sha256(value["artifact_sha256"], "ARTIFACT_SHA256")
    actual = _file_sha256(artifact_path)
    if actual != expected:
        raise LiveBindingError("ARTIFACT_SHA256_MISMATCH")
    result = {str(key): value[key] for key in value}
    result["artifact_path"] = str(artifact_path)
    result["artifact_sha256"] = expected
    if "context_runtime_sha256" in value:
        result["context_runtime_sha256"] = _assert_sha256(value["context_runtime_sha256"], "CONTEXT_RUNTIME_SHA256")
    if "context_runtime_member" in value:
        member = str(value["context_runtime_member"])
        if not member or member.startswith("/") or ".." in Path(member).parts:
            raise LiveBindingError("CONTEXT_RUNTIME_MEMBER_INVALID")
        result["context_runtime_member"] = member
        expected_runtime = result.get("context_runtime_sha256")
        if expected_runtime and artifact_path.suffix.lower() == ".zip":
            try:
                with zipfile.ZipFile(artifact_path) as archive:
                    actual_runtime = hashlib.sha256(archive.read(member)).hexdigest()
            except (OSError, KeyError, zipfile.BadZipFile) as exc:
                raise LiveBindingError("CONTEXT_RUNTIME_MEMBER_READ_FAILED") from exc
            if actual_runtime != expected_runtime:
                raise LiveBindingError("CONTEXT_RUNTIME_SHA256_MISMATCH")
    return result


def _validate_context(
    *,
    context_input: Mapping[str, Any],
    context_view: Mapping[str, Any],
    mode: str,
    source_catalog: Mapping[str, Any] | list[Mapping[str, Any]] | tuple[Mapping[str, Any], ...],
    context_builder: Callable[[Mapping[str, Any], str], Mapping[str, Any]] = build_context_view,
) -> dict[str, Any]:
    _assert_safe_value(context_input, "context_input")
    _assert_safe_value(context_view, "context_view")
    if context_view.get("schema") != CONTEXT_VIEW_SCHEMA:
        raise LiveBindingError("CONTEXT_VIEW_SCHEMA_INVALID")
    if context_view.get("context_mode") != mode:
        raise LiveBindingError("CONTEXT_MODE_MISMATCH")
    fingerprint = _assert_sha256(context_view.get("context_fingerprint"), "CONTEXT_FINGERPRINT")
    manifest = context_view.get("context_manifest")
    if not isinstance(manifest, Mapping) or manifest.get("schema") != CONTEXT_MANIFEST_SCHEMA:
        raise LiveBindingError("CONTEXT_MANIFEST_INVALID")
    if manifest.get("context_mode") != mode or manifest.get("context_fingerprint") != fingerprint:
        raise LiveBindingError("CONTEXT_MANIFEST_BINDING_INVALID")
    serialized_size = context_view.get("serialized_size")
    if not isinstance(serialized_size, Mapping) or serialized_size.get("label") != LOCAL_SERIALIZATION_PROXY:
        raise LiveBindingError("CONTEXT_SERIALIZATION_AUTHORITY_INVALID")
    try:
        validation = validate_context_bindings(context_view, source_catalog)
    except Exception as exc:  # context.py owns the detailed stale/binding taxonomy
        raise LiveBindingError(str(exc)) from exc
    rebuilt = dict(context_builder(context_input, mode))
    if rebuilt != dict(context_view):
        raise LiveBindingError("CONTEXT_VIEW_RECONSTRUCTION_MISMATCH")
    return {"context_fingerprint": fingerprint, "context_manifest": dict(manifest), "binding_validation": validation}


def _validate_fixture(value: Mapping[str, Any], scenario_id: str, condition: str, root_relative: str) -> tuple[dict[str, Any], str]:
    _assert_safe_value(value, "fixture")
    if value.get("scenario_id") not in {None, scenario_id}:
        raise LiveBindingError("FIXTURE_SCENARIO_MISMATCH")
    if value.get("condition") not in {None, condition}:
        raise LiveBindingError("FIXTURE_CONDITION_MISMATCH")
    if value.get("read_only") is not True:
        raise LiveBindingError("FIXTURE_MUST_BE_READ_ONLY")
    record = {
        "schema": "p2p-live-fixture/1",
        "scenario_id": scenario_id,
        "condition": condition,
        "root_relative": root_relative,
        "fixture": dict(value),
    }
    return record, _value_fingerprint(record)


def _host_prompt(context_view: Mapping[str, Any], trial_id: str, request_fingerprint: str) -> str:
    payload = json.dumps(context_view, ensure_ascii=False, sort_keys=True, indent=2)
    return (
        "Perform one bounded, read-only P2P-C07 context trial. Do not edit files, "
        "write project state, call external services, reveal hidden reasoning, "
        "or spawn/delegate to another worker. Use the supplied context_view as "
        "the complete task input; do not add prior trial output or resolve "
        "unlisted project state. Return a concise observable result that includes "
        "the supplied context_fingerprint and the main acceptance observations. "
        f"Trial reference: {trial_id}. Request fingerprint: {request_fingerprint}.\n\n"
        "SUPPLIED_CONTEXT_VIEW_JSON_BEGIN\n"
        f"{payload}\n"
        "SUPPLIED_CONTEXT_VIEW_JSON_END"
    )


def prepare_trial(
    *,
    trial_id: str,
    condition: str,
    scenario_id: str,
    context_input: Mapping[str, Any],
    context_view: Mapping[str, Any],
    source_catalog: Mapping[str, Any] | list[Mapping[str, Any]] | tuple[Mapping[str, Any], ...],
    fixture: Mapping[str, Any],
    artifact_binding: Mapping[str, Any],
    requested_execution: Mapping[str, Any],
    route_observation: Mapping[str, Any] | None = None,
    trial_root: str | Path,
    project_root: str | Path,
    context_builder: Callable[[Mapping[str, Any], str], Mapping[str, Any]] = build_context_view,
) -> dict[str, Any]:
    """Validate and persist a new host request without claiming execution."""

    trial_id = _assert_trial_id(trial_id)
    if condition not in CONDITION_MODES:
        raise LiveBindingError("CONDITION_INVALID")
    if scenario_id not in SUPPORTED_SCENARIOS:
        raise LiveBindingError("SCENARIO_INVALID")
    project = _project_root(project_root)
    root, root_relative = _trial_root_location(trial_root, project)
    mode = CONDITION_MODES[condition]
    execution = _validate_execution_request(requested_execution)
    route = _validate_route_observation(route_observation, str(execution["profile"]))
    artifact = _validate_artifact_binding(artifact_binding)
    context_result = _validate_context(
        context_input=context_input,
        context_view=context_view,
        mode=mode,
        source_catalog=source_catalog,
        context_builder=context_builder,
    )
    fixture_record, fixture_fingerprint = _validate_fixture(fixture, scenario_id, condition, root_relative)
    root, root_relative = _new_trial_root(trial_root, project)
    context_fingerprint_value = context_result["context_fingerprint"]
    prepared_at = _utc_now()
    prepared_monotonic_ns = time.monotonic_ns()
    request_payload: dict[str, Any] = {
        "schema": LIVE_REQUEST_SCHEMA,
        "trial_id": trial_id,
        "condition": condition,
        "scenario_id": scenario_id,
        "context_mode": mode,
        "context_fingerprint": context_fingerprint_value,
        "context_manifest": context_result["context_manifest"],
        "context_view": dict(context_view),
        "fixture_fingerprint": fixture_fingerprint,
        "artifact_binding": artifact,
        "requested_execution": execution,
        "route_observation": route,
        "guardrails": _default_guardrails(),
    }
    _assert_safe_value(request_payload, "request")
    request_fingerprint = _value_fingerprint(request_payload)
    request_path = root / "request.json"
    manifest_path = root / "context-manifest.json"
    fixture_path = root / "fixture.json"
    manifest_record = dict(context_result["context_manifest"])
    manifest_record["trial_id"] = trial_id
    manifest_record["context_manifest_pointer"] = _relative_path(manifest_path, project)
    _write_new_json(request_path, {**request_payload, "request_fingerprint": request_fingerprint})
    _write_new_json(manifest_path, manifest_record)
    _write_new_json(fixture_path, {**fixture_record, "fixture_fingerprint": fixture_fingerprint})
    return {
        "schema": LIVE_TRIAL_SCHEMA,
        "trial_id": trial_id,
        "condition": condition,
        "scenario_id": scenario_id,
        "context_mode": mode,
        "context_fingerprint": context_fingerprint_value,
        "context_manifest_pointer": _relative_path(manifest_path, project),
        "fixture_fingerprint": fixture_fingerprint,
        "artifact_binding": artifact,
        "requested_execution": execution,
        "route_observation": route,
        "requested_execution_fingerprint": _value_fingerprint(execution),
        "request_fingerprint": request_fingerprint,
        "request_pointer": _relative_path(request_path, project),
        "fixture_pointer": _relative_path(fixture_path, project),
        "trial_root": str(root),
        "project_root": str(project),
        "prepared_at": prepared_at,
        "prepared_monotonic_ns": prepared_monotonic_ns,
        "host_prompt": _host_prompt(context_view, trial_id, request_fingerprint),
        "runtime_task_execution": False,
        "status": "PREPARED",
    }


def _load_prepared_request(prepared: Mapping[str, Any]) -> tuple[dict[str, Any], Path, Path, datetime]:
    _assert_safe_value(prepared, "prepared")
    project = _project_root(str(prepared.get("project_root", "")))
    root = Path(str(prepared.get("trial_root", ""))).expanduser().resolve()
    try:
        root.relative_to(project)
    except ValueError as exc:
        raise LiveIsolationError("PREPARED_ROOT_OUTSIDE_PROJECT") from exc
    request_path = root / "request.json"
    request = _load_json(request_path)
    provided_fingerprint = request.pop("request_fingerprint", None)
    if provided_fingerprint != prepared.get("request_fingerprint") or _value_fingerprint(request) != str(prepared.get("request_fingerprint")):
        raise LiveBindingError("REQUEST_FINGERPRINT_MISMATCH")
    if request.get("schema") != LIVE_REQUEST_SCHEMA:
        raise LiveBindingError("REQUEST_SCHEMA_INVALID")
    if request.get("trial_id") != prepared.get("trial_id"):
        raise LiveBindingError("TRIAL_ID_BINDING_INVALID")
    if request.get("context_fingerprint") != prepared.get("context_fingerprint"):
        raise LiveBindingError("CONTEXT_FINGERPRINT_BINDING_INVALID")
    _validate_guardrails(request.get("guardrails"))
    requested_execution = request.get("requested_execution")
    if not isinstance(requested_execution, Mapping):
        raise LiveBindingError("REQUESTED_EXECUTION_INVALID")
    profile = str(requested_execution.get("profile") or "")
    _validate_execution_request(requested_execution)
    route_observation = request.get("route_observation")
    request["route_observation"] = _validate_route_observation(route_observation, profile)
    try:
        created_at = datetime.fromisoformat(str(prepared["prepared_at"]))
    except (KeyError, TypeError, ValueError) as exc:
        raise LiveBindingError("PREPARED_TIMESTAMP_INVALID") from exc
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    return request, project, root, created_at.astimezone(timezone.utc)


def _valid_host_receipt(value: Any) -> bool:
    if not isinstance(value, Mapping) or set(value) != _HOST_RECEIPT_FIELDS:
        return False
    if not validate_host_identity_receipt(value):
        return False
    if value.get("event") not in {"SubagentStart", "SubagentStop"}:
        return False
    for field in _HOST_RECEIPT_FIELDS - {"schema", "event", "source"}:
        if not isinstance(value.get(field), str) or not value[field].strip() or len(value[field]) > 4096:
            return False
    return True


def _find_fresh_host_receipt(
    ledger_path: Path,
    *,
    agent_id: str,
    expected_agent_type: str,
    not_before: datetime,
    project_root: Path,
    expected_session_id: str | None = None,
    expected_turn_id: str | None = None,
) -> dict[str, Any]:
    if not ledger_path.is_file():
        raise LiveHostEvidenceError("HOST_EVIDENCE_CAPTURE_FAILURE")
    matches: list[dict[str, Any]] = []
    try:
        lines = ledger_path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        raise LiveHostEvidenceError("HOST_EVIDENCE_CAPTURE_FAILURE") from exc
    for line in lines:
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if not isinstance(event, Mapping) or event.get("schema_version") != EXECUTION_LEDGER_SCHEMA or event.get("event") != "host_subagent_identity_receipt":
            continue
        receipt = event.get("receipt")
        if not _valid_host_receipt(receipt):
            continue
        if receipt.get("agent_id") != agent_id:
            continue
        observed_at = _parse_timestamp(receipt.get("timestamp"))
        if observed_at < not_before - timedelta(seconds=2):
            continue
        cwd = Path(str(receipt["cwd"])).expanduser().resolve()
        try:
            cwd.relative_to(project_root)
        except ValueError as exc:
            raise LiveHostEvidenceError("HOST_CWD_OUTSIDE_PROJECT") from exc
        matches.append(dict(receipt))
    if not matches:
        raise LiveHostEvidenceError("HOST_EVIDENCE_CAPTURE_FAILURE")
    matches.sort(key=lambda item: _parse_timestamp(item["timestamp"]))
    receipt = matches[-1]
    if receipt.get("agent_type") != expected_agent_type:
        raise LiveHostEvidenceError("HOST_IDENTITY_MISMATCH")
    if expected_session_id is not None and receipt.get("session_id") != expected_session_id:
        raise LiveHostEvidenceError("HOST_SESSION_ID_MISMATCH")
    if expected_turn_id is not None and receipt.get("turn_id") != expected_turn_id:
        raise LiveHostEvidenceError("HOST_TURN_ID_MISMATCH")
    return receipt


def _optional_host_id(value: Any, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip() or len(value) > _MAX_STRING_LENGTH:
        raise LiveHostEvidenceError(f"{field}_INVALID")
    return value


def _validate_host_permission_mode(value: Any) -> str:
    normalized = str(value or "").strip().upper().replace("-", "_").replace(" ", "_")
    if normalized not in HOST_READ_ONLY_PERMISSION_MODES:
        raise LiveHostEvidenceError("HOST_PERMISSION_BOUNDARY_UNPROVEN")
    return normalized


def _output_text(value: Any) -> str:
    if isinstance(value, str):
        output = value
    elif isinstance(value, Mapping) or isinstance(value, list):
        try:
            output = json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)
        except (TypeError, ValueError) as exc:
            raise LiveHostEvidenceError("HOST_OUTPUT_UNSERIALIZABLE") from exc
    else:
        raise LiveHostEvidenceError("HOST_OUTPUT_MISSING")
    if not output.strip():
        raise LiveHostEvidenceError("HOST_OUTPUT_EMPTY")
    if _SECRET_VALUE_RE.search(output):
        raise LiveHostEvidenceError("HOST_OUTPUT_SECRET_LIKE")
    return output


def _telemetry(value: Any, authority: str, *, reason: str | None = None) -> dict[str, Any]:
    if authority not in TELEMETRY_AUTHORITIES:
        raise LiveBindingError("TELEMETRY_AUTHORITY_INVALID")
    result = {"value": value, "authority": authority}
    if reason:
        result["reason"] = reason
    return result


def _ledger_has_trial(path: Path, trial_id: str) -> bool:
    if not path.is_file():
        return False
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError):
        return False
    for line in lines:
        try:
            event = json.loads(line)
        except ValueError:
            continue
        receipt = event.get("receipt") if isinstance(event, Mapping) else None
        if isinstance(event, Mapping) and event.get("event") == LIVE_LEDGER_EVENT and isinstance(receipt, Mapping) and receipt.get("trial_id") == trial_id:
            return True
    return False


def _append_live_ledger(path: Path, receipt: Mapping[str, Any]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    if _ledger_has_trial(path, str(receipt["trial_id"])):
        return "DUPLICATE"
    event = {
        "schema_version": EXECUTION_LEDGER_SCHEMA,
        "at": _utc_now(),
        "event": LIVE_LEDGER_EVENT,
        "receipt": dict(receipt),
    }
    try:
        with path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
    except OSError as exc:
        raise LiveBindingError("LIVE_LEDGER_APPEND_FAILED") from exc
    return "RECORDED"


def finalize_trial(
    prepared: Mapping[str, Any],
    host_result: Mapping[str, Any],
    *,
    require_live: bool = True,
    ledger_path: str | Path | None = None,
) -> dict[str, Any]:
    """Capture output and issue a receipt; only official host evidence is live."""

    request, project, root, prepared_at = _load_prepared_request(prepared)
    _assert_safe_value({key: value for key, value in host_result.items() if key != "output"}, "host_result")
    source = str(host_result.get("execution_source") or "")
    is_proxy = source in {LOCAL_PROXY_SOURCE, "LOCAL_EVALUATOR", "DETERMINISTIC_PROXY"}
    if is_proxy:
        if require_live:
            raise LiveHostEvidenceError("PROXY_CANNOT_PROMOTE_TO_LIVE")
        receipt_host: dict[str, Any] | None = None
        execution_authority = "LOCAL_PROXY"
        runtime_task_execution = False
        output = _output_text(host_result.get("output"))
    else:
        if source != HOST_EXECUTION_SOURCE:
            raise LiveHostEvidenceError("SUPPORTED_HOST_SOURCE_REQUIRED")
        if host_result.get("execution_completed") is not True:
            raise LiveHostEvidenceError("HOST_EXECUTION_NOT_COMPLETED")
        if host_result.get("child_count", 0) != 0 or host_result.get("delegation_depth", 0) != 0:
            raise LiveHostEvidenceError("RECURSIVE_DELEGATION_DETECTED")
        agent_id = str(host_result.get("host_execution_id") or "")
        expected_profile = str(request["requested_execution"]["profile"])
        if not agent_id:
            raise LiveHostEvidenceError("HOST_EXECUTION_ID_MISSING")
        expected_session_id = _optional_host_id(host_result.get("session_id"), "HOST_SESSION_ID")
        expected_turn_id = _optional_host_id(host_result.get("turn_id"), "HOST_TURN_ID")
        ledger = Path(str(ledger_path)).expanduser().resolve() if ledger_path else project / ".p2p" / "state" / "execution-ledger.jsonl"
        receipt_host = _find_fresh_host_receipt(
            ledger,
            agent_id=agent_id,
            expected_agent_type=expected_profile,
            not_before=prepared_at,
            project_root=project,
            expected_session_id=expected_session_id,
            expected_turn_id=expected_turn_id,
        )
        _validate_host_permission_mode(receipt_host.get("permission_mode"))
        output = _output_text(host_result.get("output"))
        execution_authority = "HOST"
        runtime_task_execution = True

    output_path = root / "output.txt"
    _write_new_text(output_path, output)
    elapsed_ns = time.monotonic_ns() - int(prepared.get("prepared_monotonic_ns", time.monotonic_ns()))
    elapsed_ms = round(max(0, elapsed_ns) / 1_000_000, 3)
    observed = {
        "session_id": receipt_host.get("session_id", "UNKNOWN") if receipt_host else "UNKNOWN",
        "turn_id": receipt_host.get("turn_id", "UNKNOWN") if receipt_host else "UNKNOWN",
        "agent_id": receipt_host.get("agent_id", "UNKNOWN") if receipt_host else "UNKNOWN",
        "agent_type": receipt_host.get("agent_type", "UNKNOWN") if receipt_host else "UNKNOWN",
        "permission_mode": receipt_host.get("permission_mode", "UNKNOWN") if receipt_host else "UNKNOWN",
        "model": receipt_host.get("model", "UNKNOWN") if receipt_host else "UNKNOWN",
        "provider": "UNKNOWN",
        "cwd": receipt_host.get("cwd", "UNKNOWN") if receipt_host else "UNKNOWN",
        "source": receipt_host.get("source", execution_authority) if receipt_host else execution_authority,
    }
    route_observation = request["route_observation"]
    observed_host_agent_type = observed["agent_type"]
    observed_host_executor_class = host_agent_class(observed_host_agent_type) if receipt_host else None
    provider_reason = "official identity receipt does not expose provider-owned telemetry"
    receipt: dict[str, Any] = {
        "schema": LIVE_RECEIPT_SCHEMA,
        "trial_id": request["trial_id"],
        "condition": request["condition"],
        "condition_id": request["condition"],
        "scenario_id": request["scenario_id"],
        "context_mode": request["context_mode"],
        "context_fingerprint": request["context_fingerprint"],
        "context_manifest_pointer": prepared["context_manifest_pointer"],
        "fixture_fingerprint": request["fixture_fingerprint"],
        "artifact_binding": request["artifact_binding"],
        "isolated_root": _relative_path(root, project),
        "source_version": request["artifact_binding"]["package_version"],
        "artifact_path": request["artifact_binding"]["artifact_path"],
        "artifact_sha256": request["artifact_binding"]["artifact_sha256"],
        "request_fingerprint": prepared["request_fingerprint"],
        "request_pointer": prepared["request_pointer"],
        "requested_execution": request["requested_execution"],
        "permission_envelope": dict(request["requested_execution"]["permission_envelope"]),
        "permission_observation": {
            "requested_mode": request["requested_execution"]["permission_mode"],
            "observed_mode": observed["permission_mode"],
            "status": "VERIFIED" if receipt_host else "UNKNOWN",
            "scope": request["guardrails"]["permission_scope"],
        },
        "requested_execution_fingerprint": prepared["requested_execution_fingerprint"],
        "route_observation": route_observation,
        "logical_route": route_observation["logical_route"],
        "logical_capability": route_observation["logical_capability"],
        "supporting_capabilities": route_observation["supporting_capabilities"],
        "requested_profile_if_any": route_observation["requested_profile_if_any"],
        "requested_executor_class": route_observation["executor_class"],
        "session_id": observed["session_id"],
        "turn_id": observed["turn_id"],
        "agent_type_or_profile": request["requested_execution"]["profile"],
        "observed_host_agent_type": observed_host_agent_type,
        "observed_host_executor_class": observed_host_executor_class,
        "identity_authority": receipt_host.get("source", "NONE") if receipt_host else "NONE",
        "requested_model": request["requested_execution"]["model"],
        "observed_model": observed["model"],
        "requested_reasoning_effort": request["requested_execution"]["reasoning_effort"],
        "observed_reasoning_effort": "UNKNOWN",
        "requested_provider_or_surface": HOST_EXECUTION_SOURCE,
        "observed_provider_or_surface": HOST_EXECUTION_SOURCE if receipt_host else LOCAL_PROXY_SOURCE,
        "observed_execution": observed,
        "host_identity_receipt": receipt_host,
        "host_execution_id": receipt_host.get("agent_id") if receipt_host else None,
        "runtime_task_execution": runtime_task_execution,
        "execution_authority": execution_authority,
        "output_pointer": _relative_path(output_path, project),
        "output_sha256": _file_sha256(output_path),
        "output_bytes": len(output.encode("utf-8")),
        "prepared_at": prepared["prepared_at"],
        "completed_at": _utc_now(),
        "started_at": prepared["prepared_at"],
        "finished_at": _utc_now(),
        "completion_status": "COMPLETED_LIVE" if runtime_task_execution else "PROXY_ONLY",
        "acceptance_evidence_pointers": [prepared["context_manifest_pointer"], _relative_path(output_path, project)],
        "telemetry": {
            "model": _telemetry(observed["model"], "HOST" if receipt_host else "LOCAL_PROXY"),
            "provider": _telemetry("UNKNOWN", "UNKNOWN", reason=provider_reason),
            "provider_tokens": _telemetry("UNKNOWN", "UNKNOWN", reason="provider-owned token usage is not exposed by this host receipt"),
            "provider_cost": _telemetry("UNKNOWN", "UNKNOWN", reason="provider-owned cost is not exposed by this host receipt"),
            "input_tokens": _telemetry("UNKNOWN", "UNKNOWN", reason="provider-owned input tokens are not exposed by this host receipt"),
            "cached_input_tokens": _telemetry("UNKNOWN", "UNKNOWN", reason="provider-owned cache telemetry is not exposed by this host receipt"),
            "output_tokens": _telemetry("UNKNOWN", "UNKNOWN", reason="provider-owned output tokens are not exposed by this host receipt"),
            "total_tokens": _telemetry("UNKNOWN", "UNKNOWN", reason="provider-owned total tokens are not exposed by this host receipt"),
            "provider_calls": _telemetry("UNKNOWN", "UNKNOWN", reason="provider call count is not exposed by this host receipt"),
            "tool_calls": _telemetry("UNKNOWN", "UNKNOWN", reason="tool call count is not exposed by this host receipt"),
            "child_calls": _telemetry("UNKNOWN", "UNKNOWN", reason="child call count is not provider telemetry"),
            "wall_time_ms": _telemetry(elapsed_ms, "LOCAL_MONOTONIC_TIMER"),
            "local_wall_time_ms": _telemetry(elapsed_ms, "LOCAL_MONOTONIC_TIMER"),
            "retries": _telemetry("UNKNOWN", "UNKNOWN", reason="retry count is not exposed by this host receipt"),
            "failures": _telemetry("UNKNOWN", "UNKNOWN", reason="host failure telemetry is not exposed by this receipt"),
            "compaction_events": _telemetry("UNKNOWN", "UNKNOWN", reason="compaction telemetry is not exposed by this host receipt"),
            "main_context_measure": _telemetry(request["context_view"]["serialized_size"]["bytes"], "LOCAL_PROXY", reason=LOCAL_SERIALIZATION_PROXY),
            "context_serialized_bytes": _telemetry(request["context_view"]["serialized_size"]["bytes"], "LOCAL_PROXY", reason=LOCAL_SERIALIZATION_PROXY),
            "cost": _telemetry("UNKNOWN", "UNKNOWN", reason="provider-owned cost is not exposed by this host receipt"),
            "request_fingerprint": _telemetry(prepared["request_fingerprint"], "DETERMINISTIC_RUNTIME"),
        },
    }
    receipt_path = root / "receipt.json"
    receipt["receipt_pointer"] = _relative_path(receipt_path, project)
    ledger = Path(str(ledger_path)).expanduser().resolve() if ledger_path else project / ".p2p" / "state" / "execution-ledger.jsonl"
    if runtime_task_execution:
        ledger_status = "DUPLICATE" if _ledger_has_trial(ledger, str(receipt["trial_id"])) else "RECORDED"
        receipt["ledger_event_status"] = ledger_status
        appended_status = _append_live_ledger(ledger, receipt)
        if appended_status != ledger_status:
            raise LiveBindingError("LIVE_LEDGER_STATUS_RACE")
    else:
        ledger_status = "NOT_REQUIRED"
        receipt["ledger_event_status"] = ledger_status
    _write_new_json(receipt_path, receipt)
    return receipt


def execute_live_context_trial(
    *,
    host_executor: Callable[[str], Mapping[str, Any]],
    require_live: bool = True,
    **prepare_kwargs: Any,
) -> dict[str, Any]:
    """Prepare, hand off once to a supported executor, and finalize safely.

    The host executor is an integration seam.  A local proxy may be injected
    for tests, but it can only produce a `runtime_task_execution=false` result.
    The real Codex host adapter is intentionally supplied by the supported
    host surface rather than implemented through private APIs here.
    """

    prepared = prepare_trial(**prepare_kwargs)
    result = host_executor(str(prepared["host_prompt"]))
    if not isinstance(result, Mapping):
        raise LiveHostEvidenceError("HOST_EXECUTOR_RESULT_INVALID")
    return finalize_trial(prepared, result, require_live=require_live)


__all__ = [
    "CONDITION_MODES",
    "HOST_EXECUTION_SOURCE",
    "LIVE_RECEIPT_SCHEMA",
    "LOCAL_PROXY_SOURCE",
    "PERMISSION_ACTIONS",
    "READ_ONLY_PERMISSION_ENVELOPE",
    "SUPPORTED_SCENARIOS",
    "LiveBindingError",
    "LiveExecutionError",
    "LiveHostEvidenceError",
    "LiveIsolationError",
    "default_execution_request",
    "default_route_observation",
    "execute_live_context_trial",
    "finalize_trial",
    "prepare_trial",
]
