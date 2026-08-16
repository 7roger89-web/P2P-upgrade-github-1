"""Deterministic, provider-neutral minimum-sufficient orchestration policy.

This module derives an abstract execution requirement from structured task
evidence.  It does not resolve a model/provider, execute workers, change
permissions, or replace the existing C15/C17 router and controllers.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Mapping


POLICY_SCHEMA = "p2p-adaptive-orchestration-policy/1"
DIRECT = "DIRECT"
ONE_WORKER = "ONE_WORKER"
TWO_WORKERS = "TWO_WORKERS"
BLOCKED = "BLOCKED"
WORKER_STRATEGIES = (DIRECT, ONE_WORKER, TWO_WORKERS, BLOCKED)
MINIMAL = "MINIMAL"
STANDARD = "STANDARD"
EXPANDED = "EXPANDED"
CONTEXT_INSUFFICIENT = "CONTEXT_INSUFFICIENT"
CONTEXT_CLASSES = (MINIMAL, STANDARD, EXPANDED, CONTEXT_INSUFFICIENT)
LOW = "LOW"
HIGH = "HIGH"
REASONING_CLASSES = (LOW, STANDARD, HIGH)
DETERMINISTIC = "DETERMINISTIC"
HIGH_RISK = "HIGH_RISK"
VERIFICATION_CLASSES = (DETERMINISTIC, STANDARD, HIGH_RISK)
LOCAL_SERIALIZATION_PROXY = "LOCAL_SERIALIZATION_PROXY"

_ENUMS = {
    "task_size": {"TINY", "SMALL", "MODERATE", "LARGE"},
    "dependency_complexity": {"NONE", "LOW", "HIGH", "UNKNOWN"},
    "mutation_risk": {"NONE", "LOW", "HIGH", "DESTRUCTIVE", "UNKNOWN"},
    "reversibility": {"REVERSIBLE", "PARTIAL", "IRREVERSIBLE", "UNKNOWN"},
    "ambiguity": {"LOW", "MEDIUM", "HIGH", "UNKNOWN"},
    "acceptance_clarity": {"CLEAR", "PARTIAL", "MISSING", "UNKNOWN"},
    "evidence_availability": {"COMPLETE", "PARTIAL", "MISSING", "UNKNOWN"},
    "context_breadth": {"LOCAL", "PROJECT", "CROSS_SURFACE", "BROAD"},
    "owner_gate": {"NOT_REQUIRED", "REQUIRED", "PENDING", "UNKNOWN"},
}


class OrchestrationPolicyError(ValueError):
    """Raised when a task profile cannot be interpreted safely."""


def _text(value: Any, field: str, allowed: set[str]) -> str:
    normalized = str(value).upper().strip()
    if normalized not in allowed:
        raise OrchestrationPolicyError(f"{field.upper()}_INVALID:{normalized}")
    return normalized


def _bool(value: Any, field: str) -> bool:
    if not isinstance(value, bool):
        raise OrchestrationPolicyError(f"{field.upper()}_MUST_BE_BOOLEAN")
    return value


def _refs(value: Any, field: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, (list, tuple)):
        raise OrchestrationPolicyError(f"{field.upper()}_MUST_BE_LIST")
    result = tuple(str(item).strip() for item in value if str(item).strip())
    if len(result) != len(set(result)):
        raise OrchestrationPolicyError(f"{field.upper()}_DUPLICATE")
    return result


@dataclass(frozen=True)
class TaskProfile:
    """The smallest structured profile needed for C18 decisions."""

    task_size: str = "SMALL"
    dependency_complexity: str = "NONE"
    mutation_risk: str = "NONE"
    reversibility: str = "REVERSIBLE"
    ambiguity: str = "LOW"
    acceptance_clarity: str = "CLEAR"
    evidence_availability: str = "COMPLETE"
    context_breadth: str = "LOCAL"
    specialist_need: bool = False
    isolation_value: bool = False
    independent_review_value: bool = False
    shared_resource_risk: bool = False
    owner_gate: str = "NOT_REQUIRED"
    deterministic_verifier: bool = False
    result_context_dependency: bool = False
    context_escalation_available: bool = True
    independent_ready_pair: bool = False
    material_worker_value: bool = False
    parallel_economy_passes: bool = False
    production: bool = False
    financial: bool = False
    network_or_secret: bool = False
    migration: bool = False
    task_kind: str = "IMPLEMENTATION"
    context_proxy_bytes: int = 0
    context_refs: tuple[str, ...] = ()

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any] | "TaskProfile") -> "TaskProfile":
        if isinstance(value, cls):
            return value
        if not isinstance(value, Mapping):
            raise OrchestrationPolicyError("TASK_PROFILE_MUST_BE_MAPPING")

        def enum(field: str, default: str) -> str:
            return _text(value.get(field, default), field, _ENUMS[field])

        def boolean(field: str, default: bool) -> bool:
            return _bool(value.get(field, default), field)

        raw_bytes = value.get("context_proxy_bytes", 0)
        if type(raw_bytes) is not int or raw_bytes < 0:
            raise OrchestrationPolicyError("CONTEXT_PROXY_BYTES_INVALID")
        task_kind = str(value.get("task_kind", "IMPLEMENTATION")).upper().strip()
        if not task_kind or len(task_kind) > 64:
            raise OrchestrationPolicyError("TASK_KIND_INVALID")
        return cls(
            task_size=enum("task_size", "SMALL"),
            dependency_complexity=enum("dependency_complexity", "NONE"),
            mutation_risk=enum("mutation_risk", "NONE"),
            reversibility=enum("reversibility", "REVERSIBLE"),
            ambiguity=enum("ambiguity", "LOW"),
            acceptance_clarity=enum("acceptance_clarity", "CLEAR"),
            evidence_availability=enum("evidence_availability", "COMPLETE"),
            context_breadth=enum("context_breadth", "LOCAL"),
            specialist_need=boolean("specialist_need", False),
            isolation_value=boolean("isolation_value", False),
            independent_review_value=boolean("independent_review_value", False),
            shared_resource_risk=boolean("shared_resource_risk", False),
            owner_gate=enum("owner_gate", "NOT_REQUIRED"),
            deterministic_verifier=boolean("deterministic_verifier", False),
            result_context_dependency=boolean("result_context_dependency", False),
            context_escalation_available=boolean("context_escalation_available", True),
            independent_ready_pair=boolean("independent_ready_pair", False),
            material_worker_value=boolean("material_worker_value", False),
            parallel_economy_passes=boolean("parallel_economy_passes", False),
            production=boolean("production", False),
            financial=boolean("financial", False),
            network_or_secret=boolean("network_or_secret", False),
            migration=boolean("migration", False),
            task_kind=task_kind,
            context_proxy_bytes=raw_bytes,
            context_refs=_refs(value.get("context_refs", ()), "context_refs"),
        )

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["context_refs"] = list(self.context_refs)
        return result


def _fingerprint(profile: TaskProfile) -> str:
    payload = json.dumps(profile.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _verification(profile: TaskProfile) -> tuple[str, list[str]]:
    high_risk = (
        profile.mutation_risk in {"HIGH", "DESTRUCTIVE", "UNKNOWN"}
        or profile.reversibility in {"IRREVERSIBLE", "UNKNOWN"}
        or profile.production
        or profile.financial
        or profile.network_or_secret
        or profile.migration
        or profile.owner_gate != "NOT_REQUIRED"
        or profile.task_kind in {"SECURITY", "SECURITY_ANALYSIS"}
    )
    if high_risk:
        return HIGH_RISK, ["MATERIAL_CONSEQUENCE_OR_OWNER_BOUNDARY"]
    if (
        profile.deterministic_verifier
        and profile.task_size in {"TINY", "SMALL"}
        and profile.ambiguity == "LOW"
        and profile.acceptance_clarity == "CLEAR"
        and profile.evidence_availability == "COMPLETE"
        and profile.task_kind not in {"ARCHITECTURE", "DIAGNOSIS"}
    ):
        return DETERMINISTIC, ["DETERMINISTIC_VERIFIER_SUFFICIENT"]
    return STANDARD, ["AFFECTED_EVIDENCE_AND_ACCEPTANCE_CHECKS"]


def _reasoning(profile: TaskProfile, verification: str) -> tuple[str, list[str]]:
    high_signals = (
        profile.ambiguity in {"HIGH", "UNKNOWN"}
        or profile.dependency_complexity in {"HIGH", "UNKNOWN"}
        or profile.mutation_risk in {"HIGH", "DESTRUCTIVE", "UNKNOWN"}
        or profile.reversibility in {"IRREVERSIBLE", "UNKNOWN"}
        or profile.context_breadth in {"CROSS_SURFACE", "BROAD"}
        or profile.task_kind in {"ARCHITECTURE", "DIAGNOSIS", "SECURITY_ANALYSIS"}
        or profile.result_context_dependency
    )
    if high_signals:
        reasons = ["INTERACTING_INVARIANTS_OR_UNCERTAINTY"]
        if verification == HIGH_RISK:
            reasons.append("CONSEQUENCE_REQUIRES_CAREFUL_ANALYSIS")
        return HIGH, reasons
    if profile.ambiguity == "MEDIUM" or profile.evidence_availability == "PARTIAL" or profile.acceptance_clarity == "PARTIAL":
        return STANDARD, ["BOUNDED_SYNTHESIS_OR_PARTIAL_EVIDENCE"]
    return LOW, ["LOCAL_OR_DETERMINISTIC_TASK"]


def _context(profile: TaskProfile) -> tuple[str, list[str]]:
    if profile.acceptance_clarity in {"MISSING", "UNKNOWN"} or profile.evidence_availability in {"MISSING", "UNKNOWN"}:
        return CONTEXT_INSUFFICIENT, ["ACCEPTANCE_CRITICAL_CONTEXT_UNESTABLISHED"]
    if profile.evidence_availability == "PARTIAL" and not profile.context_escalation_available:
        return CONTEXT_INSUFFICIENT, ["BOUNDED_CONTEXT_ESCALATION_UNAVAILABLE"]
    if (
        profile.task_size == "TINY"
        and profile.context_breadth == "LOCAL"
        and profile.ambiguity == "LOW"
        and profile.evidence_availability == "COMPLETE"
        and profile.acceptance_clarity == "CLEAR"
        and not profile.specialist_need
    ):
        return MINIMAL, ["TASK_LOCAL_CONTEXT_SUFFICIENT"]
    if (
        profile.context_breadth in {"CROSS_SURFACE", "BROAD"}
        or profile.ambiguity in {"HIGH", "UNKNOWN"}
        or profile.dependency_complexity in {"HIGH", "UNKNOWN"}
        or profile.evidence_availability == "PARTIAL"
        or profile.specialist_need
    ):
        return EXPANDED, ["TASK_BREADTH_OR_UNCERTAINTY_REQUIRES_BOUNDED_EXPANSION"]
    return STANDARD, ["TASK_RELEVANT_CONTEXT_REQUIRED"]


def _worker_strategy(profile: TaskProfile, context_class: str) -> tuple[str, list[str], int]:
    if profile.owner_gate != "NOT_REQUIRED":
        return BLOCKED, ["OWNER_GATE_REQUIRED_OR_PENDING"], 0
    if context_class == CONTEXT_INSUFFICIENT:
        return BLOCKED, ["CONTEXT_INSUFFICIENT"], 0
    if profile.acceptance_clarity != "CLEAR" or profile.evidence_availability == "MISSING":
        return BLOCKED, ["ACCEPTANCE_OR_EVIDENCE_NOT_READY"], 0
    if (
        profile.independent_ready_pair
        and profile.parallel_economy_passes
        and profile.material_worker_value
        and profile.task_size not in {"TINY"}
        and not profile.shared_resource_risk
        and profile.dependency_complexity == "NONE"
        and profile.result_context_dependency is False
    ):
        return TWO_WORKERS, ["TWO_READY_INDEPENDENT_TASKS_WITH_MATERIAL_VALUE"], 2
    if (
        profile.task_size == "TINY"
        and profile.deterministic_verifier
        and context_class == MINIMAL
        and not profile.specialist_need
        and not profile.independent_review_value
    ):
        return DIRECT, ["ZERO_DELEGATED_WORKERS_SUFFICIENT"], 0
    if profile.isolation_value or profile.specialist_need or profile.independent_review_value or profile.task_size == "LARGE":
        return ONE_WORKER, ["ONE_COHERENT_WORKER_HAS_MATERIAL_VALUE"], 1
    return DIRECT, ["DIRECT_PATH_HAS_SUFFICIENT_QUALITY_ADJUSTED_VALUE"], 0


def derive_requirement(value: Mapping[str, Any] | TaskProfile) -> dict[str, Any]:
    """Derive an inspectable abstract requirement without executing anything."""

    profile = TaskProfile.from_mapping(value)
    context_class, context_reasons = _context(profile)
    verification_class, verification_reasons = _verification(profile)
    reasoning_class, reasoning_reasons = _reasoning(profile, verification_class)
    worker_strategy, worker_reasons, worker_count = _worker_strategy(profile, context_class)
    reason_codes = sorted(set(context_reasons + verification_reasons + reasoning_reasons + worker_reasons))
    blocked = worker_strategy == BLOCKED
    return {
        "schema": POLICY_SCHEMA,
        "status": "BLOCKED" if blocked else "READY",
        "worker_strategy": worker_strategy,
        "worker_count": worker_count,
        "context_class": context_class,
        "reasoning_class": reasoning_class,
        "verification_class": verification_class,
        "provider_model_resolution": "DEFERRED",
        "live_execution_certification": "NOT_CERTIFIED",
        "quality_gate": {
            "acceptance_clarity": profile.acceptance_clarity,
            "evidence_availability": profile.evidence_availability,
            "owner_gate": profile.owner_gate,
            "permission_expansion": False,
            "quality_overhead_tradeoff": "QUALITY_ADJUSTED_MINIMUM_SUFFICIENT",
        },
        "provenance": {
            "profile_fingerprint": _fingerprint(profile),
            "reason_codes": reason_codes,
            "context_reasons": context_reasons,
            "reasoning_reasons": reasoning_reasons,
            "verification_reasons": verification_reasons,
            "worker_reasons": worker_reasons,
            "ordered_inputs": [
                "PROJECT_TASK_STATE",
                "TASK_CHARACTERISTICS",
                "RISK_UNCERTAINTY_ACCEPTANCE",
                "CONTEXT_NEED",
                "ORCHESTRATION_REQUIREMENT",
                "VERIFICATION_REQUIREMENT",
                "MODEL_PROVIDER_RESOLUTION_LATER",
            ],
            "hidden_reasoning_stored": False,
        },
        "context_measurement": {
            "label": LOCAL_SERIALIZATION_PROXY if profile.context_proxy_bytes else "NOT_MEASURED",
            "bytes": profile.context_proxy_bytes,
            "refs": list(profile.context_refs),
        },
        "canonical_governance": {"denominator": 8, "full_quorum": "8/8", "adaptive_worker_count_changes_quorum": False},
        "future_seams": [
            "CACHE_AWARE_CONTEXT",
            "TASK_TARGETED_RETRIEVAL",
            "PROJECT_REPO_MAP",
            "REAL_TOKEN_COST_TELEMETRY",
            "ADAPTIVE_PROVIDER_MODEL_RESOLUTION",
        ],
        "profile": profile.to_dict(),
    }


__all__ = [
    "BLOCKED",
    "CONTEXT_INSUFFICIENT",
    "CONTEXT_CLASSES",
    "DETERMINISTIC",
    "DIRECT",
    "EXPANDED",
    "HIGH",
    "HIGH_RISK",
    "LOW",
    "MINIMAL",
    "ONE_WORKER",
    "OrchestrationPolicyError",
    "POLICY_SCHEMA",
    "REASONING_CLASSES",
    "STANDARD",
    "TaskProfile",
    "TWO_WORKERS",
    "VERIFICATION_CLASSES",
    "WORKER_STRATEGIES",
    "derive_requirement",
]
