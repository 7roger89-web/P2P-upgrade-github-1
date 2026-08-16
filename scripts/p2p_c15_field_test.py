#!/usr/bin/env python3
"""Run a safe project-style C15 field test against a disposable fixture.

The fixture uses the real C11 task store and C15 controller.  It never starts
an external process, network call, worker thread, scheduler, or background
job; the child callback is the explicitly supported foreground test surface.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable, Mapping


REPO_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = REPO_ROOT / ".p2p" / "system"
if str(SYSTEM_ROOT) not in sys.path:
    sys.path.insert(0, str(SYSTEM_ROOT))

from p2p_capabilities.bounded_delegation import (  # noqa: E402
    BLOCKED,
    DELEGATE,
    DIRECT,
    UNKNOWN_IDENTITY,
    BoundedDelegationController,
    DelegationRequest,
    PermissionEnvelope,
)
from p2p_capabilities.evidence import EvidenceClaim  # noqa: E402
from p2p_capabilities.task_state import TaskPlan, TaskStateStore  # noqa: E402


FIELD_NOW = "2026-08-16T00:00:00+00:00"
PARENT_SCOPE = ("src/*.py", "README.md")
CHILD_SCOPE = ("src/main.py",)


def _goal(goal_id: str) -> dict[str, Any]:
    return {
        "goal_id": goal_id,
        "scope": list(PARENT_SCOPE),
        "out_of_scope": [".p2p/state", "release", "network"],
        "completion_criteria": [{"criterion_id": "field-c15", "description": "verified fixture task"}],
    }


def _task(task_id: str) -> dict[str, Any]:
    return {
        "task_id": task_id,
        "title": f"Field fixture {task_id}",
        "purpose": "Inspect one bounded fixture file and return a verifiable proposal.",
        "scope": list(PARENT_SCOPE),
        "non_scope": [".p2p/state", "release", "network"],
        "acceptance_requirements": [f"acceptance-{task_id}"],
        "required_evidence": [f"evidence-{task_id}"],
    }


def _prepare(root: Path, task_id: str) -> BoundedDelegationController:
    (root / "src").mkdir(parents=True, exist_ok=True)
    (root / "src" / "main.py").write_text("VALUE = 'bounded-fixture'\n", encoding="utf-8")
    (root / "README.md").write_text("C15 safe project-style fixture\n", encoding="utf-8")
    plan = TaskPlan.from_goal(_goal(f"goal-{task_id}"), [_task(task_id)], now=FIELD_NOW)
    TaskStateStore(root).initialize(plan, at=FIELD_NOW)
    return BoundedDelegationController(root)


def _candidate() -> dict[str, str]:
    return {"fixture": "p2p-c15-field", "source_ref": "src/main.py", "mode": "READ_ONLY"}


def _request(controller: BoundedDelegationController, task_id: str, *, value_reasons: tuple[str, ...], task_size: str = "MODERATE", host: bool = True) -> DelegationRequest:
    return controller.request(
        task_id=task_id,
        task_size=task_size,
        value_reasons=value_reasons,
        candidate_state=_candidate(),
        host_child_available=host,
        parent_permissions=PermissionEnvelope(grants=("READ",), scope=PARENT_SCOPE),
        child_permissions=PermissionEnvelope(grants=("READ",), scope=CHILD_SCOPE),
        observed_identity=UNKNOWN_IDENTITY,
    )


def _claim(root: Path, task_id: str) -> EvidenceClaim:
    source = root / "src" / "main.py"
    fingerprint = hashlib.sha256(source.read_bytes()).hexdigest()
    return EvidenceClaim(
        claim="The parent verified the current bounded fixture file.",
        required_evidence=(f"evidence-{task_id}",),
        actual_evidence=(
            {
                "source": "scripts/p2p_c15_field_test.py",
                "evidence_ref": f"evidence-{task_id}",
                "origin": "RUNTIME_EVIDENCE",
                "observed_at": FIELD_NOW,
                "freshness": "CURRENT",
                "scope": ["src/main.py"],
                "source_binding": "p2p-c15-field-fixture",
                "fingerprint": fingerprint,
            },
        ),
        status="VERIFIED",
    )


def _summary(result: Mapping[str, Any], *, expected_strategy: str) -> dict[str, Any]:
    return {
        "status": result.get("status"),
        "strategy": result.get("strategy"),
        "reason": result.get("reason"),
        "task_id": result.get("task_id"),
        "task_status": result.get("task_status"),
        "expected_strategy": expected_strategy,
        "strategy_matches": result.get("strategy") == expected_strategy,
        "automatic_start": result.get("automatic_start"),
        "background_execution": result.get("background_execution"),
        "parallel_execution": result.get("parallel_execution"),
        "child_delegation_allowed": result.get("child_delegation_allowed"),
        "handoff_ref": result.get("handoff_ref"),
        "checkpoint_ref": result.get("checkpoint_ref"),
    }


def _run_case(case_id: str, fn: Callable[[Path], dict[str, Any]]) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(dir=REPO_ROOT / ".tmp", prefix=f"p2p-c15-field-{case_id}-") as raw:
        root = Path(raw)
        result = fn(root)
        result["case_id"] = case_id
        result["fixture_kind"] = "disposable_project_with_real_task_state"
        return result


def _case_a_direct(root: Path) -> dict[str, Any]:
    task_id = "direct"
    controller = _prepare(root, task_id)
    request = _request(controller, task_id, value_reasons=(), task_size="SMALL")

    def action(runtime: Any) -> dict[str, Any]:
        return {"status": "SUCCEEDED", "summary": runtime.read_text("src/main.py")}

    def verify(runtime: Any, action_result: Mapping[str, Any]) -> dict[str, Any]:
        return {"status": "VERIFIED", "evidence_claims": [_claim(root, task_id)], "candidate_state": {"file": runtime.read_text("src/main.py")}}

    result = controller.execute(request, direct_action=action, direct_verify=verify)
    return {"acceptance": "A", "detail": _summary(result, expected_strategy=DIRECT)}


def _delegated_request(controller: BoundedDelegationController, task_id: str) -> DelegationRequest:
    return _request(controller, task_id, value_reasons=("SPECIALIST_ANALYSIS", "CONTEXT_ISOLATION"))


def _case_b_and_d_verified(root: Path) -> dict[str, Any]:
    task_id = "delegated"
    controller = _prepare(root, task_id)
    request = _delegated_request(controller, task_id)
    decision = controller.decide(request)

    def child(handoff: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "handoff_id": handoff["handoff_id"],
            "task_id": handoff["task_id"],
            "outcome": "SUCCEEDED",
            "candidate_fingerprint": handoff["candidate_fingerprint"],
            "observed_identity": UNKNOWN_IDENTITY,
            "identity_authority": "UNKNOWN",
            "mutation_state": "KNOWN_NONE",
            "work_performed": ["read-only specialist inspection"],
            "artifact_refs": ["src/main.py"],
            "self_checks": ["scope stayed inside src/main.py"],
        }

    def verify(result: Mapping[str, Any], handoff: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "status": "VERIFIED",
            "summary": "parent reread the fixture and checked current evidence",
            "evidence_claims": [_claim(root, task_id)],
            "candidate_state": {"candidate_fingerprint": handoff["candidate_fingerprint"]},
        }

    result = controller.execute(request, child_executor=child, verify=verify)
    summary = _summary(result, expected_strategy=DELEGATE)
    summary.update({"decision_strategy": decision.get("strategy"), "proposal_only": result.get("output_is_evidence") is False})
    return {"acceptance": ["B", "D"], "detail": summary}


def _case_c_reject(root: Path) -> dict[str, Any]:
    task_id = "reject"
    controller = _prepare(root, task_id)
    request = _delegated_request(controller, task_id)

    def child(handoff: Mapping[str, Any]) -> dict[str, Any]:
        return {"outcome": "SUCCEEDED", "candidate_fingerprint": handoff["candidate_fingerprint"]}

    result = controller.execute(
        request,
        child_executor=child,
        verify=lambda _result, _handoff: {"status": "FAILED", "summary": "required evidence was incomplete"},
    )
    return {"acceptance": "C", "detail": _summary(result, expected_strategy=DELEGATE)}


def _case_e_no_grandchild(root: Path) -> dict[str, Any]:
    task_id = "no-grandchild"
    controller = _prepare(root, task_id)
    request = _delegated_request(controller, task_id)

    def child(handoff: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "outcome": "SUCCEEDED",
            "candidate_fingerprint": handoff["candidate_fingerprint"],
            "child_delegation_allowed": True,
        }

    result = controller.execute(request, child_executor=child)
    return {"acceptance": "E", "detail": _summary(result, expected_strategy=BLOCKED)}


def _case_f_resume(root: Path) -> dict[str, Any]:
    task_id = "resume"
    controller = _prepare(root, task_id)
    request = _delegated_request(controller, task_id)

    def interrupted(_handoff: Mapping[str, Any]) -> dict[str, Any]:
        raise RuntimeError("fixture foreground interruption")

    result = controller.execute(request, child_executor=interrupted)
    stored = TaskStateStore(root).require()
    task = stored.tasks[task_id]
    checkpoint = task.checkpoint or {}
    resume = TaskStateStore(root).resume(current_state_fingerprints={task_id: checkpoint.get("state_fingerprint", "")})
    detail = _summary(result, expected_strategy=DELEGATE)
    detail.update(
        {
            "persisted_task_status": task.status,
            "checkpoint_classification": checkpoint.get("recovery_classification"),
            "resume_classification": resume["tasks"][0]["resume_classification"],
            "resume_automatic_start": resume["automatic_start"],
        }
    )
    return {"acceptance": "F", "detail": detail}


def run_field_test() -> dict[str, Any]:
    cases = [
        _run_case("a-direct", _case_a_direct),
        _run_case("b-d-delegated", _case_b_and_d_verified),
        _run_case("c-reject", _case_c_reject),
        _run_case("e-no-grandchild", _case_e_no_grandchild),
        _run_case("f-resume", _case_f_resume),
    ]
    checks = {
        "A_direct": cases[0]["detail"]["strategy_matches"] and cases[0]["detail"]["status"] == "DONE",
        "B_delegate": cases[1]["detail"]["decision_strategy"] == DELEGATE,
        "C_reject": cases[2]["detail"]["status"] == "VERIFICATION_FAILED",
        "D_done": cases[1]["detail"]["status"] == "DONE" and cases[1]["detail"]["proposal_only"],
        "E_no_grandchild": cases[3]["detail"]["status"] == "CONTROL_PLANE_ERROR" and cases[3]["detail"]["child_delegation_allowed"] is False,
        "F_resume": cases[4]["detail"]["persisted_task_status"] == "ACTIVE" and cases[4]["detail"]["resume_classification"] == "SAFE_TO_RESUME" and cases[4]["detail"]["resume_automatic_start"] is False,
    }
    return {
        "schema": "p2p-c15-field-test/1",
        "runtime": "local-supported-foreground-callback",
        "synthetic_host_identity": False,
        "no_external_side_effects": True,
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "cases": cases,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the bounded C15 project-style field fixture")
    parser.add_argument("--output", help="optional repo-local JSON evidence path")
    args = parser.parse_args(argv)
    payload = run_field_test()
    if args.output:
        target = (REPO_ROOT / args.output).resolve() if not Path(args.output).is_absolute() else Path(args.output).resolve()
        try:
            target.relative_to(REPO_ROOT.resolve())
        except ValueError as exc:
            raise SystemExit("FIELD_TEST_OUTPUT_MUST_BE_REPO_LOCAL") from exc
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if payload["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
