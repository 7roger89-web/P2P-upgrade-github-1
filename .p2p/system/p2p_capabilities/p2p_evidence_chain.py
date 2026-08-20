"""P2P-MUTATION-READINESS-GATE-01 — Execution identity chain.

ONE deterministic chain linking goal, task, run, dispatch, execution,
contract, request, backend, target, host and role receipt. Every link
is mechanically explainable: each id is sha256(canonical_bytes(payload))
over a declared, fixed payload schema.

No link depends on wall-clock ordering for its identity; timestamps
are lifecycle evidence, not identity.

Canonical fingerprint policy (GATE-01 fix of the closure fingerprint
contradiction): a role execution has exactly ONE request fingerprint
domain — the canonical RoleExecutionContract digest. The backend
dispatch and the role receipt both carry that digest as their
request_fingerprint. Cross-binding is verified by equality of digests,
never by coincidence of two different hash domains.
"""
from __future__ import annotations

import hashlib
import platform
import re
import socket
from typing import Any, Mapping

from .host_attestation import canonical_bytes

CHAIN_SCHEMA = "p2p-execution-identity-chain/1"

ID_REGEX = re.compile(r"^[0-9a-f]{64}$")

# Fixed payload schemas — identity is defined by the payload, not by
# whatever a caller happened to hash.
_PAYLOAD = {
    "run": ("goal_id", "task_id", "source_commit", "project_commit"),
    "dispatch": ("run_id", "role_id", "task_id", "sequence"),
    "execution": ("dispatch_id", "contract_digest", "target_id"),
    "receipt": ("schema", "execution_id", "contract_digest",
                "request_fingerprint", "attestation_fingerprint",
                "outcome"),
}


def _sha256_hex(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_bytes(dict(payload))).hexdigest()


def _validate_hex(text: str, label: str) -> str:
    text = str(text or "").strip().lower()
    if not ID_REGEX.fullmatch(text):
        raise ValueError(f"{label}_INVALID", {"value": text[:64]})
    return text


def machine_host_identity() -> str:
    """Deterministic vendor-neutral host identity from real runtime
    surfaces. Fail-closed: never 'synthetic' or 'unknown'. Mirrors
    host_attestation.canonical_machine_identity() byte-for-byte."""
    _un = platform.uname()
    _os = __import__("os")
    try:
        _login = _os.getlogin() or ""
    except Exception:  # noqa: BLE001 — sandbox without ctty
        _login = ""
    parts = (
        _un.system or "",   # uname.sysname alias
        _un.release or "",
        _un.machine or "",
        socket.gethostname() or "",
        _login,
    )
    raw = "|".join(parts)
    digest = hashlib.sha256(raw.encode("utf-8", "surrogateescape")).hexdigest()
    return "host-{0}".format(digest[:56])


def mint_run_id(goal_id: str, task_id: str, source_commit: str,
                project_commit: str) -> str:
    """Deterministic run identity from the goal/task and the immutable
    source + project revisions it was planned against."""
    payload = {"goal_id": str(goal_id), "task_id": str(task_id),
               "source_commit": str(source_commit).lower(),
               "project_commit": str(project_commit).lower()}
    return _sha256_hex(payload)


def mint_dispatch_id(run_id: str, role_id: str, task_id: str,
                     sequence: int) -> str:
    """Reuses host_attestation.mint_dispatch_id semantics (deterministic
    per-dispatch identity) so replay ledgers stay cross-compatible."""
    from .host_attestation import mint_dispatch_id as _mdi
    return _mdi(run_id, role_id, task_id, int(sequence))


def mint_execution_id(dispatch_id: str, contract_digest: str,
                      target_id: str) -> str:
    """Execution identity binds the dispatch, the canonical contract,
    and the resolved target."""
    return _sha256_hex({"dispatch_id": str(dispatch_id),
                        "contract_digest": str(contract_digest).lower(),
                        "target_id": str(target_id)})


def mint_receipt_id(execution_id: str, contract_digest: str,
                    request_fingerprint: str,
                    attestation_fingerprint: str,
                    outcome: str = "") -> str:
    """Role receipt identity binds execution, canonical contract, request
    fingerprint, the host attestation that witnessed it, and the
    discrete outcome. Timestamps are never identity — the identical
    payload is re-derived by _receipt_identity at verification and by
    role_receipt.gate01_receipt_identity at emission."""
    from .role_receipt import MUTATION_READY_RECEIPT_SCHEMA as _mrrs
    return _sha256_hex({
        "schema": _mrrs,
        "execution_id": str(execution_id),
        "contract_digest": str(contract_digest).lower(),
        "request_fingerprint": str(request_fingerprint).lower(),
        "attestation_fingerprint": str(attestation_fingerprint).lower(),
        "outcome": str(outcome),
    })


def contract_request_fingerprint(contract: Mapping[str, Any]) -> str:
    """The ONE canonical request fingerprint: digest of the canonical
    role execution contract (semantic field set). Dispatch and receipt
    must both carry this value — no second hash domain."""
    from .role_contract import role_contract_fingerprint
    return role_contract_fingerprint(dict(contract)).lower()


def finalize_identity_chain(chain: Mapping[str, Any],
                              attestation_fingerprint: str,
                              outcome: str = "") -> dict:
    """GATE-01B two-pass identity: the chain is derivable before the
    host attestation exists (planning side), then FINALIZED with the
    real attestation fingerprint + discrete outcome so the recorded
    role_receipt_id equals the canonical receipt identity that the
    receipt emitter and the verifier will re-derive. The chain is
    mutated in place (new object returned) and the finalization
    markers are recorded for verification: an empty attestation
    fingerprint never counts as a bound receipt (fail-closed — no
    stale pre-attestation snapshot may masquerade as evidence)."""
    final = dict(chain)
    fp = str(attestation_fingerprint or "").strip().lower()
    if not ID_REGEX.fullmatch(fp):
        raise ValueError("ATTESTATION_FINGERPRINT_NOT_BOUND",
                         {"attestation_fingerprint": fp[:32]})
    final["attestation_fingerprint"] = fp
    final["outcome"] = str(outcome)
    final["role_receipt_id"] = mint_receipt_id(
        final["execution_id"], final["role_execution_contract_digest"],
        final["request_fingerprint"], fp, outcome)
    return final


def build_identity_chain(*, goal_id: str, task_id: str, role_id: str,
                         contract: Mapping[str, Any],
                         target_id: str,
                         backend_request_id: str,
                         source_commit: str,
                         project_commit: str,
                         run_sequence: int = 1,
                         attestation_fingerprint: str = "") -> dict:
    """Mechanically derive the full chain for one execution.
    Every id is deterministic from earlier ids + declared payload."""
    run_id = mint_run_id(goal_id, task_id, source_commit, project_commit)
    dispatch_id = mint_dispatch_id(run_id, role_id, task_id,
                                   int(run_sequence))
    contract_digest = contract_request_fingerprint(contract)
    request_fingerprint = contract_digest  # one fingerprint domain
    execution_id = mint_execution_id(dispatch_id, contract_digest,
                                     target_id)
    receipt_id = mint_receipt_id(execution_id, contract_digest,
                                 request_fingerprint,
                                 attestation_fingerprint)
    chain = {
        "schema": CHAIN_SCHEMA,
        "goal_id": str(goal_id),
        "task_id": str(task_id),
        "run_id": run_id,
        "dispatch_id": dispatch_id,
        "execution_id": execution_id,
        "role_id": str(role_id),
        "role_execution_contract_digest": contract_digest,
        "request_fingerprint": request_fingerprint,
        "backend_request_id": str(backend_request_id),
        "target_id": str(target_id),
        "host_execution_identity": machine_host_identity(),
        "role_receipt_id": receipt_id,
        "source_commit": str(source_commit).lower(),
        "project_commit": str(project_commit).lower(),
        "run_sequence": int(run_sequence),
    }
    return chain


def _receipt_identity(execution_id: str, contract_digest: str,
                        request_fingerprint: str,
                        attestation_fingerprint: str,
                        outcome: str) -> str:
    """Same deterministic payload that role_receipt.gate01_receipt_identity
    hashes: execution + canonical contract + request fp + host
    attestation + discrete outcome. Timestamps are never identity."""
    from .role_receipt import MUTATION_READY_RECEIPT_SCHEMA as _mrr_schema
    payload = {"schema": _mrr_schema,
               "execution_id": str(execution_id),
               "contract_digest": str(contract_digest).lower(),
               "request_fingerprint": str(request_fingerprint).lower(),
               "attestation_fingerprint":
                   str(attestation_fingerprint).lower(),
               "outcome": str(outcome)}
    return hashlib.sha256(canonical_bytes(payload)).hexdigest()


def verify_identity_chain(chain: Mapping[str, Any]) -> dict:
    """Re-derive every derived id from the chain's own declared fields
    and report per-link equality. A link is VERIFIED only when the
    mechanically re-derived value equals the recorded value."""
    recorded = dict(chain)
    checks: dict[str, Any] = {}

    run_id = mint_run_id(recorded["goal_id"], recorded["task_id"],
                         recorded["source_commit"],
                         recorded["project_commit"])
    checks["run_derivation"] = {
        "expected": run_id, "recorded": recorded["run_id"],
        "verified": run_id == recorded["run_id"],
    }

    dispatch_id = mint_dispatch_id(run_id, recorded["role_id"],
                                   recorded["task_id"],
                                   recorded["run_sequence"])
    checks["dispatch_derivation"] = {
        "expected": dispatch_id, "recorded": recorded["dispatch_id"],
        "verified": dispatch_id == recorded["dispatch_id"],
    }

    exec_id = mint_execution_id(dispatch_id,
                                recorded["role_execution_contract_digest"],
                                recorded["target_id"])
    checks["execution_derivation"] = {
        "expected": exec_id, "recorded": recorded["execution_id"],
        "verified": exec_id == recorded["execution_id"],
    }

    checks["contract_to_dispatch_binding"] = {
        "verified": (recorded["request_fingerprint"]
                     == recorded["role_execution_contract_digest"]),
    }

    rec_id = _receipt_identity(
        exec_id, recorded["role_execution_contract_digest"],
        recorded["request_fingerprint"],
        str(recorded.get("attestation_fingerprint", "")),
        str(recorded.get("outcome", "")))
    checks["receipt_derivation"] = {
        "expected": rec_id,
        "recorded": str(recorded.get("role_receipt_id", "")),
        "verified": rec_id == str(recorded.get("role_receipt_id", "")),
    }

    overall = all(link["verified"] for link in checks.values()
                  if "verified" in link)
    return {"schema": CHAIN_SCHEMA, "overall": overall, "checks": checks}
