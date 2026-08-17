"""P2P Composable Execution Target — neutral, deterministic contract layer.

Purpose (C30): give P2P a durable data model and deterministic logic so that an
execution target can be understood as a *composition* of independently
replaceable components — Harness, Provider, Model, Protocol, ToolSet, Workspace,
Environment, Authentication, Permission, Evidence Freshness — without routing,
selecting, or executing any of them.

Deliberate non-goals (claim boundary, ET23–ET25, ET48):
- This module does NOT route, rank, score, or select targets.
- This module does NOT execute tasks or launch processes.
- This module does NOT implement provider API clients or adapters.
- This module does NOT implement worktree orchestration, background
  services, or autonomy.
- This module does NOT store task state, goal truth, or duplicate the
  Capability Ledger. The Capability Ledger remains roadmap/capability truth.

Component separation (ET1–ET9): Harness != Provider != Model != Protocol;
ToolSet is orthogonal to Protocol; Workspace identity is orthogonal to
Environment identity; harness authentication is orthogonal to provider
authentication; MCP tool support does not imply execution-host support;
protocol compatibility never implies behavioral certification.

All logic is deterministic and pure (no I/O, no network, no time side
effects). Status semantics (§22): UNKNOWN != SUPPORTED, STALE != CURRENT,
DOCUMENTED != LIVE_CERTIFIED, COMPATIBLE != BEHAVIORALLY_VERIFIED,
AUTH_PRESENT != AUTH_VALID, HEALTHY != OWNED, OWNED != CERTIFIED.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Dict, FrozenSet, List, Optional, Tuple

__version__ = "8.4.7-C-codex.24"

# ---------------------------------------------------------------------------
# Capability and evidence primitives
# ---------------------------------------------------------------------------

VALID_CAPABILITY_STATUS = ("SUPPORTED", "UNSUPPORTED", "UNKNOWN")


class CapabilityState:
    """Evidence state of a single component capability."""

    SUPPORTED = "SUPPORTED"
    UNSUPPORTED = "UNSUPPORTED"
    UNKNOWN = "UNKNOWN"

    # Evidence freshness of material (temporal) evidence.
    CURRENT = "CURRENT"
    STALE = "STALE"

    @classmethod
    def validate(cls, status: str) -> None:
        if status not in VALID_CAPABILITY_STATUS:
            raise ValueError(
                f"invalid capability status {status!r}; must be one of "
                f"{VALID_CAPABILITY_STATUS}"
            )


class EvidenceFreshness:
    CURRENT = "CURRENT"
    STALE = "STALE"


# Deterministic task-requirement capability vocabulary (data, not enforcement).
TASK_REQUIREMENT_CAPABILITIES = (
    "repo_read",
    "repo_write",
    "command_execution",
    "structured_result",
    "structured_output",
    "network",
    "browser",
    "workspace_isolation",
    "independent_verification",
    "resume",
    "cancellation",
    "execution_identity",
    "local_execution",
    "remote_async",
    "permission_enforcement",
)


class ProtocolClass:
    """Execution-host protocol classes. MCP is semantically distinct: a
    tools/context protocol, NOT an execution-host protocol.

    No claim is allowed that 'MCP supported' implies 'host execution
    supported' (ET8), nor that '*-compatible' implies behaviorally equivalent
    to the reference (ET9, ET50).
    """

    NATIVE_CLI = "NATIVE_CLI"
    NATIVE_API = "NATIVE_API"
    REMOTE_ASYNC_TASK = "REMOTE_ASYNC_TASK"
    ACP = "ACP"
    OPENAI_COMPATIBLE = "OPENAI_COMPATIBLE"
    ANTHROPIC_COMPATIBLE = "ANTHROPIC_COMPATIBLE"
    MCP_TOOLS = "MCP_TOOLS"
    OTHER_VERSIONED_PROTOCOL = "OTHER_VERSIONED_PROTOCOL"

    VALID = (
        NATIVE_CLI,
        NATIVE_API,
        REMOTE_ASYNC_TASK,
        ACP,
        OPENAI_COMPATIBLE,
        ANTHROPIC_COMPATIBLE,
        MCP_TOOLS,
        OTHER_VERSIONED_PROTOCOL,
    )


class WorkspaceClass:
    """Execution workspace classes. C30 records the classes; it does NOT
    create automatic worktrees (ET40, §31)."""

    CURRENT_REPO = "CURRENT_REPO"
    ISOLATED_GIT_WORKTREE = "ISOLATED_GIT_WORKTREE"
    EPHEMERAL_SANDBOX = "EPHEMERAL_SANDBOX"
    REMOTE_WORKSPACE = "REMOTE_WORKSPACE"
    READ_ONLY_WORKSPACE = "READ_ONLY_WORKSPACE"

    VALID = (
        CURRENT_REPO,
        ISOLATED_GIT_WORKTREE,
        EPHEMERAL_SANDBOX,
        REMOTE_WORKSPACE,
        READ_ONLY_WORKSPACE,
    )


class HealthState:
    """Runtime health/ownership ladder (§29). A process existing or listening
    does NOT prove it belongs to P2P: HEALTHY != OWNED != CERTIFIED. The
    ladder is strict — owning or certifying implies the preceding states, but
    presence alone implies none of the later ones."""

    PRESENT = "PRESENT"
    AVAILABLE = "AVAILABLE"
    HEALTHY = "HEALTHY"
    OWNED = "OWNED"
    AUTHENTICATED = "AUTHENTICATED"
    CONNECTION_READY = "CONNECTION_READY"
    LIVE_PROBE_ELIGIBLE = "LIVE_PROBE_ELIGIBLE"
    CERTIFIED = "CERTIFIED"

    # Strict ascending ladder; each state implies all earlier ones.
    ORDER = [
        PRESENT,
        AVAILABLE,
        HEALTHY,
        OWNED,
        AUTHENTICATED,
        CONNECTION_READY,
        LIVE_PROBE_ELIGIBLE,
        CERTIFIED,
    ]


class QuiesceState:
    """Safe lifecycle states (§30). UNKNOWN must fail closed for destructive
    lifecycle changes: from an unknown quiesce state, no destructive
    transition is permitted."""

    ACCEPTING_WORK = "ACCEPTING_WORK"
    DRAINING = "DRAINING"
    QUIESCENT = "QUIESCENT"
    STOPPED = "STOPPED"
    UNKNOWN = "UNKNOWN"

    # Allowed transitions under normal (non-unknown) knowledge.
    ALLOWED_TRANSITIONS = {
        ACCEPTING_WORK: (DRAINING, STOPPED),
        DRAINING: (QUIESCENT, STOPPED),
        QUIESCENT: (STOPPED,),
        STOPPED: (ACCEPTING_WORK,),
        UNKNOWN: (),  # fail closed: no transition allowed from UNKNOWN
    }


class ContractDriftState:
    """Contract identity / drift states (§26). An old certification can never
    silently remain current when material contract behavior changed."""

    CURRENT = "CURRENT"
    STALE = "STALE"
    MIGRATION_REQUIRED = "MIGRATION_REQUIRED"
    UNSUPPORTED = "UNSUPPORTED"
    REVALIDATION_REQUIRED = "REVALIDATION_REQUIRED"


class EligibilityState:
    ELIGIBLE = "ELIGIBLE"
    INELIGIBLE_CAPABILITY = "INELIGIBLE_CAPABILITY"
    INELIGIBLE_AUTH = "INELIGIBLE_AUTH"
    INELIGIBLE_PERMISSION = "INELIGIBLE_PERMISSION"
    INELIGIBLE_FRESHNESS = "INELIGIBLE_FRESHNESS"
    INELIGIBLE_PROTOCOL = "INELIGIBLE_PROTOCOL"
    INELIGIBLE_WORKSPACE = "INELIGIBLE_WORKSPACE"
    UNKNOWN = "UNKNOWN"

    # Strict precedence: first match wins (deterministic).
    ORDER = (
        ELIGIBLE,
        INELIGIBLE_CAPABILITY,
        INELIGIBLE_AUTH,
        INELIGIBLE_PERMISSION,
        INELIGIBLE_FRESHNESS,
        INELIGIBLE_PROTOCOL,
        INELIGIBLE_WORKSPACE,
        UNKNOWN,
    )


# ---------------------------------------------------------------------------
# Profiles — one per composable component
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ComponentCapabilities:
    """Deterministic, evidence-backed capability set of a component."""

    supported: FrozenSet[str] = field(default_factory=frozenset)
    unsupported: FrozenSet[str] = field(default_factory=frozenset)
    unknown: FrozenSet[str] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        overlap = (
            (self.supported & self.unsupported)
            | (self.supported & self.unknown)
            | (self.unsupported & self.unknown)
        )
        if overlap:
            raise ValueError(
                f"capability sets overlap (a capability cannot hold two "
                f"states at once): {sorted(overlap)}"
            )

    def state_of(self, capability: str) -> str:
        if capability in self.supported:
            return CapabilityState.SUPPORTED
        if capability in self.unsupported:
            return CapabilityState.UNSUPPORTED
        return CapabilityState.UNKNOWN

    def intersection(self, other: "ComponentCapabilities") -> "ComponentCapabilities":
        """Evidence intersection (§22): a capability is supported only if BOTH
        components durably support it. A component that says nothing about a
        capability (neither supported, unsupported, nor unknown) is neutral
        on that capability — silence is not evidence of unknown. Explicit
        UNSUPPORTED always propagates; explicit UNKNOWN propagates only when
        the other side is also silent or unknown (an explicit support claim
        from one component with silent other = supported by that component
        but not jointly; the honest result preserves the support claim only
        when both support it).

        Precedence when evidence conflicts across components: UNSUPPORTED
        wins over everything; then UNKNOWN; then silence; then SUPPORTED."""
        either_unsupported = (self.unsupported | other.unsupported)
        either_unknown = (self.unknown | other.unknown) - either_unsupported
        # A capability is supported only if BOTH sides hold an explicit
        # support opinion (intersection of support). A capability becomes
        # UNSUPPORTED if EITHER side holds an explicit unsupported opinion.
        # Silence (an empty set) is neutral on every capability — it never
        # converts another component's support into unknown.
        return ComponentCapabilities(
            supported=self.supported & other.supported,
            unsupported=either_unsupported,
            unknown=either_unknown,
        )


@dataclass(frozen=True)
class Evidence:
    """Material evidence for a component capability. Secrets are never
    embedded; only references and structural identity may be recorded."""

    observed_at: str  # ISO-8601 date string (data only)
    freshness: str  # CURRENT | STALE
    ref: Optional[str] = None  # durable reference (URL, report path, doc id)

    def __post_init__(self) -> None:
        if self.freshness not in (EvidenceFreshness.CURRENT, EvidenceFreshness.STALE):
            raise ValueError(f"invalid evidence freshness {self.freshness!r}")


@dataclass(frozen=True)
class HarnessProfile:
    """Execution harness: any runtime capable of agentic work (data only).

    harness_auth is the harness's own authentication state — conceptually
    distinct from the selected provider's credentials (ET7, §19)."""

    harness_id: str
    version: str
    capabilities: ComponentCapabilities
    harness_auth_state: str  # ABSENT | PRESENT | VALID | INVALID
    execution_identity: Optional[str] = None


@dataclass(frozen=True)
class ProviderProfile:
    """Model provider: the service/runtime through which inference is
    obtained. Distinct from harness (ET1, ET2). No API clients implemented
    (§12)."""

    provider_id: str
    endpoint_identity: str  # identity of the endpoint, NOT a secret
    supported_models: FrozenSet[str] = field(default_factory=frozenset)
    protocol_classes: FrozenSet[str] = field(default_factory=frozenset)
    auth_state: str = "ABSENT"  # ABSENT | PRESENT | VALID | INVALID
    vendor_metadata: Optional[str] = None  # non-authoritative, cannot self-certify


@dataclass(frozen=True)
class ModelProfile:
    """Model identity, separate from provider (§13). Volatile properties are
    evidence with freshness, never architecture constants."""

    model_id: str
    provider_compatible: FrozenSet[str] = field(default_factory=frozenset)
    tool_calling: str = CapabilityState.UNKNOWN
    structured_output: str = CapabilityState.UNKNOWN
    context_metadata: Optional[str] = None
    evidence: Optional[Evidence] = None

    def __post_init__(self) -> None:
        for attr in ("tool_calling", "structured_output"):
            CapabilityState.validate(getattr(self, attr))


@dataclass(frozen=True)
class ModelVariant:
    """Effort/reasoning variant — a dimension of a model identity, not a new
    model/provider/harness (§14). Data-only conceptual values."""

    model_id: str
    variant_id: str
    options: Optional[Dict[str, str]] = None


@dataclass(frozen=True)
class ProtocolProfile:
    """Execution protocol, represented independently (§15). MCP_TOOLS is a
    tools/context protocol and stays semantically distinct from execution-host
    protocols."""

    protocol_class: str
    version: Optional[str] = None
    evidence: Optional[Evidence] = None

    def __post_init__(self) -> None:
        if self.protocol_class not in ProtocolClass.VALID:
            raise ValueError(
                f"unknown protocol class {self.protocol_class!r}; valid: "
                f"{ProtocolClass.VALID}"
            )


@dataclass(frozen=True)
class ToolSetProfile:
    """Tool capability, separate from model/provider/harness identity (§16).
    Presence does not imply permission to use (§16)."""

    available_tools: FrozenSet[str] = field(default_factory=frozenset)
    protocol_tools: bool = False  # MCP-exposed tools present
    capabilities: ComponentCapabilities = field(default_factory=ComponentCapabilities)


@dataclass(frozen=True)
class WorkspaceProfile:
    """Execution workspace class with durable identity/binding (§17)."""

    workspace_class: str
    identity: Optional[str] = None  # durable binding for evidence (branch/wt id)
    repo_binding: Optional[str] = None
    read_only: bool = False

    def __post_init__(self) -> None:
        if self.workspace_class not in WorkspaceClass.VALID:
            raise ValueError(
                f"unknown workspace class {self.workspace_class!r}; valid: "
                f"{WorkspaceClass.VALID}"
            )
        if self.read_only and self.workspace_class != WorkspaceClass.READ_ONLY_WORKSPACE:
            # read_only is a hard property of READ_ONLY_WORKSPACE; other
            # classes record it via binding, never as a lie
            raise ValueError(
                "read_only=True is only valid for READ_ONLY_WORKSPACE"
            )


@dataclass(frozen=True)
class EnvironmentProfile:
    """Execution environment — distinct from workspace (§18). Same repo does
    NOT mean same execution environment."""

    os_identity: Optional[str] = None
    runtime_identity: Optional[str] = None
    repository_identity: Optional[str] = None
    cwd_identity: Optional[str] = None
    sandbox_identity: Optional[str] = None
    host_machine_identity: Optional[str] = None


@dataclass(frozen=True)
class AuthProfile:
    """Authentication state. Preserves C28 invariants: SECRET_REFERENCE !=
    SECRET_VALUE != AUTH_STATE. Credential *values* are never stored. Harness
    auth and provider auth are conceptually distinct (ET7, §19)."""

    harness_auth_state: str = "ABSENT"   # ABSENT | PRESENT | VALID | INVALID
    provider_auth_state: str = "ABSENT"  # ABSENT | PRESENT | VALID | INVALID
    harness_credential_ref: Optional[str] = None  # reference identity only
    provider_credential_ref: Optional[str] = None  # reference identity only

    _VALID_STATES = ("ABSENT", "PRESENT", "VALID", "INVALID")

    def __post_init__(self) -> None:
        for attr in ("harness_auth_state", "provider_auth_state"):
            if getattr(self, attr) not in self._VALID_STATES:
                raise ValueError(
                    f"invalid auth state {getattr(self, attr)!r} for {attr}; "
                    f"valid: {self._VALID_STATES}"
                )


@dataclass(frozen=True)
class PermissionProfile:
    """Permission envelope (§20). Composition rule: execution-target
    permission must be <= P2P allowed permission. Never widened through
    composition (ET16)."""

    allowed_permissions: FrozenSet[str] = field(default_factory=frozenset)

    def is_subset_of(self, other: "PermissionProfile") -> bool:
        return self.allowed_permissions.issubset(other.allowed_permissions)

    def union(self, other: "PermissionProfile") -> "PermissionProfile":
        """Union is the only sound monotone combination: it narrows authority
        to what BOTH envelopes permit jointly (intersection of allowed sets).
        Any other combination could widen permission and is forbidden."""
        return PermissionProfile(
            allowed_permissions=self.allowed_permissions & other.allowed_permissions
        )


@dataclass(frozen=True)
class ContractIdentity:
    """Verified adapter/protocol contract identity/version (§26)."""

    contract_id: str
    version: str
    protocol_class: Optional[str] = None
    certified_at: Optional[str] = None


@dataclass(frozen=True)
class HealthSnapshot:
    """Runtime health/ownership snapshot (§29)."""

    health_state: str
    evidence_ref: Optional[str] = None

    def __post_init__(self) -> None:
        if self.health_state not in HealthState.ORDER:
            raise ValueError(
                f"invalid health state {self.health_state!r}; valid: "
                f"{HealthState.ORDER}"
            )


@dataclass(frozen=True)
class ExecutionTarget:
    """A composable execution target: the full composition of components.

    This is a description and validation contract. It does NOT execute,
    route, or select (§4, §44, §45).
    """

    target_id: str
    harness: HarnessProfile
    provider: ProviderProfile
    model: ModelProfile
    variant: Optional[ModelVariant] = None
    protocol: ProtocolProfile = field(
        default_factory=lambda: ProtocolProfile(ProtocolClass.OTHER_VERSIONED_PROTOCOL)
    )
    toolset: ToolSetProfile = field(default_factory=ToolSetProfile)
    workspace: Optional[WorkspaceProfile] = None
    environment: Optional[EnvironmentProfile] = None
    auth: AuthProfile = field(default_factory=AuthProfile)
    permission: PermissionProfile = field(default_factory=PermissionProfile)
    contract: Optional[ContractIdentity] = None
    health: Optional[HealthSnapshot] = None

    # ------------------------------------------------------------------
    # Effective capability composition (§22): deterministic intersection
    # ------------------------------------------------------------------

    def effective_capability(self) -> ComponentCapabilities:
        """EffectiveCapability = evidence-aggregated capability state across
        all components (§22). Silence (a component that says nothing) is
        neutral and never converts another component's explicit evidence
        into unknown. Explicit opinions aggregate with precedence:
        UNSUPPORTED > UNKNOWN > silence > SUPPORTED. A capability supported
        by any component and contradicted by none is recorded as supported.

        UNKNOWN != SUPPORTED: a capability with NO evidence at all stays
        UNKNOWN, which is why evaluate_execution_target requires every
        required capability to have an explicit opinion."""
        sets = [
            self.harness.capabilities,
            self.provider_protocol_capability(),
            self.toolset.capabilities,
        ]
        all_supported = frozenset()
        all_unsupported = frozenset()
        all_unknown = frozenset()
        for s in sets:
            all_supported |= s.supported
            all_unsupported |= s.unsupported
            all_unknown |= s.unknown
        supported = (all_supported - all_unsupported - all_unknown)
        unknown = (all_unknown - all_unsupported)
        return ComponentCapabilities(
            supported=supported,
            unsupported=all_unsupported,
            unknown=unknown,
        )

    def provider_protocol_capability(self) -> ComponentCapabilities:
        """The provider profile carries no capability set of its own (§12);
        its contribution is the evidence that a protocol contract is
        supported. Compatibility != certification (ET9, ET50): only an
        explicit SUPPORTED marker counts."""
        return ComponentCapabilities()

    # ------------------------------------------------------------------
    # Deterministic fingerprint (§25)
    # ------------------------------------------------------------------

    def fingerprint(self) -> str:
        """Deterministic, non-secret fingerprint. Changes on any material
        configuration change. Secret values are never included; credential
        references (identity only) may be."""
        payload = _material_identity(self)
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    # ------------------------------------------------------------------
    # Health ladder predicates (§29)
    # ------------------------------------------------------------------

    def health_rank(self) -> int:
        if self.health is None:
            return -1
        return HealthState.ORDER.index(self.health.health_state)

    def is_at_least(self, state: str) -> bool:
        if state not in HealthState.ORDER:
            raise ValueError(f"unknown health ladder state {state!r}")
        return self.health_rank() >= HealthState.ORDER.index(state)


def _material_identity(target: ExecutionTarget) -> Dict:
    """Material identity fields only — no secrets, no values."""
    ws = None
    if target.workspace is not None:
        ws = {
            "workspace_class": target.workspace.workspace_class,
            "identity": target.workspace.identity,
            "repo_binding": target.workspace.repo_binding,
            "read_only": target.workspace.read_only,
        }
    env = None
    if target.environment is not None:
        env = {
            "os_identity": target.environment.os_identity,
            "runtime_identity": target.environment.runtime_identity,
            "repository_identity": target.environment.repository_identity,
            "cwd_identity": target.environment.cwd_identity,
            "sandbox_identity": target.environment.sandbox_identity,
            "host_machine_identity": target.environment.host_machine_identity,
        }
    variant = None
    if target.variant is not None:
        variant = {
            "model_id": target.variant.model_id,
            "variant_id": target.variant.variant_id,
        }
    contract = None
    if target.contract is not None:
        contract = {
            "contract_id": target.contract.contract_id,
            "version": target.contract.version,
            "protocol_class": target.contract.protocol_class,
        }
    return {
        "target_id": target.target_id,
        "harness": {
            "harness_id": target.harness.harness_id,
            "version": target.harness.version,
            "supported": sorted(target.harness.capabilities.supported),
            "unsupported": sorted(target.harness.capabilities.unsupported),
            "execution_identity": target.harness.execution_identity,
        },
        "provider": {
            "provider_id": target.provider.provider_id,
            "endpoint_identity": target.provider.endpoint_identity,
        },
        "model": {
            "model_id": target.model.model_id,
            "tool_calling": target.model.tool_calling,
            "structured_output": target.model.structured_output,
        },
        "variant": variant,
        "protocol": {
            "protocol_class": target.protocol.protocol_class,
            "version": target.protocol.version,
        },
        "toolset": {
            "available_tools": sorted(target.toolset.available_tools),
            "supported": sorted(target.toolset.capabilities.supported),
            "unsupported": sorted(target.toolset.capabilities.unsupported),
        },
        "workspace": ws,
        "environment": env,
        "auth": {
            "harness_auth_state": target.auth.harness_auth_state,
            "provider_auth_state": target.auth.provider_auth_state,
            "harness_credential_ref": target.auth.harness_credential_ref,
            "provider_credential_ref": target.auth.provider_credential_ref,
        },
        "permission": {"allowed_permissions": sorted(target.permission.allowed_permissions)},
        "contract": contract,
    }


def _material_field_changed(before: Dict, after: Dict, path: Tuple[str, ...]) -> bool:
    """Compare the material-identity projection of two fingerprints."""
    b, a = before, after
    for key in path:
        if not isinstance(b, dict) or not isinstance(a, dict):
            return True
        if key not in b or key not in a:
            return True
        b, a = b[key], a[key]
    return b != a


def material_identity_field(target: ExecutionTarget, path: Tuple[str, ...]) -> Dict:
    """Project a single material field from the fingerprint payload."""
    node = _material_identity(target)
    for key in path:
        if not isinstance(node, dict) or key not in node:
            raise KeyError(f"material path not found: {path}")
        node = node[key]
    return node  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# Task requirements and deterministic eligibility evaluation (§23, §24)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TaskRequirements:
    """Contract/data representation of required capabilities for a task.
    Never routed to a real task (§23)."""

    required_capabilities: FrozenSet[str] = field(default_factory=frozenset)
    required_workspace_class: Optional[str] = None
    required_protocol_classes: FrozenSet[str] = field(default_factory=frozenset)
    required_permissions: FrozenSet[str] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        if self.required_workspace_class is not None and (
            self.required_workspace_class not in WorkspaceClass.VALID
        ):
            raise ValueError(
                f"unknown required workspace class "
                f"{self.required_workspace_class!r}; valid: {WorkspaceClass.VALID}"
            )


@dataclass(frozen=True)
class EligibilityResult:
    """Deterministic eligibility outcome (strict precedence, no ranking)."""

    state: str
    reasons: Tuple[str, ...] = field(default_factory=tuple)

    @property
    def eligible(self) -> bool:
        return self.state == EligibilityState.ELIGIBLE


def _protocol_satisfies(target: ExecutionTarget, requirements: TaskRequirements) -> bool:
    """Protocol protocol eligibility (§21, ET21): an execution-host protocol
    class requirement must be materially satisfied; MCP_TOOLS never counts as
    an execution-host protocol (ET8)."""
    if not requirements.required_protocol_classes:
        return True
    klass = target.protocol.protocol_class
    # MCP tools protocol is semantically distinct from execution protocols.
    return klass in requirements.required_protocol_classes and klass != ProtocolClass.MCP_TOOLS


def evaluate_execution_target(
    target: ExecutionTarget,
    requirements: TaskRequirements,
    p2p_allowed_permission: Optional[PermissionProfile] = None,
) -> EligibilityResult:
    """Deterministic execution-target eligibility.

    Returns ELIGIBLE, one INELIGIBLE_* reason (strict precedence), or
    UNKNOWN. No scoring, no ranking, no selection, no execution (§24, §45).
    """
    effective = target.effective_capability()
    reasons: List[str] = []

    # 1. Capability intersection — one material missing requirement blocks.
    #    UNKNOWN evidence (no explicit opinion) is distinct from explicit
    #    UNSUPPORTED: an unknown requirement yields UNKNOWN eligibility
    #    (cannot be honestly determined), an unsupported requirement yields
    #    INELIGIBLE_CAPABILITY (explicitly refused).
    unknown_caps: List[str] = []
    for cap in sorted(requirements.required_capabilities):
        st = effective.state_of(cap)
        if st == CapabilityState.UNKNOWN:
            unknown_caps.append(cap)
        elif st == CapabilityState.UNSUPPORTED:
            reasons.append(f"capability {cap} is UNSUPPORTED")
    if reasons:
        return EligibilityResult(EligibilityState.INELIGIBLE_CAPABILITY, tuple(reasons))
    if unknown_caps:
        return EligibilityResult(
            EligibilityState.UNKNOWN,
            (f"capability evidence is UNKNOWN for: {unknown_caps}; "
             "eligibility cannot be determined"),
        )

    # 2. Protocol — MCP != execution host (ET8); compatibility != certification (ET9).
    if not _protocol_satisfies(target, requirements):
        return EligibilityResult(
            EligibilityState.INELIGIBLE_PROTOCOL,
            (f"protocol class {target.protocol.protocol_class!r} does not satisfy "
             f"required {sorted(requirements.required_protocol_classes)}"),
        )

    # 3. Workspace requirement.
    if requirements.required_workspace_class is not None:
        if target.workspace is None or (
            target.workspace.workspace_class != requirements.required_workspace_class
        ):
            return EligibilityResult(
                EligibilityState.INELIGIBLE_WORKSPACE,
                ("workspace requirement "
                 f"{requirements.required_workspace_class!r} not satisfied "
                 f"(target workspace: "
                 f"{target.workspace.workspace_class if target.workspace else None})"),
            )

    # 4. Freshness — stale material evidence blocks (STALE != CURRENT, §21).
    for label, evidence in (
        ("protocol", getattr(target.protocol, "evidence", None)),
        ("model", target.model.evidence),
    ):
        if evidence is not None and evidence.freshness == EvidenceFreshness.STALE:
            return EligibilityResult(
                EligibilityState.INELIGIBLE_FRESHNESS,
                (f"{label} evidence is STALE and requires revalidation",),
            )
    # Any REQUIRED capability left unresolved (not supported and not
    # explicitly unsupported) means the requirement is UNKNOWN: eligibility
    # cannot be honestly determined for that requirement.
    required_unknown = [
        cap for cap in sorted(requirements.required_capabilities)
        if cap not in effective.supported and cap not in effective.unsupported
    ]
    if required_unknown:
        return EligibilityResult(
            EligibilityState.UNKNOWN,
            (f"required capability evidence is UNKNOWN: {required_unknown}; "
             "eligibility cannot be determined"),
        )

    # 5. Authentication — AUTH_PRESENT != AUTH_VALID (§22, ET18).
    for label, state in (
        ("harness", target.auth.harness_auth_state),
        ("provider", target.auth.provider_auth_state),
    ):
        required = (
            "harness" if label == "harness" else "provider"
        )
        if state == "ABSENT":
            return EligibilityResult(
                EligibilityState.INELIGIBLE_AUTH,
                (f"{label} auth is ABSENT",),
            )
        if state == "PRESENT":
            return EligibilityResult(
                EligibilityState.INELIGIBLE_AUTH,
                (f"{label} auth is PRESENT but not verified VALID "
                 f"(AUTH_PRESENT != AUTH_VALID)"),
            )
        if state == "INVALID":
            return EligibilityResult(
                EligibilityState.INELIGIBLE_AUTH,
                (f"{label} auth is INVALID",),
            )
        # VALID passes.

    # 6. Permission — must not widen (ET16, ET17, §20).
    target_permission = target.permission
    if requirements.required_permissions:
        missing = requirements.required_permissions - target_permission.allowed_permissions
        if missing:
            return EligibilityResult(
                EligibilityState.INELIGIBLE_PERMISSION,
                (f"required permission(s) missing from target envelope: "
                 f"{sorted(missing)}"),
            )
    if p2p_allowed_permission is not None and not target_permission.is_subset_of(
        p2p_allowed_permission
    ):
        widening = (
            target_permission.allowed_permissions
            - p2p_allowed_permission.allowed_permissions
        )
        return EligibilityResult(
            EligibilityState.INELIGIBLE_PERMISSION,
            (f"target permission widens beyond P2P allowed permission "
             f"(forbidden): {sorted(widening)}"),
        )

    return EligibilityResult(EligibilityState.ELIGIBLE, ())


# ---------------------------------------------------------------------------
# Contract drift (§26)
# ---------------------------------------------------------------------------

def drift_state(
    current_contract: ContractIdentity,
    observed_version: str,
    behavior_changed: bool,
) -> str:
    """Contract identity / drift guard. An old certification can never
    silently remain current when material contract behavior changed (§26,
    ET36)."""
    if behavior_changed:
        if current_contract.version != observed_version:
            return ContractDriftState.MIGRATION_REQUIRED
        return ContractDriftState.REVALIDATION_REQUIRED
    if current_contract.version != observed_version:
        return ContractDriftState.STALE
    return ContractDriftState.CURRENT


# ---------------------------------------------------------------------------
# Safe quiesce lifecycle (§30)
# ---------------------------------------------------------------------------

def quiesce_transition(current: str, desired: str) -> bool:
    """Deterministic safe lifecycle transitions. UNKNOWN fails closed: no
    destructive transition is ever allowed from an unknown state."""
    if current not in QuiesceState.ALLOWED_TRANSITIONS:
        raise ValueError(f"unknown quiesce state {current!r}")
    return desired in QuiesceState.ALLOWED_TRANSITIONS[current]


def quiesce_allows_destructive(state: str) -> bool:
    """Only a certifiably known QUIESCENT or DRAINING state allows
    destructive lifecycle changes."""
    return state in (QuiesceState.QUIESCENT, QuiesceState.DRAINING)


# ---------------------------------------------------------------------------
# Backend registry — neutral profile catalog (§27, §43)
# ---------------------------------------------------------------------------

class BackendRegistry:
    """One neutral registry of execution-environment profiles and evidence.

    It stores harness/provider/model/protocol profiles with observed evidence
    and supported compositions. It deliberately does NOT route, rank, execute,
    own Task State, own Goal truth, or duplicate the Capability Ledger
    (§27, §43). The Capability Ledger remains the roadmap/capability truth;
    this registry remains execution-environment knowledge.
    """

    def __init__(self) -> None:
        self._harnesses: Dict[str, HarnessProfile] = {}
        self._providers: Dict[str, ProviderProfile] = {}
        self._models: Dict[str, ModelProfile] = {}
        self._protocols: Dict[str, ProtocolProfile] = {}

    def register_harness(self, profile: HarnessProfile) -> None:
        self._harnesses[profile.harness_id] = profile

    def register_provider(self, profile: ProviderProfile) -> None:
        self._providers[profile.provider_id] = profile

    def register_model(self, profile: ModelProfile) -> None:
        self._models[profile.model_id] = profile

    def register_protocol(self, profile: ProtocolProfile) -> None:
        key = f"{profile.protocol_class}:{profile.version or 'unversioned'}"
        self._protocols[key] = profile

    def harness(self, harness_id: str) -> Optional[HarnessProfile]:
        return self._harnesses.get(harness_id)

    def provider(self, provider_id: str) -> Optional[ProviderProfile]:
        return self._providers.get(provider_id)

    def model(self, model_id: str) -> Optional[ModelProfile]:
        return self._models.get(model_id)

    def protocol(self, protocol_class: str, version: Optional[str] = None) -> Optional[ProtocolProfile]:
        return self._protocols.get(f"{protocol_class}:{version or 'unversioned'}")

    def list_harnesses(self) -> List[str]:
        return sorted(self._harnesses)

    def list_providers(self) -> List[str]:
        return sorted(self._providers)

    def list_models(self) -> List[str]:
        return sorted(self._models)

    def eligible_targets(
        self,
        requirements: TaskRequirements,
        p2p_allowed_permission: Optional[PermissionProfile] = None,
    ) -> Tuple[ExecutionTarget, ...]:
        """Deterministic composition enumeration over registered profiles.

        NOTE: this is a mechanical enumeration of *eligible* compositions —
        NOT a ranking, NOT a selection, NOT a routing decision (§45). The
        Owner (or a future Owner-gated mechanism) decides which eligible
        target, if any, is used.
        """
        results: List[ExecutionTarget] = []
        for h in self._harnesses.values():
            for p in self._providers.values():
                for m in self._models.values():
                    if m.model_id not in p.supported_models:
                        continue
                    target = ExecutionTarget(
                        target_id=(
                            f"{h.harness_id}+{p.provider_id}+{m.model_id}+"
                            f"{m.tool_calling}:{m.structured_output}"
                        ),
                        harness=h,
                        provider=p,
                        model=m,
                    )
                    if evaluate_execution_target(
                        target, requirements, p2p_allowed_permission
                    ).eligible:
                        results.append(target)
        # Deterministic, stable ordering; never a score.
        results.sort(key=lambda t: t.target_id)
        return tuple(results)
