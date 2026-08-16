#!/usr/bin/env python3
"""CLI for the reusable p2p-uiux capability."""

import argparse
import json
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
for candidate in (HERE.parent / "src", HERE.parent, HERE):
    if (candidate / "p2p_uiux").is_dir() and str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from p2p_uiux.accessibility import audit_design_system
from p2p_uiux.contracts import generate_contract, validate_contract, write_contract
from p2p_uiux.design_system import generate_design_system, write_design_system
from p2p_uiux.drift import compare_design_systems
from p2p_uiux.recommendation import build_recommendation
from p2p_uiux.design_intelligence import design_intelligence_route


def _read_json(value):
    if isinstance(value, str) and len(value) <= 4096:
        try:
            path = Path(value)
            if path.exists() and path.is_file():
                with path.open("r", encoding="utf-8") as handle:
                    return json.load(handle)
        except (OSError, ValueError):
            pass
    return json.loads(value)


def _print(value):
    print(json.dumps(value, indent=2, sort_keys=True))


def main(argv=None):
    parser = argparse.ArgumentParser(description="P2P UI/UX design intelligence and artifact tooling")
    sub = parser.add_subparsers(dest="command", required=True)

    recommend = sub.add_parser("recommend")
    recommend.add_argument("--input", required=True, help="JSON file or inline JSON context")

    ds = sub.add_parser("design-system")
    ds.add_argument("--input", required=True)
    ds.add_argument("--project", required=True)
    ds.add_argument("--approve", action="store_true")
    ds.add_argument("--approved-by")
    ds.add_argument("--force", action="store_true")

    contract = sub.add_parser("contract")
    contract.add_argument("--input", required=True)
    contract.add_argument("--project", required=True)
    contract.add_argument("--scope", choices=("small", "large"), default="large")
    contract.add_argument("--force", action="store_true")

    drift = sub.add_parser("drift")
    drift.add_argument("--baseline", required=True)
    drift.add_argument("--candidate", required=True)

    a11y = sub.add_parser("a11y")
    a11y.add_argument("--file", required=True)

    intelligence = sub.add_parser("design-intelligence")
    intelligence.add_argument("--input", required=True, help="JSON file or inline {request, context} object")

    args = parser.parse_args(argv)
    if args.command == "recommend":
        _print(build_recommendation(_read_json(args.input)))
        return 0
    if args.command == "design-system":
        artifact = generate_design_system(_read_json(args.input), approved=args.approve, approved_by=args.approved_by)
        _print(write_design_system(args.project, artifact, force=args.force))
        return 0
    if args.command == "contract":
        artifact = generate_contract(_read_json(args.input), scope=args.scope)
        _print({"path": write_contract(args.project, artifact, force=args.force), "validation": validate_contract(artifact)})
        return 0
    if args.command == "drift":
        result = compare_design_systems(args.baseline, args.candidate)
        _print(result)
        return 0 if result.get("gate_pass") else 1
    if args.command == "a11y":
        result = audit_design_system(args.file)
        _print(result)
        return 0 if result.get("status") == "PASS" else 1
    if args.command == "design-intelligence":
        value = _read_json(args.input)
        if isinstance(value, dict):
            request = value.get("request", "")
            context = value.get("context", {})
        else:
            request = value
            context = {}
        result = design_intelligence_route(request, context)
        _print(result)
        return 0 if result.get("status") in {"READY", "NOT_APPLICABLE"} else 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
