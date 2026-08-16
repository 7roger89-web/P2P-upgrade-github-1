#!/usr/bin/env python3
"""CLI for explainable adaptive P2P request routing."""

import argparse
import json
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
for candidate in (HERE.parent / "src", HERE.parent, HERE):
    if (candidate / "p2p_uiux").is_dir() and str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from p2p_uiux.router import classify_request


def main(argv=None):
    parser = argparse.ArgumentParser(description="P2P adaptive UI/UX router")
    sub = parser.add_subparsers(dest="command", required=True)
    route = sub.add_parser("route")
    route.add_argument("--request", required=True)
    route.add_argument("--profile-root")
    route.add_argument("--profile-available", choices=("true", "false"))
    args = parser.parse_args(argv)
    forced = None if args.profile_available is None else args.profile_available == "true"
    result = classify_request(args.request, profile_root=args.profile_root, force_profile_available=forced)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
