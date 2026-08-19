"""C36 Real host execution attestation (Owner-approved design v2).

p2p-host-attestation/1 schema; fail-closed everywhere; replay ledger.
Owner amendments:
  1. Attestation binds run_id + dispatch_id + execution_contract_digest.
  2. Evidence pointers are verified sources, not self-written strings.
  3. Mandatory replay protection: reused attestations fail closed.
  4. Vendor-neutral host kinds (codex/manus/claude/generic-real).
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


class HostAttestationError(Exception):
    """Fail-closed error carrying a stable error code."""
    def __init__(self, code: str, context: dict[str, Any] | None = None) -> None:
        super().__init__(code)
        self.code = code
        self.context = context or {}


HOST_KINDS: tuple[str, ...] = ("codex", "manus", "claude", "generic-real")
MAX_HOST_METADATA_CHARS = 1024
MAX_ATTESTED_AT_CHARS = 128
EVIDENCE_SNAPSHOT_READ_LIMIT = 2 * 1024 * 1024


def _hex64(value: str, field_name: str) -> str:
    text = str(value or "").strip()
    if not re.fullmatch(r"[0-9a-fA-F]{64}", text):
        raise HostAttestationError("ATTESTATION_HASH_INVALID", {"field": field_name})
    return text.lower()


def _limited_text(value: str, field_name: str, max_length: int) -> str:
    text = str(value or "")
    if len(text) > max_length:
        raise HostAttestationError("ATTESTATION_FIELD_TOO_LONG", {"field": field_name})
    return text


def canonical_bytes(mapping: Mapping[str, Any]) -> bytes:
    return json.dumps(mapping, sort_keys=True, ensure_ascii=False).encode("utf-8")



@dataclass(frozen=True)
class HostAttestationRecord:
    """p2p-host-attestation/1. Fail-closed everywhere; absent optional
    fields stay absent (byte-identical to C35 when host_attestation is not
    declared)."""
    schema: str = "p2p-host-attestation/1"
    host_kind: str = "UNKNOWN"
    adapter_id: str = ""
    harness: str = "unknown"
    provider: str = "unknown"
    model: str = "unknown"
    host_execution_identity: str = ""
    run_id: str = ""
    dispatch_id: str = ""
    execution_contract_digest: str = ""
    host_identity_fingerprint: str = ""
    attestation_fingerprint: str = ""
    host_metadata: str = ""
    source_snapshot_digest: str = ""
    attestation_evidence_pointers: tuple[str, ...] = ()
    attested_at: str = ""

    # --------------------------------------------------------------
    # Validation (Owner amendments 1/2/3/4)
    # --------------------------------------------------------------
    def __post_init__(self) -> None:
        # Schema is fixed: p2p-host-attestation/1.
        if self.schema != "p2p-host-attestation/1":
            raise HostAttestationError("ATTESTATION_SCHEMA_MISMATCH", {})
        # Owner amendment 4: only vendor-neutral real host kinds.
        if self.host_kind not in HOST_KINDS:
            raise HostAttestationError("ATTESTATION_HOST_KIND_INVALID", {})
        # Owner amendment 2/4: identity must come from a real runtime.
        identity = str(self.host_execution_identity).strip()
        if not identity or identity.lower() in ("synthetic",
                                "unknown", "none"):
            raise HostAttestationError("ATTESTATION_IDENTITY_MISSING",
                                       {"host_execution_identity":
                                        identity[:64]})
        object.__setattr__(self, "host_execution_identity",
                           identity[:128])
        for name in ("adapter_id",):
            object.__setattr__(self, name,
                               _limited_text(str(getattr(self, name)),
                                             name, 128))
        for name in ("harness", "provider", "model"):
            object.__setattr__(self, name,
                               _limited_text(str(getattr(self, name)),
                                             name, 64))
        # Owner amendment 2: self-authored pointer strings are
        # verified sources, never assumed.
        pointers: list[str] = []
        for index, pointer in enumerate(self.attestation_evidence_pointers):
            text = str(pointer).strip()
            if not text:
                raise HostAttestationError("ATTESTATION_EMPTY_EVIDENCE_POINTER", {"index": index})
            pointers.append(text[:512])
        if not pointers:
            raise HostAttestationError("ATTESTATION_NO_EVIDENCE_POINTERS", {})
        object.__setattr__(self, "attestation_evidence_pointers",
                           tuple(pointers))
        if self.host_metadata:
            object.__setattr__(self, "host_metadata",
                               _limited_text(self.host_metadata,
                                             "host_metadata",
                                             MAX_HOST_METADATA_CHARS))
        if self.source_snapshot_digest:
            object.__setattr__(self, "source_snapshot_digest",
                               _hex64(self.source_snapshot_digest,
                                      "source_snapshot_digest"))
        object.__setattr__(self, "attested_at",
                           _limited_text(self.attested_at, "attested_at",
                                         MAX_ATTESTED_AT_CHARS))
        if not str(self.attested_at).strip():
            raise HostAttestationError("ATTESTATION_TIMESTAMP_MISSING", {})
        # Owner amendment 1: run + dispatch + contract digest bind.
        for name, value in (("run_id", self.run_id),
                            ("dispatch_id", self.dispatch_id),
                            ("execution_contract_digest",
                             self.execution_contract_digest)):
            if not str(value).strip():
                raise HostAttestationError("ATTESTATION_DISPATCH_BINDING_MISSING", {"field": name})
        object.__setattr__(self, "execution_contract_digest",
                           _hex64(self.execution_contract_digest,
                                  "execution_contract_digest"))
        for name in ("run_id", "dispatch_id"):
            object.__setattr__(self, name,
                               _limited_text(str(getattr(self, name)),
                                             name, 128))
        # Derived fingerprints: host identity surface first.
        identity_surface = {
            "adapter_id": self.adapter_id,
            "harness": self.harness,
            "provider": self.provider,
            "model": self.model,
            "host_execution_identity":
                self.host_execution_identity,
        }
        computed_identity = hashlib.sha256(canonical_bytes(identity_surface)).hexdigest()
        if (self.host_identity_fingerprint
                and self.host_identity_fingerprint != computed_identity):
            raise HostAttestationError("ATTESTATION_IDENTITY_FINGERPRINT_MISMATCH", {})
        object.__setattr__(self, "host_identity_fingerprint",
                           computed_identity)
        # Owner amendment 3: replay-distinguishable identity binds
        # the WHOLE record (computed with the field absent).
        base = self.to_dict()
        del base["attestation_fingerprint"]
        computed = hashlib.sha256(canonical_bytes(base)).hexdigest()
        if (self.attestation_fingerprint
                and self.attestation_fingerprint != computed):
            raise HostAttestationError("ATTESTATION_FINGERPRINT_MISMATCH", {})
        object.__setattr__(self, "attestation_fingerprint", computed)

    # --------------------------------------------------------------
    # Serialization / deserialization
    # --------------------------------------------------------------
    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "host_kind": self.host_kind,
            "adapter_id": self.adapter_id,
            "harness": self.harness,
            "provider": self.provider,
            "model": self.model,
            "host_execution_identity":
                self.host_execution_identity,
            "run_id": self.run_id,
            "dispatch_id": self.dispatch_id,
            "execution_contract_digest":
                self.execution_contract_digest,
            "host_identity_fingerprint":
                self.host_identity_fingerprint,
            "attestation_fingerprint":
                self.attestation_fingerprint,
            "host_metadata": self.host_metadata,
            "source_snapshot_digest":
                self.source_snapshot_digest,
            "attestation_evidence_pointers": list(self.attestation_evidence_pointers),
            "attested_at": self.attested_at,
        }

    @classmethod
    def from_mapping(cls, mapping: Mapping[str, Any]) -> "HostAttestationRecord":
        """Reconstruct a record from a plain dict (deserialized
        receipt)."""
        known = {
            "schema", "host_kind", "adapter_id", "harness",
            "provider", "model", "host_execution_identity",
            "run_id", "dispatch_id",
            "execution_contract_digest",
            "host_identity_fingerprint",
            "attestation_fingerprint", "host_metadata",
            "source_snapshot_digest",
            "attestation_evidence_pointers", "attested_at",
        }
        kwargs = {key: value for key, value in mapping.items()
                  if key in known}
        pointers = kwargs.get("attestation_evidence_pointers") or ()
        if isinstance(pointers, list):
            kwargs["attestation_evidence_pointers"] = tuple(pointers)
        return cls(**kwargs)


def make_host_attestation(
    *,
    host_kind: str = "generic-real",
    adapter_id: str = "",
    harness: str = "unknown",
    provider: str = "unknown",
    model: str = "unknown",
    host_execution_identity: str = "",
    run_id: str = "",
    dispatch_id: str = "",
    execution_contract_digest: str = "",
    host_metadata: str = "",
    source_snapshot_digest: str = "",
    attestation_evidence_pointers: tuple[str, ...] = (),
    attested_at: str = "",
) -> HostAttestationRecord:
    """Public constructor for a validated real-host attestation
    record."""
    return HostAttestationRecord(
        host_kind=host_kind, adapter_id=adapter_id, harness=harness,
        provider=provider, model=model,
        host_execution_identity=host_execution_identity,
        run_id=run_id, dispatch_id=dispatch_id,
        execution_contract_digest=execution_contract_digest,
        host_metadata=host_metadata,
        source_snapshot_digest=source_snapshot_digest,
        attestation_evidence_pointers=attestation_evidence_pointers,
        attested_at=attested_at,
    )


# ---------------------------------------------------------------------------
# Evidence source verification -- Owner amendment 2.
# A pointer string the executor wrote counts as nothing until the source
# is observed to exist and its content binds.
# ---------------------------------------------------------------------------


def verify_role_evidence_source(
    pointer: str,
    *,
    expected_digest: str = "",
    read_limit: int = EVIDENCE_SNAPSHOT_READ_LIMIT,
) -> dict[str, Any]:
    """Observe an evidence source and check its digest.
    Pointer grammar: file:<absolute path> -- the only verifier-observable
    pointer type. Any other scheme (including bare prose strings the
    executor invented) is SOURCE_UNVERIFIABLE."""
    text = str(pointer).strip()
    if not text.startswith("file:"):
        return {"status": "SOURCE_UNVERIFIABLE", "pointer": text[:256],
                "reason": "NON_FILE_EVIDENCE_POINTER_NOT_OBSERVABLE"}
    path_text = text[len("file:"):].strip()
    if not path_text:
        return {"status": "SOURCE_UNVERIFIABLE", "pointer": text[:256],
                "reason": "EMPTY_FILE_POINTER"}
    path = Path(path_text)
    if not path.is_absolute():
        candidates: list[Path] = []
    else:
        candidates = [path]
    existing: Path | None = None
    for candidate in candidates:
        if candidate.is_file():
            existing = candidate
            break
    if existing is None:
        return {"status": "SOURCE_ABSENT", "pointer": text[:256]}
    try:
        with open(existing, "rb") as handle:
            digest = hashlib.sha256(handle.read(read_limit)).hexdigest()
    except OSError:
        return {"status": "SOURCE_UNVERIFIABLE", "pointer": text[:256],
                "reason": "EVIDENCE_READ_FAILED"}
    if expected_digest:
        expected = _hex64(expected_digest, "expected_digest")
        status = ("SOURCE_PRESENT_MATCH" if digest == expected
                  else "SOURCE_PRESENT_DIGEST_MISMATCH")
        return {"status": status, "pointer": text[:256], "digest":
                digest, "source_path": str(existing)}
    return {"status": "SOURCE_PRESENT_MATCH", "pointer": text[:256],
            "digest": digest, "source_path": str(existing)}


def verify_all_attestation_sources(
    record: HostAttestationRecord,
    *,
    expect_digest: bool = False,
) -> dict[str, Any]:
    """Owner amendment 2 + 3: every declared evidence pointer must
    resolve to SOURCE_PRESENT_MATCH; embedded source_snapshot_digest
    cross-checks when expect_digest=True. Absent-or-mismatching sources
    fail closed."""
    results: list[dict[str, Any]] = []
    for pointer in record.attestation_evidence_pointers:
        results.append(verify_role_evidence_source(
            pointer, expected_digest=record.source_snapshot_digest
            if expect_digest else ""))
    all_present = all(result["status"] == "SOURCE_PRESENT_MATCH"
                      for result in results)
    digest_mismatch = any(result["status"] == "SOURCE_PRESENT_DIGEST_MISMATCH"
                      for result in results)
    return {
        "sources": results,
        "all_sources_present": all_present,
        "digest_mismatch": digest_mismatch,
    }


# ---------------------------------------------------------------------------
# Replay protection ledger -- Owner amendment 3.
# ---------------------------------------------------------------------------


def _attestation_ledger_path() -> Path:
    root = Path(__file__).resolve().parent.parent
    evidence_dir = root / "evidence" / "c36"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    return evidence_dir / "c36-replay-ledger.jsonl"


def load_attestation_ledger(path: Path | None = None) -> list[dict[str, Any]]:
    file_path = Path(path) if path is not None else _attestation_ledger_path()
    if not file_path.is_file():
        return []
    entries: list[dict[str, Any]] = []
    for line in file_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        entries.append(json.loads(line))
    return entries


def attestation_already_used(fingerprint: str,
                             path: Path | None = None) -> bool:
    return any(entry.get("attestation_fingerprint") == fingerprint
               for entry in load_attestation_ledger(path))


def record_attestation_use(record: HostAttestationRecord,
                           path: Path | None = None) -> None:
    file_path = Path(path) if path is not None else _attestation_ledger_path()
    entry = {
        "attestation_fingerprint": record.attestation_fingerprint,
        "run_id": record.run_id,
        "dispatch_id": record.dispatch_id,
        "execution_contract_digest":
            record.execution_contract_digest,
        "adapter_id": record.adapter_id,
        "host_execution_identity":
            record.host_execution_identity,
        "attested_at": record.attested_at,
    }
    with open(file_path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True, ensure_ascii=False) + "\n")


def mint_dispatch_id(run_id: str, role_id: str, task_id: str,
                     sequence: int) -> str:
    """Deterministic per-dispatch identifier: replay across dispatches
    is distinguished both by content (attestation fingerprint) and by
    this explicit dispatch id."""
    payload = canonical_bytes({
        "run_id": run_id, "role_id": role_id, "task_id": task_id,
        "sequence": sequence,
    })
    return hashlib.sha256(payload).hexdigest()
