#!/usr/bin/env python3
"""Fail-closed high-confidence secret scan."""

import argparse
import json
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
for candidate in (HERE.parent / "src", HERE.parent, HERE):
    if (candidate / "p2p_uiux").is_dir() and str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from p2p_uiux.security import scan_tree


def _default_source():
    for candidate in (HERE, HERE.parent):
        if (candidate / "p2p.manifest.json").exists():
            return candidate
    return HERE.parent


def main(argv=None):
    parser = argparse.ArgumentParser(description="Scan P2P source for high-confidence secrets")
    parser.add_argument("--source", default=str(_default_source()))
    args = parser.parse_args(argv)
    findings = scan_tree(args.source)
    result = {"schema": "p2p-secret-scan/1", "status": "PASS" if not findings else "FAIL", "findings": findings}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not findings else 1


if __name__ == "__main__":
    raise SystemExit(main())
