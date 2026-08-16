"""C17 bounded parallel foreground execution.

This module is a coordinator over the existing C11 task state and C15 child
surface.  It does not become a second executor, router, ledger, scheduler, or
worker pool.  A call selects at most two already-ready tasks, proves their
independence, starts two short-lived foreground callback bindings, waits for
both, and records the group beside the existing task ledger and C15 artifacts.
"""

from __future__ import annotations

from dataclasses import dataclass
import copy
import fnmatch
import hashlib
import inspect
import json
from pathlib import Path
import re
import threading
import time
from typing import Any, Callable, Iterable, Mapping, Sequence
import uuid

from .bounded_delegation import (
    BLOCKED,
    DELEGATE,
    DIRECT,
    DelegatedWorkerResult,
    DelegationRequest,
    BoundedDelegationController,
    BoundedDelegationError,
    DelegationControlPlaneError,
    PermissionEnvelope,
    UNKNOWN_IDENTITY,
    scope_is_subset,
)
from .task_state import TaskPlan, TaskRecord, TaskStateError, TaskStateStore


PARALLEL_SCHEMA = "p2p-bounded-parallel/1"
PARALLEL_RESULT_SCHEMA = "p2p-bounded-parallel-result/1"
PARALLEL_GROUP_RELATIVE_ROOT = ".p2p/state/foreground-executions/parallel-groups"
MAX_PARALLEL_CHILDREN = 2
MAX_PARALLEL_ATTEMPTS = 4
MAX_PARALLEL_ACTIONS = 32
MAX_PARALLEL_OUTPUT_BYTES = 32768
PARALLEL_LARGE_CONTEXT_BYTES = 65536
PARALLEL = "PARALLEL"
SEQUENTIAL = "SEQUENTIAL"
PARALLEL_BLOCKED = "BLOCKED"
GROUP_STATES = ("PLANNED", "RUNNING", "DONE", "PARTIAL", "BLOCKED", "UNKNOWN", "NEEDS_RECHECK", "CONTROL_PLANE_FAILURE")
COMBINED_VERIFICATION_STATES = ("VERIFIED", "NOT_REQUIRED_READ_ONLY", "FAILED", "NOT_RUN")

_GROUP_ID_RE = re.compile(r"^parallel-[a-f0-9]{16,64}$")
_SECRET_RE = re.compile(r"secret|token|password|credential|api[_-]?key|authorization|private[_-]?key", re.IGNORECASE)
_IDENTITY_RE = re.compile(r"^(?:agent|agent_id|agent_profile|model|model_id|provider|thread|thread_id|worker|worker_id|worker_profile)$", re.IGNORECASE)
_PATH_INVALID = re.compile(r"^(?:/|[a-zA-Z]:[\\/])")
_MUTATION_GRANTS = {"WRITE", "MUTATE", "DELETE"}
_UNSAFE_COMBINED_GRANTS = {"NETWORK", "EGRESS", "SECRET_ACCESS", "RELEASE", "DEPLOY", "DELEGATE"}
_SAFE_STRUCTURAL_KEYS = {"allow_secret_access", "allow_network", "allow_egress", "allow_mutation", "allow_delete", "allow_release", "allow_deploy"}


class ParallelExecutionError(ValueError):
    """Base error for an invalid or unsafe C17 group contract."""


class ParallelControlPlaneError(ParallelExecutionError):
    """Raised when durable group/task authority cannot be trusted."""


def _sha256(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _safe(value: Any, *, path: str = "value", depth: int = 0) -> Any:
    if depth > 8:
        raise ParallelExecutionError(f"{path}_TOO_DEEP")
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for key, child in value.items():
            name = str(key)
            if name not in _SAFE_STRUCTURAL_KEYS and (_SECRET_RE.search(name) or _IDENTITY_RE.fullmatch(name)):
                raise ParallelExecutionError(f"{path}.{name}_FORBIDDEN")
            result[name] = _safe(child, path=f"{path}.{name}", depth=depth + 1)
        return result
    if isinstance(value, (list, tuple)):
        if len(value) > 128:
            raise ParallelExecutionError(f"{path}_TOO_LARGE")
        return [_safe(item, path=f"{path}[{index}]", depth=depth + 1) for index, item in enumerate(value)]
    if isinstance(value, str):
        if len(value) > 8192 or _SECRET_RE.search(value):
            raise ParallelExecutionError(f"{path}_SECRET_LIKE")
        return value
    if value is None or isinstance(value, (bool, int, float)):
        return value
    raise ParallelExecutionError(f"{path}_TYPE_INVALID")


def _refs(values: Iterable[Any] | None, field_name: str) -> tuple[str, ...]:
    if values is None:
        return ()
    if isinstance(values, str):
        raise ParallelExecutionError(f"{field_name}_MUST_BE_LIST")
    result: list[str] = []
    seen: set[str] = set()
    for raw in values:
        if not isinstance(raw, str) or not raw.strip() or len(raw) > 1024:
            raise ParallelExecutionError(f"{field_name}_ITEM_INVALID")
        value = raw.strip().replace("\\", "/")
        if value in seen:
            raise ParallelExecutionError(f"{field_name}_DUPLICATE:{value}")
        seen.add(value)
        result.append(value)
    return tuple(result)


def _scope_ref(value: str, field_name: str) -> str:
    normalized = value.strip().replace("\\", "/")
    if not normalized or _PATH_INVALID.search(normalized) or any(part in {"", ".", ".."} for part in Path(normalized).parts):
        raise ParallelExecutionError(f"{field_name}_UNKNOWN_BOUNDARY")
    return normalized


def _overlap(left: str, right: str) -> bool:
    """Conservatively test whether two project-relative scopes may overlap."""

    a = left.casefold().rstrip("/")
    b = right.casefold().rstrip("/")
    if a == b:
        return True
    if any(token in a or token in b for token in ("*", "?", "[")):
        return True
    if a.startswith(b + "/") or b.startswith(a + "/"):
        return True
    return fnmatch.fnmatchcase(a, b) or fnmatch.fnmatchcase(b, a)


def _any_overlap(left: Iterable[str], right: Iterable[str]) -> bool:
    return any(_overlap(a, b) for a in left for b in right)


def _reachable(plan: TaskPlan, start: str, target: str, seen: set[str] | None = None) -> bool:
    visited = seen or set()
    if start in visited:
        return False
    visited.add(start)
    task = plan.tasks.get(start)
    if task is None:
        raise ParallelControlPlaneError(f"TASK_NOT_FOUND:{start}")
    if target in task.dependencies:
        return True
    return any(_reachable(plan, dependency, target, visited) for dependency in task.dependencies)


def _status(value: Any) -> str:
    return str(value or "").strip().upper()


def _call(callback: Callable[..., Any], first: Any, second: Any = None) -> Any:
    try:
        parameters = inspect.signature(callback).parameters.values()
        positional = [item for item in parameters if item.kind in {item.POSITIONAL_ONLY, item.POSITIONAL_OR_KEYWORD}]
        accepts_varargs = any(item.kind == item.VAR_POSITIONAL for item in parameters)
    except (TypeError, ValueError):
        positional = [None, None]
        accepts_varargs = True
    if accepts_varargs or len(positional) >= 2:
        return callback(first, second)
    return callback(first)


@dataclass(frozen=True)
class ParallelTaskContract:
    """Explicit C17 resource declaration for one existing task."""

    task_id: str
    read_scopes: tuple[str, ...] = ()
    write_scopes: tuple[str, ...] = ()
    delete_scopes: tuple[str, ...] = ()
    shared_resources: tuple[str, ...] = ()
    priority: int = 0

    def __post_init__(self) -> None:
        if not isinstance(self.task_id, str) or not self.task_id.strip():
            raise ParallelExecutionError("PARALLEL_TASK_ID_REQUIRED")
        for field_name in ("read_scopes", "write_scopes", "delete_scopes", "shared_resources"):
            values = tuple(_scope_ref(item, field_name) for item in _refs(getattr(self, field_name), field_name))
            object.__setattr__(self, field_name, values)
        if not isinstance(self.priority, int) or self.priority < -1000 or self.priority > 1000:
            raise ParallelExecutionError("PARALLEL_PRIORITY_INVALID")
        if not self.read_scopes and not self.write_scopes and not self.delete_scopes:
            raise ParallelExecutionError("PARALLEL_RESOURCE_BOUNDARY_REQUIRED")

    @classmethod
    def from_mapping(cls, task_id: str, value: Mapping[str, Any] | "ParallelTaskContract") -> "ParallelTaskContract":
        if isinstance(value, cls):
            if value.task_id != task_id:
                raise ParallelExecutionError("PARALLEL_CONTRACT_TASK_BINDING_MISMATCH")
            return value
        if not isinstance(value, Mapping):
            raise ParallelExecutionError("PARALLEL_CONTRACT_MUST_BE_OBJECT")
        return cls(
            task_id=task_id,
            read_scopes=tuple(value.get("read_scopes", ())),
            write_scopes=tuple(value.get("write_scopes", ())),
            delete_scopes=tuple(value.get("delete_scopes", ())),
            shared_resources=tuple(value.get("shared_resources", value.get("resources", ()))),
            priority=int(value.get("priority", 0)),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "read_scopes": list(self.read_scopes),
            "write_scopes": list(self.write_scopes),
            "delete_scopes": list(self.delete_scopes),
            "shared_resources": list(self.shared_resources),
            "priority": self.priority,
        }


@dataclass(frozen=True)
class ParallelEconomyProfile:
    """Bounded quality-adjusted signals for one parallel candidate.

    These are decision signals, not a cost model.  ``context_bytes`` is an
    explicitly labelled local serialization proxy when supplied by the
    caller; the controller never turns it into a token, price, or time claim.
    """

    expected_work_units: int = 4
    handoff_units: int = 1
    verification_units: int = 1
    context_bytes: int = 0
    context_fingerprints: tuple[str, ...] = ()
    context_proxy_label: str = "UNSPECIFIED"
    context_status: str = "SUFFICIENT"
    result_context_dependency: bool = False
    owner_interruption_risk: bool = False
    material_evidence_delta: bool = False

    def __post_init__(self) -> None:
        for field_name in ("expected_work_units", "handoff_units", "verification_units"):
            value = getattr(self, field_name)
            minimum = 1 if field_name == "expected_work_units" else 0
            if type(value) is not int or value < minimum or value > 1024:
                raise ParallelExecutionError(f"PARALLEL_{field_name.upper()}_INVALID")
        if type(self.context_bytes) is not int or self.context_bytes < 0 or self.context_bytes > 16 * 1024 * 1024:
            raise ParallelExecutionError("PARALLEL_CONTEXT_BYTES_INVALID")
        fingerprints = _refs(self.context_fingerprints, "context_fingerprints")
        if any(not re.fullmatch(r"[0-9a-f]{64}", value) for value in fingerprints):
            raise ParallelExecutionError("PARALLEL_CONTEXT_FINGERPRINT_INVALID")
        object.__setattr__(self, "context_fingerprints", fingerprints)
        if self.context_proxy_label not in {"UNSPECIFIED", "LOCAL_SERIALIZATION_PROXY", "CONTEXT_POINTER"}:
            raise ParallelExecutionError("PARALLEL_CONTEXT_PROXY_LABEL_INVALID")
        if self.context_status not in {"SUFFICIENT", "CONTEXT_INSUFFICIENT", "UNKNOWN"}:
            raise ParallelExecutionError("PARALLEL_CONTEXT_STATUS_INVALID")
        for field_name in ("result_context_dependency", "owner_interruption_risk", "material_evidence_delta"):
            if type(getattr(self, field_name)) is not bool:
                raise ParallelExecutionError(f"PARALLEL_{field_name.upper()}_INVALID")

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any] | "ParallelEconomyProfile") -> "ParallelEconomyProfile":
        if isinstance(value, cls):
            return value
        if not isinstance(value, Mapping):
            raise ParallelExecutionError("PARALLEL_ECONOMY_PROFILE_MUST_BE_OBJECT")
        def integer(name: str, default: int) -> int:
            raw = value.get(name, default)
            if type(raw) is not int:
                raise ParallelExecutionError(f"PARALLEL_{name.upper()}_INVALID")
            return raw

        def boolean(name: str, default: bool) -> bool:
            raw = value.get(name, default)
            if type(raw) is not bool:
                raise ParallelExecutionError(f"PARALLEL_{name.upper()}_INVALID")
            return raw

        fingerprints = value.get("context_fingerprints", ())
        if not fingerprints and value.get("context_fingerprint") is not None:
            fingerprints = (value["context_fingerprint"],)
        return cls(
            expected_work_units=integer("expected_work_units", 4),
            handoff_units=integer("handoff_units", 1),
            verification_units=integer("verification_units", 1),
            context_bytes=integer("context_bytes", 0),
            context_fingerprints=tuple(fingerprints),
            context_proxy_label=str(value.get("context_proxy_label", "UNSPECIFIED")),
            context_status=str(value.get("context_status", "SUFFICIENT")).upper(),
            result_context_dependency=boolean("result_context_dependency", False),
            owner_interruption_risk=boolean("owner_interruption_risk", False),
            material_evidence_delta=boolean("material_evidence_delta", False),
        )

    @classmethod
    def for_request(cls, request: DelegationRequest) -> "ParallelEconomyProfile":
        work_units = {"TINY": 1, "SMALL": 2, "MODERATE": 4, "LARGE": 8}.get(str(request.task_size).upper(), 4)
        return cls(expected_work_units=work_units)

    def has_quality_value(self, request: DelegationRequest) -> bool:
        return self.material_evidence_delta or bool(tuple(request.value_reasons))

    def to_dict(self) -> dict[str, Any]:
        return {
            "expected_work_units": self.expected_work_units,
            "handoff_units": self.handoff_units,
            "verification_units": self.verification_units,
            "context_bytes": self.context_bytes,
            "context_fingerprints": list(self.context_fingerprints),
            "context_proxy_label": self.context_proxy_label,
            "context_status": self.context_status,
            "result_context_dependency": self.result_context_dependency,
            "owner_interruption_risk": self.owner_interruption_risk,
            "material_evidence_delta": self.material_evidence_delta,
        }


@dataclass(frozen=True)
class _Candidate:
    request: DelegationRequest
    contract: ParallelTaskContract
    decision: Mapping[str, Any]
    task: TaskRecord

    @property
    def task_id(self) -> str:
        return self.task.task_id

    @property
    def mutates(self) -> bool:
        permissions = self.request.child_permissions
        return bool(permissions and permissions.allow_mutation) or bool(set(self.task.permission_needs) & _MUTATION_GRANTS) or bool(self.contract.write_scopes or self.contract.delete_scopes)


class BoundedParallelForegroundController:
    """Choose and run one bounded foreground group of independent tasks."""

    def __init__(self, root: str | Path, *, protected_roots: Iterable[str | Path] = ()) -> None:
        self.store = TaskStateStore(root, protected_roots=protected_roots)
        self.root = self.store.root
        self._group_lock = threading.RLock()

    def _group_dir(self, group_id: str) -> Path:
        if not _GROUP_ID_RE.fullmatch(group_id):
            raise ParallelExecutionError("PARALLEL_GROUP_ID_INVALID")
        directory = self.root / PARALLEL_GROUP_RELATIVE_ROOT / group_id
        try:
            directory.resolve().relative_to(self.root.resolve())
        except ValueError as exc:
            raise ParallelExecutionError("PARALLEL_GROUP_OUTSIDE_PROJECT") from exc
        return directory

    def _write_json(self, path: Path, value: Mapping[str, Any]) -> str:
        safe = _safe(value, path="parallel_artifact")
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(path.name + ".tmp")
        try:
            temporary.write_text(json.dumps(safe, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            temporary.replace(path)
        except OSError as exc:
            raise ParallelControlPlaneError(f"PARALLEL_ARTIFACT_WRITE_FAILED:{exc}") from exc
        return path.relative_to(self.root).as_posix()

    def _write_group(self, record: Mapping[str, Any]) -> str:
        group_id = str(record.get("group_id", ""))
        return self._write_json(self._group_dir(group_id) / "group.json", record)

    def _control_plane(self) -> TaskPlan:
        try:
            plan = self.store.require()
            events = self.store.read_events()
        except TaskStateError as exc:
            raise ParallelControlPlaneError(str(exc)) from exc
        if events.get("status") == "PARTIAL":
            raise ParallelControlPlaneError("CONTROL_PLANE_TASK_LEDGER_PARTIAL")
        if events.get("status") == "NOT_INITIALIZED":
            raise ParallelControlPlaneError("CONTROL_PLANE_TASK_LEDGER_NOT_INITIALIZED")
        active = [task.task_id for task in plan.tasks.values() if task.status == "ACTIVE"]
        if active:
            raise ParallelControlPlaneError("CONTROL_PLANE_ACTIVE_TASK_PRESENT:" + ",".join(sorted(active)))
        refreshed = plan.refresh_ready()
        if refreshed.canonical_hash() != plan.canonical_hash():
            try:
                return self.store.save(refreshed, event_name="parallel_ready_recovery")
            except TaskStateError as exc:
                raise ParallelControlPlaneError(str(exc)) from exc
        return plan

    def recover_ready(self) -> tuple[TaskRecord, ...]:
        """Return only durable READY tasks; no task is created or speculated."""

        plan = self._control_plane()
        return tuple(task for task in plan.tasks.values() if task.status == "READY")

    @staticmethod
    def _contract_for(request: DelegationRequest, raw: Mapping[str, Any] | ParallelTaskContract | None) -> ParallelTaskContract:
        if raw is not None:
            contract = ParallelTaskContract.from_mapping(request.task.task_id, raw)
        else:
            read_scopes = request.read_scopes
            write_scopes = request.write_scopes
            delete_scopes = request.delete_scopes
            shared_resources = request.shared_resources
            if not read_scopes and not write_scopes and not delete_scopes:
                if request.child_permissions is not None and request.child_permissions.allow_mutation:
                    write_scopes = request.task.scope
                elif set(request.task.permission_needs) & _MUTATION_GRANTS:
                    write_scopes = request.task.scope
                else:
                    read_scopes = request.task.scope
            contract = ParallelTaskContract(
                task_id=request.task.task_id,
                read_scopes=tuple(read_scopes),
                write_scopes=tuple(write_scopes),
                delete_scopes=tuple(delete_scopes),
                shared_resources=tuple(shared_resources),
            )
        declared = (*contract.read_scopes, *contract.write_scopes, *contract.delete_scopes)
        try:
            if not scope_is_subset(declared, request.child_scope, request.task.non_scope):
                raise ParallelExecutionError("PARALLEL_SCOPE_NOT_SUBSET_OF_CHILD_SCOPE")
        except BoundedDelegationError as exc:
            raise ParallelExecutionError(str(exc)) from exc
        if contract.delete_scopes and not contract.write_scopes:
            contract = ParallelTaskContract(
                task_id=contract.task_id,
                read_scopes=contract.read_scopes,
                write_scopes=contract.delete_scopes,
                delete_scopes=contract.delete_scopes,
                shared_resources=contract.shared_resources,
                priority=contract.priority,
            )
        return contract

    @staticmethod
    def _economy_profiles(
        requests: Sequence[DelegationRequest],
        raw: Mapping[str, Mapping[str, Any] | ParallelEconomyProfile] | None,
    ) -> dict[str, ParallelEconomyProfile]:
        if raw is not None and not isinstance(raw, Mapping):
            raise ParallelExecutionError("PARALLEL_ECONOMY_PROFILES_MUST_BE_OBJECT")
        profiles: dict[str, ParallelEconomyProfile] = {}
        for request in requests:
            value = raw.get(request.task.task_id) if isinstance(raw, Mapping) else None
            profiles[request.task.task_id] = ParallelEconomyProfile.for_request(request) if value is None else ParallelEconomyProfile.from_mapping(value)
        return profiles

    @staticmethod
    def _economy_reasons(
        left: _Candidate,
        right: _Candidate,
        profiles: Mapping[str, ParallelEconomyProfile],
    ) -> list[str]:
        left_profile = profiles[left.task_id]
        right_profile = profiles[right.task_id]
        reasons: list[str] = []
        for profile in (left_profile, right_profile):
            if profile.context_status != "SUFFICIENT":
                reasons.append("CONTEXT_INSUFFICIENT" if profile.context_status == "CONTEXT_INSUFFICIENT" else "CONTEXT_STATUS_UNKNOWN")
        if left_profile.result_context_dependency or right_profile.result_context_dependency:
            reasons.append("RESULT_CONTEXT_DEPENDENCY")
        if (left_profile.owner_interruption_risk or right_profile.owner_interruption_risk) and not (
            left_profile.has_quality_value(left.request) or right_profile.has_quality_value(right.request)
        ):
            reasons.append("OWNER_INTERRUPTION_OVERHEAD")
        if set(left_profile.context_fingerprints) & set(right_profile.context_fingerprints) and min(
            left_profile.context_bytes, right_profile.context_bytes
        ) >= PARALLEL_LARGE_CONTEXT_BYTES:
            reasons.append("DUPLICATED_CONTEXT_OVERHEAD")
        work_units = left_profile.expected_work_units + right_profile.expected_work_units
        coordination_units = (
            left_profile.handoff_units
            + left_profile.verification_units
            + right_profile.handoff_units
            + right_profile.verification_units
        )
        if work_units <= coordination_units and not (
            left_profile.has_quality_value(left.request) or right_profile.has_quality_value(right.request)
        ):
            reasons.append("COORDINATION_OVERHEAD_NOT_JUSTIFIED")
        return sorted(set(reasons))

    @staticmethod
    def _pair_reasons(left: _Candidate, right: _Candidate, plan: TaskPlan) -> list[str]:
        reasons: list[str] = []
        if _reachable(plan, left.task_id, right.task_id) or _reachable(plan, right.task_id, left.task_id):
            reasons.append("DEPENDENCY_RELATION_PRESENT")
        if set(left.task.context_refs) & set(right.task.context_refs):
            reasons.append("CONTEXT_BINDINGS_NOT_ISOLATED")
        if set(left.contract.shared_resources) & set(right.contract.shared_resources):
            reasons.append("SHARED_RESOURCE_CONFLICT")
        if _any_overlap(left.contract.delete_scopes, (*right.contract.read_scopes, *right.contract.write_scopes, *right.contract.delete_scopes)):
            reasons.append("DELETE_SCOPE_CONFLICT")
        if _any_overlap(right.contract.delete_scopes, (*left.contract.read_scopes, *left.contract.write_scopes, *left.contract.delete_scopes)):
            reasons.append("DELETE_SCOPE_CONFLICT")
        if _any_overlap(left.contract.write_scopes, (*right.contract.read_scopes, *right.contract.write_scopes, *right.contract.delete_scopes)):
            reasons.append("LEFT_WRITE_SCOPE_CONFLICT")
        if _any_overlap(right.contract.write_scopes, (*left.contract.read_scopes, *left.contract.write_scopes, *left.contract.delete_scopes)):
            reasons.append("RIGHT_WRITE_SCOPE_CONFLICT")
        return sorted(set(reasons))

    @staticmethod
    def _aggregate_reasons(candidates: Sequence[_Candidate]) -> list[str]:
        reasons: list[str] = []
        attempts = sum(item.request.budget.max_attempts for item in candidates)
        actions = sum(item.request.budget.max_actions for item in candidates)
        output_bytes = sum(item.request.budget.max_output_bytes for item in candidates)
        if attempts > MAX_PARALLEL_ATTEMPTS:
            reasons.append("AGGREGATE_ATTEMPT_BUDGET_EXCEEDED")
        if actions > MAX_PARALLEL_ACTIONS:
            reasons.append("AGGREGATE_ACTION_BUDGET_EXCEEDED")
        if output_bytes > MAX_PARALLEL_OUTPUT_BYTES:
            reasons.append("AGGREGATE_OUTPUT_BUDGET_EXCEEDED")
        grants: set[str] = set()
        for candidate in candidates:
            permissions = candidate.request.child_permissions
            if permissions is None:
                reasons.append("CHILD_PERMISSION_ENVELOPE_MISSING")
                continue
            grants.update(permissions.grants)
            if set(permissions.grants) & _UNSAFE_COMBINED_GRANTS:
                reasons.append("AGGREGATE_UNSAFE_PERMISSION")
            if permissions.allow_network:
                reasons.append("NETWORK_UNSUPPORTED")
            if permissions.allow_secret_access:
                reasons.append("SECRET_ACCESS_UNSUPPORTED")
            if permissions.delegate_allowed:
                reasons.append("GRANDCHILD_FORBIDDEN")
        if "DELEGATE" in grants:
            reasons.append("GRANDCHILD_FORBIDDEN")
        return sorted(set(reasons))

    @staticmethod
    def _ordered_candidates(candidates: Sequence[_Candidate], plan: TaskPlan) -> list[_Candidate]:
        order = {task_id: index for index, task_id in enumerate(plan.topological_order())}
        return sorted(candidates, key=lambda item: (-getattr(item.contract, "priority", 0), order.get(item.task_id, 999), item.task_id))

    @staticmethod
    def _child_projection(value: Mapping[str, Any], *, started_at: str | None = None, finished_at: str | None = None) -> dict[str, Any]:
        child_result = value.get("child_result") if isinstance(value.get("child_result"), Mapping) else {}
        decision = value.get("decision") if isinstance(value.get("decision"), Mapping) else {}
        return {
            "status": str(value.get("status", "CONTROL_PLANE_FAILURE")),
            "strategy": str(value.get("strategy", BLOCKED)),
            "task_id": value.get("task_id"),
            "reason": str(value.get("reason", "")),
            "handoff_ref": value.get("handoff_ref"),
            "result_ref": value.get("result_ref"),
            "verification_ref": value.get("verification_ref"),
            "checkpoint_ref": value.get("checkpoint_ref"),
            "decision_trace_ref": decision.get("decision_trace_ref"),
            "mutation_state": child_result.get("mutation_state", "UNKNOWN" if value.get("status") in {"UNKNOWN", "CONTROL_PLANE_FAILURE"} else "KNOWN_NONE"),
            "task_status": value.get("task_status"),
            "output_is_evidence": False,
            "started_at": started_at,
            "finished_at": finished_at,
        }

    @staticmethod
    def _needs_cancellation(value: Mapping[str, Any]) -> bool:
        status = str(value.get("status", ""))
        child = value.get("child_result") if isinstance(value.get("child_result"), Mapping) else {}
        return status in {"UNKNOWN", "CONTROL_PLANE_ERROR", "NEEDS_RECHECK", "STALE_HANDOFF"} or child.get("mutation_state") == "UNKNOWN"

    def decide(
        self,
        requests: Sequence[DelegationRequest],
        *,
        task_contracts: Mapping[str, Mapping[str, Any] | ParallelTaskContract] | None = None,
        economy_profiles: Mapping[str, Mapping[str, Any] | ParallelEconomyProfile] | None = None,
    ) -> dict[str, Any]:
        """Decide PARALLEL/SEQUENTIAL/BLOCKED without starting either task."""

        try:
            if not isinstance(requests, (list, tuple)) or not requests:
                raise ParallelExecutionError("PARALLEL_REQUESTS_REQUIRED")
            if len(requests) > 64:
                raise ParallelExecutionError("PARALLEL_REQUESTS_TOO_LARGE")
            if len({request.task.task_id for request in requests}) != len(requests):
                raise ParallelExecutionError("PARALLEL_TASK_IDS_MUST_BE_UNIQUE")
            profiles = self._economy_profiles(requests, economy_profiles)
            plan = self._control_plane()
            candidates: list[_Candidate] = []
            child_decisions: dict[str, Mapping[str, Any]] = {}
            excluded: dict[str, str] = {}
            for request in requests:
                task = plan.tasks.get(request.task.task_id)
                if task is None:
                    excluded[request.task.task_id] = "TASK_NOT_FOUND"
                    continue
                if task.goal_id != plan.goal_id or request.task.goal_id != plan.goal_id:
                    excluded[task.task_id] = "TASK_GOAL_MISMATCH"
                    continue
                if task.dependencies and not plan.dependencies_are_done(task.task_id):
                    excluded[task.task_id] = "DEPENDENCY_NOT_DONE"
                    continue
                if task.status != "READY":
                    excluded[task.task_id] = f"TASK_NOT_READY:{task.status}"
                    continue
                contract = self._contract_for(request, (task_contracts or {}).get(task.task_id))
                controller = BoundedDelegationController(self.root)
                decision = controller.decide(request=request)
                child_decisions[task.task_id] = _safe(decision, path=f"child_decisions.{task.task_id}")
                if decision.get("strategy") not in {DELEGATE, DIRECT}:
                    excluded[task.task_id] = str(decision.get("reason", "C15_DECISION_BLOCKED"))
                    continue
                refreshed = self.store.require().tasks.get(task.task_id)
                if refreshed is None:
                    excluded[task.task_id] = "TASK_DISAPPEARED"
                    continue
                candidates.append(_Candidate(request=request, contract=contract, decision=decision, task=refreshed))

            ordered = self._ordered_candidates(candidates, plan)
            selected: list[_Candidate] = []
            pair_rejections: dict[str, list[str]] = {}
            for index, left in enumerate(ordered):
                for right in ordered[index + 1 :]:
                    pair = (left, right)
                    reasons = [
                        *self._pair_reasons(left, right, plan),
                        *self._aggregate_reasons(pair),
                        *self._economy_reasons(left, right, profiles),
                    ]
                    if reasons:
                        pair_rejections[f"{left.task_id}+{right.task_id}"] = sorted(set(reasons))
                        continue
                    selected = [left, right]
                    break
                if selected:
                    break

            if selected and all(item.decision.get("strategy") == DELEGATE for item in selected):
                strategy = PARALLEL
                strategy_reason = "TWO_READY_TASKS_INDEPENDENT_WITH_MATERIAL_VALUE"
            elif ordered:
                selected = ordered[:1]
                strategy = SEQUENTIAL
                strategy_reason = "PARALLEL_INDEPENDENCE_OR_VALUE_GATE_NOT_SATISFIED"
                if len(ordered) > 1 and pair_rejections:
                    strategy_reason = "PARALLEL_PAIR_REJECTED_SEQUENTIAL_DEFAULT"
                    if any(
                        reason.startswith(("CONTEXT_", "RESULT_CONTEXT_", "OWNER_", "DUPLICATED_CONTEXT_", "COORDINATION_"))
                        for reasons in pair_rejections.values()
                        for reason in reasons
                    ):
                        strategy_reason = "PARALLEL_ECONOMY_GATE_NOT_SATISFIED"
            else:
                strategy = PARALLEL_BLOCKED
                strategy_reason = "NO_SAFE_READY_TASK"

            return _safe(
                {
                    "schema": PARALLEL_SCHEMA,
                    "status": "PASS" if strategy != PARALLEL_BLOCKED else "BLOCKED",
                    "strategy": strategy,
                    "task_ids": [item.task_id for item in selected],
                    "excluded_task_ids": excluded,
                    "reason": strategy_reason,
                    "child_decisions": child_decisions,
                    "pair_rejections": pair_rejections,
                    "economy_profiles": {task_id: profiles[task_id].to_dict() for task_id in profiles},
                    "economy_gate": {
                        "mode": "QUALITY_ADJUSTED_BOUNDED_SIGNALS",
                        "large_context_threshold_bytes": PARALLEL_LARGE_CONTEXT_BYTES,
                        "context_measurement": "LOCAL_SERIALIZATION_PROXY_ONLY",
                        "raw_resource_minimization": False,
                    },
                    "resource_contracts": {item.task_id: item.contract.to_dict() for item in ordered},
                    "plan_hash": self.store.require().canonical_hash(),
                    "plan_revision": self.store.require().plan_revision,
                    "automatic_start": False,
                    "background_execution": False,
                    "process_survives_session": False,
                    "max_parallel_children": MAX_PARALLEL_CHILDREN,
                    "max_delegation_depth": 1,
                    "child_delegation_allowed": False,
                    "worker_output_is_evidence": False,
                    "parallel_execution": strategy == PARALLEL,
                },
                path="parallel.decision",
            )
        except (ParallelExecutionError, BoundedDelegationError, TaskStateError) as exc:
            return {
                "schema": PARALLEL_SCHEMA,
                "status": "BLOCKED",
                "strategy": PARALLEL_BLOCKED,
                "task_ids": [],
                "reason": str(exc),
                "automatic_start": False,
                "background_execution": False,
                "process_survives_session": False,
                "max_parallel_children": MAX_PARALLEL_CHILDREN,
                "worker_output_is_evidence": False,
            }

    def _callback(self, callbacks: Mapping[str, Callable[..., Any]] | Callable[..., Any] | None, task_id: str) -> Callable[..., Any] | None:
        if isinstance(callbacks, Mapping):
            value = callbacks.get(task_id)
            return value if callable(value) else None
        return callbacks if callable(callbacks) else None

    def _effective_requests(
        self,
        requests: Sequence[DelegationRequest],
        child_executors: Mapping[str, Callable[..., Any]] | Callable[..., Any] | None,
    ) -> tuple[DelegationRequest, ...]:
        has_supported_callback = callable(child_executors) or (isinstance(child_executors, Mapping) and all(callable(child_executors.get(request.task.task_id)) for request in requests))
        if not has_supported_callback:
            return tuple(requests)
        return tuple(request if request.host_child_available else request.__class__(**{**request.__dict__, "host_child_available": True}) for request in requests)

    def _new_group_record(self, decision: Mapping[str, Any], selected: Sequence[DelegationRequest], plan: TaskPlan) -> dict[str, Any]:
        group_id = f"parallel-{uuid.uuid4().hex}"
        children = {
            request.task.task_id: {
                "task_id": request.task.task_id,
                "status": "PLANNED",
                "handoff_ref": None,
                "result_ref": None,
                "verification_ref": None,
                "decision_trace_ref": decision.get("child_decisions", {}).get(request.task.task_id, {}).get("decision_trace_ref"),
                "output_is_evidence": False,
            }
            for request in selected
        }
        return {
            "schema": PARALLEL_SCHEMA,
            "group_id": group_id,
            "goal_id": plan.goal_id,
            "plan_hash": plan.canonical_hash(),
            "plan_revision": plan.plan_revision,
            "strategy": PARALLEL,
            "status": "PLANNED",
            "task_ids": [request.task.task_id for request in selected],
            "max_parallel_children": MAX_PARALLEL_CHILDREN,
            "max_delegation_depth": 1,
            "child_delegation_allowed": False,
            "automatic_start": False,
            "background_execution": False,
            "process_survives_session": False,
            "worker_output_is_evidence": False,
            "economy_profiles": decision.get("economy_profiles", {}),
            "economy_gate": decision.get("economy_gate", {}),
            "children": children,
            "cancellation": {"status": "NOT_REQUESTED", "requests": []},
            "combined_verification": {"status": "NOT_RUN"},
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }

    def _record_event(self, event_name: str, group: Mapping[str, Any], *, task_id: str | None = None, details: Mapping[str, Any] | None = None) -> None:
        payload = {"parallel_group_id": group.get("group_id"), "strategy": PARALLEL, **(details or {})}
        try:
            self.store.record_event(event_name, task_id=task_id, details=payload)
        except TaskStateError as exc:
            raise ParallelControlPlaneError(f"CONTROL_PLANE_EVENT_WRITE_FAILED:{exc}") from exc

    def _execute_sequential(
        self,
        decision: Mapping[str, Any],
        requests: Sequence[DelegationRequest],
        child_executors: Mapping[str, Callable[..., Any]] | Callable[..., Any] | None,
        verifiers: Mapping[str, Callable[..., Any]] | Callable[..., Any] | None,
        direct_actions: Mapping[str, Callable[..., Any]] | Callable[..., Any] | None,
        direct_verifiers: Mapping[str, Callable[..., Any]] | Callable[..., Any] | None,
    ) -> dict[str, Any]:
        selected = [request for request in requests if request.task.task_id in set(decision.get("task_ids", ()))]
        child_results: dict[str, Any] = {}
        for request in selected:
            task_id = request.task.task_id
            executor = self._callback(child_executors, task_id)
            verifier = self._callback(verifiers, task_id)
            action = self._callback(direct_actions, task_id)
            direct_verify = self._callback(direct_verifiers, task_id)
            controller = BoundedDelegationController(self.root)
            result = controller.execute(request=request, child_executor=executor, verify=verifier, direct_action=action, direct_verify=direct_verify)
            child_results[task_id] = result
            if self._needs_cancellation(result):
                break
        return {
            "schema": PARALLEL_RESULT_SCHEMA,
            "status": "DONE" if child_results and all(value.get("status") in {"DONE", "DIRECT"} for value in child_results.values()) else "PARTIAL" if child_results else "BLOCKED",
            "strategy": SEQUENTIAL,
            "parallel_execution": False,
            "task_ids": list(child_results),
            "child_results": _safe(child_results, path="parallel.sequential.child_results"),
            "reason": decision.get("reason", "SEQUENTIAL_DEFAULT"),
            "automatic_start": False,
            "background_execution": False,
            "process_survives_session": False,
            "max_parallel_children": MAX_PARALLEL_CHILDREN,
            "worker_output_is_evidence": False,
        }

    def _combined_verification(self, callback: Callable[..., Any] | None, child_results: Mapping[str, Any], group: Mapping[str, Any]) -> dict[str, Any]:
        if callback is None:
            return {"status": "FAILED", "summary": "COMBINED_VERIFIER_REQUIRED", "evidence_refs": []}
        try:
            raw = _call(callback, _safe(child_results, path="combined.child_results"), _safe(group, path="combined.group"))
            if raw is True:
                return {"status": "VERIFIED", "summary": "PARENT_COMBINED_VERIFIER_PASS", "evidence_refs": []}
            if not isinstance(raw, Mapping):
                return {"status": "FAILED", "summary": "COMBINED_VERIFIER_RESULT_INVALID", "evidence_refs": []}
            status = _status(raw.get("status"))
            evidence_refs = _refs(raw.get("evidence_refs", ()), "combined.evidence_refs")
            result = {
                "status": "VERIFIED" if status in {"PASS", "VERIFIED", "DONE"} else "FAILED",
                "summary": str(raw.get("summary", ""))[:4096],
                "evidence_refs": list(evidence_refs),
                "candidate_fingerprint": raw.get("candidate_fingerprint"),
            }
            return _safe(result, path="combined.verification")
        except Exception as exc:
            return {"status": "FAILED", "summary": f"COMBINED_VERIFIER_FAILED:{type(exc).__name__}", "evidence_refs": []}

    def execute(
        self,
        requests: Sequence[DelegationRequest],
        *,
        child_executors: Mapping[str, Callable[..., Any]] | Callable[..., Any] | None = None,
        verifiers: Mapping[str, Callable[..., Any]] | Callable[..., Any] | None = None,
        combined_verify: Callable[..., Any] | None = None,
        cancellation_callbacks: Mapping[str, Callable[..., Any]] | Callable[..., Any] | None = None,
        direct_actions: Mapping[str, Callable[..., Any]] | Callable[..., Any] | None = None,
        direct_verifiers: Mapping[str, Callable[..., Any]] | Callable[..., Any] | None = None,
        task_contracts: Mapping[str, Mapping[str, Any] | ParallelTaskContract] | None = None,
        economy_profiles: Mapping[str, Mapping[str, Any] | ParallelEconomyProfile] | None = None,
    ) -> dict[str, Any]:
        """Run one finite foreground group or the explicit sequential fallback."""

        effective = self._effective_requests(requests, child_executors)
        decision = self.decide(effective, task_contracts=task_contracts, economy_profiles=economy_profiles)
        strategy = decision.get("strategy")
        if strategy == PARALLEL_BLOCKED:
            return {
                "schema": PARALLEL_RESULT_SCHEMA,
                "status": "BLOCKED",
                "strategy": PARALLEL_BLOCKED,
                "reason": decision.get("reason", "PARALLEL_DECISION_BLOCKED"),
                "decision": decision,
                "parallel_execution": False,
                "automatic_start": False,
                "background_execution": False,
                "process_survives_session": False,
                "max_parallel_children": MAX_PARALLEL_CHILDREN,
                "worker_output_is_evidence": False,
            }

        selected_ids = tuple(decision.get("task_ids", ()))
        if strategy == SEQUENTIAL:
            return self._execute_sequential(decision, effective, child_executors, verifiers, direct_actions, direct_verifiers) | {"decision": decision}
        if len(selected_ids) != MAX_PARALLEL_CHILDREN:
            return {"schema": PARALLEL_RESULT_SCHEMA, "status": "BLOCKED", "strategy": PARALLEL_BLOCKED, "reason": "PARALLEL_MAX_TWO_REQUIRED", "decision": decision, "parallel_execution": False, "worker_output_is_evidence": False}
        selected = tuple(next(request for request in effective if request.task.task_id == task_id) for task_id in selected_ids)
        for request in selected:
            if self._callback(child_executors, request.task.task_id) is None:
                return {"schema": PARALLEL_RESULT_SCHEMA, "status": "BLOCKED", "strategy": PARALLEL_BLOCKED, "reason": f"CHILD_EXECUTOR_MISSING:{request.task.task_id}", "decision": decision, "parallel_execution": False, "worker_output_is_evidence": False}
        mutating = any(bool(request.child_permissions and request.child_permissions.allow_mutation) or bool(set(request.task.permission_needs) & _MUTATION_GRANTS) or bool(request.write_scopes or request.delete_scopes) for request in selected)
        if mutating and combined_verify is None:
            return {"schema": PARALLEL_RESULT_SCHEMA, "status": "BLOCKED", "strategy": PARALLEL_BLOCKED, "reason": "COMBINED_VERIFIER_REQUIRED_FOR_MUTATION_GROUP", "decision": decision, "parallel_execution": False, "worker_output_is_evidence": False}

        try:
            plan = self._control_plane()
            group = self._new_group_record(decision, selected, plan)
            group_id = str(group["group_id"])
            self._write_group(group)
            self._record_event("parallel_group_created", group, details={"task_ids": list(selected_ids), "plan_hash": group["plan_hash"]})
            group["status"] = "RUNNING"
            self._write_group(group)
        except (ParallelExecutionError, ParallelControlPlaneError, TaskStateError) as exc:
            return {"schema": PARALLEL_RESULT_SCHEMA, "status": "CONTROL_PLANE_FAILURE", "strategy": PARALLEL_BLOCKED, "reason": str(exc), "decision": decision, "parallel_execution": False, "worker_output_is_evidence": False}

        results: dict[str, Mapping[str, Any]] = {}
        started: dict[str, str] = {}
        finished: dict[str, str] = {}
        thread_errors: dict[str, str] = {}
        child_done = {task_id: False for task_id in selected_ids}
        child_started = {task_id: False for task_id in selected_ids}
        state_lock = threading.RLock()

        def persist_child(task_id: str, result: Mapping[str, Any], started_at: str, finished_at: str) -> None:
            projection = self._child_projection(result, started_at=started_at, finished_at=finished_at)
            with state_lock:
                results[task_id] = dict(result)
                finished[task_id] = finished_at
                child_done[task_id] = True
                group["children"][task_id].update(projection)
                try:
                    self._write_group(group)
                    self._record_event("parallel_child_finished", group, task_id=task_id, details={"status": projection["status"], "mutation_state": projection["mutation_state"]})
                except (ParallelControlPlaneError, ParallelExecutionError, TaskStateError) as exc:
                    thread_errors[task_id] = f"CONTROL_PLANE_EVENT_WRITE_FAILED:{exc}"
                if self._needs_cancellation(result):
                    cancellation = group["cancellation"]
                    if cancellation.get("status") == "NOT_REQUESTED":
                        pending = [other for other in selected_ids if other != task_id and not child_done[other]]
                        cancellation["status"] = "REQUESTED" if pending else "NOT_NEEDED"
                        for other in pending:
                            callback = self._callback(cancellation_callbacks, other)
                            if callback is None:
                                cancellation["status"] = "UNAVAILABLE"
                                cancellation.setdefault("requests", []).append({"task_id": other, "status": "CANCEL_UNAVAILABLE"})
                                continue
                            try:
                                response = _call(callback, {"parallel_group_id": group_id, "task_id": other, "reason": projection["reason"]})
                                cancellation.setdefault("requests", []).append({"task_id": other, "status": _status(response.get("status") if isinstance(response, Mapping) else response) or "REQUESTED"})
                            except Exception as exc:
                                cancellation["status"] = "UNAVAILABLE"
                                cancellation.setdefault("requests", []).append({"task_id": other, "status": f"CANCEL_FAILED:{type(exc).__name__}"})
                        try:
                            self._write_group(group)
                        except ParallelControlPlaneError as exc:
                            thread_errors[task_id] = str(exc)

        def run_child(request: DelegationRequest) -> None:
            task_id = request.task.task_id
            started_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            with state_lock:
                child_started[task_id] = True
                started[task_id] = started_at
                group["children"][task_id]["status"] = "RUNNING"
                self._write_group(group)
            executor = self._callback(child_executors, task_id)
            verifier = self._callback(verifiers, task_id)
            controller = BoundedDelegationController(self.root, parallel_group_id=group_id, parallel_task_ids=selected_ids)
            try:
                value = controller.execute(request=request, child_executor=executor, verify=verifier)
                if not isinstance(value, Mapping):
                    raise ParallelControlPlaneError("C15_CHILD_RESULT_INVALID")
                result = dict(value)
            except Exception as exc:
                thread_errors[task_id] = f"CHILD_CONTROL_PLANE:{type(exc).__name__}"
                result = {
                    "schema": "p2p-bounded-delegation-result/1",
                    "status": "CONTROL_PLANE_ERROR",
                    "strategy": BLOCKED,
                    "task_id": task_id,
                    "reason": f"CHILD_CONTROL_PLANE:{type(exc).__name__}",
                    "output_is_evidence": False,
                }
            finished_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            persist_child(task_id, result, started_at, finished_at)

        threads = [threading.Thread(target=run_child, args=(request,), name=f"p2p-c17-{request.task.task_id}", daemon=False) for request in selected]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        if thread_errors:
            group["status"] = "CONTROL_PLANE_FAILURE"
        else:
            child_statuses = [str(results.get(task_id, {}).get("status", "CONTROL_PLANE_ERROR")) for task_id in selected_ids]
            if any(status == "CONTROL_PLANE_ERROR" for status in child_statuses):
                group["status"] = "CONTROL_PLANE_FAILURE"
            elif any(self._needs_cancellation(results.get(task_id, {})) for task_id in selected_ids):
                group["status"] = "UNKNOWN" if any(results.get(task_id, {}).get("status") == "UNKNOWN" for task_id in selected_ids) else "NEEDS_RECHECK"
            elif all(status == "DONE" for status in child_statuses):
                combined = self._combined_verification(combined_verify, results, group)
                group["combined_verification"] = combined
                self._write_json(self._group_dir(group_id) / "combined-verification.json", combined)
                group["status"] = "DONE" if combined.get("status") == "VERIFIED" else "NEEDS_RECHECK"
            elif any(status == "DONE" for status in child_statuses):
                group["status"] = "PARTIAL"
            elif all(status in {"BLOCKED", "FAILED", "VERIFICATION_FAILED", "STALE_HANDOFF"} for status in child_statuses):
                group["status"] = "BLOCKED"
            else:
                group["status"] = "PARTIAL"
        group["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        try:
            self._write_group(group)
            self._record_event("parallel_group_completed", group, details={"status": group["status"], "task_ids": list(selected_ids)})
        except (ParallelControlPlaneError, ParallelExecutionError, TaskStateError) as exc:
            group["status"] = "CONTROL_PLANE_FAILURE"
            group["control_plane_error"] = str(exc)
            self._write_group(group)

        return _safe(
            {
                "schema": PARALLEL_RESULT_SCHEMA,
                "status": group["status"],
                "strategy": PARALLEL,
                "parallel_execution": True,
                "parallel_group_id": group_id,
                "task_ids": list(selected_ids),
                "child_results": results,
                "children": group["children"],
                "combined_verification": group["combined_verification"],
                "cancellation": group["cancellation"],
                "decision": decision,
                "automatic_start": False,
                "background_execution": False,
                "process_survives_session": False,
                "max_parallel_children": MAX_PARALLEL_CHILDREN,
                "max_delegation_depth": 1,
                "child_delegation_allowed": False,
                "worker_output_is_evidence": False,
            },
            path="parallel.result",
        )


ParallelForegroundController = BoundedParallelForegroundController
BoundedParallelController = BoundedParallelForegroundController


__all__ = [
    "PARALLEL_SCHEMA",
    "PARALLEL_RESULT_SCHEMA",
    "PARALLEL_GROUP_RELATIVE_ROOT",
    "MAX_PARALLEL_CHILDREN",
    "MAX_PARALLEL_ATTEMPTS",
    "PARALLEL_LARGE_CONTEXT_BYTES",
    "PARALLEL",
    "SEQUENTIAL",
    "PARALLEL_BLOCKED",
    "ParallelTaskContract",
    "ParallelEconomyProfile",
    "BoundedParallelForegroundController",
    "ParallelForegroundController",
    "BoundedParallelController",
    "ParallelExecutionError",
    "ParallelControlPlaneError",
]
