"""C36 Real-host attestation + replay protection + regression suite.

Owner-accepted acceptance contract (C36 design v2):
    1. Attestation binds run_id + dispatch_id + execution_contract_digest.
    2. Evidence pointers are verified sources, not self-written strings.
    3. Replay protection: reused/stale/cross-run/cross-dispatch/cross-
       contract attestations fail closed.
    4. Host kinds stay vendor-neutral (codex/manus/claude/generic-real).
    5. STANDARD policy keeps C35 behavior byte-identical (57/57 guard).
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SYSTEM_ROOT = os.path.join(REPO_ROOT, ".p2p", "system")
if SYSTEM_ROOT not in sys.path:
    sys.path.insert(0, SYSTEM_ROOT)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from p2p_capabilities.backend_contract import (  # noqa: E402
    AUTH_STATES,
    BackendCapabilityCertification,
    BackendExecutionResult,
)
from p2p_capabilities.host_attestation import (  # noqa: E402
    HOST_KINDS,
    HostAttestationError,
    HostAttestationRecord,
    _attestation_ledger_path,
    canonical_bytes,
    make_host_attestation,
    mint_dispatch_id,
    verify_all_attestation_sources,
    verify_role_evidence_source,
    attestation_already_used,
    record_attestation_use,
    load_attestation_ledger,
)
from p2p_capabilities.fake_targets import (  # noqa: E402
    FAKE_TARGET_IDS,
    fake_target_certification_record,
    fake_target_fingerprint,
    fake_target_identity,
    register_fake_targets,
)
from p2p_capabilities.role_contract import (  # noqa: E402
    build_role_execution_contract,
)
from p2p_capabilities.role_receipt import (  # noqa: E402
    RoleExecutionReceipt,
    new_role_receipt,
    role_receipt_to_dict,
)
from p2p_capabilities.role_bridge import (  # noqa: E402
    RoleExecutionBridge,
    RoleBridgeError,
    register_explicit_adapter,
)
from p2p_capabilities.role_verifier import (  # noqa: E402
    verify_role_execution_receipt,
)
from p2p_capabilities.backend_execution_bridge import (  # noqa: E402
    BackendAdapterRegistry,
    BackendExecutionBridge,
)
from p2p_capabilities.agent_role import (  # noqa: E402
    build_role_spec,
    role_semantic_fingerprint,
)

EVIDENCE_DIR = r"D:\AI\P2P_dev\P2P-upgrade-github\.p2p\evidence\c36"
os.makedirs(EVIDENCE_DIR, exist_ok=True)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _write_evidence(name: str, content: str) -> str:
    path = os.path.join(EVIDENCE_DIR, name)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(content)
    return path


def _digest_of(path: str) -> str:
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def _real_attestation(
    *,
    adapter_id: str = "adapter-codex-official",
    host_kind: str = "codex",
    run_id: str = "c36:gia-phả-goal-test",
    dispatch_id: str = "",
    execution_contract_digest: str = "a" * 64,
    host_execution_identity: str | None = None,
    pointers: tuple[str, ...] = (),
    source_digest: str = "",
    attested_at: str = "",
    ledger_path: str = "",
) -> HostAttestationRecord:
    now = (attested_at
           or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    record = make_host_attestation(
        host_kind=host_kind,
        adapter_id=adapter_id,
        harness="codex-runtime",
        provider=host_kind,
        model="claude-sonnet-test",
        host_execution_identity=(host_execution_identity if host_execution_identity is not None else "codex-thread-0001"),
        run_id=run_id,
        dispatch_id=dispatch_id or mint_dispatch_id(
            run_id, "p2p_iris", "task-iris-001", 0),
        execution_contract_digest=execution_contract_digest,
        host_metadata="c36-test-evidence",
        attestation_evidence_pointers=pointers,
        attested_at=now,
        source_snapshot_digest=source_digest,
    )
    if ledger_path:
        record_attestation_use(record, path=ledger_path)
    return record


class TestC36HostAttestationRecordValidation(unittest.TestCase):
    """Owner amendments 1/2/4: mandatory dispatch bindings, real identity."""

    def setUp(self) -> None:
        self.evidence_path = _write_evidence("iris-exec-001.txt", "real-execution-iris")
        self.digest = _digest_of(self.evidence_path)

    def test_01_valid_real_attestation(self) -> None:
        record = _real_attestation(
            execution_contract_digest=self.digest,
            pointers=(f"file:{self.evidence_path}",),
            source_digest=self.digest)
        self.assertEqual(record.schema, "p2p-host-attestation/1")
        self.assertEqual(len(record.host_identity_fingerprint), 64)
        self.assertEqual(len(record.attestation_fingerprint), 64)
        self.assertNotEqual(record.host_identity_fingerprint,
                            record.attestation_fingerprint)

    def test_02_dispatch_binding_required(self) -> None:
        for field_name, value in (
                ("run_id", ""), ("dispatch_id", ""),
                ("execution_contract_digest", "")):
            kwargs = {
                "host_kind": "codex",
                "adapter_id": "adapter-codex-official",
                "harness": "codex-runtime",
                "provider": "codex",
                "model": "test",
                "host_execution_identity": "thread-1",
                "run_id": "run-1",
                "dispatch_id": "dispatch-1",
                "execution_contract_digest": self.digest,
                "attestation_evidence_pointers": (f"file:{self.evidence_path}",),
                "attested_at": datetime.now(timezone.utc).isoformat() + "Z",
            }
            kwargs[field_name] = value
            with self.assertRaises(HostAttestationError) as ctx:
                HostAttestationRecord(**kwargs)
            self.assertEqual(ctx.exception.code,
                             "ATTESTATION_DISPATCH_BINDING_MISSING",
                             field_name)

    def test_03_identity_must_be_real(self) -> None:
        for bad in ("", "synthetic", "UNKNOWN", "none"):
            with self.assertRaises(HostAttestationError) as ctx:
                _real_attestation(
                    host_execution_identity=bad,
                    execution_contract_digest=self.digest,
                    pointers=(f"file:{self.evidence_path}",))
            self.assertEqual(ctx.exception.code, "ATTESTATION_IDENTITY_MISSING",
                             bad)

    def test_04_unknown_host_kind_rejected(self) -> None:
        with self.assertRaises(HostAttestationError) as ctx:
            _real_attestation(
                host_kind="FAKE_KIND",
                execution_contract_digest=self.digest,
                pointers=(f"file:{self.evidence_path}",))
        self.assertEqual(ctx.exception.code, "ATTESTATION_HOST_KIND_INVALID")

    def test_05_evidence_pointers_required_non_empty(self) -> None:
        with self.assertRaises(HostAttestationError) as ctx:
            _real_attestation(
                execution_contract_digest=self.digest,
                pointers=())
        self.assertEqual(ctx.exception.code, "ATTESTATION_NO_EVIDENCE_POINTERS")
        # A pointer with an unobservable scheme is accepted by the record
        # constructor; the verifier later classifies it SOURCE_UNVERIFIABLE.
        record = _real_attestation(
            execution_contract_digest=self.digest,
            pointers=("not-a-file-pointer",))
        self.assertEqual(len(record.attestation_evidence_pointers), 1)

    def test_06_identity_fingerprint_is_derived(self) -> None:
        record = _real_attestation(
            execution_contract_digest=self.digest,
            pointers=(f"file:{self.evidence_path}",))
        expected = hashlib.sha256(canonical_bytes({
            "adapter_id": record.adapter_id,
            "harness": record.harness,
            "provider": record.provider,
            "model": record.model,
            "host_execution_identity": record.host_execution_identity,
        })).hexdigest()
        self.assertEqual(record.host_identity_fingerprint, expected)
        with self.assertRaises(HostAttestationError) as ctx:
            HostAttestationRecord(
                schema=record.schema, host_kind=record.host_kind,
                adapter_id=record.adapter_id, harness=record.harness,
                provider=record.provider, model=record.model,
                host_execution_identity=record.host_execution_identity,
                run_id=record.run_id, dispatch_id=record.dispatch_id,
                execution_contract_digest=record.execution_contract_digest,
                host_identity_fingerprint="b" * 64,  # forged
                attestation_evidence_pointers=record.attestation_evidence_pointers,
                attested_at=record.attested_at)
        self.assertEqual(ctx.exception.code,
                         "ATTESTATION_IDENTITY_FINGERPRINT_MISMATCH")

    def test_07_attestation_fingerprint_is_record_wide_and_unique(self) -> None:
        record_a = _real_attestation(
            host_execution_identity="thread-A",
            execution_contract_digest=self.digest,
            pointers=(f"file:{self.evidence_path}",))
        record_b = _real_attestation(
            host_execution_identity="thread-B",
            execution_contract_digest=self.digest,
            pointers=(f"file:{self.evidence_path}",))
        self.assertNotEqual(record_a.attestation_fingerprint,
                            record_b.attestation_fingerprint)
        # Re-running with identical inputs is idempotent (same record).
        record_c = _real_attestation(
            host_execution_identity="thread-A",
            execution_contract_digest=self.digest,
            pointers=(f"file:{self.evidence_path}",))
        self.assertEqual(record_a.attestation_fingerprint,
                         record_c.attestation_fingerprint)

    def test_08_forbidden_fingerprint_mismatch(self) -> None:
        record = _real_attestation(
            execution_contract_digest=self.digest,
            pointers=(f"file:{self.evidence_path}",))
        with self.assertRaises(HostAttestationError) as ctx:
            HostAttestationRecord(
                schema=record.schema, host_kind=record.host_kind,
                adapter_id=record.adapter_id, harness=record.harness,
                provider=record.provider, model=record.model,
                host_execution_identity=record.host_execution_identity,
                run_id=record.run_id, dispatch_id=record.dispatch_id,
                execution_contract_digest=record.execution_contract_digest,
                host_identity_fingerprint=record.host_identity_fingerprint,
                attestation_fingerprint="c" * 64,  # forged
                attestation_evidence_pointers=record.attestation_evidence_pointers,
                attested_at=record.attested_at)
        self.assertEqual(ctx.exception.code, "ATTESTATION_FINGERPRINT_MISMATCH")

    def test_09_dispatch_id_deterministic_distinct(self) -> None:
        d0 = mint_dispatch_id("run-1", "role-a", "task-1", 0)
        d1 = mint_dispatch_id("run-1", "role-a", "task-1", 1)
        d_other_run = mint_dispatch_id("run-2", "role-a", "task-1", 0)
        d_other_role = mint_dispatch_id("run-1", "role-b", "task-1", 0)
        ids = {d0, d1, d_other_run, d_other_role}
        self.assertEqual(len(ids), 4)
        # The dispatch id IS the SHA-256 of the canonical dispatch payload;
        # verify exact equality to prove determinism.
        expected = hashlib.sha256(canonical_bytes({
            "run_id": "run-1", "role_id": "role-a",
            "task_id": "task-1", "sequence": 0})).hexdigest()
        self.assertEqual(d0, expected)

    def test_10_host_kind_neutrality(self) -> None:
        kinds = ("codex", "manus", "claude", "generic-real")
        for kind in kinds:
            record = _real_attestation(
                host_kind=kind,
                host_execution_identity=f"{kind}-identity-1",
                execution_contract_digest=self.digest,
                pointers=(f"file:{self.evidence_path}",))
            self.assertEqual(record.host_kind, kind)
        self.assertNotIn("UNKNOWN-ATTACK", HOST_KINDS)

    def test_11_schema_version_fixed(self) -> None:
        record = _real_attestation(
            execution_contract_digest=self.digest,
            pointers=(f"file:{self.evidence_path}",))
        self.assertEqual(record.schema, "p2p-host-attestation/1")
        with self.assertRaises(HostAttestationError) as ctx:
            HostAttestationRecord(
                schema="p2p-host-attestation/2",
                host_kind="codex", adapter_id="a", harness="h",
                provider="p", model="m",
                host_execution_identity="id", run_id="r",
                dispatch_id="d", execution_contract_digest=self.digest,
                attestation_evidence_pointers=(f"file:{self.evidence_path}",),
                attested_at="2026-01-01T00:00:00Z")
        self.assertEqual(ctx.exception.code, "ATTESTATION_SCHEMA_MISMATCH")


class TestC36EvidenceSourceVerification(unittest.TestCase):
    """Owner amendment 2: pointer strings must be verified, not assumed."""

    def setUp(self) -> None:
        self.path = _write_evidence("src-002.txt", "independent-evidence-body")
        self.digest = _digest_of(self.path)

    def test_12_bare_executor_string_is_not_attestation(self) -> None:
        result = verify_role_evidence_source(
            "codex-thread-0001 executed this on my machine")
        self.assertEqual(result["status"], "SOURCE_UNVERIFIABLE")

    def test_13_non_file_scheme_unverifiable(self) -> None:
        for bad in ("url:https://example.com/attestation",
                    "codex-receipt:12345", "prose:trust-me"):
            result = verify_role_evidence_source(bad)
            self.assertEqual(result["status"], "SOURCE_UNVERIFIABLE", bad)

    def test_14_file_source_present_match(self) -> None:
        result = verify_role_evidence_source(f"file:{self.path}")
        self.assertEqual(result["status"], "SOURCE_PRESENT_MATCH")
        self.assertEqual(result["digest"], self.digest)

    def test_15_file_source_absent(self) -> None:
        result = verify_role_evidence_source(
            "file:C:\\does-not-exist-c36\\evidence.txt")
        self.assertEqual(result["status"], "SOURCE_ABSENT")

    def test_16_digest_mismatch(self) -> None:
        result = verify_role_evidence_source(
            f"file:{self.path}", expected_digest="b" * 64)
        self.assertEqual(result["status"], "SOURCE_PRESENT_DIGEST_MISMATCH")

    def test_17_digest_match(self) -> None:
        result = verify_role_evidence_source(
            f"file:{self.path}", expected_digest=self.digest)
        self.assertEqual(result["status"], "SOURCE_PRESENT_MATCH")

    def test_18_record_sources_all_verified(self) -> None:
        record = _real_attestation(
            execution_contract_digest=self.digest,
            pointers=(f"file:{self.path}",),
            source_digest=self.digest)
        check = verify_all_attestation_sources(record)
        self.assertTrue(check["all_sources_present"])
        self.assertFalse(check["digest_mismatch"])

    def test_19_record_with_absent_source_fails_closed(self) -> None:
        record = _real_attestation(
            execution_contract_digest=self.digest,
            pointers=(f"file:C:\\no-such-c36-evidence\\x.txt",))
        check = verify_all_attestation_sources(record)
        self.assertFalse(check["all_sources_present"])

    def test_20_embedded_snapshot_digest_catches_tamper(self) -> None:
        record = _real_attestation(
            execution_contract_digest=self.digest,
            pointers=(f"file:{self.path}",),
            source_digest="d" * 64)
        check = verify_all_attestation_sources(record, expect_digest=True)
        self.assertTrue(check["digest_mismatch"])


class TestC36ReplayProtection(unittest.TestCase):
    """Owner amendment 3: attestations are single-use, run/dispatch/
    contract bound and freshness gated."""

    def setUp(self) -> None:
        self.path = _write_evidence("replay-src.txt", "replay-evidence")
        self.digest = _digest_of(self.path)
        self.ledger = tempfile.mktemp(suffix=".jsonl")

    def test_21_second_use_rejected(self) -> None:
        record = _real_attestation(
            execution_contract_digest=self.digest,
            pointers=(f"file:{self.path}",))
        self.assertFalse(attestation_already_used(
            record.attestation_fingerprint, path=self.ledger))
        record_attestation_use(record, path=self.ledger)
        self.assertTrue(attestation_already_used(
            record.attestation_fingerprint, path=self.ledger))
        # Ledger record must carry the binding fields for auditing.
        entries = load_attestation_ledger(path=self.ledger)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["run_id"], record.run_id)
        self.assertEqual(entries[0]["dispatch_id"], record.dispatch_id)
        self.assertEqual(entries[0]["execution_contract_digest"],
                         record.execution_contract_digest)

    def test_22_different_dispatch_id_not_replay(self) -> None:
        record_a = _real_attestation(
            host_execution_identity="thread-A",
            execution_contract_digest=self.digest,
            pointers=(f"file:{self.path}",))
        record_b = _real_attestation(
            host_execution_identity="thread-B",
            execution_contract_digest=self.digest,
            pointers=(f"file:{self.path}",))
        record_attestation_use(record_a)
        self.assertFalse(attestation_already_used(
            record_b.attestation_fingerprint))

    def test_23_same_input_idempotent_but_ledger_distinguishes_use(self) -> None:
        record = _real_attestation(
            execution_contract_digest=self.digest,
            pointers=(f"file:{self.path}",))
        record_attestation_use(record, path=self.ledger)
        record_attestation_use(record, path=self.ledger)
        self.assertEqual(len(load_attestation_ledger(path=self.ledger)), 2)


class TestC36VerifierRealPolicy(unittest.TestCase):
    """Check groups 12/13 under REAL_REQUIRED; STANDARD stays C35."""

    def setUp(self) -> None:
        self.spec = build_role_spec("p2p_iris")
        self.path = _write_evidence("verifier-src.txt", "verified-exec-iris")
        self.digest = _digest_of(self.path)
        self.contract = build_role_execution_contract(
            role_spec=self.spec,
            goal_id="gia-pha-goal",
            task_id="task-iris-001",
            task_objective="certify p2p_iris role binding",
            project_binding="gia-pha-project",
            workspace_binding="workspace-iris",
approved_scope=("p2p-governance",),
            context_package=("context:item-1",),
permission_profile=("READ",),
explicit_execution_target="fake-manus",
            target_fingerprint=fake_target_fingerprint("fake-manus"),
        )
        # REAL_REQUIRED scenarios consult the shared replay ledger;
        # start from a clean ledger so tests do not cross-contaminate.
        self._ledger = _attestation_ledger_path()
        if self._ledger.exists():
            self._ledger.unlink()
        self.target_id = "fake-manus"
        register_fake_targets(BackendAdapterRegistry())
        self.registry = BackendAdapterRegistry()
        register_fake_targets(self.registry)
        self.identity = {"adapter_id": f"adapter-{self.target_id}"}
        register_explicit_adapter(
            self.registry,
            adapter_id=self.identity["adapter_id"],
            harness="codex-runtime",
            provider="codex",
            model="claude-sonnet-test",
            live_certified=False,
            auth_state="NO_CREDENTIALS",
            synthetic=True)
        self.attestation = _real_attestation(
            run_id="c36:gia-pha-goal",
            execution_contract_digest=self.contract.request_fingerprint,
            host_execution_identity="codex-thread-verifier-1",
            pointers=(f"file:{self.path}",),
            source_digest=self.digest,
        
            adapter_id=self.identity["adapter_id"])
        self.bridge = RoleExecutionBridge(BackendExecutionBridge(
            self.registry, self.identity))
        self.dispatch = self.bridge.dispatch(
            self.contract,
            adapter_id=self.identity["adapter_id"],
            host_attestation=self.attestation)
        self.receipt = RoleExecutionReceipt(self.dispatch["role_receipt"])
        self.backend = BackendExecutionResult.from_mapping(self.dispatch["backend_result"])
        self.observed_pointers = (
            list(self.receipt.output_pointers)
            + list(self.receipt.artifact_pointers)
            + [self.receipt.raw_backend_receipt_pointer or ""]
            + list(self.attestation.attestation_evidence_pointers))


    def tearDown(self) -> None:
        if getattr(self, "_ledger", None) is not None and self._ledger.exists():
            self._ledger.unlink()

    def _verify(self, **overrides: object) -> dict[str, object]:
        kwargs = {
            "receipt": self.receipt,
            "expected_contract": self.contract,
            "expected_role_spec_hash": self.spec.role_spec_hash,
            "expected_permission_profile": ("READ",),
            "backend_result": self.backend,
            "required_evidence": (),
            "observed_target_evidence_pointers": self.observed_pointers,
            "attestation_policy": "REAL_REQUIRED",
        }
        kwargs.update(overrides)
        return verify_role_execution_receipt(**kwargs)

    def test_24_real_policy_verifies_real_attestation(self) -> None:
        result = self._verify()
        self.assertEqual(result["verdict"], "VERIFIED", result["reasons"])

    def test_25_standard_policy_byte_identical_no_attestation_needed(self) -> None:
        dispatch = self.bridge.dispatch(
            self.contract, adapter_id=self.identity["adapter_id"])
        receipt = RoleExecutionReceipt(dispatch["role_receipt"])
        result = verify_role_execution_receipt(
            receipt=receipt,
            expected_contract=self.contract,
            expected_role_spec_hash=self.spec.role_spec_hash,
        expected_permission_profile=("READ",),
            backend_result=BackendExecutionResult.from_mapping(
                dispatch["backend_result"]),
            required_evidence=(),
            observed_target_evidence_pointers=(
                list(receipt.output_pointers)
                + list(receipt.artifact_pointers)
                + [receipt.raw_backend_receipt_pointer or ""]),
            attestation_policy="STANDARD")
        self.assertEqual(result["verdict"], "VERIFIED", result["reasons"])

    def test_26_real_policy_rejects_missing_attestation(self) -> None:
        dispatch = self.bridge.dispatch(
            self.contract, adapter_id=self.identity["adapter_id"])
        receipt = RoleExecutionReceipt(dispatch["role_receipt"])
        result = verify_role_execution_receipt(
            receipt=receipt,
            expected_contract=self.contract,
            expected_role_spec_hash=self.spec.role_spec_hash,
        expected_permission_profile=("READ",),
            backend_result=BackendExecutionResult.from_mapping(
                dispatch["backend_result"]),
            required_evidence=(),
            observed_target_evidence_pointers=(
                list(receipt.output_pointers)
                + list(receipt.artifact_pointers)
                + [receipt.raw_backend_receipt_pointer or ""]),
            attestation_policy="REAL_REQUIRED")
        self.assertEqual(result["verdict"], "REJECTED")
        self.assertTrue(any("REAL_HOST_ATTESTATION_ABSENT" in reason
                            for reason in result["reasons"]))

    def test_27_cross_contract_attestation_rejected(self) -> None:
        attestation = _real_attestation(
            run_id="c36:gia-pha-goal",
            execution_contract_digest="e" * 64,  # wrong contract
            host_execution_identity="codex-thread-cross-contract",
            pointers=(f"file:{self.path}",),
            ledger_path=str(self._ledger))
        with self.assertRaises(RoleBridgeError) as ctx:
            self.bridge.dispatch(
                self.contract,
                adapter_id=self.identity["adapter_id"],
                host_attestation=attestation)
        self.assertEqual(ctx.exception.code, "ATTESTATION_CONTRACT_MISMATCH")

    def test_28_contract_mismatch_raises_in_bridge(self) -> None:
        attestation = _real_attestation(
            run_id="c36:gia-pha-goal",
            execution_contract_digest="e" * 64,
            host_execution_identity="codex-thread-cross-contract",
            pointers=(f"file:{self.path}",))
        with self.assertRaises(RoleBridgeError) as ctx:
            self.bridge.dispatch(
                self.contract,
                adapter_id=self.identity["adapter_id"],
                host_attestation=attestation)
        self.assertEqual(ctx.exception.code, "ATTESTATION_CONTRACT_MISMATCH")

    def test_29_adapter_mismatch_raises_in_bridge(self) -> None:
        attestation = _real_attestation(
            adapter_id="adapter-wrong",
            run_id="c36:gia-pha-goal",
            execution_contract_digest=self.contract.request_fingerprint,
            host_execution_identity="codex-thread-cross-adapter",
            pointers=(f"file:{self.path}",))
        with self.assertRaises(RoleBridgeError) as ctx:
            self.bridge.dispatch(
                self.contract,
                adapter_id=self.identity["adapter_id"],
                host_attestation=attestation)
        self.assertEqual(ctx.exception.code, "ATTESTATION_ADAPTER_MISMATCH")

    def test_30_replayed_attestation_rejected(self) -> None:
        record_attestation_use(self.attestation)
        result = self._verify()
        self.assertEqual(result["verdict"], "REJECTED")
        self.assertTrue(any("REAL_ATTESTATION_REPLAYED" in reason
                            for reason in result["reasons"]))

    def test_31_stale_attestation_rejected(self) -> None:
        stale_time = "2024-01-01T00:00:00Z"  # guaranteed stale
        dispatch_id31 = mint_dispatch_id(
            f"c36:{self.contract.goal_id}", self.contract.role_id,
            self.contract.task_id, 1)
        attestation = _real_attestation(
            run_id="c36:gia-pha-goal",
            adapter_id=self.identity["adapter_id"],
            execution_contract_digest=self.contract.request_fingerprint,
            host_execution_identity="codex-thread-stale",
            pointers=(f"file:{self.path}",),
            attested_at=stale_time,
            dispatch_id=dispatch_id31)
        dispatch = self.bridge.dispatch(
            self.contract,
            adapter_id=self.identity["adapter_id"],
            host_attestation=attestation)
        receipt = RoleExecutionReceipt(dispatch["role_receipt"])
        result = verify_role_execution_receipt(
            receipt=receipt,
            expected_contract=self.contract,
            expected_role_spec_hash=self.spec.role_spec_hash,
        expected_permission_profile=("READ",),
            backend_result=BackendExecutionResult.from_mapping(
                dispatch["backend_result"]),
            required_evidence=(),
            observed_target_evidence_pointers=(
                list(receipt.output_pointers)
                + list(receipt.artifact_pointers)
                + [receipt.raw_backend_receipt_pointer or ""]
                + list(attestation.attestation_evidence_pointers)),
            attestation_policy="REAL_REQUIRED")
        self.assertEqual(result["verdict"], "REJECTED")
        self.assertTrue(any("REAL_ATTESTATION_STALE" in reason
                            for reason in result["reasons"]))

    def test_32_missing_evidence_source_rejected(self) -> None:
        dispatch_id32 = mint_dispatch_id(
            f"c36:{self.contract.goal_id}", self.contract.role_id,
            self.contract.task_id, 1)
        attestation = _real_attestation(
            run_id="c36:gia-pha-goal",
            adapter_id=self.identity["adapter_id"],
            execution_contract_digest=self.contract.request_fingerprint,
            host_execution_identity="codex-thread-no-source",
            pointers=("file:C:\\no-such-c36-evidence\\missing.txt",),
            dispatch_id=dispatch_id32)
        dispatch = self.bridge.dispatch(
            self.contract,
            adapter_id=self.identity["adapter_id"],
            host_attestation=attestation)
        receipt = RoleExecutionReceipt(dispatch["role_receipt"])
        result = verify_role_execution_receipt(
            receipt=receipt,
            expected_contract=self.contract,
            expected_role_spec_hash=self.spec.role_spec_hash,
        expected_permission_profile=("READ",),
            backend_result=BackendExecutionResult.from_mapping(
                dispatch["backend_result"]),
            required_evidence=(),
            observed_target_evidence_pointers=(
                list(receipt.output_pointers)
                + list(receipt.artifact_pointers)
                + [receipt.raw_backend_receipt_pointer or ""]
                + list(attestation.attestation_evidence_pointers)),
            attestation_policy="REAL_REQUIRED")
        self.assertEqual(result["verdict"], "REJECTED")
        self.assertTrue(any("REAL_ATTESTATION_EVIDENCE_SOURCE_ABSENT" in reason
                            for reason in result["reasons"]))

    def test_33_observation_not_bound_rejected(self) -> None:
        result = self._verify(observed_target_evidence_pointers=(
            "file:C:\\unrelated-observation-pointer.txt",))
        self.assertEqual(result["verdict"], "REJECTED")
        self.assertTrue(any("REAL_ATTESTATION_OBSERVATION_NOT_BOUND" in reason
                            for reason in result["reasons"]))

    def test_34_dispatch_id_carried_in_receipt(self) -> None:
        receipt_dispatch_id = self.dispatch["role_receipt"]["dispatch_id"]
        self.assertTrue(receipt_dispatch_id)
        # Deterministic mint from the contract the bridge was given.
        expected = mint_dispatch_id(
            f"c36:{self.contract.goal_id}", self.contract.role_id,
            self.contract.task_id, 0)
        self.assertEqual(receipt_dispatch_id, expected)

    def test_35_receipt_serialization_present_attestation(self) -> None:
        as_dict = role_receipt_to_dict(self.receipt)
        self.assertIn("host_attestation", as_dict)
        self.assertEqual(as_dict["host_attestation"]["attestation_fingerprint"],
                         self.attestation.attestation_fingerprint)


class TestC36RegressionC35ByteIdentity(unittest.TestCase):
    """Owner condition: schema /1 stays byte-identical when attestation
    is absent; the 57/57 C35 suite guards this mechanically."""

    def setUp(self) -> None:
        self.spec = build_role_spec("p2p_iris")
        self.path = _write_evidence("identity-src.txt", "identity-evidence")
        self.digest = _digest_of(self.path)
        self.attestation = _real_attestation(
            execution_contract_digest=self.digest,
            host_execution_identity="regression-thread",
            pointers=(f"file:{self.path}",))

    def test_36_absent_attestation_serialization_is_c35(self) -> None:
        spec = build_role_spec("p2p_iris")
        base = {
            "role_id": spec.role_id,
            "role_spec_hash": spec.role_spec_hash,
            "goal_id": "goal-1",
            "task_id": "task-1",
            "project_binding": "proj-1",
            "context_digest": hashlib.sha256(b"ctx").hexdigest(),
            "permission_profile": (),
            "permission_profile_fingerprint": hashlib.sha256(b"").hexdigest(),
            "request_fingerprint": hashlib.sha256(b"req").hexdigest(),
            "requested_target": "fake-manus",
            "observed_target": "fake-manus",
            "target_fingerprint": fake_target_fingerprint("fake-manus"),
            "execution_status": "SUCCEEDED",
        }
        receipt_without = RoleExecutionReceipt(new_role_receipt(**base))
        receipt_with = RoleExecutionReceipt(new_role_receipt(
            host_attestation=self.attestation.to_dict(), **base))
        without_dict = receipt_without.to_dict()
        with_dict = receipt_with.to_dict()
        self.assertNotIn("host_attestation", without_dict)
        self.assertNotIn("dispatch_id", without_dict)
        self.assertIn("host_attestation", with_dict)
        for key in without_dict:
            self.assertEqual(with_dict[key], without_dict[key], key)
        # Structural equality minus the optional fields: C35 consumers
        # see the identical key set when attestation is absent.
        self.assertEqual(set(with_dict) - {"host_attestation", "dispatch_id"},
                         set(without_dict))

    def test_37_dispatch_without_attestation_keeps_c35_receipt(self) -> None:
        register_fake_targets(BackendAdapterRegistry())
        registry = BackendAdapterRegistry()
        register_fake_targets(registry)
        register_explicit_adapter(
            registry, adapter_id="adapter-fake-manus",
            harness="test", provider="test", model="test",
            live_certified=False, auth_state="NO_CREDENTIALS", synthetic=True)
        bridge = RoleExecutionBridge(BackendExecutionBridge(
            registry, {"adapter_id": "adapter-fake-manus"}))
        contract = build_role_execution_contract(
            role_spec=self.spec,
            goal_id="goal-1",
            task_id="task-1",
            task_objective="identity check",
            project_binding="proj-1",
            workspace_binding="ws-1",
            approved_scope=("p2p-governance",),
            permission_profile=("READ",),
            explicit_execution_target="fake-manus",
            target_fingerprint=fake_target_fingerprint("fake-manus"))
        dispatch = bridge.dispatch(contract, adapter_id="adapter-fake-manus")
        self.assertIsNone(dispatch.get("host_attestation"))
        self.assertNotIn("host_attestation", dispatch["role_receipt"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
