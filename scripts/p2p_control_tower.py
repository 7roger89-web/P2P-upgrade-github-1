"""CLI for the provider-neutral durable Control Tower handoff boundary."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


REPO_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = REPO_ROOT / ".p2p" / "system"
for candidate in (str(REPO_ROOT), str(SYSTEM_ROOT), str(REPO_ROOT / "scripts")):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from p2p_capabilities.control_tower_handoff import (  # noqa: E402
    UNKNOWN,
    BindingError,
    ControlTower,
    ControlTowerHandoffError,
    SessionBinding,
    new_session_id,
    render_snapshot,
)


def _root(args: argparse.Namespace) -> Path:
    return Path(args.root).expanduser().resolve() if args.root else REPO_ROOT


def _print_result(result: dict[str, Any], *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
        return
    snapshot = result.get("snapshot")
    if isinstance(snapshot, dict):
        print(render_snapshot(snapshot))
    recommendation = result.get("recommendation")
    if isinstance(recommendation, dict):
        print("\nEXACT CHAT NAME")
        print(recommendation.get("CHAT_NAME", UNKNOWN))
        print("\nREADY-TO-PASTE PROMPT")
        print(recommendation.get("PROMPT", ""))
    reconciliation = result.get("reconciliation")
    if reconciliation is not None:
        print("\nINGEST RECONCILIATION")
        print(json.dumps(reconciliation, ensure_ascii=False, sort_keys=True, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Start, inspect, and ingest provider-neutral Control Tower sessions."
    )
    parser.add_argument("--root", help="project root; defaults to the repository containing this script")
    parser.add_argument("--json", action="store_true", dest="as_json", help="emit machine-readable JSON")
    parser.add_argument("--current-canonical-base-sha", default=UNKNOWN)
    parser.add_argument("--current-canonical-base-tree", default=UNKNOWN)
    sub = parser.add_subparsers(dest="command", required=True)

    start = sub.add_parser("start", help="register a bounded session and print its prompt")
    start.add_argument("--host", required=True)
    start.add_argument("--goal-id", required=True)
    start.add_argument("--goal", required=True)
    start.add_argument("--task-id", default=UNKNOWN)
    start.add_argument("--session-id")
    start.add_argument("--canonical-base-sha", default=UNKNOWN)
    start.add_argument("--canonical-base-tree", default=UNKNOWN)
    start.add_argument("--worktree", default=UNKNOWN)
    start.add_argument("--branch", default=UNKNOWN)
    start.add_argument("--acceptance-criterion", action="append", default=[])
    start.add_argument("--json", action="store_true", dest="as_json", default=argparse.SUPPRESS)

    snapshot = sub.add_parser("snapshot", help="show the reconciled Control Tower projection")
    snapshot.add_argument("--json", action="store_true", dest="as_json", default=argparse.SUPPRESS)

    ingest = sub.add_parser("ingest", help="ingest a complete executor response from a UTF-8 text file")
    ingest.add_argument("--response-file", required=True)
    ingest.add_argument("--json", action="store_true", dest="as_json", default=argparse.SUPPRESS)

    next_session = sub.add_parser(
        "next",
        help="derive and register the next safe task-state session without launching a host",
    )
    next_session.add_argument("--host", required=True)
    next_session.add_argument("--session-id")
    next_session.add_argument("--worktree", default=UNKNOWN)
    next_session.add_argument("--branch", default=UNKNOWN)
    next_session.add_argument("--json", action="store_true", dest="as_json", default=argparse.SUPPRESS)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        root = _root(args)
        tower = ControlTower(
            root,
            current_canonical_base_sha=args.current_canonical_base_sha,
            current_canonical_base_tree=args.current_canonical_base_tree,
        )
        if args.command == "start":
            binding = SessionBinding(
                session_id=args.session_id or new_session_id(args.host, args.goal_id, args.task_id),
                host=args.host,
                goal_id=args.goal_id,
                goal=args.goal,
            )
            result = tower.start_session(
                binding,
                task_id=args.task_id,
                canonical_base_sha=args.canonical_base_sha,
                canonical_base_tree=args.canonical_base_tree,
                worktree=args.worktree,
                branch=args.branch,
                acceptance_criteria=args.acceptance_criterion,
            )
        elif args.command == "snapshot":
            result = {"status": "PASS", "snapshot": tower.snapshot()}
        elif args.command == "ingest":
            response_path = Path(args.response_file).expanduser().resolve()
            result = tower.ingest_response(
                response_path.read_text(encoding="utf-8"),
                current_canonical_base_sha=args.current_canonical_base_sha,
                current_canonical_base_tree=args.current_canonical_base_tree,
            )
        elif args.command == "next":
            result = tower.start_next_session(
                args.host,
                session_id=args.session_id,
                worktree=args.worktree,
                branch=args.branch,
            )
        else:  # pragma: no cover - argparse constrains this branch.
            raise BindingError(f"UNSUPPORTED_COMMAND:{args.command}")
        _print_result(result, as_json=args.as_json)
        return 0
    except (ControlTowerHandoffError, OSError, UnicodeError) as exc:
        print(f"CONTROL_TOWER_ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
