"""P2P-BOUNDED-DOCUMENTATION-WRITE-01A — Authority-chain certification
ledger.

Two narrow, additive (write-only) certification registries close the
authority chain for the canonical bounded documentation write:

  1. BACKEND_MUTATION_CERTIFICATION: the execution target is
     LIVE_CERTIFIED for the DOCUMENTATION_MUTATION_BOUNDED scope.
  2. ROLE_MUTATION_CERTIFICATION: the selected role holds a
     subject-bound WRITE_BOUNDED certification for
     bounded_documentation_write, anchored by an owner mutation
     authorization id.

These registries are STATE (write-only additive ledgers, latest entry
per key wins) — never policy, never an invention of the executor. A
record absent from the ledger is provably absent (positive negative),
not UNKNOWN (fail closed).

Ledger shape (dict list, one JSON file each):
  .p2p/state/authority_chain_registry.json
  entries: list[dict]  (write-only append; latest matching entry wins)

No record grants current eligibility by itself: eligibility remains
task-gated and owner-gated (OWNER_GATE_REQUIRED semantics). A mutation
receipt without BOTH ledger records closed over its exact execution
context fails the whole-claim authority-chain check.
"""
from __future__ import annotations

import datetime as _ac_datetime
import json as _ac_json
import os as _ac_os
import pathlib as _ac_pathlib

AUTHORITY_CHAIN_SCHEMA = "p2p-authority-chain-certification/1"


def authority_chain_registry_path() -> _ac_pathlib.Path:
    """Lazy path resolution: P2P_STATE_DIR is re-evaluated on every
    access so bounded test fixtures get an isolated ledger. Production
    uses the canonical .p2p/state location."""
    return _ac_pathlib.Path(_ac_os.environ.get(
        "P2P_STATE_DIR", "") or str(
            _ac_pathlib.Path(__file__).resolve().parents[1] / ".p2p" /
            "state")) / "authority_chain_registry.json"


def _registry_entries() -> list:
    try:
        _path = authority_chain_registry_path()
        if _path.exists():
            return list(_ac_json.loads(_path.read_text()) or [])
    except Exception:
        pass
    return []


def _persist_registry(records: list) -> None:
    _path = authority_chain_registry_path()
    _path.parent.mkdir(parents=True, exist_ok=True)
    _path.write_text(
        _ac_json.dumps(records, indent=2, sort_keys=False,
                       ensure_ascii=False) + "\n")

BACKEND_MUTATION_CERTIFICATION = "BACKEND_MUTATION_CERTIFICATION"
ROLE_MUTATION_CERTIFICATION = "ROLE_MUTATION_CERTIFICATION"
AUTHORITY_CERTIFICATION_KINDS = (BACKEND_MUTATION_CERTIFICATION,
                                 ROLE_MUTATION_CERTIFICATION)
MUTATION_TARGET_LIVE = "LIVE_CERTIFIED_FOR_CAPABILITY"
ROLE_MUTATION_LIVE = "ROLE_MUTATION_CERTIFIED"
CANONICAL_BOUNDED_SCOPE = "DOCUMENTATION_MUTATION_BOUNDED"
CANONICAL_BOUNDED_CAPABILITY = "bounded_documentation_write"
CANONICAL_ROLE_MUTATION_GRANT = "WRITE_BOUNDED"


def _utc_now() -> str:
    return _ac_datetime.datetime.now(_ac_datetime.timezone.utc).isoformat()


def append_backend_mutation_certification(
        *, target_id: str, adapter_id: str,
        evidence_pointers: tuple[str, ...] = (),
        lifetime_days: int = 7,
        certified_at: str | None = None) -> dict:
    """Record that the target is LIVE_CERTIFIED for the bounded
    documentation-mutation scope. Write-only additive; the latest
    matching entry wins for lookup purposes. Fail closed on any
    placeholder or unknown target identity."""
    target_id = str(target_id).strip()
    adapter_id = str(adapter_id).strip()
    if not target_id or target_id.upper() in ("UNKNOWN", "NONE", ""):
        raise ValueError("backend mutation certification: target_id "
                         "placeholder rejected")
    if not adapter_id or adapter_id.upper() in ("UNKNOWN", "NONE", ""):
        raise ValueError("backend mutation certification: adapter_id "
                         "placeholder rejected")
    if not isinstance(lifetime_days, int) or lifetime_days <= 0:
        raise ValueError("backend mutation certification: lifetime_days "
                         "must be a positive integer")
    _certified_at = (str(certified_at).strip() if certified_at
                     else _utc_now())
    _expiry = (_ac_datetime.datetime.fromisoformat(
        _certified_at.replace("Z", "+00:00"))
        + _ac_datetime.timedelta(days=lifetime_days)).isoformat()
    entry = {
        "schema": AUTHORITY_CHAIN_SCHEMA,
        "kind": BACKEND_MUTATION_CERTIFICATION,
        "target_id": target_id,
        "adapter_id": adapter_id,
        "scope": CANONICAL_BOUNDED_SCOPE,
        "status": MUTATION_TARGET_LIVE,
        "evidence_pointers": tuple(evidence_pointers),
        "certified_at": _certified_at,
        "expires_at": _expiry,
        "registered_at": _utc_now(),
    }
    records = _registry_entries()
    records.append(entry)
    _persist_registry(records)
    return entry


def append_role_mutation_certification(
        *, role_id: str, owner_authorization_id: str,
        scope: str = CANONICAL_BOUNDED_SCOPE,
        permission_grant: str = CANONICAL_ROLE_MUTATION_GRANT,
        capability_id: str = CANONICAL_BOUNDED_CAPABILITY,
        source_commit: str = "",
        evidence_pointers: tuple[str, ...] = (),
        lifetime_days: int = 7,
        certified_at: str | None = None) -> dict:
    """Record a subject-bound role certification for the canonical
    bounded documentation write: the selected role, the capability,
    the certified execution scope, and the single owner mutation
    authorization that licensed the grant. Fail closed on any
    placeholder identity, non-canonical grant, or non-canonical
    scope."""
    role_id = str(role_id).strip()
    _oaid = str(owner_authorization_id).strip()
    if not role_id or role_id.upper() in ("UNKNOWN", "NONE", ""):
        raise ValueError("role mutation certification: role_id "
                         "placeholder rejected")
    if (not _oaid or _oaid.upper() in ("UNKNOWN", "NONE", "")
            or not _oaid.startswith("owner-mutation-")):
        raise ValueError("role mutation certification: "
                         "owner_authorization_id must be a non-empty "
                         "owner-mutation-* id")
    if permission_grant != CANONICAL_ROLE_MUTATION_GRANT:
        raise ValueError("role mutation certification: permission_grant "
                         f"must be {CANONICAL_ROLE_MUTATION_GRANT}")
    if scope not in (CANONICAL_BOUNDED_SCOPE,):
        raise ValueError("role mutation certification: scope must be "
                         f"{CANONICAL_BOUNDED_SCOPE}")
    if capability_id != CANONICAL_BOUNDED_CAPABILITY:
        raise ValueError("role mutation certification: capability_id "
                         f"must be {CANONICAL_BOUNDED_CAPABILITY}")
    _certified_at = (str(certified_at).strip() if certified_at
                     else _utc_now())
    _expiry = (_ac_datetime.datetime.fromisoformat(
        _certified_at.replace("Z", "+00:00"))
        + _ac_datetime.timedelta(days=lifetime_days)).isoformat()
    entry = {
        "schema": AUTHORITY_CHAIN_SCHEMA,
        "kind": ROLE_MUTATION_CERTIFICATION,
        "role_id": role_id,
        "capability_id": capability_id,
        "scope": scope,
        "permission_grant": permission_grant,
        "owner_authorization_id": _oaid,
        "source_commit": str(source_commit or "").strip().lower(),
        "evidence_pointers": tuple(evidence_pointers),
        "certified_at": _certified_at,
        "expires_at": _expiry,
        "registered_at": _utc_now(),
    }
    records = _registry_entries()
    records.append(entry)
    _persist_registry(records)
    return entry


def latest_backend_mutation_certification(target_id: str) -> dict | None:
    """Latest backend mutation certification for the target. An absent
    target is provably uncertified (positive negative) — never
    UNKNOWN."""
    out: dict | None = None
    for entry in _registry_entries():
        if (entry.get("kind") == BACKEND_MUTATION_CERTIFICATION
                and str(entry.get("target_id", "")).strip()
                == str(target_id).strip()):
            out = entry
    return out


def latest_role_mutation_certification(
        role_id: str, owner_authorization_id: str | None = None) -> dict | None:
    """Latest role mutation certification for the role (optionally
    bound to the exact owner authorization id). Absent means
    provably uncertified."""
    out: dict | None = None
    for entry in _registry_entries():
        if entry.get("kind") != ROLE_MUTATION_CERTIFICATION:
            continue
        if str(entry.get("role_id", "")).strip() != str(role_id).strip():
            continue
        if owner_authorization_id and str(
                entry.get("owner_authorization_id", "")).strip() != \
                str(owner_authorization_id).strip():
            continue
        out = entry
    return out


def clear_authority_chain_registry_for_tests() -> None:
    """TEST-ONLY: wipe the ledger for a clean fixture state. Must never
    be called outside a bounded test fixture (ledger is write-only
    additive in production)."""
    _persist_registry([])
