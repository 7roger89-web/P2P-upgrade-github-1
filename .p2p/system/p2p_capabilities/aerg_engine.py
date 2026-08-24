"""Deterministic, provider-neutral AI Execution Reliability Guard."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
import hashlib
import json
import re
from typing import Any, Mapping

from .evidence import EvidenceClaim
from .trust import FACT_ORIGINS
from .aerg_model import (
    AERGResult,
    ASSURANCE_LEVELS,
    ASSURANCE_RANK,
    ClaimExpectation,
    EvidenceObservation,
    ReliabilityClaim,
    SubjectBinding,
)


_SUCCESS_STATUSES = {"PASS", "PASSED", "SUCCESS", "SUCCEEDED", "HEALTHY", "VERIFIED", "CERTIFIED"}
_FAILURE_STATUSES = {"FAIL", "FAILED", "ERROR", "REJECTED", "UNHEALTHY", "CONTRADICTED"}
_NONPROOF_STATUSES = {"NOT_RUN", "UNKNOWN", "WARN", "INCOMPLETE", "UNVERIFIED", "NOT_VERIFIED"}
_MECHANICAL_ORIGINS = {"TOOL_OUTPUT", "RUNTIME_EVIDENCE", "OFFICIAL_SOURCE"}
_NO_MUTATION_RE = re.compile(r"\b(?:no\s+(?:files?\s+)?changed|no\s+mutation|unchanged)\b", re.IGNORECASE)
_INDEPENDENT_RE = re.compile(r"\bindependently?\s+verified\b", re.IGNORECASE)
_DOCTOR_HEALTHY_RE = re.compile(r"\bdoctor\b.*\bhealthy\b", re.IGNORECASE)
_STATUS_RE = re.compile(r"\b(pass(?:ed)?|fail(?:ed)?|error|verified|unknown|not_run|warn|healthy|unhealthy)\b", re.IGNORECASE)
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _now(value: str | datetime | None) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    if isinstance(value, datetime):
        parsed = value
    else:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("AERG_NOW_TIMEZONE_REQUIRED")
    return parsed.astimezone(timezone.utc)


def _parse_observed_at(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def _status(value: str | None) -> str:
    return str(value or "").strip().upper().replace(" ", "_")


def _status_equivalent(expected: str, observed: str) -> bool:
    expected = _status(expected)
    observed = _status(observed)
    if expected == observed:
        return True
    return expected in _SUCCESS_STATUSES and observed in _SUCCESS_STATUSES


class AERGEngine:
    """Evaluate claims against one current subject without persistence."""

    def __init__(
        self,
        subject: SubjectBinding,
        *,
        now: str | datetime | None = None,
        freshness_seconds: int = 300,
    ) -> None:
        if freshness_seconds <= 0:
            raise ValueError("AERG_FRESHNESS_WINDOW_INVALID")
        self.subject = subject
        self.now = _now(now)
        self.freshness_seconds = int(freshness_seconds)
        self._claims: dict[str, ReliabilityClaim] = {}

    def create_claim(
        self,
        statement: str,
        expectation: ClaimExpectation | None = None,
        *,
        subject: SubjectBinding | None = None,
    ) -> ReliabilityClaim:
        """Create a deterministic claim; the original statement is immutable."""
        statement = str(statement)
        bound_subject = subject or self.subject
        parsed_expectation = self._expectation_from_statement(statement, expectation)
        identity = {
            "subject": bound_subject.as_contract(),
            "statement": statement,
            "expectation": parsed_expectation.as_contract(),
        }
        claim_id = "AERG-" + hashlib.sha256(
            json.dumps(identity, sort_keys=True, ensure_ascii=False).encode("utf-8")
        ).hexdigest()[:16]
        claim = ReliabilityClaim(
            claim_id=claim_id,
            subject=bound_subject,
            statement=statement,
            expectation=parsed_expectation,
        )
        self._claims[claim_id] = claim
        return claim

    def add_evidence(
        self,
        claim_id: str,
        evidence: EvidenceObservation | Mapping[str, Any],
    ) -> bool:
        claim = self._claims.get(str(claim_id))
        if claim is None:
            return False
        observation = evidence if isinstance(evidence, EvidenceObservation) else EvidenceObservation.from_mapping(evidence)
        self._claims[claim.claim_id] = claim.with_evidence(observation)
        return True

    def get_claims(self) -> tuple[ReliabilityClaim, ...]:
        """Expose immutable in-memory claims for the current evaluation only."""
        return tuple(self._claims.values())

    def evaluate_claim(self, claim_id: str) -> AERGResult:
        claim = self._claims.get(str(claim_id))
        if claim is None:
            return self._empty_result("CLAIM_NOT_FOUND")
        if not claim.evidence:
            return self._result(
                claim,
                decision="INSUFFICIENT",
                status="INCOMPLETE",
                assurance="DECLARED",
                subject_binding="UNBOUND",
                freshness="UNKNOWN",
                provenance="INCOMPLETE",
                authority="NOT_PROVEN",
                contradiction="UNKNOWN",
                reasons=("CLAIM_WITHOUT_EVIDENCE",),
                evidence_claims=(),
            )

        observations = [self._evaluate_observation(claim, item) for item in claim.evidence]
        reasons = tuple(sorted({reason for item in observations for reason in item["reasons"]}))
        decisions = [item["decision"] for item in observations]
        if "CONTRADICTED" in decisions:
            decision = "CONTRADICTED"
        elif "SUBJECT_MISMATCH" in decisions:
            decision = "SUBJECT_MISMATCH"
        elif "STALE" in decisions:
            decision = "STALE"
        elif "INSUFFICIENT" in decisions:
            decision = "INSUFFICIENT"
        else:
            decision = "SUPPORTED"

        status = "VERIFIED" if decision == "SUPPORTED" else (
            "CONTRADICTED" if decision == "CONTRADICTED" else "INCOMPLETE"
        )
        assurance = max(
            (item["assurance"] for item in observations),
            key=lambda value: ASSURANCE_RANK[value],
        )
        subject_binding = "SUBJECT_MISMATCH" if "SUBJECT_MISMATCH" in decisions else (
            "UNBOUND" if any(item["subject_binding"] == "UNBOUND" for item in observations) else "BOUND"
        )
        freshness = "STALE" if "STALE" in decisions else (
            "UNKNOWN" if any(item["freshness"] == "UNKNOWN" for item in observations) else "CURRENT"
        )
        provenance = "INVALID" if any(item["provenance"] == "INVALID" for item in observations) else (
            "INCOMPLETE" if any(item["provenance"] == "INCOMPLETE" for item in observations) else "BOUND"
        )
        authority = "INDEPENDENT" if any(item["authority"] == "INDEPENDENT" for item in observations) else (
            "MECHANICAL" if any(item["authority"] == "MECHANICAL" for item in observations) else "NOT_PROVEN"
        )
        contradiction = "CONTRADICTED" if decision == "CONTRADICTED" else (
            "UNKNOWN" if decision == "INSUFFICIENT" and not reasons else "NONE"
        )
        evidence_claims = tuple(item["evidence_claim"] for item in observations)
        return self._result(
            claim,
            decision=decision,
            status=status,
            assurance=assurance,
            subject_binding=subject_binding,
            freshness=freshness,
            provenance=provenance,
            authority=authority,
            contradiction=contradiction,
            reasons=reasons,
            evidence_claims=evidence_claims,
        )

    def evaluate_all(self) -> tuple[AERGResult, ...]:
        return tuple(self.evaluate_claim(claim_id) for claim_id in self._claims)

    def _empty_result(self, reason: str) -> AERGResult:
        return AERGResult(
            claim_id="UNKNOWN",
            original_claim="",
            status="INCOMPLETE",
            decision="INSUFFICIENT",
            assurance="NONE",
            subject_binding="UNBOUND",
            freshness="UNKNOWN",
            provenance="INCOMPLETE",
            authority="NOT_PROVEN",
            contradiction="UNKNOWN",
            reasons=(reason,),
        )

    def _result(self, claim: ReliabilityClaim, **values: Any) -> AERGResult:
        decision = str(values["decision"])
        return AERGResult(
            claim_id=claim.claim_id,
            original_claim=claim.statement,
            evidence_refs=tuple(item.evidence_ref for item in claim.evidence),
            supports_existing_contract=decision == "SUPPORTED",
            **values,
        )

    def _expectation_from_statement(
        self,
        statement: str,
        expectation: ClaimExpectation | None,
    ) -> ClaimExpectation:
        expectation = expectation or ClaimExpectation()
        status = expectation.expected_status
        if status is None:
            match = _STATUS_RE.search(statement)
            if match:
                token = _status(match.group(1))
                if token in {"PASSED", "PASS"}:
                    status = "PASS"
                elif token in {"VERIFIED"}:
                    status = "VERIFIED"
                elif token in {"FAIL", "FAILED", "ERROR"}:
                    status = token
        doctor_status = expectation.expected_doctor_status
        if doctor_status is None and _DOCTOR_HEALTHY_RE.search(statement):
            doctor_status = "HEALTHY"
        no_mutation = expectation.no_mutation or bool(_NO_MUTATION_RE.search(statement))
        requires_independent = expectation.requires_independent or bool(_INDEPENDENT_RE.search(statement))
        return replace(
            expectation,
            expected_status=status,
            expected_doctor_status=doctor_status,
            no_mutation=no_mutation,
            requires_independent=requires_independent,
        )

    def _evaluate_observation(self, claim: ReliabilityClaim, observation: EvidenceObservation) -> dict[str, Any]:
        expectation = claim.expectation
        reasons: list[str] = []
        decisions: list[str] = []
        provenance = "BOUND"
        subject_binding = "BOUND"
        freshness = "CURRENT"
        authority = "NOT_PROVEN"
        assurance = "DECLARED"

        if not observation.evidence_ref or not observation.source:
            reasons.append("EVIDENCE_REFERENCE_REQUIRED")
            provenance = "INCOMPLETE"
        if observation.origin not in FACT_ORIGINS:
            reasons.append("EVIDENCE_ORIGIN_INVALID")
            provenance = "INVALID"
        if not _SHA256_RE.fullmatch(str(observation.fingerprint).lower()):
            reasons.append("EVIDENCE_FINGERPRINT_INVALID")
            provenance = "INCOMPLETE"
        observed_at = _parse_observed_at(observation.observed_at)
        if observed_at is None:
            reasons.append("OBSERVED_AT_INVALID")
            freshness = "UNKNOWN"
            provenance = "INCOMPLETE"
        else:
            age = self.now - observed_at
            if age < timedelta(seconds=0):
                reasons.append("OBSERVED_AT_IN_FUTURE")
                freshness = "UNKNOWN"
            elif age > timedelta(seconds=self.freshness_seconds):
                reasons.append("EVIDENCE_EXPIRED")
                freshness = "STALE"
        if observation.freshness not in ("CURRENT", "FRESH"):
            reasons.append("EVIDENCE_NOT_CURRENT")
            freshness = "STALE" if observation.freshness == "STALE" else "UNKNOWN"

        if not observation.subject_id:
            reasons.append("SUBJECT_BINDING_REQUIRED")
            subject_binding = "UNBOUND"
        elif observation.subject_id != claim.subject.subject_id:
            reasons.append("SUBJECT_MISMATCH")
            subject_binding = "SUBJECT_MISMATCH"
            decisions.append("SUBJECT_MISMATCH")
        if claim.subject.path and observation.path and claim.subject.path != observation.path:
            reasons.append("SUBJECT_PATH_MISMATCH")
            subject_binding = "SUBJECT_MISMATCH"
            decisions.append("SUBJECT_MISMATCH")
        if claim.subject.process_identity and observation.process_identity != claim.subject.process_identity:
            reasons.append("SUBJECT_PROCESS_MISMATCH")
            subject_binding = "SUBJECT_MISMATCH"
            decisions.append("SUBJECT_MISMATCH")

        expected_source = expectation.expected_source_commit
        if expected_source:
            if observation.source_commit != expected_source:
                reasons.append("SOURCE_COMMIT_MISMATCH")
                decisions.append("CONTRADICTED")
        elif observation.source_commit != claim.subject.source_commit:
            reasons.append("STALE_SOURCE_COMMIT")
            freshness = "STALE"
            decisions.append("STALE")
        if expectation.expected_tree_sha256 and observation.tree_sha256 != expectation.expected_tree_sha256:
            reasons.append("TREE_SHA256_MISMATCH")
            decisions.append("CONTRADICTED")
        elif claim.subject.tree_sha256 and observation.tree_sha256 != claim.subject.tree_sha256:
            reasons.append("STALE_TREE_SHA256")
            freshness = "STALE"
            decisions.append("STALE")
        if expectation.expected_artifact_sha256:
            if observation.artifact_sha256 != expectation.expected_artifact_sha256:
                reasons.append("ARTIFACT_SHA256_MISMATCH")
                decisions.append("CONTRADICTED")
        elif claim.subject.artifact_sha256 and observation.artifact_sha256 != claim.subject.artifact_sha256:
            reasons.append("STALE_ARTIFACT_SHA256")
            freshness = "STALE"
            decisions.append("STALE")
        if claim.subject.project_fingerprint and observation.project_fingerprint != claim.subject.project_fingerprint:
            reasons.append("PROJECT_FINGERPRINT_MISMATCH")
            freshness = "STALE"
            decisions.append("STALE")

        expected_status = _status(expectation.expected_status)
        observed_status = _status(observation.observed_status)
        if expected_status and not observed_status:
            reasons.append("OBSERVED_STATUS_REQUIRED")
            decisions.append("INSUFFICIENT")
        elif expected_status and observed_status and not _status_equivalent(expected_status, observed_status):
            if observed_status in _NONPROOF_STATUSES:
                reasons.append("OBSERVED_STATUS_NOT_PROVEN")
                decisions.append("INSUFFICIENT")
            elif observed_status in _FAILURE_STATUSES or expected_status in _SUCCESS_STATUSES:
                reasons.append("OBSERVED_STATUS_CONTRADICTS_CLAIM")
                decisions.append("CONTRADICTED")
            else:
                reasons.append("OBSERVED_STATUS_MISMATCH")
                decisions.append("INSUFFICIENT")
        if observed_status in _NONPROOF_STATUSES:
            reasons.append(f"{observed_status}_IS_NOT_PROOF")
            decisions.append("INSUFFICIENT")
        if expectation.expected_exit_code is not None:
            if observation.exit_code is None:
                reasons.append("EXIT_CODE_REQUIRED")
                decisions.append("INSUFFICIENT")
            elif observation.exit_code != expectation.expected_exit_code:
                reasons.append("EXIT_CODE_MISMATCH")
                decisions.append("CONTRADICTED")
        elif expected_status in _SUCCESS_STATUSES and observation.exit_code is not None and observation.exit_code != 0:
            reasons.append("EXIT_CODE_CONTRADICTS_PASS")
            decisions.append("CONTRADICTED")
        if expectation.expected_doctor_status:
            doctor = _status(observation.doctor_status)
            if not doctor:
                reasons.append("DOCTOR_STATUS_REQUIRED")
                decisions.append("INSUFFICIENT")
            elif doctor != _status(expectation.expected_doctor_status):
                if doctor in {"WARN", "UNKNOWN", "NOT_RUN"}:
                    reasons.append("DOCTOR_STATUS_NOT_HEALTHY_PROOF")
                    decisions.append("INSUFFICIENT")
                else:
                    reasons.append("DOCTOR_STATUS_CONTRADICTION")
                    decisions.append("CONTRADICTED")
        if expectation.no_mutation:
            if observation.mutation_state == "MUTATED" or observation.changed_paths:
                reasons.append("MUTATION_CONTRADICTS_NO_MUTATION")
                decisions.append("CONTRADICTED")
            elif observation.mutation_state != "UNCHANGED":
                reasons.append("MUTATION_STATE_REQUIRED")
                decisions.append("INSUFFICIENT")

        if expectation.requires_live and (observation.live is not True or observation.fixture or observation.mock):
            reasons.append("FIXTURE_OR_MOCK_IS_NOT_LIVE")
            decisions.append("INSUFFICIENT")
        if expectation.requires_external:
            if observation.execution_scope != "EXTERNAL":
                reasons.append("INTERNAL_EXECUTION_IS_NOT_EXTERNAL_PROOF")
                decisions.append("INSUFFICIENT")
            if not observation.external_id:
                reasons.append("EXTERNAL_ID_REQUIRED")
                decisions.append("INSUFFICIENT")

        same_identity = bool(observation.producer_identity and observation.verifier_identity
                             and observation.producer_identity == observation.verifier_identity)
        same_evidence = bool(observation.verifier_evidence_ref
                             and observation.verifier_evidence_ref == observation.evidence_ref)
        if (
            observation.independent_verifier_status == "VERIFIED"
            and observation.verifier_identity
            and observation.verifier_evidence_ref
            and not same_identity
            and not same_evidence
        ):
            authority = "INDEPENDENT"
        elif observation.producer_identity or observation.verifier_identity:
            authority = "NOT_PROVEN"
        if same_identity or same_evidence:
            reasons.append("EXECUTOR_SELF_VERIFICATION_NOT_INDEPENDENT")
            authority = "NOT_PROVEN"
        if expectation.requires_independent and authority != "INDEPENDENT":
            reasons.append("INDEPENDENT_ASSURANCE_NOT_PROVEN")
            decisions.append("INSUFFICIENT")

        hard_mechanical = bool(
            observation.exit_code is not None
            or observation.artifact_sha256
            or observation.doctor_status
            or observation.mutation_state
        )
        if observation.origin in _MECHANICAL_ORIGINS and hard_mechanical:
            assurance = "DETERMINISTIC" if observation.exit_code is not None or observation.artifact_sha256 else "MECHANICAL"
            if authority != "INDEPENDENT" and not (same_identity or same_evidence):
                authority = "MECHANICAL"
        elif observation.origin in _MECHANICAL_ORIGINS and observed_status in {"PASS", "VERIFIED", "HEALTHY"}:
            assurance = "MECHANICAL"
            if authority != "INDEPENDENT" and not (same_identity or same_evidence):
                authority = "MECHANICAL"
        else:
            reasons.append("UNSUPPORTED_ASSERTION_ORIGIN")
            decisions.append("INSUFFICIENT")
            assurance = "DECLARED"
        if ASSURANCE_RANK[assurance] < ASSURANCE_RANK[expectation.required_assurance]:
            reasons.append("ASSURANCE_INSUFFICIENT")
            decisions.append("INSUFFICIENT")

        if provenance != "BOUND" or subject_binding == "UNBOUND" or freshness == "UNKNOWN":
            decisions.append("INSUFFICIENT")
        if decisions:
            decision = "CONTRADICTED" if "CONTRADICTED" in decisions else (
                "SUBJECT_MISMATCH" if "SUBJECT_MISMATCH" in decisions else (
                    "STALE" if "STALE" in decisions else "INSUFFICIENT"
                )
            )
        else:
            decision = "SUPPORTED"
        raw_status = "VERIFIED" if decision == "SUPPORTED" else (
            "CONTRADICTED" if decision == "CONTRADICTED" else "INCOMPLETE"
        )
        evidence_contract = EvidenceClaim(
            claim=claim.statement,
            required_evidence=(observation.evidence_ref,),
            actual_evidence=(observation.as_evidence_contract(claim.subject),),
            status=raw_status,
        )
        return {
            "decision": decision,
            "assurance": assurance,
            "subject_binding": subject_binding,
            "freshness": freshness,
            "provenance": provenance,
            "authority": authority,
            "reasons": tuple(sorted(set(reasons))),
            "evidence_claim": evidence_contract,
        }


__all__ = ["AERGEngine"]
