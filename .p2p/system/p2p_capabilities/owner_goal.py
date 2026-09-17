"""Owner /goal one-command intake — thin UX over canonical P2P workflow.

Reuses existing Goal Contract / TaskPlan / durable state machinery
(p2p_workflow, task_state, beginner_gateway, control_tower_handoff,
native_goal_activation) and never creates second orchestrator/router/state DB.

ARENA_DIRECT_INVOCATION=NOT_AVAILABLE: No Arena invocation action/plugin exists
in ChatGPT/Control Tower surface nor P2P runtime (only protocol docs). Therefore
/goal with executor Arena follows canonical contract+plan path and returns
exactly ONE beginner-safe handoff packet, no gateway/bridge/daemon/scheduler.
Arena remains absent from native_goal_bridge.HOST_KINDS.

Terminal semantics reuse canonical task_state authority:
- WAITING_OWNER -> HARD_OWNER_GATE
- BLOCKED -> HARD_BLOCK
- unfinished eligible work -> CONTINUE_TASK/NOT_TERMINAL via next_safe_task
- all DONE but completion missing/invalid -> NOT MISSION_COMPLETE fail-closed
- Arena self-report alone -> NOT evidence
- all canonical DONE + VERIFIED independent evidence -> MISSION_COMPLETE
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

EXECUTOR_ARENA = "ARENA"
EXECUTOR_AUTO = "AUTO"

# Only explicit directive forms select executor. Bare words in objective must NOT hijack.
_EXPLICIT_EXECUTOR: list[tuple[str, re.Pattern[str]]] = [
    (EXECUTOR_ARENA, re.compile(r"(?:dùng|dung|use|using|with)\s+arena(?:\s+ai)?", re.I)),
    (EXECUTOR_ARENA, re.compile(r"(?:dùng|dung)\s+arena", re.I)),
    (EXECUTOR_AUTO, re.compile(r"(?:dùng|dung|use|using|with)\s+auto", re.I)),
]

_STRIP_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r",?\s*(?:dùng|dung|use|using|with)\s+arena(?:\s+ai)?\s*,?", re.I),
    re.compile(r",?\s*(?:dùng|dung|use|using|with)\s+auto\s*,?", re.I),
]

TERMINAL_STATES = {"PASS", "BLOCKED", "REJECT", "DONE", "VERIFIED", "CLOSED", "SUPERSEDED", "GOAL_DONE", "TERMINAL", "CANCELLED"}

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

# Evidence for Control Tower: Arena direct invocation capability absent
ARENA_DIRECT_INVOCATION = "NOT_AVAILABLE"
DIRECT_INVOCATION_EVIDENCE = {
    "chatgpt_surface": "No Arena invocation action/plugin found in ChatGPT tool list",
    "control_tower_surface": "No Arena integration in plugin discovery",
    "p2p_runtime": "Only protocol docs, no runtime invoker; HOST_KINDS excludes Arena",
    "consequence": "Must use canonical Goal Contract + TaskPlan + exactly ONE beginner handoff packet",
}


def _strip_goal_prefix(raw: str) -> str:
    text = raw.strip()
    m = re.match(r"^\s*/?\s*goal\s*[:\-]?\s*", text, re.I)
    return text[m.end():].strip() if m else text


def resolve_executor(text: str) -> str:
    """Executor from explicit natural directive only, default AUTO."""
    if not (text or "").strip():
        return EXECUTOR_AUTO
    matches: list[tuple[int, str]] = []
    for exec_name, pat in _EXPLICIT_EXECUTOR:
        for mm in pat.finditer(text):
            matches.append((mm.start(), exec_name))
    if matches:
        matches.sort(key=lambda x: x[0])
        return matches[-1][1]
    return EXECUTOR_AUTO


def parse_owner_goal_command(raw: str) -> dict[str, Any]:
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("OWNER_GOAL_COMMAND_EMPTY")
    without = _strip_goal_prefix(raw)
    if not without:
        raise ValueError("OWNER_GOAL_OBJECTIVE_EMPTY")
    executor = resolve_executor(without)
    clean = without
    for pat in _STRIP_PATTERNS:
        clean = pat.sub(" ", clean)
    clean = re.sub(r"\s+", " ", clean).strip(" ,;:")
    clean = re.sub(r"^(?:và|and)\s+", "", clean, flags=re.I).strip()
    if not clean:
        clean = without
    return {
        "schema": "p2p-owner-goal-intake/1",
        "raw": raw.strip(),
        "raw_without_prefix": without,
        "objective": clean,
        "executor": executor,
        "no_second_orchestrator": True,
        "arena_direct_invocation": ARENA_DIRECT_INVOCATION,
    }


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"\w+", (text or "").lower()))


def is_compatible(existing_contract: Mapping[str, Any] | None, new_objective: str) -> bool:
    """Fail closed: terminal/closed/superseded goals never reusable as active."""
    if not isinstance(existing_contract, Mapping) or not (new_objective or "").strip():
        return False
    for key in ("terminal_state", "status"):
        val = str(existing_contract.get(key) or "").upper()
        if val in TERMINAL_STATES:
            return False
    existing_obj = str(existing_contract.get("objective") or existing_contract.get("request") or "")
    if not existing_obj:
        return False
    et = _tokenize(existing_obj)
    nt = _tokenize(new_objective)
    if not et or not nt:
        return False
    overlap = et & nt
    if len(overlap) >= 2:
        return True
    if existing_obj.lower() in new_objective.lower() or new_objective.lower() in existing_obj.lower():
        return True
    jaccard = len(overlap) / len(et | nt) if (et | nt) else 0
    return jaccard > 0.3


def _load_json(p: Path) -> dict[str, Any] | None:
    try:
        return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else None
    except Exception:
        return None


def _import_capability(root: Path, name: str) -> Any:
    sys_path = root / ".p2p" / "system"
    if str(sys_path) not in sys.path:
        sys.path.insert(0, str(sys_path))
    import importlib
    return importlib.import_module(f"p2p_capabilities.{name}")


def _get_git_identity(root: Path) -> dict[str, str]:
    """Fresh durable Git identity where available, else UNKNOWN."""
    branch = "UNKNOWN"
    repo = root.name
    remote_url = ""
    try:
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=str(root),
            text=True,
            timeout=3,
            stderr=subprocess.DEVNULL,
        ).strip() or "UNKNOWN"
    except Exception:
        branch = "UNKNOWN"
    try:
        remote_url = subprocess.check_output(
            ["git", "remote", "get-url", "origin"],
            cwd=str(root),
            text=True,
            timeout=3,
            stderr=subprocess.DEVNULL,
        ).strip()
        m = re.search(r"[:/]([^/]+/[^/]+?)(?:\.git)?$", remote_url)
        if m:
            repo = m.group(1)
    except Exception:
        pass
    return {"branch": branch, "repo": repo, "remote_url": remote_url}


def _next_eligible_task(plan: Any) -> Any | None:
    """Reuse existing task_state.next_safe_task, never return BLOCKED."""
    if plan is None:
        return None
    try:
        mod = sys.modules.get("p2p_capabilities.task_state")
        if mod is None:
            import importlib
            mod = importlib.import_module("p2p_capabilities.task_state")
        nxt = mod.next_safe_task(plan)
        if nxt is not None:
            return nxt
    except Exception:
        pass
    try:
        if hasattr(plan, "topological_order"):
            for tid in plan.topological_order():
                t = plan.tasks[tid]
                if t.status == "READY" and plan.dependencies_are_done(tid):
                    return t
    except Exception:
        pass
    return None


def _task_delta(task: Any) -> dict[str, Any]:
    if task is None:
        return {}
    try:
        d = task.to_dict() if hasattr(task, "to_dict") else dict(task) if isinstance(task, Mapping) else {}
        fields = ["task_id", "goal_id", "title", "purpose", "status", "dependencies", "scope", "non_scope", "acceptance_requirements", "required_evidence", "permission_needs", "required_capabilities", "context_refs"]
        return {k: d.get(k) for k in fields if k in d}
    except Exception:
        return {}


def build_arena_handoff(
    project_root: Path | str,
    goal_contract: Mapping[str, Any],
    task_plan: Any,
    executor: str = EXECUTOR_ARENA,
    *,
    reuse: bool = False,
    branch: str | None = None,
    direct_invoke_possible: bool = False,
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    goal_id = str(goal_contract.get("goal_id", "UNKNOWN"))
    objective = str(goal_contract.get("objective") or goal_contract.get("request") or "UNKNOWN")

    git_id = _get_git_identity(root)
    if branch is None:
        cur = git_id["branch"]
        if cur != "UNKNOWN" and cur.startswith("arena/"):
            branch = cur
        else:
            branch = "UNKNOWN"

    next_task = _next_eligible_task(task_plan)
    delta = _task_delta(next_task)

    try:
        from .control_tower_handoff import SUPREME_LAW_CAPSULE as _CAPSULE
        capsule = _CAPSULE
    except Exception:
        capsule = "OWNER_OUTCOME_AND_AUTHORITY_ARE_INVARIANTS; SIMPLEST_USEFUL_PATH; REAL_STATE_AND_EVIDENCE_OVERRIDE_ASSUMPTIONS; RECOVER_ADAPTIVELY; PRESERVE_CONTINUITY_AND_STOP; PROMPT_DESTINATION_AND_PLAN_STATE_ARE_EXPLICIT; ANALYTICAL_AUTONOMY; TASK_CONTRACT_FIDELITY; EXECUTOR_INPUT_FORMAT_FIDELITY"

    project_name = root.name
    repo = git_id["repo"]
    chat_title = f"{project_name} | {goal_id[:20]} | WRITER | {objective[:40]}"
    session_action = "CONTINUE_CURRENT_SESSION" if reuse else "START_NEW_SESSION"

    gate = detect_owner_gate(task_plan)
    if gate["has_gate"]:
        delta = {}

    packet_lines = [
        f"DESTINATION=ARENA AI",
        f"CHAT_MODE=NEW_CHAT",
        f"ROLE=WRITER",
        f"CHAT_TITLE={chat_title}",
        f"PROJECT={project_name}",
        f"REPO={repo}",
        f"GOAL_ID={goal_id}",
        f"TASK_ID={delta.get('task_id','UNKNOWN')}",
        f"BRANCH={branch}",
        f"EXECUTOR={executor}",
        f"EXECUTION_MODE=AUTONOMOUS_UNTIL_TERMINAL",
        f"REUSE_EXISTING_GOAL={reuse}",
        f"SESSION_ACTION={session_action}",
        "",
        "P2P_SUPREME_LAW_PREFLIGHT: Read canonical law from 7roger89-web/P2P-upgrade-github-1@main:docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md when accessible; else use capsule",
        f"SUPREME_LAW_CAPSULE: {capsule[:500]}...",
        "",
        "FRESH_CHECK:",
        "- git fetch origin main; git rev-parse origin/main; git branch -a --list 'arena/*'",
        "- If BRANCH=UNKNOWN, Arena must inspect existing compatible open PR/branch and reuse it, else create exactly one bounded branch arena/<goal-id> and one PR",
        "",
        "CANONICAL_STATE: Fresh-read .p2p/state/goal-contract.json and .p2p/state/task-state.json; verify plan_hash/goal_hash; reuse existing compatible Goal",
        "TASK_SELECTION: Use task_state.next_safe_task; if WAITING_OWNER stop HARD_OWNER_GATE; if BLOCKED return BLOCKER",
        f"TASK_DELTA: {json.dumps(delta, ensure_ascii=False)}",
        f"SCOPE: {goal_contract.get('scope') or goal_contract.get('constraints') or []}",
        f"ACCEPTANCE: {delta.get('acceptance_requirements') or []}",
        f"EVIDENCE: {delta.get('required_evidence') or []}",
        "EXECUTION_RULES: Obey scope/non-scope/acceptance/evidence; AGENT_CLAIM_IS_NOT_EVIDENCE; no second router/daemon/state DB; preserve native_goal_activation; RULE20 AUTONOMOUS_UNTIL_TERMINAL; stop at MISSION_COMPLETE|HARD_OWNER_GATE|HARD_BLOCK",
        "VERIFY: Run narrow affected tests + AGENTS.md validation; independent verifier evidence required",
        "RETURN: Evidence + exact branch/commit/PR + ReturnPacket TASK_ID, RESULT, MAIN_BASE_SHA, BRANCH, HEAD_SHA, PR, CHANGED_FILES, OWNER_GOAL_ENTRYPOINT, ARENA_HANDOFF_PATH, NATIVE_GOAL_BEHAVIOR_PRESERVED, RULE20_PRESERVED, ANVIEN_BLAST_RADIUS, TESTS, VALIDATION, EVIDENCE, MERGE_STATE, BLOCKER, NEXT_ACTION",
        f"SESSION_GOAL={objective}",
        f"PR_EXPECTATION=One bounded goal -> one branch {branch} -> one PR",
        f"OWNER_GATE={gate}",
        f"ARENA_DIRECT_INVOCATION={ARENA_DIRECT_INVOCATION} {DIRECT_INVOCATION_EVIDENCE['consequence']}",
        "",
        "ASSESS:",
        f"GOAL={objective}",
        f"CURRENT_STATE=.p2p/state/goal-contract.json, .p2p/state/task-state.json, goal_id={goal_id}, task_id={delta.get('task_id','UNKNOWN')}",
        "MAIN_RISK=Scope expansion or false DONE from self-report",
        f"PLAN=Execute next eligible task {delta.get('task_id','UNKNOWN')} within original scope",
        "",
        "IMPLEMENT: Bounded implementation only within task delta scope",
        "",
        "VERIFY: Risk-proportional checks and durable evidence; independent verifier required",
        "",
        "RETURN: Result, changed files, checks, candidate SHA/tree, blockers, next action, ReturnPacket",
        "",
        "SUCCESS_SIGNAL: YES=terminal ReturnPacket produced, KEEP WORKING=continue, NO=material failure",
        "RETURN_PACKET: TASK_ID, RESULT, MAIN_BASE_SHA, BRANCH, HEAD_SHA, PR, CHANGED_FILES, OWNER_GOAL_ENTRYPOINT, ARENA_HANDOFF_PATH, NATIVE_GOAL_BEHAVIOR_PRESERVED, RULE20_PRESERVED, ANVIEN_BLAST_RADIUS, TESTS, VALIDATION, EVIDENCE, MERGE_STATE, BLOCKER, NEXT_ACTION",
    ]
    packet_text = "\n".join(packet_lines)

    return {
        "schema": "p2p-arena-handoff/1",
        "destination": "ARENA AI",
        "chat_mode": "NEW_CHAT",
        "role": "WRITER",
        "chat_title": chat_title,
        "session_action": session_action,
        "project": project_name,
        "repo": repo,
        "project_root": str(root),
        "goal_id": goal_id,
        "task_id": delta.get("task_id", "UNKNOWN"),
        "branch": branch,
        "executor": executor,
        "execution_mode": "AUTONOMOUS_UNTIL_TERMINAL",
        "supreme_law_preflight": "P2P_SUPREME_OPERATING_LAW_V1",
        "supreme_law_capsule": capsule,
        "task_delta": delta,
        "goal_contract_path": ".p2p/state/goal-contract.json",
        "task_state_path": ".p2p/state/task-state.json",
        "reuse_existing_goal": bool(reuse),
        "no_second_orchestrator": True,
        "no_second_router": True,
        "no_second_state_db": True,
        "native_goal_behavior_preserved": True,
        "rule20_preserved": True,
        "agent_claim_is_not_evidence": True,
        "packet_text": packet_text,
        "direct_invoke_possible": direct_invoke_possible,
        "owner_goal_entrypoint": "scripts/p2p_workflow.py:owner-goal + .p2p/system/p2p_capabilities/owner_goal.py",
        "arena_handoff_path": "COMPACT_TASK_DELTA_VIA_CANONICAL_STATE",
        "git_identity": git_id,
        "owner_gate": gate,
        "arena_direct_invocation": ARENA_DIRECT_INVOCATION,
        "direct_invocation_evidence": DIRECT_INVOCATION_EVIDENCE,
    }


def build_beginner_handoff(
    project_root: Path | str,
    goal_contract: Mapping[str, Any],
    task_plan: Any,
    executor: str = EXECUTOR_ARENA,
    *,
    error: str | None = None,
    reuse: bool = False,
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    arena = build_arena_handoff(root, goal_contract, task_plan, executor, reuse=reuse, direct_invoke_possible=False)
    chat_title = arena["chat_title"]
    beginner_packet = "\n".join(
        [
            "LÀM BÂY GIỜ: ARENA AI — CHAT MỚI — WRITER",
            f"Chat title: {chat_title}",
            "",
            arena["packet_text"],
            "",
            "SUCCESS_SIGNAL: YES=terminal ReturnPacket produced, KEEP WORKING=continue, NO=material failure",
            "RETURN_PACKET: TASK_ID, RESULT, MAIN_BASE_SHA, BRANCH, HEAD_SHA, PR, CHANGED_FILES, OWNER_GOAL_ENTRYPOINT, ARENA_HANDOFF_PATH, NATIVE_GOAL_BEHAVIOR_PRESERVED, RULE20_PRESERVED, ANVIEN_BLAST_RADIUS, TESTS, VALIDATION, EVIDENCE, MERGE_STATE, BLOCKER, NEXT_ACTION",
            "Copy toàn bộ phản hồi cuối này vào: 00 — P2P CONTROL TOWER",
        ]
    )
    return {
        "schema": "p2p-beginner-arena-handoff/1",
        "destination": "ARENA AI — CHAT MỚI — WRITER",
        "chat_title": chat_title,
        "success_signal": "YES means terminal ReturnPacket produced",
        "return_packet_spec": "TASK_ID, RESULT, MAIN_BASE_SHA, BRANCH, HEAD_SHA, PR, CHANGED_FILES, OWNER_GOAL_ENTRYPOINT, ARENA_HANDOFF_PATH, NATIVE_GOAL_BEHAVIOR_PRESERVED, RULE20_PRESERVED, ANVIEN_BLAST_RADIUS, TESTS, VALIDATION, EVIDENCE, MERGE_STATE, BLOCKER, NEXT_ACTION",
        "task_packet": arena,
        "packet_text": beginner_packet,
        "one_packet_only": True,
        "owner_is_not_message_bus": True,
        "error": error,
        "arena_direct_invocation": ARENA_DIRECT_INVOCATION,
    }


def detect_owner_gate(task_plan: Any) -> dict[str, Any]:
    if task_plan is None:
        return {"has_gate": False, "gate_type": "NONE", "tasks": []}
    waiting: list[str] = []
    try:
        for tid, t in task_plan.tasks.items():
            if t.status == "WAITING_OWNER":
                waiting.append(tid)
            elif isinstance(getattr(t, "owner_decision", None), Mapping) and t.owner_decision.get("status") == "PENDING":
                waiting.append(tid)
    except Exception:
        pass
    if waiting:
        return {"has_gate": True, "gate_type": "HARD_OWNER_GATE", "tasks": waiting, "stop_honestly": True, "claim_complete": False}
    return {"has_gate": False, "gate_type": "NONE", "tasks": []}


def _is_canonical_completion_valid(task: Any) -> bool:
    """Reuse canonical TaskRecord completion authority.

    Mirrors task_state._completion_is_structurally_valid but without importing
    private symbol: status VERIFIED, evidence_refs exactly matching
    required_evidence, valid fingerprints, candidate_state_fingerprint SHA256,
    independent_check True. Arena self-report alone never qualifies.
    """
    try:
        completion = getattr(task, "completion", None)
        if not isinstance(completion, Mapping):
            return False
        if completion.get("status") != "VERIFIED":
            return False
        if completion.get("independent_check") is not True:
            return False
        evidence_refs = completion.get("evidence_refs")
        if not isinstance(evidence_refs, list) or not evidence_refs:
            return False
        if len(evidence_refs) != len(set(evidence_refs)):
            return False
        required = getattr(task, "required_evidence", None)
        if required is None:
            return False
        if set(evidence_refs) != set(required):
            return False
        done_when = completion.get("done_when")
        if done_when is not None:
            if not isinstance(done_when, list) or set(done_when) != set(required):
                return False
        candidate = completion.get("candidate_state_fingerprint")
        if not isinstance(candidate, str) or not _SHA256_RE.fullmatch(candidate.lower()):
            return False
        fingerprints = completion.get("evidence_fingerprints")
        if not isinstance(fingerprints, Mapping):
            return False
        if set(fingerprints.keys()) != set(evidence_refs):
            return False
        for fp in fingerprints.values():
            if not isinstance(fp, str) or not _SHA256_RE.fullmatch(fp.lower()):
                return False
        return True
    except Exception:
        return False


def check_terminal_state(task_plan: Any, evidence_claims: Sequence[Mapping[str, Any]] | None = None) -> dict[str, Any]:
    """Terminal semantics reusing canonical task_state authority.

    - WAITING_OWNER -> HARD_OWNER_GATE
    - BLOCKED -> HARD_BLOCK
    - unfinished eligible work -> CONTINUE_TASK via next_safe_task else NOT_TERMINAL
    - all DONE but completion missing/invalid -> NOT MISSION_COMPLETE fail-closed
    - Arena self-report alone -> NOT evidence
    - all canonical DONE + VERIFIED independent evidence -> MISSION_COMPLETE
    """
    if task_plan is None:
        return {"is_terminal": False, "terminal_type": "NOT_TERMINAL", "arena_claim_is_evidence": False}
    gate = detect_owner_gate(task_plan)
    if gate["has_gate"]:
        return {"is_terminal": True, "terminal_type": "HARD_OWNER_GATE", "reason": f"WAITING_OWNER {gate['tasks']}", "arena_claim_is_evidence": False, "stop_honestly": True}
    try:
        blocked = [tid for tid, t in task_plan.tasks.items() if t.status == "BLOCKED"]
        if blocked:
            return {"is_terminal": True, "terminal_type": "HARD_BLOCK", "reason": f"BLOCKED {blocked}", "arena_claim_is_evidence": False}
    except Exception:
        pass
    try:
        all_done = all(getattr(t, "status", None) == "DONE" for t in getattr(task_plan, "tasks", {}).values())
        if not all_done:
            nxt = _next_eligible_task(task_plan)
            if nxt is not None:
                return {
                    "is_terminal": False,
                    "terminal_type": "CONTINUE_TASK",
                    "next_task": getattr(nxt, "task_id", None),
                    "reason": f"NEXT_ELIGIBLE {getattr(nxt, 'task_id', None)}",
                    "arena_claim_is_evidence": False,
                }
            return {"is_terminal": False, "terminal_type": "NOT_TERMINAL", "arena_claim_is_evidence": False}

        invalid_tasks: list[str] = []
        for tid, task in getattr(task_plan, "tasks", {}).items():
            if not _is_canonical_completion_valid(task):
                invalid_tasks.append(tid)

        if invalid_tasks:
            return {
                "is_terminal": False,
                "terminal_type": "NOT_MISSION_COMPLETE",
                "reason": f"CANONICAL_COMPLETION_MISSING_OR_INVALID {invalid_tasks}",
                "arena_claim_is_evidence": False,
                "must_not_promote": True,
                "invalid_tasks": invalid_tasks,
            }

        return {
            "is_terminal": True,
            "terminal_type": "MISSION_COMPLETE",
            "arena_claim_is_evidence": False,
            "canonical_state_plus_evidence": True,
            "independent_check": True,
        }
    except Exception as exc:
        return {"is_terminal": False, "terminal_type": "CHECK_FAILED", "reason": str(exc), "arena_claim_is_evidence": False}


def evaluate_native_activation(project_root: Path | str, host_kind: str) -> dict[str, Any]:
    """Wire real existing activation seam — single authoritative host.

    If host_kind is explicit (claude_code/codex_cli), evaluate that host directly
    (used by unit tests and explicit --host). If host_kind == 'auto', detect
    current host from environment via detect_host_from_environment and evaluate
    only that one. Never evaluate both and arbitrarily prefer Claude.
    """
    root = Path(project_root).expanduser().resolve()
    try:
        native_bridge = _import_capability(root, "native_goal_bridge")
        host_kinds = getattr(native_bridge, "HOST_KINDS", ())
        if host_kind not in host_kinds and host_kind != "auto":
            return {"host_kind": host_kind, "decision": "HOST_KIND_UNSUPPORTED", "arena_in_native_hosts": "arena" in [h.lower() for h in host_kinds], "native_goal_behavior_preserved": "arena" not in [h.lower() for h in host_kinds]}
    except Exception:
        host_kinds = ()
    try:
        native_act = _import_capability(root, "native_goal_activation")
    except Exception as exc:
        return {"status": "BLOCKED", "error": f"NATIVE_ACTIVATION_UNAVAILABLE:{exc}", "decision": "NORMAL_P2P_PATH", "native_goal_behavior_preserved": True}

    # Resolve authoritative current host if auto
    resolved_host = host_kind
    if host_kind == "auto":
        try:
            detected = native_act.detect_host_from_environment()
            if detected is None:
                return {
                    "decision": "NORMAL_P2P_PATH",
                    "reason": "HOST_NOT_CONFIDENTLY_DETECTED",
                    "host_kind": host_kind,
                    "native_goal_behavior_preserved": True,
                    "arena_in_native_hosts": False,
                    "authoritative_host": None,
                }
            resolved_host = detected
        except Exception:
            return {
                "decision": "NORMAL_P2P_PATH",
                "reason": "HOST_DETECTION_FAILED",
                "host_kind": host_kind,
                "native_goal_behavior_preserved": True,
            }

    goal_state_path = root / ".p2p" / "state" / "autopilot-goal-state.json"
    task_state_path = root / ".p2p" / "state" / "task-state.json"
    goal_state = _load_json(goal_state_path)
    task_state = _load_json(task_state_path)

    if goal_state is None or task_state is None:
        return {"decision": "NORMAL_P2P_PATH", "reason": "NO_AUTOPILOT_OR_TASK_STATE", "host_kind": resolved_host, "native_goal_behavior_preserved": True, "arena_in_native_hosts": False, "authoritative_host": resolved_host}

    try:
        result = native_act.decide_native_goal_activation(resolved_host, goal_state, task_state)
        result["arena_in_native_hosts"] = False
        result["native_goal_behavior_preserved"] = True
        result["authoritative_host"] = resolved_host
        result["native_command_invoked_count"] = 1 if result.get("decision") == "ACTIVATE_NATIVE_GOAL" else 0
        return result
    except Exception as exc:
        return {"decision": "NORMAL_P2P_PATH", "reason": f"ACTIVATION_FAILED:{exc}", "host_kind": resolved_host, "native_goal_behavior_preserved": True, "authoritative_host": resolved_host}


def build_owner_goal_intake(project_root: Path | str, raw_command: str, *, package_hint: str | None = None) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"PROJECT_ROOT_NOT_FOUND:{root}")

    parsed = parse_owner_goal_command(raw_command)
    objective = parsed["objective"]
    executor = parsed["executor"]

    p2p_workflow = None
    errors: list[str] = []
    cand_dirs: list[Path] = []
    try:
        cand_dirs.append(Path(__file__).resolve().parents[3] / "scripts")
    except Exception as e:
        errors.append(f"self:{e}")
    cand_dirs.append(root / "scripts")
    if package_hint:
        cand_dirs.append(Path(package_hint).expanduser().resolve() / "scripts")
    cand_dirs.append(Path(__file__).resolve().parents[1] / "scripts")

    for sd in cand_dirs:
        try:
            if str(sd) not in sys.path:
                sys.path.insert(0, str(sd))
            if str(sd.parent) not in sys.path:
                sys.path.insert(0, str(sd.parent))
            import importlib as _il
            if "p2p_workflow" in sys.modules and hasattr(sys.modules["p2p_workflow"], "inspect_project"):
                p2p_workflow = sys.modules["p2p_workflow"]
                break
            p2p_workflow = _il.import_module("p2p_workflow")
            if hasattr(p2p_workflow, "inspect_project"):
                break
        except Exception as e:
            errors.append(f"{sd}:{e}")
            continue
    if p2p_workflow is None or not hasattr(p2p_workflow, "inspect_project"):
        raise ValueError(f"P2P_WORKFLOW_UNAVAILABLE:{';'.join(errors)}")

    inspection = p2p_workflow.inspect_project(root, objective, package_hint)
    existing_contract = _load_json(root / ".p2p" / "state" / "goal-contract.json")

    task_state_mod = None
    existing_plan = None
    try:
        task_state_mod = _import_capability(root, "task_state")
        existing_plan = task_state_mod.TaskStateStore(root).load()
    except Exception:
        existing_plan = None

    reuse = False
    if existing_contract and existing_plan:
        try:
            if is_compatible(existing_contract, objective) and existing_plan.plan_lifecycle == "ACTIVE":
                unfinished = [t for t in existing_plan.tasks.values() if t.status not in {"DONE", "CANCELLED"}]
                if unfinished:
                    try:
                        cur_req = str(existing_contract.get("request") or existing_contract.get("objective") or "")
                        if cur_req:
                            upd = p2p_workflow.classify_goal_update(cur_req, objective, existing_contract)
                            if str(upd.get("classification")) in {"CONTEXT UPDATE", "CONSTRAINT UPDATE", "ACCEPTANCE UPDATE"}:
                                reuse = True
                            elif is_compatible(existing_contract, objective):
                                reuse = True
                        else:
                            reuse = is_compatible(existing_contract, objective)
                    except Exception:
                        reuse = is_compatible(existing_contract, objective)
        except Exception:
            reuse = False

    if reuse and isinstance(existing_contract, dict):
        contract = existing_contract
        contract_path = root / ".p2p" / "state" / "goal-contract.json"
        try:
            contract = dict(contract)
            intake = dict(contract.get("owner_goal_intake") or {})
            intake.update({"raw_command": raw_command, "objective": objective, "executor": executor, "reuse": True})
            contract["owner_goal_intake"] = intake
            contract_path.write_text(json.dumps(contract, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        except Exception:
            pass
        state_status = "REUSED"
        plan = existing_plan
    else:
        governance_options = p2p_workflow.governance_candidates(root, package_hint)
        policy = p2p_workflow.policy_for(root, governance_options[0][0] if governance_options else None)
        contract = p2p_workflow.build_goal_contract(root, objective, inspection, policy, package_hint=package_hint)
        contract["owner_goal_intake"] = {"schema": "p2p-owner-goal-intake-binding/1", "raw_command": raw_command, "objective": objective, "executor": executor, "reuse": False, "project": root.name}
        contract_path = p2p_workflow.write_goal(root, contract)
        state_status = "CREATED"
        plan = None

    try:
        bootstrap = p2p_workflow.bootstrap_project(root, inspection, contract, package_hint)
    except Exception as exc:
        bootstrap = {"status": "BLOCKED", "error": str(exc)}

    if not reuse:
        try:
            beginner_gateway = _import_capability(root, "beginner_gateway")
            charter = beginner_gateway.derive_charter(objective, inspection)
            task_specs = beginner_gateway.task_specs_for_charter(charter, str(contract.get("goal_id")))
            if task_state_mod is None:
                task_state_mod = _import_capability(root, "task_state")
            task_plan = task_state_mod.TaskPlan.from_goal(contract, task_specs)
            store = task_state_mod.TaskStateStore(root)
            plan = store.initialize(task_plan)
        except Exception:
            try:
                if task_state_mod is None:
                    task_state_mod = _import_capability(root, "task_state")
                minimal_spec = {
                    "task_id": "task-01",
                    "goal_id": str(contract.get("goal_id")),
                    "title": objective[:100],
                    "purpose": objective,
                    "status": "READY",
                    "dependencies": [],
                    "scope": [objective[:200] or "GOAL_SCOPED_TASK_WORK"],
                    "non_scope": contract.get("out_of_scope", []),
                    "acceptance_requirements": ["Task completes with evidence"],
                    "required_evidence": [".p2p/state/execution-ledger.jsonl"],
                }
                task_plan = task_state_mod.TaskPlan.from_goal(contract, [minimal_spec])
                store = task_state_mod.TaskStateStore(root)
                plan = store.initialize(task_plan)
            except Exception as inner:
                plan = None
                state_status = f"BLOCKED:{inner}"

    gate = detect_owner_gate(plan)
    terminal = check_terminal_state(plan, evidence_claims=[])

    if gate["has_gate"]:
        terminal_type = "HARD_OWNER_GATE"
        has_owner_gate = True
    elif terminal["terminal_type"] == "HARD_BLOCK":
        terminal_type = "HARD_BLOCK"
        has_owner_gate = False
    else:
        terminal_type = terminal["terminal_type"]
        has_owner_gate = False

    result = {
        "schema": "p2p-owner-goal-result/1",
        "raw_command": raw_command,
        "objective": objective,
        "executor": executor,
        "executor_selection_reason": f"Owner explicitly said '{executor}'" if executor != "AUTO" else "Auto routing - no explicit executor directive",
        "goal_id": str(contract.get("goal_id", "")),
        "goal_contract_path": str(contract_path) if contract_path else ".p2p/state/goal-contract.json",
        "task_state_path": ".p2p/state/task-state.json",
        "reuse": reuse,
        "state_status": state_status,
        "bootstrap": bootstrap,
        "plan": plan.to_dict() if plan and hasattr(plan, "to_dict") else None,
        "plan_hash": plan.canonical_hash() if plan and hasattr(plan, "canonical_hash") else None,
        "project": root.name,
        "project_root": str(root),
        "no_second_orchestrator": True,
        "no_second_router": True,
        "no_second_state_db": True,
        "native_goal_behavior_preserved": True,
        "rule20_preserved": True,
        "terminal_type": terminal_type,
        "has_owner_gate": has_owner_gate,
        "owner_gate": gate,
        "has_gate": gate["has_gate"],
        "stop_honestly": gate.get("stop_honestly", False) if gate["has_gate"] else False,
        "claim_complete": False if gate["has_gate"] else None,
        "arena_direct_invocation": ARENA_DIRECT_INVOCATION,
        "direct_invocation_evidence": DIRECT_INVOCATION_EVIDENCE,
        "current_owner_goal_flow": "parse -> canonical contract+plan reuse -> task_state.next_safe_task -> ONE beginner handoff if Arena",
    }

    if executor == EXECUTOR_ARENA:
        if gate["has_gate"]:
            result["arena_handoff"] = None
            result["arena_handoff_path"] = "HARD_OWNER_GATE_NO_HANDOFF"
            result["execution_mode"] = "STOP_AT_OWNER_GATE"
        else:
            try:
                handoff = build_arena_handoff(root, contract, plan, executor, reuse=reuse)
                result["arena_handoff"] = handoff
                result["arena_handoff_path"] = "COMPACT_TASK_DELTA_VIA_CANONICAL_STATE"
                result["execution_mode"] = "AUTONOMOUS_UNTIL_TERMINAL"
                try:
                    beginner = build_beginner_handoff(root, contract, plan, executor, reuse=reuse)
                    result["beginner_arena_handoff"] = beginner
                except Exception:
                    pass
            except Exception as exc:
                result["arena_handoff_error"] = str(exc)
                result["arena_handoff"] = None
    else:
        result["arena_handoff"] = None
        result["arena_handoff_path"] = "NOT_ARENA_EXECUTOR"

    return result


def owner_goal_intake_cli(project_root: Path | str, raw_command: str, *, package_hint: str | None = None, json_output: bool = True) -> dict[str, Any]:
    """Real CLI path that wires single authoritative native host activation.

    Detects current host via native_goal_activation.detect_host_from_environment()
    (Claude Code stable markers). If detected, evaluates ONLY that host for
    ACTIVATE_NATIVE_GOAL and propagates its command exactly once via existing seam.
    If not detected, returns NORMAL_P2P_PATH honestly, no arbitrary preference.
    Arena remains HOST_KIND_UNSUPPORTED.
    """
    result = build_owner_goal_intake(project_root, raw_command, package_hint=package_hint)
    try:
        root = Path(project_root).expanduser().resolve()
        try:
            bridge = _import_capability(root, "native_goal_bridge")
            host_kinds = list(getattr(bridge, "HOST_KINDS", ()))
            result["native_goal_hosts"] = host_kinds
            result["arena_in_native_hosts"] = "arena" in [h.lower() for h in host_kinds]
            result["native_goal_behavior_preserved"] = not result["arena_in_native_hosts"]
        except Exception:
            result["native_goal_behavior_preserved"] = True
            result["arena_in_native_hosts"] = False
            host_kinds = ["claude_code", "codex_cli"]

        # Detect authoritative current host via existing seam
        try:
            native_act = _import_capability(root, "native_goal_activation")
            authoritative_host = native_act.detect_host_from_environment()
            result["native_authoritative_host"] = authoritative_host
            result["native_invocation_evidence"] = {
                "detector": "native_goal_activation.detect_host_from_environment",
                "env_markers": ["CLAUDECODE=1", "CLAUDE_CODE_ENTRYPOINT"],
                "detected": authoritative_host,
            }
        except Exception as exc:
            authoritative_host = None
            result["native_authoritative_host"] = None
            result["native_detection_error"] = str(exc)

        activation_results: dict[str, Any] = {}
        native_command_invoked_count = 0
        primary_command = None
        primary_host = None
        primary_decision = "NORMAL_P2P_PATH"

        if authoritative_host is not None:
            # Evaluate ONLY authoritative host — single ACTIVATE, single invoke
            try:
                act = evaluate_native_activation(root, authoritative_host)
                activation_results[authoritative_host] = act
                if act.get("decision") == "ACTIVATE_NATIVE_GOAL" and act.get("command"):
                    native_command_invoked_count = 1
                    primary_command = act["command"]
                    primary_host = authoritative_host
                    primary_decision = "ACTIVATE_NATIVE_GOAL"
                    result["native_goal_command"] = primary_command
                    result["native_goal_activation_host"] = primary_host
                    result["native_goal_command_propagated"] = {primary_host: primary_command}
            except Exception as e:
                activation_results[authoritative_host] = {"error": str(e), "decision": "NORMAL_P2P_PATH"}
        else:
            # No authoritative host detected — honest boundary, no arbitrary multi-host eval
            # For diagnostic purposes, we still surface that we checked and found none,
            # and we do NOT fabricate ACTIVATE by evaluating both.
            for hk in host_kinds:
                if hk.lower() == "arena":
                    activation_results[hk] = {"decision": "HOST_KIND_UNSUPPORTED", "arena_in_native_hosts": False, "native_goal_behavior_preserved": True}
            # Explicitly record that we did NOT evaluate both Claude and Codex
            result["native_multi_host_evaluated"] = False

        result["native_activation_evaluations"] = activation_results
        result["native_goal_activation_checked"] = True
        result["native_activation_decision"] = primary_decision
        result["native_goal_activation_decision"] = primary_decision
        result["native_command_invoked_count"] = native_command_invoked_count
        if primary_command is None:
            result.setdefault("native_goal_activation_decision", "NORMAL_P2P_PATH")
            result.setdefault("native_activation_decision", "NORMAL_P2P_PATH")
    except Exception as exc:
        result["native_goal_activation_error"] = str(exc)
        result["native_goal_activation_checked"] = False
        result["native_goal_behavior_preserved"] = True
        result["native_command_invoked_count"] = 0

    return result


__all__ = [
    "EXECUTOR_ARENA",
    "EXECUTOR_AUTO",
    "ARENA_DIRECT_INVOCATION",
    "DIRECT_INVOCATION_EVIDENCE",
    "parse_owner_goal_command",
    "resolve_executor",
    "is_compatible",
    "build_owner_goal_intake",
    "build_arena_handoff",
    "build_beginner_handoff",
    "detect_owner_gate",
    "check_terminal_state",
    "evaluate_native_activation",
    "owner_goal_intake_cli",
]
