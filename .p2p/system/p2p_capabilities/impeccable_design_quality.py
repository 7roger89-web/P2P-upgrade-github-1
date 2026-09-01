"""Bounded adapter for the pinned Impeccable design-quality capability.

This module is an adapter over the EXISTING P2P capability registry, router and
vendor-skill machinery (``p2p_capabilities.vendor_skill``). It is deliberately
not a second router, orchestrator, design system, skill loader, permission
system, authority plane, token service, scheduler or daemon, and it holds no
implementation authority: it observes and reports design-quality problems and
never rewrites a project surface.

Execution class::

    EXECUTION_CLASS = READ_ONLY_LOCAL_DETERMINISTIC_CHECK

What that means, stated honestly:

* ``deterministic_check`` reads explicitly supplied, repository-local files and
  runs the pinned offline detector on them. It is read-only, local,
  deterministic, target-explicit; no network, no model, no browser, no
  credentials, no install, no source mutation.
* Explicit P2P selection/invocation of this read-only capability is sufficient
  to run it. This adapter makes **no runtime permission-authority claim**
  (``RUNTIME_PERMISSION_AUTHORITY_CLAIM = NONE``): it does not mint grants, does
  not verify permissions, and no metadata it emits should be read as authority.
* An individual read-only check is not an Owner Gate. The Owner Gate that
  matters is promotion/merge of the capability itself.

The security boundary that IS enforced here is artifact identity, not
permission: pinned upstream commit/tree, exact vendor snapshot, canonical
snapshot hash, repository-local explicit targets, and a final vendor-identity
gate re-run immediately before ``subprocess.run`` with no unrelated filesystem
or preparation work in between.

Staged law enforced here::

    AVAILABLE != LOADED != SELECTED != EXECUTED
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, Sequence

from .model import load_registry
from .vendor_skill import (
    is_vendor_skill,
    snapshot_tree_sha256,
    vendor_readiness_snapshot,
    vendor_skill_metadata,
)

CAPABILITY_ID = "ui.design_quality"
AVAILABILITY_SCHEMA = "p2p-impeccable-availability/1"
SELECTION_SCHEMA = "p2p-impeccable-selection/1"
CHECK_SCHEMA = "p2p-impeccable-deterministic-check/1"
RUNNER_RELATIVE = ".p2p/system/p2p_capabilities/impeccable_detector_runner.mjs"

#: Truthful execution class of the one executable action.
EXECUTION_CLASS = "READ_ONLY_LOCAL_DETERMINISTIC_CHECK"

#: This adapter claims no runtime permission authority of any kind.
RUNTIME_PERMISSION_AUTHORITY_CLAIM = "NONE"

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


class DesignQualityError(RuntimeError):
    """Raised when a design-quality operation cannot run safely."""


class DesignQualityVendorIdentityError(DesignQualityError):
    """Raised when the pinned vendor artifact identity no longer holds."""


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


def _resolve_identity(
    registry: Path,
    root: Path,
    *,
    require_snapshot: bool = True,
) -> dict[str, Any]:
    """Recompute registry, manifest and vendor-snapshot identity from disk.

    This is artifact identity, not permission: it proves that the code about to
    run is exactly the pinned, unmodified vendor snapshot recorded in the
    registry.
    """

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
            raise DesignQualityVendorIdentityError("VENDOR_SNAPSHOT_MISSING")
        observed = snapshot_tree_sha256(vendor_root)
        if canonical_expected in {"", "UNKNOWN"}:
            raise DesignQualityVendorIdentityError("CANONICAL_SNAPSHOT_HASH_UNDECLARED")
        if observed != canonical_expected:
            raise DesignQualityVendorIdentityError("VENDOR_SNAPSHOT_HASH_MISMATCH")
    return {
        "loaded": loaded,
        "manifest": manifest,
        "registry_hash": loaded["registry_hash"],
        "manifest_identity": manifest.identity_hash,
        "vendor_relative": vendor_relative,
        "vendor_root": vendor_root,
        "canonical_snapshot_sha256": canonical_expected,
        "snapshot_sha256": observed,
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
        "execution_class": EXECUTION_CLASS,
        "vendor_path": metadata["vendor_path"],
        "upstream_commit": metadata["upstream_commit"],
        "license": metadata["license"],
        "default_context_loading": False,
        "global_activation": False,
        "content_loaded": False,
        "selected": False,
        "executed": False,
    }


def select_action(
    action: str,
    *,
    registry_path: str | Path | None = None,
    repository_root: str | Path | None = None,
) -> dict[str, Any]:
    """Record an explicit selection of one projected action.

    This is a selection record for evidence and routing clarity. It is NOT an
    authorization, a permission, a grant or a token, and nothing here is treated
    as authority by :func:`deterministic_check`: the executable action is a
    read-only local check whose safety comes from artifact identity and explicit
    repository-local targets, not from this record.
    """

    if action not in PROJECTED_ACTIONS:
        raise DesignQualityError("ACTION_NOT_PROJECTED")
    registry, root = _paths(registry_path, repository_root)
    executable = action in EXECUTABLE_ACTIONS
    identity = _resolve_identity(registry, root, require_snapshot=executable)
    return {
        "schema": SELECTION_SCHEMA,
        "capability_id": CAPABILITY_ID,
        "action": action,
        "selected": True,
        "executed": False,
        "executable": executable,
        "advisory_only": not executable,
        "execution_class": EXECUTION_CLASS if executable else "ADVISORY_REFERENCE_TEXT",
        "runtime_permission_authority_claim": RUNTIME_PERMISSION_AUTHORITY_CLAIM,
        "owner_gate_required_for_read_only_check": False,
        "owner_gate_required_for_promotion": True,
        "registry_hash": identity["registry_hash"],
        "manifest_identity": identity["manifest_identity"],
        "vendor_path": identity["vendor_relative"],
        "snapshot_sha256": identity["snapshot_sha256"],
        "upstream_commit": identity["upstream_commit"],
        "implementation_authority": "P2P",
    }


def _final_vendor_identity_gate(registry: Path, root: Path, runner: Path) -> dict[str, Any]:
    """Re-prove pinned artifact identity and the declared execution surface."""

    identity = _resolve_identity(registry, root)
    if identity["snapshot_sha256"] != identity["canonical_snapshot_sha256"]:
        raise DesignQualityVendorIdentityError("VENDOR_SNAPSHOT_DRIFT")
    if not runner.is_file():
        raise DesignQualityVendorIdentityError("RUNNER_MISSING")
    try:
        runner.resolve().relative_to(root)
    except ValueError as exc:
        raise DesignQualityVendorIdentityError("RUNNER_OUTSIDE_REPOSITORY") from exc
    return identity


def deterministic_check(
    targets: Sequence[str | Path],
    *,
    selection: dict[str, Any] | None = None,
    repository_root: str | Path | None = None,
    registry_path: str | Path | None = None,
    timeout: int = 120,
) -> dict[str, Any]:
    """Run the pinned offline detector on explicitly supplied files.

    Read-only, local, deterministic. Calling this function IS the explicit
    invocation of the capability; no permission grant is minted, required or
    claimed. What is enforced:

    * at least one explicitly supplied target (no filesystem crawl),
    * every target resolves to a file inside ``repository_root``,
    * an optional ``selection`` record must name the executable action,
    * pinned vendor artifact identity, re-proved IMMEDIATELY before
      ``subprocess.run`` — manifest re-resolved, vendor snapshot re-resolved,
      snapshot hash recomputed and matched against the canonical declared hash,
      runner surface still valid — with no unrelated filesystem or preparation
      work between that gate and the launch.

    Any failure raises and no detector process is started.
    """

    registry, root = _paths(registry_path, repository_root)

    if selection is not None:
        if not isinstance(selection, dict) or selection.get("schema") != SELECTION_SCHEMA:
            raise DesignQualityError("SELECTION_RECORD_INVALID")
        if selection.get("capability_id") != CAPABILITY_ID:
            raise DesignQualityError("SELECTION_CAPABILITY_MISMATCH")
        if selection.get("action") not in EXECUTABLE_ACTIONS:
            raise DesignQualityError("ACTION_NOT_EXECUTABLE")

    resolved_targets = [Path(target) for target in targets]
    if not resolved_targets:
        raise DesignQualityError("NO_TARGET_SUPPLIED")

    # Early artifact-identity check, before any target work.
    _resolve_identity(registry, root)

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

    # --- FINAL VENDOR IDENTITY GATE ---------------------------------------
    # Everything else (targets, runtime lookup) is already done. Nothing but
    # the argv list stands between this gate and the launch, so a vendor
    # mutation landing after the earlier check is still caught here and the
    # detector process is never started.
    identity = _final_vendor_identity_gate(registry, root, runner)
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
            "action": EXECUTABLE_ACTIONS[0],
            "status": "COMPLETED",
            "executed": True,
            "execution_class": EXECUTION_CLASS,
            "runtime_permission_authority_claim": RUNTIME_PERMISSION_AUTHORITY_CLAIM,
            "owner_gate_required_for_read_only_check": False,
            "owner_gate_required_for_promotion": True,
            "vendor_identity_revalidated_immediately_before_subprocess": True,
            "registry_hash": identity["registry_hash"],
            "manifest_identity": identity["manifest_identity"],
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
