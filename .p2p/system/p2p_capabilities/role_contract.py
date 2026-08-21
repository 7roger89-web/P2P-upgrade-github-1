"""C35 RoleExecutionContract — deterministic, provider-neutral role task
binding.

Conceptually:

    AgentRoleSpec (role_spec_hash) + TaskContract + bounded context package
    + permission envelope + acceptance/evidence contract
        -> RoleExecutionContract

No backend/vendor-specific fields live in the core contract. Adapter-
specific transport data belongs behind the adapter boundary.

The contract is deterministic: the same inputs always produce the same
REQUEST_FINGERPRINT (canonical JSON -> SHA-256), and the fingerprint
changes when any material field changes. The request fingerprint follows
the existing C22/C30 fingerprint semantics family (deterministic payload
hash) without duplicating C34's goal/task-only scope — a role contract
additionally binds environment, context digest, permission profile, and
target attestation.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

from .agent_role import (
    AgentRoleError,
    AgentRoleSpec,
    CANONICAL_ROLES,
    OPTIONAL_SPECIALIST_ROLE,
)

ROLE_CONTRACT_SCHEMA = "p2p-role-execution-contract/1"

CONTEXT_POLICIES = ("NONE", "BOUNDED_EXPLICIT", "UNKNOWN")
PERMISSION_GRANTS = (
    "NONE",
    "READ",
    "WRITE_BOUNDED",  # bounded documentation write only (BW01)
    "WRITE",
    "EXECUTE",
    "NETWORK",
    "OWNER_GATE_REQUIRED",
    "UNKNOWN",
)
TARGET_ATTESTATION_STATES = (
    "REQUESTED_ONLY",           # target declared; no observed evidence yet
    "ATTESTED_MATCH",           # requested == observed, evidence present
    "ATTESTED_DIFFERS",         # observed target differs, evidence present
    "UNAVAILABLE",              # attestation evidence unavailable
    "UNKNOWN",
)

# Core contract field names (semantic binding set, in canonical order).
_CONTRACT_FIELDS = (
    "role_id",
    "role_spec_hash",
    "goal_id",
    "task_id",
    "project_binding",
    "environment_binding",
    "workspace_binding",
    "objective",
    "approved_scope",
    "dependencies",
    "context_package",
    "context_digest",
    "permission_profile",
    "required_capabilities",
    "acceptance_criteria",
    "required_evidence",
    "verification_policy",
    "explicit_execution_target",
    "target_fingerprint",
    "requested_target_attestation",
    "budget",
    "request_fingerprint",
    "mutation_class",
    "mutation_authorization_id",
    "mutation_target_fingerprint",
    "pre_mutation_surface_fingerprint",
)


class RoleContractError(ValueError):
    """Raised only when a role contract cannot be safely used."""

    def __init__(self, code: str, details: Mapping[str, Any] | None = None):
        self.code = code
        self.details = details or {}
        super().__init__("ROLE_CONTRACT_ERROR:" + code)


@dataclass(frozen=True)
class RoleExecutionContract:
    """Bounded role + task execution contract. Provider/model/harness neutral.

    TASK != AGENT_ROLE: the contract binds both, and neither can stand in
    for the other. A task record without a role binding is NOT a role
    contract; a role spec without a task binding is NOT executable.
    """
    schema: str = ROLE_CONTRACT_SCHEMA
    role_id: str = ""
    role_spec_hash: str = ""

    goal_id: str = ""
    task_id: str = ""

    project_binding: str = ""
    environment_binding: str = "LOCAL_PROJECT"
    workspace_binding: str = ""

    objective: str = ""
    approved_scope: tuple[str, ...] = ()
    dependencies: tuple[str, ...] = ()

    context_package: tuple[str, ...] = ()
    context_digest: str = ""

    permission_profile: tuple[str, ...] = ()
    required_capabilities: tuple[str, ...] = ()
    acceptance_criteria: tuple[str, ...] = ()
    required_evidence: tuple[str, ...] = ()
    verification_policy: str = "INDEPENDENT"

    explicit_execution_target: str = ""
    target_fingerprint: str = ""
    requested_target_attestation: str = "REQUESTED_ONLY"

    budget: str = "BOUNDED"
    request_fingerprint: str = ""
    # P2P-BOUNDED-DOCUMENTATION-WRITE-01 mutation contract fields. Empty
    # values mean NO mutation is bound to this contract (default, safe).
    mutation_class: str = ""
    mutation_authorization_id: str = ""
    mutation_target_fingerprint: str = ""
    pre_mutation_surface_fingerprint: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "role_id", _role_id(self.role_id))
        for name, max_len in (("goal_id", 256), ("task_id", 256),
                              ("project_binding", 256), ("environment_binding", 128),
                              ("workspace_binding", 512), ("objective", 4096),
                              ("explicit_execution_target", 128)):
            object.__setattr__(self, name,
                               _limited_text(getattr(self, name), name, max_len))
        object.__setattr__(self, "role_spec_hash",
                           _hex64(self.role_spec_hash, "role_spec_hash"))
        object.__setattr__(self, "context_digest",
                           _hex64(self.context_digest, "context_digest"))
        object.__setattr__(self, "target_fingerprint",
                           _hex64(self.target_fingerprint, "target_fingerprint"))
        object.__setattr__(self, "request_fingerprint",
                           _hex64(self.request_fingerprint, "request_fingerprint"))
        _assert_enum(self.requested_target_attestation, TARGET_ATTESTATION_STATES,
                     "requested_target_attestation")
        _assert_enum(self.verification_policy, ("INDEPENDENT", "UNKNOWN"),
                     "verification_policy")
        _assert_enum(self.budget, ("BOUNDED", "UNKNOWN"), "budget")
        _assert_enum(self.mutation_class,
                     ("", "bounded_documentation_write", "UNKNOWN"),
                     "mutation_class")
        for mfield in ("mutation_authorization_id", "mutation_target_fingerprint",
                       "pre_mutation_surface_fingerprint"):
            object.__setattr__(self, mfield,
                               _limited_text(getattr(self, mfield), mfield, 256))
        # Fail-closed mutation coupling: a live mutation class requires ALL
        # three material bindings (authorization, target, pre-surface). A
        # purely READ permission profile never carries a mutation class —
        # WRITE_BOUNDED must be explicitly granted.
        _mutation_set = bool(self.mutation_class) and \
            self.mutation_class != "UNKNOWN"
        if _mutation_set and not (self.mutation_authorization_id and
                                  self.mutation_target_fingerprint and
                                  self.pre_mutation_surface_fingerprint):
            raise RoleContractError("MUTATION_BINDING_INCOMPLETE",
                                    {"mutation_class": self.mutation_class})
        if _mutation_set and self.permission_profile and \
                "READ" in self.permission_profile and \
                "WRITE_BOUNDED" not in self.permission_profile:
            raise RoleContractError("MUTATION_PERMISSION_MISMATCH",
                                    {"permission_profile": list(
                                        self.permission_profile)})
        for name, values in (
            ("approved_scope", self.approved_scope),
            ("dependencies", self.dependencies),
            ("context_package", self.context_package),
            ("permission_profile", self.permission_profile),
            ("required_capabilities", self.required_capabilities),
            ("acceptance_criteria", self.acceptance_criteria),
            ("required_evidence", self.required_evidence),
        ):
            _assert_text_tuple(values, name)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "role_id": self.role_id,
            "role_spec_hash": self.role_spec_hash,
            "goal_id": self.goal_id,
            "task_id": self.task_id,
            "project_binding": self.project_binding,
            "environment_binding": self.environment_binding,
            "workspace_binding": self.workspace_binding,
            "objective": self.objective,
            "approved_scope": list(self.approved_scope),
            "dependencies": list(self.dependencies),
            "context_package": list(self.context_package),
            "context_digest": self.context_digest,
            "permission_profile": list(self.permission_profile),
            "required_capabilities": list(self.required_capabilities),
            "acceptance_criteria": list(self.acceptance_criteria),
            "required_evidence": list(self.required_evidence),
            "verification_policy": self.verification_policy,
            "explicit_execution_target": self.explicit_execution_target,
            "target_fingerprint": self.target_fingerprint,
            "requested_target_attestation": self.requested_target_attestation,
            "budget": self.budget,
            "request_fingerprint": self.request_fingerprint,
            "mutation_class": self.mutation_class,
            "mutation_authorization_id": self.mutation_authorization_id,
            "mutation_target_fingerprint": self.mutation_target_fingerprint,
            "pre_mutation_surface_fingerprint": self.pre_mutation_surface_fingerprint,
        }


# ---------------------------------------------------------------------------
# Deterministic request fingerprint (semantic binding set).
# ---------------------------------------------------------------------------

def role_contract_fingerprint(contract_fields: Mapping[str, Any]) -> str:
    """Deterministic fingerprint of a role contract's material bindings.
    Follows the existing fingerprint policy: canonical JSON of the
    semantic field set -> SHA-256. Formatting/non-semantic metadata does
    not alter it."""
    semantic = {name: contract_fields.get(name) for name in _CONTRACT_FIELDS
                if name != "request_fingerprint"}
    payload = json.dumps(semantic, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def context_digest_fingerprint(context_package: Iterable[str]) -> str:
    """Bounded explicit context digest: approved context pointers/files,
    not the parent transcript (TRANSCRIPT != STATE)."""
    package = tuple(str(item) for item in context_package)
    payload = json.dumps(package, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def target_fingerprint_from_profile(target_profile: Mapping[str, Any]) -> str:
    """Deterministic target identity fingerprint from an explicit
    execution target profile (adapter identity + harness + provider +
    model). Material identity changes change the fingerprint."""
    payload = json.dumps({
        "adapter_id": str(target_profile.get("adapter_id", "")),
        "harness": str(target_profile.get("harness", "")),
        "provider": str(target_profile.get("provider", "")),
        "model": str(target_profile.get("model", "")),
    }, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


# ---------------------------------------------------------------------------
# Contract construction: RoleSpec + TaskContract + bounded context +
# permission envelope + acceptance/evidence contract.
# ---------------------------------------------------------------------------

def build_role_execution_contract(
    role_spec: AgentRoleSpec,
    *,
    goal_id: str,
    task_id: str,
    task_objective: str,
    project_binding: str,
    environment_binding: str = "LOCAL_PROJECT",
    workspace_binding: str,
    approved_scope: Iterable[str] = (),
    task_dependencies: Iterable[str] = (),
    context_package: Iterable[str] = (),
    permission_profile: Iterable[str] = (),
    acceptance_criteria: Iterable[str] = (),
    required_evidence: Iterable[str] = (),
    budget: str = "BOUNDED",
    explicit_execution_target: str,
    target_fingerprint: str,
    mutation_class: str = "",
    mutation_authorization_id: str = "",
    mutation_target_fingerprint: str = "",
    pre_mutation_surface_fingerprint: str = "",
) -> RoleExecutionContract:
    """Build a bounded role execution contract. FRESH CHILD BY DEFAULT:
    the contract receives only approved context pointers (no parent
    transcript); the context_digest is derived from that bounded package.

    Permission never widens: a role whose ceiling is read-only cannot
    request WRITE/EXECUTE grants; the composed profile is validated by
    the eligibility layer."""
    if not required_evidence:
        required_evidence = tuple(role_spec.evidence_requirements)
    capabilities = tuple(role_spec.required_capabilities)
    acceptance = tuple(str(item) for item in acceptance_criteria) or ("role-objective-done",)
    verification_policy = "INDEPENDENT"
    attestation = ("REQUESTED_ONLY"
                   if requested_target_attestation_is_unverified(target_fingerprint)
                   else "REQUESTED_ONLY")
    contract_fields: dict[str, Any] = {
        "role_id": role_spec.role_id,
        "role_spec_hash": role_spec.role_spec_hash,
        "goal_id": goal_id,
        "task_id": task_id,
        "project_binding": project_binding,
        "environment_binding": environment_binding,
        "workspace_binding": workspace_binding,
        "objective": task_objective,
        "approved_scope": tuple(str(item) for item in approved_scope),
        "dependencies": tuple(str(item) for item in task_dependencies),
        "context_package": tuple(str(item) for item in context_package),
        "context_digest": context_digest_fingerprint(context_package),
        "permission_profile": tuple(str(item) for item in permission_profile) or ("READ",),
        "required_capabilities": capabilities,
        "acceptance_criteria": acceptance,
        "required_evidence": tuple(str(item) for item in required_evidence),
        "verification_policy": verification_policy,
        "explicit_execution_target": explicit_execution_target,
        "target_fingerprint": target_fingerprint,
        "requested_target_attestation": attestation,
        "budget": budget,
        "mutation_class": str(mutation_class or ""),
        "mutation_authorization_id": str(mutation_authorization_id or ""),
        "mutation_target_fingerprint": str(mutation_target_fingerprint or ""),
        "pre_mutation_surface_fingerprint": str(
            pre_mutation_surface_fingerprint or ""),
    }
    fingerprint = role_contract_fingerprint(contract_fields)
    contract_fields["request_fingerprint"] = fingerprint
    return RoleExecutionContract(**contract_fields)


def requested_target_attestation_is_unverified(target_fingerprint: str) -> bool:
    """A freshly minted contract cannot claim attestation — observed
    target evidence only exists after execution (requested != observed
    until runtime evidence binds them)."""
    return bool(target_fingerprint)


# ---------------------------------------------------------------------------
# Field validation helpers (shared style with model.py / backend_contract).
# ---------------------------------------------------------------------------

def _role_id(value: str) -> str:
    text = str(value or "").strip()
    if not re.fullmatch(r"p2p_[a-z][a-z0-9_]{2,40}", text):
        raise RoleContractError("ROLE_ID_INVALID", {"role_id": str(value)})
    if text not in CANONICAL_ROLES and text != OPTIONAL_SPECIALIST_ROLE:
        raise RoleContractError("ROLE_ID_NOT_P2P_ROLE", {"role_id": text})
    return text


def _hex64(value: str, field_name: str) -> str:
    text = str(value or "").strip()
    if not re.fullmatch(r"[0-9a-fA-F]{64}", text):
        raise RoleContractError("CONTRACT_HASH_FIELD_INVALID", {"field": field_name})
    return text.lower()


def _limited_text(value: str, field_name: str, max_length: int) -> str:
    text = str(value or "")
    if len(text) > max_length:
        raise RoleContractError("CONTRACT_FIELD_TOO_LONG", {"field": field_name})
    return text


def _assert_enum(value: str, allowed: tuple[str, ...], field_name: str) -> None:
    if value not in allowed:
        raise RoleContractError("CONTRACT_ENUM_INVALID",
                                {"field": field_name, "value": value})


def _assert_text_tuple(values: tuple[str, ...], name: str) -> None:
    if not isinstance(values, tuple):
        raise RoleContractError("CONTRACT_TUPLE_INVALID", {"field": name})
    for index, item in enumerate(values):
        if not isinstance(item, str):
            raise RoleContractError("CONTRACT_TUPLE_ITEM_INVALID",
                                    {"field": name, "index": index})
