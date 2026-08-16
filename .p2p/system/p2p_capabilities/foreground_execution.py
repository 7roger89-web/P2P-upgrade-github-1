"""Bounded, synchronous foreground execution over the C11 task state.

This module is intentionally a control-plane adapter.  It selects one durable
task, records an execution intent, performs one caller-supplied direct action
inside a finite scope and budget, and asks a separate read-only verifier for
current evidence before using the C11 ``DONE`` transition.  It never starts a
background process, creates a worker, delegates to an agent, opens a network
connection, or creates a second ledger.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
import fnmatch
import hashlib
import inspect
import json
import math
import os
from pathlib import Path
import re
import tempfile
import time
from typing import Any, Callable, Iterable, Mapping, Sequence
import uuid

from .evidence import EvidenceClaim
from .task_state import (
    TaskControlPlaneError,
    TaskGateError,
    TaskPlan,
    TaskRecord,
    TaskStateError,
    TaskStateStore,
    classify_resume,
    next_safe_task,
    request_owner_decision,
    utc_now,
)


FOREGROUND_INTENT_SCHEMA = "p2p-foreground-execution-intent/1"
FOREGROUND_RECEIPT_SCHEMA = "p2p-foreground-execution-receipt/1"
FOREGROUND_CHECKPOINT_SCHEMA = "p2p-foreground-execution-checkpoint/1"
FOREGROUND_RESULT_SCHEMA = "p2p-foreground-execution-result/1"
FOREGROUND_STATE_RELATIVE_ROOT = ".p2p/state/foreground-executions"
FOREGROUND_EXECUTION_STRATEGY = "DIRECT"
DELEGATION_STATUS = "DEFERRED_NOT_CERTIFIED"

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_EXECUTION_ID_RE = re.compile(r"^fg-[a-z0-9][a-z0-9-]{7,127}$")
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
    "child_agents",
    "delegated_children",
}
_PROTECTED_PREFIXES = (
    ".git",
    ".p2p/state",
    ".p2p/install-backups",
    "source/8.4.6-c",
    "source/v5",
    "v5",
    "release",
)


class ForegroundExecutionError(ValueError):
    """Base error for an unsafe or invalid foreground execution."""


class ForegroundContractError(ForegroundExecutionError):
    """Raised when an intent, result, or receipt violates its contract."""


class ForegroundScopeError(ForegroundExecutionError):
    """Raised when a direct action leaves its declared path scope."""


class ForegroundBudgetError(ForegroundExecutionError):
    """Raised when a finite execution budget is exhausted."""


class ForegroundPermissionError(ForegroundExecutionError):
    """Raised when a mutation has no explicit owner authorization."""


class ForegroundControlPlaneError(ForegroundExecutionError):
    """Raised when durable task state or its ledger cannot be trusted."""


class ForegroundInterrupted(ForegroundExecutionError):
    """Raised by the direct runtime when an action is intentionally interrupted."""


class ForegroundVerificationError(ForegroundExecutionError):
    """Raised for malformed or insufficient independent verification."""


def _check_timestamp(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > 128:
        raise ForegroundContractError(f"{field_name}_INVALID")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ForegroundContractError(f"{field_name}_INVALID") from exc
    if parsed.tzinfo is None:
        raise ForegroundContractError(f"{field_name}_TIMEZONE_REQUIRED")
    return value


def _sha256(value: Any) -> str:
    try:
        payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ForegroundContractError("JSON_VALUE_NOT_SERIALIZABLE") from exc
    return hashlib.sha256(payload).hexdigest()


def _assert_sha256(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not _SHA256_RE.fullmatch(value.lower()):
        raise ForegroundContractError(f"{field_name}_SHA256_REQUIRED")
    return value.lower()


def _safe_value(value: Any, *, path: str = "value", depth: int = 0) -> Any:
    """Copy bounded JSON data while rejecting secrets and identity coupling."""

    if depth > 8:
        raise ForegroundContractError(f"{path}_TOO_DEEP")
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for key, child in value.items():
            key_text = str(key)
            lowered = key_text.lower()
            if _SECRET_KEY_RE.search(key_text):
                raise ForegroundContractError(f"{path}.{key_text}_SECRET_FIELD")
            if lowered == "delegated_children" and child == 0:
                result[key_text] = 0
                continue
            if lowered in _IDENTITY_KEYS:
                raise ForegroundContractError(f"{path}.{key_text}_IDENTITY_FORBIDDEN")
            result[key_text] = _safe_value(child, path=f"{path}.{key_text}", depth=depth + 1)
        return result
    if isinstance(value, (list, tuple)):
        if len(value) > 128:
            raise ForegroundContractError(f"{path}_TOO_LARGE")
        return [_safe_value(child, path=f"{path}[{index}]", depth=depth + 1) for index, child in enumerate(value)]
    if isinstance(value, str):
        if len(value) > 8192:
            raise ForegroundContractError(f"{path}_TOO_LARGE")
        if _SECRET_VALUE_RE.search(value):
            raise ForegroundContractError(f"{path}_SECRET_LIKE")
        return value
    if isinstance(value, float) and not math.isfinite(value):
        raise ForegroundContractError(f"{path}_NON_FINITE")
    if value is None or isinstance(value, (bool, int, float)):
        return value
    raise ForegroundContractError(f"{path}_TYPE_INVALID")


def _refs(values: Iterable[Any] | None, field_name: str) -> tuple[str, ...]:
    if values is None:
        return ()
    if isinstance(values, str):
        raise ForegroundContractError(f"{field_name}_MUST_BE_LIST")
    result: list[str] = []
    seen: set[str] = set()
    try:
        iterator = iter(values)
    except TypeError as exc:
        raise ForegroundContractError(f"{field_name}_MUST_BE_LIST") from exc
    for value in iterator:
        if not isinstance(value, str) or not value.strip() or len(value) > 1024:
            raise ForegroundContractError(f"{field_name}_ITEM_INVALID")
        item = value.strip().replace("\\", "/")
        if item in seen:
            raise ForegroundContractError(f"{field_name}_DUPLICATE:{item}")
        seen.add(item)
        result.append(item)
    return tuple(result)


def _execution_id(value: Any) -> str:
    if not isinstance(value, str) or not _EXECUTION_ID_RE.fullmatch(value):
        raise ForegroundContractError("EXECUTION_ID_INVALID")
    return value


def _new_execution_id() -> str:
    return f"fg-{uuid.uuid4().hex}"


def _relative_ref(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError as exc:
        raise ForegroundScopeError("ARTIFACT_REF_OUTSIDE_PROJECT") from exc


def _is_approved_gate(value: Mapping[str, Any] | None) -> bool:
    if not isinstance(value, Mapping):
        return False
    status = str(value.get("status", "")).upper()
    return bool(value.get("approved") is True or status in {"APPROVED", "GRANTED", "OBSERVED"}) and bool(
        str(value.get("source_ref") or value.get("decision_ref") or "").strip()
    )


@dataclass(frozen=True)
class ExecutionBudget:
    """Finite direct-execution limits; background and delegation are impossible."""

    max_attempts: int = 1
    max_retries: int = 0
    max_tool_actions: int = 8
    max_wall_clock_seconds: float = 60.0
    max_output_bytes: int = 8192
    allow_mutation: bool = False
    allow_network: bool = False
    max_delegated_children: int = 0

    def __post_init__(self) -> None:
        if not isinstance(self.max_attempts, int) or not 1 <= self.max_attempts <= 16:
            raise ForegroundContractError("BUDGET_MAX_ATTEMPTS_INVALID")
        if not isinstance(self.max_retries, int) or not 0 <= self.max_retries < self.max_attempts:
            raise ForegroundContractError("BUDGET_MAX_RETRIES_INVALID")
        if not isinstance(self.max_tool_actions, int) or not 1 <= self.max_tool_actions <= 128:
            raise ForegroundContractError("BUDGET_MAX_TOOL_ACTIONS_INVALID")
        if not isinstance(self.max_wall_clock_seconds, (int, float)) or not 0 < float(self.max_wall_clock_seconds) <= 600:
            raise ForegroundContractError("BUDGET_WALL_CLOCK_INVALID")
        if not isinstance(self.max_output_bytes, int) or not 128 <= self.max_output_bytes <= 1_048_576:
            raise ForegroundContractError("BUDGET_OUTPUT_BYTES_INVALID")
        if self.allow_network:
            raise ForegroundContractError("NETWORK_EXECUTION_NOT_PROVIDED")
        if self.max_delegated_children != 0:
            raise ForegroundContractError("DELEGATION_NOT_PROVIDED")

    @property
    def max_actions(self) -> int:
        return self.max_tool_actions

    @property
    def max_children(self) -> int:
        return self.max_delegated_children

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_attempts": self.max_attempts,
            "max_retries": self.max_retries,
            "max_tool_actions": self.max_tool_actions,
            "max_wall_clock_seconds": float(self.max_wall_clock_seconds),
            "max_output_bytes": self.max_output_bytes,
            "allow_mutation": bool(self.allow_mutation),
            "allow_network": False,
            "max_delegated_children": 0,
        }

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any] | None) -> "ExecutionBudget":
        if value is None:
            return cls()
        if not isinstance(value, Mapping):
            raise ForegroundContractError("BUDGET_MUST_BE_OBJECT")
        allowed = {
            "max_attempts",
            "max_retries",
            "max_tool_actions",
            "max_wall_clock_seconds",
            "max_output_bytes",
            "allow_mutation",
            "allow_network",
            "max_delegated_children",
        }
        unknown = sorted(str(key) for key in value if str(key) not in allowed)
        if unknown:
            raise ForegroundContractError("BUDGET_FIELDS_INVALID:" + ",".join(unknown))
        return cls(
            max_attempts=int(value.get("max_attempts", 1)),
            max_retries=int(value.get("max_retries", 0)),
            max_tool_actions=int(value.get("max_tool_actions", 8)),
            max_wall_clock_seconds=float(value.get("max_wall_clock_seconds", 60.0)),
            max_output_bytes=int(value.get("max_output_bytes", 8192)),
            allow_mutation=bool(value.get("allow_mutation", False)),
            allow_network=bool(value.get("allow_network", False)),
            max_delegated_children=int(value.get("max_delegated_children", 0)),
        )


@dataclass(frozen=True)
class ExecutionIntent:
    """Durable, identity-free authorization for one direct foreground run."""

    execution_id: str
    task_id: str
    goal_id: str
    plan_hash: str
    plan_revision: int
    project_binding: str
    action_name: str
    scope: tuple[str, ...]
    non_scope: tuple[str, ...]
    required_capabilities: tuple[str, ...] = ()
    permission_needs: tuple[str, ...] = ()
    context_refs: tuple[str, ...] = ()
    acceptance_requirements: tuple[str, ...] = ()
    required_evidence: tuple[str, ...] = ()
    verification_plan: Mapping[str, Any] = field(default_factory=dict)
    budget: ExecutionBudget = field(default_factory=ExecutionBudget)
    owner_gate: Mapping[str, Any] | None = None
    created_at: str = field(default_factory=utc_now)
    strategy: str = FOREGROUND_EXECUTION_STRATEGY

    def __post_init__(self) -> None:
        _execution_id(self.execution_id)
        _refs((self.task_id,), "task_id")
        _refs((self.goal_id,), "goal_id")
        _assert_sha256(self.plan_hash, "plan_hash")
        if not isinstance(self.plan_revision, int) or self.plan_revision < 1:
            raise ForegroundContractError("PLAN_REVISION_INVALID")
        if not isinstance(self.project_binding, str) or not self.project_binding.strip():
            raise ForegroundContractError("PROJECT_BINDING_REQUIRED")
        if len(self.project_binding) > 1024 or _SECRET_VALUE_RE.search(self.project_binding):
            raise ForegroundContractError("PROJECT_BINDING_INVALID")
        if not isinstance(self.action_name, str) or not self.action_name.strip() or len(self.action_name) > 256:
            raise ForegroundContractError("ACTION_NAME_INVALID")
        if self.strategy != FOREGROUND_EXECUTION_STRATEGY:
            raise ForegroundContractError("FOREGROUND_STRATEGY_INVALID")
        if not self.scope:
            raise ForegroundContractError("EXECUTION_SCOPE_REQUIRED")
        for field_name, values in (
            ("scope", self.scope),
            ("non_scope", self.non_scope),
            ("required_capabilities", self.required_capabilities),
            ("permission_needs", self.permission_needs),
            ("context_refs", self.context_refs),
            ("acceptance_requirements", self.acceptance_requirements),
            ("required_evidence", self.required_evidence),
        ):
            if not isinstance(values, tuple) or tuple(values) != _refs(values, field_name):
                raise ForegroundContractError(f"{field_name}_MUST_BE_UNIQUE_TUPLE")
        if not isinstance(self.verification_plan, Mapping):
            raise ForegroundContractError("VERIFICATION_PLAN_MUST_BE_OBJECT")
        _safe_value(self.verification_plan, path="verification_plan")
        if not isinstance(self.budget, ExecutionBudget):
            raise ForegroundContractError("BUDGET_REQUIRED")
        if self.owner_gate is not None:
            if not isinstance(self.owner_gate, Mapping):
                raise ForegroundContractError("OWNER_GATE_MUST_BE_OBJECT")
            _safe_value(self.owner_gate, path="owner_gate")
        _check_timestamp(self.created_at, "intent.created_at")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": FOREGROUND_INTENT_SCHEMA,
            "execution_id": self.execution_id,
            "task_id": self.task_id,
            "goal_id": self.goal_id,
            "plan_hash": self.plan_hash,
            "plan_revision": self.plan_revision,
            "project_binding": self.project_binding,
            "action_name": self.action_name,
            "strategy": FOREGROUND_EXECUTION_STRATEGY,
            "scope": list(self.scope),
            "non_scope": list(self.non_scope),
            "required_capabilities": list(self.required_capabilities),
            "permission_needs": list(self.permission_needs),
            "context_refs": list(self.context_refs),
            "acceptance_requirements": list(self.acceptance_requirements),
            "required_evidence": list(self.required_evidence),
            "verification_plan": _safe_value(self.verification_plan, path="verification_plan"),
            "budget": self.budget.to_dict(),
            "owner_gate": _safe_value(self.owner_gate, path="owner_gate") if self.owner_gate is not None else None,
            "created_at": self.created_at,
            "automatic_start": False,
            "background_execution": False,
            "process_survives_session": False,
            "parallel_execution": False,
            "delegated_children": 0,
            "delegation_status": DELEGATION_STATUS,
        }

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ExecutionIntent":
        if not isinstance(value, Mapping) or value.get("schema") != FOREGROUND_INTENT_SCHEMA:
            raise ForegroundContractError("INTENT_SCHEMA_INVALID")
        forbidden_runtime_fields = {
            "automatic_start",
            "background_execution",
            "process_survives_session",
            "parallel_execution",
            "delegated_children",
            "delegation_status",
        }
        for key in forbidden_runtime_fields:
            if key in value and value[key] not in {False, 0, DELEGATION_STATUS}:
                raise ForegroundContractError(f"INTENT_RUNTIME_FIELD_INVALID:{key}")
        allowed = {
            "schema",
            "execution_id",
            "task_id",
            "goal_id",
            "plan_hash",
            "plan_revision",
            "project_binding",
            "action_name",
            "strategy",
            "scope",
            "non_scope",
            "required_capabilities",
            "permission_needs",
            "context_refs",
            "acceptance_requirements",
            "required_evidence",
            "verification_plan",
            "budget",
            "owner_gate",
            "created_at",
            *forbidden_runtime_fields,
        }
        unknown = sorted(str(key) for key in value if str(key) not in allowed)
        if unknown:
            raise ForegroundContractError("INTENT_FIELDS_INVALID:" + ",".join(unknown))
        return cls(
            execution_id=str(value.get("execution_id", "")),
            task_id=str(value.get("task_id", "")),
            goal_id=str(value.get("goal_id", "")),
            plan_hash=str(value.get("plan_hash", "")),
            plan_revision=int(value.get("plan_revision", 0)),
            project_binding=str(value.get("project_binding", "")),
            action_name=str(value.get("action_name", "")),
            scope=_refs(value.get("scope", ()), "scope"),
            non_scope=_refs(value.get("non_scope", ()), "non_scope"),
            required_capabilities=_refs(value.get("required_capabilities", ()), "required_capabilities"),
            permission_needs=_refs(value.get("permission_needs", ()), "permission_needs"),
            context_refs=_refs(value.get("context_refs", ()), "context_refs"),
            acceptance_requirements=_refs(value.get("acceptance_requirements", ()), "acceptance_requirements"),
            required_evidence=_refs(value.get("required_evidence", ()), "required_evidence"),
            verification_plan=dict(value.get("verification_plan") or {}),
            budget=ExecutionBudget.from_mapping(value.get("budget")),
            owner_gate=dict(value["owner_gate"]) if isinstance(value.get("owner_gate"), Mapping) else None,
            created_at=str(value.get("created_at", "")),
            strategy=str(value.get("strategy", FOREGROUND_EXECUTION_STRATEGY)),
        )


@dataclass(frozen=True)
class ActionResult:
    """Safe summary of one direct action attempt; it is never DONE evidence."""

    status: str = "SUCCEEDED"
    summary: str = ""
    artifact_refs: tuple[str, ...] = ()
    retryable: bool = False
    mutation_performed: bool = False

    def __post_init__(self) -> None:
        if self.status not in {"SUCCEEDED", "FAILED", "INTERRUPTED", "BLOCKED"}:
            raise ForegroundContractError("ACTION_STATUS_INVALID")
        if len(self.summary) > 2048 or _SECRET_VALUE_RE.search(self.summary):
            raise ForegroundContractError("ACTION_SUMMARY_INVALID")
        if not isinstance(self.artifact_refs, tuple) or tuple(self.artifact_refs) != _refs(self.artifact_refs, "artifact_refs"):
            raise ForegroundContractError("ACTION_ARTIFACT_REFS_INVALID")

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "summary": self.summary,
            "artifact_refs": list(self.artifact_refs),
            "retryable": bool(self.retryable),
            "mutation_performed": bool(self.mutation_performed),
        }


@dataclass(frozen=True)
class VerificationResult:
    """Independent verification output consumed by the C10 completion contract."""

    status: str
    evidence_claims: tuple[EvidenceClaim | Mapping[str, Any], ...] = ()
    candidate_state: Any = None
    summary: str = ""

    def __post_init__(self) -> None:
        if self.status not in {"VERIFIED", "FAILED", "INCOMPLETE", "BLOCKED"}:
            raise ForegroundContractError("VERIFICATION_STATUS_INVALID")
        if len(self.summary) > 2048 or _SECRET_VALUE_RE.search(self.summary):
            raise ForegroundContractError("VERIFICATION_SUMMARY_INVALID")


class ExecutionRuntime:
    """The only direct-action surface exposed by the controller."""

    def __init__(self, root: Path, intent: ExecutionIntent, *, read_only: bool = False) -> None:
        self.root = root.resolve()
        self.intent = intent
        self.read_only = read_only
        self._started = time.monotonic()
        self._actions = 0
        self._attempt = 0
        self._interrupted = False
        self._artifact_paths: set[str] = set()
        self._mutation_performed = False
        self._max_bytes = intent.budget.max_output_bytes

    @property
    def action_count(self) -> int:
        return self._actions

    @property
    def attempt(self) -> int:
        return self._attempt

    @property
    def mutation_performed(self) -> bool:
        return self._mutation_performed

    @property
    def artifact_refs(self) -> tuple[str, ...]:
        return tuple(sorted(self._artifact_paths))

    def _ensure_budget(self) -> None:
        if self._interrupted:
            raise ForegroundInterrupted("EXECUTION_INTERRUPTED")
        if time.monotonic() - self._started > float(self.intent.budget.max_wall_clock_seconds):
            raise ForegroundBudgetError("BUDGET_WALL_CLOCK_EXCEEDED")
        if self._actions >= self.intent.budget.max_tool_actions:
            raise ForegroundBudgetError("BUDGET_ACTIONS_EXCEEDED")

    def _consume(self, operation: str) -> None:
        self._ensure_budget()
        self._actions += 1
        if self._actions > self.intent.budget.max_tool_actions:
            raise ForegroundBudgetError(f"BUDGET_ACTIONS_EXCEEDED:{operation}")

    def check_budget(self) -> None:
        """Check the finite deadline after a caller-supplied direct callback."""

        self._ensure_budget()

    def begin_attempt(self, attempt: int) -> None:
        if not isinstance(attempt, int) or attempt < 1:
            raise ForegroundContractError("ATTEMPT_INVALID")
        self._attempt = attempt
        self._consume("direct_attempt")

    def record_action(self, label: str = "direct_action") -> None:
        if not isinstance(label, str) or not label.strip():
            raise ForegroundContractError("ACTION_LABEL_REQUIRED")
        self._consume(label.strip())

    def interrupt(self) -> None:
        self._interrupted = True
        raise ForegroundInterrupted("EXECUTION_INTERRUPTED")

    def enter_verification(self) -> None:
        self.read_only = True

    def _relative_path(self, value: str | Path) -> str:
        if not isinstance(value, (str, Path)):
            raise ForegroundScopeError("PATH_MUST_BE_TEXT")
        raw = str(value).replace("\\", "/").strip()
        if not raw or "\x00" in raw or raw.startswith("/") or re.match(r"^[A-Za-z]:", raw):
            raise ForegroundScopeError("PATH_MUST_BE_PROJECT_RELATIVE")
        path = Path(raw)
        if any(part in {"", ".", ".."} for part in path.parts):
            raise ForegroundScopeError("PATH_TRAVERSAL_REJECTED")
        relative = "/".join(path.parts)
        lowered = relative.lower()
        if any(lowered == prefix or lowered.startswith(prefix + "/") for prefix in _PROTECTED_PREFIXES):
            raise ForegroundScopeError("PROTECTED_PATH_REJECTED")
        if any(fnmatch.fnmatchcase(lowered, pattern) or fnmatch.fnmatchcase(lowered, pattern + "/*") for pattern in self._normalized_patterns(self.intent.non_scope)):
            raise ForegroundScopeError("NON_SCOPE_PATH_REJECTED")
        patterns = self._normalized_patterns(self.intent.scope)
        if not any(
            fnmatch.fnmatchcase(relative, pattern)
            or fnmatch.fnmatchcase(lowered, pattern.lower())
            or relative == pattern.rstrip("/")
            or relative.startswith(pattern.rstrip("/") + "/")
            for pattern in patterns
        ):
            raise ForegroundScopeError("PATH_OUTSIDE_DECLARED_SCOPE")
        candidate = (self.root / relative).resolve(strict=False)
        try:
            candidate.relative_to(self.root)
        except ValueError as exc:
            raise ForegroundScopeError("PATH_OUTSIDE_PROJECT") from exc
        current = self.root
        for part in Path(relative).parts[:-1]:
            current = current / part
            if current.is_symlink():
                raise ForegroundScopeError("SYMLINK_PARENT_REJECTED")
        if candidate.exists() and candidate.is_symlink():
            raise ForegroundScopeError("SYMLINK_TARGET_REJECTED")
        return relative

    @staticmethod
    def _normalized_patterns(values: Sequence[str]) -> tuple[str, ...]:
        return tuple(str(value).replace("\\", "/").strip() for value in values if str(value).strip())

    def _path(self, value: str | Path) -> tuple[str, Path]:
        relative = self._relative_path(value)
        return relative, self.root / relative

    def read_text(self, path: str | Path, *, encoding: str = "utf-8") -> str:
        self._consume("read_text")
        relative, target = self._path(path)
        if not target.is_file() or target.is_symlink():
            raise ForegroundScopeError("READ_TARGET_NOT_FILE")
        try:
            size = target.stat().st_size
            if size > self._max_bytes:
                raise ForegroundBudgetError("READ_OUTPUT_BYTES_EXCEEDED")
            return target.read_text(encoding=encoding)
        except OSError as exc:
            raise ForegroundExecutionError(f"READ_FAILED:{relative}") from exc

    def file_sha256(self, path: str | Path) -> str:
        self._consume("file_sha256")
        relative, target = self._path(path)
        if not target.is_file() or target.is_symlink():
            raise ForegroundScopeError("HASH_TARGET_NOT_FILE")
        digest = hashlib.sha256()
        try:
            with target.open("rb") as handle:
                while chunk := handle.read(64 * 1024):
                    digest.update(chunk)
        except OSError as exc:
            raise ForegroundExecutionError(f"HASH_FAILED:{relative}") from exc
        self._artifact_paths.add(relative)
        return digest.hexdigest()

    def declare_artifact(self, path: str | Path) -> str:
        self._consume("declare_artifact")
        relative, target = self._path(path)
        if not target.is_file() or target.is_symlink():
            raise ForegroundScopeError("ARTIFACT_NOT_FILE")
        self._artifact_paths.add(relative)
        return relative

    def write_text(self, path: str | Path, content: str, *, encoding: str = "utf-8") -> str:
        self._consume("write_text")
        if self.read_only:
            raise ForegroundPermissionError("VERIFICATION_IS_READ_ONLY")
        if not self.intent.budget.allow_mutation:
            raise ForegroundPermissionError("EXPLICIT_MUTATION_BUDGET_REQUIRED")
        if not _is_approved_gate(self.intent.owner_gate):
            raise ForegroundPermissionError("OWNER_GATE_REQUIRED_FOR_MUTATION")
        if not isinstance(content, str):
            raise ForegroundExecutionError("WRITE_CONTENT_MUST_BE_TEXT")
        if len(content.encode(encoding)) > self._max_bytes:
            raise ForegroundBudgetError("WRITE_OUTPUT_BYTES_EXCEEDED")
        relative, target = self._path(path)
        if target.exists() and target.is_dir():
            raise ForegroundScopeError("WRITE_TARGET_DIRECTORY")
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.is_symlink():
                raise ForegroundScopeError("SYMLINK_TARGET_REJECTED")
            fd, temporary_name = tempfile.mkstemp(prefix=".c12-", dir=str(target.parent))
            temporary = Path(temporary_name)
            try:
                with os.fdopen(fd, "w", encoding=encoding, newline="") as handle:
                    handle.write(content)
                temporary.replace(target)
            finally:
                if temporary.exists():
                    temporary.unlink()
        except ForegroundExecutionError:
            raise
        except OSError as exc:
            raise ForegroundExecutionError(f"WRITE_FAILED:{relative}") from exc
        self._artifact_paths.add(relative)
        self._mutation_performed = True
        return relative

    def artifact_bindings(self) -> list[dict[str, Any]]:
        bindings: list[dict[str, Any]] = []
        for relative in sorted(self._artifact_paths):
            target = self.root / relative
            digest = "MISSING"
            if target.is_file() and not target.is_symlink():
                hasher = hashlib.sha256()
                try:
                    with target.open("rb") as handle:
                        while chunk := handle.read(64 * 1024):
                            hasher.update(chunk)
                    digest = hasher.hexdigest()
                except OSError:
                    digest = "UNREADABLE"
            bindings.append({"path": relative, "sha256": digest})
        return bindings

    def state_fingerprint(self) -> str:
        return _sha256({
            "schema": "p2p-foreground-state-binding/1",
            "task_id": self.intent.task_id,
            "plan_hash": self.intent.plan_hash,
            "artifacts": self.artifact_bindings(),
        })


def _coerce_action_result(value: Any, runtime: ExecutionRuntime) -> ActionResult:
    if isinstance(value, ActionResult):
        return replace(value, artifact_refs=tuple(dict.fromkeys((*value.artifact_refs, *runtime.artifact_refs))), mutation_performed=value.mutation_performed or runtime.mutation_performed)
    if value is None:
        return ActionResult(artifact_refs=runtime.artifact_refs, mutation_performed=runtime.mutation_performed)
    if isinstance(value, Mapping):
        status_raw = str(value.get("status", "SUCCEEDED")).upper()
        status = {
            "SUCCESS": "SUCCEEDED",
            "PASS": "SUCCEEDED",
            "DONE": "SUCCEEDED",
            "RETRY": "FAILED",
        }.get(status_raw, status_raw)
        if status not in {"SUCCEEDED", "FAILED", "INTERRUPTED", "BLOCKED"}:
            raise ForegroundContractError("ACTION_RESULT_STATUS_INVALID")
        summary = str(value.get("summary", ""))[:2048]
        refs = _refs(value.get("artifact_refs", value.get("changed_paths", ())), "action.artifact_refs")
        refs = tuple(dict.fromkeys((*refs, *runtime.artifact_refs)))
        return ActionResult(
            status=status,
            summary=summary,
            artifact_refs=refs,
            retryable=bool(value.get("retryable", False)),
            mutation_performed=bool(value.get("mutation_performed", False)) or runtime.mutation_performed,
        )
    if isinstance(value, str):
        return ActionResult(summary=value[:2048], artifact_refs=runtime.artifact_refs, mutation_performed=runtime.mutation_performed)
    raise ForegroundContractError("ACTION_RESULT_INVALID")


def _coerce_verification_result(value: Any) -> VerificationResult:
    if isinstance(value, VerificationResult):
        return value
    if isinstance(value, EvidenceClaim):
        return VerificationResult(status="VERIFIED", evidence_claims=(value,))
    if isinstance(value, Mapping):
        status_raw = str(value.get("status", "FAILED")).upper()
        status = {"PASS": "VERIFIED", "SUCCESS": "VERIFIED", "DONE": "VERIFIED"}.get(status_raw, status_raw)
        if status not in {"VERIFIED", "FAILED", "INCOMPLETE", "BLOCKED"}:
            raise ForegroundVerificationError("VERIFICATION_RESULT_STATUS_INVALID")
        raw_claims = value.get("evidence_claims", value.get("claims", ()))
        if isinstance(raw_claims, (str, bytes)) or not isinstance(raw_claims, (list, tuple)):
            raise ForegroundVerificationError("VERIFICATION_CLAIMS_MUST_BE_LIST")
        candidate_state = value.get("candidate_state")
        if candidate_state is not None:
            _safe_value(candidate_state, path="candidate_state")
        return VerificationResult(
            status=status,
            evidence_claims=tuple(raw_claims),
            candidate_state=candidate_state,
            summary=str(value.get("summary", ""))[:2048],
        )
    if value is True:
        return VerificationResult(status="VERIFIED")
    return VerificationResult(status="FAILED", summary="VERIFIER_DID_NOT_CONFIRM_CURRENT_EVIDENCE")


def _invoke(callback: Callable[..., Any], runtime: ExecutionRuntime, second: Any = None, *, allow_second: bool = False) -> Any:
    if not callable(callback):
        raise ForegroundContractError("CALLBACK_REQUIRED")
    try:
        signature = inspect.signature(callback)
        positional = [
            parameter
            for parameter in signature.parameters.values()
            if parameter.kind in {parameter.POSITIONAL_ONLY, parameter.POSITIONAL_OR_KEYWORD}
        ]
        accepts_varargs = any(parameter.kind == parameter.VAR_POSITIONAL for parameter in signature.parameters.values())
    except (TypeError, ValueError):
        positional = []
        accepts_varargs = False
    if allow_second and (accepts_varargs or len(positional) >= 2):
        return callback(runtime, second)
    return callback(runtime)


class ForegroundExecutionController:
    """Synchronous one-task controller backed by ``TaskStateStore``."""

    def __init__(self, root: str | Path, *, protected_roots: Iterable[str | Path] = ()) -> None:
        self.store = TaskStateStore(root, protected_roots=protected_roots)
        self.root = self.store.root

    def _result(self, status: str, *, task_id: str | None = None, execution_id: str | None = None, reason: str = "", **extra: Any) -> dict[str, Any]:
        result: dict[str, Any] = {
            "schema": FOREGROUND_RESULT_SCHEMA,
            "status": status,
            "task_id": task_id,
            "execution_id": execution_id,
            "reason": reason,
            "automatic_start": False,
            "background_execution": False,
            "process_survives_session": False,
            "parallel_execution": False,
            "delegated_children": 0,
            "execution_strategy": FOREGROUND_EXECUTION_STRATEGY,
            "delegation_status": DELEGATION_STATUS,
            "output_is_evidence": False,
        }
        result.update(_safe_value(extra, path="result"))
        return result

    def _control_plane(self) -> TaskPlan:
        try:
            plan = self.store.require()
            events = self.store.read_events()
        except TaskStateError as exc:
            raise ForegroundControlPlaneError(str(exc)) from exc
        if events.get("status") == "PARTIAL":
            raise ForegroundControlPlaneError("TASK_LEDGER_PARTIAL")
        if events.get("status") == "NOT_INITIALIZED":
            raise ForegroundControlPlaneError("TASK_LEDGER_NOT_INITIALIZED")
        if plan.canonical_hash() != self.store.require().canonical_hash():
            raise ForegroundControlPlaneError("TASK_PLAN_CHANGED_DURING_READ")
        active = [task.task_id for task in plan.tasks.values() if task.status == "ACTIVE"]
        if len(active) > 1:
            raise ForegroundControlPlaneError("MULTIPLE_ACTIVE_TASKS")
        return plan

    @staticmethod
    def _active_tasks(plan: TaskPlan) -> tuple[TaskRecord, ...]:
        return tuple(task for task in plan.tasks.values() if task.status == "ACTIVE")

    def _refresh_ready(self, plan: TaskPlan) -> TaskPlan:
        refreshed = plan.refresh_ready()
        if refreshed.canonical_hash() != plan.canonical_hash():
            try:
                return self.store.save(refreshed, event_name="foreground_ready_refresh")
            except TaskStateError as exc:
                raise ForegroundControlPlaneError(str(exc)) from exc
        return refreshed

    def _candidate(self, plan: TaskPlan, task_id: str | None = None) -> TaskRecord | None:
        if task_id is not None:
            task = plan.tasks.get(task_id)
            if task is None:
                raise ForegroundContractError(f"TASK_NOT_FOUND:{task_id}")
            return task
        ready = next_safe_task(plan)
        if ready is not None:
            return ready
        for candidate_id in plan.topological_order():
            task = plan.tasks[candidate_id]
            if task.status in {"PLANNED", "BLOCKED", "WAITING_OWNER"} and plan.dependencies_are_done(candidate_id):
                return task
        return None

    def select(self, task_id: str | None = None) -> dict[str, Any]:
        try:
            plan = self._refresh_ready(self._control_plane())
            active = self._active_tasks(plan)
            if active:
                return self._result("BLOCKED", task_id=active[0].task_id, reason="ACTIVE_TASK_REQUIRES_EXPLICIT_RESUME", active_task_id=active[0].task_id)
            task = self._candidate(plan, task_id)
            if task is None:
                return self._result("BLOCKED", reason="NO_SAFE_READY_TASK")
            if task.status != "READY":
                return self._result("BLOCKED", task_id=task.task_id, reason=f"TASK_NOT_READY:{task.status}", task_status=task.status)
            if not plan.dependencies_are_done(task.task_id):
                return self._result("BLOCKED", task_id=task.task_id, reason="DEPENDENCY_NOT_DONE")
            return self._result("SELECTED", task_id=task.task_id, goal_id=plan.goal_id, plan_hash=plan.canonical_hash(), task_status=task.status, scope=list(task.scope))
        except ForegroundExecutionError as exc:
            return self._result("CONTROL_PLANE_ERROR", task_id=task_id, reason=str(exc))

    def preflight(
        self,
        task_id: str | None = None,
        *,
        capability_readiness: Mapping[str, Mapping[str, Any]] | None = None,
        permission_state: Mapping[str, Mapping[str, Any]] | None = None,
        context_state: Mapping[str, Mapping[str, Any]] | None = None,
    ) -> dict[str, Any]:
        try:
            plan = self._control_plane()
            candidate = self._candidate(plan, task_id)
            if candidate is None:
                return self._result("BLOCKED", task_id=task_id, reason="NO_PREFLIGHT_CANDIDATE")
            try:
                updated, preflight_result = self.store.preflight(
                    candidate.task_id,
                    capability_readiness=capability_readiness,
                    permission_state=permission_state,
                    context_state=context_state,
                )
            except TaskStateError as exc:
                raise ForegroundControlPlaneError(str(exc)) from exc
            result = self._result(
                str(preflight_result.get("status", "UNKNOWN")),
                task_id=candidate.task_id,
                goal_id=updated.goal_id,
                plan_hash=updated.canonical_hash(),
                task_status=updated.tasks[candidate.task_id].status,
                preflight=preflight_result,
                optional_capabilities_unavailable=[
                    key
                    for key in candidate.optional_capabilities
                    if not isinstance((capability_readiness or {}).get(key), Mapping)
                    or (capability_readiness or {}).get(key, {}).get("state") in {"UNKNOWN", "STALE", "NOT_READY"}
                ],
            )
            if preflight_result.get("owner_decision"):
                result["owner_question"] = preflight_result["owner_decision"]
            return result
        except ForegroundExecutionError as exc:
            return self._result("CONTROL_PLANE_ERROR", task_id=task_id, reason=str(exc))

    def _build_intent(
        self,
        plan: TaskPlan,
        task: TaskRecord,
        *,
        action_name: str,
        budget: ExecutionBudget,
        verification_plan: Mapping[str, Any] | None,
        owner_gate: Mapping[str, Any] | None,
    ) -> ExecutionIntent:
        return ExecutionIntent(
            execution_id=_new_execution_id(),
            task_id=task.task_id,
            goal_id=plan.goal_id,
            plan_hash=plan.canonical_hash(),
            plan_revision=plan.plan_revision,
            project_binding="PROJECT_ROOT_BOUND",
            action_name=action_name,
            scope=tuple(task.scope),
            non_scope=tuple(task.non_scope),
            required_capabilities=tuple(task.required_capabilities),
            permission_needs=tuple(task.permission_needs),
            context_refs=tuple(task.context_refs),
            acceptance_requirements=tuple(task.acceptance_requirements),
            required_evidence=tuple(task.required_evidence),
            verification_plan=dict(verification_plan or {"mode": "CALLER_SUPPLIED_INDEPENDENT_CHECK"}),
            budget=budget,
            owner_gate=dict(owner_gate) if isinstance(owner_gate, Mapping) else None,
        )

    def _execution_dir(self, execution_id: str) -> Path:
        _execution_id(execution_id)
        return self.root / FOREGROUND_STATE_RELATIVE_ROOT / execution_id

    def _write_json(self, path: Path, payload: Mapping[str, Any], *, immutable: bool = False) -> str:
        try:
            path = path.resolve(strict=False)
            path.relative_to(self.root)
        except ValueError as exc:
            raise ForegroundScopeError("PERSISTENCE_PATH_OUTSIDE_PROJECT") from exc
        if path.is_symlink():
            raise ForegroundControlPlaneError("PERSISTENCE_SYMLINK_REJECTED")
        safe_payload = _safe_value(payload, path="persisted")
        path.parent.mkdir(parents=True, exist_ok=True)
        if immutable and path.exists():
            try:
                existing = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError) as exc:
                raise ForegroundControlPlaneError("IMMUTABLE_ARTIFACT_CORRUPT") from exc
            if existing != safe_payload:
                raise ForegroundControlError("IMMUTABLE_ARTIFACT_CONFLICT")
            return _relative_ref(path, self.root)
        temporary = path.with_name(path.name + ".tmp")
        try:
            temporary.write_text(json.dumps(safe_payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            temporary.replace(path)
        except OSError as exc:
            raise ForegroundControlPlaneError(f"PERSISTENCE_WRITE_FAILED:{path.name}") from exc
        return _relative_ref(path, self.root)

    def _persist_intent(self, intent: ExecutionIntent) -> str:
        return self._write_json(self._execution_dir(intent.execution_id) / "intent.json", intent.to_dict(), immutable=True)

    def _persist_receipt(
        self,
        intent: ExecutionIntent,
        *,
        phase: str,
        status: str,
        attempt: int,
        runtime: ExecutionRuntime | None = None,
        summary: str = "",
        evidence_refs: Iterable[str] = (),
        checkpoint_ref: str | None = None,
    ) -> str:
        directory = self._execution_dir(intent.execution_id) / "receipts"
        directory.mkdir(parents=True, exist_ok=True)
        existing = sorted(directory.glob("*.json"))
        sequence = len(existing) + 1
        artifact_refs = runtime.artifact_refs if runtime is not None else ()
        state_fingerprint = runtime.state_fingerprint() if runtime is not None else _sha256({"task_id": intent.task_id, "plan_hash": intent.plan_hash})
        payload = {
            "schema": FOREGROUND_RECEIPT_SCHEMA,
            "execution_id": intent.execution_id,
            "task_id": intent.task_id,
            "goal_id": intent.goal_id,
            "plan_hash": intent.plan_hash,
            "phase": phase,
            "status": status,
            "attempt": attempt,
            "action_count": runtime.action_count if runtime is not None else 0,
            "artifact_refs": list(artifact_refs),
            "evidence_refs": list(_refs(evidence_refs, "receipt.evidence_refs")),
            "state_fingerprint": state_fingerprint,
            "checkpoint_ref": checkpoint_ref,
            "summary": summary[:2048],
            "created_at": utc_now(),
            "execution_strategy": FOREGROUND_EXECUTION_STRATEGY,
            "automatic_start": False,
            "background_execution": False,
            "process_survives_session": False,
            "parallel_execution": False,
            "delegated_children": 0,
            "delegation_status": DELEGATION_STATUS,
        }
        return self._write_json(directory / f"{sequence:04d}.json", payload, immutable=True)

    def _persist_checkpoint(
        self,
        intent: ExecutionIntent,
        runtime: ExecutionRuntime,
        *,
        classification: str,
        next_safe_step: str,
        completed_refs: Iterable[str] = (),
        pending_refs: Iterable[str] = (),
        evidence_fingerprints: Mapping[str, str] | None = None,
        notes: str = "",
    ) -> str:
        if classification not in {"DONE", "SAFE_TO_RESUME", "NEEDS_RECHECK", "BLOCKED", "UNKNOWN"}:
            raise ForegroundContractError("CHECKPOINT_CLASSIFICATION_INVALID")
        checkpoint_number = len(list((self._execution_dir(intent.execution_id) / "checkpoints").glob("*.json"))) + 1
        checkpoint_path = self._execution_dir(intent.execution_id) / "checkpoints" / f"{checkpoint_number:04d}.json"
        checkpoint_ref = _relative_ref(checkpoint_path, self.root)
        state_fingerprint = runtime.state_fingerprint()
        fingerprints = {str(key): _assert_sha256(value, f"checkpoint.evidence_fingerprints.{key}") for key, value in (evidence_fingerprints or {}).items()}
        checkpoint = {
            "checkpoint_ref": checkpoint_ref,
            "state_fingerprint": state_fingerprint,
            "recovery_classification": classification,
            "next_safe_step": next_safe_step,
            "completed_refs": list(_refs(completed_refs, "checkpoint.completed_refs")),
            "pending_refs": list(_refs(pending_refs, "checkpoint.pending_refs")),
            "evidence_fingerprints": dict(sorted(fingerprints.items())),
            "captured_at": utc_now(),
            "notes": notes[:4096],
        }
        self._write_json(
            checkpoint_path,
            {
                "schema": FOREGROUND_CHECKPOINT_SCHEMA,
                "execution_id": intent.execution_id,
                "task_id": intent.task_id,
                "plan_hash": intent.plan_hash,
                **checkpoint,
            },
            immutable=True,
        )
        try:
            self.store.checkpoint(intent.task_id, checkpoint, now=checkpoint["captured_at"])
        except TaskStateError as exc:
            raise ForegroundControlPlaneError(str(exc)) from exc
        return checkpoint_ref

    def _block_task(self, task_id: str, reason: str, refs: Iterable[str] = ()) -> None:
        try:
            self.store.transition(
                task_id,
                "BLOCKED",
                blocker={"reason": reason, "refs": list(_refs(refs, "blocker.refs")), "source": "foreground-controller"},
            )
        except TaskStateError as exc:
            raise ForegroundControlPlaneError(str(exc)) from exc

    def _mutation_gate(self, intent: ExecutionIntent) -> bool:
        if not intent.budget.allow_mutation:
            return True
        if not _is_approved_gate(intent.owner_gate):
            return False
        return True

    def _candidate_state(self, runtime: ExecutionRuntime, supplied: Any) -> Any:
        if supplied is not None:
            _safe_value(supplied, path="candidate_state")
            return supplied
        return {
            "verification_mode": "INDEPENDENT_READ_ONLY",
            "artifact_bindings": runtime.artifact_bindings(),
            "state_fingerprint": runtime.state_fingerprint(),
        }

    def _execute_inner(
        self,
        *,
        action: Callable[..., Any],
        verify: Callable[..., Any] | None,
        task_id: str | None,
        action_name: str,
        budget: ExecutionBudget,
        verification_plan: Mapping[str, Any] | None,
        owner_gate: Mapping[str, Any] | None,
        capability_readiness: Mapping[str, Mapping[str, Any]] | None,
        permission_state: Mapping[str, Mapping[str, Any]] | None,
        context_state: Mapping[str, Mapping[str, Any]] | None,
    ) -> dict[str, Any]:
        plan = self._refresh_ready(self._control_plane())
        if self._active_tasks(plan):
            active = self._active_tasks(plan)[0]
            return self._result("BLOCKED", task_id=active.task_id, reason="ACTIVE_TASK_REQUIRES_EXPLICIT_RESUME", active_task_id=active.task_id)
        candidate = self._candidate(plan, task_id)
        if candidate is None:
            return self._result("BLOCKED", task_id=task_id, reason="NO_SAFE_READY_TASK")
        intent = self._build_intent(
            plan,
            candidate,
            action_name=action_name,
            budget=budget,
            verification_plan=verification_plan,
            owner_gate=owner_gate,
        )
        intent_ref = self._persist_intent(intent)
        if not self._mutation_gate(intent):
            owner_question = {
                "question": "May this direct task change only the files in its recorded scope?",
                "options": ["Allow only for this task", "Keep the task read-only"],
                "recommendation": "Keep the task read-only unless the stated acceptance requires this scoped change.",
                "consequences": {
                    "Allow only for this task": "The controller may mutate only the declared task scope for this foreground run.",
                    "Keep the task read-only": "The task remains waiting for an owner decision and no mutation is attempted.",
                },
                "approval_metadata": {"approval_boundary": "OWNER_ONLY", "auto_grant_permissions": False},
            }
            try:
                waiting_plan = request_owner_decision(
                    plan,
                    candidate.task_id,
                    owner_question["question"],
                    options=owner_question["options"],
                    source_refs=("foreground-controller", intent_ref),
                    recommendation=owner_question["recommendation"],
                    consequences=owner_question["consequences"],
                    approval_metadata=owner_question["approval_metadata"],
                )
                waiting_plan = self.store.save(
                    waiting_plan,
                    event_name="foreground_owner_gate",
                    task_id=candidate.task_id,
                    details={"intent_ref": intent_ref, "reason": "OWNER_GATE_REQUIRED_FOR_MUTATION"},
                )
            except TaskStateError as exc:
                raise ForegroundControlPlaneError(str(exc)) from exc
            durable_owner_question = waiting_plan.tasks[candidate.task_id].owner_decision or owner_question
            return self._result(
                "WAITING_OWNER",
                task_id=candidate.task_id,
                execution_id=intent.execution_id,
                reason="OWNER_GATE_REQUIRED_FOR_MUTATION",
                intent_ref=intent_ref,
                owner_question=durable_owner_question,
                task_status=waiting_plan.tasks[candidate.task_id].status,
            )
        try:
            preflight = self.store.preflight(
                candidate.task_id,
                capability_readiness=capability_readiness,
                permission_state=permission_state,
                context_state=context_state,
            )
        except TaskStateError as exc:
            raise ForegroundControlPlaneError(str(exc)) from exc
        plan_after_preflight, preflight_result = preflight
        if preflight_result.get("status") != "PASS":
            owner_question = preflight_result.get("owner_decision")
            result = self._result(
                str(preflight_result.get("status", "UNKNOWN")),
                task_id=candidate.task_id,
                execution_id=intent.execution_id,
                reason=";".join(str(item) for item in preflight_result.get("reasons", [])),
                intent_ref=intent_ref,
                preflight=preflight_result,
                task_status=plan_after_preflight.tasks[candidate.task_id].status,
            )
            if owner_question:
                result["owner_question"] = owner_question
            return result
        current_task = plan_after_preflight.tasks[candidate.task_id]
        if current_task.status != "READY":
            return self._result("BLOCKED", task_id=current_task.task_id, execution_id=intent.execution_id, reason=f"TASK_NOT_READY_AFTER_PREFLIGHT:{current_task.status}", intent_ref=intent_ref)
        try:
            active_plan = self.store.transition(candidate.task_id, "ACTIVE", preflight=preflight_result)
        except TaskStateError as exc:
            raise ForegroundControlPlaneError(str(exc)) from exc
        active_task = active_plan.tasks[candidate.task_id]
        runtime = ExecutionRuntime(self.root, intent)
        initial_checkpoint_ref = self._persist_checkpoint(
            intent,
            runtime,
            classification="UNKNOWN",
            next_safe_step="Perform the explicit direct action once within the recorded finite budget.",
            pending_refs=("DIRECT_ACTION",),
            notes="Intent persisted before any material action; process survival is not assumed.",
        )
        receipt_refs = [self._persist_receipt(intent, phase="INTENT_AND_CHECKPOINT", status="ACTIVE", attempt=0, runtime=runtime, checkpoint_ref=initial_checkpoint_ref)]
        last_action = ActionResult(status="FAILED", summary="NO_ACTION_ATTEMPTED")
        attempt = 0
        while attempt < budget.max_attempts:
            attempt += 1
            try:
                runtime.begin_attempt(attempt)
                value = _invoke(action, runtime)
                runtime.check_budget()
                last_action = _coerce_action_result(value, runtime)
            except ForegroundInterrupted as exc:
                last_action = ActionResult(status="INTERRUPTED", summary=str(exc), artifact_refs=runtime.artifact_refs, mutation_performed=runtime.mutation_performed)
            except ForegroundExecutionError as exc:
                last_action = ActionResult(status="FAILED", summary=str(exc), artifact_refs=runtime.artifact_refs, mutation_performed=runtime.mutation_performed)
            except Exception as exc:  # direct callback failures are bounded and surfaced, never retried by default
                last_action = ActionResult(status="FAILED", summary=f"DIRECT_ACTION_FAILED:{type(exc).__name__}", artifact_refs=runtime.artifact_refs, mutation_performed=runtime.mutation_performed)
            receipt_refs.append(self._persist_receipt(intent, phase="ACTION_ATTEMPT", status=last_action.status, attempt=attempt, runtime=runtime, summary=last_action.summary))
            if last_action.status == "SUCCEEDED":
                break
            retry_allowed = bool(last_action.retryable and not runtime.mutation_performed and attempt < budget.max_attempts and attempt <= budget.max_retries + 1)
            if not retry_allowed or last_action.status in {"INTERRUPTED", "BLOCKED"}:
                break
        if last_action.status != "SUCCEEDED":
            if last_action.status == "INTERRUPTED" or runtime.mutation_performed:
                checkpoint_ref = self._persist_checkpoint(
                    intent,
                    runtime,
                    classification="NEEDS_RECHECK",
                    next_safe_step="Recheck the changed scoped artifacts with a read-only verifier before deciding completion.",
                    completed_refs=receipt_refs,
                    pending_refs=("INDEPENDENT_VERIFICATION",),
                    notes="The direct action did not complete the verification boundary; the task remains non-DONE.",
                )
                receipt_refs.append(self._persist_receipt(intent, phase="INTERRUPTED_OR_PARTIAL", status="NEEDS_RECHECK", attempt=attempt, runtime=runtime, summary=last_action.summary, checkpoint_ref=checkpoint_ref))
                return self._result("INTERRUPTED" if last_action.status == "INTERRUPTED" else "NEEDS_RECHECK", task_id=candidate.task_id, execution_id=intent.execution_id, reason=last_action.summary or "ACTION_DID_NOT_COMPLETE", intent_ref=intent_ref, checkpoint_ref=checkpoint_ref, receipt_refs=receipt_refs, task_status="ACTIVE")
            checkpoint_ref = self._persist_checkpoint(
                intent,
                runtime,
                classification="BLOCKED",
                next_safe_step="Resolve the direct-action failure before another explicit foreground attempt.",
                completed_refs=receipt_refs,
                pending_refs=("DIRECT_ACTION",),
                notes="No material mutation was observed; the task is blocked rather than retried in the background.",
            )
            self._block_task(candidate.task_id, "DIRECT_ACTION_FAILED", refs=(checkpoint_ref,))
            return self._result("FAILED", task_id=candidate.task_id, execution_id=intent.execution_id, reason=last_action.summary or "DIRECT_ACTION_FAILED", intent_ref=intent_ref, checkpoint_ref=checkpoint_ref, receipt_refs=receipt_refs, task_status="BLOCKED")
        post_action_checkpoint = self._persist_checkpoint(
            intent,
            runtime,
            classification="NEEDS_RECHECK",
            next_safe_step="Run the separate read-only verifier against current scoped artifacts.",
            completed_refs=receipt_refs,
            pending_refs=("INDEPENDENT_VERIFICATION",),
            notes="Action output is not evidence; verification remains pending.",
        )
        receipt_refs.append(self._persist_receipt(intent, phase="VERIFICATION_PENDING", status="NEEDS_RECHECK", attempt=attempt, runtime=runtime, summary=last_action.summary, checkpoint_ref=post_action_checkpoint))
        if verify is None:
            return self._result("NEEDS_RECHECK", task_id=candidate.task_id, execution_id=intent.execution_id, reason="INDEPENDENT_VERIFIER_REQUIRED", intent_ref=intent_ref, checkpoint_ref=post_action_checkpoint, receipt_refs=receipt_refs, task_status="ACTIVE")
        runtime.enter_verification()
        try:
            verification = _coerce_verification_result(_invoke(verify, runtime, last_action.to_dict(), allow_second=True))
        except ForegroundExecutionError as exc:
            verification = VerificationResult(status="FAILED", summary=str(exc))
        except Exception as exc:  # verification errors are evidence failures, not retry triggers
            verification = VerificationResult(status="FAILED", summary=f"VERIFIER_FAILED:{type(exc).__name__}")
        if verification.status != "VERIFIED" or not verification.evidence_claims:
            return self._result("VERIFICATION_FAILED", task_id=candidate.task_id, execution_id=intent.execution_id, reason=verification.summary or "CURRENT_EVIDENCE_REQUIRED", intent_ref=intent_ref, checkpoint_ref=post_action_checkpoint, receipt_refs=receipt_refs, task_status="ACTIVE")
        try:
            candidate_state = self._candidate_state(runtime, verification.candidate_state)
            completed = self.store.complete(candidate.task_id, verification.evidence_claims, candidate_state)
        except (TaskStateError, ForegroundExecutionError) as exc:
            return self._result("VERIFICATION_FAILED", task_id=candidate.task_id, execution_id=intent.execution_id, reason=f"EVIDENCE_NOT_ACCEPTED:{exc}", intent_ref=intent_ref, checkpoint_ref=post_action_checkpoint, receipt_refs=receipt_refs, task_status="ACTIVE")
        evidence_refs: list[str] = []
        for claim in verification.evidence_claims:
            if isinstance(claim, EvidenceClaim):
                for item in claim.actual_evidence:
                    if isinstance(item, Mapping):
                        reference = str(item.get("evidence_ref") or item.get("source") or "").strip()
                        if reference and reference not in evidence_refs:
                            evidence_refs.append(reference)
            elif isinstance(claim, Mapping):
                for item in claim.get("actual_evidence", ()) if isinstance(claim.get("actual_evidence", ()), (list, tuple)) else ():
                    if isinstance(item, Mapping):
                        reference = str(item.get("evidence_ref") or item.get("source") or "").strip()
                        if reference and reference not in evidence_refs:
                            evidence_refs.append(reference)
        final_receipt = self._persist_receipt(intent, phase="VERIFIED", status="DONE", attempt=attempt, runtime=runtime, summary=verification.summary, evidence_refs=evidence_refs, checkpoint_ref=post_action_checkpoint)
        receipt_refs.append(final_receipt)
        return self._result("DONE", task_id=candidate.task_id, execution_id=intent.execution_id, reason="CURRENT_EVIDENCE_VERIFIED", intent_ref=intent_ref, checkpoint_ref=post_action_checkpoint, receipt_refs=receipt_refs, task_status=completed.tasks[candidate.task_id].status, evidence_refs=evidence_refs, plan_hash=completed.canonical_hash())

    def execute(
        self,
        action: Callable[..., Any],
        verify: Callable[..., Any] | None,
        *,
        task_id: str | None = None,
        action_name: str = "direct_foreground_action",
        budget: ExecutionBudget | None = None,
        verification_plan: Mapping[str, Any] | None = None,
        owner_gate: Mapping[str, Any] | None = None,
        capability_readiness: Mapping[str, Mapping[str, Any]] | None = None,
        permission_state: Mapping[str, Mapping[str, Any]] | None = None,
        context_state: Mapping[str, Mapping[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Execute at most one task through the explicit direct foreground path."""

        try:
            if not callable(action):
                return self._result("FAILED", task_id=task_id, reason="DIRECT_ACTION_CALLBACK_REQUIRED")
            return self._execute_inner(
                action=action,
                verify=verify,
                task_id=task_id,
                action_name=action_name,
                budget=budget or ExecutionBudget(),
                verification_plan=verification_plan,
                owner_gate=owner_gate,
                capability_readiness=capability_readiness,
                permission_state=permission_state,
                context_state=context_state,
            )
        except ForegroundExecutionError as exc:
            return self._result("CONTROL_PLANE_ERROR", task_id=task_id, reason=str(exc))
        except Exception as exc:
            return self._result("CONTROL_PLANE_ERROR", task_id=task_id, reason=f"CONTROLLER_FAILURE:{type(exc).__name__}")

    def _find_execution(self, task: TaskRecord) -> tuple[ExecutionIntent, Path, dict[str, Any] | None] | None:
        base = self.root / FOREGROUND_STATE_RELATIVE_ROOT
        if not base.exists() or not base.is_dir() or base.is_symlink():
            return None
        matches: list[tuple[str, Path, dict[str, Any] | None]] = []
        for directory in sorted(base.iterdir()):
            if not directory.is_dir() or directory.is_symlink() or not _EXECUTION_ID_RE.fullmatch(directory.name):
                continue
            intent_path = directory / "intent.json"
            if not intent_path.is_file() or intent_path.is_symlink():
                continue
            try:
                intent = ExecutionIntent.from_mapping(json.loads(intent_path.read_text(encoding="utf-8")))
            except (OSError, UnicodeError, json.JSONDecodeError, ForegroundExecutionError):
                continue
            if intent.task_id != task.task_id or intent.goal_id != task.goal_id:
                continue
            latest: dict[str, Any] | None = None
            receipts = directory / "receipts"
            if receipts.is_dir() and not receipts.is_symlink():
                for receipt_path in sorted(receipts.glob("*.json"))[-1:]:
                    try:
                        candidate = json.loads(receipt_path.read_text(encoding="utf-8"))
                        if isinstance(candidate, Mapping) and candidate.get("schema") == FOREGROUND_RECEIPT_SCHEMA:
                            latest = dict(candidate)
                    except (OSError, UnicodeError, json.JSONDecodeError):
                        continue
            matches.append((intent.created_at, intent, latest))
        if not matches:
            return None
        _, intent, latest = sorted(matches, key=lambda item: item[0])[-1]
        return intent, self._execution_dir(intent.execution_id), latest

    def _resume_artifact_bindings(self, intent: ExecutionIntent, latest: Mapping[str, Any] | None) -> tuple[dict[str, Any], ...]:
        refs = _refs(latest.get("artifact_refs", ()) if isinstance(latest, Mapping) else (), "resume.artifact_refs")
        bindings: list[dict[str, Any]] = []
        for relative in refs:
            normalized = relative.replace("\\", "/")
            if any(part in {"", ".", ".."} for part in Path(normalized).parts):
                raise ForegroundScopeError("RESUME_ARTIFACT_PATH_INVALID")
            target = (self.root / normalized).resolve(strict=False)
            try:
                target.relative_to(self.root)
            except ValueError as exc:
                raise ForegroundScopeError("RESUME_ARTIFACT_OUTSIDE_PROJECT") from exc
            digest = "MISSING"
            if target.is_file() and not target.is_symlink():
                hasher = hashlib.sha256()
                with target.open("rb") as handle:
                    while chunk := handle.read(64 * 1024):
                        hasher.update(chunk)
                digest = hasher.hexdigest()
            bindings.append({"path": normalized, "sha256": digest})
        return tuple(bindings)

    def resume(
        self,
        verify: Callable[..., Any] | None = None,
        *,
        capability_readiness: Mapping[str, Mapping[str, Any]] | None = None,
        permission_state: Mapping[str, Mapping[str, Any]] | None = None,
        context_state: Mapping[str, Mapping[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Recheck one ACTIVE task without rerunning its direct action."""

        try:
            plan = self._control_plane()
            active = self._active_tasks(plan)
            if not active:
                return self._result("NO_ACTIVE_TASK", reason="NO_ACTIVE_FOREGROUND_EXECUTION")
            if len(active) != 1:
                raise ForegroundControlPlaneError("MULTIPLE_ACTIVE_TASKS")
            task = active[0]
            found = self._find_execution(task)
            if found is None:
                return self._result("UNKNOWN", task_id=task.task_id, reason="EXECUTION_INTENT_NOT_FOUND", task_status=task.status)
            intent, execution_dir, latest = found
            if intent.plan_revision != plan.plan_revision:
                return self._result("NEEDS_RECHECK", task_id=task.task_id, execution_id=intent.execution_id, reason="PLAN_REVISION_CHANGED", task_status=task.status)
            try:
                updated, preflight_result = self.store.preflight(
                    task.task_id,
                    capability_readiness=capability_readiness,
                    permission_state=permission_state,
                    context_state=context_state,
                )
            except TaskStateError as exc:
                raise ForegroundControlPlaneError(str(exc)) from exc
            task = updated.tasks[task.task_id]
            if preflight_result.get("status") != "PASS":
                return self._result(str(preflight_result.get("status", "UNKNOWN")), task_id=task.task_id, execution_id=intent.execution_id, reason="CURRENT_PREFLIGHT_NOT_PASS", preflight=preflight_result, task_status=task.status)
            bindings = self._resume_artifact_bindings(intent, latest)
            current_state_fingerprint = _sha256({
                "schema": "p2p-foreground-state-binding/1",
                "task_id": intent.task_id,
                "plan_hash": intent.plan_hash,
                "artifacts": list(bindings),
            })
            current_evidence = task.checkpoint.get("evidence_fingerprints", {}) if isinstance(task.checkpoint, Mapping) else {}
            classification = classify_resume(
                task,
                current_state_fingerprint=current_state_fingerprint,
                current_evidence_fingerprints=current_evidence,
                current_preflight=preflight_result,
            )
            runtime = ExecutionRuntime(self.root, replace(intent, budget=replace(intent.budget, allow_mutation=False)), read_only=True)
            for item in bindings:
                runtime._artifact_paths.add(str(item["path"]))
            if classification.get("resume_classification") not in {"SAFE_TO_RESUME", "NEEDS_RECHECK"}:
                return self._result(str(classification.get("resume_classification", "UNKNOWN")), task_id=task.task_id, execution_id=intent.execution_id, reason=str(classification.get("reason", "RESUME_NOT_SAFE")), resume=classification, task_status=task.status)
            if verify is None:
                return self._result(str(classification["resume_classification"]), task_id=task.task_id, execution_id=intent.execution_id, reason="READ_ONLY_VERIFIER_REQUIRED", resume=classification, task_status=task.status)
            try:
                verification = _coerce_verification_result(_invoke(verify, runtime))
            except ForegroundExecutionError as exc:
                verification = VerificationResult(status="FAILED", summary=str(exc))
            except Exception as exc:
                verification = VerificationResult(status="FAILED", summary=f"VERIFIER_FAILED:{type(exc).__name__}")
            if verification.status != "VERIFIED" or not verification.evidence_claims:
                checkpoint_ref = self._persist_checkpoint(
                    intent,
                    runtime,
                    classification="NEEDS_RECHECK",
                    next_safe_step="Run the read-only verifier again only after the current evidence is corrected or refreshed.",
                    completed_refs=(),
                    pending_refs=("INDEPENDENT_VERIFICATION",),
                    evidence_fingerprints=current_evidence,
                    notes=verification.summary or "Resume verification did not provide current bound evidence.",
                )
                return self._result("NEEDS_RECHECK", task_id=task.task_id, execution_id=intent.execution_id, reason=verification.summary or "CURRENT_EVIDENCE_REQUIRED", resume=classification, checkpoint_ref=checkpoint_ref, task_status="ACTIVE")
            try:
                completed = self.store.complete(task.task_id, verification.evidence_claims, self._candidate_state(runtime, verification.candidate_state))
            except (TaskStateError, ForegroundExecutionError) as exc:
                return self._result("VERIFICATION_FAILED", task_id=task.task_id, execution_id=intent.execution_id, reason=f"EVIDENCE_NOT_ACCEPTED:{exc}", resume=classification, task_status="ACTIVE")
            final_receipt = self._persist_receipt(intent, phase="RESUME_VERIFIED", status="DONE", attempt=0, runtime=runtime, summary=verification.summary, checkpoint_ref=str(task.checkpoint.get("checkpoint_ref")) if isinstance(task.checkpoint, Mapping) else None)
            return self._result("DONE", task_id=task.task_id, execution_id=intent.execution_id, reason="CURRENT_EVIDENCE_VERIFIED_ON_RESUME", resume=classification, receipt_refs=[final_receipt], task_status=completed.tasks[task.task_id].status, plan_hash=completed.canonical_hash())
        except ForegroundExecutionError as exc:
            return self._result("CONTROL_PLANE_ERROR", reason=str(exc))
        except Exception as exc:
            return self._result("CONTROL_PLANE_ERROR", reason=f"RESUME_FAILURE:{type(exc).__name__}")


__all__ = [
    "FOREGROUND_INTENT_SCHEMA",
    "FOREGROUND_RECEIPT_SCHEMA",
    "FOREGROUND_CHECKPOINT_SCHEMA",
    "FOREGROUND_RESULT_SCHEMA",
    "FOREGROUND_STATE_RELATIVE_ROOT",
    "FOREGROUND_EXECUTION_STRATEGY",
    "DELEGATION_STATUS",
    "ForegroundExecutionError",
    "ForegroundContractError",
    "ForegroundScopeError",
    "ForegroundBudgetError",
    "ForegroundPermissionError",
    "ForegroundControlPlaneError",
    "ForegroundInterrupted",
    "ForegroundVerificationError",
    "ExecutionBudget",
    "ExecutionIntent",
    "ActionResult",
    "VerificationResult",
    "ExecutionRuntime",
    "ForegroundExecutionController",
]
