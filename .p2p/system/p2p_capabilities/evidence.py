"""Independent done and minimal no-progress contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
import re
from typing import Any, Iterable, Mapping

from .trust import FACT_ORIGINS


EVIDENCE_STATUSES = ("VERIFIED", "INCOMPLETE", "CONTRADICTED", "NOT_APPLICABLE")
EVIDENCE_FRESHNESS = ("CURRENT", "FRESH")
EVIDENCE_FIELDS = {
    "source",
    "evidence_ref",
    "origin",
    "observed_at",
    "freshness",
    "scope",
    "source_binding",
    "fingerprint",
}
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_SECRET_KEY_RE = re.compile(r"(?:secret|token|password|credential|api[_-]?key|private[_-]?key|authorization|environment)", re.IGNORECASE)
_SECRET_VALUE_RE = re.compile(r"(?:api[_-]?key|password|token|secret|authorization|private[_-]?key)\s*[:=]\s*[^\s,;]+|sk-[A-Za-z0-9_-]{16,}", re.IGNORECASE)


def _safe_string(value: Any, field: str) -> list[str]:
    if not isinstance(value, str) or not value.strip() or len(value) > 4096:
        return [f"{field}_INVALID"]
    if _SECRET_VALUE_RE.search(value):
        return [f"{field}_SECRET_LIKE"]
    return []


def _actual_evidence_errors(value: Any) -> list[str]:
    if not isinstance(value, Mapping):
        return ["ACTUAL_EVIDENCE_ITEM_INVALID"]
    errors: list[str] = []
    unknown = sorted(str(key) for key in value if str(key) not in EVIDENCE_FIELDS)
    if unknown:
        errors.append("ACTUAL_EVIDENCE_FIELDS_INVALID")
    for field in ("source", "evidence_ref", "observed_at", "freshness", "source_binding"):
        errors.extend(_safe_string(value.get(field), field.upper()))
    origin = value.get("origin")
    if origin not in FACT_ORIGINS:
        errors.append("EVIDENCE_ORIGIN_INVALID")
    freshness = value.get("freshness")
    if freshness not in EVIDENCE_FRESHNESS:
        errors.append("EVIDENCE_NOT_CURRENT")
    observed_at = value.get("observed_at")
    if isinstance(observed_at, str) and observed_at.strip():
        try:
            parsed = datetime.fromisoformat(observed_at.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                errors.append("OBSERVED_AT_TIMEZONE_REQUIRED")
        except ValueError:
            errors.append("OBSERVED_AT_INVALID")
    fingerprint = value.get("fingerprint")
    if not isinstance(fingerprint, str) or not _SHA256_RE.fullmatch(fingerprint.lower()):
        errors.append("EVIDENCE_FINGERPRINT_INVALID")
    scope = value.get("scope")
    if not isinstance(scope, (list, tuple)) or not scope or any(
        not isinstance(item, str) or not item.strip() or len(item) > 512 for item in scope
    ):
        errors.append("EVIDENCE_SCOPE_INVALID")
    for key in value:
        if _SECRET_KEY_RE.search(str(key)):
            errors.append("ACTUAL_EVIDENCE_SECRET_FIELD")
    return sorted(set(errors))


def _safe_actual_evidence(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {"status": "INVALID"}
    # Keep only the bounded reference metadata; raw evidence content is not a
    # permitted part of this contract and must not reach a trace or report.
    safe: dict[str, Any] = {}
    for key in sorted(EVIDENCE_FIELDS):
        if key not in value:
            continue
        item = value[key]
        if isinstance(item, str):
            safe[key] = "[REDACTED]" if len(item) > 4096 or _SECRET_VALUE_RE.search(item) else item
        elif key == "scope" and isinstance(item, (list, tuple)):
            safe[key] = [
                "[REDACTED]" if not isinstance(scope_item, str) or len(scope_item) > 512 or _SECRET_VALUE_RE.search(scope_item) else scope_item
                for scope_item in item[:32]
            ]
        else:
            safe[key] = "[REDACTED]"
    return safe


@dataclass(frozen=True)
class EvidenceClaim:
    claim: str
    required_evidence: tuple[str, ...]
    actual_evidence: tuple[dict[str, Any], ...]
    status: str

    def __post_init__(self) -> None:
        if self.status not in EVIDENCE_STATUSES:
            raise ValueError("EVIDENCE_STATUS_INVALID")

    def binding_diagnostics(self) -> list[str]:
        if self.status != "VERIFIED":
            return []
        errors: list[str] = []
        items = list(self.actual_evidence)
        if not items:
            errors.append("ACTUAL_EVIDENCE_REQUIRED")
        for item in items:
            errors.extend(_actual_evidence_errors(item))
        references = {
            str(item.get("evidence_ref") or item.get("source"))
            for item in items
            if isinstance(item, Mapping)
        }
        missing = [str(required) for required in self.required_evidence if str(required) not in references]
        if missing:
            errors.append("REQUIRED_EVIDENCE_UNBOUND:" + ",".join(sorted(missing)))
        return sorted(set(errors))

    def effective_status(self) -> str:
        if self.status != "VERIFIED":
            return self.status
        return "VERIFIED" if not self.binding_diagnostics() else "INCOMPLETE"

    def as_contract(self) -> dict[str, Any]:
        diagnostics = self.binding_diagnostics()
        return {
            "CLAIM": self.claim,
            "REQUIRED_EVIDENCE": list(self.required_evidence),
            "ACTUAL_EVIDENCE": [_safe_actual_evidence(item) for item in self.actual_evidence],
            "STATUS": self.effective_status(),
            "EVIDENCE_BINDING": {
                "STATUS": "BOUND" if not diagnostics else "INCOMPLETE",
                "ERRORS": diagnostics,
            },
        }


def evaluate_done(done_when: Iterable[str], evidence: Iterable[EvidenceClaim]) -> dict[str, Any]:
    required = list(done_when)
    actual = list(evidence)
    statuses = [item.effective_status() for item in actual]
    if any(status == "CONTRADICTED" for status in statuses):
        status = "CONTRADICTED"
    elif required and len(actual) < len(required):
        status = "INCOMPLETE"
    elif any(status == "INCOMPLETE" for status in statuses):
        status = "INCOMPLETE"
    else:
        status = "VERIFIED" if actual and all(item.effective_status() == "VERIFIED" for item in actual) else "NOT_APPLICABLE"
    return {
        "schema": "p2p-independent-done-check/1",
        "done_when": required,
        "evidence": [item.as_contract() for item in actual],
        "status": status,
        "agent_done_is_not_goal_done": True,
        "independent_check": True,
    }


def detect_no_progress(observations: Iterable[dict[str, Any]], *, repeat_threshold: int = 3) -> dict[str, Any]:
    items = list(observations)
    if not items:
        return {"status": "NOT_APPLICABLE", "reason": "NO_OBSERVATIONS"}
    fingerprints = [str(item.get("state_fingerprint", "")) for item in items]
    same_state = len(fingerprints) >= repeat_threshold and len(set(fingerprints[-repeat_threshold:])) == 1
    repeated_failure = len(items) >= repeat_threshold and all(item.get("status") in {"FAILED", "INCOMPLETE", "BLOCKED"} for item in items[-repeat_threshold:])
    if same_state or repeated_failure:
        return {"status": "ESCALATE", "reason": "NO_MATERIAL_STATE_CHANGE", "attempts": len(items), "framework_retry": False}
    return {"status": "PROGRESSING", "attempts": len(items), "framework_retry": False}
