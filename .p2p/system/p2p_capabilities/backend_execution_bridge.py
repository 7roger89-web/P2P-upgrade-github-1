"""C34 BackendExecutionBridge: provider-neutral bridge between the C33
AutoPilot core (which calls backend.execute(contract)) and any C34
backend-contract adapter (hermes-cli, manus-api, or a future registered
adapter).

This module is intentionally NOT vendor-specific: it selects the target
adapter exclusively through the adapter registry (explicit target profile),
never through provider heuristics, never through silent fallback, and never
through routing logic. Adding a new adapter requires registering its factory
in a caller-supplied registry; nothing in the AutoPilot core changes.

Key invariants (mirror the contract):

    - Adapter permission <= task permission <= Goal-approved permission.
    - Request fingerprint is computed on the P2P contract; the backend
      result must bind to goal_id/task_id/fingerprint and the core rejects
      any receipt that binds elsewhere.
    - Transcripts are evidence-only pointers; the core consumes only the
      normalized BackendExecutionResult fields.
    - UNKNOWN error classes fail closed (verdict UNKNOWN -> never ACCEPT).
"""

from __future__ import annotations

import hashlib
import json
import time
from typing import Callable, Mapping

from typing import Any

from .backend_contract import (
    ADAPTER_STATES,
    BackendContractError,
    BackendExecutionResult,
)
from .fake_execution_backend import (
    OUTCOME_CRASH_BEFORE_VERIFY, OUTCOME_MUTATION_UNKNOWN, OUTCOME_PASS,
    OUTCOME_VERIFY_FAIL, validate_task_contract,
)

# Normalized failure vocabulary (C34 Phase 4, canonical P2P classes).
ERROR_AUTH_REQUIRED = "AUTH_REQUIRED"
ERROR_AUTH_INVALID = "AUTH_INVALID"
ERROR_RATE_LIMIT = "RATE_LIMIT"
ERROR_UNAVAILABLE = "UNAVAILABLE"
ERROR_TIMEOUT = "TIMEOUT"
ERROR_PERMISSION_DENIED = "PERMISSION_DENIED"
ERROR_CONTRACT_REJECTED = "CONTRACT_REJECTED"
ERROR_EXECUTION_FAILED = "EXECUTION_FAILED"
ERROR_INTERRUPTED = "INTERRUPTED"
ERROR_UNKNOWN = "UNKNOWN"

CANONICAL_ERROR_CLASSES = (
    ERROR_AUTH_REQUIRED, ERROR_AUTH_INVALID, ERROR_RATE_LIMIT, ERROR_UNAVAILABLE,
    ERROR_TIMEOUT, ERROR_PERMISSION_DENIED, ERROR_CONTRACT_REJECTED,
    ERROR_EXECUTION_FAILED, ERROR_INTERRUPTED, ERROR_UNKNOWN,
)

# Adapter registration states — reuse the contract vocabulary so the
# bridge and the contract share one honest registry vocabulary.
ADAPTER_ARCHITECTURALLY_COMPATIBLE, ADAPTER_IMPLEMENTED, ADAPTER_TESTED, \
    ADAPTER_LIVE_CERTIFIED, ADAPTER_CURRENTLY_ELIGIBLE = ADAPTER_STATES

AdapterFactory = Callable[[], Any]


def contract_request_fingerprint(contract: Mapping[str, Any]) -> str:
    """Deterministic request fingerprint reusing C22/C30 semantics."""
    payload = json.dumps({
        "goal": str(contract.get("goal_id", "")),
        "task": str(contract.get("task_id", "")),
        "objective": str(contract.get("task_objective", "")),
        "workspace": str(contract.get("workspace", "")),
        "target": str(contract.get("execution_target", "")),
        "required_capabilities": tuple(
            str(item) for item in (contract.get("required_capabilities") or ())),
        "execution_claims": tuple(
            str(item).strip().upper()
            for item in (contract.get("execution_claims") or ())),
        "reasoning_provider_id": str(
            contract.get("reasoning_provider_id") or ""),
    }, sort_keys=True).encode()
    return hashlib.sha256(payload).hexdigest()


def canonical_error_class_for(error_class: str | None) -> str:
    """Map adapter-reported class to canonical P2P class; UNKNOWN fails
    closed."""
    if not error_class:
        return ERROR_UNKNOWN
    text = str(error_class).strip()
    if text == "AUTH_REQUIRED":
        return ERROR_AUTH_REQUIRED
    if text == "AUTH_INVALID":
        return ERROR_AUTH_INVALID
    if text == "RATE_LIMIT":
        return ERROR_RATE_LIMIT
    if text == "TIMEOUT":
        return ERROR_TIMEOUT
    if text == "PERMISSION_DENIED":
        return ERROR_PERMISSION_DENIED
    if text == "CONTRACT_REJECTED":
        return ERROR_CONTRACT_REJECTED
    if text == "EXECUTION_FAILED":
        return ERROR_EXECUTION_FAILED
    if text == "INTERRUPTED":
        return ERROR_INTERRUPTED
    return ERROR_UNKNOWN


class BackendAdapterRegistry:
    """Explicit registry of adapter factories. Registry != router: lookup
    requires an explicit adapter_id; there is no ranking, no fallback, and
    no cost/quality selection."""

    def __init__(self) -> None:
        self._factories: dict[str, AdapterFactory] = {}
        self._live_certified: dict[str, bool] = {}
        self._auth_state: dict[str, str] = {}

    def register(self, adapter_id: str, factory: AdapterFactory,
                 *, live_certified: bool = False, auth_state: str = "UNKNOWN") -> None:
        self._factories[str(adapter_id)] = factory
        self._live_certified[str(adapter_id)] = bool(live_certified)
        self._auth_state[str(adapter_id)] = str(auth_state)

    def resolve(self, adapter_id: str) -> BackendAdapter:
        factory = self._factories.get(str(adapter_id))
        if factory is None:
            raise BackendContractError(
                f"ADAPTER_NOT_REGISTERED:{adapter_id}")
        return factory()

    def registered_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._factories))

    def summary(self) -> list[dict[str, Any]]:
        return [
            {"adapter_id": aid,
             "live_certified": bool(self._live_certified.get(aid)),
             "auth_state": str(self._auth_state.get(aid, "UNKNOWN"))}
            for aid in self.registered_ids()
        ]


class BackendExecutionBridge:
    """Bridge that satisfies the C33 core's backend.execute(contract) duck
    interface using a C34 backend adapter resolved by explicit target
    profile. The AutoPilot core carries NO vendor branching."""

    def __init__(self, registry: BackendAdapterRegistry,
                 target_profile: Mapping[str, Any]) -> None:
        self.registry = registry
        self.target_profile = dict(target_profile)
        self._adapter_id = str(target_profile.get("adapter_id", ""))
        if not self._adapter_id:
            raise BackendContractError("NO_TARGET_ADAPTER")

    @property
    def adapter_id(self) -> str:
        return self._adapter_id

    def execute(self, contract: Mapping[str, Any]) -> Mapping[str, Any]:
        contract = validate_task_contract(contract)
        fingerprint = contract_request_fingerprint(contract)
        task_id = str(contract["task_id"])
        goal_id = str(contract["goal_id"])
        started = time.time()
        try:
            adapter = self.registry.resolve(self._adapter_id)
        except BackendContractError as exc:
            return self._normalized_failure(
                contract, fingerprint, error_class=ERROR_CONTRACT_REJECTED,
                detail=f"ADAPTER_SELECTION:{exc}")
        try:
            profile = dict(self.target_profile)
            if "adapter_id" in profile:
                del profile["adapter_id"]
            result = adapter.execute(
                request_id=f"p2p-{task_id}",
                request_fingerprint=fingerprint,
                task_id=task_id,
                goal_id=goal_id,
                prompt=str(contract.get("task_objective", "")),
                max_turns=int(profile.get("max_turns", 25)),
                timeout_seconds=int(profile.get("timeout_seconds", 900)),
                evidence_dir=str(profile.get("evidence_dir") or ""),
                **{k: v for k, v in profile.items()
                   if k in ("provider", "model", "agent_profile", "title",
                            "toolsets", "workdir", "api_key", "workspace")},
            )
        except BackendContractError as exc:
            return self._normalized_failure(
                contract, fingerprint,
                error_class=self._map_adapter_contract_error(exc),
                detail=f"BRIDGE_REJECTED:{exc}")
        return self._normalize_receipt(contract, fingerprint, result, started)

    def _normalize_receipt(self, contract: Mapping[str, Any],
                           fingerprint: str,
                           result: BackendExecutionResult,
                           started: float) -> Mapping[str, Any]:
        now = lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        # Bind check: receipt must reference THIS goal/task/fingerprint.
        bound = (
            str(result.request_id).endswith(str(contract["task_id"]))
            and str(result.task_id) == str(contract["task_id"])
            and str(result.goal_id) == str(contract["goal_id"])
            and result.request_fingerprint == fingerprint
        )
        # Fail-closed rule applies ONLY when the result is itself UNKNOWN
        # (status or class); a SUCCEEDED result with no error class is NOT
        # UNKNOWN — its verification is done P2P-side on output evidence.
        error_class = canonical_error_class_for(result.error_class)
        fail_closed = result.execution_status == "UNKNOWN"
        if fail_closed and not result.error_class:
            error_class = ERROR_UNKNOWN
        verdict = self._verdict_for(result, fail_closed)
        changed_surface = tuple()
        artifacts = ()
        if result.execution_status == "SUCCEEDED":
            artifacts = tuple(result.artifact_pointers)
        outcome = self._outcome_for(result, fail_closed, verdict)
        return {
            "schema": "p2p-autopilot-execution-result/1",
            "goal_id": contract["goal_id"],
            "task_id": contract["task_id"],
            "request_fingerprint": fingerprint,
            "outcome": outcome,
            "verdict_hint": verdict,
            "changed_surface": changed_surface,
            "artifacts": artifacts,
            "error_class": error_class,
            "execution_status": result.execution_status,
            "auth_state_after": result.auth_state_after or "UNKNOWN",
            "usage_evidence": dict(result.usage_evidence),
            "evidence_pointers": tuple(result.artifact_pointers),
            "execution_evidence_pointers": tuple(
                result.execution_evidence_pointers),
            "required_capabilities": tuple(
                contract.get("required_capabilities") or ()),
            "execution_claims": tuple(contract.get("execution_claims") or ()),
            "target_fingerprint": result.target_fingerprint,
            "raw_backend_receipt_pointer": result.raw_backend_receipt_pointer,
            "bound_to_contract": bound,
            "fail_closed": fail_closed,
            "execution_receipt": {
                "schema": "p2p-backend-execution-result/1",
                "adapter_id": result.adapter_id,
                "request_id": result.request_id,
                "started_at": result.started_at,
                "finished_at": result.finished_at,
                "exit_status": result.exit_status,
                "target_fingerprint": result.target_fingerprint,
                "execution_evidence_pointers": tuple(
                    result.execution_evidence_pointers),
                "possible_mutation": bool(result.possible_mutation),
            },
            "duration_seconds": time.time() - started,
            "recorded_at": now(),
        }

    def _verdict_for(self, result: BackendExecutionResult,
                     fail_closed: bool) -> str:
        if fail_closed:
            return "UNKNOWN"
        if result.execution_status == "SUCCEEDED":
            # Backend self-report is acceptable input; the P2P verifier
            # still decides acceptance on output evidence.
            return "ACCEPTABLE"
        return "UNACCEPTABLE"

    def _outcome_for(self, result: BackendExecutionResult, fail_closed: bool,
                     verdict: str) -> str:
        if fail_closed:
            return OUTCOME_MUTATION_UNKNOWN
        if result.execution_status == "SUCCEEDED" and verdict == "ACCEPTABLE":
            return OUTCOME_PASS
        if result.execution_status == "FAILED":
            return OUTCOME_VERIFY_FAIL
        if result.execution_status == "UNKNOWN":
            return OUTCOME_CRASH_BEFORE_VERIFY
        return OUTCOME_MUTATION_UNKNOWN

    def _normalized_failure(self, contract: Mapping[str, Any],
                            fingerprint: str, *, error_class: str,
                            detail: str) -> Mapping[str, Any]:
        now = lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        return {
            "schema": "p2p-autopilot-execution-result/1",
            "goal_id": contract["goal_id"],
            "task_id": contract["task_id"],
            "request_fingerprint": fingerprint,
            "outcome": OUTCOME_MUTATION_UNKNOWN,
            "verdict_hint": "UNKNOWN",
            "changed_surface": (),
            "artifacts": (),
            "error_class": error_class,
            "execution_status": "UNKNOWN",
            "auth_state_after": "UNKNOWN",
            "usage_evidence": {},
            "evidence_pointers": (),
            "execution_evidence_pointers": (),
            "required_capabilities": tuple(
                contract.get("required_capabilities") or ()),
            "execution_claims": tuple(contract.get("execution_claims") or ()),
            "target_fingerprint": None,
            "raw_backend_receipt_pointer": None,
            "bound_to_contract": False,
            "fail_closed": True,
            "execution_receipt": {
                "schema": "p2p-backend-execution-result/1",
                "adapter_id": self._adapter_id,
                "request_id": f"p2p-{contract['task_id']}",
                "started_at": "",
                "finished_at": "",
                "exit_status": "NOT_RUN",
                "target_fingerprint": None,
                "execution_evidence_pointers": (),
                "possible_mutation": False,
            },
            "duration_seconds": 0.0,
            "recorded_at": now(),
            "detail": detail,
        }

    @staticmethod
    def _map_adapter_contract_error(exc: BackendContractError) -> str:
        code = str(exc).strip()
        if "AUTH" in code.upper():
            return ERROR_AUTH_REQUIRED
        if "PERMISSION" in code.upper() or "SCOPE" in code.upper():
            return ERROR_PERMISSION_DENIED
        if "TIMEOUT" in code.upper():
            return ERROR_TIMEOUT
        if "PROMPT" in code.upper() or "RANGE" in code.upper() or "TYPE" in code.upper():
            return ERROR_CONTRACT_REJECTED
        return ERROR_CONTRACT_REJECTED


def state_family_identifier_for_adapter(adapter_id: str) -> str:
    """Deterministic state-family id for a registered adapter (P0-B /
    collision prevention)."""
    return hashlib.sha256(adapter_id.encode()).hexdigest()[:16]
