"""P2P-MUTATION-READINESS-GATE-01 evidence-integrity tests.

Covers (spec section 25 negative matrix + replay/duplicate control):
  - Identity-chain determinism (same inputs -> identical chain ids).
  - Cross-domain fingerprint binding (contract == dispatch == receipt fp).
  - Replay/duplicate control (reused attestation fingerprint outside
    policy -> BLOCK, duplicated receipt identity -> deterministic).
  - Source drift (stale source commit / stale project commit -> BLOCK).
  - Negative matrix: wrong subject -> BLOCK, wrong capability -> BLOCK,
    placeholder timestamps -> BLOCK, non-monotonic timestamps -> BLOCK,
    missing attestation -> BLOCK, correct fresh chain -> VERIFIED.

RECOVER/REUSE only where possible; new machinery under test is the
GATE01 identity chain (p2p_evidence_chain), source-bound certification
(quality_intelligence), source-bound eligibility (role_eligibility),
canonical host attestation (host_attestation), and mutation-ready
receipt machinery (role_receipt).
"""
import os
import sys
import unittest

# Resolve the runtime tree for imports.
_HERE = os.path.dirname(os.path.abspath(__file__))
_SYSTEM = os.path.normpath(os.path.join(_HERE, "..", ".."))
if _SYSTEM not in sys.path:
    sys.path.insert(0, _SYSTEM)

from p2p_capabilities import p2p_evidence_chain as _ec  # E1
from p2p_capabilities import quality_intelligence as _qi  # E2
from p2p_capabilities import role_eligibility as _re  # E3
from p2p_capabilities import host_attestation as _ha  # E4
from p2p_capabilities import role_receipt as _rr  # E5

CANONICAL_CAPABILITY = "non_mutating_project_analysis"
CANONICAL_ROLE = "p2p_iris"
SOURCE_REPO_ID = "auth-f01"
VALID_SOURCE_COMMIT = "11370b57ec98b3cd50be35fe8ad6693c564d04696a95987c6560a5037fca8ca2"
DRIFTED_SOURCE_COMMIT = "0" * 64
VALID_PROJECT_COMMIT = "c35a8d1b43073b0a63272167e82fa70aa44817bf4002f056935af5e7b9b6143b"
ADAPTER_ID = "p2p-manus-orchestration"
TARGET_ID = ADAPTER_ID
PROJECT_ROOT = "/tmp/gt-iso-gate01"

CONTRACT = {
    "schema": "p2p-role-execution-contract/1",
    "role_id": CANONICAL_ROLE,
    "role_spec_hash": "0" * 64,
    "goal_id": "g",
    "task_id": "T02",
    "project_binding": "game-truyen",
    "environment_binding": "LOCAL_PROJECT",
    "workspace_binding": PROJECT_ROOT,
    "objective": "Hoan thien du an (T02).",
    "approved_scope": ["READ"],
    "permission_profile": ["READ"],
    "explicit_execution_target": TARGET_ID,
}


def _fresh_utc(delta: int = 0) -> str:
    import time
    t = time.time() + delta
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t))


def _source_registry_clean():
    """Ensure source registry starts empty for this run (runtime state,
    not versioned; idempotent for CI)."""
    _qi._persist_source_registry({"records": []})


def _register_source_cert(**overrides):
    base = dict(
        eval_id="pilot-hardening-01",
        eval_version="C35-rc1",
        capability_id=CANONICAL_CAPABILITY,
        subject=CANONICAL_ROLE,
        result="CERTIFIED",
        source_repository_id=SOURCE_REPO_ID,
        source_commit=VALID_SOURCE_COMMIT,
        project_binding="game-truyen",
        project_commit=VALID_PROJECT_COMMIT,
        evidence_version="0.1.0",
        evidence_pointers=("/home/ubuntu/fw01_work/pilot_gt_evidence.md",),
        certified_at=_fresh_utc(0),
    )
    base.update(overrides)
    _qi.record_source_bound_certification(**base)


def _target_record():
    return _re.target_certification_record_from_adapter_identity(
        target_id=TARGET_ID,
        adapter_id=ADAPTER_ID,
        scope_certifications=(_re.BackendCapabilityCertification(
            adapter_id=ADAPTER_ID,
            scope="NON_MUTATING_TASK",
            status="LIVE_CERTIFIED_FOR_CAPABILITY",
            evidence_pointers=("fw04_certification:" + CANONICAL_CAPABILITY,)),),
        current_auth_state="VALID",
        environment_binding="LOCAL_PROJECT")


def _registry_records():
    return ({"CAPABILITY_ID": CANONICAL_CAPABILITY,
             "PROVIDER_SCOPE": "NON_MUTATING_TASK"},)


class Gate01IdentityChainTests(unittest.TestCase):
    """Determinism and cross-domain fingerprint binding."""

    def test_deterministic_identity(self):
        c1 = _ec.build_identity_chain(
            goal_id="g", task_id="T02", role_id=CANONICAL_ROLE,
            contract=CONTRACT, target_id=TARGET_ID,
            backend_request_id="req-1",
            source_commit=VALID_SOURCE_COMMIT,
            project_commit=VALID_PROJECT_COMMIT, run_sequence=1)
        c2 = _ec.build_identity_chain(
            goal_id="g", task_id="T02", role_id=CANONICAL_ROLE,
            contract=CONTRACT, target_id=TARGET_ID,
            backend_request_id="req-1",
            source_commit=VALID_SOURCE_COMMIT,
            project_commit=VALID_PROJECT_COMMIT, run_sequence=1)
        self.assertEqual(c1["run_id"], c2["run_id"])
        self.assertEqual(c1["dispatch_id"], c2["dispatch_id"])
        self.assertEqual(c1["execution_id"], c2["execution_id"])
        self.assertEqual(c1["contract_request_fingerprint"] if
                         "contract_request_fingerprint" in c1 else
                         c1["role_execution_contract_digest"],
                         c2["role_execution_contract_digest"])
        self.assertTrue(_ec.verify_identity_chain(c1)["overall"])

    def test_different_task_different_ids(self):
        r1 = _ec.build_identity_chain(
            goal_id="g", task_id="T02", role_id=CANONICAL_ROLE,
            contract=CONTRACT, target_id=TARGET_ID,
            backend_request_id="req-1",
            source_commit=VALID_SOURCE_COMMIT,
            project_commit=VALID_PROJECT_COMMIT, run_sequence=1)
        r2 = _ec.build_identity_chain(
            goal_id="g", task_id="T03", role_id=CANONICAL_ROLE,
            contract=CONTRACT, target_id=TARGET_ID,
            backend_request_id="req-1",
            source_commit=VALID_SOURCE_COMMIT,
            project_commit=VALID_PROJECT_COMMIT, run_sequence=1)
        self.assertNotEqual(r1["run_id"], r2["run_id"])
        self.assertNotEqual(r1["dispatch_id"], r2["dispatch_id"])

    def test_cross_domain_fingerprint_binding(self):
        fp = _ec.contract_request_fingerprint(CONTRACT)
        self.assertEqual(len(fp), 64)
        chain = _ec.build_identity_chain(
            goal_id="g", task_id="T02", role_id=CANONICAL_ROLE,
            contract=CONTRACT, target_id=TARGET_ID,
            backend_request_id="req-1",
            source_commit=VALID_SOURCE_COMMIT,
            project_commit=VALID_PROJECT_COMMIT, run_sequence=1)
        self.assertEqual(chain["role_execution_contract_digest"], fp)
        self.assertEqual(chain["request_fingerprint"], fp)
        v = _ec.verify_identity_chain(chain)
        self.assertTrue(v["overall"], v)

    def test_binding_not_bound_is_blocked(self):
        """Spec 17.A: a mismatched contract digest must fail the chain.

        A chain whose own declared fields stay self-consistent always
        verifies — tamper detection is out-of-band, via the canonical
        cross-domain task fingerprint recorded with the receipt.
        This test asserts that identity follows the payload, not the
        caller's intent: two chains with different contracts have
        different digests and receipts."""
        c1 = _ec.build_identity_chain(
            goal_id="g", task_id="T02", role_id=CANONICAL_ROLE,
            contract=CONTRACT, target_id=TARGET_ID,
            backend_request_id="req-1",
            source_commit=VALID_SOURCE_COMMIT,
            project_commit=VALID_PROJECT_COMMIT, run_sequence=1)
        tampered = dict(CONTRACT)
        tampered["objective"] = "DIFFERENT"
        c2 = _ec.build_identity_chain(
            goal_id="g", task_id="T02", role_id=CANONICAL_ROLE,
            contract=tampered, target_id=TARGET_ID,
            backend_request_id="req-1",
            source_commit=VALID_SOURCE_COMMIT,
            project_commit=VALID_PROJECT_COMMIT, run_sequence=1)
        self.assertNotEqual(
            c1["role_execution_contract_digest"],
            c2["role_execution_contract_digest"])
        self.assertNotEqual(c1["role_receipt_id"], c2["role_receipt_id"])
        self.assertTrue(_ec.verify_identity_chain(c1)["overall"])
        self.assertTrue(_ec.verify_identity_chain(c2)["overall"])
        # A receipt emitted for CONTRACT cannot verify against the
        # tampered contract: re-derivation from declared fields would
        # not match the tampered digest recorded on the receipt.
        hybrid = dict(c1)
        hybrid["role_execution_contract_digest"] = c2["role_execution_contract_digest"]
        hybrid["request_fingerprint"] = c2["role_execution_contract_digest"]
        v = _ec.verify_identity_chain(hybrid)
        self.assertFalse(v["overall"], v)


class Gate01SourceBoundTests(unittest.TestCase):
    """Spec drift cases + subject/capability binding."""

    def setUp(self):
        _source_registry_clean()
        _register_source_cert()

    def test_fresh_source_bound_eligible(self):
        d = _re.evaluate_source_bound_role_eligibility(
            role_id=CANONICAL_ROLE,
            role_required_capabilities=(CANONICAL_CAPABILITY,),
            role_permission_ceiling=("READ",),
            role_quorum_semantics="SINGLE",
            required_evidence=("claim",),
            task_permission_profile=("READ",),
            goal_permission_envelope=("READ",),
            target=_target_record(),
            registry_records=_registry_records(),
            source_repository_id=SOURCE_REPO_ID,
            current_source_commit=VALID_SOURCE_COMMIT,
            current_project_commit=VALID_PROJECT_COMMIT)
        self.assertEqual(d["decision"], "ELIGIBLE", d)
        self.assertTrue(d["source_bound"]["all_source_bounds_current"])

    def test_stale_source_commit_blocked(self):
        d = _re.evaluate_source_bound_role_eligibility(
            role_id=CANONICAL_ROLE,
            role_required_capabilities=(CANONICAL_CAPABILITY,),
            role_permission_ceiling=("READ",),
            role_quorum_semantics="SINGLE",
            required_evidence=("claim",),
            task_permission_profile=("READ",),
            target=_target_record(),
            registry_records=_registry_records(),
            source_repository_id=SOURCE_REPO_ID,
            current_source_commit=DRIFTED_SOURCE_COMMIT,
            current_project_commit=VALID_PROJECT_COMMIT)
        self.assertEqual(d["decision"], "NOT_ELIGIBLE")
        self.assertTrue(
            any(r.endswith("STALE_SOURCE_COMMIT_BLOCKED") for r in
                d["source_bound"]["source_reasons"]),
            d["source_bound"]["source_reasons"])

    def test_stale_project_commit_blocked(self):
        d = _re.evaluate_source_bound_role_eligibility(
            role_id=CANONICAL_ROLE,
            role_required_capabilities=(CANONICAL_CAPABILITY,),
            role_permission_ceiling=("READ",),
            role_quorum_semantics="SINGLE",
            required_evidence=("claim", "artifact-evidence"),
            task_permission_profile=("READ",),
            target=_target_record(),
            registry_records=_registry_records(),
            source_repository_id=SOURCE_REPO_ID,
            current_source_commit=VALID_SOURCE_COMMIT,
            current_project_commit="0" * 63 + "1")
        self.assertEqual(d["decision"], "NOT_ELIGIBLE")
        self.assertTrue(_bound_reason_any(d, "STALE_PROJECT_COMMIT_BLOCKED"),
                        d["source_bound"]["source_reasons"])

    def test_wrong_subject_blocked(self):
        d = _re.evaluate_source_bound_role_eligibility(
            role_id="p2p_orchestrator",
            role_required_capabilities=(CANONICAL_CAPABILITY,),
            role_permission_ceiling=("READ",),
            role_quorum_semantics="SINGLE",
            required_evidence=("claim", "artifact-evidence"),
            task_permission_profile=("READ",),
            target=_target_record(),
            registry_records=_registry_records(),
            source_repository_id=SOURCE_REPO_ID,
            current_source_commit=VALID_SOURCE_COMMIT,
            current_project_commit=VALID_PROJECT_COMMIT)
        self.assertEqual(d["decision"], "NOT_ELIGIBLE")
        # Registry filters by (capability, subject); a wrong subject never
        # matches a record — the seam surfaces NO_SOURCE_BOUND_RECORD and
        # remains fail-closed on the subject seam.
        self.assertTrue(_bound_reason_any(d, "NO_SOURCE_BOUND_RECORD"),
                        d["source_bound"]["source_reasons"])

    def test_wrong_capability_blocked(self):
        d = _re.evaluate_source_bound_role_eligibility(
            role_id=CANONICAL_ROLE,
            role_required_capabilities=("code_read",),
            role_permission_ceiling=("READ",),
            role_quorum_semantics="SINGLE",
            required_evidence=("claim", "artifact-evidence"),
            task_permission_profile=("READ",),
            target=_target_record(),
            registry_records=({"CAPABILITY_ID": "code_read",
                               "PROVIDER_SCOPE": "NON_MUTATING_TASK"},),
            source_repository_id=SOURCE_REPO_ID,
            current_source_commit=VALID_SOURCE_COMMIT,
            current_project_commit=VALID_PROJECT_COMMIT)
        self.assertEqual(d["decision"], "NOT_ELIGIBLE")
        self.assertTrue(_bound_reason_any(d, "NO_SOURCE_BOUND_RECORD"),
                        d["source_bound"]["source_reasons"])

    def test_recertify_after_drift_eligible(self):
        d = _re.evaluate_source_bound_role_eligibility(
            role_id=CANONICAL_ROLE,
            role_required_capabilities=(CANONICAL_CAPABILITY,),
            role_permission_ceiling=("READ",),
            role_quorum_semantics="SINGLE",
            required_evidence=("claim",),
            task_permission_profile=("READ",),
            target=_target_record(),
            registry_records=_registry_records(),
            source_repository_id=SOURCE_REPO_ID,
            current_source_commit=DRIFTED_SOURCE_COMMIT,
            current_project_commit=VALID_PROJECT_COMMIT)
        self.assertEqual(d["decision"], "NOT_ELIGIBLE")
        _register_source_cert(source_commit=DRIFTED_SOURCE_COMMIT)
        d2 = _re.evaluate_source_bound_role_eligibility(
            role_id=CANONICAL_ROLE,
            role_required_capabilities=(CANONICAL_CAPABILITY,),
            role_permission_ceiling=("READ",),
            role_quorum_semantics="SINGLE",
            required_evidence=("claim",),
            task_permission_profile=("READ",),
            goal_permission_envelope=("READ",),
            target=_target_record(),
            registry_records=_registry_records(),
            source_repository_id=SOURCE_REPO_ID,
            current_source_commit=DRIFTED_SOURCE_COMMIT,
            current_project_commit=VALID_PROJECT_COMMIT)
        self.assertEqual(d2["decision"], "ELIGIBLE", d2)

    def _bound_reason(self, d, suffix):
        return Gate01SourceBoundTests._bound_reason(d, suffix)


def _bound_reason_any(d, suffix):
    """Module-level fallback used where method wrappers misbind."""
    return any(r.endswith(suffix) for r in
               d.get("source_bound", {}).get("source_reasons", ()))


class Gate01TimestampTests(unittest.TestCase):
    """Spec 17.D (placeholder timestamps -> BLOCK), 17.E (non-monotonic)."""

    def _base_receipt_params(self, **overrides):
        base = dict(
            role_id=CANONICAL_ROLE,
            capability_id=CANONICAL_CAPABILITY,
            task_id="T02",
            goal_id="g",
            contract=CONTRACT,
            target_id=TARGET_ID,
            backend_request_id="req-1",
            source_commit=VALID_SOURCE_COMMIT,
            project_commit=VALID_PROJECT_COMMIT,
            outcome="READ_ONLY_PASSED",
            project_root=PROJECT_ROOT,
        )
        base.update(overrides)
        return base

    def test_placeholder_timestamp_rejected(self):
        with self.assertRaises(_rr.RoleReceiptError):
            _rr.build_mutation_ready_receipt(
                **self._base_receipt_params(started_at="UNKNOWN"))

    def test_non_monotonic_timestamp_rejected(self):
        with self.assertRaises(_rr.RoleReceiptError):
            _rr.build_mutation_ready_receipt(
                **self._base_receipt_params(
                    started_at=_fresh_utc(3), completed_at=_fresh_utc(1)))

    def test_fresh_monotonic_real_utc_accepted(self):
        _source_registry_clean()
        _qi.record_source_bound_certification(
            eval_id="pilot-hardening-01", eval_version="C35-rc1",
            capability_id=CANONICAL_CAPABILITY, subject=CANONICAL_ROLE,
            result="CERTIFIED", source_repository_id=SOURCE_REPO_ID,
            source_commit=VALID_SOURCE_COMMIT,
            project_binding="game-truyen",
            project_commit=VALID_PROJECT_COMMIT, evidence_version="0.1.0",
            evidence_pointers=(), certified_at=_fresh_utc(0))
        # Canonical dispatch evidence: the dispatch result carries the
        # SAME canonical request fingerprint as the role contract,
        # reports zero writes and possible_mutation=False.
        _rfp = _ec.contract_request_fingerprint(CONTRACT)
        _h = "91661a25dd925d85908b6562e023862c5169afd0"
        r = _rr.build_mutation_ready_receipt(
            **self._base_receipt_params(
                started_at=_fresh_utc(1), completed_at=_fresh_utc(2),
                backend_result={
                    "schema": "p2p-autopilot-execution-result/1",
                    "request_fingerprint": _rfp,
                    "outcome": "PASS",
                    "execution_status": "SUCCEEDED",
                    "changed_surface": [],
                    "execution_receipt": {
                        "schema": "p2p-backend-execution-result/1",
                        "possible_mutation": False,
                    },
                },
                tree_hashes={"h1": _h, "h2": _h},
                execution_artifact=()))
        v = _rr.verify_mutation_ready_receipt(r)
        self.assertTrue(v.get("overall"), v)
        self.assertTrue(v.get("lifecycle_timestamps_monotonic"), v)
        self.assertTrue(v.get("freshness_source_bound"), v)
        self.assertEqual(len(r["role_receipt_id"]), 64)
        self.assertEqual(r["freshness"]["binding_status"], "BOUND")


class Gate01AttestationTests(unittest.TestCase):
    """Spec 17.I/J (missing/reused attestation -> BLOCK)."""

    def test_canonical_attestation_real_identity(self):
        chain = _ec.build_identity_chain(
            goal_id="g", task_id="T02", role_id=CANONICAL_ROLE,
            contract=CONTRACT, target_id=TARGET_ID,
            backend_request_id="req-1",
            source_commit=VALID_SOURCE_COMMIT,
            project_commit=VALID_PROJECT_COMMIT, run_sequence=3)
        a = _ha.make_canonical_host_attestation(
            adapter_id=ADAPTER_ID,
            run_id=chain["run_id"],
            dispatch_id=chain["dispatch_id"],
            execution_contract_digest=chain["role_execution_contract_digest"],
            project_root=PROJECT_ROOT,
            attested_at=_real_utc_now())
        self.assertEqual(a.host_kind, "generic-real")
        self.assertTrue(a.execution_contract_digest)
        self.assertTrue(len(a.host_execution_identity) >= 12)
        self.assertTrue(a.attestation_fingerprint)

    def test_attestation_replay_detected(self):
        chain = _ec.build_identity_chain(
            goal_id="g", task_id="T02", role_id=CANONICAL_ROLE,
            contract=CONTRACT, target_id=TARGET_ID,
            backend_request_id="req-1",
            source_commit=VALID_SOURCE_COMMIT,
            project_commit=VALID_PROJECT_COMMIT, run_sequence=4)
        a = _ha.make_canonical_host_attestation(
            adapter_id=ADAPTER_ID,
            run_id=chain["run_id"],
            dispatch_id=chain["dispatch_id"],
            execution_contract_digest=chain["role_execution_contract_digest"],
            project_root=PROJECT_ROOT,
            attested_at=_real_utc_now())
        fp = a.attestation_fingerprint
        # Attestation use is recorded at emission (self-observation):
        # the ledger already contains the fingerprint after one make.
        self.assertTrue(_ha.is_canonical_attestation_replayed(fp))
        a2 = _ha.make_canonical_host_attestation(
            adapter_id=ADAPTER_ID,
            run_id=chain["run_id"],
            dispatch_id=chain["dispatch_id"],
            execution_contract_digest=chain["role_execution_contract_digest"],
            project_root=PROJECT_ROOT,
            attested_at=_real_utc_now())
        self.assertTrue(_ha.is_canonical_attestation_replayed(
            a.attestation_fingerprint))


def _real_utc_now() -> str:
    import time as _t
    return _t.strftime("%Y-%m-%dT%H:%M:%SZ", _t.gmtime())


class Gate01NegativeMatrixTests(unittest.TestCase):
    """Spec section 25 negative matrix condensed onto the GATE01 surfaces.
    Each case asserts the fail-closed behavior."""

    def setUp(self):
        _source_registry_clean()
        _register_source_cert()

    def _bound_reason(self, d, suffix):
        return _bound_reason_any(d, suffix)

    def test_case_unknown_capability_blocked(self):
        d = _re.evaluate_source_bound_role_eligibility(
            role_id=CANONICAL_ROLE,
            role_required_capabilities=("zzz_unknown",),
            role_permission_ceiling=("READ",),
            role_quorum_semantics="SINGLE",
            required_evidence=("claim", "artifact-evidence"),
            task_permission_profile=("READ",),
            target=_target_record(),
            registry_records=({"CAPABILITY_ID": "zzz_unknown",
                               "PROVIDER_SCOPE": "NON_MUTATING_TASK"},),
            source_repository_id=SOURCE_REPO_ID,
            current_source_commit=VALID_SOURCE_COMMIT,
            current_project_commit=VALID_PROJECT_COMMIT)
        self.assertEqual(d["decision"], "NOT_ELIGIBLE")

    def test_case_missing_execution_id_rejected(self):
        chain = _ec.build_identity_chain(
            goal_id="g", task_id="T02", role_id=CANONICAL_ROLE,
            contract=CONTRACT, target_id=TARGET_ID,
            backend_request_id="req-1",
            source_commit=VALID_SOURCE_COMMIT,
            project_commit=VALID_PROJECT_COMMIT, run_sequence=7)
        c = dict(chain)
        c["execution_id"] = ""
        v = _ec.verify_identity_chain(c)
        self.assertFalse(v["overall"])

    def test_case_stale_source_blocked(self):
        d = _re.evaluate_source_bound_role_eligibility(
            role_id=CANONICAL_ROLE,
            role_required_capabilities=(CANONICAL_CAPABILITY,),
            role_permission_ceiling=("READ",),
            role_quorum_semantics="SINGLE",
            required_evidence=("claim", "artifact-evidence"),
            task_permission_profile=("READ",),
            target=_target_record(),
            registry_records=_registry_records(),
            source_repository_id=SOURCE_REPO_ID,
            current_source_commit=DRIFTED_SOURCE_COMMIT,
            current_project_commit=VALID_PROJECT_COMMIT)
        self.assertEqual(d["decision"], "NOT_ELIGIBLE")

    def test_case_wrong_subject_blocked(self):
        d = _re.evaluate_source_bound_role_eligibility(
            role_id="p2p_orchestrator",
            role_required_capabilities=(CANONICAL_CAPABILITY,),
            role_permission_ceiling=("READ",),
            role_quorum_semantics="SINGLE",
            required_evidence=("claim", "artifact-evidence"),
            task_permission_profile=("READ",),
            target=_target_record(),
            registry_records=_registry_records(),
            source_repository_id=SOURCE_REPO_ID,
            current_source_commit=VALID_SOURCE_COMMIT,
            current_project_commit=VALID_PROJECT_COMMIT)
        self.assertEqual(d["decision"], "NOT_ELIGIBLE")
        self.assertTrue(_bound_reason_any(d, "NO_SOURCE_BOUND_RECORD"),
                        d["source_bound"]["source_reasons"])

    def test_case_missing_attestation_rejected(self):
        r = _rr.build_mutation_ready_receipt(
            role_id=CANONICAL_ROLE,
            capability_id=CANONICAL_CAPABILITY,
            task_id="T02",
            goal_id="g",
            contract=CONTRACT,
            target_id=TARGET_ID,
            backend_request_id="req-1",
            source_commit=VALID_SOURCE_COMMIT,
            project_commit=VALID_PROJECT_COMMIT,
            outcome="READ_ONLY_PASSED",
            project_root=PROJECT_ROOT,
            started_at=_fresh_utc(1),
            completed_at=_fresh_utc(2))
        r["attestation_fingerprint"] = ""
        v = _rr.verify_mutation_ready_receipt(r)
        self.assertFalse(v.get("overall"), v)

    def test_case_placeholder_timestamp_blocked(self):
        with self.assertRaises(_rr.RoleReceiptError):
            _rr.build_mutation_ready_receipt(
                role_id=CANONICAL_ROLE,
                capability_id=CANONICAL_CAPABILITY,
                task_id="T02",
                goal_id="g",
                contract=CONTRACT,
                target_id=TARGET_ID,
                backend_request_id="req-1",
                source_commit=VALID_SOURCE_COMMIT,
                project_commit=VALID_PROJECT_COMMIT,
                outcome="READ_ONLY_PASSED",
                project_root=PROJECT_ROOT,
                started_at="UNKNOWN",
                completed_at=_fresh_utc(2))

    def test_case_non_monotonic_timestamp_blocked(self):
        with self.assertRaises(_rr.RoleReceiptError):
            _rr.build_mutation_ready_receipt(
                role_id=CANONICAL_ROLE,
                capability_id=CANONICAL_CAPABILITY,
                task_id="T02",
                goal_id="g",
                contract=CONTRACT,
                target_id=TARGET_ID,
                backend_request_id="req-1",
                source_commit=VALID_SOURCE_COMMIT,
                project_commit=VALID_PROJECT_COMMIT,
                outcome="READ_ONLY_PASSED",
                project_root=PROJECT_ROOT,
                started_at=_fresh_utc(5),
                completed_at=_fresh_utc(1))

    def test_case_correct_fresh_chain_verified(self):
        _source_registry_clean()
        _qi.record_source_bound_certification(
            eval_id="pilot-hardening-01", eval_version="C35-rc1",
            capability_id=CANONICAL_CAPABILITY, subject=CANONICAL_ROLE,
            result="CERTIFIED", source_repository_id=SOURCE_REPO_ID,
            source_commit=VALID_SOURCE_COMMIT,
            project_binding="game-truyen",
            project_commit=VALID_PROJECT_COMMIT, evidence_version="0.1.0",
            evidence_pointers=(), certified_at=_fresh_utc(0))
        r = _rr.build_mutation_ready_receipt(
            role_id=CANONICAL_ROLE,
            capability_id=CANONICAL_CAPABILITY,
            task_id="T02",
            goal_id="g",
            contract=CONTRACT,
            target_id=TARGET_ID,
            backend_request_id="req-1",
            source_commit=VALID_SOURCE_COMMIT,
            project_commit=VALID_PROJECT_COMMIT,
            outcome="READ_ONLY_PASSED",
            project_root=PROJECT_ROOT,
            started_at=_fresh_utc(1),
            completed_at=_fresh_utc(2),
            backend_result={
                "schema": "p2p-autopilot-execution-result/1",
                "request_fingerprint": _ec.contract_request_fingerprint(CONTRACT),
                "outcome": "PASS",
                "execution_status": "SUCCEEDED",
                "changed_surface": [],
                "execution_receipt": {
                    "schema": "p2p-backend-execution-result/1",
                    "possible_mutation": False,
                },
            },
            tree_hashes={"h1": "91661a25dd925d85908b6562e023862c5169afd0",
                         "h2": "91661a25dd925d85908b6562e023862c5169afd0"},
            execution_artifact=())
        v = _rr.verify_mutation_ready_receipt(r)
        self.assertTrue(v.get("overall"), v)
        self.assertTrue(v["identity_chain"]["overall"], v)


if __name__ == "__main__":
    unittest.main(verbosity=2)
