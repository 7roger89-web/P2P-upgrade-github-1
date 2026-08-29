"""C35 Portable Agent Role Specification (provider-neutral).

Recovers canonical P2P role definitions from repository truth —
``capabilities.json`` (structured capability registry) and
``.codex/agents/p2p-*.toml`` (codex agent profile bodies) — and represents
each role as a portable, deterministic, cryptographically-fingerprintable
specification.

Recovery order is RECOVER -> REUSE -> EXTEND -> CREATE ONLY IF NECESSARY:

    capabilities.json  (structured authority: authority, prohibited
                         actions, evidence contract, approval boundary,
                         requires, version)
    .codex/agents/     (canonical profile bodies: description, purpose,
                         sandbox_mode, developer_instructions)
    governance.py      (canonical membership + quorum denominator truth)

Source-of-truth fields in capabilities.json win. The codex profile supplies
a deterministic profile-body fingerprint and human-readable purpose text.

Role identity is cryptographically bindable: the ROLE_SPEC_HASH changes
when material execution semantics change (any field affecting what the
role may do, must not do, or must prove). Formatting-only / non-semantic
metadata does NOT alter the fingerprint — only the semantic field set is
hashed, per the existing canonical fingerprint policy (model.py's
identity_hash = canonical JSON -> SHA-256, reuse-identical style).

Canonical council membership is recovered from ``CANONICAL_ROLES`` below,
which MUST stay byte-identical to the governance/manifest canonical
identity set. Do not rename, collapse, replace, or reinterpret.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping

from .backend_contract import CERTIFICATION_SCOPES

# ---------------------------------------------------------------------------
# Canonical truth — recovered, not invented. MUST equal the governance set.
# ---------------------------------------------------------------------------
CANONICAL_ROLES = (
    "p2p_iris",
    "p2p_tecton",
    "p2p_axiom",
    "p2p_vector",
    "p2p_datos",
    "p2p_anon",
    "p2p_architecton",
    "p2p_helios",
)
OPTIONAL_SPECIALIST_ROLE = "p2p_aesthetica"
CANONICAL_ROLE_DENOMINATOR = 8

ALL_P2P_ROLES = tuple(list(CANONICAL_ROLES) + [OPTIONAL_SPECIALIST_ROLE])

ROLE_SPEC_SCHEMA = "p2p-agent-role-spec/1"
ROLE_REGISTRY_SCHEMA = "p2p-agent-role-registry/1"

AUTHORITY_CLASSES = (
    "GOVERNANCE_MANDATED",   # requires a governance gate to invoke
    "MODEL_ROUTABLE",        # the model layer may route to it (specialist)
    "USER_REQUESTED",        # direct owner request
    "UNKNOWN",
)

MUTATION_POLICIES = ("READ_ONLY", "BOUNDED_MUTATION", "UNKNOWN")

CONTEXT_POLICIES = ("NONE", "BOUNDED_EXPLICIT", "UNKNOWN")

QUORUM_SEMANTICS_TYPES = (
    "CANONICAL_QUORUM_MEMBER",
    "OPTIONAL_SPECIALIST",
    "SUPPORTING_SPECIALIST",
    "NOT_A_ROLE",
    "UNKNOWN",
)

CAPABILITY_REQUIREMENT_CLASSES = (
    # C34 certification scopes, including the normalized operational
    # vocabulary, are the role capability vocabulary too.
    *CERTIFICATION_SCOPES,
    # Registry-internal authority/ledger needs (not backend capabilities).
    "FACT_LEDGER",
    "evidence-contract",
    "EXISTING_P2P_ROUTER",
    "real-profile-readiness",
    "UNKNOWN",
)


class AgentRoleError(ValueError):
    """Raised only when a role spec cannot be safely used."""

    def __init__(self, code: str, details: Mapping[str, Any] | None = None):
        self.code = code
        self.details = details or {}
        message = f"AGENT_ROLE_ERROR:{code}"
        if details:
            message += ":" + json.dumps(details, sort_keys=True)[:256]
        super().__init__(message)


# Semantic field set for fingerprinting: fields that change what the role
# may do, must not do, or must prove. Descriptions, profile-body prose, and
# source pointers are non-semantic (they do NOT change the hash) per the
# existing canonical fingerprint policy.
_SEMANTIC_FIELDS = (
    "role_id",
    "authority",
    "forbidden_actions",
    "permission_ceiling",
    "default_mutation_policy",
    "required_capabilities",
    "evidence_requirements",
    "context_policy",
    "quorum_semantics",
    "authority_class",
    "schema_version",
)

# Codex profile field for the profile-body fingerprint (prose is excluded
# from the role identity; the profile body has its own stable hash).
_PROFILE_SEMANTIC_KEYS = ("name", "description", "sandbox_mode")


@dataclass(frozen=True)
class AgentRoleSpec:
    """Portable canonical role specification. Provider/model/harness neutral."""
    schema: str = ROLE_SPEC_SCHEMA
    role_id: str = ""
    schema_version: str = "1"
    source_provenance: Mapping[str, Any] = field(default_factory=dict)
    purpose: str = ""
    responsibilities: tuple[str, ...] = ()
    forbidden_actions: tuple[str, ...] = ()
    authority_class: str = "UNKNOWN"
    default_mutation_policy: str = "UNKNOWN"
    permission_ceiling: tuple[str, ...] = ()
    required_capabilities: tuple[str, ...] = ()
    optional_capabilities: tuple[str, ...] = ()
    required_input_classes: tuple[str, ...] = ()
    output_schema: tuple[str, ...] = ()
    evidence_requirements: tuple[str, ...] = ()
    verification_requirements: tuple[str, ...] = ()
    context_policy: str = "UNKNOWN"
    quorum_semantics: str = "UNKNOWN"
    specialist_trigger_metadata: Mapping[str, Any] = field(default_factory=dict)
    profile_body_fingerprint: str = ""
    role_spec_hash: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "role_id", _role_id_text(self.role_id))
        object.__setattr__(self, "purpose", _limited_text(self.purpose, "purpose", 512))
        _assert_enum(self.authority_class, AUTHORITY_CLASSES, "authority_class")
        _assert_enum(self.default_mutation_policy, MUTATION_POLICIES,
                     "default_mutation_policy")
        _assert_enum(self.context_policy, CONTEXT_POLICIES, "context_policy")
        _assert_enum(self.quorum_semantics, QUORUM_SEMANTICS_TYPES, "quorum_semantics")
        for name, values in (
            ("responsibilities", self.responsibilities),
            ("forbidden_actions", self.forbidden_actions),
            ("permission_ceiling", self.permission_ceiling),
            ("required_capabilities", self.required_capabilities),
            ("optional_capabilities", self.optional_capabilities),
            ("required_input_classes", self.required_input_classes),
            ("output_schema", self.output_schema),
            ("evidence_requirements", self.evidence_requirements),
            ("verification_requirements", self.verification_requirements),
        ):
            _assert_text_tuple(values, name)
        _assert_provenance(self.source_provenance)
        object.__setattr__(self, "profile_body_fingerprint",
                           _hex64(self.profile_body_fingerprint, "profile_body_fingerprint"))
        object.__setattr__(self, "role_spec_hash",
                           _hex64(self.role_spec_hash, "role_spec_hash"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "role_id": self.role_id,
            "schema_version": self.schema_version,
            "source_provenance": dict(self.source_provenance),
            "purpose": self.purpose,
            "responsibilities": list(self.responsibilities),
            "forbidden_actions": list(self.forbidden_actions),
            "authority_class": self.authority_class,
            "default_mutation_policy": self.default_mutation_policy,
            "permission_ceiling": list(self.permission_ceiling),
            "required_capabilities": list(self.required_capabilities),
            "optional_capabilities": list(self.optional_capabilities),
            "required_input_classes": list(self.required_input_classes),
            "output_schema": list(self.output_schema),
            "evidence_requirements": list(self.evidence_requirements),
            "verification_requirements": list(self.verification_requirements),
            "context_policy": self.context_policy,
            "quorum_semantics": self.quorum_semantics,
            "specialist_trigger_metadata": dict(self.specialist_trigger_metadata),
            "profile_body_fingerprint": self.profile_body_fingerprint,
            "role_spec_hash": self.role_spec_hash,
        }


def _hex64(value: str, field_name: str) -> str:
    if not isinstance(value, str):
        raise AgentRoleError("ROLE_SPEC_FIELD_INVALID", {"field": field_name})
    text = value.strip()
    if not re.fullmatch(r"[0-9a-fA-F]{64}", text):
        raise AgentRoleError("ROLE_SPEC_HASH_INVALID", {"field": field_name})
    return text.lower()


def _role_id_text(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"p2p_[a-z][a-z0-9_]{2,40}", value):
        raise AgentRoleError("ROLE_ID_INVALID", {"role_id": str(value)})
    return value


def _limited_text(value: str, field_name: str, max_length: int) -> str:
    if not isinstance(value, str):
        raise AgentRoleError("ROLE_SPEC_FIELD_INVALID", {"field": field_name})
    if len(value) > max_length:
        raise AgentRoleError("ROLE_SPEC_FIELD_TOO_LONG", {"field": field_name})
    return value


def _assert_enum(value: str, allowed: tuple[str, ...], field_name: str) -> None:
    if value not in allowed:
        raise AgentRoleError("ROLE_SPEC_FIELD_INVALID",
                             {"field": field_name, "allowed": list(allowed), "value": value})


def _assert_text_tuple(values: tuple[str, ...], name: str) -> None:
    if not isinstance(values, tuple):
        raise AgentRoleError("ROLE_SPEC_FIELD_INVALID", {"field": name})
    for index, item in enumerate(values):
        if not isinstance(item, str) or not item.strip():
            raise AgentRoleError("ROLE_SPEC_FIELD_INVALID", {"field": name, "index": index})


def _assert_provenance(provenance: Mapping[str, Any]) -> None:
    if not isinstance(provenance, Mapping):
        raise AgentRoleError("SOURCE_PROVENANCE_INVALID", {})
    for key, value in provenance.items():
        if not isinstance(key, str) or not key.strip():
            raise AgentRoleError("SOURCE_PROVENANCE_KEY_INVALID", {"key": str(key)})
        if not isinstance(value, (str, bool, type(None))):
            raise AgentRoleError("SOURCE_PROVENANCE_VALUE_INVALID", {"key": key})


def role_semantic_fingerprint(spec_fields: Mapping[str, Any]) -> str:
    """Deterministic fingerprint of a role spec's material execution
    semantics. Formatting-only / non-semantic metadata does NOT alter it
    (purpose, responsibilities prose, profile fingerprints, specialist
    trigger metadata are non-semantic)."""
    semantic = {name: spec_fields.get(name) for name in _SEMANTIC_FIELDS}
    payload = json.dumps(semantic, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def profile_body_fingerprint(raw_profile: Mapping[str, Any]) -> str:
    """Deterministic hash of a codex profile's semantic body (name,
    description, sandbox_mode). Developer instructions prose is excluded
    from the role identity; it is downstream prompt compilation."""
    body = {key: raw_profile.get(key) for key in _PROFILE_SEMANTIC_KEYS}
    payload = json.dumps(body, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


# ---------------------------------------------------------------------------
# Recovery: capabilities.json + codex profiles + governance membership.
# ---------------------------------------------------------------------------

def _canonical_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _registry_path() -> Path:
    return _canonical_root() / "p2p_capabilities" / "capabilities.json"


def _profile_dir() -> Path:
    root = _canonical_root().parent.parent
    candidate = root / ".codex" / "agents"
    if candidate.is_dir():
        return candidate
    return root / ".agents" / "skills" / "p2p-quorum" / "assets" / "codex-agents"


def load_capability_registry(path: str | Path | None = None) -> list[dict[str, Any]]:
    """Load the structured capability registry. Returns raw records."""
    resolved = Path(path) if path else _registry_path()
    raw = json.loads(resolved.read_text(encoding="utf-8"))
    capabilities = raw.get("capabilities")
    if not isinstance(capabilities, list) or not capabilities:
        raise AgentRoleError("CAPABILITY_REGISTRY_EMPTY", {"path": str(resolved)})
    return list(capabilities)


def _find_record(records: Iterable[Mapping[str, Any]], role_id: str) -> dict[str, Any] | None:
    for record in records:
        if isinstance(record, Mapping) and record.get("CAPABILITY_ID") == role_id:
            return dict(record)
    return None


def _load_profile(role_id: str) -> dict[str, Any] | None:
    directory = _profile_dir()
    file_name = role_id.replace("_", "-") + ".toml"
    path = directory / file_name
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8")
    record: dict[str, Any] = {}
    for match in re.finditer(r'^([a-zA-Z_]+)\s*=\s*(.+)$', text, re.MULTILINE):
        key, value = match.group(1), match.group(2).strip()
        if key in _PROFILE_SEMANTIC_KEYS:
            record[key] = value.strip('"').strip("'")
    return record or None


def _role_purpose(record: dict[str, Any], profile: dict[str, Any] | None) -> str:
    purpose = str(record.get("DESCRIPTION") or "")
    if not purpose and profile:
        purpose = str(profile.get("description") or "")
    return purpose


def _quorum_semantics(record: Mapping[str, Any]) -> str:
    if record.get("CANONICAL_QUORUM_MEMBER") is True:
        return "CANONICAL_QUORUM_MEMBER"
    if record.get("OPTIONAL_SPECIALIST") is True:
        return "OPTIONAL_SPECIALIST"
    return "NOT_A_ROLE"


def build_role_spec(role_id: str, registry_records: Iterable[Mapping[str, Any]]
                    | None = None) -> AgentRoleSpec:
    """Recover one canonical role spec from repository truth.

    Raises AgentRoleError for unknown or non-role ids."""
    role_id = _role_id_text(role_id)
    records = list(registry_records) if registry_records is not None else load_capability_registry()
    record = _find_record(records, role_id)
    if record is None:
        raise AgentRoleError("ROLE_ID_UNKNOWN", {"role_id": role_id})
    profile = _load_profile(role_id)
    authority = tuple(str(item) for item in record.get("AUTHORITY") or ())
    forbidden = tuple(str(item) for item in record.get("PROHIBITED_ACTIONS") or ())
    requires = tuple(str(item) for item in record.get("REQUIRES") or ())
    evidence = tuple(str(item) for item in record.get("EVIDENCE_CONTRACT") or ())
    approval = tuple(str(item) for item in record.get("APPROVAL_BOUNDARY") or ())
    context_pointers = tuple(str(item) for item in record.get("CONTEXT_POINTERS") or ())

    capabilities: list[str] = []
    for name in requires:
        if name in CAPABILITY_REQUIREMENT_CLASSES:
            capabilities.append(name)
    responsibilities = (f"exercise-authority:{item}" for item in authority)

    trigger_metadata: dict[str, Any] = {}
    if record.get("OPTIONAL_SPECIALIST") is True:
        triggers = record.get("TRIGGERS") or ()
        negative = record.get("NEGATIVE_TRIGGERS") or ()
        trigger_metadata = {
            "triggers": tuple(str(t) for t in triggers)[:20],
            "negative_triggers": tuple(str(t) for t in negative)[:20],
        }

    spec_fields: dict[str, Any] = {
        "role_id": role_id,
        "schema_version": str(record.get("VERSION") or "1.0.0"),
        "source_provenance": {
            "capability_registry": "p2p-capability-registry/1",
            "capability_record_version": str(record.get("VERSION") or "1.0.0"),
            "registry_field_names": ",".join(sorted(str(key) for key in record.keys())),
            "codex_profile": profile is not None,
        },
        "purpose": _role_purpose(record, profile),
        "responsibilities": tuple(responsibilities),
        "forbidden_actions": forbidden,
        "authority_class": ("GOVERNANCE_MANDATED"
                            if record.get("INVOCATION_CLASS") == "GOVERNANCE_MANDATED"
                            else "MODEL_ROUTABLE"),
        "default_mutation_policy": ("READ_ONLY"
                                    if (profile or {}).get("sandbox_mode") == "read-only"
                                    else "BOUNDED_MUTATION"),
        "permission_ceiling": approval,
        "required_capabilities": tuple(capabilities),
        "optional_capabilities": tuple(),
        "required_input_classes": context_pointers,
        "output_schema": tuple(str(item) for item in record.get("EVIDENCE_CONTRACT") or ())[:6],
        "evidence_requirements": evidence,
        "verification_requirements": tuple(str(item) for item in evidence) + ("independent-check",),
        "context_policy": "BOUNDED_EXPLICIT",
        "quorum_semantics": _quorum_semantics(record),
        "specialist_trigger_metadata": trigger_metadata,
    }
    if profile:
        spec_fields["source_provenance"] = dict(spec_fields["source_provenance"])
        spec_fields["source_provenance"]["codex_profile_file"] = f".codex/agents/{role_id.replace('_', '-')}.toml"
        spec_fields["profile_body_fingerprint"] = profile_body_fingerprint(profile)

    fingerprint = role_semantic_fingerprint(spec_fields)
    return AgentRoleSpec(
        schema=spec_fields.get("schema", ROLE_SPEC_SCHEMA),
        role_id=str(spec_fields["role_id"]),
        schema_version=str(spec_fields.get("schema_version", "1")),
        source_provenance=spec_fields.get("source_provenance"),
        purpose=str(spec_fields.get("purpose", "")),
        responsibilities=spec_fields.get("responsibilities", ()),
        forbidden_actions=spec_fields.get("forbidden_actions", ()),
        authority_class=spec_fields.get("authority_class", "UNKNOWN"),
        default_mutation_policy=spec_fields.get("default_mutation_policy", "UNKNOWN"),
        permission_ceiling=spec_fields.get("permission_ceiling", ()),
        required_capabilities=spec_fields.get("required_capabilities", ()),
        optional_capabilities=spec_fields.get("optional_capabilities", ()),
        required_input_classes=spec_fields.get("required_input_classes", ()),
        output_schema=spec_fields.get("output_schema", ()),
        evidence_requirements=spec_fields.get("evidence_requirements", ()),
        verification_requirements=spec_fields.get("verification_requirements", ()),
        context_policy=spec_fields.get("context_policy", "UNKNOWN"),
        quorum_semantics=spec_fields.get("quorum_semantics", "UNKNOWN"),
        specialist_trigger_metadata=spec_fields.get("specialist_trigger_metadata", {}),
        profile_body_fingerprint=str(spec_fields.get("profile_body_fingerprint", "")),
        role_spec_hash=fingerprint,
    )


def canonical_role_specs(registry_records: Iterable[Mapping[str, Any]]
                         | None = None) -> list[AgentRoleSpec]:
    """Recover all eight canonical role specs (progressive disclosure: the
    caller loads full bodies only for the roles it participates with)."""
    return [build_role_spec(role_id, registry_records) for role_id in CANONICAL_ROLES]


def role_spec_lookup(registry_records: Iterable[Mapping[str, Any]]
                     | None = None) -> dict[str, AgentRoleSpec]:
    records = list(registry_records) if registry_records is not None else load_capability_registry()
    specs: dict[str, AgentRoleSpec] = {}
    for role_id in ALL_P2P_ROLES:
        record = _find_record(records, role_id)
        if record is not None:
            specs[role_id] = build_role_spec(role_id, records)
    return specs


def validate_role_inventory(registry_records: Iterable[Mapping[str, Any]]
                            | None = None) -> dict[str, Any]:
    """Recovered canonical identity validation. Mirrors governance
    semantics: exactly eight canonical members, aesthetica optional and
    excluded from the denominator."""
    records = list(registry_records) if registry_records is not None else load_capability_registry()
    ids = [str(record.get("CAPABILITY_ID")) for record in records
           if isinstance(record, Mapping) and record.get("CAPABILITY_ID")]
    canonical_present = sorted(set(ids) & set(CANONICAL_ROLES))
    canonical_missing = sorted(set(CANONICAL_ROLES) - set(canonical_present))
    optional_members = sorted(
        str(record.get("CAPABILITY_ID")) for record in records
        if isinstance(record, Mapping) and record.get("OPTIONAL_SPECIALIST") is True
    )
    errors: list[dict[str, Any]] = []
    if canonical_missing:
        errors.append({"code": "CANONICAL_ROLE_MISSING", "missing": canonical_missing})
    if set(canonical_present) != set(CANONICAL_ROLES):
        errors.append({"code": "CANONICAL_ROLE_SET_INVALID",
                       "expected": list(CANONICAL_ROLES), "actual": canonical_present})
    aesthetica_missing = OPTIONAL_SPECIALIST_ROLE not in ids
    aesthetica_extra_count = ids.count(OPTIONAL_SPECIALIST_ROLE) > 1
    if aesthetica_missing or aesthetica_extra_count:
        errors.append({"code": "AESTHETICA_OPTIONAL_PROFILE_INVALID",
                       "missing": aesthetica_missing, "duplicated": aesthetica_extra_count})
    for record in records:
        if not isinstance(record, Mapping):
            continue
        role_id = str(record.get("CAPABILITY_ID"))
        if role_id in CANONICAL_ROLES:
            if record.get("CANONICAL_QUORUM_MEMBER") is not True:
                errors.append({"code": "CANONICAL_QUORUM_MEMBERSHIP_INVALID", "role_id": role_id})
            if record.get("OPTIONAL_SPECIALIST") is not False:
                errors.append({"code": "CANONICAL_OPTIONAL_SPECIALIST_INVALID", "role_id": role_id})
        elif role_id == OPTIONAL_SPECIALIST_ROLE:
            if record.get("CANONICAL_QUORUM_MEMBER") is not False:
                errors.append({"code": "AESTHETICA_QUORUM_MEMBER_INVALID", "role_id": role_id})
            if record.get("OPTIONAL_SPECIALIST") is not True:
                errors.append({"code": "AESTHETICA_OPTIONAL_FLAG_INVALID", "role_id": role_id})
    return {
        "schema": ROLE_REGISTRY_SCHEMA,
        "canonical_roles": list(CANONICAL_ROLES),
        "canonical_count": len(canonical_present),
        "canonical_denominator": CANONICAL_ROLE_DENOMINATOR,
        "optional_specialist": OPTIONAL_SPECIALIST_ROLE,
        "optional_excluded_from_denominator": True,
        "optional_members": optional_members,
        "aesthetica_present": OPTIONAL_SPECIALIST_ROLE in ids,
        "errors": errors,
        "valid": not errors,
    }
