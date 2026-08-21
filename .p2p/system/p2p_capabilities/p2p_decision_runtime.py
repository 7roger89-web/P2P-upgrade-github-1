"""FRAMEWORK-01 decision trace runtime.

Per operating-loop iteration, persist a compact Decision Trace (Owner
contract §28):

- why this task; why now; dependencies satisfied; risk class;
- skills activated; role/team selected; target selected; permission;
- verification required; continue-gate result; why continue / why stop.

Decisions and evidence are recorded — never private chain-of-thought.
Secret scrubbing is mandatory. Machine-readable ledger + beginner
rendering. REUSES the canonical decision_trace module for material
decisions (activation receipts are not duplicated there).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .decision_trace import append_trace, make_trace, _sanitize

DECISION_TRACE_SCHEMA = "p2p-decision-trace-fw01/1"


def _check_text(value: Any, field: str, *, max_length: int = 4096) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field}_MUST_BE_TEXT")
    return value[:max_length].strip()


def _check_enum(value: Any, field: str, options: Iterable[str]) -> str:
    text = _check_text(value, field, max_length=128)
    if text not in tuple(options):
        raise ValueError(f"{field}_INVALID_VALUE")
    return text


CONTINUE_OUTCOMES = ("AUTO_CONTINUE", "OWNER_GATE", "STOP_DONE",
                     "STOP_BLOCKED", "STOP_UNKNOWN", "STOP_LOOP_GUARD")
RISK_CLASSES = ("READ_ONLY", "SAFE_WORKSPACE", "MUTATING_SAFE",
                "MUTATING_SENSITIVE", "MUTATING_PROTECTED")
ROLE_CLASSES = ("SINGLE_ROLE", "SMALL_REVIEW_SET", "SPECIALIST_SET",
                "FULL_COUNCIL_REQUIRED")


def record_iteration_trace(
    root: Path,
    *,
    iteration: int,
    goal_id: str,
    task_id: str,
    why_this_task: str,
    why_now: str,
    dependencies_satisfied: bool,
    risk_class: str,
    skills_activated: Iterable[str] = (),
    role_selected: str | None = None,
    team_selected: Iterable[str] = (),
    target_selected: str | None = None,
    permission: str = "P2P_AUTONOMOUS_READ_ONLY",
    verification_required: str,
    continue_gate_result: str,
    why_stop_or_continue: str,
    extra: dict[str, Any] | None = None,
    at: str | None = None,
) -> dict[str, Any]:
    record = {
        "schema": DECISION_TRACE_SCHEMA,
        "trace_id": f"I{int(iteration)}:{_check_text(goal_id)}:{_check_text(task_id)}",
        "iteration": int(iteration),
        "goal_id": _check_text(goal_id),
        "task_id": _check_text(task_id),
        "why_this_task": _check_text(why_this_task),
        "why_now": _check_text(why_now),
        "dependencies_satisfied": bool(dependencies_satisfied),
        "risk_class": _check_enum(risk_class, "risk_class", RISK_CLASSES),
        "skills_activated": [_check_text(s, "skill_id") for s in skills_activated],
        "role_selected": (_check_enum(role_selected, "role_selected", ROLE_CLASSES)
                          if role_selected else None),
        "team_selected": [_check_text(r, "team_role_id") for r in team_selected],
        "target_selected": (_check_text(target_selected, "target_selected")
                            if target_selected else None),
        "permission": _check_text(permission, "permission", max_length=256),
        "verification_required": _check_text(verification_required),
        "continue_gate_result": _check_enum(continue_gate_result,
                                            "continue_gate_result",
                                            CONTINUE_OUTCOMES),
        "why_stop_or_continue": _check_text(why_stop_or_continue),
        "recorded_utc": _check_text(at or datetime.now(timezone.utc).isoformat()),
        "extra": _sanitize(dict(extra or {})) if extra else {},
    }
    append_trace(root, record)
    return record


def render_beginner_status(ledger: Iterable[dict[str, Any]] | Path,
                           project: str) -> str:
    """Beginner-readable projection from the trace ledger (no hidden
    reasoning, decisions + evidence only)."""
    if isinstance(ledger, Path):
        rows: list[dict[str, Any]] = []
        if ledger.exists():
            for line in ledger.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
    else:
        rows = list(ledger)
    if not rows:
        return (f"Project: {project}\nGoal: (chưa có iteration nào)\n"
                "Current: —\nP2P: Healthy (chưa có hoạt động)\n"
                "Needs Owner: No\n")
    last = rows[-1]
    done = [r for r in rows if r.get("continue_gate_result") == "AUTO_CONTINUE"]
    needs_owner = last.get("continue_gate_result") == "OWNER_GATE"
    return ("\n".join([
        f"Project: {project}",
        f"Goal: {last.get('goal_id')}",
        f"Progress: {len(done)} task đã hoàn tất, "
        f"tổng {len(rows)} iteration",
        f"Current: {last.get('task_id')}",
        f"Last verified task: "
        f"{last.get('verification_required')}",
        f"Continue gate: {last.get('continue_gate_result')}",
        f"Risk class: {last.get('risk_class')}",
        f"Needs Owner: {'Yes' if needs_owner else 'No'}",
        f"Vì sao: {last.get('why_stop_or_continue')}",
        "",
    ]))


def main(argv: list[str] | None = None) -> int:
    """CLI demo: python3 p2p_decision_runtime.py render <ledger> <project>"""
    import sys
    args = (argv or sys.argv[1:])
    if len(args) >= 3 and args[0] == "render":
        print(render_beginner_status(Path(args[1]), args[2]))
        return 0
    print("usage: p2p_decision_runtime.py render <ledger> <project>",
          file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
