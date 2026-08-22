#!/usr/bin/env python3
"""P2P Safe Installer — hardened project-adoption machinery.

Spec RM-PRIORITY-RELEASE-LIFECYCLE §6:
- Idempotent install/upgrade/rollback
- Artifact SHA verification
- Project fingerprinting
- No silent source overwrite (fail-closed)
- Portable paths
- Project-local P2P state separation
- Doctor immediately after install

Corrective 01A Upgrades:
- Fail-closed identity validation (VERSION vs Manifest vs Requested)
- Strict Doctor semantics (UNHEALTHY != SUCCESS)
- Project Pin integrity
"""
import argparse
import datetime
import hashlib
import importlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

INSTALL_MANIFEST_SCHEMA = "p2p-install-manifest/2"
RELEASE_MARKER_SCHEMA = "p2p-install-release/2"
PROJECT_PIN_SCHEMA = "p2p-project-pin/1"
CANDIDATE_MANIFEST_NAME = "CANDIDATE-DISTRIBUTION-MANIFEST.json"

class InstallerError(Exception):
    pass

def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def get_project_fingerprint(root: Path) -> str:
    """Use the one canonical project-fingerprint implementation."""
    return _project_pin_module(root).project_fingerprint(root)


def _project_pin_module(metadata_root: Path | None = None):
    candidates = []
    if metadata_root is not None:
        candidates.extend((metadata_root, metadata_root / "runtime", metadata_root / ".p2p" / "system"))
    candidates.extend((Path(__file__).resolve().parents[1] / ".p2p" / "system", Path(__file__).resolve().parents[1]))
    for candidate in candidates:
        module_path = candidate / "p2p_capabilities" / "project_pin.py"
        if module_path.is_file():
            if str(candidate) not in sys.path:
                sys.path.insert(0, str(candidate))
            return importlib.import_module("p2p_capabilities.project_pin")
    raise InstallerError("PROJECT_PIN_PRODUCER_MISSING")

def load_json(p: Path) -> Dict:
    if not p.exists():
        return {}
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

def dump_json(p: Path, obj: Any) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
        f.write("\n")

def stamp_now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d-%H%M%S")

def _validate_artifact_identity(temp_extract: Path, requested_version: str, artifact_sha: str) -> str:
    """Performs fail-closed identity validation (§2)."""
    version_file = temp_extract / "VERSION"
    if not version_file.exists():
        raise InstallerError("INSTALL_BLOCKED / MISSING_VERSION_FILE")
    
    embedded_version = version_file.read_text().strip()
    
    package_manifest = load_json(temp_extract / "manifest" / "package.json")
    if package_manifest.get("version") != embedded_version:
        raise InstallerError(
            "INSTALL_BLOCKED / PACKAGE_VERSION_IDENTITY_MISMATCH: "
            "VERSION and manifest/package.json differ")
    candidate_manifest = load_json(temp_extract / CANDIDATE_MANIFEST_NAME)
    if candidate_manifest:
        if candidate_manifest.get("candidate_version") != embedded_version:
            raise InstallerError(
                "INSTALL_BLOCKED / PACKAGE_VERSION_IDENTITY_MISMATCH: "
                "candidate distribution manifest differs from VERSION")
        if candidate_manifest.get("candidate_vs_official") != "UNPROMOTED_SUCCESSOR_CANDIDATE":
            raise InstallerError("INSTALL_BLOCKED / CANDIDATE_PROMOTION_STATE_INVALID")
    
    if embedded_version != requested_version:
        raise InstallerError(
            f"INSTALL_BLOCKED / PACKAGE_VERSION_IDENTITY_MISMATCH: "
            f"Requested {requested_version}, but package declares {embedded_version}"
        )
    
    return embedded_version

def install(project_root: Path, artifact_path: Path, expected_sha: str, requested_version: str, mode: str = "PORTABLE") -> Dict:
    project_root = project_root.resolve()
    
    # 0. Pre-validation
    if not artifact_path.exists():
        raise InstallerError(f"Artifact not found: {artifact_path}")
    actual_sha = sha256(artifact_path)
    if actual_sha != expected_sha:
        raise InstallerError(f"Artifact SHA mismatch — expected {expected_sha}, got {actual_sha}")

    # 1. Discovery & Fingerprint
    fingerprint = get_project_fingerprint(project_root)
    p2p_dir = project_root / ".p2p"
    system_dir = p2p_dir / "system"
    backups_root = p2p_dir / "install-backups"
    
    # 2. Pre-install Snapshot (Rollback source)
    stamp = stamp_now()
    snapshot_dir = backups_root / stamp
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    
    if system_dir.exists():
        shutil.copytree(system_dir, snapshot_dir / "system_backup")
    
    # 3. Extract to temp & Validate Identity
    temp_root = project_root / ".tmp"
    temp_root.mkdir(parents=True, exist_ok=True)
    temp_extract = Path(tempfile.mkdtemp(prefix=f"p2p-install-{stamp}-", dir=str(temp_root)))
    shutil.unpack_archive(str(artifact_path), str(temp_extract))
    
    try:
        embedded_version = _validate_artifact_identity(temp_extract, requested_version, expected_sha)
        candidate_metadata = load_json(temp_extract / CANDIDATE_MANIFEST_NAME)
    except Exception as e:
        shutil.rmtree(temp_extract)
        raise e
    
    # 4. Safe Copy
    managed_files = []
    if system_dir.exists():
        shutil.rmtree(system_dir)
    system_dir.mkdir(parents=True, exist_ok=True)
    
    for item in temp_extract.rglob("*"):
        if item.is_file():
            rel = item.relative_to(temp_extract)
            dest = system_dir / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, dest)
            managed_files.append(rel.as_posix())
            
    # 5. Doctor before pin creation uses the portable contract because the
    # project pin is the output of this operation.
    doctor_path = system_dir / "scripts" / "doctor.py"
    doctor_result = "UNKNOWN"
    if doctor_path.exists():
        try:
            # Set PYTHONPATH to include system_dir for capability discovery
            env = os.environ.copy()
            env["PYTHONPATH"] = str(system_dir) + os.pathsep + env.get("PYTHONPATH", "")
            # Validate the extracted package before the project is classified as
            # installed. Running portable Doctor against project_root after
            # creating .p2p/system makes role inference report "installed" and
            # falsely rejects the package. The extracted archive itself is the
            # portable package root at this point.
            res = subprocess.run(
                [sys.executable, str(doctor_path), "--package", str(system_dir)],
                capture_output=True, text=True, env=env
            )
            doctor_result = "HEALTHY" if res.returncode == 0 else "UNHEALTHY"
        except Exception:
            doctor_result = "EXECUTION_FAILED"
    
    pin_module = _project_pin_module(temp_extract)
    pin = pin_module.build_pin(
        project_root=project_root,
        metadata_root=temp_extract,
        artifact_sha256=expected_sha,
        installation_mode=mode,
        rollback_source=str(snapshot_dir.relative_to(project_root)),
        managed_files=managed_files,
        doctor_result=doctor_result,
    )
    pin_module.write_pin(project_root, pin)
    if doctor_result == "HEALTHY":
        installed_result = subprocess.run(
            [sys.executable, str(doctor_path), "--root", str(project_root), "--role", "installed"],
            capture_output=True, text=True, env=env
        )
        if installed_result.returncode != 0:
            pin = pin_module.build_pin(
                project_root=project_root,
                metadata_root=temp_extract,
                artifact_sha256=expected_sha,
                installation_mode=mode,
                rollback_source=str(snapshot_dir.relative_to(project_root)),
                managed_files=managed_files,
                doctor_result="UNHEALTHY",
            )
            pin_module.write_pin(project_root, pin)
            shutil.rmtree(temp_extract)
            raise InstallerError("INSTALLED_UNVERIFIED / DOCTOR_UNHEALTHY")
        pin_module.validate_pin(
            project_root,
            metadata_root=system_dir,
            expected_artifact_sha256=expected_sha,
            expected_version=embedded_version,
        )
    else:
        shutil.rmtree(temp_extract)
        raise InstallerError(f"INSTALLED_UNVERIFIED / DOCTOR_UNHEALTHY (Result: {doctor_result})")

    shutil.rmtree(temp_extract)
    return pin

def rollback(project_root: Path) -> str:
    p2p_dir = project_root / ".p2p"
    pin_path = p2p_dir / "project-pin.json"
    if not pin_path.exists():
        raise InstallerError("No project pin found; cannot rollback.")
    
    pin = load_json(pin_path)
    rollback_rel = pin.get("rollback_source")
    if not rollback_rel:
        raise InstallerError("No rollback source defined in pin.")
    
    rollback_path = project_root / rollback_rel / "system_backup"
    system_dir = p2p_dir / "system"
    
    if not rollback_path.exists():
        if system_dir.exists():
            shutil.rmtree(system_dir)
        os.remove(pin_path)
        return "CLEARED (No prior backup found)"
    
    if system_dir.exists():
        shutil.rmtree(system_dir)
    
    shutil.copytree(rollback_path, system_dir)
    os.remove(pin_path)
    return f"RESTORED FROM {rollback_rel}"

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    
    inst = subparsers.add_parser("install")
    inst.add_argument("project_root")
    inst.add_argument("artifact")
    inst.add_argument("--sha", required=True)
    inst.add_argument("--version", required=True)

    pin_cmd = subparsers.add_parser("pin")
    pin_cmd.add_argument("project_root")
    pin_cmd.add_argument("--package-root", required=True)
    pin_cmd.add_argument("--artifact", required=True)
    pin_cmd.add_argument("--sha", required=True)
    pin_cmd.add_argument("--version", required=True)
    pin_cmd.add_argument("--mode", default="PACKAGED_PROJECT")
    pin_cmd.add_argument("--rollback-source", required=True)
    
    rb = subparsers.add_parser("rollback")
    rb.add_argument("project_root")
    
    args = parser.parse_args()
    
    try:
        if args.command == "install":
            res = install(Path(args.project_root), Path(args.artifact), args.sha, args.version)
            print(f"SUCCESS: Installed candidate {res['p2p_candidate_version']} to {args.project_root}")
            print(f"Verification: {res['verification_status']}")
        elif args.command == "rollback":
            res = rollback(Path(args.project_root))
            print(f"SUCCESS: Rollback complete - {res}")
        elif args.command == "pin":
            package_root = Path(args.package_root).resolve()
            artifact = Path(args.artifact).resolve()
            if not artifact.is_file() or sha256(artifact) != args.sha.lower():
                raise InstallerError("INSTALL_BLOCKED / ARTIFACT_SHA256_MISMATCH")
            module = _project_pin_module(package_root)
            system = Path(args.project_root).resolve() / ".p2p" / "system"
            managed = [path.relative_to(system).as_posix() for path in system.rglob("*") if path.is_file()]
            pin = module.build_pin(
                project_root=Path(args.project_root),
                metadata_root=package_root,
                artifact_sha256=args.sha,
                installation_mode=args.mode,
                rollback_source=args.rollback_source,
                managed_files=managed,
                doctor_result="HEALTHY",
            )
            module.write_pin(Path(args.project_root), pin)
            module.validate_pin(
                Path(args.project_root),
                metadata_root=system,
                expected_artifact_sha256=args.sha,
                expected_version=args.version,
            )
            print(json.dumps({"status": "PASS", "pin": str(Path(args.project_root).resolve() / ".p2p" / "project-pin.json"), "version": args.version}, ensure_ascii=False))
        else:
            parser.print_help()
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)
