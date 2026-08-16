#!/usr/bin/env python3
"""Record host-owned Codex subagent identity receipts.

This module is deliberately small and standard-library-only.  It consumes one
official Codex command-hook JSON object, copies only the identity/lifecycle
fields required by the receipt contract, and appends the receipt to the
existing P2P execution ledger.  The command-line entry point never writes to
stdout and always exits successfully: a malformed payload or ledger failure is
an absence of proof and must not change child execution.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


RECEIPT_SCHEMA = "p2p-host-subagent-identity/1"
LEDGER_SCHEMA = "p2p-execution-event/1"
LEDGER_EVENT = "host_subagent_identity_receipt"
HOST_SOURCE = "codex_official_hook"
SUBAGENT_EVENTS = ("SubagentStart", "SubagentStop")
LEDGER_RELATIVE_PATH = Path(".p2p") / "state" / "execution-ledger.jsonl"

# These are the only host identities that this boundary is allowed to trust.
# The generic/default value is an official Codex host executor class, not a
# ninth P2P identity and not a substitute for any canonical quorum member.
CANONICAL_HOST_AGENT_TYPES = frozenset(
    {
        "p2p_iris",
        "p2p_tecton",
        "p2p_axiom",
        "p2p_vector",
        "p2p_datos",
        "p2p_anon",
        "p2p_architecton",
        "p2p_helios",
    }
)
OPTIONAL_HOST_AGENT_TYPES = frozenset({"p2p_aesthetica"})
GENERIC_HOST_AGENT_TYPES = frozenset({"default"})
SUPPORTED_HOST_AGENT_TYPES = (
    CANONICAL_HOST_AGENT_TYPES | OPTIONAL_HOST_AGENT_TYPES | GENERIC_HOST_AGENT_TYPES
)
_SECRET_VALUE_RE = re.compile(
    r"(?:api[_-]?key|password|token|secret|authorization|private[_-]?key)\s*[:=]\s*[^\s,;]+|sk-[A-Za-z0-9_-]{16,}",
    re.IGNORECASE,
)

_COMMON_REQUIRED_FIELDS = (
    "session_id",
    "turn_id",
    "cwd",
    "hook_event_name",
    "model",
    "permission_mode",
    "agent_id",
    "agent_type",
)
_STOP_REQUIRED_FIELDS = ("agent_transcript_path", "stop_hook_active", "last_assistant_message")
_MAX_STRING_LENGTH = 4096
_RECEIPT_FIELDS = {
    "schema",
    "event",
    "timestamp",
    "session_id",
    "turn_id",
    "agent_id",
    "agent_type",
    "permission_mode",
    "model",
    "cwd",
    "source",
}


def utc_now() -> str:
    """Return a compact UTC timestamp suitable for a ledger event."""

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _required_string(payload: Mapping[str, Any], name: str) -> str | None:
    value = payload.get(name)
    if not isinstance(value, str):
        return None
    value = value.strip()
    if not value or len(value) > _MAX_STRING_LENGTH:
        return None
    if _SECRET_VALUE_RE.search(value):
        return None
    return value


def is_supported_host_agent_type(agent_type: object) -> bool:
    """Return whether an exact host-owned identity is allow-listed."""

    return isinstance(agent_type, str) and agent_type in SUPPORTED_HOST_AGENT_TYPES


def host_agent_class(agent_type: object) -> str | None:
    """Classify a supported host identity without adding a P2P identity."""

    if not is_supported_host_agent_type(agent_type):
        return None
    if agent_type in GENERIC_HOST_AGENT_TYPES:
        return "HOST_DEFAULT / GENERIC"
    return "CUSTOM_PROFILE"


def _nullable_string(payload: Mapping[str, Any], name: str) -> bool:
    value = payload.get(name)
    return value is None or (isinstance(value, str) and len(value) <= _MAX_STRING_LENGTH)


def build_receipt(payload: Mapping[str, Any], *, timestamp: str | None = None) -> dict[str, Any] | None:
    """Build an allow-listed receipt from one official hook payload.

    Unknown fields are intentionally discarded.  In particular, prompt,
    transcript, assistant-message, tool, environment, and secret-like fields
    never enter the returned object.  A missing or malformed required field
    returns ``None`` rather than a partially trusted receipt.
    """

    if not isinstance(payload, Mapping):
        return None
    event = payload.get("hook_event_name")
    if event not in SUBAGENT_EVENTS:
        return None
    values: dict[str, str] = {}
    for name in _COMMON_REQUIRED_FIELDS:
        value = _required_string(payload, name)
        if value is None:
            return None
        values[name] = value
    if not is_supported_host_agent_type(values["agent_type"]):
        return None
    if event == "SubagentStop":
        if not all(name in payload for name in _STOP_REQUIRED_FIELDS):
            return None
        if not _nullable_string(payload, "agent_transcript_path"):
            return None
        if not isinstance(payload.get("stop_hook_active"), bool):
            return None
        if not _nullable_string(payload, "last_assistant_message"):
            return None
    return {
        "schema": RECEIPT_SCHEMA,
        "event": event,
        "timestamp": timestamp or utc_now(),
        "session_id": values["session_id"],
        "turn_id": values["turn_id"],
        "agent_id": values["agent_id"],
        "agent_type": values["agent_type"],
        "permission_mode": values["permission_mode"],
        "model": values["model"],
        "cwd": values["cwd"],
        "source": HOST_SOURCE,
    }


def receipt_key(receipt: Mapping[str, Any]) -> tuple[str, str, str, str, str]:
    """Return the deterministic replay key for one receipt."""

    return (
        str(receipt.get("event", "")),
        str(receipt.get("session_id", "")),
        str(receipt.get("turn_id", "")),
        str(receipt.get("agent_id", "")),
        str(receipt.get("agent_type", "")),
    )


def validate_receipt(receipt: Mapping[str, Any]) -> bool:
    """Validate the complete persisted contract before it can prove identity."""

    if not isinstance(receipt, Mapping) or set(receipt) != _RECEIPT_FIELDS:
        return False
    if receipt.get("schema") != RECEIPT_SCHEMA or receipt.get("source") != HOST_SOURCE:
        return False
    if receipt.get("event") not in SUBAGENT_EVENTS:
        return False
    for name in ("timestamp", "session_id", "turn_id", "agent_id", "agent_type", "permission_mode", "model", "cwd"):
        value = receipt.get(name)
        if not isinstance(value, str) or not value.strip() or len(value) > _MAX_STRING_LENGTH:
            return False
        if _SECRET_VALUE_RE.search(value):
            return False
    if not is_supported_host_agent_type(receipt.get("agent_type")):
        return False
    return True


def _ledger_path(root: str | Path) -> Path:
    candidate = Path(root).expanduser().resolve()
    if candidate.suffix.lower() == ".jsonl":
        return candidate
    return candidate / LEDGER_RELATIVE_PATH


def _discover_project_root(candidate: Path) -> Path:
    """Find the nearest project root when Codex started in a subdirectory."""

    candidate = candidate.expanduser().resolve()
    for parent in (candidate, *candidate.parents):
        if (parent / ".p2p").is_dir() and (parent / ".codex" / "config.toml").is_file():
            return parent
    return candidate


def _existing_receipt(ledger: Path, key: tuple[str, str, str, str, str]) -> dict[str, Any] | None:
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
        if isinstance(receipt, Mapping) and receipt_key(receipt) == key:
            return dict(receipt)
    return None


def append_receipt(receipt: Mapping[str, Any], ledger: str | Path) -> dict[str, Any]:
    """Append one receipt to the existing execution ledger, deduplicating it."""

    if not validate_receipt(receipt):
        raise ValueError("invalid host identity receipt")
    path = _ledger_path(ledger)
    key = receipt_key(receipt)
    existing = _existing_receipt(path, key)
    if existing is not None:
        return {"status": "DUPLICATE", "receipt": existing, "key": list(key)}
    path.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "schema_version": LEDGER_SCHEMA,
        "at": str(receipt.get("timestamp", utc_now())),
        "event": LEDGER_EVENT,
        "receipt": dict(receipt),
    }
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
    return {"status": "RECORDED", "receipt": dict(receipt), "key": list(key)}


def process_payload(payload: object, root: str | Path) -> dict[str, Any]:
    """Process a hook payload without raising into the host."""

    if not isinstance(payload, Mapping):
        return {"status": "IGNORED", "reason": "INVALID_JSON_OBJECT"}
    receipt = build_receipt(payload)
    if receipt is None:
        return {"status": "IGNORED", "reason": "INVALID_SUBAGENT_LIFECYCLE_PAYLOAD"}
    try:
        return append_receipt(receipt, _discover_project_root(Path(root)))
    except (OSError, UnicodeError, TypeError, ValueError):
        return {"status": "IGNORED", "reason": "LEDGER_WRITE_FAILED"}


def _read_payload() -> object | None:
    try:
        raw = sys.stdin.read()
        return json.loads(raw)
    except (OSError, UnicodeError, ValueError):
        return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Project root or a path below the project root")
    args = parser.parse_args(argv)
    payload = _read_payload()
    if payload is not None:
        process_payload(payload, args.root)
    # Never write hook output: stdout can become model-visible context.  A
    # failed receipt is intentionally indistinguishable from no receipt to the
    # child and therefore cannot block or rewrite its execution.
    return 0


def read_receipts(ledger: str | Path) -> list[dict[str, Any]]:
    """Return only valid host receipt objects from an execution ledger."""

    path = _ledger_path(ledger)
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
        if not isinstance(receipt, Mapping) or not validate_receipt(receipt):
            continue
        receipts.append(dict(receipt))
    return receipts


def find_verified_identity(
    ledger: str | Path,
    expected_agent_type: str = "p2p_aesthetica",
    *,
    agent_id: str | None = None,
) -> dict[str, Any] | None:
    """Return an exact host receipt or ``None``; never infer from a profile."""

    if not is_supported_host_agent_type(expected_agent_type):
        return None
    for receipt in read_receipts(ledger):
        if receipt.get("agent_type") != expected_agent_type:
            continue
        if agent_id is not None and receipt.get("agent_id") != agent_id:
            continue
        return receipt
    return None


if __name__ == "__main__":
    raise SystemExit(main())
