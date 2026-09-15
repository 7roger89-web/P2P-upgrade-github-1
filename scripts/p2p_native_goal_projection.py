#!/usr/bin/env python3
"""Render a host-native /goal projection from canonical P2P durable state.

Read-only. This command never launches Claude/Codex, mutates P2P state, grants
permissions, retries work, or changes provider/model routing.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve()
RUNTIME_ROOT: Path | None = None
for parent in HERE.parents:
    for candidate in (parent / ".p2p" / "system", parent):
        if (candidate / "p2p_capabilities" / "native_goal_bridge.py").is_file():
            RUNTIME_ROOT = candidate
            break
    if RUNTIME_ROOT is not None:
        break
if RUNTIME_ROOT is None:
    raise RuntimeError("P2P native-goal runtime was not found")
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

from p2p_capabilities.native_goal_bridge import (  # noqa: E402
    CODEX_CLI,
    CLAUDE_CODE,
    NativeGoalBridgeError,
    build_native_goal_projection,
)


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise NativeGoalBridgeError(f"JSON_READ_FAILED:{path}:{exc}") from exc
    if not isinstance(value, dict):
        raise NativeGoalBridgeError(f"JSON_OBJECT_REQUIRED:{path}")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    parser.add_argument("--host", required=True, choices=(CLAUDE_CODE, CODEX_CLI))
    parser.add_argument("--goal-state", default=".p2p/state/autopilot-goal-state.json")
    parser.add_argument("--task-state", default=".p2p/state/task-state.json")
    parser.add_argument("--baseline")
    parser.add_argument("--format", choices=("json", "command"), default="json")
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    try:
        projection = build_native_goal_projection(
            args.host,
            _read_json(root / args.goal_state),
            _read_json(root / args.task_state),
            baseline_ref=args.baseline,
        )
    except (OSError, NativeGoalBridgeError) as exc:
        print(json.dumps({
            "schema": "p2p-native-goal-projection/1",
            "status": "BLOCKED",
            "error": str(exc),
        }, ensure_ascii=False, sort_keys=True))
        return 2

    if args.format == "command":
        print(projection["command"])
    else:
        print(json.dumps(projection, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
