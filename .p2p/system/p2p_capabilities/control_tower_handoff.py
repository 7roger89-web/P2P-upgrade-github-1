"""Provider-neutral Control Tower session handoff contract.

This module is a small composition boundary over the existing P2P task,
evidence, execution-ledger, and host-executor surfaces. It does not launch a
host, select a provider, inherit chat state, write canonical truth, approve
protected actions, or transfer state between Control Tower instances. A
successor packet is compact bootstrap data that must be reconciled with
durable P2P evidence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Mapping, Sequence


CONTROL_TOWER_PACKET_SCHEMA = "p2p-control-tower-return-packet/1"
CONTROL_TOWER_PROMPT_SCHEMA = "p2p-control-tower-execution-prompt/1"
CONTROL_TOWER_EVENT_SCHEMA = "p2p-control-tower-return-event/1"
CONTROL_TOWER_SESSION_START_EVENT_SCHEMA = "p2p-control-tower-session-start/1"
CONTROL_TOWER_PROJECTION_SCHEMA = "p2p-control-tower-state-projection/2"
ATTACHMENT_MANIFEST_SCHEMA = "p2p-control-tower-attachment-manifest/1"
CONTROL_TOWER_SUCCESSOR_PACKET_SCHEMA = "p2p-control-tower-successor-packet/1"
CONTROL_TOWER_ROTATION_HANDOFF_SCHEMA = "p2p-control-tower-rotation-handoff/1"
SUPREME_LAW_DEVELOPMENT_PATH = "docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md"
SUPREME_LAW_INSTALLED_PATH = ".p2p/system/docs/P2P-OPERATIONS-NOTEBOOK.md"
SUPREME_LAW_CAPSULE = "\n".join(
    (
        "1. Preserve the Owner's outcome and authority; decide routine technical details inside approved scope.",
        "2. Take the simplest useful path to completion; do not build speculative infrastructure before a demonstrated need.",
        "3. Real state and scoped evidence override assumptions; reconcile UNKNOWN side effects before unsafe retry.",
        "4. Retry by process type and detect stuckness by lack of preserved progress, not a fixed failure count.",
        "5. Preserve only the durable checkpoint needed to continue and STOP when the required outcome is proven.",
    )
)
UNKNOWN = "UNKNOWN"

TERMINAL_STATES = (
    "COMPLETED",
    "READY",
    "WAITING_OWNER_GATE",
    "BLOCKED",
    "FAILED",
    "ABORTED",
)
CANONICAL_RELATIONS = ("CURRENT", "STALE", "UNKNOWN")
CONTROL_TOWER_STATUSES = (
    "IDLE",
    *TERMINAL_STATES,
    "RECONCILIATION_REQUIRED",
)

EXISTING_LIFECYCLE_STATE = {
    "COMPLETED": "DONE",
    "READY": "READY",
    "WAITING_OWNER_GATE": "WAITING_OWNER",
    "BLOCKED": "BLOCKED",
    "FAILED": "BLOCKED",
    "ABORTED": "CANCELLED",
}

USER_ACTION_BLOCK = (
    "USER_ACTION:\n"
    "Copy nguyên toàn bộ phản hồi cuối này vào:\n"
    "00 — P2P CONTROL TOWER\n"
    "\n"
    "Không cần viết thêm nội dung bàn giao."
)
PACKET_BEGIN = "CONTROL_TOWER_RETURN_PACKET_BEGIN"
PACKET_END = "CONTROL_TOWER_RETURN_PACKET_END"
UPLOAD_REQUIRED_VALUES = ("YES", "NO")
ATTACHMENT_CLASSIFICATIONS = ("REQUIRED", "OPTIONAL", "DO_NOT_UPLOAD")
NO_UPLOAD_INSTRUCTION = (
    "Chỉ cần copy toàn bộ final response về 00 — P2P CONTROL TOWER; không cần upload file."
)
UPLOAD_MANIFEST_INSTRUCTION = (
    "Upload only the listed REQUIRED attachments; OPTIONAL entries are not required, and "
    "DO_NOT_UPLOAD entries must not be uploaded."
)

_HOST_PATTERN = re.compile(r"^[A-Z][A-Z0-9_-]{1,63}$")
_CONTROL_TOWER_INSTANCE_PATTERN = re.compile(r"^CT[A-Z0-9_-]{1,63}$")
_CONFIDENCE_PATTERN = re.compile(r"^[A-Z][A-Z0-9_-]{0,31}$")
_HASH_PATTERN = re.compile(r"^(?:[0-9a-fA-F]{40}|[0-9a-fA-F]{64})$")
_PROMOTION_TERM_PATTERN = re.compile(
    r"(?:promot|release|deploy|publish|push|merge|live|production)",
    re.IGNORECASE,
)
_SECRET_KEY_PATTERN = re.compile(
    r"(?:secret|password|api[_-]?key|credential|token_value|"
    r"chain[_-]?of[_-]?thought|chat[_-]?history|conversation)",
    re.IGNORECASE,
)
_SECRET_VALUE_PATTERN = re.compile(
    r"(?:\bsk-[A-Za-z0-9]|\btoken\s*=|\bpassword\s*=|"
    r"\bBEGIN\s+(?:RSA|OPENSSH|PRIVATE))",
    re.IGNORECASE,
)
_INHERITANCE_KEYS = frozenset(
    {
        "chat_history",
        "conversation",
        "conversation_id",
        "previous_session",
        "previous_turn",
        "inherited_state",
        "implicit_context",
    }
)


class ControlTowerHandoffError(ValueError):
    """Raised when a Control Tower handoff violates a fail-closed boundary."""


class PacketParseError(ControlTowerHandoffError):
    """Raised when a marked executor response has no valid return packet."""


class BindingError(ControlTowerHandoffError):
    """Raised when a packet does not match its registered session binding."""


class ProjectionError(ControlTowerHandoffError):
    """Raised when the existing durable ledger cannot be projected safely."""


def _text(value: Any, field_name: str, *, max_length: int = 1024) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > max_length:
        raise ControlTowerHandoffError(f"{field_name}_INVALID")
    normalized = value.strip()
    if _SECRET_VALUE_PATTERN.search(normalized):
        raise ControlTowerHandoffError(f"{field_name}_SECRET_LIKE")
    return normalized


def _optional_text(value: Any, field_name: str, *, max_length: int = 1024) -> str:
    if value is None:
        return "UNKNOWN"
    return _text(value, field_name, max_length=max_length)


def _safe_json(value: Any, *, path: str = "value", depth: int = 0) -> Any:
    if depth > 8:
        raise ControlTowerHandoffError(f"{path}_TOO_DEEP")
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for raw_key, raw_child in value.items():
            key = _text(str(raw_key), f"{path}_KEY", max_length=128)
            if _SECRET_KEY_PATTERN.search(key):
                raise ControlTowerHandoffError(f"{path}.{key}_SECRET_FIELD")
            result[key] = _safe_json(raw_child, path=f"{path}.{key}", depth=depth + 1)
        return result
    if isinstance(value, (list, tuple)):
        if len(value) > 256:
            raise ControlTowerHandoffError(f"{path}_TOO_LARGE")
        return [_safe_json(item, path=f"{path}[{index}]", depth=depth + 1) for index, item in enumerate(value)]
    if isinstance(value, str):
        if len(value) > 8192 or _SECRET_VALUE_PATTERN.search(value):
            raise ControlTowerHandoffError(f"{path}_SECRET_OR_TOO_LARGE")
        return value
    if value is None or isinstance(value, (bool, int, float)):
        return value
    raise ControlTowerHandoffError(f"{path}_TYPE_INVALID")


def _reject_secret_keys(value: Any, *, path: str = "value", depth: int = 0) -> None:
    """Reject secret-bearing fields even when they are outside known fields."""

    if depth > 8:
        raise ControlTowerHandoffError(f"{path}_TOO_DEEP")
    if isinstance(value, Mapping):
        for raw_key, child in value.items():
            key = str(raw_key)
            if _SECRET_KEY_PATTERN.search(key):
                raise ControlTowerHandoffError(f"{path}.{key}_SECRET_FIELD")
            _reject_secret_keys(child, path=f"{path}.{key}", depth=depth + 1)
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            _reject_secret_keys(child, path=f"{path}[{index}]", depth=depth + 1)


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def new_session_id(host: str, goal_id: str, task_id: str = "UNKNOWN") -> str:
    """Derive a deterministic session ID without choosing a provider or host."""

    normalized_host = normalize_host(host)
    normalized_goal = _text(goal_id, "goal_id", max_length=256)
    normalized_task = _text(task_id, "task_id", max_length=256)
    slug = re.sub(r"[^a-z0-9]+", "-", normalized_goal.lower()).strip("-")[:48] or "goal"
    digest = hashlib.sha256(
        f"{normalized_host}\0{normalized_goal}\0{normalized_task}".encode("utf-8")
    ).hexdigest()[:12]
    return f"session-{normalized_host.lower()}-{slug}-{digest}"


def _refs(values: Sequence[Any] | None, field_name: str, *, max_length: int = 2048) -> tuple[str, ...]:
    if values is None:
        return ()
    if isinstance(values, (str, bytes)):
        raise ControlTowerHandoffError(f"{field_name}_MUST_BE_SEQUENCE")
    try:
        iterator = iter(values)
    except TypeError as exc:
        raise ControlTowerHandoffError(f"{field_name}_MUST_BE_SEQUENCE") from exc
    result: list[str] = []
    seen: set[str] = set()
    for raw in iterator:
        item = _text(raw, f"{field_name}_ITEM", max_length=max_length).replace("\\", "/")
        if item in seen:
            raise ControlTowerHandoffError(f"{field_name}_DUPLICATE:{item}")
        seen.add(item)
        result.append(item)
    return tuple(result)


def normalize_host(value: Any) -> str:
    """Normalize one explicit host label; never parse narrative prose."""

    raw = _text(value, "host", max_length=64)
    if any(character.isspace() for character in raw):
        raise ControlTowerHandoffError("HOST_LABEL_MUST_BE_ONE_TOKEN")
    normalized = raw.upper().replace("-", "_")
    if not _HOST_PATTERN.fullmatch(normalized):
        raise ControlTowerHandoffError("HOST_LABEL_INVALID")
    return normalized


def _state(value: Any) -> str:
    normalized = _text(value, "session_state", max_length=64).upper().replace("-", "_")
    aliases = {
        "DONE": "COMPLETED",
        "SUCCESS": "COMPLETED",
        "WAITING_OWNER": "WAITING_OWNER_GATE",
        "CANCELLED": "ABORTED",
        "CANCELED": "ABORTED",
    }
    normalized = aliases.get(normalized, normalized)
    if normalized not in TERMINAL_STATES:
        raise ControlTowerHandoffError("SESSION_STATE_INVALID")
    return normalized


def _relation(value: Any) -> str:
    normalized = _text(value, "canonical_relation", max_length=32).upper()
    if normalized not in CANONICAL_RELATIONS:
        raise ControlTowerHandoffError("CANONICAL_RELATION_INVALID")
    return normalized


def _hash_or_unknown(value: Any, field_name: str) -> str:
    normalized = _optional_text(value, field_name, max_length=128)
    if normalized.upper() in {"UNKNOWN", "NONE"}:
        return normalized.upper()
    if not _HASH_PATTERN.fullmatch(normalized):
        raise ControlTowerHandoffError(f"{field_name}_INVALID")
    return normalized.lower()


def _location(value: Any, field_name: str) -> str:
    normalized = _optional_text(value, field_name, max_length=2048)
    return normalized.replace("\\", "/")


def _upload_required(value: Any) -> str:
    normalized = _text(value, "upload_required", max_length=8).upper()
    if normalized not in UPLOAD_REQUIRED_VALUES:
        raise ControlTowerHandoffError("UPLOAD_REQUIRED_INVALID")
    return normalized


def _attachment_classification(value: Any) -> str:
    normalized = _text(value, "attachment_classification", max_length=32).upper().replace("-", "_")
    if normalized not in ATTACHMENT_CLASSIFICATIONS:
        raise ControlTowerHandoffError("ATTACHMENT_CLASSIFICATION_INVALID")
    return normalized


def _control_tower_instance_id(value: Any, field_name: str) -> str:
    normalized = _text(value, field_name, max_length=64).upper()
    if not _CONTROL_TOWER_INSTANCE_PATTERN.fullmatch(normalized):
        raise ControlTowerHandoffError(f"{field_name.upper()}_INVALID")
    return normalized


def _canonical_confidence(value: Any) -> str:
    if value is None:
        return "UNKNOWN"
    normalized = _text(value, "canonical_confidence", max_length=32).upper().replace("-", "_")
    if not _CONFIDENCE_PATTERN.fullmatch(normalized):
        raise ControlTowerHandoffError("CANONICAL_CONFIDENCE_INVALID")
    return normalized


def _positive_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ControlTowerHandoffError(f"{field_name}_INVALID")
    return value


def _safe_items(values: Sequence[Any] | None, field_name: str) -> tuple[Any, ...]:
    if values is None:
        return ()
    if isinstance(values, (str, bytes, Mapping)):
        raise ControlTowerHandoffError(f"{field_name}_MUST_BE_SEQUENCE")
    try:
        iterator = iter(values)
    except TypeError as exc:
        raise ControlTowerHandoffError(f"{field_name}_MUST_BE_SEQUENCE") from exc
    items: list[Any] = []
    for index, item in enumerate(iterator):
        if index >= 256:
            raise ControlTowerHandoffError(f"{field_name}_TOO_LARGE")
        items.append(_safe_json(item, path=f"{field_name}[{index}]"))
    return tuple(items)


def _canonical_claim(value: Any) -> Any:
    if value is None:
        return None
    return _safe_json(value, path="current_canonical_claim")


def _host_lanes(value: Mapping[str, Any] | None) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise ControlTowerHandoffError("HOST_LANES_MUST_BE_OBJECT")
    lanes: dict[str, Any] = {}
    for raw_host, raw_lane in value.items():
        host = normalize_host(raw_host)
        if host in lanes:
            raise ControlTowerHandoffError(f"HOST_LANE_DUPLICATE:{host}")
        lanes[host] = _safe_json(raw_lane, path=f"host_lanes.{host}")
    return lanes


def _active_execution(value: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise ControlTowerHandoffError("CONFIRMED_ACTIVE_EXECUTION_MUST_BE_OBJECT")
    result = _safe_json(value, path="confirmed_active_execution")
    if not isinstance(result, dict):
        raise ControlTowerHandoffError("CONFIRMED_ACTIVE_EXECUTION_MUST_BE_OBJECT")
    for field_name in ("SESSION_ID", "HOST", "GOAL_ID"):
        if field_name not in result:
            raise ControlTowerHandoffError(f"CONFIRMED_ACTIVE_EXECUTION_{field_name}_REQUIRED")
        _text(result[field_name], f"confirmed_active_execution_{field_name.lower()}", max_length=256)
    result["HOST"] = normalize_host(result["HOST"])
    return result


def _reject_inheritance(value: Any) -> None:
    if value is None:
        return
    if not isinstance(value, Mapping):
        raise ControlTowerHandoffError("IMPLICIT_INHERITANCE_FORBIDDEN")
    for raw_key in value:
        key = str(raw_key).lower()
        if key in _INHERITANCE_KEYS or "history" in key or "conversation" in key:
            raise ControlTowerHandoffError("IMPLICIT_INHERITANCE_FORBIDDEN")
    raise ControlTowerHandoffError("IMPLICIT_INHERITANCE_FORBIDDEN")


@dataclass(frozen=True)
class SessionBinding:
    """The minimum authoritative identity for one short-lived session."""

    session_id: str
    host: str
    goal_id: str
    goal: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "session_id", _text(self.session_id, "session_id", max_length=256))
        object.__setattr__(self, "host", normalize_host(self.host))
        object.__setattr__(self, "goal_id", _text(self.goal_id, "goal_id", max_length=256))
        object.__setattr__(self, "goal", _text(self.goal, "goal", max_length=8192))

    def to_dict(self) -> dict[str, str]:
        return {
            "SESSION_ID": self.session_id,
            "HOST": self.host,
            "GOAL_ID": self.goal_id,
            "GOAL": self.goal,
        }

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "SessionBinding":
        if not isinstance(value, Mapping):
            raise ControlTowerHandoffError("SESSION_BINDING_MUST_BE_OBJECT")
        return cls(
            session_id=value.get("SESSION_ID"),
            host=value.get("HOST"),
            goal_id=value.get("GOAL_ID"),
            goal=value.get("GOAL"),
        )


@dataclass(frozen=True)
class ControlTowerAttachment:
    """One explicit file entry; a path is not proof that its contents are readable."""

    filename: str
    local_path: str
    purpose: str
    why_control_tower_needs_contents: str
    classification: str = "REQUIRED"

    def __post_init__(self) -> None:
        filename = _text(self.filename, "attachment_filename", max_length=256)
        if "/" in filename or "\\" in filename:
            raise ControlTowerHandoffError("ATTACHMENT_FILENAME_MUST_BE_BASENAME")
        object.__setattr__(self, "filename", filename)
        object.__setattr__(self, "local_path", _location(self.local_path, "attachment_local_path"))
        object.__setattr__(
            self,
            "purpose",
            _text(self.purpose, "attachment_purpose", max_length=4096),
        )
        object.__setattr__(
            self,
            "why_control_tower_needs_contents",
            _text(
                self.why_control_tower_needs_contents,
                "attachment_why_contents",
                max_length=4096,
            ),
        )
        object.__setattr__(
            self,
            "classification",
            _attachment_classification(self.classification),
        )

    def to_dict(self) -> dict[str, str]:
        return {
            "FILENAME": self.filename,
            "LOCAL_PATH": self.local_path,
            "PURPOSE": self.purpose,
            "WHY_CONTROL_TOWER_NEEDS_CONTENTS": self.why_control_tower_needs_contents,
            "CLASSIFICATION": self.classification,
            "LOCAL_PATH_ALONE_PROVES_CONTENTS_AVAILABLE": "NO",
            "CONTENTS_AVAILABLE_TO_CONTROL_TOWER": "UNKNOWN",
            "ATTACHMENT_IS_CANONICAL_TRUTH": "NO",
        }

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ControlTowerAttachment":
        if not isinstance(value, Mapping):
            raise ControlTowerHandoffError("ATTACHMENT_ENTRY_MUST_BE_OBJECT")
        return cls(
            filename=value.get("FILENAME"),
            local_path=value.get("LOCAL_PATH"),
            purpose=value.get("PURPOSE"),
            why_control_tower_needs_contents=value.get("WHY_CONTROL_TOWER_NEEDS_CONTENTS"),
            classification=value.get("CLASSIFICATION", "REQUIRED"),
        )


@dataclass(frozen=True)
class ControlTowerAttachmentManifest:
    """Explicit upload instructions and evidence-only attachment semantics."""

    upload_required: str = "NO"
    attachments: tuple[ControlTowerAttachment, ...] = ()

    def __post_init__(self) -> None:
        upload_required = _upload_required(self.upload_required)
        raw_entries = self.attachments
        if raw_entries is None or isinstance(raw_entries, (str, bytes)):
            raise ControlTowerHandoffError("ATTACHMENTS_MUST_BE_SEQUENCE")
        try:
            iterator = iter(raw_entries)
        except TypeError as exc:
            raise ControlTowerHandoffError("ATTACHMENTS_MUST_BE_SEQUENCE") from exc
        entries: list[ControlTowerAttachment] = []
        seen_names: set[str] = set()
        seen_paths: set[str] = set()
        for raw_entry in iterator:
            entry = (
                raw_entry
                if isinstance(raw_entry, ControlTowerAttachment)
                else ControlTowerAttachment.from_mapping(raw_entry)
            )
            if entry.filename in seen_names:
                raise ControlTowerHandoffError(f"ATTACHMENT_FILENAME_DUPLICATE:{entry.filename}")
            if entry.local_path in seen_paths:
                raise ControlTowerHandoffError(f"ATTACHMENT_PATH_DUPLICATE:{entry.local_path}")
            seen_names.add(entry.filename)
            seen_paths.add(entry.local_path)
            entries.append(entry)
        if upload_required == "NO" and entries:
            raise ControlTowerHandoffError("ATTACHMENTS_FORBIDDEN_WHEN_UPLOAD_NOT_REQUIRED")
        if upload_required == "YES":
            if not 1 <= len(entries) <= 3:
                raise ControlTowerHandoffError("UPLOAD_REQUIRED_NEEDS_ONE_TO_THREE_ATTACHMENTS")
            if not any(entry.classification == "REQUIRED" for entry in entries):
                raise ControlTowerHandoffError("UPLOAD_REQUIRED_NEEDS_REQUIRED_ATTACHMENT")
        object.__setattr__(self, "upload_required", upload_required)
        object.__setattr__(self, "attachments", tuple(entries))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": ATTACHMENT_MANIFEST_SCHEMA,
            "UPLOAD_REQUIRED": self.upload_required,
            "ATTACHMENTS": [entry.to_dict() for entry in self.attachments],
            "LOCAL_PATH_ALONE_PROVES_CONTENTS_AVAILABLE": "NO",
            "ATTACHMENTS_ARE_EVIDENCE_INPUT_ONLY": "YES",
            "ATTACHMENTS_ARE_CANONICAL_TRUTH": "NO",
            "ATTACHMENTS_PROVE_PROMOTION_DEPLOYMENT_LIVE_OR_OWNER_APPROVAL": "NO",
            "USER_INSTRUCTION": (
                NO_UPLOAD_INSTRUCTION
                if self.upload_required == "NO"
                else UPLOAD_MANIFEST_INSTRUCTION
            ),
        }

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ControlTowerAttachmentManifest":
        if not isinstance(value, Mapping) or value.get("schema") != ATTACHMENT_MANIFEST_SCHEMA:
            raise ControlTowerHandoffError("ATTACHMENT_MANIFEST_SCHEMA_INVALID")
        raw_entries = value.get("ATTACHMENTS") or ()
        if isinstance(raw_entries, (str, bytes)):
            raise ControlTowerHandoffError("ATTACHMENTS_MUST_BE_SEQUENCE")
        return cls(
            upload_required=value.get("UPLOAD_REQUIRED"),
            attachments=tuple(ControlTowerAttachment.from_mapping(item) for item in raw_entries),
        )


@dataclass(frozen=True)
class ControlTowerSuccessorPacket:
    """Compact CT001 -> CT002 bootstrap data, never canonical truth."""

    current_control_tower_instance_id: str
    proposed_successor_control_tower_instance_id: str
    latest_control_tower_snapshot_sequence: int
    current_canonical_claim: Any = None
    current_canonical_confidence: str = "UNKNOWN"
    host_lanes: Mapping[str, Any] = field(default_factory=dict)
    confirmed_active_execution: Mapping[str, Any] | None = None
    owner_gates: Sequence[Any] = field(default_factory=tuple)
    pending_work: Sequence[Any] = field(default_factory=tuple)
    recently_closed_material_work: Sequence[Any] = field(default_factory=tuple)
    blockers_and_risks: Sequence[Any] = field(default_factory=tuple)
    critical_invariants: Sequence[Any] = field(default_factory=tuple)
    next_safe_action: str = (
        "Reconcile this successor packet against durable P2P evidence before continuing."
    )
    durable_evidence_checkpoint_refs: Sequence[Any] = field(default_factory=tuple)
    unresolved_chat_only_not_canonical: Sequence[Any] = field(default_factory=tuple)
    attachment_manifest: ControlTowerAttachmentManifest = field(
        default_factory=ControlTowerAttachmentManifest
    )

    def __post_init__(self) -> None:
        current_id = _control_tower_instance_id(
            self.current_control_tower_instance_id,
            "current_control_tower_instance_id",
        )
        successor_id = _control_tower_instance_id(
            self.proposed_successor_control_tower_instance_id,
            "proposed_successor_control_tower_instance_id",
        )
        if current_id == successor_id:
            raise ControlTowerHandoffError("SUCCESSOR_CONTROL_TOWER_INSTANCE_MUST_DIFFER")
        object.__setattr__(self, "current_control_tower_instance_id", current_id)
        object.__setattr__(self, "proposed_successor_control_tower_instance_id", successor_id)
        object.__setattr__(
            self,
            "latest_control_tower_snapshot_sequence",
            _positive_int(
                self.latest_control_tower_snapshot_sequence,
                "latest_control_tower_snapshot_sequence",
            ),
        )
        claim = _canonical_claim(self.current_canonical_claim)
        object.__setattr__(self, "current_canonical_claim", claim)
        confidence = _canonical_confidence(self.current_canonical_confidence)
        if claim is None:
            confidence = "UNKNOWN"
        object.__setattr__(self, "current_canonical_confidence", confidence)
        object.__setattr__(self, "host_lanes", _host_lanes(self.host_lanes))
        object.__setattr__(
            self,
            "confirmed_active_execution",
            _active_execution(self.confirmed_active_execution),
        )
        for field_name in (
            "owner_gates",
            "pending_work",
            "recently_closed_material_work",
            "blockers_and_risks",
            "critical_invariants",
        ):
            object.__setattr__(self, field_name, _safe_items(getattr(self, field_name), field_name))
        object.__setattr__(
            self,
            "next_safe_action",
            _text(self.next_safe_action, "next_safe_action", max_length=4096),
        )
        object.__setattr__(
            self,
            "durable_evidence_checkpoint_refs",
            _refs(self.durable_evidence_checkpoint_refs, "durable_evidence_checkpoint_refs"),
        )
        object.__setattr__(
            self,
            "unresolved_chat_only_not_canonical",
            _refs(
                self.unresolved_chat_only_not_canonical,
                "unresolved_chat_only_not_canonical",
            ),
        )
        manifest = self.attachment_manifest
        if manifest is None:
            manifest = ControlTowerAttachmentManifest()
        elif isinstance(manifest, Mapping):
            manifest = ControlTowerAttachmentManifest.from_mapping(manifest)
        elif not isinstance(manifest, ControlTowerAttachmentManifest):
            raise ControlTowerHandoffError("ATTACHMENT_MANIFEST_REQUIRED")
        object.__setattr__(self, "attachment_manifest", manifest)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": CONTROL_TOWER_SUCCESSOR_PACKET_SCHEMA,
            "P2P_CONTROL_TOWER_SUCCESSOR_PACKET": True,
            "CONTROL_TOWER_SUCCESSOR_PACKET": True,
            "CURRENT_CONTROL_TOWER_INSTANCE_ID": self.current_control_tower_instance_id,
            "PROPOSED_SUCCESSOR_CONTROL_TOWER_INSTANCE_ID": self.proposed_successor_control_tower_instance_id,
            "LATEST_CONTROL_TOWER_SNAPSHOT_SEQUENCE": self.latest_control_tower_snapshot_sequence,
            "CURRENT_CANONICAL_CLAIM": _safe_json(
                self.current_canonical_claim,
                path="current_canonical_claim",
            ),
            "CURRENT_CANONICAL_CONFIDENCE": self.current_canonical_confidence,
            "HOST_LANES": _safe_json(self.host_lanes, path="host_lanes"),
            "CONFIRMED_ACTIVE_EXECUTION": _safe_json(
                self.confirmed_active_execution,
                path="confirmed_active_execution",
            ),
            "OWNER_GATES": _safe_json(self.owner_gates, path="owner_gates"),
            "PENDING_WORK": _safe_json(self.pending_work, path="pending_work"),
            "RECENTLY_CLOSED_MATERIAL_WORK": _safe_json(
                self.recently_closed_material_work,
                path="recently_closed_material_work",
            ),
            "BLOCKERS_AND_RISKS": _safe_json(self.blockers_and_risks, path="blockers_and_risks"),
            "CRITICAL_INVARIANTS": _safe_json(self.critical_invariants, path="critical_invariants"),
            "NEXT_SAFE_ACTION": self.next_safe_action,
            "DURABLE_EVIDENCE_CHECKPOINT_REFS": list(self.durable_evidence_checkpoint_refs),
            "UNRESOLVED_CHAT_ONLY_NOT_CANONICAL": list(self.unresolved_chat_only_not_canonical),
            "CHAT_ONLY_NOT_CANONICAL": list(self.unresolved_chat_only_not_canonical),
            "CONTROL_TOWER_LIFECYCLE_LAYERS": {
                "EXECUTION_SESSION": "SHORT_LIVED_BOUNDED",
                "CONTROL_TOWER_INSTANCE": "ROTATABLE",
                "P2P_REPOSITORY_EVIDENCE_GOVERNANCE": "LONG_LIVED_SOURCE_OF_TRUTH",
            },
            "FULL_CHAT_HISTORY_INCLUDED": "NO",
            "UPLOAD_REQUIRED": self.attachment_manifest.upload_required,
            "CONTROL_TOWER_ATTACHMENT_MANIFEST": self.attachment_manifest.to_dict(),
            "SUCCESSOR_PACKET_IS_CANONICAL_TRUTH": "NO",
            "PACKET_IS_CANONICAL_TRUTH": "NO",
            "PROMOTION_EXECUTED": "NO",
            "DEPLOYMENT_EXECUTED": "NO",
            "LIVE_ACTION_EXECUTED": "NO",
            "OWNER_APPROVAL_INHERITED": "NO",
        }

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ControlTowerSuccessorPacket":
        if not isinstance(value, Mapping) or value.get("schema") != CONTROL_TOWER_SUCCESSOR_PACKET_SCHEMA:
            raise ControlTowerHandoffError("CONTROL_TOWER_SUCCESSOR_PACKET_SCHEMA_INVALID")
        if value.get("P2P_CONTROL_TOWER_SUCCESSOR_PACKET") is not True:
            raise ControlTowerHandoffError("CONTROL_TOWER_SUCCESSOR_PACKET_MARKER_INVALID")
        raw_manifest = value.get("CONTROL_TOWER_ATTACHMENT_MANIFEST")
        if raw_manifest is None:
            manifest = ControlTowerAttachmentManifest(
                upload_required=value.get("UPLOAD_REQUIRED", "NO")
            )
        else:
            manifest = ControlTowerAttachmentManifest.from_mapping(raw_manifest)
            if "UPLOAD_REQUIRED" in value and value.get("UPLOAD_REQUIRED") != manifest.upload_required:
                raise ControlTowerHandoffError("UPLOAD_REQUIRED_MANIFEST_MISMATCH")
        return cls(
            current_control_tower_instance_id=value.get("CURRENT_CONTROL_TOWER_INSTANCE_ID"),
            proposed_successor_control_tower_instance_id=value.get(
                "PROPOSED_SUCCESSOR_CONTROL_TOWER_INSTANCE_ID"
            ),
            latest_control_tower_snapshot_sequence=value.get(
                "LATEST_CONTROL_TOWER_SNAPSHOT_SEQUENCE"
            ),
            current_canonical_claim=value.get("CURRENT_CANONICAL_CLAIM"),
            current_canonical_confidence=value.get("CURRENT_CANONICAL_CONFIDENCE", "UNKNOWN"),
            host_lanes=value.get("HOST_LANES") or {},
            confirmed_active_execution=value.get("CONFIRMED_ACTIVE_EXECUTION"),
            owner_gates=tuple(value.get("OWNER_GATES") or ()),
            pending_work=tuple(value.get("PENDING_WORK") or ()),
            recently_closed_material_work=tuple(value.get("RECENTLY_CLOSED_MATERIAL_WORK") or ()),
            blockers_and_risks=tuple(value.get("BLOCKERS_AND_RISKS") or ()),
            critical_invariants=tuple(value.get("CRITICAL_INVARIANTS") or ()),
            next_safe_action=value.get(
                "NEXT_SAFE_ACTION",
                "Reconcile this successor packet against durable P2P evidence before continuing.",
            ),
            durable_evidence_checkpoint_refs=tuple(
                value.get("DURABLE_EVIDENCE_CHECKPOINT_REFS") or ()
            ),
            unresolved_chat_only_not_canonical=tuple(
                value.get("UNRESOLVED_CHAT_ONLY_NOT_CANONICAL")
                or value.get("CHAT_ONLY_NOT_CANONICAL")
                or ()
            ),
            attachment_manifest=manifest,
        )


@dataclass(frozen=True)
class ControlTowerRotationHandoff:
    """Beginner-facing rotation wrapper around one successor packet."""

    successor_packet: ControlTowerSuccessorPacket
    old_chat_archive_name: str
    new_chat_name: str
    user_action: str

    def __post_init__(self) -> None:
        if not isinstance(self.successor_packet, ControlTowerSuccessorPacket):
            raise ControlTowerHandoffError("SUCCESSOR_PACKET_REQUIRED")
        object.__setattr__(
            self,
            "old_chat_archive_name",
            _text(self.old_chat_archive_name, "old_chat_archive_name", max_length=256),
        )
        object.__setattr__(
            self,
            "new_chat_name",
            _text(self.new_chat_name, "new_chat_name", max_length=256),
        )
        object.__setattr__(
            self,
            "user_action",
            _text(self.user_action, "rotation_user_action", max_length=8192),
        )

    def to_dict(self) -> dict[str, Any]:
        packet = self.successor_packet.to_dict()
        return {
            "schema": CONTROL_TOWER_ROTATION_HANDOFF_SCHEMA,
            "CONTROL_TOWER_ROTATION_HANDOFF": True,
            "P2P_CONTROL_TOWER_SUCCESSOR_PACKET": packet,
            "CURRENT_CONTROL_TOWER_ARCHIVE_NAME": self.old_chat_archive_name,
            "OLD_CHAT_ARCHIVE_NAME": self.old_chat_archive_name,
            "SUCCESSOR_CONTROL_TOWER_CHAT_NAME": self.new_chat_name,
            "NEW_CHAT_NAME": self.new_chat_name,
            "ROTATION_USER_ACTION": self.user_action,
            "UPLOAD_REQUIRED": self.successor_packet.attachment_manifest.upload_required,
            "CONTROL_TOWER_ATTACHMENT_MANIFEST": self.successor_packet.attachment_manifest.to_dict(),
            "SUCCESSOR_PACKET_IS_CANONICAL_TRUTH": "NO",
            "FULL_CHAT_HISTORY_INCLUDED": "NO",
            "OWNER_APPROVAL_INHERITED": "NO",
            "PROMOTION_EXECUTED": "NO",
            "DEPLOYMENT_EXECUTED": "NO",
            "LIVE_ACTION_EXECUTED": "NO",
        }

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ControlTowerRotationHandoff":
        if not isinstance(value, Mapping) or value.get("schema") != CONTROL_TOWER_ROTATION_HANDOFF_SCHEMA:
            raise ControlTowerHandoffError("CONTROL_TOWER_ROTATION_HANDOFF_SCHEMA_INVALID")
        if value.get("CONTROL_TOWER_ROTATION_HANDOFF") is not True:
            raise ControlTowerHandoffError("CONTROL_TOWER_ROTATION_HANDOFF_MARKER_INVALID")
        raw_packet = value.get("P2P_CONTROL_TOWER_SUCCESSOR_PACKET")
        packet = ControlTowerSuccessorPacket.from_mapping(raw_packet)
        if "UPLOAD_REQUIRED" in value and value.get("UPLOAD_REQUIRED") != packet.attachment_manifest.upload_required:
            raise ControlTowerHandoffError("UPLOAD_REQUIRED_MANIFEST_MISMATCH")
        return cls(
            successor_packet=packet,
            old_chat_archive_name=value.get(
                "CURRENT_CONTROL_TOWER_ARCHIVE_NAME",
                value.get("OLD_CHAT_ARCHIVE_NAME"),
            ),
            new_chat_name=value.get(
                "SUCCESSOR_CONTROL_TOWER_CHAT_NAME",
                value.get("NEW_CHAT_NAME"),
            ),
            user_action=value.get("ROTATION_USER_ACTION"),
        )


@dataclass(frozen=True)
class ControlTowerSuccessorReconciliation:
    """Read-only reconciliation result for a proposed successor packet."""

    current_control_tower_instance_id: str
    successor_control_tower_instance_id: str
    canonical_claim_relation: str
    snapshot_sequence_relation: str
    control_tower_status: str
    host_lanes: Mapping[str, Any]
    confirmed_active_execution: Mapping[str, Any] | None
    owner_gates: tuple[Any, ...]
    pending_work: tuple[Any, ...]
    recently_closed_material_work: tuple[Any, ...]
    blockers_and_risks: tuple[Any, ...]
    critical_invariants: tuple[Any, ...]
    unresolved_chat_only_not_canonical: tuple[str, ...]
    blockers: tuple[str, ...]
    next_safe_action: str
    promoted: bool = False
    owner_gate_executed: bool = False
    active_execution_closed: bool = False
    active_execution_invented: bool = False
    host_lane_reassigned: bool = False
    owner_approval_inherited: bool = False
    packet_is_canonical_truth: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "p2p-control-tower-successor-reconciliation/1",
            "P2P_CONTROL_TOWER_SUCCESSOR_RECONCILIATION": True,
            "CURRENT_CONTROL_TOWER_INSTANCE_ID": self.current_control_tower_instance_id,
            "SUCCESSOR_CONTROL_TOWER_INSTANCE_ID": self.successor_control_tower_instance_id,
            "CANONICAL_CLAIM_RELATION": self.canonical_claim_relation,
            "SNAPSHOT_SEQUENCE_RELATION": self.snapshot_sequence_relation,
            "CONTROL_TOWER_STATUS": self.control_tower_status,
            "HOST_LANES": _safe_json(self.host_lanes, path="host_lanes"),
            "CONFIRMED_ACTIVE_EXECUTION": _safe_json(
                self.confirmed_active_execution,
                path="confirmed_active_execution",
            ),
            "OWNER_GATES": _safe_json(self.owner_gates, path="owner_gates"),
            "PENDING_WORK": _safe_json(self.pending_work, path="pending_work"),
            "RECENTLY_CLOSED_MATERIAL_WORK": _safe_json(
                self.recently_closed_material_work,
                path="recently_closed_material_work",
            ),
            "BLOCKERS_AND_RISKS": _safe_json(self.blockers_and_risks, path="blockers_and_risks"),
            "CRITICAL_INVARIANTS": _safe_json(self.critical_invariants, path="critical_invariants"),
            "UNRESOLVED_CHAT_ONLY_NOT_CANONICAL": list(self.unresolved_chat_only_not_canonical),
            "BLOCKERS": list(self.blockers),
            "NEXT_SAFE_ACTION": self.next_safe_action,
            "PROMOTED": self.promoted,
            "OWNER_GATE_EXECUTED": "YES" if self.owner_gate_executed else "NO",
            "ACTIVE_EXECUTION_CLOSED": "YES" if self.active_execution_closed else "NO",
            "ACTIVE_EXECUTION_INVENTED": "YES" if self.active_execution_invented else "NO",
            "HOST_LANE_REASSIGNED": "YES" if self.host_lane_reassigned else "NO",
            "OWNER_APPROVAL_INHERITED": "YES" if self.owner_approval_inherited else "NO",
            "SUCCESSOR_PACKET_IS_CANONICAL_TRUTH": "YES" if self.packet_is_canonical_truth else "NO",
            "PACKET_IS_CANONICAL_TRUTH": "YES" if self.packet_is_canonical_truth else "NO",
        }


def bind_session(
    *,
    session_id: str,
    host: str,
    goal_id: str,
    goal: str,
    inherited_state: Any = None,
) -> SessionBinding:
    """Create a session only from explicit authority; inherited state is forbidden."""

    if inherited_state is not None:
        _reject_inheritance(inherited_state)
    return SessionBinding(session_id=session_id, host=host, goal_id=goal_id, goal=goal)


@dataclass(frozen=True)
class ControlTowerReturnPacket:
    """A structured return proposal. It is never canonical truth."""

    binding: SessionBinding
    session_state: str
    canonical_base_sha: str = "UNKNOWN"
    canonical_base_tree: str = "UNKNOWN"
    canonical_relation: str = "UNKNOWN"
    worktree: str = "UNKNOWN"
    branch: str = "UNKNOWN"
    changes: Any = field(default_factory=list)
    test_results: Mapping[str, Any] = field(default_factory=dict)
    evidence: tuple[str, ...] = ()
    candidate_or_checkpoint_sha: str = "UNKNOWN"
    terminal_verdict: str | None = None
    owner_gate: Mapping[str, Any] | None = None
    blockers: tuple[str, ...] = ()
    next_recommended_action: str = "Return this packet to the Control Tower for reconciliation."
    attachment_manifest: ControlTowerAttachmentManifest = field(
        default_factory=ControlTowerAttachmentManifest
    )

    def __post_init__(self) -> None:
        if not isinstance(self.binding, SessionBinding):
            raise ControlTowerHandoffError("SESSION_BINDING_REQUIRED")
        normalized_state = _state(self.session_state)
        object.__setattr__(self, "session_state", normalized_state)
        object.__setattr__(self, "canonical_base_sha", _hash_or_unknown(self.canonical_base_sha, "canonical_base_sha"))
        object.__setattr__(self, "canonical_base_tree", _hash_or_unknown(self.canonical_base_tree, "canonical_base_tree"))
        object.__setattr__(self, "canonical_relation", _relation(self.canonical_relation))
        object.__setattr__(self, "worktree", _location(self.worktree, "worktree"))
        object.__setattr__(self, "branch", _location(self.branch, "branch"))
        object.__setattr__(self, "changes", _safe_json(self.changes, path="changes"))
        if not isinstance(self.test_results, Mapping):
            raise ControlTowerHandoffError("TEST_RESULTS_MUST_BE_OBJECT")
        object.__setattr__(self, "test_results", _safe_json(self.test_results, path="test_results"))
        object.__setattr__(self, "evidence", _refs(self.evidence, "evidence"))
        object.__setattr__(
            self,
            "candidate_or_checkpoint_sha",
            _hash_or_unknown(self.candidate_or_checkpoint_sha, "candidate_or_checkpoint_sha"),
        )
        verdict = normalized_state if self.terminal_verdict is None else _state(self.terminal_verdict)
        if verdict != normalized_state:
            raise ControlTowerHandoffError("TERMINAL_VERDICT_MUST_MATCH_SESSION_STATE")
        object.__setattr__(self, "terminal_verdict", verdict)
        if self.owner_gate is not None:
            if not isinstance(self.owner_gate, Mapping):
                raise ControlTowerHandoffError("OWNER_GATE_MUST_BE_OBJECT")
            object.__setattr__(self, "owner_gate", _safe_json(self.owner_gate, path="owner_gate"))
        if normalized_state == "WAITING_OWNER_GATE" and not self.owner_gate:
            raise ControlTowerHandoffError("OWNER_GATE_REQUIRED")
        object.__setattr__(self, "blockers", _refs(self.blockers, "blockers"))
        object.__setattr__(
            self,
            "next_recommended_action",
            _text(self.next_recommended_action, "next_recommended_action", max_length=4096),
        )
        manifest = self.attachment_manifest
        if manifest is None:
            manifest = ControlTowerAttachmentManifest()
        elif isinstance(manifest, Mapping):
            manifest = ControlTowerAttachmentManifest.from_mapping(manifest)
        elif not isinstance(manifest, ControlTowerAttachmentManifest):
            raise ControlTowerHandoffError("ATTACHMENT_MANIFEST_REQUIRED")
        object.__setattr__(self, "attachment_manifest", manifest)

    @property
    def mapped_lifecycle_state(self) -> str:
        return EXISTING_LIFECYCLE_STATE[self.session_state]

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "schema": CONTROL_TOWER_PACKET_SCHEMA,
            "CONTROL_TOWER_RETURN_PACKET": True,
            **self.binding.to_dict(),
            "SESSION_STATE": self.session_state,
            "MAPPED_LIFECYCLE_STATE": self.mapped_lifecycle_state,
            "CANONICAL_BASE_SHA": self.canonical_base_sha,
            "CANONICAL_BASE_TREE": self.canonical_base_tree,
            "CANONICAL_RELATION": self.canonical_relation,
            "WORKTREE": self.worktree,
            "BRANCH": self.branch,
            "CHANGES": _safe_json(self.changes, path="changes"),
            "TEST_RESULTS": _safe_json(self.test_results, path="test_results"),
            "EVIDENCE": list(self.evidence),
            "CANDIDATE_OR_CHECKPOINT_SHA": self.candidate_or_checkpoint_sha,
            "CANDIDATE_OR_CHECKPOINT": self.candidate_or_checkpoint_sha,
            "TERMINAL_VERDICT": self.terminal_verdict,
            "OWNER_GATE": _safe_json(self.owner_gate, path="owner_gate") if self.owner_gate is not None else None,
            "BLOCKERS": list(self.blockers),
            "NEXT_RECOMMENDED_ACTION": self.next_recommended_action,
            "UPLOAD_REQUIRED": self.attachment_manifest.upload_required,
            "CONTROL_TOWER_ATTACHMENT_MANIFEST": self.attachment_manifest.to_dict(),
            "PACKET_IS_CANONICAL_TRUTH": "NO",
            "CANONICAL_TRUTH": "NO",
        }
        return result

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ControlTowerReturnPacket":
        if not isinstance(value, Mapping) or value.get("schema") != CONTROL_TOWER_PACKET_SCHEMA:
            raise ControlTowerHandoffError("CONTROL_TOWER_PACKET_SCHEMA_INVALID")
        _reject_secret_keys(value)
        if value.get("CONTROL_TOWER_RETURN_PACKET") is not True:
            raise ControlTowerHandoffError("CONTROL_TOWER_PACKET_MARKER_INVALID")
        raw_manifest = value.get("CONTROL_TOWER_ATTACHMENT_MANIFEST")
        if raw_manifest is None:
            manifest = ControlTowerAttachmentManifest(
                upload_required=value.get("UPLOAD_REQUIRED", "NO")
            )
        else:
            manifest = ControlTowerAttachmentManifest.from_mapping(raw_manifest)
            if "UPLOAD_REQUIRED" in value and value.get("UPLOAD_REQUIRED") != manifest.upload_required:
                raise ControlTowerHandoffError("UPLOAD_REQUIRED_MANIFEST_MISMATCH")
        return cls(
            binding=SessionBinding.from_mapping(value),
            session_state=value.get("SESSION_STATE"),
            canonical_base_sha=value.get("CANONICAL_BASE_SHA", "UNKNOWN"),
            canonical_base_tree=value.get("CANONICAL_BASE_TREE", "UNKNOWN"),
            canonical_relation=value.get("CANONICAL_RELATION", "UNKNOWN"),
            worktree=value.get("WORKTREE", "UNKNOWN"),
            branch=value.get("BRANCH", "UNKNOWN"),
            changes=value.get("CHANGES", []),
            test_results=value.get("TEST_RESULTS", {}),
            evidence=tuple(value.get("EVIDENCE") or ()),
            candidate_or_checkpoint_sha=value.get(
                "CANDIDATE_OR_CHECKPOINT_SHA",
                value.get("CANDIDATE_OR_CHECKPOINT", "UNKNOWN"),
            ),
            terminal_verdict=value.get("TERMINAL_VERDICT"),
            owner_gate=value.get("OWNER_GATE"),
            blockers=tuple(value.get("BLOCKERS") or ()),
            next_recommended_action=value.get(
                "NEXT_RECOMMENDED_ACTION",
                "Return this packet to the Control Tower for reconciliation.",
            ),
            attachment_manifest=manifest,
        )

    def fingerprint(self) -> str:
        """Return a deterministic content fingerprint for replay protection."""

        encoded = json.dumps(
            self.to_dict(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def to_marked_text(self) -> str:
        payload = json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, indent=2)
        return f"{PACKET_BEGIN}\n{payload}\n{PACKET_END}"


def parse_return_packet(final_response: str) -> ControlTowerReturnPacket:
    """Extract exactly one structured packet from a complete final response."""

    if not isinstance(final_response, str):
        raise ControlTowerHandoffError("FINAL_RESPONSE_MUST_BE_TEXT")
    if len(final_response) > 500_000:
        raise ControlTowerHandoffError("FINAL_RESPONSE_TOO_LARGE")
    if final_response.count(PACKET_BEGIN) != 1 or final_response.count(PACKET_END) != 1:
        raise ControlTowerHandoffError("RETURN_PACKET_MARKERS_MUST_BE_UNIQUE")
    start = final_response.index(PACKET_BEGIN) + len(PACKET_BEGIN)
    end = final_response.index(PACKET_END)
    if end <= start:
        raise ControlTowerHandoffError("RETURN_PACKET_MARKERS_OUT_OF_ORDER")
    try:
        payload = json.loads(final_response[start:end].strip())
    except json.JSONDecodeError as exc:
        raise ControlTowerHandoffError(f"RETURN_PACKET_JSON_INVALID:{exc.msg}") from exc
    if not isinstance(payload, Mapping):
        raise ControlTowerHandoffError("RETURN_PACKET_MUST_BE_OBJECT")
    try:
        packet = ControlTowerReturnPacket.from_mapping(payload)
    except ControlTowerHandoffError:
        raise
    supplied_fingerprint = payload.get("PACKET_FINGERPRINT")
    if supplied_fingerprint not in (None, "UNKNOWN"):
        supplied = _hash_or_unknown(supplied_fingerprint, "packet_fingerprint")
        if supplied != packet.fingerprint():
            raise ControlTowerHandoffError("PACKET_FINGERPRINT_MISMATCH")
    return packet


def create_return_packet(binding: SessionBinding, **values: Any) -> ControlTowerReturnPacket:
    """Construct a packet while keeping the binding explicit at the call site."""

    return ControlTowerReturnPacket(binding=binding, **values)


def prepare_control_tower_rotation(
    *,
    current_control_tower_instance_id: str,
    proposed_successor_control_tower_instance_id: str,
    latest_control_tower_snapshot_sequence: int,
    current_canonical_claim: Any = None,
    current_canonical_confidence: str = "UNKNOWN",
    host_lanes: Mapping[str, Any] | None = None,
    confirmed_active_execution: Mapping[str, Any] | None = None,
    owner_gates: Sequence[Any] = (),
    pending_work: Sequence[Any] = (),
    recently_closed_material_work: Sequence[Any] = (),
    blockers_and_risks: Sequence[Any] = (),
    critical_invariants: Sequence[Any] = (),
    next_safe_action: str = (
        "Reconcile this successor packet against durable P2P evidence before continuing."
    ),
    durable_evidence_checkpoint_refs: Sequence[Any] = (),
    unresolved_chat_only_not_canonical: Sequence[Any] = (),
    attachment_manifest: ControlTowerAttachmentManifest | Mapping[str, Any] | None = None,
) -> ControlTowerRotationHandoff:
    """Emit the compact beginner-facing packet for one Control Tower rotation."""

    packet = ControlTowerSuccessorPacket(
        current_control_tower_instance_id=current_control_tower_instance_id,
        proposed_successor_control_tower_instance_id=proposed_successor_control_tower_instance_id,
        latest_control_tower_snapshot_sequence=latest_control_tower_snapshot_sequence,
        current_canonical_claim=current_canonical_claim,
        current_canonical_confidence=current_canonical_confidence,
        host_lanes=host_lanes or {},
        confirmed_active_execution=confirmed_active_execution,
        owner_gates=owner_gates,
        pending_work=pending_work,
        recently_closed_material_work=recently_closed_material_work,
        blockers_and_risks=blockers_and_risks,
        critical_invariants=critical_invariants,
        next_safe_action=next_safe_action,
        durable_evidence_checkpoint_refs=durable_evidence_checkpoint_refs,
        unresolved_chat_only_not_canonical=unresolved_chat_only_not_canonical,
        attachment_manifest=attachment_manifest,
    )
    old_name = f"90 — P2P CONTROL TOWER — {packet.current_control_tower_instance_id} — ARCHIVE"
    new_name = f"00 — P2P CONTROL TOWER — {packet.proposed_successor_control_tower_instance_id}"
    user_action = "\n".join(
        (
            "ROTATION_USER_ACTION:",
            f"1. Rename the current Control Tower chat to: {old_name}",
            f"2. Create a new chat named: {new_name}",
            "3. Paste the complete P2P_CONTROL_TOWER_SUCCESSOR_PACKET below.",
            "4. Upload only explicitly listed REQUIRED attachments when UPLOAD_REQUIRED=YES.",
            "5. Ask the successor to reconcile material claims with durable P2P evidence before continuing.",
            "Do not manually summarize the old chat. The successor packet is bootstrap data, not canonical truth.",
        )
    )
    return ControlTowerRotationHandoff(
        successor_packet=packet,
        old_chat_archive_name=old_name,
        new_chat_name=new_name,
        user_action=user_action,
    )


def _compare_successor_claims(
    packet: ControlTowerSuccessorPacket,
    current_canonical_claim: Any,
    current_canonical_confidence: Any,
) -> str:
    current_claim = _canonical_claim(current_canonical_claim)
    current_confidence = _canonical_confidence(current_canonical_confidence)
    if (
        packet.current_canonical_claim is None
        or current_claim is None
        or packet.current_canonical_confidence == "UNKNOWN"
        or current_confidence == "UNKNOWN"
    ):
        return "UNKNOWN"
    if (
        packet.current_canonical_claim == current_claim
        and packet.current_canonical_confidence == current_confidence
    ):
        return "CURRENT"
    return "STALE"


def _compare_snapshot_sequence(packet_sequence: int, current_sequence: Any) -> str:
    if isinstance(current_sequence, bool) or not isinstance(current_sequence, int) or current_sequence < 1:
        return "UNKNOWN"
    if packet_sequence == current_sequence:
        return "CURRENT"
    return "STALE"


def reconcile_control_tower_successor(
    packet: ControlTowerSuccessorPacket,
    *,
    current_canonical_claim: Any,
    current_canonical_confidence: str,
    current_snapshot_sequence: int | None,
    expected_successor_control_tower_instance_id: str | None = None,
) -> ControlTowerSuccessorReconciliation:
    """Reconcile successor bootstrap data without applying authority or state."""

    if not isinstance(packet, ControlTowerSuccessorPacket):
        raise ControlTowerHandoffError("SUCCESSOR_PACKET_REQUIRED")
    claim_relation = _compare_successor_claims(
        packet,
        current_canonical_claim,
        current_canonical_confidence,
    )
    snapshot_relation = _compare_snapshot_sequence(
        packet.latest_control_tower_snapshot_sequence,
        current_snapshot_sequence,
    )
    blockers: list[str] = []
    if claim_relation != "CURRENT":
        blockers.append(f"CANONICAL_CLAIM_{claim_relation}")
    if snapshot_relation != "CURRENT":
        blockers.append(f"CONTROL_TOWER_SNAPSHOT_{snapshot_relation}")
    successor_id = packet.proposed_successor_control_tower_instance_id
    if expected_successor_control_tower_instance_id is not None:
        expected_id = _control_tower_instance_id(
            expected_successor_control_tower_instance_id,
            "expected_successor_control_tower_instance_id",
        )
        if expected_id != successor_id:
            blockers.append("SUCCESSOR_CONTROL_TOWER_INSTANCE_MISMATCH")
    status = "READY" if not blockers else "RECONCILIATION_REQUIRED"
    next_action = (
        packet.next_safe_action
        if status == "READY"
        else "Reconcile the successor packet against durable P2P evidence and the current snapshot before accepting material claims."
    )
    return ControlTowerSuccessorReconciliation(
        current_control_tower_instance_id=packet.current_control_tower_instance_id,
        successor_control_tower_instance_id=successor_id,
        canonical_claim_relation=claim_relation,
        snapshot_sequence_relation=snapshot_relation,
        control_tower_status=status,
        host_lanes=_safe_json(packet.host_lanes, path="host_lanes"),
        confirmed_active_execution=_safe_json(
            packet.confirmed_active_execution,
            path="confirmed_active_execution",
        ),
        owner_gates=tuple(_safe_json(packet.owner_gates, path="owner_gates")),
        pending_work=tuple(_safe_json(packet.pending_work, path="pending_work")),
        recently_closed_material_work=tuple(
            _safe_json(packet.recently_closed_material_work, path="recently_closed_material_work")
        ),
        blockers_and_risks=tuple(_safe_json(packet.blockers_and_risks, path="blockers_and_risks")),
        critical_invariants=tuple(_safe_json(packet.critical_invariants, path="critical_invariants")),
        unresolved_chat_only_not_canonical=packet.unresolved_chat_only_not_canonical,
        blockers=tuple(dict.fromkeys(blockers)),
        next_safe_action=next_action,
    )


@dataclass(frozen=True)
class ControlTowerIngestResult:
    host: str
    session_id: str
    session_state: str
    mapped_lifecycle_state: str
    canonical_relation: str
    control_tower_status: str
    owner_gate: Mapping[str, Any] | None
    blockers: tuple[str, ...]
    next_action: str
    promoted: bool = False
    protected_action_executed: bool = False
    packet_is_canonical_truth: bool = False
    canonical_state_overwritten: bool = False
    failure_recorded: bool = False
    narrative_host_ignored: bool = False
    idempotent: bool = False
    packet_fingerprint: str = "UNKNOWN"
    promotion_claim_detected: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "HOST": self.host,
            "SESSION_ID": self.session_id,
            "SESSION_STATE": self.session_state,
            "MAPPED_LIFECYCLE_STATE": self.mapped_lifecycle_state,
            "CANONICAL_RELATION": self.canonical_relation,
            "CONTROL_TOWER_STATUS": self.control_tower_status,
            "OWNER_GATE": _safe_json(self.owner_gate, path="owner_gate") if self.owner_gate is not None else None,
            "BLOCKERS": list(self.blockers),
            "NEXT_ACTION": self.next_action,
            "PROMOTED": self.promoted,
            "PROTECTED_ACTION_EXECUTED": self.protected_action_executed,
            "PACKET_IS_CANONICAL_TRUTH": "YES" if self.packet_is_canonical_truth else "NO",
            "CANONICAL_STATE_OVERWRITTEN": self.canonical_state_overwritten,
            "FAILURE_RECORDED": self.failure_recorded,
            "NARRATIVE_HOST_IGNORED": self.narrative_host_ignored,
            "IDEMPOTENT": self.idempotent,
            "PACKET_FINGERPRINT": self.packet_fingerprint,
            "PROMOTION_CLAIM_DETECTED": self.promotion_claim_detected,
        }


def _compare_bases(packet: ControlTowerReturnPacket, current_sha: Any, current_tree: Any) -> str:
    observed_sha = _hash_or_unknown(current_sha, "current_canonical_base_sha")
    observed_tree = _hash_or_unknown(current_tree, "current_canonical_base_tree")
    if "UNKNOWN" in {packet.canonical_base_sha, packet.canonical_base_tree, observed_sha, observed_tree}:
        return "UNKNOWN"
    if "NONE" in {packet.canonical_base_sha, packet.canonical_base_tree, observed_sha, observed_tree}:
        return "UNKNOWN"
    if packet.canonical_base_sha == observed_sha and packet.canonical_base_tree == observed_tree:
        return "CURRENT"
    return "STALE"


def _contains_promotion_claim(value: Any) -> bool:
    if isinstance(value, str):
        return _PROMOTION_TERM_PATTERN.search(value) is not None
    if isinstance(value, Mapping):
        return any(_contains_promotion_claim(child) for child in value.values())
    if isinstance(value, (list, tuple)):
        return any(_contains_promotion_claim(child) for child in value)
    return False


@dataclass
class ControlTowerState:
    """Durable-semantic projection over existing task/evidence/ledger state.

    The object is intentionally only a serializable projection. Callers that
    persist events must use the existing execution-ledger writer; this class
    never opens files or mutates canonical state itself.
    """

    lanes: dict[str, dict[str, Any]] = field(default_factory=dict)
    return_events: list[dict[str, Any]] = field(default_factory=list)
    session_records: dict[str, dict[str, Any]] = field(default_factory=dict)

    @classmethod
    def empty(cls, hosts: Sequence[str] = ()) -> "ControlTowerState":
        lanes: dict[str, dict[str, Any]] = {}
        for host in hosts:
            normalized = normalize_host(host)
            lanes[normalized] = {
                "HOST": normalized,
                "CONTROL_TOWER_STATUS": "IDLE",
                "PROMOTED": False,
                "PROTECTED_ACTION_EXECUTED": False,
                "PACKET_IS_CANONICAL_TRUTH": "NO",
            }
        return cls(lanes=lanes)

    def ingest(
        self,
        packet: ControlTowerReturnPacket,
        *,
        current_canonical_base_sha: str,
        current_canonical_base_tree: str,
        narrative_host: Any = None,
        record_event: bool = True,
    ) -> ControlTowerIngestResult:
        if not isinstance(packet, ControlTowerReturnPacket):
            raise ControlTowerHandoffError("CONTROL_TOWER_PACKET_REQUIRED")
        relation = _compare_bases(packet, current_canonical_base_sha, current_canonical_base_tree)
        blockers = list(packet.blockers)
        if relation != "CURRENT":
            status = "RECONCILIATION_REQUIRED"
            blockers.append(f"CANONICAL_BASE_{relation}")
            next_action = "Reconcile the packet against fresh canonical SHA/tree before any merge, promotion, or protected action."
        else:
            status = packet.session_state
            next_action = packet.next_recommended_action
        deduped_blockers = tuple(dict.fromkeys(blockers))
        promotion_claim_detected = _contains_promotion_claim(
            (
                packet.changes,
                packet.test_results,
                packet.evidence,
                packet.owner_gate,
                packet.blockers,
                packet.next_recommended_action,
            )
        )
        lane = {
            "HOST": packet.binding.host,
            "SESSION_ID": packet.binding.session_id,
            "GOAL_ID": packet.binding.goal_id,
            "SESSION_STATE": packet.session_state,
            "MAPPED_LIFECYCLE_STATE": packet.mapped_lifecycle_state,
            "CONTROL_TOWER_STATUS": status,
            "CANONICAL_RELATION": relation,
            "CURRENT_CANONICAL_BASE_SHA": _hash_or_unknown(
                current_canonical_base_sha, "current_canonical_base_sha"
            ),
            "CURRENT_CANONICAL_BASE_TREE": _hash_or_unknown(
                current_canonical_base_tree, "current_canonical_base_tree"
            ),
            "OWNER_GATE": _safe_json(packet.owner_gate, path="owner_gate") if packet.owner_gate is not None else None,
            "UPLOAD_REQUIRED": packet.attachment_manifest.upload_required,
            "CONTROL_TOWER_ATTACHMENT_MANIFEST": packet.attachment_manifest.to_dict(),
            "BLOCKERS": list(deduped_blockers),
            "NEXT_RECOMMENDED_ACTION": next_action,
            "PROMOTED": False,
            "PROTECTED_ACTION_EXECUTED": False,
            "PROMOTION_CLAIM_DETECTED": promotion_claim_detected,
            "PACKET_IS_CANONICAL_TRUTH": "NO",
            "CANONICAL_STATE_OVERWRITTEN": False,
        }
        self.lanes[packet.binding.host] = lane
        result = ControlTowerIngestResult(
            host=packet.binding.host,
            session_id=packet.binding.session_id,
            session_state=packet.session_state,
            mapped_lifecycle_state=packet.mapped_lifecycle_state,
            canonical_relation=relation,
            control_tower_status=status,
            owner_gate=packet.owner_gate,
            blockers=deduped_blockers,
            next_action=next_action,
            failure_recorded=packet.session_state == "FAILED",
            narrative_host_ignored=narrative_host is not None,
            packet_fingerprint=packet.fingerprint(),
            promotion_claim_detected=promotion_claim_detected,
        )
        if record_event:
            self.return_events.append(to_execution_ledger_event(packet, result))
        return result

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": CONTROL_TOWER_PROJECTION_SCHEMA,
            "LANES": _safe_json(self.lanes, path="lanes"),
            "RETURN_EVENTS": _safe_json(self.return_events, path="return_events"),
            "SESSION_RECORDS": _safe_json(self.session_records, path="session_records"),
            "CANONICAL_TRUTH_UPDATED": "NO",
            "PROMOTION_EXECUTED": "NO",
        }


def to_execution_ledger_event(
    packet: ControlTowerReturnPacket,
    reconciliation: ControlTowerIngestResult | None = None,
) -> dict[str, Any]:
    """Return a JSON event for the existing execution-ledger writer.

    This function deliberately does not write a file. The caller may pass the
    event to the repository's existing append_event surface.
    """

    if not isinstance(packet, ControlTowerReturnPacket):
        raise ControlTowerHandoffError("CONTROL_TOWER_PACKET_REQUIRED")
    return {
        "schema": CONTROL_TOWER_EVENT_SCHEMA,
        "event_type": "CONTROL_TOWER_RETURN_PACKET",
        "PACKET_FINGERPRINT": packet.fingerprint(),
        "CONTROL_TOWER_RETURN_PACKET": packet.to_dict(),
        "CONTROL_TOWER_RECONCILIATION": reconciliation.to_dict() if reconciliation is not None else None,
        "CANONICAL_TRUTH_UPDATED": "NO",
        "PROTECTED_ACTION_EXECUTED": "NO",
    }


CONTROL_TOWER_LEDGER_RELATIVE_PATH = Path(".p2p") / "state" / "execution-ledger.jsonl"


def _control_tower_ledger_path(root: str | Path) -> Path:
    root_path = Path(root).expanduser().resolve()
    if not root_path.is_dir():
        raise ProjectionError(f"CONTROL_TOWER_ROOT_NOT_FOUND:{root_path}")
    ledger = root_path / CONTROL_TOWER_LEDGER_RELATIVE_PATH
    if ledger.is_symlink() or (ledger.exists() and not ledger.is_file()):
        raise ProjectionError("CONTROL_TOWER_LEDGER_PATH_INVALID")
    return ledger


def _read_control_tower_events(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        raise ProjectionError(f"CONTROL_TOWER_LEDGER_UNREADABLE:{exc}") from exc
    events: list[dict[str, Any]] = []
    for line_number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            raw = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ProjectionError(f"CONTROL_TOWER_LEDGER_INVALID_JSON:{line_number}") from exc
        if not isinstance(raw, Mapping):
            continue
        if raw.get("event_type") not in {
            "CONTROL_TOWER_SESSION_STARTED",
            "CONTROL_TOWER_RETURN_PACKET",
        }:
            continue
        try:
            _reject_secret_keys(raw)
            safe = _safe_json(raw, path=f"ledger[{line_number}]")
        except ControlTowerHandoffError as exc:
            raise ProjectionError(f"CONTROL_TOWER_LEDGER_EVENT_UNSAFE:{line_number}:{exc}") from exc
        if not isinstance(safe, dict):
            raise ProjectionError(f"CONTROL_TOWER_LEDGER_EVENT_INVALID:{line_number}")
        safe["_LINE_NUMBER"] = line_number
        events.append(safe)
    return events


def _append_existing_execution_event(path: Path, event: Mapping[str, Any]) -> None:
    """Use the repository's existing execution-ledger writer; never create a second store."""

    try:
        from p2p_workflow import append_event
    except ImportError:
        try:
            from scripts.p2p_workflow import append_event
        except ImportError as exc:
            raise ProjectionError("EXISTING_EXECUTION_LEDGER_WRITER_UNAVAILABLE") from exc
    try:
        append_event(path, dict(event))
    except (OSError, TypeError, ValueError) as exc:
        raise ProjectionError(f"CONTROL_TOWER_LEDGER_APPEND_FAILED:{exc}") from exc


def _same_binding(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    return all(left.get(field_name) == right.get(field_name) for field_name in ("SESSION_ID", "HOST", "GOAL_ID", "GOAL"))


def _session_recommendation(
    binding: SessionBinding,
    *,
    task_prompt: str | None = None,
    worktree: str = UNKNOWN,
    branch: str = UNKNOWN,
    canonical_base_sha: str = UNKNOWN,
    canonical_base_tree: str = UNKNOWN,
    acceptance_criteria: Sequence[str] = (),
    task_id: str = UNKNOWN,
) -> dict[str, Any]:
    prompt = build_execution_prompt(
        binding,
        task_prompt or binding.goal,
        worktree=worktree,
        branch=branch,
        canonical_base_sha=canonical_base_sha,
        canonical_base_tree=canonical_base_tree,
        acceptance_criteria=acceptance_criteria,
    )
    return {
        "CHAT_NAME": f"{binding.host} — {binding.goal_id} — {binding.goal}",
        "HOST": binding.host,
        "SESSION_ID": binding.session_id,
        "GOAL_ID": binding.goal_id,
        "TASK_ID": task_id,
        "PROMPT": prompt,
        "PACKET_IS_CANONICAL_TRUTH": "NO",
    }


class ControlTower:
    """Durable coordinator over the existing execution ledger.

    The coordinator persists only structured session-start and return events
    through the repository's existing ledger writer.  It never creates a
    second state store, launches a host, or promotes a candidate.
    """

    def __init__(
        self,
        root: str | Path,
        *,
        current_canonical_base_sha: str = UNKNOWN,
        current_canonical_base_tree: str = UNKNOWN,
    ) -> None:
        self.root = Path(root).expanduser().resolve()
        self.ledger_path = _control_tower_ledger_path(self.root)
        self.current_canonical_base_sha = _hash_or_unknown(
            current_canonical_base_sha,
            "current_canonical_base_sha",
        )
        self.current_canonical_base_tree = _hash_or_unknown(
            current_canonical_base_tree,
            "current_canonical_base_tree",
        )

    def _observed_bases(
        self,
        current_canonical_base_sha: str | None,
        current_canonical_base_tree: str | None,
    ) -> tuple[str, str]:
        sha = self.current_canonical_base_sha if current_canonical_base_sha is None else current_canonical_base_sha
        tree = self.current_canonical_base_tree if current_canonical_base_tree is None else current_canonical_base_tree
        return (
            _hash_or_unknown(sha, "current_canonical_base_sha"),
            _hash_or_unknown(tree, "current_canonical_base_tree"),
        )

    def _replay(
        self,
        *,
        current_canonical_base_sha: str | None = None,
        current_canonical_base_tree: str | None = None,
    ) -> tuple[ControlTowerState, list[dict[str, Any]]]:
        current_sha, current_tree = self._observed_bases(
            current_canonical_base_sha,
            current_canonical_base_tree,
        )
        state = ControlTowerState.empty()
        records: dict[str, dict[str, Any]] = {}
        orphan_returns: list[dict[str, Any]] = []
        for event in _read_control_tower_events(self.ledger_path):
            event_type = event.get("event_type")
            if event_type == "CONTROL_TOWER_SESSION_STARTED":
                raw_binding = event.get("SESSION_BINDING")
                if not isinstance(raw_binding, Mapping):
                    raise ProjectionError("CONTROL_TOWER_SESSION_BINDING_INVALID")
                binding = SessionBinding.from_mapping(raw_binding)
                session_id = binding.session_id
                existing = records.get(session_id)
                if existing is not None and not _same_binding(
                    existing.get("BINDING", {}),
                    binding.to_dict(),
                ):
                    raise ProjectionError("CONTROL_TOWER_SESSION_BINDING_CONFLICT")
                record = dict(existing or {})
                record.update(
                    {
                        "SESSION_ID": session_id,
                        "HOST": binding.host,
                        "GOAL_ID": binding.goal_id,
                        "GOAL": binding.goal,
                        "BINDING": binding.to_dict(),
                        "TASK_ID": event.get("TASK_ID", UNKNOWN),
                        "WORKTREE": event.get("WORKTREE", UNKNOWN),
                        "BRANCH": event.get("BRANCH", UNKNOWN),
                        "CANONICAL_BASE_SHA": event.get("CANONICAL_BASE_SHA", UNKNOWN),
                        "CANONICAL_BASE_TREE": event.get("CANONICAL_BASE_TREE", UNKNOWN),
                        "SESSION_STATE": record.get("SESSION_STATE", "ACTIVE"),
                        "PACKET_FINGERPRINT": record.get("PACKET_FINGERPRINT", UNKNOWN),
                        "RECOMMENDED_NEW_CHAT": event.get("RECOMMENDED_NEW_CHAT"),
                    }
                )
                records[session_id] = record
                state.lanes.setdefault(
                    binding.host,
                    {
                        "HOST": binding.host,
                        "SESSION_ID": session_id,
                        "CONTROL_TOWER_STATUS": "ACTIVE",
                        "PROMOTED": False,
                        "PROTECTED_ACTION_EXECUTED": False,
                        "PACKET_IS_CANONICAL_TRUTH": "NO",
                    },
                )
                continue

            raw_packet = event.get("CONTROL_TOWER_RETURN_PACKET")
            if not isinstance(raw_packet, Mapping):
                raise ProjectionError("CONTROL_TOWER_RETURN_PACKET_INVALID")
            try:
                packet = ControlTowerReturnPacket.from_mapping(raw_packet)
            except ControlTowerHandoffError as exc:
                raise ProjectionError(f"CONTROL_TOWER_RETURN_PACKET_INVALID:{exc}") from exc
            record = records.get(packet.binding.session_id)
            if record is None:
                orphan_returns.append(
                    {
                        "LINE": event.get("_LINE_NUMBER"),
                        "SESSION_ID": packet.binding.session_id,
                        "HOST": packet.binding.host,
                    }
                )
                continue
            packet_fingerprint = event.get("PACKET_FINGERPRINT") or packet.fingerprint()
            if packet_fingerprint != packet.fingerprint():
                raise ProjectionError("CONTROL_TOWER_PACKET_FINGERPRINT_MISMATCH")
            previous_fingerprint = record.get("PACKET_FINGERPRINT", UNKNOWN)
            if previous_fingerprint not in (UNKNOWN, packet_fingerprint):
                raise ProjectionError("CONTROL_TOWER_MULTIPLE_DIFFERENT_RETURN_PACKETS")
            result = state.ingest(
                packet,
                current_canonical_base_sha=current_sha,
                current_canonical_base_tree=current_tree,
                record_event=False,
            )
            state.return_events.append({key: value for key, value in event.items() if key != "_LINE_NUMBER"})
            updated = dict(record)
            updated.update(
                {
                    "SESSION_STATE": packet.session_state,
                    "WORKTREE": packet.worktree,
                    "BRANCH": packet.branch,
                    "CANONICAL_BASE_SHA": packet.canonical_base_sha,
                    "CANONICAL_BASE_TREE": packet.canonical_base_tree,
                    "CANDIDATE_OR_CHECKPOINT_SHA": packet.candidate_or_checkpoint_sha,
                    "OWNER_GATE": packet.owner_gate,
                    "BLOCKERS": list(packet.blockers),
                    "NEXT_RECOMMENDED_ACTION": packet.next_recommended_action,
                    "PACKET": packet.to_dict(),
                    "PACKET_FINGERPRINT": packet_fingerprint,
                    "RECONCILIATION": result.to_dict(),
                }
            )
            records[packet.binding.session_id] = updated
        state.session_records = records
        return state, orphan_returns

    @staticmethod
    def _next_action(record: Mapping[str, Any] | None) -> dict[str, Any]:
        if not isinstance(record, Mapping):
            return {
                "ACTION": "NO_ACTIVE_EXECUTION",
                "REASON": "No Control Tower session is registered.",
            }
        session_state = record.get("SESSION_STATE", UNKNOWN)
        reconciliation = record.get("RECONCILIATION")
        relation = reconciliation.get("CANONICAL_RELATION", UNKNOWN) if isinstance(reconciliation, Mapping) else UNKNOWN
        if session_state == "WAITING_OWNER_GATE":
            return {"ACTION": "WAIT_FOR_OWNER_DECISION", "REASON": "The packet records a pending Owner Gate."}
        if session_state in {"FAILED", "BLOCKED", "ABORTED"}:
            return {"ACTION": "REVIEW_FAILURE_AND_RECONCILE_BEFORE_RETRY", "REASON": "A terminal non-success state must remain visible."}
        if relation != "CURRENT":
            return {"ACTION": "RECONCILE_STALE_OR_UNKNOWN_BASE", "REASON": "The packet base is not freshly confirmed against both SHA and tree."}
        next_action = record.get("NEXT_RECOMMENDED_ACTION", UNKNOWN)
        if not isinstance(next_action, str) or next_action in {"", UNKNOWN} or _PROMOTION_TERM_PATTERN.search(next_action):
            return {"ACTION": "NO_AUTOMATIC_CONTINUATION", "REASON": "The next action is unknown or crosses a protected boundary."}
        return {"ACTION": next_action, "REASON": "Use only the registered session scope."}

    def _projection(
        self,
        state: ControlTowerState,
        orphan_returns: Sequence[Mapping[str, Any]],
        *,
        current_canonical_base_sha: str | None = None,
        current_canonical_base_tree: str | None = None,
    ) -> dict[str, Any]:
        current_sha, current_tree = self._observed_bases(
            current_canonical_base_sha,
            current_canonical_base_tree,
        )
        active: list[dict[str, Any]] = []
        closed: list[dict[str, Any]] = []
        owner_gates: list[dict[str, Any]] = []
        risks: list[dict[str, Any]] = []
        latest: Mapping[str, Any] | None = None
        for record in state.session_records.values():
            if record.get("SESSION_STATE") == "ACTIVE":
                active.append(
                    {
                        "SESSION_ID": record.get("SESSION_ID", UNKNOWN),
                        "HOST": record.get("HOST", UNKNOWN),
                        "GOAL_ID": record.get("GOAL_ID", UNKNOWN),
                        "TASK_ID": record.get("TASK_ID", UNKNOWN),
                    }
                )
            else:
                closed.append(dict(record))
            owner_gate = record.get("OWNER_GATE")
            if owner_gate not in (None, UNKNOWN, "") and isinstance(owner_gate, Mapping):
                owner_gates.append(dict(owner_gate))
            reconciliation = record.get("RECONCILIATION")
            relation = reconciliation.get("CANONICAL_RELATION", UNKNOWN) if isinstance(reconciliation, Mapping) else UNKNOWN
            if record.get("SESSION_STATE") in {"BLOCKED", "FAILED", "ABORTED"} or relation != "CURRENT":
                risks.append(
                    {
                        "SESSION_ID": record.get("SESSION_ID", UNKNOWN),
                        "HOST": record.get("HOST", UNKNOWN),
                        "SESSION_STATE": record.get("SESSION_STATE", UNKNOWN),
                        "CANONICAL_RELATION": relation,
                        "BLOCKERS": record.get("BLOCKERS", []),
                    }
                )
            latest = record
        projection = state.to_dict()
        projection.update(
            {
                "schema": CONTROL_TOWER_PROJECTION_SCHEMA,
                "CANONICAL": {
                    "CURRENT_BASE_SHA": current_sha,
                    "CURRENT_BASE_TREE": current_tree,
                    "CANONICAL_TRUTH_UPDATED": "NO",
                },
                "HOST_LANES": state.lanes,
                "ACTIVE_EXECUTION": active,
                "OWNER_GATES": owner_gates,
                "RECENTLY_CLOSED": closed,
                "BLOCKED_RISKS": risks,
                "ORPHAN_RETURN_EVENTS": list(orphan_returns),
                "NEXT_SAFE_ACTION": self._next_action(latest) if not active else {
                    "ACTION": "EXECUTE_ONLY_REGISTERED_SESSION_SCOPE",
                    "REASON": "An explicitly bound execution session is active.",
                },
                "PROMOTION": {
                    "STATUS": "NOT_INFERRED",
                    "PROMOTED": False,
                    "REASON": "A packet or session state cannot establish promotion.",
                },
                "PERSISTENCE": {
                    "PATH": CONTROL_TOWER_LEDGER_RELATIVE_PATH.as_posix(),
                    "EXISTING_EXECUTION_LEDGER_ONLY": "YES",
                    "SECOND_STORE_CREATED": "NO",
                },
                "PACKET_IS_CANONICAL_TRUTH": "NO",
                "CONTROL_TOWER_STATUS": "ACTIVE" if active else (latest.get("SESSION_STATE", "IDLE") if latest else "IDLE"),
            }
        )
        return projection

    def snapshot(
        self,
        *,
        current_canonical_base_sha: str | None = None,
        current_canonical_base_tree: str | None = None,
    ) -> dict[str, Any]:
        state, orphan_returns = self._replay(
            current_canonical_base_sha=current_canonical_base_sha,
            current_canonical_base_tree=current_canonical_base_tree,
        )
        return self._projection(
            state,
            orphan_returns,
            current_canonical_base_sha=current_canonical_base_sha,
            current_canonical_base_tree=current_canonical_base_tree,
        )

    def start_session(
        self,
        binding: SessionBinding,
        *,
        task_id: str = UNKNOWN,
        task_prompt: str | None = None,
        worktree: str = UNKNOWN,
        branch: str = UNKNOWN,
        canonical_base_sha: str = UNKNOWN,
        canonical_base_tree: str = UNKNOWN,
        acceptance_criteria: Sequence[str] = (),
    ) -> dict[str, Any]:
        if not isinstance(binding, SessionBinding):
            raise BindingError("SESSION_BINDING_REQUIRED")
        task_id = _optional_text(task_id, "task_id", max_length=256)
        worktree = _location(worktree, "worktree")
        branch = _location(branch, "branch")
        canonical_base_sha = _hash_or_unknown(canonical_base_sha, "canonical_base_sha")
        canonical_base_tree = _hash_or_unknown(canonical_base_tree, "canonical_base_tree")
        criteria = _refs(acceptance_criteria, "acceptance_criteria", max_length=4096)
        state, orphan_returns = self._replay()
        existing = state.session_records.get(binding.session_id)
        if existing is not None:
            existing_binding = existing.get("BINDING")
            if not isinstance(existing_binding, Mapping) or not _same_binding(existing_binding, binding.to_dict()):
                raise BindingError("SESSION_ID_ALREADY_BOUND_TO_DIFFERENT_SESSION")
            if existing.get("SESSION_STATE") != "ACTIVE":
                raise BindingError("SESSION_ID_ALREADY_HAS_TERMINAL_RESULT")
            recommendation = existing.get("RECOMMENDED_NEW_CHAT")
            if not isinstance(recommendation, Mapping):
                recommendation = _session_recommendation(
                    binding,
                    task_prompt=task_prompt,
                    worktree=worktree,
                    branch=branch,
                    canonical_base_sha=canonical_base_sha,
                    canonical_base_tree=canonical_base_tree,
                    acceptance_criteria=criteria,
                    task_id=task_id,
                )
            return {
                "status": "PASS",
                "idempotent": True,
                "binding": binding.to_dict(),
                "task_id": existing.get("TASK_ID", task_id),
                "recommendation": dict(recommendation),
                "snapshot": self._projection(state, orphan_returns),
            }
        recommendation = _session_recommendation(
            binding,
            task_prompt=task_prompt,
            worktree=worktree,
            branch=branch,
            canonical_base_sha=canonical_base_sha,
            canonical_base_tree=canonical_base_tree,
            acceptance_criteria=criteria,
            task_id=task_id,
        )
        event = {
            "schema": CONTROL_TOWER_SESSION_START_EVENT_SCHEMA,
            "event_type": "CONTROL_TOWER_SESSION_STARTED",
            "CONTROL_TOWER_SESSION_STARTED": True,
            "SESSION_BINDING": binding.to_dict(),
            "TASK_ID": task_id,
            "WORKTREE": worktree,
            "BRANCH": branch,
            "CANONICAL_BASE_SHA": canonical_base_sha,
            "CANONICAL_BASE_TREE": canonical_base_tree,
            "RECOMMENDED_NEW_CHAT": recommendation,
            "PACKET_IS_CANONICAL_TRUTH": "NO",
            "PROMOTED": False,
            "PROTECTED_ACTION_EXECUTED": False,
        }
        _append_existing_execution_event(self.ledger_path, event)
        return {
            "status": "PASS",
            "idempotent": False,
            "binding": binding.to_dict(),
            "task_id": task_id,
            "recommendation": recommendation,
            "snapshot": self.snapshot(),
        }

    def ingest_response(
        self,
        final_response: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        try:
            packet = parse_return_packet(final_response)
        except ControlTowerHandoffError as exc:
            raise PacketParseError(str(exc)) from exc
        return self.ingest_packet(packet, **kwargs)

    def ingest_packet(
        self,
        packet: ControlTowerReturnPacket,
        *,
        current_canonical_base_sha: str | None = None,
        current_canonical_base_tree: str | None = None,
        narrative_host: Any = None,
    ) -> dict[str, Any]:
        if not isinstance(packet, ControlTowerReturnPacket):
            raise BindingError("CONTROL_TOWER_PACKET_REQUIRED")
        current_sha, current_tree = self._observed_bases(
            current_canonical_base_sha,
            current_canonical_base_tree,
        )
        state, orphan_returns = self._replay(
            current_canonical_base_sha=current_sha,
            current_canonical_base_tree=current_tree,
        )
        record = state.session_records.get(packet.binding.session_id)
        if not isinstance(record, Mapping):
            raise BindingError("SESSION_ID_NOT_REGISTERED_IN_CONTROL_TOWER_LEDGER")
        binding = record.get("BINDING")
        if not isinstance(binding, Mapping) or not _same_binding(binding, packet.binding.to_dict()):
            raise BindingError("PACKET_BINDING_REJECTED")
        packet_fingerprint = packet.fingerprint()
        previous_fingerprint = record.get("PACKET_FINGERPRINT", UNKNOWN)
        if previous_fingerprint != UNKNOWN:
            if previous_fingerprint == packet_fingerprint:
                return {
                    "status": "PASS",
                    "idempotent": True,
                    "reconciliation": record.get("RECONCILIATION"),
                    "snapshot": self._projection(
                        state,
                        orphan_returns,
                        current_canonical_base_sha=current_sha,
                        current_canonical_base_tree=current_tree,
                    ),
                }
            raise BindingError("SESSION_ALREADY_HAS_A_DIFFERENT_RETURN_PACKET")
        result = state.ingest(
            packet,
            current_canonical_base_sha=current_sha,
            current_canonical_base_tree=current_tree,
            narrative_host=narrative_host,
            record_event=False,
        )
        _append_existing_execution_event(self.ledger_path, to_execution_ledger_event(packet, result))
        snapshot = self.snapshot(
            current_canonical_base_sha=current_sha,
            current_canonical_base_tree=current_tree,
        )
        return {
            "status": "PASS",
            "idempotent": False,
            "reconciliation": result.to_dict(),
            "snapshot": snapshot,
        }

    def recommend_next_session(
        self,
        host: str,
        *,
        session_id: str | None = None,
        worktree: str = UNKNOWN,
        branch: str = UNKNOWN,
    ) -> dict[str, Any]:
        """Derive one safe task-state session without starting a host."""

        try:
            from .task_state import TaskStateStore, next_safe_task
        except ImportError as exc:
            raise ProjectionError("TASK_STATE_SURFACE_UNAVAILABLE") from exc
        try:
            plan = TaskStateStore(self.root).load()
        except Exception as exc:  # task-state errors must remain fail-closed
            raise ProjectionError(f"TASK_STATE_UNREADABLE:{exc}") from exc
        if plan is None:
            return {
                "status": "UNKNOWN",
                "reason": "TASK_STATE_NOT_INITIALIZED",
                "source": (Path(".p2p") / "state" / "task-state.json").as_posix(),
                "automatic_start": False,
                "recommendation": None,
            }
        task = next_safe_task(plan)
        if task is None:
            waiting = next(
                (
                    item
                    for item in plan.tasks.values()
                    if item.status == "WAITING_OWNER"
                    or (
                        isinstance(item.owner_decision, Mapping)
                        and str(item.owner_decision.get("status", "")).upper() in {"PENDING", "WAITING"}
                    )
                ),
                None,
            )
            if waiting is not None:
                return {
                    "status": "WAITING_OWNER_GATE",
                    "reason": "OWNER_DECISION_PENDING",
                    "task_id": waiting.task_id,
                    "owner_gate": waiting.owner_decision,
                    "automatic_start": False,
                    "recommendation": None,
                }
            return {
                "status": "UNKNOWN",
                "reason": "NO_SAFE_READY_TASK",
                "automatic_start": False,
                "recommendation": None,
            }
        normalized_host = normalize_host(host)
        state, orphan_returns = self._replay()
        for record in state.session_records.values():
            if record.get("SESSION_STATE") != "ACTIVE" or record.get("TASK_ID") != task.task_id:
                continue
            existing_binding = record.get("BINDING")
            recommendation = record.get("RECOMMENDED_NEW_CHAT")
            if isinstance(existing_binding, Mapping) and isinstance(recommendation, Mapping):
                return {
                    "status": "PASS",
                    "idempotent": True,
                    "task_id": task.task_id,
                    "plan_hash": plan.canonical_hash(),
                    "acceptance_criteria": list(task.acceptance_requirements),
                    "binding": dict(existing_binding),
                    "recommendation": dict(recommendation),
                    "snapshot": self._projection(state, orphan_returns),
                }
            return {
                "status": "BLOCKED",
                "reason": "TASK_ALREADY_HAS_AN_ACTIVE_CONTROL_TOWER_SESSION",
                "task_id": task.task_id,
                "automatic_start": False,
                "recommendation": None,
            }
        binding = SessionBinding(
            session_id=session_id or new_session_id(normalized_host, plan.goal_id, task.task_id),
            host=normalized_host,
            goal_id=plan.goal_id,
            goal=task.purpose,
        )
        recommendation = _session_recommendation(
            binding,
            task_prompt=task.purpose,
            worktree=worktree,
            branch=branch,
            acceptance_criteria=task.acceptance_requirements,
            task_id=task.task_id,
        )
        return {
            "status": "PASS",
            "idempotent": False,
            "task_id": task.task_id,
            "plan_hash": plan.canonical_hash(),
            "acceptance_criteria": list(task.acceptance_requirements),
            "binding": binding.to_dict(),
            "recommendation": recommendation,
            "automatic_start": False,
        }

    def start_next_session(
        self,
        host: str,
        *,
        session_id: str | None = None,
        worktree: str = UNKNOWN,
        branch: str = UNKNOWN,
    ) -> dict[str, Any]:
        result = self.recommend_next_session(
            host,
            session_id=session_id,
            worktree=worktree,
            branch=branch,
        )
        if result.get("status") != "PASS":
            return result
        binding_mapping = result.get("binding")
        if not isinstance(binding_mapping, Mapping):
            raise ProjectionError("NEXT_SESSION_BINDING_INVALID")
        started = self.start_session(
            SessionBinding.from_mapping(binding_mapping),
            task_id=str(result.get("task_id", UNKNOWN)),
            worktree=worktree,
            branch=branch,
            acceptance_criteria=tuple(result.get("acceptance_criteria") or ()),
        )
        started.update(
            {
                "source": (Path(".p2p") / "state" / "task-state.json").as_posix(),
                "task_id": result.get("task_id", UNKNOWN),
                "plan_hash": result.get("plan_hash", UNKNOWN),
            }
        )
        return started


def next_safe_session(
    root: str | Path,
    host: str,
    *,
    session_id: str | None = None,
    worktree: str = UNKNOWN,
    branch: str = UNKNOWN,
) -> dict[str, Any]:
    return ControlTower(root).recommend_next_session(
        host,
        session_id=session_id,
        worktree=worktree,
        branch=branch,
    )


def build_execution_prompt(
    binding: SessionBinding,
    task_prompt: str,
    *,
    worktree: str = "UNKNOWN",
    branch: str = "UNKNOWN",
    canonical_base_sha: str = "UNKNOWN",
    canonical_base_tree: str = "UNKNOWN",
    acceptance_criteria: Sequence[str] = (),
) -> str:
    """Build a self-contained recursive prompt for one compatible host."""

    if not isinstance(binding, SessionBinding):
        raise ControlTowerHandoffError("SESSION_BINDING_REQUIRED")
    task = _text(task_prompt, "task_prompt", max_length=12000)
    worktree_value = _location(worktree, "worktree")
    branch_value = _location(branch, "branch")
    sha_value = _hash_or_unknown(canonical_base_sha, "canonical_base_sha")
    tree_value = _hash_or_unknown(canonical_base_tree, "canonical_base_tree")
    criteria = _refs(acceptance_criteria, "acceptance_criteria", max_length=4096)
    criteria_text = "\n".join(f"- {item}" for item in criteria) or "- Return a truthful terminal packet."
    return "\n".join(
        (
            f"CONTROL_TOWER_EXECUTION_PROMPT: {CONTROL_TOWER_PROMPT_SCHEMA}",
            "AUTHORITATIVE_SESSION_BINDING:",
            f"SESSION_ID: {binding.session_id}",
            f"HOST: {binding.host}",
            f"GOAL_ID: {binding.goal_id}",
            f"GOAL: {binding.goal}",
            f"WORKTREE: {worktree_value}",
            f"BRANCH: {branch_value}",
            f"CANONICAL_BASE_SHA: {sha_value}",
            f"CANONICAL_BASE_TREE: {tree_value}",
            "",
            "TASK:",
            task,
            "",
            "ACCEPTANCE_CRITERIA:",
            criteria_text,
            "",
            "P2P_SUPREME_LAW_PREFLIGHT:",
            f"- Before implementation, read P2P_SUPREME_OPERATING_LAW_V1 from {SUPREME_LAW_DEVELOPMENT_PATH} when that path is accessible.",
            f"- In an installed project, use {SUPREME_LAW_INSTALLED_PATH}.",
            "- If neither repository path is readable, the inline SUPREME_LAW_CAPSULE below is authoritative for this execution.",
            "- Do not claim that a repository file was read unless it actually was.",
            "- Apply the law to outcome, authority, next useful action, verification, retry/stuckness, and stopping; do not turn preflight into a separate report.",
            "SUPREME_LAW_CAPSULE:",
            SUPREME_LAW_CAPSULE,
            "",
            "SESSION_RULES:",
            "- Use the explicit HOST above as authoritative; never infer a host from narrative prose.",
            "- Do not inherit chat history, prior session state, or implicit context.",
            "- Do not promote, merge, deploy, release, or perform a protected action from this prompt.",
            "- Finish with one structured CONTROL_TOWER_RETURN_PACKET.",
            "",
            "CONTROL_TOWER_RETURN_PACKET:",
            PACKET_BEGIN,
            "Return one JSON object matching the packet schema between these markers.",
            "SESSION_STATE must be one of COMPLETED, READY, WAITING_OWNER_GATE, BLOCKED, FAILED, or ABORTED.",
            "Include SESSION_ID, HOST, GOAL_ID, GOAL, SESSION_STATE, CANONICAL_BASE_SHA, CANONICAL_BASE_TREE,",
            "CANONICAL_RELATION, WORKTREE, BRANCH, CHANGES, TEST_RESULTS, EVIDENCE,",
            "CANDIDATE_OR_CHECKPOINT_SHA, TERMINAL_VERDICT, OWNER_GATE, BLOCKERS, and NEXT_RECOMMENDED_ACTION.",
            "Every terminal response must declare UPLOAD_REQUIRED as YES or NO.",
            "Include CONTROL_TOWER_ATTACHMENT_MANIFEST in the terminal packet.",
            "When UPLOAD_REQUIRED is NO, state that the user only needs to copy the entire final response",
            "to 00 — P2P CONTROL TOWER and does not need to upload a file.",
            "When UPLOAD_REQUIRED is YES, list exactly 1-3 minimal files with FILENAME, LOCAL_PATH, PURPOSE,",
            "WHY_CONTROL_TOWER_NEEDS_CONTENTS, and CLASSIFICATION as REQUIRED, OPTIONAL, or DO_NOT_UPLOAD.",
            "A local path alone does not make file contents available to the Control Tower.",
            "Attachments are evidence input only and never canonical truth or proof of promotion, deployment,",
            "live certification, or Owner approval.",
            "Prefer one SESSION_ID-CONTROL-TOWER-HANDOFF.md artifact when appropriate.",
            "PACKET_IS_CANONICAL_TRUTH: NO",
            "Return the packet to the Control Tower for reconciliation; the packet is not canonical truth.",
            "Control Tower chats are rotatable instances; durable P2P repository/evidence/governance remains the long-lived source of truth.",
            "When asked to prepare rotation, emit P2P_CONTROL_TOWER_SUCCESSOR_PACKET with the current instance, proposed successor,",
            "snapshot sequence, canonical claim/confidence, host lanes, active execution, Owner Gates, pending/closed work,",
            "blockers/risks, critical invariants, next safe action, durable refs, and CHAT_ONLY_NOT_CANONICAL.",
            "The successor packet is compact bootstrap data: do not copy full chat history, execute Owner Gates, inherit approval,",
            "close active execution, move host lanes, invent execution, or treat the packet as canonical truth.",
            PACKET_END,
            "",
            USER_ACTION_BLOCK,
        )
    )


def load_snapshot(
    root: str | Path,
    *,
    current_canonical_base_sha: str = UNKNOWN,
    current_canonical_base_tree: str = UNKNOWN,
) -> dict[str, Any]:
    return ControlTower(
        root,
        current_canonical_base_sha=current_canonical_base_sha,
        current_canonical_base_tree=current_canonical_base_tree,
    ).snapshot()


def render_snapshot(snapshot: Mapping[str, Any]) -> str:
    if not isinstance(snapshot, Mapping):
        raise ProjectionError("CONTROL_TOWER_SNAPSHOT_REQUIRED")
    canonical = snapshot.get("CANONICAL", {})
    lines = [
        "P2P CONTROL TOWER SNAPSHOT",
        "",
        "CANONICAL",
        f"  Current base SHA: {canonical.get('CURRENT_BASE_SHA', UNKNOWN) if isinstance(canonical, Mapping) else UNKNOWN}",
        f"  Current base tree: {canonical.get('CURRENT_BASE_TREE', UNKNOWN) if isinstance(canonical, Mapping) else UNKNOWN}",
        "  Promotion: NOT_INFERRED",
        "",
        "HOST LANES",
    ]
    lanes = snapshot.get("HOST_LANES", {})
    if isinstance(lanes, Mapping) and lanes:
        for host in sorted(lanes):
            lane = lanes[host]
            if isinstance(lane, Mapping):
                lines.append(
                    f"  {host}: {lane.get('CONTROL_TOWER_STATUS', UNKNOWN)} / {lane.get('SESSION_STATE', UNKNOWN)}"
                )
    else:
        lines.append("  (none)")
    lines.extend(
        [
            "",
            "ACTIVE EXECUTION",
            f"  {len(snapshot.get('ACTIVE_EXECUTION', [])) if isinstance(snapshot.get('ACTIVE_EXECUTION', []), Sequence) else 0} active session(s)",
            "",
            "OWNER GATES",
        ]
    )
    gates = snapshot.get("OWNER_GATES", [])
    if isinstance(gates, Sequence) and not isinstance(gates, (str, bytes)) and gates:
        lines.extend(f"  {json.dumps(gate, ensure_ascii=False, sort_keys=True)}" for gate in gates)
    else:
        lines.append("  (none)")
    lines.extend(
        [
            "",
            "NEXT SAFE ACTION",
            f"  {snapshot.get('NEXT_SAFE_ACTION', {}).get('ACTION', UNKNOWN) if isinstance(snapshot.get('NEXT_SAFE_ACTION'), Mapping) else UNKNOWN}",
            "",
            "PERSISTENCE",
            "  EXISTING_EXECUTION_LEDGER_ONLY",
        ]
    )
    return "\n".join(lines)


__all__ = [
    "ATTACHMENT_CLASSIFICATIONS",
    "ATTACHMENT_MANIFEST_SCHEMA",
    "BindingError",
    "CANONICAL_RELATIONS",
    "CONTROL_TOWER_EVENT_SCHEMA",
    "CONTROL_TOWER_LEDGER_RELATIVE_PATH",
    "CONTROL_TOWER_PACKET_SCHEMA",
    "CONTROL_TOWER_PROMPT_SCHEMA",
    "CONTROL_TOWER_PROJECTION_SCHEMA",
    "CONTROL_TOWER_ROTATION_HANDOFF_SCHEMA",
    "CONTROL_TOWER_SESSION_START_EVENT_SCHEMA",
    "CONTROL_TOWER_SUCCESSOR_PACKET_SCHEMA",
    "CONTROL_TOWER_STATUSES",
    "ControlTowerAttachment",
    "ControlTowerAttachmentManifest",
    "ControlTowerHandoffError",
    "ControlTowerIngestResult",
    "ControlTowerReturnPacket",
    "ControlTowerRotationHandoff",
    "ControlTower",
    "ControlTowerState",
    "ControlTowerSuccessorPacket",
    "ControlTowerSuccessorReconciliation",
    "EXISTING_LIFECYCLE_STATE",
    "PacketParseError",
    "ProjectionError",
    "SessionBinding",
    "TERMINAL_STATES",
    "UPLOAD_MANIFEST_INSTRUCTION",
    "UPLOAD_REQUIRED_VALUES",
    "USER_ACTION_BLOCK",
    "bind_session",
    "build_execution_prompt",
    "create_return_packet",
    "load_snapshot",
    "new_session_id",
    "normalize_host",
    "next_safe_session",
    "parse_return_packet",
    "prepare_control_tower_rotation",
    "reconcile_control_tower_successor",
    "render_snapshot",
    "to_execution_ledger_event",
]
