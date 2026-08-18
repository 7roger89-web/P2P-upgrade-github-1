"""C37 Eligibility Filter (capability / certification / auth / permission /
environment / context).

This is the FIRST stage of the selection pipeline. A candidate that is
ineligible is EXCLUDED with a recorded reason before any cost, latency,
token, or ranking consideration exists (scenario B: cheap but ineligible
never reaches the price conversation).

The filter is declarative and inspectable: every exclusion reason is a
constant string the pipeline records in SelectionReceipt.EXCLUDED_REASONS.
No hidden scoring, no vendor branch, no retry, no fallback.

The filter never mutates request constraints: an owner-prohibited provider
family, a permission ceiling, or a reasoning-effort ceiling always narrows
the eligible set (OwnerConstraints never widen — enforced by
SelectionRequest).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence, Tuple

from .selection_request import UNKNOWN
from .selection_target import SelectionCandidateEvidence, SelectionTargetError

EXCLUDED_CAPABILITY = "TARGET_EXCLUDED_CAPABILITY"
EXCLUDED_CERTIFICATION = "TARGET_EXCLUDED_CERTIFICATION"
EXCLUDED_AUTH = "TARGET_EXCLUDED_AUTH"
EXCLUDED_PERMISSION = "TARGET_EXCLUDED_PERMISSION"
EXCLUDED_CONTEXT = "TARGET_EXCLUDED_CONTEXT"
EXCLUDED_ENVIRONMENT = "TARGET_EXCLUDED_ENVIRONMENT"
EXCLUDED_QUALITY = "TARGET_EXCLUDED_QUALITY"
EXCLUDED_OWNER_CONSTRAINT = "TARGET_EXCLUDED_OWNER_CONSTRAINT"
ELIGIBLE = "TARGET_ELIGIBLE"

EXCLUSION_REASONS = (
    EXCLUDED_CAPABILITY,
    EXCLUDED_CERTIFICATION,
    EXCLUDED_AUTH,
    EXCLUDED_PERMISSION,
    EXCLUDED_CONTEXT,
    EXCLUDED_ENVIRONMENT,
    EXCLUDED_QUALITY,
    EXCLUDED_OWNER_CONSTRAINT,
)

FILTER_SCHEMA = "p2p-selection-filter-c37/1"


def _as_set(values: Iterable[str] | None) -> set[str]:
    if values is None:
        return set()
    return {str(v).strip() for v in values if isinstance(v, str) and v.strip()}


@dataclass(frozen=True)
class EligibilityRequirements:
    """The neutral requirements a candidate must satisfy. All fields are
    capability-shaped lists; an empty list means the requirement is not
    asserted (absent requirement never excludes)."""

    required_capabilities: tuple[str, ...] = ()
    required_certifications: tuple[str, ...] = ()
    required_auth_facts: Mapping[str, Any] = ()  # key->expected truthy value
    permission_profile: tuple[str, ...] = ()
    required_context_capabilities: tuple[str, ...] = ()
    required_environment: str = UNKNOWN
    minimum_quality_class: str = UNKNOWN
    reasoning_effort_class: str = UNKNOWN
    prohibited_provider_families: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _ = _as_set(self.required_capabilities)
        _ = _as_set(self.required_certifications)
        _ = _as_set(self.required_context_capabilities)
        _ = _as_set(self.prohibited_provider_families)
        _ = _as_set(self.permission_profile)
        if isinstance(self.required_auth_facts, tuple):
            object.__setattr__(self, "required_auth_facts", {})
        if not isinstance(self.required_auth_facts, Mapping):
            raise SelectionTargetError("REQUIRED_AUTH_FACTS_MUST_BE_OBJECT")
        if self.minimum_quality_class not in ("VERIFIED_HIGH", "VERIFIED",
                                              "MIXED", UNKNOWN, "FAILED"):
            raise SelectionTargetError("MINIMUM_QUALITY_CLASS_INVALID")
        _text = self.reasoning_effort_class
        if _text not in ("LOW", "MEDIUM", "HIGH", "VERY_HIGH", UNKNOWN):
            raise SelectionTargetError("REASONING_EFFORT_CLASS_INVALID")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": FILTER_SCHEMA,
            "required_capabilities": list(self.required_capabilities),
            "required_certifications": list(self.required_certifications),
            "required_auth_facts": {str(k): v for k, v in self.required_auth_facts.items()},
            "permission_profile": list(self.permission_profile),
            "required_context_capabilities": list(self.required_context_capabilities),
            "required_environment": self.required_environment,
            "minimum_quality_class": self.minimum_quality_class,
            "reasoning_effort_class": self.reasoning_effort_class,
            "prohibited_provider_families": list(self.prohibited_provider_families),
        }

    @property
    def identity(self) -> str:
        return "sel-filter-" + _stable_sha(self.to_dict())


def _stable_sha(payload: Mapping[str, Any]) -> str:
    import hashlib
    import json
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str)
                          .encode()).hexdigest()


@dataclass(frozen=True)
class FilterDecision:
    target_id: str
    eligible: bool
    reason: str
    detail: str
    evidence_rev: int = 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_id": self.target_id,
            "eligible": self.eligible,
            "reason": self.reason,
            "detail": self.detail,
            "evidence_rev": self.evidence_rev,
        }


def _auth_fact_matches(observed: Any, expected: Any) -> bool:
    """Auth fact matching is strict equality on the JSON-safe form: an
    expired certificate, a missing claim, or a mismatched claim value is
    a failure (scenario K). Empty expected value means 'any truthy value'
    presence check."""
    if expected in ("", None):
        return observed not in ("", None, False)
    return str(observed) == str(expected)


def filter_target(req: EligibilityRequirements,
                  candidate: SelectionCandidateEvidence) -> FilterDecision:
    """Deterministic, reason-only eligibility decision. First failing gate
    wins (capabilities before permissions before environment) so that the
    recorded reason is stable and reproducible."""
    caps = set(candidate.capabilities)
    for cap in req.required_capabilities:
        if cap not in caps:
            return FilterDecision(candidate.target_id, False,
                                  EXCLUDED_CAPABILITY,
                                  f"missing capability {cap}")
    for cert in req.required_certifications:
        if cert not in set(candidate.certification_refs):
            return FilterDecision(candidate.target_id, False,
                                  EXCLUDED_CERTIFICATION,
                                  f"missing certification {cert}")
    observed_auth = dict(candidate.auth_evidence or {})
    for key, expected in req.required_auth_facts.items():
        if not _auth_fact_matches(observed_auth.get(key), expected):
            return FilterDecision(candidate.target_id, False, EXCLUDED_AUTH,
                                  f"auth fact {key} missing or invalid")
    if req.required_environment not in (UNKNOWN, candidate.environment):
        return FilterDecision(candidate.target_id, False,
                              EXCLUDED_ENVIRONMENT,
                              f"environment {candidate.environment} "
                              f"!= required {req.required_environment}")
    if req.minimum_quality_class != UNKNOWN:
        from .selection_quality import quality_floor_violated
        if quality_floor_violated(candidate.quality_class,
                                  req.minimum_quality_class):
            return FilterDecision(candidate.target_id, False,
                                  EXCLUDED_QUALITY,
                                  f"quality {candidate.quality_class} below "
                                  f"floor {req.minimum_quality_class}")
    owner_caps = set(candidate.capabilities)
    for perm in req.permission_profile:
        if perm not in owner_caps:
            return FilterDecision(candidate.target_id, False,
                                  EXCLUDED_PERMISSION,
                                  f"permission {perm} not in target "
                                  f"capabilities")
    for ctx in req.required_context_capabilities:
        if ctx not in set(candidate.context_capabilities):
            return FilterDecision(candidate.target_id, False,
                                  EXCLUDED_CONTEXT,
                                  f"missing context capability {ctx}")
    vendor = candidate.vendor_family
    if vendor not in (UNKNOWN,) and vendor in req.prohibited_provider_families:
        return FilterDecision(candidate.target_id, False,
                              EXCLUDED_OWNER_CONSTRAINT,
                              f"vendor family {vendor} is owner-prohibited")
    return FilterDecision(candidate.target_id, True, ELIGIBLE, "all gates pass")


def filter_candidates(req: EligibilityRequirements,
                      candidates: Sequence[SelectionCandidateEvidence]
                      ) -> Tuple[Tuple[FilterDecision, ...], ...]:
    return tuple(filter_target(req, c) for c in candidates)


__all__ = [
    "EXCLUDED_CAPABILITY",
    "EXCLUDED_CERTIFICATION",
    "EXCLUDED_AUTH",
    "EXCLUDED_PERMISSION",
    "EXCLUDED_CONTEXT",
    "EXCLUDED_ENVIRONMENT",
    "EXCLUDED_QUALITY",
    "EXCLUDED_OWNER_CONSTRAINT",
    "ELIGIBLE",
    "EXCLUSION_REASONS",
    "FILTER_SCHEMA",
    "EligibilityRequirements",
    "FilterDecision",
    "filter_target",
    "filter_candidates",
]
