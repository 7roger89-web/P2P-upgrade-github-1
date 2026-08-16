from __future__ import annotations

"""C20 provider-neutral host/executor boundary primitives.

This module is a contract and normalization seam only. It does not launch
hosts, select providers, create background workers, or replace C12/C15.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
import re
from typing import Any, Iterable, Mapping, Sequence


HOST_CONTRACT_SCHEMA = "p2p-host-executor-contract/1"
PORTABLE_REQUEST_SCHEMA = "p2p-portable-execution-request/1"
PORTABLE_RECEIPT_SCHEMA = "p2p-portable-execution-receipt/1"
PORTABLE_HANDOFF_SCHEMA = "p2p-portable-handoff/1"

SUPPORTED = "SUPPORTED"
UNSUPPORTED = "UNSUPPORTED"
UNKNOWN = "UNKNOWN"
CAPABILITY_STATES = (SUPPORTED, UNSUPPORTED, UNKNOWN)

ENVIRONMENTS = ("LOCAL_PROJECT", "REMOTE_COPY", "CLOUD_SANDBOX", "REMOTE_REPOSITORY", UNKNOWN)

CAPABILITY_DIMENSIONS = (
    "can_read_files",
    "can_write_files",
    "can_execute_commands",
    "can_run_tests",
    "can_use_network",
    "can_receive_context_refs",
    "can_return_artifact_refs",
    "can_cancel",
    "can_report_progress",
    "can_return_authoritative_execution_id",
    "can_report_model_provider",
    "can_report_token_telemetry",
    "can_resume",
    "supports_foreground_execution",
    "supports_delegated_child_execution",
)

ERROR_CLASSES = (
    "CAPABILITY_UNAVAILABLE",
    "PERMISSION_BLOCKED",
    "OWNER_ACTION_REQUIRED",
    "HOST_UNAVAILABLE",
    "CONTROL_PLANE_FAILURE",
    "EXECUTION_FAILED",
    "EXECUTION_INTERRUPTED",
    "RESULT_UNKNOWN",
    "PARTIAL_MUTATION_UNKNOWN",
    "TIMEOUT",
    "CANCELLED",
    "STALE_REQUEST",
    "STALE_CONTEXT",
    "IDENTITY_EVIDENCE_UNAVAILABLE",
    "RECONCILIATION_REQUIRED",
)

_EXECUTION_STATUSES = ("SUCCEEDED", "FAILED", "INTERRUPTED", "UNKNOWN", "BLOCKED", "CANCELLED", "PARTIAL_MUTATION_UNKNOWN")
_VERIFICATION_STATUSES = ("VERIFIED", "FAILED", "INCOMPLETE", "UNKNOWN")
_SECRET_KEYS = re.compile(r"(?:secret|password|api[_-]?key|credential|token_value|chain[_-]?of[_-]?thought|chat[_-]?history)", re.I)
_SECRET_VALUES = re.compile(r"(?:\bsk-[A-Za-z0-9]|\btoken\s*=|\bpassword\s*=|\bBEGIN\s+(?:RSA|OPENSSH|PRIVATE))", re.I)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _text(value: Any, field_name: str, *, max_length: int = 1024) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > max_length:
        raise HostExecutorContractError(f"{field_name}_INVALID")
    if _SECRET_VALUES.search(value):
        raise HostExecutorContractError(f"{field_name}_SECRET_LIKE")
    return value.strip()


def _optional_text(value: Any, field_name: str, *, max_length: int = 512) -> str | None:
    if value is None:
        return None
    return _text(value, field_name, max_length=max_length)


def _refs(values: Iterable[Any] | None, field_name: str, *, max_length: int = 1024) -> tuple[str, ...]:
    if values is None:
        return ()
    if isinstance(values, str):
        raise HostExecutorContractError(f"{field_name}_MUST_BE_LIST")
    result: list[str] = []
    seen: set[str] = set()
    try:
        iterator = iter(values)
    except TypeError as exc:
        raise HostExecutorContractError(f"{field_name}_MUST_BE_LIST") from exc
    for raw in iterator:
        item = _text(raw, f"{field_name}_ITEM", max_length=max_length).replace("\\", "/")
        if item in seen:
            raise HostExecutorContractError(f"{field_name}_DUPLICATE:{item}")
        seen.add(item)
        result.append(item)
    return tuple(result)


def _safe_json(value: Any, *, path: str = "value", depth: int = 0) -> Any:
    if depth > 8:
        raise HostExecutorContractError(f"{path}_TOO_DEEP")
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for raw_key, raw_child in value.items():
            key = str(raw_key)
            if _SECRET_KEYS.search(key):
                raise HostExecutorContractError(f"{path}.{key}_SECRET_FIELD")
            result[key] = _safe_json(raw_child, path=f"{path}.{key}", depth=depth + 1)
        return result
    if isinstance(value, (list, tuple)):
        if len(value) > 128:
            raise HostExecutorContractError(f"{path}_TOO_LARGE")
        return [_safe_json(item, path=f"{path}[{index}]", depth=depth + 1) for index, item in enumerate(value)]
    if isinstance(value, str):
        if len(value) > 8192 or _SECRET_VALUES.search(value):
            raise HostExecutorContractError(f"{path}_SECRET_OR_TOO_LARGE")
        return value
    if value is None or isinstance(value, (bool, int, float)):
        return value
    raise HostExecutorContractError(f"{path}_TYPE_INVALID")


def _canonical_fingerprint(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


class HostExecutorContractError(ValueError):
    """Raised when a portable host contract violates a bounded invariant."""


class HostExecutorStaleRequestError(HostExecutorContractError):
    """Raised when a portable request is bound to stale project state."""


@dataclass(frozen=True)
class HostCapabilityProfile:
    """A declarative host capability profile; it grants no P2P permission."""

    adapter_class: str
    capabilities: Mapping[str, str] = field(default_factory=dict)
    environment: str = UNKNOWN
    host_label: str | None = None
    provider: str | None = None
    model: str | None = None

    def __post_init__(self) -> None:
        _text(self.adapter_class, "adapter_class", max_length=256)
        if self.environment not in ENVIRONMENTS:
            raise HostExecutorContractError("ENVIRONMENT_INVALID")
        if self.host_label is not None:
            _text(self.host_label, "host_label", max_length=256)
        if self.provider is not None:
            _text(self.provider, "provider", max_length=256)
        if self.model is not None:
            _text(self.model, "model", max_length=256)
        if not isinstance(self.capabilities, Mapping):
            raise HostExecutorContractError("CAPABILITIES_MUST_BE_OBJECT")
        for name, state in self.capabilities.items():
            _text(name, "capability_name", max_length=128)
            if state not in CAPABILITY_STATES:
                raise HostExecutorContractError(f"CAPABILITY_STATE_INVALID:{name}")

    def state(self, capability: str) -> str:
        return str(self.capabilities.get(capability, UNKNOWN))

    def supports(self, capability: str) -> bool:
        return self.state(capability) == SUPPORTED

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": HOST_CONTRACT_SCHEMA,
            "adapter_class": self.adapter_class,
            "host_label": self.host_label,
            "environment": self.environment,
            "capabilities": {name: self.state(name) for name in CAPABILITY_DIMENSIONS},
            "provider": self.provider,
            "model": self.model,
            "provider_status": SUPPORTED if self.provider else UNKNOWN,
            "model_status": SUPPORTED if self.model else UNKNOWN,
        }

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "HostCapabilityProfile":
        if not isinstance(value, Mapping) or value.get("schema") != HOST_CONTRACT_SCHEMA:
            raise HostExecutorContractError("HOST_CONTRACT_SCHEMA_INVALID")
        return cls(
            adapter_class=_text(value.get("adapter_class"), "adapter_class", max_length=256),
            capabilities=dict(value.get("capabilities") or {}),
            environment=value.get("environment", UNKNOWN),
            host_label=value.get("host_label"),
            provider=value.get("provider"),
            model=value.get("model"),
        )


@dataclass(frozen=True)
class PortableExecutionRequest:
    """Smallest sufficient neutral request; it contains no chat history."""

    request_id: str
    task_id: str
    goal_id: str
    task_fingerprint: str
    project_binding: str
    candidate_binding: str
    purpose: str
    scope: tuple[str, ...]
    required_capabilities: tuple[str, ...] = ()
    permission_needs: tuple[str, ...] = ()
    granted_permissions: tuple[str, ...] = ()
    context_refs: tuple[str, ...] = ()
    context_materialization_refs: tuple[str, ...] = ()
    acceptance_criteria: tuple[str, ...] = ()
    verification_expectations: tuple[str, ...] = ()
    execution_budget: Mapping[str, Any] = field(default_factory=dict)
    identity_required: bool = False
    expected_environment: str = UNKNOWN
    owner_gate: Mapping[str, Any] | None = None
    created_at: str = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        for field_name, value in (("request_id", self.request_id), ("task_id", self.task_id), ("goal_id", self.goal_id), ("task_fingerprint", self.task_fingerprint), ("project_binding", self.project_binding), ("candidate_binding", self.candidate_binding), ("purpose", self.purpose)):
            _text(value, field_name)
        if len(self.task_fingerprint) != 64 or not re.fullmatch(r"[0-9a-fA-F]{64}", self.task_fingerprint):
            raise HostExecutorContractError("TASK_FINGERPRINT_INVALID")
        if self.expected_environment not in ENVIRONMENTS:
            raise HostExecutorContractError("EXPECTED_ENVIRONMENT_INVALID")
        if not self.scope:
            raise HostExecutorContractError("SCOPE_REQUIRED")
        for field_name, values in (("scope", self.scope), ("required_capabilities", self.required_capabilities), ("permission_needs", self.permission_needs), ("granted_permissions", self.granted_permissions), ("context_refs", self.context_refs), ("context_materialization_refs", self.context_materialization_refs), ("acceptance_criteria", self.acceptance_criteria), ("verification_expectations", self.verification_expectations)):
            if not isinstance(values, tuple) or tuple(values) != _refs(values, field_name):
                raise HostExecutorContractError(f"{field_name}_MUST_BE_UNIQUE_TUPLE")
        if not isinstance(self.execution_budget, Mapping):
            raise HostExecutorContractError("EXECUTION_BUDGET_MUST_BE_OBJECT")
        _safe_json(self.execution_budget, path="execution_budget")
        if self.owner_gate is not None:
            _safe_json(self.owner_gate, path="owner_gate")
        if not isinstance(self.identity_required, bool):
            raise HostExecutorContractError("IDENTITY_REQUIRED_INVALID")
        _text(self.created_at, "created_at", max_length=128)

    @property
    def fingerprint(self) -> str:
        return _canonical_fingerprint(self.to_dict(include_request_id=False, include_created_at=False))

    @property
    def mutation_requested(self) -> bool:
        return bool({"WRITE", "MUTATE", "DELETE"} & set(self.permission_needs))

    def to_dict(self, *, include_request_id: bool = True, include_created_at: bool = True) -> dict[str, Any]:
        result: dict[str, Any] = {
            "schema": PORTABLE_REQUEST_SCHEMA,
            "request_id": self.request_id,
            "task_id": self.task_id,
            "goal_id": self.goal_id,
            "task_fingerprint": self.task_fingerprint,
            "project_binding": self.project_binding,
            "candidate_binding": self.candidate_binding,
            "purpose": self.purpose,
            "scope": list(self.scope),
            "required_capabilities": list(self.required_capabilities),
            "permission_needs": list(self.permission_needs),
            "granted_permissions": list(self.granted_permissions),
            "context_refs": list(self.context_refs),
            "context_materialization_refs": list(self.context_materialization_refs),
            "acceptance_criteria": list(self.acceptance_criteria),
            "verification_expectations": list(self.verification_expectations),
            "execution_budget": _safe_json(self.execution_budget, path="execution_budget"),
            "identity_required": self.identity_required,
            "expected_environment": self.expected_environment,
            "owner_gate": _safe_json(self.owner_gate, path="owner_gate") if self.owner_gate is not None else None,
        }
        if include_request_id:
            result["request_id"] = self.request_id
        else:
            result.pop("request_id", None)
        if include_created_at:
            result["created_at"] = self.created_at
        return result

    @classmethod
    def from_foreground_intent(
        cls,
        intent: Any,
        *,
        request_id: str,
        candidate_binding: str,
        expected_environment: str = UNKNOWN,
        identity_required: bool = False,
    ) -> "PortableExecutionRequest":
        raw = intent.to_dict() if hasattr(intent, "to_dict") else intent
        if not isinstance(raw, Mapping):
            raise HostExecutorContractError("FOREGROUND_INTENT_MUST_BE_OBJECT")
        return cls(
            request_id=request_id,
            task_id=_text(raw.get("task_id"), "task_id"),
            goal_id=_text(raw.get("goal_id"), "goal_id"),
            task_fingerprint=_text(raw.get("plan_hash"), "plan_hash"),
            project_binding=_text(raw.get("project_binding"), "project_binding"),
            candidate_binding=_text(candidate_binding, "candidate_binding"),
            purpose=_text(raw.get("action_name"), "action_name"),
            scope=tuple(raw.get("scope") or ()),
            required_capabilities=tuple(raw.get("required_capabilities") or ()),
            permission_needs=tuple(raw.get("permission_needs") or ()),
            context_refs=tuple(raw.get("context_refs") or ()),
            acceptance_criteria=tuple(raw.get("acceptance_requirements") or ()),
            verification_expectations=tuple(raw.get("required_evidence") or ()),
            execution_budget=raw.get("budget") or {},
            identity_required=identity_required,
            expected_environment=expected_environment,
            owner_gate=raw.get("owner_gate"),
            created_at=raw.get("created_at", utc_now()),
        )

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "PortableExecutionRequest":
        if not isinstance(value, Mapping) or value.get("schema") != PORTABLE_REQUEST_SCHEMA:
            raise HostExecutorContractError("PORTABLE_REQUEST_SCHEMA_INVALID")
        return cls(
            request_id=_text(value.get("request_id"), "request_id"),
            task_id=_text(value.get("task_id"), "task_id"),
            goal_id=_text(value.get("goal_id"), "goal_id"),
            task_fingerprint=_text(value.get("task_fingerprint"), "task_fingerprint"),
            project_binding=_text(value.get("project_binding"), "project_binding"),
            candidate_binding=_text(value.get("candidate_binding"), "candidate_binding"),
            purpose=_text(value.get("purpose"), "purpose"),
            scope=tuple(value.get("scope") or ()),
            required_capabilities=tuple(value.get("required_capabilities") or ()),
            permission_needs=tuple(value.get("permission_needs") or ()),
            granted_permissions=tuple(value.get("granted_permissions") or ()),
            context_refs=tuple(value.get("context_refs") or ()),
            context_materialization_refs=tuple(value.get("context_materialization_refs") or ()),
            acceptance_criteria=tuple(value.get("acceptance_criteria") or ()),
            verification_expectations=tuple(value.get("verification_expectations") or ()),
            execution_budget=value.get("execution_budget") or {},
            identity_required=value.get("identity_required", False),
            expected_environment=value.get("expected_environment", UNKNOWN),
            owner_gate=value.get("owner_gate"),
            created_at=value.get("created_at", utc_now()),
        )


@dataclass(frozen=True)
class PortableExecutionReceipt:
    """Normalized proposal/evidence; it never self-authorizes task completion."""

    request_id: str
    request_fingerprint: str
    task_id: str
    host_adapter_class: str
    execution_status: str
    verification_status: str = UNKNOWN
    authoritative_execution_id: str | None = None
    host_label: str | None = None
    provider: str | None = None
    model: str | None = None
    artifact_refs: tuple[str, ...] = ()
    commands: tuple[str, ...] = ()
    proposed_facts: Mapping[str, Any] = field(default_factory=dict)
    evidence_refs: tuple[str, ...] = ()
    unresolved_facts: tuple[str, ...] = ()
    risks: tuple[str, ...] = ()
    telemetry: Mapping[str, Any] = field(default_factory=dict)
    error_class: str | None = None
    possible_mutation: bool = False
    received_at: str = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        for field_name, value in (("request_id", self.request_id), ("request_fingerprint", self.request_fingerprint), ("task_id", self.task_id), ("host_adapter_class", self.host_adapter_class)):
            _text(value, field_name)
        if len(self.request_fingerprint) != 64 or not re.fullmatch(r"[0-9a-fA-F]{64}", self.request_fingerprint):
            raise HostExecutorContractError("REQUEST_FINGERPRINT_INVALID")
        if self.execution_status not in _EXECUTION_STATUSES:
            raise HostExecutorContractError("EXECUTION_STATUS_INVALID")
        if self.verification_status not in _VERIFICATION_STATUSES:
            raise HostExecutorContractError("VERIFICATION_STATUS_INVALID")
        if self.authoritative_execution_id is not None:
            _text(self.authoritative_execution_id, "authoritative_execution_id", max_length=256)
        for field_name, value in (("host_label", self.host_label), ("provider", self.provider), ("model", self.model)):
            if value is not None:
                _text(value, field_name, max_length=256)
        for field_name, values in (("artifact_refs", self.artifact_refs), ("commands", self.commands), ("evidence_refs", self.evidence_refs), ("unresolved_facts", self.unresolved_facts), ("risks", self.risks)):
            if not isinstance(values, tuple) or tuple(values) != _refs(values, field_name):
                raise HostExecutorContractError(f"{field_name}_MUST_BE_UNIQUE_TUPLE")
        _safe_json(self.proposed_facts, path="proposed_facts")
        _safe_json(self.telemetry, path="telemetry")
        if self.error_class is not None and self.error_class not in ERROR_CLASSES:
            raise HostExecutorContractError("ERROR_CLASS_INVALID")
        if not isinstance(self.possible_mutation, bool):
            raise HostExecutorContractError("POSSIBLE_MUTATION_INVALID")
        _text(self.received_at, "received_at", max_length=128)

    @property
    def completion_status(self) -> str:
        if self.execution_status == "SUCCEEDED" and self.verification_status == "VERIFIED":
            return "DONE"
        if self.execution_status == "BLOCKED":
            return "BLOCKED"
        if self.execution_status == "PARTIAL_MUTATION_UNKNOWN" or (self.possible_mutation and self.execution_status == "UNKNOWN"):
            return "NEEDS_RECHECK"
        return "NOT_DONE"

    @property
    def telemetry_status(self) -> str:
        return SUPPORTED if self.telemetry else UNKNOWN

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": PORTABLE_RECEIPT_SCHEMA,
            "request_id": self.request_id,
            "request_fingerprint": self.request_fingerprint,
            "task_id": self.task_id,
            "host_adapter_class": self.host_adapter_class,
            "host_label": self.host_label,
            "authoritative_execution_id": self.authoritative_execution_id,
            "provider": self.provider,
            "model": self.model,
            "execution_status": self.execution_status,
            "verification_status": self.verification_status,
            "completion_status": self.completion_status,
            "artifact_refs": list(self.artifact_refs),
            "commands": list(self.commands),
            "proposed_facts": _safe_json(self.proposed_facts, path="proposed_facts"),
            "evidence_refs": list(self.evidence_refs),
            "unresolved_facts": list(self.unresolved_facts),
            "risks": list(self.risks),
            "telemetry": _safe_json(self.telemetry, path="telemetry"),
            "telemetry_status": self.telemetry_status,
            "error_class": self.error_class,
            "possible_mutation": self.possible_mutation,
            "received_at": self.received_at,
        }

    @classmethod
    def from_host_result(cls, request: PortableExecutionRequest, profile: HostCapabilityProfile, host_result: Mapping[str, Any]) -> "PortableExecutionReceipt":
        if not isinstance(host_result, Mapping):
            raise HostExecutorContractError("HOST_RESULT_MUST_BE_OBJECT")
        raw_status = str(host_result.get("status", "UNKNOWN")).upper()
        execution_status = {
            "DONE": "SUCCEEDED",
            "SUCCEEDED": "SUCCEEDED",
            "SUCCESS": "SUCCEEDED",
            "FAILED": "FAILED",
            "BLOCKED": "BLOCKED",
            "INTERRUPTED": "INTERRUPTED",
            "CANCELLED": "CANCELLED",
            "UNKNOWN": "UNKNOWN",
        }.get(raw_status, "UNKNOWN")
        message = str(host_result.get("error") or host_result.get("message") or "")
        error_class = normalize_host_error(message) if message else None
        if error_class == "PARTIAL_MUTATION_UNKNOWN":
            execution_status = "PARTIAL_MUTATION_UNKNOWN"
        elif execution_status == "UNKNOWN" and error_class == "HOST_UNAVAILABLE":
            execution_status = "FAILED"
        authoritative_id = host_result.get("authoritative_execution_id")
        verification_status = str(host_result.get("verification_status", UNKNOWN)).upper()
        if verification_status not in _VERIFICATION_STATUSES:
            verification_status = UNKNOWN
        return cls(
            request_id=request.request_id,
            request_fingerprint=request.fingerprint,
            task_id=request.task_id,
            host_adapter_class=profile.adapter_class,
            host_label=profile.host_label,
            provider=host_result.get("provider") if isinstance(host_result.get("provider"), str) else profile.provider,
            model=host_result.get("model") if isinstance(host_result.get("model"), str) else profile.model,
            authoritative_execution_id=authoritative_id if isinstance(authoritative_id, str) else None,
            execution_status=execution_status,
            verification_status=verification_status,
            artifact_refs=tuple(host_result.get("artifact_refs") or ()),
            commands=tuple(host_result.get("commands") or ()),
            proposed_facts=host_result.get("proposed_facts") or {},
            evidence_refs=tuple(host_result.get("evidence_refs") or ()),
            unresolved_facts=tuple(host_result.get("unresolved_facts") or ()),
            risks=tuple(host_result.get("risks") or ()),
            telemetry=host_result.get("telemetry") or {},
            error_class=error_class,
            possible_mutation=bool(host_result.get("possible_mutation", False)),
        )


@dataclass(frozen=True)
class PortableHandoff:
    """Human-mediated or future-programmatic continuation package."""

    request: PortableExecutionRequest
    checkpoint_ref: str
    next_step: str
    verification_required: tuple[str, ...]
    unfinished_safe_work: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _text(self.checkpoint_ref, "checkpoint_ref")
        _text(self.next_step, "next_step")
        for field_name, values in (("verification_required", self.verification_required), ("unfinished_safe_work", self.unfinished_safe_work)):
            if not isinstance(values, tuple) or tuple(values) != _refs(values, field_name):
                raise HostExecutorContractError(f"{field_name}_MUST_BE_UNIQUE_TUPLE")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": PORTABLE_HANDOFF_SCHEMA,
            "request": self.request.to_dict(),
            "request_fingerprint": self.request.fingerprint,
            "project_binding": self.request.project_binding,
            "candidate_binding": self.request.candidate_binding,
            "checkpoint_ref": self.checkpoint_ref,
            "next_step": self.next_step,
            "verification_required": list(self.verification_required),
            "unfinished_safe_work": list(self.unfinished_safe_work),
            "chat_history_required": False,
            "host_required": False,
        }


def evaluate_host_preflight(
    profile: HostCapabilityProfile,
    request: PortableExecutionRequest,
    *,
    parent_permission_grants: Iterable[str] | None = None,
) -> dict[str, Any]:
    if parent_permission_grants is not None:
        parent_grants = getattr(parent_permission_grants, "grants", parent_permission_grants)
        if not set(request.granted_permissions).issubset(set(parent_grants)):
            return {
            "status": "BLOCKED",
            "reason": "PERMISSION_BLOCKED",
            "permission_granted": False,
                "permission_source": "PARENT_ENVELOPE",
            }
    missing = [
        {"capability": name, "state": profile.state(name)}
        for name in request.required_capabilities
        if not profile.supports(name)
    ]
    if missing:
        return {"status": "BLOCKED", "reason": "CAPABILITY_UNAVAILABLE", "missing_capabilities": missing, "permission_granted": False}
    missing_permissions = sorted(set(request.permission_needs) - set(request.granted_permissions))
    if missing_permissions:
        return {"status": "BLOCKED", "reason": "PERMISSION_BLOCKED", "missing_permissions": missing_permissions, "permission_granted": False}
    if request.expected_environment != UNKNOWN and profile.environment != request.expected_environment:
        return {"status": "BLOCKED", "reason": "RECONCILIATION_REQUIRED", "expected_environment": request.expected_environment, "actual_environment": profile.environment, "permission_granted": True}
    if request.identity_required and profile.state("can_return_authoritative_execution_id") != SUPPORTED:
        return {"status": "BLOCKED", "reason": "IDENTITY_EVIDENCE_UNAVAILABLE", "identity_state": profile.state("can_return_authoritative_execution_id"), "permission_granted": True}
    return {"status": "READY", "reason": "HOST_CAPABILITY_MATCH", "missing_capabilities": [], "missing_permissions": [], "permission_granted": True}


def normalize_host_error(value: Any) -> str:
    text = str(value or "").strip().lower()
    ordered = (
        ("stale context", "STALE_CONTEXT"),
        ("identity", "IDENTITY_EVIDENCE_UNAVAILABLE"),
        ("partial", "PARTIAL_MUTATION_UNKNOWN"),
        ("permission", "PERMISSION_BLOCKED"),
        ("owner", "OWNER_ACTION_REQUIRED"),
        ("capability", "CAPABILITY_UNAVAILABLE"),
        ("control", "CONTROL_PLANE_FAILURE"),
        ("unavailable", "HOST_UNAVAILABLE"),
        ("timeout", "TIMEOUT"),
        ("cancel", "CANCELLED"),
        ("interrupt", "EXECUTION_INTERRUPTED"),
        ("stale", "STALE_REQUEST"),
        ("unknown", "RESULT_UNKNOWN"),
    )
    for marker, error_class in ordered:
        if marker in text:
            return error_class
    return "EXECUTION_FAILED"


def build_portable_handoff(request: PortableExecutionRequest, *, checkpoint_ref: str, next_step: str, verification_required: Sequence[str], unfinished_safe_work: Sequence[str] = ()) -> PortableHandoff:
    return PortableHandoff(
        request=request,
        checkpoint_ref=checkpoint_ref,
        next_step=next_step,
        verification_required=tuple(verification_required),
        unfinished_safe_work=tuple(unfinished_safe_work),
    )


def reconcile_receipt(receipt: PortableExecutionReceipt, *, current_project_binding: str, current_candidate_binding: str) -> dict[str, Any]:
    if receipt.request_fingerprint.strip() == "":
        raise HostExecutorContractError("REQUEST_FINGERPRINT_REQUIRED")
    if not current_project_binding or not current_candidate_binding:
        raise HostExecutorContractError("CURRENT_BINDING_REQUIRED")
    # The caller must compare the request binding before accepting a receipt.
    if receipt.completion_status == "DONE":
        return {"status": "DONE", "retry_allowed": False, "verification_required": False}
    if receipt.error_class == "HOST_UNAVAILABLE" and not receipt.possible_mutation:
        return {"status": "RECOVERABLE_HOST_FAILURE", "retry_allowed": True, "verification_required": False}
    if receipt.completion_status == "NEEDS_RECHECK":
        return {"status": "NEEDS_RECHECK", "retry_allowed": False, "verification_required": True, "reason": "PARTIAL_MUTATION_UNKNOWN"}
    return {"status": "NOT_DONE", "retry_allowed": False, "verification_required": True}


def validate_binding(*, request: PortableExecutionRequest, current_project_binding: str, current_candidate_binding: str) -> dict[str, Any]:
    if request.project_binding != current_project_binding or request.candidate_binding != current_candidate_binding:
        return {"status": "BLOCKED", "reason": "STALE_REQUEST", "retry_allowed": False}
    return {"status": "BOUND", "reason": "PROJECT_AND_CANDIDATE_MATCH", "retry_allowed": True}


def import_artifact(receipt: PortableExecutionReceipt, *, current_candidate_binding: str, artifact_candidate_binding: str) -> dict[str, Any]:
    if artifact_candidate_binding != current_candidate_binding:
        return {"status": "BLOCKED", "reason": "STALE_REQUEST", "reconciliation_required": True}
    return {"status": "ACCEPTABLE_PROPOSAL", "requires_verification": True}


def select_compatible_executor(profiles: Sequence[HostCapabilityProfile], request: PortableExecutionRequest) -> dict[str, Any]:
    compatible = [profile for profile in profiles if evaluate_host_preflight(profile, request)["status"] == "READY"]
    if len(compatible) == 1:
        return {"status": "ONE_COMPATIBLE_HOST", "selected": compatible[0].to_dict(), "called_hosts": 0}
    if len(compatible) > 1:
        return {"status": "MULTIPLE_HOSTS_AVAILABLE", "selected": None, "called_hosts": 0, "future_resolver_seam": True}
    return {"status": "NO_COMPATIBLE_HOST", "selected": None, "called_hosts": 0}


def beginner_handoff_instruction() -> str:
    return "Open another compatible AI with this project and continue."


def governance_projection(canonical_identities: Sequence[str]) -> dict[str, Any]:
    identities = tuple(canonical_identities)
    if len(identities) != 8 or len(set(identities)) != 8:
        raise HostExecutorContractError("CANONICAL_GOVERNANCE_INVALID")
    return {"canonical_count": 8, "denominator": 8, "full_quorum": "8/8", "host_is_not_agent": True}


__all__ = [
    "CAPABILITY_DIMENSIONS",
    "CAPABILITY_STATES",
    "ERROR_CLASSES",
    "ENVIRONMENTS",
    "SUPPORTED",
    "UNSUPPORTED",
    "UNKNOWN",
    "HostCapabilityProfile",
    "HostExecutorContractError",
    "PortableExecutionRequest",
    "PortableExecutionReceipt",
    "PortableHandoff",
    "beginner_handoff_instruction",
    "build_portable_handoff",
    "evaluate_host_preflight",
    "governance_projection",
    "import_artifact",
    "normalize_host_error",
    "reconcile_receipt",
    "select_compatible_executor",
    "validate_binding",
]
