"""Provider-neutral AERG claim and observation contracts.

AERG is an evidence/assurance layer.  It does not persist state, grant
permissions, certify releases, or replace the existing evidence, role-verifier,
quality, or owner-authority contracts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import re
from typing import Any, Mapping

from .evidence import EVIDENCE_STATUSES, EvidenceClaim
from .trust import FACT_ORIGINS


ASSURANCE_LEVELS = ("NONE", "DECLARED", "MECHANICAL", "DETERMINISTIC")
ASSURANCE_RANK = {value: index for index, value in enumerate(ASSURANCE_LEVELS)}
SUBJECT_BINDING_STATES = ("BOUND", "SUBJECT_MISMATCH", "UNBOUND")
FRESHNESS_STATES = ("CURRENT", "STALE", "UNKNOWN")
PROVENANCE_STATES = ("BOUND", "INCOMPLETE", "INVALID")
AUTHORITY_STATES = ("MECHANICAL", "INDEPENDENT", "NOT_PROVEN")
CONTRADICTION_STATES = ("NONE", "CONTRADICTED", "NOT_PROVEN", "UNKNOWN")
AERG_DECISIONS = ("SUPPORTED", "CONTRADICTED", "STALE", "SUBJECT_MISMATCH", "INSUFFICIENT")

_HEX_RE = re.compile(r"^[0-9a-fA-F]+$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _canonical(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _canonical(value[key]) for key in sorted(value, key=str)}
    if isinstance(value, (list, tuple)):
        return [_canonical(item) for item in value]
    return value


def _digest(value: Any) -> str:
    payload = json.dumps(_canonical(value), ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _optional_string(value: Any) -> str | None:
    if value is None:
        return None
    value = str(value).strip()
    return value or None


@dataclass(frozen=True)
class SubjectBinding:
    """The exact subject against which an AERG claim is evaluated."""

    subject_id: str
    source_commit: str
    tree_sha256: str | None = None
    artifact_sha256: str | None = None
    project_fingerprint: str | None = None
    path: str | None = None
    process_identity: str | None = None

    def __post_init__(self) -> None:
        if not str(self.subject_id).strip() or not str(self.source_commit).strip():
            raise ValueError("AERG_SUBJECT_BINDING_REQUIRED")
        for field_name in ("source_commit", "tree_sha256", "artifact_sha256", "project_fingerprint"):
            value = getattr(self, field_name)
            if value is None:
                continue
            value = str(value)
            if not _HEX_RE.fullmatch(value) or len(value) not in (40, 64):
                raise ValueError(f"AERG_{field_name.upper()}_FINGERPRINT_INVALID")

    def as_contract(self) -> dict[str, Any]:
        return {
            "subject_id": self.subject_id,
            "source_commit": self.source_commit,
            "tree_sha256": self.tree_sha256,
            "artifact_sha256": self.artifact_sha256,
            "project_fingerprint": self.project_fingerprint,
            "path": self.path,
            "process_identity": self.process_identity,
        }


@dataclass(frozen=True)
class ClaimExpectation:
    """Gate-specific expectations; these are not a project truth state."""

    expected_status: str | None = None
    expected_exit_code: int | None = None
    expected_doctor_status: str | None = None
    expected_artifact_sha256: str | None = None
    expected_source_commit: str | None = None
    expected_tree_sha256: str | None = None
    no_mutation: bool = False
    requires_live: bool = False
    requires_external: bool = False
    requires_independent: bool = False
    required_assurance: str = "MECHANICAL"

    def __post_init__(self) -> None:
        if self.required_assurance not in ASSURANCE_LEVELS:
            raise ValueError("AERG_ASSURANCE_LEVEL_INVALID")

    def as_contract(self) -> dict[str, Any]:
        return {
            "expected_status": self.expected_status,
            "expected_exit_code": self.expected_exit_code,
            "expected_doctor_status": self.expected_doctor_status,
            "expected_artifact_sha256": self.expected_artifact_sha256,
            "expected_source_commit": self.expected_source_commit,
            "expected_tree_sha256": self.expected_tree_sha256,
            "no_mutation": self.no_mutation,
            "requires_live": self.requires_live,
            "requires_external": self.requires_external,
            "requires_independent": self.requires_independent,
            "required_assurance": self.required_assurance,
        }


@dataclass(frozen=True)
class EvidenceObservation:
    """Bounded structured evidence metadata; raw evidence content is excluded."""

    evidence_ref: str
    source: str
    origin: str
    observed_at: str
    fingerprint: str
    subject_id: str | None = None
    source_commit: str | None = None
    tree_sha256: str | None = None
    artifact_sha256: str | None = None
    project_fingerprint: str | None = None
    path: str | None = None
    process_identity: str | None = None
    producer_identity: str | None = None
    verifier_identity: str | None = None
    verifier_evidence_ref: str | None = None
    independent_verifier_status: str | None = None
    observed_status: str | None = None
    doctor_status: str | None = None
    exit_code: int | None = None
    mutation_state: str | None = None
    changed_paths: tuple[str, ...] = ()
    freshness: str = "CURRENT"
    live: bool | None = None
    fixture: bool = False
    mock: bool = False
    execution_scope: str = "INTERNAL"
    external_id: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "changed_paths", tuple(str(item) for item in self.changed_paths))

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "EvidenceObservation":
        """Map an adapter observation without making provider identity semantic."""
        exit_code = value.get("exit_code")
        if exit_code is not None:
            try:
                exit_code = int(exit_code)
            except (TypeError, ValueError):
                exit_code = None
        return cls(
            evidence_ref=str(value.get("evidence_ref") or value.get("source") or ""),
            source=str(value.get("source") or ""),
            origin=str(value.get("origin") or ""),
            observed_at=str(value.get("observed_at") or ""),
            fingerprint=str(value.get("fingerprint") or ""),
            subject_id=_optional_string(value.get("subject_id")),
            source_commit=_optional_string(value.get("source_commit")),
            tree_sha256=_optional_string(value.get("tree_sha256")),
            artifact_sha256=_optional_string(value.get("artifact_sha256") or value.get("actual_artifact_sha256")),
            project_fingerprint=_optional_string(value.get("project_fingerprint")),
            path=_optional_string(value.get("path")),
            process_identity=_optional_string(value.get("process_identity")),
            producer_identity=_optional_string(value.get("producer_identity")),
            verifier_identity=_optional_string(value.get("verifier_identity")),
            verifier_evidence_ref=_optional_string(value.get("verifier_evidence_ref")),
            independent_verifier_status=_optional_string(
                value.get("independent_verifier_status") or value.get("verifier_status")
            ),
            observed_status=_optional_string(value.get("observed_status") or value.get("status")),
            doctor_status=_optional_string(value.get("doctor_status")),
            exit_code=exit_code,
            mutation_state=_optional_string(value.get("mutation_state")),
            changed_paths=tuple(value.get("changed_paths") or ()),
            freshness=str(value.get("freshness") or "CURRENT"),
            live=value.get("live"),
            fixture=bool(value.get("fixture", False)),
            mock=bool(value.get("mock", False)),
            execution_scope=str(value.get("execution_scope") or "INTERNAL"),
            external_id=_optional_string(value.get("external_id")),
        )

    def as_evidence_contract(self, subject: SubjectBinding) -> dict[str, Any]:
        """Project into the existing bounded EvidenceClaim metadata contract."""
        scope = [f"aerg:{subject.subject_id}", self.evidence_ref]
        if self.path:
            scope.append(self.path)
        return {
            "source": self.source,
            "evidence_ref": self.evidence_ref,
            "origin": self.origin,
            "observed_at": self.observed_at,
            "freshness": self.freshness,
            "scope": scope,
            "source_binding": f"{subject.subject_id}:{self.source_commit or 'UNKNOWN'}",
            "fingerprint": self.fingerprint,
        }


@dataclass(frozen=True)
class ReliabilityClaim:
    claim_id: str
    subject: SubjectBinding
    statement: str
    expectation: ClaimExpectation
    evidence: tuple[EvidenceObservation, ...] = ()

    def with_evidence(self, observation: EvidenceObservation) -> "ReliabilityClaim":
        return ReliabilityClaim(
            claim_id=self.claim_id,
            subject=self.subject,
            statement=self.statement,
            expectation=self.expectation,
            evidence=self.evidence + (observation,),
        )

    def as_contract(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "subject": self.subject.as_contract(),
            "statement": self.statement,
            "expectation": self.expectation.as_contract(),
            "evidence_refs": [item.evidence_ref for item in self.evidence],
        }


@dataclass(frozen=True)
class AERGResult:
    claim_id: str
    original_claim: str
    status: str
    decision: str
    assurance: str
    subject_binding: str
    freshness: str
    provenance: str
    authority: str
    contradiction: str
    reasons: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    evidence_claims: tuple[EvidenceClaim, ...] = ()
    supports_existing_contract: bool = False
    can_promote: bool = False
    can_release: bool = False
    can_deploy: bool = False

    def __post_init__(self) -> None:
        if self.status not in EVIDENCE_STATUSES:
            raise ValueError("AERG_EVIDENCE_STATUS_INVALID")
        if self.decision not in AERG_DECISIONS:
            raise ValueError("AERG_DECISION_INVALID")
        if self.assurance not in ASSURANCE_LEVELS:
            raise ValueError("AERG_ASSURANCE_INVALID")
        if self.subject_binding not in SUBJECT_BINDING_STATES:
            raise ValueError("AERG_SUBJECT_BINDING_STATE_INVALID")
        if self.freshness not in FRESHNESS_STATES:
            raise ValueError("AERG_FRESHNESS_STATE_INVALID")
        if self.provenance not in PROVENANCE_STATES:
            raise ValueError("AERG_PROVENANCE_STATE_INVALID")
        if self.authority not in AUTHORITY_STATES:
            raise ValueError("AERG_AUTHORITY_STATE_INVALID")
        if self.contradiction not in CONTRADICTION_STATES:
            raise ValueError("AERG_CONTRADICTION_STATE_INVALID")

    def as_quality_input(self) -> dict[str, Any]:
        """Return a bounded derived input for the existing QI contract."""
        return {
            "claim_id": self.claim_id,
            "decision": self.decision,
            "status": self.status,
            "assurance": self.assurance,
            "subject_binding": self.subject_binding,
            "freshness": self.freshness,
            "provenance": self.provenance,
            "authority": self.authority,
            "contradiction": self.contradiction,
            "reasons": list(self.reasons),
            "supports_existing_contract": self.supports_existing_contract,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "original_claim": self.original_claim,
            "status": self.status,
            "decision": self.decision,
            "assurance": self.assurance,
            "subject_binding": self.subject_binding,
            "freshness": self.freshness,
            "provenance": self.provenance,
            "authority": self.authority,
            "contradiction": self.contradiction,
            "reasons": list(self.reasons),
            "evidence_refs": list(self.evidence_refs),
            "evidence_claims": [item.as_contract() for item in self.evidence_claims],
            "supports_existing_contract": self.supports_existing_contract,
            "can_promote": False,
            "can_release": False,
            "can_deploy": False,
        }


__all__ = [
    "AERG_DECISIONS",
    "AERGResult",
    "ASSURANCE_LEVELS",
    "AUTHORITY_STATES",
    "ClaimExpectation",
    "CONTRADICTION_STATES",
    "EvidenceObservation",
    "FRESHNESS_STATES",
    "PROVENANCE_STATES",
    "ReliabilityClaim",
    "SubjectBinding",
    "SUBJECT_BINDING_STATES",
]
