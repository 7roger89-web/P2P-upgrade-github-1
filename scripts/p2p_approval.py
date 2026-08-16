#!/usr/bin/env python3
"""Create and verify auditable P2P user-approval records.

This is a workflow control, not an operating-system identity boundary.  The
strong path is an interactive local decision made after technical gates pass.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


POLICY_SCHEMA = "p2p-codex-approval-policy/1"
RECORD_SCHEMA = "p2p-codex-approval-record/2"
EXCLUDED_TREE_PARTS = {
    ".git",
    ".p2p/approvals",
    ".p2p/gates",
    ".p2p/evals/reports",
    "__pycache__",
    ".pytest_cache",
    "node_modules",
}


class ApprovalError(ValueError):
    pass


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat()


def parse_datetime(value: object, field: str) -> datetime:
    if not isinstance(value, str):
        raise ApprovalError(f"{field} must be an ISO date-time")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ApprovalError(f"{field} is not a valid ISO date-time") from exc
    if parsed.tzinfo is None:
        raise ApprovalError(f"{field} must include a timezone")
    return parsed.astimezone(timezone.utc)


def load_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ApprovalError(f"Cannot read JSON {path}: {exc}") from exc


def write_json_atomic(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise ApprovalError(f"Refusing to overwrite existing approval artifact: {path}")
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def excluded_relative(relative: str) -> bool:
    normalized = relative.replace("\\", "/").strip("/")
    return any(
        normalized == item or normalized.startswith(item + "/") or f"/{item}/" in f"/{normalized}/"
        for item in EXCLUDED_TREE_PARTS
    )


def fingerprint_subject(path: Path) -> str:
    resolved = path.expanduser().resolve()
    if not resolved.exists():
        raise ApprovalError(f"Approval subject does not exist: {resolved}")
    if resolved.is_symlink():
        raise ApprovalError("Approval subject cannot be a symbolic link")
    if resolved.is_file():
        return sha256_file(resolved)
    digest = hashlib.sha256()
    files = []
    for item in resolved.rglob("*"):
        if item.is_symlink() or not item.is_file():
            continue
        relative = item.relative_to(resolved).as_posix()
        if not excluded_relative(relative):
            files.append((relative, item))
    for relative, item in sorted(files):
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(bytes.fromhex(sha256_file(item)))
        digest.update(b"\n")
    return digest.hexdigest()


def default_governance() -> Path:
    package = Path(__file__).resolve().parents[1]
    direct = package / "governance"
    return direct if direct.is_dir() else package / ".p2p" / "system" / "governance"


def validate_policy(value: object) -> dict:
    if not isinstance(value, dict) or value.get("schema_version") != POLICY_SCHEMA:
        raise ApprovalError(f"approval policy schema must be {POLICY_SCHEMA}")
    ttl = value.get("default_request_ttl_hours")
    actions = value.get("protected_actions")
    principles = value.get("principles")
    if not isinstance(ttl, int) or ttl < 1:
        raise ApprovalError("approval policy needs a positive default_request_ttl_hours")
    if not isinstance(actions, dict) or not actions:
        raise ApprovalError("approval policy needs protected_actions")
    if not isinstance(principles, dict) or principles.get("agent_may_self_approve") is not False:
        raise ApprovalError("approval policy must explicitly prohibit agent self-approval")
    for name, action in actions.items():
        if not isinstance(name, str) or not isinstance(action, dict):
            raise ApprovalError("invalid protected action")
        if not action.get("description") or not isinstance(action.get("required_technical_gates"), list):
            raise ApprovalError(f"protected action {name} is incomplete")
        action_ttl = action.get("approval_ttl_hours")
        if not isinstance(action_ttl, int) or action_ttl < 1:
            raise ApprovalError(f"protected action {name} needs a positive approval_ttl_hours")
    return value


def validate_record(
    value: object,
    policy: dict,
    *,
    expected_action: str | None = None,
    expected_subject_sha256: str | None = None,
    expected_technical_report_sha256: str | None = None,
    provenance_only: bool = False,
    as_of: datetime | None = None,
) -> list[str]:
    errors: list[str] = []
    if not isinstance(value, dict) or value.get("schema_version") != RECORD_SCHEMA:
        return [f"approval schema must be {RECORD_SCHEMA}"]
    required = {
        "request_id", "state", "action", "scope", "subject", "subject_sha256",
        "requested_at", "request_expires_at", "requested_by", "risk_summary",
        "technical_report", "technical_report_sha256",
    }
    missing = sorted(required - value.keys())
    if missing:
        return [f"approval record is missing: {', '.join(missing)}"]
    if not re.fullmatch(r"P2P-APR-[A-Za-z0-9._-]+", str(value.get("request_id", ""))):
        errors.append("request_id is invalid")
    action = str(value.get("action", ""))
    if action not in policy["protected_actions"]:
        errors.append(f"action is not protected by policy: {action}")
    if expected_action and action != expected_action:
        errors.append(f"approval action mismatch: {action} != {expected_action}")
    subject_hash = str(value.get("subject_sha256", ""))
    if not re.fullmatch(r"[a-f0-9]{64}", subject_hash):
        errors.append("subject_sha256 is invalid")
    if expected_subject_sha256 and subject_hash != expected_subject_sha256:
        errors.append("approval subject hash does not match the current subject")
    report_reference = value.get("technical_report")
    if not isinstance(report_reference, str) or not report_reference.strip():
        errors.append("technical_report is missing")
    report_hash = str(value.get("technical_report_sha256", ""))
    if not re.fullmatch(r"[a-f0-9]{64}", report_hash):
        errors.append("technical_report_sha256 is invalid")
    if expected_technical_report_sha256 is not None and report_hash != expected_technical_report_sha256:
        errors.append("approval technical-report hash mismatch")
    try:
        requested = parse_datetime(value.get("requested_at"), "requested_at")
        expires = parse_datetime(value.get("request_expires_at"), "request_expires_at")
    except ApprovalError as exc:
        errors.append(str(exc))
        return errors
    if expires <= requested:
        errors.append("approval request expires before or when it was created")
    if value.get("state") != "APPROVED" or value.get("decision") != "APPROVE":
        errors.append("approval state is not APPROVED")
        return errors
    for field in (
        "decided_at", "decided_by", "decision_note", "approval_method",
        "identity_assurance", "recorded_by",
    ):
        if not value.get(field):
            errors.append(f"approved record is missing {field}")
    try:
        decided = parse_datetime(value.get("decided_at"), "decided_at")
    except ApprovalError as exc:
        errors.append(str(exc))
        return errors
    if not requested <= decided <= expires:
        errors.append("approval decision was not made inside the request window")
    if value.get("requested_by") == value.get("decided_by"):
        errors.append("requester and approver must be distinct")
    if value.get("approval_method") not in {"manual_cli", "conversation_explicit"}:
        errors.append("approval_method is invalid")
    if value.get("identity_assurance") not in {"local_interactive", "active_user_message"}:
        errors.append("identity_assurance is invalid")
    if not provenance_only and (as_of or utc_now()) > expires:
        errors.append("approval request has expired")
    return errors


def command_request(args: argparse.Namespace) -> int:
    governance = Path(args.governance).expanduser().resolve()
    policy = validate_policy(load_json(governance / "approval-policy.json"))
    if args.action not in policy["protected_actions"]:
        raise ApprovalError(f"Unknown protected action: {args.action}")
    subject = Path(args.subject).expanduser().resolve()
    subject_hash = fingerprint_subject(subject)
    report = Path(args.technical_report).expanduser().resolve()
    if not report.is_file():
        raise ApprovalError(f"Technical report does not exist: {report}")
    report_value = load_json(report)
    if (
        not isinstance(report_value, dict)
        or report_value.get("status") != "PASS"
        or bool(report_value.get("failures"))
    ):
        raise ApprovalError("Technical report must be a JSON object with status PASS")
    if report_value.get("action") != args.action:
        raise ApprovalError("Technical report action does not match the approval action")
    if report_value.get("subject_sha256") != subject_hash:
        raise ApprovalError("Technical report subject hash does not match the current subject")
    technical_hash = sha256_file(report)
    now = utc_now()
    action_policy = policy["protected_actions"][args.action]
    ttl = int(action_policy.get("approval_ttl_hours", policy["default_request_ttl_hours"]))
    suffix = hashlib.sha256(f"{args.action}\0{subject_hash}\0{iso(now)}".encode()).hexdigest()[:10]
    request_id = f"P2P-APR-{now.strftime('%Y%m%dT%H%M%SZ')}-{suffix}"
    record = {
        "schema_version": RECORD_SCHEMA,
        "request_id": request_id,
        "state": "PENDING",
        "action": args.action,
        "scope": args.scope,
        "subject": str(subject),
        "subject_sha256": subject_hash,
        "requested_at": iso(now),
        "request_expires_at": iso(now + timedelta(hours=ttl)),
        "requested_by": args.requested_by,
        "risk_summary": args.risk_summary,
        "technical_report": str(report),
        "technical_report_sha256": technical_hash,
    }
    if args.out:
        output = Path(args.out).expanduser().resolve()
    else:
        project = Path(args.project).expanduser().resolve()
        output = project / ".p2p" / "approvals" / "requests" / f"{request_id}.json"
    write_json_atomic(output, record)
    print(json.dumps({"status": "PENDING_USER_APPROVAL", "request": str(output), **record}, ensure_ascii=False, indent=2))
    return 0


def decide(args: argparse.Namespace, decision: str) -> int:
    request_path = Path(args.request).expanduser().resolve()
    value = load_json(request_path)
    if not isinstance(value, dict) or value.get("schema_version") != RECORD_SCHEMA:
        raise ApprovalError("Invalid approval request")
    if value.get("state") != "PENDING":
        raise ApprovalError("Only a PENDING request can be decided")
    expires = parse_datetime(value.get("request_expires_at"), "request_expires_at")
    now = utc_now()
    if now > expires:
        raise ApprovalError("Approval request has expired; create a new request")
    if not sys.stdin.isatty():
        raise ApprovalError("User decision requires an interactive terminal; an agent must not approve on the user's behalf")
    phrase = f"{decision} {value['request_id']}"
    print(f"Action:  {value['action']}")
    print(f"Scope:   {value['scope']}")
    print(f"Subject: {value['subject']}")
    print(f"SHA-256: {value['subject_sha256']}")
    print(f"Report:  {value['technical_report']}")
    print(f"Report SHA-256: {value['technical_report_sha256']}")
    print(f"Risk:    {value['risk_summary']}")
    typed = input(f"Type exactly '{phrase}' to continue: ").strip()
    if typed != phrase:
        raise ApprovalError("Confirmation phrase did not match; no decision record was written")
    result = dict(value)
    result.update(
        {
            "state": "APPROVED" if decision == "APPROVE" else "REJECTED",
            "decision": decision,
            "decided_at": iso(now),
            "decided_by": args.by,
            "decision_note": args.note or "Interactive user decision.",
            "approval_method": "manual_cli",
            "identity_assurance": "local_interactive",
            "recorded_by": "p2p_approval.py",
        }
    )
    if args.out:
        output = Path(args.out).expanduser().resolve()
    else:
        output = request_path.parent.parent / "records" / f"{value['request_id']}.json"
    write_json_atomic(output, result)
    print(json.dumps({"status": result["state"], "record": str(output)}, ensure_ascii=False, indent=2))
    return 0


def command_approve(args: argparse.Namespace) -> int:
    return decide(args, "APPROVE")


def command_reject(args: argparse.Namespace) -> int:
    return decide(args, "REJECT")


def command_verify(args: argparse.Namespace) -> int:
    governance = Path(args.governance).expanduser().resolve()
    policy = validate_policy(load_json(governance / "approval-policy.json"))
    record = load_json(Path(args.record).expanduser().resolve())
    subject_hash = fingerprint_subject(Path(args.subject)) if args.subject else None
    technical_hash = sha256_file(Path(args.technical_report).expanduser().resolve()) if args.technical_report else None
    errors = validate_record(
        record,
        policy,
        expected_action=args.action,
        expected_subject_sha256=subject_hash,
        expected_technical_report_sha256=technical_hash,
        provenance_only=args.provenance_only,
    )
    result = {"status": "PASS" if not errors else "FAIL", "errors": errors}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 2


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--governance", default=str(default_governance()))
    sub = p.add_subparsers(dest="command", required=True)
    request = sub.add_parser("request", help="Create a pending approval request")
    request.add_argument("--project", default=".")
    request.add_argument("--action", required=True)
    request.add_argument("--scope", required=True)
    request.add_argument("--subject", required=True)
    request.add_argument("--technical-report", required=True)
    request.add_argument("--requested-by", default="Codex")
    request.add_argument("--risk-summary", required=True)
    request.add_argument("--out")
    request.set_defaults(func=command_request)
    for name, func in (("approve", command_approve), ("reject", command_reject)):
        decision = sub.add_parser(name, help=f"Interactively {name} a pending request")
        decision.add_argument("--request", required=True)
        decision.add_argument("--by", required=True)
        decision.add_argument("--note")
        decision.add_argument("--out")
        decision.set_defaults(func=func)
    verify = sub.add_parser("verify", help="Verify an approval against the current subject")
    verify.add_argument("--record", required=True)
    verify.add_argument("--action")
    verify.add_argument("--subject")
    verify.add_argument("--technical-report")
    verify.add_argument("--provenance-only", action="store_true")
    verify.set_defaults(func=command_verify)
    return p


if __name__ == "__main__":
    parsed = parser().parse_args()
    try:
        raise SystemExit(parsed.func(parsed))
    except (ApprovalError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
