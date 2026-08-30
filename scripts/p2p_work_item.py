#!/usr/bin/env python3
"""Foreground CLI for the bounded P2P work-item and handoff flow.

This command only reads/writes the existing execution ledger (the same store
the Control Tower and task state use). It never starts background work,
launches a host, selects a provider, executes an Owner Gate, or promotes,
merges, releases, or deploys anything.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = REPO_ROOT / ".p2p" / "system"
for candidate in (str(REPO_ROOT), str(SYSTEM_ROOT), str(REPO_ROOT / "scripts")):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from p2p_capabilities.control_tower_handoff import (  # noqa: E402
    UNKNOWN,
    BindingError,
    ControlTowerHandoffError,
    PacketParseError,
    ProjectionError,
)
from p2p_capabilities.work_item_handoff import (  # noqa: E402
    WorkItemHandoff,
    WorkItemHandoffError,
)


def _root(args: argparse.Namespace) -> Path:
    return Path(args.root).expanduser().resolve() if args.root else REPO_ROOT


def _print_result(result: dict[str, Any], *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
        return
    status = result.get("status", "PASS")
    print(f"STATUS: {status}")
    work_item = result.get("work_item")
    if isinstance(work_item, dict):
        print("WORK_ITEM_ID: " + str(work_item.get("WORK_ITEM_ID", UNKNOWN)))
        print("PROJECT: " + str(work_item.get("PROJECT", UNKNOWN)))
        print("WORKSTREAM: " + str(work_item.get("WORKSTREAM", UNKNOWN)))
        print("EXECUTOR: " + str(work_item.get("EXECUTOR", UNKNOWN)))
        print("LANE: " + str(work_item.get("LANE", UNKNOWN)))
        print("BASE_SHA: " + str(work_item.get("BASE_SHA", UNKNOWN)))
        print("BASE_TREE: " + str(work_item.get("BASE_TREE", UNKNOWN)))
        print("SESSION_ID: " + str(work_item.get("SESSION_ID", UNKNOWN)))
    for key, label in (
        ("work_item_id", "WORK_ITEM_ID"),
        ("work_item_status", "WORK_ITEM_STATUS"),
        ("verdict", "VERDICT"),
        ("next_gate", "NEXT_GATE"),
        ("canonical_relation", "CANONICAL_RELATION"),
        ("candidate_sha", "CANDIDATE_SHA"),
        ("candidate_tree", "CANDIDATE_TREE"),
        ("packet_fingerprint", "PACKET_FINGERPRINT"),
    ):
        if key in result:
            print(f"{label}: {result[key]}")
    queue = result.get("integration_queue")
    if isinstance(queue, dict):
        print("\nINTEGRATION_QUEUE_STATUS: " + str(queue.get("INTEGRATION_QUEUE_STATUS", UNKNOWN)))
        for entry in queue.get("ENTRIES", []):
            print(
                "  {position}. {work_item_id} [{project}/{workstream}] "
                "{status} -> {next_gate} (lane: {lane})".format(
                    position=entry.get("QUEUE_POSITION", "?"),
                    work_item_id=entry.get("WORK_ITEM_ID", UNKNOWN),
                    project=entry.get("PROJECT", UNKNOWN),
                    workstream=entry.get("WORKSTREAM", UNKNOWN),
                    status=entry.get("STATUS", UNKNOWN),
                    next_gate=entry.get("NEXT_GATE", UNKNOWN),
                    lane=entry.get("LANE", UNKNOWN),
                )
            )
    verify = result if result.get("schema", "").startswith("p2p-work-item-verify") else None
    if verify is not None:
        print("\nVERIFY:")
        for entry in verify.get("ENTRIES", []):
            reasons = ",".join(entry.get("REASONS", [])) or "-"
            print(
                "  {work_item_id}: {verify_status} (next gate: {next_gate}) [{reasons}]".format(
                    work_item_id=entry.get("WORK_ITEM_ID", UNKNOWN),
                    verify_status=entry.get("VERIFY_STATUS", UNKNOWN),
                    next_gate=entry.get("NEXT_GATE", UNKNOWN),
                    reasons=reasons,
                )
            )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Register work items, start executor lanes, ingest return packets, and project the integration queue."
    )
    parser.add_argument("--root", help="project root; defaults to the repository containing this script")
    parser.add_argument("--json", action="store_true", dest="as_json", help="emit machine-readable JSON")
    parser.add_argument("--current-canonical-base-sha", default=UNKNOWN)
    parser.add_argument("--current-canonical-base-tree", default=UNKNOWN)
    sub = parser.add_subparsers(dest="command", required=True)

    def _add_common(subparser: argparse.ArgumentParser) -> None:
        subparser.add_argument("--json", action="store_true", dest="as_json", default=argparse.SUPPRESS)
        subparser.add_argument("--current-canonical-base-sha", default=argparse.SUPPRESS)
        subparser.add_argument("--current-canonical-base-tree", default=argparse.SUPPRESS)

    register = sub.add_parser("register", help="register one minimum durable work-item identity")
    register.add_argument("--work-item-id", required=True)
    register.add_argument("--project", required=True)
    register.add_argument("--workstream", required=True)
    register.add_argument("--base-sha", required=True)
    register.add_argument("--base-tree", required=True)
    register.add_argument("--executor", required=True)
    register.add_argument("--scope", action="append", required=True)
    register.add_argument("--dependency", action="append", default=[])
    register.add_argument("--expected-output", required=True)
    register.add_argument("--session-id")
    _add_common(register)

    lane = sub.add_parser("lane", help="start the executor lane for one registered work item")
    lane.add_argument("--work-item-id", required=True)
    _add_common(lane)

    ret = sub.add_parser("return", help="ingest one executor return packet from a UTF-8 text file")
    ret.add_argument("--response-file", required=True)
    ret.add_argument("--candidate-sha", required=True)
    ret.add_argument("--candidate-tree", required=True)
    _add_common(ret)

    queue = sub.add_parser("queue", help="show the durable integration queue projection")
    _add_common(queue)

    verify = sub.add_parser("verify", help="run the deterministic verify step (preserves Owner Gates)")
    _add_common(verify)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        root = _root(args)
        handoff = WorkItemHandoff(
            root,
            current_canonical_base_sha=args.current_canonical_base_sha,
            current_canonical_base_tree=args.current_canonical_base_tree,
        )
        if args.command == "register":
            result = handoff.register_work_item(
                work_item_id=args.work_item_id,
                project=args.project,
                workstream=args.workstream,
                base_sha=args.base_sha,
                base_tree=args.base_tree,
                executor=args.executor,
                scope=args.scope,
                dependencies=args.dependency,
                expected_output=args.expected_output,
                session_id=args.session_id,
            )
        elif args.command == "lane":
            result = handoff.start_lane(args.work_item_id)
        elif args.command == "return":
            response_path = Path(args.response_file).expanduser().resolve()
            result = handoff.ingest_return(
                response_path.read_text(encoding="utf-8"),
                candidate_sha=args.candidate_sha,
                candidate_tree=args.candidate_tree,
                current_canonical_base_sha=args.current_canonical_base_sha,
                current_canonical_base_tree=args.current_canonical_base_tree,
            )
        elif args.command == "queue":
            result = handoff.integration_queue(
                current_canonical_base_sha=args.current_canonical_base_sha,
                current_canonical_base_tree=args.current_canonical_base_tree,
            )
            result = {"status": "PASS", **result}
        elif args.command == "verify":
            result = handoff.verify_integration_queue(
                current_canonical_base_sha=args.current_canonical_base_sha,
                current_canonical_base_tree=args.current_canonical_base_tree,
            )
            result = {"status": "PASS", **result}
        else:  # pragma: no cover - argparse constrains this branch.
            raise WorkItemHandoffError(f"UNSUPPORTED_COMMAND:{args.command}")
        _print_result(result, as_json=args.as_json)
        return 0
    except (
        WorkItemHandoffError,
        ControlTowerHandoffError,
        BindingError,
        PacketParseError,
        ProjectionError,
        OSError,
        UnicodeError,
    ) as exc:
        print(f"WORK_ITEM_HANDOFF_ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
