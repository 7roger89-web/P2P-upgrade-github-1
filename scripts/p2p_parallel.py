#!/usr/bin/env python3
"""Inspect the C17 bounded parallel foreground decision.

The CLI is deliberately an inspection boundary.  It accepts durable task
contracts and reports unavailable host callbacks instead of simulating child
execution.  Real execution is supplied through the Python runtime API.
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
        if (candidate / "p2p_capabilities" / "parallel_execution.py").is_file():
            RUNTIME_ROOT = candidate
            break
    if RUNTIME_ROOT is not None:
        break
if RUNTIME_ROOT is None:
    raise RuntimeError("P2P parallel foreground runtime was not found")
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

from p2p_capabilities.bounded_delegation import DelegationBudget, DelegationRequest, PermissionEnvelope  # noqa: E402
from p2p_capabilities.parallel_execution import BoundedParallelForegroundController  # noqa: E402
from p2p_capabilities.task_state import TaskStateError, TaskStateStore  # noqa: E402


def _read_json(path: str | Path) -> Any:
    source = Path(path).expanduser().resolve()
    try:
        return json.loads(source.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise TaskStateError(f"JSON_READ_FAILED:{source}:{exc}") from exc


def _request(root: Path, value: Mapping[str, Any]) -> DelegationRequest:
    task_id = str(value.get("task_id", "")).strip()
    if not task_id:
        raise TaskStateError("PARALLEL_TASK_ID_REQUIRED")
    task = TaskStateStore(root).require().tasks.get(task_id)
    if task is None:
        raise TaskStateError(f"TASK_NOT_FOUND:{task_id}")
    parent = PermissionEnvelope.from_value(value.get("parent_permissions"), default_scope=task.scope)
    child = PermissionEnvelope.from_value(value.get("child_permissions"), default_scope=value.get("child_scope", task.scope))
    allowed = {
        "task_size",
        "value_reasons",
        "child_scope",
        "read_scopes",
        "write_scopes",
        "delete_scopes",
        "shared_resources",
        "candidate_state",
        "candidate_fingerprint",
        "project_binding",
        "context_state",
        "relevant_context",
        "capability_readiness",
        "permission_state",
        "dependency_outcomes",
        "relevant_decisions",
        "known_risks",
        "unknowns",
        "requested_execution_class",
        "identity_required",
        "required_identity",
        "observed_identity",
        "identity_authority",
        "owner_gate",
        "allow_direct_fallback",
    }
    values = {key: value[key] for key in allowed if key in value}
    values["value_reasons"] = tuple(values.get("value_reasons", ()))
    values["budget"] = DelegationBudget()
    return DelegationRequest(task=task, parent_permissions=parent, child_permissions=child, **values)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="P2P C17 bounded parallel foreground decision; maximum two children")
    parser.add_argument("--root", default=".")
    parser.add_argument("--requests", required=True, help="JSON file containing a list of existing task request objects; each may include economy_profile")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("decide", help="evaluate the bounded pair without starting work")
    sub.add_parser("run", help="report the foreground run; CLI has no child callback and will not simulate one")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        raw = _read_json(args.requests)
        if not isinstance(raw, list) or not all(isinstance(item, Mapping) for item in raw):
            raise TaskStateError("PARALLEL_REQUEST_FILE_MUST_BE_LIST")
        root = Path(args.root).expanduser().resolve()
        requests = tuple(_request(root, item) for item in raw)
        economy_profiles = {
            str(item["task_id"]): item["economy_profile"]
            for item in raw
            if item.get("economy_profile") is not None
        }
        controller = BoundedParallelForegroundController(root)
        if args.command == "decide":
            print(json.dumps(controller.decide(requests, economy_profiles=economy_profiles or None), ensure_ascii=False, indent=2, sort_keys=True))
            return 0
        result = controller.execute(requests, economy_profiles=economy_profiles or None)
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 0 if result.get("status") in {"DONE", "PARTIAL", "BLOCKED"} else 2
    except (TaskStateError, ValueError, TypeError) as exc:
        print(json.dumps({"status": "BLOCKED", "strategy": "BLOCKED", "reason": str(exc), "parallel_execution": False, "worker_output_is_evidence": False}, ensure_ascii=False, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
