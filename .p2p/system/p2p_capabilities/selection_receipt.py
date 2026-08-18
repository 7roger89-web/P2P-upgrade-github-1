"""C37 SelectionReceipt — the durable, inspectable, reason-only record of a
selection decision.

Minimum durable fields (spec-mandated):
  SELECTION_REQUEST_ID, GOAL_ID, TASK_ID, ROLE_ID,
  CANDIDATES_CONSIDERED, CANDIDATES_EXCLUDED, EXCLUSION_REASONS,
  SELECTED_TARGET, SELECTED_MODEL, SELECTED_REASONING_EFFORT,
  QUALITY_EVIDENCE_POINTERS, EFFICIENCY_EVIDENCE_POINTERS,
  CERTIFICATION_POINTERS, AUTH_STATE, PERMISSION_PROFILE,
  POLICY_VERSION, POLICY_FINGERPRINT, DECISION_TRACE_POINTER,
  SELECTION_TIMESTAMP / sequence.

The receipt binds to exactly one (goal, task, role) triple. A receipt
issued for a different triple is REJECTED — never silently accepted
(scenario U). A BLOCKED outcome (NO_ELIGIBLE_TARGET) has
SELECTED_TARGET=UNKNOWN and a reason-only WHY text; there is no hidden
chain-of-thought and no silent fallback embedded anywhere.

Provider-neutral: vendor families travel as DATA (a string field), never
as code branches. Fingerprint is computed over the full record contents
excluding mutable fields (timestamp, sequence) so the policy version and
decision inputs determine the identity (scenario V, O).
"""

from __future__ import annotations

import hashlib
import json
import time
from typing import Any, Iterable, Mapping, Sequence

from .selection_request import UNKNOWN
from .selection_target import SelectionTargetError

RECEIPT_SCHEMA = "p2p-selection-receipt-c37/1"
POLICY_VERSION = "p2p-selection-policy-c37/1"

BLOCKED = "BLOCKED"
SELECTED = "SELECTED"
RECEIPT_OUTCOMES = (BLOCKED, SELECTED)


class SelectionReceiptError(SelectionTargetError):
    pass


def _render_number(value: Any) -> Any:
    if value is None:
        return UNKNOWN
    if isinstance(value, float) and value != value:
        return UNKNOWN
    return value


class SelectionReceipt:
    __slots__ = (
        "_data",
    )

    def __init__(
        self,
        *,
        selection_request_id: str,
        goal_id: str,
        task_id: str,
        role_id: str,
        candidates_considered: Sequence[str] = (),
        candidates_excluded: Sequence[str] = (),
        exclusion_reasons: Sequence[str] = (),
        selected_target: str = UNKNOWN,
        selected_model: str = UNKNOWN,
        selected_reasoning_effort: str = UNKNOWN,
        quality_evidence_pointers: Sequence[str] = (),
        efficiency_evidence_pointers: Sequence[str] = (),
        certification_pointers: Sequence[str] = (),
        auth_state: str = UNKNOWN,
        permission_profile: Sequence[str] = (),
        decision_trace_pointer: str | None = None,
        outcome: str = SELECTED,
        selection_timestamp: float | None = None,
        sequence: int = 1,
        policy_fingerprint_extra: Mapping[str, Any] | None = None,
    ) -> None:
        if not selection_request_id:
            raise SelectionReceiptError("SELECTION_REQUEST_ID_REQUIRED")
        if not goal_id:
            raise SelectionReceiptError("GOAL_ID_REQUIRED")
        if not task_id:
            raise SelectionReceiptError("TASK_ID_REQUIRED")
        if not role_id:
            raise SelectionReceiptError("ROLE_ID_REQUIRED")
        if outcome not in RECEIPT_OUTCOMES:
            raise SelectionReceiptError(f"OUTCOME_INVALID: {outcome}")
        if outcome == SELECTED:
            if selected_target in ("", UNKNOWN, None):
                raise SelectionReceiptError(
                    "SELECTED_OUTCOME_REQUIRES_SELECTED_TARGET")
        unknowns = {"", UNKNOWN, None}
        if selected_model in unknowns and outcome == SELECTED:
            pass  # model binding optional for non-model targets
        self._data = {
            "schema": RECEIPT_SCHEMA,
            "policy_version": POLICY_VERSION,
            "selection_request_id": selection_request_id,
            "goal_id": goal_id,
            "task_id": task_id,
            "role_id": role_id,
            "candidates_considered": list(candidates_considered),
            "candidates_excluded": list(candidates_excluded),
            "exclusion_reasons": list(exclusion_reasons),
            "selected_target": selected_target,
            "selected_model": selected_model,
            "selected_reasoning_effort": selected_reasoning_effort,
            "quality_evidence_pointers": list(quality_evidence_pointers),
            "efficiency_evidence_pointers": list(efficiency_evidence_pointers),
            "certification_pointers": list(certification_pointers),
            "auth_state": auth_state,
            "permission_profile": list(permission_profile),
            "policy_fingerprint_extra": {} if policy_fingerprint_extra is None
            else {str(k): v for k, v in policy_fingerprint_extra.items()},
            "decision_trace_pointer": decision_trace_pointer or "",
            "outcome": outcome,
            "sequence": int(sequence),
            "selection_timestamp": selection_timestamp
            if selection_timestamp is not None else time.time(),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "SelectionReceipt":
        p = dict(payload)
        extra = p.pop("policy_fingerprint_extra", None) or {}
        return cls(selection_request_id=p["selection_request_id"],
                   goal_id=p["goal_id"], task_id=p["task_id"],
                   role_id=p["role_id"],
                   candidates_considered=p.get("candidates_considered", ()),
                   candidates_excluded=p.get("candidates_excluded", ()),
                   exclusion_reasons=p.get("exclusion_reasons", ()),
                   selected_target=p.get("selected_target", UNKNOWN),
                   selected_model=p.get("selected_model", UNKNOWN),
                   selected_reasoning_effort=p.get(
                       "selected_reasoning_effort", UNKNOWN),
                   quality_evidence_pointers=p.get(
                       "quality_evidence_pointers", ()),
                   efficiency_evidence_pointers=p.get(
                       "efficiency_evidence_pointers", ()),
                   certification_pointers=p.get("certification_pointers", ()),
                   auth_state=p.get("auth_state", UNKNOWN),
                   permission_profile=p.get("permission_profile", ()),
                   decision_trace_pointer=p.get("decision_trace_pointer"),
                   outcome=p.get("outcome", SELECTED),
                   selection_timestamp=p.get("selection_timestamp"),
                   sequence=p.get("sequence", 1),
                   policy_fingerprint_extra=extra)

    def to_dict(self) -> dict[str, Any]:
        return dict(self._data)

    @property
    def policy_fingerprint(self) -> str:
        """Deterministic policy+decision identity. Excludes mutable
        timestamp/sequence so the same decision inputs always yield the
        same fingerprint (scenario O)."""
        d = {k: v for k, v in self._data.items()
             if k not in ("selection_timestamp", "sequence", "schema",
                          "policy_version")}
        if d.get("policy_fingerprint_extra") is None:
            d["policy_fingerprint_extra"] = {}
        return "sel-fp-" + hashlib.sha256(
            json.dumps(d, sort_keys=True, default=str)
            .encode()).hexdigest()

    def binding_matches(self, goal_id: str, task_id: str,
                        role_id: str) -> bool:
        return (self._data["goal_id"] == goal_id
                and self._data["task_id"] == task_id
                and self._data["role_id"] == role_id)

    def validate_binding(self, goal_id: str, task_id: str,
                         role_id: str) -> None:
        """Scenario U: a receipt bound to a wrong (goal, task, role) is
        REJECTED. Never silently accepted for other work."""
        if not self.binding_matches(goal_id, task_id, role_id):
            raise SelectionReceiptError(
                f"RECEIPT_BINDING_REJECTED: receipt bound to "
                f"goal={self._data['goal_id']} task={self._data['task_id']} "
                f"role={self._data['role_id']} does not match "
                f"goal={goal_id} task={task_id} role={role_id}")

    @property
    def selected_target(self) -> str:
        return self._data["selected_target"]

    @property
    def selected_model(self) -> str:
        return self._data["selected_model"]

    @property
    def selected_reasoning_effort(self) -> str:
        return self._data["selected_reasoning_effort"]

    @property
    def outcome(self) -> str:
        return self._data["outcome"]

    def to_evidence_text(self) -> str:
        """Beginner-first: a plain, evidence-only explanation of WHY. No
        vendor names, no hidden reasoning — every claim references the
        recorded reason constants and evidence pointers."""
        lines = [f"Selection outcome: {self.outcome}"]
        if self.outcome == SELECTED:
            lines.append(f"Selected target: {self.selected_target}")
            if self.selected_model not in ("", UNKNOWN):
                lines.append(f"Selected model: {self.selected_model}")
            if self.selected_reasoning_effort not in ("", UNKNOWN):
                lines.append(f"Selected reasoning effort: "
                             f"{self.selected_reasoning_effort}")
        else:
            lines.append("No eligible target; selection honestly BLOCKED.")
        for reason in self._data["exclusion_reasons"]:
            lines.append(f"Exclusion reason: {reason}")
        for ptr in self._data["quality_evidence_pointers"]:
            lines.append(f"Quality evidence: {ptr}")
        for ptr in self._data["efficiency_evidence_pointers"]:
            lines.append(f"Efficiency evidence: {ptr}")
        for ptr in self._data["certification_pointers"]:
            lines.append(f"Certification evidence: {ptr}")
        return " | ".join(lines)


def build_selection_receipt(request_id: str, goal_id: str, task_id: str,
                            role_id: str,
                            **kwargs: Any) -> SelectionReceipt:
    """Canonical factory; selection policies MUST construct through here."""
    return SelectionReceipt(selection_request_id=request_id,
                            goal_id=goal_id, task_id=task_id,
                            role_id=role_id, **kwargs)


__all__ = [
    "RECEIPT_SCHEMA",
    "POLICY_VERSION",
    "BLOCKED",
    "SELECTED",
    "RECEIPT_OUTCOMES",
    "SelectionReceipt",
    "SelectionReceiptError",
    "build_selection_receipt",
]
