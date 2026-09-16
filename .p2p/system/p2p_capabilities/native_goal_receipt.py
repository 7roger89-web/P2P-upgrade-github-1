"""Durable audit receipts for actual host-native ``/goal`` use.

Receipts are appended to the existing P2P execution ledger.  They do not
create a second truth store and are never acceptance authority.  In
particular, an activation decision or generated command is NOT an invocation
receipt: ``INVOKED`` may be recorded only after the current host/session has
accepted the native command and its goal status has been observed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .native_goal_bridge import CLAUDE_CODE, CODEX_CLI, HOST_KINDS

RECEIPT_SCHEMA = "p2p-native-goal-invocation/1"
LEDGER_SCHEMA = "p2p-execution-event/1"
LEDGER_EVENT = "native_goal_invocation_receipt"
LEDGER_RELATIVE_PATH = Path(".p2p") / "state" / "execution-ledger.jsonl"
INVOKED = "INVOKED"
UNAVAILABLE = "UNAVAILABLE"
RECEIPT_STATES = (INVOKED, UNAVAILABLE)
PROOF_KINDS = (
    "CLAUDE_GOAL_STATUS_VIEW",
    "CODEX_GOAL_STATUS_VIEW",
    "HOST_PROBE",
    "HOST_NATIVE_REJECTION",
)
_SECRET_VALUE_RE = re.compile(
    r"(?:api[_-]?key|password|token|secret|authorization|private[_-]?key)\s*[:=]\s*[^\s,;]+|sk-[A-Za-z0-9_-]{16,}",
    re.IGNORECASE,
)
_MAX_TEXT = 1024


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _text(value: Any, field: str, *, max_length: int = _MAX_TEXT) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field.upper()}_INVALID")
    text = value.strip()
    if not text or len(text) > max_length or _SECRET_VALUE_RE.search(text):
        raise ValueError(f"{field.upper()}_INVALID")
    return text


def _ledger_path(root: str | Path) -> Path:
    candidate = Path(root).expanduser().resolve()
    if candidate.suffix.lower() == ".jsonl":
        return candidate
    return candidate / LEDGER_RELATIVE_PATH


def _fingerprint(receipt: Mapping[str, Any]) -> str:
    payload = json.dumps(receipt, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_receipt(
    *,
    host_kind: str,
    goal_id: str,
    state: str,
    proof_kind: str,
    reason: str,
    observed_at: str | None = None,
) -> dict[str, Any]:
    """Build one bounded receipt without raw prompt/goal/command content."""

    if host_kind not in HOST_KINDS:
        raise ValueError("HOST_KIND_UNSUPPORTED")
    if state not in RECEIPT_STATES:
        raise ValueError("RECEIPT_STATE_UNSUPPORTED")
    if proof_kind not in PROOF_KINDS:
        raise ValueError("PROOF_KIND_UNSUPPORTED")
    if state == INVOKED:
        expected = "CLAUDE_GOAL_STATUS_VIEW" if host_kind == CLAUDE_CODE else "CODEX_GOAL_STATUS_VIEW"
        if proof_kind != expected:
            raise ValueError("INVOKED_REQUIRES_HOST_GOAL_STATUS_VIEW")
    if state == UNAVAILABLE and proof_kind not in {"HOST_PROBE", "HOST_NATIVE_REJECTION"}:
        raise ValueError("UNAVAILABLE_REQUIRES_HOST_FAILURE_PROOF")

    receipt = {
        "schema": RECEIPT_SCHEMA,
        "host_kind": host_kind,
        "goal_id": _text(goal_id, "goal_id", max_length=256),
        "state": state,
        "proof_kind": proof_kind,
        "reason": _text(reason, "reason", max_length=512),
        "observed_at": observed_at or utc_now(),
        "raw_goal_stored": False,
        "raw_command_stored": False,
        "acceptance_authority": False,
    }
    receipt["fingerprint"] = _fingerprint(receipt)
    return receipt


def validate_receipt(receipt: Mapping[str, Any]) -> bool:
    if not isinstance(receipt, Mapping):
        return False
    expected_fields = {
        "schema",
        "host_kind",
        "goal_id",
        "state",
        "proof_kind",
        "reason",
        "observed_at",
        "raw_goal_stored",
        "raw_command_stored",
        "acceptance_authority",
        "fingerprint",
    }
    if set(receipt) != expected_fields or receipt.get("schema") != RECEIPT_SCHEMA:
        return False
    if receipt.get("host_kind") not in HOST_KINDS or receipt.get("state") not in RECEIPT_STATES:
        return False
    if receipt.get("proof_kind") not in PROOF_KINDS:
        return False
    if any(receipt.get(key) is not False for key in ("raw_goal_stored", "raw_command_stored", "acceptance_authority")):
        return False
    try:
        rebuilt = build_receipt(
            host_kind=str(receipt.get("host_kind")),
            goal_id=str(receipt.get("goal_id")),
            state=str(receipt.get("state")),
            proof_kind=str(receipt.get("proof_kind")),
            reason=str(receipt.get("reason")),
            observed_at=str(receipt.get("observed_at")),
        )
    except ValueError:
        return False
    return rebuilt == dict(receipt)


def receipt_key(receipt: Mapping[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(receipt.get("host_kind", "")),
        str(receipt.get("goal_id", "")),
        str(receipt.get("state", "")),
        str(receipt.get("fingerprint", "")),
    )


def _existing(ledger: Path, key: tuple[str, str, str, str]) -> dict[str, Any] | None:
    if not ledger.is_file():
        return None
    try:
        lines = ledger.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError):
        return None
    for line in lines:
        try:
            event = json.loads(line)
        except (TypeError, ValueError):
            continue
        if not isinstance(event, Mapping) or event.get("event") != LEDGER_EVENT:
            continue
        receipt = event.get("receipt")
        if isinstance(receipt, Mapping) and receipt_key(receipt) == key and validate_receipt(receipt):
            return dict(receipt)
    return None


def append_receipt(receipt: Mapping[str, Any], root: str | Path = ".") -> dict[str, Any]:
    """Append a valid receipt to the existing execution ledger, idempotently."""

    if not validate_receipt(receipt):
        raise ValueError("NATIVE_GOAL_RECEIPT_INVALID")
    path = _ledger_path(root)
    key = receipt_key(receipt)
    existing = _existing(path, key)
    if existing is not None:
        return {"status": "DUPLICATE", "ledger": str(path), "receipt": existing}
    path.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "schema_version": LEDGER_SCHEMA,
        "at": str(receipt["observed_at"]),
        "event": LEDGER_EVENT,
        "receipt": dict(receipt),
    }
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
    return {"status": "RECORDED", "ledger": str(path), "receipt": dict(receipt)}


def read_receipts(root: str | Path = ".") -> list[dict[str, Any]]:
    path = _ledger_path(root)
    if not path.is_file():
        return []
    receipts: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError):
        return []
    for line in lines:
        try:
            event = json.loads(line)
        except (TypeError, ValueError):
            continue
        if not isinstance(event, Mapping) or event.get("event") != LEDGER_EVENT:
            continue
        receipt = event.get("receipt")
        if isinstance(receipt, Mapping) and validate_receipt(receipt):
            receipts.append(dict(receipt))
    return receipts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)

    record = sub.add_parser("record")
    record.add_argument("--root", default=".")
    record.add_argument("--host", required=True, choices=HOST_KINDS)
    record.add_argument("--goal-id", required=True)
    record.add_argument("--state", required=True, choices=RECEIPT_STATES)
    record.add_argument("--proof-kind", required=True, choices=PROOF_KINDS)
    record.add_argument("--reason", required=True)

    show = sub.add_parser("list")
    show.add_argument("--root", default=".")

    args = parser.parse_args(argv)
    if args.action == "list":
        print(json.dumps(read_receipts(args.root), ensure_ascii=False, sort_keys=True, indent=2))
        return 0
    try:
        result = append_receipt(
            build_receipt(
                host_kind=args.host,
                goal_id=args.goal_id,
                state=args.state,
                proof_kind=args.proof_kind,
                reason=args.reason,
            ),
            args.root,
        )
    except (OSError, ValueError) as exc:
        print(json.dumps({"status": "BLOCKED", "error": str(exc)}, ensure_ascii=False, sort_keys=True))
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
