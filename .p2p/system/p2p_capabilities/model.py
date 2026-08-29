"""Manifest and canonical safety contracts for reusable capabilities."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping


CANONICAL_IDENTITIES = (
    "p2p_iris",
    "p2p_tecton",
    "p2p_axiom",
    "p2p_vector",
    "p2p_datos",
    "p2p_anon",
    "p2p_architecton",
    "p2p_helios",
)
CAPABILITY_CLASSES = (
    "SKILL",
    "OPTIONAL_SPECIALIST",
    "GOVERNANCE_POLICY",
    "KNOWLEDGE_SOURCE",
    "EVIDENCE_PROVIDER",
    "BACKEND_PROVIDER",
)
# `TYPE` remains the six-class capability contract above.  This orthogonal
# vocabulary describes the semantic role of a capability/tool seam without
# creating new registry classes or a second registry.
SEMANTIC_KINDS = (
    "SKILL",
    "TOOL",
    "ADAPTER",
    "VENDOR",
    "EXTERNAL_RUNTIME",
    "KNOWLEDGE_SOURCE",
)
INVOCATION_CLASSES = ("USER_REQUESTED", "MODEL_ROUTABLE", "GOVERNANCE_MANDATED", "HOST_PRIMITIVE")
TRUST_LEVELS = ("PURE_DATA", "HOST_CODE", "EXTERNAL_SERVICE")
STATUSES = ("ACTIVE", "DISCOVERED", "DEFERRED", "RETIRED")
READINESS_STATES = ("INSTALLED", "DISCOVERED", "ELIGIBLE", "RESOLVED", "EXECUTABLE", "HEALTHY")
MANIFEST_FIELDS = (
    "CAPABILITY_ID",
    "TYPE",
    "DESCRIPTION",
    "TRIGGERS",
    "NEGATIVE_TRIGGERS",
    "INVOCATION_CLASS",
    "CANONICAL_QUORUM_MEMBER",
    "OPTIONAL_SPECIALIST",
    "AUTHORITY",
    "PROHIBITED_ACTIONS",
    "REQUIRES",
    "CONTEXT_POINTERS",
    "APPROVAL_BOUNDARY",
    "EVIDENCE_CONTRACT",
    "TRUST_LEVEL",
    "UPSTREAM_PROVENANCE",
    "VERSION",
    "STATUS",
)
REQUIRED_FIELDS = set(MANIFEST_FIELDS)


class ManifestValidationError(ValueError):
    """Raised only when a registry cannot be safely used."""

    def __init__(self, errors: list[dict[str, Any]]):
        self.errors = errors
        super().__init__("invalid capability manifest: " + "; ".join(error["code"] for error in errors))


@dataclass(frozen=True)
class CapabilityManifest:
    capability_id: str
    type: str
    description: str
    triggers: tuple[str, ...]
    negative_triggers: tuple[str, ...]
    invocation_class: str
    canonical_quorum_member: bool
    optional_specialist: bool
    authority: tuple[str, ...]
    prohibited_actions: tuple[str, ...]
    requires: tuple[str, ...]
    context_pointers: tuple[str, ...]
    approval_boundary: tuple[str, ...]
    evidence_contract: tuple[str, ...]
    trust_level: str
    upstream_provenance: Mapping[str, Any]
    version: str
    status: str
    raw: Mapping[str, Any] = field(repr=False, compare=False)
    semantic_kind: str | None = None

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "CapabilityManifest":
        errors = _validate_one(value)
        if errors:
            raise ManifestValidationError(errors)
        return cls(
            capability_id=value["CAPABILITY_ID"],
            type=value["TYPE"],
            description=value["DESCRIPTION"],
            triggers=tuple(value["TRIGGERS"]),
            negative_triggers=tuple(value["NEGATIVE_TRIGGERS"]),
            invocation_class=value["INVOCATION_CLASS"],
            canonical_quorum_member=value["CANONICAL_QUORUM_MEMBER"],
            optional_specialist=value["OPTIONAL_SPECIALIST"],
            authority=tuple(value["AUTHORITY"]),
            prohibited_actions=tuple(value["PROHIBITED_ACTIONS"]),
            requires=tuple(value["REQUIRES"]),
            context_pointers=tuple(value["CONTEXT_POINTERS"]),
            approval_boundary=tuple(value["APPROVAL_BOUNDARY"]),
            evidence_contract=tuple(value["EVIDENCE_CONTRACT"]),
            trust_level=value["TRUST_LEVEL"],
            upstream_provenance=dict(value["UPSTREAM_PROVENANCE"]),
            version=value["VERSION"],
            status=value["STATUS"],
            raw=dict(value),
            semantic_kind=(
                str(value["SEMANTIC_KIND"]).upper().strip()
                if value.get("SEMANTIC_KIND") is not None
                else None
            ),
        )

    @property
    def identity_hash(self) -> str:
        payload = json.dumps(self.raw, sort_keys=True, ensure_ascii=False).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()


def _as_string_list(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) and item.strip() for item in value)


def _validate_one(value: Mapping[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    missing = sorted(REQUIRED_FIELDS - set(value))
    if missing:
        errors.append({"code": "MANIFEST_FIELDS_MISSING", "fields": missing})
        return errors
    if not isinstance(value["CAPABILITY_ID"], str) or not value["CAPABILITY_ID"].strip():
        errors.append({"code": "CAPABILITY_ID_INVALID"})
    if value["TYPE"] not in CAPABILITY_CLASSES:
        errors.append({"code": "CAPABILITY_TYPE_INVALID", "actual": value["TYPE"]})
    if value.get("SEMANTIC_KIND") is not None:
        semantic_kind = value["SEMANTIC_KIND"]
        if not isinstance(semantic_kind, str) or semantic_kind.upper().strip() not in SEMANTIC_KINDS:
            errors.append({"code": "SEMANTIC_KIND_INVALID", "actual": semantic_kind})
    if value["INVOCATION_CLASS"] not in INVOCATION_CLASSES:
        errors.append({"code": "INVOCATION_CLASS_INVALID", "actual": value["INVOCATION_CLASS"]})
    if value["TRUST_LEVEL"] not in TRUST_LEVELS:
        errors.append({"code": "TRUST_LEVEL_INVALID", "actual": value["TRUST_LEVEL"]})
    if value["STATUS"] not in STATUSES:
        errors.append({"code": "STATUS_INVALID", "actual": value["STATUS"]})
    for field_name in ("TRIGGERS", "NEGATIVE_TRIGGERS", "AUTHORITY", "PROHIBITED_ACTIONS", "REQUIRES", "CONTEXT_POINTERS", "APPROVAL_BOUNDARY", "EVIDENCE_CONTRACT"):
        if not _as_string_list(value[field_name]):
            errors.append({"code": "MANIFEST_LIST_INVALID", "field": field_name})
    for field_name in ("CANONICAL_QUORUM_MEMBER", "OPTIONAL_SPECIALIST"):
        if not isinstance(value[field_name], bool):
            errors.append({"code": "MANIFEST_BOOLEAN_INVALID", "field": field_name})
    if not isinstance(value["UPSTREAM_PROVENANCE"], dict):
        errors.append({"code": "UPSTREAM_PROVENANCE_INVALID"})
    if not isinstance(value["DESCRIPTION"], str) or not value["DESCRIPTION"].strip():
        errors.append({"code": "DESCRIPTION_INVALID"})
    if not isinstance(value["VERSION"], str) or not value["VERSION"].strip():
        errors.append({"code": "VERSION_INVALID"})
    if value["CANONICAL_QUORUM_MEMBER"] and value["CAPABILITY_ID"] not in CANONICAL_IDENTITIES:
        errors.append({"code": "CANONICAL_DECLARATION_INVALID", "capability_id": value["CAPABILITY_ID"]})
    if value["CANONICAL_QUORUM_MEMBER"] and value["OPTIONAL_SPECIALIST"]:
        errors.append({"code": "CANONICAL_OPTIONAL_CONFLICT", "capability_id": value["CAPABILITY_ID"]})
    if value["OPTIONAL_SPECIALIST"] and value["TYPE"] != "OPTIONAL_SPECIALIST":
        errors.append({"code": "OPTIONAL_SPECIALIST_TYPE_INVALID", "capability_id": value["CAPABILITY_ID"]})
    if value["CAPABILITY_ID"] == "p2p_aesthetica" and (not value["OPTIONAL_SPECIALIST"] or value["CANONICAL_QUORUM_MEMBER"]):
        errors.append({"code": "AESTHETICA_CLASSIFICATION_INVALID"})
    return errors


def validate_registry(values: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    entries = list(values)
    errors: list[dict[str, Any]] = []
    identities: list[str] = []
    parsed: list[CapabilityManifest] = []
    for value in entries:
        one_errors = _validate_one(value)
        errors.extend(one_errors)
        if not one_errors:
            identity = value["CAPABILITY_ID"]
            identities.append(identity)
            parsed.append(CapabilityManifest.from_mapping(value))
    duplicates = sorted({identity for identity in identities if identities.count(identity) > 1})
    if duplicates:
        errors.append({"code": "CAPABILITY_ID_DUPLICATE", "identities": duplicates})
    canonical = [identity for identity in identities if identity in CANONICAL_IDENTITIES]
    canonical_flags = [value["CAPABILITY_ID"] for value in entries if value.get("CANONICAL_QUORUM_MEMBER") is True]
    if tuple(canonical_flags) != CANONICAL_IDENTITIES:
        errors.append({"code": "CANONICAL_IDENTITY_SET_INVALID", "expected": list(CANONICAL_IDENTITIES), "actual": canonical_flags})
    if len(canonical) != 8 or len(set(canonical)) != 8:
        errors.append({"code": "CANONICAL_COUNT_INVALID", "expected": 8, "actual": len(canonical)})
    if sum(1 for value in entries if value.get("CAPABILITY_ID") == "p2p_aesthetica") != 1:
        errors.append({"code": "AESTHETICA_REQUIRED"})
    return {
        "schema": "p2p-capability-registry/1",
        "valid": not errors,
        "capability_count": len(entries),
        "capability_classes": list(CAPABILITY_CLASSES),
        "semantic_kinds": list(SEMANTIC_KINDS),
        "canonical_identities": list(CANONICAL_IDENTITIES),
        "canonical_denominator": 8,
        "full_quorum": "8/8",
        "optional_specialist": "p2p_aesthetica",
        "optional_excluded_from_denominator": True,
        "identities": identities,
        "parsed": parsed,
        "errors": errors,
    }


def load_registry(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    payload = json.loads(source.read_text(encoding="utf-8"))
    values = payload.get("capabilities") if isinstance(payload, dict) else payload
    if not isinstance(values, list):
        raise ManifestValidationError([{"code": "REGISTRY_FORMAT_INVALID"}])
    result = validate_registry(values)
    if not result["valid"]:
        raise ManifestValidationError(result["errors"])
    return {**result, "path": str(source), "registry_hash": hashlib.sha256(source.read_bytes()).hexdigest()}
