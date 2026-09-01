"""Durable task state and minimal dependency graph contracts.

This module is deliberately a structured-data boundary.  It does not start
work, select an agent, install a capability, run a scheduler, or keep a
process alive after the current session.  ``TaskPlan`` is a projection over an
existing Goal and existing P2P evidence/decision/context references.  The
durable adapter is added separately so the kernel remains usable in isolated
tests and future runtimes.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
import hashlib
import json
import re
import threading
from typing import Any, Iterable, Mapping, Sequence

from .evidence import EvidenceClaim, evaluate_done
from .isolation import assert_isolated_target


TASK_STATE_SCHEMA = "p2p-task-state/1"
TASK_PLAN_SCHEMA = "p2p-task-plan/1"
TASK_EVENT_SCHEMA = "p2p-task-event/1"
PLAN_REVISION_SCHEMA = "p2p-task-plan-revision/1"
PLAN_LIFECYCLE_EVENT_SCHEMA = "p2p-task-plan-lifecycle-event/1"
PLAN_IDENTITY_SCHEMA = "p2p-task-plan-identity/1"
PLAN_AUTHORITY_RESOLUTION_SCHEMA = "p2p-plan-authority-resolution/1"

# Plan-level authority lifecycle (P2P-CONTEXT-HYGIENE-01).  A plan is
# created ACTIVE; an explicit closure or supersession makes it historical.
# CLOSED and SUPERSEDED plans are retained, explicitly readable, and lose
# ACTIVE authority: they can never transition back to ACTIVE, and any
# mutation of their tasks fails closed.  Continuation of closed work is a
# NEW plan that references the closed one through source refs.
PLAN_LIFECYCLE_STATES = ("ACTIVE", "CLOSED", "SUPERSEDED")

TASK_STATES = (
    "PLANNED",
    "READY",
    "ACTIVE",
    "BLOCKED",
    "WAITING_OWNER",
    "DONE",
    "CANCELLED",
)
OWNER_DECISION_STATES = ("PENDING", "RESOLVED", "REJECTED")
PREFLIGHT_STATES = ("PASS", "BLOCKED", "WAITING_OWNER", "STALE", "UNKNOWN")
RESUME_CLASSIFICATIONS = (
    "DONE",
    "SAFE_TO_RESUME",
    "NEEDS_RECHECK",
    "BLOCKED",
    "UNKNOWN",
)
LINEAGE_STATES = ("UNKNOWN", "OBSERVED")
CAPABILITY_READY_STATES = (
    "INSTALLED",
    "DISCOVERED",
    "ELIGIBLE",
    "RESOLVED",
    "EXECUTABLE",
    "HEALTHY",
)
STATE_RELATIVE_PATH = ".p2p/state/task-state.json"
LEDGER_RELATIVE_PATH = ".p2p/state/execution-ledger.jsonl"
_STORE_LOCKS: dict[str, threading.RLock] = {}
_STORE_LOCKS_GUARD = threading.Lock()
_CHECKPOINT_FIELDS = {
    "checkpoint_ref",
    "state_fingerprint",
    "recovery_classification",
    "next_safe_step",
    "completed_refs",
    "pending_refs",
    "evidence_fingerprints",
    "captured_at",
    "notes",
}
_PREFLIGHT_FIELDS = {
    "status",
    "task_id",
    "checked_at",
    "required_capabilities",
    "optional_capabilities",
    "capability_readiness",
    "permission_needs",
    "permission_state",
    "context_refs",
    "context_state",
    "missing_capabilities",
    "stale_capabilities",
    "missing_permissions",
    "denied_permissions",
    "stale_context",
    "owner_decision",
    "reasons",
    "source_refs",
}
_TASK_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_SECRET_KEY_RE = re.compile(
    r"(?:secret|token|password|credential|api[_-]?key|private[_-]?key|authorization|environment)",
    re.IGNORECASE,
)
_FORBIDDEN_TASK_IDENTITY_FIELDS = {
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
}


class TaskStateError(ValueError):
    """Base error for invalid or unsafe task state."""


class TaskContractError(TaskStateError):
    """Raised when one task or owner record violates its contract."""


class TaskGraphError(TaskStateError):
    """Raised when task dependency references or cycles are invalid."""


class TaskTransitionError(TaskStateError):
    """Raised when a state transition is not explicitly allowed."""


class TaskEvidenceError(TaskStateError):
    """Raised when a completion claim is not evidence-backed."""


class TaskGateError(TaskStateError):
    """Raised when capability, permission, or owner preflight is not safe."""


class TaskControlPlaneError(TaskStateError):
    """Raised when durable task control-plane state cannot be trusted."""


class TaskLifecycleError(TaskStateError):
    """Raised when a non-active (closed/superseded) plan is used as active authority."""


def utc_now() -> str:
    """Return a timezone-qualified timestamp suitable for durable state."""

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _required_text(value: Any, field_name: str, *, max_length: int = 4096) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > max_length:
        raise TaskContractError(f"{field_name}_REQUIRED")
    if _SECRET_KEY_RE.search(field_name) or _looks_secret_like(value):
        raise TaskContractError(f"{field_name}_SECRET_LIKE")
    return value.strip()


def _safe_text(value: Any, field_name: str, *, max_length: int = 4096) -> str:
    if value is None:
        return ""
    if not isinstance(value, str) or len(value) > max_length:
        raise TaskContractError(f"{field_name}_INVALID")
    if value and (_SECRET_KEY_RE.search(field_name) or _looks_secret_like(value)):
        raise TaskContractError(f"{field_name}_SECRET_LIKE")
    return value.strip()


def _looks_secret_like(value: str) -> bool:
    lowered = value.lower()
    return bool(
        re.search(r"(?:api[_-]?key|password|token|secret|authorization)\s*[:=]\s*\S+", lowered)
        or re.search(r"\bsk-[a-z0-9_-]{16,}\b", value, re.IGNORECASE)
    )


def _unique_refs(values: Any, field_name: str, *, required: bool = False) -> tuple[str, ...]:
    if values is None:
        values = []
    if isinstance(values, str) or not isinstance(values, (list, tuple, set)):
        raise TaskContractError(f"{field_name}_MUST_BE_LIST")
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        item = _required_text(value, field_name, max_length=1024)
        if item in seen:
            raise TaskContractError(f"{field_name}_DUPLICATE:{item}")
        seen.add(item)
        result.append(item)
    if required and not result:
        raise TaskContractError(f"{field_name}_REQUIRED")
    return tuple(result)


def _tuple_refs(values: Any, field_name: str, *, required: bool = False) -> tuple[str, ...]:
    """Normalize a serialized reference list without accepting a string."""

    return _unique_refs(values, field_name, required=required)


def _safe_mapping(value: Any, field_name: str) -> dict[str, Any] | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise TaskContractError(f"{field_name}_MUST_BE_OBJECT")
    result: dict[str, Any] = {}
    for key, child in value.items():
        key_text = str(key)
        if _SECRET_KEY_RE.search(key_text):
            raise TaskContractError(f"{field_name}_SECRET_FIELD")
        if isinstance(child, Mapping):
            result[key_text] = _safe_mapping(child, f"{field_name}.{key_text}")
        elif isinstance(child, (list, tuple)):
            normalized_items: list[Any] = []
            for item in child:
                if isinstance(item, str) and _looks_secret_like(item):
                    raise TaskContractError(f"{field_name}.{key_text}_SECRET_LIKE")
                normalized_items.append(str(item))
            result[key_text] = normalized_items
        elif isinstance(child, str):
            if _looks_secret_like(child):
                raise TaskContractError(f"{field_name}.{key_text}_SECRET_LIKE")
            result[key_text] = child
        elif isinstance(child, (int, float, bool)) or child is None:
            result[key_text] = child
        else:
            raise TaskContractError(f"{field_name}_VALUE_INVALID")
    return result


def _sha256(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _assert_sha256(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not _SHA256_RE.fullmatch(value.lower()):
        raise TaskContractError(f"{field_name}_SHA256_REQUIRED")
    return value.lower()


def _json_safe(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_safe(child) for key, child in value.items()}
    if isinstance(value, tuple):
        return [_json_safe(child) for child in value]
    if isinstance(value, list):
        return [_json_safe(child) for child in value]
    return value


def _assert_no_identity_fields(value: Any, *, path: str = "task") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key).lower()
            if key_text in _FORBIDDEN_TASK_IDENTITY_FIELDS:
                raise TaskContractError(f"TASK_AGENT_IDENTITY_FORBIDDEN:{path}.{key}")
            _assert_no_identity_fields(child, path=f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            _assert_no_identity_fields(child, path=f"{path}[{index}]")


def _check_timestamp(value: Any, field_name: str) -> str:
    text = _required_text(value, field_name, max_length=128)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise TaskContractError(f"{field_name}_INVALID") from exc
    if parsed.tzinfo is None:
        raise TaskContractError(f"{field_name}_TIMEZONE_REQUIRED")
    return text


def _copy_dict(value: Mapping[str, Any] | None) -> dict[str, Any] | None:
    return None if value is None else _json_safe(dict(value))


@dataclass(frozen=True)
class LogicalOwner:
    """The one durable orchestration owner for a Goal.

    This is a logical state owner, not an agent, model, provider, thread, or
    background process.  Its stable ID is derived from the existing Goal ID.
    """

    owner_id: str
    goal_id: str
    owner_type: str = "PERSISTENT_LOGICAL_OWNER"
    state_ref: str = ".p2p/state/task-state.json"
    background_execution: bool = False
    process_survives_session: bool = False

    @classmethod
    def for_goal(cls, goal_id: str) -> "LogicalOwner":
        goal = _required_text(goal_id, "goal_id", max_length=512)
        return cls(owner_id=f"logical-owner:{goal}", goal_id=goal)

    def __post_init__(self) -> None:
        goal = _required_text(self.goal_id, "goal_id", max_length=512)
        owner = _required_text(self.owner_id, "owner_id", max_length=1024)
        if owner != f"logical-owner:{goal}":
            raise TaskContractError("LOGICAL_OWNER_MUST_BE_GOAL_SCOPED")
        if self.owner_type != "PERSISTENT_LOGICAL_OWNER":
            raise TaskContractError("LOGICAL_OWNER_TYPE_INVALID")
        if not self.state_ref or self.state_ref.startswith("/") or ".." in self.state_ref.split("/"):
            raise TaskContractError("LOGICAL_OWNER_STATE_REF_INVALID")
        if self.background_execution or self.process_survives_session:
            raise TaskContractError("BACKGROUND_EXECUTION_NOT_PROVIDED")

    def to_dict(self) -> dict[str, Any]:
        return {
            "owner_id": self.owner_id,
            "goal_id": self.goal_id,
            "owner_type": self.owner_type,
            "state_ref": self.state_ref,
            "background_execution": False,
            "process_survives_session": False,
        }

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "LogicalOwner":
        if not isinstance(value, Mapping):
            raise TaskContractError("LOGICAL_OWNER_MUST_BE_OBJECT")
        _assert_no_identity_fields(value, path="logical_owner")
        allowed = {"owner_id", "goal_id", "owner_type", "state_ref", "background_execution", "process_survives_session"}
        unknown = sorted(str(key) for key in value if str(key) not in allowed)
        if unknown:
            raise TaskContractError("LOGICAL_OWNER_FIELDS_INVALID:" + ",".join(unknown))
        return cls(
            owner_id=str(value.get("owner_id", "")),
            goal_id=str(value.get("goal_id", "")),
            owner_type=str(value.get("owner_type", "")),
            state_ref=str(value.get("state_ref", "")),
            background_execution=bool(value.get("background_execution", False)),
            process_survives_session=bool(value.get("process_survives_session", False)),
        )


@dataclass(frozen=True)
class PlanIdentity:
    """Exact durable identity binding for a plan.

    The binding is the repository plus the workstream plus the current
    durable subject, optionally tightened with a source SHA-256, a git tree
    SHA-256, and a PR reference.  Exact durable identity outranks semantic
    text similarity: a record whose binding does not match exactly is
    ineligible for active authority no matter how similar its text is.
    """

    repository: str
    workstream: str
    subject: str
    source_sha256: str = ""
    source_tree: str = ""
    pr: str = ""

    def __post_init__(self) -> None:
        _required_text(self.repository, "plan_identity.repository", max_length=512)
        _required_text(self.workstream, "plan_identity.workstream", max_length=256)
        _required_text(self.subject, "plan_identity.subject", max_length=512)
        if self.source_sha256:
            _assert_sha256(self.source_sha256, "plan_identity.source_sha256")
        if self.source_tree:
            _assert_sha256(self.source_tree, "plan_identity.source_tree")
        if self.pr:
            _required_text(self.pr, "plan_identity.pr", max_length=64)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": PLAN_IDENTITY_SCHEMA,
            "repository": self.repository,
            "workstream": self.workstream,
            "subject": self.subject,
            "source_sha256": self.source_sha256,
            "source_tree": self.source_tree,
            "pr": self.pr,
        }

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "PlanIdentity":
        if not isinstance(value, Mapping):
            raise TaskContractError("PLAN_IDENTITY_MUST_BE_OBJECT")
        _assert_no_identity_fields(value, path="plan_identity")
        allowed = {"schema", "repository", "workstream", "subject", "source_sha256", "source_tree", "pr"}
        unknown = sorted(str(key) for key in value if str(key) not in allowed)
        if unknown:
            raise TaskContractError("PLAN_IDENTITY_FIELDS_INVALID:" + ",".join(unknown))
        return cls(
            repository=str(value.get("repository", "")),
            workstream=str(value.get("workstream", "")),
            subject=str(value.get("subject", "")),
            source_sha256=str(value.get("source_sha256", "") or "").strip().lower(),
            source_tree=str(value.get("source_tree", "") or "").strip().lower(),
            pr=str(value.get("pr", "") or "").strip(),
        )


@dataclass(frozen=True)
class TaskRecord:
    """Minimal durable description of one work item."""

    task_id: str
    goal_id: str
    title: str
    purpose: str
    status: str = "PLANNED"
    dependencies: tuple[str, ...] = ()
    scope: tuple[str, ...] = ()
    non_scope: tuple[str, ...] = ()
    acceptance_requirements: tuple[str, ...] = ()
    required_evidence: tuple[str, ...] = ()
    permission_needs: tuple[str, ...] = ()
    required_capabilities: tuple[str, ...] = ()
    optional_capabilities: tuple[str, ...] = ()
    context_refs: tuple[str, ...] = ()
    output_refs: tuple[str, ...] = ()
    requirement_refs: tuple[str, ...] = ()
    decision_refs: tuple[str, ...] = ()
    blocker: dict[str, Any] | None = None
    owner_decision: dict[str, Any] | None = None
    completion: dict[str, Any] | None = None
    checkpoint: dict[str, Any] | None = None
    execution_lineage: dict[str, Any] = field(default_factory=lambda: {"status": "UNKNOWN", "refs": []})
    last_preflight: dict[str, Any] | None = None
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        task_id = _required_text(self.task_id, "task_id", max_length=128).lower()
        if not _TASK_ID_RE.fullmatch(task_id):
            raise TaskContractError("TASK_ID_INVALID")
        _required_text(self.goal_id, "goal_id", max_length=512)
        _required_text(self.title, "title")
        _required_text(self.purpose, "purpose")
        if self.status not in TASK_STATES:
            raise TaskContractError("TASK_STATUS_INVALID")
        for field_name, value, required in (
            ("dependencies", self.dependencies, False),
            ("scope", self.scope, True),
            ("non_scope", self.non_scope, False),
            ("acceptance_requirements", self.acceptance_requirements, True),
            ("required_evidence", self.required_evidence, True),
            ("permission_needs", self.permission_needs, False),
            ("required_capabilities", self.required_capabilities, False),
            ("optional_capabilities", self.optional_capabilities, False),
            ("context_refs", self.context_refs, False),
            ("output_refs", self.output_refs, False),
            ("requirement_refs", self.requirement_refs, False),
            ("decision_refs", self.decision_refs, False),
        ):
            if not isinstance(value, tuple):
                raise TaskContractError(f"{field_name}_MUST_BE_TUPLE")
            normalized = _unique_refs(value, field_name, required=required)
            if tuple(value) != normalized:
                raise TaskContractError(f"{field_name}_MUST_BE_UNIQUE_AND_ORDERED")
        _assert_no_identity_fields(self.execution_lineage, path="execution_lineage")
        if not isinstance(self.execution_lineage, Mapping):
            raise TaskContractError("EXECUTION_LINEAGE_MUST_BE_OBJECT")
        lineage_status = self.execution_lineage.get("status")
        if lineage_status not in LINEAGE_STATES:
            raise TaskContractError("EXECUTION_LINEAGE_STATUS_INVALID")
        lineage_refs = self.execution_lineage.get("refs", [])
        _unique_refs(lineage_refs, "execution_lineage.refs")
        if self.blocker is not None:
            _assert_no_identity_fields(self.blocker, path="blocker")
            _safe_mapping(self.blocker, "blocker")
        if self.owner_decision is not None:
            _assert_no_identity_fields(self.owner_decision, path="owner_decision")
            _safe_mapping(self.owner_decision, "owner_decision")
        if self.completion is not None:
            _assert_no_identity_fields(self.completion, path="completion")
            _safe_mapping(self.completion, "completion")
        if self.checkpoint is not None:
            _assert_no_identity_fields(self.checkpoint, path="checkpoint")
            _safe_mapping(self.checkpoint, "checkpoint")
            _validate_checkpoint(self.checkpoint)
        if self.last_preflight is not None:
            _assert_no_identity_fields(self.last_preflight, path="last_preflight")
            _safe_mapping(self.last_preflight, "last_preflight")
            if self.last_preflight.get("status") not in PREFLIGHT_STATES:
                raise TaskContractError("PREFLIGHT_STATUS_INVALID")
        _check_timestamp(self.created_at, "created_at")
        _check_timestamp(self.updated_at, "updated_at")

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "TaskRecord":
        if not isinstance(value, Mapping):
            raise TaskContractError("TASK_MUST_BE_OBJECT")
        _assert_no_identity_fields(value)
        allowed = {
            "task_id",
            "goal_id",
            "title",
            "purpose",
            "status",
            "dependencies",
            "scope",
            "non_scope",
            "acceptance_requirements",
            "required_evidence",
            "permission_needs",
            "required_capabilities",
            "optional_capabilities",
            "context_refs",
            "output_refs",
            "requirement_refs",
            "decision_refs",
            "blocker",
            "owner_decision",
            "completion",
            "checkpoint",
            "execution_lineage",
            "last_preflight",
            "created_at",
            "updated_at",
        }
        unknown = sorted(str(key) for key in value if str(key) not in allowed)
        if unknown:
            raise TaskContractError("TASK_FIELDS_INVALID:" + ",".join(unknown))
        return cls(
            task_id=str(value.get("task_id", "")),
            goal_id=str(value.get("goal_id", "")),
            title=str(value.get("title", "")),
            purpose=str(value.get("purpose", "")),
            status=str(value.get("status", "PLANNED")),
            dependencies=_tuple_refs(value.get("dependencies", ()), "dependencies"),
            scope=_tuple_refs(value.get("scope", ()), "scope", required=True),
            non_scope=_tuple_refs(value.get("non_scope", ()), "non_scope"),
            acceptance_requirements=_tuple_refs(value.get("acceptance_requirements", ()), "acceptance_requirements", required=True),
            required_evidence=_tuple_refs(value.get("required_evidence", ()), "required_evidence", required=True),
            permission_needs=_tuple_refs(value.get("permission_needs", ()), "permission_needs"),
            required_capabilities=_tuple_refs(value.get("required_capabilities", ()), "required_capabilities"),
            optional_capabilities=_tuple_refs(value.get("optional_capabilities", ()), "optional_capabilities"),
            context_refs=_tuple_refs(value.get("context_refs", ()), "context_refs"),
            output_refs=_tuple_refs(value.get("output_refs", ()), "output_refs"),
            requirement_refs=_tuple_refs(value.get("requirement_refs", ()), "requirement_refs"),
            decision_refs=_tuple_refs(value.get("decision_refs", ()), "decision_refs"),
            blocker=_copy_dict(value.get("blocker")),
            owner_decision=_copy_dict(value.get("owner_decision")),
            completion=_copy_dict(value.get("completion")),
            checkpoint=_copy_dict(value.get("checkpoint")),
            execution_lineage=dict(value.get("execution_lineage") or {"status": "UNKNOWN", "refs": []}),
            last_preflight=_copy_dict(value.get("last_preflight")),
            created_at=str(value.get("created_at") or utc_now()),
            updated_at=str(value.get("updated_at") or utc_now()),
        )

    def to_dict(self) -> dict[str, Any]:
        return _json_safe({
            "task_id": self.task_id,
            "goal_id": self.goal_id,
            "title": self.title,
            "purpose": self.purpose,
            "status": self.status,
            "dependencies": self.dependencies,
            "scope": self.scope,
            "non_scope": self.non_scope,
            "acceptance_requirements": self.acceptance_requirements,
            "required_evidence": self.required_evidence,
            "permission_needs": self.permission_needs,
            "required_capabilities": self.required_capabilities,
            "optional_capabilities": self.optional_capabilities,
            "context_refs": self.context_refs,
            "output_refs": self.output_refs,
            "requirement_refs": self.requirement_refs,
            "decision_refs": self.decision_refs,
            "blocker": self.blocker,
            "owner_decision": self.owner_decision,
            "completion": self.completion,
            "checkpoint": self.checkpoint,
            "execution_lineage": self.execution_lineage,
            "last_preflight": self.last_preflight,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        })


ALLOWED_TRANSITIONS: dict[str, tuple[str, ...]] = {
    "PLANNED": ("READY", "BLOCKED", "WAITING_OWNER", "CANCELLED"),
    "READY": ("ACTIVE", "BLOCKED", "WAITING_OWNER", "CANCELLED"),
    "ACTIVE": ("DONE", "BLOCKED", "WAITING_OWNER", "CANCELLED"),
    "BLOCKED": ("PLANNED", "READY", "WAITING_OWNER", "CANCELLED"),
    "WAITING_OWNER": ("PLANNED", "READY", "ACTIVE", "BLOCKED", "CANCELLED"),
    "DONE": (),
    "CANCELLED": (),
}


def validate_dependency_graph(tasks: Mapping[str, TaskRecord]) -> tuple[str, ...]:
    """Validate references/self-dependencies/cycles and return topo order."""

    if not isinstance(tasks, Mapping) or not tasks:
        raise TaskGraphError("TASK_GRAPH_EMPTY")
    task_ids = set(tasks)
    for key, task in tasks.items():
        if key != task.task_id:
            raise TaskGraphError(f"TASK_ID_KEY_MISMATCH:{key}")
        for dependency in task.dependencies:
            if dependency not in task_ids:
                raise TaskGraphError(f"TASK_DEPENDENCY_NOT_FOUND:{task.task_id}:{dependency}")
            if dependency == task.task_id:
                raise TaskGraphError(f"TASK_SELF_DEPENDENCY:{task.task_id}")
    visiting: set[str] = set()
    visited: set[str] = set()
    order: list[str] = []

    def visit(task_id: str) -> None:
        if task_id in visiting:
            raise TaskGraphError(f"TASK_DEPENDENCY_CYCLE:{task_id}")
        if task_id in visited:
            return
        visiting.add(task_id)
        for dependency in tasks[task_id].dependencies:
            visit(dependency)
        visiting.remove(task_id)
        visited.add(task_id)
        order.append(task_id)

    for task_id in sorted(task_ids):
        visit(task_id)
    return tuple(order)


def _completion_is_structurally_valid(task: TaskRecord) -> bool:
    completion = task.completion
    if not isinstance(completion, Mapping):
        return False
    if completion.get("status") != "VERIFIED":
        return False
    evidence_refs = completion.get("evidence_refs")
    if not isinstance(evidence_refs, list) or not evidence_refs:
        return False
    if len(evidence_refs) != len(set(evidence_refs)) or set(evidence_refs) != set(task.required_evidence):
        return False
    done_when = completion.get("done_when")
    if done_when is not None and (not isinstance(done_when, list) or set(done_when) != set(task.required_evidence)):
        return False
    candidate = completion.get("candidate_state_fingerprint")
    if not isinstance(candidate, str) or not _SHA256_RE.fullmatch(candidate.lower()):
        return False
    fingerprints = completion.get("evidence_fingerprints")
    if not isinstance(fingerprints, Mapping) or set(fingerprints) != set(evidence_refs):
        return False
    if any(not isinstance(value, str) or not _SHA256_RE.fullmatch(value.lower()) for value in fingerprints.values()):
        return False
    return True


def _owner_decision_is_pending(task: TaskRecord) -> bool:
    decision = task.owner_decision
    return isinstance(decision, Mapping) and decision.get("status") == "PENDING" and bool(str(decision.get("question", "")).strip())


def _coerce_evidence_claim(value: EvidenceClaim | Mapping[str, Any]) -> EvidenceClaim:
    if isinstance(value, EvidenceClaim):
        return value
    if not isinstance(value, Mapping):
        raise TaskEvidenceError("EVIDENCE_CLAIM_MUST_BE_OBJECT")
    claim = _required_text(value.get("claim"), "evidence.claim")
    required = tuple(value.get("required_evidence", ()))
    actual = value.get("actual_evidence", ())
    status = str(value.get("status", "INCOMPLETE"))
    if not isinstance(actual, (list, tuple)):
        raise TaskEvidenceError("ACTUAL_EVIDENCE_MUST_BE_LIST")
    for item in actual:
        if not isinstance(item, Mapping):
            raise TaskEvidenceError("ACTUAL_EVIDENCE_ITEM_INVALID")
        _assert_no_identity_fields(item, path="actual_evidence")
    try:
        return EvidenceClaim(
            claim=claim,
            required_evidence=required,
            actual_evidence=tuple(dict(item) for item in actual),
            status=status,
        )
    except (TypeError, ValueError) as exc:
        raise TaskEvidenceError(f"EVIDENCE_CLAIM_INVALID:{exc}") from exc


def _evidence_refs_and_fingerprints(
    claims: Sequence[EvidenceClaim],
) -> tuple[tuple[str, ...], dict[str, str]]:
    references: list[str] = []
    fingerprints: dict[str, str] = {}
    for claim in claims:
        for item in claim.actual_evidence:
            if not isinstance(item, Mapping):
                continue
            reference = str(item.get("evidence_ref") or item.get("source") or "").strip()
            if not reference:
                continue
            fingerprint = item.get("fingerprint")
            if reference in fingerprints:
                if fingerprints[reference] != fingerprint:
                    raise TaskEvidenceError(f"EVIDENCE_FINGERPRINT_CONFLICT:{reference}")
                continue
            fingerprints[reference] = _assert_sha256(fingerprint, f"evidence[{reference}].fingerprint")
            references.append(reference)
    return tuple(references), fingerprints


def evaluate_task_completion(
    task: TaskRecord,
    evidence_claims: Iterable[EvidenceClaim | Mapping[str, Any]],
    candidate_state: Any,
) -> dict[str, Any]:
    """Evaluate DONE-WHEN without persisting raw evidence or candidate state."""

    if not isinstance(task, TaskRecord):
        raise TaskEvidenceError("TASK_RECORD_REQUIRED")
    claims = tuple(_coerce_evidence_claim(item) for item in evidence_claims)
    evaluation = evaluate_done(task.required_evidence, claims)
    evidence_refs, evidence_fingerprints = _evidence_refs_and_fingerprints(claims)
    required = set(task.required_evidence)
    if set(evidence_refs) != required:
        evaluation = dict(evaluation)
        evaluation["status"] = "INCOMPLETE"
        evaluation["reason"] = "REQUIRED_EVIDENCE_NOT_EXACTLY_BOUND"
    if evaluation.get("status") != "VERIFIED":
        raise TaskEvidenceError(
            f"TASK_COMPLETION_{str(evaluation.get('status', 'UNKNOWN')).upper()}:{task.task_id}"
        )
    _assert_no_identity_fields(candidate_state, path="candidate_state")
    candidate_payload = _json_safe(candidate_state)
    try:
        candidate_json = json.dumps(candidate_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    except (TypeError, ValueError) as exc:
        raise TaskEvidenceError("CANDIDATE_STATE_NOT_SERIALIZABLE") from exc
    if _looks_secret_like(candidate_json):
        raise TaskEvidenceError("CANDIDATE_STATE_SECRET_LIKE")
    completion = {
        "status": "VERIFIED",
        "done_when": list(task.required_evidence),
        "evidence_refs": list(evidence_refs),
        "evidence_fingerprints": dict(sorted(evidence_fingerprints.items())),
        "candidate_state_fingerprint": hashlib.sha256(candidate_json.encode("utf-8")).hexdigest(),
        "independent_check": True,
        "evaluation_schema": evaluation.get("schema"),
    }
    return {
        "status": "VERIFIED",
        "completion": completion,
        "evaluation": evaluation,
    }


def _readiness_is_healthy(snapshot: Any) -> bool:
    if not isinstance(snapshot, Mapping):
        return False
    if snapshot.get("profile_presence_is_runtime_proof") is True:
        return False
    states = snapshot.get("states")
    if not isinstance(states, Mapping):
        return False
    return all(bool(states.get(state)) for state in CAPABILITY_READY_STATES)


def _permission_is_approved(value: Any) -> bool:
    if not isinstance(value, Mapping):
        return False
    status = str(value.get("status", "")).upper()
    source_ref = str(value.get("source_ref") or value.get("source") or "").strip()
    return status in {"AVAILABLE", "APPROVED", "GRANTED", "OBSERVED"} and bool(source_ref)


def evaluate_task_preflight(
    task: TaskRecord,
    *,
    capability_readiness: Mapping[str, Mapping[str, Any]] | None = None,
    permission_state: Mapping[str, Mapping[str, Any]] | None = None,
    context_state: Mapping[str, Mapping[str, Any]] | None = None,
    now: str | None = None,
) -> dict[str, Any]:
    """Evaluate current readiness and owner/permission boundaries.

    This function only observes supplied state.  It never installs a
    capability, grants a permission, or discovers a provider.
    """

    if not isinstance(task, TaskRecord):
        raise TaskGateError("TASK_RECORD_REQUIRED")
    checked_at = _check_timestamp(now or utc_now(), "preflight.checked_at")
    readiness = capability_readiness or {}
    permissions = permission_state or {}
    contexts = context_state or {}
    missing_capabilities: list[str] = []
    stale_capabilities: list[str] = []
    capability_view: dict[str, Any] = {}
    for capability in task.required_capabilities:
        snapshot = readiness.get(capability)
        capability_view[capability] = _json_safe(snapshot) if isinstance(snapshot, Mapping) else {"state": "UNKNOWN"}
        if not isinstance(snapshot, Mapping):
            missing_capabilities.append(capability)
        elif not _readiness_is_healthy(snapshot):
            state = str(snapshot.get("state", "UNKNOWN"))
            (stale_capabilities if state in {"STALE", "UNKNOWN", "NOT_READY"} else missing_capabilities).append(capability)
    optional_view: dict[str, Any] = {}
    for capability in task.optional_capabilities:
        snapshot = readiness.get(capability)
        optional_view[capability] = _json_safe(snapshot) if isinstance(snapshot, Mapping) else {"state": "UNKNOWN"}
    missing_permissions: list[str] = []
    denied_permissions: list[str] = []
    permission_view: dict[str, Any] = {}
    for permission in task.permission_needs:
        record = permissions.get(permission)
        permission_view[permission] = _json_safe(record) if isinstance(record, Mapping) else {"status": "MISSING"}
        if not isinstance(record, Mapping):
            missing_permissions.append(permission)
        elif str(record.get("status", "")).upper() in {"DENIED", "REJECTED"}:
            denied_permissions.append(permission)
        elif not _permission_is_approved(record):
            missing_permissions.append(permission)
    stale_context: list[str] = []
    context_view: dict[str, Any] = {}
    for reference in task.context_refs:
        record = contexts.get(reference)
        context_view[reference] = _json_safe(record) if isinstance(record, Mapping) else {"status": "UNKNOWN"}
        if not isinstance(record, Mapping) or str(record.get("status", "")).upper() not in {"CURRENT", "FRESH", "BOUND"}:
            stale_context.append(reference)
    reasons: list[str] = []
    owner_decision: dict[str, Any] | None = None
    if missing_capabilities:
        reasons.append("CAPABILITY_NOT_READY")
    if stale_capabilities:
        reasons.append("CAPABILITY_READINESS_UNKNOWN_OR_STALE")
    if denied_permissions:
        reasons.append("PERMISSION_DENIED")
    if missing_permissions:
        reasons.append("OWNER_PERMISSION_DECISION_REQUIRED")
        owner_decision = {
            "status": "PENDING",
            "question": "May this task use the explicitly listed permission scope?",
            "options": ["Allow only for this task", "Keep the task blocked"],
            "recommendation": "Keep the task blocked unless this permission is necessary for the stated acceptance.",
            "consequences": {
                "Allow only for this task": "The task may proceed only within its recorded permission scope.",
                "Keep the task blocked": "No permission is granted and the task remains paused.",
            },
            "approval_metadata": {
                "approval_boundary": "OWNER_ONLY",
                "permission_refs": list(missing_permissions),
                "auto_grant_permissions": False,
            },
            "permission_refs": list(missing_permissions),
            "requested_at": checked_at,
        }
    if stale_context:
        reasons.append("CONTEXT_POINTER_NOT_CURRENT")
    if missing_capabilities or stale_capabilities or denied_permissions or stale_context:
        status = "BLOCKED"
    elif missing_permissions:
        status = "WAITING_OWNER"
    else:
        status = "PASS"
    return {
        "schema": "p2p-task-preflight/1",
        "status": status,
        "task_id": task.task_id,
        "checked_at": checked_at,
        "required_capabilities": list(task.required_capabilities),
        "optional_capabilities": list(task.optional_capabilities),
        "capability_readiness": capability_view,
        "permission_needs": list(task.permission_needs),
        "permission_state": permission_view,
        "context_refs": list(task.context_refs),
        "context_state": context_view,
        "missing_capabilities": sorted(set(missing_capabilities)),
        "stale_capabilities": sorted(set(stale_capabilities)),
        "missing_permissions": sorted(set(missing_permissions)),
        "denied_permissions": sorted(set(denied_permissions)),
        "stale_context": sorted(set(stale_context)),
        "owner_decision": owner_decision,
        "reasons": reasons or ["ALL_REQUIRED_GATES_PASS"],
        "source_refs": ["capability-readiness", "permission-boundary", "context-pointers"],
    }


def _validate_lifecycle_event(value: Any, *, expected_to_state: str) -> None:
    """Validate one provenance-linked plan-lifecycle event.

    The only legal lifecycle transitions are ACTIVE -> CLOSED and
    ACTIVE -> SUPERSEDED.  A closed or superseded plan can never carry an
    event that leads back to ACTIVE, which is what keeps a closed plan
    from silently regaining ACTIVE authority.
    """

    if not isinstance(value, Mapping):
        raise TaskContractError("PLAN_LIFECYCLE_ENTRY_INVALID")
    allowed = {"schema", "at", "from_state", "to_state", "reason", "source_refs", "successor_ref"}
    unknown = sorted(str(key) for key in value if str(key) not in allowed)
    if unknown:
        raise TaskContractError("PLAN_LIFECYCLE_FIELDS_INVALID:" + ",".join(unknown))
    if value.get("schema") != PLAN_LIFECYCLE_EVENT_SCHEMA:
        raise TaskContractError("PLAN_LIFECYCLE_ENTRY_INVALID")
    if value.get("from_state") != "ACTIVE":
        raise TaskContractError("PLAN_LIFECYCLE_FROM_STATE_INVALID")
    if value.get("to_state") != expected_to_state:
        raise TaskContractError("PLAN_LIFECYCLE_TO_STATE_INVALID")
    _check_timestamp(value.get("at"), "plan_lifecycle.at")
    _required_text(value.get("reason"), "plan_lifecycle.reason", max_length=4096)
    _unique_refs(value.get("source_refs", ()), "plan_lifecycle.source_refs")
    if expected_to_state == "SUPERSEDED":
        _required_text(value.get("successor_ref"), "plan_lifecycle.successor_ref", max_length=1024)


@dataclass(frozen=True)
class TaskPlan:
    """A bounded Goal-scoped task projection."""

    goal_id: str
    logical_owner: LogicalOwner
    tasks: Mapping[str, TaskRecord]
    goal_requirement_refs: tuple[str, ...] = ()
    plan_scope: tuple[str, ...] = ()
    plan_non_scope: tuple[str, ...] = ()
    source_refs: tuple[str, ...] = ()
    plan_revision: int = 1
    plan_revisions: tuple[dict[str, Any], ...] = ()
    plan_lifecycle: str = "ACTIVE"
    plan_lifecycle_events: tuple[dict[str, Any], ...] = ()
    plan_identity: PlanIdentity | None = None
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        if self.plan_lifecycle not in PLAN_LIFECYCLE_STATES:
            raise TaskContractError("PLAN_LIFECYCLE_INVALID")
        if not isinstance(self.plan_lifecycle_events, tuple):
            raise TaskContractError("PLAN_LIFECYCLE_EVENTS_MUST_BE_TUPLE")
        if self.plan_lifecycle == "ACTIVE" and self.plan_lifecycle_events:
            raise TaskContractError("ACTIVE_PLAN_MUST_HAVE_NO_LIFECYCLE_EVENTS")
        if self.plan_lifecycle != "ACTIVE":
            if len(self.plan_lifecycle_events) != 1:
                raise TaskContractError("PLAN_LIFECYCLE_EVENTS_INVALID")
            _validate_lifecycle_event(self.plan_lifecycle_events[0], expected_to_state=self.plan_lifecycle)
        if self.plan_identity is not None and not isinstance(self.plan_identity, PlanIdentity):
            raise TaskContractError("PLAN_IDENTITY_INVALID")
        goal_id = _required_text(self.goal_id, "goal_id", max_length=512)
        if self.logical_owner.goal_id != goal_id:
            raise TaskContractError("LOGICAL_OWNER_GOAL_MISMATCH")
        if not isinstance(self.tasks, Mapping) or not self.tasks:
            raise TaskContractError("TASK_PLAN_EMPTY")
        if len(self.tasks) > 64:
            raise TaskContractError("TASK_PLAN_TOO_LARGE")
        for key, task in self.tasks.items():
            if not isinstance(task, TaskRecord):
                raise TaskContractError("TASK_PLAN_ENTRY_INVALID")
            if key != task.task_id or task.goal_id != goal_id:
                raise TaskContractError("TASK_PLAN_TASK_ID_OR_GOAL_MISMATCH")
            self._validate_task_invariants(task)
        validate_dependency_graph(self.tasks)
        _unique_refs(self.goal_requirement_refs, "goal_requirement_refs")
        _unique_refs(self.plan_scope, "plan_scope", required=True)
        _unique_refs(self.plan_non_scope, "plan_non_scope")
        _unique_refs(self.source_refs, "source_refs")
        if not isinstance(self.plan_revision, int) or self.plan_revision < 1:
            raise TaskContractError("PLAN_REVISION_INVALID")
        _check_timestamp(self.created_at, "created_at")
        _check_timestamp(self.updated_at, "updated_at")
        if not isinstance(self.plan_revisions, tuple):
            raise TaskContractError("PLAN_REVISIONS_MUST_BE_TUPLE")
        _assert_no_identity_fields(self.plan_revisions, path="plan_revisions")
        seen_revisions: set[int] = set()
        for revision in self.plan_revisions:
            if not isinstance(revision, Mapping) or revision.get("schema") != PLAN_REVISION_SCHEMA:
                raise TaskContractError("PLAN_REVISION_ENTRY_INVALID")
            number = revision.get("revision")
            if not isinstance(number, int) or number < 1 or number in seen_revisions:
                raise TaskContractError("PLAN_REVISION_NUMBER_INVALID")
            if number > self.plan_revision:
                raise TaskContractError("PLAN_REVISION_AHEAD_OF_PLAN")
            seen_revisions.add(number)
            _check_timestamp(revision.get("at"), "plan_revision.at")
            _required_text(revision.get("reason"), "plan_revision.reason", max_length=4096)
            _unique_refs(revision.get("source_refs", ()), "plan_revision.source_refs")
            if revision.get("prior_plan_hash") is not None:
                _assert_sha256(revision.get("prior_plan_hash"), "plan_revision.prior_plan_hash")
            _assert_sha256(revision.get("plan_base_hash"), "plan_revision.plan_base_hash")

    @staticmethod
    def _validate_task_invariants(task: TaskRecord) -> None:
        if task.status == "DONE" and not _completion_is_structurally_valid(task):
            raise TaskEvidenceError(f"DONE_REQUIRES_CURRENT_EVIDENCE:{task.task_id}")
        if task.status == "READY":
            if task.blocker is not None or _owner_decision_is_pending(task):
                raise TaskTransitionError(f"READY_GATE_PRESENT:{task.task_id}")
            if (task.required_capabilities or task.permission_needs) and (
                not isinstance(task.last_preflight, Mapping) or task.last_preflight.get("status") != "PASS"
            ):
                raise TaskGateError(f"READY_PREFLIGHT_REQUIRED:{task.task_id}")
        if task.status == "ACTIVE":
            if task.blocker is not None or _owner_decision_is_pending(task):
                raise TaskTransitionError(f"ACTIVE_GATE_PRESENT:{task.task_id}")
            if (task.required_capabilities or task.permission_needs) and (
                not isinstance(task.last_preflight, Mapping) or task.last_preflight.get("status") != "PASS"
            ):
                raise TaskGateError(f"ACTIVE_PREFLIGHT_REQUIRED:{task.task_id}")
        if task.status == "BLOCKED" and not isinstance(task.blocker, Mapping):
            raise TaskTransitionError(f"BLOCKED_REASON_REQUIRED:{task.task_id}")
        if task.status == "WAITING_OWNER" and not _owner_decision_is_pending(task):
            raise TaskTransitionError(f"OWNER_DECISION_REQUIRED:{task.task_id}")
        if task.status == "CANCELLED" and task.completion is not None:
            raise TaskTransitionError(f"CANCELLED_CANNOT_HAVE_COMPLETION:{task.task_id}")

    @classmethod
    def from_goal(
        cls,
        goal: Mapping[str, Any],
        task_specs: Sequence[Mapping[str, Any] | TaskRecord],
        *,
        now: str | None = None,
        plan_identity: PlanIdentity | Mapping[str, Any] | None = None,
    ) -> "TaskPlan":
        if not isinstance(goal, Mapping):
            raise TaskContractError("GOAL_CONTRACT_MUST_BE_OBJECT")
        goal_id = str(goal.get("goal_id") or goal.get("GOAL_ID") or "")
        _required_text(goal_id, "goal_id", max_length=512)
        if not isinstance(task_specs, (list, tuple)) or not task_specs:
            raise TaskContractError("TASK_SPECS_REQUIRED")
        requirement_refs: list[str] = []
        criteria = goal.get("completion_criteria", [])
        if isinstance(criteria, list):
            for item in criteria:
                if isinstance(item, Mapping) and item.get("criterion_id"):
                    requirement_refs.append(str(item["criterion_id"]))
        tasks: dict[str, TaskRecord] = {}
        timestamp = now or utc_now()
        for raw in task_specs:
            if isinstance(raw, TaskRecord):
                task = raw
            else:
                if not isinstance(raw, Mapping):
                    raise TaskContractError("TASK_SPEC_MUST_BE_OBJECT")
                task_payload = dict(raw)
                task_payload.setdefault("goal_id", goal_id)
                task_payload.setdefault("scope", goal.get("scope") or goal.get("constraints") or ["GOAL_SCOPED_TASK_WORK"])
                task_payload.setdefault("non_scope", goal.get("out_of_scope") or [])
                task = TaskRecord.from_mapping(task_payload)
            if task.goal_id != goal_id:
                raise TaskContractError(f"TASK_GOAL_MISMATCH:{task.task_id}")
            if task.task_id in tasks:
                raise TaskContractError(f"TASK_ID_DUPLICATE:{task.task_id}")
            if task.created_at != timestamp or task.updated_at != timestamp:
                task = replace(task, created_at=timestamp, updated_at=timestamp)
            tasks[task.task_id] = task
        plan_scope = tuple(str(item) for item in (goal.get("scope") or goal.get("constraints") or ["GOAL_SCOPED_TASK_WORK"]))
        if not plan_scope:
            plan_scope = ("GOAL_SCOPED_TASK_WORK",)
        plan_non_scope = tuple(str(item) for item in (goal.get("out_of_scope") or []))
        identity = (
            None
            if plan_identity is None
            else (plan_identity if isinstance(plan_identity, PlanIdentity) else PlanIdentity.from_mapping(plan_identity))
        )
        plan = cls(
            goal_id=goal_id,
            logical_owner=LogicalOwner.for_goal(goal_id),
            tasks=tasks,
            goal_requirement_refs=tuple(dict.fromkeys(requirement_refs)),
            plan_scope=plan_scope,
            plan_non_scope=plan_non_scope,
            source_refs=(".p2p/state/goal-contract.json",),
            created_at=timestamp,
            updated_at=timestamp,
            plan_identity=identity,
        )
        initial_hash = _sha256(plan.to_dict())
        return replace(
            plan,
            plan_revisions=(
                {
                    "schema": PLAN_REVISION_SCHEMA,
                    "revision": 1,
                    "at": timestamp,
                    "reason": "INITIAL_PLAN_FROM_GOAL",
                    "source_refs": list(plan.source_refs),
                    "prior_plan_hash": None,
                    "plan_base_hash": initial_hash,
                },
            ),
        )

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "TaskPlan":
        if not isinstance(value, Mapping):
            raise TaskContractError("TASK_PLAN_MUST_BE_OBJECT")
        allowed = {
            "schema",
            "goal_id",
            "logical_owner",
            "tasks",
            "goal_requirement_refs",
            "plan_scope",
            "plan_non_scope",
            "source_refs",
            "plan_revision",
            "plan_revisions",
            "plan_lifecycle",
            "plan_lifecycle_events",
            "plan_identity",
            "created_at",
            "updated_at",
        }
        unknown = sorted(str(key) for key in value if str(key) not in allowed)
        if unknown:
            raise TaskContractError("TASK_PLAN_FIELDS_INVALID:" + ",".join(unknown))
        if value.get("schema") not in {None, TASK_PLAN_SCHEMA}:
            raise TaskContractError("TASK_PLAN_SCHEMA_INVALID")
        raw_tasks = value.get("tasks")
        if not isinstance(raw_tasks, list):
            raise TaskContractError("TASK_PLAN_TASKS_MUST_BE_LIST")
        tasks: dict[str, TaskRecord] = {}
        for raw_task in raw_tasks:
            task = TaskRecord.from_mapping(raw_task)
            if task.task_id in tasks:
                raise TaskContractError(f"TASK_ID_DUPLICATE:{task.task_id}")
            tasks[task.task_id] = task
        revisions = value.get("plan_revisions", [])
        if not isinstance(revisions, list):
            raise TaskContractError("PLAN_REVISIONS_MUST_BE_LIST")
        lifecycle_events = value.get("plan_lifecycle_events", [])
        if not isinstance(lifecycle_events, list):
            raise TaskContractError("PLAN_LIFECYCLE_EVENTS_MUST_BE_LIST")
        raw_identity = value.get("plan_identity")
        return cls(
            goal_id=str(value.get("goal_id", "")),
            logical_owner=LogicalOwner.from_mapping(value.get("logical_owner", {})),
            tasks=tasks,
            goal_requirement_refs=tuple(value.get("goal_requirement_refs", ())),
            plan_scope=tuple(value.get("plan_scope", ())),
            plan_non_scope=tuple(value.get("plan_non_scope", ())),
            source_refs=tuple(value.get("source_refs", ())),
            plan_revision=int(value.get("plan_revision", 1)),
            plan_revisions=tuple(_copy_dict(item) or {} for item in revisions),
            plan_lifecycle=str(value.get("plan_lifecycle", "ACTIVE")),
            plan_lifecycle_events=tuple(_copy_dict(item) or {} for item in lifecycle_events),
            plan_identity=PlanIdentity.from_mapping(raw_identity) if isinstance(raw_identity, Mapping) else None,
            created_at=str(value.get("created_at", "")),
            updated_at=str(value.get("updated_at", "")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": TASK_PLAN_SCHEMA,
            "goal_id": self.goal_id,
            "logical_owner": self.logical_owner.to_dict(),
            "tasks": [self.tasks[task_id].to_dict() for task_id in sorted(self.tasks)],
            "goal_requirement_refs": list(self.goal_requirement_refs),
            "plan_scope": list(self.plan_scope),
            "plan_non_scope": list(self.plan_non_scope),
            "source_refs": list(self.source_refs),
            "plan_revision": self.plan_revision,
            "plan_revisions": [_json_safe(item) for item in self.plan_revisions],
            "plan_lifecycle": self.plan_lifecycle,
            "plan_lifecycle_events": [_json_safe(item) for item in self.plan_lifecycle_events],
            "plan_identity": None if self.plan_identity is None else self.plan_identity.to_dict(),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def canonical_hash(self) -> str:
        return _sha256(self.to_dict())

    def topological_order(self) -> tuple[str, ...]:
        return validate_dependency_graph(self.tasks)

    def _require_active(self) -> None:
        """Fail closed when a non-active plan is used as active authority."""

        if self.plan_lifecycle != "ACTIVE":
            raise TaskLifecycleError(f"PLAN_NOT_ACTIVE:{self.plan_lifecycle}")

    def close_plan(
        self,
        reason: str,
        *,
        source_refs: Iterable[str] = (),
        now: str | None = None,
    ) -> "TaskPlan":
        """Explicitly close this plan; it loses ACTIVE authority.

        The plan is retained, not deleted: it remains readable for explicit
        historical retrieval, but every mutating operation on it fails
        closed.  Continuation of closed work is a NEW plan that references
        this one through source refs.
        """

        self._require_active()
        timestamp = _check_timestamp(now or utc_now(), "plan_lifecycle.at")
        event = {
            "schema": PLAN_LIFECYCLE_EVENT_SCHEMA,
            "at": timestamp,
            "from_state": "ACTIVE",
            "to_state": "CLOSED",
            "reason": _required_text(reason, "plan_lifecycle.reason", max_length=4096),
            "source_refs": list(_unique_refs(tuple(str(item) for item in source_refs), "plan_lifecycle.source_refs")),
        }
        return replace(self, plan_lifecycle="CLOSED", plan_lifecycle_events=(event,), updated_at=timestamp)

    def supersede_plan(
        self,
        successor_ref: str,
        reason: str,
        *,
        source_refs: Iterable[str] = (),
        now: str | None = None,
    ) -> "TaskPlan":
        """Explicitly supersede this plan with a durable successor reference."""

        self._require_active()
        timestamp = _check_timestamp(now or utc_now(), "plan_lifecycle.at")
        event = {
            "schema": PLAN_LIFECYCLE_EVENT_SCHEMA,
            "at": timestamp,
            "from_state": "ACTIVE",
            "to_state": "SUPERSEDED",
            "reason": _required_text(reason, "plan_lifecycle.reason", max_length=4096),
            "source_refs": list(_unique_refs(tuple(str(item) for item in source_refs), "plan_lifecycle.source_refs")),
            "successor_ref": _required_text(successor_ref, "plan_lifecycle.successor_ref", max_length=1024),
        }
        return replace(self, plan_lifecycle="SUPERSEDED", plan_lifecycle_events=(event,), updated_at=timestamp)

    def bind_plan_identity(
        self,
        identity: PlanIdentity | Mapping[str, Any],
        *,
        now: str | None = None,
    ) -> "TaskPlan":
        """Bind the one exact durable identity for this plan (one-shot).

        A plan's identity is bound exactly once while the plan is active;
        it can never be silently rebound.  A re-bound identity is a NEW
        plan, not a mutation of this one.
        """

        self._require_active()
        if self.plan_identity is not None:
            raise TaskContractError("PLAN_IDENTITY_ALREADY_BOUND")
        normalized = identity if isinstance(identity, PlanIdentity) else PlanIdentity.from_mapping(identity)
        timestamp = _check_timestamp(now or utc_now(), "plan_identity.bound_at")
        return replace(self, plan_identity=normalized, updated_at=timestamp)

    def transition(
        self,
        task_id: str,
        target_status: str,
        *,
        now: str | None = None,
        blocker: Mapping[str, Any] | None = None,
        owner_decision: Mapping[str, Any] | None = None,
        completion: Mapping[str, Any] | None = None,
        checkpoint: Mapping[str, Any] | None = None,
        preflight: Mapping[str, Any] | None = None,
    ) -> "TaskPlan":
        self._require_active()
        task = self.tasks.get(task_id)
        if task is None:
            raise TaskTransitionError(f"TASK_NOT_FOUND:{task_id}")
        if target_status not in TASK_STATES:
            raise TaskTransitionError("TARGET_STATUS_INVALID")
        if target_status not in ALLOWED_TRANSITIONS[task.status]:
            raise TaskTransitionError(f"TRANSITION_NOT_ALLOWED:{task.status}->{target_status}")
        timestamp = now or utc_now()
        updates: dict[str, Any] = {"status": target_status, "updated_at": timestamp}
        if preflight is not None:
            updates["last_preflight"] = _copy_dict(preflight)
        if target_status == "BLOCKED":
            if not isinstance(blocker, Mapping) or not str(blocker.get("reason", "")).strip():
                raise TaskTransitionError("BLOCKER_REASON_REQUIRED")
            updates.update(blocker=_copy_dict(blocker), owner_decision=None)
        elif target_status == "WAITING_OWNER":
            if not isinstance(owner_decision, Mapping) or owner_decision.get("status") != "PENDING":
                raise TaskTransitionError("PENDING_OWNER_DECISION_REQUIRED")
            updates.update(owner_decision=_copy_dict(owner_decision), blocker=None)
        elif target_status == "DONE":
            updates.update(completion=_copy_dict(completion), blocker=None, owner_decision=None)
        elif target_status == "ACTIVE":
            if not self.dependencies_are_done(task_id):
                raise TaskTransitionError(f"DEPENDENCY_NOT_DONE:{task_id}")
            if task.required_capabilities or task.permission_needs:
                gate = preflight if isinstance(preflight, Mapping) else task.last_preflight
                if not isinstance(gate, Mapping) or gate.get("status") != "PASS":
                    raise TaskGateError("ACTIVE_REQUIRES_PASS_PREFLIGHT")
            updates.update(last_preflight=_copy_dict(preflight or task.last_preflight or {"status": "PASS", "reason": "NO_ADDITIONAL_GATE_REQUIRED"}), blocker=None, owner_decision=None)
        elif target_status in {"READY", "PLANNED"}:
            updates.update(blocker=None, owner_decision=None)
            if target_status == "READY" and not self.dependencies_are_done(task_id):
                raise TaskTransitionError(f"DEPENDENCY_NOT_DONE:{task_id}")
            if target_status == "READY" and (task.required_capabilities or task.permission_needs):
                gate = preflight if isinstance(preflight, Mapping) else task.last_preflight
                if not isinstance(gate, Mapping) or gate.get("status") != "PASS":
                    raise TaskGateError("READY_REQUIRES_PASS_PREFLIGHT")
        elif target_status == "CANCELLED":
            updates.update(blocker=None, owner_decision=None, completion=None)
        if target_status == "DONE" and completion is None:
            raise TaskEvidenceError("DONE_COMPLETION_REQUIRED")
        if checkpoint is not None:
            updates["checkpoint"] = _copy_dict(checkpoint)
        replacement = replace(task, **updates)
        next_tasks = dict(self.tasks)
        next_tasks[task_id] = replacement
        return replace(self, tasks=next_tasks, updated_at=timestamp)

    def dependencies_are_done(self, task_id: str) -> bool:
        task = self.tasks.get(task_id)
        if task is None:
            raise TaskGraphError(f"TASK_NOT_FOUND:{task_id}")
        return all(self.tasks[dependency].status == "DONE" and _completion_is_structurally_valid(self.tasks[dependency]) for dependency in task.dependencies)

    def complete(
        self,
        task_id: str,
        evidence_claims: Iterable[EvidenceClaim | Mapping[str, Any]],
        candidate_state: Any,
        *,
        now: str | None = None,
    ) -> "TaskPlan":
        self._require_active()
        task = self.tasks.get(task_id)
        if task is None:
            raise TaskEvidenceError(f"TASK_NOT_FOUND:{task_id}")
        if task.status != "ACTIVE":
            raise TaskEvidenceError(f"TASK_MUST_BE_ACTIVE_TO_COMPLETE:{task_id}")
        result = evaluate_task_completion(task, evidence_claims, candidate_state)
        return self.transition(task_id, "DONE", now=now, completion=result["completion"])

    def preflight(
        self,
        task_id: str,
        *,
        capability_readiness: Mapping[str, Mapping[str, Any]] | None = None,
        permission_state: Mapping[str, Mapping[str, Any]] | None = None,
        context_state: Mapping[str, Mapping[str, Any]] | None = None,
        now: str | None = None,
    ) -> tuple["TaskPlan", dict[str, Any]]:
        self._require_active()
        task = self.tasks.get(task_id)
        if task is None:
            raise TaskGateError(f"TASK_NOT_FOUND:{task_id}")
        result = evaluate_task_preflight(
            task,
            capability_readiness=capability_readiness,
            permission_state=permission_state,
            context_state=context_state,
            now=now,
        )
        timestamp = str(result["checked_at"])
        if result["status"] == "PASS":
            if task.status in {"PLANNED", "BLOCKED", "WAITING_OWNER"} and self.dependencies_are_done(task_id):
                return self.transition(task_id, "READY", now=timestamp, preflight=result), result
            if task.status in {"PLANNED", "READY", "ACTIVE"}:
                updated = replace(task, last_preflight=_copy_dict(result), updated_at=timestamp)
                tasks = dict(self.tasks)
                tasks[task_id] = updated
                return replace(self, tasks=tasks, updated_at=timestamp), result
            return self, result
        if result["status"] == "WAITING_OWNER":
            decision = result.get("owner_decision")
            if not isinstance(decision, Mapping):
                raise TaskGateError("OWNER_DECISION_PAYLOAD_REQUIRED")
            if task.status == "WAITING_OWNER":
                updated = replace(task, owner_decision=_copy_dict(decision), last_preflight=_copy_dict(result), updated_at=timestamp)
                tasks = dict(self.tasks)
                tasks[task_id] = updated
                return replace(self, tasks=tasks, updated_at=timestamp), result
            return self.transition(task_id, "WAITING_OWNER", now=timestamp, owner_decision=decision, preflight=result), result
        blocker = {
            "reason": ";".join(str(item) for item in result.get("reasons", [])) or "PREFLIGHT_BLOCKED",
            "preflight_status": result["status"],
            "checked_at": timestamp,
            "refs": list(result.get("source_refs", [])),
        }
        if task.status == "BLOCKED":
            updated = replace(task, blocker=blocker, owner_decision=None, last_preflight=_copy_dict(result), updated_at=timestamp)
            tasks = dict(self.tasks)
            tasks[task_id] = updated
            return replace(self, tasks=tasks, updated_at=timestamp), result
        return self.transition(task_id, "BLOCKED", now=timestamp, blocker=blocker, preflight=result), result

    def refresh_ready(self, *, now: str | None = None) -> "TaskPlan":
        """Promote only dependency-complete tasks with no extra gate.

        Capability and permission tasks remain PLANNED until an explicit
        current preflight is supplied.  This keeps a stale persisted plan from
        becoming executable merely because a session resumed.  A closed or
        superseded plan is never refreshed: it has no active authority.
        """

        self._require_active()
        current = self
        timestamp = now or utc_now()
        for task_id in current.topological_order():
            task = current.tasks[task_id]
            if task.status != "PLANNED" or task.required_capabilities or task.permission_needs:
                continue
            if current.dependencies_are_done(task_id):
                current = current.transition(task_id, "READY", now=timestamp)
        return current

    def revise(
        self,
        task_updates: Mapping[str, Mapping[str, Any] | TaskRecord] | None = None,
        *,
        add_tasks: Sequence[Mapping[str, Any] | TaskRecord] = (),
        remove_task_ids: Sequence[str] = (),
        source_refs: Iterable[str] = (),
        reason: str,
        now: str | None = None,
    ) -> "TaskPlan":
        """Create a provenance-linked plan revision without erasing history."""

        self._require_active()
        revision_reason = _required_text(reason, "plan_revision.reason", max_length=4096)
        timestamp = now or utc_now()
        next_tasks = dict(self.tasks)
        for task_id, raw in (task_updates or {}).items():
            if task_id not in next_tasks:
                raise TaskContractError(f"TASK_NOT_FOUND:{task_id}")
            existing = next_tasks[task_id]
            if isinstance(raw, TaskRecord):
                replacement = raw
            elif isinstance(raw, Mapping):
                payload = existing.to_dict()
                payload.update(dict(raw))
                payload.pop("schema", None)
                payload["goal_id"] = self.goal_id
                replacement = TaskRecord.from_mapping(payload)
            else:
                raise TaskContractError(f"TASK_REVISION_INVALID:{task_id}")
            if replacement.task_id != task_id or replacement.goal_id != self.goal_id:
                raise TaskContractError(f"TASK_REVISION_ID_OR_GOAL_MISMATCH:{task_id}")
            if existing.status == "DONE" and replacement.to_dict() != existing.to_dict():
                raise TaskContractError(f"DONE_TASK_IMMUTABLE:{task_id}")
            next_tasks[task_id] = replace(replacement, updated_at=timestamp)
        for raw in add_tasks:
            if isinstance(raw, TaskRecord):
                task = raw
            elif isinstance(raw, Mapping):
                payload = dict(raw)
                payload.setdefault("goal_id", self.goal_id)
                payload.setdefault("scope", self.plan_scope)
                payload.setdefault("non_scope", self.plan_non_scope)
                task = TaskRecord.from_mapping(payload)
            else:
                raise TaskContractError("TASK_REVISION_ADD_INVALID")
            if task.goal_id != self.goal_id or task.task_id in next_tasks:
                raise TaskContractError(f"TASK_REVISION_ADD_CONFLICT:{task.task_id}")
            next_tasks[task.task_id] = replace(task, created_at=timestamp, updated_at=timestamp)
        removals = tuple(dict.fromkeys(str(item) for item in remove_task_ids))
        for task_id in removals:
            if task_id not in next_tasks:
                raise TaskContractError(f"TASK_NOT_FOUND:{task_id}")
            if next_tasks[task_id].status == "DONE":
                raise TaskContractError(f"DONE_TASK_IMMUTABLE:{task_id}")
            if any(task_id in task.dependencies for task in next_tasks.values() if task.task_id != task_id):
                raise TaskGraphError(f"TASK_REMOVE_HAS_DEPENDENTS:{task_id}")
            del next_tasks[task_id]
        if not next_tasks:
            raise TaskContractError("TASK_REVISION_EMPTY")
        merged_sources = tuple(dict.fromkeys((*self.source_refs, *tuple(str(item) for item in source_refs))))
        draft = replace(
            self,
            tasks=next_tasks,
            source_refs=merged_sources,
            plan_revision=self.plan_revision + 1,
            plan_revisions=(),
            updated_at=timestamp,
        )
        base_hash = _sha256(draft.to_dict())
        entry = {
            "schema": PLAN_REVISION_SCHEMA,
            "revision": draft.plan_revision,
            "at": timestamp,
            "reason": revision_reason,
            "source_refs": list(merged_sources),
            "prior_plan_hash": self.canonical_hash(),
            "plan_base_hash": base_hash,
        }
        return replace(draft, plan_revisions=tuple((*self.plan_revisions, entry)))


def complete_task(
    plan: TaskPlan,
    task_id: str,
    evidence_claims: Iterable[EvidenceClaim | Mapping[str, Any]],
    candidate_state: Any,
    *,
    now: str | None = None,
) -> TaskPlan:
    """Pure convenience wrapper for evidence-backed task completion."""

    return plan.complete(task_id, evidence_claims, candidate_state, now=now)


def preflight_task(
    plan: TaskPlan,
    task_id: str,
    *,
    capability_readiness: Mapping[str, Mapping[str, Any]] | None = None,
    permission_state: Mapping[str, Mapping[str, Any]] | None = None,
    context_state: Mapping[str, Mapping[str, Any]] | None = None,
    now: str | None = None,
) -> tuple[TaskPlan, dict[str, Any]]:
    return plan.preflight(
        task_id,
        capability_readiness=capability_readiness,
        permission_state=permission_state,
        context_state=context_state,
        now=now,
    )


def request_owner_decision(
    plan: TaskPlan,
    task_id: str,
    question: str,
    *,
    options: Iterable[str] = (),
    source_refs: Iterable[str] = (),
    recommendation: str | None = None,
    consequences: Mapping[str, str] | None = None,
    approval_metadata: Mapping[str, Any] | None = None,
    now: str | None = None,
) -> TaskPlan:
    plan._require_active()
    task = plan.tasks.get(task_id)
    if task is None:
        raise TaskGateError(f"TASK_NOT_FOUND:{task_id}")
    if task.status in {"DONE", "CANCELLED"}:
        raise TaskGateError(f"TASK_TERMINAL:{task_id}")
    timestamp = now or utc_now()
    option_values = _unique_refs(tuple(options), "owner_decision.options")
    if len(option_values) not in {2, 3}:
        raise TaskGateError("OWNER_DECISION_REQUIRES_TWO_OR_THREE_OPTIONS")
    consequence_values = dict(consequences or {})
    if set(consequence_values) != set(option_values):
        consequence_values = {
            option: "This choice applies only to the bounded task and does not widen the Goal."
            for option in option_values
        }
    consequence_values = {
        str(key): _required_text(value, f"owner_decision.consequences.{key}", max_length=2048)
        for key, value in consequence_values.items()
    }
    safe_approval = _safe_mapping(approval_metadata, "owner_decision.approval_metadata") or {}
    safe_approval.update({"approval_boundary": safe_approval.get("approval_boundary", "OWNER_ONLY"), "auto_grant_permissions": False})
    decision = {
        "status": "PENDING",
        "question": _required_text(question, "owner_decision.question", max_length=4096),
        "options": list(option_values),
        "recommendation": _required_text(recommendation or "Choose the smallest option that satisfies the stated acceptance.", "owner_decision.recommendation", max_length=2048),
        "consequences": consequence_values,
        "approval_metadata": safe_approval,
        "source_refs": list(_unique_refs(tuple(source_refs), "owner_decision.source_refs")),
        "requested_at": timestamp,
    }
    if task.status == "WAITING_OWNER":
        updated = replace(task, owner_decision=decision, blocker=None, updated_at=timestamp)
        tasks = dict(plan.tasks)
        tasks[task_id] = updated
        return replace(plan, tasks=tasks, updated_at=timestamp)
    return plan.transition(task_id, "WAITING_OWNER", now=timestamp, owner_decision=decision)


def resolve_owner_decision(
    plan: TaskPlan,
    task_id: str,
    *,
    approved: bool,
    answer: str,
    decision_refs: Iterable[str] = (),
    now: str | None = None,
) -> TaskPlan:
    plan._require_active()
    task = plan.tasks.get(task_id)
    if task is None:
        raise TaskGateError(f"TASK_NOT_FOUND:{task_id}")
    if not _owner_decision_is_pending(task):
        raise TaskGateError(f"OWNER_DECISION_NOT_PENDING:{task_id}")
    timestamp = now or utc_now()
    refs = tuple(dict.fromkeys((*task.decision_refs, *tuple(str(item) for item in decision_refs))))
    record = dict(task.owner_decision or {})
    record.update({
        "status": "RESOLVED" if approved else "REJECTED",
        "answer": _required_text(answer, "owner_decision.answer", max_length=4096),
        "decision_refs": list(refs),
        "resolved_at": timestamp,
    })
    if approved:
        next_status = "PLANNED"
        if plan.dependencies_are_done(task_id) and not (task.required_capabilities or task.permission_needs):
            next_status = "READY"
        elif plan.dependencies_are_done(task_id) and isinstance(task.last_preflight, Mapping) and task.last_preflight.get("status") == "PASS":
            next_status = "READY"
        updated = replace(task, status=next_status, owner_decision=record, blocker=None, decision_refs=refs, updated_at=timestamp)
    else:
        updated = replace(
            task,
            status="BLOCKED",
            owner_decision=record,
            decision_refs=refs,
            blocker={"reason": "OWNER_DECISION_REJECTED", "decision_refs": list(refs), "resolved_at": timestamp},
            updated_at=timestamp,
        )
    tasks = dict(plan.tasks)
    tasks[task_id] = updated
    return replace(plan, tasks=tasks, updated_at=timestamp)


def beginner_owner_message(plan: TaskPlan, task_id: str) -> dict[str, Any]:
    task = plan.tasks.get(task_id)
    if task is None:
        raise TaskGateError(f"TASK_NOT_FOUND:{task_id}")
    decision = task.owner_decision if _owner_decision_is_pending(task) else None
    return {
        "schema": "p2p-task-owner-question/1",
        "task_id": task_id,
        "needs_owner_decision": decision is not None,
        "question": str(decision.get("question")) if isinstance(decision, Mapping) else None,
        "options": list(decision.get("options", [])) if isinstance(decision, Mapping) else [],
        "recommendation": str(decision.get("recommendation")) if isinstance(decision, Mapping) else None,
        "consequences": _json_safe(decision.get("consequences", {})) if isinstance(decision, Mapping) else {},
        "approval_metadata": _json_safe(decision.get("approval_metadata", {})) if isinstance(decision, Mapping) else {},
        "why": "The task is paused because an explicit scope or permission decision is required." if decision else "No owner decision is currently required.",
        "technical_questions": [],
        "auto_grant_permissions": False,
    }


def _validate_checkpoint(value: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise TaskStateError("CHECKPOINT_MUST_BE_OBJECT")
    unknown = sorted(str(key) for key in value if str(key) not in _CHECKPOINT_FIELDS)
    if unknown:
        raise TaskStateError("CHECKPOINT_FIELDS_INVALID:" + ",".join(unknown))
    checkpoint_ref = _required_text(value.get("checkpoint_ref"), "checkpoint.checkpoint_ref", max_length=1024)
    state_fingerprint = _assert_sha256(value.get("state_fingerprint"), "checkpoint.state_fingerprint")
    classification = str(value.get("recovery_classification", ""))
    if classification not in RESUME_CLASSIFICATIONS:
        raise TaskStateError("CHECKPOINT_CLASSIFICATION_INVALID")
    next_step = _required_text(value.get("next_safe_step"), "checkpoint.next_safe_step", max_length=4096)
    captured_at = _check_timestamp(value.get("captured_at"), "checkpoint.captured_at")
    completed_refs = _unique_refs(value.get("completed_refs", ()), "checkpoint.completed_refs")
    pending_refs = _unique_refs(value.get("pending_refs", ()), "checkpoint.pending_refs")
    evidence = value.get("evidence_fingerprints", {})
    if not isinstance(evidence, Mapping):
        raise TaskStateError("CHECKPOINT_EVIDENCE_FINGERPRINTS_INVALID")
    evidence_fingerprints = {str(key): _assert_sha256(item, f"checkpoint.evidence_fingerprints.{key}") for key, item in evidence.items()}
    notes = _safe_text(value.get("notes"), "checkpoint.notes", max_length=4096)
    return {
        "checkpoint_ref": checkpoint_ref,
        "state_fingerprint": state_fingerprint,
        "recovery_classification": classification,
        "next_safe_step": next_step,
        "completed_refs": list(completed_refs),
        "pending_refs": list(pending_refs),
        "evidence_fingerprints": dict(sorted(evidence_fingerprints.items())),
        "captured_at": captured_at,
        "notes": notes,
    }


def checkpoint_task(plan: TaskPlan, task_id: str, checkpoint: Mapping[str, Any], *, now: str | None = None) -> TaskPlan:
    plan._require_active()
    task = plan.tasks.get(task_id)
    if task is None:
        raise TaskStateError(f"TASK_NOT_FOUND:{task_id}")
    if task.status in {"DONE", "CANCELLED"}:
        raise TaskStateError(f"TASK_TERMINAL:{task_id}")
    normalized = _validate_checkpoint(checkpoint)
    timestamp = now or normalized["captured_at"]
    lineage = dict(task.execution_lineage)
    lineage_refs = list(_unique_refs(lineage.get("refs", ()), "execution_lineage.refs"))
    if normalized["checkpoint_ref"] not in lineage_refs:
        lineage_refs.append(normalized["checkpoint_ref"])
    lineage.update({"status": "OBSERVED", "refs": lineage_refs})
    updated = replace(task, checkpoint=normalized, execution_lineage=lineage, updated_at=timestamp)
    tasks = dict(plan.tasks)
    tasks[task_id] = updated
    return replace(plan, tasks=tasks, updated_at=timestamp)


def classify_resume(
    task: TaskRecord,
    *,
    current_state_fingerprint: str | None = None,
    current_evidence_fingerprints: Mapping[str, str] | None = None,
    current_preflight: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if not isinstance(task, TaskRecord):
        raise TaskStateError("TASK_RECORD_REQUIRED")
    if task.status == "DONE":
        return {"schema": "p2p-task-resume/1", "task_id": task.task_id, "resume_classification": "DONE", "reason": "TASK_ALREADY_DONE", "automatic_start": False}
    if task.status == "CANCELLED":
        return {"schema": "p2p-task-resume/1", "task_id": task.task_id, "resume_classification": "BLOCKED", "reason": "TASK_CANCELLED", "automatic_start": False}
    if task.status == "WAITING_OWNER" or _owner_decision_is_pending(task):
        return {"schema": "p2p-task-resume/1", "task_id": task.task_id, "resume_classification": "BLOCKED", "reason": "OWNER_DECISION_PENDING", "automatic_start": False}
    checkpoint = task.checkpoint
    if not isinstance(checkpoint, Mapping):
        return {"schema": "p2p-task-resume/1", "task_id": task.task_id, "resume_classification": "UNKNOWN", "reason": "NO_CHECKPOINT", "automatic_start": False}
    classification = str(checkpoint.get("recovery_classification", "UNKNOWN"))
    if classification == "BLOCKED" or task.status == "BLOCKED":
        return {"schema": "p2p-task-resume/1", "task_id": task.task_id, "resume_classification": "BLOCKED", "reason": "CHECKPOINT_OR_TASK_BLOCKED", "checkpoint_ref": checkpoint.get("checkpoint_ref"), "automatic_start": False}
    if classification == "UNKNOWN":
        return {"schema": "p2p-task-resume/1", "task_id": task.task_id, "resume_classification": "UNKNOWN", "reason": "CHECKPOINT_UNCERTAIN", "checkpoint_ref": checkpoint.get("checkpoint_ref"), "automatic_start": False}
    expected_state = str(checkpoint.get("state_fingerprint", ""))
    if current_state_fingerprint is not None and str(current_state_fingerprint).lower() != expected_state.lower():
        return {"schema": "p2p-task-resume/1", "task_id": task.task_id, "resume_classification": "NEEDS_RECHECK", "reason": "STATE_FINGERPRINT_CHANGED", "checkpoint_ref": checkpoint.get("checkpoint_ref"), "automatic_start": False}
    expected_evidence = checkpoint.get("evidence_fingerprints", {})
    if current_evidence_fingerprints is not None and dict(current_evidence_fingerprints) != dict(expected_evidence):
        return {"schema": "p2p-task-resume/1", "task_id": task.task_id, "resume_classification": "NEEDS_RECHECK", "reason": "EVIDENCE_FINGERPRINT_CHANGED", "checkpoint_ref": checkpoint.get("checkpoint_ref"), "automatic_start": False}
    if task.required_capabilities or task.permission_needs:
        if not isinstance(current_preflight, Mapping) or current_preflight.get("status") != "PASS":
            return {"schema": "p2p-task-resume/1", "task_id": task.task_id, "resume_classification": "NEEDS_RECHECK", "reason": "CURRENT_PREFLIGHT_REQUIRED", "checkpoint_ref": checkpoint.get("checkpoint_ref"), "automatic_start": False}
    if classification == "NEEDS_RECHECK":
        result = "NEEDS_RECHECK"
        reason = "CHECKPOINT_REQUESTS_RECHECK"
    else:
        result = "SAFE_TO_RESUME"
        reason = "CHECKPOINT_AND_CURRENT_BINDINGS_MATCH"
    return {
        "schema": "p2p-task-resume/1",
        "task_id": task.task_id,
        "resume_classification": result,
        "reason": reason,
        "checkpoint_ref": checkpoint.get("checkpoint_ref"),
        "next_safe_step": checkpoint.get("next_safe_step"),
        "automatic_start": False,
    }


def resume_summary(
    plan: TaskPlan,
    *,
    current_state_fingerprints: Mapping[str, str] | None = None,
    current_evidence_fingerprints: Mapping[str, Mapping[str, str]] | None = None,
    current_preflights: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    current_state_fingerprints = current_state_fingerprints or {}
    current_evidence_fingerprints = current_evidence_fingerprints or {}
    current_preflights = current_preflights or {}
    items = [
        classify_resume(
            plan.tasks[task_id],
            current_state_fingerprint=current_state_fingerprints.get(task_id),
            current_evidence_fingerprints=current_evidence_fingerprints.get(task_id),
            current_preflight=current_preflights.get(task_id),
        )
        for task_id in plan.topological_order()
    ]
    return {
        "schema": "p2p-task-resume-summary/1",
        "goal_id": plan.goal_id,
        "plan_hash": plan.canonical_hash(),
        "automatic_start": False,
        "tasks": items,
        "safe_to_resume": [item["task_id"] for item in items if item["resume_classification"] == "SAFE_TO_RESUME"],
        "needs_recheck": [item["task_id"] for item in items if item["resume_classification"] == "NEEDS_RECHECK"],
        "blocked": [item["task_id"] for item in items if item["resume_classification"] == "BLOCKED"],
        "unknown": [item["task_id"] for item in items if item["resume_classification"] == "UNKNOWN"],
    }


def next_safe_task(plan: TaskPlan) -> TaskRecord | None:
    if plan.plan_lifecycle != "ACTIVE":
        return None
    for task_id in plan.topological_order():
        task = plan.tasks[task_id]
        if task.status != "READY" or task.blocker is not None or _owner_decision_is_pending(task):
            continue
        if not plan.dependencies_are_done(task_id):
            continue
        if (task.required_capabilities or task.permission_needs) and (
            not isinstance(task.last_preflight, Mapping) or task.last_preflight.get("status") != "PASS"
        ):
            continue
        return task
    return None


def dependency_handoff(plan: TaskPlan, completed_task_id: str) -> dict[str, Any]:
    completed = plan.tasks.get(completed_task_id)
    if completed is None:
        raise TaskGraphError(f"TASK_NOT_FOUND:{completed_task_id}")
    if completed.status != "DONE" or not _completion_is_structurally_valid(completed):
        raise TaskGraphError(f"TASK_NOT_COMPLETED:{completed_task_id}")
    downstream: list[dict[str, Any]] = []
    for task_id in plan.topological_order():
        task = plan.tasks[task_id]
        if completed_task_id not in task.dependencies:
            continue
        dependencies_done = plan.dependencies_are_done(task_id)
        gate = "PREFLIGHT_REQUIRED" if task.required_capabilities or task.permission_needs else "NONE"
        downstream.append({
            "task_id": task_id,
            "status": task.status,
            "dependencies_done": dependencies_done,
            "next_gate": gate,
            "owner_decision_pending": _owner_decision_is_pending(task),
            "required_capabilities": list(task.required_capabilities),
            "permission_needs": list(task.permission_needs),
        })
    return {
        "schema": "p2p-task-dependency-handoff/1",
        "goal_id": plan.goal_id,
        "plan_hash": plan.canonical_hash(),
        "completed_task_id": completed_task_id,
        "downstream_tasks": downstream,
        "automatic_start": False,
    }


def is_active_authority(plan: TaskPlan) -> bool:
    """True only when the plan is in the ACTIVE lifecycle."""

    if not isinstance(plan, TaskPlan):
        raise TaskContractError("TASK_PLAN_REQUIRED")
    return plan.plan_lifecycle == "ACTIVE"


def close_plan(
    plan: TaskPlan,
    reason: str,
    *,
    source_refs: Iterable[str] = (),
    now: str | None = None,
) -> TaskPlan:
    """Pure convenience wrapper: explicitly close a plan."""

    return plan.close_plan(reason, source_refs=source_refs, now=now)


def supersede_plan(
    plan: TaskPlan,
    successor_ref: str,
    reason: str,
    *,
    source_refs: Iterable[str] = (),
    now: str | None = None,
) -> TaskPlan:
    """Pure convenience wrapper: explicitly supersede a plan."""

    return plan.supersede_plan(successor_ref, reason, source_refs=source_refs, now=now)


def bind_plan_identity(
    plan: TaskPlan,
    identity: PlanIdentity | Mapping[str, Any],
    *,
    now: str | None = None,
) -> TaskPlan:
    """Pure convenience wrapper: bind the one exact durable plan identity."""

    return plan.bind_plan_identity(identity, now=now)


def resolve_authoritative_plan(
    candidates: Iterable[TaskPlan | Mapping[str, Any]],
    binding: PlanIdentity | Mapping[str, Any],
) -> dict[str, Any]:
    """Determine the single authoritative plan for an exact durable binding.

    Exact durable identity -- repository + workstream + current durable
    subject, plus source SHA / tree / PR where the binding supplies them --
    outranks semantic text similarity.  A candidate whose identity does not
    match exactly is simply ineligible; similarity is never consulted.  A
    plan that is closed or superseded can never win, so a closed plan cannot
    silently regain active authority through resolution.
    """

    bind = binding if isinstance(binding, PlanIdentity) else PlanIdentity.from_mapping(binding)
    eligible: list[TaskPlan] = []
    diagnostics: list[dict[str, Any]] = []
    for index, raw in enumerate(candidates):
        label = f"candidate-{index}"
        if isinstance(raw, TaskPlan):
            plan = raw
        else:
            try:
                plan = TaskPlan.from_mapping(raw)
            except TaskStateError as exc:
                diagnostics.append({"candidate": label, "status": "INVALID_PLAN", "detail": str(exc)})
                continue
        entry: dict[str, Any] = {
            "candidate": label,
            "goal_id": plan.goal_id,
            "plan_hash": plan.canonical_hash(),
            "plan_lifecycle": plan.plan_lifecycle,
        }
        identity = plan.plan_identity
        if identity is None:
            entry["status"] = "UNBOUND"
            diagnostics.append(entry)
            continue
        if not (
            identity.repository.casefold() == bind.repository.casefold()
            and identity.workstream.casefold() == bind.workstream.casefold()
            and identity.subject.casefold() == bind.subject.casefold()
        ):
            entry["status"] = "IDENTITY_MISMATCH"
            diagnostics.append(entry)
            continue
        field_mismatches = [
            field_name
            for field_name in ("source_sha256", "source_tree", "pr")
            if getattr(bind, field_name) and getattr(identity, field_name).casefold() != getattr(bind, field_name).casefold()
        ]
        if field_mismatches:
            entry["status"] = "BINDING_FIELD_MISMATCH"
            entry["fields"] = field_mismatches
            diagnostics.append(entry)
            continue
        if plan.plan_lifecycle != "ACTIVE":
            entry["status"] = f"PLAN_NOT_ACTIVE:{plan.plan_lifecycle}"
            diagnostics.append(entry)
            continue
        entry["status"] = "ELIGIBLE"
        diagnostics.append(entry)
        eligible.append(plan)
    if len(eligible) > 1:
        status = "AUTHORITY_CONFLICT"
        selected: TaskPlan | None = None
    elif len(eligible) == 1:
        status = "PASS"
        selected = eligible[0]
    else:
        status = "NOT_FOUND"
        selected = None
    result: dict[str, Any] = {
        "schema": PLAN_AUTHORITY_RESOLUTION_SCHEMA,
        "status": status,
        "binding": bind.to_dict(),
        "similarity_used": False,
        "candidates": diagnostics,
    }
    if selected is not None:
        result["selected_plan"] = {
            "goal_id": selected.goal_id,
            "plan_hash": selected.canonical_hash(),
            "plan_revision": selected.plan_revision,
            "plan_lifecycle": selected.plan_lifecycle,
            "plan_identity": selected.plan_identity.to_dict() if selected.plan_identity is not None else None,
        }
    return result


class TaskStateStore:
    """Atomic durable adapter over task-state.json and the existing ledger.

    The store is intentionally synchronous and foreground-only.  It never
    spawns work, owns a process, creates a worker, or writes a second event
    ledger.  A corrupt or mismatched state file is a control-plane error and is
    never silently replaced.
    """

    def __init__(self, root: str | Path, *, protected_roots: Iterable[str | Path] = ()) -> None:
        from pathlib import Path

        project = Path(root).expanduser().resolve()
        if not project.is_dir():
            raise TaskControlPlaneError(f"PROJECT_ROOT_NOT_FOUND:{project}")
        roots = tuple(Path(item).expanduser().resolve() for item in protected_roots)
        if roots:
            try:
                assert_isolated_target(project, roots)
            except ValueError as exc:
                raise TaskControlPlaneError(str(exc)) from exc
        self.root = project
        self.state_path = project / STATE_RELATIVE_PATH
        self.ledger_path = project / LEDGER_RELATIVE_PATH
        lock_key = str(project).casefold()
        with _STORE_LOCKS_GUARD:
            self._lock = _STORE_LOCKS.setdefault(lock_key, threading.RLock())

    def _read_state_payload(self) -> dict[str, Any] | None:
        if not self.state_path.exists():
            return None
        if not self.state_path.is_file() or self.state_path.is_symlink():
            raise TaskControlPlaneError("TASK_STATE_PATH_INVALID")
        try:
            raw = json.loads(self.state_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise TaskControlPlaneError(f"TASK_STATE_UNREADABLE:{exc}") from exc
        if not isinstance(raw, Mapping):
            raise TaskControlPlaneError("TASK_STATE_MUST_BE_OBJECT")
        allowed = {"schema", "plan", "plan_hash", "saved_at", "state_ref"}
        unknown = sorted(str(key) for key in raw if str(key) not in allowed)
        if unknown:
            raise TaskControlPlaneError("TASK_STATE_FIELDS_INVALID:" + ",".join(unknown))
        if raw.get("schema") != TASK_STATE_SCHEMA:
            raise TaskControlPlaneError("TASK_STATE_SCHEMA_INVALID")
        plan_payload = raw.get("plan")
        try:
            plan = TaskPlan.from_mapping(plan_payload) if isinstance(plan_payload, Mapping) else None
        except TaskStateError as exc:
            raise TaskControlPlaneError(f"TASK_STATE_PLAN_INVALID:{exc}") from exc
        if plan is None:
            raise TaskControlPlaneError("TASK_STATE_PLAN_REQUIRED")
        if raw.get("plan_hash") != plan.canonical_hash():
            raise TaskControlPlaneError("TASK_STATE_PLAN_HASH_MISMATCH")
        if raw.get("state_ref") not in {None, STATE_RELATIVE_PATH}:
            raise TaskControlPlaneError("TASK_STATE_REF_INVALID")
        saved_at = raw.get("saved_at")
        if saved_at is not None:
            _check_timestamp(saved_at, "task_state.saved_at")
        return dict(raw)

    def load(self) -> TaskPlan | None:
        with self._lock:
            payload = self._read_state_payload()
            if payload is None:
                return None
            plan_payload = payload.get("plan")
            return TaskPlan.from_mapping(plan_payload)

    def require(self) -> TaskPlan:
        with self._lock:
            plan = self.load()
            if plan is None:
                raise TaskControlPlaneError(f"TASK_STATE_NOT_INITIALIZED:{STATE_RELATIVE_PATH}")
            return plan

    @staticmethod
    def _safe_event_details(details: Mapping[str, Any] | None) -> dict[str, Any]:
        if details is None:
            return {}
        if not isinstance(details, Mapping):
            raise TaskControlPlaneError("TASK_EVENT_DETAILS_MUST_BE_OBJECT")
        _assert_no_identity_fields(details, path="event.details")
        safe = _safe_mapping(details, "event.details")
        return safe or {}

    def _append_event(
        self,
        plan: TaskPlan,
        event_name: str,
        *,
        task_id: str | None = None,
        details: Mapping[str, Any] | None = None,
        at: str | None = None,
    ) -> None:
        event = {
            "schema_version": "p2p-execution-event/1",
            "task_state_schema": TASK_EVENT_SCHEMA,
            "at": _check_timestamp(at or utc_now(), "task_event.at"),
            "event": _required_text(event_name, "task_event.event", max_length=256),
            "goal_id": plan.goal_id,
            "plan_hash": plan.canonical_hash(),
            "state_ref": STATE_RELATIVE_PATH,
            "task_id": task_id,
            "details": self._safe_event_details(details),
            "automatic_start": False,
            "background_execution": False,
            "process_survives_session": False,
        }
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with self.ledger_path.open("a", encoding="utf-8", newline="\n") as handle:
                handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
        except OSError as exc:
            raise TaskControlPlaneError(f"TASK_EVENT_APPEND_FAILED:{exc}") from exc

    def save(
        self,
        plan: TaskPlan,
        *,
        event_name: str = "task_plan_saved",
        task_id: str | None = None,
        details: Mapping[str, Any] | None = None,
        at: str | None = None,
    ) -> TaskPlan:
        with self._lock:
            if not isinstance(plan, TaskPlan):
                raise TaskControlPlaneError("TASK_PLAN_REQUIRED")
            # Loading first is deliberate: invalid or another-goal state must not
            # be overwritten by a recovery attempt.
            existing = self.load()
            if existing is not None and existing.goal_id != plan.goal_id:
                raise TaskControlPlaneError(f"TASK_STATE_GOAL_MISMATCH:{existing.goal_id}:{plan.goal_id}")
            if existing is not None and existing.canonical_hash() == plan.canonical_hash():
                return existing
            saved_at = _check_timestamp(at or utc_now(), "task_state.saved_at")
            payload = {
                "schema": TASK_STATE_SCHEMA,
                "state_ref": STATE_RELATIVE_PATH,
                "plan": plan.to_dict(),
                "plan_hash": plan.canonical_hash(),
                "saved_at": saved_at,
            }
            self.state_path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.state_path.with_name(self.state_path.name + ".tmp")
            try:
                temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
                temporary.replace(self.state_path)
            except OSError as exc:
                raise TaskControlPlaneError(f"TASK_STATE_WRITE_FAILED:{exc}") from exc
            self._append_event(plan, event_name, task_id=task_id, details=details, at=saved_at)
            return plan

    def initialize(self, plan: TaskPlan, *, at: str | None = None) -> TaskPlan:
        with self._lock:
            if self.state_path.exists():
                existing = self.load()
                if existing is None:
                    raise TaskControlPlaneError("TASK_STATE_EXISTS_BUT_EMPTY")
                if existing.canonical_hash() != plan.canonical_hash():
                    raise TaskControlPlaneError("TASK_STATE_ALREADY_INITIALIZED")
                return existing
            return self.save(plan, event_name="task_plan_initialized", at=at)

    def transition(self, task_id: str, target_status: str, *, now: str | None = None, **kwargs: Any) -> TaskPlan:
        with self._lock:
            current = self.require()
            previous = current.tasks.get(task_id)
            if previous is None:
                raise TaskTransitionError(f"TASK_NOT_FOUND:{task_id}")
            updated = current.transition(task_id, target_status, now=now, **kwargs)
            return self.save(
                updated,
                event_name="task_transition",
                task_id=task_id,
                details={"from_status": previous.status, "to_status": target_status},
                at=now,
            )

    def preflight(self, task_id: str, **kwargs: Any) -> tuple[TaskPlan, dict[str, Any]]:
        with self._lock:
            current = self.require()
            updated, result = preflight_task(current, task_id, **kwargs)
            if updated.canonical_hash() != current.canonical_hash():
                updated = self.save(updated, event_name="task_preflight", task_id=task_id, details={"status": result["status"]}, at=result["checked_at"])
            return updated, result

    def complete(
        self,
        task_id: str,
        evidence_claims: Iterable[EvidenceClaim | Mapping[str, Any]],
        candidate_state: Any,
        *,
        now: str | None = None,
    ) -> TaskPlan:
        with self._lock:
            current = self.require()
            updated = complete_task(current, task_id, evidence_claims, candidate_state, now=now)
            return self.save(updated, event_name="task_completed", task_id=task_id, details={"status": "DONE"}, at=now)

    def checkpoint(self, task_id: str, checkpoint: Mapping[str, Any], *, now: str | None = None) -> TaskPlan:
        with self._lock:
            current = self.require()
            updated = checkpoint_task(current, task_id, checkpoint, now=now)
            return self.save(updated, event_name="task_checkpoint", task_id=task_id, details={"checkpoint_ref": checkpoint.get("checkpoint_ref")}, at=now)

    def revise(self, *args: Any, **kwargs: Any) -> TaskPlan:
        with self._lock:
            current = self.require()
            updated = current.revise(*args, **kwargs)
            return self.save(updated, event_name="task_plan_revised", details={"plan_revision": updated.plan_revision}, at=kwargs.get("now"))

    def close_plan(self, reason: str, *, source_refs: Iterable[str] = (), at: str | None = None) -> TaskPlan:
        """Persist an explicit plan closure; the plan loses active authority."""

        with self._lock:
            current = self.require()
            updated = current.close_plan(reason, source_refs=source_refs, now=at)
            return self.save(
                updated,
                event_name="task_plan_closed",
                details={"from_state": "ACTIVE", "to_state": "CLOSED", "reason": reason},
                at=at,
            )

    def supersede_plan(self, successor_ref: str, reason: str, *, source_refs: Iterable[str] = (), at: str | None = None) -> TaskPlan:
        """Persist an explicit plan supersession with a durable successor ref."""

        with self._lock:
            current = self.require()
            updated = current.supersede_plan(successor_ref, reason, source_refs=source_refs, now=at)
            return self.save(
                updated,
                event_name="task_plan_superseded",
                details={"from_state": "ACTIVE", "to_state": "SUPERSEDED", "successor_ref": successor_ref, "reason": reason},
                at=at,
            )

    def record_event(
        self,
        event_name: str,
        *,
        task_id: str | None = None,
        details: Mapping[str, Any] | None = None,
        at: str | None = None,
    ) -> dict[str, Any]:
        """Append a bounded event to the existing execution ledger."""

        with self._lock:
            plan = self.require()
            timestamp = _check_timestamp(at or utc_now(), "task_event.at")
            self._append_event(plan, event_name, task_id=task_id, details=details, at=timestamp)
            return {"status": "PASS", "event": event_name, "task_id": task_id, "plan_hash": plan.canonical_hash(), "at": timestamp}

    def read_events(self) -> dict[str, Any]:
        with self._lock:
            if not self.ledger_path.exists():
                return {"schema": "p2p-task-event-query/1", "status": "NOT_INITIALIZED", "events": [], "diagnostics": [], "ledger": LEDGER_RELATIVE_PATH}
            try:
                lines = self.ledger_path.read_text(encoding="utf-8").splitlines()
            except (OSError, UnicodeError) as exc:
                raise TaskControlPlaneError(f"TASK_LEDGER_UNREADABLE:{exc}") from exc
            events: list[dict[str, Any]] = []
            diagnostics: list[dict[str, Any]] = []
            for line_number, line in enumerate(lines, 1):
                if not line.strip():
                    continue
                try:
                    item = json.loads(line)
                except json.JSONDecodeError:
                    diagnostics.append({"line": line_number, "status": "INVALID_JSON"})
                    continue
                if not isinstance(item, Mapping) or item.get("task_state_schema") != TASK_EVENT_SCHEMA:
                    continue
                if not item.get("plan_hash") or not item.get("goal_id"):
                    diagnostics.append({"line": line_number, "status": "INVALID_TASK_EVENT"})
                    continue
                events.append({"line": line_number, **dict(item)})
            return {
                "schema": "p2p-task-event-query/1",
                "status": "PASS" if not diagnostics else "PARTIAL",
                "events": events,
                "diagnostics": diagnostics,
                "ledger": LEDGER_RELATIVE_PATH,
            }

    def resume(self, **kwargs: Any) -> dict[str, Any]:
        return resume_summary(self.require(), **kwargs)


__all__ = [
    "TASK_STATE_SCHEMA",
    "TASK_PLAN_SCHEMA",
    "TASK_EVENT_SCHEMA",
    "PLAN_LIFECYCLE_EVENT_SCHEMA",
    "PLAN_IDENTITY_SCHEMA",
    "PLAN_AUTHORITY_RESOLUTION_SCHEMA",
    "STATE_RELATIVE_PATH",
    "LEDGER_RELATIVE_PATH",
    "TASK_STATES",
    "OWNER_DECISION_STATES",
    "PREFLIGHT_STATES",
    "RESUME_CLASSIFICATIONS",
    "ALLOWED_TRANSITIONS",
    "PLAN_LIFECYCLE_STATES",
    "TaskStateError",
    "TaskContractError",
    "TaskGraphError",
    "TaskTransitionError",
    "TaskEvidenceError",
    "TaskGateError",
    "TaskControlPlaneError",
    "TaskLifecycleError",
    "LogicalOwner",
    "PlanIdentity",
    "TaskRecord",
    "TaskPlan",
    "EvidenceClaim",
    "evaluate_task_completion",
    "evaluate_task_preflight",
    "complete_task",
    "preflight_task",
    "request_owner_decision",
    "resolve_owner_decision",
    "beginner_owner_message",
    "checkpoint_task",
    "classify_resume",
    "resume_summary",
    "next_safe_task",
    "dependency_handoff",
    "is_active_authority",
    "close_plan",
    "supersede_plan",
    "bind_plan_identity",
    "resolve_authoritative_plan",
    "TaskStateStore",
    "validate_dependency_graph",
    "utc_now",
]
