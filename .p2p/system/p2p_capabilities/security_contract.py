"""Small, provider-neutral security and reverse-engineering contracts.

This module adds vocabulary and result validation to the existing P2P control
plane. It is deliberately not a router, registry, risk engine, executor, or
authority store. Backend output remains evidence and never grants permission.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from .model import SEMANTIC_KINDS

SECURITY_REVERSE_CONTRACT_SCHEMA = "p2p-security-reverse-contract/1"
SECURITY_EXECUTION_CLASSES = (
    "SAFE_READONLY",
    "ANALYSIS_LOCAL",
    "ACTIVE_TEST_AUTHORIZED",
    "OFFENSIVE_HIGH_RISK",
    "DESTRUCTIVE_OR_INTRUSIVE",
)
SAFE_READONLY = "SAFE_READONLY"
ANALYSIS_LOCAL = "ANALYSIS_LOCAL"
ACTIVE_TEST_AUTHORIZED = "ACTIVE_TEST_AUTHORIZED"
OFFENSIVE_HIGH_RISK = "OFFENSIVE_HIGH_RISK"
DESTRUCTIVE_OR_INTRUSIVE = "DESTRUCTIVE_OR_INTRUSIVE"

SECURITY_RESULT_STATUSES = ("VERIFIED", "UNKNOWN", "UNAVAILABLE", "REJECTED")
FINDING_CATEGORIES = ("PACKER", "PROTECTOR", "COMPILER", "OBFUSCATOR")
CONFIDENCE_LEVELS = ("HIGH", "MEDIUM", "LOW", "UNKNOWN")
UNCERTAINTY_STATES = ("NONE", "UNKNOWN", "INSUFFICIENT_EVIDENCE", "CONTRADICTED")
REVERSE_OUTPUT_KINDS = ("DECOMPILED_OUTPUT", "RECONSTRUCTED_SEMANTICS")


class SecurityContractError(ValueError):
    """Raised when a security or reverse result cannot be represented safely."""


def _text(value: Any, field_name: str, *, max_length: int = 256) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SecurityContractError(f"{field_name.upper()}_REQUIRED")
    value = value.strip()
    if len(value) > max_length:
        raise SecurityContractError(f"{field_name.upper()}_TOO_LONG")
    return value


def _refs(value: Any, field_name: str) -> tuple[str, ...]:
    if not isinstance(value, (tuple, list)):
        raise SecurityContractError(f"{field_name.upper()}_MUST_BE_LIST")
    result = tuple(_text(item, field_name, max_length=512) for item in value)
    if len(result) != len(set(result)):
        raise SecurityContractError(f"{field_name.upper()}_DUPLICATE")
    return result


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _validate_sha256(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
        raise SecurityContractError(f"{field_name.upper()}_INVALID")
    return value


def normalize_execution_class(value: Any) -> str:
    normalized = str(value).upper().strip()
    if normalized not in SECURITY_EXECUTION_CLASSES:
        raise SecurityContractError(f"SECURITY_EXECUTION_CLASS_INVALID:{normalized}")
    return normalized


def authorize_security_execution(
    execution_class: str,
    *,
    target_authorized: bool = False,
    controlled_test_environment: bool = False,
    explicit_task_authority: bool = False,
) -> dict[str, Any]:
    """Return the existing-control-plane authorization decision.

    SAFE_READONLY and ANALYSIS_LOCAL are bounded local classes; the adapter or
    caller still has to validate its local artifact boundary. Active and more
    dangerous classes are never implicitly authorized by this function.
    """

    normalized = normalize_execution_class(execution_class)
    for name, value in (
        ("target_authorized", target_authorized),
        ("controlled_test_environment", controlled_test_environment),
        ("explicit_task_authority", explicit_task_authority),
    ):
        if not isinstance(value, bool):
            raise SecurityContractError(f"{name.upper()}_MUST_BE_BOOLEAN")

    required = {
        "target_authorized": normalized in {
            ACTIVE_TEST_AUTHORIZED,
            OFFENSIVE_HIGH_RISK,
            DESTRUCTIVE_OR_INTRUSIVE,
        },
        "controlled_test_environment": normalized in {
            ACTIVE_TEST_AUTHORIZED,
            OFFENSIVE_HIGH_RISK,
            DESTRUCTIVE_OR_INTRUSIVE,
        },
        "explicit_task_authority": normalized == OFFENSIVE_HIGH_RISK,
    }
    reasons: list[str] = []
    allowed = True
    if normalized == DESTRUCTIVE_OR_INTRUSIVE:
        allowed = False
        reasons.append("DESTRUCTIVE_OR_INTRUSIVE_DENIED_BY_DEFAULT")
    elif required["target_authorized"] and not target_authorized:
        allowed = False
        reasons.append("TARGET_AUTHORIZATION_REQUIRED")
    elif required["controlled_test_environment"] and not controlled_test_environment:
        allowed = False
        reasons.append("CONTROLLED_TEST_ENVIRONMENT_REQUIRED")
    elif required["explicit_task_authority"] and not explicit_task_authority:
        allowed = False
        reasons.append("EXPLICIT_TASK_AUTHORITY_REQUIRED")
    else:
        reasons.append("BOUNDED_SECURITY_CLASS_ALLOWED")

    return {
        "schema": SECURITY_REVERSE_CONTRACT_SCHEMA,
        "execution_class": normalized,
        "status": "ALLOWED" if allowed else "BLOCKED",
        "allowed": allowed,
        "fail_closed": True,
        "required": required,
        "observed": {
            "target_authorized": target_authorized,
            "controlled_test_environment": controlled_test_environment,
            "explicit_task_authority": explicit_task_authority,
        },
        "reason_codes": reasons,
    }


@dataclass(frozen=True)
class SecurityArtifactIdentity:
    """Hash-bound identity for a local analysis artifact."""

    path: str
    sha256: str
    size_bytes: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", _text(self.path, "path", max_length=4096))
        _validate_sha256(self.sha256, "sha256")
        if type(self.size_bytes) is not int or self.size_bytes < 0:
            raise SecurityContractError("SIZE_BYTES_INVALID")

    @classmethod
    def from_path(cls, path: str | Path) -> "SecurityArtifactIdentity":
        source = Path(path)
        return cls(
            path=str(source),
            sha256=_sha256(source.read_bytes()),
            size_bytes=source.stat().st_size,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
        }


@dataclass(frozen=True)
class NormalizedSecurityFinding:
    """A backend-supported security finding with no invented certainty."""

    category: str
    label: str
    evidence_refs: tuple[str, ...]
    confidence: str = "UNKNOWN"
    semantic_label: str | None = None

    def __post_init__(self) -> None:
        if self.category not in FINDING_CATEGORIES:
            raise SecurityContractError("FINDING_CATEGORY_INVALID")
        object.__setattr__(self, "label", _text(self.label, "label", max_length=512))
        object.__setattr__(self, "evidence_refs", _refs(self.evidence_refs, "evidence_refs"))
        if self.confidence not in CONFIDENCE_LEVELS:
            raise SecurityContractError("CONFIDENCE_INVALID")
        if self.semantic_label is not None:
            object.__setattr__(self, "semantic_label", _text(self.semantic_label, "semantic_label"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "label": self.label,
            "evidence_refs": list(self.evidence_refs),
            "confidence": self.confidence,
            "semantic_label": self.semantic_label,
        }


@dataclass(frozen=True)
class NormalizedSecurityEvidence:
    """Minimum result envelope shared by bounded security adapters."""

    capability_id: str
    status: str
    artifact_identity: SecurityArtifactIdentity | None
    backend_identity: Mapping[str, Any]
    findings: tuple[NormalizedSecurityFinding, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    uncertainty_state: str = "NONE"
    execution_class: str = SAFE_READONLY
    error_code: str | None = None
    mutation_observed: bool = False
    external_interaction: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "capability_id", _text(self.capability_id, "capability_id"))
        if self.status not in SECURITY_RESULT_STATUSES:
            raise SecurityContractError("SECURITY_RESULT_STATUS_INVALID")
        if not isinstance(self.backend_identity, Mapping) or not self.backend_identity:
            raise SecurityContractError("BACKEND_IDENTITY_REQUIRED")
        object.__setattr__(self, "findings", tuple(self.findings))
        if not all(isinstance(item, NormalizedSecurityFinding) for item in self.findings):
            raise SecurityContractError("FINDINGS_INVALID")
        object.__setattr__(self, "evidence_refs", _refs(self.evidence_refs, "evidence_refs"))
        if self.uncertainty_state not in UNCERTAINTY_STATES:
            raise SecurityContractError("UNCERTAINTY_STATE_INVALID")
        normalized_class = normalize_execution_class(self.execution_class)
        object.__setattr__(self, "execution_class", normalized_class)
        if self.status in {"UNKNOWN", "UNAVAILABLE", "REJECTED"} and self.uncertainty_state == "NONE":
            object.__setattr__(self, "uncertainty_state", "UNKNOWN")
        if self.error_code is not None:
            object.__setattr__(self, "error_code", _text(self.error_code, "error_code", max_length=128))
        if not isinstance(self.mutation_observed, bool) or not isinstance(self.external_interaction, bool):
            raise SecurityContractError("BOUNDARY_FLAGS_MUST_BE_BOOLEAN")
        if self.status != "REJECTED" and self.execution_class in {SAFE_READONLY, ANALYSIS_LOCAL} and (
            self.mutation_observed or self.external_interaction
        ):
            raise SecurityContractError("SAFE_ANALYSIS_BOUNDARY_VIOLATION")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": SECURITY_REVERSE_CONTRACT_SCHEMA,
            "capability_id": self.capability_id,
            "status": self.status,
            "artifact_identity": self.artifact_identity.to_dict() if self.artifact_identity else None,
            "backend_identity": dict(self.backend_identity),
            "findings": [item.to_dict() for item in self.findings],
            "evidence_refs": list(self.evidence_refs),
            "uncertainty_state": self.uncertainty_state,
            "execution_class": self.execution_class,
            "error_code": self.error_code,
            "boundary": {
                "mutation_observed": self.mutation_observed,
                "external_interaction": self.external_interaction,
            },
            "decompiled_output_is_reconstructed_source": False,
        }


@dataclass(frozen=True)
class ReverseEvidence:
    """Distinguishes raw decompiler output from semantic reconstruction."""

    output_kind: str
    source_evidence_refs: tuple[str, ...]
    tool_backend_identity: Mapping[str, Any]
    inferred_semantic_label: str
    confidence: str
    uncertainty_state: str

    def __post_init__(self) -> None:
        if self.output_kind not in REVERSE_OUTPUT_KINDS:
            raise SecurityContractError("REVERSE_OUTPUT_KIND_INVALID")
        object.__setattr__(self, "source_evidence_refs", _refs(self.source_evidence_refs, "source_evidence_refs"))
        if not isinstance(self.tool_backend_identity, Mapping) or not self.tool_backend_identity:
            raise SecurityContractError("TOOL_BACKEND_IDENTITY_REQUIRED")
        object.__setattr__(self, "inferred_semantic_label", _text(self.inferred_semantic_label, "inferred_semantic_label"))
        if self.confidence not in CONFIDENCE_LEVELS:
            raise SecurityContractError("CONFIDENCE_INVALID")
        if self.uncertainty_state not in UNCERTAINTY_STATES:
            raise SecurityContractError("UNCERTAINTY_STATE_INVALID")
        forbidden = {"ORIGINAL_SOURCE", "ORIGINAL_SOURCE_RECOVERED", "SOURCE_RECOVERED"}
        if self.inferred_semantic_label.upper() in forbidden:
            raise SecurityContractError("ORIGINAL_SOURCE_RECOVERY_NOT_CLAIMABLE")
        if self.output_kind == "RECONSTRUCTED_SEMANTICS":
            if not self.source_evidence_refs and self.uncertainty_state not in {
                "INSUFFICIENT_EVIDENCE",
                "CONTRADICTED",
            }:
                raise SecurityContractError("SOURCE_EVIDENCE_REQUIRED")

    @classmethod
    def unknown(cls, *, evidence_refs: tuple[str, ...] = ()) -> "ReverseEvidence":
        return cls(
            output_kind="RECONSTRUCTED_SEMANTICS",
            source_evidence_refs=evidence_refs,
            tool_backend_identity={"status": "UNKNOWN"},
            inferred_semantic_label="UNKNOWN",
            confidence="UNKNOWN",
            uncertainty_state="INSUFFICIENT_EVIDENCE",
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": SECURITY_REVERSE_CONTRACT_SCHEMA,
            "output_kind": self.output_kind,
            "source_evidence_refs": list(self.source_evidence_refs),
            "tool_backend_identity": dict(self.tool_backend_identity),
            "inferred_semantic_label": self.inferred_semantic_label,
            "confidence": self.confidence,
            "uncertainty_state": self.uncertainty_state,
            "original_source_recovery": "NOT_CLAIMED",
            "decompiled_output_is_reconstructed_source": False,
        }


__all__ = [
    "ACTIVE_TEST_AUTHORIZED",
    "ANALYSIS_LOCAL",
    "CONFIDENCE_LEVELS",
    "DECOMPILED_OUTPUT",
    "DESTRUCTIVE_OR_INTRUSIVE",
    "FINDING_CATEGORIES",
    "NormalizedSecurityEvidence",
    "NormalizedSecurityFinding",
    "OFFENSIVE_HIGH_RISK",
    "RECONSTRUCTED_SEMANTICS",
    "REVERSE_OUTPUT_KINDS",
    "ReverseEvidence",
    "SAFE_READONLY",
    "SECURITY_EXECUTION_CLASSES",
    "SECURITY_REVERSE_CONTRACT_SCHEMA",
    "SECURITY_RESULT_STATUSES",
    "SEMANTIC_KINDS",
    "SecurityArtifactIdentity",
    "SecurityContractError",
    "UNCERTAINTY_STATES",
    "authorize_security_execution",
    "normalize_execution_class",
]


# Readable aliases are kept as constants for callers that describe evidence
# in prose; they do not represent an original-source recovery claim.
DECOMPILED_OUTPUT = "DECOMPILED_OUTPUT"
RECONSTRUCTED_SEMANTICS = "RECONSTRUCTED_SEMANTICS"
