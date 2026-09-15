#!/usr/bin/env python3
"""Packaged P2P native-goal/worktree bridge.

This script is shipped through the existing `p2p` skill directory. It is a
thin CLI over canonical runtime modules; it creates no parallel state.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve()
RUNTIME_ROOT: Path | None = None
PROJECT_ROOT: Path | None = None
for parent in HERE.parents:
    candidate = parent / ".p2p" / "system"
    if (
        (candidate / "p2p_capabilities" / "native_goal_bridge.py").is_file()
        and (candidate / "p2p_capabilities" / "worktree_evidence.py").is_file()
    ):
        RUNTIME_ROOT = candidate
        PROJECT_ROOT = parent
        break
if RUNTIME_ROOT is None or PROJECT_ROOT is None:
    raise RuntimeError("P2P native-goal runtime was not found from packaged skill")
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

from p2p_capabilities.native_goal_bridge import (  # noqa: E402
    CODEX_CLI,
    CLAUDE_CODE,
    NativeGoalBridgeError,
    build_native_goal_projection,
)
from p2p_capabilities.worktree_evidence import (  # noqa: E402
    SCHEMA as WORKTREE_SCHEMA,
    WorktreeEvidenceError,
    complete_worktree_summary,
    deliverable_evidence,
)


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise NativeGoalBridgeError(f"JSON_READ_FAILED:{path}:{exc}") from exc
    if not isinstance(value, dict):
        raise NativeGoalBridgeError(f"JSON_OBJECT_REQUIRED:{path}")
    return value


def _print(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2))


def _goal(args: argparse.Namespace, root: Path) -> int:
    try:
        result = build_native_goal_projection(
            args.host,
            _read_json(root / args.goal_state),
            _read_json(root / args.task_state),
            baseline_ref=args.baseline,
        )
    except (OSError, NativeGoalBridgeError) as exc:
        _print({
            "schema": "p2p-native-goal-projection/1",
            "status": "BLOCKED",
            "error": str(exc),
        })
        return 2
    if args.format == "command":
        print(result["command"])
    else:
        _print(result)
    return 0


def _worktree(args: argparse.Namespace, root: Path) -> int:
    try:
        if args.worktree_command == "summary":
            result = complete_worktree_summary(root, args.baseline)
        else:
            result = deliverable_evidence(root, args.baseline, args.path)
    except (OSError, WorktreeEvidenceError) as exc:
        _print({"schema": WORKTREE_SCHEMA, "status": "BLOCKED", "error": str(exc)})
        return 2
    _print(result)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(PROJECT_ROOT))
    sub = parser.add_subparsers(dest="command", required=True)

    goal = sub.add_parser("goal")
    goal.add_argument("--host", required=True, choices=(CLAUDE_CODE, CODEX_CLI))
    goal.add_argument("--goal-state", default=".p2p/state/autopilot-goal-state.json")
    goal.add_argument("--task-state", default=".p2p/state/task-state.json")
    goal.add_argument("--baseline")
    goal.add_argument("--format", choices=("json", "command"), default="json")

    worktree = sub.add_parser("worktree")
    worktree_sub = worktree.add_subparsers(dest="worktree_command", required=True)
    summary = worktree_sub.add_parser("summary")
    summary.add_argument("--baseline", required=True)
    deliverable = worktree_sub.add_parser("deliverable")
    deliverable.add_argument("--baseline", required=True)
    deliverable.add_argument("--path", required=True)

    args = parser.parse_args()
    root = Path(args.root).expanduser().resolve()
    if args.command == "goal":
        return _goal(args, root)
    return _worktree(args, root)


if __name__ == "__main__":
    raise SystemExit(main())
