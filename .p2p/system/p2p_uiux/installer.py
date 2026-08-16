"""Safe project installation primitives for the P2P capability."""

import hashlib
import json
import re
import shutil
import tempfile
import tomllib
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from .governance import CANONICAL_AGENTS, OPTIONAL_AESTHETICA, load_manifest, validate_manifest
from .security import scan_tree


MANAGED_SCRIPT_NAMES = (
    "p2p_uiux.py",
    "p2p_router.py",
    "p2p_governance.py",
    "p2p_eval.py",
    "doctor.py",
    "p2p_host_identity_hook.py",
    "drift_check.py",
    "secret_scan.py",
)


def _sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _assert_distinct_paths(source, target):
    source = source.resolve()
    target = target.resolve()
    if source == target:
        raise ValueError("source and project target must be different")
    try:
        target.relative_to(source)
        raise ValueError("project target cannot be inside the package source")
    except ValueError as exc:
        if str(exc) != "project target cannot be inside the package source":
            pass
        else:
            raise
    try:
        source.relative_to(target)
        raise ValueError("package source cannot be inside the project target")
    except ValueError as exc:
        if str(exc) != "package source cannot be inside the project target":
            pass
        else:
            raise


def _profile_name(path):
    text = Path(path).read_text(encoding="utf-8")
    match = re.search(r'^name\s*=\s*["\']([^"\']+)["\']', text, re.MULTILINE)
    return match.group(1) if match else None


def _profile_inventory(profile_dir):
    inventory = {}
    if not profile_dir.exists():
        return inventory
    for path in sorted(profile_dir.glob("p2p-*.toml")):
        name = _profile_name(path)
        if name:
            inventory.setdefault(name, []).append(path)
    return inventory


def _validate_existing_profiles(project_root):
    inventory = _profile_inventory(project_root / ".codex" / "agents")
    present_canonical = set(inventory) & set(CANONICAL_AGENTS)
    if present_canonical and present_canonical != set(CANONICAL_AGENTS):
        missing = sorted(set(CANONICAL_AGENTS) - present_canonical)
        raise ValueError("partial canonical profile set; refusing upgrade: " + ", ".join(missing))
    duplicate_canonical = {name: paths for name, paths in inventory.items() if name in CANONICAL_AGENTS and len(paths) != 1}
    if duplicate_canonical:
        raise ValueError("duplicate canonical profile names; refusing upgrade")
    aesthetica = inventory.get(OPTIONAL_AESTHETICA, [])
    if len(aesthetica) > 1:
        raise ValueError("duplicate p2p_aesthetica profiles; refusing upgrade")
    if aesthetica:
        try:
            profile = tomllib.loads(aesthetica[0].read_text(encoding="utf-8"))
        except tomllib.TOMLDecodeError as exc:
            raise ValueError("existing p2p_aesthetica profile is invalid TOML; refusing overwrite") from exc
        required = {
            "name": profile.get("name") == OPTIONAL_AESTHETICA,
            "description": bool(profile.get("description")),
            "developer_instructions": bool(profile.get("developer_instructions")),
            "sandbox_mode": profile.get("sandbox_mode") == "read-only",
        }
        if not all(required.values()):
            raise ValueError("existing p2p_aesthetica profile is not safely host-compatible; refusing overwrite")
    return {
        "canonical_existing": present_canonical == set(CANONICAL_AGENTS),
        "aesthetica_existing": bool(aesthetica),
        "inventory": {name: [str(path) for path in paths] for name, paths in inventory.items()},
    }


def managed_file_map(source_root, project_root=None):
    source_root = Path(source_root).resolve()
    project_root = Path(project_root).resolve() if project_root else None
    entries = []

    def add_tree(source_dir, target_dir):
        if not source_dir.exists():
            raise FileNotFoundError(str(source_dir))
        for path in sorted(source_dir.rglob("*")):
            if path.is_file():
                rel = path.relative_to(source_dir)
                entries.append((path, Path(target_dir) / rel))

    target_profiles = _validate_existing_profiles(project_root) if project_root else {"canonical_existing": False, "aesthetica_existing": False}
    source_profiles = source_root / ".codex" / "agents"
    if not target_profiles["canonical_existing"]:
        for name in CANONICAL_AGENTS:
            source = source_profiles / (name.replace("p2p_", "p2p-") + ".toml")
            entries.append((source, Path(".codex") / "agents" / source.name))
    if not target_profiles["aesthetica_existing"]:
        source = source_profiles / "p2p-aesthetica.toml"
        entries.append((source, Path(".codex") / "agents" / source.name))
    core_skill = source_root / "skills" / "p2p" / "SKILL.md"
    if project_root is None or not (project_root / ".agents" / "skills" / "p2p" / "SKILL.md").exists():
        entries.append((core_skill, Path(".agents") / "skills" / "p2p" / "SKILL.md"))
    add_tree(source_root / "skills" / "p2p-uiux", Path(".agents") / "skills" / "p2p-uiux")
    add_tree(source_root / "src" / "p2p_uiux", Path(".p2p") / "system" / "p2p_uiux")
    for name in MANAGED_SCRIPT_NAMES:
        path = source_root / "scripts" / name
        if path.exists():
            entries.append((path, Path(".p2p") / "system" / "scripts" / name))
    for name in ("VERSION", "p2p.manifest.json"):
        entries.append((source_root / name, Path(".p2p") / "system" / name))
    for path in (source_root / "references").rglob("*"):
        if path.is_file():
            entries.append((path, Path(".p2p") / "system" / "references" / path.relative_to(source_root / "references")))
    eval_suite = source_root / "docs" / "evals" / "p2p-uiux-eval-suite.json"
    if eval_suite.exists():
        entries.append((eval_suite, Path(".p2p") / "system" / "docs" / "evals" / eval_suite.name))
    return entries


def _protected_hashes(project_root, protected_paths):
    result = {}
    for relative in protected_paths:
        root = project_root / relative
        if root.is_file():
            result[str(relative)] = _sha256(root)
        elif root.is_dir():
            for path in sorted(root.rglob("*")):
                if path.is_file():
                    result[str(path.relative_to(project_root))] = _sha256(path)
    return result


def _safe_extract(archive, destination):
    destination = Path(destination).resolve()
    with zipfile.ZipFile(archive) as handle:
        for member in handle.infolist():
            member_path = (destination / member.filename).resolve()
            try:
                member_path.relative_to(destination)
            except ValueError:
                raise ValueError("package contains an unsafe path")
            if member.is_dir():
                member_path.mkdir(parents=True, exist_ok=True)
            else:
                member_path.parent.mkdir(parents=True, exist_ok=True)
                member_path.write_bytes(handle.read(member))


def _write_managed(source, target, project_root, backup_root, backups):
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and target.read_bytes() == source.read_bytes():
        return False
    if target.exists():
        relative = target.relative_to(project_root)
        backup = backup_root / relative
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(target, backup)
        backups.append(str(backup.relative_to(project_root)))
    temporary = target.with_name(target.name + ".p2p-tmp")
    temporary.write_bytes(source.read_bytes())
    temporary.replace(target)
    return True


def _ensure_core_extension(source_root, project_root, backup_root, backups):
    core_skill = project_root / ".agents" / "skills" / "p2p" / "SKILL.md"
    extension = source_root / "skills" / "p2p-uiux" / "P2P-CORE-EXTENSION.md"
    if not core_skill.exists() or not extension.exists():
        return False
    original = core_skill.read_bytes()
    if b"P2P_UIUX_CAPABILITY_EXTENSION" in original:
        return False
    backup = backup_root / core_skill.relative_to(project_root)
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(core_skill, backup)
    backups.append(str(backup.relative_to(project_root)))
    updated = original.rstrip() + b"\n\n" + extension.read_bytes().lstrip() + b"\n"
    temporary = core_skill.with_name(core_skill.name + ".p2p-tmp")
    temporary.write_bytes(updated)
    temporary.replace(core_skill)
    return True


def install_package(source_root, project_root):
    source_root = Path(source_root).resolve()
    project_root = Path(project_root).resolve()
    if source_root.is_file() and source_root.suffix.lower() == ".zip":
        with tempfile.TemporaryDirectory(prefix="p2p-uiux-package-") as unpacked:
            unpacked_root = Path(unpacked)
            _safe_extract(source_root, unpacked_root)
            return install_package(unpacked_root, project_root)
    _assert_distinct_paths(source_root, project_root)
    manifest = load_manifest(source_root / "p2p.manifest.json")
    validation = validate_manifest(manifest, source_root / ".codex" / "agents")
    if not validation["valid"]:
        raise ValueError("manifest validation failed: " + json.dumps(validation["errors"], sort_keys=True))
    secret_findings = scan_tree(source_root)
    if secret_findings:
        raise ValueError("secret scan failed before install: " + json.dumps(secret_findings, sort_keys=True))
    project_root.mkdir(parents=True, exist_ok=True)
    system_dir = project_root / ".p2p" / "system"
    release_path = system_dir / "release.json"
    prior = {}
    if release_path.exists():
        with release_path.open("r", encoding="utf-8") as handle:
            prior = json.load(handle)
    version = manifest["package_version"]
    if not prior:
        install_class = "FRESH_INSTALL"
    elif prior.get("package_version") == version:
        install_class = "SAME_VERSION_REINSTALL"
    else:
        install_class = "UPGRADE"
    protected_paths = manifest.get("protected_project_paths", [])
    before_protected = _protected_hashes(project_root, protected_paths)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_root = project_root / ".p2p" / "install-backups" / timestamp
    backups = []
    changed = []
    profile_state = _validate_existing_profiles(project_root)
    entries = managed_file_map(source_root, project_root)
    for source, relative_target in entries:
        target = project_root / relative_target
        if _write_managed(source, target, project_root, backup_root, backups):
            changed.append(str(relative_target))
    if _ensure_core_extension(source_root, project_root, backup_root, backups):
        changed.append(str(Path(".agents") / "skills" / "p2p" / "SKILL.md"))
    after_protected = _protected_hashes(project_root, protected_paths)
    if before_protected != after_protected:
        raise RuntimeError("protected project state changed during installation")
    release = {
        "schema": "p2p-install-release/1",
        "package_name": manifest["package_name"],
        "package_version": version,
        "install_class": install_class,
        "installed_at": timestamp,
        "managed_file_count": len(entries),
        "changed_files": changed,
        "backups": backups,
        "protected_state_hashes": after_protected,
        "canonical_denominator": 8,
        "optional_specialist": "p2p_aesthetica",
        "preserved_existing_canonical_profiles": profile_state["canonical_existing"],
        "preserved_existing_core_skill": (project_root / ".agents" / "skills" / "p2p" / "SKILL.md").exists(),
    }
    system_dir.mkdir(parents=True, exist_ok=True)
    release_path.write_text(json.dumps(release, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return release
