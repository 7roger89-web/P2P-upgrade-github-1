#!/usr/bin/env python3
"""CLI for read-only complete-working-tree evidence.

The implementation lives in p2p_capabilities.worktree_evidence so the source
repository CLI and the packaged P2P skill use one contract.
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
        if (candidate / "p2p_capabilities" / "worktree_evidence.py").is_file():
            RUNTIME_ROOT = candidate
            break
    if RUNTIME_ROOT is not None:
        break
if RUNTIME_ROOT is None:
    raise RuntimeError("P2P worktree-evidence runtime was not found")
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

from p2p_capabilities.worktree_evidence import (  # noqa: E402
    SCHEMA,
    WorktreeEvidenceError,
    complete_worktree_summary,
    deliverable_evidence,
)


def _print(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    sub = parser.add_subparsers(dest="command", required=True)

    summary = sub.add_parser("summary")
    summary.add_argument("--baseline", required=True)

    deliverable = sub.add_parser("deliverable")
    deliverable.add_argument("--baseline", required=True)
    deliverable.add_argument("--path", required=True)

    args = parser.parse_args()
    try:
        if args.command == "summary":
            result = complete_worktree_summary(args.root, args.baseline)
        else:
            result = deliverable_evidence(args.root, args.baseline, args.path)
    except (OSError, WorktreeEvidenceError) as exc:
        _print({"schema": SCHEMA, "status": "BLOCKED", "error": str(exc)})
        return 2
    _print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
