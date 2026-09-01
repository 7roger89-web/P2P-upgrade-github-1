"""Bounded adapter for the pinned Impeccable design-quality capability.

This module is an adapter over the EXISTING P2P capability registry, router,
vendor-skill machinery (``p2p_capabilities.vendor_skill``) and portable
execution-binding contract (``p2p_capabilities.host_executor``). It deliberately
is not a second router, orchestrator, design system, skill loader, permission
system, authority plane, token service, scheduler or daemon, and it holds no
implementation authority: it can observe and report design-quality problems,
never rewrite a project surface.

Staged law enforced here:

    AVAILABLE != LOADED != AUTHORIZED != EXECUTED

``availability`` reads registry metadata only.

``authorize`` does NOT grant permission. Permission comes from the existing P2P
control plane: the durable task state store (``p2p_capabilities.task_state``)
and its C11 preflight (``evaluate_task_preflight``). An executable grant is
issued only when an active task in that store declares this capability and the
READ permission need and its preflight evaluates to ``PASS``. On top of that
verified permission, ``authorize`` mints a ``PortableExecutionRequest`` which is
used strictly as an IDENTITY/BINDING record (capability, action, registry and
manifest identity, pinned vendor snapshot, task and preflight binding) — the
binding contract is never the permission authority.

``deterministic_check`` fails closed unless the grant was minted here, the
permission authority still holds, and every binding still validates against
freshly recomputed state. The final manifest/snapshot/binding/permission
revalidation happens immediately before ``subprocess.run`` with no filesystem or
preflight work in between. A hand-built ``{"authorized": true}`` mapping, or any
caller-minted binding without an existing P2P permission decision, cannot
execute anything.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, Sequence

from .host_executor import (
    HostExecutorContractError,
    PortableExecutionRequest,
    validate_binding,
)
from .model import load_registry
from .task_state import (
    TaskControlPlaneError,
    TaskStateError,
    TaskStateStore,
    evaluate_task_preflight,
)
from .vendor_skill import (
    is_vendor_skill,
    snapshot_tree_sha256,
    vendor_readiness_snapshot,
    vendor_skill_metadata,
)

CAPABILITY_ID = "ui.design_quality"
AVAILABILITY_SCHEMA = "p2p-impeccable-availability/1"
AUTHORIZATION_SCHEMA = "p2p-impeccable-authorization/3"
CHECK_SCHEMA = "p2p-impeccable-deterministic-check/1"
RUNNER_RELATIVE = ".p2p/system/p2p_capabilities/impeccable_detector_runner.mjs"

#: Design-quality actions projected from the pinned upstream command surface.
#: Only ``deterministic_check`` is executable host code; the rest are advisory
#: review actions carried by the on-demand vendor reference text.
PROJECTED_ACTIONS = (
    "ui.design_quality.critique",
    "ui.design_quality.polish",
    "ui.design_quality.bolder",
    "ui.design_quality.quieter",
    "ui.design_quality.layout",
    "ui.design_quality.typeset",
    "ui.design_quality.deterministic_check",
)
EXECUTABLE_ACTIONS = ("ui.design_quality.deterministic_check",)

#: The single permission this capability ever needs. It is read-only by
#: construction: the detector never writes to a project surface.
REQUIRED_PERMISSION = "READ"

#: Task states in the existing durable task store that may carry live work.
ACTIVE_TASK_STATES = ("READY", "ACTIVE")

#: Schema emitted by the existing C11 preflight evaluator.
PREFLIGHT_SCHEMA = "p2p-task-preflight/1"

#: Canonical name of the EXISTING permission authority that is reused here.
#: No new permission system, authority plane, database, daemon or token
#: service is introduced by this adapter.
PERMISSION_AUTHORITY_SURFACE = (
    "p2p_capabilities.task_state.evaluate_task_preflight"
    "@.p2p/state/task-state.json"
)

#: Binding schema for the permission record carried inside the portable
#: request. The binding proves WHICH durable permission decision was verified;
#: it never creates one.
PERMISSION_BINDING_SCHEMA = "p2p-impeccable-permission-binding/1"

#: Fingerprints of grants minted by :func:`authorize` in THIS process.
#: Deliberately in-memory: no new database, ledger, daemon or token service.
#: A grant that was never minted here is not an authorization, it is caller data.
_ISSUED_GRANTS: set[str] = set()


class DesignQualityError(RuntimeError):
    """Raised when a design-quality operation cannot run safely."""


class DesignQualityAuthorizationError(DesignQualityError):
    """Raised when the authorization boundary fails closed."""


class DesignQualityPermissionError(DesignQualityAuthorizationError):
    """Raised when the existing P2P permission authority did not grant this."""


def _paths(registry_path: str | Path | None, repository_root: str | Path | None) -> tuple[Path, Path]:
    registry = (
        Path(registry_path).expanduser().resolve()
        if registry_path is not None
        else Path(__file__).resolve().with_name("capabilities.json")
    )
    root = (
        Path(repository_root).expanduser().resolve()
        if repository_root is not None
        else registry.parents[3]
    )
    return registry, root


def _manifest(registry: Path):
    loaded = load_registry(registry)
    for manifest in loaded["parsed"]:
        if manifest.capability_id == CAPABILITY_ID:
            return loaded, manifest
    raise DesignQualityError("DESIGN_QUALITY_CAPABILITY_NOT_REGISTERED")


def _project_binding(registry_hash: str, manifest) -> str:
    """Current registry + capability-manifest identity."""

    return f"registry:{registry_hash}:capability:{manifest.identity_hash}"


def _candidate_binding(snapshot_sha256: str) -> str:
    """Pinned vendor snapshot identity."""

    return f"vendor-snapshot:{CAPABILITY_ID}:{snapshot_sha256}"


def _resolve_identity(
    registry: Path,
    root: Path,
    *,
    require_snapshot: bool = True,
) -> dict[str, Any]:
    """Recompute registry, manifest and vendor-snapshot identity from disk."""

    loaded, manifest = _manifest(registry)
    if not is_vendor_skill(manifest):
        raise DesignQualityError("NOT_A_LOCAL_VENDOR_SKILL")
    provenance = manifest.upstream_provenance
    vendor_relative = str(provenance.get("vendor_path") or "")
    if not vendor_relative:
        raise DesignQualityError("VENDOR_PATH_MISSING")
    vendor_root = (root / vendor_relative).resolve()
    try:
        vendor_root.relative_to(root)
    except ValueError as exc:
        raise DesignQualityError("VENDOR_PATH_OUTSIDE_REPOSITORY") from exc
    canonical_expected = str(provenance.get("snapshot_sha256") or "UNKNOWN")
    observed = None
    if require_snapshot:
        if not vendor_root.is_dir():
            raise DesignQualityAuthorizationError("VENDOR_SNAPSHOT_MISSING")
        observed = snapshot_tree_sha256(vendor_root)
        if canonical_expected in {"", "UNKNOWN"}:
            raise DesignQualityAuthorizationError("CANONICAL_SNAPSHOT_HASH_UNDECLARED")
        if observed != canonical_expected:
            raise DesignQualityAuthorizationError("VENDOR_SNAPSHOT_HASH_MISMATCH")
    return {
        "loaded": loaded,
        "manifest": manifest,
        "registry_hash": loaded["registry_hash"],
        "manifest_identity": manifest.identity_hash,
        "vendor_relative": vendor_relative,
        "vendor_root": vendor_root,
        "canonical_snapshot_sha256": canonical_expected,
        "snapshot_sha256": observed,
        "project_binding": _project_binding(loaded["registry_hash"], manifest),
        "candidate_binding": _candidate_binding(observed or canonical_expected),
        "upstream_commit": provenance.get("upstream_commit", "UNKNOWN"),
    }


def _permission_binding(plan, task, preflight: dict[str, Any]) -> str:
    """Canonical identity of the durable permission decision that was verified."""

    permissions = preflight.get("permission_state")
    view = {
        str(name): str((record or {}).get("status", "UNKNOWN")).upper()
        for name, record in (permissions or {}).items()
        if isinstance(record, dict)
    }
    payload = {
        "schema": PERMISSION_BINDING_SCHEMA,
        "plan_hash": plan.canonical_hash(),
        "goal_id": task.goal_id,
        "task_id": task.task_id,
        "task_status": task.status,
        "permission_needs": sorted(task.permission_needs),
        "permission_state": dict(sorted(view.items())),
        "preflight_status": str(preflight.get("status")),
        "preflight_checked_at": str(preflight.get("checked_at")),
    }
    digest = hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return f"task-preflight:{task.task_id}:{digest}"


def _permission_authority(
    root: Path,
    registry: Path,
    identity: dict[str, Any],
    *,
    task_id: str | None = None,
) -> dict[str, Any]:
    """Verify EXISTING P2P permission authority for an executable action.

    Authority is not invented here. It is read from the durable task state
    store (``.p2p/state/task-state.json``) written by the existing task control
    plane, and re-evaluated through the existing C11 preflight evaluator with
    live capability readiness. The caller supplies no permission input at all:
    the approved permission record and the owner decision come from the
    persisted preflight of a real, active task.
    """

    try:
        plan = TaskStateStore(root).load()
    except (TaskControlPlaneError, TaskStateError) as exc:
        raise DesignQualityPermissionError(f"PERMISSION_AUTHORITY_UNREADABLE:{exc}") from exc
    if plan is None:
        raise DesignQualityPermissionError("PERMISSION_AUTHORITY_STATE_MISSING")
    if plan.plan_lifecycle != "ACTIVE":
        raise DesignQualityPermissionError("PERMISSION_PLAN_NOT_ACTIVE")

    if task_id is not None:
        task = plan.tasks.get(str(task_id).strip().lower())
        if task is None:
            raise DesignQualityPermissionError("PERMISSION_TASK_NOT_FOUND")
    else:
        candidates = [
            item
            for item in plan.tasks.values()
            if CAPABILITY_ID in item.required_capabilities and item.status in ACTIVE_TASK_STATES
        ]
        if not candidates:
            raise DesignQualityPermissionError("PERMISSION_TASK_NOT_FOUND")
        if len(candidates) > 1:
            raise DesignQualityPermissionError("PERMISSION_TASK_AMBIGUOUS")
        task = candidates[0]

    if task.status not in ACTIVE_TASK_STATES:
        raise DesignQualityPermissionError(f"PERMISSION_TASK_NOT_ACTIVE:{task.status}")
    if CAPABILITY_ID not in task.required_capabilities:
        raise DesignQualityPermissionError("PERMISSION_CAPABILITY_NOT_IN_TASK_SCOPE")
    if REQUIRED_PERMISSION not in task.permission_needs:
        raise DesignQualityPermissionError("PERMISSION_NOT_REQUESTED_BY_TASK")

    persisted = task.last_preflight
    if not isinstance(persisted, dict) or persisted.get("schema") != PREFLIGHT_SCHEMA:
        raise DesignQualityPermissionError("PERMISSION_PREFLIGHT_MISSING")
    if persisted.get("status") != "PASS":
        raise DesignQualityPermissionError(
            f"PERMISSION_PREFLIGHT_NOT_PASSED:{persisted.get('status', 'UNKNOWN')}"
        )
    granted_state = persisted.get("permission_state")
    if not isinstance(granted_state, dict) or not granted_state:
        raise DesignQualityPermissionError("PERMISSION_STATE_MISSING")

    # Re-evaluate the SAME gate with live capability readiness. The permission
    # side is exactly the durable owner-approved record; the readiness side is
    # recomputed from disk so a broken/absent snapshot blocks the grant.
    readiness_view = {
        str(name): value
        for name, value in (persisted.get("capability_readiness") or {}).items()
        if isinstance(value, dict)
    }
    readiness_view[CAPABILITY_ID] = vendor_readiness_snapshot(
        identity["manifest"], repository_root=root, registry_path=registry
    )
    try:
        fresh = evaluate_task_preflight(
            task,
            capability_readiness=readiness_view,
            permission_state=granted_state,
            context_state=persisted.get("context_state") or {},
        )
    except TaskStateError as exc:
        raise DesignQualityPermissionError(f"PERMISSION_PREFLIGHT_INVALID:{exc}") from exc
    if fresh["status"] != "PASS":
        raise DesignQualityPermissionError(f"PERMISSION_PREFLIGHT_{fresh['status']}")
    if fresh.get("missing_permissions") or fresh.get("denied_permissions"):
        raise DesignQualityPermissionError("PERMISSION_NOT_GRANTED_BY_P2P_PREFLIGHT")

    return {
        "plan": plan,
        "task": task,
        "persisted_preflight": persisted,
        "reevaluated_preflight": fresh,
        "permission_binding": _permission_binding(plan, task, persisted),
        "authority_surface": PERMISSION_AUTHORITY_SURFACE,
        "state_ref": ".p2p/state/task-state.json",
    }


def availability(
    *,
    registry_path: str | Path | None = None,
    repository_root: str | Path | None = None,
) -> dict[str, Any]:
    """Report registry-level availability. Reads no vendor content."""

    registry, root = _paths(registry_path, repository_root)
    _, manifest = _manifest(registry)
    if not is_vendor_skill(manifest):
        raise DesignQualityError("NOT_A_LOCAL_VENDOR_SKILL")
    metadata = vendor_skill_metadata(manifest, registry_path=registry, repository_root=root)
    readiness = vendor_readiness_snapshot(manifest, repository_root=root, registry_path=registry)
    return {
        "schema": AVAILABILITY_SCHEMA,
        "capability_id": CAPABILITY_ID,
        "available": readiness["states"]["ELIGIBLE"],
        "readiness": readiness,
        "projected_actions": list(PROJECTED_ACTIONS),
        "executable_actions": list(EXECUTABLE_ACTIONS),
        "vendor_path": metadata["vendor_path"],
        "upstream_commit": metadata["upstream_commit"],
        "license": metadata["license"],
        "default_context_loading": False,
        "global_activation": False,
        "content_loaded": False,
        "authorized": False,
        "executed": False,
    }


def authorize(
    action: str,
    *,
    granted_by: str,
    task_id: str | None = None,
    registry_path: str | Path | None = None,
    repository_root: str | Path | None = None,
) -> dict[str, Any]:
    """Verify EXISTING P2P permission, then mint the identity/binding record.

    ``granted_by`` is a provenance LABEL, not authority: no value of it can
    produce an executable grant. For an executable action the permission
    decision must already exist in the durable P2P task state store and its C11
    preflight must still evaluate to ``PASS`` (see :func:`_permission_authority`).
    Only then is a ``PortableExecutionRequest`` minted, and it is used strictly
    as the identity/binding half of the law:

        AUTHORIZATION = verified existing P2P permission
                      + PortableExecutionRequest identity/binding
    """

    if action not in PROJECTED_ACTIONS:
        raise DesignQualityAuthorizationError("ACTION_NOT_PROJECTED")
    if not str(granted_by or "").strip():
        raise DesignQualityAuthorizationError("AUTHORIZATION_GRANT_MISSING")
    registry, root = _paths(registry_path, repository_root)
    identity = _resolve_identity(registry, root)
    executable = action in EXECUTABLE_ACTIONS

    authority: dict[str, Any] | None = None
    if executable:
        # Permission first. A caller-minted binding without this is nothing.
        authority = _permission_authority(root, registry, identity, task_id=task_id)

    bound_task = authority["task"] if authority else None
    permission_binding = authority["permission_binding"] if authority else ""
    try:
        request = PortableExecutionRequest(
            request_id=f"impeccable-{action}-{identity['snapshot_sha256'][:12]}",
            task_id=bound_task.task_id if bound_task else "P2P-IMPECCABLE-01",
            goal_id=bound_task.goal_id if bound_task else "IMPECCABLE_01",
            task_fingerprint=identity["manifest_identity"],
            project_binding=identity["project_binding"],
            candidate_binding=identity["candidate_binding"],
            purpose=action,
            scope=(identity["vendor_relative"],),
            required_capabilities=(CAPABILITY_ID,),
            permission_needs=(REQUIRED_PERMISSION,),
            granted_permissions=(REQUIRED_PERMISSION,) if executable else (),
            context_refs=(permission_binding,) if permission_binding else (),
            expected_environment="LOCAL_PROJECT",
            created_at="P2P-IMPECCABLE-01",
        )
    except HostExecutorContractError as exc:  # pragma: no cover - defensive
        raise DesignQualityAuthorizationError(f"AUTHORIZATION_CONTRACT_INVALID:{exc}") from exc

    fingerprint = request.fingerprint
    _ISSUED_GRANTS.add(fingerprint)
    return {
        "schema": AUTHORIZATION_SCHEMA,
        "capability_id": CAPABILITY_ID,
        "action": action,
        "granted_by": str(granted_by).strip(),
        "authorized": True,
        "executed": False,
        "request": request.to_dict(),
        "request_fingerprint": fingerprint,
        "project_binding": identity["project_binding"],
        "candidate_binding": identity["candidate_binding"],
        "registry_hash": identity["registry_hash"],
        "manifest_identity": identity["manifest_identity"],
        "vendor_path": identity["vendor_relative"],
        "snapshot_sha256": identity["snapshot_sha256"],
        "upstream_commit": identity["upstream_commit"],
        "implementation_authority": "P2P",
        "advisory_only": not executable,
        "permission_authority_surface": PERMISSION_AUTHORITY_SURFACE if executable else None,
        "permission_binding": permission_binding or None,
        "permission_task_id": bound_task.task_id if bound_task else None,
        "permission_preflight_status": (
            authority["persisted_preflight"].get("status") if authority else None
        ),
        "permission_preflight_checked_at": (
            authority["persisted_preflight"].get("checked_at") if authority else None
        ),
        "binding_surface": "p2p_capabilities.host_executor.PortableExecutionRequest",
        "binding_is_not_permission": True,
        "authority_surface": "p2p_capabilities.host_executor.PortableExecutionRequest",
    }


def _verify_grant_for_execution(
    authorization: Any,
    registry: Path,
    root: Path,
    *,
    stage: str = "PRE_EXECUTION",
) -> dict[str, Any]:
    """Fail closed unless permission still holds AND the binding still matches.

    This is called twice: once as an early gate, and once again IMMEDIATELY
    before ``subprocess.run`` with no other filesystem or preflight work in
    between (``stage="FINAL_PRE_LAUNCH"``). Both calls recompute everything
    from disk; nothing is cached between them.
    """

    if not isinstance(authorization, dict):
        raise DesignQualityAuthorizationError("AUTHORIZATION_MALFORMED")
    if authorization.get("schema") != AUTHORIZATION_SCHEMA:
        raise DesignQualityAuthorizationError("AUTHORIZATION_SCHEMA_INVALID")
    if authorization.get("capability_id") != CAPABILITY_ID:
        raise DesignQualityAuthorizationError("AUTHORIZATION_CAPABILITY_MISMATCH")
    action = authorization.get("action")
    if action not in EXECUTABLE_ACTIONS:
        raise DesignQualityAuthorizationError("ACTION_NOT_EXECUTABLE")

    raw_request = authorization.get("request")
    if not isinstance(raw_request, dict):
        raise DesignQualityAuthorizationError("AUTHORIZATION_REQUEST_MISSING")
    try:
        request = PortableExecutionRequest.from_mapping(raw_request)
    except HostExecutorContractError as exc:
        raise DesignQualityAuthorizationError(f"AUTHORIZATION_REQUEST_INVALID:{exc}") from exc

    # 1. The presented fingerprint must be the canonical fingerprint of the
    #    presented request, and must have been minted by authorize() here.
    fingerprint = request.fingerprint
    if authorization.get("request_fingerprint") != fingerprint:
        raise DesignQualityAuthorizationError("AUTHORIZATION_FINGERPRINT_MISMATCH")
    if fingerprint not in _ISSUED_GRANTS:
        raise DesignQualityAuthorizationError("AUTHORIZATION_NOT_ISSUED_BY_P2P_AUTHORITY")

    # 2. The request must still describe this capability and this action.
    if request.purpose != action or request.required_capabilities != (CAPABILITY_ID,):
        raise DesignQualityAuthorizationError("AUTHORIZATION_ACTION_BINDING_MISMATCH")
    if "READ" not in request.granted_permissions or request.mutation_requested:
        raise DesignQualityAuthorizationError("AUTHORIZATION_PERMISSION_BINDING_INVALID")

    # 3. Re-resolve manifest + vendor snapshot from disk RIGHT NOW and require
    #    an exact match with the canonical expected snapshot (TOCTOU close).
    identity = _resolve_identity(registry, root)
    if request.task_fingerprint != identity["manifest_identity"]:
        raise DesignQualityAuthorizationError("REGISTRY_MANIFEST_IDENTITY_DRIFT")
    if identity["snapshot_sha256"] != identity["canonical_snapshot_sha256"]:
        raise DesignQualityAuthorizationError("VENDOR_SNAPSHOT_DRIFT")

    # 4. Revalidate the binding through the existing portable contract.
    binding = validate_binding(
        request=request,
        current_project_binding=identity["project_binding"],
        current_candidate_binding=identity["candidate_binding"],
    )
    if binding["status"] != "BOUND":
        raise DesignQualityAuthorizationError(f"AUTHORIZATION_BINDING_{binding['reason']}")

    # 5. The EXISTING P2P permission authority must still say yes, right now,
    #    and must still be the exact decision this request was bound to.
    authority = _permission_authority(root, registry, identity, task_id=request.task_id)
    expected_binding = authority["permission_binding"]
    if request.context_refs != (expected_binding,):
        raise DesignQualityPermissionError("PERMISSION_AUTHORITY_DRIFT")
    if authorization.get("permission_binding") not in {None, expected_binding}:
        raise DesignQualityPermissionError("PERMISSION_BINDING_MISMATCH")
    if authority["task"].task_id != request.task_id or authority["task"].goal_id != request.goal_id:
        raise DesignQualityPermissionError("PERMISSION_TASK_BINDING_MISMATCH")

    return {
        "request": request,
        "identity": identity,
        "binding": binding,
        "authority": authority,
        "stage": stage,
    }


def deterministic_check(
    targets: Sequence[str | Path],
    *,
    authorization: dict[str, Any],
    repository_root: str | Path | None = None,
    registry_path: str | Path | None = None,
    timeout: int = 120,
) -> dict[str, Any]:
    """Run the pinned offline detector on explicitly supplied files.

    Two gates, in this order:

    1. an early gate (permission authority + binding) before any target work,
    2. a FINAL gate immediately before ``subprocess.run`` — manifest, vendor
       snapshot hash, canonical snapshot identity, project/candidate binding
       and P2P permission authority are all recomputed from disk again, with
       no unrelated filesystem or preflight work between that verification and
       the launch.

    Any failure raises and no detector process is started.
    """

    registry, root = _paths(registry_path, repository_root)
    verified = _verify_grant_for_execution(authorization, registry, root, stage="PRE_EXECUTION")

    resolved_targets = [Path(target) for target in targets]
    if not resolved_targets:
        raise DesignQualityError("NO_TARGET_SUPPLIED")
    runner = root / RUNNER_RELATIVE
    if not runner.is_file():
        raise DesignQualityError("RUNNER_MISSING")

    absolute: list[str] = []
    for target in resolved_targets:
        candidate = (target if target.is_absolute() else root / target).resolve()
        try:
            candidate.relative_to(root)
        except ValueError as exc:
            raise DesignQualityError("TARGET_OUTSIDE_REPOSITORY") from exc
        if not candidate.is_file():
            raise DesignQualityError("TARGET_NOT_A_FILE")
        absolute.append(str(candidate))

    node = shutil.which("node")
    if node is None:
        return {
            "schema": CHECK_SCHEMA,
            "capability_id": CAPABILITY_ID,
            "status": "BLOCKED_OPTIONAL_RUNTIME",
            "missing": ["node"],
            "checked_without_install": True,
            "network_used": False,
            "executed": False,
        }

    # --- FINAL GATE ------------------------------------------------------
    # Last statement before launch. Everything above (targets, node lookup) is
    # already done; nothing but the re-verification stands between this and
    # subprocess.run, so a vendor mutation that lands after the early gate is
    # still caught here and the process is never started.
    verified = _verify_grant_for_execution(authorization, registry, root, stage="FINAL_PRE_LAUNCH")
    identity = verified["identity"]
    command = [node, str(runner), "--root", str(root), *absolute]

    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
        cwd=str(root),
    )
    if completed.returncode != 0:
        raise DesignQualityError(f"DETECTOR_FAILED: {completed.stderr.strip()[:400]}")
    report = json.loads(completed.stdout)
    report.update(
        {
            "capability_id": CAPABILITY_ID,
            "action": authorization["action"],
            "status": "COMPLETED",
            "executed": True,
            "authorized_by": authorization.get("granted_by"),
            "authority_surface": "p2p_capabilities.host_executor.PortableExecutionRequest",
            "permission_authority_surface": PERMISSION_AUTHORITY_SURFACE,
            "permission_binding": verified["authority"]["permission_binding"],
            "permission_task_id": verified["authority"]["task"].task_id,
            "request_fingerprint": verified["request"].fingerprint,
            "binding_revalidated_before_execution": True,
            "final_revalidation_stage": verified["stage"],
            "final_revalidation_position": "IMMEDIATELY_BEFORE_SUBPROCESS",
            "project_binding": identity["project_binding"],
            "candidate_binding": identity["candidate_binding"],
            "vendor_path": identity["vendor_relative"],
            "snapshot_sha256": identity["snapshot_sha256"],
            "upstream_commit": identity["upstream_commit"],
            "implementation_authority": "P2P",
            "source_mutation": False,
        }
    )
    return report


def summarize(report: dict[str, Any]) -> dict[str, int]:
    """Return the stable antipattern histogram of a check report."""

    counts = report.get("antipattern_counts")
    if isinstance(counts, dict):
        return {str(key): int(value) for key, value in sorted(counts.items())}
    return {}


def diff_reports(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    """Deterministic before/after delta for evidence records."""

    before_counts = summarize(before)
    after_counts = summarize(after)
    resolved = sorted(set(before_counts) - set(after_counts))
    introduced = sorted(set(after_counts) - set(before_counts))
    return {
        "before_finding_count": int(before.get("finding_count", 0)),
        "after_finding_count": int(after.get("finding_count", 0)),
        "resolved_antipatterns": resolved,
        "introduced_antipatterns": introduced,
        "engine_mode_before": before.get("engine_mode"),
        "engine_mode_after": after.get("engine_mode"),
    }
