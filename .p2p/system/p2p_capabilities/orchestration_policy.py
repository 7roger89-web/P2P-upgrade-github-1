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

from .security_contract import (
    ACTIVE_TEST_AUTHORIZED,
    ANALYSIS_LOCAL,
    DESTRUCTIVE_OR_INTRUSIVE,
    OFFENSIVE_HIGH_RISK,
    SAFE_READONLY,
    SECURITY_EXECUTION_CLASSES,
    authorize_security_execution,
    normalize_execution_class,
)


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

# These principles and lanes are part of the existing C18 policy output. They
# do not create a second router or execution engine; they make the policy's
# lowest-safe execution choice explicit before any host/runtime binding.
MINIMUM_SUFFICIENT_WORK = "MINIMUM_SUFFICIENT_WORK"
RISK_PROPORTIONAL_EXECUTION = "RISK_PROPORTIONAL_EXECUTION"
FAST = "FAST"
STRICT = "STRICT"
CRITICAL = "CRITICAL"
EXECUTION_LANES = (FAST, STANDARD, STRICT, CRITICAL)

# OWNER_MICRO_LOOP_SUPPRESSION (P2P-CONTEXT-HYGIENE-01 / notebook RULE 11).
# A bounded finding and the repairs it directly induces stay inside the SAME
# Writer repair loop; they are not relayed to the Owner as decisions.  Only
# real Owner Gates escalate.  This policy classifies requests -- it grants
# nothing and removes no real Owner Gate.
OWNER_MICRO_LOOP_SUPPRESSION = "OWNER_MICRO_LOOP_SUPPRESSION"
OWNER_GATE_CLASSES = (
    # MERGE_PROMOTION = a merge that itself constitutes canonical
    # promotion/release, i.e. the promotion action.  It stays an Owner Gate.
    # An ordinary code merge into canonical main is classified as
    # VALIDATED_PR_MERGE instead (see VALIDATED_PR_AUTO_MERGE_AUTHORITY).
    "MERGE_PROMOTION",
    "PRODUCTION_DEPLOY",
    "DESTRUCTIVE_MUTATION",
    "SECRETS",
    "MAJOR_SPEND_INFRASTRUCTURE",
    "HARD_ROLLBACK",
    "SCOPE_CHANGING_BLOCKER",
)
OWNER_MICRO_REPAIR_CLASSES = (
    "FINDING",
    "FIXTURE_REPAIR",
    "FOCUSED_TEST_REPAIR",
    "EVIDENCE_COUNT_CORRECTION",
    "REMOTE_SYNC_CORRECTION",
)

# VALIDATED_PR_AUTO_MERGE_AUTHORITY (notebook RULE 11, standing Owner
# authorization).  A fully validated PR merge into canonical main is a
# routine integration step and is not re-asked of the Owner.  Promotion,
# release, and deployment are NOT authorized by it and stay Owner Gates.
# This classification grants nothing: every condition must be affirmatively
# proven `True` by the caller, and anything missing, false, or uncertain
# routes back to the Owner Gate.
VALIDATED_PR_AUTO_MERGE_AUTHORITY = "VALIDATED_PR_AUTO_MERGE_AUTHORITY"
VALIDATED_PR_MERGE = "VALIDATED_PR_MERGE"
STANDING_AUTHORITY_MERGE = "STANDING_AUTHORITY_MERGE"
VALIDATED_MERGE_CONDITIONS = (
    "exact_head_fresh_checked",
    "validation_evidence_sufficient",
    "required_checks_passed_or_baseline_unrelated",
    "no_unresolved_blocker",
    "mergeable_against_current_target",
    "scope_unchanged_since_validation",
    "no_separately_gated_side_effect",
)

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
    "blast_radius": {"EXPECTED", "MATERIAL", "UNKNOWN"},
    "dependency_path": {"CLEAR", "UNCLEAR", "UNKNOWN"},
    "targeted_evidence": {"SUFFICIENT", "INSUFFICIENT", "UNKNOWN"},
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
    execution_class: str = SAFE_READONLY
    target_authorized: bool = False
    controlled_test_environment: bool = False
    explicit_task_authority: bool = False
    context_proxy_bytes: int = 0
    context_refs: tuple[str, ...] = ()
    source_mutation: bool = False
    runtime_change: bool = False
    registry_change: bool = False
    governance_change: bool = False
    security_risk: bool = False
    promotion: bool = False
    destructive: bool = False
    blast_radius: str = "EXPECTED"
    dependency_path: str = "CLEAR"
    targeted_evidence: str = "SUFFICIENT"
    acceptance_requires_testing: bool = False
    unexplained_material_failure: bool = False
    acceptance_proven: bool = False
    baseline_failure: bool = False
    baseline_invalidates_acceptance: bool = False
    baseline_on_dependency_path: bool = False
    baseline_safety_risk: bool = False

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
        try:
            execution_class = normalize_execution_class(value.get("execution_class", SAFE_READONLY))
        except ValueError as exc:
            raise OrchestrationPolicyError(str(exc)) from exc
        if "dependency_path_clear" in value:
            dependency_path = "CLEAR" if _bool(value["dependency_path_clear"], "dependency_path_clear") else "UNCLEAR"
        else:
            dependency_path = enum("dependency_path", "CLEAR")
        if "targeted_evidence_sufficient" in value:
            targeted_evidence = "SUFFICIENT" if _bool(
                value["targeted_evidence_sufficient"], "targeted_evidence_sufficient"
            ) else "INSUFFICIENT"
        else:
            targeted_evidence = enum("targeted_evidence", "SUFFICIENT")
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
            execution_class=execution_class,
            target_authorized=boolean("target_authorized", False),
            controlled_test_environment=boolean("controlled_test_environment", False),
            explicit_task_authority=boolean("explicit_task_authority", False),
            context_proxy_bytes=raw_bytes,
            context_refs=_refs(value.get("context_refs", ()), "context_refs"),
            source_mutation=boolean("source_mutation", False),
            runtime_change=boolean("runtime_change", False),
            registry_change=boolean("registry_change", False),
            governance_change=boolean("governance_change", False),
            security_risk=boolean("security_risk", False),
            promotion=boolean("promotion", False),
            destructive=boolean("destructive", False),
            blast_radius=enum("blast_radius", "EXPECTED"),
            dependency_path=dependency_path,
            targeted_evidence=targeted_evidence,
            acceptance_requires_testing=boolean("acceptance_requires_testing", False),
            unexplained_material_failure=boolean("unexplained_material_failure", False),
            acceptance_proven=boolean("acceptance_proven", False),
            baseline_failure=boolean("baseline_failure", False),
            baseline_invalidates_acceptance=boolean("baseline_invalidates_acceptance", False),
            baseline_on_dependency_path=boolean("baseline_on_dependency_path", False),
            baseline_safety_risk=boolean("baseline_safety_risk", False),
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
        or profile.execution_class in {
            ACTIVE_TEST_AUTHORIZED,
            OFFENSIVE_HIGH_RISK,
            DESTRUCTIVE_OR_INTRUSIVE,
        }
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


def _execution_lane(profile: TaskProfile) -> tuple[str, list[str]]:
    """Select the lowest safe execution lane from material evidence only."""

    critical: list[str] = []
    if profile.execution_class in {
        ACTIVE_TEST_AUTHORIZED,
        OFFENSIVE_HIGH_RISK,
        DESTRUCTIVE_OR_INTRUSIVE,
    }:
        critical.append("SECURITY_EXECUTION_CLASS")
    if profile.security_risk:
        critical.append("SECURITY_RISK")
    if profile.production:
        critical.append("PRODUCTION_RISK")
    if profile.financial:
        critical.append("FINANCIAL_RISK")
    if profile.network_or_secret:
        critical.append("SECRET_OR_NETWORK_RISK")
    if profile.promotion or profile.task_kind in {"PROMOTION", "RELEASE", "DEPLOYMENT"}:
        critical.append("PROMOTION_OR_RELEASE_BOUNDARY")
    if profile.destructive or profile.mutation_risk == "DESTRUCTIVE":
        critical.append("DESTRUCTIVE_RISK")
    if profile.owner_gate != "NOT_REQUIRED":
        critical.append("OWNER_AUTHORITY_GATE")
    if profile.reversibility in {"IRREVERSIBLE", "UNKNOWN"}:
        critical.append("IRREVERSIBILITY_NOT_SAFE")
    if profile.mutation_risk == "UNKNOWN":
        critical.append("MUTATION_RISK_UNKNOWN")
    if profile.task_kind in {"SECURITY", "SECURITY_ANALYSIS"}:
        critical.append("SECURITY_TASK")
    if profile.baseline_failure and profile.baseline_safety_risk:
        critical.append("BASELINE_SAFETY_RISK")
    if critical:
        return CRITICAL, sorted(set(critical))

    strict: list[str] = []
    if profile.registry_change or profile.task_kind in {"REGISTRY", "REGISTRY_CHANGE"}:
        strict.append("REGISTRY_CHANGE")
    if profile.runtime_change or profile.task_kind in {"RUNTIME", "RUNTIME_CHANGE"}:
        strict.append("RUNTIME_CHANGE")
    if profile.governance_change:
        strict.append("GOVERNANCE_CHANGE")
    if profile.blast_radius in {"MATERIAL", "UNKNOWN"}:
        strict.append("BLAST_RADIUS_MATERIAL_OR_UNKNOWN")
    if profile.dependency_path in {"UNCLEAR", "UNKNOWN"}:
        strict.append("DEPENDENCY_PATH_UNCLEAR")
    if profile.targeted_evidence in {"INSUFFICIENT", "UNKNOWN"}:
        strict.append("TARGETED_EVIDENCE_INSUFFICIENT")
    if profile.acceptance_clarity in {"MISSING", "UNKNOWN"}:
        strict.append("ACCEPTANCE_NOT_ESTABLISHED")
    if profile.evidence_availability in {"MISSING", "UNKNOWN"}:
        strict.append("EVIDENCE_NOT_ESTABLISHED")
    if profile.mutation_risk == "HIGH":
        strict.append("HIGH_MUTATION_RISK")
    if profile.migration:
        strict.append("MIGRATION_CHANGE")
    if profile.shared_resource_risk:
        strict.append("SHARED_RESOURCE_RISK")
    if profile.baseline_failure and (
        profile.baseline_invalidates_acceptance or profile.baseline_on_dependency_path
    ):
        strict.append("BASELINE_AFFECTS_ACCEPTANCE_OR_DEPENDENCY")
    if strict:
        return STRICT, sorted(set(strict))

    standard: list[str] = []
    if profile.execution_class == ANALYSIS_LOCAL:
        standard.append("LOCAL_SECURITY_ANALYSIS")
    if profile.source_mutation:
        standard.append("SOURCE_MUTATION_REQUIRED")
    if profile.mutation_risk == "LOW":
        standard.append("MATERIAL_MUTATION_SIGNAL")
    if profile.acceptance_requires_testing:
        standard.append("ACCEPTANCE_TESTING_REQUIRED")
    if standard:
        return STANDARD, sorted(set(standard))

    return FAST, ["NO_MATERIAL_ESCALATION_SIGNAL"]


def _jit_skills(profile: TaskProfile, lane: str) -> list[str]:
    """Return only skills justified by the current policy evidence."""

    skills: list[str] = []
    if profile.source_mutation:
        skills.append("coder")
    if profile.unexplained_material_failure:
        skills.append("debugging")
    testing_required = (
        profile.acceptance_requires_testing
        or profile.source_mutation
        or profile.runtime_change
        or profile.registry_change
        or profile.governance_change
        or lane in {STRICT, CRITICAL}
    )
    if testing_required:
        skills.append("qa")
    if lane == CRITICAL:
        skills.append("supervisor")
    return skills


def _test_ceiling(profile: TaskProfile, lane: str) -> dict[str, Any]:
    """Select the smallest validation level that the lane can require."""

    if profile.acceptance_proven:
        return {
            "ordered_levels": [],
            "selected_level": "ACCEPTANCE_PROVEN",
            "broad_full_regression": False,
            "broad_full_justification": None,
            "optional_checks_executed": False,
        }
    if lane == FAST:
        levels = ["ACCEPTANCE_SPECIFIC"] if profile.acceptance_requires_testing else []
        return {
            "ordered_levels": levels,
            "selected_level": levels[-1] if levels else "TARGETED_EVIDENCE",
            "broad_full_regression": False,
            "broad_full_justification": None,
            "optional_checks_executed": False,
        }
    if lane == STANDARD:
        return {
            "ordered_levels": ["ACCEPTANCE_SPECIFIC", "DIRECTLY_AFFECTED_MODULE"],
            "selected_level": "DIRECTLY_AFFECTED_MODULE",
            "broad_full_regression": False,
            "broad_full_justification": None,
            "optional_checks_executed": False,
        }
    if lane == STRICT:
        return {
            "ordered_levels": [
                "ACCEPTANCE_SPECIFIC",
                "DIRECTLY_AFFECTED_MODULE",
                "DEPENDENCY_NEIGHBOR",
            ],
            "selected_level": "DEPENDENCY_NEIGHBOR",
            "broad_full_regression": False,
            "broad_full_justification": None,
            "optional_checks_executed": False,
        }
    return {
        "ordered_levels": [
            "ACCEPTANCE_SPECIFIC",
            "DIRECTLY_AFFECTED_MODULE",
            "DEPENDENCY_NEIGHBOR",
            "BROAD_FULL_REGRESSION",
        ],
        "selected_level": "BROAD_FULL_REGRESSION",
        "broad_full_regression": True,
        "broad_full_justification": "CRITICAL_SECURITY_PRODUCTION_AUTHORITY_OR_DESTRUCTIVE_PREDICATE",
        "optional_checks_executed": False,
    }


def _baseline_failure_policy(profile: TaskProfile) -> dict[str, Any]:
    if not profile.baseline_failure:
        return {
            "status": "NOT_APPLICABLE",
            "action": "NONE",
            "investigation_required": False,
            "lane_escalation": False,
        }
    material = (
        profile.baseline_invalidates_acceptance
        or profile.baseline_on_dependency_path
        or profile.baseline_safety_risk
    )
    if not material:
        return {
            "status": "PRE_EXISTING_UNRELATED",
            "action": "RECORD_CLASSIFY_CONTINUE",
            "investigation_required": False,
            "lane_escalation": False,
        }
    return {
        "status": "PRE_EXISTING_MATERIAL",
        "action": "RECORD_AND_ESCALATE_WITH_EVIDENCE",
        "investigation_required": True,
        "lane_escalation": True,
    }


def _safety_invariants(profile: TaskProfile, lane: str) -> dict[str, Any]:
    mutation = profile.source_mutation or profile.runtime_change or profile.registry_change or profile.governance_change
    return {
        "canonical_integrity": "PRESERVED",
        "permission_expansion": False,
        "production_protection": "FAIL_CLOSED",
        "destructive_operations": "FAIL_CLOSED",
        "provenance": "REQUIRED",
        "owner_approval": "REQUIRED" if lane == CRITICAL else "UNCHANGED",
        "rollback": "REQUIRED_FOR_MUTATION" if mutation else "NOT_APPLICABLE",
        "promotion": "OWNER_GATE_REQUIRED" if profile.promotion else "NOT_AUTHORIZED_BY_POLICY",
        "deployment": "NOT_AUTHORIZED_BY_POLICY",
        "live_activation": "NOT_AUTHORIZED_BY_POLICY",
        "force_push": "NOT_AUTHORIZED_BY_POLICY",
    }


def _security_execution(profile: TaskProfile) -> dict[str, Any]:
    """Bind security execution semantics into the existing policy output."""

    return authorize_security_execution(
        profile.execution_class,
        target_authorized=profile.target_authorized,
        controlled_test_environment=profile.controlled_test_environment,
        explicit_task_authority=profile.explicit_task_authority,
    )


def derive_requirement(value: Mapping[str, Any] | TaskProfile) -> dict[str, Any]:
    """Derive an inspectable abstract requirement without executing anything."""

    profile = TaskProfile.from_mapping(value)
    context_class, context_reasons = _context(profile)
    verification_class, verification_reasons = _verification(profile)
    reasoning_class, reasoning_reasons = _reasoning(profile, verification_class)
    worker_strategy, worker_reasons, worker_count = _worker_strategy(profile, context_class)
    execution_lane, execution_lane_reasons = _execution_lane(profile)
    security_execution = _security_execution(profile)
    if not security_execution["allowed"]:
        worker_strategy = BLOCKED
        worker_count = 0
        worker_reasons = sorted(set(worker_reasons + ["SECURITY_AUTHORIZATION_BLOCKED"]))
    jit_skills = _jit_skills(profile, execution_lane)
    test_ceiling = _test_ceiling(profile, execution_lane)
    baseline_failure = _baseline_failure_policy(profile)
    safety_invariants = _safety_invariants(profile, execution_lane)
    reason_codes = sorted(
        set(
            context_reasons
            + verification_reasons
            + reasoning_reasons
            + worker_reasons
            + security_execution["reason_codes"]
        )
    )
    blocked = worker_strategy == BLOCKED
    return {
        "schema": POLICY_SCHEMA,
        "status": "BLOCKED" if blocked else "READY",
        "policy_principles": [MINIMUM_SUFFICIENT_WORK, RISK_PROPORTIONAL_EXECUTION],
        "execution_lane": execution_lane,
        "execution_lane_reasons": execution_lane_reasons,
        "security_execution": security_execution,
        "execution_policy": {
            "minimum_sufficient_work": "ENFORCED",
            "risk_proportional_execution": "ENFORCED",
            "default_lane": FAST,
            "selected_lane": execution_lane,
            "escalation_requires_material_evidence": True,
            "template_or_skill_recommendation_is_not_escalation_evidence": True,
        },
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
        "jit_skills": {
            "required": jit_skills,
            "coder": "coder" in jit_skills,
            "debugging": "debugging" in jit_skills,
            "qa": "qa" in jit_skills,
            "supervisor": "supervisor" in jit_skills,
            "selection_rule": "JUST_IN_TIME_ONLY",
        },
        "test_ceiling": test_ceiling,
        "baseline_failure": baseline_failure,
        "stop_rule": {
            "do_not_prove_more_than_task_requires": True,
            "acceptance_proven": profile.acceptance_proven,
            "stop_after": test_ceiling["selected_level"],
            "optional_checks_executed": test_ceiling["optional_checks_executed"],
        },
        "safety_invariants": safety_invariants,
        "provenance": {
            "profile_fingerprint": _fingerprint(profile),
            "reason_codes": reason_codes,
            "context_reasons": context_reasons,
            "reasoning_reasons": reasoning_reasons,
            "verification_reasons": verification_reasons,
            "worker_reasons": worker_reasons,
            "execution_lane": execution_lane,
            "execution_lane_reasons": execution_lane_reasons,
            "security_execution_class": profile.execution_class,
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
        "canonical_governance": {
            "denominator": 8,
            "full_quorum": "8/8",
            "adaptive_worker_count_changes_quorum": False,
            "execution_lane_changes_quorum": False,
        },
        "future_seams": [
            "CACHE_AWARE_CONTEXT",
            "TASK_TARGETED_RETRIEVAL",
            "PROJECT_REPO_MAP",
            "REAL_TOKEN_COST_TELEMETRY",
            "ADAPTIVE_PROVIDER_MODEL_RESOLUTION",
        ],
        "profile": profile.to_dict(),
    }


def _classify_validated_pr_merge(validated_merge: Any) -> dict[str, Any]:
    """Classify one validated-PR merge under the standing Owner authorization.

    Fails closed to the Owner Gate unless every canonical condition in
    `VALIDATED_MERGE_CONDITIONS` is affirmatively `True`.  Absent or empty
    evidence, a `False` value, a non-boolean value, and an omitted condition
    are all treated as unmet.  Unknown condition keys are a caller contract
    violation and raise, so a typo can never silently narrow the required
    evidence.
    """

    result: dict[str, Any] = {
        "schema": "p2p-owner-escalation-classification/1",
        "policy": VALIDATED_PR_AUTO_MERGE_AUTHORITY,
        "action": VALIDATED_PR_MERGE,
        "real_owner_gates_preserved": True,
        "owner_gate_classes": list(OWNER_GATE_CLASSES),
        "standing_authorization_scope": "MERGE_ONLY",
        "not_authorized_by_standing_authority": [
            "MERGE_PROMOTION",
            "PRODUCTION_DEPLOY",
            "SECRETS",
            "DESTRUCTIVE_MUTATION",
            "MAJOR_SPEND_INFRASTRUCTURE",
            "HARD_ROLLBACK",
        ],
    }
    if not isinstance(validated_merge, Mapping) or not validated_merge:
        result.update(
            route="OWNER_GATE",
            owner_gate_required=True,
            auto_merge="NO",
            fail_closed_reason="VALIDATED_MERGE_EVIDENCE_MISSING",
            unmet_conditions=list(VALIDATED_MERGE_CONDITIONS),
            conditions={},
        )
        return result
    unknown = sorted(set(validated_merge) - set(VALIDATED_MERGE_CONDITIONS))
    if unknown:
        raise OrchestrationPolicyError(
            "VALIDATED_MERGE_CONDITION_UNKNOWN:" + ",".join(str(key) for key in unknown)
        )
    conditions = {name: validated_merge.get(name) for name in VALIDATED_MERGE_CONDITIONS}
    unmet = [name for name, value in conditions.items() if value is not True]
    if unmet:
        result.update(
            route="OWNER_GATE",
            owner_gate_required=True,
            auto_merge="NO",
            fail_closed_reason="VALIDATED_MERGE_CONDITION_UNMET",
            unmet_conditions=unmet,
            conditions=conditions,
        )
        return result
    result.update(
        route=STANDING_AUTHORITY_MERGE,
        owner_gate_required=False,
        auto_merge="YES",
        conditions=conditions,
    )
    return result


def classify_owner_escalation(
    action: Any,
    *,
    finding_ref: Any = None,
    validated_merge: Any = None,
) -> dict[str, Any]:
    """Classify one escalation request under the notebook RULE 11 policy.

    Real Owner Gates (canonical promotion/release, production deploy,
    destructive mutation, secrets, major spend/infrastructure, hard rollback,
    genuine scope-changing blockers) always route to the Owner.  A bounded
    finding and the repairs it directly induces (fixture repair, focused test
    repair, evidence-count correction, remote-sync correction) route back
    into the SAME Writer repair loop instead of being relayed to the Owner.

    `VALIDATED_PR_MERGE` carries the Owner's standing
    VALIDATED_PR_AUTO_MERGE_AUTHORITY: it routes to STANDING_AUTHORITY_MERGE
    with no redundant Owner prompt only when every condition in
    `VALIDATED_MERGE_CONDITIONS` is affirmatively proven; anything else fails
    closed to the Owner Gate.  Unknown action classes fail closed with an
    error.  This function grants no permission and removes no real Owner Gate.
    """

    normalized = str(action).upper().strip()
    if normalized == VALIDATED_PR_MERGE:
        return _classify_validated_pr_merge(validated_merge)
    if normalized in OWNER_GATE_CLASSES:
        route = "OWNER_GATE"
    elif normalized in OWNER_MICRO_REPAIR_CLASSES:
        route = "WRITER_REPAIR_LOOP"
    else:
        raise OrchestrationPolicyError(f"ESCALATION_ACTION_INVALID:{normalized}")
    result: dict[str, Any] = {
        "schema": "p2p-owner-escalation-classification/1",
        "policy": OWNER_MICRO_LOOP_SUPPRESSION,
        "action": normalized,
        "route": route,
        "owner_gate_required": route == "OWNER_GATE",
        "real_owner_gates_preserved": True,
        "owner_gate_classes": list(OWNER_GATE_CLASSES),
    }
    if route == "WRITER_REPAIR_LOOP":
        result["suppressed_owner_relay"] = True
        result["finding_ref"] = str(finding_ref) if finding_ref else None
    return result


__all__ = [
    "ACTIVE_TEST_AUTHORIZED",
    "ANALYSIS_LOCAL",
    "BLOCKED",
    "CRITICAL",
    "CONTEXT_INSUFFICIENT",
    "CONTEXT_CLASSES",
    "DETERMINISTIC",
    "DIRECT",
    "DESTRUCTIVE_OR_INTRUSIVE",
    "EXPANDED",
    "EXECUTION_LANES",
    "FAST",
    "HIGH",
    "HIGH_RISK",
    "LOW",
    "MINIMAL",
    "MINIMUM_SUFFICIENT_WORK",
    "ONE_WORKER",
    "OrchestrationPolicyError",
    "OWNER_GATE_CLASSES",
    "OWNER_MICRO_LOOP_SUPPRESSION",
    "OWNER_MICRO_REPAIR_CLASSES",
    "STANDING_AUTHORITY_MERGE",
    "VALIDATED_MERGE_CONDITIONS",
    "VALIDATED_PR_AUTO_MERGE_AUTHORITY",
    "VALIDATED_PR_MERGE",
    "classify_owner_escalation",
    "POLICY_SCHEMA",
    "OFFENSIVE_HIGH_RISK",
    "REASONING_CLASSES",
    "STANDARD",
    "STRICT",
    "SAFE_READONLY",
    "SECURITY_EXECUTION_CLASSES",
    "TaskProfile",
    "TWO_WORKERS",
    "VERIFICATION_CLASSES",
    "WORKER_STRATEGIES",
    "RISK_PROPORTIONAL_EXECUTION",
    "derive_requirement",
]
