#!/usr/bin/env python3
"""Clone Vietnamese legal-tech research upstreams into separate directories.

This script deliberately does not vendor upstream code into P2P and does not
fetch large datasets. It only clones catalog entries explicitly marked
clone_enabled=true.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CATALOG = REPO_ROOT / "docs" / "research" / "legal-vn" / "upstreams.json"


def load_catalog(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if data.get("schema_version") != "p2p-legal-vn/upstreams/1":
        raise ValueError(f"Unsupported catalog schema: {data.get('schema_version')!r}")
    return data


def cloneable_sources(catalog: dict[str, Any], only: set[str] | None = None) -> list[dict[str, Any]]:
    sources = [
        item
        for item in catalog.get("sources", [])
        if item.get("kind") == "git_repository" and item.get("clone_enabled") is True
    ]
    if only:
        known = {item["id"] for item in sources}
        unknown = only - known
        if unknown:
            raise ValueError(f"Unknown or non-cloneable source id(s): {', '.join(sorted(unknown))}")
        sources = [item for item in sources if item["id"] in only]
    return sorted(sources, key=lambda item: (item.get("priority", 999), item["id"]))


def build_clone_command(source: dict[str, Any], target: Path) -> list[str]:
    return ["git", "clone", "--depth", "1", "--", source["url"], str(target)]


def ensure_target_is_safe(target: Path) -> None:
    if not target.exists():
        return
    if target.is_dir() and not any(target.iterdir()):
        return
    raise FileExistsError(f"Refusing to overwrite existing non-empty path: {target}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--dest", type=Path, default=REPO_ROOT.parent / "p2p-legal-upstreams")
    parser.add_argument("--only", action="append", default=[], help="Clone only this source id; repeatable")
    parser.add_argument("--list", action="store_true", help="List cloneable sources and exit")
    parser.add_argument("--dry-run", action="store_true", help="Print clone commands without executing them")
    args = parser.parse_args()

    catalog = load_catalog(args.catalog.resolve())
    sources = cloneable_sources(catalog, set(args.only) or None)

    if args.list:
        for source in sources:
            print(f"{source['id']}\t{source['url']}\t{source['reuse_policy']}")
        return 0

    destination = args.dest.resolve()
    destination.mkdir(parents=True, exist_ok=True)

    for source in sources:
        target = destination / source["local_dir"]
        ensure_target_is_safe(target)
        command = build_clone_command(source, target)
        print("+", " ".join(command))
        if args.dry_run:
            continue
        subprocess.run(command, check=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
