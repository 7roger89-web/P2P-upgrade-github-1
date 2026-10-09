"""Provider-neutral Control Tower session handoff contract.

This module is a small composition boundary over the existing P2P task,
evidence, execution-ledger, and host-executor surfaces. It does not launch a
host, select a provider, inherit chat state, write canonical truth, approve
protected actions, or transfer state between Control Tower instances. A
successor packet is compact bootstrap data that must be reconciled with
durable P2P evidence.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
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
CANARY_EVIDENCE_SCHEMA = "p2p-canary-evidence-packet/1"
CANARY_EVIDENCE_EVENT_SCHEMA = "p2p-control-tower-canary-evidence/1"
CANARY_CONTINUATION_EVENT_SCHEMA = "p2p-control-tower-canary-continuation/1"
SUPREME_LAW_CANONICAL_REPO = "7roger89-web/P2P-upgrade-github-1"
SUPREME_LAW_CANONICAL_REF = "main"
SUPREME_LAW_DEVELOPMENT_PATH = "docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md"
SUPREME_LAW_INSTALLED_PATH = ".p2p/system/docs/P2P-OPERATIONS-NOTEBOOK.md"
# Compact fallback capsule aligned with the canonical P2P_SUPREME_OPERATING_LAW_V1
# supreme laws #1-#9 (docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md, section 2A).
# Exactly nine entries; each begins with the exact canonical law identifier. This
# constant must stay self-contained: build_execution_prompt() never reads the
# canonical notebook at runtime, because the capsule exists for executors that
# cannot reach it.
SUPREME_LAW_CAPSULE = "\n".join(
    (
        "1. OWNER_OUTCOME_AND_AUTHORITY_ARE_INVARIANTS — Preserve the Owner's outcome, acceptance, and authority; decide routine technical details inside approved scope; never lower acceptance or widen authority to manufacture success.",
        "2. SIMPLEST_USEFUL_PATH_TO_COMPLETION — Choose the simplest useful action that materially advances outcome, evidence, recovery, or risk reduction; do not build speculative supporting infrastructure first.",
        "3. REAL_STATE_AND_EVIDENCE_OVERRIDE_ASSUMPTIONS — Fresh-check mutable state; evidence proves only its own scope; reconcile UNKNOWN side effects before unsafe retry.",
        "4. RECOVER_ADAPTIVELY; DO_NOT_ENTER_SPECULATIVE_FIX_LOOPS — Retry according to process/failure type; diagnose root cause; change route when progress stalls; do not use ritual fixed-count retries.",
        "5. PRESERVE_CONTINUITY_AND_STOP — Retain only the durable checkpoint needed to continue and stop when the required outcome is proven.",
        "6. PROMPT_TITLE_DESTINATION_AND_PLAN_STATE_ARE_EXPLICIT — Cross-tool operational prompts state project/workstream, destination, chat mode/title, role where applicable, fresh durable plan checkpoint, and one next bounded step. Arena NEW_CHAT prompts use ARENA_CHAT_TITLE_FIRST_LINE_V1: first nonblank line is a concise human-readable <PROJECT> — <bounded task/outcome>; routing boilerplate such as GỬI CHO:, DESTINATION=, TASK_ID=, code fences, or generic P2P prefixes must not be first; CHAT_TITLE repeats the exact first-line title.",
        "7. ANALYTICAL_AUTONOMY_AND_DELEGATION_ALIGNMENT — Use analytical scepticism, top-down deconstruction plus bottom-up reconstruction, distinguish evidence/inference when material, prefer root-cause repair, and rewrite delegation prompts that could drift from the Owner outcome.",
        "8. TASK_CONTRACT_AND_ACCEPTANCE_FIDELITY — Bind objective, scope, representative scenario/quality invariant where relevant, observable acceptance, evidence class, failure/blocker criteria, and stop condition; never promote local/mock/proxy evidence to live/business/visual/official PASS without representative proof; reuse authoritative existing components first.",
        "9. EXECUTOR_INPUT_FORMAT_AND_ARTIFACT_TRANSPORT_FIDELITY — Verify destination input capability before handoff; prefer direct lossless transport when supported, otherwise the simplest trustworthy reversible transport; never spoof MIME/extensions or disguise semantic conversion; when artifact identity matters verify reconstructed byte size and SHA-256 before use; transport never expands authority or bypasses security/privacy/Owner Gates.",
    )
)
UNKNOWN = "UNKNOWN"

# --- Arena FAST_CANARY runtime enforcement (MODEL_CANARY_GATE_V1) ------------
# These constants make the existing canonical gate executable inside the
# existing Control Tower prompt/session lifecycle. They add no router,
# scheduler, daemon, benchmark service, score database, or second state store:
# the canary decision is derived from the explicit host label, an explicit
# Control Tower low-risk/mechanical declaration, and durable Control Tower state
# in the existing execution ledger.
MODEL_CANARY_GATE_V1 = "MODEL_CANARY_GATE_V1"
OWNER_CONTINUATION_GATE_V1 = "OWNER_CONTINUATION_GATE_V1"
CANARY_EVIDENCE_HEADER = "CANARY_EVIDENCE_PACKET_V1"
CANARY_REQUIRED_HOST = "ARENA"
CANARY_SESSION_QUALITY_ESTABLISHED = "ESTABLISHED"
CANARY_SESSION_QUALITY_UNKNOWN = "UNKNOWN"
# The free-text seams (Control Tower ``start`` and Owner ``/goal``) carry no
# structured TaskProfile or mutation class, so no existing authoritative P2P
# risk signal is usable here. The smallest conservative rule is therefore
# binary: an explicit Control Tower LOW_RISK_MECHANICAL declaration bypasses the
# canary; everything else fails closed into MEDIUM_OR_HIGH_RISK. No task-text
# classifier or parallel risk taxonomy is maintained.
LOW_RISK_MECHANICAL = "LOW_RISK_MECHANICAL"
MEDIUM_OR_HIGH_RISK = "MEDIUM_OR_HIGH_RISK"
RISK_CLASSES = (LOW_RISK_MECHANICAL, MEDIUM_OR_HIGH_RISK)
# One unambiguous first-turn return contract for a triggered canary session.
FIRST_TURN_RETURN_CONTRACT = "CANARY_EVIDENCE_PACKET_V1_THEN_STOP"
CANARY_CLASSIFICATIONS = ("GREEN", "YELLOW", "ORANGE", "RED", "UNVERIFIED")
CANARY_SESSION_POLICIES = {
    "GREEN": "KEEP_SESSION",
    "YELLOW": "LIMIT_SESSION",
    "ORANGE": "ADVISORY_OR_LOW_RISK_ONLY",
    "RED": "REROLL_OR_SWITCH_EXECUTOR",
    "UNVERIFIED": "NO_DEFAULT_CONTINUATION",
}
CANARY_CONTINUATION_RECOMMENDATIONS = {
    "GREEN": "CONTINUE_REAL_TASK_IN_SAME_SESSION_AFTER_OWNER_CONTINUATION",
    "YELLOW": "CONTINUE_LIMITED_WITH_DECLARED_VERIFICATION_BOUND",
    "ORANGE": "ADVISORY_OR_LOW_RISK_ONLY",
    "RED": "REROLL_OR_SWITCH_EXECUTOR_NO_KEEP_WORKING",
    "UNVERIFIED": "NO_DEFAULT_CONTINUATION",
}
# A tested executor must never authoritatively emit its own grade or session
# policy. Presence of any of these as an executor-authored classification is a
# canary contract violation.
EXECUTOR_SELF_CLASSIFICATION_FORBIDDEN = (
    "GREEN",
    "YELLOW",
    "ORANGE",
    "RED",
    "KEEP_SESSION",
    "LIMIT_SESSION",
    "REROLL",
    "REROLL_OR_SWITCH_EXECUTOR",
    "ADVISORY_OR_LOW_RISK_ONLY",
    "NO_DEFAULT_CONTINUATION",
)
CANARY_EVIDENCE_FIELDS = (
    "P2P_LAW_SOURCE",
    "CURRENT_STATE",
    "FACTS",
    "DECISIVE_CHECK",
    "CHECK_RESULT",
    "ERRORS_ENCOUNTERED",
    "RECOVERY_ACTIONS",
    "DURABLE_MUTATION_CREATED",
    "MODEL_IDENTITY",
)
CANARY_EVIDENCE_REQUIRED_FIELDS = (
    "P2P_LAW_SOURCE",
    "CURRENT_STATE",
    "DECISIVE_CHECK",
    "CHECK_RESULT",
    "DURABLE_MUTATION_CREATED",
    "MODEL_IDENTITY",
)
CANARY_CHECKPOINT_FIELDS = (
    "CONTINUATION_CHECKPOINT=READY",
    "OWNER_ACTION_REQUIRED=YES",
    "NATIVE_ACTION_HINT=KEEP_WORKING_IF_APPROVED",
    "FALLBACK_OWNER_REPLY=Tiếp tục công việc",
)
FALLBACK_OWNER_REPLY = "Tiếp tục công việc"
# Existing execution-ledger event types read by the Control Tower. The canary
# phase adds exactly two: the externally graded canary turn and the recorded
# Owner continuation decision.
CONTROL_TOWER_EVENT_TYPES = (
    "CONTROL_TOWER_SESSION_STARTED",
    "CONTROL_TOWER_RETURN_PACKET",
    "CONTROL_TOWER_CANARY_EVIDENCE",
    "CONTROL_TOWER_CANARY_CONTINUATION",
)
# Executor terminal conclusions that are past the canary stop boundary.
CANARY_TERMINAL_CONCLUSION_STATES = ("COMPLETED", "FAILED", "ABORTED")
# Deterministic prompt-budget floor for required canary context: the Control
# Tower prompt budget must never be smaller than this, otherwise the mandatory
# FAST_CANARY context could not fit and generation would fail closed on every
# triggered Arena session.
CANARY_PROMPT_BUDGET_GUARD_CHARS = 12000
# One Control Tower execution prompt is a single ledger string value. The
# durable-value cap must stay above the prompt budget so required canary context
# is neither rejected nor silently truncated when the event is persisted.
MAX_LEDGER_STRING_CHARS = 16384

_CHECK_RESULT_FAILURE_PATTERN = re.compile(
    r"\b(fail\w*|error\w*|mismatch\w*|reject\w*|broken|exit[_ ]?code[=: ]*[1-9]|non[- ]zero|"
    r"not[_ ]pass\w*|unverified|unknown)\b",
    re.I,
)
_CHECK_RESULT_PASS_PATTERN = re.compile(r"\b(pass\w*|ok|success\w*|exit[_ ]?code[=: ]*0)\b", re.I)
_CANARY_EVIDENCE_LINE = re.compile(r"^([A-Z][A-Z0-9_]{2,63})=(.*)$")
_SELF_CLASSIFICATION_KEY = re.compile(r"(classif|grade|score|self|verdict|session[_ ]?policy|keep|reroll)", re.I)

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
        if len(value) > MAX_LEDGER_STRING_CHARS or _SECRET_VALUE_PATTERN.search(value):
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


# --- MODEL_CANARY_GATE_V1 executable runtime --------------------------------
# Deterministic risk classification reuses the existing P2P risk-class taxonomy
# (LOW / MODERATE / CROSS_SUBSYSTEM / SECURITY / ARCHITECTURE) so no new
# scoring, ranking, or benchmark subsystem is introduced.


@dataclass(frozen=True)
class CanaryDirective:
    """The executable FAST_CANARY directive for one Arena session.

    ``original_task`` is the durable real bounded task that must be restored
    from Control Tower state after external grading plus Owner continuation.
    It is never reconstructed from chat memory.
    """

    host: str
    session_id: str
    goal_id: str
    goal: str
    original_task: str
    risk_class: str = MEDIUM_OR_HIGH_RISK
    task_id: str = UNKNOWN
    session_quality: str = CANARY_SESSION_QUALITY_UNKNOWN
    model_identity: str = UNKNOWN
    durable_mutation_allowed: str = "NO"
    stop_after_canary: str = "YES"
    gate: str = MODEL_CANARY_GATE_V1
    owner_continuation_gate: str = OWNER_CONTINUATION_GATE_V1

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": CANARY_EVIDENCE_SCHEMA,
            "GATE": self.gate,
            "HOST": self.host,
            "SESSION_ID": self.session_id,
            "GOAL_ID": self.goal_id,
            "GOAL": self.goal,
            "TASK_ID": self.task_id,
            "ORIGINAL_TASK": self.original_task,
            "RISK_CLASS": self.risk_class,
            "SESSION_QUALITY": self.session_quality,
            "FAST_CANARY_REQUIRED": "YES",
            "REAL_TASK_FIRST_SLICE": "CANARY",
            "CANARY_DURABLE_MUTATION_ALLOWED": self.durable_mutation_allowed,
            "STOP_AFTER_CANARY": self.stop_after_canary,
            "EXECUTOR_SELF_CLASSIFICATION": "FORBIDDEN",
            "MODEL_IDENTITY": self.model_identity,
            "OWNER_CONTINUATION_GATE": self.owner_continuation_gate,
            "CANARY_CLASSIFIER": "CONTROL_TOWER_OR_INDEPENDENT_VERIFIER",
            "CONTINUATION_CHECKPOINT": "READY",
            "OWNER_ACTION_REQUIRED": "YES",
            "NATIVE_ACTION_HINT": "KEEP_WORKING_IF_APPROVED",
            "FALLBACK_OWNER_REPLY": FALLBACK_OWNER_REPLY,
        }

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "CanaryDirective":
        if not isinstance(value, Mapping):
            raise ControlTowerHandoffError("CANARY_DIRECTIVE_REQUIRED")
        return cls(
            host=str(value.get("HOST") or CANARY_REQUIRED_HOST),
            session_id=str(value.get("SESSION_ID") or UNKNOWN),
            goal_id=str(value.get("GOAL_ID") or UNKNOWN),
            goal=str(value.get("GOAL") or UNKNOWN),
            original_task=str(value.get("ORIGINAL_TASK") or value.get("GOAL") or UNKNOWN),
            risk_class=str(value.get("RISK_CLASS") or MEDIUM_OR_HIGH_RISK),
            task_id=str(value.get("TASK_ID") or UNKNOWN),
            session_quality=str(value.get("SESSION_QUALITY") or CANARY_SESSION_QUALITY_UNKNOWN),
            model_identity=str(value.get("MODEL_IDENTITY") or UNKNOWN),
            durable_mutation_allowed=str(value.get("CANARY_DURABLE_MUTATION_ALLOWED") or "NO"),
            stop_after_canary=str(value.get("STOP_AFTER_CANARY") or "YES"),
        )


def canary_prompt_lines(directive: CanaryDirective) -> tuple[str, ...]:
    """Serialize the FAST_CANARY directive into executable prompt context."""

    if not isinstance(directive, CanaryDirective):
        raise ControlTowerHandoffError("CANARY_DIRECTIVE_REQUIRED")
    return (
        "FAST_CANARY (MODEL_CANARY_GATE_V1 + OWNER_CONTINUATION_GATE_V1):",
        "This Arena session is NEW and its session quality is materially unproven, so the",
        "first safe real-task slice IS the canary. The real bounded task is preserved below and",
        "in durable Control Tower state; it is restored only after external grading plus explicit",
        "Owner continuation. Do not reconstruct it from chat memory.",
        "",
        "FAST_CANARY_REQUIRED=YES",
        "REAL_TASK_FIRST_SLICE=CANARY",
        f"CANARY_DURABLE_MUTATION_ALLOWED={directive.durable_mutation_allowed}",
        f"STOP_AFTER_CANARY={directive.stop_after_canary}",
        "EXECUTOR_SELF_CLASSIFICATION=FORBIDDEN",
        f"MODEL_IDENTITY={directive.model_identity}",
        f"RISK_CLASS={directive.risk_class}",
        f"SESSION_QUALITY={directive.session_quality}",
        f"OWNER_CONTINUATION_GATE={directive.owner_continuation_gate}",
        "CANARY_CLASSIFIER=CONTROL_TOWER_OR_INDEPENDENT_VERIFIER",
        "",
        "ORIGINAL_REAL_TASK (bounded goal preserved for continuation):",
        directive.original_task,
        "",
        "CANARY EXECUTION RULES:",
        "- Perform exactly ONE first safe real-task slice: the smallest read-only or disposable",
        "  probe of the real task above that materially answers whether this session can do the work.",
        "- Do not create durable commits, branches, PRs, remote writes, deployments, or protected",
        "  actions for the canary. Disposable scratch edits and focused checks are allowed.",
        "- Stop after that one decisive probe. Do not sweep budgets, re-run broad investigations,",
        "  or continue toward a terminal technical conclusion in this turn.",
        "- Judge nothing yourself. You MUST NOT emit GREEN, YELLOW, ORANGE, RED, KEEP_SESSION,",
        "  LIMIT_SESSION, or REROLL; that classification belongs to Control Tower or another",
        "  independent verifier.",
        "- Do not infer or claim a hidden model, provider, or reasoning level; MODEL_IDENTITY=UNKNOWN.",
        "",
        f"FIRST_TURN_RETURN_CONTRACT={FIRST_TURN_RETURN_CONTRACT}",
        "CANARY_EVIDENCE_PACKET_V1 is the ONLY return of this turn (return exactly this shape, then stop):",
        "CANARY_EVIDENCE_PACKET_V1",
        "P2P_LAW_SOURCE=<actual source; INLINE_SUPREME_LAW_CAPSULE allowed>",
        "LAW_CHECK=PASS | SOURCE=<actual source> | SOURCE_SHA256=<canonical SHA256 from CONTROL_TOWER_SELF_LAW_RECEIPT>",
        "Inline capsule => PASS with that canonical SHA256; never claim repo-file read. Else LAW_CHECK=BLOCKED | REASON=<reason>.",
        "EXPERIENCE_CHECK=USE_ACTIVE_EXPERIENCE | IDS=<experience_id,...>",
        "or EXPERIENCE_CHECK=NO_MATCH or EXPERIENCE_CHECK=UNAVAILABLE",
        "CURRENT_STATE=<pinned repo/task state>",
        "FACTS=<max 5 task-relevant observed facts>",
        "DECISIVE_CHECK=<one representative real check>",
        "CHECK_RESULT=<actual result/exit/status>",
        "ERRORS_ENCOUNTERED=<brief or NONE>",
        "RECOVERY_ACTIONS=<brief or NONE>",
        "DURABLE_MUTATION_CREATED=NO",
        "MODEL_IDENTITY=UNKNOWN",
        "",
        "END OF CANARY TURN — checkpoint metadata (not a self-grade):",
        *CANARY_CHECKPOINT_FIELDS,
        "",
        "After you stop, Control Tower ingests this evidence, grades the session externally, and",
        "the Owner decides continuation. Do not continue the original task in this turn.",
    )


def canary_resumed_task_pointer_lines() -> tuple[str, ...]:
    """Deferred pointer that replaces the terminal return contract in a canary turn."""

    return (
        "RESUMED_TASK_RETURN_CONTRACT=SUPPLIED_BY_CONTROL_TOWER_AT_OWNER_CONTINUATION",
        "The terminal return contract for the ORIGINAL_REAL_TASK is not part of this turn: after",
        "external GREEN plus explicit Owner continuation, Control Tower supplies it for this SAME session.",
    )


def canary_requirement(
    host: Any,
    *,
    session_quality: str = CANARY_SESSION_QUALITY_UNKNOWN,
    session_action: str | None = None,
    low_risk_mechanical: bool = False,
) -> dict[str, Any]:
    """Decide whether FAST_CANARY is required for one generated session.

    Fail-closed order: non-Arena executors bypass; an existing-session
    continuation does not re-canary; an explicit Control Tower
    LOW_RISK_MECHANICAL declaration bypasses; a session whose quality is already
    durably established for the same bounded goal does not re-canary; every
    other NEW Arena session is treated as MEDIUM_OR_HIGH_RISK and canaries.
    Task text is never classified here.
    """

    normalized_host = str(host or "").strip().upper().replace("-", "_")
    resolved_risk = LOW_RISK_MECHANICAL if low_risk_mechanical is True else MEDIUM_OR_HIGH_RISK
    decision = {
        "GATE": MODEL_CANARY_GATE_V1,
        "HOST": normalized_host or UNKNOWN,
        "RISK_CLASS": resolved_risk,
        "RISK_DECISION": (
            "EXPLICIT_CONTROL_TOWER_DECLARATION"
            if resolved_risk == LOW_RISK_MECHANICAL
            else "FAIL_CLOSED_NOT_DECLARED_LOW_RISK_MECHANICAL"
        ),
        "SESSION_QUALITY": str(session_quality or CANARY_SESSION_QUALITY_UNKNOWN).upper(),
        "FAST_CANARY_REQUIRED": "NO",
        "REASON": UNKNOWN,
        "SESSION_ACTION": str(session_action or UNKNOWN),
    }
    if normalized_host != CANARY_REQUIRED_HOST:
        decision["REASON"] = "NON_ARENA_EXECUTOR"
        return decision
    if str(session_action or "").upper() == "CONTINUE_CURRENT_SESSION":
        decision["REASON"] = "EXISTING_SESSION_CONTINUATION"
        return decision
    if resolved_risk == LOW_RISK_MECHANICAL:
        decision["REASON"] = "LOW_RISK_MECHANICAL_ARENA_TASK"
        return decision
    if decision["SESSION_QUALITY"] == CANARY_SESSION_QUALITY_ESTABLISHED:
        decision["REASON"] = "SESSION_QUALITY_ALREADY_ESTABLISHED"
        return decision
    decision["FAST_CANARY_REQUIRED"] = "YES"
    decision["REASON"] = "NEW_ARENA_SESSION_MEDIUM_OR_HIGH_RISK_SESSION_QUALITY_UNKNOWN"
    decision["REAL_TASK_FIRST_SLICE"] = "CANARY"
    decision["CANARY_DURABLE_MUTATION_ALLOWED"] = "NO"
    decision["STOP_AFTER_CANARY"] = "YES"
    decision["EXECUTOR_SELF_CLASSIFICATION"] = "FORBIDDEN"
    decision["FIRST_TURN_RETURN_CONTRACT"] = FIRST_TURN_RETURN_CONTRACT
    decision["MODEL_IDENTITY"] = UNKNOWN
    return decision


def parse_canary_evidence_packet(response_text: Any) -> dict[str, Any] | None:
    """Parse a CANARY_EVIDENCE_PACKET_V1 block from an executor response."""

    text = str(response_text or "")
    lines = text.splitlines()
    header_index = None
    for index, line in enumerate(lines):
        if line.strip().upper().startswith(CANARY_EVIDENCE_HEADER):
            header_index = index
            break
    if header_index is None:
        return None
    fields: dict[str, str] = {}
    order: list[str] = []
    for line in lines[header_index + 1 :]:
        stripped = line.strip()
        if not stripped:
            if fields:
                break
            continue
        match = _CANARY_EVIDENCE_LINE.match(stripped)
        if match is None:
            if fields:
                break
            continue
        key, value = match.group(1), match.group(2).strip()
        if key not in fields:
            order.append(key)
        fields[key] = value
    if not fields:
        return None
    return {"schema": CANARY_EVIDENCE_SCHEMA, "FIELDS": fields, "FIELD_ORDER": tuple(order)}


def _canary_self_classification_violation(fields: Mapping[str, Any]) -> str | None:
    for key, value in fields.items():
        normalized = str(value or "").strip().upper()
        if _SELF_CLASSIFICATION_KEY.search(key) and normalized in EXECUTOR_SELF_CLASSIFICATION_FORBIDDEN:
            return f"{key}={normalized}"
    return None


def classify_canary_evidence(
    evidence: Mapping[str, Any] | None,
    *,
    return_packet: Any = None,
    response_text: Any = None,
) -> dict[str, Any]:
    """Externally grade one canary return using deterministic existing policy.

    The tested executor never grades itself. Control Tower (or an independent
    verifier) grades externally observable evidence only. When independent
    verification is unavailable the result is UNVERIFIED, never implicit GREEN.
    """

    fields: dict[str, Any] = {}
    if isinstance(evidence, Mapping):
        raw_fields = evidence.get("FIELDS")
        fields = dict(raw_fields) if isinstance(raw_fields, Mapping) else dict(evidence)
    session_state = ""
    if return_packet is not None:
        session_state = str(getattr(return_packet, "session_state", "") or "").upper()

    def _result(classification: str, reasons: tuple[str, ...]) -> dict[str, Any]:
        return {
            "GATE": MODEL_CANARY_GATE_V1,
            "CLASSIFICATION": classification,
            "SESSION_POLICY": CANARY_SESSION_POLICIES[classification],
            "CONTINUATION_RECOMMENDATION": CANARY_CONTINUATION_RECOMMENDATIONS[classification],
            "REASONS": list(reasons),
            "EXECUTOR_SELF_CLASSIFICATION": "FORBIDDEN",
            "CANARY_CLASSIFIER": "CONTROL_TOWER_OR_INDEPENDENT_VERIFIER",
            "OWNER_CONTINUATION_REQUIRED": "YES" if classification == "GREEN" else "NO",
            "MODEL_IDENTITY": str(fields.get("MODEL_IDENTITY") or UNKNOWN),
        }

    if not fields:
        # Live regression shape: a canary session that keeps investigating and
        # returns a terminal conclusion without the evidence packet.
        if session_state in CANARY_TERMINAL_CONCLUSION_STATES:
            return _result(
                "RED",
                ("CANARY_EVIDENCE_PACKET_MISSING_AFTER_TERMINAL_CONCLUSION",),
            )
        return _result("UNVERIFIED", ("CANARY_EVIDENCE_PACKET_MISSING",))

    self_grade = _canary_self_classification_violation(fields)
    if self_grade is not None:
        return _result("RED", (f"EXECUTOR_SELF_CLASSIFICATION_FORBIDDEN:{self_grade}",))

    # A terminal technical conclusion in the canary turn means the executor ran
    # past the first safe probe, even when an evidence packet is attached.
    if session_state in CANARY_TERMINAL_CONCLUSION_STATES:
        return _result("RED", ("CANARY_STOP_BOUNDARY_VIOLATION:TERMINAL_CONCLUSION_IN_CANARY_TURN",))

    missing = [name for name in CANARY_EVIDENCE_REQUIRED_FIELDS if not str(fields.get(name) or "").strip()]
    if missing:
        return _result("UNVERIFIED", (f"CANARY_EVIDENCE_INCOMPLETE:{','.join(missing)}",))

    if str(fields.get("DURABLE_MUTATION_CREATED") or "").strip().upper() == "YES":
        return _result("RED", ("CANARY_DURABLE_MUTATION_BOUNDARY_VIOLATED",))

    response = str(response_text or "")
    checkpoint_missing = [
        token
        for token in CANARY_CHECKPOINT_FIELDS
        if token not in response and token.split("=", 1)[0] not in fields
    ]
    if checkpoint_missing:
        return _result("RED", (f"CANARY_STOP_BOUNDARY_VIOLATION:{','.join(checkpoint_missing)}",))

    check_result = str(fields.get("CHECK_RESULT") or "").strip()
    errors = str(fields.get("ERRORS_ENCOUNTERED") or "").strip()
    recovery = str(fields.get("RECOVERY_ACTIONS") or "").strip()
    recovered = bool(recovery) and recovery.upper() not in {"NONE", "UNKNOWN", "N/A"}
    identity = str(fields.get("MODEL_IDENTITY") or "").strip().upper()

    if not check_result or check_result.upper() in {"UNKNOWN", "NONE", "N/A"}:
        return _result("ORANGE", ("CANARY_DECISIVE_CHECK_RESULT_UNKNOWN",))

    if _CHECK_RESULT_FAILURE_PATTERN.search(check_result) and not _CHECK_RESULT_PASS_PATTERN.search(check_result):
        if recovered:
            return _result("YELLOW", ("CANARY_CHECK_FAILED_THEN_RECOVERED",))
        return _result("RED", ("CANARY_CHECK_FAILED_WITHOUT_RECOVERY",))

    if errors and errors.upper() != "NONE":
        return _result("YELLOW", ("CANARY_ERRORS_ENCOUNTERED_WITH_RECOVERY" if recovered else "CANARY_ERRORS_WITHOUT_RECOVERY",))

    if identity not in {"", UNKNOWN}:
        return _result("YELLOW", ("MODEL_IDENTITY_SELF_REPORT_IS_NOT_EVIDENCE",))

    return _result("GREEN", ("CANARY_PROBE_PASSED_WITHOUT_MATERIAL_WEAKNESS",))


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
    law_check: Mapping[str, Any] | None = None
    learning_reconciliation: Mapping[str, Any] | None = None
    experience_check: Mapping[str, Any] | None = None
    skill_consumption_receipt: Mapping[str, Any] | None = None

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
        if self.skill_consumption_receipt is not None:
            if not isinstance(self.skill_consumption_receipt, Mapping):
                raise ControlTowerHandoffError(
                    "SKILL_CONSUMPTION_RECEIPT_MUST_BE_OBJECT"
                )
            object.__setattr__(
                self,
                "skill_consumption_receipt",
                _safe_json(
                    self.skill_consumption_receipt,
                    path="skill_consumption_receipt",
                ),
            )

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
        if self.law_check is not None:
            result["LAW_CHECK"] = _safe_json(self.law_check, path="law_check")
        if self.learning_reconciliation is not None:
            result["LEARNING_RECONCILIATION"] = _safe_json(self.learning_reconciliation, path="learning_reconciliation")
        if self.experience_check is not None:
            result["EXPERIENCE_CHECK"] = _safe_json(self.experience_check, path="experience_check")
        if self.skill_consumption_receipt is not None:
            result["SKILL_CONSUMPTION_RECEIPT"] = _safe_json(
                self.skill_consumption_receipt,
                path="skill_consumption_receipt",
            )
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
            law_check=value.get("LAW_CHECK"),
            learning_reconciliation=value.get("LEARNING_RECONCILIATION"),
            experience_check=value.get("EXPERIENCE_CHECK"),
            skill_consumption_receipt=value.get("SKILL_CONSUMPTION_RECEIPT"),
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


def _parse_law_check_dict_or_str(val: Any) -> dict[str, Any] | None:
    if isinstance(val, Mapping):
        status = str(val.get("status") or "").upper()
        if status in ("PASS", "BLOCKED", "INVALID", "MISSING", "CONTRADICTORY"):
            return dict(val)
        return {"status": "INVALID", "reason": "UNKNOWN_STATUS"}
    if not isinstance(val, str):
        return None
    raw = val.strip()
    if not re.match(r"(?i)^\s*LAW_CHECK\s*=", raw):
        return None
    directives = list(re.finditer(r"(?i)\bLAW_CHECK\s*=", raw))
    if len(directives) != 1:
        return {"status": "INVALID", "reason": "REPEATED_LAW_CHECK_DIRECTIVE"}
    m = re.match(r"(?im)^\s*LAW_CHECK\s*=\s*(PASS|BLOCKED)\b(.*)$", raw)
    if not m:
        return {"status": "INVALID", "reason": "MALFORMED_LAW_CHECK"}
    verdict, rest = m.group(1).upper(), m.group(2).strip()
    if verdict == "BLOCKED":
        rm = re.search(r"REASON\s*=\s*([^|;\n]+)", rest)
        return {"status": "BLOCKED", "reason": (rm.group(1).strip() if rm else rest) or "EXECUTOR_BLOCKED"}
    source_fields = list(re.finditer(r"(?i)\bSOURCE\s*=\s*([^|;\n]*)", rest))
    sha_fields = list(re.finditer(r"(?i)\bSOURCE_SHA256\s*=\s*([^|;\n]*)", rest))
    if len(source_fields) != 1:
        return {"status": "INVALID", "reason": "SOURCE_FIELD_DUPLICATED_OR_MISSING"}
    if len(sha_fields) != 1:
        return {"status": "INVALID", "reason": "SOURCE_SHA256_FIELD_DUPLICATED_OR_MISSING"}
    source = source_fields[0].group(1).strip()
    source_sha = sha_fields[0].group(1).strip()
    if not source or re.fullmatch(r"[0-9a-fA-F]{64}", source_sha) is None:
        return {"status": "INVALID", "reason": "SOURCE_OR_SHA256_MISSING_OR_INVALID"}
    return {"status": "PASS", "source": source, "source_sha256": source_sha.lower()}


def _parse_experience_check_dict_or_str(val: Any) -> dict[str, Any] | None:
    if isinstance(val, Mapping):
        dec = str(val.get("decision") or val.get("EXPERIENCE_CHECK") or "").upper()
        if dec in ("USE_ACTIVE_EXPERIENCE", "NO_MATCH", "UNAVAILABLE", "BLOCKED"):
            ids = val.get("ids") or val.get("IDS") or []
            if isinstance(ids, str):
                ids = [i.strip() for i in ids.split(",") if i.strip()]
            return {"decision": dec, "ids": list(ids), "reason": str(val.get("reason", ""))}
        return {"decision": "INVALID", "raw": dict(val)}
    if not isinstance(val, str):
        return None
    raw = val.strip()
    if not re.match(r"(?i)^\s*EXPERIENCE_CHECK\s*=", raw):
        return None
    directives = list(re.finditer(r"(?i)\bEXPERIENCE_CHECK\s*=", raw))
    if len(directives) != 1:
        return {"decision": "INVALID", "reason": "REPEATED_EXPERIENCE_CHECK_DIRECTIVE"}
    m = re.match(r"(?im)^\s*EXPERIENCE_CHECK\s*=\s*(USE_ACTIVE_EXPERIENCE|NO_MATCH|UNAVAILABLE|BLOCKED)\b(.*)$", raw)
    if not m:
        return {"decision": "INVALID", "raw": raw}
    dec, rest = m.group(1).upper(), m.group(2).strip()
    if dec == "USE_ACTIVE_EXPERIENCE":
        id_fields = list(re.finditer(r"(?i)\bIDS?\s*=\s*([^|;\n]*)", rest))
        if len(id_fields) != 1:
            return {"decision": "INVALID", "reason": "IDS_FIELD_DUPLICATED_OR_MISSING"}
        ids_value = id_fields[0].group(1).strip()
        if not ids_value:
            return {"decision": "INVALID", "reason": "IDS_VALUE_MISSING"}
        ids = [i.strip() for i in ids_value.split(",") if i.strip()]
        if not ids:
            return {"decision": "INVALID", "reason": "IDS_VALUE_MISSING"}
        return {"decision": "USE_ACTIVE_EXPERIENCE", "ids": ids}
    elif dec == "NO_MATCH":
        return {"decision": "NO_MATCH", "ids": []}
    elif dec in ("UNAVAILABLE", "BLOCKED"):
        rm = re.search(r"REASON\s*=\s*([^|;\n]+)", rest)
        return {"decision": dec, "reason": rm.group(1).strip() if rm else dec, "ids": []}
    return {"decision": "INVALID", "raw": raw}


def _parse_learning_dict_or_str(val: Any) -> dict[str, Any] | None:
    if isinstance(val, Mapping):
        ltype = str(val.get("type") or val.get("LEARNING_RECONCILIATION") or "").upper()
        if ltype in ("NONE", "CANDIDATE"):
            return {"type": ltype, "reason": str(val.get("reason", ""))}
        return {"type": "INVALID", "raw": dict(val)}
    if not isinstance(val, str):
        return None
    raw = val.strip()
    m = re.match(r"(?im)^\s*LEARNING_RECONCILIATION\s*=\s*(NONE|CANDIDATE)\b(.*)$", raw)
    if not m:
        return None
    ltype, rest = m.group(1).upper(), m.group(2).strip()
    rm = re.search(r"REASON\s*=\s*([^|;\n]+)", rest)
    return {"type": ltype, "reason": rm.group(1).strip() if rm else ""}


def _extract_executor_receipts(
    final_response: str,
    payload: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Extract and parse actor-own LAW_CHECK, EXPERIENCE_CHECK, and LEARNING_RECONCILIATION receipts."""

    # 1. LAW_CHECK
    narrative_lc_list: list[dict[str, Any]] = []
    for line in final_response.splitlines():
        if "CONTROL_TOWER_SELF_LAW_RECEIPT" in line or "ACTOR=CONTROL_TOWER_SELF" in line:
            continue
        parsed = _parse_law_check_dict_or_str(line)
        if parsed is not None:
            narrative_lc_list.append(parsed)

    narrative_lc: dict[str, Any] | None = None
    if narrative_lc_list:
        first = narrative_lc_list[0]
        if any(p != first for p in narrative_lc_list):
            narrative_lc = {"status": "CONTRADICTORY", "count": len(narrative_lc_list)}
        else:
            narrative_lc = first

    payload_lc = _parse_law_check_dict_or_str(payload.get("LAW_CHECK"))

    law_check: dict[str, Any]
    if payload_lc is None and narrative_lc is None:
        law_check = {"status": "MISSING"}
    elif payload_lc is None:
        law_check = narrative_lc
    elif narrative_lc is None:
        law_check = payload_lc
    else:
        p_status = payload_lc.get("status")
        n_status = narrative_lc.get("status")
        if p_status != n_status:
            law_check = {"status": "CONTRADICTORY", "reason": "CROSS_SURFACE_STATUS_MISMATCH"}
        elif p_status == "PASS":
            p_sha = str(payload_lc.get("source_sha256", "")).lower()
            n_sha = str(narrative_lc.get("source_sha256", "")).lower()
            p_src = str(payload_lc.get("source", "")).strip()
            n_src = str(narrative_lc.get("source", "")).strip()
            if p_sha != n_sha or p_src != n_src:
                law_check = {"status": "CONTRADICTORY", "reason": "CROSS_SURFACE_PASS_DETAIL_MISMATCH"}
            else:
                law_check = payload_lc
        else:
            law_check = payload_lc

    # 2. EXPERIENCE_CHECK
    narrative_ec_list: list[dict[str, Any]] = []
    for line in final_response.splitlines():
        parsed = _parse_experience_check_dict_or_str(line)
        if parsed is not None:
            narrative_ec_list.append(parsed)

    narrative_ec: dict[str, Any] | None = None
    if len(narrative_ec_list) > 1:
        narrative_ec = {
            "decision": "CONTRADICTORY",
            "reason": "REPEATED_EXPERIENCE_CHECK_DIRECTIVE",
            "count": len(narrative_ec_list),
        }
    elif narrative_ec_list:
        narrative_ec = narrative_ec_list[0]

    payload_ec = _parse_experience_check_dict_or_str(payload.get("EXPERIENCE_CHECK"))

    experience_check: dict[str, Any]
    if payload_ec is None and narrative_ec is None:
        experience_check = {"decision": "MISSING"}
    elif payload_ec is None:
        experience_check = narrative_ec
    elif narrative_ec is None:
        experience_check = payload_ec
    else:
        p_dec = payload_ec.get("decision")
        n_dec = narrative_ec.get("decision")
        if p_dec != n_dec:
            experience_check = {"decision": "CONTRADICTORY", "reason": "CROSS_SURFACE_DECISION_MISMATCH"}
        elif p_dec == "USE_ACTIVE_EXPERIENCE":
            p_ids = set(payload_ec.get("ids") or [])
            n_ids = set(narrative_ec.get("ids") or [])
            if p_ids != n_ids:
                experience_check = {"decision": "CONTRADICTORY", "reason": "CROSS_SURFACE_IDS_MISMATCH"}
            else:
                experience_check = payload_ec
        else:
            experience_check = payload_ec

    # 3. LEARNING_RECONCILIATION
    narrative_lr_list: list[dict[str, Any]] = []
    for line in final_response.splitlines():
        parsed = _parse_learning_dict_or_str(line)
        if parsed is not None:
            narrative_lr_list.append(parsed)

    narrative_lr: dict[str, Any] | None = None
    if narrative_lr_list:
        first_lr = narrative_lr_list[0]
        if any(l != first_lr for l in narrative_lr_list):
            narrative_lr = {"type": "CONTRADICTORY", "count": len(narrative_lr_list)}
        else:
            narrative_lr = first_lr

    payload_lr = _parse_learning_dict_or_str(payload.get("LEARNING_RECONCILIATION"))

    learning: dict[str, Any]
    if payload_lr is None and narrative_lr is None:
        learning = {"type": "MISSING"}
    elif payload_lr is None:
        learning = narrative_lr
    elif narrative_lr is None:
        learning = payload_lr
    else:
        p_type = payload_lr.get("type")
        n_type = narrative_lr.get("type")
        if p_type != n_type:
            learning = {"type": "CONTRADICTORY", "reason": "CROSS_SURFACE_TYPE_MISMATCH"}
        else:
            learning = payload_lr

    return law_check, experience_check, learning


def _validate_executor_receipts(
    law_check: Mapping[str, Any] | None,
    experience_check: Mapping[str, Any] | None,
    *,
    expected_law_sha: str | None = None,
    expected_experience_ids: Sequence[str] = (),
) -> tuple[list[str], bool]:
    """Apply the existing actor-receipt semantics to terminal and canary returns."""

    blockers: list[str] = []
    law_blocked = False
    lc = law_check if isinstance(law_check, Mapping) else {"status": "MISSING"}
    law_status = str(lc.get("status") or "MISSING").upper()
    if law_status == "MISSING":
        blockers.append("EXECUTOR_LAW_CHECK_MISSING")
    elif law_status == "CONTRADICTORY":
        blockers.append("EXECUTOR_LAW_CHECK_CONTRADICTORY")
    elif law_status == "INVALID":
        blockers.append("EXECUTOR_LAW_CHECK_INVALID")
    elif law_status == "BLOCKED":
        blockers.append("EXECUTOR_LAW_CHECK_BLOCKED")
        law_blocked = True
    elif law_status == "PASS":
        source = str(lc.get("source") or "").strip()
        actual_sha = str(lc.get("source_sha256") or "").lower()
        if not source or re.fullmatch(r"[0-9a-f]{64}", actual_sha) is None:
            blockers.append("EXECUTOR_LAW_CHECK_INVALID")
        elif expected_law_sha and actual_sha != str(expected_law_sha).lower():
            blockers.append("EXECUTOR_LAW_HASH_MISMATCH")
    else:
        blockers.append("EXECUTOR_LAW_CHECK_INVALID")

    if law_blocked:
        return list(dict.fromkeys(blockers)), law_blocked

    ec = experience_check if isinstance(experience_check, Mapping) else {"decision": "MISSING"}
    decision = str(ec.get("decision") or "MISSING").upper()
    if decision == "MISSING":
        blockers.append("EXPERIENCE_CHECK_MISSING")
    elif decision == "CONTRADICTORY":
        blockers.append("EXPERIENCE_CHECK_CONTRADICTORY")
    elif decision == "BLOCKED":
        blockers.append("EXPERIENCE_CHECK_BLOCKED")
    elif decision == "INVALID":
        blockers.append("EXPERIENCE_CHECK_INVALID")
    elif decision not in ("USE_ACTIVE_EXPERIENCE", "NO_MATCH", "UNAVAILABLE"):
        blockers.append("EXPERIENCE_CHECK_INVALID")
    elif decision == "USE_ACTIVE_EXPERIENCE":
        reported = {str(item).strip() for item in (ec.get("ids") or []) if str(item).strip()}
        if not reported:
            blockers.append("EXPERIENCE_CHECK_INVALID")
        elif expected_experience_ids and not (reported & {str(item) for item in expected_experience_ids}):
            blockers.append("EXPERIENCE_CHECK_IDS_MISMATCH")
    elif decision == "NO_MATCH" and expected_experience_ids:
        blockers.append("EXPERIENCE_CHECK_INCONSISTENT_WITH_ACTIVE_EXPECTATION")

    return list(dict.fromkeys(blockers)), law_blocked


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
        expected_law_sha: str | None = None,
        expected_experience_ids: Sequence[str] = (),
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

        session_rec = self.session_records.get(packet.binding.session_id, {})
        effective_expected_law_sha = expected_law_sha or session_rec.get("EXPECTED_LAW_SHA")
        effective_expected_exp_ids = list(expected_experience_ids) or session_rec.get("EXPECTED_EXPERIENCE_IDS", [])

        receipt_blockers, is_law_blocked = _validate_executor_receipts(
            packet.law_check,
            packet.experience_check,
            expected_law_sha=effective_expected_law_sha,
            expected_experience_ids=effective_expected_exp_ids,
        )
        # Preserve the direct-packet API's historical optional-receipt behavior;
        # parsed executor responses carry explicit MISSING mappings and are enforced.
        if packet.law_check is None:
            receipt_blockers = [item for item in receipt_blockers if not item.startswith("EXECUTOR_LAW_")]
        if packet.experience_check is None:
            receipt_blockers = [item for item in receipt_blockers if not item.startswith("EXPERIENCE_CHECK_")]
        if receipt_blockers:
            if is_law_blocked:
                if status not in ("BLOCKED", "FAILED"):
                    status = "BLOCKED"
            else:
                status = "RECONCILIATION_REQUIRED"
            blockers.extend(receipt_blockers)
            next_action = "Resolve actor-own LAW_CHECK and EXPERIENCE_CHECK receipts before reconciliation."

        expected_skill_handoff = session_rec.get("SKILL_HANDOFF")
        if isinstance(expected_skill_handoff, Mapping):
            from .skill_consumption import validate_consumption_receipt
            skill_receipt_result = validate_consumption_receipt(
                expected_skill_handoff,
                packet.skill_consumption_receipt,
            )
            if not skill_receipt_result.get("valid"):
                status = "RECONCILIATION_REQUIRED"
                blockers.extend(
                    str(code)
                    for code in skill_receipt_result.get("reason_codes", ())
                )
                next_action = (
                    "Reconcile the executor skill-consumption receipt against "
                    "the frozen session skill handoff before terminal close."
                )

        # Ingest-level enforcement of LEARNING_RECONCILIATION (Blocker 5)
        # Every terminal substantive task must provide LEARNING_RECONCILIATION=NONE or CANDIDATE
        # (no keyword heuristics)
        is_terminal_substantive = packet.session_state in ("COMPLETED", "FAILED") and not is_law_blocked
        if is_terminal_substantive and packet.learning_reconciliation is not None:
            lr = packet.learning_reconciliation
            lr_type = lr.get("type")
            if lr_type == "MISSING":
                status = "RECONCILIATION_REQUIRED"
                blockers.append("LEARNING_RECONCILIATION_MISSING")
                next_action = "Record LEARNING_RECONCILIATION=NONE or CANDIDATE before terminal close."
            elif lr_type == "CONTRADICTORY":
                status = "RECONCILIATION_REQUIRED"
                blockers.append("LEARNING_RECONCILIATION_CONTRADICTORY")
                next_action = "Resolve contradictory LEARNING_RECONCILIATION receipts before reconciliation."
            elif lr_type not in ("NONE", "CANDIDATE"):
                status = "RECONCILIATION_REQUIRED"
                blockers.append("LEARNING_RECONCILIATION_INVALID")
                next_action = "Provide valid LEARNING_RECONCILIATION (NONE or CANDIDATE)."
            elif lr_type == "NONE" and packet.session_state == "FAILED" and not lr.get("reason"):
                status = "RECONCILIATION_REQUIRED"
                blockers.append("LEARNING_RECONCILIATION_REASON_REQUIRED")
                next_action = "Supply evidence-based reason why no reusable lesson exists for failed task."

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
        if raw.get("event_type") not in CONTROL_TOWER_EVENT_TYPES:
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


def _canary_record(value: Any) -> dict[str, Any]:
    """Project one durable canary directive without creating a second store."""

    if not isinstance(value, Mapping):
        return {"FAST_CANARY_REQUIRED": "NO", "REASON": "NOT_RECORDED"}
    record = _safe_json(dict(value), path="canary")
    record["FAST_CANARY_REQUIRED"] = str(record.get("FAST_CANARY_REQUIRED") or "NO").upper()
    return record


def canary_session_quality(
    records: Mapping[str, Any],
    *,
    goal_id: str,
    session_id: str,
) -> str:
    """Return durable session quality for one SAME session and bounded goal.

    Quality is established only by a durable external GREEN grade for the same
    session id AND the same bounded goal. A NEW Arena session, a material reset,
    or a changed harness is a different durable session record, so quality is
    UNKNOWN again and medium/high-risk work must canary again.
    """

    if not str(session_id or "").strip():
        return CANARY_SESSION_QUALITY_UNKNOWN
    for record in records.values():
        if not isinstance(record, Mapping):
            continue
        if str(record.get("GOAL_ID") or "") != str(goal_id or ""):
            continue
        if str(record.get("SESSION_ID") or "") != str(session_id or ""):
            continue
        grade = record.get("CANARY_GRADE")
        if isinstance(grade, Mapping) and str(grade.get("CLASSIFICATION") or "").upper() == "GREEN":
            return CANARY_SESSION_QUALITY_ESTABLISHED
    return CANARY_SESSION_QUALITY_UNKNOWN


def _arena_chat_title(binding: SessionBinding, project_identity: str | None = None) -> str:
    """Build a concise title from the durable project/workstream and bounded goal."""

    workstream = re.sub(
        r"[-_]+",
        " ",
        str(project_identity or binding.goal_id or "").strip(),
    )
    workstream = re.sub(r"\s+", " ", workstream).strip()
    goal = re.sub(r"\s+", " ", str(binding.goal or "").strip())
    if not goal:
        goal = workstream or "Arena workstream"
    if len(goal) > 78:
        shortened = goal[:75].rsplit(" ", 1)[0].rstrip(" ,;:-")
        goal = (shortened or goal[:75].rstrip()) + "…"
    title = f"{workstream} — {goal}" if workstream and workstream.upper() != "UNKNOWN" else goal
    return title[:120].rstrip()


def _checkpoint_text(value: Any, field_name: str, *, max_length: int = 1024) -> str:
    """Normalize one compact prompt field without inventing or truncating state."""

    if not isinstance(value, str):
        raise BindingError(f"ARENA_CHECKPOINT_FIELD_INVALID:{field_name}")
    text = re.sub(r"\s+", " ", value).strip()
    if not text or len(text) > max_length:
        raise BindingError(f"ARENA_CHECKPOINT_FIELD_INVALID:{field_name}")
    return text


def _arena_prompt_checkpoint(
    binding: SessionBinding,
    task_prompt: str,
    task_id: str,
    acceptance_criteria: Sequence[str],
    *,
    plan: Any = None,
    task_record: Any = None,
    session_checkpoint: str | None = None,
) -> dict[str, str]:
    """Project current durable plan/task state into a bounded Arena handoff."""

    session_checkpoint_text = (
        _checkpoint_text(session_checkpoint, "session_checkpoint", max_length=1024)
        if session_checkpoint is not None
        else None
    )
    session_gate = "NONE_RECORDED"
    if session_checkpoint_text:
        session_checkpoint_upper = session_checkpoint_text.upper()
        if "OWNER_CONTINUATION=BLOCKED_UNTIL_GREEN" in session_checkpoint_upper:
            session_gate = "OWNER_CONTINUATION=BLOCKED_UNTIL_GREEN"
        elif "OWNER_CONTINUATION=PENDING" in session_checkpoint_upper:
            session_gate = "OWNER_CONTINUATION=PENDING"

    if plan is None:
        project = binding.goal_id
        if project.strip().upper() in {"", UNKNOWN} and task_id.strip().upper() not in {"", UNKNOWN}:
            project = task_id
        if str(project).strip().upper() in {"", UNKNOWN}:
            project = "NONE_RECORDED"
        session_task = task_id if task_id.strip().upper() not in {"", UNKNOWN} else "NONE_RECORDED"
        session_goal = binding.goal_id if binding.goal_id.strip().upper() not in {"", UNKNOWN} else "NONE_RECORDED"
        return {
            "project": _checkpoint_text(project, "project", max_length=1024),
            "plan_reference": "NO_FORMAL_PLAN",
            "already_completed": "NONE_RECORDED",
            "current_checkpoint": _checkpoint_text(
                session_checkpoint_text
                or f"SESSION_START; SESSION_ID={binding.session_id}; GOAL_ID={session_goal}; "
                f"TASK_ID={session_task}; EXECUTION_PROGRESS=NONE_RECORDED",
                "current_checkpoint",
                max_length=1024,
            ),
            "blocker_or_owner_gate": session_gate,
            "next_bounded_step": (
                "Wait for explicit Owner continuation before resuming the recorded task."
                if session_gate == "OWNER_CONTINUATION=PENDING"
                else "Wait for the external GREEN grade before requesting Owner continuation."
                if session_gate == "OWNER_CONTINUATION=BLOCKED_UNTIL_GREEN"
                else "Take the first safe bounded step from the recorded TASK above; no narrower step is recorded."
            ),
        }

    if getattr(plan, "plan_lifecycle", None) != "ACTIVE":
        raise ProjectionError("ARENA_TASK_PLAN_NOT_ACTIVE")
    if str(getattr(plan, "goal_id", "")) != binding.goal_id:
        raise ProjectionError("ARENA_TASK_PLAN_GOAL_MISMATCH")
    if task_record is None:
        task_map = getattr(plan, "tasks", None)
        normalized_task_id = task_id.strip().lower()
        if not isinstance(task_map, Mapping):
            raise ProjectionError("ARENA_TASK_PLAN_TASKS_INVALID")
        task_record = task_map.get(normalized_task_id)
        if task_record is None and task_id.strip().upper() in {"", UNKNOWN}:
            try:
                from .task_state import next_safe_task

                task_record = next_safe_task(plan)
            except Exception as exc:
                raise ProjectionError(f"ARENA_TASK_SELECTION_FAILED:{exc}") from exc
    if task_record is None:
        raise ProjectionError("ARENA_TASK_RECORD_NOT_FOUND")
    if getattr(task_record, "goal_id", None) != binding.goal_id:
        raise ProjectionError("ARENA_TASK_RECORD_GOAL_MISMATCH")

    identity = getattr(plan, "plan_identity", None)
    if identity is not None:
        identity_values = [
            str(getattr(identity, field, "") or "").strip()
            for field in ("repository", "workstream", "subject")
        ]
        identity_values = [
            "NONE_RECORDED" if value.upper() in {"", UNKNOWN, "NONE_RECORDED"} else value
            for value in identity_values
        ]
        repository, workstream, subject = identity_values
        project = f"{repository} / {workstream}"
        identity_parts = [repository, workstream, subject]
        identity_pr = str(getattr(identity, "pr", "") or "").strip()
        if identity_pr and identity_pr.upper() not in {UNKNOWN, "NONE_RECORDED"}:
            identity_parts.append(f"PR {identity_pr}")
        plan_identity_ref = " / ".join(identity_parts)
    else:
        workstream = next(
            (
                str(scope_ref).split(":", 1)[1].strip()
                for scope_ref in getattr(task_record, "scope", ())
                if str(scope_ref).startswith("WORKSTREAM:")
                and str(scope_ref).split(":", 1)[1].strip().upper() not in {UNKNOWN, "NONE_RECORDED"}
            ),
            str(getattr(task_record, "task_id", "")),
        )
        if workstream.strip().upper() in {"", UNKNOWN, "NONE_RECORDED"}:
            workstream = "NONE_RECORDED"
        plan_goal_id = str(getattr(plan, "goal_id", "") or "").strip()
        if plan_goal_id.upper() in {"", UNKNOWN, "NONE_RECORDED"}:
            plan_goal_id = "NONE_RECORDED"
        project = f"{plan_goal_id} / {workstream}"
        plan_identity_ref = f"goal {plan_goal_id}"
    plan_hash = plan.canonical_hash()
    plan_reference = (
        f".p2p/state/task-state.json#{plan_identity_ref}; plan_hash={plan_hash}"
    )

    completed_ids = [
        str(item_id)
        for item_id, item in getattr(plan, "tasks", {}).items()
        if getattr(item, "status", None) == "DONE"
    ]
    completed = ", ".join(completed_ids) if completed_ids else "NONE_RECORDED"

    checkpoint = getattr(task_record, "checkpoint", None)
    checkpoint = checkpoint if isinstance(checkpoint, Mapping) else {}
    checkpoint_ref = str(checkpoint.get("checkpoint_ref") or "NONE_RECORDED")
    recovery = str(checkpoint.get("recovery_classification") or "NONE_RECORDED")
    current = (
        f"TASK_ID={task_record.task_id}; STATUS={task_record.status}; TITLE={task_record.title}; "
        f"CHECKPOINT_REF={checkpoint_ref}; RECOVERY={recovery}"
    )
    if session_checkpoint_text:
        current += f"; SESSION_CHECKPOINT={session_checkpoint_text}"

    blocker_parts: list[str] = []
    if session_gate != "NONE_RECORDED":
        blocker_parts.append(session_gate)
    blocker = getattr(task_record, "blocker", None)
    if isinstance(blocker, Mapping):
        reason = blocker.get("reason")
        blocker_reason = (
            reason
            if isinstance(reason, str) and reason.strip() and reason.strip().upper() not in {UNKNOWN, "NONE_RECORDED"}
            else task_record.status
        )
        blocker_parts.append(f"BLOCKER={blocker_reason}")
    owner_decision = getattr(task_record, "owner_decision", None)
    if isinstance(owner_decision, Mapping) and str(owner_decision.get("status") or "").upper() == "PENDING":
        question = owner_decision.get("question")
        blocker_parts.append(
            "OWNER_GATE=PENDING" + (f": {question}" if isinstance(question, str) and question.strip() else "")
        )
    if not blocker_parts and str(task_record.status) == "BLOCKED":
        blocker_parts.append("BLOCKER=BLOCKED_WITHOUT_REASON")
    blocker_value = "; ".join(blocker_parts) if blocker_parts else "NONE_RECORDED"

    next_step = checkpoint.get("next_safe_step")
    if (
        not isinstance(next_step, str)
        or not next_step.strip()
        or next_step.strip().upper() in {UNKNOWN, "NONE_RECORDED"}
    ):
        if blocker_parts:
            next_step = "Resolve the recorded blocker or Owner Gate before executing this task."
        else:
            first_acceptance = next(iter(getattr(task_record, "acceptance_requirements", ())), None)
            next_step = f"Work on {task_record.task_id}: {task_record.title} within its recorded scope."
            if first_acceptance:
                next_step += f" Verify: {first_acceptance}"

    return {
        "project": _checkpoint_text(project, "project", max_length=1024),
        "plan_reference": _checkpoint_text(plan_reference, "plan_reference", max_length=2048),
        "already_completed": _checkpoint_text(completed, "already_completed", max_length=2048),
        "current_checkpoint": _checkpoint_text(current, "current_checkpoint", max_length=2048),
        "blocker_or_owner_gate": _checkpoint_text(blocker_value, "blocker_or_owner_gate", max_length=2048),
        "next_bounded_step": _checkpoint_text(next_step, "next_bounded_step", max_length=2048),
    }


def _load_arena_prompt_checkpoint(
    root: str | Path,
    binding: SessionBinding,
    task_prompt: str,
    task_id: str,
    acceptance_criteria: Sequence[str],
    *,
    session_checkpoint: str | None = None,
) -> dict[str, str]:
    """Read the existing task-state store; unreadable formal state fails closed."""

    try:
        from .task_state import TaskStateStore
    except ImportError as exc:
        raise ProjectionError("TASK_STATE_SURFACE_UNAVAILABLE") from exc
    try:
        plan = TaskStateStore(root).load()
    except Exception as exc:
        raise ProjectionError(f"TASK_STATE_UNREADABLE:{exc}") from exc
    return _arena_prompt_checkpoint(
        binding,
        task_prompt,
        task_id,
        acceptance_criteria,
        plan=plan,
        session_checkpoint=session_checkpoint,
    )


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
    canary_directive: CanaryDirective | None = None,
    max_prompt_chars: int | None = None,
    arena_prompt_checkpoint: Mapping[str, str] | None = None,
    chat_mode: str = "NEW_CHAT",
    chat_title_override: str | None = None,
    skill_handoff: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    project_identity = (
        arena_prompt_checkpoint.get("project")
        if isinstance(arena_prompt_checkpoint, Mapping)
        else None
    )
    chat_title = (
        _checkpoint_text(chat_title_override, "chat_title", max_length=120)
        if binding.host == "ARENA" and chat_title_override is not None
        else _arena_chat_title(binding, project_identity)
        if binding.host == "ARENA"
        else None
    )
    prompt = build_execution_prompt(
        binding,
        task_prompt or binding.goal,
        worktree=worktree,
        branch=branch,
        canonical_base_sha=canonical_base_sha,
        canonical_base_tree=canonical_base_tree,
        acceptance_criteria=acceptance_criteria,
        canary_directive=canary_directive,
        max_prompt_chars=max_prompt_chars,
        task_id=task_id,
        arena_prompt_checkpoint=arena_prompt_checkpoint,
        chat_mode=chat_mode,
        chat_title_override=chat_title,
        skill_handoff=skill_handoff,
    )
    recommendation = {
        "CHAT_NAME": chat_title or f"{binding.host} — {binding.goal_id} — {binding.goal}",
        "HOST": binding.host,
        "SESSION_ID": binding.session_id,
        "GOAL_ID": binding.goal_id,
        "TASK_ID": task_id,
        "PROMPT": prompt,
        "PACKET_IS_CANONICAL_TRUTH": "NO",
    }
    if chat_title is not None:
        recommendation["CHAT_TITLE"] = chat_title
    if isinstance(skill_handoff, Mapping):
        recommendation["SKILL_HANDOFF"] = _safe_json(
            dict(skill_handoff), path="skill_handoff"
        )
        recommendation["REQUIRED_SKILLS"] = list(
            skill_handoff.get("REQUIRED_SKILLS") or ()
        )
    if canary_directive is not None:
        recommendation["CANARY"] = canary_directive.to_dict()
        recommendation["FAST_CANARY_REQUIRED"] = "YES"
    return recommendation


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
                        "EXPECTED_LAW_SHA": event.get("EXPECTED_LAW_SHA"),
                        "EXPECTED_EXPERIENCE_IDS": event.get("EXPECTED_EXPERIENCE_IDS", []),
                        "ACCEPTANCE_CRITERIA": list(event.get("ACCEPTANCE_CRITERIA") or []),
                        "SKILL_HANDOFF": _safe_json(
                            event.get("SKILL_HANDOFF"),
                            path="skill_handoff",
                        ) if isinstance(event.get("SKILL_HANDOFF"), Mapping) else None,
                        "CANARY": _canary_record(event.get("CANARY")),
                    }
                )
                records[session_id] = record
                state.session_records = records
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

            if event_type == "CONTROL_TOWER_CANARY_EVIDENCE":
                raw_binding = event.get("SESSION_BINDING")
                if not isinstance(raw_binding, Mapping):
                    raise ProjectionError("CONTROL_TOWER_CANARY_BINDING_INVALID")
                binding = SessionBinding.from_mapping(raw_binding)
                record = records.get(binding.session_id)
                if record is None:
                    orphan_returns.append(
                        {
                            "LINE": event.get("_LINE_NUMBER"),
                            "SESSION_ID": binding.session_id,
                            "HOST": binding.host,
                        }
                    )
                    continue
                if not _same_binding(record.get("BINDING", {}), binding.to_dict()):
                    raise ProjectionError("CONTROL_TOWER_CANARY_BINDING_CONFLICT")
                fingerprint = str(event.get("EVIDENCE_FINGERPRINT") or "")
                previous = record.get("CANARY_EVIDENCE_FINGERPRINT")
                if previous not in (None, fingerprint):
                    raise ProjectionError("CONTROL_TOWER_MULTIPLE_DIFFERENT_CANARY_EVIDENCE")
                grade = event.get("CONTROL_TOWER_CANARY")
                if not isinstance(grade, Mapping):
                    raise ProjectionError("CONTROL_TOWER_CANARY_GRADE_INVALID")
                grade = _safe_json(dict(grade), path="canary_grade")
                classification = str(grade.get("CLASSIFICATION") or "UNVERIFIED").upper()
                updated = dict(record)
                updated.update(
                    {
                        "CANARY_GRADE": grade,
                        "CANARY_EVIDENCE_FINGERPRINT": fingerprint,
                        # The session pauses at OWNER_CONTINUATION_GATE_V1; it is
                        # neither executing nor terminally returned.
                        "SESSION_STATE": "WAITING_OWNER_GATE",
                        "OWNER_GATE": {
                            "GATE": OWNER_CONTINUATION_GATE_V1,
                            "SESSION_ID": binding.session_id,
                            "CANARY_CLASSIFICATION": classification,
                            "SESSION_POLICY": CANARY_SESSION_POLICIES.get(classification, "NO_DEFAULT_CONTINUATION"),
                            "CONTINUATION_RECOMMENDATION": CANARY_CONTINUATION_RECOMMENDATIONS.get(
                                classification, "NO_DEFAULT_CONTINUATION"
                            ),
                            "FALLBACK_OWNER_REPLY": FALLBACK_OWNER_REPLY,
                        },
                    }
                )
                records[binding.session_id] = updated
                continue

            if event_type == "CONTROL_TOWER_CANARY_CONTINUATION":
                record = records.get(str(event.get("SESSION_ID") or ""))
                if record is None:
                    continue
                record["CANARY_CONTINUATION"] = _safe_json(
                    {
                        key: value
                        for key, value in event.items()
                        if key not in {"_LINE_NUMBER", "schema", "event_type"}
                    },
                    path="canary_continuation",
                )
                recommendation = event.get("RECOMMENDED_NEW_CHAT")
                if isinstance(recommendation, Mapping):
                    record["RECOMMENDED_NEW_CHAT"] = _safe_json(
                        dict(recommendation), path="canary_continuation_recommendation"
                    )
                # The Owner continuation reopens the SAME session for the original
                # real task; the canary is never repeated for that session.
                record["SESSION_STATE"] = "ACTIVE"
                record["OWNER_GATE"] = None
                records[str(event.get("SESSION_ID"))] = record
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
        canary = record.get("CANARY")
        if isinstance(canary, Mapping) and canary.get("FAST_CANARY_REQUIRED") == "YES":
            grade = record.get("CANARY_GRADE")
            if not isinstance(grade, Mapping):
                return {
                    "ACTION": "WAIT_FOR_CANARY_EXTERNAL_GRADE",
                    "REASON": "The canary evidence packet has not been externally graded yet.",
                }
            classification = str(grade.get("CLASSIFICATION") or "UNVERIFIED").upper()
            if classification != "GREEN":
                return {
                    "ACTION": CANARY_SESSION_POLICIES.get(classification, "NO_DEFAULT_CONTINUATION"),
                    "REASON": f"External canary classification is {classification}; "
                    f"{CANARY_CONTINUATION_RECOMMENDATIONS.get(classification, 'NO_DEFAULT_CONTINUATION')}.",
                }
            if not isinstance(record.get("CANARY_CONTINUATION"), Mapping):
                return {
                    "ACTION": "WAIT_FOR_OWNER_CONTINUATION",
                    "REASON": "External GREEN alone does not unlock full execution; explicit Owner continuation is required.",
                }
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
        canary_gates: list[dict[str, Any]] = []
        latest: Mapping[str, Any] | None = None
        for record in state.session_records.values():
            canary = record.get("CANARY")
            if isinstance(canary, Mapping) and canary.get("FAST_CANARY_REQUIRED") == "YES":
                grade = record.get("CANARY_GRADE")
                classification = (
                    str(grade.get("CLASSIFICATION") or "UNVERIFIED").upper()
                    if isinstance(grade, Mapping)
                    else "UNVERIFIED"
                )
                canary_gates.append(
                    {
                        "SESSION_ID": record.get("SESSION_ID", UNKNOWN),
                        "HOST": record.get("HOST", UNKNOWN),
                        "GOAL_ID": record.get("GOAL_ID", UNKNOWN),
                        "TASK_ID": record.get("TASK_ID", UNKNOWN),
                        "GATE": MODEL_CANARY_GATE_V1,
                        "RISK_CLASS": canary.get("RISK_CLASS", UNKNOWN),
                        "SESSION_QUALITY": canary.get("SESSION_QUALITY", UNKNOWN),
                        "CLASSIFICATION": classification,
                        "SESSION_POLICY": CANARY_SESSION_POLICIES.get(classification, "NO_DEFAULT_CONTINUATION"),
                        "CONTINUATION_RECOMMENDATION": CANARY_CONTINUATION_RECOMMENDATIONS.get(
                            classification, "NO_DEFAULT_CONTINUATION"
                        ),
                        "OWNER_CONTINUATION_RECORDED": (
                            "YES"
                            if isinstance(record.get("CANARY_CONTINUATION"), Mapping)
                            else "NO"
                        ),
                        "CANARY_REPEAT": (
                            "NO"
                            if isinstance(record.get("CANARY_CONTINUATION"), Mapping)
                            else "PENDING_OWNER_CONTINUATION"
                        ),
                        "ORIGINAL_TASK_SOURCE": "CONTROL_TOWER_DURABLE_STATE",
                    }
                )
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
                "CANARY_GATES": canary_gates,
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
        required_skills: Sequence[str] = (),
        host_discovery_record: Mapping[str, Any] | None = None,
        expected_law_sha: str | None = None,
        expected_experience_ids: Sequence[str] = (),
        canary_directive: CanaryDirective | None = None,
    ) -> dict[str, Any]:
        if not isinstance(binding, SessionBinding):
            raise BindingError("SESSION_BINDING_REQUIRED")
        if canary_directive is not None and not isinstance(canary_directive, CanaryDirective):
            raise BindingError("CANARY_DIRECTIVE_REQUIRED")
        task_id = _optional_text(task_id, "task_id", max_length=256)
        worktree = _location(worktree, "worktree")
        branch = _location(branch, "branch")
        canonical_base_sha = _hash_or_unknown(canonical_base_sha, "canonical_base_sha")
        canonical_base_tree = _hash_or_unknown(canonical_base_tree, "canonical_base_tree")
        criteria = _refs(acceptance_criteria, "acceptance_criteria", max_length=4096)
        required_skill_refs = _refs(required_skills, "required_skills", max_length=256)
        state, orphan_returns = self._replay()
        existing = state.session_records.get(binding.session_id)
        if existing is not None:
            existing_binding = existing.get("BINDING")
            if not isinstance(existing_binding, Mapping) or not _same_binding(existing_binding, binding.to_dict()):
                raise BindingError("SESSION_ID_ALREADY_BOUND_TO_DIFFERENT_SESSION")
            if existing.get("SESSION_STATE") != "ACTIVE":
                raise BindingError("SESSION_ID_ALREADY_HAS_TERMINAL_RESULT")

        existing_continuation = existing.get("CANARY_CONTINUATION") if isinstance(existing, Mapping) else None
        effective_directive = canary_directive
        if effective_directive is None and isinstance(existing, Mapping) and not isinstance(existing_continuation, Mapping):
            recorded_canary = existing.get("CANARY")
            if isinstance(recorded_canary, Mapping) and recorded_canary.get("FAST_CANARY_REQUIRED") == "YES":
                effective_directive = CanaryDirective.from_mapping(recorded_canary)
        effective_task_id = task_id
        if effective_task_id.strip().upper() in {"", UNKNOWN} and effective_directive is not None:
            effective_task_id = effective_directive.task_id
        if effective_task_id.strip().upper() in {"", UNKNOWN} and isinstance(existing, Mapping):
            effective_task_id = str(existing.get("TASK_ID") or UNKNOWN)
        recorded_original_task = (
            existing_continuation.get("ORIGINAL_TASK")
            if isinstance(existing_continuation, Mapping)
            else None
        )
        prompt_task = task_prompt or (
            effective_directive.original_task
            if effective_directive is not None
            else recorded_original_task or binding.goal
        )
        prompt_criteria = criteria or tuple(existing.get("ACCEPTANCE_CRITERIA") or ()) if isinstance(existing, Mapping) else criteria
        chat_mode = "SAME_CHAT" if isinstance(existing_continuation, Mapping) else "NEW_CHAT"
        chat_title_override = None
        if chat_mode == "SAME_CHAT" and isinstance(existing, Mapping):
            previous_recommendation = existing.get("RECOMMENDED_NEW_CHAT")
            if isinstance(previous_recommendation, Mapping):
                previous_title = previous_recommendation.get("CHAT_TITLE")
                if isinstance(previous_title, str):
                    chat_title_override = previous_title
        session_checkpoint = None
        if isinstance(existing, Mapping):
            if isinstance(existing_continuation, Mapping):
                session_checkpoint = (
                    f"SESSION_ID={binding.session_id}; TASK_ID={effective_task_id}; "
                    "CANARY_GRADE=GREEN; OWNER_CONTINUATION=YES; EXECUTION_PROGRESS=NOT_RECORDED"
                )
            else:
                existing_grade = existing.get("CANARY_GRADE")
                if isinstance(existing_grade, Mapping):
                    classification = str(existing_grade.get("CLASSIFICATION") or "UNVERIFIED").upper()
                    owner_gate = "PENDING" if classification == "GREEN" else "BLOCKED_UNTIL_GREEN"
                    session_checkpoint = (
                        f"SESSION_ID={binding.session_id}; TASK_ID={effective_task_id}; "
                        f"CANARY_GRADE={classification}; OWNER_CONTINUATION={owner_gate}"
                    )
                elif isinstance(existing.get("CANARY"), Mapping) and existing["CANARY"].get("FAST_CANARY_REQUIRED") == "YES":
                    session_checkpoint = (
                        f"SESSION_ID={binding.session_id}; TASK_ID={effective_task_id}; "
                        "CANARY_GRADE=AWAITING_EXTERNAL_GRADE; "
                        "OWNER_CONTINUATION=BLOCKED_UNTIL_GREEN"
                    )
                else:
                    session_checkpoint = (
                        f"SESSION_ID={binding.session_id}; TASK_ID={effective_task_id}; "
                        "SESSION_STATE=ACTIVE; EXECUTION_PROGRESS=NONE_RECORDED"
                    )
        skill_handoff = None
        skill_registry_available = (
            self.root / ".p2p" / "system" / "p2p_capabilities"
            / "capabilities.json"
        ).is_file()
        if skill_registry_available:
            existing_handoff = (
                existing.get("SKILL_HANDOFF")
                if isinstance(existing, Mapping)
                else None
            )
            # F01: detect generic cached prompt to fail-closed on tampered handoff
            is_generic_cached_start = False
            if isinstance(existing, Mapping):
                rec = existing.get("RECOMMENDED_NEW_CHAT")
                if isinstance(rec, Mapping):
                    rh = rec.get("SKILL_HANDOFF")
                    if isinstance(rh, Mapping):
                        rh_mode = str(rh.get("SKILL_HOST_MODE") or "")
                        rh_check = str(rh.get("SKILL_CHECK") or "").upper()
                        rh_selected = rh.get("SKILLS_SELECTED") or ()
                        rh_required = rh.get("REQUIRED_SKILLS") or ()
                        if rh_mode == "GENERIC_EXACT_REPO_READ":
                            is_generic_cached_start = True
                        elif rh_check == "PASS" and (rh_selected or rh_required):
                            is_generic_cached_start = True
                        elif rh_required:
                            is_generic_cached_start = True
                    if rec.get("REQUIRED_SKILLS"):
                        is_generic_cached_start = True
                if isinstance(existing_handoff, Mapping) and str(existing_handoff.get("SKILL_HOST_MODE") or "") == "GENERIC_EXACT_REPO_READ":
                    is_generic_cached_start = True
            should_validate_start = is_generic_cached_start or isinstance(existing_handoff, Mapping)
            if is_generic_cached_start and not isinstance(existing_handoff, Mapping):
                should_validate_start = True
            if should_validate_start:
                if isinstance(existing_handoff, Mapping):
                    skill_handoff = dict(existing_handoff)
                    from .skill_consumption import validate_cached_skill_handoff_host_evidence
                    host_evidence = validate_cached_skill_handoff_host_evidence(
                        self.root,
                        host=binding.host,
                        skill_handoff=skill_handoff,
                        host_discovery_record=host_discovery_record,
                    )
                    if not host_evidence.get("valid"):
                        raise BindingError(
                            "SKILL_HANDOFF_HOST_EVIDENCE_STALE:"
                            + str(host_evidence.get("reason") or "UNKNOWN")
                        )
                    if required_skill_refs:
                        normalize_required = lambda value: (
                            str(value or "").strip().lower().lstrip("@$")
                            .replace("_", "-").replace(" ", "-")
                        )
                        existing_required = tuple(
                            normalize_required(value)
                            for value in (skill_handoff.get("REQUIRED_SKILLS") or ())
                        )
                        requested_required = tuple(
                            normalize_required(value)
                            for value in required_skill_refs
                        )
                        if requested_required != existing_required:
                            raise BindingError(
                                "REQUIRED_SKILLS_CHANGED_FOR_ACTIVE_SESSION"
                            )
                else:
                    from .skill_consumption import validate_cached_skill_handoff_host_evidence
                    host_evidence = validate_cached_skill_handoff_host_evidence(
                        self.root,
                        host=binding.host,
                        skill_handoff=existing_handoff,
                        host_discovery_record=host_discovery_record,
                    )
                    raise BindingError(
                        "SKILL_HANDOFF_HOST_EVIDENCE_STALE:"
                        + str(host_evidence.get("reason") or "UNKNOWN")
                    )
            else:
                from .skill_consumption import prepare_skill_handoff
                skill_handoff = prepare_skill_handoff(
                    self.root,
                    prompt_task,
                    host=binding.host,
                    required_skills=required_skill_refs,
                    host_discovery_record=host_discovery_record,
                )
            if skill_handoff.get("SKILL_CHECK") == "BLOCKED":
                reasons = ",".join(
                    str(v)
                    for v in skill_handoff.get("REJECTION_REASON", ())
                )
                raise BindingError(
                    "SKILL_HANDOFF_BLOCKED:" + (reasons or "UNKNOWN")
                )

        arena_checkpoint = None
        if binding.host == "ARENA":
            arena_checkpoint = _load_arena_prompt_checkpoint(
                self.root,
                binding,
                prompt_task,
                effective_task_id,
                prompt_criteria,
                session_checkpoint=session_checkpoint,
            )

        if existing is not None:
            recommendation = existing.get("RECOMMENDED_NEW_CHAT")
            if binding.host == "ARENA" or not isinstance(recommendation, Mapping):
                recommendation = _session_recommendation(
                    binding,
                    task_prompt=prompt_task,
                    worktree=worktree,
                    branch=branch,
                    canonical_base_sha=canonical_base_sha,
                    canonical_base_tree=canonical_base_tree,
                    acceptance_criteria=prompt_criteria,
                    task_id=effective_task_id,
                    canary_directive=effective_directive,
                    arena_prompt_checkpoint=arena_checkpoint,
                    chat_mode=chat_mode,
                    chat_title_override=chat_title_override,
                    skill_handoff=skill_handoff,
                )
                if isinstance(existing_continuation, Mapping):
                    existing_grade = existing.get("CANARY_GRADE") if isinstance(existing, Mapping) else None
                    classification = (
                        str(existing_grade.get("CLASSIFICATION") or "UNVERIFIED").upper()
                        if isinstance(existing_grade, Mapping)
                        else "UNVERIFIED"
                    )
                    recommendation.update(
                        {
                            "CANARY_REPEAT": "NO",
                            "CONTINUATION_MODE": "RESUME_ORIGINAL_TASK_IN_SAME_SESSION",
                            "CANARY_CLASSIFICATION": classification,
                            "SESSION_POLICY": CANARY_SESSION_POLICIES.get(classification, "NO_DEFAULT_CONTINUATION"),
                            "ORIGINAL_TASK_SOURCE": "CONTROL_TOWER_DURABLE_STATE",
                        }
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
            task_prompt=prompt_task,
            worktree=worktree,
            branch=branch,
            canonical_base_sha=canonical_base_sha,
            canonical_base_tree=canonical_base_tree,
            acceptance_criteria=criteria,
            task_id=effective_task_id,
            canary_directive=effective_directive,
            arena_prompt_checkpoint=arena_checkpoint,
            chat_mode=chat_mode,
            skill_handoff=skill_handoff,
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
            "EXPECTED_LAW_SHA": expected_law_sha,
            "EXPECTED_EXPERIENCE_IDS": list(expected_experience_ids),
            "ACCEPTANCE_CRITERIA": list(criteria),
            "SKILL_HANDOFF": _safe_json(
                skill_handoff, path="skill_handoff"
            ) if isinstance(skill_handoff, Mapping) else None,
            "CANARY": canary_directive.to_dict() if canary_directive is not None else None,
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
        *,
        session_id: str | None = None,
        expected_law_sha: str | None = None,
        expected_experience_ids: Sequence[str] = (),
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Ingest one complete executor response.

        A triggered canary turn returns the canonical CANARY_EVIDENCE_PACKET_V1
        plus neutral checkpoint metadata only. That evidence-only response is
        bound to the Control Tower session the caller names explicitly and is
        graded externally; no CONTROL_TOWER_RETURN_PACKET is required from the
        executor. Every other response still requires exactly one marked
        CONTROL_TOWER_RETURN_PACKET.
        """

        if not isinstance(final_response, str):
            raise PacketParseError("FINAL_RESPONSE_MUST_BE_TEXT")
        canary_evidence = kwargs.pop("canary_evidence", parse_canary_evidence_packet(final_response))
        has_packet_marker = PACKET_BEGIN in final_response or PACKET_END in final_response
        if not has_packet_marker and canary_evidence is not None:
            if not str(session_id or "").strip():
                raise PacketParseError("CANARY_EVIDENCE_SESSION_ID_REQUIRED")
            return self.ingest_canary_evidence(
                final_response,
                session_id=str(session_id),
                canary_evidence=canary_evidence,
            )
        try:
            packet = parse_return_packet(final_response)
        except ControlTowerHandoffError as exc:
            raise PacketParseError(str(exc)) from exc
        if session_id is not None and str(session_id) != packet.binding.session_id:
            raise BindingError("INGEST_SESSION_ID_DOES_NOT_MATCH_PACKET_BINDING")
        payload: dict[str, Any] = {}
        try:
            start = final_response.index(PACKET_BEGIN) + len(PACKET_BEGIN)
            end = final_response.index(PACKET_END)
            payload = json.loads(final_response[start:end].strip())
        except (ValueError, json.JSONDecodeError):
            pass
        law_check, experience_check, learning_reconciliation = _extract_executor_receipts(final_response, payload)
        return self.ingest_packet(
            packet,
            law_check=kwargs.pop("law_check", law_check),
            experience_check=kwargs.pop("experience_check", experience_check),
            learning_reconciliation=kwargs.pop("learning_reconciliation", learning_reconciliation),
            canary_evidence=canary_evidence,
            response_text=kwargs.pop("response_text", final_response),
            expected_law_sha=expected_law_sha,
            expected_experience_ids=expected_experience_ids,
            **kwargs,
        )

    def ingest_canary_evidence(
        self,
        response_text: str,
        *,
        session_id: str,
        canary_evidence: Mapping[str, Any] | None = None,
        packet: ControlTowerReturnPacket | None = None,
    ) -> dict[str, Any]:
        """Ingest and externally grade one triggered canary turn.

        MODEL_CANARY_GATE_V1: the tested executor never grades itself; Control
        Tower grades the externally observable evidence here. The canary turn is
        persisted as ONE ``CONTROL_TOWER_CANARY_EVIDENCE`` event in the existing
        execution ledger (canonical evidence fields, checkpoint presence, an
        optional executor-packet summary, and the external grade). The raw
        executor response is never persisted, and a canary turn never becomes
        the session's terminal return: that slot stays reserved for the resumed
        ORIGINAL task after external GREEN plus explicit Owner continuation.
        """

        text = response_text if isinstance(response_text, str) else ""
        if len(text) > 500_000:
            raise PacketParseError("FINAL_RESPONSE_TOO_LARGE")
        state, orphan_returns = self._replay()
        record = state.session_records.get(str(session_id or ""))
        if not isinstance(record, Mapping):
            raise BindingError("SESSION_ID_NOT_REGISTERED_IN_CONTROL_TOWER_LEDGER")
        law_check, experience_check, _ = _extract_executor_receipts(text, {})
        effective_expected_law_sha = record.get("EXPECTED_LAW_SHA")
        effective_expected_exp_ids = record.get("EXPECTED_EXPERIENCE_IDS")
        receipt_blockers, _ = _validate_executor_receipts(
            law_check,
            experience_check,
            expected_law_sha=(effective_expected_law_sha if isinstance(effective_expected_law_sha, str) else None),
            expected_experience_ids=(effective_expected_exp_ids if isinstance(effective_expected_exp_ids, list) else ()),
        )
        if not isinstance(effective_expected_law_sha, str) or re.fullmatch(r"[0-9a-fA-F]{64}", effective_expected_law_sha) is None:
            receipt_blockers.append("SESSION_EXPECTED_LAW_SHA_MISSING_OR_INVALID")
        if not isinstance(effective_expected_exp_ids, list):
            receipt_blockers.append("SESSION_EXPECTED_EXPERIENCE_IDS_MISSING_OR_INVALID")
        receipt_blockers = list(dict.fromkeys(receipt_blockers))
        canary = record.get("CANARY")
        if not isinstance(canary, Mapping) or canary.get("FAST_CANARY_REQUIRED") != "YES":
            raise BindingError("CANARY_EVIDENCE_REQUIRES_TRIGGERED_CANARY_SESSION")
        binding_mapping = record.get("BINDING")
        if not isinstance(binding_mapping, Mapping):
            raise BindingError("CONTROL_TOWER_SESSION_BINDING_INVALID")
        binding = SessionBinding.from_mapping(binding_mapping)
        if packet is not None and not _same_binding(binding.to_dict(), packet.binding.to_dict()):
            raise BindingError("PACKET_BINDING_REJECTED")
        evidence = canary_evidence if canary_evidence is not None else parse_canary_evidence_packet(text)
        raw_fields = evidence.get("FIELDS") if isinstance(evidence, Mapping) else None
        fields = {str(key): str(value) for key, value in raw_fields.items()} if isinstance(raw_fields, Mapping) else {}
        checkpoint = [token for token in CANARY_CHECKPOINT_FIELDS if token in text]
        packet_summary = (
            None
            if packet is None
            else {"SESSION_STATE": packet.session_state, "PACKET_FINGERPRINT": packet.fingerprint()}
        )
        fingerprint = hashlib.sha256(
            json.dumps(
                {
                    "FIELDS": fields,
                    "CHECKPOINT": checkpoint,
                    "EXECUTOR_RETURN_PACKET": packet_summary,
                    "LAW_CHECK": law_check,
                    "EXPERIENCE_CHECK": experience_check,
                },
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        previous = record.get("CANARY_EVIDENCE_FINGERPRINT")
        if previous is not None:
            grade = record.get("CANARY_GRADE")
            classification = (
                str(grade.get("CLASSIFICATION") or "UNVERIFIED").upper() if isinstance(grade, Mapping) else "UNVERIFIED"
            )
            if previous == fingerprint and isinstance(grade, Mapping):
                return {
                    "status": "PASS",
                    "idempotent": True,
                    "ingest_kind": "CANARY_EVIDENCE",
                    "binding": binding.to_dict(),
                    "task_id": record.get("TASK_ID", UNKNOWN),
                    "canary_grade": dict(grade),
                    "snapshot": self._projection(state, orphan_returns),
                }
            required = (
                "RESUMED_TASK_REQUIRES_CONTROL_TOWER_RETURN_PACKET"
                if isinstance(record.get("CANARY_CONTINUATION"), Mapping)
                else "CANARY_OWNER_CONTINUATION_REQUIRED"
            )
            raise BindingError(f"CANARY_SESSION_ALREADY_GRADED:{classification}:{required}")
        grade = classify_canary_evidence(evidence, return_packet=packet, response_text=text)
        if receipt_blockers:
            grade = dict(grade)
            if grade.get("CLASSIFICATION") != "RED":
                grade["CLASSIFICATION"] = "UNVERIFIED"
                grade["SESSION_POLICY"] = CANARY_SESSION_POLICIES["UNVERIFIED"]
                grade["CONTINUATION_RECOMMENDATION"] = CANARY_CONTINUATION_RECOMMENDATIONS["UNVERIFIED"]
                grade["OWNER_CONTINUATION_REQUIRED"] = "NO"
            grade["REASONS"] = [
                *grade.get("REASONS", []),
                "EXECUTOR_RECEIPT_VALIDATION_FAILED:" + ",".join(receipt_blockers),
            ]
        event = {
            "schema": CANARY_EVIDENCE_EVENT_SCHEMA,
            "event_type": "CONTROL_TOWER_CANARY_EVIDENCE",
            "SESSION_BINDING": binding.to_dict(),
            "TASK_ID": str(record.get("TASK_ID") or UNKNOWN),
            "GATE": MODEL_CANARY_GATE_V1,
            "CANARY_EVIDENCE": {name: fields[name] for name in CANARY_EVIDENCE_FIELDS if name in fields} or None,
            "ACTOR_RECEIPTS": {"LAW_CHECK": law_check, "EXPERIENCE_CHECK": experience_check},
            "ACTOR_RECEIPT_BLOCKERS": receipt_blockers,
            "CHECKPOINT_METADATA_PRESENT": checkpoint,
            "EXECUTOR_RETURN_PACKET": packet_summary,
            "EVIDENCE_FINGERPRINT": fingerprint,
            "CONTROL_TOWER_CANARY": dict(grade),
            "RAW_EXECUTOR_RESPONSE_PERSISTED": "NO",
            "PACKET_IS_CANONICAL_TRUTH": "NO",
            "PROMOTED": False,
            "PROTECTED_ACTION_EXECUTED": False,
        }
        # Validate with the same rules replay applies, BEFORE writing: unsafe or
        # oversized executor evidence is rejected here instead of poisoning
        # every later replay of the existing ledger.
        try:
            _reject_secret_keys(event)
            event = _safe_json(event, path="canary_evidence_event")
        except ControlTowerHandoffError as exc:
            raise BindingError(f"CANARY_EVIDENCE_UNSAFE_FOR_LEDGER:{exc}") from exc
        _append_existing_execution_event(self.ledger_path, event)
        return {
            "status": "PASS",
            "idempotent": False,
            "ingest_kind": "CANARY_EVIDENCE",
            "binding": binding.to_dict(),
            "task_id": record.get("TASK_ID", UNKNOWN),
            "canary_grade": dict(grade),
            "snapshot": self.snapshot(),
        }

    def ingest_packet(
        self,
        packet: ControlTowerReturnPacket,
        *,
        current_canonical_base_sha: str | None = None,
        current_canonical_base_tree: str | None = None,
        narrative_host: Any = None,
        law_check: Mapping[str, Any] | None = None,
        learning_reconciliation: Mapping[str, Any] | None = None,
        experience_check: Mapping[str, Any] | None = None,
        expected_law_sha: str | None = None,
        expected_experience_ids: Sequence[str] = (),
        canary_evidence: Mapping[str, Any] | None = None,
        response_text: str | None = None,
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
        canary = record.get("CANARY")
        if (
            isinstance(canary, Mapping)
            and canary.get("FAST_CANARY_REQUIRED") == "YES"
            and not isinstance(record.get("CANARY_CONTINUATION"), Mapping)
        ):
            # MODEL_CANARY_GATE_V1: until the Owner continuation is recorded, the
            # only response a triggered canary session can return is its canary
            # turn. It is graded externally and never becomes the terminal return.
            return self.ingest_canary_evidence(
                response_text if isinstance(response_text, str) else packet.to_marked_text(),
                session_id=packet.binding.session_id,
                canary_evidence=canary_evidence,
                packet=packet,
            )
        effective_packet = packet
        if law_check is not None or learning_reconciliation is not None or experience_check is not None:
            effective_packet = replace(
                packet,
                law_check=law_check if law_check is not None else packet.law_check,
                learning_reconciliation=learning_reconciliation if learning_reconciliation is not None else packet.learning_reconciliation,
                experience_check=experience_check if experience_check is not None else packet.experience_check,
            )
        # Idempotency is recognised against the packet as received and against
        # the receipt-completed packet that is actually appended to the ledger,
        # so a repeated identical ingest is never mistaken for a different
        # packet whichever surface delivered it.
        packet_fingerprint = effective_packet.fingerprint()
        received_fingerprint = packet.fingerprint()
        previous_fingerprint = record.get("PACKET_FINGERPRINT", UNKNOWN)
        if previous_fingerprint != UNKNOWN:
            if previous_fingerprint in (packet_fingerprint, received_fingerprint):
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
            effective_packet,
            current_canonical_base_sha=current_sha,
            current_canonical_base_tree=current_tree,
            narrative_host=narrative_host,
            record_event=False,
            expected_law_sha=expected_law_sha,
            expected_experience_ids=expected_experience_ids,
        )
        _append_existing_execution_event(self.ledger_path, to_execution_ledger_event(effective_packet, result))
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

    def session_quality(self, goal_id: str, session_id: str) -> str:
        """Return durable session quality for one SAME session and bounded goal.

        A NEW session, a material reset, or a changed harness has no durable
        GREEN record for that session, so quality is UNKNOWN again.
        """

        state, _ = self._replay()
        return canary_session_quality(
            state.session_records,
            goal_id=goal_id,
            session_id=session_id,
        )

    def continue_canary_session(
        self,
        session_id: str,
        *,
        owner_continuation: str = "YES",
        owner_reply: str = "",
    ) -> dict[str, Any]:
        """Apply OWNER_CONTINUATION_GATE_V1 after an external GREEN grade.

        The original real task is restored from durable Control Tower state and
        resumed in the SAME Arena session. Continuation before external GREEN is
        blocked, GREEN without explicit Owner continuation is blocked, and a
        same-session same-goal continuation never repeats the canary.
        """

        state, orphan_returns = self._replay()
        record = state.session_records.get(str(session_id or ""))
        if not isinstance(record, Mapping):
            raise BindingError("SESSION_ID_NOT_REGISTERED_IN_CONTROL_TOWER_LEDGER")
        canary = record.get("CANARY")
        if not isinstance(canary, Mapping) or canary.get("FAST_CANARY_REQUIRED") != "YES":
            raise BindingError("CANARY_SESSION_NOT_REQUIRED")
        grade = record.get("CANARY_GRADE")
        classification = str(grade.get("CLASSIFICATION") or "UNVERIFIED").upper() if isinstance(grade, Mapping) else "UNVERIFIED"
        if classification != "GREEN":
            raise BindingError(f"CANARY_OWNER_CONTINUATION_BLOCKED:{classification}")
        approved = str(owner_continuation or "").strip().upper() == "YES" or str(
            owner_reply or ""
        ).strip() == FALLBACK_OWNER_REPLY
        if not approved:
            raise BindingError("CANARY_OWNER_CONTINUATION_REQUIRED")
        binding_mapping = record.get("BINDING")
        if not isinstance(binding_mapping, Mapping):
            raise BindingError("CONTROL_TOWER_SESSION_BINDING_INVALID")
        binding = SessionBinding.from_mapping(binding_mapping)
        original_task = str(canary.get("ORIGINAL_TASK") or record.get("GOAL") or UNKNOWN)
        existing = record.get("CANARY_CONTINUATION")
        task_id = str(record.get("TASK_ID") or UNKNOWN)
        acceptance_criteria = tuple(record.get("ACCEPTANCE_CRITERIA") or ())
        stored_recommendation = record.get("RECOMMENDED_NEW_CHAT")
        stored_title = (
            stored_recommendation.get("CHAT_TITLE")
            if isinstance(stored_recommendation, Mapping)
            else None
        )
        chat_title_override = stored_title if isinstance(stored_title, str) else None
        skill_handoff = (
            dict(record.get("SKILL_HANDOFF"))
            if isinstance(record.get("SKILL_HANDOFF"), Mapping)
            else None
        )
        arena_checkpoint = None
        if binding.host == "ARENA":
            arena_checkpoint = _load_arena_prompt_checkpoint(
                self.root,
                binding,
                original_task,
                task_id,
                acceptance_criteria,
                session_checkpoint=(
                    f"SESSION_ID={binding.session_id}; TASK_ID={task_id}; "
                    "CANARY_GRADE=GREEN; OWNER_CONTINUATION=YES; EXECUTION_PROGRESS=NOT_RECORDED"
                ),
            )
        if isinstance(existing, Mapping) and existing.get("OWNER_CONTINUATION") == "YES":
            recommendation = record.get("RECOMMENDED_NEW_CHAT")
            if isinstance(recommendation, Mapping):
                if binding.host == "ARENA":
                    recommendation = _session_recommendation(
                        binding,
                        task_prompt=original_task,
                        worktree=str(record.get("WORKTREE") or UNKNOWN),
                        branch=str(record.get("BRANCH") or UNKNOWN),
                        canonical_base_sha=str(record.get("CANONICAL_BASE_SHA") or UNKNOWN),
                        canonical_base_tree=str(record.get("CANONICAL_BASE_TREE") or UNKNOWN),
                        acceptance_criteria=acceptance_criteria,
                        task_id=task_id,
                        arena_prompt_checkpoint=arena_checkpoint,
                        chat_mode="SAME_CHAT",
                        chat_title_override=chat_title_override,
                        skill_handoff=skill_handoff,
                    )
                    recommendation.update(
                        {"CANARY_REPEAT": "NO", "CONTINUATION_MODE": "RESUME_ORIGINAL_TASK_IN_SAME_SESSION"}
                    )
                return {
                    "status": "PASS",
                    "idempotent": True,
                    "binding": binding.to_dict(),
                    "task_id": record.get("TASK_ID", UNKNOWN),
                    "canary_classification": classification,
                    "canary_repeat": "NO",
                    "recommendation": dict(recommendation),
                    "snapshot": self._projection(state, orphan_returns),
                }
        recommendation = _session_recommendation(
            binding,
            task_prompt=original_task,
            worktree=str(record.get("WORKTREE") or UNKNOWN),
            branch=str(record.get("BRANCH") or UNKNOWN),
            canonical_base_sha=str(record.get("CANONICAL_BASE_SHA") or UNKNOWN),
            canonical_base_tree=str(record.get("CANONICAL_BASE_TREE") or UNKNOWN),
            acceptance_criteria=acceptance_criteria,
            task_id=task_id,
            arena_prompt_checkpoint=arena_checkpoint,
            chat_mode="SAME_CHAT" if binding.host == "ARENA" else "NEW_CHAT",
            chat_title_override=chat_title_override,
            skill_handoff=skill_handoff,
        )
        recommendation["CANARY_REPEAT"] = "NO"
        recommendation["CONTINUATION_MODE"] = "RESUME_ORIGINAL_TASK_IN_SAME_SESSION"
        recommendation["CANARY_CLASSIFICATION"] = classification
        recommendation["SESSION_POLICY"] = CANARY_SESSION_POLICIES[classification]
        recommendation["ORIGINAL_TASK_SOURCE"] = "CONTROL_TOWER_DURABLE_STATE"
        event = {
            "schema": CANARY_CONTINUATION_EVENT_SCHEMA,
            "event_type": "CONTROL_TOWER_CANARY_CONTINUATION",
            "SESSION_ID": binding.session_id,
            "HOST": binding.host,
            "GOAL_ID": binding.goal_id,
            "GOAL": binding.goal,
            "TASK_ID": str(record.get("TASK_ID") or UNKNOWN),
            "GATE": OWNER_CONTINUATION_GATE_V1,
            "CANARY_CLASSIFICATION": classification,
            "SESSION_POLICY": CANARY_SESSION_POLICIES[classification],
            "OWNER_CONTINUATION": "YES",
            "OWNER_REPLY": str(owner_reply or FALLBACK_OWNER_REPLY),
            "ORIGINAL_TASK_SOURCE": "CONTROL_TOWER_DURABLE_STATE",
            "ORIGINAL_TASK": original_task,
            "CANARY_REPEAT": "NO",
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
            "task_id": record.get("TASK_ID", UNKNOWN),
            "canary_classification": classification,
            "canary_repeat": "NO",
            "recommendation": recommendation,
            "snapshot": self.snapshot(),
        }

    def recommend_next_session(
        self,
        host: str,
        *,
        session_id: str | None = None,
        worktree: str = UNKNOWN,
        branch: str = UNKNOWN,
        host_discovery_record: Mapping[str, Any] | None = None,
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
                existing_session = SessionBinding.from_mapping(existing_binding)
                if existing_session.host != normalized_host:
                    return {
                        "status": "BLOCKED",
                        "reason": "ACTIVE_SESSION_HOST_MISMATCH",
                        "task_id": task.task_id,
                        "automatic_start": False,
                        "recommendation": None,
                    }
                existing_handoff = record.get("SKILL_HANDOFF")
                # F01: never trust cached SKILL_HOST_MODE to skip validation.
                # If the cached RECOMMENDED_NEW_CHAT still carries a generic
                # skill prompt, any missing/wrong-type/empty/NOT_REQUIRED
                # session handoff must be treated as stale and BLOCKED.
                is_generic_cached = False
                if isinstance(recommendation, Mapping):
                    rh = recommendation.get("SKILL_HANDOFF")
                    if isinstance(rh, Mapping):
                        rh_mode = str(rh.get("SKILL_HOST_MODE") or "")
                        rh_check = str(rh.get("SKILL_CHECK") or "").upper()
                        rh_selected = rh.get("SKILLS_SELECTED") or ()
                        rh_required = rh.get("REQUIRED_SKILLS") or ()
                        if rh_mode == "GENERIC_EXACT_REPO_READ":
                            is_generic_cached = True
                        elif rh_check == "PASS" and (rh_selected or rh_required):
                            is_generic_cached = True
                        elif rh_required:
                            is_generic_cached = True
                    if recommendation.get("REQUIRED_SKILLS"):
                        is_generic_cached = True
                if isinstance(existing_handoff, Mapping) and str(existing_handoff.get("SKILL_HOST_MODE") or "") == "GENERIC_EXACT_REPO_READ":
                    is_generic_cached = True
                should_validate = is_generic_cached or isinstance(existing_handoff, Mapping)
                if is_generic_cached and not isinstance(existing_handoff, Mapping):
                    should_validate = True
                if should_validate:
                    from .skill_consumption import validate_cached_skill_handoff_host_evidence
                    host_evidence = validate_cached_skill_handoff_host_evidence(
                        self.root,
                        host=normalized_host,
                        skill_handoff=existing_handoff,
                        host_discovery_record=host_discovery_record,
                    )
                    if not host_evidence.get("valid"):
                        return {
                            "status": "BLOCKED",
                            "reason": (
                                "SKILL_HANDOFF_HOST_EVIDENCE_STALE:"
                                + str(host_evidence.get("reason") or "UNKNOWN")
                            ),
                            "task_id": task.task_id,
                            "automatic_start": False,
                            "recommendation": None,
                        }
                if normalized_host == "ARENA":
                    arena_checkpoint = _arena_prompt_checkpoint(
                        existing_session,
                        task.purpose,
                        task.task_id,
                        task.acceptance_requirements,
                        plan=plan,
                        task_record=task,
                    )
                    recommendation = _session_recommendation(
                        existing_session,
                        task_prompt=task.purpose,
                        worktree=worktree,
                        branch=branch,
                        acceptance_criteria=task.acceptance_requirements,
                        task_id=task.task_id,
                        arena_prompt_checkpoint=arena_checkpoint,
                        skill_handoff=(
                            dict(existing_handoff)
                            if isinstance(existing_handoff, Mapping)
                            else None
                        ),
                    )
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
        arena_checkpoint = (
            _arena_prompt_checkpoint(
                binding,
                task.purpose,
                task.task_id,
                task.acceptance_requirements,
                plan=plan,
                task_record=task,
            )
            if normalized_host == "ARENA"
            else None
        )
        preview_skill_handoff = None
        skill_registry_available = (
            self.root / ".p2p" / "system" / "p2p_capabilities"
            / "capabilities.json"
        ).is_file()
        if skill_registry_available:
            from .skill_consumption import prepare_skill_handoff
            preview_skill_handoff = prepare_skill_handoff(
                self.root,
                task.purpose,
                host=normalized_host,
                host_discovery_record=host_discovery_record,
            )
            if preview_skill_handoff.get("SKILL_CHECK") == "BLOCKED":
                return {
                    "status": "BLOCKED",
                    "reason": "SKILL_HANDOFF_BLOCKED",
                    "task_id": task.task_id,
                    "automatic_start": False,
                    "recommendation": None,
                }
        recommendation = _session_recommendation(
            binding,
            task_prompt=task.purpose,
            worktree=worktree,
            branch=branch,
            acceptance_criteria=task.acceptance_requirements,
            task_id=task.task_id,
            arena_prompt_checkpoint=arena_checkpoint,
            skill_handoff=preview_skill_handoff,
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
        host_discovery_record: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        result = self.recommend_next_session(
            host,
            session_id=session_id,
            worktree=worktree,
            branch=branch,
            host_discovery_record=host_discovery_record,
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
            host_discovery_record=host_discovery_record,
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
    host_discovery_record: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return ControlTower(root).recommend_next_session(
        host,
        session_id=session_id,
        worktree=worktree,
        branch=branch,
        host_discovery_record=host_discovery_record,
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
    canary_directive: CanaryDirective | None = None,
    max_prompt_chars: int | None = None,
    task_id: str = UNKNOWN,
    arena_prompt_checkpoint: Mapping[str, str] | None = None,
    chat_mode: str = "NEW_CHAT",
    chat_title_override: str | None = None,
    skill_handoff: Mapping[str, Any] | None = None,
) -> str:
    """Build a self-contained recursive prompt for one compatible host.

    When ``canary_directive`` is supplied the prompt automatically enters
    FAST_CANARY: the first safe real-task slice is the canary, the executor
    returns evidence only and stops, and full continuation requires external
    grading plus explicit Owner continuation. Required canary context is never
    silently truncated or evicted; if it cannot fit inside the deterministic
    prompt budget the call fails closed.
    """

    if not isinstance(binding, SessionBinding):
        raise ControlTowerHandoffError("SESSION_BINDING_REQUIRED")
    if canary_directive is not None and not isinstance(canary_directive, CanaryDirective):
        raise ControlTowerHandoffError("CANARY_DIRECTIVE_REQUIRED")
    task = _text(task_prompt, "task_prompt", max_length=12000)
    worktree_value = _location(worktree, "worktree")
    branch_value = _location(branch, "branch")
    sha_value = _hash_or_unknown(canonical_base_sha, "canonical_base_sha")
    tree_value = _hash_or_unknown(canonical_base_tree, "canonical_base_tree")
    criteria = _refs(acceptance_criteria, "acceptance_criteria", max_length=4096)
    canary_turn = canary_directive is not None
    chat_mode_value = "NEW_CHAT"
    arena_context: dict[str, str] | None = None
    if binding.host == "ARENA":
        chat_mode_value = _text(chat_mode, "chat_mode", max_length=32).upper()
        if chat_mode_value not in {"NEW_CHAT", "SAME_CHAT"}:
            raise BindingError("ARENA_CHAT_MODE_INVALID")
        raw_context = arena_prompt_checkpoint or _arena_prompt_checkpoint(
            binding,
            task,
            task_id,
            criteria,
        )
        required_context_fields = (
            "project",
            "plan_reference",
            "already_completed",
            "current_checkpoint",
            "blocker_or_owner_gate",
            "next_bounded_step",
        )
        if not isinstance(raw_context, Mapping) or any(key not in raw_context for key in required_context_fields):
            raise BindingError("ARENA_PROMPT_CHECKPOINT_INCOMPLETE")
        arena_context = {
            key: _checkpoint_text(raw_context[key], key)
            for key in required_context_fields
        }
    skill_lines: tuple[str, ...] = ()
    if isinstance(skill_handoff, Mapping):
        from .skill_consumption import skill_handoff_prompt_lines
        skill_lines = skill_handoff_prompt_lines(skill_handoff)

    if canary_turn:
        # ONE first-turn return contract: the canary evidence packet, then STOP.
        # The terminal CONTROL_TOWER_RETURN_PACKET contract belongs to the
        # resumed ORIGINAL task and is supplied at Owner continuation.
        criteria_header = "ACCEPTANCE_CRITERIA (ORIGINAL_REAL_TASK; evaluated after Owner continuation, not in this canary turn):"
        criteria_text = "\n".join(f"- {item}" for item in criteria) or "- Defined by ORIGINAL_REAL_TASK."
        return_rule = (
            "- FAST_CANARY turn (see FIRST_TURN_RETURN_CONTRACT below): end this turn with "
            "CANARY_EVIDENCE_PACKET_V1 plus the checkpoint metadata only; do not emit a "
            "CONTROL_TOWER_RETURN_PACKET or any terminal verdict in this turn."
        )
        return_contract_lines: tuple[str, ...] = canary_resumed_task_pointer_lines()
    else:
        criteria_header = "ACCEPTANCE_CRITERIA:"
        criteria_text = "\n".join(f"- {item}" for item in criteria) or "- Return a truthful terminal packet."
        return_rule = "- Finish with one structured CONTROL_TOWER_RETURN_PACKET."
        return_contract_lines = _terminal_return_contract_lines()
    title_lines: tuple[str, ...] = ()
    if binding.host == "ARENA":
        assert arena_context is not None
        title = (
            _checkpoint_text(chat_title_override, "chat_title", max_length=120)
            if chat_title_override is not None
            else _arena_chat_title(binding, arena_context["project"])
        )
        title_lines = (
            title,
            "GỬI CHO: ARENA AI",
            f"PROJECT={arena_context['project']}",
            f"CHAT_MODE={chat_mode_value}",
            f"CHAT_TITLE={title}",
            f"CHAT_NAME={title}",
            f"PLAN_REFERENCE={arena_context['plan_reference']}",
            f"ALREADY_COMPLETED={arena_context['already_completed']}",
            f"CURRENT_CHECKPOINT={arena_context['current_checkpoint']}",
            f"BLOCKER_OR_OWNER_GATE={arena_context['blocker_or_owner_gate']}",
            f"NEXT_BOUNDED_STEP={arena_context['next_bounded_step']}",
            "",
        )
    prompt = "\n".join(
        (
            *title_lines,
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
            criteria_header,
            criteria_text,
            "",
            "P2P_SUPREME_LAW_PREFLIGHT:",
            "- TASK_BRANCH != LAW_AUTHORITY and TARGET_PROJECT != LAW_SOURCE. The current target repository, worktree, and branch are execution state only and must never decide which Supreme Law version applies.",
            f"- Canonical law source: {SUPREME_LAW_CANONICAL_REPO}@{SUPREME_LAW_CANONICAL_REF}:{SUPREME_LAW_DEVELOPMENT_PATH}. Read it when that canonical source is accessible, even when the task executes in a different repository or branch.",
            f"- In an installed project, {SUPREME_LAW_INSTALLED_PATH} may be used only when it contains P2P_SUPREME_OPERATING_LAW_V1; a stale task-branch copy is not higher authority than the inline capsule.",
            "- The inline SUPREME_LAW_CAPSULE below is always included. If the canonical P2P source is unavailable or the local copy is stale/missing, the capsule is the authoritative minimum operating law for this execution.",
            "- Do not claim that a repository file was read unless it actually was.",
            "- Apply the law to outcome, authority, next useful action, verification, retry/stuckness, and stopping; do not turn preflight into a separate report.",
            "SUPREME_LAW_CAPSULE:",
            SUPREME_LAW_CAPSULE,
            "",
            *skill_lines,
            *(("",) if skill_lines else ()),
            "SESSION_RULES:",
            "- Use the explicit HOST above as authoritative; never infer a host from narrative prose.",
            "- Do not inherit chat history, prior session state, or implicit context.",
            "- Do not promote, merge, deploy, release, or perform a protected action from this prompt.",
            return_rule,
            "",
            *(canary_prompt_lines(canary_directive) if canary_directive is not None else ()),
            *(("",) if canary_turn else ()),
            *return_contract_lines,
            "",
            USER_ACTION_BLOCK,
        )
    )
    prompt_budget = max_prompt_chars
    if binding.host == "ARENA" and prompt_budget is None:
        prompt_budget = CANARY_PROMPT_BUDGET_GUARD_CHARS
    if prompt_budget is not None and len(prompt) > prompt_budget:
        # Required routing/checkpoint and canary context must never be truncated.
        if canary_directive is not None:
            raise BindingError(
                "CONTROL_TOWER_CANARY_CONTEXT_DID_NOT_FIT:"
                f"chars={len(prompt)}:budget={prompt_budget}"
            )
        if binding.host == "ARENA":
            raise BindingError(
                "CONTROL_TOWER_ARENA_ROUTING_CONTEXT_DID_NOT_FIT:"
                f"chars={len(prompt)}:budget={prompt_budget}"
            )
    return prompt


def _terminal_return_contract_lines() -> tuple[str, ...]:
    """The existing terminal CONTROL_TOWER_RETURN_PACKET contract (non-canary turns)."""

    return (
        "CONTROL_TOWER_RETURN_PACKET:",
        PACKET_BEGIN,
        f'Return exactly one JSON object with "schema":"{CONTROL_TOWER_PACKET_SCHEMA}" between these markers.',
        'The JSON object must include "CONTROL_TOWER_RETURN_PACKET":true as a boolean marker.',
        "SESSION_STATE must be one of COMPLETED, READY, WAITING_OWNER_GATE, BLOCKED, FAILED, or ABORTED.",
        "Include SESSION_ID, HOST, GOAL_ID, GOAL, SESSION_STATE, CANONICAL_BASE_SHA, CANONICAL_BASE_TREE,",
        "CANONICAL_RELATION, WORKTREE, BRANCH, CHANGES, TEST_RESULTS, EVIDENCE,",
        "CANDIDATE_OR_CHECKPOINT_SHA, TERMINAL_VERDICT, OWNER_GATE, BLOCKERS, and NEXT_RECOMMENDED_ACTION.",
        "Include actor-own LAW_CHECK, EXPERIENCE_CHECK, and LEARNING_RECONCILIATION in the JSON packet.",
        "LAW_CHECK must be source-bound; EXPERIENCE_CHECK must use the existing receipt vocabulary;",
        "LEARNING_RECONCILIATION must be NONE or CANDIDATE according to the existing task-end policy.",
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
