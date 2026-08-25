"""Manifest-driven, offline-safe access to local vendor skill snapshots.

This module is an adapter around the existing capability registry and router.
It is intentionally not a skill engine, router, executor, package manager, or
provider implementation. Discovery returns metadata only. Content is read only
after the existing router selects a vendor capability, and optional operations
never install dependencies or use network credentials.
"""

from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping

from .model import CapabilityManifest, load_registry
from .routing import classify_capabilities, readiness_snapshot


VENDOR_ROUTE_SCHEMA = "p2p-vendor-skill-route/1"
VENDOR_LOAD_SCHEMA = "p2p-vendor-skill-load/1"
VENDOR_DEPENDENCY_SCHEMA = "p2p-vendor-skill-dependency/1"
VENDOR_INTEGRATION_MODE = "LOCAL_VENDOR_SNAPSHOT"
_IGNORED_SNAPSHOT_DIRS = frozenset({".venv", "node_modules", "__pycache__"})


class VendorSkillError(ValueError):
    """Raised when a vendor declaration cannot be resolved safely."""


def _registry_path(registry_path: str | Path | None) -> Path:
    if registry_path is not None:
        return Path(registry_path).expanduser().resolve()
    return Path(__file__).resolve().with_name("capabilities.json")


def _repository_root(registry_path: Path, repository_root: str | Path | None) -> Path:
    if repository_root is not None:
        return Path(repository_root).expanduser().resolve()
    # .p2p/system/p2p_capabilities/capabilities.json -> repository root.
    try:
        return registry_path.resolve().parents[3]
    except IndexError as exc:  # pragma: no cover - defensive for malformed paths
        raise VendorSkillError("REPOSITORY_ROOT_UNRESOLVED") from exc


def _safe_relative(value: Any, *, field: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise VendorSkillError(f"{field}_INVALID")
    candidate = Path(value.replace("/", "\\"))
    if candidate.is_absolute() or candidate.drive or value.startswith(("/", "\\")):
        raise VendorSkillError(f"{field}_MUST_BE_REPOSITORY_RELATIVE")
    if ".." in candidate.parts:
        raise VendorSkillError(f"{field}_PATH_TRAVERSAL")
    return Path(value.replace("\\", "/"))


def _within(root: Path, relative: Path, *, field: str) -> Path:
    root = root.resolve()
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise VendorSkillError(f"{field}_OUTSIDE_REPOSITORY") from exc
    return candidate


def _integration(manifest: CapabilityManifest) -> Mapping[str, Any]:
    provenance = manifest.upstream_provenance
    if not isinstance(provenance, Mapping) or provenance.get("mode") != VENDOR_INTEGRATION_MODE:
        raise VendorSkillError("NOT_A_LOCAL_VENDOR_SKILL")
    integration = provenance.get("integration")
    if not isinstance(integration, Mapping):
        raise VendorSkillError("VENDOR_INTEGRATION_METADATA_MISSING")
    return integration


def is_vendor_skill(manifest: CapabilityManifest) -> bool:
    try:
        _integration(manifest)
    except VendorSkillError:
        return False
    return manifest.type == "SKILL" and not manifest.canonical_quorum_member and not manifest.optional_specialist


def _vendor_root(manifest: CapabilityManifest, root: Path) -> Path:
    provenance = manifest.upstream_provenance
    relative = _safe_relative(provenance.get("vendor_path"), field="vendor_path")
    return _within(root, relative, field="vendor_path")


def _entrypoint(manifest: CapabilityManifest, vendor_root: Path) -> tuple[Path, str]:
    integration = _integration(manifest)
    relative = _safe_relative(integration.get("entrypoint"), field="entrypoint")
    return _within(vendor_root, relative, field="entrypoint"), relative.as_posix()


def _declared_path(relative: str, declarations: Iterable[Any], *, field: str) -> Path:
    requested = _safe_relative(relative, field=field).as_posix()
    allowed: list[str] = []
    for item in declarations:
        raw = str(item)
        directory = raw.replace("\\", "/").endswith("/")
        normalized = _safe_relative(raw, field=f"{field}_declaration").as_posix()
        allowed.append(normalized + "/" if directory else normalized)
    if not any(
        requested == item or (item.endswith("/") and requested.startswith(item))
        for item in allowed
    ):
        raise VendorSkillError(f"{field.upper()}_NOT_DECLARED")
    return Path(requested)


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _canonical_source_bytes(data: bytes) -> bytes:
    """Match the repository's portable text hashing policy.

    Git stores text surfaces with LF under the repository's ``text=auto``
    attribute. A Windows checkout may materialize those same bytes as CRLF.
    Canonicalize text line endings for identity checks while preserving binary
    files exactly, as the existing governance hash contract does.
    """

    if b"\x00" in data:
        return data
    return data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(_canonical_source_bytes(data)).hexdigest()


def canonical_source_sha256(data: bytes) -> str:
    """Return the canonical identity hash for a repository source payload."""

    return _sha256_bytes(data)


def snapshot_tree_sha256(root: str | Path) -> str:
    """Hash canonical source bytes and relative names, excluding local output."""

    root_path = Path(root).expanduser().resolve()
    if not root_path.is_dir():
        raise VendorSkillError("VENDOR_SNAPSHOT_MISSING")
    entries: list[str] = []
    for path in sorted(root_path.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root_path)
        if any(part in _IGNORED_SNAPSHOT_DIRS for part in relative.parts):
            continue
        entries.append(f"{relative.as_posix()}\n{_sha256_file(path)}")
    return hashlib.sha256("\n".join(entries).encode("utf-8")).hexdigest()


def _manifest_for(capability_id: str, registry_path: Path) -> tuple[dict[str, Any], CapabilityManifest]:
    loaded = load_registry(registry_path)
    for manifest in loaded["parsed"]:
        if manifest.capability_id == capability_id:
            return loaded, manifest
    raise VendorSkillError("VENDOR_CAPABILITY_NOT_FOUND")


def vendor_skill_metadata(
    manifest: CapabilityManifest,
    *,
    registry_path: str | Path | None = None,
    repository_root: str | Path | None = None,
) -> dict[str, Any]:
    """Return metadata without reading the vendor entrypoint or references."""

    integration = _integration(manifest)
    registry = _registry_path(registry_path)
    root = _repository_root(registry, repository_root)
    vendor_root = _vendor_root(manifest, root)
    entrypoint = _safe_relative(integration.get("entrypoint"), field="entrypoint")
    return {
        "capability_id": manifest.capability_id,
        "implementation": manifest.upstream_provenance.get("implementation", "UNKNOWN"),
        "vendor_path": _safe_relative(manifest.upstream_provenance.get("vendor_path"), field="vendor_path").as_posix(),
        "entrypoint": entrypoint.as_posix(),
        "load_mode": integration.get("load_mode", "UNKNOWN"),
        "dependency_mode": integration.get("dependency_mode", "UNKNOWN"),
        "references": list(integration.get("references", [])),
        "assets": list(integration.get("assets", [])),
        "script_entrypoints": list(integration.get("script_entrypoints", [])),
        "snapshot_sha256": manifest.upstream_provenance.get("snapshot_sha256", "UNKNOWN"),
        "entrypoint_sha256": integration.get("entrypoint_sha256", "UNKNOWN"),
        "upstream_repository": manifest.upstream_provenance.get("upstream_repository", "UNKNOWN"),
        "upstream_commit": manifest.upstream_provenance.get("upstream_commit", "UNKNOWN"),
        "version": manifest.version,
        "license": manifest.upstream_provenance.get("license", "UNKNOWN"),
        "source_state": "PRESENT" if vendor_root.is_dir() else "MISSING",
        "entrypoint_present": (vendor_root / entrypoint).is_file(),
        "content_loaded": False,
        "permission_grant": False,
        "network_runtime": False,
    }


def vendor_readiness_snapshot(
    manifest: CapabilityManifest,
    *,
    repository_root: str | Path,
    registry_path: str | Path | None = None,
) -> dict[str, Any]:
    """Derive structural readiness without loading vendor content."""

    registry = _registry_path(registry_path)
    root = _repository_root(registry, repository_root)
    try:
        vendor_root = _vendor_root(manifest, root)
        entrypoint, _ = _entrypoint(manifest, vendor_root)
    except VendorSkillError as exc:
        return readiness_snapshot(manifest, installed=False, reasons=[str(exc)])
    if not vendor_root.is_dir():
        return readiness_snapshot(manifest, installed=False, reasons=["VENDOR_SNAPSHOT_MISSING"])
    if not entrypoint.is_file():
        return readiness_snapshot(
            manifest,
            installed=True,
            discovered=True,
            eligible=True,
            resolved=False,
            executable=False,
            healthy=False,
            reasons=["VENDOR_ENTRYPOINT_MISSING"],
        )
    return readiness_snapshot(
        manifest,
        installed=True,
        discovered=True,
        eligible=True,
        resolved=True,
        executable=True,
        healthy=True,
        reasons=["LOCAL_SNAPSHOT_PRESENT", "CONTENT_LOAD_ON_DEMAND"],
    )


def project_vendor_route(
    request: str,
    manifests: Iterable[CapabilityManifest],
    route: Mapping[str, Any],
    *,
    registry_path: str | Path | None = None,
    repository_root: str | Path | None = None,
) -> dict[str, Any]:
    """Project selected vendor metadata into the existing route result."""

    selected = set(route.get("selected", []))
    skills: list[dict[str, Any]] = []
    for manifest in manifests:
        if not is_vendor_skill(manifest):
            continue
        metadata = vendor_skill_metadata(
            manifest,
            registry_path=registry_path,
            repository_root=repository_root,
        )
        result = next(
            (item for item in route.get("results", []) if item.get("capability_id") == manifest.capability_id),
            {},
        )
        metadata.update(
            {
                "selected": manifest.capability_id in selected,
                "classification": result.get("classification", "NOT_APPLICABLE"),
                "readiness": result.get("readiness", {}),
                "request": str(request or "").strip(),
            }
        )
        skills.append(metadata)
    return {
        "schema": VENDOR_ROUTE_SCHEMA,
        "selected": [item["capability_id"] for item in skills if item["selected"]],
        "skills": skills,
        "content_loaded": False,
        "permission_grant": False,
    }


def discover_vendor_skills(
    request: str,
    *,
    registry_path: str | Path | None = None,
    repository_root: str | Path | None = None,
) -> dict[str, Any]:
    """Route and return vendor metadata only; no SKILL.md is read."""

    registry = _registry_path(registry_path)
    loaded = load_registry(registry)
    root = _repository_root(registry, repository_root)
    readiness = {
        manifest.capability_id: vendor_readiness_snapshot(
            manifest,
            repository_root=root,
            registry_path=registry,
        )
        for manifest in loaded["parsed"]
        if is_vendor_skill(manifest)
    }
    route = classify_capabilities(request, loaded["parsed"], readiness=readiness)
    projection = project_vendor_route(
        request,
        loaded["parsed"],
        route,
        registry_path=registry,
        repository_root=root,
    )
    return {
        **projection,
        "route": route,
        "registry_hash": loaded["registry_hash"],
    }


def load_vendor_skill(
    capability_id: str,
    *,
    registry_path: str | Path | None = None,
    repository_root: str | Path | None = None,
    references: Iterable[str] = (),
    assets: Iterable[str] = (),
) -> dict[str, Any]:
    """Load exact upstream skill text and explicitly requested context only."""

    registry = _registry_path(registry_path)
    loaded, manifest = _manifest_for(capability_id, registry)
    if not is_vendor_skill(manifest):
        raise VendorSkillError("NOT_A_LOCAL_VENDOR_SKILL")
    root = _repository_root(registry, repository_root)
    vendor_root = _vendor_root(manifest, root)
    if not vendor_root.is_dir():
        raise VendorSkillError("VENDOR_SNAPSHOT_MISSING")
    entrypoint, entrypoint_relative = _entrypoint(manifest, vendor_root)
    if not entrypoint.is_file():
        raise VendorSkillError("VENDOR_ENTRYPOINT_MISSING")

    provenance = manifest.upstream_provenance
    integration = _integration(manifest)
    expected_tree = provenance.get("snapshot_sha256")
    if expected_tree and expected_tree != "UNKNOWN" and snapshot_tree_sha256(vendor_root) != expected_tree:
        raise VendorSkillError("VENDOR_SNAPSHOT_HASH_MISMATCH")
    entrypoint_bytes = entrypoint.read_bytes()
    entrypoint_hash = _sha256_bytes(entrypoint_bytes)
    expected_entrypoint = integration.get("entrypoint_sha256")
    if expected_entrypoint and expected_entrypoint != "UNKNOWN" and entrypoint_hash != expected_entrypoint:
        raise VendorSkillError("VENDOR_ENTRYPOINT_HASH_MISMATCH")

    loaded_references: dict[str, dict[str, Any]] = {}
    declared_references = integration.get("references", [])
    for requested in references:
        relative = _declared_path(requested, declared_references, field="reference")
        path = _within(vendor_root, relative, field="reference")
        if not path.is_file():
            raise VendorSkillError("VENDOR_REFERENCE_MISSING")
        content = path.read_text(encoding="utf-8")
        loaded_references[relative.as_posix()] = {
            "content": content,
            "sha256": _sha256_file(path),
        }

    loaded_assets: dict[str, dict[str, Any]] = {}
    declared_assets = integration.get("assets", [])
    for requested in assets:
        relative = _declared_path(requested, declared_assets, field="asset")
        path = _within(vendor_root, relative, field="asset")
        if not path.is_file():
            raise VendorSkillError("VENDOR_ASSET_MISSING")
        loaded_assets[relative.as_posix()] = {
            "sha256": _sha256_file(path),
            "size": path.stat().st_size,
        }

    return {
        "schema": VENDOR_LOAD_SCHEMA,
        "status": "LOADED",
        "capability_id": manifest.capability_id,
        "implementation": provenance.get("implementation", "UNKNOWN"),
        "entrypoint": entrypoint_relative,
        "skill": {
            "content": entrypoint_bytes.decode("utf-8"),
            "sha256": entrypoint_hash,
        },
        "references": loaded_references,
        "assets": loaded_assets,
        "loaded_paths": [entrypoint_relative, *loaded_references.keys(), *loaded_assets.keys()],
        "content_loaded": True,
        "permission_grant": False,
        "network_used": False,
        "registry_hash": loaded["registry_hash"],
    }


def optional_dependency_status(
    capability_id: str,
    *,
    operation: str = "load",
    registry_path: str | Path | None = None,
    repository_root: str | Path | None = None,
) -> dict[str, Any]:
    """Probe optional operations without installing or contacting a service."""

    registry = _registry_path(registry_path)
    loaded, manifest = _manifest_for(capability_id, registry)
    if not is_vendor_skill(manifest):
        raise VendorSkillError("NOT_A_LOCAL_VENDOR_SKILL")
    root = _repository_root(registry, repository_root)
    vendor_root = _vendor_root(manifest, root)
    if operation not in {"render", "execute"}:
        return {
            "schema": VENDOR_DEPENDENCY_SCHEMA,
            "capability_id": capability_id,
            "operation": operation,
            "status": "NOT_REQUIRED",
            "checked_without_install": True,
            "network_used": False,
            "missing": [],
        }
    if not vendor_root.is_dir():
        return {
            "schema": VENDOR_DEPENDENCY_SCHEMA,
            "capability_id": capability_id,
            "operation": operation,
            "status": "BLOCKED_VENDOR_SNAPSHOT",
            "checked_without_install": True,
            "network_used": False,
            "missing": ["vendor-snapshot"],
        }

    integration = _integration(manifest)
    missing: list[str] = []
    probe = str(integration.get("dependency_probe", ""))
    if capability_id == "media.whiteboard_animation":
        if not probe:
            missing.append("dependency-probe")
        else:
            probe_path = _within(vendor_root, _safe_relative(probe.split(" ", 1)[0], field="dependency_probe"), field="dependency_probe")
            if not probe_path.is_file():
                missing.append("dependency-probe")
            else:
                if sys.platform.startswith("win"):
                    venv_python = vendor_root / ".venv" / "Scripts" / "python.exe"
                else:
                    venv_python = vendor_root / ".venv" / "bin" / "python"
                if not venv_python.is_file():
                    missing.append("vendor-venv")
                else:
                    check = subprocess.run(
                        [sys.executable, str(probe_path), "--check"],
                        cwd=str(vendor_root),
                        capture_output=True,
                        text=True,
                        timeout=20,
                        check=False,
                    )
                    if check.returncode != 0:
                        missing.append("whiteboard-python-dependencies")
    elif capability_id == "creative.copywriting":
        canvas_module = vendor_root / "assets" / "node_modules" / "@napi-rs" / "canvas"
        if not canvas_module.is_dir():
            missing.append("@napi-rs/canvas")
        if not (vendor_root / "assets" / "package.json").is_file():
            missing.append("asset-package-manifest")
    else:
        missing.append("unsupported-optional-operation")

    return {
        "schema": VENDOR_DEPENDENCY_SCHEMA,
        "capability_id": capability_id,
        "operation": operation,
        "status": "BLOCKED_OPTIONAL_DEPENDENCY" if missing else "AVAILABLE_UNCERTIFIED",
        "checked_without_install": True,
        "network_used": False,
        "credentials_used": False,
        "missing": missing,
        "registry_hash": loaded["registry_hash"],
    }
