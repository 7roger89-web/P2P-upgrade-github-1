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

``availability`` reads registry metadata only. ``authorize`` MINTS a grant on
the existing ``PortableExecutionRequest`` contract, binding it to the capability
identity, the exact action, the current registry/manifest identity and the
pinned vendor snapshot identity, and records the minted request fingerprint in
this process' issuance set. ``deterministic_check`` fails closed unless the
presented grant was minted here AND every binding still validates against
freshly recomputed state at the moment of execution. A hand-built
``{"authorized": true}`` mapping therefore cannot execute anything.
"""

from __future__ import annotations

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
from .vendor_skill import (
    is_vendor_skill,
    snapshot_tree_sha256,
    vendor_readiness_snapshot,
    vendor_skill_metadata,
)

CAPABILITY_ID = "ui.design_quality"
AVAILABILITY_SCHEMA = "p2p-impeccable-availability/1"
AUTHORIZATION_SCHEMA = "p2p-impeccable-authorization/2"
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

#: Fingerprints of grants minted by :func:`authorize` in THIS process.
#: Deliberately in-memory: no new database, ledger, daemon or token service.
#: A grant that was never minted here is not an authorization, it is caller data.
_ISSUED_GRANTS: set[str] = set()


class DesignQualityError(RuntimeError):
    """Raised when a design-quality operation cannot run safely."""


class DesignQualityAuthorizationError(DesignQualityError):
    """Raised when the authorization boundary fails closed."""


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
    registry_path: str | Path | None = None,
    repository_root: str | Path | None = None,
) -> dict[str, Any]:
    """Mint a bound grant on the existing portable execution contract.

    The grant is a ``PortableExecutionRequest`` bound to the capability, the
    exact action, the current registry/manifest identity and the pinned vendor
    snapshot identity. Its canonical fingerprint is recorded in this process'
    issuance set so that only grants minted here can later execute.
    """

    if action not in PROJECTED_ACTIONS:
        raise DesignQualityAuthorizationError("ACTION_NOT_PROJECTED")
    if not str(granted_by or "").strip():
        raise DesignQualityAuthorizationError("AUTHORIZATION_GRANT_MISSING")
    registry, root = _paths(registry_path, repository_root)
    identity = _resolve_identity(registry, root)
    executable = action in EXECUTABLE_ACTIONS
    try:
        request = PortableExecutionRequest(
            request_id=f"impeccable-{action}-{identity['snapshot_sha256'][:12]}",
            task_id="P2P-IMPECCABLE-01",
            goal_id="IMPECCABLE_01",
            task_fingerprint=identity["manifest_identity"],
            project_binding=identity["project_binding"],
            candidate_binding=identity["candidate_binding"],
            purpose=action,
            scope=(identity["vendor_relative"],),
            required_capabilities=(CAPABILITY_ID,),
            permission_needs=("READ",),
            granted_permissions=("READ",) if executable else (),
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
        "authority_surface": "p2p_capabilities.host_executor.PortableExecutionRequest",
    }


def _verify_grant_for_execution(
    authorization: Any,
    registry: Path,
    root: Path,
) -> dict[str, Any]:
    """Fail closed unless the grant was minted here AND still binds to disk."""

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
    return {"request": request, "identity": identity, "binding": binding}


def deterministic_check(
    targets: Sequence[str | Path],
    *,
    authorization: dict[str, Any],
    repository_root: str | Path | None = None,
    registry_path: str | Path | None = None,
    timeout: int = 120,
) -> dict[str, Any]:
    """Run the pinned offline detector on explicitly supplied files.

    Every authorization and binding check happens BEFORE the subprocess is
    launched; any failure raises and no detector process is started.
    """

    registry, root = _paths(registry_path, repository_root)
    verified = _verify_grant_for_execution(authorization, registry, root)
    identity = verified["identity"]

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

    completed = subprocess.run(
        [node, str(runner), "--root", str(root), *absolute],
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
            "request_fingerprint": verified["request"].fingerprint,
            "binding_revalidated_before_execution": True,
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
