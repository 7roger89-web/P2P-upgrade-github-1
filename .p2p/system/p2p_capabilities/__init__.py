"""Small, offline-safe P2P capability foundation contracts."""

from .model import (
    CAPABILITY_CLASSES,
    CANONICAL_IDENTITIES,
    INVOCATION_CLASSES,
    READINESS_STATES,
    SEMANTIC_KINDS,
    TRUST_LEVELS,
    CapabilityManifest,
    ManifestValidationError,
    load_registry,
    validate_registry,
)
from .security_contract import (
    ACTIVE_TEST_AUTHORIZED,
    ANALYSIS_LOCAL,
    DECOMPILED_OUTPUT,
    DESTRUCTIVE_OR_INTRUSIVE,
    FINDING_CATEGORIES,
    NormalizedSecurityEvidence,
    NormalizedSecurityFinding,
    OFFENSIVE_HIGH_RISK,
    RECONSTRUCTED_SEMANTICS,
    ReverseEvidence,
    SAFE_READONLY,
    SECURITY_EXECUTION_CLASSES,
    SECURITY_REVERSE_CONTRACT_SCHEMA,
    SECURITY_RESULT_STATUSES,
    SecurityArtifactIdentity,
    SecurityContractError,
    authorize_security_execution,
    normalize_execution_class,
)
from .apkid_adapter import ApkidAdapter, normalize_apkid_output
from .routing import classify_capabilities, readiness_snapshot
from .context import (
    ContextPointer,
    resolve_context,
    retrieve_task_context,
    escalate_task_context,
    validate_context_reuse,
    materialize_task_context,
    build_knowledge_delta,
)
from .trust import FactClaim, InstructionBoundary, evaluate_fact_claim, classify_retrieved_item
from .evidence import EvidenceClaim, evaluate_done, detect_no_progress
from .providers import ProviderDeclaration, native_provider_state
from .specialist import validate_optional_specialist
from .skill_standard import ADAPTIVE_SKILL_FIELDS, default_uiux_contract, validate_skill_contract
from .beginner import discover_beginner_request
from .isolation import IsolationViolation, assert_isolated_target
from .domain import ProjectDomainModel
from .task_state import (
    LogicalOwner,
    PlanIdentity,
    TaskPlan,
    TaskRecord,
    TaskStateStore,
    TaskStateError,
    TaskContractError,
    TaskGraphError,
    TaskTransitionError,
    TaskEvidenceError,
    TaskGateError,
    TaskControlPlaneError,
    TaskLifecycleError,
    PLAN_LIFECYCLE_STATES,
    complete_task,
    preflight_task,
    evaluate_task_completion,
    evaluate_task_preflight,
    request_owner_decision,
    resolve_owner_decision,
    checkpoint_task,
    classify_resume,
    resume_summary,
    next_safe_task,
    dependency_handoff,
    is_active_authority,
    close_plan,
    supersede_plan,
    bind_plan_identity,
    resolve_authoritative_plan,
)
from .foreground_execution import (
    ActionResult,
    ExecutionBudget,
    ExecutionIntent,
    ExecutionRuntime,
    ForegroundExecutionController,
    ForegroundExecutionError,
    ForegroundControlPlaneError,
    ForegroundContractError,
    ForegroundScopeError,
    ForegroundBudgetError,
    ForegroundPermissionError,
    ForegroundInterrupted,
    ForegroundVerificationError,
    VerificationResult,
)
from .bounded_delegation import (
    BLOCKED,
    DELEGATE,
    DIRECT,
    MAX_DELEGATED_CHILDREN,
    MAX_DELEGATION_DEPTH,
    UNKNOWN_IDENTITY,
    BoundedDelegationController,
    BoundedDelegationError,
    ChildResult,
    CodexHostAdapter,
    DelegatedWorkerResult,
    DelegationBudget,
    DelegationContractError,
    DelegationControlPlaneError,
    DelegationDecision,
    DelegationPermissionError,
    DelegationRequest,
    DelegationScopeError,
    DelegationStaleError,
    ForegroundDelegationController,
    Handoff,
    PermissionEnvelope,
    WorkerHandoff,
    WorkerHandoffController,
    WorkerResult,
    scope_is_subset,
)
from .parallel_execution import (
    MAX_PARALLEL_CHILDREN,
    PARALLEL_LARGE_CONTEXT_BYTES,
    PARALLEL,
    PARALLEL_BLOCKED,
    PARALLEL_GROUP_RELATIVE_ROOT,
    PARALLEL_RESULT_SCHEMA,
    PARALLEL_SCHEMA,
    SEQUENTIAL,
    BoundedParallelController,
    BoundedParallelForegroundController,
    ParallelControlPlaneError,
    ParallelEconomyProfile,
    ParallelExecutionError,
    ParallelForegroundController,
    ParallelTaskContract,
)

__all__ = [
    "CAPABILITY_CLASSES",
    "CANONICAL_IDENTITIES",
    "INVOCATION_CLASSES",
    "READINESS_STATES",
    "SEMANTIC_KINDS",
    "TRUST_LEVELS",
    "CapabilityManifest",
    "ManifestValidationError",
    "load_registry",
    "validate_registry",
    "ACTIVE_TEST_AUTHORIZED",
    "ANALYSIS_LOCAL",
    "DECOMPILED_OUTPUT",
    "DESTRUCTIVE_OR_INTRUSIVE",
    "FINDING_CATEGORIES",
    "NormalizedSecurityEvidence",
    "NormalizedSecurityFinding",
    "OFFENSIVE_HIGH_RISK",
    "RECONSTRUCTED_SEMANTICS",
    "ReverseEvidence",
    "SAFE_READONLY",
    "SECURITY_EXECUTION_CLASSES",
    "SECURITY_REVERSE_CONTRACT_SCHEMA",
    "SECURITY_RESULT_STATUSES",
    "SecurityArtifactIdentity",
    "SecurityContractError",
    "authorize_security_execution",
    "normalize_execution_class",
    "ApkidAdapter",
    "normalize_apkid_output",
    "classify_capabilities",
    "readiness_snapshot",
    "ContextPointer",
    "resolve_context",
    "retrieve_task_context",
    "escalate_task_context",
    "validate_context_reuse",
    "materialize_task_context",
    "build_knowledge_delta",
    "FactClaim",
    "InstructionBoundary",
    "evaluate_fact_claim",
    "classify_retrieved_item",
    "EvidenceClaim",
    "evaluate_done",
    "detect_no_progress",
    "ProviderDeclaration",
    "native_provider_state",
    "validate_optional_specialist",
    "ADAPTIVE_SKILL_FIELDS",
    "default_uiux_contract",
    "validate_skill_contract",
    "discover_beginner_request",
    "IsolationViolation",
    "assert_isolated_target",
    "ProjectDomainModel",
    "LogicalOwner",
    "PlanIdentity",
    "TaskPlan",
    "TaskRecord",
    "TaskStateStore",
    "TaskStateError",
    "TaskContractError",
    "TaskGraphError",
    "TaskTransitionError",
    "TaskEvidenceError",
    "TaskGateError",
    "TaskControlPlaneError",
    "TaskLifecycleError",
    "PLAN_LIFECYCLE_STATES",
    "complete_task",
    "preflight_task",
    "evaluate_task_completion",
    "evaluate_task_preflight",
    "request_owner_decision",
    "resolve_owner_decision",
    "checkpoint_task",
    "classify_resume",
    "resume_summary",
    "next_safe_task",
    "dependency_handoff",
    "is_active_authority",
    "close_plan",
    "supersede_plan",
    "bind_plan_identity",
    "resolve_authoritative_plan",
    "ActionResult",
    "ExecutionBudget",
    "ExecutionIntent",
    "ExecutionRuntime",
    "ForegroundExecutionController",
    "ForegroundExecutionError",
    "ForegroundControlPlaneError",
    "ForegroundContractError",
    "ForegroundScopeError",
    "ForegroundBudgetError",
    "ForegroundPermissionError",
    "ForegroundInterrupted",
    "ForegroundVerificationError",
    "VerificationResult",
    "DIRECT",
    "DELEGATE",
    "BLOCKED",
    "MAX_DELEGATION_DEPTH",
    "MAX_DELEGATED_CHILDREN",
    "UNKNOWN_IDENTITY",
    "PermissionEnvelope",
    "DelegationBudget",
    "DelegationRequest",
    "DelegationDecision",
    "WorkerHandoff",
    "Handoff",
    "DelegatedWorkerResult",
    "CodexHostAdapter",
    "ChildResult",
    "WorkerResult",
    "BoundedDelegationController",
    "ForegroundDelegationController",
    "WorkerHandoffController",
    "BoundedDelegationError",
    "DelegationContractError",
    "DelegationScopeError",
    "DelegationPermissionError",
    "DelegationControlPlaneError",
    "DelegationStaleError",
    "scope_is_subset",
    "PARALLEL_SCHEMA",
    "PARALLEL_RESULT_SCHEMA",
    "PARALLEL_GROUP_RELATIVE_ROOT",
    "MAX_PARALLEL_CHILDREN",
    "PARALLEL_LARGE_CONTEXT_BYTES",
    "PARALLEL",
    "SEQUENTIAL",
    "PARALLEL_BLOCKED",
    "ParallelTaskContract",
    "ParallelEconomyProfile",
    "BoundedParallelForegroundController",
    "ParallelForegroundController",
    "BoundedParallelController",
    "ParallelExecutionError",
    "ParallelControlPlaneError",
]

from .host_selection import (
    AVAILABLE,
    UNAVAILABLE,
    AVAILABILITY_UNKNOWN,
    SELECTED,
    NO_COMPATIBLE_HOST,
    HOST_EVIDENCE_INSUFFICIENT,
    HostRequirementProfile,
    HostDiscoveryRecord,
    HostCandidate,
    HostSelectionDecision,
    HostSelector,
    discover_host_profiles,
    safe_reselection_allowed,
    compare_naive_policies,
)

# Host attestation — evidence-verification capability (C36 lane, exact reuse).
# Evidence surface only: no orchestration, no routing, no auth/permission
# authority, no model selection. CERTIFIED != CURRENTLY_ELIGIBLE.
# Capability intelligence — FRAMEWORK-02 deterministic-first, evidence-bound
# layer (provider-neutral, FAIL-CLOSED). One export surface; FW01 remains
# the sole operating loop.
from .capability_intelligence import (
    UNKNOWN,
    REQUIRED_OR_OPTIONAL,
    FAIL_CLOSED,
    MINIMUM_EVIDENCE_LEVELS,
    FRESHNESS_CLASSES,
    SOURCE_TYPES,
    CANONICAL_CAPABILITIES,
    CAPABILITY_VOCABULARY,
    COVERAGE_STATES,
    GAP_CLASSES,
    CapabilityRequirement,
    CapabilitySource,
    CapabilityIntelligenceError,
    ProjectProfile,
    SkillIntelligenceResult,
    CapabilityCoverage,
    CapabilityDecisionTrace,
    ExecutionRequirements,
    build_project_profile,
    build_source_inventory,
    infer_required_capabilities,
    resolve_eligibility,
    select_skills_bounded,
    evaluate_coverage,
    required_context_items,
    classify_task,
    compute_execution_requirements,
    beginner_status,
)

from .host_attestation import (
    HostAttestationError,
    HostAttestationRecord,
    make_host_attestation,
    verify_role_evidence_source,
    verify_all_attestation_sources,
    load_attestation_ledger,
    attestation_already_used,
    record_attestation_use,
    mint_dispatch_id,
)

__all__ += [
    "UNKNOWN",
    "REQUIRED_OR_OPTIONAL",
    "FAIL_CLOSED",
    "MINIMUM_EVIDENCE_LEVELS",
    "FRESHNESS_CLASSES",
    "SOURCE_TYPES",
    "CANONICAL_CAPABILITIES",
    "CAPABILITY_VOCABULARY",
    "COVERAGE_STATES",
    "GAP_CLASSES",
    "CapabilityRequirement",
    "CapabilitySource",
    "CapabilityIntelligenceError",
    "ProjectProfile",
    "SkillIntelligenceResult",
    "CapabilityCoverage",
    "CapabilityDecisionTrace",
    "ExecutionRequirements",
    "build_project_profile",
    "build_source_inventory",
    "infer_required_capabilities",
    "resolve_eligibility",
    "select_skills_bounded",
    "evaluate_coverage",
    "required_context_items",
    "classify_task",
    "compute_execution_requirements",
    "beginner_status",
]

from .static_glb_standardizer import (
    CAPABILITY_ID as STATIC_GLB_CAPABILITY_ID,
    CAPABILITY_VERSION as STATIC_GLB_CAPABILITY_VERSION,
    STATIC_CONTRACT,
    StaticGlbError,
    standardize_static_glb,
    validate_static_glb_output,
)

# Keep the compact execution capsule aligned with the canonical GitHub connector
# failure-classification law. This runs once at package import, before callers
# obtain build_execution_prompt from the control_tower_handoff submodule.
from . import control_tower_handoff as _control_tower_handoff  # noqa: E402

_GITHUB_CONNECTOR_LAW_MARKER = (
    "EXECUTOR_GITHUB_ACCESS != OWNER_GITHUB_CONNECTOR_STATUS"
)
_GITHUB_CONNECTOR_LAW_CAPSULE = "\n".join(
    (
        "8. For GitHub-dependent work, distinguish executor/session access from Owner connector state: EXECUTOR_GITHUB_ACCESS != OWNER_GITHUB_CONNECTOR_STATUS; ONE_FAILED_CALL != GITHUB_CONNECTOR_DISABLED; SESSION_TOOL_UNAVAILABLE != ACCOUNT_CONNECTION_BROKEN.",
        "9. Classify direct GitHub evidence as WORKING, SESSION_SURFACE_UNAVAILABLE, REPO_SCOPE_BROKEN, AUTH_CONNECTION_BROKEN, or PROVIDER_OUTAGE. Public web search is not proof of private repository, branch, PR, or HEAD state.",
        "10. If the current executor/session has no GitHub tool, report GITHUB_CONNECTOR_STATUS=SESSION_SURFACE_UNAVAILABLE, EXECUTOR_GITHUB_ACCESS=UNAVAILABLE_IN_THIS_SESSION, and OWNER_GITHUB_CONNECTOR_STATUS=NOT_PROVEN_BROKEN. Do not reconnect, uninstall, or change credentials without direct auth/scope evidence.",
    )
)
if _GITHUB_CONNECTOR_LAW_MARKER not in _control_tower_handoff.SUPREME_LAW_CAPSULE:
    _control_tower_handoff.SUPREME_LAW_CAPSULE = "\n".join(
        (_control_tower_handoff.SUPREME_LAW_CAPSULE, _GITHUB_CONNECTOR_LAW_CAPSULE)
    )

# Every cross-tool execution prompt should explicitly surface repository-local
# project instructions before substantive work. This is intentionally appended
# to the runtime execution capsule rather than copied into each historical task
# prompt, so one central change applies to every managed project using the P2P
# prompt builder. Project AGENTS.md remains subordinate to the valid Supreme Law.
_PROJECT_AGENT_PREFLIGHT_MARKER = "PROJECT_AGENT_INSTRUCTIONS_PREFLIGHT"
_PROJECT_AGENT_PREFLIGHT_CAPSULE = (
    "PROJECT_AGENT_INSTRUCTIONS_PREFLIGHT — Before substantive analysis, planning, "
    "implementation, review, or merge decisions in a target repository, read the "
    "repository-root AGENTS.md when present. Treat AGENTS.md as project-specific "
    "instructions subordinate to the valid P2P Supreme Law source. If AGENTS.md is "
    "absent, continue under the valid P2P law context without inventing project-specific "
    "rules. Do not claim AGENTS.md was read unless it actually was."
)
if _PROJECT_AGENT_PREFLIGHT_MARKER not in _control_tower_handoff.SUPREME_LAW_CAPSULE:
    _control_tower_handoff.SUPREME_LAW_CAPSULE = "\n".join(
        (_control_tower_handoff.SUPREME_LAW_CAPSULE, _PROJECT_AGENT_PREFLIGHT_CAPSULE)
    )

# Runtime prompt serialization must carry the two operational gates explicitly.
# This closes the gap where an executor could receive the law capsule but no
# visible instruction to report its real law source or run the canonical OE gate.
_RUNTIME_PROMPT_SERIALIZATION_MARKER = "P2P_RUNTIME_PROMPT_SERIALIZATION_CONTRACT"
_RUNTIME_PROMPT_SERIALIZATION_CAPSULE = "\n".join(
    (
        "P2P_RUNTIME_PROMPT_SERIALIZATION_CONTRACT — Every generated operational prompt must carry P2P_LAW_PREFLIGHT and OE_GATE explicitly; never rely on chat memory or an implicit prior read.",
        "P2P_LAW_PREFLIGHT — Read repository-root AGENTS.md before substantive work when present; establish the actual valid law source using canonical > installed > portable > inline capsule > blocked; report exactly one P2P_LAW_SOURCE=<actual source>; never claim a source was read when it was not.",
        "OE_GATE — Ask exactly: Không bị over engineering chứ? Evaluate SIMPLER_PATH, MATERIAL_PROGRESS, NECESSITY, CORE_BEFORE_SUPPORT, SMALLER_VERIFIABLE_SLICE. Return OE_VERDICT=DO_IT|SKIP_IT|DEFER_UNTIL_NEEDED with one concrete reason. A weak or negative answer means reduce, remove, or defer the step; never return a ceremonial PASS.",
    )
)
if _RUNTIME_PROMPT_SERIALIZATION_MARKER not in _control_tower_handoff.SUPREME_LAW_CAPSULE:
    _control_tower_handoff.SUPREME_LAW_CAPSULE = "\n".join(
        (
            _control_tower_handoff.SUPREME_LAW_CAPSULE,
            _RUNTIME_PROMPT_SERIALIZATION_CAPSULE,
        )
    )

# Prompt-writing work reuses the existing Supreme Law/task-contract/destination
# surfaces. This is a bounded authoring discipline, not a second prompt framework,
# prompt-review service, model folklore registry, or extra planning phase.
_PROMPT_AUTHORING_DISCIPLINE_MARKER = "PROMPT_AUTHORING_DISCIPLINE_V1"
_PROMPT_AUTHORING_DISCIPLINE_CAPSULE = "\n".join(
    (
        "PROMPT_AUTHORING_DISCIPLINE_V1 — Apply this section only when the active task writes, improves, revises, or delegates a prompt. Reuse the existing P2P task contract, destination, durable state, evidence, and stop rules; do not create a parallel prompt framework.",
        "PROMPT_INPUT_MATURITY — Internally classify the supplied material as READY_PROMPT, PARTIAL_DRAFT, CLEAR_SIMPLE_REQUEST, or AMBIGUOUS_HIGH_IMPACT. READY_PROMPT: preserve known task/output/constraints and clarify only real weak points. PARTIAL_DRAFT: fill only material gaps. CLEAR_SIMPLE_REQUEST: compose immediately with the smallest reasonable assumptions. AMBIGUOUS_HIGH_IMPACT: ask only questions whose answers can materially change correctness, authority, acceptance, or destination execution.",
        "CLARIFICATION_DISCIPLINE — Never re-ask facts already explicit in the Owner request, durable project state, or active task contract. Group genuinely blocking clarifications compactly, normally 2-4 at a time. After one useful clarification round, do not enter an interview loop for non-blocking gaps: state reasonable assumptions and proceed. Ask the Owner only when the uncertainty is genuinely outcome-, authority-, risk-, or execution-blocking.",
        "DESTINATION_RESOLUTION — Resolve target model/executor from the Owner request and fresh durable routing state when already known; never ask again merely because a generic prompt recipe says to. If the destination is truly unknown and materially changes execution, clarify it. Otherwise use destination-neutral instructions until a concrete destination is resolved by existing P2P routing.",
        "CAPABILITY_OVER_FOLKLORE — Adapt structure and transport to verified/current destination capabilities or authoritative instructions when that materially changes execution. Do not hard-code folklore such as 'Claude likes XML' or similar model stereotypes as law. Fresh destination capability evidence outranks stale prompting folklore.",
        "PROPORTIONAL_PROMPT_COMPLEXITY — Prompt structure must be proportional to task complexity. A simple one-purpose task gets a concise executable prompt; a genuinely multi-part or high-risk task may use additional sections, placeholders, examples, edge-case rules, or strict output schemas only when they materially improve acceptance or recovery. No decorative roles, duplicated constraints, or checklist inflation.",
        "NO_PRIVATE_CHAIN_OF_THOUGHT_REQUEST — Do not instruct an executor to reveal private chain-of-thought, hidden scratchpad, or step-by-step internal reasoning. Request the final answer, concise decision rationale, assumptions, evidence, calculations, verification results, or an auditable action summary when those are needed.",
        "REVISION_CONTINUITY — When the Owner asks to change an existing prompt, revise that prompt rather than restarting requirements collection. Preserve unaffected constraints and return the complete revised prompt unless the Owner explicitly requests only a diff or fragment.",
        "OUTPUT_SURFACE_FIDELITY — Use the output form best supported by the destination and Owner workflow. Do not require Markdown code blocks, files, XML, JSON, tables, or another wrapper by default; require a format only when the task contract, destination capability, machine parsing, or copy/paste workflow materially benefits from it.",
        "PROMPT_AUTHORING_STOP — Stop when the prompt is executable, aligned to the Owner outcome, destination, scope, acceptance, evidence, authority boundaries, and stop condition. Do not add optional prompt theory, explanations, examples, or future-proofing after those conditions are satisfied unless explicitly requested.",
    )
)
if _PROMPT_AUTHORING_DISCIPLINE_MARKER not in _control_tower_handoff.SUPREME_LAW_CAPSULE:
    _control_tower_handoff.SUPREME_LAW_CAPSULE = "\n".join(
        (
            _control_tower_handoff.SUPREME_LAW_CAPSULE,
            _PROMPT_AUTHORING_DISCIPLINE_CAPSULE,
        )
    )
