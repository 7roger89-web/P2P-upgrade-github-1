"""Foreground P2P Control Tower coordinator.

Control Tower coordinates durable task state, bounded delegation, evidence
reconciliation, and the next safe action. It is not the law authority, the
executor, a second router, or a second truth store.

The runtime prompt keeps exactly the nine canonical Supreme-Law capsule entries.
Operational guidance (project preflight, OE, GitHub handling, prompt-authoring)
and verified experience are task-scoped context, not extra Supreme Laws.
"""

from __future__ import annotations

import argparse
import json
import re
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

# Importing the package executes legacy compatibility projections that append
# operational guidance to control_tower_handoff.SUPREME_LAW_CAPSULE. For the
# canonical foreground Control Tower CLI we immediately restore the pristine
# nine-law capsule. Those appended texts remain available in installed/project
# instructions; they are not independent Supreme Laws and must not ride in every
# executor prompt.
from p2p_capabilities import control_tower_handoff as _handoff  # noqa: E402

_CANONICAL_LAW_IDENTIFIERS = (
    "OWNER_OUTCOME_AND_AUTHORITY_ARE_INVARIANTS",
    "SIMPLEST_USEFUL_PATH_TO_COMPLETION",
    "REAL_STATE_AND_EVIDENCE_OVERRIDE_ASSUMPTIONS",
    "RECOVER_ADAPTIVELY; DO_NOT_ENTER_SPECULATIVE_FIX_LOOPS",
    "PRESERVE_CONTINUITY_AND_STOP",
    "PROMPT_DESTINATION_AND_PLAN_STATE_ARE_EXPLICIT",
    "ANALYTICAL_AUTONOMY_AND_DELEGATION_ALIGNMENT",
    "TASK_CONTRACT_AND_ACCEPTANCE_FIDELITY",
    "EXECUTOR_INPUT_FORMAT_AND_ARTIFACT_TRANSPORT_FIDELITY",
)
_law_lines = tuple(line for line in _handoff.SUPREME_LAW_CAPSULE.splitlines() if line.strip())
if len(_law_lines) < 9 or any(
    identifier not in _law_lines[index]
    for index, identifier in enumerate(_CANONICAL_LAW_IDENTIFIERS)
):
    raise RuntimeError("CONTROL_TOWER_CANONICAL_SUPREME_LAW_CAPSULE_INVALID")
_handoff.SUPREME_LAW_CAPSULE = "\n".join(_law_lines[:9])

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
from p2p_capabilities.review_extension_activation import render_review_guidance  # noqa: E402


CONTEXT_MARKER = "CONTROL_TOWER_CONTEXT:"
MAX_ACTIVE_EXPERIENCES = 3
PROMPT_GUARD_CHARS = 8192
MIN_CONTEXT_BUDGET = 380
MAX_PRIMARY_RISK_WRAPPER_CHARS = 360
CONTROL_TOWER_FLOW = (
    "OUTCOME>FRESH_STATE>ONE_LAW>TASK_CONTRACT>SELECT_EXISTING_CAPABILITY_OR_HOST>"
    "BOUNDED_CONTEXT>EXECUTE>EVIDENCE>RECONCILE>DONE|NEXT|BLOCKED|OWNER_GATE"
)
_GITHUB_TASK = re.compile(r"\b(github|pull request|\bpr\b|merge|branch|commit|repository|repo|head sha)\b", re.I)
_PROMPT_TASK = re.compile(r"\b(prompt|instruction|delegate|delegation|handoff|executor prompt|rewrite prompt)\b", re.I)


def _root(args: argparse.Namespace) -> Path:
    return Path(args.root).expanduser().resolve() if args.root else REPO_ROOT


def _experience_summary(root: Path, task_text: str) -> dict[str, Any]:
    """Retrieve bounded ACTIVE experience without making it execution authority."""

    try:
        return activation_summary(root, task_text, max_results=MAX_ACTIVE_EXPERIENCES)
    except (ExperienceEvolutionError, OSError):
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


def _append_if_fits(parts: list[str], value: str, max_chars: int) -> bool:
    candidate = "\n".join((*parts, value))
    if len(candidate) > max_chars:
        return False
    parts.append(value)
    return True


def _render_context_block(
    summary: Mapping[str, Any],
    task_text: str,
    *,
    max_chars: int,
) -> str:
    """Render mandatory runtime gates plus trigger-scoped guidance and experience."""

    mandatory = [
        CONTEXT_MARKER,
        "LAW_AUTHORITY=ONE; Supreme Law=canonical 9-law capsule; projections/fallbacks/subordinate profiles are not independent laws.",
        f"CONTROL_TOWER_FLOW={CONTROL_TOWER_FLOW}",
        "P2P_LAW_PREFLIGHT=read root AGENTS.md when present; resolve canonical>installed>portable>inline; report actual P2P_LAW_SOURCE; never fake a read.",
        "OE_GATE=Không bị over engineering chứ? Check SIMPLER_PATH,MATERIAL_PROGRESS,NECESSITY,CORE_BEFORE_SUPPORT,SMALLER_VERIFIABLE_SLICE; return DO_IT|SKIP_IT|DEFER_UNTIL_NEEDED.",
    ]
    block = "\n".join(mandatory)
    if len(block) > max_chars:
        return ""
    parts = list(mandatory)

    task = str(task_text or "")
    if _GITHUB_TASK.search(task):
        _append_if_fits(
            parts,
            "GITHUB_GUIDANCE=EXECUTOR_GITHUB_ACCESS != OWNER_GITHUB_CONNECTOR_STATUS; direct repo/PR/HEAD evidence wins; do not infer account breakage from one unavailable session.",
            max_chars,
        )
    if _PROMPT_TASK.search(task):
        _append_if_fits(
            parts,
            "PROMPT_AUTHORING_DISCIPLINE_V1=classify PROMPT_INPUT_MATURITY as READY_PROMPT|PARTIAL_DRAFT|CLEAR_SIMPLE_REQUEST|AMBIGUOUS_HIGH_IMPACT; CLARIFICATION_DISCIPLINE=no re-ask/interview loop; DESTINATION_RESOLUTION from durable state; CAPABILITY_OVER_FOLKLORE; PROPORTIONAL_PROMPT_COMPLEXITY; NO_PRIVATE_CHAIN_OF_THOUGHT_REQUEST; REVISION_CONTINUITY; OUTPUT_SURFACE_FIDELITY; PROMPT_AUTHORING_STOP.",
            max_chars,
        )

    review_guidance = render_review_guidance(task)
    if review_guidance and not _append_if_fits(parts, review_guidance, max_chars):
        return ""

    decision = _compact_text(summary.get("decision", "UNAVAILABLE"), 32)
    _append_if_fits(
        parts,
        f"EXPERIENCE=XP={decision}; ACTIVE_ONLY; MAX={MAX_ACTIVE_EXPERIENCES}; NONAUTHORITATIVE; current law/task/state/permissions/evidence win.",
        max_chars,
    )

    experiences = summary.get("experiences")
    active_items = [
        item
        for item in (experiences[:MAX_ACTIVE_EXPERIENCES] if isinstance(experiences, list) else [])
        if isinstance(item, Mapping)
    ]
    if not active_items:
        return "\n".join(parts)

    refs = ",".join(_compact_text(item.get("experience_id") or UNKNOWN, 80) for item in active_items)
    _append_if_fits(parts, f"ACTIVE_EXPERIENCE_REFS={refs}", max_chars)

    primary = active_items[0]
    risk_source = primary.get("correction") or primary.get("lesson")
    prefix = "PRIMARY_RISK_WRAPPER="
    used = len("\n".join(parts)) + 1 + len(prefix)
    remaining = max_chars - used
    if remaining >= 32:
        risk = _compact_text(risk_source, min(remaining, MAX_PRIMARY_RISK_WRAPPER_CHARS))
        if risk:
            _append_if_fits(parts, prefix + risk, max_chars)
    return "\n".join(parts)


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
    """Fit runtime guidance + relevant experience into the exact prompt budget."""

    task = str(task_text or "").strip()
    if not task:
        raise BindingError("CONTROL_TOWER_TASK_REQUIRED")
    if CONTEXT_MARKER in task:
        return task

    base_prompt = build_execution_prompt(
        binding,
        task,
        worktree=worktree,
        branch=branch,
        canonical_base_sha=canonical_base_sha,
        canonical_base_tree=canonical_base_tree,
        acceptance_criteria=acceptance_criteria,
    )
    remaining = PROMPT_GUARD_CHARS - len(base_prompt) - 2
    if remaining < MIN_CONTEXT_BUDGET:
        raise BindingError(
            f"CONTROL_TOWER_PROMPT_BUDGET_EXHAUSTED:base={len(base_prompt)}:remaining={remaining}"
        )

    block = _render_context_block(
        _experience_summary(root, task),
        task,
        max_chars=remaining,
    )
    if not block:
        raise BindingError("CONTROL_TOWER_REQUIRED_CONTEXT_DID_NOT_FIT")
    contextual = f"{task}\n\n{block}"

    final_prompt = build_execution_prompt(
        binding,
        contextual,
        worktree=worktree,
        branch=branch,
        canonical_base_sha=canonical_base_sha,
        canonical_base_tree=canonical_base_tree,
        acceptance_criteria=acceptance_criteria,
    )
    if len(final_prompt) > PROMPT_GUARD_CHARS:
        raise BindingError(f"CONTROL_TOWER_FINAL_PROMPT_TOO_LARGE:{len(final_prompt)}")
    return contextual


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
            "Coordinate durable P2P task state, assemble bounded runtime/experience context, "
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
