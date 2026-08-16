"""Fact-origin and retrieved-content authority boundaries."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Mapping


FACT_ORIGINS = ("OWNER", "RUNTIME_EVIDENCE", "OFFICIAL_SOURCE", "RETRIEVED_SOURCE", "TOOL_OUTPUT", "MODEL_INFERENCE", "SPECIALIST_OPINION")
CONTENT_CLASSES = ("CONTENT", "INSTRUCTION_AUTHORITY", "UNKNOWN")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class FactClaim:
    claim: str
    origin: str
    source: str
    protected: bool = False
    approval_reference: str | Mapping[str, Any] | None = None


@dataclass(frozen=True)
class InstructionBoundary:
    content: str
    content_class: str
    source: str
    requests_permission: bool = False


def classify_retrieved_item(item: InstructionBoundary) -> dict[str, Any]:
    if item.content_class not in CONTENT_CLASSES:
        return {"status": "UNKNOWN", "reason": "CONTENT_CLASS_INVALID", "can_grant_tools": False, "can_grant_permissions": False}
    if item.content_class == "CONTENT":
        status = "CONTENT_WITHOUT_AUTHORITY"
    elif item.content_class == "INSTRUCTION_AUTHORITY":
        status = "REQUIRES_VALIDATED_SOURCE"
    else:
        status = "UNKNOWN"
    return {
        "status": status,
        "source": item.source,
        "can_grant_tools": False,
        "can_grant_permissions": False,
        "requests_permission": item.requests_permission,
    }


def evaluate_fact_claim(claim: FactClaim) -> dict[str, Any]:
    if claim.origin not in FACT_ORIGINS:
        return {"status": "UNKNOWN", "reason": "FACT_ORIGIN_INVALID", "canonical_write": False}
    protected_write_allowed = claim.origin in {"OWNER", "RUNTIME_EVIDENCE", "OFFICIAL_SOURCE"} and bool(claim.approval_reference or not claim.protected)
    if claim.protected and claim.approval_reference:
        approval = claim.approval_reference
        if not isinstance(approval, Mapping):
            return {
                "status": "INCOMPLETE",
                "reason": "PROTECTED_FACT_APPROVAL_UNBOUND",
                "canonical_write": False,
                "origin": claim.origin,
            }
        if (
            str(approval.get("ref") or "").strip() == ""
            or approval.get("subject") != claim.source
            or not _SHA256_RE.fullmatch(str(approval.get("subject_sha256") or "").lower())
            or approval.get("state") != "APPROVED"
            or approval.get("decision") != "APPROVE"
        ):
            return {
                "status": "INCOMPLETE",
                "reason": "PROTECTED_FACT_APPROVAL_UNBOUND",
                "canonical_write": False,
                "origin": claim.origin,
            }
    if claim.protected and not protected_write_allowed:
        return {"status": "INCOMPLETE", "reason": "PROTECTED_FACT_REQUIRES_AUTHORITY", "canonical_write": False, "origin": claim.origin}
    if claim.origin in {"RETRIEVED_SOURCE", "TOOL_OUTPUT", "MODEL_INFERENCE", "SPECIALIST_OPINION"}:
        return {"status": "INCOMPLETE", "reason": "PROPOSED_FACT_NOT_CANONICAL", "canonical_write": False, "origin": claim.origin}
    return {"status": "VERIFIED", "reason": "AUTHORIZED_ORIGIN", "canonical_write": True, "origin": claim.origin}
