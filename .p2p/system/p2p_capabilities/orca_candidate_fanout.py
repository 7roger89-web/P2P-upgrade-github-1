"""ORCA bounded candidate fanout — a narrow composition seam over C17, C15, and FW06.

This module owns only these bounded responsibilities:

1. deterministic candidate identity (``CandidateSpec.candidate_id``);
2. hard fanout admission (``HARD_FANOUT_CAP = 2``; reject empty, oversized,
   duplicate, or invalid requests — no truncation, queue, or rescue candidate);
3. C15 permission no-widen admission (equal or narrower only);
4. candidate-bound workspace records composed through FW06's existing lease,
   worktree, and lifecycle surfaces;
5. immutable, bounded execution receipts with deterministic validation; and
6. one deterministic acceptance-criteria comparator over revalidated receipts.

This is not an executor or a second workspace/lease/state manager. FW06 owns
workspace, worktree, lease, and lifecycle state. ORCA adds no checkpoint store,
recovery path, router, scheduler, queue, generic scoring/judging system,
promotion path, or background/autonomous execution. Receipt and comparator
validation do not run candidates or mutate authoritative task state. The hard
cap never widens C17. ``REAL_CANDIDATE_MUTATION_RUNTIME=NOT_PROVEN``.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Mapping, Sequence

from . import fw06_operational_resilience as fw06
from .bounded_delegation import PermissionEnvelope, scope_is_subset
from .parallel_execution import MAX_PARALLEL_CHILDREN

ORCA_CANDIDATE_SCHEMA = "p2p-orca-candidate/1"
ORCA_FANOUT_SCHEMA = "p2p-orca-candidate-fanout/1"

# Hard ORCA ceiling. Equals the existing C17 bounded-parallelism ceiling; ORCA
# never widens it, and the guard below fails closed if it ever would.
HARD_FANOUT_CAP = 2
C17_PARALLEL_CEILING = MAX_PARALLEL_CHILDREN

if HARD_FANOUT_CAP > C17_PARALLEL_CEILING:  # pragma: no cover - structural guard
    raise RuntimeError("ORCA_FANOUT_CAP_EXCEEDS_C17_CEILING")

ERROR_FANOUT_INPUT_INVALID = "ORCA_FANOUT_INPUT_INVALID"
ERROR_FANOUT_EMPTY = "ORCA_FANOUT_EMPTY"
ERROR_FANOUT_CAP_EXCEEDED = "ORCA_FANOUT_CAP_EXCEEDED"
ERROR_CANDIDATE_INVALID = "ORCA_CANDIDATE_INVALID"
ERROR_CANDIDATE_DUPLICATE = "ORCA_CANDIDATE_DUPLICATE"
ERROR_PARENT_PERMISSION_INVALID = "ORCA_PARENT_PERMISSION_INVALID"
ERROR_PERMISSION_ENVELOPE_INVALID = "ORCA_PERMISSION_ENVELOPE_INVALID"
ERROR_PERMISSION_FINGERPRINT_MISMATCH = "ORCA_PERMISSION_FINGERPRINT_MISMATCH"
ERROR_PERMISSION_SCOPE_MISSING = "ORCA_PERMISSION_SCOPE_MISSING"
ERROR_PERMISSION_WIDENED = "ORCA_PERMISSION_WIDENED"
ERROR_SCOPE_WIDENED = "ORCA_SCOPE_WIDENED"

ORCA_WORKSPACE_SCHEMA = "p2p-orca-candidate-workspace/1"
ORCA_RECEIPT_SCHEMA = "p2p-orca-candidate-execution-receipt/1"

ERROR_WORKSPACE_INPUT_INVALID = "ORCA_WORKSPACE_INPUT_INVALID"
ERROR_WORKSPACE_BASE_INVALID = "ORCA_WORKSPACE_BASE_INVALID"
ERROR_WORKSPACE_CAPACITY = "ORCA_WORKSPACE_CAPACITY"
ERROR_WORKSPACE_LEASE_UNAVAILABLE = "ORCA_WORKSPACE_LEASE_UNAVAILABLE"
ERROR_WORKSPACE_CREATE_FAILED = "ORCA_WORKSPACE_CREATE_FAILED"
ERROR_WORKSPACE_PARTIAL_FAILURE = "ORCA_WORKSPACE_PARTIAL_FAILURE"
ERROR_WORKSPACE_CANDIDATE_MISMATCH = "ORCA_WORKSPACE_CANDIDATE_MISMATCH"
ERROR_WORKSPACE_BASE_MISMATCH = "ORCA_WORKSPACE_BASE_MISMATCH"
ERROR_WORKSPACE_BINDING_INVALID = "ORCA_WORKSPACE_BINDING_INVALID"
ERROR_WORKSPACE_STALE = "ORCA_WORKSPACE_STALE"
ERROR_WORKSPACE_PERMISSION_MISMATCH = "ORCA_WORKSPACE_PERMISSION_MISMATCH"

ERROR_RECEIPT_MALFORMED = "ORCA_RECEIPT_MALFORMED"
ERROR_RECEIPT_FINGERPRINT_MISMATCH = "ORCA_RECEIPT_FINGERPRINT_MISMATCH"
ERROR_RECEIPT_CANDIDATE_MISMATCH = "ORCA_RECEIPT_CANDIDATE_MISMATCH"
ERROR_RECEIPT_TASK_MISMATCH = "ORCA_RECEIPT_TASK_MISMATCH"
ERROR_RECEIPT_BASE_MISMATCH = "ORCA_RECEIPT_BASE_MISMATCH"
ERROR_RECEIPT_WORKSPACE_MISMATCH = "ORCA_RECEIPT_WORKSPACE_MISMATCH"
ERROR_RECEIPT_PERMISSION_MISMATCH = "ORCA_RECEIPT_PERMISSION_MISMATCH"
ERROR_RECEIPT_ACCEPTANCE_MISMATCH = "ORCA_RECEIPT_ACCEPTANCE_MISMATCH"
ERROR_RECEIPT_EXECUTION_INVALID = "ORCA_RECEIPT_EXECUTION_INVALID"
ERROR_RECEIPT_VERIFICATION_INVALID = "ORCA_RECEIPT_VERIFICATION_INVALID"
ERROR_RECEIPT_EVIDENCE_MISSING = "ORCA_RECEIPT_EVIDENCE_MISSING"

_MAX_TEXT = 1024
_MAX_REVISION = 256
_MAX_FINGERPRINT = 128
_MAX_RECEIPT_REFS = 8
_MAX_RECEIPT_REF_LENGTH = 256
_ABSOLUTE_REF = re.compile(r"^(?:/|[a-zA-Z]:[\\/])")
_SECRET_LIKE = re.compile(r"secret|token|password|credential|api[_-]?key", re.IGNORECASE)
_COMMIT_ID = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
_CANDIDATE_ID = re.compile(r"^orca-candidate-[0-9a-f]{32}$")
_WORKSPACE_ID = re.compile(r"^orca-ws-[0-9a-f]{32}$")
_WORKSPACE_PURPOSE_PREFIX = "orca_candidate:"
_EXECUTION_STATUSES = frozenset({"COMPLETED", "FAILED", "BLOCKED", "NOT_RUN"})
_VERIFICATION_STATUSES = frozenset({"PASS", "FAIL", "BLOCKED", "NOT_VERIFIED"})
_WORKSPACE_STATES = frozenset({("ACTIVE", "ACTIVE"), ("QUIESCED", "COMPLETE")})


class OrcaFanoutError(ValueError):
    """Base error for an invalid or unsafe ORCA fanout request."""

    code = ERROR_FANOUT_INPUT_INVALID

    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}:{detail}" if detail else code)


class OrcaCandidateError(OrcaFanoutError):
    """Raised when a candidate object is invalid or duplicated."""


class OrcaPermissionBoundaryError(OrcaFanoutError):
    """Raised when a candidate would widen parent permission or scope."""


def _sha256(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _bounded_text(value: Any, field: str, *, limit: int, forbid_absolute: bool = False) -> str:
    if not isinstance(value, str):
        raise OrcaCandidateError(ERROR_CANDIDATE_INVALID, f"{field}_MUST_BE_STRING")
    text = value.strip()
    if not text or text != value:
        raise OrcaCandidateError(ERROR_CANDIDATE_INVALID, f"{field}_MUST_BE_NON_EMPTY_TRIMMED")
    if len(text) > limit:
        raise OrcaCandidateError(ERROR_CANDIDATE_INVALID, f"{field}_TOO_LONG")
    if any(character.isspace() for character in text):
        raise OrcaCandidateError(ERROR_CANDIDATE_INVALID, f"{field}_WHITESPACE")
    if _SECRET_LIKE.search(text):
        raise OrcaCandidateError(ERROR_CANDIDATE_INVALID, f"{field}_SECRET_LIKE")
    if forbid_absolute and _ABSOLUTE_REF.match(text):
        raise OrcaCandidateError(ERROR_CANDIDATE_INVALID, f"{field}_MUST_BE_RELATIVE")
    if "\\" in text:
        raise OrcaCandidateError(ERROR_CANDIDATE_INVALID, f"{field}_MUST_USE_FORWARD_SLASH")
    return text


def permission_fingerprint(envelope: PermissionEnvelope) -> str:
    """Deterministic C15 fingerprint for an explicit permission envelope."""

    if not isinstance(envelope, PermissionEnvelope):
        raise OrcaPermissionBoundaryError(ERROR_PERMISSION_ENVELOPE_INVALID, "not_a_permission_envelope")
    return _sha256({"schema": "p2p-permission-envelope/1", "envelope": envelope.to_dict()})


@dataclass(frozen=True)
class CandidateSpec:
    """Immutable identity of one isolated ORCA candidate.

    All identity fields are canonical inputs: the same inputs always produce
    the same ``candidate_id``, and changing any one of spec ref, base
    revision, permission fingerprint, ordinal/variant, or acceptance
    fingerprint changes the identity. No random UUID is used.
    """

    spec_ref: str
    base_revision: str
    permission_fingerprint: str
    candidate_ordinal: int
    acceptance_fingerprint: str
    permission: PermissionEnvelope = PermissionEnvelope()
    variant: str = ""

    def __post_init__(self) -> None:
        _bounded_text(self.spec_ref, "spec_ref", limit=_MAX_TEXT, forbid_absolute=True)
        _bounded_text(self.base_revision, "base_revision", limit=_MAX_REVISION)
        _bounded_text(self.permission_fingerprint, "permission_fingerprint", limit=_MAX_FINGERPRINT)
        _bounded_text(self.acceptance_fingerprint, "acceptance_fingerprint", limit=_MAX_FINGERPRINT)
        if self.variant:
            _bounded_text(self.variant, "variant", limit=_MAX_FINGERPRINT)
        if isinstance(self.candidate_ordinal, bool) or not isinstance(self.candidate_ordinal, int):
            raise OrcaCandidateError(ERROR_CANDIDATE_INVALID, "candidate_ordinal_MUST_BE_INT")
        if self.candidate_ordinal < 0:
            raise OrcaCandidateError(ERROR_CANDIDATE_INVALID, "candidate_ordinal_MUST_BE_NON_NEGATIVE")
        if not isinstance(self.permission, PermissionEnvelope):
            raise OrcaCandidateError(ERROR_CANDIDATE_INVALID, "permission_MUST_BE_PERMISSION_ENVELOPE")

    @property
    def identity_payload(self) -> dict[str, Any]:
        """Canonical identity inputs; stable key order and separators."""

        return {
            "acceptance_fingerprint": self.acceptance_fingerprint,
            "base_revision": self.base_revision,
            "candidate_ordinal": self.candidate_ordinal,
            "permission_fingerprint": self.permission_fingerprint,
            "schema": ORCA_CANDIDATE_SCHEMA,
            "spec_ref": self.spec_ref,
            "variant": self.variant,
        }

    @property
    def candidate_id(self) -> str:
        """Deterministic candidate identity; same canonical inputs => same ID."""

        return f"orca-candidate-{_sha256(self.identity_payload)[:32]}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "spec_ref": self.spec_ref,
            "base_revision": self.base_revision,
            "permission_fingerprint": self.permission_fingerprint,
            "candidate_ordinal": self.candidate_ordinal,
            "variant": self.variant,
            "acceptance_fingerprint": self.acceptance_fingerprint,
            "permission": self.permission.to_dict(),
        }


@dataclass(frozen=True)
class FanoutPlan:
    """Admitted bounded candidate set. A plan, not a runner or a receipt."""

    candidates: tuple[CandidateSpec, ...]
    hard_fanout_cap: int = HARD_FANOUT_CAP
    c17_parallel_ceiling: int = C17_PARALLEL_CEILING
    schema: str = ORCA_FANOUT_SCHEMA

    @property
    def planned_count(self) -> int:
        return len(self.candidates)

    @property
    def candidate_ids(self) -> tuple[str, ...]:
        return tuple(candidate.candidate_id for candidate in self.candidates)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "hard_fanout_cap": self.hard_fanout_cap,
            "c17_parallel_ceiling": self.c17_parallel_ceiling,
            "planned_count": self.planned_count,
            "candidates": [candidate.to_dict() for candidate in self.candidates],
        }


def check_candidate_permission(candidate: CandidateSpec, parent_permission: PermissionEnvelope) -> None:
    """Fail closed unless the candidate permission is equal or narrower (C15)."""

    if not isinstance(candidate, CandidateSpec):
        raise OrcaCandidateError(ERROR_CANDIDATE_INVALID, "not_a_candidate_spec")
    envelope = candidate.permission
    if candidate.permission_fingerprint != permission_fingerprint(envelope):
        raise OrcaPermissionBoundaryError(
            ERROR_PERMISSION_FINGERPRINT_MISMATCH, candidate.candidate_id
        )
    if not isinstance(parent_permission, PermissionEnvelope):
        raise OrcaPermissionBoundaryError(ERROR_PARENT_PERMISSION_INVALID, "parent_permission_not_a_permission_envelope")
    if not envelope.scope:
        raise OrcaPermissionBoundaryError(
            ERROR_PERMISSION_SCOPE_MISSING, f"{candidate.candidate_id}_SCOPE_MUST_BE_EXPLICIT"
        )
    # Reuse C15 semantics directly; do not restate permission theory here.
    if not set(envelope.grants).issubset(set(parent_permission.grants)):
        raise OrcaPermissionBoundaryError(ERROR_PERMISSION_WIDENED, candidate.candidate_id)
    if not scope_is_subset(envelope.scope, parent_permission.scope):
        raise OrcaPermissionBoundaryError(ERROR_SCOPE_WIDENED, candidate.candidate_id)
    if not envelope.subset_of(parent_permission):
        # Authoritative fail-closed net over the full C15 subset contract.
        raise OrcaPermissionBoundaryError(ERROR_PERMISSION_WIDENED, candidate.candidate_id)


def plan_candidate_fanout(
    candidates: Sequence[CandidateSpec],
    parent_permission: PermissionEnvelope,
) -> FanoutPlan:
    """Admit 1..HARD_FANOUT_CAP valid, distinct, no-widen candidates.

    Rejections are total: an invalid request is never truncated, queued,
    retried, or rescued with a substitute candidate.
    """

    if not isinstance(parent_permission, PermissionEnvelope):
        raise OrcaPermissionBoundaryError(ERROR_PARENT_PERMISSION_INVALID, "parent_permission_not_a_permission_envelope")
    if isinstance(candidates, (str, bytes, bytearray, dict, set, frozenset)) or not isinstance(candidates, Sequence):
        raise OrcaFanoutError(ERROR_FANOUT_INPUT_INVALID, "candidates_MUST_BE_ORDERED_SEQUENCE")

    items = tuple(candidates)
    for index, candidate in enumerate(items):
        if not isinstance(candidate, CandidateSpec):
            raise OrcaCandidateError(ERROR_CANDIDATE_INVALID, f"index_{index}_NOT_A_CANDIDATE_SPEC")

    if not items:
        raise OrcaFanoutError(ERROR_FANOUT_EMPTY, f"minimum_1_candidate_cap_{HARD_FANOUT_CAP}")
    if len(items) > HARD_FANOUT_CAP:
        raise OrcaFanoutError(
            ERROR_FANOUT_CAP_EXCEEDED,
            f"requested_{len(items)}_cap_{HARD_FANOUT_CAP}_NO_TRUNCATION",
        )

    seen: set[str] = set()
    for candidate in items:
        candidate_id = candidate.candidate_id
        if candidate_id in seen:
            raise OrcaCandidateError(ERROR_CANDIDATE_DUPLICATE, candidate_id)
        seen.add(candidate_id)

    for candidate in items:
        check_candidate_permission(candidate, parent_permission)

    return FanoutPlan(candidates=items)


class OrcaWorkspaceError(OrcaFanoutError):
    """Raised when an FW06-backed candidate workspace cannot be bound safely."""


class OrcaWorkspacePartialFailure(OrcaWorkspaceError):
    """One bounded failure record for a partially-created candidate batch."""

    def __init__(
        self,
        *,
        created_workspace_ids: Sequence[str],
        failed_candidate_id: str,
        failed_candidate_index: int,
        failure_code: str,
        lease_id: str,
        lease_released: bool,
        marked_workspace_ids: Sequence[str],
        durable_partial_recorded: bool,
        containment_error_codes: Sequence[str] = (),
    ) -> None:
        self.created_workspace_ids = tuple(created_workspace_ids)
        self.failed_candidate_id = failed_candidate_id
        self.failed_candidate_index = failed_candidate_index
        self.failure_code = failure_code
        self.lease_id = lease_id
        self.lease_released = lease_released
        self.marked_workspace_ids = tuple(marked_workspace_ids)
        self.durable_partial_recorded = durable_partial_recorded
        self.containment_error_codes = tuple(containment_error_codes)
        created = ",".join(self.created_workspace_ids) or "none"
        marked = ",".join(self.marked_workspace_ids) or "none"
        detail = (
            f"created={created};failed={failed_candidate_id};index={failed_candidate_index};"
            f"cause={failure_code};marked={marked};lease_released={lease_released};"
            f"durable={durable_partial_recorded}"
        )
        super().__init__(ERROR_WORKSPACE_PARTIAL_FAILURE, detail)


def _record_partial_workspace_failure(
    root: str | Path,
    *,
    project_id: str,
    owner_task_id: str,
    created_workspace_ids: Sequence[str],
    failed_candidate_id: str,
    failed_candidate_index: int,
    failure_code: str,
    lease_released: bool,
) -> tuple[tuple[str, ...], bool, tuple[str, ...]]:
    """Keep ambiguous workspaces and mark them through the existing FW06 ledger."""

    rows = {
        str(row.get("workspace_id", "")): row
        for row in fw06.list_all_workspaces(root, project_id)
    }
    marker = {
        "schema": "p2p-orca-partial-workspace-failure/1",
        "created_workspace_ids": list(created_workspace_ids),
        "failed_candidate_id": failed_candidate_id,
        "failed_candidate_index": failed_candidate_index,
        "failure_code": failure_code,
        "lease_released": lease_released,
    }
    marked: list[str] = []
    errors: list[str] = []
    for workspace_id in created_workspace_ids:
        record = rows.get(workspace_id)
        if not isinstance(record, Mapping):
            errors.append("FW06_WORKSPACE_RECORD_MISSING")
            continue
        updated = dict(record)
        updated["status"] = "CONFLICT"
        reasons = updated.get("protection_reasons")
        if not isinstance(reasons, (list, tuple)):
            reasons = []
        preserved = [reason for reason in reasons if isinstance(reason, str)]
        if "UNKNOWN" not in preserved:
            preserved.append("UNKNOWN")
        updated["protection_reasons"] = preserved
        updated["orca_partial_failure"] = marker
        try:
            fw06.register_workspace(root, updated)
            marked.append(workspace_id)
        except Exception as exc:  # fail closed; preserve the original FW06 row
            errors.append(f"FW06_MARK_{type(exc).__name__.upper()}")

    try:
        fw06.append_fw06_event(root, "ORCA_CANDIDATE_FANOUT_PARTIAL_FAILURE", {
            "project_id": project_id,
            "task_id": owner_task_id,
            **marker,
            "marked_workspace_ids": marked,
        })
        event_recorded = True
    except Exception as exc:  # fail closed; the structured exception still reports it
        errors.append(f"FW06_EVENT_{type(exc).__name__.upper()}")
        event_recorded = False
    durable = event_recorded and len(marked) == len(created_workspace_ids)
    return tuple(marked), durable, tuple(errors)


class OrcaReceiptError(OrcaFanoutError):
    """Raised when a candidate execution receipt is malformed or stale."""


def _workspace_id_for(candidate_id: str) -> str:
    """Stable FW06 workspace ID namespaced to exactly one candidate."""

    return "orca-ws-" + _sha256({
        "candidate_id": candidate_id,
        "schema": ORCA_WORKSPACE_SCHEMA,
    })[:32]


def _workspace_purpose_for(candidate_id: str, spec_ref: str) -> str:
    """Use FW06's existing purpose discriminator for candidate and spec IDs."""

    return f"{_WORKSPACE_PURPOSE_PREFIX}{candidate_id}:{spec_ref}"


def _workspace_text(value: Any, field: str, *, limit: int) -> str:
    try:
        return _bounded_text(value, field, limit=limit)
    except OrcaCandidateError as exc:
        raise OrcaWorkspaceError(
            ERROR_WORKSPACE_INPUT_INVALID, f"{field}:{exc.detail}"
        ) from exc


@dataclass(frozen=True)
class CandidateWorkspaceBinding:
    """Immutable identity view over one FW06-managed candidate worktree.

    ``purpose`` is the existing FW06 purpose discriminator, set to the
    candidate ID. Workspace ID and root path are separate for every candidate;
    lifecycle/status values are copied from the FW06 registry, not invented
    by ORCA.
    """

    candidate_id: str
    spec_ref: str
    owner_task_id: str
    project_id: str
    base_revision: str
    workspace_id: str
    worktree_path: str
    permission_fingerprint: str
    acceptance_fingerprint: str
    status: str
    lifecycle_state: str
    purpose: str
    schema: str = ORCA_WORKSPACE_SCHEMA

    def __post_init__(self) -> None:
        if self.schema != ORCA_WORKSPACE_SCHEMA:
            raise OrcaWorkspaceError(ERROR_WORKSPACE_BINDING_INVALID, "SCHEMA_INVALID")
        if not isinstance(self.candidate_id, str) or not _CANDIDATE_ID.fullmatch(self.candidate_id):
            raise OrcaWorkspaceError(ERROR_WORKSPACE_BINDING_INVALID, "CANDIDATE_ID_INVALID")
        _workspace_text(self.spec_ref, "spec_ref", limit=_MAX_TEXT)
        _workspace_text(self.owner_task_id, "owner_task_id", limit=128)
        _workspace_text(self.project_id, "project_id", limit=128)
        _workspace_text(self.permission_fingerprint, "permission_fingerprint", limit=_MAX_FINGERPRINT)
        _workspace_text(self.acceptance_fingerprint, "acceptance_fingerprint", limit=_MAX_FINGERPRINT)
        if not isinstance(self.base_revision, str) or not _COMMIT_ID.fullmatch(self.base_revision):
            raise OrcaWorkspaceError(ERROR_WORKSPACE_BINDING_INVALID, "BASE_REVISION_INVALID")
        if self.workspace_id != _workspace_id_for(self.candidate_id):
            raise OrcaWorkspaceError(ERROR_WORKSPACE_BINDING_INVALID, "WORKSPACE_ID_NOT_CANDIDATE_BOUND")
        if self.purpose != _workspace_purpose_for(self.candidate_id, self.spec_ref):
            raise OrcaWorkspaceError(ERROR_WORKSPACE_BINDING_INVALID, "FW06_PURPOSE_NOT_CANDIDATE_SPEC_BOUND")
        if (self.status, self.lifecycle_state) not in _WORKSPACE_STATES:
            raise OrcaWorkspaceError(ERROR_WORKSPACE_BINDING_INVALID, "FW06_WORKSPACE_STATE_INVALID")
        if not isinstance(self.worktree_path, str) or not self.worktree_path.strip():
            raise OrcaWorkspaceError(ERROR_WORKSPACE_BINDING_INVALID, "WORKTREE_PATH_MISSING")
        resolved = Path(self.worktree_path).expanduser().resolve()
        object.__setattr__(self, "worktree_path", str(resolved))

def create_candidate_workspace_bindings(
    candidates: Sequence[CandidateSpec],
    parent_permission: PermissionEnvelope,
    *,
    root: str | Path,
    repo_path: str | Path,
    worktree_parent: str | Path,
    project_id: str,
    owner_task_id: str,
    goal_id: str = "",
    session_id: str = "",
    creator: str = "orca_candidate_fanout",
) -> tuple[CandidateWorkspaceBinding, ...]:
    """Create isolated, candidate-bound worktrees through existing FW06 APIs.

    The whole fanout and every permission envelope are checked before any
    worktree is created. The FW06 lease covers this bounded binding operation;
    FW06 remains the source of workspace/worktree/lifecycle records. No
    candidate execution, checkpoint store, receipt persistence, or cleanup is
    performed here.
    """

    plan = plan_candidate_fanout(candidates, parent_permission)
    project_id = _workspace_text(project_id, "project_id", limit=128)
    owner_task_id = _workspace_text(owner_task_id, "owner_task_id", limit=128)
    goal_id = _workspace_text(goal_id or owner_task_id, "goal_id", limit=128)
    creator = _workspace_text(creator, "creator", limit=128)
    if session_id:
        session_id = _workspace_text(session_id, "session_id", limit=128)

    fw06_root = Path(root).expanduser().resolve()
    repo = Path(repo_path).expanduser().resolve()
    worktree_base = Path(worktree_parent).expanduser().resolve()
    if not repo.is_dir():
        raise OrcaWorkspaceError(ERROR_WORKSPACE_INPUT_INVALID, "repo_path_NOT_DIRECTORY")

    # Require an immutable commit ID; FW06 resolves it and records the exact
    # base used for each worktree. Permission fingerprints were checked during
    # fanout admission before any workspace side effect.
    for candidate in plan.candidates:
        if not _COMMIT_ID.fullmatch(candidate.base_revision):
            raise OrcaWorkspaceError(
                ERROR_WORKSPACE_BASE_INVALID, "base_revision_MUST_BE_FULL_COMMIT_ID"
            )

    existing = {
        str(row.get("workspace_id", ""))
        for row in fw06.list_all_workspaces(fw06_root)
    }
    workspace_paths: list[tuple[CandidateSpec, str, Path]] = []
    planned_workspace_ids: set[str] = set()
    for candidate in plan.candidates:
        workspace_id = _workspace_id_for(candidate.candidate_id)
        path = worktree_base / workspace_id
        if (workspace_id in existing or workspace_id in planned_workspace_ids
                or path.exists() or path.is_symlink()):
            raise OrcaWorkspaceError(
                ERROR_WORKSPACE_STALE, f"{workspace_id}_ALREADY_REGISTERED_OR_PRESENT"
            )
        planned_workspace_ids.add(workspace_id)
        workspace_paths.append((candidate, workspace_id, path))

    capacity = fw06.parallel_capacity(fw06_root, project_id, HARD_FANOUT_CAP)
    active = capacity.get("active_workspaces")
    if (not isinstance(active, int) or isinstance(active, bool)
            or active + plan.planned_count > HARD_FANOUT_CAP):
        raise OrcaWorkspaceError(
            ERROR_WORKSPACE_CAPACITY, "FW06_PARALLEL_CAPACITY_EXCEEDED"
        )

    lease_result = fw06.acquire_lease(
        fw06_root,
        owner_process=creator,
        project_id=project_id,
        goal_id=goal_id,
        task_id=owner_task_id,
    )
    if lease_result.get("acquired") is not True:
        raise OrcaWorkspaceError(
            ERROR_WORKSPACE_LEASE_UNAVAILABLE,
            str(lease_result.get("failure_class", "LEASE_NOT_ACQUIRED")),
        )
    lease = lease_result.get("lease")
    lease_id = str(lease.get("lease_id", "")) if isinstance(lease, Mapping) else ""
    if not lease_id:
        raise OrcaWorkspaceError(ERROR_WORKSPACE_LEASE_UNAVAILABLE, "LEASE_ID_MISSING")

    bindings: list[CandidateWorkspaceBinding] = []
    created_workspace_ids: list[str] = []
    failed_candidate_id = ""
    failed_candidate_index = -1
    try:
        for index, (candidate, workspace_id, worktree_path) in enumerate(workspace_paths):
            failed_candidate_id = candidate.candidate_id
            failed_candidate_index = index
            purpose = _workspace_purpose_for(candidate.candidate_id, candidate.spec_ref)
            record = fw06.create_isolated_worktree(
                fw06_root,
                repo_path=repo,
                workspace_id=workspace_id,
                base_revision=candidate.base_revision,
                worktree_path=worktree_path,
                project_id=project_id,
                task_id=owner_task_id,
                session_id=session_id,
                creator=creator,
                purpose=purpose,
            )
            created_workspace_ids.append(workspace_id)
            expected_path = str(worktree_path.resolve())
            expected_record = {
                "workspace_id": workspace_id,
                "project_id": project_id,
                "owner_task_id": owner_task_id,
                "task_id": owner_task_id,
                "root_path": expected_path,
                "git_worktree": expected_path,
                "base_revision": candidate.base_revision,
                "workspace_type": "GIT_WORKTREE",
                "purpose": purpose,
                "mutation_policy": "SYNTHETIC_ONLY",
                "status": "ACTIVE",
                "lifecycle_state": "ACTIVE",
            }
            if any(record.get(key) != value for key, value in expected_record.items()):
                raise OrcaWorkspaceError(
                    ERROR_WORKSPACE_BINDING_INVALID, "FW06_WORKSPACE_RECORD_MISMATCH"
                )
            bindings.append(CandidateWorkspaceBinding(
                candidate_id=candidate.candidate_id,
                spec_ref=candidate.spec_ref,
                owner_task_id=owner_task_id,
                project_id=project_id,
                base_revision=candidate.base_revision,
                workspace_id=workspace_id,
                worktree_path=expected_path,
                permission_fingerprint=candidate.permission_fingerprint,
                acceptance_fingerprint=candidate.acceptance_fingerprint,
                status=str(record["status"]),
                lifecycle_state=str(record["lifecycle_state"]),
                purpose=str(record["purpose"]),
            ))
    except Exception as exc:
        failure_code = (
            exc.code if isinstance(exc, OrcaFanoutError)
            else f"FW06_{type(exc).__name__.upper()}"
        )
        containment_errors: list[str] = []
        try:
            lease_released = fw06.release_lease(fw06_root, lease_id) is True
        except Exception as release_exc:
            lease_released = False
            containment_errors.append(f"LEASE_RELEASE_{type(release_exc).__name__.upper()}")
        try:
            marked_ids, durable, mark_errors = _record_partial_workspace_failure(
                fw06_root,
                project_id=project_id,
                owner_task_id=owner_task_id,
                created_workspace_ids=created_workspace_ids,
                failed_candidate_id=failed_candidate_id,
                failed_candidate_index=failed_candidate_index,
                failure_code=failure_code,
                lease_released=lease_released,
            )
            containment_errors.extend(mark_errors)
        except Exception as mark_exc:
            marked_ids = ()
            durable = False
            containment_errors.append(f"FW06_PARTIAL_MARK_{type(mark_exc).__name__.upper()}")
        raise OrcaWorkspacePartialFailure(
            created_workspace_ids=created_workspace_ids,
            failed_candidate_id=failed_candidate_id,
            failed_candidate_index=failed_candidate_index,
            failure_code=failure_code,
            lease_id=lease_id,
            lease_released=lease_released,
            marked_workspace_ids=marked_ids,
            durable_partial_recorded=durable,
            containment_error_codes=containment_errors,
        ) from exc

    if not fw06.release_lease(fw06_root, lease_id):
        raise OrcaWorkspaceError(ERROR_WORKSPACE_LEASE_UNAVAILABLE, "LEASE_RELEASE_FAILED")
    return tuple(bindings)


def validate_candidate_workspace(
    candidate: CandidateSpec,
    binding: CandidateWorkspaceBinding,
    *,
    root: str | Path,
    parent_permission: PermissionEnvelope,
) -> CandidateWorkspaceBinding:
    """Validate candidate/workspace identity against the current FW06 record."""

    if not isinstance(candidate, CandidateSpec):
        raise OrcaWorkspaceError(ERROR_WORKSPACE_BINDING_INVALID, "CANDIDATE_SPEC_INVALID")
    if not isinstance(binding, CandidateWorkspaceBinding):
        raise OrcaWorkspaceError(ERROR_WORKSPACE_BINDING_INVALID, "BINDING_INVALID")
    check_candidate_permission(candidate, parent_permission)
    if candidate.base_revision != binding.base_revision:
        raise OrcaWorkspaceError(ERROR_WORKSPACE_BASE_MISMATCH, "CANDIDATE_BASE_DIFFERS_FROM_BINDING")
    if candidate.candidate_id != binding.candidate_id:
        raise OrcaWorkspaceError(ERROR_WORKSPACE_CANDIDATE_MISMATCH, "CANDIDATE_ID_DIFFERS_FROM_BINDING")
    if candidate.spec_ref != binding.spec_ref:
        raise OrcaWorkspaceError(ERROR_WORKSPACE_CANDIDATE_MISMATCH, "SPEC_REF_DIFFERS_FROM_BINDING")
    if (candidate.permission_fingerprint != binding.permission_fingerprint
            or candidate.acceptance_fingerprint != binding.acceptance_fingerprint):
        raise OrcaWorkspaceError(ERROR_WORKSPACE_BINDING_INVALID, "CANDIDATE_FINGERPRINT_DIFFERS_FROM_BINDING")
    if binding.workspace_id != _workspace_id_for(candidate.candidate_id):
        raise OrcaWorkspaceError(ERROR_WORKSPACE_CANDIDATE_MISMATCH, "WORKSPACE_ID_NOT_CANDIDATE_BOUND")

    registered_rows = [
        row for row in fw06.list_all_workspaces(Path(root).expanduser().resolve())
        if str(row.get("workspace_id", "")) == binding.workspace_id
    ]
    if len(registered_rows) != 1:
        raise OrcaWorkspaceError(ERROR_WORKSPACE_STALE, "FW06_WORKSPACE_RECORD_MISSING_OR_DUPLICATE")
    record = registered_rows[0]
    worktree_path = Path(binding.worktree_path).expanduser().resolve()
    expected_path = str(worktree_path)
    expected_record = {
        "project_id": binding.project_id,
        "owner_task_id": binding.owner_task_id,
        "task_id": binding.owner_task_id,
        "root_path": expected_path,
        "git_worktree": expected_path,
        "base_revision": candidate.base_revision,
        "workspace_type": "GIT_WORKTREE",
        "purpose": _workspace_purpose_for(candidate.candidate_id, candidate.spec_ref),
        "mutation_policy": "SYNTHETIC_ONLY",
    }
    if any(record.get(key) != value for key, value in expected_record.items()):
        raise OrcaWorkspaceError(ERROR_WORKSPACE_STALE, "FW06_WORKSPACE_RECORD_DIFFERS_FROM_BINDING")
    current_state = (record.get("status"), record.get("lifecycle_state"))
    binding_state = (binding.status, binding.lifecycle_state)
    if current_state not in _WORKSPACE_STATES:
        raise OrcaWorkspaceError(ERROR_WORKSPACE_STALE, "FW06_WORKSPACE_STATE_NOT_RECEIPT_SAFE")
    if binding_state != current_state and not (
            binding_state == ("ACTIVE", "ACTIVE")
            and current_state == ("QUIESCED", "COMPLETE")):
        raise OrcaWorkspaceError(ERROR_WORKSPACE_STALE, "FW06_WORKSPACE_STATE_REGRESSED_OR_CHANGED")
    if not worktree_path.is_dir():
        raise OrcaWorkspaceError(ERROR_WORKSPACE_STALE, "FW06_WORKTREE_ROOT_MISSING")
    return CandidateWorkspaceBinding(
        candidate_id=candidate.candidate_id,
        spec_ref=candidate.spec_ref,
        owner_task_id=binding.owner_task_id,
        project_id=binding.project_id,
        base_revision=candidate.base_revision,
        workspace_id=binding.workspace_id,
        worktree_path=expected_path,
        permission_fingerprint=binding.permission_fingerprint,
        acceptance_fingerprint=binding.acceptance_fingerprint,
        status=str(record["status"]),
        lifecycle_state=str(record["lifecycle_state"]),
        purpose=str(record["purpose"]),
    )


def _receipt_text(value: Any, field: str, *, limit: int, forbid_absolute: bool = False) -> str:
    try:
        return _bounded_text(value, field, limit=limit, forbid_absolute=forbid_absolute)
    except OrcaCandidateError as exc:
        raise OrcaReceiptError(ERROR_RECEIPT_MALFORMED, f"{field}:{exc.detail}") from exc


@dataclass(frozen=True)
class CandidateExecutionReceipt:
    """Immutable, source-bound receipt; it contains references, not raw output."""

    candidate_id: str
    spec_ref: str
    owner_task_id: str
    base_revision: str
    workspace_id: str
    permission_fingerprint: str
    acceptance_fingerprint: str
    execution_status: str
    verification_status: str
    output_refs: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    schema: str = ORCA_RECEIPT_SCHEMA
    receipt_fingerprint: str = ""

    def __post_init__(self) -> None:
        if self.schema != ORCA_RECEIPT_SCHEMA:
            raise OrcaReceiptError(ERROR_RECEIPT_MALFORMED, "SCHEMA_INVALID")
        candidate_id = _receipt_text(self.candidate_id, "candidate_id", limit=64)
        if not _CANDIDATE_ID.fullmatch(candidate_id):
            raise OrcaReceiptError(ERROR_RECEIPT_MALFORMED, "CANDIDATE_ID_INVALID")
        _receipt_text(self.spec_ref, "spec_ref", limit=_MAX_TEXT, forbid_absolute=True)
        _receipt_text(self.owner_task_id, "owner_task_id", limit=128)
        base_revision = _receipt_text(self.base_revision, "base_revision", limit=_MAX_REVISION)
        if not _COMMIT_ID.fullmatch(base_revision):
            raise OrcaReceiptError(ERROR_RECEIPT_MALFORMED, "BASE_REVISION_NOT_EXACT_COMMIT_ID")
        workspace_id = _receipt_text(self.workspace_id, "workspace_id", limit=64)
        if not _WORKSPACE_ID.fullmatch(workspace_id):
            raise OrcaReceiptError(ERROR_RECEIPT_MALFORMED, "WORKSPACE_ID_INVALID")
        _receipt_text(self.permission_fingerprint, "permission_fingerprint", limit=_MAX_FINGERPRINT)
        _receipt_text(self.acceptance_fingerprint, "acceptance_fingerprint", limit=_MAX_FINGERPRINT)
        if (not isinstance(self.execution_status, str)
                or self.execution_status not in _EXECUTION_STATUSES):
            raise OrcaReceiptError(ERROR_RECEIPT_MALFORMED, "EXECUTION_STATUS_INVALID")
        if (not isinstance(self.verification_status, str)
                or self.verification_status not in _VERIFICATION_STATUSES):
            raise OrcaReceiptError(ERROR_RECEIPT_VERIFICATION_INVALID, "VERIFICATION_STATUS_MISSING_OR_INVALID")

        for field_name, refs in (("output_refs", self.output_refs), ("evidence_refs", self.evidence_refs)):
            if not isinstance(refs, tuple) or len(refs) > _MAX_RECEIPT_REFS:
                raise OrcaReceiptError(ERROR_RECEIPT_MALFORMED, f"{field_name}_MUST_BE_BOUNDED_TUPLE")
            normalized: list[str] = []
            for ref in refs:
                normalized.append(_receipt_text(
                    ref, field_name, limit=_MAX_RECEIPT_REF_LENGTH, forbid_absolute=True
                ))
            if len(set(normalized)) != len(normalized):
                raise OrcaReceiptError(ERROR_RECEIPT_MALFORMED, f"{field_name}_DUPLICATE")
        if self.verification_status == "PASS" and not self.evidence_refs:
            raise OrcaReceiptError(ERROR_RECEIPT_EVIDENCE_MISSING, "PASS_REQUIRES_EVIDENCE_REFERENCE")

        if not isinstance(self.receipt_fingerprint, str):
            raise OrcaReceiptError(ERROR_RECEIPT_MALFORMED, "RECEIPT_FINGERPRINT_MUST_BE_STRING")
        expected_fingerprint = _sha256(self.identity_payload)
        if self.receipt_fingerprint == "":
            object.__setattr__(self, "receipt_fingerprint", expected_fingerprint)
        else:
            supplied = _receipt_text(self.receipt_fingerprint, "receipt_fingerprint", limit=64)
            if not re.fullmatch(r"[0-9a-f]{64}", supplied) or supplied != expected_fingerprint:
                raise OrcaReceiptError(ERROR_RECEIPT_FINGERPRINT_MISMATCH, "RECEIPT_CONTENT_CHANGED")

    @property
    def identity_payload(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "candidate_id": self.candidate_id,
            "spec_ref": self.spec_ref,
            "owner_task_id": self.owner_task_id,
            "base_revision": self.base_revision,
            "workspace_id": self.workspace_id,
            "permission_fingerprint": self.permission_fingerprint,
            "acceptance_fingerprint": self.acceptance_fingerprint,
            "execution_status": self.execution_status,
            "verification_status": self.verification_status,
            "output_refs": list(self.output_refs),
            "evidence_refs": list(self.evidence_refs),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.identity_payload,
            "receipt_fingerprint": self.receipt_fingerprint,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "CandidateExecutionReceipt":
        required = {
            "schema", "candidate_id", "spec_ref", "owner_task_id", "base_revision",
            "workspace_id", "permission_fingerprint", "acceptance_fingerprint",
            "execution_status", "verification_status", "output_refs", "evidence_refs",
            "receipt_fingerprint",
        }
        if not isinstance(value, Mapping) or set(value) != required:
            raise OrcaReceiptError(ERROR_RECEIPT_MALFORMED, "REQUIRED_FIELDS_MISMATCH")
        output_refs = value.get("output_refs")
        evidence_refs = value.get("evidence_refs")
        if not isinstance(output_refs, (list, tuple)) or not isinstance(evidence_refs, (list, tuple)):
            raise OrcaReceiptError(ERROR_RECEIPT_MALFORMED, "REFERENCE_FIELDS_MUST_BE_LISTS")
        fingerprint = value.get("receipt_fingerprint")
        if not isinstance(fingerprint, str) or not fingerprint:
            raise OrcaReceiptError(ERROR_RECEIPT_MALFORMED, "RECEIPT_FINGERPRINT_MISSING")
        return cls(
            schema=value["schema"],
            candidate_id=value["candidate_id"],
            spec_ref=value["spec_ref"],
            owner_task_id=value["owner_task_id"],
            base_revision=value["base_revision"],
            workspace_id=value["workspace_id"],
            permission_fingerprint=value["permission_fingerprint"],
            acceptance_fingerprint=value["acceptance_fingerprint"],
            execution_status=value["execution_status"],
            verification_status=value["verification_status"],
            output_refs=tuple(output_refs),
            evidence_refs=tuple(evidence_refs),
            receipt_fingerprint=value["receipt_fingerprint"],
        )


def validate_candidate_receipt(
    receipt: CandidateExecutionReceipt | Mapping[str, Any],
    candidate: CandidateSpec,
    binding: CandidateWorkspaceBinding,
    *,
    root: str | Path,
    parent_permission: PermissionEnvelope,
) -> CandidateExecutionReceipt:
    """Return only a well-formed, current, completed-and-verified receipt.

    A rejected receipt is never eligible for a later comparator. Validation is
    deterministic and read-only: no judge, execution, checkpoint, or mutation
    is performed here.
    """

    if isinstance(receipt, CandidateExecutionReceipt):
        validated = receipt
    elif isinstance(receipt, Mapping):
        validated = CandidateExecutionReceipt.from_dict(receipt)
    else:
        raise OrcaReceiptError(ERROR_RECEIPT_MALFORMED, "RECEIPT_MUST_BE_OBJECT")
    current_binding = validate_candidate_workspace(
        candidate, binding, root=root, parent_permission=parent_permission
    )
    if validated.candidate_id != candidate.candidate_id:
        raise OrcaReceiptError(ERROR_RECEIPT_CANDIDATE_MISMATCH, "CANDIDATE_ID_MISMATCH")
    if validated.spec_ref != candidate.spec_ref or validated.owner_task_id != current_binding.owner_task_id:
        raise OrcaReceiptError(ERROR_RECEIPT_TASK_MISMATCH, "SPEC_OR_OWNER_TASK_MISMATCH")
    if validated.base_revision != candidate.base_revision or validated.base_revision != current_binding.base_revision:
        raise OrcaReceiptError(ERROR_RECEIPT_BASE_MISMATCH, "BASE_REVISION_MISMATCH")
    if validated.workspace_id != current_binding.workspace_id:
        raise OrcaReceiptError(ERROR_RECEIPT_WORKSPACE_MISMATCH, "WORKSPACE_ID_MISMATCH")
    if (validated.permission_fingerprint != candidate.permission_fingerprint
            or validated.permission_fingerprint != current_binding.permission_fingerprint):
        raise OrcaReceiptError(ERROR_RECEIPT_PERMISSION_MISMATCH, "PERMISSION_FINGERPRINT_MISMATCH")
    if (validated.acceptance_fingerprint != candidate.acceptance_fingerprint
            or validated.acceptance_fingerprint != current_binding.acceptance_fingerprint):
        raise OrcaReceiptError(ERROR_RECEIPT_ACCEPTANCE_MISMATCH, "ACCEPTANCE_FINGERPRINT_MISMATCH")
    if validated.execution_status != "COMPLETED":
        raise OrcaReceiptError(ERROR_RECEIPT_EXECUTION_INVALID, "EXECUTION_NOT_COMPLETED")
    if validated.verification_status != "PASS":
        raise OrcaReceiptError(ERROR_RECEIPT_VERIFICATION_INVALID, "VERIFICATION_NOT_PASSED")
    return validated


def _bounded_comparison_items(
    value: Any,
    *,
    field: str,
    max_items: int,
    max_length: int,
    allow_empty: bool = False,
    forbid_absolute: bool = False,
) -> tuple[str, ...] | None:
    if (isinstance(value, (str, bytes, bytearray, dict, set, frozenset))
            or not isinstance(value, Sequence)):
        return None
    items = tuple(value)
    if len(items) > max_items or (not allow_empty and not items):
        return None
    try:
        normalized = tuple(
            _bounded_text(item, field, limit=max_length, forbid_absolute=forbid_absolute)
            for item in items
        )
    except OrcaCandidateError:
        return None
    if len(set(normalized)) != len(normalized):
        return None
    return normalized


def compare_validated_candidate_receipts(
    receipts: Sequence[CandidateExecutionReceipt],
    *,
    candidate_specs: Mapping[str, CandidateSpec],
    workspace_bindings: Mapping[str, CandidateWorkspaceBinding],
    root: str | Path,
    parent_permission: PermissionEnvelope,
    required_acceptance_criteria: Sequence[str],
    required_evidence_refs: Sequence[str],
    comparison_evidence: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """Deterministically select a unique acceptance winner, or abstain.

    Receipt objects are revalidated against their current candidate and FW06
    binding at the point of comparison. Caller-supplied facts are restricted to
    explicit acceptance-criterion IDs, completeness flags, and bounded evidence
    references. References are not dereferenced: this function does not prove
    their factual truth or introduce an LLM judge, score, or mutation path.
    """

    def result(verdict: str, selected: str | None, ids: Sequence[str], reason: str,
               evidence_refs: Sequence[str] = ()) -> dict[str, Any]:
        return {
            "verdict": verdict,
            "selected_candidate_id": selected,
            "candidate_ids_considered": sorted(set(ids)),
            "reason_codes": [reason],
            "evidence_refs_used": sorted(set(evidence_refs)),
        }

    if (isinstance(receipts, (str, bytes, bytearray, dict, set, frozenset))
            or not isinstance(receipts, Sequence)
            or len(receipts) < 1 or len(receipts) > HARD_FANOUT_CAP):
        return result("ABSTAIN", None, (), "FANOUT_CARDINALITY_INVALID")
    if any(not isinstance(receipt, CandidateExecutionReceipt) for receipt in receipts):
        ids = [receipt.candidate_id for receipt in receipts
               if isinstance(receipt, CandidateExecutionReceipt)]
        return result("ABSTAIN", None, ids, "RECEIPT_OBJECT_INVALID")

    candidate_ids = [receipt.candidate_id for receipt in receipts]
    if len(set(candidate_ids)) != len(candidate_ids):
        return result("ABSTAIN", None, candidate_ids, "DUPLICATE_CANDIDATE_ID")
    id_set = set(candidate_ids)
    if (not isinstance(candidate_specs, Mapping)
            or not isinstance(workspace_bindings, Mapping)
            or set(candidate_specs) != id_set
            or set(workspace_bindings) != id_set):
        return result("ABSTAIN", None, candidate_ids, "VALIDATION_CONTEXT_MISMATCH")

    receipt_by_id = {receipt.candidate_id: receipt for receipt in receipts}
    try:
        for candidate_id in sorted(id_set):
            validate_candidate_receipt(
                receipt_by_id[candidate_id],
                candidate_specs[candidate_id],
                workspace_bindings[candidate_id],
                root=root,
                parent_permission=parent_permission,
            )
    except Exception:  # any stale or failed validation makes the set ineligible
        return result("ABSTAIN", None, candidate_ids, "RECEIPT_VALIDATION_FAILED")

    criteria = _bounded_comparison_items(
        required_acceptance_criteria,
        field="acceptance_criterion_id",
        max_items=_MAX_RECEIPT_REFS,
        max_length=64,
    )
    if criteria is None:
        return result("ABSTAIN", None, candidate_ids, "COMPARISON_CRITERIA_INVALID")
    required_refs = _bounded_comparison_items(
        required_evidence_refs,
        field="comparison_evidence_ref",
        max_items=_MAX_RECEIPT_REFS,
        max_length=_MAX_RECEIPT_REF_LENGTH,
        forbid_absolute=True,
    )
    if required_refs is None:
        return result("ABSTAIN", None, candidate_ids, "COMPARISON_EVIDENCE_MISSING")
    if any(
        not set(required_refs).issubset(set(receipt_by_id[candidate_id].evidence_refs))
        for candidate_id in id_set
    ):
        return result("ABSTAIN", None, candidate_ids, "COMPARISON_EVIDENCE_MISSING")
    if not isinstance(comparison_evidence, Mapping) or set(comparison_evidence) != id_set:
        return result("ABSTAIN", None, candidate_ids, "COMPARISON_EVIDENCE_MISSING")

    fact_fields = {"satisfied_acceptance_criteria", "evidence_complete", "evidence_refs"}
    normalized_facts: dict[str, tuple[set[str], tuple[str, ...]]] = {}
    for candidate_id in sorted(id_set):
        facts = comparison_evidence[candidate_id]
        if not isinstance(facts, Mapping) or set(facts) != fact_fields:
            return result("ABSTAIN", None, candidate_ids, "COMPARISON_EVIDENCE_INVALID")
        satisfied = _bounded_comparison_items(
            facts.get("satisfied_acceptance_criteria"),
            field="acceptance_criterion_id",
            max_items=_MAX_RECEIPT_REFS,
            max_length=64,
            allow_empty=True,
        )
        if satisfied is None:
            return result("ABSTAIN", None, candidate_ids, "COMPARISON_EVIDENCE_INVALID")
        if not set(satisfied).issubset(set(criteria)):
            return result("ABSTAIN", None, candidate_ids, "INCOMPARABLE_CRITERIA")
        if type(facts.get("evidence_complete")) is not bool:
            return result("ABSTAIN", None, candidate_ids, "COMPARISON_EVIDENCE_INVALID")
        if facts["evidence_complete"] is not True:
            return result("ABSTAIN", None, candidate_ids, "EVIDENCE_INCOMPLETE")
        evidence_refs = _bounded_comparison_items(
            facts.get("evidence_refs"),
            field="comparison_evidence_ref",
            max_items=_MAX_RECEIPT_REFS,
            max_length=_MAX_RECEIPT_REF_LENGTH,
            forbid_absolute=True,
        )
        if evidence_refs is None:
            return result("ABSTAIN", None, candidate_ids, "COMPARISON_EVIDENCE_MISSING")
        if not set(required_refs).issubset(set(evidence_refs)):
            return result("ABSTAIN", None, candidate_ids, "COMPARISON_EVIDENCE_MISSING")
        normalized_facts[candidate_id] = (set(satisfied), evidence_refs)

    evidence_used = list(required_refs)
    passing = [
        candidate_id for candidate_id in sorted(id_set)
        if set(criteria).issubset(normalized_facts[candidate_id][0])
    ]
    if len(passing) == 1:
        return result("SELECT_CANDIDATE", passing[0], candidate_ids,
                      "UNIQUE_ACCEPTANCE_CRITERIA_WINNER", evidence_used)
    if len(passing) == len(candidate_ids):
        return result("ABSTAIN", None, candidate_ids,
                      "ACCEPTANCE_CRITERIA_TIE", evidence_used)
    reason = "ACCEPTANCE_CRITERIA_NOT_SATISFIED" if len(candidate_ids) == 1 \
        else "NO_CANDIDATE_MET_REQUIRED_CRITERIA"
    return result("ABSTAIN", None, candidate_ids, reason, evidence_used)


__all__ = [
    "C17_PARALLEL_CEILING",
    "CandidateExecutionReceipt",
    "CandidateSpec",
    "CandidateWorkspaceBinding",
    "ERROR_CANDIDATE_DUPLICATE",
    "ERROR_CANDIDATE_INVALID",
    "ERROR_FANOUT_CAP_EXCEEDED",
    "ERROR_FANOUT_EMPTY",
    "ERROR_FANOUT_INPUT_INVALID",
    "ERROR_PARENT_PERMISSION_INVALID",
    "ERROR_PERMISSION_ENVELOPE_INVALID",
    "ERROR_PERMISSION_FINGERPRINT_MISMATCH",
    "ERROR_PERMISSION_SCOPE_MISSING",
    "ERROR_PERMISSION_WIDENED",
    "ERROR_SCOPE_WIDENED",
    "ERROR_RECEIPT_ACCEPTANCE_MISMATCH",
    "ERROR_RECEIPT_BASE_MISMATCH",
    "ERROR_RECEIPT_CANDIDATE_MISMATCH",
    "ERROR_RECEIPT_EVIDENCE_MISSING",
    "ERROR_RECEIPT_EXECUTION_INVALID",
    "ERROR_RECEIPT_FINGERPRINT_MISMATCH",
    "ERROR_RECEIPT_MALFORMED",
    "ERROR_RECEIPT_PERMISSION_MISMATCH",
    "ERROR_RECEIPT_TASK_MISMATCH",
    "ERROR_RECEIPT_VERIFICATION_INVALID",
    "ERROR_RECEIPT_WORKSPACE_MISMATCH",
    "ERROR_WORKSPACE_BASE_INVALID",
    "ERROR_WORKSPACE_BASE_MISMATCH",
    "ERROR_WORKSPACE_BINDING_INVALID",
    "ERROR_WORKSPACE_CANDIDATE_MISMATCH",
    "ERROR_WORKSPACE_CAPACITY",
    "ERROR_WORKSPACE_CREATE_FAILED",
    "ERROR_WORKSPACE_INPUT_INVALID",
    "ERROR_WORKSPACE_LEASE_UNAVAILABLE",
    "ERROR_WORKSPACE_PARTIAL_FAILURE",
    "ERROR_WORKSPACE_PERMISSION_MISMATCH",
    "ERROR_WORKSPACE_STALE",
    "FanoutPlan",
    "HARD_FANOUT_CAP",
    "ORCA_CANDIDATE_SCHEMA",
    "ORCA_FANOUT_SCHEMA",
    "ORCA_RECEIPT_SCHEMA",
    "ORCA_WORKSPACE_SCHEMA",
    "OrcaCandidateError",
    "OrcaFanoutError",
    "OrcaPermissionBoundaryError",
    "OrcaReceiptError",
    "OrcaWorkspaceError",
    "OrcaWorkspacePartialFailure",
    "check_candidate_permission",
    "compare_validated_candidate_receipts",
    "create_candidate_workspace_bindings",
    "permission_fingerprint",
    "plan_candidate_fanout",
    "validate_candidate_receipt",
    "validate_candidate_workspace",
]
