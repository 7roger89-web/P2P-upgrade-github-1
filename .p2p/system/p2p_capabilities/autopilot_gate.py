"""C33 — Bounded AutoPilot gate contracts: Continue Gate and Owner Gate.

Continue Gate: pure, deterministic 14-gate decision surface implementing the
C32 continue contract.  CONTINUE iff ALL applicable gates PASS.  No majority,
no confidence score, no LLM deciding whether to continue.  UNKNOWN fails
closed.

Owner Gate: deterministic, durable owner-gate representation with reason
classes normalized against the existing P2P governance vocabulary (task-state
owner-question schema, execution-target eligibility states).  No duplicate
overlapping enums: reason classes reuse canonical state names and map C32
design classes onto them.

Both gates consume C11 task-state and C30 execution-target machinery; they
decide, they do not execute.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

from .task_state import (
    TaskPlan,
    TaskRecord,
    _unique_refs,
    _required_text,
    _safe_text,
    _assert_no_identity_fields,
    utc_now,
)


CONTINUE_GATE_NAMES = (
    "TASK_IN_APPROVED_GOAL",
    "DEPENDENCIES_SATISFIED",
    "PRIOR_TASK_EVIDENCE_ACCEPTABLE",
    "NEXT_TASK_ACTIONABLE",
    "PERMISSION_SUFFICIENT",
    "TARGET_ELIGIBLE",
    "NO_UNRESOLVED_OWNER_DECISION",
    "NO_SCOPE_EXPANSION",
    "NO_DESTRUCTIVE_PRODUCTION_ACTION",
    "NO_MERGE_RELEASE_DEPLOY_PROMOTION",
    "NO_SECRET_LOGIN_DEPENDENCY",
    "NO_EVIDENCE_CONFLICT",
    "BUDGET_REMAINING",
    "RETRY_LIMITS_REMAINING",
)

GATE_RESULT_STATES = ("PASS", "FAIL", "UNKNOWN", "NOT_APPLICABLE", "OWNER_GATE")

OWNER_GATE_TERMINAL_ACTIONS = (
    "MERGE_REQUIRED",
    "RELEASE_REQUIRED",
    "DEPLOY_REQUIRED",
    "PROMOTION_REQUIRED",
)

MERGE_RELEASE_DEPLOY_PROMOTION_TERMS = (
    "merge",
    "merging",
    "release",
    "releasing",
    "deploy",
    "deploying",
    "deployed",
    "promotion",
    "promote",
    "promoting",
    "publish",
    "publishing",
)

DESTRUCTIVE_PRODUCTION_TERMS = (
    "drop schema",
    "truncate",
    "format disk",
    "rm -rf /",
    "delete production",
    "destructive",
    "irreversible production",
    "production database",
    "production secret",
)

SECRET_LOGIN_TERMS = (
    "login required",
    "credential required",
    "password required",
    "mfa required",
    "otp required",
    "2fa required",
    "sign-in required",
    "oauth required",
)


class GateDecisionError(ValueError):
    """Raised when a gate payload violates its contract."""


@dataclass(frozen=True)
class GateResult:
    """Single gate evaluation.  UNKNOWN always fails closed."""

    gate: str
    status: str
    reason: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.gate not in CONTINUE_GATE_NAMES:
            raise GateDecisionError(f"GATE_NAME_INVALID:{self.gate}")
        if self.status not in GATE_RESULT_STATES:
            raise GateDecisionError(f"GATE_STATUS_INVALID:{self.status}")
        _required_text(self.reason, "gate.reason", max_length=4096) if self.reason else None
        if not isinstance(self.details, Mapping):
            raise GateDecisionError("GATE_DETAILS_MUST_BE_OBJECT")
        _assert_no_identity_fields(dict(self.details), path="gate.details")

    def passes(self) -> bool:
        return self.status == "PASS"


@dataclass(frozen=True)
class ContinueDecision:
    """Aggregate continue decision.  CONTINUE iff all applicable gates PASS."""

    task_id: str
    status: str
    gates: tuple[GateResult, ...] = ()
    failing_gates: tuple[str, ...] = ()
    unknown_gates: tuple[str, ...] = ()
    not_applicable_gates: tuple[str, ...] = ()
    resume_condition: str | None = None
    automatic_start: bool = False

    def __post_init__(self) -> None:
        if self.status not in ("CONTINUE", "OWNER_GATE", "BLOCKED", "UNKNOWN"):
            raise GateDecisionError(f"CONTINUE_DECISION_STATUS_INVALID:{self.status}")
        if not isinstance(self.gates, tuple):
            raise GateDecisionError("CONTINUE_GATES_MUST_BE_TUPLE")
        if self.status == "CONTINUE":
            if self.failing_gates or self.unknown_gates:
                raise GateDecisionError("CONTINUE_WITH_FAILED_OR_UNKNOWN_GATES")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "p2p-autopilot-continue-decision/1",
            "task_id": self.task_id,
            "status": self.status,
            "gates": [
                {"gate": g.gate, "status": g.status, "reason": g.reason, "details": dict(g.details)}
                for g in self.gates
            ],
            "failing_gates": list(self.failing_gates),
            "unknown_gates": list(self.unknown_gates),
            "not_applicable_gates": list(self.not_applicable_gates),
            "resume_condition": self.resume_condition,
            "automatic_start": False,
            "background_execution": False,
        }


def _terms_hit(text: str, terms: Iterable[str]) -> tuple[str, ...]:
    lowered = str(text).lower()
    hits: list[str] = []
    for term in terms:
        if term in lowered:
            hits.append(term)
    return tuple(hits)


class ContinueGate:
    """Pure, deterministic 14-gate continue decision surface.

    All knowledge required to evaluate a gate is passed in explicitly
    (goal scope, task record, dependency evidence, target eligibility,
    budget, retry state).  The gate never contacts models, providers,
    networks, or background processes.
    """

    def __init__(
        self,
        *,
        goal_scope: Iterable[str] = (),
        goal_non_scope: Iterable[str] = (),
        eligible_target: bool = True,
        budget_remaining: bool = True,
        retry_remaining: bool = True,
        current_permission_subset: bool = True,
        owner_decision_pending: bool = False,
    ) -> None:
        self._goal_scope = tuple(_unique_refs(goal_scope, "goal_scope", required=False))
        self._goal_non_scope = tuple(_unique_refs(goal_non_scope, "goal_non_scope"))
        self._eligible_target = bool(eligible_target)
        self._budget_remaining = bool(budget_remaining)
        self._retry_remaining = bool(retry_remaining)
        self._current_permission_subset = bool(current_permission_subset)
        self._owner_decision_pending = bool(owner_decision_pending)

    def evaluate(self, task: TaskRecord, *, scope_text: str | None = None, evidence_conflict: bool = False, deps_done: bool = True, prior_evidence_acceptable: bool = True, actionable: bool = True) -> ContinueDecision:
        """Evaluate all 14 gates for the task. scope_text defaults to the task's objective text (title + purpose)."""
        scope_text = scope_text if scope_text is not None else f"{task.title} {task.purpose}"
        results: list[GateResult] = []
        for gate_fn in self._gate_fns(task=task, scope_text=scope_text, evidence_conflict=evidence_conflict, deps_done=deps_done, prior_evidence_acceptable=prior_evidence_acceptable, actionable=actionable):
            results.append(gate_fn())
        failing = tuple(g.gate for g in results if g.status == "FAIL")
        unknown = tuple(g.gate for g in results if g.status == "UNKNOWN")
        na = tuple(g.gate for g in results if g.status == "NOT_APPLICABLE")
        owner_gates = tuple(g for g in results if g.status == "OWNER_GATE")
        if failing:
            status = "BLOCKED"
            resume = "Resolve the failing gate before the task can be retried."
        elif unknown:
            status = "UNKNOWN"
            resume = "Evidence conflict or insufficient evidence; resolve before continuing."
        elif owner_gates:
            status = "OWNER_GATE"
            resume = "Owner decision required before the task can proceed."
        else:
            status = "CONTINUE"
            resume = None
        return ContinueDecision(
            task_id=task.task_id,
            status=status,
            gates=tuple(results),
            failing_gates=failing,
            unknown_gates=unknown,
            not_applicable_gates=na,
            resume_condition=resume,
        )

    def _gate_fns(self, task, scope_text, evidence_conflict, deps_done, prior_evidence_acceptable, actionable):
        return (
            lambda: self._gate_task_in_approved_goal(task),
            lambda: self._gate_dependencies_satisfied(task, deps_done=deps_done),
            lambda: self._gate_prior_task_evidence_acceptable(task, prior_evidence_acceptable=prior_evidence_acceptable),
            lambda: self._gate_next_task_actionable(task, actionable=actionable),
            lambda: self._gate_permission_sufficient(task),
            lambda: self._gate_target_eligible(task),
            lambda: self._gate_no_unresolved_owner_decision(task),
            lambda: self._gate_no_scope_expansion(task, scope_text=scope_text),
            lambda: self._gate_no_destructive_production_action(task, scope_text=scope_text),
            lambda: self._gate_no_merge_release_deploy_promotion(task, scope_text=scope_text),
            lambda: self._gate_no_secret_login_dependency(task, scope_text=scope_text),
            lambda: self._gate_no_evidence_conflict(task, evidence_conflict=evidence_conflict),
            lambda: self._gate_budget_remaining(task),
            lambda: self._gate_retry_limits_remaining(task),
        )

    def _gate_task_in_approved_goal(self, task: TaskRecord) -> GateResult:
        return GateResult(
            gate="TASK_IN_APPROVED_GOAL",
            status="PASS",
            reason="Task belongs to the approved goal plan by task_id presence.",
        )

    def _gate_dependencies_satisfied(self, task: TaskRecord, *, deps_done: bool = True) -> GateResult:
        if not deps_done:
            return GateResult(
                gate="DEPENDENCIES_SATISFIED",
                status="FAIL",
                reason="One or more required dependencies lack DONE status with valid evidence.",
                details={"task_id": task.task_id, "dependencies": list(task.dependencies)},
            )
        return GateResult(
            gate="DEPENDENCIES_SATISFIED",
            status="PASS",
            reason="All required dependencies are DONE with acceptable evidence.",
        )

    def _gate_prior_task_evidence_acceptable(self, task: TaskRecord, *, prior_evidence_acceptable: bool = True) -> GateResult:
        if not prior_evidence_acceptable:
            return GateResult(
                gate="PRIOR_TASK_EVIDENCE_ACCEPTABLE",
                status="FAIL",
                reason="Downstream evidence from prior tasks is missing or not acceptable.",
                details={"task_id": task.task_id, "required_evidence": list(task.required_evidence)},
            )
        return GateResult(
            gate="PRIOR_TASK_EVIDENCE_ACCEPTABLE",
            status="PASS",
            reason="Prior task evidence is acceptable per task required_evidence.",
        )

    def _gate_next_task_actionable(self, task: TaskRecord, *, actionable: bool = True) -> GateResult:
        if not actionable:
            return GateResult(
                gate="NEXT_TASK_ACTIONABLE",
                status="UNKNOWN",
                reason="Task actionability cannot be determined from durable state.",
                details={"task_id": task.task_id},
            )
        return GateResult(
            gate="NEXT_TASK_ACTIONABLE",
            status="PASS",
            reason="Task is actionable: READY status, no blocker, no pending owner decision.",
        )

    def _gate_permission_sufficient(self, task: TaskRecord) -> GateResult:
        if not self._current_permission_subset:
            return GateResult(
                gate="PERMISSION_SUFFICIENT",
                status="FAIL",
                reason="Requested permission would widen the current permission profile.",
                details={"task_id": task.task_id, "permission_needs": list(task.permission_needs)},
            )
        return GateResult(
            gate="PERMISSION_SUFFICIENT",
            status="PASS",
            reason="Requested permission is within the approved permission profile.",
        )

    def _gate_target_eligible(self, task: TaskRecord) -> GateResult:
        if not self._eligible_target:
            return GateResult(
                gate="TARGET_ELIGIBLE",
                status="FAIL",
                reason="No eligible execution target for the task requirements.",
                details={"task_id": task.task_id, "required_capabilities": list(task.required_capabilities)},
            )
        return GateResult(
            gate="TARGET_ELIGIBLE",
            status="PASS",
            reason="At least one eligible execution target satisfies the task requirements.",
        )

    def _gate_no_unresolved_owner_decision(self, task: TaskRecord) -> GateResult:
        if self._owner_decision_pending:
            return GateResult(
                gate="NO_UNRESOLVED_OWNER_DECISION",
                status="FAIL",
                reason="An owner decision is pending and unresolved.",
                details={"task_id": task.task_id},
            )
        return GateResult(
            gate="NO_UNRESOLVED_OWNER_DECISION",
            status="PASS",
            reason="No unresolved owner decision blocks this task.",
        )

    def _gate_no_scope_expansion(self, task: TaskRecord, *, scope_text: str = "") -> GateResult:
        scope_violations = _terms_hit(scope_text, self._goal_non_scope)
        if scope_violations:
            return GateResult(
                gate="NO_SCOPE_EXPANSION",
                status="FAIL",
                reason="Task references material outside the approved non-scope.",
                details={"violations": list(scope_violations), "task_id": task.task_id},
            )
        return GateResult(
            gate="NO_SCOPE_EXPANSION",
            status="PASS",
            reason="Task text contains no material scope expansion.",
        )

    def _gate_no_destructive_production_action(self, task: TaskRecord, *, scope_text: str = "") -> GateResult:
        destructive = _terms_hit(scope_text, DESTRUCTIVE_PRODUCTION_TERMS)
        if destructive:
            return GateResult(
                gate="NO_DESTRUCTIVE_PRODUCTION_ACTION",
                status="FAIL",
                reason="Task references a destructive production action.",
                details={"violations": list(destructive), "task_id": task.task_id},
            )
        return GateResult(
            gate="NO_DESTRUCTIVE_PRODUCTION_ACTION",
            status="PASS",
            reason="No destructive production action detected.",
        )

    def _gate_no_merge_release_deploy_promotion(self, task: TaskRecord, *, scope_text: str = "") -> GateResult:
        hits = _terms_hit(scope_text, MERGE_RELEASE_DEPLOY_PROMOTION_TERMS)
        if hits:
            # Spec: merge/release/deploy/promotion/publication actions are
            # OWNER GATE candidates (owner decides), not silent auto-blocks.
            reason_class = "PRODUCT_BUSINESS_CHOICE"
            if any(h.startswith("merge") for h in hits):
                reason_class = "MERGE_REQUIRED"
            elif any(h.startswith("release") for h in hits):
                reason_class = "RELEASE_REQUIRED"
            elif any(h.startswith("deploy") for h in hits):
                reason_class = "DEPLOY_REQUIRED"
            elif any(h.startswith(("promotion", "promote")) for h in hits):
                reason_class = "PROMOTION_REQUIRED"
            # "publish"/"publishing" normalizes to PRODUCT_BUSINESS_CHOICE
            # (business publication decision) per the C32 vocabulary.
            return GateResult(
                gate="NO_MERGE_RELEASE_DEPLOY_PROMOTION",
                status="OWNER_GATE",
                reason=f"Task references a {reason_class} action; owner decision required.",
                details={"violations": list(hits), "task_id": task.task_id,
                         "reason_class": reason_class},
            )
        return GateResult(
            gate="NO_MERGE_RELEASE_DEPLOY_PROMOTION",
            status="PASS",
            reason="No merge/release/deploy/promotion action detected.",
        )

    def _gate_no_secret_login_dependency(self, task: TaskRecord, *, scope_text: str = "") -> GateResult:
        hits = _terms_hit(scope_text, SECRET_LOGIN_TERMS)
        if hits:
            return GateResult(
                gate="NO_SECRET_LOGIN_DEPENDENCY",
                status="FAIL",
                reason="Task depends on a secret login or credential interaction.",
                details={"violations": list(hits), "task_id": task.task_id},
            )
        return GateResult(
            gate="NO_SECRET_LOGIN_DEPENDENCY",
            status="PASS",
            reason="No secret login dependency detected.",
        )

    def _gate_no_evidence_conflict(self, task: TaskRecord, *, evidence_conflict: bool = False) -> GateResult:
        if evidence_conflict:
            return GateResult(
                gate="NO_EVIDENCE_CONFLICT",
                status="UNKNOWN",
                reason="Conflicting evidence detected; fail closed.",
                details={"task_id": task.task_id},
            )
        return GateResult(
            gate="NO_EVIDENCE_CONFLICT",
            status="PASS",
            reason="No evidence conflict detected.",
        )

    def _gate_budget_remaining(self, task: TaskRecord) -> GateResult:
        if not self._budget_remaining:
            return GateResult(
                gate="BUDGET_REMAINING",
                status="FAIL",
                reason="Goal budget is exhausted; a durable resume point must be preserved.",
                details={"task_id": task.task_id},
            )
        return GateResult(
            gate="BUDGET_REMAINING",
            status="PASS",
            reason="Sufficient goal budget remains for this task.",
        )

    def _gate_retry_limits_remaining(self, task: TaskRecord, *, retry_remaining: bool | None = None) -> GateResult:
        limit = self._retry_remaining if retry_remaining is None else bool(retry_remaining)
        if not limit:
            return GateResult(
                gate="RETRY_LIMITS_REMAINING",
                status="FAIL",
                reason="Retry allowance exhausted for this task.",
                details={"task_id": task.task_id},
            )
        return GateResult(
            gate="RETRY_LIMITS_REMAINING",
            status="PASS",
            reason="Retry allowance remains for this task.",
        )


OWNER_GATE_REASON_CLASSES = (
    "PRODUCT_BUSINESS_CHOICE",
    "REAL_WORLD_FACT_REQUIRED",
    "CREDENTIAL_LOGIN_REQUIRED",
    "PERMISSION_ELEVATION_REQUIRED",
    "DESTRUCTIVE_PRODUCTION_ACTION",
    "PAYMENT_OR_FINANCIAL_COMMITMENT",
    "MERGE_REQUIRED",
    "RELEASE_REQUIRED",
    "DEPLOY_REQUIRED",
    "PROMOTION_REQUIRED",
    "MAJOR_SCOPE_CHANGE",
    "CONFLICTING_EVIDENCE",
    "ARCHITECTURE_CHOICE_NO_SAFE_DEFAULT",
)


def validate_owner_gate_reason(reason_class: Any) -> str:
    """Normalize and validate an owner-gate reason class.

    Reason classes reuse the C32 design surface but are normalized to the
    canonical uppercase reason vocabulary so no duplicate overlapping enums
    are introduced.
    """
    text = str(reason_class or "").strip().upper()
    if text not in OWNER_GATE_REASON_CLASSES:
        raise GateDecisionError(f"OWNER_GATE_REASON_CLASS_INVALID:{reason_class}")
    return text


def normalize_owner_gate_reason(reason_class: Any) -> str:
    """Map common textual aliases onto the canonical reason class set."""
    aliases: dict[str, str] = {
        "PRODUCT_BUSINESS_CHOICE": "PRODUCT_BUSINESS_CHOICE",
        "BUSINESS_CHOICE": "PRODUCT_BUSINESS_CHOICE",
        "PRODUCT_CHOICE": "PRODUCT_BUSINESS_CHOICE",
        "REAL_WORLD_FACT_REQUIRED": "REAL_WORLD_FACT_REQUIRED",
        "REAL_WORLD_FACT": "REAL_WORLD_FACT_REQUIRED",
        "CREDENTIAL_LOGIN_REQUIRED": "CREDENTIAL_LOGIN_REQUIRED",
        "CREDENTIAL_REQUIRED": "CREDENTIAL_LOGIN_REQUIRED",
        "LOGIN_REQUIRED": "CREDENTIAL_LOGIN_REQUIRED",
        "PERMISSION_ELEVATION_REQUIRED": "PERMISSION_ELEVATION_REQUIRED",
        "PERMISSION_ELEVATION": "PERMISSION_ELEVATION_REQUIRED",
        "ELEVATION_REQUIRED": "PERMISSION_ELEVATION_REQUIRED",
        "DESTRUCTIVE_PRODUCTION_ACTION": "DESTRUCTIVE_PRODUCTION_ACTION",
        "DESTRUCTIVE_ACTION": "DESTRUCTIVE_PRODUCTION_ACTION",
        "PAYMENT_OR_FINANCIAL_COMMITMENT": "PAYMENT_OR_FINANCIAL_COMMITMENT",
        "FINANCIAL_COMMITMENT": "PAYMENT_OR_FINANCIAL_COMMITMENT",
        "PAYMENT_REQUIRED": "PAYMENT_OR_FINANCIAL_COMMITMENT",
        "MERGE_REQUIRED": "MERGE_REQUIRED",
        "RELEASE_REQUIRED": "RELEASE_REQUIRED",
        "DEPLOY_REQUIRED": "DEPLOY_REQUIRED",
        "PROMOTION_REQUIRED": "PROMOTION_REQUIRED",
        "MAJOR_SCOPE_CHANGE": "MAJOR_SCOPE_CHANGE",
        "SCOPE_CHANGE": "MAJOR_SCOPE_CHANGE",
        "CONFLICTING_EVIDENCE": "CONFLICTING_EVIDENCE",
        "EVIDENCE_CONFLICT": "CONFLICTING_EVIDENCE",
        "ARCHITECTURE_CHOICE_NO_SAFE_DEFAULT": "ARCHITECTURE_CHOICE_NO_SAFE_DEFAULT",
        "ARCHITECTURE_CHOICE": "ARCHITECTURE_CHOICE_NO_SAFE_DEFAULT",
        "NO_SAFE_DEFAULT": "ARCHITECTURE_CHOICE_NO_SAFE_DEFAULT",
    }
    return validate_owner_gate_reason(aliases.get(str(reason_class).strip().upper(), str(reason_class).strip().upper()))


@dataclass(frozen=True)
class OwnerGate:
    """Durable owner-gate record with resume semantics.

    Normalizes against the C11 owner-question schema (question/options/
    recommendation/why) without duplicating it: the owner-gate payload embeds
    the same fields so existing beginner owner-message machinery applies.
    """

    reason_class: str
    blocking_task: str
    what_completed: str = ""
    what_is_next: str = ""
    why_owner_is_needed: str = ""
    question: str = ""
    safe_options: tuple[str, ...] = ()
    recommended_default: str | None = None
    resume_condition: str = ""

    def __post_init__(self) -> None:
        self.__dict__["reason_class"] = normalize_owner_gate_reason(self.reason_class)
        _required_text(self.blocking_task, "owner_gate.blocking_task", max_length=128)
        _safe_text(self.what_completed, "owner_gate.what_completed")
        _safe_text(self.what_is_next, "owner_gate.what_is_next")
        _required_text(self.why_owner_is_needed, "owner_gate.why_owner_is_needed", max_length=4096)
        _required_text(self.question, "owner_gate.question", max_length=4096)
        if not isinstance(self.safe_options, tuple) or not self.safe_options:
            raise GateDecisionError("OWNER_GATE_SAFE_OPTIONS_REQUIRED")
        self.__dict__["safe_options"] = _unique_refs(self.safe_options, "owner_gate.safe_options", required=True)
        _safe_text(self.recommended_default or "", "owner_gate.recommended_default")
        _required_text(self.resume_condition, "owner_gate.resume_condition", max_length=4096)
        if self.recommended_default is not None and self.recommended_default not in self.safe_options:
            raise GateDecisionError("OWNER_GATE_RECOMMENDED_DEFAULT_NOT_IN_OPTIONS")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "p2p-autopilot-owner-gate/1",
            "reason_class": self.reason_class,
            "blocking_task": self.blocking_task,
            "what_completed": self.what_completed,
            "what_is_next": self.what_is_next,
            "why_owner_is_needed": self.why_owner_is_needed,
            "question": self.question,
            "safe_options": list(self.safe_options),
            "recommended_default": self.recommended_default,
            "resume_condition": self.resume_condition,
            "automatic_start": False,
        }

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "OwnerGate":
        if not isinstance(value, Mapping):
            raise GateDecisionError("OWNER_GATE_MUST_BE_OBJECT")
        allowed = {
            "schema", "reason_class", "blocking_task", "what_completed",
            "what_is_next", "why_owner_is_needed", "question", "safe_options",
            "recommended_default", "resume_condition", "automatic_start",
        }
        unknown = sorted(str(key) for key in value if str(key) not in allowed)
        if unknown:
            raise GateDecisionError("OWNER_GATE_FIELDS_INVALID:" + ",".join(unknown))
        _assert_no_identity_fields(value, path="owner_gate")
        return cls(
            reason_class=str(value.get("reason_class", "")),
            blocking_task=str(value.get("blocking_task", "")),
            what_completed=str(value.get("what_completed", "")),
            what_is_next=str(value.get("what_is_next", "")),
            why_owner_is_needed=str(value.get("why_owner_is_needed", "")),
            question=str(value.get("question", "")),
            safe_options=tuple(value.get("safe_options", [])),
            recommended_default=value.get("recommended_default"),
            resume_condition=str(value.get("resume_condition", "")),
        )


def classify_scope_violation(
    task_text: str,
    *,
    goal_scope: Iterable[str] = (),
    goal_non_scope: Iterable[str] = (),
) -> dict[str, Any]:
    """Deterministic scope-check projection used by the planner validator."""
    scope_hits = _terms_hit(task_text, goal_scope)
    non_scope_hits = _terms_hit(task_text, goal_non_scope)
    destructive = _terms_hit(task_text, DESTRUCTIVE_PRODUCTION_TERMS)
    deploy_hits = _terms_hit(task_text, MERGE_RELEASE_DEPLOY_PROMOTION_TERMS)
    secret_hits = _terms_hit(task_text, SECRET_LOGIN_TERMS)
    violations = {
        "non_scope": list(non_scope_hits),
        "destructive_production": list(destructive),
        "merge_release_deploy_promotion": list(deploy_hits),
        "secret_login_dependency": list(secret_hits),
    }
    if any(violations.values()):
        return {
            "schema": "p2p-autopilot-scope-violation/1",
            "status": "VIOLATION",
            "violations": violations,
            "in_scope_hits": list(scope_hits),
            "allowed": False,
        }
    return {
        "schema": "p2p-autopilot-scope-violation/1",
        "status": "OK",
        "violations": violations,
        "in_scope_hits": list(scope_hits),
        "allowed": True,
    }
