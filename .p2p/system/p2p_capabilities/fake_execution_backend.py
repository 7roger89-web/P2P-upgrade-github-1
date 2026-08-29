"""FakeDeterministicExecutionBackend for synthetic C33 AutoPilot proofs.

Pure, deterministic, provider-neutral execution simulator consumed by the
AutoPilot core loop through the same normalized result contract a real
C30-based adapter would return. Contains NO provider/vendor branching.

Deterministic failure modes (fixture-driven): PASS / DONE_UNVERIFIED /
VERIFY_FAIL / CRASH_BEFORE_VERIFY / MUTATION_UNKNOWN / SCOPE_VIOLATION /
BUDGET / NO_ELIGIBLE_TARGET / OWNER_GATE_REQUIRED.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping

CONTRACT_SCHEMA = "p2p-autopilot-task-contract/1"
RESULT_SCHEMA = "p2p-autopilot-execution-result/1"

OUTCOME_PASS = "PASS"
OUTCOME_DONE_UNVERIFIED = "DONE_UNVERIFIED"
OUTCOME_VERIFY_FAIL = "VERIFY_FAIL"
OUTCOME_CRASH_BEFORE_VERIFY = "CRASH_BEFORE_VERIFY"
OUTCOME_MUTATION_UNKNOWN = "MUTATION_UNKNOWN"
OUTCOME_SCOPE_VIOLATION = "SCOPE_VIOLATION"
OUTCOME_BUDGET = "BUDGET"
OUTCOME_NO_ELIGIBLE_TARGET = "NO_ELIGIBLE_TARGET"
OUTCOME_OWNER_GATE_REQUIRED = "OWNER_GATE_REQUIRED"
OUTCOME_PERM_BLOCKED = "PERM_BLOCKED"

EXECUTION_OUTCOMES = (
    OUTCOME_PASS, OUTCOME_DONE_UNVERIFIED, OUTCOME_VERIFY_FAIL,
    OUTCOME_CRASH_BEFORE_VERIFY, OUTCOME_MUTATION_UNKNOWN, OUTCOME_SCOPE_VIOLATION,
    OUTCOME_BUDGET, OUTCOME_NO_ELIGIBLE_TARGET, OUTCOME_OWNER_GATE_REQUIRED,
    OUTCOME_PERM_BLOCKED,
)

# Verifier outcome mapping (deterministic): backend outcome -> verifier verdict
OUTCOME_VERIFIER_VERDICT = {
    OUTCOME_PASS: "ACCEPTABLE",
    OUTCOME_DONE_UNVERIFIED: "UNACCEPTABLE",
    OUTCOME_VERIFY_FAIL: "UNACCEPTABLE",
    OUTCOME_CRASH_BEFORE_VERIFY: "UNKNOWN",
    OUTCOME_MUTATION_UNKNOWN: "UNKNOWN",
    OUTCOME_SCOPE_VIOLATION: "UNACCEPTABLE",
    OUTCOME_BUDGET: "UNKNOWN",
    OUTCOME_NO_ELIGIBLE_TARGET: "UNKNOWN",
    OUTCOME_OWNER_GATE_REQUIRED: "UNKNOWN",
    OUTCOME_PERM_BLOCKED: "UNACCEPTABLE",
}

FORBIDDEN_ACTIONS_DEFAULT: tuple[str, ...] = (
    "merge-to-main", "release", "deploy-production", "promote-candidate",
    "drop-database", "rm-recursive-root",
)
ALLOWED_TOOLS_DEFAULT: tuple[str, ...] = ("read", "write", "run-tests", "diff")


def validate_task_contract(contract: Mapping[str, Any]) -> Mapping[str, Any]:
    if not isinstance(contract, Mapping):
        raise ValueError("TASK_CONTRACT_INVALID_TYPE")
    if str(contract.get("schema", "")) != CONTRACT_SCHEMA:
        raise ValueError("TASK_CONTRACT_SCHEMA_INVALID")
    required = ("goal_id", "task_id", "task_objective", "workspace", "allowed_scope",
                "execution_target", "expected_output", "verify_spec")
    missing = [k for k in required if not contract.get(k)]
    if missing:
        raise ValueError("TASK_CONTRACT_FIELDS_MISSING:" + ",".join(missing))
    body = {k: contract[k] for k in contract if k != "schema"}
    body.setdefault("allowed_toolset", tuple(ALLOWED_TOOLS_DEFAULT))
    body.setdefault("permission_profile", "sandboxed-default")
    body.setdefault("input_evidence_pointers", ())
    body.setdefault("required_capabilities", ())
    body.setdefault("execution_claims", ())
    body.setdefault("reasoning_provider_id", "")
    body.setdefault("task_budget", {"execution_attempts": 1, "retry": 0, "verification_attempts": 1})
    body.setdefault("retry_budget", 0)
    body.setdefault("forbidden_actions", tuple(FORBIDDEN_ACTIONS_DEFAULT))
    for field in ("goal_id", "task_id", "task_objective", "workspace", "execution_target"):
        body[field] = str(body[field]).strip()
    body["allowed_scope"] = tuple(body["allowed_scope"])
    body["expected_output"] = tuple(body["expected_output"])
    body["verify_spec"] = tuple(body["verify_spec"])
    body["input_evidence_pointers"] = tuple(body["input_evidence_pointers"])
    body["required_capabilities"] = tuple(
        str(capability).strip() for capability in body["required_capabilities"])
    body["execution_claims"] = tuple(
        str(claim).strip().upper() for claim in body["execution_claims"])
    body["reasoning_provider_id"] = str(body["reasoning_provider_id"] or "").strip()
    body["forbidden_actions"] = tuple(str(a) for a in body["forbidden_actions"])
    return body


class FakeDeterministicExecutionBackend:
    """Fixture-driven backend. Outcome is resolved by outcome_fixtures keyed
    by task_id in registration order (rotating), or OUTCOME_PASS when empty.
    No network, no model, no OS execution, no provider branching.
    """

    def __init__(self) -> None:
        self._fixtures: dict[str, list[str]] = {}
        self._default_outcome: str = OUTCOME_PASS
        self._log: list[Mapping[str, Any]] = []
        self._paused: bool = False

    def set_fixtures(self, fixtures: Mapping[str, Iterable[str]]) -> None:
        """fixtures: task_id -> sequence of outcomes consumed per execute()."""
        self._fixtures = {str(k): list(v) for k, v in fixtures.items()}

    def set_default_outcome(self, outcome: str) -> None:
        if outcome not in EXECUTION_OUTCOMES:
            raise ValueError(f"INVALID_OUTCOME:{outcome}")
        self._default_outcome = outcome

    def pause(self) -> None:
        self._paused = True

    def resume(self) -> None:
        self._paused = False

    def cancel(self, reason: str = "OWNER_CANCEL") -> None:
        self._paused = True
        self._log.append({
            "schema": RESULT_SCHEMA,
            "cancelled": True, "cancel_reason": str(reason),
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        })

    def execute(self, contract: Mapping[str, Any]) -> Mapping[str, Any]:
        contract = validate_task_contract(contract)
        task_id = contract["task_id"]
        if self._paused:
            return {
                "schema": RESULT_SCHEMA, "goal_id": contract["goal_id"], "task_id": task_id,
                "outcome": OUTCOME_MUTATION_UNKNOWN, "verdict_hint": "UNKNOWN",
                "changed_surface": (), "artifacts": (),
                "error": "BACKEND_PAUSED", "recorded_at": datetime.now(timezone.utc).isoformat(),
            }
        fixtures = self._fixtures.get(task_id)
        if fixtures:
            outcome = fixtures.pop(0)
            if outcome not in EXECUTION_OUTCOMES:
                raise ValueError(f"FIXTURE_OUTCOME_INVALID:{outcome}")
        else:
            outcome = self._default_outcome

        # Forbidden actions are rejected at contract layer (backend refuses
        # authority wider than the goal/task contract; composition never widens).
        changed_surface = tuple()
        artifacts = tuple()
        if outcome == OUTCOME_PASS:
            changed_surface = tuple(f"artifact:{contract['workspace']}/task-{task_id}/out" for e in contract["expected_output"])
            artifacts = changed_surface
            # self-claims; verifier remains authoritative
            artifacts = tuple(artifacts)

        now = datetime.now(timezone.utc).isoformat()
        result = {
            "schema": RESULT_SCHEMA,
            "goal_id": contract["goal_id"],
            "task_id": task_id,
            "request_fingerprint": hashlib.sha256(
                json.dumps({"goal": contract["goal_id"], "task": task_id,
                            "objective": contract["task_objective"],
                            "workspace": contract["workspace"]}, sort_keys=True).encode()
            ).hexdigest()[:32],
            "outcome": outcome,
            "verdict_hint": OUTCOME_VERIFIER_VERDICT[outcome],
            "changed_surface": changed_surface,
            "artifacts": artifacts,
            "execution_receipt": {
                "schema": "p2p-autopilot-execution-receipt/1",
                "outcome": outcome,
                "target": contract["execution_target"],
                "workspace": contract["workspace"],
            },
            "owner_gate_required": outcome == OUTCOME_OWNER_GATE_REQUIRED,
            "scope_violated": outcome == OUTCOME_SCOPE_VIOLATION,
            "no_eligible_target": outcome == OUTCOME_NO_ELIGIBLE_TARGET,
            "recorded_at": now,
        }
        self._log.append(result)
        return result

    @property
    def log(self) -> list[Mapping[str, Any]]:
        return list(self._log)

    def reset(self) -> None:
        self._fixtures = {}
        self._log = []
        self._paused = False
