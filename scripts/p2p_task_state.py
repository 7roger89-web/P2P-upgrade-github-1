#!/usr/bin/env python3
"""Foreground CLI for the bounded P2P durable task-state projection.

This command only reads/writes the Goal-scoped task projection and appends
references to the existing execution ledger.  It never starts background work,
selects an agent, installs a capability, grants permissions, or survives the
current process.
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
    for candidate in (parent / ".p2p" / "system", parent):
        if (candidate / "p2p_capabilities" / "task_state.py").is_file():
            RUNTIME_ROOT = candidate
            break
    if RUNTIME_ROOT is not None:
        break
if RUNTIME_ROOT is None:
    raise RuntimeError("P2P task-state runtime was not found")
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

from p2p_capabilities.task_state import (  # noqa: E402
    TaskPlan,
    TaskStateError,
    TaskStateStore,
    beginner_owner_message,
    next_safe_task,
    request_owner_decision,
    resolve_owner_decision,
)


def _read_json(path: str | Path) -> Any:
    source = Path(path).expanduser().resolve()
    try:
        return json.loads(source.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise TaskStateError(f"JSON_READ_FAILED:{source}:{exc}") from exc


def _write_result(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def _root(args: argparse.Namespace) -> Path:
    return Path(args.root).expanduser().resolve()


def _store(args: argparse.Namespace) -> TaskStateStore:
    return TaskStateStore(_root(args))


def _task_specs(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, Mapping):
        value = value.get("tasks")
    if not isinstance(value, list):
        raise TaskStateError("TASK_INPUT_MUST_BE_LIST")
    if any(not isinstance(item, Mapping) for item in value):
        raise TaskStateError("TASK_INPUT_ENTRY_MUST_BE_OBJECT")
    return [dict(item) for item in value]


def _mapping(value: Any, error: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise TaskStateError(error)
    return dict(value)


def _summary(plan: TaskPlan) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for task in plan.tasks.values():
        counts[task.status] = counts.get(task.status, 0) + 1
    safe_task = next_safe_task(plan)
    return {
        "schema": "p2p-task-state-summary/1",
        "goal_id": plan.goal_id,
        "plan_revision": plan.plan_revision,
        "plan_hash": plan.canonical_hash(),
        "task_count": len(plan.tasks),
        "status_counts": counts,
        "topological_order": list(plan.topological_order()),
        "next_safe_task": safe_task.task_id if safe_task else None,
        "automatic_start": False,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="P2P durable task state; foreground and bounded only")
    parser.add_argument("--root", default=".", help="project root containing .p2p/state")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="create task-state.json from an existing Goal contract")
    init.add_argument("--goal-contract", default=".p2p/state/goal-contract.json")
    init.add_argument("--tasks", required=True, help="JSON file containing a task list or {tasks: [...]}")

    sub.add_parser("show", help="show bounded task-state summary")
    sub.add_parser("ready", help="promote dependency-complete no-gate tasks to READY")

    transition = sub.add_parser("transition", help="apply one explicit state transition")
    transition.add_argument("--task-id", required=True)
    transition.add_argument("--status", required=True)
    transition.add_argument("--blocker")
    transition.add_argument("--owner-decision")
    transition.add_argument("--completion")
    transition.add_argument("--checkpoint")
    transition.add_argument("--preflight")

    preflight = sub.add_parser("preflight", help="observe capability/permission/context gates")
    preflight.add_argument("--task-id", required=True)
    preflight.add_argument("--readiness")
    preflight.add_argument("--permissions")
    preflight.add_argument("--contexts")

    complete = sub.add_parser("complete", help="complete a task with independent evidence")
    complete.add_argument("--task-id", required=True)
    complete.add_argument("--evidence", required=True)
    complete.add_argument("--candidate-state", required=True)

    checkpoint = sub.add_parser("checkpoint", help="persist an explicit interruption checkpoint")
    checkpoint.add_argument("--task-id", required=True)
    checkpoint.add_argument("--checkpoint", required=True)

    resume = sub.add_parser("resume", help="inspect resume safety; never auto-starts")
    resume.add_argument("--state-fingerprints")
    resume.add_argument("--evidence-fingerprints")
    resume.add_argument("--preflights")

    handoff = sub.add_parser("handoff", help="show dependency handoff candidates")
    handoff.add_argument("--task-id", required=True)

    events = sub.add_parser("events", help="read task events from the existing execution ledger")
    events.set_defaults(include_summary=False)

    revise = sub.add_parser("revise", help="create a provenance-linked plan revision")
    revise.add_argument("--changes", required=True, help="JSON object keyed by task ID")
    revise.add_argument("--reason", required=True)
    revise.add_argument("--source-ref", action="append", default=[])

    owner_request = sub.add_parser("owner-request", help="record a pending owner decision")
    owner_request.add_argument("--task-id", required=True)
    owner_request.add_argument("--question", required=True)
    owner_request.add_argument("--option", action="append", default=[])
    owner_request.add_argument("--source-ref", action="append", default=[])

    owner_resolve = sub.add_parser("owner-resolve", help="record an explicit owner answer")
    owner_resolve.add_argument("--task-id", required=True)
    owner_resolve.add_argument("--approved", action="store_true")
    owner_resolve.add_argument("--answer", required=True)
    owner_resolve.add_argument("--decision-ref", action="append", default=[])

    owner = sub.add_parser("owner-question", help="show a beginner-friendly owner question")
    owner.add_argument("--task-id", required=True)
    return parser


def _load_optional(path: str | None) -> dict[str, Any] | None:
    return None if not path else _mapping(_read_json(path), "JSON_OBJECT_REQUIRED")


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        store = _store(args)
        if args.command == "init":
            goal = _mapping(_read_json(Path(args.root) / args.goal_contract if not Path(args.goal_contract).is_absolute() else args.goal_contract), "GOAL_CONTRACT_OBJECT_REQUIRED")
            specs = _task_specs(_read_json(Path(args.root) / args.tasks if not Path(args.tasks).is_absolute() else args.tasks))
            plan = TaskPlan.from_goal(goal, specs)
            _write_result({"status": "PASS", "state": str(store.initialize(plan)), "summary": _summary(store.require())})
            return 0
        if args.command == "show":
            plan = store.require()
            _write_result(_summary(plan))
            return 0
        if args.command == "ready":
            current = store.require()
            updated = current.refresh_ready()
            if updated.canonical_hash() != current.canonical_hash():
                store.save(updated, event_name="task_ready_refresh")
            _write_result(_summary(updated))
            return 0
        if args.command == "transition":
            updated = store.transition(
                args.task_id,
                args.status,
                blocker=_load_optional(args.blocker),
                owner_decision=_load_optional(args.owner_decision),
                completion=_load_optional(args.completion),
                checkpoint=_load_optional(args.checkpoint),
                preflight=_load_optional(args.preflight),
            )
            _write_result(_summary(updated))
            return 0
        if args.command == "preflight":
            updated, result = store.preflight(
                args.task_id,
                capability_readiness=_load_optional(args.readiness),
                permission_state=_load_optional(args.permissions),
                context_state=_load_optional(args.contexts),
            )
            _write_result({"preflight": result, "summary": _summary(updated)})
            return 0
        if args.command == "complete":
            evidence = _read_json(args.evidence)
            claims = evidence if isinstance(evidence, list) else [evidence]
            candidate = _read_json(args.candidate_state)
            updated = store.complete(args.task_id, claims, candidate)
            _write_result(_summary(updated))
            return 0
        if args.command == "checkpoint":
            updated = store.checkpoint(args.task_id, _mapping(_read_json(args.checkpoint), "CHECKPOINT_OBJECT_REQUIRED"))
            _write_result(_summary(updated))
            return 0
        if args.command == "resume":
            result = store.resume(
                current_state_fingerprints=_load_optional(args.state_fingerprints),
                current_evidence_fingerprints=_load_optional(args.evidence_fingerprints),
                current_preflights=_load_optional(args.preflights),
            )
            _write_result(result)
            return 0
        if args.command == "handoff":
            from p2p_capabilities.task_state import dependency_handoff

            _write_result(dependency_handoff(store.require(), args.task_id))
            return 0
        if args.command == "events":
            _write_result(store.read_events())
            return 0
        if args.command == "revise":
            changes = _mapping(_read_json(args.changes), "CHANGES_OBJECT_REQUIRED")
            _write_result(_summary(store.revise(task_updates=changes, reason=args.reason, source_refs=args.source_ref)))
            return 0
        if args.command == "owner-request":
            current = store.require()
            updated = request_owner_decision(current, args.task_id, args.question, options=args.option, source_refs=args.source_ref)
            _write_result(_summary(store.save(updated, event_name="owner_decision_requested", task_id=args.task_id)))
            return 0
        if args.command == "owner-resolve":
            current = store.require()
            updated = resolve_owner_decision(current, args.task_id, approved=args.approved, answer=args.answer, decision_refs=args.decision_ref)
            _write_result(_summary(store.save(updated, event_name="owner_decision_resolved", task_id=args.task_id)))
            return 0
        if args.command == "owner-question":
            _write_result(beginner_owner_message(store.require(), args.task_id))
            return 0
        parser.error("unknown command")
    except TaskStateError as exc:
        _write_result({"status": "BLOCKED", "error": str(exc), "automatic_start": False})
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
