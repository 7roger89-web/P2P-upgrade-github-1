"""C37 Selection Target Evidence.

Describes what a candidate ExecutionTarget can show the selection policy:
neutral capability claims, quality evidence pointers, cost/latency/token
evidence (UNKNOWN allowed), certification/auth pointers, context capability,
and reason-effort support. The core selection policy only sees these neutral
fields; provider/vendor names are DATA on candidate evidence, never code
branches (scenario V).

REQUESTED_TARGET != OBSERVED_TARGET: the target observed at runtime must be
re-bound against the selected target identity before its evidence counts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

from .selection_request import _stable_json, _stable_sha, UNKNOWN

TARGET_EVIDENCE_SCHEMA = "p2p-selection-target-c37/1"

# Confidence classes: canonical from C35 risk vocabulary, not invented.
CONFIDENCE_CLASSES = ("HIGH", "MEDIUM", "LOW", UNKNOWN)


class SelectionTargetError(ValueError):
    """A safe, user-facing selection-target contract error."""


def _tuple(values: Iterable[str] | None, field: str) -> tuple[str, ...]:
    if values is None:
        return ()
    if isinstance(values, str):
        raise SelectionTargetError(f"{field}_MUST_BE_LIST")
    result = tuple(str(value).strip() for value in values)
    for item in result:
        if not item:
            raise SelectionTargetError(f"{field}_EMPTY_ITEM")
    if len(result) != len(set(result)):
        raise SelectionTargetError(f"{field}_DUPLICATE")
    return result


def _text(value: Any, field: str, max_length: int = 256) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SelectionTargetError(f"{field}_INVALID")
    if len(value) > max_length:
        raise SelectionTargetError(f"{field}_TOO_LONG")
    return value.strip()


def _confidence(value: Any) -> str:
    if value is None:
        return UNKNOWN
    text = str(value).upper().strip()
    return text if text in CONFIDENCE_CLASSES else UNKNOWN


def _number(value: Any) -> float:
    if value is None or (isinstance(value, str) and value.upper() == UNKNOWN):
        return float("nan")
    if isinstance(value, (int, float)):
        if isinstance(value, float) and value != value:
            return float("nan")
        return float(value)
    raise SelectionTargetError("NUMBER_INVALID")


def _render_number(value: float) -> Any:
    if isinstance(value, float) and value != value:
        return UNKNOWN
    if float(value).is_integer():
        return int(value)
    return value


@dataclass(frozen=True)
class SelectionCandidateEvidence:
    """Neutral evidence a candidate target presents. No vendor name appears
    in any code path; vendor identifiers live only inside the `vendor` data
    fields, which selection treats as opaque strings."""

    target_id: str
    target_kind: str  # harness | provider | model | protocol | tool_set | workspace | reasoning_effort | execution_target
    vendor_family: str = UNKNOWN
    model_id: str = UNKNOWN
    reasoning_effort_classes: tuple[str, ...] = ()
    capabilities: tuple[str, ...] = ()
    quality_class: str = UNKNOWN
    quality_evidence_refs: tuple[str, ...] = ()
    certification_refs: tuple[str, ...] = ()
    auth_evidence: Mapping[str, Any] = field(default_factory=dict)
    permission_profile: tuple[str, ...] = ()
    environment: str = UNKNOWN
    cost_usd: float = float("nan")
    input_tokens: float = float("nan")
    output_tokens: float = float("nan")
    latency_seconds: float = float("nan")
    failed_verification_count: int = 0
    rework_cost_ratio: float = float("nan")
    context_capabilities: tuple[str, ...] = ()
    observable_model: bool = False
    identity_evidence_refs: tuple[str, ...] = ()
    evidence_revision: int = 1
    observed_identity: str = UNKNOWN
    confidence: str = UNKNOWN

    def __post_init__(self) -> None:
        _text(self.target_id, "target_id")
        _text(self.target_kind, "target_kind")
        _text(self.vendor_family, "vendor_family")
        _text(self.model_id, "model_id")
        _tuple(self.reasoning_effort_classes, "reasoning_effort_classes")
        _tuple(self.capabilities, "capabilities")
        if self.quality_class not in ("VERIFIED_HIGH", "VERIFIED", "MIXED",
                                      UNKNOWN, "FAILED"):
            raise SelectionTargetError("QUALITY_CLASS_INVALID")
        _tuple(self.quality_evidence_refs, "quality_evidence_refs")
        _tuple(self.certification_refs, "certification_refs")
        if not isinstance(self.auth_evidence, Mapping):
            raise SelectionTargetError("AUTH_EVIDENCE_MUST_BE_OBJECT")
        _tuple(self.permission_profile, "permission_profile")
        _text(self.environment, "environment")
        _number(self.cost_usd)
        _number(self.input_tokens)
        _number(self.output_tokens)
        _number(self.latency_seconds)
        if not isinstance(self.failed_verification_count, int) or self.failed_verification_count < 0:
            raise SelectionTargetError("FAILED_VERIFICATION_COUNT_INVALID")
        _number(self.rework_cost_ratio)
        _tuple(self.context_capabilities, "context_capabilities")
        if not isinstance(self.observable_model, bool):
            raise SelectionTargetError("OBSERVABLE_MODEL_BOOLEAN_INVALID")
        _tuple(self.identity_evidence_refs, "identity_evidence_refs")
        if not isinstance(self.evidence_revision, int) or self.evidence_revision < 1:
            raise SelectionTargetError("EVIDENCE_REVISION_INVALID")
        _text(self.observed_identity, "observed_identity")
        _confidence(self.confidence)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": TARGET_EVIDENCE_SCHEMA,
            "target_id": self.target_id,
            "target_kind": self.target_kind,
            "vendor_family": self.vendor_family,
            "model_id": self.model_id,
            "reasoning_effort_classes": list(self.reasoning_effort_classes),
            "capabilities": list(self.capabilities),
            "quality_class": self.quality_class,
            "quality_evidence_refs": list(self.quality_evidence_refs),
            "certification_refs": list(self.certification_refs),
            "auth_evidence": {str(k): _safe_value(v) for k, v in self.auth_evidence.items()},
            "permission_profile": list(self.permission_profile),
            "environment": self.environment,
            "cost_usd": _render_number(self.cost_usd),
            "input_tokens": _render_number(self.input_tokens),
            "output_tokens": _render_number(self.output_tokens),
            "latency_seconds": _render_number(self.latency_seconds),
            "failed_verification_count": self.failed_verification_count,
            "rework_cost_ratio": _render_number(self.rework_cost_ratio),
            "context_capabilities": list(self.context_capabilities),
            "observable_model": self.observable_model,
            "identity_evidence_refs": list(self.identity_evidence_refs),
            "evidence_revision": self.evidence_revision,
            "observed_identity": self.observed_identity,
            "confidence": self.confidence,
        }

    @property
    def identity(self) -> str:
        return "sel-target-" + _stable_sha(self.to_dict())


def _safe_value(value: Any) -> Any:
    try:
        _stable_json(value)
        return value
    except (TypeError, ValueError):
        return UNKNOWN


__all__ = [
    "TARGET_EVIDENCE_SCHEMA",
    "CONFIDENCE_CLASSES",
    "SelectionTargetError",
    "SelectionCandidateEvidence",
]
