#!/usr/bin/env python3
"""CLI for canonical identity and quorum invariants."""

import argparse
import json
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
for candidate in (HERE.parent / "src", HERE.parent, HERE):
    if (candidate / "p2p_uiux").is_dir() and str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from p2p_uiux.governance import load_manifest, validate_manifest, validate_quorum


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


def main(argv=None):
    parser = argparse.ArgumentParser(description="P2P canonical governance validator")
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate")
    validate.add_argument("--source", default=str(_default_source()))
    quorum = sub.add_parser("quorum")
    quorum.add_argument("--active", nargs="*", default=[])
    quorum.add_argument("--supporting", nargs="*", default=[])
    args = parser.parse_args(argv)
    if args.command == "validate":
        source = Path(args.source).resolve()
        result = validate_manifest(load_manifest(source / "p2p.manifest.json"), _profile_dir(source))
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["valid"] else 1
    result = validate_quorum(args.active or None, args.supporting)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["full_quorum_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
