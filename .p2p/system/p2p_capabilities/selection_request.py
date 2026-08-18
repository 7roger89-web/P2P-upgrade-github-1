"""C37 Selection Request: the deterministic contract describing WHAT may be
selected before any candidate is examined.

SelectionRequest carries:
- task classification (risk class derived from the C18 TaskProfile vocabulary,
  not free-form scores);
- quality floor (HARD constraint, not a ranking preference);
- resource bounds (cost / tokens / latency) with explicit UNKNOWN semantics;
- reasoning-effort selection (provider-neutral effort class);
- owner constraints (provider prohibition family, effort ceilings,
  permission ceiling) which never widen;
- request revision for bounded reselection (each new revision requires
  fresh decision evidence).

Nothing in this module speaks about models, providers, or vendors by name.
All candidate-side evidence enters through SelectionEvidenceContract shapes
held by SelectionPolicy.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
import re
from typing import Any, Iterable, Mapping

UNKNOWN = "UNKNOWN"
UNKNOWN_VALUE = "UNKNOWN"

REQUEST_SCHEMA = "p2p-selection-request-c37/1"

# Reasoning effort is a neutral class. Adapters map classes to provider
# mechanics; the selection layer never mentions provider-specific flags.
REASONING_EFFORT_CLASSES = ("LOW", "MEDIUM", "HIGH", "VERY_HIGH", UNKNOWN)

# Risk class is derived strictly from C18 TaskProfile vocabulary. The
# derivation lives in selection_risk.py; this list is the canonical range.
RISK_CLASSES = ("LOW", "MATERIAL", "HIGH", UNKNOWN)

ALLOWED_RISK_SOURCES = (
    "mutation_risk",
    "production",
    "financial",
    "network_or_secret",
    "owner_gate",
    "task_size",
    "acceptance_clarity",
    "evidence_availability",
)


class SelectionRequestError(ValueError):
    """A safe, user-facing selection-request contract error."""


def _text(value: Any, field: str, max_length: int = 256) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SelectionRequestError(f"{field}_INVALID")
    if len(value) > max_length:
        raise SelectionRequestError(f"{field}_TOO_LONG")
    return value.strip()


def _text_or_unknown(value: Any, field: str, allowed: Iterable[str]) -> str:
    text = _text(value, field)
    if text not in allowed:
        raise SelectionRequestError(f"{field}_INVALID: {text}")
    return text


def _tuple(values: Iterable[str] | None, field: str) -> tuple[str, ...]:
    if values is None:
        return ()
    if isinstance(values, str):
        raise SelectionRequestError(f"{field}_MUST_BE_LIST")
    result = tuple(_text(value, f"{field}_ITEM") for value in values)
    if len(result) != len(set(result)):
        raise SelectionRequestError(f"{field}_DUPLICATE")
    return result


_NAN_DEFAULT = float("nan")


def _bounded_number(value: Any, field: str, allow_unknown: bool = True) -> float:
    if value is None:
        if allow_unknown:
            return _NAN_DEFAULT
        raise SelectionRequestError(f"{field}_REQUIRED")
    if isinstance(value, str) and value.upper() == UNKNOWN:
        if allow_unknown:
            return _NAN_DEFAULT
        raise SelectionRequestError(f"{field}_CANNOT_BE_UNKNOWN")
    if isinstance(value, float) and value != value:
        if allow_unknown:
            return _NAN_DEFAULT
        raise SelectionRequestError(f"{field}_UNKNOWN_DEFAULT_NOT_ALLOWED")
    if isinstance(value, (int, float)):
        if isinstance(value, float) and value != value:
            raise SelectionRequestError(f"{field}_INVALID")
        if value < 0:
            raise SelectionRequestError(f"{field}_NEGATIVE")
        return float(value)
    raise SelectionRequestError(f"{field}_INVALID")


def _render_number(value: Any) -> Any:
    if value is None:
        return UNKNOWN_VALUE
    if isinstance(value, float) and value != value:
        return UNKNOWN_VALUE
    if float(value).is_integer():
        return int(value)
    return value


def _stable_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True)
class OwnerConstraints:
    """Deterministic owner constraints that never widen between revisions.
    Every field holds either a concrete neutral value or UNKNOWN. An UNKNOWN
    owner constraint is fail-closed: selection cannot treat it as approval.
    """

    prohibited_provider_families: tuple[str, ...] = ()
    permission_ceiling: tuple[str, ...] = ("READ",)
    maximum_reasoning_effort: str = UNKNOWN
    require_live_certification: bool = False
    require_identity_evidence: bool = False
    notes: str = ""

    def __post_init__(self) -> None:
        _tuple(self.prohibited_provider_families, "prohibited_provider_families")
        _tuple(self.permission_ceiling, "permission_ceiling")
        if self.maximum_reasoning_effort != UNKNOWN:
            _text_or_unknown(self.maximum_reasoning_effort, "maximum_reasoning_effort",
                             REASONING_EFFORT_CLASSES)
        for item in self.permission_ceiling:
            if item not in ("NONE", "READ", "WRITE", "MUTATE", "DELETE", "OWNER_LOCAL"):
                raise SelectionRequestError(f"PERMISSION_CEILING_INVALID: {item}")
        if not isinstance(self.require_live_certification, bool) or not isinstance(
                self.require_identity_evidence, bool):
            raise SelectionRequestError("BOOLEAN_FLAG_INVALID")
        if len(self.notes) > 512:
            raise SelectionRequestError("NOTES_TOO_LONG")

    def to_dict(self) -> dict[str, Any]:
        return {
            "prohibited_provider_families": list(self.prohibited_provider_families),
            "permission_ceiling": list(self.permission_ceiling),
            "maximum_reasoning_effort": self.maximum_reasoning_effort,
            "require_live_certification": self.require_live_certification,
            "require_identity_evidence": self.require_identity_evidence,
            "notes": self.notes,
        }


@dataclass(frozen=True)
class ResourceBounds:
    """Resource bounds for the selected attempt. Bounds are HARD rejection
    constraints in SelectionPolicy; they are never silently ignored. Unknown
    bounds hold UNKNOWN and never count as approval to exceed them.
    """

    max_cost_usd: Any = _NAN_DEFAULT
    max_input_tokens: Any = _NAN_DEFAULT
    max_output_tokens: Any = _NAN_DEFAULT
    max_latency_seconds: Any = _NAN_DEFAULT
    max_total_tokens: Any = _NAN_DEFAULT

    def __post_init__(self) -> None:
        _bounded_number(self.max_cost_usd, "max_cost_usd")
        _bounded_number(self.max_input_tokens, "max_input_tokens")
        _bounded_number(self.max_output_tokens, "max_output_tokens")
        _bounded_number(self.max_latency_seconds, "max_latency_seconds")
        _bounded_number(self.max_total_tokens, "max_total_tokens")

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_cost_usd": _render_number(self.max_cost_usd),
            "max_input_tokens": _render_number(self.max_input_tokens),
            "max_output_tokens": _render_number(self.max_output_tokens),
            "max_latency_seconds": _render_number(self.max_latency_seconds),
            "max_total_tokens": _render_number(self.max_total_tokens),
        }

    @property
    def fully_known(self) -> bool:
        return all(not (v != v) for v in (
            self.max_cost_usd, self.max_input_tokens, self.max_output_tokens,
            self.max_latency_seconds, self.max_total_tokens))


@dataclass(frozen=True)
class SelectionRequest:
    """Deterministic selection request. This is a contract describing WHAT may
    be selected; it performs no selection and knows nothing about providers.

    request_revision increments on every meaningful change to this contract.
    Reselection after an exclusion/retry must carry a higher revision; a
    reselection with an identical revision and unchanged fingerprint is
    bounded and blocked by SelectionLoopGuard.
    """

    request_id: str
    task_id: str
    role_id: str
    goal_id: str
    task_fingerprint: str
    project_binding: str
    candidate_binding: str
    purpose: str
    required_capabilities: tuple[str, ...] = ()
    permission_needs: tuple[str, ...] = ()
    granted_permissions: tuple[str, ...] = ()
    risk_class: str = UNKNOWN
    quality_floor: str = UNKNOWN
    reasoning_effort: str = UNKNOWN
    context_requirement: str = UNKNOWN
    verification_requirement: str = UNKNOWN
    resource_bounds: ResourceBounds = field(default_factory=ResourceBounds)
    owner_constraints: OwnerConstraints = field(default_factory=OwnerConstraints)
    request_revision: int = 1
    expected_environment: str = UNKNOWN
    request_context_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name in ("request_id", "task_id", "role_id", "goal_id",
                     "project_binding", "candidate_binding", "purpose"):
            _text(getattr(self, name), name)
        if len(self.task_fingerprint) != 64 or not re.fullmatch(r"[0-9a-fA-F]{64}",
                                                               self.task_fingerprint):
            raise SelectionRequestError("TASK_FINGERPRINT_INVALID")
        for name, values in (("required_capabilities", self.required_capabilities),
                             ("permission_needs", self.permission_needs),
                             ("granted_permissions", self.granted_permissions),
                             ("request_context_refs", self.request_context_refs)):
            _tuple(values, name)
        _text_or_unknown(self.risk_class, "risk_class", RISK_CLASSES)
        _text_or_unknown(self.quality_floor, "quality_floor", ("LOW", "MEDIUM", "HIGH", UNKNOWN))
        _text_or_unknown(self.reasoning_effort, "reasoning_effort", REASONING_EFFORT_CLASSES)
        _text_or_unknown(self.context_requirement, "context_requirement",
                         ("NONE", "BRIEF", "TASK", "FULL", UNKNOWN))
        _text_or_unknown(self.verification_requirement, "verification_requirement",
                         ("NONE", "SAME_ENVIRONMENT", "INDEPENDENT", "CERTIFIED", UNKNOWN))
        if not isinstance(self.resource_bounds, ResourceBounds):
            raise SelectionRequestError("RESOURCE_BOUNDS_INVALID")
        if not isinstance(self.owner_constraints, OwnerConstraints):
            raise SelectionRequestError("OWNER_CONSTRAINTS_INVALID")
        if not isinstance(self.request_revision, int) or self.request_revision < 1:
            raise SelectionRequestError("REQUEST_REVISION_INVALID")
        _text_or_unknown(self.expected_environment, "expected_environment",
                         ("LOCAL_PROJECT", "LOCAL_AUTHORITATIVE_PROJECT", "UNKNOWN"))
        if self.risk_class == UNKNOWN:
            raise SelectionRequestError("RISK_CLASS_UNKNOWN_FAILS_CLOSED")

    @property
    def mutation_requested(self) -> bool:
        return bool({"WRITE", "MUTATE", "DELETE"} & set(self.permission_needs))

    def to_dict(self, *, include_request_id: bool = True) -> dict[str, Any]:
        result: dict[str, Any] = {
            "schema": REQUEST_SCHEMA,
            "task_id": self.task_id,
            "role_id": self.role_id,
            "goal_id": self.goal_id,
            "task_fingerprint": self.task_fingerprint,
            "project_binding": self.project_binding,
            "candidate_binding": self.candidate_binding,
            "purpose": self.purpose,
            "required_capabilities": list(self.required_capabilities),
            "permission_needs": list(self.permission_needs),
            "granted_permissions": list(self.granted_permissions),
            "risk_class": self.risk_class,
            "quality_floor": self.quality_floor,
            "reasoning_effort": self.reasoning_effort,
            "context_requirement": self.context_requirement,
            "verification_requirement": self.verification_requirement,
            "resource_bounds": self.resource_bounds.to_dict(),
            "owner_constraints": self.owner_constraints.to_dict(),
            "request_revision": self.request_revision,
            "expected_environment": self.expected_environment,
            "request_context_refs": list(self.request_context_refs),
        }
        if include_request_id:
            result["request_id"] = self.request_id
        return result

    @property
    def fingerprint(self) -> str:
        return _stable_sha(self.to_dict(include_request_id=False))


def _stable_sha(value: Any) -> str:
    return hashlib.sha256(_stable_json(value).encode("utf-8")).hexdigest()


__all__ = [
    "UNKNOWN",
    "UNKNOWN_VALUE",
    "REQUEST_SCHEMA",
    "REASONING_EFFORT_CLASSES",
    "RISK_CLASSES",
    "ALLOWED_RISK_SOURCES",
    "SelectionRequestError",
    "OwnerConstraints",
    "ResourceBounds",
    "SelectionRequest",
]
