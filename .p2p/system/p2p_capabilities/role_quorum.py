"""C35 Canonical role quorum consumption of VERIFIED role receipts.

For the canonical 8/8 gate: eight DISTINCT verified canonical ROLE_IDs,
one receipt per role, current role-spec hash, bound to the task/goal,
independently verified by the role verifier.

One receipt cannot satisfy two roles. Eight backend calls from the same
role do NOT satisfy 8/8. Unverified / stale / wrong-task receipts do not
count.

CANONICAL COUNCIL MEMBERSHIP != CURRENT TASK PARTICIPANTS: adaptive
participation accepts a policy-defined subset for bounded tasks, while
the canonical registry remains eight. The quorum layer never mutates the
canonical registry.
"""
from __future__ import annotations

import json
from typing import Any, Iterable, Mapping

from .agent_role import (
    CANONICAL_ROLE_DENOMINATOR,
    CANONICAL_ROLES,
    OPTIONAL_SPECIALIST_ROLE,
)
from .role_receipt import RoleExecutionReceipt

ROLE_QUORUM_SCHEMA = "p2p-role-quorum-evaluation/1"

QUORUM_DECISIONS = ("COMPLETE", "INCOMPLETE", "UNKNOWN")


class RoleQuorumError(ValueError):
    """Raised only when quorum evaluation cannot proceed safely."""

    def __init__(self, code: str, details: Mapping[str, Any] | None = None):
        self.code = code
        self.details = details or {}
        super().__init__("ROLE_QUORUM_ERROR:" + code)


def evaluate_role_quorum(
    receipts: Iterable[RoleExecutionReceipt],
    *,
    required_roles: Iterable[str] = tuple(CANONICAL_ROLES),
    expected_role_spec_hashes: Mapping[str, str] | None = None,
    expected_goal_id: str | None = None,
    expected_task_id: str | None = None,
    current_spec_hashes: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Deterministic canonical role quorum evaluation.

    - Only receipts whose verifier_result == VERIFIED count.
    - Distinct roles only: the first valid receipt per role counts;
      duplicates (same role, different receipts) are reported as
      duplicates and do NOT fill a missing slot.
    - Fresh role-spec hash: a receipt whose role_spec_hash differs from
      the current canonical hash is stale and does not count.
    - Goal/task binding must match the expected gate context.
    - Canonical membership never changes: required_roles defaults to
      the eight canonical IDs; aesthetica is optional and never
      alters the denominator."""
    required = tuple(str(role) for role in required_roles)
    expected_goal = str(expected_goal_id or "")
    expected_task = str(expected_task_id or "")
    # Aggregate gate: expected_task_id "ALL" matches any task id;
    # each receipt still binds to its own declared task. The canonical
    # 8/8 gate is goal-level, not single-task-level.
    all_tasks_gate = expected_task == "ALL"
    current_hashes = dict(current_spec_hashes or {})
    expected_hashes = dict(expected_role_spec_hashes or {})

    satisfied: dict[str, list[dict[str, Any]]] = {}
    duplicates: list[dict[str, Any]] = []
    disqualified: list[dict[str, Any]] = []
    seen_roles: list[str] = []

    for receipt in receipts:
        role = receipt.role_id
        reasons: list[str] = []
        if receipt.verifier_result != "VERIFIED":
            reasons.append("RECEIPT_NOT_VERIFIED")
        if expected_goal and receipt.goal_id != expected_goal:
            reasons.append("WRONG_GOAL")
        if expected_task and not all_tasks_gate \
                and receipt.task_id != expected_task:
            reasons.append("WRONG_TASK")
        expected_hash = expected_hashes.get(role) or current_hashes.get(role)
        if expected_hash and receipt.role_spec_hash != expected_hash:
            reasons.append("STALE_ROLE_SPEC_HASH")
        # Aggregate gate: one role may not be satisfied twice — a second
        # receipt for the same role (different task) is a duplicate, not
        # an additional slot.
        if role in seen_roles:
            duplicates.append({
                "role_id": role, "task_id": receipt.task_id,
                "receipt": receipt.to_dict(),
            })
            continue
        if role not in required:
            reasons.append("ROLE_NOT_IN_REQUIRED_SET")
        if reasons:
            disqualified.append({
                "role_id": role, "task_id": receipt.task_id,
                "reasons": reasons, "receipt": receipt.to_dict(),
            })
            continue
        seen_roles.append(role)
        satisfied.setdefault(role, []).append({
            "role_id": role, "task_id": receipt.task_id,
            "receipt": receipt.to_dict(),
        })

    missing = sorted(set(required) - set(satisfied))
    decision = "INCOMPLETE" if missing else "COMPLETE"
    if not required:
        decision = "INCOMPLETE"
    # UNKNOWN only when an UNDISQUALIFIED receipt carries an undecidable
    # verification truth for a role slot — a known negative
    # (RECEIPT_NOT_VERIFIED, WRONG_ROLE_ID, ...) never makes the gate
    # UNKNOWN: the negative is a positive fact, not uncertainty. Fail
    # closed means the gate refuses to CLOSE, not that it pretends
    # the truth is unknowable.
    undecided_role_slots = set()
    for receipt in receipts:
        if receipt.verifier_result == "UNKNOWN" and receipt.role_id in required \
                and receipt.role_id not in satisfied:
            disqualified_roles = {dq["role_id"] for dq in disqualified}
            if receipt.role_id not in disqualified_roles:
                undecided_role_slots.add(receipt.role_id)
    if undecided_role_slots:
        decision = "UNKNOWN"

    return {
        "schema": ROLE_QUORUM_SCHEMA,
        "decision": decision,
        "required_roles": list(required),
        "canonical_denominator": CANONICAL_ROLE_DENOMINATOR,
        "satisfied_roles": sorted(satisfied.keys()),
        "satisfied_count": len(satisfied),
        "missing_roles": missing,
        "duplicate_receipts": duplicates,
        "disqualified_receipts": disqualified,
    }


def adaptive_participant_set(
    task_risk_class: str,
    *,
    policy_roles: Mapping[str, tuple[str, ...]] | None = None,
) -> dict[str, Any]:
    """Adaptive participation: canonical council membership != current
    task participants. Policy-level mapping; the canonical registry is
    never mutated. No swarm — participant count stays bounded and
    evidence-driven."""
    policy = dict(policy_roles or {
        "LOW_RISK_DETERMINISTIC": ("p2p_datos",),
        "MATERIAL": ("p2p_datos", "p2p_axiom"),
        "SECURITY": ("p2p_anon", "p2p_datos"),
        "ARCHITECTURE": ("p2p_tecton", "p2p_axiom", "p2p_architecton"),
        "DOMAIN_RISK": ("p2p_vector", "p2p_datos", "p2p_anon"),
        "CANONICAL_GOVERNANCE_GATE": tuple(CANONICAL_ROLES),
    })
    roles = tuple(policy.get(str(task_risk_class).upper(), ("p2p_datos",)))
    invalid = [role for role in roles if role not in CANONICAL_ROLES
               and role != OPTIONAL_SPECIALIST_ROLE]
    if invalid:
        raise RoleQuorumError("PARTICIPANT_NOT_P2P_ROLE", {"roles": invalid})
    return {
        "schema": ROLE_QUORUM_SCHEMA,
        "task_risk_class": str(task_risk_class).upper(),
        "participant_roles": list(roles),
        "canonical_registry_unchanged": True,
        "canonical_denominator": CANONICAL_ROLE_DENOMINATOR,
        "participant_count_bounded": len(roles) <= CANONICAL_ROLE_DENOMINATOR,
    }
