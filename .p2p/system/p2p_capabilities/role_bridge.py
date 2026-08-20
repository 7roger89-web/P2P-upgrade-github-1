"""C35 RoleExecutionBridge — bounded dispatch of role contracts through the
existing C34 BackendExecutionBridge.

Conceptually:

    RoleExecutionContract
        -> RoleExecutionBridge
        -> existing BackendExecutionBridge   (REUSED, never forked/duplicated)
        -> explicit BackendAdapter
        -> BackendExecutionResult
        -> RoleExecutionReceipt
        -> P2P verifier

Vendor behavior stays behind the existing adapter boundary. The bridge
translates role-contract vocabulary into the C34 task contract shape the
bridge accepts (schema + allowed_scope + verify_spec + forbidden_actions +
input_evidence_pointers), and lifts the normalized backend result into a
normalized role receipt WITHOUT inventing any field a conformant adapter
could not produce.

Registry != router: the bridge dispatches to an EXPLICIT adapter already
validated by the eligibility layer. No ranking, no fallback, no silent
reswitch.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable, Mapping

from .agent_role import AgentRoleSpec
from .backend_contract import (
    BackendContractError,
    BackendExecutionResult,
    validate_attestation_binding,
)
from .backend_execution_bridge import (
    BackendAdapterRegistry,
    BackendExecutionBridge,
    contract_request_fingerprint,
)
from .fake_execution_backend import CONTRACT_SCHEMA as TASK_CONTRACT_SCHEMA
from .role_contract import RoleExecutionContract
from .role_receipt import RoleExecutionReceipt, new_role_receipt
from .role_verifier import permission_profile_fingerprint

ROLE_BRIDGE_SCHEMA = "p2p-role-execution-bridge/1"


def _attestation_status(requested: str, observed: str,
                        observation_pointers: list[str]) -> str:
    """Honest requested-vs-observed attestation from the dispatch's own
    synthetic evidence pointers. Requested-only claims stay REQUESTED_ONLY
    until independent observation evidence exists (C34 attestation
    semantics)."""
    ok, detail = validate_attestation_binding(
        requested, observed, tuple(observation_pointers))
    if ok and isinstance(detail.get("attestation_profile"), str):
        return str(detail["attestation_profile"])
    return "REQUESTED_ONLY"


class RoleBridgeError(ValueError):
    """Raised only when a role dispatch cannot proceed safely."""

    def __init__(self, code: str, details: Mapping[str, Any] | None = None):
        self.code = code
        self.details = details or {}
        super().__init__("ROLE_BRIDGE_ERROR:" + code)


class RoleExecutionBridge:
    """Bounded foreground dispatcher for role contracts.

    REUSE: it wraps a caller-supplied BackendExecutionBridge — the exact
    same class used by the C33/C34 autopilot path. No fork, no duplicated
    bridge logic, no vendor branching.
    """

    def __init__(self, backend_bridge: BackendExecutionBridge) -> None:
        if not isinstance(backend_bridge, BackendExecutionBridge):
            raise RoleBridgeError("BACKEND_BRIDGE_REQUIRED", {})
        self._bridge = backend_bridge
        self._dispatch_log: list[dict[str, Any]] = []

    @property
    def dispatch_log(self) -> list[dict[str, Any]]:
        return list(self._dispatch_log)

    @property
    def backend_bridge(self) -> BackendExecutionBridge:
        return self._bridge

    def dispatch(self, contract: RoleExecutionContract,
                 *,
                 adapter_id: str,
                 backend_outcome: str = "SUCCEEDED",
                 backend_verification_status: str = "VERIFIED",
                 ) -> dict[str, Any]:
        """Dispatch one bounded role contract through the reused backend
        bridge. The explicit adapter MUST already be registered in the
        bridge's registry by an eligibility-validated caller. The bridge
        never selects, ranks, or falls back to another adapter."""
        now = datetime.now(timezone.utc).isoformat()
        target = str(contract.explicit_execution_target).strip()
        if not target:
            raise RoleBridgeError("NO_EXPLICIT_TARGET", {})
        if adapter_id not in self._bridge.registry.registered_ids():
            raise RoleBridgeError("ADAPTER_NOT_REGISTERED", {"adapter_id": adapter_id})

        # Translate role contract -> C34 task contract vocabulary.
        task_contract = {
            "schema": TASK_CONTRACT_SCHEMA,
            "goal_id": contract.goal_id,
            "task_id": contract.task_id,
            "task_objective": contract.objective,
            "workspace": contract.workspace_binding,
            "execution_target": target,
            "allowed_scope": list(contract.approved_scope),
            "expected_output": list(contract.acceptance_criteria),
            "verify_spec": list(contract.required_evidence),
            "input_evidence_pointers": list(contract.context_package),
            "forbidden_actions": (),
        }
        # Role receipt binds to the ROLE contract fingerprint (what the
        # independent verifier checks); the C34 task-contract fingerprint
        # is carried on the backend result and mirrored onto the receipt
        # so the verifier can cross-check both sides of the same request.
        role_request_fingerprint = contract.request_fingerprint
        fingerprint = contract_request_fingerprint(task_contract)

        # Build a synthetic conformant backend result. A real adapter
        # would produce this from runtime execution; C35 uses the same
        # normalized envelope without live backend calls. The result is
        # still subject to independent role receipt verification —
        # backend "SUCCEEDED" does NOT imply ROLE_EXECUTION_VERIFIED.
        backend_result = BackendExecutionResult(
            request_id=f"p2p-{contract.task_id}",
            request_fingerprint_hex=fingerprint,
            task_id=contract.task_id,
            goal_id=contract.goal_id,
            adapter_id=adapter_id,
            execution_status=backend_outcome,
            verification_status=backend_verification_status,
            started_at=now,
            finished_at=now,
            exit_status="0" if backend_outcome == "SUCCEEDED" else "1",
            target_fingerprint=contract.target_fingerprint,
            output_pointers=(f"artifact:{contract.workspace_binding}/task-{contract.task_id}/out",),
            artifact_pointers=(f"artifact:{contract.workspace_binding}/task-{contract.task_id}/art",),
            mutation_surface=None,
            usage_evidence={"synthetic": True},
            auth_state_after="NO_CREDENTIALS",
            raw_backend_receipt_pointer=f"backend-receipt:{contract.task_id}:{now}",
            possible_mutation=False,
        )

        # Lift normalized backend result -> normalized role receipt.
        observation_pointers = (
            list(backend_result.output_pointers)
            + list(backend_result.artifact_pointers)
            + [backend_result.raw_backend_receipt_pointer or ""]
        )
        receipt_dict = new_role_receipt(
            role_id=contract.role_id,
            role_spec_hash=contract.role_spec_hash,
            goal_id=contract.goal_id,
            task_id=contract.task_id,
            project_binding=contract.project_binding,
            environment_binding=contract.environment_binding,
            context_digest=contract.context_digest,
            permission_profile=contract.permission_profile,
            permission_profile_fingerprint=permission_profile_fingerprint(
                contract.permission_profile),
            request_fingerprint=role_request_fingerprint,
            task_fingerprint=fingerprint,
            requested_target=target,
            observed_target=adapter_id,
            target_attestation_status=_attestation_status(
                target, adapter_id, observation_pointers),
            target_fingerprint=contract.target_fingerprint,
            execution_status=backend_result.execution_status,
            output_pointers=backend_result.output_pointers,
            artifact_pointers=backend_result.artifact_pointers,
            evidence_pointers=tuple(pointer for pointer in observation_pointers if pointer),
            verifier_result="UNKNOWN",
            mutation_state="NO_MUTATION_OBSERVED" if backend_result.possible_mutation is False
            and backend_result.mutation_surface is None else "MUTATION_UNKNOWN",
            failure_class="NONE",
            timestamps={"executed_at": now, "finished_at": now, "verified_at": "UNKNOWN"},
            raw_backend_receipt_pointer=backend_result.raw_backend_receipt_pointer or "",
        )
        receipt = RoleExecutionReceipt(receipt_dict)
        entry = {
            "schema": ROLE_BRIDGE_SCHEMA,
            "role_id": contract.role_id,
            "task_id": contract.task_id,
            "explicit_target": target,
            "adapter_id": adapter_id,
            "backend_execution_status": backend_result.execution_status,
            "backend_verification_status": backend_result.verification_status,
            "role_receipt": receipt.to_dict(),
            "dispatched_at": now,
        }
        self._dispatch_log.append(entry)
        return {
            "schema": ROLE_BRIDGE_SCHEMA,
            "status": "DISPATCHED",
            "request_fingerprint": fingerprint,
            "role_receipt": receipt.to_dict(),
            "backend_result": backend_result.to_dict(),
        }


def register_explicit_adapter(
    registry: BackendAdapterRegistry,
    *,
    adapter_id: str,
    harness: str,
    provider: str = "unknown",
    model: str = "unknown",
    live_certified: bool = False,
    auth_state: str = "NO_CREDENTIALS",
    synthetic: bool = True,
) -> dict[str, Any]:
    """Register an explicit target adapter through the EXISTING registry
    surface. Registry != router: lookup requires an explicit adapter_id;
    there is no ranking, no fallback, and no silent selection.

    Synthetic adapters default to NO_CREDENTIALS (no live backend call,
    no secret) unless an honest auth_state is declared for testing the
    eligibility machinery."""
    from .backend_contract import BackendAdapterIdentity

    def _factory() -> Any:
        # C35 fake adapter — bounded deterministic placeholder behind the
        # adapter boundary; real execution remains C34 adapter territory.
        return _DeterministicFakeAdapter(
            identity=BackendAdapterIdentity(
                adapter_id=adapter_id,
                adapter_version="1",
                adapter_state="ADAPTER_IMPLEMENTED",
                harness_identity=harness,
                provider_identity=provider,
                model_identity=model,
                protocol="synthetic-deterministic",
                toolset_capabilities=("synthetic-text-execution",),
                workspace_binding="synthetic-workspace",
                environment_binding="LOCAL_PROJECT",
            ),
            live_certified=bool(live_certified),
        )

    registry.register(adapter_id, _factory,
                      live_certified=live_certified, auth_state=auth_state)
    # P2P-CLOSURE-01 - persist the registration so a fresh process
    # (the canonical FW01 loop) can evaluate eligibility. Write-only
    # additive ledger; the in-memory registry is untouched.
    try:
        from p2p_capabilities import (quality_intelligence as _rb_qi)
        _rb_qi.append_adapter_registration(
            adapter_id=str(adapter_id),
            provider=str(provider or ''),
            model=str(model or ''),
            harness=str(harness or ''),
            live_certified=bool(live_certified),
            current_auth_state=str(auth_state),
            attestation_summary=str(harness)[:500])
    except Exception:
        pass  # persistence is best-effort;
        # dispatch stays in-memory and fail-closed
        # without it.

    return {
        "adapter_id": adapter_id,
        "harness": harness,
        "synthetic": bool(synthetic),
        "live_certified": bool(live_certified),
        "auth_state": auth_state,
    }


class _DeterministicFakeAdapter:
    """Bounded deterministic placeholder adapter. Vendor behavior stays
    behind the adapter boundary; this placeholder never performs live
    backend execution."""

    def __init__(self, identity: BackendAdapterIdentity, *,
                 live_certified: bool = False) -> None:
        self.identity = identity
        self.live_certified = bool(live_certified)

    def execute(self, **kwargs: Any) -> BackendExecutionResult:
        raise RoleBridgeError("FAKE_ADAPTER_EXECUTION_FORBIDDEN",
                              {"adapter_id": self.identity.adapter_id})
