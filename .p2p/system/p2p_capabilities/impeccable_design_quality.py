"""Bounded adapter for the pinned Impeccable design-quality capability.

This module is an adapter over the EXISTING P2P capability registry, router and
vendor-skill machinery (``p2p_capabilities.vendor_skill``). It deliberately is
not a second router, orchestrator, design system, skill loader, scheduler or
daemon, and it holds no implementation authority: it can observe and report
design-quality problems, never rewrite a project surface.

Staged law enforced here:

    AVAILABLE != LOADED != AUTHORIZED != EXECUTED

``availability`` reads registry metadata only. ``authorize`` binds an explicit
caller grant to a verified vendor snapshot. ``deterministic_check`` refuses to
run without that grant, and runs the pinned offline detector engines only: no
model, no network, no browser, no install, no live/cache session state.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, Sequence

from .model import load_registry
from .vendor_skill import (
    VendorSkillError,
    is_vendor_skill,
    snapshot_tree_sha256,
    vendor_readiness_snapshot,
    vendor_skill_metadata,
)

CAPABILITY_ID = "ui.design_quality"
AVAILABILITY_SCHEMA = "p2p-impeccable-availability/1"
AUTHORIZATION_SCHEMA = "p2p-impeccable-authorization/1"
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


class DesignQualityError(RuntimeError):
    """Raised when a design-quality operation cannot run safely."""


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
    for manifest in load_registry(registry)["parsed"]:
        if manifest.capability_id == CAPABILITY_ID:
            return manifest
    raise DesignQualityError("DESIGN_QUALITY_CAPABILITY_NOT_REGISTERED")


def availability(
    *,
    registry_path: str | Path | None = None,
    repository_root: str | Path | None = None,
) -> dict[str, Any]:
    """Report registry-level availability. Reads no vendor content."""

    registry, root = _paths(registry_path, repository_root)
    manifest = _manifest(registry)
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
    """Bind an explicit caller grant to a hash-verified vendor snapshot."""

    if action not in PROJECTED_ACTIONS:
        raise DesignQualityError("ACTION_NOT_PROJECTED")
    if not str(granted_by or "").strip():
        raise DesignQualityError("AUTHORIZATION_GRANT_MISSING")
    registry, root = _paths(registry_path, repository_root)
    manifest = _manifest(registry)
    provenance = manifest.upstream_provenance
    vendor_root = root / str(provenance.get("vendor_path"))
    if not vendor_root.is_dir():
        raise DesignQualityError("VENDOR_SNAPSHOT_MISSING")
    observed = snapshot_tree_sha256(vendor_root)
    expected = str(provenance.get("snapshot_sha256", "UNKNOWN"))
    if expected in {"", "UNKNOWN"} or observed != expected:
        raise DesignQualityError("VENDOR_SNAPSHOT_HASH_MISMATCH")
    return {
        "schema": AUTHORIZATION_SCHEMA,
        "capability_id": CAPABILITY_ID,
        "action": action,
        "granted_by": str(granted_by).strip(),
        "authorized": True,
        "executed": False,
        "vendor_path": str(provenance.get("vendor_path")),
        "snapshot_sha256": observed,
        "upstream_commit": provenance.get("upstream_commit", "UNKNOWN"),
        "implementation_authority": "P2P",
        "advisory_only": action not in EXECUTABLE_ACTIONS,
    }


def deterministic_check(
    targets: Sequence[str | Path],
    *,
    authorization: dict[str, Any],
    repository_root: str | Path | None = None,
    registry_path: str | Path | None = None,
    timeout: int = 120,
) -> dict[str, Any]:
    """Run the pinned offline detector on explicitly supplied files."""

    if not isinstance(authorization, dict) or not authorization.get("authorized"):
        raise DesignQualityError("NOT_AUTHORIZED")
    if authorization.get("capability_id") != CAPABILITY_ID:
        raise DesignQualityError("AUTHORIZATION_CAPABILITY_MISMATCH")
    if authorization.get("action") not in EXECUTABLE_ACTIONS:
        raise DesignQualityError("ACTION_NOT_EXECUTABLE")
    resolved_targets = [Path(target) for target in targets]
    if not resolved_targets:
        raise DesignQualityError("NO_TARGET_SUPPLIED")

    registry, root = _paths(registry_path, repository_root)
    runner = root / RUNNER_RELATIVE
    if not runner.is_file():
        raise DesignQualityError("RUNNER_MISSING")
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
            "vendor_path": authorization.get("vendor_path"),
            "snapshot_sha256": authorization.get("snapshot_sha256"),
            "upstream_commit": authorization.get("upstream_commit"),
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
