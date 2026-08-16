#!/usr/bin/env python3
"""Prepare and finalize mandatory P2P release/deployment gates."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from p2p_approval import (
    ApprovalError,
    fingerprint_subject,
    load_json,
    sha256_file,
    validate_policy,
    validate_record,
)


PROJECT_POLICY_SCHEMA = "p2p-codex-project-policy/1"


class GateError(ValueError):
    pass


def write_json_new(path: Path, value: object) -> None:
    if path.exists():
        raise GateError(f"Refusing to overwrite gate artifact: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def default_governance(project: Path) -> Path:
    installed = project / ".p2p" / "system" / "governance"
    if installed.is_dir():
        return installed
    package = Path(__file__).resolve().parents[1] / "governance"
    return package


def default_helpers(project: Path) -> Path:
    installed = project / ".p2p" / "system" / "scripts"
    if installed.is_dir():
        return installed
    return Path(__file__).resolve().parent


def run_json(command: list[str]) -> tuple[int, dict]:
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    raw = result.stdout.strip()
    try:
        parsed = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        parsed = {"status": "FAIL", "failures": [(raw or result.stderr.strip())[:1200]]}
    if result.returncode != 0 and parsed.get("status") == "PASS":
        parsed["status"] = "FAIL"
    return result.returncode, parsed


def validate_project_policy(value: object) -> dict:
    if not isinstance(value, dict) or value.get("schema_version") != PROJECT_POLICY_SCHEMA:
        raise GateError(f"project policy schema must be {PROJECT_POLICY_SCHEMA}")
    for key in ("protected_actions", "eval_gate", "rag_gate", "release_gate"):
        if not value.get(key):
            raise GateError(f"project policy is missing {key}")
    release = value["release_gate"]
    for key in (
        "require_drift_pass", "require_eval_pass", "require_rag_pass_if_affected",
        "require_rollback_artifact", "require_final_user_approval",
        "invalidate_on_subject_hash_change",
    ):
        if release.get(key) is not True:
            raise GateError(f"project policy must keep release_gate.{key}=true")
    return value


def compare_eval_policy(suite: dict, project_policy: dict) -> list[str]:
    failures: list[str] = []
    actual = suite.get("policy", {})
    required = project_policy["eval_gate"]
    for key in ("minimum_cases", "minimum_trials_per_variant", "minimum_p2p_pass_rate"):
        if not isinstance(actual.get(key), (int, float)) or actual[key] < required[key]:
            failures.append(f"eval policy weakened {key}: {actual.get(key)!r} < {required[key]!r}")
    for key in ("maximum_mean_regression", "maximum_case_regressions", "maximum_score_spread"):
        if not isinstance(actual.get(key), (int, float)) or actual[key] > required[key]:
            failures.append(f"eval policy weakened {key}: {actual.get(key)!r} > {required[key]!r}")
    if required.get("blocked_cases_allowed") is False and actual.get("blocked_cases_allowed") is not False:
        failures.append("eval policy cannot allow blocked cases")
    return failures


def compare_rag_policy(check: dict, project_policy: dict) -> list[str]:
    failures: list[str] = []
    actual = check.get("policy", {})
    required = project_policy["rag_gate"]
    minimums = (
        "minimum_recall_at_k", "minimum_grounding_rate",
        "minimum_citation_verifiability", "minimum_injection_resistance_rate",
    )
    for key in minimums:
        if not isinstance(actual.get(key), (int, float)) or actual[key] < required[key]:
            failures.append(f"RAG policy weakened {key}: {actual.get(key)!r} < {required[key]!r}")
    key = "maximum_cross_boundary_leakage_rate"
    if not isinstance(actual.get(key), (int, float)) or actual[key] > required[key]:
        failures.append(f"RAG policy weakened {key}: {actual.get(key)!r} > {required[key]!r}")
    return failures


def command_prepare(args: argparse.Namespace) -> int:
    project = Path(args.project).expanduser().resolve()
    if not project.is_dir():
        raise GateError(f"Project directory does not exist: {project}")
    governance = Path(args.governance).expanduser().resolve() if args.governance else default_governance(project)
    helpers = Path(args.helpers).expanduser().resolve() if args.helpers else default_helpers(project)
    policy_path = Path(args.policy).expanduser().resolve() if args.policy else project / ".p2p" / "project-policy.json"
    project_policy = validate_project_policy(load_json(policy_path))
    if args.action not in project_policy["protected_actions"]:
        raise GateError(f"Action is not enabled by project policy: {args.action}")
    subject = Path(args.subject).expanduser().resolve()
    rollback = Path(args.rollback).expanduser().resolve()
    if not subject.exists():
        raise GateError(f"Release/deployment subject does not exist: {subject}")
    if not rollback.exists():
        raise GateError(f"Rollback artifact does not exist: {rollback}")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = Path(args.out_dir).expanduser().resolve() if args.out_dir else project / ".p2p" / "gates" / stamp
    if out_dir.exists():
        raise GateError(f"Gate output directory already exists: {out_dir}")
    out_dir.mkdir(parents=True)
    suite = Path(args.suite).expanduser().resolve() if args.suite else project / ".p2p" / "evals" / "suite.json"
    technical_failures: list[str] = []
    gates: dict[str, object] = {}

    drift_code, drift = run_json(
        [
            sys.executable, str(helpers / "p2p_governance.py"), "drift",
            "--root", str(project), "--governance", str(governance),
        ]
    )
    gates["drift"] = drift
    if drift_code != 0 or drift.get("status") != "PASS":
        technical_failures.append("drift gate failed")

    if not suite.is_file():
        gates["project_eval"] = {"status": "FAIL", "failures": [f"missing suite: {suite}"]}
        technical_failures.append("project eval suite is missing")
    else:
        suite_value = load_json(suite)
        policy_failures = compare_eval_policy(suite_value if isinstance(suite_value, dict) else {}, project_policy)
        eval_report = out_dir / "eval-report.json"
        eval_code, eval_result = run_json(
            [sys.executable, str(helpers / "p2p_eval.py"), "gate", "--suite", str(suite), "--report", str(eval_report)]
        )
        if policy_failures:
            eval_result.setdefault("failures", []).extend(policy_failures)
            eval_result["status"] = "FAIL"
        gates["project_eval"] = eval_result
        if eval_code != 0 or eval_result.get("status") != "PASS":
            technical_failures.append("project eval gate failed")

    if args.rag_affected:
        if not args.rag_check:
            gates["rag"] = {"status": "FAIL", "failures": ["--rag-check is required when --rag-affected is set"]}
            technical_failures.append("RAG gate is required but no check was supplied")
        else:
            rag_path = Path(args.rag_check).expanduser().resolve()
            if not rag_path.is_file():
                gates["rag"] = {"status": "FAIL", "failures": [f"missing RAG check: {rag_path}"]}
                technical_failures.append("RAG check is missing")
            else:
                rag_value = load_json(rag_path)
                policy_failures = compare_rag_policy(rag_value if isinstance(rag_value, dict) else {}, project_policy)
                rag_report = out_dir / "rag-report.json"
                rag_code, rag_result = run_json(
                    [sys.executable, str(helpers / "p2p_eval.py"), "rag-gate", "--check", str(rag_path), "--report", str(rag_report)]
                )
                if policy_failures:
                    rag_result.setdefault("failures", []).extend(policy_failures)
                    rag_result["status"] = "FAIL"
                gates["rag"] = rag_result
                if rag_code != 0 or rag_result.get("status") != "PASS":
                    technical_failures.append("RAG retrieval gate failed")
    else:
        gates["rag"] = {"status": "NOT_APPLICABLE", "reason": "Caller declared no RAG/source/index change."}

    subject_hash = fingerprint_subject(subject)
    rollback_hash = fingerprint_subject(rollback)
    report = {
        "schema_version": "p2p-codex-technical-gate-report/1",
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "project": str(project),
        "action": args.action,
        "subject": str(subject),
        "subject_sha256": subject_hash,
        "rollback": str(rollback),
        "rollback_sha256": rollback_hash,
        "rag_affected": bool(args.rag_affected),
        "status": "PASS" if not technical_failures else "FAIL",
        "failures": technical_failures,
        "gates": gates,
        "approval_state": "NOT_REQUESTED" if technical_failures else "PENDING",
    }
    report_path = out_dir / "technical-gate-report.json"
    write_json_new(report_path, report)
    if technical_failures:
        print(json.dumps({"status": "BLOCKED_TECHNICAL_GATES", "report": str(report_path), "failures": technical_failures}, ensure_ascii=False, indent=2))
        return 2

    request_path = out_dir / "approval-request.json"
    request_code, request_result = run_json(
        [
            sys.executable, str(helpers / "p2p_approval.py"),
            "--governance", str(governance), "request",
            "--project", str(project), "--action", args.action,
            "--scope", args.scope, "--subject", str(subject),
            "--technical-report", str(report_path), "--requested-by", "Codex",
            "--risk-summary", args.risk_summary, "--out", str(request_path),
        ]
    )
    if request_code != 0:
        raise GateError(f"Could not create approval request: {request_result}")
    print(
        json.dumps(
            {
                "status": "TECHNICAL_GATES_PASS_USER_APPROVAL_REQUIRED",
                "report": str(report_path),
                "approval_request": str(request_path),
                "next_command": f'py "{helpers / "p2p_approval.py"}" approve --request "{request_path}" --by "YOUR_NAME"',
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def command_finalize(args: argparse.Namespace) -> int:
    governance = Path(args.governance).expanduser().resolve() if args.governance else Path(__file__).resolve().parents[1] / "governance"
    policy = validate_policy(load_json(governance / "approval-policy.json"))
    report_path = Path(args.technical_report).expanduser().resolve()
    report = load_json(report_path)
    if not isinstance(report, dict) or report.get("schema_version") != "p2p-codex-technical-gate-report/1":
        raise GateError("Invalid technical gate report")
    failures: list[str] = []
    if report.get("status") != "PASS" or report.get("failures"):
        failures.append("technical gates are not PASS")
    subject = Path(args.subject).expanduser().resolve()
    subject_hash = fingerprint_subject(subject)
    if subject_hash != report.get("subject_sha256"):
        failures.append("subject changed after technical gates")
    approval = load_json(Path(args.approval).expanduser().resolve())
    failures.extend(
        validate_record(
            approval,
            policy,
            expected_action=report.get("action"),
            expected_subject_sha256=subject_hash,
            expected_technical_report_sha256=sha256_file(report_path),
        )
    )
    result = {
        "schema_version": "p2p-codex-final-gate-report/1",
        "finalized_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "action": report.get("action"),
        "subject": str(subject),
        "subject_sha256": subject_hash,
        "technical_report_sha256": sha256_file(report_path),
        "approval_request_id": approval.get("request_id") if isinstance(approval, dict) else None,
        "status": "PASS" if not failures else "FAIL",
        "release_decision": "APPROVED" if not failures else "BLOCKED",
        "failures": failures,
    }
    output = Path(args.out).expanduser().resolve() if args.out else report_path.with_name("final-gate-report.json")
    write_json_new(output, result)
    print(json.dumps({**result, "report": str(output)}, ensure_ascii=False, indent=2))
    return 0 if not failures else 2


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    prepare = sub.add_parser("prepare", help="Run technical gates and create an approval request")
    prepare.add_argument("--project", default=".")
    prepare.add_argument("--governance")
    prepare.add_argument("--helpers")
    prepare.add_argument("--policy")
    prepare.add_argument("--suite")
    prepare.add_argument("--subject", required=True)
    prepare.add_argument("--rollback", required=True)
    prepare.add_argument("--action", default="release_or_deploy")
    prepare.add_argument("--scope", required=True)
    prepare.add_argument("--risk-summary", required=True)
    prepare.add_argument("--rag-affected", action="store_true")
    prepare.add_argument("--rag-check")
    prepare.add_argument("--out-dir")
    prepare.set_defaults(func=command_prepare)
    finalize = sub.add_parser("finalize", help="Verify final user approval and unchanged subject")
    finalize.add_argument("--governance")
    finalize.add_argument("--technical-report", required=True)
    finalize.add_argument("--approval", required=True)
    finalize.add_argument("--subject", required=True)
    finalize.add_argument("--out")
    finalize.set_defaults(func=command_finalize)
    return p


if __name__ == "__main__":
    parsed = parser().parse_args()
    try:
        raise SystemExit(parsed.func(parsed))
    except (GateError, ApprovalError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
