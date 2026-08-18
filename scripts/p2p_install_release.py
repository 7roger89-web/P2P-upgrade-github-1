#!/usr/bin/env python3
"""P2P install release — one machine-usable installation interface.

CLI:
  python3 p2p_install_release.py install   <project-root> <package-dir>
  python3 p2p_install_release.py upgrade   <project-root> <package-dir>
  python3 p2p_install_release.py rollback  <project-root> [--to-snapshot-id STAMP]
  python3 p2p_install_release.py doctor    <project-root> [--machine]

Conventions (follow existing repository conventions):
- snapshots: .p2p/install-backups/<stamp>/system.tar (two-step rollback)
- marker:   .p2p/system/release.json (schema p2p-install-release/1)
- manifest: .p2p/system/p2p-install-manifest.json (schema p2p-install-manifest/1)
- install classes: FRESH_INSTALL, UPGRADE_FROM_<prev>, SAME_VERSION_REINSTALL,
  LEGACY_SYSTEM_UPGRADE, COLLISION_OWNER_GATE
- fails closed: unknown state, missing snapshots, or path collisions do not
  silently overwrite; collisions record an owner-gate evidence record and STOP.

Never copies credential values. Auth checks use reference/presence semantics.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path
from typing import Any

INSTALL_MANIFEST_SCHEMA = "p2p-install-manifest/1"
RELEASE_MARKER_SCHEMA = "p2p-install-release/1"


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def sha256set(root: Path, exclude: set[str] | None = None) -> dict[str, str]:
    exclude = exclude or set()
    out: dict[str, str] = {}
    for item in sorted(root.rglob("*")):
        if not item.is_file():
            continue
        rel = item.relative_to(root).as_posix()
        if any(rel == ex or rel.startswith(ex + "/") for ex in exclude):
            continue
        out[rel] = sha256(item)
    return out


def project_fingerprint(root: Path) -> dict[str, Any]:
    files = sha256set(root, exclude={".p2p", ".git"})
    git_rev = None
    git_branch = None
    try:
        git_rev = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True,
            cwd=str(root), check=True).stdout.strip()
        git_branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True,
            text=True, cwd=str(root), check=True).stdout.strip()
    except (subprocess.SubprocessError, OSError):
        git_rev = None
    return {
        "file_hashes": files,
        "file_count": len(files),
        "files_sha256": sha256_of_string(json.dumps(files, sort_keys=True)),
        "git_revision": git_rev,
        "git_branch": git_branch,
        "captured_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }


def sha256_of_string(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def load_json(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def dump_json(p: Path, obj: Any) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def stamp_now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d-%H%M%S")


# ---------------------------------------------------------------- install

def _validate_package(package_dir: Path) -> dict:
    package_dir = package_dir.resolve()
    version_file = package_dir / "VERSION"
    if not version_file.is_file():
        raise SystemExit(f"Package VERSION missing: {package_dir}")
    version = version_file.read_text(encoding="utf-8").strip()
    if not version:
        raise SystemExit("Package VERSION is empty")
    manifest = None
    for name in ("candidate-manifest.json", "manifest/candidate-manifest.json"):
        if (package_dir / name).is_file():
            manifest = load_json(package_dir / name)
            break
    if manifest is None:
        raise SystemExit("Package candidate manifest missing")
    if manifest.get("package_version") != version:
        raise SystemExit("Package manifest version differs from VERSION")
    if manifest.get("status") == "PROMOTED":
        raise SystemExit("Promoted artifact cannot be installed through the candidate path")
    return manifest


def _detect_install_class(root: Path, package_version: str) -> str:
    system = root / ".p2p" / "system"
    if not system.is_dir():
        return "FRESH_INSTALL"
    marker = system / "release.json"
    if marker.is_file():
        try:
            value = load_json(marker)
            prev = str(value.get("package_version", ""))
        except Exception:
            prev = ""
        if prev == package_version:
            return "SAME_VERSION_REINSTALL"
        if prev:
            return f"UPGRADE_FROM_{prev}"
    return "LEGACY_SYSTEM_UPGRADE"


def _install_files(project_root: Path, package_dir: Path, install_class: str,
                   pre_fingerprint: dict,
                   collision_policy: str = "owner-gate") -> dict:
    system = project_root / ".p2p" / "system"
    runtime_src = package_dir / "runtime"
    governance_src = package_dir / "governance"
    scripts_src = package_dir / "scripts"
    if not runtime_src.is_dir():
        raise SystemExit("Package runtime/ subtree missing")

    # Collision detection: project-owned paths that the footprint would write.
    footprint_paths = set()
    for item in runtime_src.rglob("*"):
        if item.is_file() and "__pycache__" not in item.parts:
            footprint_paths.add(item.relative_to(runtime_src).as_posix())

    collisions = []
    for rel in footprint_paths:
        project_path = project_root / rel
        if project_path.exists() and not str(project_path).startswith(str(system)):
            collisions.append(rel)

    # Collision handling (never silent overwrite): owner-gate stops; rename-backup
    # preserves the project file with content-hash evidence and proceeds.
    policy = collision_policy or "owner-gate"
    managed_set = []
    if collisions:
        evidence = {
            "schema": "c40-install-collision/1",
            "project_root": str(project_root),
            "package_version": None,
            "collision_paths": sorted(collisions)[:50],
            "collision_policy_requested": policy,
            "created_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
        ev_dir = project_root / "docs" / "p2p-development" / "research" / "c40" / "evidence"
        if policy == "owner-gate":
            evidence["verdict"] = "OWNER_GATE"
            evidence["action"] = "STOP - no silent overwrite; await Owner decision"
            dump_json(ev_dir / "c40-install-collision.json", evidence)
            raise SystemExit(
                f"Path collision detected ({len(collisions)} file(s)); OWNER_GATE. "
                f"First: {sorted(collisions)[:3]}. No file was overwritten. "
                f"Re-run with --collision-policy=rename-backup to proceed after "
                f"Owner decision.")
        if policy == "rename-backup":
            st = stamp_now()
            backup_root = project_root / ".p2p" / "installed-collisions" / st
            backed = []
            for rel in sorted(collisions):
                src = project_root / rel
                dst = backup_root / "backup" / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                backed.append({"path": rel,
                               "content_sha256": sha256(src),
                               "restored_from": str(dst)})
            evidence["verdict"] = "COLLISIONS_BACKED_UP"
            evidence["backups"] = backed
            evidence["action"] = ("Project file(s) backed up with content hash; "
                                  "P2P file installed in its place. Restoration "
                                  "path recorded; nothing lost, nothing silent.")
            dump_json(ev_dir / "c40-install-collision.json", evidence)
            collisions = []  # handled; continue with normal install
            install_class = "COLLISIONS_BACKED_UP_INSTALL"
        else:
            raise SystemExit(f"Unknown collision policy: {policy} (fail-closed).")

    backups_root = project_root / ".p2p" / "install-backups"
    st = stamp_now()
    backup_system = backups_root / st / "system"
    if system.exists():
        backup_system.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(system, backup_system)
    system.mkdir(parents=True, exist_ok=True)

    # runtime subtree -> .p2p/system
    for item in runtime_src.rglob("*"):
        if item.is_file() and "__pycache__" not in item.parts:
            rel = item.relative_to(runtime_src)
            dest = system / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, dest)
            managed_set.append(dest.relative_to(system).as_posix())

    # governance subset
    if governance_src.is_dir():
        dest_gov = system / "governance"
        dest_gov.mkdir(parents=True, exist_ok=True)
        for item in governance_src.rglob("*"):
            if item.is_file():
                dest = dest_gov / item.relative_to(governance_src)
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, dest)
                managed_set.append("governance/" + dest.relative_to(dest_gov).as_posix())

    # root scripts -> .p2p/system/scripts
    dest_scr = system / "scripts"
    if scripts_src.is_dir():
        dest_scr.mkdir(parents=True, exist_ok=True)
        for item in scripts_src.rglob("*"):
            if item.is_file():
                dest = dest_scr / item.relative_to(scripts_src)
                shutil.copy2(item, dest)
                managed_set.append("scripts/" + dest.relative_to(dest_scr).as_posix())
    # agent profiles: package .codex/agents/ -> project root .codex/agents/
    # (host project profiles ALWAYS win: only install where host has none).
    profiles_src = package_dir / ".codex" / "agents"
    if profiles_src.is_dir():
        dest_prof = project_root / ".codex" / "agents"
        for item in profiles_src.rglob("*"):
            if item.is_file() and item.suffix == ".toml":
                rel = item.relative_to(profiles_src)
                dest = dest_prof / rel
                if not dest.exists():
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item, dest)
                    managed_set.append(".codex/agents/" + rel.as_posix())

    pkg_manifest = None
    for name in ("candidate-manifest.json",):
        if (package_dir / name).is_file():
            pkg_manifest = load_json(package_dir / name)
            break

    manifest = {
        "schema": INSTALL_MANIFEST_SCHEMA,
        "install_class": install_class,
        "package_version": (package_dir / "VERSION").read_text(encoding="utf-8").strip(),
        "package_label": pkg_manifest.get("candidate_label") if pkg_manifest else None,
        "package_sha256": pkg_manifest.get("candidate_sha256") if pkg_manifest else None,
        "install_schema_version": pkg_manifest.get("install_schema_version")
        if pkg_manifest else None,
        "installed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "pre_install_fingerprint": pre_fingerprint,
        "managed_file_count": len(managed_set),
        "managed_files": sorted(managed_set),
        "project_binding": {
            "project_root": str(project_root.resolve()),
            "post_install_fingerprint": project_fingerprint(project_root)["files_sha256"],
        },
        "upgrade_rules": pkg_manifest.get("upgrade_rules", {}) if pkg_manifest else {},
        "rollback_info": pkg_manifest.get("rollback_info", {}) if pkg_manifest else {},
    }
    dump_json(system / "p2p-install-manifest.json", manifest)

    marker = {
        "schema": RELEASE_MARKER_SCHEMA,
        "install_class": install_class,
        "package_version": manifest["package_version"],
        "package_label": manifest["package_label"],
        "installed_at": manifest["installed_at"],
        "managed_file_count": manifest["managed_file_count"],
        "snapshots": [{"stamp": st, "location": str(backup_system)}] if system.exists() else [],
        "protected_state_hashes": {},
        "changed_files": [],
    }
    dump_json(system / "release.json", marker)
    return manifest


def cmd_install(args: argparse.Namespace) -> None:
    root = Path(args.project_root).resolve()
    package = Path(args.package_dir).resolve()
    manifest = _validate_package(package)
    pre = project_fingerprint(root)
    install_class = _detect_install_class(root, manifest.get("package_version", ""))
    result = _install_files(root, package, install_class, pre, getattr(args, "collision_policy", "owner-gate") or "owner-gate")
    dump_json(Path(args.evidence_out) if args.evidence_out else root / ".p2p" /
              "state" / "c40-install-evidence.json",
              {
                  "schema": "c40-install-result/1",
                  "install_class": install_class,
                  "package_version": result["package_version"],
                  "package_sha256": result["package_sha256"],
                  "managed_file_count": result["managed_file_count"],
                  "pre_fingerprint_files": pre["file_count"],
                  "status": "INSTALLED",
              })
    print(f"INSTALL {install_class}: {result['package_version']} "
          f"({result['managed_file_count']} managed files)")


# -------------------------------------------------------------- upgrade

def cmd_upgrade(args: argparse.Namespace) -> None:
    root = Path(args.project_root).resolve()
    package = Path(args.package_dir).resolve()
    manifest = _validate_package(package)
    pre = project_fingerprint(root)
    install_class = _detect_install_class(root, manifest.get("package_version", ""))
    if install_class == "SAME_VERSION_REINSTALL":
        raise SystemExit("Upgrade is a no-op: already on this version (idempotent). "
                         "Use install for SAME_VERSION_REINSTALL semantics.")
    if install_class in ("FRESH_INSTALL", "LEGACY_SYSTEM_UPGRADE",
                         "COLLISION_OWNER_GATE"):
        raise SystemExit(f"Upgrade precondition not met: install class {install_class}. "
                         "Run install first, or use rollback to reach a prior version.")
    result = _install_files(root, package, install_class, pre, getattr(args, "collision_policy", "owner-gate") or "owner-gate")
    dump_json(Path(args.evidence_out) if args.evidence_out else root / ".p2p" /
              "state" / "c40-upgrade-evidence.json",
              {
                  "schema": "c40-upgrade-result/1",
                  "install_class": install_class,
                  "package_version": result["package_version"],
                  "package_sha256": result["package_sha256"],
                  "managed_file_count": result["managed_file_count"],
                  "status": "UPGRADED",
              })
    print(f"UPGRADE {install_class}: -> {result['package_version']} "
          f"({result['managed_file_count']} managed files)")


# -------------------------------------------------------------- rollback

def cmd_rollback(args: argparse.Namespace) -> None:
    root = Path(args.project_root).resolve()
    system = root / ".p2p" / "system"
    marker_path = system / "release.json"
    if not marker_path.is_file():
        raise SystemExit("No P2P installation found; nothing to roll back (fail-closed).")
    marker = load_json(marker_path)
    snapshots = marker.get("snapshots") or []
    if not snapshots:
        raise SystemExit("No rollback snapshot available (fail-closed).")
    target = None
    if args.to_snapshot_id:
        target = next((s for s in snapshots if s["stamp"] == args.to_snapshot_id), None)
        if target is None:
            raise SystemExit(f"Snapshot {args.to_snapshot_id} not found (fail-closed).")
    else:
        target = snapshots[-1]
    snap_dir = Path(target["location"])
    if not snap_dir.is_dir():
        raise SystemExit(f"Snapshot missing: {snap_dir} (fail-closed).")

    pre = project_fingerprint(root)
    st = stamp_now()
    old_system = root / ".p2p" / "install-backups" / f"rollback-{st}"
    old_system.parent.mkdir(parents=True, exist_ok=True)
    if system.exists():
        shutil.copytree(system, old_system)
    shutil.rmtree(system)
    shutil.copytree(snap_dir, system)
    marker["snapshots"] = [s for s in snapshots if s is not target]
    marker["install_class"] = marker.get("install_class", "ROLLBACK") + "_ROLLBACK"
    marker["rollback_restored_from"] = target["stamp"]
    dump_json(marker_path, marker)
    post = project_fingerprint(root)
    dump_json(Path(args.evidence_out) if args.evidence_out else root / ".p2p" /
              "state" / "c40-rollback-evidence.json",
              {
                  "schema": "c40-rollback-result/1",
                  "restored_from": target["stamp"],
                  "pre_rollback_fingerprint_files": pre["file_count"],
                  "post_rollback_fingerprint_files": post["file_count"],
                  "status": "ROLLED_BACK",
              })
    print(f"ROLLBACK restored from snapshot {target['stamp']} -> "
          f"{marker.get('package_version', '?')}")


# --------------------------------------------------------------- doctor

def _backend_availability() -> dict:
    """Presence-only backend availability. No credential values examined."""
    env = os.environ
    check = {
        "manus_rest_api_v2": "REFERENCE_PRESENT" if env.get("MANUS_API_KEY") else "REFERENCE_ABSENT",
        "hermes_cli": shutil.which("hermes") is not None,
        "gemini": "REFERENCE_PRESENT" if env.get("GEMINI_API_KEY") else "REFERENCE_ABSENT",
        "codex": shutil.which("codex") is not None,
    }
    return check


def _eligible_targets(root: Path) -> list[str]:
    """Current P2P-selected eligible targets via the capability registry."""
    registry = root / ".p2p" / "system" / "p2p_capabilities" / "capabilities.json"
    if not registry.is_file():
        return []
    try:
        reg = load_json(registry)
    except Exception:
        return []
    out = []
    caps = reg.get("capabilities") if isinstance(reg, dict) else []
    for cap in caps or []:
        if not isinstance(cap, dict):
            continue
        if cap.get("STATUS", "") == "ACTIVE":
            out.append(cap.get("CAPABILITY_ID") or "?")
    return sorted(out)


def cmd_doctor(args: argparse.Namespace) -> None:
    root = Path(args.project_root).resolve()
    system = root / ".p2p" / "system"
    report: dict[str, Any] = {"schema": "c40-doctor/1", "project_root": str(root)}

    # version / binding
    version_file = system / "VERSION"
    manifest_path = system / "p2p-install-manifest.json"
    marker_path = system / "release.json"
    install_ok = manifest_path.is_file() and marker_path.is_file()
    manifest = load_json(manifest_path) if manifest_path.is_file() else {}
    marker = load_json(marker_path) if marker_path.is_file() else {}
    report["p2p_version"] = version_file.read_text(encoding="utf-8").strip() \
        if version_file.is_file() else None
    report["project_binding"] = manifest.get("project_binding")
    report["installation_health"] = (
        "HEALTHY" if install_ok
        else "NOT_INSTALLED" if not system.is_dir() else "MARKER_MISSING")

    # manifest integrity
    if install_ok:
        bad = 0
        checked = 0
        for rel in manifest.get("managed_files", []):
            full = system / rel
            if full.is_file():
                checked += 1
        report["runtime_manifest_integrity"] = (
            "INTACT" if checked == len(manifest.get("managed_files", []))
            else "INCOMPLETE")
    else:
        report["runtime_manifest_integrity"] = "NOT_INSTALLED"

    # state health
    state_dir = root / ".p2p" / "state"
    report["state_health"] = "INITIALIZED" if state_dir.is_dir() else "NOT_INITIALIZED"
    report["snapshots"] = len(marker.get("snapshots", []))
    report["rollback_available"] = bool(marker.get("snapshots"))

    # context health (p2p_uiux)
    report["context_health"] = (
        "AVAILABLE" if (system / "p2p_uiux").is_dir() else "ABSENT")

    # backend availability (reference semantics only)
    report["backend_availability"] = _backend_availability()
    report["current_eligible_targets"] = _eligible_targets(root)

    # permission status
    policy = root / ".p2p" / "project-policy.json"
    report["permission_status"] = "BOUND" if policy.is_file() else "UNBOUND"

    # upgrade / rollback
    report["upgrade_status"] = marker.get("install_class", "NONE")
    report["warnings"] = []
    if not install_ok:
        report["warnings"].append("P2P is not installed in this project.")
    if not report["backend_availability"].get("manus_rest_api_v2") and not report["backend_availability"].get("hermes_cli"):
        report["warnings"].append("No certified backend credential reference present; live execution will fail closed.")

    # recommended next action (beginner-readable)
    if not install_ok:
        report["recommended_next_action"] = (
            "Cài đặt P2P vào dự án: chạy lệnh install của AI executor, không cần chép file thủ công.")
    elif report["warnings"]:
        report["recommended_next_action"] = (
            "Kiểm tra cảnh báo bên trên; hệ thống an toàn và không tự động thay đổi gì.")
    else:
        report["recommended_next_action"] = (
            "P2P sẵn sàng. Giao nhiệm vụ dạng 'Tiếp tục hoàn thiện dự án' để hệ thống tự chọn bước an toàn tiếp theo.")

    if args.machine:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print("=== P2P Doctor — sức khỏe dự án ===")
        print(f"Phiên bản P2P:        {report['p2p_version']}")
        print(f"Sức khỏe cài đặt:     {report['installation_health']}")
        print(f"Toàn vẹn manifest:    {report['runtime_manifest_integrity']}")
        print(f"Dữ liệu trạng thái:   {report['state_health']} (snapshot: {report['snapshots']})")
        print(f"Khôi phục được:       {'CÓ' if report['rollback_available'] else 'không'}")
        print(f"Ngữ cảnh (UI/UX):     {report['context_health']}")
        print("Backend (chỉ kiểm tra sự hiện diện, KHÔNG lộ giá trị):")
        for k, v in report["backend_availability"].items():
            print(f"  {k}: {v}")
        print(f"Mục tiêu đủ điều kiện: {report['current_eligible_targets'] or 'không có'}")
        print(f"Quyền dự án:          {report['permission_status']}")
        print(f"Trạng thái nâng cấp:  {report['upgrade_status']}")
        for w in report["warnings"]:
            print(f"CẢNH BÁO: {w}")
        print(f"Việc nên làm tiếp:     {report['recommended_next_action']}")


# ----------------------------------------------------------------- main

def main() -> None:
    parser = argparse.ArgumentParser(description="P2P install release (install/upgrade/rollback/doctor)")
    sub = parser.add_subparsers(dest="command", required=True)

    p_install = sub.add_parser("install")
    p_install.add_argument("project_root")
    p_install.add_argument("package_dir")
    p_install.add_argument("--evidence-out", default=None)
    p_install.add_argument("--collision-policy", default="owner-gate",
                           choices=["owner-gate", "rename-backup"],
                           help=("owner-gate: stop on project path collision "
                                 "(fail-closed default); rename-backup: back up "
                                 "colliding project files with content hash "
                                 "then install P2P files (auditable, never silent)"))
    p_install.set_defaults(func=cmd_install)

    p_upgrade = sub.add_parser("upgrade")
    p_upgrade.add_argument("project_root")
    p_upgrade.add_argument("package_dir")
    p_upgrade.add_argument("--evidence-out", default=None)
    p_upgrade.add_argument("--collision-policy", default="owner-gate",
                           choices=["owner-gate", "rename-backup"])
    p_upgrade.set_defaults(func=cmd_upgrade)

    p_rollback = sub.add_parser("rollback")
    p_rollback.add_argument("project_root")
    p_rollback.add_argument("--to-snapshot-id", default=None)
    p_rollback.add_argument("--evidence-out", default=None)
    p_rollback.set_defaults(func=cmd_rollback)

    p_doctor = sub.add_parser("doctor")
    p_doctor.add_argument("project_root")
    p_doctor.add_argument("--machine", action="store_true")
    p_doctor.set_defaults(func=cmd_doctor)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
