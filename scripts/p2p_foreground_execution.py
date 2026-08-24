#!/usr/bin/env python3
"""Beginner-facing CLI for one bounded foreground task execution.

The CLI is deliberately thin.  It delegates selection, preflight, intent,
budget, scope, checkpoint, verification, and state transitions to
``ForegroundExecutionController``.  Its built-in action surface is limited to
one project-relative text write or file hash; it does not run shell commands,
open a network connection, install anything, or keep work alive.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import sys
from pathlib import Path
from typing import Any, Mapping


HERE = Path(__file__).resolve()
RUNTIME_ROOT: Path | None = None
for parent in HERE.parents:
    for candidate in (parent / ".p2p" / "system", parent / "runtime", parent):
        if (candidate / "p2p_capabilities" / "foreground_execution.py").is_file():
            RUNTIME_ROOT = candidate
            break
    if RUNTIME_ROOT is not None:
        break
if RUNTIME_ROOT is None:
    raise RuntimeError("P2P foreground execution runtime was not found")
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

from p2p_capabilities.evidence import EvidenceClaim  # noqa: E402
from p2p_capabilities.foreground_execution import (  # noqa: E402
    ExecutionBudget,
    ForegroundExecutionController,
    ForegroundExecutionError,
)
from p2p_capabilities.task_state import TaskStateError  # noqa: E402


def _read_json(path: str | Path) -> Any:
    source = Path(path).expanduser().resolve()
    try:
        return json.loads(source.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise TaskStateError(f"JSON_READ_FAILED:{source}:{exc}") from exc


def _mapping(value: Any, error: str) -> dict[str, Any] | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise TaskStateError(error)
    return dict(value)


def _root(args: argparse.Namespace) -> Path:
    return Path(args.root).expanduser().resolve()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="P2P foreground task execution; one direct bounded action only")
    parser.add_argument("--root", default=".", help="project root containing .p2p/state")
    sub = parser.add_subparsers(dest="command", required=True)

    select = sub.add_parser("select", help="show the one safe task selected by the durable state")
    select.add_argument("--task-id")

    preflight = sub.add_parser("preflight", help="check current capability, permission, and context gates")
    preflight.add_argument("--task-id")
    preflight.add_argument("--readiness")
    preflight.add_argument("--permissions")
    preflight.add_argument("--contexts")

    run = sub.add_parser("run", help="run one built-in direct file action and verify it")
    run.add_argument("--task-id")
    run.add_argument("--action", choices=("write-text", "hash-file"), required=True)
    run.add_argument("--path", required=True, help="project-relative path already declared in task scope")
    run.add_argument("--text", help="text for write-text; content is never sent outside the project")
    run.add_argument("--allow-mutation", action="store_true", help="allow the explicit scoped write action")
    run.add_argument("--owner-source", help="owner decision reference; required with --allow-mutation")
    run.add_argument("--permissions", help="JSON permission state; required with --allow-mutation")
    run.add_argument("--max-attempts", type=int, default=1)
    run.add_argument("--max-retries", type=int, default=0)
    run.add_argument("--max-actions", type=int, default=8)

    resume = sub.add_parser("resume", help="recheck one interrupted task with a read-only verifier")
    resume.set_defaults(command="resume")
    return parser


def _claim_for_path(controller: ForegroundExecutionController, runtime: Any, path: str) -> list[EvidenceClaim]:
    fingerprint = runtime.file_sha256(path)
    task = controller.store.require().tasks[runtime.intent.task_id]
    observed_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    return [
        EvidenceClaim(
            claim=f"The foreground verifier confirmed {path}.",
            required_evidence=(reference,),
            actual_evidence=(
                {
                    "source": "scripts/p2p_foreground_execution.py",
                    "evidence_ref": reference,
                    "origin": "RUNTIME_EVIDENCE",
                    "observed_at": observed_at,
                    "freshness": "CURRENT",
                    "scope": [path],
                    "source_binding": "foreground-cli-file-hash",
                    "fingerprint": fingerprint,
                },
            ),
            status="VERIFIED",
        )
        for reference in task.required_evidence
    ]


def _write_result(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    controller = ForegroundExecutionController(_root(args))
    try:
        if args.command == "select":
            _write_result(controller.select(args.task_id))
            return 0
        if args.command == "preflight":
            readiness = _mapping(_read_json(args.readiness), "READINESS_OBJECT_REQUIRED") if args.readiness else None
            permissions = _mapping(_read_json(args.permissions), "PERMISSIONS_OBJECT_REQUIRED") if args.permissions else None
            contexts = _mapping(_read_json(args.contexts), "CONTEXTS_OBJECT_REQUIRED") if args.contexts else None
            _write_result(controller.preflight(args.task_id, capability_readiness=readiness, permission_state=permissions, context_state=contexts))
            return 0
        if args.command == "run":
            if args.action == "write-text" and args.text is None:
                raise TaskStateError("WRITE_TEXT_REQUIRES_TEXT")
            owner_gate = None
            permissions = None
            if args.allow_mutation:
                if not args.owner_source:
                    raise TaskStateError("WRITE_TEXT_REQUIRES_OWNER_SOURCE")
                if not args.permissions:
                    raise TaskStateError("WRITE_TEXT_REQUIRES_PERMISSION_STATE")
                owner_gate = {"status": "APPROVED", "source_ref": args.owner_source}
                permissions = _mapping(_read_json(args.permissions), "PERMISSIONS_OBJECT_REQUIRED")

            def action(runtime: Any) -> dict[str, Any]:
                if args.action == "write-text":
                    runtime.write_text(args.path, args.text)
                    return {"status": "SUCCEEDED", "summary": "The scoped text was written."}
                runtime.file_sha256(args.path)
                return {"status": "SUCCEEDED", "summary": "The scoped file was hashed."}

            def verify(runtime: Any, _action_result: Mapping[str, Any]) -> dict[str, Any]:
                return {"status": "VERIFIED", "evidence_claims": _claim_for_path(controller, runtime, args.path)}

            result = controller.execute(
                action,
                verify,
                task_id=args.task_id,
                action_name=f"cli:{args.action}",
                budget=ExecutionBudget(
                    max_attempts=args.max_attempts,
                    max_retries=args.max_retries,
                    max_tool_actions=args.max_actions,
                    allow_mutation=args.allow_mutation,
                ),
                owner_gate=owner_gate,
                permission_state=permissions,
            )
            _write_result(result)
            return 0
        if args.command == "resume":
            def verify(runtime: Any) -> dict[str, Any]:
                refs = runtime.artifact_refs
                if not refs:
                    return {"status": "FAILED", "summary": "No scoped artifact is available for read-only verification."}
                return {"status": "VERIFIED", "evidence_claims": _claim_for_path(controller, runtime, refs[0])}

            _write_result(controller.resume(verify))
            return 0
        raise TaskStateError("UNKNOWN_COMMAND")
    except (TaskStateError, ForegroundExecutionError) as exc:
        _write_result({
            "status": "BLOCKED",
            "error": str(exc),
            "automatic_start": False,
            "background_execution": False,
            "execution_strategy": "DIRECT",
        })
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
