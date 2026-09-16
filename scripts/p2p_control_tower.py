"""Foreground P2P Control Tower coordinator.

The Control Tower coordinates durable task state, bounded delegation, evidence
reconciliation, and the next safe action. It is not a law authority, executor,
or second truth store. Before starting a new executor session this CLI composes
only the relevant ACTIVE verified experience into the existing self-contained
Control Tower prompt, without weakening its prompt-size safety guard.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence


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
    build_execution_prompt,
    new_session_id,
    render_snapshot,
)
from p2p_capabilities.experience_evolution import (  # noqa: E402
    ExperienceEvolutionError,
    activation_summary,
)


CONTEXT_MARKER = "CONTROL_TOWER_CONTEXT:"
MAX_ACTIVE_EXPERIENCES = 3
PROMPT_GUARD_CHARS = 8192


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
    if limit <= 0:
        return ""
    if len(normalized) <= limit:
        return normalized
    if limit == 1:
        return "…"
    return normalized[: limit - 1].rstrip() + "…"


def _render_context_block(summary: Mapping[str, Any], *, max_chars: int) -> str:
    """Render one budgeted risk wrapper; full experience stays in the ledger."""

    if max_chars <= len(CONTEXT_MARKER) + 16:
        return ""
    decision = _compact_text(summary.get("decision", "UNAVAILABLE"), 32)
    block = f"{CONTEXT_MARKER} XP={decision}; NONAUTH"
    if len(block) > max_chars:
        return ""

    experiences = summary.get("experiences")
    active_items = [
        item
        for item in (experiences[:MAX_ACTIVE_EXPERIENCES] if isinstance(experiences, list) else [])
        if isinstance(item, Mapping)
    ]
    if not active_items:
        return block

    count_piece = f"; N={len(active_items)}"
    if len(block) + len(count_piece) <= max_chars:
        block += count_piece

    primary = active_items[0]
    ref = _compact_text(primary.get("experience_id") or UNKNOWN, 96)
    ref_piece = f"; REF={ref}"
    if len(block) + len(ref_piece) <= max_chars:
        block += ref_piece

    # The operational correction is more useful than verbose history. Only the
    # top-ranked correction/lesson is injected; all verified details and other
    # matching experience IDs remain discoverable in the existing ledger.
    risk_source = primary.get("correction") or primary.get("lesson")
    risk_prefix = "; RISK="
    remaining = max_chars - len(block) - len(risk_prefix)
    if remaining >= 24:
        risk = _compact_text(risk_source, remaining)
        if risk:
            block += risk_prefix + risk
    return block


def _contextual_task_for_session(
    root: Path,
    binding: SessionBinding,
    task_text: str,
    *,
    worktree: str = UNKNOWN,
    branch: str = UNKNOWN,
    canonical_base_sha: str = UNKNOWN,
    canonical_base_tree: str = UNKNOWN,
    acceptance_criteria: Sequence[str] = (),
) -> str:
    """Fit relevant experience into the exact final prompt budget, fail-soft."""

    task = str(task_text or "").strip()
    if not task:
        raise BindingError("CONTROL_TOWER_TASK_REQUIRED")
    if CONTEXT_MARKER in task:
        return task

    # Build the exact prompt shape first. The existing handoff module already
    # serializes the canonical Supreme-Law hierarchy, so this layer must not
    # duplicate the law text. It only uses the remaining safe prompt slack.
    base_prompt = build_execution_prompt(
        binding,
        task,
        worktree=worktree,
        branch=branch,
        canonical_base_sha=canonical_base_sha,
        canonical_base_tree=canonical_base_tree,
        acceptance_criteria=acceptance_criteria,
    )
    remaining = PROMPT_GUARD_CHARS - len(base_prompt) - 2  # two newlines before context
    if remaining <= 0:
        return task

    block = _render_context_block(_experience_summary(root, task), max_chars=remaining)
    if not block:
        return task
    return f"{task}\n\n{block}"


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
            "Coordinate durable P2P task state, assemble bounded ACTIVE experience context, "
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
    task_id = str(planned.get("task_id", UNKNOWN))
    criteria = tuple(planned.get("acceptance_criteria") or ())
    result = tower.start_session(
        binding,
        task_id=task_id,
        task_prompt=_contextual_task_for_session(
            root,
            binding,
            _extract_task_text(prompt),
            worktree=worktree,
            branch=branch,
            acceptance_criteria=criteria,
        ),
        worktree=worktree,
        branch=branch,
        acceptance_criteria=criteria,
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
            criteria = tuple(args.acceptance_criterion)
            result = tower.start_session(
                binding,
                task_id=args.task_id,
                task_prompt=_contextual_task_for_session(
                    root,
                    binding,
                    args.goal,
                    worktree=args.worktree,
                    branch=args.branch,
                    canonical_base_sha=args.canonical_base_sha,
                    canonical_base_tree=args.canonical_base_tree,
                    acceptance_criteria=criteria,
                ),
                canonical_base_sha=args.canonical_base_sha,
                canonical_base_tree=args.canonical_base_tree,
                worktree=args.worktree,
                branch=args.branch,
                acceptance_criteria=criteria,
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
