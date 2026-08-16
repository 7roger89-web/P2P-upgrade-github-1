#!/usr/bin/env python3
"""Check source/package metadata drift without touching projects."""

import argparse
import json
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
for candidate in (HERE.parent / "src", HERE.parent, HERE):
    if (candidate / "p2p_uiux").is_dir() and str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from p2p_uiux.governance import load_manifest, validate_manifest


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


def check_source_drift(source_root):
    source_root = Path(source_root).resolve()
    manifest = load_manifest(source_root / "p2p.manifest.json")
    version = (source_root / "VERSION").read_text(encoding="utf-8").strip()
    if (source_root / "skills").exists():
        required_paths = [
            source_root / "skills" / "p2p-uiux" / "SKILL.md",
            source_root / ".codex" / "agents" / "p2p-aesthetica.toml",
            source_root / "src" / "p2p_uiux",
            source_root / "references" / "UPSTREAM-UI-UX-PRO-MAX-PROVENANCE.md",
        ]
    else:
        script_root = source_root / "scripts" if (source_root / "scripts").exists() else source_root
        required_paths = [script_root / "p2p_uiux.py", script_root / "p2p_router.py", _profile_dir(source_root) / "p2p-aesthetica.toml"]
    missing = [str(path.relative_to(source_root)) for path in required_paths if not path.exists()]
    errors = []
    if version != manifest.get("package_version"):
        errors.append({"code": "VERSION_MANIFEST_MISMATCH", "version": version, "manifest": manifest.get("package_version")})
    upstream = manifest.get("upstream", {})
    for field in ("repository", "commit", "license", "last_verified", "recheck_after"):
        if not upstream.get(field):
            errors.append({"code": "UPSTREAM_PROVENANCE_MISSING", "field": field})
    validation = validate_manifest(manifest, _profile_dir(source_root))
    errors.extend(validation["errors"])
    errors.extend({"code": "REQUIRED_PATH_MISSING", "path": path} for path in missing)
    return {"schema": "p2p-source-drift/1", "status": "PASS" if not errors else "FAIL", "errors": errors, "package_version": version}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Check P2P source metadata drift")
    parser.add_argument("--source", default=str(_default_source()))
    args = parser.parse_args(argv)
    result = check_source_drift(args.source)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
