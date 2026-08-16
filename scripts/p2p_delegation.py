#!/usr/bin/env python3
"""Beginner-safe inspection and execution boundary for C15 delegation.

This CLI intentionally has no child-spawn, shell, network, model, profile, or
provider controls.  A real host callback can be supplied by the supported
runtime API; the CLI can inspect the deterministic decision and will report a
delegated execution surface as unavailable rather than simulate one.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping


HERE = Path(__file__).resolve()
RUNTIME_ROOT: Path | None = None
for parent in HERE.parents:
    for candidate in (parent / ".p2p" / "system", parent / "runtime", parent):
        if (candidate / "p2p_capabilities" / "bounded_delegation.py").is_file():
            RUNTIME_ROOT = candidate
            break
    if RUNTIME_ROOT is not None:
        break
if RUNTIME_ROOT is None:
    raise RuntimeError("P2P bounded delegation runtime was not found")
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

from p2p_capabilities.bounded_delegation import (  # noqa: E402
    BoundedDelegationController,
    BoundedDelegationError,
    DelegationBudget,
    PermissionEnvelope,
)
from p2p_capabilities.task_state import TaskStateError  # noqa: E402


def _read_json(path: str | Path) -> Any:
    source = Path(path).expanduser().resolve()
    try:
        return json.loads(source.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise TaskStateError(f"JSON_READ_FAILED:{source}:{exc}") from exc


def _mapping(path: str | None, error: str) -> Mapping[str, Any] | None:
    if path is None:
        return None
    value = _read_json(path)
    if not isinstance(value, Mapping):
        raise TaskStateError(error)
    return value


def _root(args: argparse.Namespace) -> Path:
    return Path(args.root).expanduser().resolve()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="P2P bounded foreground delegation; deterministic and one-child maximum")
    parser.add_argument("--root", default=".", help="project root containing .p2p/state")
    sub = parser.add_subparsers(dest="command", required=True)

    decide = sub.add_parser("decide", help="show the internal DIRECT/DELEGATE/BLOCKED decision")
    decide.add_argument("--task-id")
    decide.add_argument("--task-size", choices=("TINY", "SMALL", "MODERATE", "LARGE"), default="MODERATE")
    decide.add_argument("--value-reason", action="append", default=[])
    decide.add_argument("--candidate-state")
    decide.add_argument("--parent-permissions")
    decide.add_argument("--child-permissions")
    decide.add_argument("--readiness")
    decide.add_argument("--permissions")
    decide.add_argument("--contexts")
    decide.add_argument("--requested-execution-class", default="HOST_DEFAULT")

    run = sub.add_parser("run", help="evaluate one bounded foreground run; no CLI child simulation is performed")
    run.add_argument("--task-id")
    run.add_argument("--task-size", choices=("TINY", "SMALL", "MODERATE", "LARGE"), default="MODERATE")
    run.add_argument("--value-reason", action="append", default=[])
    run.add_argument("--candidate-state")
    run.add_argument("--parent-permissions")
    run.add_argument("--child-permissions")
    run.add_argument("--readiness")
    run.add_argument("--permissions")
    run.add_argument("--contexts")
    run.add_argument("--requested-execution-class", default="HOST_DEFAULT")

    return parser


def _common_kwargs(args: argparse.Namespace) -> dict[str, Any]:
    candidate_state = _read_json(args.candidate_state) if args.candidate_state else None
    parent_permissions = PermissionEnvelope.from_value(_mapping(args.parent_permissions, "PARENT_PERMISSIONS_OBJECT_REQUIRED")) if args.parent_permissions else None
    child_permissions = PermissionEnvelope.from_value(_mapping(args.child_permissions, "CHILD_PERMISSIONS_OBJECT_REQUIRED")) if args.child_permissions else None
    readiness = _mapping(args.readiness, "READINESS_OBJECT_REQUIRED")
    permission_state = _mapping(args.permissions, "PERMISSIONS_OBJECT_REQUIRED")
    context_state = _mapping(args.contexts, "CONTEXTS_OBJECT_REQUIRED")
    return {
        "task_id": args.task_id,
        "task_size": args.task_size,
        "value_reasons": tuple(args.value_reason),
        "candidate_state": candidate_state,
        "parent_permissions": parent_permissions,
        "child_permissions": child_permissions,
        "capability_readiness": readiness or {},
        "permission_state": permission_state or {},
        "context_state": context_state or {},
        "requested_execution_class": args.requested_execution_class,
        "budget": DelegationBudget(),
    }


def _write(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    controller = BoundedDelegationController(_root(args))
    try:
        values = _common_kwargs(args)
        if args.command == "decide":
            task_id = values.pop("task_id")
            _write(controller.decide(task_id=task_id, **values))
            return 0
        if args.command == "run":
            task_id = values.pop("task_id")
            _write(controller.execute(task_id=task_id, **values))
            return 0
        raise TaskStateError("UNKNOWN_COMMAND")
    except (TaskStateError, BoundedDelegationError) as exc:
        _write(
            {
                "status": "BLOCKED",
                "strategy": "BLOCKED",
                "reason": str(exc),
                "automatic_start": False,
                "background_execution": False,
                "parallel_execution": False,
                "child_delegation_allowed": False,
            }
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
