#!/usr/bin/env python3
"""P2P temporary-workspace inventory and fail-closed garbage collection.

The command is intentionally a thin facade over the existing FW06 durable
workspace registry, lease, event, and cleanup surfaces.  ``gc`` is dry-run
unless ``--apply`` is explicitly supplied.  ``schedule`` only prints an
Owner-gated Windows registration preview; it never installs a task.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SYSTEM_ROOT = Path(__file__).resolve().parent.parent / ".p2p" / "system"
if str(SYSTEM_ROOT) not in sys.path:
    sys.path.insert(0, str(SYSTEM_ROOT))

from p2p_capabilities import fw06_operational_resilience as fw06  # noqa: E402


def _json(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def _windows_registration_preview(root: Path,
                                  policy: dict) -> dict[str, object]:
    schedule = policy["schedule"]
    def quote(value: object) -> str:
        return '"' + str(value).replace('"', '\\"') + '"'

    task_run = " ".join((
        quote(sys.executable),
        quote(Path(__file__).resolve()),
        "--root",
        quote(root),
        "gc",
    ))
    escaped_task_run = task_run.replace('"', '\\"')
    # This is output data, not an execution path.  The command intentionally
    # omits --apply: activation and any deletion authority remain Owner-gated.
    task_command = (
        f'schtasks /Create /TN "P2P-TMP-GC01" /SC DAILY '
        f'/ST {schedule["daily_local_time"]} /TR '
        f'"{escaped_task_run}"'
    )
    return {
        "schema": fw06.TMP_GC_SCHEMA,
        "activated": False,
        "activation": schedule["activation"],
        "daily_local_time": schedule["daily_local_time"],
        "registration_argv_preview": [
            "schtasks", "/Create", "/TN", "P2P-TMP-GC01", "/SC", "DAILY",
            "/ST", schedule["daily_local_time"], "/TR", task_run,
        ],
        "registration_command_preview": task_command,
        "warning": "PREVIEW_ONLY_OWNER_MUST_ACTIVATE",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="P2P fail-closed temporary workspace GC",
    )
    parser.add_argument("--root", default=".", help="P2P project root")
    parser.add_argument("--policy", help="optional policy JSON path")
    sub = parser.add_subparsers(dest="command", required=True)

    gc = sub.add_parser("gc", help="inventory; add --apply for guarded fixture/apply mode")
    gc.add_argument("--apply", action="store_true", help="revalidate and delete only eligible workspaces")
    gc.add_argument("--now", help="deterministic UTC timestamp for tests")

    sub.add_parser("schedule", help="print an inactive Owner-gated schedule preview")

    args = parser.parse_args(argv)
    root = Path(args.root).expanduser().resolve()
    try:
        policy = fw06.load_tmp_gc_policy(root, args.policy)
        if args.command == "schedule":
            _json(_windows_registration_preview(root, policy))
            return 0
        if args.apply and args.now:
            raise fw06.TmpGcError("NOW_OVERRIDE_NOT_ALLOWED_IN_APPLY")
        result = fw06.run_tmp_gc(
            root,
            apply=bool(args.apply),
            policy=policy,
            now=args.now,
        )
        _json(result)
        return 0
    except (OSError, ValueError, fw06.TmpGcError) as exc:
        _json({
            "schema": fw06.TMP_GC_SCHEMA,
            "status": "BLOCKED",
            "dry_run": not bool(getattr(args, "apply", False)),
            "legacy_workspace_delete_count": 0,
            "reason": str(exc),
        })
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
