"""Minimum durable multi-executor work-item and handoff flow (P2P-WORK-FACTORY-01).

This module is a small composition boundary over the existing P2P seams. It
adds the minimum durable work-item identity and the integration-queue
projection only; it adds no scheduler, no worker pool, no second Control
Tower, no second ledger, no new ontology, and no authority framework.

Flow:

    GOAL -> WORK_ITEM -> EXECUTION_LANE -> RETURN_PACKET
         -> INTEGRATION_QUEUE -> VERIFY -> OWNER_GATE

Reused surfaces:

- the existing execution ledger (``.p2p/state/execution-ledger.jsonl``) and
  its existing writer; work-item events are appended there, and the queue is
  a deterministic replay projection of the same ledger;
- the existing Control Tower session/return-packet contract
  (``ControlTower``, ``SessionBinding``, ``ControlTowerReturnPacket``,
  ``parse_return_packet``) for execution-lane registration, packet parsing,
  binding enforcement, idempotent replay, and stale-base reconciliation;
- host normalization (``normalize_host``): the executor's host lane is the
  existing Control Tower host lane.

Ownership semantics: a work item belongs to exactly one lane (its executor).
The queue carries explicit PROJECT/WORKSTREAM bindings, provenance
(session, packet fingerprint, base and candidate identity), and preserves
Owner Gates without executing them. ``PROMOTED``/``MERGED``/``DEPLOYED``/
``RELEASED`` are always NO here.
"""

from __future__ import annotations

from dataclasses import dataclass
import fnmatch
import json
from pathlib import Path
import re
from typing import Any, Mapping, Sequence

from .control_tower_handoff import (
    CONTROL_TOWER_LEDGER_RELATIVE_PATH,
    UNKNOWN,
    ControlTower,
    ControlTowerHandoffError,
    ControlTowerReturnPacket,
    SessionBinding,
    _append_existing_execution_event,
    _hash_or_unknown,
    _reject_secret_keys,
    _safe_json,
    _text,
    new_session_id,
    normalize_host,
    parse_return_packet,
)


WORK_ITEM_SCHEMA = "p2p-work-item/1"
WORK_ITEM_REGISTERED_EVENT_SCHEMA = "p2p-work-item-registered-event/1"
WORK_ITEM_LANE_STARTED_EVENT_SCHEMA = "p2p-work-item-lane-started-event/1"
WORK_ITEM_RETURN_EVENT_SCHEMA = "p2p-work-item-return-event/1"
WORK_ITEM_QUEUE_SCHEMA = "p2p-work-item-integration-queue/1"
WORK_ITEM_VERIFY_SCHEMA = "p2p-work-item-verify/1"

REGISTERED_EVENT_TYPE = "WORK_ITEM_REGISTERED"
LANE_STARTED_EVENT_TYPE = "WORK_ITEM_LANE_STARTED"
RETURN_EVENT_TYPE = "WORK_ITEM_RETURN"
_WORK_ITEM_EVENT_TYPES = frozenset(
    {REGISTERED_EVENT_TYPE, LANE_STARTED_EVENT_TYPE, RETURN_EVENT_TYPE}
)

WORK_ITEM_STATUSES = (
    "PLANNED",
    "ACTIVE",
    "QUEUED",
    "STALE_BASE",
    "WAITING_OWNER_GATE",
    "VERIFIED",
    "BLOCKED",
)
WORK_ITEM_NEXT_GATES = (
    "LANE",
    "RETURN_PACKET",
    "VERIFY",
    "INTEGRATION_QUEUE",
    "OWNER_GATE",
    "OWNER_REVIEW",
    "RECONCILIATION",
)
WORK_ITEM_QUEUE_STATES = (
    "EMPTY",
    "IN_PROGRESS",
    "READY_FOR_OWNER_REVIEW",
    "RECONCILIATION_REQUIRED",
)
BASE_RELATIONS = ("CURRENT", "STALE", "UNKNOWN")

_STATUS_NEXT_GATE = {
    "PLANNED": "LANE",
    "ACTIVE": "RETURN_PACKET",
    "QUEUED": "VERIFY",
    "STALE_BASE": "RECONCILIATION",
    "WAITING_OWNER_GATE": "OWNER_GATE",
    "VERIFIED": "OWNER_REVIEW",
    "BLOCKED": "RECONCILIATION",
}

_WORK_ITEM_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")
_SCOPE_ABSOLUTE_RE = re.compile(r"^(?:/|[a-zA-Z]:[\\/])")
_MAX_LABEL_LENGTH = 100


class WorkItemHandoffError(ValueError):
    """Raised when a work-item handoff violates a fail-closed boundary."""


def _work_item_id(value: Any) -> str:
    normalized = _text(value, "work_item_id", max_length=128).lower()
    if not _WORK_ITEM_ID_RE.fullmatch(normalized):
        raise WorkItemHandoffError("WORK_ITEM_ID_INVALID")
    return normalized


def _binding_label(value: Any, field_name: str) -> str:
    try:
        normalized = _text(value, field_name, max_length=_MAX_LABEL_LENGTH)
    except ControlTowerHandoffError as exc:
        raise WorkItemHandoffError(f"AMBIGUOUS_PROJECT_WORKSTREAM_BINDING:{field_name}") from exc
    if normalized.upper() in {"UNKNOWN", "NONE"}:
        raise WorkItemHandoffError("AMBIGUOUS_PROJECT_WORKSTREAM_BINDING")
    return normalized


def _explicit_hash(value: Any, field_name: str) -> str:
    normalized = _hash_or_unknown(value, field_name)
    if normalized in {"UNKNOWN", "NONE"}:
        raise WorkItemHandoffError(f"{field_name.upper()}_MUST_BE_EXPLICIT")
    return normalized


def _scope_ref(value: Any, field_name: str) -> str:
    normalized = str(value).strip().replace("\\", "/")
    if not normalized or normalized == "*" or len(normalized) > 256:
        raise WorkItemHandoffError(f"{field_name.upper()}_INVALID")
    if _SCOPE_ABSOLUTE_RE.search(normalized):
        raise WorkItemHandoffError(f"{field_name.upper()}_UNKNOWN_BOUNDARY")
    if any(part in {"", ".", ".."} for part in Path(normalized).parts):
        raise WorkItemHandoffError(f"{field_name.upper()}_UNKNOWN_BOUNDARY")
    return normalized


def _unique_refs(values: Sequence[Any] | None, field_name: str, *, required: bool) -> tuple[str, ...]:
    if values is None:
        values = ()
    if isinstance(values, (str, bytes, Mapping)):
        raise WorkItemHandoffError(f"{field_name.upper()}_MUST_BE_SEQUENCE")
    try:
        iterator = iter(values)
    except TypeError as exc:
        raise WorkItemHandoffError(f"{field_name.upper()}_MUST_BE_SEQUENCE") from exc
    result: list[str] = []
    seen: set[str] = set()
    for raw in iterator:
        item = str(raw)
        if item in seen:
            raise WorkItemHandoffError(f"{field_name.upper()}_DUPLICATE:{item}")
        seen.add(item)
        result.append(item)
    if required and not result:
        raise WorkItemHandoffError(f"{field_name.upper()}_REQUIRED")
    return tuple(result)


def _scopes_overlap(left: Sequence[str], right: Sequence[str]) -> bool:
    """Conservative scope-overlap test (same semantics as the C17 pair gate)."""

    for raw_a in left:
        for raw_b in right:
            a = raw_a.casefold().rstrip("/")
            b = raw_b.casefold().rstrip("/")
            if a == b:
                return True
            if any(token in a or token in b for token in ("*", "?", "[")):
                return True
            if a.startswith(b + "/") or b.startswith(a + "/"):
                return True
            if fnmatch.fnmatchcase(a, b) or fnmatch.fnmatchcase(b, a):
                return True
    return False


def _base_relation(base_sha: Any, base_tree: Any, current_sha: Any, current_tree: Any) -> str:
    values = (
        _hash_or_unknown(base_sha, "base_sha"),
        _hash_or_unknown(base_tree, "base_tree"),
        _hash_or_unknown(current_sha, "current_canonical_base_sha"),
        _hash_or_unknown(current_tree, "current_canonical_base_tree"),
    )
    if any(value in {"UNKNOWN", "NONE"} for value in values):
        return "UNKNOWN"
    if values[0] == values[2] and values[1] == values[3]:
        return "CURRENT"
    return "STALE"


@dataclass(frozen=True)
class WorkItem:
    """Minimum durable identity for one unit of work on one execution lane.

    ``expected_output`` doubles as the Control Tower session ``GOAL`` text,
    so a returned packet must carry the exact expected output the work item
    was registered with.
    """

    work_item_id: str
    project: str
    workstream: str
    base_sha: str
    base_tree: str
    executor: str
    scope: tuple[str, ...]
    dependencies: tuple[str, ...]
    expected_output: str
    session_id: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "work_item_id", _work_item_id(self.work_item_id))
        object.__setattr__(self, "project", _binding_label(self.project, "project"))
        object.__setattr__(self, "workstream", _binding_label(self.workstream, "workstream"))
        object.__setattr__(self, "base_sha", _explicit_hash(self.base_sha, "base_sha"))
        object.__setattr__(self, "base_tree", _explicit_hash(self.base_tree, "base_tree"))
        object.__setattr__(self, "executor", normalize_host(self.executor))
        raw_scope = self.scope
        if not isinstance(raw_scope, (tuple, list)):
            raise WorkItemHandoffError("WORK_ITEM_SCOPE_MUST_BE_SEQUENCE")
        scope = tuple(_scope_ref(item, "scope") for item in raw_scope)
        if not scope:
            raise WorkItemHandoffError("WORK_ITEM_SCOPE_REQUIRED")
        if len(set(scope)) != len(scope):
            raise WorkItemHandoffError("WORK_ITEM_SCOPE_DUPLICATE")
        object.__setattr__(self, "scope", scope)
        raw_dependencies = self.dependencies
        if not isinstance(raw_dependencies, (tuple, list)):
            raise WorkItemHandoffError("WORK_ITEM_DEPENDENCIES_MUST_BE_SEQUENCE")
        dependencies = tuple(_work_item_id(item) for item in raw_dependencies)
        if len(set(dependencies)) != len(dependencies):
            raise WorkItemHandoffError("WORK_ITEM_DEPENDENCIES_DUPLICATE")
        if self.work_item_id in dependencies:
            raise WorkItemHandoffError("WORK_ITEM_DEPENDENCY_SELF")
        object.__setattr__(self, "dependencies", dependencies)
        object.__setattr__(self, "expected_output", _text(self.expected_output, "expected_output", max_length=4096))
        object.__setattr__(self, "session_id", _text(self.session_id, "session_id", max_length=256))

    @property
    def lane(self) -> str:
        """The execution lane is the executor's existing host lane."""

        return self.executor

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": WORK_ITEM_SCHEMA,
            "WORK_ITEM_ID": self.work_item_id,
            "PROJECT": self.project,
            "WORKSTREAM": self.workstream,
            "BASE_SHA": self.base_sha,
            "BASE_TREE": self.base_tree,
            "EXECUTOR": self.executor,
            "LANE": self.lane,
            "SCOPE": list(self.scope),
            "DEPENDENCIES": list(self.dependencies),
            "EXPECTED_OUTPUT": self.expected_output,
            "SESSION_ID": self.session_id,
        }

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "WorkItem":
        if not isinstance(value, Mapping):
            raise WorkItemHandoffError("WORK_ITEM_MUST_BE_OBJECT")
        if value.get("schema") != WORK_ITEM_SCHEMA:
            raise WorkItemHandoffError("WORK_ITEM_SCHEMA_INVALID")
        allowed = {
            "schema",
            "WORK_ITEM_ID",
            "PROJECT",
            "WORKSTREAM",
            "BASE_SHA",
            "BASE_TREE",
            "EXECUTOR",
            "LANE",
            "SCOPE",
            "DEPENDENCIES",
            "EXPECTED_OUTPUT",
            "SESSION_ID",
        }
        unknown = sorted(str(key) for key in value if str(key) not in allowed)
        if unknown:
            raise WorkItemHandoffError("WORK_ITEM_FIELDS_INVALID:" + ",".join(unknown))
        item = cls(
            work_item_id=value.get("WORK_ITEM_ID"),
            project=value.get("PROJECT"),
            workstream=value.get("WORKSTREAM"),
            base_sha=value.get("BASE_SHA"),
            base_tree=value.get("BASE_TREE"),
            executor=value.get("EXECUTOR"),
            scope=tuple(value.get("SCOPE") or ()),
            dependencies=tuple(value.get("DEPENDENCIES") or ()),
            expected_output=value.get("EXPECTED_OUTPUT"),
            session_id=value.get("SESSION_ID"),
        )
        if value.get("LANE") is not None and value.get("LANE") != item.lane:
            raise WorkItemHandoffError("WORK_ITEM_LANE_MUST_BE_EXECUTOR")
        return item


class WorkItemHandoff:
    """Durable coordinator over the existing execution ledger.

    The coordinator persists only structured work-item events through the
    existing ledger writer and reuses the existing Control Tower session and
    return-packet boundary. It never launches a host, executes an Owner
    Gate, or promotes/merges/releases anything.
    """

    def __init__(
        self,
        root: str | Path,
        *,
        current_canonical_base_sha: str = UNKNOWN,
        current_canonical_base_tree: str = UNKNOWN,
    ) -> None:
        self.root = Path(root).expanduser().resolve()
        if not self.root.is_dir():
            raise WorkItemHandoffError(f"WORK_ITEM_ROOT_NOT_FOUND:{self.root}")
        self.ledger_path = self.root / CONTROL_TOWER_LEDGER_RELATIVE_PATH
        self.current_canonical_base_sha = _hash_or_unknown(
            current_canonical_base_sha, "current_canonical_base_sha"
        )
        self.current_canonical_base_tree = _hash_or_unknown(
            current_canonical_base_tree, "current_canonical_base_tree"
        )

    # ------------------------------------------------------------------
    # Ledger replay
    # ------------------------------------------------------------------

    def _read_events(self) -> list[dict[str, Any]]:
        if not self.ledger_path.exists():
            return []
        if self.ledger_path.is_symlink() or not self.ledger_path.is_file():
            raise WorkItemHandoffError("WORK_ITEM_LEDGER_PATH_INVALID")
        try:
            lines = self.ledger_path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeError) as exc:
            raise WorkItemHandoffError(f"WORK_ITEM_LEDGER_UNREADABLE:{exc}") from exc
        events: list[dict[str, Any]] = []
        for line_number, line in enumerate(lines, 1):
            if not line.strip():
                continue
            try:
                raw = json.loads(line)
            except json.JSONDecodeError as exc:
                raise WorkItemHandoffError(f"WORK_ITEM_LEDGER_INVALID_JSON:{line_number}") from exc
            if not isinstance(raw, Mapping) or raw.get("event_type") not in _WORK_ITEM_EVENT_TYPES:
                continue
            try:
                _reject_secret_keys(raw)
                safe = _safe_json(raw, path=f"ledger[{line_number}]")
            except ControlTowerHandoffError as exc:
                raise WorkItemHandoffError(f"WORK_ITEM_LEDGER_EVENT_UNSAFE:{line_number}:{exc}") from exc
            if not isinstance(safe, dict):
                raise WorkItemHandoffError(f"WORK_ITEM_LEDGER_EVENT_INVALID:{line_number}")
            safe["_LINE_NUMBER"] = line_number
            events.append(safe)
        return events

    def _replay(self) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
        """Replay the durable registry: (items, lane_starts, returns)."""

        items: dict[str, dict[str, Any]] = {}
        lane_starts: dict[str, dict[str, Any]] = {}
        returns: dict[str, dict[str, Any]] = {}
        for event in self._read_events():
            event_type = event.get("event_type")
            if event_type == REGISTERED_EVENT_TYPE:
                try:
                    item = WorkItem.from_mapping(event.get("WORK_ITEM"))
                except WorkItemHandoffError as exc:
                    raise WorkItemHandoffError(f"WORK_ITEM_LEDGER_ENTRY_INVALID:{exc}") from exc
                existing = items.get(item.work_item_id)
                if existing is not None:
                    if existing["WORK_ITEM"] != item.to_dict():
                        raise WorkItemHandoffError(f"WORK_ITEM_IDENTITY_CONFLICT:{item.work_item_id}")
                    continue
                items[item.work_item_id] = {
                    "WORK_ITEM": item.to_dict(),
                    "LINE": event.get("_LINE_NUMBER"),
                }
            elif event_type == LANE_STARTED_EVENT_TYPE:
                work_item_id = _work_item_id(event.get("WORK_ITEM_ID"))
                entry = items.get(work_item_id)
                if entry is None:
                    raise WorkItemHandoffError(f"WORK_ITEM_LANE_START_WITHOUT_REGISTRATION:{work_item_id}")
                executor = event.get("EXECUTOR")
                if executor != entry["WORK_ITEM"]["EXECUTOR"]:
                    raise WorkItemHandoffError(f"WORK_ITEM_LANE_START_CONFLICT:{work_item_id}")
                previous = lane_starts.get(work_item_id)
                if previous is not None and previous["SESSION_ID"] != event.get("SESSION_ID"):
                    raise WorkItemHandoffError(f"WORK_ITEM_LANE_START_CONFLICT:{work_item_id}")
                lane_starts.setdefault(
                    work_item_id,
                    {
                        "EXECUTOR": entry["WORK_ITEM"]["EXECUTOR"],
                        "SESSION_ID": entry["WORK_ITEM"]["SESSION_ID"],
                        "LINE": event.get("_LINE_NUMBER"),
                    },
                )
            elif event_type == RETURN_EVENT_TYPE:
                work_item_id = _work_item_id(event.get("WORK_ITEM_ID"))
                entry = items.get(work_item_id)
                if entry is None:
                    raise WorkItemHandoffError(f"WORK_ITEM_RETURN_WITHOUT_REGISTRATION:{work_item_id}")
                if entry["WORK_ITEM"]["SESSION_ID"] != event.get("SESSION_ID"):
                    raise WorkItemHandoffError(f"WORK_ITEM_RETURN_SESSION_CONFLICT:{work_item_id}")
                if _explicit_hash(event.get("CANDIDATE_SHA"), "CANDIDATE_SHA") != event.get("CANDIDATE_SHA"):
                    raise WorkItemHandoffError(f"WORK_ITEM_RETURN_CANDIDATE_MISSING:{work_item_id}")
                previous = returns.get(work_item_id)
                if previous is not None:
                    if previous.get("PACKET_FINGERPRINT") != event.get("PACKET_FINGERPRINT"):
                        raise WorkItemHandoffError(f"WORK_ITEM_MULTIPLE_RETURN_CONFLICT:{work_item_id}")
                    continue
                returns[work_item_id] = dict(event)
        return items, lane_starts, returns

    @staticmethod
    def _topological_order(items: Mapping[str, Mapping[str, Any]]) -> list[str]:
        remaining = {
            work_item_id: set(item["WORK_ITEM"]["DEPENDENCIES"]) for work_item_id, item in items.items()
        }
        order: list[str] = []
        while remaining:
            ready = sorted(work_item_id for work_item_id, deps in remaining.items() if not deps)
            if not ready:
                raise WorkItemHandoffError("WORK_ITEM_CYCLE_DETECTED")
            for work_item_id in ready:
                order.append(work_item_id)
                del remaining[work_item_id]
            for deps in remaining.values():
                deps.difference_update(ready)
        return order

    # ------------------------------------------------------------------
    # Flow steps
    # ------------------------------------------------------------------

    def register_work_item(
        self,
        *,
        work_item_id: str,
        project: str,
        workstream: str,
        base_sha: str,
        base_tree: str,
        executor: str,
        scope: Sequence[str],
        dependencies: Sequence[str] = (),
        expected_output: str,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """Register one minimum durable work-item identity (idempotent)."""

        normalized_executor = normalize_host(executor)
        if session_id is None:
            # Validate the binding labels before deriving the session ID so
            # ambiguous bindings fail with the binding error, not a session
            # derivation error.
            project_label = _binding_label(project, "project")
            workstream_label = _binding_label(workstream, "workstream")
            session_id = new_session_id(normalized_executor, workstream_label, f"{project_label}:{work_item_id}")
        item = WorkItem(
            work_item_id=work_item_id,
            project=project,
            workstream=workstream,
            base_sha=base_sha,
            base_tree=base_tree,
            executor=executor,
            scope=tuple(scope or ()),
            dependencies=tuple(dependencies or ()),
            expected_output=expected_output,
            session_id=session_id,
        )
        items, lane_starts, returns = self._replay()
        existing = items.get(item.work_item_id)
        if existing is not None:
            if existing["WORK_ITEM"] != item.to_dict():
                raise WorkItemHandoffError(f"WORK_ITEM_IDENTITY_CONFLICT:{item.work_item_id}")
            derived_status = self._derive_status(
                existing["WORK_ITEM"],
                item.work_item_id in lane_starts,
                returns.get(item.work_item_id),
            )
            return {
                "status": "PASS",
                "idempotent": True,
                "work_item": item.to_dict(),
                "lane": item.lane,
                "next_gate": _STATUS_NEXT_GATE[derived_status],
                "integration_queue": self.integration_queue(),
            }
        for other_id, other in items.items():
            other_item = other["WORK_ITEM"]
            if other_item["SESSION_ID"] == item.session_id:
                raise WorkItemHandoffError(f"WORK_ITEM_SESSION_CONFLICT:{other_id}")
            if (
                other_item["PROJECT"] == item.project
                and other_item["WORKSTREAM"] == item.workstream
                and _scopes_overlap(item.scope, other_item["SCOPE"])
            ):
                raise WorkItemHandoffError(f"WORK_ITEM_SCOPE_OVERLAP:{other_id}")
        for dependency in item.dependencies:
            dep_entry = items.get(dependency)
            if dep_entry is None:
                raise WorkItemHandoffError(f"WORK_ITEM_DEPENDENCY_NOT_REGISTERED:{dependency}")
            dep_item = dep_entry["WORK_ITEM"]
            if dep_item["PROJECT"] != item.project or dep_item["WORKSTREAM"] != item.workstream:
                raise WorkItemHandoffError(f"WORK_ITEM_DEPENDENCY_CROSS_BINDING:{dependency}")

        binding = SessionBinding(
            session_id=item.session_id,
            host=item.executor,
            goal_id=item.workstream,
            goal=item.expected_output,
        )
        tower = ControlTower(self.root)
        tower.start_session(
            binding,
            task_id=item.work_item_id,
            worktree=UNKNOWN,
            branch=UNKNOWN,
            canonical_base_sha=item.base_sha,
            canonical_base_tree=item.base_tree,
            acceptance_criteria=(item.expected_output,),
        )
        event = {
            "schema": WORK_ITEM_REGISTERED_EVENT_SCHEMA,
            "event_type": REGISTERED_EVENT_TYPE,
            "WORK_ITEM_REGISTERED": True,
            "WORK_ITEM": item.to_dict(),
            "SESSION_BINDING": binding.to_dict(),
            "PACKET_IS_CANONICAL_TRUTH": "NO",
            "PROMOTED": False,
            "PROTECTED_ACTION_EXECUTED": False,
        }
        _append_existing_execution_event(self.ledger_path, event)
        return {
            "status": "PASS",
            "idempotent": False,
            "work_item": item.to_dict(),
            "lane": item.lane,
            "next_gate": "LANE",
            "integration_queue": self.integration_queue(),
        }

    def start_lane(self, work_item_id: str) -> dict[str, Any]:
        """Move one registered work item into its executor lane (idempotent)."""

        wid = _work_item_id(work_item_id)
        items, lane_starts, returns = self._replay()
        entry = items.get(wid)
        if entry is None:
            raise WorkItemHandoffError(f"WORK_ITEM_NOT_FOUND:{wid}")
        if wid in returns:
            raise WorkItemHandoffError(f"WORK_ITEM_LANE_START_AFTER_RETURN:{wid}")
        item = entry["WORK_ITEM"]
        idempotent = wid in lane_starts
        if not idempotent:
            event = {
                "schema": WORK_ITEM_LANE_STARTED_EVENT_SCHEMA,
                "event_type": LANE_STARTED_EVENT_TYPE,
                "WORK_ITEM_LANE_STARTED": True,
                "WORK_ITEM_ID": wid,
                "EXECUTOR": item["EXECUTOR"],
                "LANE": item["EXECUTOR"],
                "SESSION_ID": item["SESSION_ID"],
                "PROMOTED": False,
                "PROTECTED_ACTION_EXECUTED": False,
            }
            _append_existing_execution_event(self.ledger_path, event)
        return {
            "status": "PASS",
            "idempotent": idempotent,
            "work_item": item,
            "lane": item["EXECUTOR"],
            "next_gate": "RETURN_PACKET",
            "integration_queue": self.integration_queue(),
        }

    def ingest_return(
        self,
        final_response: str,
        *,
        candidate_sha: str,
        candidate_tree: str,
        current_canonical_base_sha: str | None = None,
        current_canonical_base_tree: str | None = None,
    ) -> dict[str, Any]:
        """Ingest one executor's return packet for a registered work item.

        The existing Control Tower boundary parses, binding-checks, and
        reconciles the packet; this layer then binds the explicit candidate
        identity to the work item and appends the durable work-item return
        event to the same ledger.
        """

        current_sha = (
            self.current_canonical_base_sha
            if current_canonical_base_sha is None
            else current_canonical_base_sha
        )
        current_tree = (
            self.current_canonical_base_tree
            if current_canonical_base_tree is None
            else current_canonical_base_tree
        )
        current_sha = _hash_or_unknown(current_sha, "current_canonical_base_sha")
        current_tree = _hash_or_unknown(current_tree, "current_canonical_base_tree")
        # All work-item-layer validation happens BEFORE the Control Tower
        # ingestion side effect, so a refused return leaves no ledger event.
        packet = parse_return_packet(final_response)
        cand_sha = _explicit_hash(candidate_sha, "candidate_sha")
        cand_tree = _explicit_hash(candidate_tree, "candidate_tree")
        if packet.candidate_or_checkpoint_sha != "UNKNOWN" and packet.candidate_or_checkpoint_sha != cand_sha:
            raise WorkItemHandoffError("WORK_ITEM_CANDIDATE_MISMATCH")

        items, lane_starts, returns = self._replay()
        by_session = {
            item["WORK_ITEM"]["SESSION_ID"]: (wid, item["WORK_ITEM"]) for wid, item in items.items()
        }
        found = by_session.get(packet.binding.session_id)
        if found is None:
            raise WorkItemHandoffError(f"WORK_ITEM_NOT_FOUND_FOR_SESSION:{packet.binding.session_id}")
        wid, item = found
        if item["EXECUTOR"] != packet.binding.host:
            raise WorkItemHandoffError(f"WORK_ITEM_EXECUTOR_MISMATCH:{wid}")
        if wid not in lane_starts:
            raise WorkItemHandoffError(f"WORK_ITEM_RETURN_BEFORE_LANE_START:{wid}")
        if (
            _base_relation(
                item["BASE_SHA"],
                item["BASE_TREE"],
                packet.canonical_base_sha,
                packet.canonical_base_tree,
            )
            != "CURRENT"
        ):
            raise WorkItemHandoffError(f"WORK_ITEM_BASE_MISMATCH:{wid}")
        fingerprint = packet.fingerprint()
        existing_return = returns.get(wid)
        if existing_return is not None:
            if existing_return.get("PACKET_FINGERPRINT") != fingerprint:
                raise WorkItemHandoffError(f"WORK_ITEM_MULTIPLE_RETURN_CONFLICT:{wid}")
            return {
                "status": "PASS",
                "idempotent": True,
                "work_item_id": wid,
                "work_item_status": self._derive_status(item, True, existing_return),
                "packet_fingerprint": fingerprint,
                "integration_queue": self.integration_queue(current_sha, current_tree),
            }

        tower = ControlTower(
            self.root,
            current_canonical_base_sha=current_sha,
            current_canonical_base_tree=current_tree,
        )
        ct_result = tower.ingest_response(
            final_response,
            current_canonical_base_sha=current_sha,
            current_canonical_base_tree=current_tree,
        )
        reconciliation = ct_result.get("reconciliation")
        relation = reconciliation.get("CANONICAL_RELATION", UNKNOWN) if isinstance(reconciliation, Mapping) else UNKNOWN
        session_state = packet.session_state
        owner_gate = packet.owner_gate
        status, verdict, next_gate = self._return_outcome(relation, session_state, owner_gate)
        event = {
            "schema": WORK_ITEM_RETURN_EVENT_SCHEMA,
            "event_type": RETURN_EVENT_TYPE,
            "WORK_ITEM_RETURN": True,
            "WORK_ITEM_ID": wid,
            "PROJECT": item["PROJECT"],
            "WORKSTREAM": item["WORKSTREAM"],
            "EXECUTOR": item["EXECUTOR"],
            "LANE": item["EXECUTOR"],
            "BASE_SHA": item["BASE_SHA"],
            "BASE_TREE": item["BASE_TREE"],
            "SESSION_ID": item["SESSION_ID"],
            "RETURN_BASE_SHA": packet.canonical_base_sha,
            "RETURN_BASE_TREE": packet.canonical_base_tree,
            "CURRENT_CANONICAL_BASE_SHA": current_sha,
            "CURRENT_CANONICAL_BASE_TREE": current_tree,
            "CANDIDATE_SHA": cand_sha,
            "CANDIDATE_TREE": cand_tree,
            "PACKET_FINGERPRINT": fingerprint,
            "RETURN_SESSION_STATE": session_state,
            "OWNER_GATE": _safe_json(owner_gate, path="owner_gate") if owner_gate is not None else None,
            "VERDICT": verdict,
            "NEXT_GATE": next_gate,
            "PACKET_IS_CANONICAL_TRUTH": "NO",
            "PROMOTED": False,
            "MERGED": False,
            "DEPLOYED": False,
            "RELEASED": False,
        }
        _append_existing_execution_event(self.ledger_path, event)
        return {
            "status": "PASS",
            "idempotent": False,
            "work_item_id": wid,
            "work_item_status": status,
            "verdict": verdict,
            "next_gate": next_gate,
            "canonical_relation": relation,
            "candidate_sha": cand_sha,
            "candidate_tree": cand_tree,
            "packet_fingerprint": fingerprint,
            "integration_queue": self.integration_queue(current_sha, current_tree),
        }

    def integration_queue(
        self,
        current_canonical_base_sha: str | None = None,
        current_canonical_base_tree: str | None = None,
    ) -> dict[str, Any]:
        """Deterministic replay projection of the durable integration queue."""

        current_sha = (
            self.current_canonical_base_sha
            if current_canonical_base_sha is None
            else current_canonical_base_sha
        )
        current_tree = (
            self.current_canonical_base_tree
            if current_canonical_base_tree is None
            else current_canonical_base_tree
        )
        current_sha = _hash_or_unknown(current_sha, "current_canonical_base_sha")
        current_tree = _hash_or_unknown(current_tree, "current_canonical_base_tree")
        items, lane_starts, returns = self._replay()
        order = self._topological_order(items)
        entries: list[dict[str, Any]] = []
        lanes: dict[str, list[str]] = {}
        owner_gates: list[dict[str, Any]] = []
        for position, wid in enumerate(order, start=1):
            item = items[wid]["WORK_ITEM"]
            ret = returns.get(wid)
            lane_started = wid in lane_starts
            status = self._derive_status(item, lane_started, ret)
            base_relation = (
                _base_relation(item["BASE_SHA"], item["BASE_TREE"], current_sha, current_tree)
                if ret is None
                else _base_relation(
                    ret.get("RETURN_BASE_SHA"),
                    ret.get("RETURN_BASE_TREE"),
                    current_sha,
                    current_tree,
                )
            )
            owner_gate = ret.get("OWNER_GATE") if ret is not None else None
            entry = {
                "QUEUE_POSITION": position,
                "WORK_ITEM_ID": wid,
                "PROJECT": item["PROJECT"],
                "WORKSTREAM": item["WORKSTREAM"],
                "BASE_SHA": item["BASE_SHA"],
                "BASE_TREE": item["BASE_TREE"],
                "EXECUTOR": item["EXECUTOR"],
                "LANE": item["EXECUTOR"],
                "SCOPE": list(item["SCOPE"]),
                "DEPENDENCIES": list(item["DEPENDENCIES"]),
                "EXPECTED_OUTPUT": item["EXPECTED_OUTPUT"],
                "SESSION_ID": item["SESSION_ID"],
                "STATUS": status,
                "BASE_RELATION": base_relation,
                "CANDIDATE_SHA": ret.get("CANDIDATE_SHA", UNKNOWN) if ret is not None else UNKNOWN,
                "CANDIDATE_TREE": ret.get("CANDIDATE_TREE", UNKNOWN) if ret is not None else UNKNOWN,
                "PACKET_FINGERPRINT": ret.get("PACKET_FINGERPRINT", UNKNOWN) if ret is not None else UNKNOWN,
                "VERDICT": ret.get("VERDICT", UNKNOWN) if ret is not None else UNKNOWN,
                "NEXT_GATE": _STATUS_NEXT_GATE[status],
                "OWNER_GATE": owner_gate,
            }
            if isinstance(owner_gate, Mapping):
                owner_gates.append({"WORK_ITEM_ID": wid, "OWNER_GATE": dict(owner_gate)})
            lanes.setdefault(item["EXECUTOR"], []).append(wid)
            entries.append(entry)
        return {
            "schema": WORK_ITEM_QUEUE_SCHEMA,
            "CANONICAL": {
                "CURRENT_BASE_SHA": current_sha,
                "CURRENT_BASE_TREE": current_tree,
                "CANONICAL_TRUTH_UPDATED": "NO",
            },
            "ENTRIES": entries,
            "LANES": lanes,
            "OWNER_GATES": owner_gates,
            "CONFLICTS": [],
            "INTEGRATION_QUEUE_STATUS": self._queue_state(entries),
            "PERSISTENCE": {
                "PATH": CONTROL_TOWER_LEDGER_RELATIVE_PATH.as_posix(),
                "EXISTING_EXECUTION_LEDGER_ONLY": "YES",
                "SECOND_STORE_CREATED": "NO",
            },
            "PROMOTED": False,
            "MERGED": False,
            "DEPLOYED": False,
            "RELEASED": False,
            "PACKET_IS_CANONICAL_TRUTH": "NO",
        }

    def verify_integration_queue(
        self,
        current_canonical_base_sha: str | None = None,
        current_canonical_base_tree: str | None = None,
    ) -> dict[str, Any]:
        """Deterministic VERIFY step; preserves Owner Gates, executes nothing."""

        queue = self.integration_queue(current_canonical_base_sha, current_canonical_base_tree)
        entries = queue["ENTRIES"]
        results: list[dict[str, Any]] = []
        for entry in entries:
            status = entry["STATUS"]
            if status == "PLANNED":
                verify_status, reasons = "NOT_READY", ["NOT_IN_INTEGRATION_QUEUE"]
            elif status == "ACTIVE":
                verify_status, reasons = "NOT_READY", ["NOT_IN_INTEGRATION_QUEUE"]
            elif status == "STALE_BASE":
                verify_status, reasons = "STALE_BASE", ["CANONICAL_BASE_NOT_CURRENT"]
            elif status == "BLOCKED":
                verify_status, reasons = "BLOCKED", ["SESSION_BLOCKED"]
            elif status == "WAITING_OWNER_GATE":
                verify_status, reasons = "WAITING_OWNER_GATE", ["OWNER_GATE_PENDING"]
            else:  # QUEUED
                reasons = []
                if entry["BASE_RELATION"] != "CURRENT":
                    reasons.append("CANONICAL_BASE_NOT_CURRENT")
                for dependency in entry["DEPENDENCIES"]:
                    dep_result = next((r for r in results if r["WORK_ITEM_ID"] == dependency), None)
                    if dep_result is None or dep_result["VERIFY_STATUS"] != "VERIFIED":
                        reasons.append(f"DEPENDENCY_NOT_VERIFIED:{dependency}")
                verify_status = "NOT_READY" if reasons else "VERIFIED"
            next_gate = (
                "OWNER_REVIEW"
                if verify_status == "VERIFIED"
                else _STATUS_NEXT_GATE[status]
                if status in _STATUS_NEXT_GATE
                else "VERIFY"
            )
            results.append(
                {
                    "WORK_ITEM_ID": entry["WORK_ITEM_ID"],
                    "VERIFY_STATUS": verify_status,
                    "REASONS": reasons,
                    "NEXT_GATE": next_gate,
                    "CANDIDATE_SHA": entry["CANDIDATE_SHA"],
                    "CANDIDATE_TREE": entry["CANDIDATE_TREE"],
                    "PACKET_FINGERPRINT": entry["PACKET_FINGERPRINT"],
                }
            )
        verify_statuses = {r["VERIFY_STATUS"] for r in results}
        if not results:
            overall = "EMPTY"
        elif {"STALE_BASE", "BLOCKED"} & verify_statuses or queue["INTEGRATION_QUEUE_STATUS"] == "RECONCILIATION_REQUIRED":
            overall = "RECONCILIATION_REQUIRED"
        elif (
            verify_statuses <= {"VERIFIED", "WAITING_OWNER_GATE"}
            and verify_statuses & {"VERIFIED", "WAITING_OWNER_GATE"}
        ):
            overall = "READY_FOR_OWNER_REVIEW"
        else:
            overall = "IN_PROGRESS"
        return {
            "schema": WORK_ITEM_VERIFY_SCHEMA,
            "ENTRIES": results,
            "INTEGRATION_QUEUE_STATUS": overall,
            "OWNER_GATES": queue["OWNER_GATES"],
            "OWNER_GATES_PRESERVED": True,
            "OWNER_GATE_EXECUTED": False,
            "PROMOTED": False,
            "MERGED": False,
            "DEPLOYED": False,
            "RELEASED": False,
            "PROTECTED_ACTION_EXECUTED": False,
            "PACKET_IS_CANONICAL_TRUTH": "NO",
        }

    # ------------------------------------------------------------------
    # Derivations
    # ------------------------------------------------------------------

    @staticmethod
    def _return_outcome(relation: str, session_state: str, owner_gate: Any) -> tuple[str, str, str]:
        # The durable VERDICT is the queue outcome status; the raw session
        # state is preserved separately as RETURN_SESSION_STATE.
        if relation != "CURRENT":
            return "STALE_BASE", "STALE_BASE", "RECONCILIATION"
        if session_state in {"BLOCKED", "FAILED", "ABORTED"}:
            return "BLOCKED", "BLOCKED", "RECONCILIATION"
        if owner_gate is not None or session_state == "WAITING_OWNER_GATE":
            return "WAITING_OWNER_GATE", "WAITING_OWNER_GATE", "OWNER_GATE"
        return "QUEUED", "QUEUED", "VERIFY"

    @staticmethod
    def _derive_status(item: Mapping[str, Any], lane_started: bool, ret: Mapping[str, Any] | None) -> str:
        if ret is None:
            return "ACTIVE" if lane_started else "PLANNED"
        status = ret.get("VERDICT", UNKNOWN)
        if status in {"STALE_BASE", "WAITING_OWNER_GATE", "BLOCKED", "QUEUED"}:
            return status
        return "BLOCKED"

    @staticmethod
    def _queue_state(entries: Sequence[Mapping[str, Any]]) -> str:
        if not entries:
            return "EMPTY"
        statuses = [entry["STATUS"] for entry in entries]
        if any(status in {"STALE_BASE", "BLOCKED"} for status in statuses):
            return "RECONCILIATION_REQUIRED"
        if not any(status in {"QUEUED", "WAITING_OWNER_GATE"} for status in statuses):
            return "IN_PROGRESS"
        return "READY_FOR_OWNER_REVIEW"


def work_item_handoff(
    root: str | Path,
    *,
    current_canonical_base_sha: str = UNKNOWN,
    current_canonical_base_tree: str = UNKNOWN,
) -> WorkItemHandoff:
    return WorkItemHandoff(
        root,
        current_canonical_base_sha=current_canonical_base_sha,
        current_canonical_base_tree=current_canonical_base_tree,
    )


__all__ = [
    "BASE_RELATIONS",
    "CONTROL_TOWER_LEDGER_RELATIVE_PATH",
    "LANE_STARTED_EVENT_TYPE",
    "REGISTERED_EVENT_TYPE",
    "RETURN_EVENT_TYPE",
    "UNKNOWN",
    "WORK_ITEM_LANE_STARTED_EVENT_SCHEMA",
    "WORK_ITEM_NEXT_GATES",
    "WORK_ITEM_QUEUE_SCHEMA",
    "WORK_ITEM_QUEUE_STATES",
    "WORK_ITEM_REGISTERED_EVENT_SCHEMA",
    "WORK_ITEM_RETURN_EVENT_SCHEMA",
    "WORK_ITEM_SCHEMA",
    "WORK_ITEM_STATUSES",
    "WORK_ITEM_VERIFY_SCHEMA",
    "WorkItem",
    "WorkItemHandoff",
    "WorkItemHandoffError",
    "work_item_handoff",
]
