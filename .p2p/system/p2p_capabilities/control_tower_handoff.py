"""Provider-neutral Control Tower session handoff contract.

This module is a small composition boundary over the existing P2P task,
evidence, execution-ledger, and host-executor surfaces. It does not launch a
host, select a provider, inherit chat state, write canonical truth, or approve
protected actions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any, Mapping, Sequence


CONTROL_TOWER_PACKET_SCHEMA = "p2p-control-tower-return-packet/1"
CONTROL_TOWER_PROMPT_SCHEMA = "p2p-control-tower-execution-prompt/1"
CONTROL_TOWER_EVENT_SCHEMA = "p2p-control-tower-return-event/1"
ATTACHMENT_MANIFEST_SCHEMA = "p2p-control-tower-attachment-manifest/1"

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
_HASH_PATTERN = re.compile(r"^[0-9a-fA-F]{64}$")
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


def create_return_packet(binding: SessionBinding, **values: Any) -> ControlTowerReturnPacket:
    """Construct a packet while keeping the binding explicit at the call site."""

    return ControlTowerReturnPacket(binding=binding, **values)


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


@dataclass
class ControlTowerState:
    """Durable-semantic projection over existing task/evidence/ledger state.

    The object is intentionally only a serializable projection. Callers that
    persist events must use the existing execution-ledger writer; this class
    never opens files or mutates canonical state itself.
    """

    lanes: dict[str, dict[str, Any]] = field(default_factory=dict)
    return_events: list[dict[str, Any]] = field(default_factory=list)

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
        )
        self.return_events.append(to_execution_ledger_event(packet, result))
        return result

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "p2p-control-tower-state-projection/1",
            "LANES": _safe_json(self.lanes, path="lanes"),
            "RETURN_EVENTS": _safe_json(self.return_events, path="return_events"),
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
        "CONTROL_TOWER_RETURN_PACKET": packet.to_dict(),
        "CONTROL_TOWER_RECONCILIATION": reconciliation.to_dict() if reconciliation is not None else None,
        "CANONICAL_TRUTH_UPDATED": "NO",
        "PROTECTED_ACTION_EXECUTED": "NO",
    }


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
            "SESSION_RULES:",
            "- Use the explicit HOST above as authoritative; never infer a host from narrative prose.",
            "- Do not inherit chat history, prior session state, or implicit context.",
            "- Do not promote, merge, deploy, release, or perform a protected action from this prompt.",
            "- Finish with one structured CONTROL_TOWER_RETURN_PACKET.",
            "",
            "CONTROL_TOWER_RETURN_PACKET:",
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
            "",
            USER_ACTION_BLOCK,
        )
    )


__all__ = [
    "ATTACHMENT_CLASSIFICATIONS",
    "ATTACHMENT_MANIFEST_SCHEMA",
    "CANONICAL_RELATIONS",
    "CONTROL_TOWER_EVENT_SCHEMA",
    "CONTROL_TOWER_PACKET_SCHEMA",
    "CONTROL_TOWER_PROMPT_SCHEMA",
    "CONTROL_TOWER_STATUSES",
    "ControlTowerAttachment",
    "ControlTowerAttachmentManifest",
    "ControlTowerHandoffError",
    "ControlTowerIngestResult",
    "ControlTowerReturnPacket",
    "ControlTowerState",
    "EXISTING_LIFECYCLE_STATE",
    "SessionBinding",
    "TERMINAL_STATES",
    "UPLOAD_MANIFEST_INSTRUCTION",
    "UPLOAD_REQUIRED_VALUES",
    "USER_ACTION_BLOCK",
    "bind_session",
    "build_execution_prompt",
    "create_return_packet",
    "normalize_host",
    "to_execution_ledger_event",
]
