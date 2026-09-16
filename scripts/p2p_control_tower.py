"""Foreground P2P Control Tower coordinator.

The Control Tower coordinates durable task state, bounded delegation, evidence
reconciliation, and the next safe action. It is not a law authority, executor,
or second truth store. Before starting a new executor session this CLI composes
a compact task context from the single canonical Supreme Law hierarchy and only
matching ACTIVE verified experience from the existing execution ledger.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping


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
from p2p_capabilities.experience_evolution import (  # noqa: E402
    ExperienceEvolutionError,
    activation_summary,
)


CONTEXT_MARKER = "CONTROL_TOWER_CONTEXT_ASSEMBLY:"
MAX_ACTIVE_EXPERIENCES = 3
PRIMARY_WRAPPER_CHARS = 220


def _root(args: argparse.Namespace) -> Path:
    return Path(args.root).expanduser().resolve() if args.root else REPO_ROOT


def _experience_summary(root: Path, task_text: str) -> dict[str, Any]:
    """Retrieve bounded ACTIVE experience without making it execution authority."""

    try:
        return activation_summary(root, task_text, max_results=MAX_ACTIVE_EXPERIENCES)
    except (ExperienceEvolutionError, OSError):
        # Prior experience is useful context, never a prerequisite for executing
        # the current authoritative task. Surface unavailability without turning
        # the experience subsystem into a new blocker/control plane.
        return {
            "schema": "p2p-experience-evolution/1",
            "decision": "UNAVAILABLE",
            "experiences": [],
            "authority": "NON_AUTHORITATIVE_VERIFIED_EXPERIENCE",
            "current_state_wins": True,
            "law_and_task_contract_win": True,
            "permission_effect": "NONE",
            "acceptance_authority": False,
            "mutated": False,
        }


def _compact_text(value: Any, limit: int) -> str:
    normalized = " ".join(str(value or "").split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: max(1, limit - 1)].rstrip() + "…"


def _render_context_block(summary: Mapping[str, Any]) -> str:
    """Render a deliberately thin delegation wrapper, not another policy bundle."""

    decision = str(summary.get("decision", "UNAVAILABLE"))
    lines = [
        CONTEXT_MARKER,
        "- LAW_AUTHORITY=ONE; canonical Supreme Law wins; installed/portable/capsule copies are projection/fallback only; subordinate profiles are trigger-only.",
        f"- EXPERIENCE={decision}; ACTIVE_ONLY; MAX={MAX_ACTIVE_EXPERIENCES}; NON_AUTHORITATIVE; current law/task/state/permissions/evidence win.",
    ]

    experiences = summary.get("experiences")
    active_items = [item for item in experiences[:MAX_ACTIVE_EXPERIENCES] if isinstance(item, Mapping)] if isinstance(experiences, list) else []
    if not active_items:
        return "\n".join(lines)

    refs: list[str] = []
    for item in active_items:
        eid = _compact_text(item.get("experience_id") or UNKNOWN, 96)
        kind = _compact_text(item.get("kind") or UNKNOWN, 24)
        matched = ",".join(_compact_text(value, 32) for value in (item.get("matched_triggers") or ())) or "UNKNOWN"
        refs.append(f"{eid}:{kind}:{matched}")
    lines.append("- ACTIVE_EXPERIENCE_REFS=" + ";".join(refs))

    # Put only the best matching correction into the operational prompt. The
    # complete verified lesson stays in the durable ledger and is addressable by
    # the refs above. This preserves the existing prompt-size safety guard rather
    # than weakening it just to carry more context.
    primary = active_items[0]
    wrapper = _compact_text(primary.get("correction") or primary.get("lesson"), PRIMARY_WRAPPER_CHARS)
    if wrapper:
        lines.append(f"- PRIMARY_RISK_WRAPPER={wrapper}")
    return "\n".join(lines)


def _contextual_task(root: Path, task_text: str) -> str:
    """Compose the task with bounded law hierarchy + relevant ACTIVE experience."""

    task = str(task_text or "").strip()
    if not task:
        raise BindingError("CONTROL_TOWER_TASK_REQUIRED")
    if CONTEXT_MARKER in task:
        return task
    return f"{task}\n\n{_render_context_block(_experience_summary(root, task))}"


def _extract_task_text(prompt: str) -> str:
    start_marker = "\nTASK:\n"
    end_marker = "\nACCEPTANCE_CRITERIA:\n"
    start = prompt.find(start_marker)
    if start < 0:
        raise BindingError("CONTROL_TOWER_TASK_SECTION_MISSING")
    start += len(start_marker)
    end = prompt.find(end_marker, start)
    if end < 0:
        raise BindingError("CONTROL_TOWER_ACCEPTANCE_SECTION_MISSING")
    task = prompt[start:end].strip()
    if not task:
        raise BindingError("CONTROL_TOWER_TASK_SECTION_EMPTY")
    return task


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
        description=(
            "Coordinate durable P2P task state, assemble bounded law/experience context, "
            "start executor sessions, and reconcile their evidence."
        )
    )
    parser.add_argument("--root", help="project root; defaults to the repository containing this script")
    parser.add_argument("--json", action="store_true", dest="as_json", help="emit machine-readable JSON")
    parser.add_argument("--current-canonical-base-sha", default=UNKNOWN)
    parser.add_argument("--current-canonical-base-tree", default=UNKNOWN)
    sub = parser.add_subparsers(dest="command", required=True)

    start = sub.add_parser("start", help="register a bounded session and print its context-assembled prompt")
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
        help="derive and register the next safe task-state session with bounded context assembly",
    )
    next_session.add_argument("--host", required=True)
    next_session.add_argument("--session-id")
    next_session.add_argument("--worktree", default=UNKNOWN)
    next_session.add_argument("--branch", default=UNKNOWN)
    next_session.add_argument("--json", action="store_true", dest="as_json", default=argparse.SUPPRESS)
    return parser


def _start_next_with_context(
    tower: ControlTower,
    root: Path,
    host: str,
    *,
    session_id: str | None,
    worktree: str,
    branch: str,
) -> dict[str, Any]:
    planned = tower.recommend_next_session(
        host,
        session_id=session_id,
        worktree=worktree,
        branch=branch,
    )
    if planned.get("status") != "PASS":
        return planned
    if planned.get("idempotent"):
        return tower.start_next_session(
            host,
            session_id=session_id,
            worktree=worktree,
            branch=branch,
        )
    binding_mapping = planned.get("binding")
    recommendation = planned.get("recommendation")
    if not isinstance(binding_mapping, Mapping) or not isinstance(recommendation, Mapping):
        raise BindingError("CONTROL_TOWER_NEXT_RECOMMENDATION_INVALID")
    prompt = recommendation.get("PROMPT")
    if not isinstance(prompt, str):
        raise BindingError("CONTROL_TOWER_NEXT_PROMPT_INVALID")
    binding = SessionBinding.from_mapping(binding_mapping)
    result = tower.start_session(
        binding,
        task_id=str(planned.get("task_id", UNKNOWN)),
        task_prompt=_contextual_task(root, _extract_task_text(prompt)),
        worktree=worktree,
        branch=branch,
        acceptance_criteria=tuple(planned.get("acceptance_criteria") or ()),
    )
    result.update(
        {
            "source": (Path(".p2p") / "state" / "task-state.json").as_posix(),
            "task_id": planned.get("task_id", UNKNOWN),
            "plan_hash": planned.get("plan_hash", UNKNOWN),
        }
    )
    return result


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
                task_prompt=_contextual_task(root, args.goal),
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
            result = _start_next_with_context(
                tower,
                root,
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
