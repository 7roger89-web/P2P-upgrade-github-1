#!/usr/bin/env python3
"""Fail-closed package health check."""

import argparse
import hashlib
import json
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
for candidate in (HERE.parent / "src", HERE.parent, HERE):
    if (candidate / "p2p_uiux").is_dir() and str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from p2p_uiux.governance import load_manifest, validate_manifest
from p2p_uiux.security import scan_tree


def _default_source():
    for candidate in (HERE, HERE.parent):
        if (candidate / "p2p.manifest.json").exists():
            return candidate
    return HERE.parent


def _profile_dir(source):
    source = Path(source)
    for candidate in (source / ".codex" / "agents", source.parent.parent / ".codex" / "agents", source.parent / ".codex" / "agents"):
        if candidate.exists():
            return candidate
    return source / ".codex" / "agents"


def _sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_doctor(source_root):
    source_root = Path(source_root).resolve()
    errors = []
    manifest_path = source_root / "p2p.manifest.json"
    try:
        manifest = load_manifest(manifest_path)
        validation = validate_manifest(manifest, _profile_dir(source_root))
        errors.extend(validation["errors"])
    except Exception as exc:
        manifest = {}
        errors.append({"code": "MANIFEST_READ_FAILED", "reason": str(exc)})
    version = (source_root / "VERSION").read_text(encoding="utf-8").strip() if (source_root / "VERSION").exists() else ""
    if version != manifest.get("package_version"):
        errors.append({"code": "VERSION_MANIFEST_MISMATCH", "version": version, "manifest": manifest.get("package_version")})
    if (source_root / "skills").exists():
        required = ("skills/p2p/SKILL.md", "skills/p2p-uiux/SKILL.md", ".codex/agents/p2p-aesthetica.toml", "scripts/p2p_uiux.py")
    elif (source_root / "scripts").exists():
        namespaced = (source_root / "scripts" / "p2p_uiux_doctor.py").exists()
        required = (
            ("scripts/p2p_uiux.py", "scripts/p2p_router.py", "scripts/p2p_uiux_governance.py", "scripts/p2p_uiux_eval.py", "scripts/p2p_uiux_eval_impl.py", "scripts/p2p_uiux_doctor.py", "scripts/p2p_uiux_drift_check.py", "scripts/p2p_uiux_secret_scan.py")
            if namespaced
            else ("scripts/p2p_uiux.py", "scripts/p2p_router.py", "scripts/p2p_governance.py")
        )
    else:
        required = ("p2p_uiux.py", "p2p_router.py", "p2p_governance.py")
    for relative in required:
        if not (source_root / relative).exists():
            errors.append({"code": "REQUIRED_PATH_MISSING", "path": relative})
    findings = scan_tree(source_root)
    if findings:
        errors.append({"code": "SECRET_FINDINGS", "findings": findings})
    package_results = []
    dist = source_root / "dist"
    for checksum in sorted(dist.glob("*.zip.sha256")) if dist.exists() else []:
        line = checksum.read_text(encoding="utf-8").strip().split()
        archive = checksum.with_suffix("")
        if len(line) != 2 or not archive.exists() or _sha256(archive) != line[0]:
            errors.append({"code": "PACKAGE_CHECKSUM_INVALID", "checksum": str(checksum)})
        else:
            package_results.append({"archive": str(archive), "sha256": line[0]})
    return {"schema": "p2p-doctor/1", "status": "PASS" if not errors else "FAIL", "package_version": version, "package_results": package_results, "errors": errors}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Check P2P UI/UX capability health")
    parser.add_argument("--source", default=str(_default_source()))
    args = parser.parse_args(argv)
    result = run_doctor(args.source)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
