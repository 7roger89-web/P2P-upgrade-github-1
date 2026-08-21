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
from .host_attestation import make_canonical_host_attestation
from .role_receipt import RoleExecutionReceipt, new_role_receipt
from .role_verifier import permission_profile_fingerprint

# P2P-BOUNDED-DOCUMENTATION-WRITE-01: the single canonical bounded write
# primitive. Imported lazily inside dispatch to keep the default READ_ONLY
# path free of mutation dependencies for runtimes that never bind one.
from . import bounded_documentation_write as _bdw

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


def _inspect_callable_kwargs(callable_: Any) -> set[str]:
    """Recover the keyword parameters a bounded-write callable accepts.
    Callables that cannot be inspected receive NO forwarded kwargs
    (fail-closed: the execute path never guesses)."""
    import inspect as _inspect
    try:
        signature = _inspect.signature(callable_)
    except (TypeError, ValueError):
        return set()
    names: set[str] = set()
    for name, param in signature.parameters.items():
        if param.kind in (_inspect.Parameter.KEYWORD_ONLY,
                          _inspect.Parameter.POSITIONAL_OR_KEYWORD):
            names.add(name)
    if any(p.kind == _inspect.Parameter.VAR_KEYWORD
           for p in signature.parameters.values()):
        return names  # **kwargs accepts everything we forward
    return names


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
                 execute_bounded_write=None,
                 # P2P-BOUNDED-DOCUMENTATION-WRITE-01A: the REAL canonical
                 # HostAttestation object for the mutation-ready path.
                 # When present and a bounded mutation contract is live,
                 # it is forwarded to the executor so the primitive's
                 # authority gate (§6 real attestation) is enforced end-
                 # to-end. When None the bounded path stays BLOCKED
                 # (derived identities are never promoted to
                 # mutation-ready authority).
                 execute_bounded_write_host_attestation=None,
                 execute_bounded_write_authority_mode=None,
                 ) -> dict[str, Any]:
        """Dispatch one bounded role contract through the reused backend
        bridge. The explicit adapter MUST already be registered in the
        bridge's registry by an eligibility-validated caller. The bridge
        never selects, ranks, or falls back to another adapter.

        execute_bounded_write_authority_mode: optional canonical
            authority mode (bounded_documentation_write.TEST_ONLY |
            MUTATION_READY) passed to the callback. Default
            MUTATION_READY. Unknown modes BLOCK (fail-closed). An
            execute_bounded_write callable with keyword
            mutation_authority_mode receives it; callables without the
            kwarg receive only the project root and host attestation.
        execute_bounded_write: optional callable(project_root,
        host_attestation=...) -> evidence dict returned by
        bounded_documentation_write.execute_bounded_document_mutation.
        When None (default) the dispatch stays pure READ_ONLY regardless
        of the contract's mutation class."""
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

        # ------------------------------------------------------------------
        # P2P-BOUNDED-DOCUMENTATION-WRITE-01: optional bounded mutation
        # execution. The bridge remains READ_ONLY by default. A bounded
        # documentation mutation is performed ONLY when ALL of these hold:
        #
        # 1. the role contract declares the canonical mutation class
        #    (bounded_documentation_write) AND carries all three material
        #    bindings (authorization id, target fingerprint, pre-surface
        #    fingerprint) — the contract layer enforces this coupling;
        # 2. the permission profile explicitly grants WRITE_BOUNDED —
        #    READ-only profiles can never mutate;
        # 3. the caller supplies an explicit executor callback — the
        #    bridge never decides WHAT to write on its own;
        # 4. the execution environment exposes the project root the
        #    contract is bound to.
        #
        # Every gate above failing BLOCKS with the default READ_ONLY
        # outcome — this is the fail-closed rule the first pilot proved.
        # ------------------------------------------------------------------
        mutation_evidence: dict[str, Any] | None = None
        possible_mutation = False
        receipt_attestation: dict[str, Any] | None = None  # 01A real att block
        mutation_state = ("NO_MUTATION_OBSERVED"
                          if backend_outcome == "SUCCEEDED" else "MUTATION_UNKNOWN")
        quality_evaluator: Any | None = None  # injected project-root -> quality dict
        _mutation_class = str(contract.mutation_class or "").strip()
        _mutation_contract_live = (
            _mutation_class == "bounded_documentation_write"
            and bool(contract.mutation_authorization_id)
            and bool(contract.mutation_target_fingerprint)
            and bool(contract.pre_mutation_surface_fingerprint))
        _write_bounded_granted = "WRITE_BOUNDED" in tuple(
            str(g) for g in contract.permission_profile or ())
        # P2P-BOUNDED-DOCUMENTATION-WRITE-01B: the dispatch authority
        # mode is canonical and fail-closed. A real HostAttestation is
        # required for every MUTATION_READY execution — including
        # isolated, non-production pilots; the requirement is keyed to
        # the mode, never to any environment label. TEST_ONLY evidence
        # can never satisfy a mutation-ready pass.
        _canonical_modes = (
            _bdw.TEST_ONLY_AUTHORITY_MODE,
            _bdw.MUTATION_READY_AUTHORITY_MODE)
        _auth_mode = (str(execute_bounded_write_authority_mode or "")
                      .strip().upper()) or _bdw.MUTATION_READY_AUTHORITY_MODE
        if _auth_mode not in _canonical_modes:
            raise RoleBridgeError("BOUND_MUTATION_AUTHORITY_MODE_INVALID", {
                "mutation_authority_mode": execute_bounded_write_authority_mode,
                "canonical_modes": list(_canonical_modes)})
        if _mutation_contract_live and execute_bounded_write is not None:
            if not _write_bounded_granted:
                raise RoleBridgeError("BOUND_MUTATION_PERMISSION_NOT_GRANTED", {
                    "permission_profile": list(contract.permission_profile)})
            _project_root = str(contract.project_binding or "").strip()
            if not _project_root:
                raise RoleBridgeError("NO_PROJECT_BINDING_FOR_MUTATION", {})
            try:
                _call_kwargs = {
                    "host_attestation": execute_bounded_write_host_attestation,
                    "mutation_authority_mode": _auth_mode,
                }
                _sig = _inspect_callable_kwargs(execute_bounded_write)
                evidence = execute_bounded_write(
                    _project_root,
                    **{k: v for k, v in _call_kwargs.items()
                       if k in _sig})
            except _bdw.BoundedDocWriteError as exc:
                raise RoleBridgeError("BOUND_MUTATION_BLOCKED", {
                    "code": exc.code, "details": exc.details})
            if not isinstance(evidence, dict) or not evidence.get("before_file_hash"):
                raise RoleBridgeError("BOUND_MUTATION_EVIDENCE_MISSING", {})
            if int(evidence.get("changed_bytes", 0)) <= 0:
                raise RoleBridgeError("BOUND_MUTATION_NO_CHANGED_BYTES",
                                      {"changed_bytes": evidence.get("changed_bytes")})
            # FW04 quality evaluation (spec 16): EXECUTION_SUCCESS !=
            # QUALITY_VERIFIED. A quality failure BLOCKS the bounded
            # mutation and forces rollback-required downstream — a
            # successful write is never accepted as proof of quality.
            if quality_evaluator is not None:
                _q = quality_evaluator(_project_root)
                if not isinstance(_q, dict) or _q.get("overall") != "QUALITY_VERIFIED":
                    raise RoleBridgeError("BOUND_MUTATION_QUALITY_NOT_VERIFIED", {
                        "quality": _q})
                mutation_evidence["quality_evaluation"] = dict(_q)
            mutation_evidence = dict(evidence)
            # P2P-BOUNDED-DOCUMENTATION-WRITE-01B: record the canonical
            # authority mode inside the evidence surface so the receipt
            # verifier can bind mode, attestation and execution in one
            # claim (TEST_ONLY evidence is bound and verifiable, never
            # silently promoted to mutation-ready).
            mutation_evidence["mutation_authority_mode"] = _auth_mode
            possible_mutation = True
            mutation_state = "BOUNDED_MUTATION_OBSERVED"
            # P2P-BOUNDED-DOCUMENTATION-WRITE-01A: bind the receipt to a
            # REAL canonical host attestation (Owner amendment 1/§6 and
            # §9 whole-claim verification). The dispatch's role-request
            # fingerprint is the identity domain the attestation binds
            # to (run/dispatch/execution identity chain of this dispatch),
            # so the verifier's identity-binding checks close over the
            # same fingerprint used by the receipt.
            _att = make_canonical_host_attestation(
                adapter_id=adapter_id,
                run_id=str(contract.task_id) or "p2p-unknown",
                dispatch_id=f"p2p-{str(contract.task_id)}",
                execution_contract_digest=role_request_fingerprint,
                project_root=_project_root,
                attested_at=now)
            mutation_evidence["host_attestation_id"] = \
                _att.attestation_fingerprint
            receipt_attestation = _att.to_dict()

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
            mutation_surface=mutation_evidence,
            usage_evidence={"synthetic": True},
            auth_state_after="NO_CREDENTIALS",
            raw_backend_receipt_pointer=f"backend-receipt:{contract.task_id}:{now}",
            possible_mutation=possible_mutation,
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
            mutation_state=mutation_state,
            failure_class="NONE",
            timestamps={"executed_at": now, "finished_at": now, "verified_at": "UNKNOWN"},
            raw_backend_receipt_pointer=backend_result.raw_backend_receipt_pointer or "",
            mutation_evidence=mutation_evidence,
            # 01A whole-claim authority chain: the real attestation block
            # is attached only for the bounded mutation path so the
            # verifier's host-attestation checks are exercised by the
            # same evidence the executor used.
            attestation=receipt_attestation,
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
