"""Bounded foreground delegation over the C11/C12 foundations.

This module is deliberately an additive adapter.  ``TaskStateStore`` remains
the durable task owner, ``ForegroundExecutionController`` remains the direct
executor, and C10 evidence remains the only completion authority.  The module
adds one deterministic strategy decision and one narrow, foreground child
handoff.  It never resolves a model/profile, starts background work, creates a
second ledger, or treats a child result as evidence.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
import fnmatch
import hashlib
import inspect
import json
import math
from pathlib import Path
import re
import time
from typing import Any, Callable, Iterable, Mapping, Sequence
import uuid

from .evidence import EvidenceClaim
from .decision_trace import DecisionTraceError, append_trace, make_trace
from .foreground_execution import ForegroundExecutionController, ForegroundExecutionError
from .task_state import (
    TaskPlan,
    TaskRecord,
    TaskStateError,
    TaskStateStore,
    next_safe_task,
    utc_now,
)
from scripts.p2p_host_identity_hook import read_receipts, validate_receipt as validate_host_identity_receipt


DELEGATION_SCHEMA = "p2p-bounded-delegation/1"
HANDOFF_SCHEMA = "p2p-worker-handoff/1"
CHILD_RESULT_SCHEMA = "p2p-worker-result/1"
DELEGATION_RESULT_SCHEMA = "p2p-bounded-delegation-result/1"
DELEGATION_STATE_RELATIVE_ROOT = ".p2p/state/foreground-executions/delegations"
MAX_DELEGATION_DEPTH = 1
MAX_DELEGATED_CHILDREN = 1
UNKNOWN_IDENTITY = "UNKNOWN"
HOST_DEFAULT_EXECUTION_CLASS = "HOST_DEFAULT"
HOST_EXECUTION_SOURCE = "codex_official_host"
HOST_ADAPTER_SCHEMA = "p2p-c15-host-adapter/1"
RAW_HOST_RECEIPT_KEY = "RAW_HOST_RECEIPT"
NORMALIZED_C15_RECEIPT_KEY = "NORMALIZED_C15_RECEIPT"

DIRECT = "DIRECT"
DELEGATE = "DELEGATE"
BLOCKED = "BLOCKED"

VALUE_REASONS = (
    "SPECIALIST_ANALYSIS",
    "CONTEXT_ISOLATION",
    "INDEPENDENT_REVIEW",
    "EXPENSIVE_REASONING",
    "OWNER_CONTROL_SEPARATION",
)
TASK_SIZES = ("TINY", "SMALL", "MODERATE", "LARGE")
CHILD_OUTCOMES = ("SUCCEEDED", "FAILED", "INTERRUPTED", "BLOCKED", "UNKNOWN")
MUTATION_STATES = ("KNOWN_NONE", "KNOWN_COMPLETE", "UNKNOWN")
BOUNDARY_FAILURE_MARKERS = (
    "PERMISSION",
    "OWNER",
    "SCOPE",
    "STALE",
    "UNSUPPORTED",
    "IDENTITY",
    "CONTROL_PLANE",
    "CONTROL-PLANE",
    "HANDOFF",
    "SPAWN",
)

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_ID_RE = re.compile(r"^[a-z][a-z0-9-]{1,127}$")
_HANDOFF_ID_RE = re.compile(r"^handoff-[a-f0-9]{16,64}$")
_SECRET_KEY_RE = re.compile(
    r"(?:secret|token|password|credential|api[_-]?key|private[_-]?key|authorization|environment)",
    re.IGNORECASE,
)
_SECRET_VALUE_RE = re.compile(
    r"(?:api[_-]?key|password|token|secret|authorization)\s*[:=]\s*\S+|\bsk-[a-z0-9_-]{16,}\b",
    re.IGNORECASE,
)
_IDENTITY_KEYS = {
    "agent",
    "agent_id",
    "agent_profile",
    "model",
    "model_id",
    "provider",
    "thread",
    "thread_id",
    "worker",
    "worker_id",
    "worker_profile",
    "child_agents",
    "delegated_children",
}
_STRUCTURAL_SAFE_KEYS = {
    "allow_secret_access",
    "allow_mutation",
    "allow_network",
    "allow_egress",
    "allow_delete",
    "allow_release",
    "allow_deploy",
}
_PROTECTED_PREFIXES = (
    ".git",
    ".p2p/install-backups",
    "source/8.4.6-c",
    "source/v5",
    "v5",
    "release",
)


class BoundedDelegationError(ValueError):
    """Base error for an invalid or unsafe delegation contract."""


class DelegationContractError(BoundedDelegationError):
    """Raised when a request, handoff, or child result is malformed."""


class DelegationScopeError(BoundedDelegationError):
    """Raised when a child scope or artifact leaves the parent scope."""


class DelegationPermissionError(BoundedDelegationError):
    """Raised when the child permission envelope is not a subset."""


class DelegationControlPlaneError(BoundedDelegationError):
    """Raised when task state, handoff, or result binding is not trustworthy."""


class DelegationStaleError(BoundedDelegationError):
    """Raised when a handoff no longer matches the current task contract."""


def _safe_json(value: Any, *, path: str = "value", depth: int = 0) -> Any:
    """Return bounded JSON data without secrets or identity coupling."""

    if depth > 8:
        raise DelegationContractError(f"{path}_TOO_DEEP")
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for key, child in value.items():
            key_text = str(key)
            lowered = key_text.lower()
            if _SECRET_KEY_RE.search(key_text) and lowered not in _STRUCTURAL_SAFE_KEYS:
                raise DelegationContractError(f"{path}.{key_text}_SECRET_FIELD")
            if lowered == "delegated_children" and child == 0:
                result[key_text] = 0
                continue
            if lowered == RAW_HOST_RECEIPT_KEY.lower():
                result[key_text] = None if child is None else _safe_host_receipt(child, path=f"{path}.{key_text}")
                continue
            if lowered == NORMALIZED_C15_RECEIPT_KEY.lower():
                result[key_text] = None if child is None else _safe_host_receipt(child, path=f"{path}.{key_text}", normalized=True)
                continue
            if lowered in _IDENTITY_KEYS:
                raise DelegationContractError(f"{path}.{key_text}_IDENTITY_FORBIDDEN")
            result[key_text] = _safe_json(child, path=f"{path}.{key_text}", depth=depth + 1)
        return result
    if isinstance(value, (list, tuple)):
        if len(value) > 128:
            raise DelegationContractError(f"{path}_TOO_LARGE")
        return [_safe_json(item, path=f"{path}[{index}]", depth=depth + 1) for index, item in enumerate(value)]
    if isinstance(value, str):
        if len(value) > 8192:
            raise DelegationContractError(f"{path}_TOO_LARGE")
        if _SECRET_VALUE_RE.search(value):
            raise DelegationContractError(f"{path}_SECRET_LIKE")
        return value
    if isinstance(value, float) and not math.isfinite(value):
        raise DelegationContractError(f"{path}_NON_FINITE")
    if value is None or isinstance(value, (bool, int, float)):
        return value
    raise DelegationContractError(f"{path}_TYPE_INVALID")


def _safe_host_receipt(value: Any, *, path: str, normalized: bool = False) -> dict[str, Any]:
    """Validate the allow-listed host receipt without weakening result safety."""

    if not isinstance(value, Mapping):
        raise DelegationControlPlaneError(f"{path}_MUST_BE_OBJECT")
    if not normalized and (not validate_host_identity_receipt(value) or set(value) != {
        "schema", "event", "timestamp", "session_id", "turn_id", "agent_id", "agent_type",
        "permission_mode", "model", "cwd", "source",
    }):
        raise DelegationControlPlaneError(f"{path}_INVALID")
    allowed = {
        "schema", "adapter_schema", "event", "timestamp", "session_id", "turn_id", "agent_id",
        "agent_type", "permission_mode", "model", "cwd", "source", "handoff_id", "task_id",
        "host_execution_id", "status", "execution_source", "identity_authority", "output_is_evidence",
        "plan_hash",
    }
    if set(value) - allowed:
        raise DelegationControlPlaneError(f"{path}_FIELDS_INVALID")
    result: dict[str, Any] = {}
    for key, child in value.items():
        if isinstance(child, str):
            if len(child) > 4096 or _SECRET_VALUE_RE.search(child):
                raise DelegationControlPlaneError(f"{path}.{key}_INVALID")
            result[str(key)] = child
        elif isinstance(child, bool) and key == "output_is_evidence":
            result[str(key)] = child
        else:
            raise DelegationControlPlaneError(f"{path}.{key}_INVALID")
    return result


def _refs(values: Iterable[Any] | None, field_name: str, *, required: bool = False) -> tuple[str, ...]:
    if values is None:
        values = ()
    if isinstance(values, str):
        raise DelegationContractError(f"{field_name}_MUST_BE_LIST")
    result: list[str] = []
    seen: set[str] = set()
    try:
        iterator = iter(values)
    except TypeError as exc:
        raise DelegationContractError(f"{field_name}_MUST_BE_LIST") from exc
    for value in iterator:
        if not isinstance(value, str) or not value.strip() or len(value) > 1024:
            raise DelegationContractError(f"{field_name}_ITEM_INVALID")
        item = value.strip().replace("\\", "/")
        if item in seen:
            raise DelegationContractError(f"{field_name}_DUPLICATE:{item}")
        seen.add(item)
        result.append(item)
    if required and not result:
        raise DelegationContractError(f"{field_name}_REQUIRED")
    return tuple(result)


def _sha256(value: Any) -> str:
    try:
        payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise DelegationContractError("JSON_VALUE_NOT_SERIALIZABLE") from exc
    return hashlib.sha256(payload).hexdigest()


def _assert_sha256(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not _SHA256_RE.fullmatch(value.lower()):
        raise DelegationContractError(f"{field_name}_SHA256_REQUIRED")
    return value.lower()


def _status(value: Any) -> str:
    return str(value or "").strip().upper()


def _now() -> str:
    return utc_now()


def _new_handoff_id() -> str:
    return f"handoff-{uuid.uuid4().hex}"


def _path_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > 1024:
        raise DelegationContractError(f"{field_name}_INVALID")
    normalized = value.strip().replace("\\", "/")
    if normalized.startswith("/") or re.match(r"^[a-zA-Z]:", normalized):
        raise DelegationScopeError(f"{field_name}_MUST_BE_PROJECT_RELATIVE")
    if any(part in {"", ".", ".."} for part in Path(normalized).parts):
        raise DelegationScopeError(f"{field_name}_PATH_INVALID")
    if normalized.startswith(_PROTECTED_PREFIXES):
        raise DelegationScopeError(f"{field_name}_PROTECTED")
    return normalized


def _scope_match(child: str, parent: str) -> bool:
    child_text = child.replace("\\", "/")
    parent_text = parent.replace("\\", "/")
    if child_text == parent_text:
        return True
    if any(token in child_text for token in ("*", "?", "[")):
        return False
    return fnmatch.fnmatchcase(child_text, parent_text)


def scope_is_subset(child_scope: Iterable[str], parent_scope: Iterable[str], non_scope: Iterable[str] = ()) -> bool:
    """Prove an explicit child path list is contained by the parent scope."""

    child = tuple(_path_text(item, "child_scope") for item in child_scope)
    parent = tuple(_path_text(item, "parent_scope") for item in parent_scope)
    excluded = tuple(str(item).replace("\\", "/") for item in non_scope)
    if not child or not parent:
        return False
    for item in child:
        if not any(_scope_match(item, allowed) for allowed in parent):
            return False
        if any(fnmatch.fnmatchcase(item, blocked) for blocked in excluded):
            return False
    return True


def _invoke(callback: Callable[..., Any], first: Any, second: Any = None, *, allow_second: bool = False) -> Any:
    """Call an injected host/verifier surface without adding an executor."""

    try:
        signature = inspect.signature(callback)
        positional = [
            parameter
            for parameter in signature.parameters.values()
            if parameter.kind in {parameter.POSITIONAL_ONLY, parameter.POSITIONAL_OR_KEYWORD}
        ]
        accepts_varargs = any(parameter.kind == parameter.VAR_POSITIONAL for parameter in signature.parameters.values())
    except (TypeError, ValueError):
        positional = [None, None]
        accepts_varargs = True
    if allow_second and (accepts_varargs or len(positional) >= 2):
        return callback(first, second)
    return callback(first)


@dataclass(frozen=True)
class PermissionEnvelope:
    """Explicit parent/child authority with structural no-delegation."""

    grants: tuple[str, ...] = ()
    scope: tuple[str, ...] = ()
    delegate_allowed: bool = False

    def __post_init__(self) -> None:
        normalized = tuple(sorted({str(item).strip().upper() for item in self.grants if str(item).strip()}))
        if normalized != tuple(self.grants):
            raise DelegationContractError("PERMISSION_GRANTS_MUST_BE_UNIQUE_UPPERCASE")
        normalized_scope = _refs(self.scope, "permission.scope")
        if tuple(self.scope) != normalized_scope:
            raise DelegationContractError("PERMISSION_SCOPE_MUST_BE_UNIQUE_AND_ORDERED")
        if self.delegate_allowed:
            raise DelegationPermissionError("CHILD_DELEGATE_MUST_BE_FALSE")

    @classmethod
    def from_value(cls, value: Any, *, default_scope: Iterable[str] = ()) -> "PermissionEnvelope":
        if value is None:
            return cls(scope=_refs(default_scope, "permission.default_scope"))
        if isinstance(value, cls):
            if value.scope:
                return value
            return replace(value, scope=_refs(default_scope, "permission.default_scope"))
        if not isinstance(value, Mapping):
            raise DelegationContractError("PERMISSION_ENVELOPE_MUST_BE_OBJECT")
        raw_grants = value.get("grants", value.get("permissions", value.get("permission_names", ())))
        if isinstance(raw_grants, str):
            raw_grants = (raw_grants,)
        grants = {str(item).strip().upper() for item in (raw_grants or ()) if str(item).strip()}
        aliases = {
            "allow_mutation": "WRITE",
            "allow_network": "NETWORK",
            "allow_egress": "EGRESS",
            "allow_secret_access": "SECRET_ACCESS",
            "allow_delete": "DELETE",
            "allow_release": "RELEASE",
            "allow_deploy": "DEPLOY",
        }
        for key, grant in aliases.items():
            if value.get(key) is True:
                grants.add(grant)
        if value.get("allow_delegate") is True or value.get("delegate_allowed") is True:
            raise DelegationPermissionError("CHILD_DELEGATE_MUST_BE_FALSE")
        return cls(
            grants=tuple(sorted(grants)),
            scope=_refs(value.get("scope", default_scope), "permission.scope"),
            delegate_allowed=False,
        )

    @property
    def allow_mutation(self) -> bool:
        return bool({"WRITE", "MUTATE", "DELETE"} & set(self.grants))

    @property
    def allow_network(self) -> bool:
        return bool({"NETWORK", "EGRESS"} & set(self.grants))

    @property
    def allow_secret_access(self) -> bool:
        return "SECRET_ACCESS" in self.grants

    def subset_of(self, parent: "PermissionEnvelope", *, parent_scope: Iterable[str] = (), non_scope: Iterable[str] = ()) -> bool:
        if not isinstance(parent, PermissionEnvelope):
            return False
        if self.delegate_allowed:
            return False
        if not set(self.grants).issubset(set(parent.grants)):
            return False
        allowed_scope = tuple(parent.scope) or tuple(parent_scope)
        return scope_is_subset(self.scope, allowed_scope, non_scope)

    def to_dict(self) -> dict[str, Any]:
        return {
            "grants": list(self.grants),
            "scope": list(self.scope),
            "allow_mutation": self.allow_mutation,
            "allow_network": self.allow_network,
            "allow_secret_access": self.allow_secret_access,
            "delegation_allowed": False,
        }


@dataclass(frozen=True)
class DelegationBudget:
    """Finite child limits; C15 structurally allows one child at depth one."""

    max_attempts: int = 1
    max_retries: int = 0
    max_actions: int = 8
    max_wall_clock_seconds: float = 60.0
    max_output_bytes: int = 8192
    allow_mutation: bool = False
    allow_network: bool = False
    max_children: int = MAX_DELEGATED_CHILDREN
    max_depth: int = MAX_DELEGATION_DEPTH
    child_delegation_allowed: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.max_attempts, int) or self.max_attempts < 1 or self.max_attempts > 8:
            raise DelegationContractError("BUDGET_MAX_ATTEMPTS_INVALID")
        if not isinstance(self.max_retries, int) or self.max_retries < 0 or self.max_retries >= self.max_attempts:
            raise DelegationContractError("BUDGET_MAX_RETRIES_INVALID")
        if not isinstance(self.max_actions, int) or self.max_actions < 1 or self.max_actions > 128:
            raise DelegationContractError("BUDGET_MAX_ACTIONS_INVALID")
        if not isinstance(self.max_wall_clock_seconds, (int, float)) or not math.isfinite(float(self.max_wall_clock_seconds)) or self.max_wall_clock_seconds <= 0 or self.max_wall_clock_seconds > 3600:
            raise DelegationContractError("BUDGET_WALL_CLOCK_INVALID")
        if not isinstance(self.max_output_bytes, int) or self.max_output_bytes < 256 or self.max_output_bytes > 1_048_576:
            raise DelegationContractError("BUDGET_OUTPUT_INVALID")
        if self.allow_network:
            raise DelegationPermissionError("C15_NETWORK_UNSUPPORTED")
        if self.max_children != MAX_DELEGATED_CHILDREN:
            raise DelegationContractError("C15_MAX_CHILDREN_MUST_BE_ONE")
        if self.max_depth != MAX_DELEGATION_DEPTH:
            raise DelegationContractError("C15_MAX_DEPTH_MUST_BE_ONE")
        if self.child_delegation_allowed:
            raise DelegationPermissionError("CHILD_DELEGATE_MUST_BE_FALSE")

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_attempts": self.max_attempts,
            "max_retries": self.max_retries,
            "max_actions": self.max_actions,
            "max_wall_clock_seconds": float(self.max_wall_clock_seconds),
            "max_output_bytes": self.max_output_bytes,
            "allow_mutation": self.allow_mutation,
            "allow_network": False,
            "max_children": MAX_DELEGATED_CHILDREN,
            "max_depth": MAX_DELEGATION_DEPTH,
            "child_delegation_allowed": False,
        }

    def to_foreground_budget(self) -> Any:
        """Reuse C12's finite direct budget for an explicitly safe fallback."""

        from .foreground_execution import ExecutionBudget

        return ExecutionBudget(
            max_attempts=self.max_attempts,
            max_retries=self.max_retries,
            max_tool_actions=self.max_actions,
            max_wall_clock_seconds=self.max_wall_clock_seconds,
            max_output_bytes=self.max_output_bytes,
            allow_mutation=self.allow_mutation,
            allow_network=False,
            max_delegated_children=0,
        )


@dataclass(frozen=True)
class DelegationRequest:
    """Validated policy input; no model/profile selection is present."""

    task: TaskRecord
    task_size: str = "MODERATE"
    value_reasons: tuple[str, ...] = ()
    parent_permissions: PermissionEnvelope = field(default_factory=PermissionEnvelope)
    child_permissions: PermissionEnvelope | None = None
    child_scope: tuple[str, ...] = ()
    read_scopes: tuple[str, ...] = ()
    write_scopes: tuple[str, ...] = ()
    delete_scopes: tuple[str, ...] = ()
    shared_resources: tuple[str, ...] = ()
    candidate_state: Any = None
    candidate_fingerprint: str | None = None
    project_binding: str = "PROJECT_ROOT_BOUND"
    context_state: Mapping[str, Mapping[str, Any]] = field(default_factory=dict)
    relevant_context: Mapping[str, Mapping[str, Any]] = field(default_factory=dict)
    capability_readiness: Mapping[str, Mapping[str, Any]] = field(default_factory=dict)
    permission_state: Mapping[str, Mapping[str, Any]] = field(default_factory=dict)
    dependency_outcomes: tuple[Mapping[str, Any], ...] = ()
    relevant_decisions: tuple[str, ...] = ()
    known_risks: tuple[str, ...] = ()
    unknowns: tuple[str, ...] = ()
    requested_execution_class: str = HOST_DEFAULT_EXECUTION_CLASS
    identity_required: bool = False
    required_identity: str | None = None
    observed_identity: str = UNKNOWN_IDENTITY
    identity_authority: str = "UNKNOWN"
    host_child_available: bool = False
    owner_gate: Mapping[str, Any] | None = None
    allow_direct_fallback: bool = False
    budget: DelegationBudget = field(default_factory=DelegationBudget)

    def __post_init__(self) -> None:
        if not isinstance(self.task, TaskRecord):
            raise DelegationContractError("TASK_RECORD_REQUIRED")
        if self.task_size not in TASK_SIZES:
            raise DelegationContractError("TASK_SIZE_INVALID")
        reasons = tuple(str(item).strip().upper() for item in self.value_reasons if str(item).strip())
        if tuple(sorted(set(reasons))) != tuple(sorted(reasons)) or len(set(reasons)) != len(reasons):
            raise DelegationContractError("VALUE_REASONS_MUST_BE_UNIQUE")
        if any(item not in VALUE_REASONS for item in reasons):
            raise DelegationContractError("VALUE_REASON_UNSUPPORTED")
        object.__setattr__(self, "value_reasons", reasons)
        if not isinstance(self.parent_permissions, PermissionEnvelope):
            object.__setattr__(self, "parent_permissions", PermissionEnvelope.from_value(self.parent_permissions, default_scope=self.task.scope))
        child_scope = _refs(self.child_scope or self.task.scope, "child_scope", required=True)
        object.__setattr__(self, "child_scope", child_scope)
        object.__setattr__(self, "read_scopes", _refs(self.read_scopes, "read_scopes"))
        object.__setattr__(self, "write_scopes", _refs(self.write_scopes, "write_scopes"))
        object.__setattr__(self, "delete_scopes", _refs(self.delete_scopes, "delete_scopes"))
        object.__setattr__(self, "shared_resources", _refs(self.shared_resources, "shared_resources"))
        if self.child_permissions is None:
            child = PermissionEnvelope(grants=self.parent_permissions.grants, scope=child_scope)
        else:
            child = PermissionEnvelope.from_value(self.child_permissions, default_scope=child_scope)
        if not child.scope:
            child = replace(child, scope=child_scope)
        object.__setattr__(self, "child_permissions", child)
        if self.candidate_fingerprint is not None:
            object.__setattr__(self, "candidate_fingerprint", _assert_sha256(self.candidate_fingerprint, "candidate_fingerprint"))
        if self.candidate_state is not None:
            safe_candidate = _safe_json(self.candidate_state, path="candidate_state")
            object.__setattr__(self, "candidate_state", safe_candidate)
            if self.candidate_fingerprint is None:
                object.__setattr__(self, "candidate_fingerprint", _sha256(safe_candidate))
        if not isinstance(self.project_binding, str) or not self.project_binding.strip() or len(self.project_binding) > 512:
            raise DelegationContractError("PROJECT_BINDING_INVALID")
        context_state = {} if self.context_state is None else self.context_state
        relevant_context = {} if self.relevant_context is None else self.relevant_context
        if not isinstance(context_state, Mapping) or not isinstance(relevant_context, Mapping):
            raise DelegationContractError("CONTEXT_STATE_MUST_BE_OBJECT")
        object.__setattr__(self, "context_state", _safe_json(context_state, path="context_state"))
        object.__setattr__(self, "relevant_context", _safe_json(relevant_context, path="relevant_context"))
        capability_readiness = {} if self.capability_readiness is None else self.capability_readiness
        permission_state = {} if self.permission_state is None else self.permission_state
        if not isinstance(capability_readiness, Mapping) or not isinstance(permission_state, Mapping):
            raise DelegationContractError("PREFLIGHT_STATE_MUST_BE_OBJECT")
        object.__setattr__(self, "capability_readiness", _safe_json(capability_readiness, path="capability_readiness"))
        object.__setattr__(self, "permission_state", _safe_json(permission_state, path="permission_state"))
        object.__setattr__(self, "dependency_outcomes", tuple(_safe_json(item, path="dependency_outcomes") for item in self.dependency_outcomes))
        object.__setattr__(self, "relevant_decisions", _refs(self.relevant_decisions, "relevant_decisions"))
        object.__setattr__(self, "known_risks", _refs(self.known_risks, "known_risks"))
        object.__setattr__(self, "unknowns", _refs(self.unknowns, "unknowns"))
        if not isinstance(self.requested_execution_class, str) or not self.requested_execution_class.strip() or len(self.requested_execution_class) > 128:
            raise DelegationContractError("REQUESTED_EXECUTION_CLASS_INVALID")
        if self.required_identity and not self.identity_required:
            object.__setattr__(self, "identity_required", True)
        if self.identity_required and (not isinstance(self.required_identity, str) or not self.required_identity.strip()):
            raise DelegationContractError("REQUIRED_IDENTITY_MISSING")
        if not isinstance(self.observed_identity, str) or not self.observed_identity.strip():
            raise DelegationContractError("OBSERVED_IDENTITY_INVALID")
        if not isinstance(self.identity_authority, str) or not self.identity_authority.strip():
            raise DelegationContractError("IDENTITY_AUTHORITY_INVALID")
        if not isinstance(self.budget, DelegationBudget):
            raise DelegationContractError("DELEGATION_BUDGET_REQUIRED")

    @property
    def parent_scope(self) -> tuple[str, ...]:
        return self.parent_permissions.scope or self.task.scope

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": DELEGATION_SCHEMA,
            "task_id": self.task.task_id,
            "goal_id": self.task.goal_id,
            "task_size": self.task_size,
            "value_reasons": list(self.value_reasons),
            "parent_permissions": self.parent_permissions.to_dict(),
            "child_permissions": self.child_permissions.to_dict() if self.child_permissions else None,
            "child_scope": list(self.child_scope),
            "read_scopes": list(self.read_scopes),
            "write_scopes": list(self.write_scopes),
            "delete_scopes": list(self.delete_scopes),
            "shared_resources": list(self.shared_resources),
            "candidate_fingerprint": self.candidate_fingerprint,
            "project_binding": self.project_binding,
            "context_refs": list(self.task.context_refs),
            "capability_readiness": self.capability_readiness,
            "permission_state": self.permission_state,
            "relevant_decisions": list(self.relevant_decisions),
            "requested_execution_class": self.requested_execution_class,
            "identity_required": self.identity_required,
            "required_identity": self.required_identity,
            "observed_identity": self.observed_identity,
            "identity_authority": self.identity_authority,
            "host_child_available": self.host_child_available,
            "allow_direct_fallback": self.allow_direct_fallback,
            "budget": self.budget.to_dict(),
        }


@dataclass(frozen=True)
class DelegationDecision:
    strategy: str
    task_id: str
    goal_id: str
    reason: str
    value_reasons: tuple[str, ...] = ()
    rationale: Mapping[str, Any] = field(default_factory=dict)
    plan_hash: str = ""
    plan_revision: int = 0
    requested_execution_class: str = HOST_DEFAULT_EXECUTION_CLASS
    decided_at: str = field(default_factory=_now)

    def __post_init__(self) -> None:
        if self.strategy not in {DIRECT, DELEGATE, BLOCKED}:
            raise DelegationContractError("DELEGATION_STRATEGY_INVALID")
        if not isinstance(self.task_id, str) or not self.task_id.strip():
            raise DelegationContractError("DECISION_TASK_ID_INVALID")
        if self.plan_hash:
            _assert_sha256(self.plan_hash, "decision.plan_hash")
        if not isinstance(self.rationale, Mapping):
            raise DelegationContractError("DECISION_RATIONALE_INVALID")
        _safe_json(self.rationale, path="decision.rationale")

    @property
    def decision(self) -> str:
        return self.strategy

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "schema": DELEGATION_SCHEMA,
            "strategy": self.strategy,
            "decision": self.strategy,
            "task_id": self.task_id,
            "goal_id": self.goal_id,
            "reason": self.reason,
            "value_reasons": list(self.value_reasons),
            "rationale": _safe_json(self.rationale, path="decision.rationale"),
            "plan_hash": self.plan_hash,
            "plan_revision": self.plan_revision,
            "requested_execution_class": self.requested_execution_class,
            "execution_selection_order": ["TASK", "DELEGATION_STRATEGY", "EXECUTION_CLASS_IF_NEEDED"],
            "model_profile_resolution": "NOT_REQUESTED",
            "decided_at": self.decided_at,
        }
        return payload


def _handoff_payload(
    *,
    handoff_id: str,
    task_id: str,
    goal_id: str,
    task_purpose: str,
    scope: Sequence[str],
    non_scope: Sequence[str],
    acceptance_requirements: Sequence[str],
    dependency_outcomes: Sequence[Mapping[str, Any]],
    decision_refs: Sequence[str],
    context_refs: Sequence[str],
    context_manifest: Mapping[str, Any],
    candidate_fingerprint: str,
    project_fingerprint: str,
    required_capabilities: Sequence[str],
    permissions: PermissionEnvelope,
    budget: DelegationBudget,
    output_contract: Sequence[str],
    verification_expectations: Sequence[str],
    known_risks: Sequence[str],
    unknowns: Sequence[str],
    requested_execution_class: str,
    identity_required: bool,
    required_identity: str | None,
    plan_hash: str,
    plan_revision: int,
) -> dict[str, Any]:
    return {
        "schema": HANDOFF_SCHEMA,
        "handoff_id": handoff_id,
        "task_id": task_id,
        "goal_id": goal_id,
        "task_purpose": task_purpose,
        "scope": list(scope),
        "non_scope": list(non_scope),
        "acceptance_requirements": list(acceptance_requirements),
        "dependency_outcomes": [_safe_json(item, path="handoff.dependency_outcomes") for item in dependency_outcomes],
        "decision_refs": list(decision_refs),
        "context_refs": list(context_refs),
        "context_manifest": _safe_json(context_manifest, path="handoff.context_manifest"),
        "candidate_fingerprint": candidate_fingerprint,
        "project_fingerprint": project_fingerprint,
        "required_capabilities": list(required_capabilities),
        "permissions": permissions.to_dict(),
        "budget": budget.to_dict(),
        "output_contract": list(output_contract),
        "verification_expectations": list(verification_expectations),
        "known_risks": list(known_risks),
        "unknowns": list(unknowns),
        "requested_execution_class": requested_execution_class,
        "identity_required": identity_required,
        "required_identity": required_identity,
        "plan_hash": plan_hash,
        "plan_revision": plan_revision,
        "max_depth": MAX_DELEGATION_DEPTH,
        "child_count": 1,
        "child_delegation_allowed": False,
        "parent_verifies": True,
        "output_is_evidence": False,
    }


@dataclass(frozen=True)
class WorkerHandoff:
    """Minimal child packet; the fingerprint binds the immutable contract."""

    handoff_id: str
    task_id: str
    goal_id: str
    task_purpose: str
    scope: tuple[str, ...]
    non_scope: tuple[str, ...]
    acceptance_requirements: tuple[str, ...]
    dependency_outcomes: tuple[Mapping[str, Any], ...]
    decision_refs: tuple[str, ...]
    context_refs: tuple[str, ...]
    context_manifest: Mapping[str, Any]
    candidate_fingerprint: str
    project_fingerprint: str
    required_capabilities: tuple[str, ...]
    permissions: PermissionEnvelope
    budget: DelegationBudget
    output_contract: tuple[str, ...]
    verification_expectations: tuple[str, ...]
    known_risks: tuple[str, ...]
    unknowns: tuple[str, ...]
    requested_execution_class: str
    identity_required: bool
    required_identity: str | None
    plan_hash: str
    plan_revision: int
    fingerprint: str
    created_at: str = field(default_factory=_now)
    max_depth: int = MAX_DELEGATION_DEPTH
    child_count: int = 1
    child_delegation_allowed: bool = False

    def __post_init__(self) -> None:
        if not _HANDOFF_ID_RE.fullmatch(self.handoff_id):
            raise DelegationContractError("HANDOFF_ID_INVALID")
        if not self.scope or not scope_is_subset(self.scope, self.scope, self.non_scope):
            raise DelegationScopeError("HANDOFF_SCOPE_INVALID")
        _assert_sha256(self.candidate_fingerprint, "handoff.candidate_fingerprint")
        _assert_sha256(self.project_fingerprint, "handoff.project_fingerprint")
        _assert_sha256(self.plan_hash, "handoff.plan_hash")
        _assert_sha256(self.fingerprint, "handoff.fingerprint")
        if self.max_depth != MAX_DELEGATION_DEPTH or self.child_count != 1 or self.child_delegation_allowed:
            raise DelegationContractError("HANDOFF_DEPTH_OR_CHILD_LIMIT_INVALID")
        if self.permissions.delegate_allowed:
            raise DelegationPermissionError("CHILD_DELEGATE_MUST_BE_FALSE")
        _safe_json(self.context_manifest, path="handoff.context_manifest")

    @classmethod
    def create(
        cls,
        *,
        handoff_id: str,
        task: TaskRecord,
        plan_hash: str,
        plan_revision: int,
        context_manifest: Mapping[str, Any],
        dependency_outcomes: Sequence[Mapping[str, Any]],
        decision_refs: Sequence[str],
        candidate_fingerprint: str,
        project_fingerprint: str,
        permissions: PermissionEnvelope,
        scope: Sequence[str],
        budget: DelegationBudget,
        requested_execution_class: str,
        identity_required: bool,
        required_identity: str | None,
        known_risks: Sequence[str],
        unknowns: Sequence[str],
    ) -> "WorkerHandoff":
        normalized_scope = _refs(scope, "handoff.scope", required=True)
        normalized_non_scope = _refs(task.non_scope, "handoff.non_scope")
        normalized_acceptance = _refs(task.acceptance_requirements, "handoff.acceptance_requirements", required=True)
        normalized_capabilities = _refs(task.required_capabilities, "handoff.required_capabilities")
        normalized_decisions = _refs(decision_refs, "handoff.decision_refs")
        normalized_context_refs = _refs(task.context_refs, "handoff.context_refs")
        output_contract = (
            "handoff_id",
            "task_id",
            "outcome",
            "work_performed",
            "artifact_refs",
            "candidate_fingerprint",
            "self_checks",
            "unresolved",
            "risks",
            "recommended_next_step",
            "host_execution_id_if_available",
            "observed_identity",
            "identity_authority",
            "mutation_state",
        )
        verification_expectations = (
            "parent_reads_current_candidate_state",
            "parent_checks_required_evidence",
            "worker_output_is_proposal_only",
        )
        payload = _handoff_payload(
            handoff_id=handoff_id,
            task_id=task.task_id,
            goal_id=task.goal_id,
            task_purpose=task.purpose,
            scope=normalized_scope,
            non_scope=normalized_non_scope,
            acceptance_requirements=normalized_acceptance,
            dependency_outcomes=dependency_outcomes,
            decision_refs=normalized_decisions,
            context_refs=normalized_context_refs,
            context_manifest=context_manifest,
            candidate_fingerprint=candidate_fingerprint,
            project_fingerprint=project_fingerprint,
            required_capabilities=normalized_capabilities,
            permissions=permissions,
            budget=budget,
            output_contract=output_contract,
            verification_expectations=verification_expectations,
            known_risks=known_risks,
            unknowns=unknowns,
            requested_execution_class=requested_execution_class,
            identity_required=identity_required,
            required_identity=required_identity,
            plan_hash=plan_hash,
            plan_revision=plan_revision,
        )
        fingerprint_payload = dict(payload)
        fingerprint_payload.pop("handoff_id", None)
        fingerprint = _sha256(fingerprint_payload)
        return cls(
            handoff_id=handoff_id,
            task_id=task.task_id,
            goal_id=task.goal_id,
            task_purpose=task.purpose,
            scope=normalized_scope,
            non_scope=normalized_non_scope,
            acceptance_requirements=normalized_acceptance,
            dependency_outcomes=tuple(_safe_json(item, path="handoff.dependency_outcomes") for item in dependency_outcomes),
            decision_refs=normalized_decisions,
            context_refs=normalized_context_refs,
            context_manifest=_safe_json(context_manifest, path="handoff.context_manifest"),
            candidate_fingerprint=candidate_fingerprint,
            project_fingerprint=project_fingerprint,
            required_capabilities=normalized_capabilities,
            permissions=permissions,
            budget=budget,
            output_contract=output_contract,
            verification_expectations=verification_expectations,
            known_risks=_refs(known_risks, "handoff.known_risks"),
            unknowns=_refs(unknowns, "handoff.unknowns"),
            requested_execution_class=requested_execution_class,
            identity_required=identity_required,
            required_identity=required_identity,
            plan_hash=_assert_sha256(plan_hash, "handoff.plan_hash"),
            plan_revision=plan_revision,
            fingerprint=fingerprint,
        )

    def to_dict(self) -> dict[str, Any]:
        payload = _handoff_payload(
            handoff_id=self.handoff_id,
            task_id=self.task_id,
            goal_id=self.goal_id,
            task_purpose=self.task_purpose,
            scope=self.scope,
            non_scope=self.non_scope,
            acceptance_requirements=self.acceptance_requirements,
            dependency_outcomes=self.dependency_outcomes,
            decision_refs=self.decision_refs,
            context_refs=self.context_refs,
            context_manifest=self.context_manifest,
            candidate_fingerprint=self.candidate_fingerprint,
            project_fingerprint=self.project_fingerprint,
            required_capabilities=self.required_capabilities,
            permissions=self.permissions,
            budget=self.budget,
            output_contract=self.output_contract,
            verification_expectations=self.verification_expectations,
            known_risks=self.known_risks,
            unknowns=self.unknowns,
            requested_execution_class=self.requested_execution_class,
            identity_required=self.identity_required,
            required_identity=self.required_identity,
            plan_hash=self.plan_hash,
            plan_revision=self.plan_revision,
        )
        payload.update(
            {
                "fingerprint": self.fingerprint,
                "created_at": self.created_at,
                "max_depth": MAX_DELEGATION_DEPTH,
                "child_count": 1,
                "child_delegation_allowed": False,
                "parent_verifies": True,
                "output_is_evidence": False,
            }
        )
        return payload


@dataclass(frozen=True)
class DelegatedWorkerResult:
    """Structured child proposal; never an evidence claim."""

    handoff_id: str
    task_id: str
    outcome: str
    candidate_fingerprint: str
    summary: str = ""
    work_performed: tuple[str, ...] = ()
    artifact_refs: tuple[str, ...] = ()
    self_checks: tuple[str, ...] = ()
    unresolved: tuple[str, ...] = ()
    risks: tuple[str, ...] = ()
    recommended_next_step: str = ""
    host_execution_id: str | None = None
    host_session_ref: str | None = None
    requested_execution_class: str = HOST_DEFAULT_EXECUTION_CLASS
    observed_identity: str = UNKNOWN_IDENTITY
    identity_authority: str = "UNKNOWN"
    retryable: bool = False
    mutation_performed: bool = False
    mutation_state: str = "KNOWN_NONE"
    actions_used: int = 0
    output_bytes: int = 0
    child_delegation_allowed: bool = False
    depth: int = MAX_DELEGATION_DEPTH
    raw_host_receipt: Mapping[str, Any] | None = None
    normalized_c15_receipt: Mapping[str, Any] | None = None
    proposal_only: bool = True
    output_is_evidence: bool = False
    received_at: str = field(default_factory=_now)

    def __post_init__(self) -> None:
        if self.outcome not in CHILD_OUTCOMES:
            raise DelegationContractError("CHILD_OUTCOME_INVALID")
        _assert_sha256(self.candidate_fingerprint, "result.candidate_fingerprint")
        if self.mutation_state not in MUTATION_STATES:
            raise DelegationContractError("RESULT_MUTATION_STATE_INVALID")
        if self.child_delegation_allowed or self.depth != MAX_DELEGATION_DEPTH:
            raise DelegationPermissionError("CHILD_DELEGATION_FORBIDDEN")
        if self.actions_used < 0 or self.output_bytes < 0:
            raise DelegationContractError("RESULT_RESOURCE_COUNTER_INVALID")
        if not isinstance(self.observed_identity, str) or not self.observed_identity.strip():
            raise DelegationContractError("RESULT_IDENTITY_INVALID")
        if self.observed_identity != UNKNOWN_IDENTITY and not self.identity_authority.strip():
            raise DelegationContractError("RESULT_IDENTITY_AUTHORITY_REQUIRED")
        if self.raw_host_receipt is not None:
            _safe_host_receipt(self.raw_host_receipt, path="result.raw_host_receipt")
        if self.normalized_c15_receipt is not None:
            _safe_host_receipt(self.normalized_c15_receipt, path="result.normalized_c15_receipt", normalized=True)
        if not self.proposal_only or self.output_is_evidence:
            raise DelegationPermissionError("WORKER_RESULT_MUST_REMAIN_PROPOSAL_ONLY")

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any], handoff: WorkerHandoff) -> "DelegatedWorkerResult":
        if not isinstance(value, Mapping):
            raise DelegationControlPlaneError("CHILD_RESULT_MUST_BE_OBJECT")
        raw_host_receipt = value.get(RAW_HOST_RECEIPT_KEY, value.get("raw_host_receipt"))
        normalized_c15_receipt = value.get(NORMALIZED_C15_RECEIPT_KEY, value.get("normalized_c15_receipt"))
        ordinary_value = dict(value)
        ordinary_value.pop(RAW_HOST_RECEIPT_KEY, None)
        ordinary_value.pop("raw_host_receipt", None)
        ordinary_value.pop(NORMALIZED_C15_RECEIPT_KEY, None)
        ordinary_value.pop("normalized_c15_receipt", None)
        safe = _safe_json(ordinary_value, path="child_result")
        outcome = _status(safe.get("outcome", safe.get("status")))
        if outcome == "DONE":
            outcome = "SUCCEEDED"
        candidate = safe.get("candidate_fingerprint", safe.get("candidate_binding"))
        if not isinstance(candidate, str):
            raise DelegationControlPlaneError("CHILD_RESULT_CANDIDATE_BINDING_REQUIRED")
        raw_mutation = safe.get("mutation_state")
        if raw_mutation is None:
            raw_mutation = "UNKNOWN" if safe.get("mutation_uncertain") is True else ("KNOWN_COMPLETE" if safe.get("mutation_performed") is True else "KNOWN_NONE")
        raw_work = safe.get("work_performed", ())
        if isinstance(raw_work, str):
            raw_work = (raw_work,)
        raw_artifacts = safe.get("artifact_refs", ())
        if isinstance(raw_artifacts, str):
            raw_artifacts = (raw_artifacts,)
        return cls(
            handoff_id=str(safe.get("handoff_id", handoff.handoff_id)),
            task_id=str(safe.get("task_id", handoff.task_id)),
            outcome=outcome,
            candidate_fingerprint=_assert_sha256(candidate, "result.candidate_fingerprint"),
            summary=str(safe.get("summary", ""))[:8192],
            work_performed=_refs(raw_work, "result.work_performed"),
            artifact_refs=_refs(raw_artifacts, "result.artifact_refs"),
            self_checks=_refs(safe.get("self_checks", ()), "result.self_checks"),
            unresolved=_refs(safe.get("unresolved", ()), "result.unresolved"),
            risks=_refs(safe.get("risks", ()), "result.risks"),
            recommended_next_step=str(safe.get("recommended_next_step", ""))[:4096],
            host_execution_id=str(safe["host_execution_id"]) if safe.get("host_execution_id") else None,
            host_session_ref=str(safe["host_session_ref"]) if safe.get("host_session_ref") else None,
            requested_execution_class=str(safe.get("requested_execution_class", handoff.requested_execution_class)),
            observed_identity=str(safe.get("observed_identity", UNKNOWN_IDENTITY)),
            identity_authority=str(safe.get("identity_authority", "UNKNOWN")),
            retryable=bool(safe.get("retryable", False)),
            mutation_performed=bool(safe.get("mutation_performed", False)),
            mutation_state=str(raw_mutation),
            actions_used=int(safe.get("actions_used", 0)),
            output_bytes=int(safe.get("output_bytes", 0)),
            child_delegation_allowed=bool(safe.get("child_delegation_allowed", False)),
            depth=int(safe.get("depth", MAX_DELEGATION_DEPTH)),
            raw_host_receipt=raw_host_receipt,
            normalized_c15_receipt=normalized_c15_receipt,
            proposal_only=bool(safe.get("proposal_only", True)),
            output_is_evidence=bool(safe.get("output_is_evidence", False)),
            received_at=str(safe.get("received_at", _now())),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": CHILD_RESULT_SCHEMA,
            "handoff_id": self.handoff_id,
            "task_id": self.task_id,
            "outcome": self.outcome,
            "summary": self.summary,
            "work_performed": list(self.work_performed),
            "artifact_refs": list(self.artifact_refs),
            "candidate_fingerprint": self.candidate_fingerprint,
            "self_checks": list(self.self_checks),
            "unresolved": list(self.unresolved),
            "risks": list(self.risks),
            "recommended_next_step": self.recommended_next_step,
            "host_execution_id": self.host_execution_id,
            "host_session_ref": self.host_session_ref,
            "requested_execution_class": self.requested_execution_class,
            "observed_identity": self.observed_identity,
            "identity_authority": self.identity_authority,
            "retryable": self.retryable,
            "mutation_performed": self.mutation_performed,
            "mutation_state": self.mutation_state,
            "actions_used": self.actions_used,
            "output_bytes": self.output_bytes,
            "child_delegation_allowed": False,
            "depth": MAX_DELEGATION_DEPTH,
            "proposal_only": self.proposal_only,
            "output_is_evidence": self.output_is_evidence,
            RAW_HOST_RECEIPT_KEY: _safe_host_receipt(self.raw_host_receipt, path="result.raw_host_receipt") if self.raw_host_receipt is not None else None,
            NORMALIZED_C15_RECEIPT_KEY: _safe_host_receipt(self.normalized_c15_receipt, path="result.normalized_c15_receipt", normalized=True) if self.normalized_c15_receipt is not None else None,
            "received_at": self.received_at,
        }


ChildResult = DelegatedWorkerResult
WorkerResult = DelegatedWorkerResult


class CodexHostAdapter:
    """Bind one bounded handoff to the supported Codex host seam.

    The project runtime cannot call the desktop host's ``multi_agent_v1``
    tool directly.  The supported host surface supplies ``host_executor``.
    This adapter therefore owns only the narrow binding contract: it sends
    the already-created C15 handoff package, requires an official host result
    and a fresh C09 identity receipt, and returns a proposal-only C15 result.
    Missing host evidence is a hard control-plane failure; no identity or
    result is inferred from a profile, output text, or a caller-supplied ID.
    """

    def __init__(
        self,
        root: str | Path,
        host_executor: Callable[..., Any],
        *,
        ledger_path: str | Path | None = None,
    ) -> None:
        if not callable(host_executor):
            raise DelegationControlPlaneError("HOST_EXECUTOR_REQUIRED")
        self.root = Path(root).expanduser().resolve()
        self.ledger_path = (
            Path(ledger_path).expanduser().resolve()
            if ledger_path is not None
            else self.root / ".p2p" / "state" / "execution-ledger.jsonl"
        )
        self.host_executor = host_executor

    @staticmethod
    def _receipt_key(receipt: Mapping[str, Any]) -> tuple[str, str, str, str, str]:
        return (
            str(receipt.get("event", "")),
            str(receipt.get("session_id", "")),
            str(receipt.get("turn_id", "")),
            str(receipt.get("agent_id", "")),
            str(receipt.get("agent_type", "")),
        )

    @staticmethod
    def _required_text(value: Any, field: str) -> str:
        if not isinstance(value, str) or not value.strip() or len(value) > 4096:
            raise DelegationControlPlaneError(f"HOST_{field.upper()}_MISSING")
        return value.strip()

    def _minimum_package(self, handoff: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
        safe_handoff = _safe_json(handoff, path="host.handoff")
        if safe_handoff.get("schema") != HANDOFF_SCHEMA:
            raise DelegationControlPlaneError("HOST_HANDOFF_SCHEMA_INVALID")
        safe_context = _safe_json(context, path="host.context")
        allowed_context = {
            "handoff_id",
            "depth",
            "child_count",
            "child_delegation_allowed",
            "budget",
            "permissions",
        }
        if set(safe_context) - allowed_context:
            raise DelegationControlPlaneError("HOST_CONTEXT_PACKAGE_OUTSIDE_BOUNDARY")
        if safe_context.get("handoff_id") != safe_handoff.get("handoff_id"):
            raise DelegationControlPlaneError("HOST_CONTEXT_HANDOFF_MISMATCH")
        if safe_context.get("depth") != MAX_DELEGATION_DEPTH or safe_context.get("child_count") != 1:
            raise DelegationControlPlaneError("HOST_CONTEXT_DEPTH_OR_CHILD_LIMIT_INVALID")
        if safe_context.get("child_delegation_allowed") is not False:
            raise DelegationControlPlaneError("HOST_CONTEXT_CHILD_DELEGATION_FORBIDDEN")
        return {
            "schema": HOST_ADAPTER_SCHEMA,
            "handoff": safe_handoff,
            "context": safe_context,
            "package_fields": (
                "handoff",
                "context",
            ),
            "omitted_context": (
                "conversation_history",
                "unrelated_project_files",
                "provider_telemetry",
                "secrets",
            ),
        }

    def _fresh_receipt(
        self,
        before: set[tuple[str, str, str, str, str]],
        raw: Mapping[str, Any],
        handoff: Mapping[str, Any],
    ) -> dict[str, Any]:
        try:
            receipts = read_receipts(self.ledger_path)
        except Exception as exc:
            raise DelegationControlPlaneError("HOST_RECEIPT_READ_FAILED") from exc
        host_id = self._required_text(raw.get("host_execution_id"), "execution_id")
        session_id = raw.get("session_id")
        turn_id = raw.get("turn_id")
        required_identity = handoff.get("required_identity")
        matches: list[dict[str, Any]] = []
        for receipt in receipts:
            if not validate_host_identity_receipt(receipt):
                continue
            if self._receipt_key(receipt) in before:
                continue
            if receipt.get("agent_id") != host_id:
                continue
            if session_id is not None and receipt.get("session_id") != session_id:
                continue
            if turn_id is not None and receipt.get("turn_id") != turn_id:
                continue
            if required_identity is not None and receipt.get("agent_type") != required_identity:
                continue
            matches.append(dict(receipt))
        if not matches:
            raise DelegationControlPlaneError("HOST_RECEIPT_MISSING_OR_UNBOUND")
        matches.sort(key=lambda item: str(item.get("timestamp", "")))
        return matches[-1]

    def __call__(self, handoff: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
        package = self._minimum_package(handoff, context)
        before = {self._receipt_key(receipt) for receipt in read_receipts(self.ledger_path)}
        try:
            raw = _invoke(self.host_executor, package, context, allow_second=True)
        except Exception as exc:
            raise DelegationControlPlaneError(f"HOST_INVOCATION_FAILED:{type(exc).__name__}") from exc
        if not isinstance(raw, Mapping):
            raise DelegationControlPlaneError("HOST_RESULT_MUST_BE_OBJECT")
        safe = _safe_json(raw, path="host.raw_result")
        if safe.get("execution_source") != HOST_EXECUTION_SOURCE:
            raise DelegationControlPlaneError("HOST_EXECUTION_SOURCE_INVALID")
        if safe.get("execution_completed") is not True:
            raise DelegationControlPlaneError("HOST_EXECUTION_NOT_COMPLETED")
        if safe.get("child_count") != 0 or safe.get("delegation_depth") != 0:
            raise DelegationPermissionError("HOST_RECURSIVE_DELEGATION_FORBIDDEN")
        host_receipt = self._fresh_receipt(before, safe, handoff)
        worker_result = safe.get("worker_result")
        if not isinstance(worker_result, Mapping):
            raise DelegationControlPlaneError("HOST_WORKER_RESULT_REQUIRED")
        worker_payload = dict(_safe_json(worker_result, path="host.worker_result"))
        worker_payload.setdefault("handoff_id", handoff.get("handoff_id"))
        worker_payload.setdefault("task_id", handoff.get("task_id"))
        worker_payload.setdefault("host_execution_id", safe.get("host_execution_id"))
        worker_payload.setdefault("host_session_ref", safe.get("session_id"))
        worker_payload.setdefault("requested_execution_class", handoff.get("requested_execution_class", HOST_DEFAULT_EXECUTION_CLASS))
        worker_payload.setdefault("observed_identity", host_receipt.get("agent_type", UNKNOWN_IDENTITY))
        worker_payload.setdefault("identity_authority", host_receipt.get("source", "UNKNOWN"))
        worker_payload.setdefault("output_bytes", len(str(safe.get("output", "")).encode("utf-8")))
        worker_payload[RAW_HOST_RECEIPT_KEY] = host_receipt
        worker_payload[NORMALIZED_C15_RECEIPT_KEY] = {
            "schema": "p2p-c15-normalized-host-receipt/1",
            "adapter_schema": HOST_ADAPTER_SCHEMA,
            "handoff_id": handoff.get("handoff_id"),
            "task_id": handoff.get("task_id"),
            "plan_hash": handoff.get("plan_hash"),
            "host_execution_id": safe.get("host_execution_id"),
            "session_id": host_receipt.get("session_id"),
            "turn_id": host_receipt.get("turn_id"),
            "status": "COMPLETED",
            "execution_source": safe.get("execution_source"),
            "agent_type": host_receipt.get("agent_type"),
            "permission_mode": host_receipt.get("permission_mode"),
            "identity_authority": host_receipt.get("source"),
            "timestamp": host_receipt.get("timestamp"),
            "output_is_evidence": False,
        }
        worker_payload["proposal_only"] = True
        worker_payload["output_is_evidence"] = False
        return worker_payload


def _coerce_verification(value: Any) -> tuple[str, tuple[EvidenceClaim | Mapping[str, Any], ...], Any, str]:
    if isinstance(value, Mapping):
        status = _status(value.get("status"))
        raw_claims = value.get("evidence_claims", ())
        candidate_state = value.get("candidate_state")
        summary = str(value.get("summary", ""))
    else:
        status = _status(getattr(value, "status", ""))
        raw_claims = getattr(value, "evidence_claims", ())
        candidate_state = getattr(value, "candidate_state", None)
        summary = str(getattr(value, "summary", ""))
    if isinstance(raw_claims, (str, bytes)) or raw_claims is None:
        raw_claims = ()
    claims = tuple(item for item in raw_claims if isinstance(item, (EvidenceClaim, Mapping)))
    return status, claims, candidate_state, summary


def _candidate_binding_matches(candidate_state: Any, expected: str) -> bool:
    if candidate_state is None:
        return False
    safe = _safe_json(candidate_state, path="verification.candidate_state")
    if isinstance(safe, Mapping):
        for key in ("candidate_fingerprint", "candidate_state_fingerprint", "state_fingerprint", "handoff_fingerprint"):
            if key in safe:
                return str(safe[key]).lower() == expected.lower()
    return _sha256(safe) == expected.lower()


def _plan_contract_fingerprint(plan: TaskPlan, task: TaskRecord) -> str:
    """Hash the immutable handoff contract, excluding volatile run metadata."""

    return _sha256(
        {
            "schema": "p2p-c15-plan-contract/1",
            "goal_id": plan.goal_id,
            "logical_owner": plan.logical_owner.to_dict(),
            "plan_scope": list(plan.plan_scope),
            "plan_non_scope": list(plan.plan_non_scope),
            "plan_revision": plan.plan_revision,
            "task": {
                "task_id": task.task_id,
                "goal_id": task.goal_id,
                "title": task.title,
                "purpose": task.purpose,
                "dependencies": list(task.dependencies),
                "scope": list(task.scope),
                "non_scope": list(task.non_scope),
                "acceptance_requirements": list(task.acceptance_requirements),
                "required_capabilities": list(task.required_capabilities),
                "permission_needs": list(task.permission_needs),
                "context_refs": list(task.context_refs),
                "output_refs": list(task.output_refs),
                "requirement_refs": list(task.requirement_refs),
                "decision_refs": list(task.decision_refs),
            },
        }
    )


class BoundedDelegationController:
    """Select, hand off, and verify at most one foreground child."""

    def __init__(
        self,
        root: str | Path,
        *,
        protected_roots: Iterable[str | Path] = (),
        parallel_group_id: str | None = None,
        parallel_task_ids: Iterable[str] = (),
    ) -> None:
        self.store = TaskStateStore(root, protected_roots=protected_roots)
        self.root = self.store.root
        self._live_children = 0
        self.parallel_group_id = parallel_group_id
        self.parallel_task_ids = tuple(dict.fromkeys(str(item) for item in parallel_task_ids if str(item).strip()))
        if self.parallel_group_id is not None:
            if not re.fullmatch(r"parallel-[a-f0-9]{16,64}", self.parallel_group_id):
                raise DelegationContractError("PARALLEL_GROUP_ID_INVALID")
            if not self.parallel_task_ids or len(self.parallel_task_ids) > 2:
                raise DelegationContractError("PARALLEL_GROUP_TASK_LIMIT_INVALID")

    def _parallel_context_allows(self, active: Sequence[TaskRecord | str], selected_id: str | None = None) -> bool:
        if not self.parallel_group_id or not self.parallel_task_ids or len(active) > 2:
            return False
        active_ids = {task.task_id if isinstance(task, TaskRecord) else str(task) for task in active}
        if not active_ids.issubset(set(self.parallel_task_ids)):
            return False
        return selected_id is None or (selected_id in self.parallel_task_ids and selected_id not in active_ids)

    def _result(self, status: str, *, strategy: str = BLOCKED, task_id: str | None = None, reason: str = "", **extra: Any) -> dict[str, Any]:
        result: dict[str, Any] = {
            "schema": DELEGATION_RESULT_SCHEMA,
            "status": status,
            "strategy": strategy,
            "delegation_decision": strategy,
            "task_id": task_id,
            "reason": reason,
            "automatic_start": False,
            "background_execution": False,
            "process_survives_session": False,
            "parallel_execution": self.parallel_group_id is not None,
            "parallel_group_id": self.parallel_group_id,
            "delegated_children": 1 if strategy == DELEGATE else 0,
            "max_delegated_children": MAX_DELEGATED_CHILDREN,
            "max_delegation_depth": MAX_DELEGATION_DEPTH,
            "child_delegation_allowed": False,
            "model_profile_resolution": "NOT_REQUESTED",
            "output_is_evidence": False,
        }
        result.update(_safe_json(extra, path="delegation.result"))
        return result

    def _control_plane(self) -> TaskPlan:
        try:
            plan = self.store.require()
            events = self.store.read_events()
        except TaskStateError as exc:
            raise DelegationControlPlaneError(str(exc)) from exc
        if events.get("status") == "PARTIAL":
            raise DelegationControlPlaneError("CONTROL_PLANE_TASK_LEDGER_PARTIAL")
        if events.get("status") == "NOT_INITIALIZED":
            raise DelegationControlPlaneError("CONTROL_PLANE_TASK_LEDGER_NOT_INITIALIZED")
        active = [task.task_id for task in plan.tasks.values() if task.status == "ACTIVE"]
        if len(active) > 1 and not self._parallel_context_allows(active):
            raise DelegationControlPlaneError("CONTROL_PLANE_MULTIPLE_ACTIVE_TASKS")
        if len(active) > 0 and self.parallel_group_id and not self._parallel_context_allows(active):
            raise DelegationControlPlaneError("CONTROL_PLANE_PARALLEL_GROUP_BINDING_INVALID")
        return plan

    def _refresh_ready(self, plan: TaskPlan) -> TaskPlan:
        refreshed = plan.refresh_ready()
        if refreshed.canonical_hash() == plan.canonical_hash():
            return plan
        try:
            return self.store.save(refreshed, event_name="delegation_ready_refresh")
        except TaskStateError as exc:
            raise DelegationControlPlaneError(str(exc)) from exc

    @staticmethod
    def _active_tasks(plan: TaskPlan) -> tuple[TaskRecord, ...]:
        return tuple(task for task in plan.tasks.values() if task.status == "ACTIVE")

    def _candidate(self, plan: TaskPlan, task_id: str | None) -> TaskRecord | None:
        if task_id is not None:
            task = plan.tasks.get(task_id)
            if task is None:
                raise DelegationContractError(f"TASK_NOT_FOUND:{task_id}")
            return task
        return next_safe_task(plan)

    def _select_base(self, task_id: str | None) -> tuple[TaskPlan, TaskRecord]:
        """Select a current task before evaluating the C15 policy."""

        plan = self._refresh_ready(self._control_plane())
        active = self._active_tasks(plan)
        if active and not self._parallel_context_allows(active, task_id):
            raise DelegationControlPlaneError(f"ACTIVE_TASK_REQUIRES_EXPLICIT_RESUME:{active[0].task_id}")
        task = self._candidate(plan, task_id)
        if task is None:
            raise DelegationControlPlaneError("NO_SAFE_READY_TASK")
        return plan, task

    def _prepare(self, task_id: str | None, request: DelegationRequest | None) -> tuple[TaskPlan, TaskRecord, dict[str, Any]]:
        base_plan = self._control_plane()
        plan = base_plan if request is not None else self._refresh_ready(base_plan)
        active = self._active_tasks(plan)
        selected_id = task_id or (request.task.task_id if request else None)
        if active and not self._parallel_context_allows(active, selected_id):
            raise DelegationControlPlaneError(f"ACTIVE_TASK_REQUIRES_EXPLICIT_RESUME:{active[0].task_id}")
        task = self._candidate(plan, selected_id)
        if task is None:
            raise DelegationControlPlaneError("NO_SAFE_READY_TASK")
        kwargs: dict[str, Any] = {}
        if request is not None:
            kwargs = {
                "capability_readiness": request.capability_readiness,
                "permission_state": request.permission_state,
                "context_state": request.context_state,
            }
        try:
            updated, preflight = self.store.preflight(task.task_id, **kwargs)
        except TaskStateError as exc:
            raise DelegationControlPlaneError(str(exc)) from exc
        task = updated.tasks[task.task_id]
        return updated, task, preflight

    @staticmethod
    def _context_manifest(task: TaskRecord, request: DelegationRequest) -> dict[str, Any]:
        manifest: dict[str, Any] = {}
        sources: dict[str, Any] = {}
        if isinstance(request.context_state, Mapping):
            sources.update(request.context_state)
        if isinstance(request.relevant_context, Mapping):
            sources.update(request.relevant_context)
        allowed_keys = {"status", "source_ref", "fingerprint", "version", "observed_at", "freshness", "scope"}
        for reference in task.context_refs:
            raw = sources.get(reference)
            if not isinstance(raw, Mapping):
                manifest[reference] = {"status": "UNKNOWN"}
                continue
            manifest[reference] = {
                str(key): _safe_json(value, path=f"context_manifest.{reference}.{key}")
                for key, value in raw.items()
                if str(key) in allowed_keys
            }
        return manifest

    @staticmethod
    def _dependency_outcomes(plan: TaskPlan, task: TaskRecord, supplied: Sequence[Mapping[str, Any]]) -> tuple[Mapping[str, Any], ...]:
        if supplied:
            return tuple(_safe_json(item, path="dependency_outcomes") for item in supplied)
        return tuple(
            {
                "task_id": dependency,
                "status": plan.tasks[dependency].status,
                "completion_verified": plan.tasks[dependency].status == "DONE" and plan.tasks[dependency].completion is not None,
            }
            for dependency in task.dependencies
        )

    @staticmethod
    def _coerce_request(task: TaskRecord, request: DelegationRequest | None, overrides: Mapping[str, Any]) -> DelegationRequest:
        if request is not None:
            if request.task.task_id != task.task_id or request.task.goal_id != task.goal_id:
                raise DelegationStaleError("REQUEST_TASK_BINDING_STALE")
            return replace(request, task=task)
        values = dict(overrides)
        parent = PermissionEnvelope.from_value(values.pop("parent_permissions", None), default_scope=task.scope)
        child = values.pop("child_permissions", None)
        if child is not None:
            child = PermissionEnvelope.from_value(child, default_scope=values.get("child_scope", task.scope))
        allowed = {
            "task_size",
            "value_reasons",
            "child_scope",
            "read_scopes",
            "write_scopes",
            "delete_scopes",
            "shared_resources",
            "candidate_state",
            "candidate_fingerprint",
            "project_binding",
            "context_state",
            "capability_readiness",
            "permission_state",
            "relevant_context",
            "dependency_outcomes",
            "relevant_decisions",
            "known_risks",
            "unknowns",
            "requested_execution_class",
            "identity_required",
            "required_identity",
            "observed_identity",
            "identity_authority",
            "host_child_available",
            "owner_gate",
            "allow_direct_fallback",
            "budget",
        }
        values = {key: value for key, value in values.items() if key in allowed}
        return DelegationRequest(task=task, parent_permissions=parent, child_permissions=child, **values)

    def _resolve_request(
        self,
        task_id: str | None,
        request: DelegationRequest | None,
        overrides: Mapping[str, Any],
    ) -> tuple[TaskPlan, TaskRecord, dict[str, Any], DelegationRequest]:
        if request is None:
            _, base_task = self._select_base(task_id)
            normalized = self._coerce_request(base_task, None, overrides)
        else:
            normalized = request
        plan, task, preflight = self._prepare(task_id, normalized)
        normalized = self._coerce_request(task, normalized, {})
        return plan, task, preflight, normalized

    def _decision_from_request(self, plan: TaskPlan, task: TaskRecord, preflight: Mapping[str, Any], request: DelegationRequest) -> DelegationDecision:
        decision_plan_hash = _plan_contract_fingerprint(plan, task)
        if preflight.get("status") != "PASS":
            reason = "OWNER_GATE_UNRESOLVED" if preflight.get("status") == "WAITING_OWNER" else "PREFLIGHT_BLOCKED"
            return DelegationDecision(
                strategy=BLOCKED,
                task_id=task.task_id,
                goal_id=task.goal_id,
                reason=reason,
                value_reasons=request.value_reasons,
                plan_hash=decision_plan_hash,
                plan_revision=plan.plan_revision,
                requested_execution_class=request.requested_execution_class,
                rationale={"preflight_status": preflight.get("status"), "preflight_reasons": list(preflight.get("reasons", ()))},
            )
        if task.status != "READY":
            return DelegationDecision(
                strategy=BLOCKED,
                task_id=task.task_id,
                goal_id=plan.goal_id,
                reason=f"TASK_NOT_READY:{task.status}",
                value_reasons=request.value_reasons,
                plan_hash=decision_plan_hash,
                plan_revision=plan.plan_revision,
                requested_execution_class=request.requested_execution_class,
                rationale={"task_status": task.status},
            )
        if not plan.dependencies_are_done(task.task_id):
            return DelegationDecision(
                strategy=BLOCKED,
                task_id=task.task_id,
                goal_id=plan.goal_id,
                reason="DEPENDENCY_NOT_DONE",
                value_reasons=request.value_reasons,
                plan_hash=decision_plan_hash,
                plan_revision=plan.plan_revision,
                requested_execution_class=request.requested_execution_class,
                rationale={"dependencies": list(task.dependencies)},
            )
        if request.owner_gate is not None and _status(request.owner_gate.get("status")) not in {"APPROVED", "GRANTED", "OBSERVED"}:
            return DelegationDecision(
                strategy=BLOCKED,
                task_id=task.task_id,
                goal_id=plan.goal_id,
                reason="OWNER_GATE_UNRESOLVED",
                value_reasons=request.value_reasons,
                plan_hash=decision_plan_hash,
                plan_revision=plan.plan_revision,
                requested_execution_class=request.requested_execution_class,
                rationale={"owner_gate_status": request.owner_gate.get("status")},
            )
        # DIRECT is deliberately evaluated before any delegation-specific data.
        if not request.value_reasons:
            return DelegationDecision(
                strategy=DIRECT,
                task_id=task.task_id,
                goal_id=plan.goal_id,
                reason="NO_MATERIAL_DELEGATION_VALUE",
                value_reasons=(),
                plan_hash=decision_plan_hash,
                plan_revision=plan.plan_revision,
                requested_execution_class=request.requested_execution_class,
                rationale={"task_size": request.task_size, "handoff_overhead": "NOT_JUSTIFIED"},
            )
        if request.task_size in {"TINY", "SMALL"} and not ({"INDEPENDENT_REVIEW", "SPECIALIST_ANALYSIS"} & set(request.value_reasons)):
            return DelegationDecision(
                strategy=DIRECT,
                task_id=task.task_id,
                goal_id=plan.goal_id,
                reason="DIRECT_LOW_OVERHEAD_WINS",
                value_reasons=request.value_reasons,
                plan_hash=decision_plan_hash,
                plan_revision=plan.plan_revision,
                requested_execution_class=request.requested_execution_class,
                rationale={"task_size": request.task_size, "material_value": False},
            )
        if request.candidate_fingerprint is None:
            return DelegationDecision(
                strategy=BLOCKED,
                task_id=task.task_id,
                goal_id=plan.goal_id,
                reason="CANDIDATE_STATE_UNKNOWN",
                value_reasons=request.value_reasons,
                plan_hash=decision_plan_hash,
                plan_revision=plan.plan_revision,
                requested_execution_class=request.requested_execution_class,
                rationale={"candidate_binding": "MISSING"},
            )
        parent_grants = set(request.parent_permissions.grants)
        required_grants = {str(item).strip().upper() for item in task.permission_needs if str(item).strip()}
        if required_grants and not required_grants.issubset(parent_grants):
            return DelegationDecision(
                strategy=BLOCKED,
                task_id=task.task_id,
                goal_id=plan.goal_id,
                reason="PARENT_PERMISSION_ENVELOPE_INCOMPLETE",
                value_reasons=request.value_reasons,
                plan_hash=decision_plan_hash,
                plan_revision=plan.plan_revision,
                requested_execution_class=request.requested_execution_class,
                rationale={"required_permissions": sorted(required_grants), "parent_grants": sorted(parent_grants)},
            )
        child = request.child_permissions
        if child is None or not child.subset_of(request.parent_permissions, parent_scope=request.parent_scope, non_scope=task.non_scope):
            return DelegationDecision(
                strategy=BLOCKED,
                task_id=task.task_id,
                goal_id=plan.goal_id,
                reason="CHILD_PERMISSION_OR_SCOPE_NOT_SUBSET",
                value_reasons=request.value_reasons,
                plan_hash=decision_plan_hash,
                plan_revision=plan.plan_revision,
                requested_execution_class=request.requested_execution_class,
                rationale={"child_delegation_allowed": False},
            )
        high_risk_grants = {"WRITE", "MUTATE", "DELETE", "NETWORK", "EGRESS", "SECRET_ACCESS", "RELEASE", "DEPLOY", "DELEGATE"}
        if (set(child.grants) & high_risk_grants) - required_grants:
            return DelegationDecision(
                strategy=BLOCKED,
                task_id=task.task_id,
                goal_id=plan.goal_id,
                reason="CHILD_PERMISSION_NOT_REQUIRED_BY_TASK",
                value_reasons=request.value_reasons,
                plan_hash=decision_plan_hash,
                plan_revision=plan.plan_revision,
                requested_execution_class=request.requested_execution_class,
                rationale={"child_grants": list(child.grants), "task_permission_needs": list(task.permission_needs)},
            )
        if child.allow_mutation and request.owner_gate is None:
            return DelegationDecision(
                strategy=BLOCKED,
                task_id=task.task_id,
                goal_id=plan.goal_id,
                reason="OWNER_GATE_UNRESOLVED",
                value_reasons=request.value_reasons,
                plan_hash=decision_plan_hash,
                plan_revision=plan.plan_revision,
                requested_execution_class=request.requested_execution_class,
                rationale={"mutation": True, "owner_gate": "MISSING"},
            )
        if child.allow_network:
            return DelegationDecision(
                strategy=BLOCKED,
                task_id=task.task_id,
                goal_id=plan.goal_id,
                reason="NETWORK_UNSUPPORTED",
                value_reasons=request.value_reasons,
                plan_hash=decision_plan_hash,
                plan_revision=plan.plan_revision,
                requested_execution_class=request.requested_execution_class,
                rationale={"network": False},
            )
        if not request.host_child_available:
            return DelegationDecision(
                strategy=BLOCKED,
                task_id=task.task_id,
                goal_id=plan.goal_id,
                reason="DELEGATED_EXECUTION_UNAVAILABLE",
                value_reasons=request.value_reasons,
                plan_hash=decision_plan_hash,
                plan_revision=plan.plan_revision,
                requested_execution_class=request.requested_execution_class,
                rationale={"host_child_surface": "UNAVAILABLE", "simulated_child": False},
            )
        if request.identity_required and request.observed_identity == UNKNOWN_IDENTITY:
            return DelegationDecision(
                strategy=BLOCKED,
                task_id=task.task_id,
                goal_id=plan.goal_id,
                reason="IDENTITY_REQUIRED_BUT_UNVERIFIED",
                value_reasons=request.value_reasons,
                plan_hash=decision_plan_hash,
                plan_revision=plan.plan_revision,
                requested_execution_class=request.requested_execution_class,
                rationale={"identity_required": True, "observed_identity": UNKNOWN_IDENTITY},
            )
        return DelegationDecision(
            strategy=DELEGATE,
            task_id=task.task_id,
            goal_id=plan.goal_id,
            reason="MATERIAL_DELEGATION_VALUE_WITHIN_BOUNDARY",
            value_reasons=request.value_reasons,
                plan_hash=decision_plan_hash,
            plan_revision=plan.plan_revision,
            requested_execution_class=request.requested_execution_class,
            rationale={
                "task_size": request.task_size,
                "material_value": True,
                "host_child_surface": "SUPPORTED",
                "handoff_overhead": "BOUNDED",
                "max_children": MAX_DELEGATED_CHILDREN,
                "max_depth": MAX_DELEGATION_DEPTH,
                "child_delegation_allowed": False,
                "identity_required": request.identity_required,
                "observed_identity": request.observed_identity,
            },
        )

    def _record_decision_trace(self, task: TaskRecord, decision: DelegationDecision, *, artifact_refs: Iterable[str] = ()) -> str:
        """Record material C15 rationale in the existing Execution Ledger."""

        decision_payload = decision.to_dict()
        decision_identity = dict(decision_payload)
        decision_identity.pop("decided_at", None)
        decision_id = f"D-C15-{_sha256(decision_identity)[:20]}"
        try:
            trace = make_trace(
                decision_id=decision_id,
                goal_id=task.goal_id,
                decision_type="GOVERNANCE",
                status="RECORDED",
                outcome=f"{decision.strategy}:{decision.reason}",
                decision_basis={
                    "summary": f"C15 selected {decision.strategy} before any execution-class or profile resolution.",
                    "selection_rule": decision.reason,
                    "task_characteristics": {
                        "task_id": task.task_id,
                        "value_reasons": list(decision.value_reasons),
                        "plan_revision": decision.plan_revision,
                    },
                    "rationale": decision.rationale,
                    "identity_is_not_inferred": True,
                },
                source_refs=(".p2p/state/task-state.json", ".p2p/state/execution-ledger.jsonl"),
                constraint_refs=("C15/strategy-before-profile", "C15/one-child-depth-one"),
                artifact_refs=tuple(artifact_refs),
            )
            append_trace(self.root, trace)
        except DecisionTraceError as exc:
            raise DelegationControlPlaneError(f"DECISION_TRACE_WRITE_FAILED:{exc}") from exc
        return decision_id

    def decide(self, request: DelegationRequest | None = None, *, task_id: str | None = None, **kwargs: Any) -> dict[str, Any]:
        """Return DIRECT/DELEGATE/BLOCKED before any host/model selection."""

        try:
            plan, task, preflight, normalized = self._resolve_request(task_id, request, kwargs)
            decision = self._decision_from_request(plan, task, preflight, normalized)
            result = decision.to_dict()
            result["decision_trace_ref"] = self._record_decision_trace(task, decision)
            return result
        except (BoundedDelegationError, ForegroundExecutionError) as exc:
            return self._result("CONTROL_PLANE_ERROR", strategy=BLOCKED, task_id=task_id or (request.task.task_id if request else None), reason=str(exc))
        except Exception as exc:
            return self._result("CONTROL_PLANE_ERROR", strategy=BLOCKED, task_id=task_id or (request.task.task_id if request else None), reason=f"CONTROLLER_FAILURE:{type(exc).__name__}")

    def _build_handoff(self, plan: TaskPlan, task: TaskRecord, request: DelegationRequest, decision: DelegationDecision) -> WorkerHandoff:
        if request.candidate_fingerprint is None:
            raise DelegationControlPlaneError("CANDIDATE_STATE_UNKNOWN")
        child_permissions = request.child_permissions
        if child_permissions is None:
            raise DelegationPermissionError("CHILD_PERMISSION_ENVELOPE_REQUIRED")
        if not child_permissions.subset_of(request.parent_permissions, parent_scope=request.parent_scope, non_scope=task.non_scope):
            raise DelegationPermissionError("CHILD_PERMISSION_OR_SCOPE_NOT_SUBSET")
        context_manifest = self._context_manifest(task, request)
        project_fingerprint = _sha256({"project_binding": request.project_binding, "candidate_fingerprint": request.candidate_fingerprint})
        plan_contract_fingerprint = _plan_contract_fingerprint(plan, task)
        handoff = WorkerHandoff.create(
            handoff_id=_new_handoff_id(),
            task=task,
            plan_hash=plan_contract_fingerprint,
            plan_revision=plan.plan_revision,
            context_manifest=context_manifest,
            dependency_outcomes=self._dependency_outcomes(plan, task, request.dependency_outcomes),
            decision_refs=tuple(dict.fromkeys((*task.decision_refs, *request.relevant_decisions))),
            candidate_fingerprint=request.candidate_fingerprint,
            project_fingerprint=project_fingerprint,
            permissions=child_permissions,
            scope=request.child_scope,
            budget=request.budget,
            requested_execution_class=request.requested_execution_class,
            identity_required=request.identity_required,
            required_identity=request.required_identity,
            known_risks=request.known_risks,
            unknowns=request.unknowns,
        )
        if decision.strategy != DELEGATE:
            raise DelegationContractError("HANDOFF_REQUIRES_DELEGATE_DECISION")
        return handoff

    def _artifact_dir(self, handoff_id: str) -> Path:
        if not _HANDOFF_ID_RE.fullmatch(handoff_id):
            raise DelegationContractError("HANDOFF_ID_INVALID")
        directory = self.root / DELEGATION_STATE_RELATIVE_ROOT / handoff_id
        try:
            directory.resolve().relative_to(self.root.resolve())
        except ValueError as exc:
            raise DelegationScopeError("HANDOFF_ARTIFACT_OUTSIDE_PROJECT") from exc
        return directory

    @staticmethod
    def _write_json(path: Path, value: Mapping[str, Any]) -> str:
        safe = _safe_json(value, path="artifact")
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(path.name + ".tmp")
        try:
            temporary.write_text(json.dumps(safe, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            temporary.replace(path)
        except OSError as exc:
            raise DelegationControlPlaneError(f"DELEGATION_ARTIFACT_WRITE_FAILED:{exc}") from exc
        return path.relative_to(path.parents[4]).as_posix() if len(path.parents) > 4 else path.as_posix()

    def _persist_handoff(self, handoff: WorkerHandoff) -> str:
        directory = self._artifact_dir(handoff.handoff_id)
        path = directory / "handoff.json"
        self._write_json(path, handoff.to_dict())
        return path.relative_to(self.root).as_posix()

    def _persist_result(self, handoff: WorkerHandoff, result: DelegatedWorkerResult, attempt: int) -> str:
        directory = self._artifact_dir(handoff.handoff_id) / "results"
        path = directory / f"attempt-{attempt:03d}.json"
        self._write_json(path, result.to_dict())
        return path.relative_to(self.root).as_posix()

    def _persist_verification(self, handoff: WorkerHandoff, value: Mapping[str, Any]) -> str:
        path = self._artifact_dir(handoff.handoff_id) / "verification.json"
        self._write_json(path, value)
        return path.relative_to(self.root).as_posix()

    def _checkpoint(self, task_id: str, handoff: WorkerHandoff, *, classification: str, next_step: str, pending: Sequence[str], notes: str) -> str:
        checkpoint_ref = f"{DELEGATION_STATE_RELATIVE_ROOT}/{handoff.handoff_id}/checkpoint.json"
        checkpoint = {
            "checkpoint_ref": checkpoint_ref,
            "state_fingerprint": handoff.fingerprint,
            "recovery_classification": classification,
            "next_safe_step": next_step,
            "completed_refs": [f"{DELEGATION_STATE_RELATIVE_ROOT}/{handoff.handoff_id}/handoff.json"],
            "pending_refs": list(pending),
            "evidence_fingerprints": {},
            "captured_at": _now(),
            "notes": notes,
        }
        try:
            self.store.checkpoint(task_id, checkpoint, now=checkpoint["captured_at"])
        except TaskStateError as exc:
            raise DelegationControlPlaneError(str(exc)) from exc
        self._write_json(self.root / checkpoint_ref, checkpoint)
        return checkpoint_ref

    def _task_contract_matches(self, handoff: WorkerHandoff) -> bool:
        try:
            plan = self._control_plane()
            task = plan.tasks.get(handoff.task_id)
        except BoundedDelegationError:
            return False
        if task is None or task.goal_id != handoff.goal_id or plan.plan_revision != handoff.plan_revision:
            return False
        return (
            task.purpose == handoff.task_purpose
            and scope_is_subset(handoff.scope, task.scope, task.non_scope)
            and tuple(task.acceptance_requirements) == tuple(handoff.acceptance_requirements)
        )

    def _validate_result(self, handoff: WorkerHandoff, result: DelegatedWorkerResult) -> None:
        if result.handoff_id != handoff.handoff_id or result.task_id != handoff.task_id:
            raise DelegationControlPlaneError("CHILD_RESULT_HANDOFF_BINDING_MISMATCH")
        if result.candidate_fingerprint != handoff.candidate_fingerprint:
            raise DelegationStaleError("CHILD_RESULT_CANDIDATE_BINDING_STALE")
        if result.depth != MAX_DELEGATION_DEPTH or result.child_delegation_allowed:
            raise DelegationPermissionError("CHILD_DELEGATION_FORBIDDEN")
        if result.actions_used > handoff.budget.max_actions:
            raise DelegationControlPlaneError("CHILD_ACTION_BUDGET_EXCEEDED")
        if result.output_bytes > handoff.budget.max_output_bytes:
            raise DelegationControlPlaneError("CHILD_OUTPUT_BUDGET_EXCEEDED")
        if result.mutation_state == "UNKNOWN" or (result.mutation_performed and result.outcome != "SUCCEEDED"):
            return
        for reference in result.artifact_refs:
            if not scope_is_subset((reference,), handoff.scope, handoff.non_scope):
                raise DelegationScopeError("CHILD_ARTIFACT_OUTSIDE_SCOPE")
        if handoff.identity_required:
            if result.observed_identity == UNKNOWN_IDENTITY:
                raise DelegationControlPlaneError("IDENTITY_REQUIRED_BUT_UNVERIFIED")
            if result.observed_identity != handoff.required_identity:
                raise DelegationControlPlaneError("IDENTITY_REQUIRED_MISMATCH")
            if result.identity_authority in {"", "UNKNOWN", "NONE"}:
                raise DelegationControlPlaneError("IDENTITY_AUTHORITY_REQUIRED")

    @staticmethod
    def _is_boundary_failure(result: DelegatedWorkerResult) -> bool:
        summary = result.summary.upper()
        return any(marker in summary for marker in BOUNDARY_FAILURE_MARKERS)

    def _safe_direct_fallback(
        self,
        *,
        handoff: WorkerHandoff,
        request: DelegationRequest,
        child_result: DelegatedWorkerResult,
        direct_action: Callable[..., Any] | None,
        direct_verify: Callable[..., Any] | None,
    ) -> dict[str, Any] | None:
        if direct_action is None or direct_verify is None:
            return None
        if not request.allow_direct_fallback:
            return None
        if child_result.outcome != "FAILED" or child_result.mutation_state != "KNOWN_NONE" or child_result.mutation_performed:
            return None
        if self._is_boundary_failure(child_result):
            return None
        try:
            self.store.transition(
                handoff.task_id,
                "BLOCKED",
                blocker={"reason": "DELEGATED_CHILD_FAILED_NO_MUTATION", "refs": [f"{DELEGATION_STATE_RELATIVE_ROOT}/{handoff.handoff_id}/handoff.json"]},
            )
            self.store.transition(handoff.task_id, "READY")
        except TaskStateError as exc:
            raise DelegationControlPlaneError(f"DIRECT_FALLBACK_REOPEN_FAILED:{exc}") from exc
        direct_result = ForegroundExecutionController(self.root).execute(
            direct_action,
            direct_verify,
            task_id=handoff.task_id,
            action_name="safe_direct_fallback",
            budget=handoff.budget.to_foreground_budget(),
            owner_gate=request.owner_gate,
            capability_readiness=request.capability_readiness,
            permission_state=request.permission_state,
            context_state=request.context_state,
        )
        return self._result(
            str(direct_result.get("status", "CONTROL_PLANE_ERROR")),
            strategy=DIRECT,
            task_id=handoff.task_id,
            reason="SAFE_DIRECT_FALLBACK_AFTER_KNOWN_NO_MUTATION",
            direct_fallback=True,
            delegated_child_result=child_result.to_dict(),
            direct_result=direct_result,
        )

    def execute(
        self,
        request: DelegationRequest | None = None,
        *,
        task_id: str | None = None,
        child_executor: Callable[..., Any] | None = None,
        verify: Callable[..., Any] | None = None,
        direct_action: Callable[..., Any] | None = None,
        direct_verify: Callable[..., Any] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Execute one direct path or one real callback-backed child path."""

        try:
            execute_overrides = dict(kwargs)
            if callable(child_executor):
                execute_overrides["host_child_available"] = True
            plan, task, preflight, normalized = self._resolve_request(task_id, request, execute_overrides)
            decision = self._decision_from_request(plan, task, preflight, normalized)
            decision_payload = decision.to_dict()
            decision_trace_ref = self._record_decision_trace(task, decision)
            decision_payload["decision_trace_ref"] = decision_trace_ref
            normalized = replace(normalized, relevant_decisions=tuple(dict.fromkeys((*normalized.relevant_decisions, decision_trace_ref))))
            if decision.strategy == BLOCKED:
                return self._result("BLOCKED", strategy=BLOCKED, task_id=task.task_id, reason=decision.reason, decision=decision_payload, task_status=task.status, preflight=preflight)
            if decision.strategy == DIRECT:
                if direct_action is None:
                    return self._result("DIRECT", strategy=DIRECT, task_id=task.task_id, reason=decision.reason, decision=decision_payload, task_status=task.status)
                direct_result = ForegroundExecutionController(self.root).execute(
                    direct_action,
                    direct_verify,
                    task_id=task.task_id,
                    action_name="direct_first_class_path",
                    verification_plan={"strategy_decision": DIRECT, "decision_reason": decision.reason},
                    owner_gate=normalized.owner_gate,
                    capability_readiness=normalized.capability_readiness,
                    permission_state=normalized.permission_state,
                    context_state=normalized.context_state,
                )
                return self._result(
                    str(direct_result.get("status", "CONTROL_PLANE_ERROR")),
                    strategy=DIRECT,
                    task_id=task.task_id,
                    reason=decision.reason,
                    decision=decision_payload,
                    direct_result=direct_result,
                )
            if not callable(child_executor):
                return self._result("BLOCKED", strategy=BLOCKED, task_id=task.task_id, reason="DELEGATED_EXECUTION_UNAVAILABLE", decision=decision_payload)
            if self._live_children >= MAX_DELEGATED_CHILDREN:
                return self._result("BLOCKED", strategy=BLOCKED, task_id=task.task_id, reason="MAX_LIVE_CHILDREN_REACHED", decision=decision_payload)
            try:
                active_plan = self.store.transition(task.task_id, "ACTIVE", preflight=preflight)
            except TaskStateError as exc:
                raise DelegationControlPlaneError(str(exc)) from exc
            active_task = active_plan.tasks[task.task_id]
            handoff = self._build_handoff(active_plan, active_task, normalized, decision)
            handoff_ref = self._persist_handoff(handoff)
            self._checkpoint(
                task.task_id,
                handoff,
                classification="SAFE_TO_RESUME",
                next_step="Await the one foreground child result, then independently verify current state.",
                pending=(f"{DELEGATION_STATE_RELATIVE_ROOT}/{handoff.handoff_id}/results", "INDEPENDENT_VERIFICATION"),
                notes="C15 handoff persisted; the child is foreground-bound and may not delegate.",
            )
            self._live_children += 1
            try:
                started = time.monotonic()
                last_result: DelegatedWorkerResult | None = None
                for attempt in range(1, normalized.budget.max_attempts + 1):
                    context = {
                        "handoff_id": handoff.handoff_id,
                        "depth": MAX_DELEGATION_DEPTH,
                        "child_count": 1,
                        "child_delegation_allowed": False,
                        "budget": normalized.budget.to_dict(),
                        "permissions": handoff.permissions.to_dict(),
                    }
                    try:
                        raw = _invoke(child_executor, handoff.to_dict(), context, allow_second=True)
                        raw_size = len(json.dumps(raw, ensure_ascii=False, sort_keys=True).encode("utf-8"))
                        if time.monotonic() - started > normalized.budget.max_wall_clock_seconds:
                            raise DelegationControlPlaneError("CHILD_WALL_CLOCK_BUDGET_EXCEEDED")
                        if isinstance(raw, DelegatedWorkerResult):
                            child_result = raw
                        else:
                            if not isinstance(raw, Mapping):
                                raise DelegationControlPlaneError("CHILD_RESULT_MUST_BE_OBJECT")
                            raw = dict(raw)
                            raw.setdefault("output_bytes", raw_size)
                            child_result = DelegatedWorkerResult.from_mapping(raw, handoff)
                        if child_result.output_bytes == 0:
                            child_result = replace(child_result, output_bytes=raw_size)
                        self._validate_result(handoff, child_result)
                    except DelegationStaleError:
                        raise
                    except (BoundedDelegationError, ForegroundExecutionError) as exc:
                        raise DelegationControlPlaneError(str(exc)) from exc
                    except Exception as exc:
                        raise DelegationControlPlaneError(f"CHILD_EXECUTION_CONTROL_PLANE:{type(exc).__name__}") from exc
                    result_ref = self._persist_result(handoff, child_result, attempt)
                    last_result = child_result
                    if child_result.mutation_state == "UNKNOWN":
                        checkpoint_ref = self._checkpoint(
                            task.task_id,
                            handoff,
                            classification="UNKNOWN",
                            next_step="Recheck current candidate state before any further execution.",
                            pending=("INDEPENDENT_VERIFICATION",),
                            notes="The child may have mutated state but authoritative binding is uncertain; direct fallback is forbidden.",
                        )
                        return self._result("UNKNOWN", strategy=DELEGATE, task_id=task.task_id, reason="UNCERTAIN_PARTIAL_MUTATION", decision=decision_payload, handoff=handoff.to_dict(), handoff_ref=handoff_ref, child_result=child_result.to_dict(), result_ref=result_ref, checkpoint_ref=checkpoint_ref)
                    if child_result.outcome in {"INTERRUPTED", "BLOCKED"} and child_result.mutation_performed:
                        checkpoint_ref = self._checkpoint(
                            task.task_id,
                            handoff,
                            classification="NEEDS_RECHECK",
                            next_step="Read current scoped artifacts before deciding completion.",
                            pending=("INDEPENDENT_VERIFICATION",),
                            notes="The child stopped after a material mutation; task remains non-DONE.",
                        )
                        return self._result("NEEDS_RECHECK", strategy=DELEGATE, task_id=task.task_id, reason="PARTIAL_MUTATION_REQUIRES_RECHECK", decision=decision_payload, handoff=handoff.to_dict(), handoff_ref=handoff_ref, child_result=child_result.to_dict(), result_ref=result_ref, checkpoint_ref=checkpoint_ref)
                    if child_result.outcome == "SUCCEEDED":
                        if not self._task_contract_matches(handoff):
                            raise DelegationStaleError("HANDOFF_TASK_CONTRACT_STALE")
                        if verify is None:
                            checkpoint_ref = self._checkpoint(
                                task.task_id,
                                handoff,
                                classification="NEEDS_RECHECK",
                                next_step="Run an independent parent verifier against current candidate state.",
                                pending=("INDEPENDENT_VERIFICATION",),
                                notes="Child output is a proposal and cannot establish completion.",
                            )
                            return self._result("NEEDS_RECHECK", strategy=DELEGATE, task_id=task.task_id, reason="INDEPENDENT_VERIFIER_REQUIRED", decision=decision_payload, handoff=handoff.to_dict(), handoff_ref=handoff_ref, child_result=child_result.to_dict(), result_ref=result_ref, checkpoint_ref=checkpoint_ref)
                        try:
                            verification_raw = _invoke(verify, child_result.to_dict(), handoff.to_dict(), allow_second=True)
                            verification_status, claims, candidate_state, verification_summary = _coerce_verification(verification_raw)
                        except Exception as exc:
                            verification_status, claims, candidate_state, verification_summary = "FAILED", (), None, f"PARENT_VERIFIER_FAILED:{type(exc).__name__}"
                        verification_payload = {
                            "schema": "p2p-parent-verification/1",
                            "status": verification_status,
                            "summary": verification_summary,
                            "evidence_claims": [item.as_contract() if isinstance(item, EvidenceClaim) else dict(item) for item in claims],
                            "candidate_state": {
                                "candidate_fingerprint": handoff.candidate_fingerprint,
                                "projection": "FINGERPRINT_ONLY",
                            },
                            "independent_check": True,
                            "worker_output_is_proposal": True,
                        }
                        verification_ref = self._persist_verification(handoff, verification_payload)
                        if verification_status not in {"VERIFIED", "DONE"} or not claims:
                            checkpoint_ref = self._checkpoint(
                                task.task_id,
                                handoff,
                                classification="NEEDS_RECHECK",
                                next_step="Resolve failed independent verification before another explicit task attempt.",
                                pending=("INDEPENDENT_VERIFICATION",),
                                notes="Parent verification did not establish current evidence; worker self-checks were not accepted.",
                            )
                            return self._result("VERIFICATION_FAILED", strategy=DELEGATE, task_id=task.task_id, reason=verification_summary or "CURRENT_EVIDENCE_REQUIRED", decision=decision_payload, handoff=handoff.to_dict(), handoff_ref=handoff_ref, child_result=child_result.to_dict(), result_ref=result_ref, verification_ref=verification_ref, checkpoint_ref=checkpoint_ref)
                        if not _candidate_binding_matches(candidate_state, handoff.candidate_fingerprint):
                            checkpoint_ref = self._checkpoint(
                                task.task_id,
                                handoff,
                                classification="NEEDS_RECHECK",
                                next_step="Rebind the parent verifier to the current candidate fingerprint.",
                                pending=("INDEPENDENT_VERIFICATION",),
                                notes="Verification did not bind to the handoff candidate; DONE is forbidden.",
                            )
                            return self._result("STALE_HANDOFF", strategy=DELEGATE, task_id=task.task_id, reason="VERIFICATION_CANDIDATE_BINDING_MISMATCH", decision=decision_payload, handoff=handoff.to_dict(), handoff_ref=handoff_ref, child_result=child_result.to_dict(), result_ref=result_ref, verification_ref=verification_ref, checkpoint_ref=checkpoint_ref)
                        try:
                            completed = self.store.complete(task.task_id, claims, candidate_state)
                        except TaskStateError as exc:
                            return self._result("VERIFICATION_FAILED", strategy=DELEGATE, task_id=task.task_id, reason=f"EVIDENCE_NOT_ACCEPTED:{exc}", decision=decision_payload, handoff=handoff.to_dict(), handoff_ref=handoff_ref, child_result=child_result.to_dict(), result_ref=result_ref, verification_ref=verification_ref)
                        evidence_refs: list[str] = []
                        for claim in claims:
                            actual = claim.actual_evidence if isinstance(claim, EvidenceClaim) else claim.get("actual_evidence", ()) if isinstance(claim, Mapping) else ()
                            for item in actual if isinstance(actual, (list, tuple)) else ():
                                if isinstance(item, Mapping):
                                    ref = str(item.get("evidence_ref") or item.get("source") or "").strip()
                                    if ref and ref not in evidence_refs:
                                        evidence_refs.append(ref)
                        return self._result("DONE", strategy=DELEGATE, task_id=task.task_id, reason="CURRENT_EVIDENCE_VERIFIED", decision=decision_payload, handoff=handoff.to_dict(), handoff_ref=handoff_ref, child_result=child_result.to_dict(), result_ref=result_ref, verification_ref=verification_ref, evidence_refs=evidence_refs, plan_hash=completed.canonical_hash(), task_status="DONE")
                    if child_result.retryable and not self._is_boundary_failure(child_result) and not child_result.mutation_performed and attempt < normalized.budget.max_attempts and attempt <= normalized.budget.max_retries + 1:
                        continue
                    fallback = self._safe_direct_fallback(
                        handoff=handoff,
                        request=normalized,
                        child_result=child_result,
                        direct_action=direct_action,
                        direct_verify=direct_verify,
                    )
                    if fallback is not None:
                        fallback["decision"] = decision_payload
                        fallback["handoff_ref"] = handoff_ref
                        fallback["result_ref"] = result_ref
                        return fallback
                    checkpoint_ref = self._checkpoint(
                        task.task_id,
                        handoff,
                        classification="BLOCKED",
                        next_step="Resolve the child failure before another explicit foreground attempt.",
                        pending=("DELEGATION_REVIEW",),
                        notes="No safe verified completion was established; no background retry was started.",
                    )
                    return self._result("FAILED", strategy=DELEGATE, task_id=task.task_id, reason=child_result.summary or "CHILD_FAILED", decision=decision_payload, handoff=handoff.to_dict(), handoff_ref=handoff_ref, child_result=child_result.to_dict(), result_ref=result_ref, checkpoint_ref=checkpoint_ref, task_status="ACTIVE")
                return self._result("FAILED", strategy=DELEGATE, task_id=task.task_id, reason="CHILD_ATTEMPTS_EXHAUSTED", decision=decision_payload, handoff=handoff.to_dict(), handoff_ref=handoff_ref, child_result=last_result.to_dict() if last_result else None)
            finally:
                self._live_children = max(0, self._live_children - 1)
        except DelegationStaleError as exc:
            return self._result("STALE_HANDOFF", strategy=DELEGATE, task_id=task_id or (request.task.task_id if request else None), reason=str(exc))
        except (BoundedDelegationError, ForegroundExecutionError) as exc:
            return self._result("CONTROL_PLANE_ERROR", strategy=BLOCKED, task_id=task_id or (request.task.task_id if request else None), reason=str(exc))
        except Exception as exc:
            return self._result("CONTROL_PLANE_ERROR", strategy=BLOCKED, task_id=task_id or (request.task.task_id if request else None), reason=f"CONTROLLER_FAILURE:{type(exc).__name__}")

    def request(self, task_id: str | None = None, **kwargs: Any) -> DelegationRequest:
        """Build a request from the current C11 candidate for internal callers."""

        try:
            _, task = self._select_base(task_id)
        except DelegationControlPlaneError as exc:
            if str(exc) != "NO_SAFE_READY_TASK":
                raise
            base_plan = self._control_plane()
            task = self._candidate(base_plan, task_id)
            if task is None:
                raise
        request = self._coerce_request(task, None, kwargs)
        self._prepare(task_id, request)
        return request


# Backwards/brief-friendly aliases.  They refer to the same one controller,
# not to additional routers or executors.
ForegroundDelegationController = BoundedDelegationController
WorkerHandoffController = BoundedDelegationController
Handoff = WorkerHandoff


__all__ = [
    "DELEGATION_SCHEMA",
    "HANDOFF_SCHEMA",
    "CHILD_RESULT_SCHEMA",
    "DELEGATION_RESULT_SCHEMA",
    "DELEGATION_STATE_RELATIVE_ROOT",
    "MAX_DELEGATION_DEPTH",
    "MAX_DELEGATED_CHILDREN",
    "UNKNOWN_IDENTITY",
    "HOST_DEFAULT_EXECUTION_CLASS",
    "HOST_EXECUTION_SOURCE",
    "HOST_ADAPTER_SCHEMA",
    "RAW_HOST_RECEIPT_KEY",
    "NORMALIZED_C15_RECEIPT_KEY",
    "DIRECT",
    "DELEGATE",
    "BLOCKED",
    "VALUE_REASONS",
    "PermissionEnvelope",
    "DelegationBudget",
    "DelegationRequest",
    "DelegationDecision",
    "WorkerHandoff",
    "Handoff",
    "DelegatedWorkerResult",
    "CodexHostAdapter",
    "ChildResult",
    "WorkerResult",
    "BoundedDelegationController",
    "ForegroundDelegationController",
    "WorkerHandoffController",
    "BoundedDelegationError",
    "DelegationContractError",
    "DelegationScopeError",
    "DelegationPermissionError",
    "DelegationControlPlaneError",
    "DelegationStaleError",
    "scope_is_subset",
]
