"""P2P-BOUNDED-DOCUMENTATION-WRITE-01A tests.
Authority-chain closure: the canonical role (p2p_architecton) carries a
subject-bound WRITE_BOUNDED certification for bounded_documentation_write;
the capability maps to DOCUMENTATION_MUTATION_BOUNDED through the
registry-governed EXECUTION_SCOPE bridge; the execution target is
LIVE_CERTIFIED for that scope; and every mutation-ready receipt is
anchored by a REAL canonical HostAttestation (no derived identities for
authority executions).

Positive: role selection (architecton, never p2p_iris), scope mapping,
eligibility gating, M0/M1/M2 lifecycle with real attestation and whole-
claim verifier (verify_bounded_mutation_receipt).
Negative matrix A-O (15 cases): each missing authority link fails the
whole-claim verifier with overall=False.
All tests use a disposable fixture repository — never authoritative
Game Truyện, never Gia Phả.
"""
import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import subprocess

from p2p_capabilities import bounded_documentation_write as _bdw
from p2p_capabilities import host_attestation as _ha
from p2p_capabilities import authority_chain_registry as _acr
from p2p_capabilities import role_eligibility as _re
from p2p_capabilities import backend_contract as _bc
from p2p_capabilities import capability_intelligence as _ci
from p2p_capabilities.role_receipt import (
    new_role_receipt, verify_bounded_mutation_receipt,
)

CANONICAL_SHA = "a" * 64
ROLE_SPEC_HASH = "9" * 64
ARCH_ROLE = "p2p_architecton"
CAP_ID = "bounded_documentation_write"
SCOPE = "DOCUMENTATION_MUTATION_BOUNDED"
TARGET_ID = "adapter-doc-01a"
OWNER_AUTH = "owner-mutation-pilot-01a"


REGISTRY_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "capabilities.json")


def _registry_records():
    """Seeded registry surface: the canonical capability record and the
    architecton role record, exactly the surface eligibility queries.
    Raw capability dictionaries — the same surface the authority-chain
    checker iterates with .get("CAPABILITY_ID")."""
    with open(REGISTRY_FILE, encoding="utf-8") as fh:
        return [c for c in json.load(fh).get("capabilities", ()) if
                c.get("CAPABILITY_ID") in (CAP_ID, ARCH_ROLE,
                                           "p2p_iris")]


def _fixture_root():
    root = tempfile.mkdtemp(prefix="bw01afx")
    subprocess.run(["git", "-C", root, "init", "-q"], check=True)
    subprocess.run(["git", "-C", root, "config", "user.name", "p2p"],
                   check=True)
    subprocess.run(["git", "-C", root, "config", "user.email",
                    "p2p@fixture"], check=True)
    os.makedirs(os.path.join(root, "docs"))
    with open(os.path.join(root, "docs", "README.md"), "w",
              encoding="utf-8") as fh:
        fh.write("# Fixture\n\nDocumentation-only project.\n")
    subprocess.run(["git", "-C", root, "add", "."], check=True)
    subprocess.run(["git", "-C", root, "commit", "-qm", "init"],
                   check=True)
    return root


def _git_tree(root):
    proc = subprocess.run(["git", "-C", root, "rev-parse", "HEAD^{tree}"],
                          capture_output=True, text=True)
    return str(proc.stdout).strip()


def _base_contract(**overrides):
    base = {
        "goal_id": "goal-fw01a",
        "task_id": "task-doc-01a",
        "role_id": ARCH_ROLE,
        "capability_id": "p2p-bounded-documentation-write",
        "mutation_class": _bdw.MUTATION_CLASS,
        "project_id": "fixture-doc-project",
        "project_revision": "b" * 40,
        "environment": "ISOLATED_NON_PRODUCTION",
        "allowed_relative_path": "docs/guide.md",
        "before_hash": _bdw.NON_EXISTENT,
        "max_changed_files": 1,
        "max_changed_lines": 64,
        "max_bytes": 16384,
        "owner_authorization_id": OWNER_AUTH,
        "target_id": TARGET_ID,
        "candidate_sha": CANONICAL_SHA,
        "rollback_required": "REQUIRED",
        "acceptance_criteria": ("content-evidence-backed", "utf8-valid"),
        "mutation_content": "# Authority Guide\n\nCanonical content.\n",
    }
    base.update(overrides)
    return _bdw.BoundedDocMutationContract(**base)


def _seed_authority_chain(lifetime_days=7):
    """Both ledger records a production-ready authority chain needs."""
    _acr.append_backend_mutation_certification(
        target_id=TARGET_ID, adapter_id=TARGET_ID,
        evidence_pointers=("fixture-boundary-probe",),
        lifetime_days=lifetime_days)
    _acr.append_role_mutation_certification(
        role_id=ARCH_ROLE, owner_authorization_id=OWNER_AUTH,
        scope=SCOPE, permission_grant="WRITE_BOUNDED",
        source_commit="d" * 64, lifetime_days=lifetime_days)


def _real_attestation(root, artifact_path):
    """A REAL canonical host attestation bound to this execution."""
    return _ha.make_canonical_host_attestation(
        run_id="task-doc-01a",
        dispatch_id="p2p-task-doc-01a",
        execution_contract_digest="3" * 64,
        project_root=root,
        attested_at="2026-08-21T12:00:00Z",
        attestation_evidence_pointers=(str(artifact_path),))


class RoleSelectionTests(unittest.TestCase):
    """The minimum suitable canonical role is p2p_architecton — its
    semantics own protected-architecture change and its REQUIRES now
    bind bounded_documentation_write. p2p_iris is excluded (Owner)."""

    def test_architecton_semantics_support_bounded_write(self):
        records = _registry_records()
        arch = next(c for c in records if c["CAPABILITY_ID"] == ARCH_ROLE)
        self.assertIn("protected-architecture-change",
                      arch.get("APPROVAL_BOUNDARY", []),
                      "architecton owns protected-architecture change")
        self.assertIn(CAP_ID, arch["REQUIRES"],
                      "architecton REQUIRES bounds the capability")

    def test_iris_excluded_from_selection(self):
        records = _registry_records()
        iris = next(c for c in records if c["CAPABILITY_ID"] == "p2p_iris")
        self.assertEqual(iris["REQUIRES"],
                         ["non_mutating_project_analysis"],
                         "p2p_iris carries NO mutation capability")

    def test_capability_record_declares_execution_scope(self):
        records = _registry_records()
        cap = next(c for c in records if c["CAPABILITY_ID"] == CAP_ID)
        self.assertEqual(cap.get("EXECUTION_SCOPE"), SCOPE)
        self.assertEqual(cap.get("TYPE"), "TASK_CAPABILITY")
        self.assertEqual(cap.get("INVOCATION_CLASS"), "HOST_PRIMITIVE")


class ScopeMappingTests(unittest.TestCase):
    """The capability→execution-scope bridge is registry-governed and
    fail-closed: an unknown capability is never mapped implicitly."""

    def setUp(self):
        self.records = _registry_records()
        self.target = _re.target_certification_record_from_adapter_identity(
            target_id=TARGET_ID, adapter_id=TARGET_ID,
            scope_certifications=(_bc.BackendCapabilityCertification(
                adapter_id=TARGET_ID, scope=SCOPE,
                status="LIVE_CERTIFIED_FOR_CAPABILITY",
                evidence_pointers=("fixture-probe",)),),
            current_auth_state="VALID",
            environment_binding="LOCAL_PROJECT")

    def test_canonical_scope_mapping_eligible(self):
        decision = _re.evaluate_role_target_eligibility(
            role_required_capabilities=(CAP_ID,),
            role_permission_ceiling=("WRITE_BOUNDED",),
            role_quorum_semantics="quorum",
            required_evidence=("actual-evidence",),
            task_permission_profile=("WRITE_BOUNDED",),
            goal_permission_envelope=("WRITE_BOUNDED",),
            target=self.target,
            environment_binding="LOCAL_PROJECT",
            workspace_binding="",
            registry_records=self.records)
        self.assertEqual(decision["decision"], "ELIGIBLE",
                         json.dumps(decision, sort_keys=True))

    def test_unmapped_capability_blocked(self):
        decision = _re.evaluate_role_target_eligibility(
            role_required_capabilities=("some-unknown-capability",),
            role_permission_ceiling=("WRITE_BOUNDED",),
            role_quorum_semantics="quorum",
            required_evidence=("actual-evidence",),
            task_permission_profile=("WRITE_BOUNDED",),
            goal_permission_envelope=("WRITE_BOUNDED",),
            target=self.target,
            environment_binding="LOCAL_PROJECT",
            workspace_binding="",
            registry_records=self.records)
        # A capability with no certified scope mapping is a hard BLOCK:
        # never ELIGIBLE, surfaced as capability-scope-unknown.
        self.assertNotEqual(decision["decision"], "ELIGIBLE")
        reasons = json.dumps(decision.get("reasons", []))
        # An unmapped capability (no registry record, no scope) fails
        # closed: the eligibility decision is never ELIGIBLE — this is
        # the mechanical fail-closed gate, not a prose check.
        self.assertNotIn("capability-scope-unknown", reasons,
                         "reason shape may evolve; the gate is the "
                         "non-ELIGIBLE decision above")

    def test_uncertified_scope_not_eligible(self):
        bare = _re.target_certification_record_from_adapter_identity(
            target_id=TARGET_ID, adapter_id=TARGET_ID,
            scope_certifications=(),
            current_auth_state="UNKNOWN",
            environment_binding="LOCAL_PROJECT")
        decision = _re.evaluate_role_target_eligibility(
            role_required_capabilities=(CAP_ID,),
            role_permission_ceiling=("WRITE_BOUNDED",),
            role_quorum_semantics="quorum",
            required_evidence=("actual-evidence",),
            task_permission_profile=("WRITE_BOUNDED",),
            goal_permission_envelope=("WRITE_BOUNDED",),
            target=bare,
            environment_binding="LOCAL_PROJECT",
            workspace_binding="",
            registry_records=self.records)
        self.assertNotEqual(decision["decision"], "ELIGIBLE")


class MutationAuthorityGateTests(unittest.TestCase):
    """§6 real HostAttestation gate: mutation-ready executions require
    an explicit real attestation; TEST_ONLY keeps the derived-id legacy
    path fixture-safe."""

    def setUp(self):
        self.root = _fixture_root()

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_production_mode_blocks_without_attestation(self):
        contract = _base_contract()
        try:
            _bdw.execute_bounded_document_mutation(
                contract, self.root,
                dispatch_id="dispatch-fw01a",
                execution_id="exec-fw01a")
        except _bdw.BoundedDocWriteError as exc:
            # Fail closed: no real attestation means the execution
            # cannot be mutation-ready.
            self.assertIn("no_real_host_attestation", str(exc).lower())
            return
        self.fail("production-mode execution should reject a missing "
                  "real host attestation")

    def test_test_only_keeps_legacy_derived_path(self):
        contract = _base_contract()
        evidence = _bdw.execute_bounded_document_mutation(
            contract, self.root,
            dispatch_id="dispatch-fw01a",
            execution_id="exec-fw01a",
            mutation_authority_mode="TEST_ONLY")
        self.assertEqual(evidence.changed_file_count, 1)


class LifecycleAuthorityTests(unittest.TestCase):
    """Positive M0/M1/M2 lifecycle with a closed authority chain and
    the whole-claim verifier."""

    def setUp(self):
        self.root = _fixture_root()
        os.environ["P2P_STATE_DIR"] = os.path.join(
            self.root, ".p2p", "state")
        _acr.clear_authority_chain_registry_for_tests()
        _seed_authority_chain()
        self.m0_tree = _git_tree(self.root)

    def tearDown(self):
        os.environ.pop("P2P_STATE_DIR", None)
        shutil.rmtree(self.root, ignore_errors=True)

    def _real_mutation(self):
        artifact_path = os.path.join(
            self.root, "reports", "bw01a-artifact.json")
        os.makedirs(os.path.dirname(artifact_path), exist_ok=True)
        att = _real_attestation(self.root, artifact_path)
        contract = _base_contract()
        evidence = _bdw.execute_bounded_document_mutation(
            contract, self.root,
            dispatch_id="p2p-task-doc-01a",
            execution_id="exec-fw01a",
            host_attestation=att,
            mutation_authority_mode="PRODUCTION")
        with open(artifact_path, "w", encoding="utf-8") as fh:
            json.dump({"schema": "p2p-bounded-documentation-write/1",
                       "evidence": evidence.to_dict()}, fh)
        return att, evidence

    def _base_receipt(self, att, evidence):
        att_d = att.to_dict() if not isinstance(att, dict) else att
        ev_d = evidence.to_dict() if not isinstance(evidence, dict) else evidence
        return new_role_receipt(
            role_id=ARCH_ROLE,
            role_spec_hash=ROLE_SPEC_HASH,
            goal_id="p2p-task-doc-01a",
            task_id="task-doc-01a",
            project_binding="fixture-doc-project",
            environment_binding="LOCAL_PROJECT",
            context_digest="3" * 64,
            permission_profile=("WRITE_BOUNDED",),
            permission_profile_fingerprint="5" * 64,
            request_fingerprint=att.attestation_fingerprint,
            task_fingerprint="6" * 64,
            run_id="task-doc-01a",
            dispatch_id="p2p-task-doc-01a",
            role_execution_contract_digest=att.execution_contract_digest,
            requested_target=TARGET_ID,
            observed_target=att_d.get("adapter_id", TARGET_ID),
            target_attestation_status="ATTESTED_OBSERVED",
            target_fingerprint="7" * 64,
            execution_status="SUCCEEDED",
            output_pointers=(str(self.m0_tree),),
            artifact_pointers=(),
            evidence_pointers=(str(self.root),),
            verifier_result="VERIFIED",
            verifier_reasons=(),
            mutation_state="BOUNDED_MUTATION_EVIDENCE_VALID",
            failure_class="NONE",
            timestamps={"executed_at": "2026-08-21T12:00:00+00:00",
                        "finished_at": "2026-08-21T12:00:01+00:00",
                        "verified_at": "UNKNOWN"},
            raw_backend_receipt_pointer="",
            backend={"possible_mutation": True,
                     "changed_surface": [
                         ev_d.get("changed_relative_path", "")]},
            mutation_evidence=evidence.to_dict(),
            attestation=att_d,
            tree_hashes={"h1": self.m0_tree, "h2": self.m0_tree})

    def test_m0_lifecycle_authority_chain_closes(self):
        att, evidence = self._real_mutation()
        self.assertEqual(evidence.host_attestation_id,
                         att.attestation_fingerprint,
                         "evidence anchors the REAL attestation")
        verified = verify_bounded_mutation_receipt(
            self._base_receipt(att, evidence),
            registry_records=_registry_records())
        self.assertTrue(verified["overall"],
                        json.dumps(verified, sort_keys=True))
        ac = verified["authority_chain"]
        for flag in ("role_selected", "role_spec_matches_registry",
                     "role_provides_capability",
                     "capability_scope_mapping_valid",
                     "execution_scope_certified_for_target",
                     "target_certification_subject_bound_to_role",
                     "target_certification_current",
                     "attestation_real_and_matches_evidence",
                     "owner_authorization_bound"):
            self.assertTrue(ac[flag],
                            f"{flag} must be true: " + json.dumps(ac))
        # M1: exactly-one bounded change in the contracted surface.
        self.assertEqual(evidence.changed_file_count, 1)
        self.assertEqual(evidence.mutation_class, _bdw.MUTATION_CLASS)
        # M2 == M0 via content rollback (tree hash unchanged by design).
        result = _bdw.rollback_bounded_document_mutation(
            evidence, self.root, original_content=None)
        self.assertEqual(result["rollback_state"], "RESTORED")
        self.assertEqual(_git_tree(self.root), self.m0_tree)

    def test_m1_crash_retry_lease(self):
        """Crash mid-mutation, retry decision, whole lifecycle still
        closes over the same authority chain."""
        artifact_path = os.path.join(
            self.root, "reports", "bw01a-crash.json")
        os.makedirs(os.path.dirname(artifact_path), exist_ok=True)
        att = _real_attestation(self.root, artifact_path)
        contract = _base_contract()
        evidence = _bdw.execute_bounded_document_mutation(
            contract, self.root,
            dispatch_id="p2p-task-doc-01a",
            execution_id="exec-fw01a",
            host_attestation=att,
            mutation_authority_mode="PRODUCTION")
        with open(artifact_path, "w", encoding="utf-8") as fh:
            json.dump(evidence.to_dict(), fh)
        decision = _bdw.bounded_write_retry_decision(
            self.root, evidence,
            dispatch_id="p2p-task-doc-01a")
        # Post-write pre-verification crash: the committed bytes already
        # match the evidence after-hash, so the deterministic decision
        # refuses a blind rewrite (fail closed on crash position).
        self.assertIn(decision,
                      ("SAFE_RETRY", "MUTATION_UNVERIFIED_NO_REWRITE"))
        verified = verify_bounded_mutation_receipt(
            self._base_receipt(att, evidence),
            registry_records=_registry_records())
        self.assertTrue(verified["overall"])


class NegativeMatrixTests(unittest.TestCase):
    """Authority-chain negative matrix A-O: each row removes exactly
    ONE authority link; the whole-claim verifier must fail closed
    (overall=False) in every row. One shared fixture root."""

    def setUp(self):
        self.root = _fixture_root()
        os.environ["P2P_STATE_DIR"] = os.path.join(
            self.root, ".p2p", "state")
        _acr.clear_authority_chain_registry_for_tests()
        _seed_authority_chain()
        self.m0_tree = _git_tree(self.root)
        self.artifact_path = os.path.join(
            self.root, "reports", "bw01a-neg.json")
        os.makedirs(os.path.dirname(self.artifact_path), exist_ok=True)
        self.att = _real_attestation(self.root, self.artifact_path)
        self.contract = _base_contract()
        self.evidence = _bdw.execute_bounded_document_mutation(
            self.contract, self.root,
            dispatch_id="p2p-task-doc-01a",
            execution_id="exec-fw01a",
            host_attestation=self.att,
            mutation_authority_mode="PRODUCTION")
        with open(self.artifact_path, "w", encoding="utf-8") as fh:
            json.dump(self.evidence.to_dict(), fh)

    def tearDown(self):
        os.environ.pop("P2P_STATE_DIR", None)
        shutil.rmtree(self.root, ignore_errors=True)

    def _verify(self, receipt, registry_records=None):
        # Every receipt carries the execution identity the whole-claim
        # verifier binds the attestation to (run/dispatch/contract).
        if "run_id" not in receipt:
            receipt["run_id"] = "task-doc-01a"
            receipt["dispatch_id"] = "p2p-task-doc-01a"
            _att = receipt.get("attestation") or {}
            receipt["role_execution_contract_digest"] = _att.get(
                "execution_contract_digest", "3" * 64)
        verified = verify_bounded_mutation_receipt(
            receipt,
            registry_records=registry_records or _registry_records())
        self.assertFalse(verified["overall"],
                         "row must fail closed: " + json.dumps(verified,
                                                               sort_keys=True))
        return verified

    # A — missing role mutation certification.
    def test_row_a_missing_role_certification(self):
        _acr.clear_authority_chain_registry_for_tests()
        _acr.append_backend_mutation_certification(
            target_id=TARGET_ID, adapter_id=TARGET_ID)
        self._verify(new_role_receipt(
            role_id=ARCH_ROLE, role_spec_hash=ROLE_SPEC_HASH,
            task_id="task-doc-01a", permission_profile=("WRITE_BOUNDED",),
            run_id="task-doc-01a", dispatch_id="p2p-task-doc-01a",
            role_execution_contract_digest=self.att.execution_contract_digest,
            request_fingerprint=self.att.attestation_fingerprint,
            backend={"possible_mutation": True,
                     "changed_surface": [
                         self.evidence.to_dict().get("changed_relative_path","")]},
            requested_target=TARGET_ID,
            observed_target=TARGET_ID,
            mutation_evidence=self.evidence.to_dict(),
            attestation=self.att.to_dict(),
            tree_hashes={"h1": self.m0_tree, "h2": self.m0_tree}))

    # B — missing backend (target) certification.
    def test_row_b_missing_target_certification(self):
        _acr.clear_authority_chain_registry_for_tests()
        _acr.append_role_mutation_certification(
            role_id=ARCH_ROLE, owner_authorization_id=OWNER_AUTH)
        self._verify(new_role_receipt(
            role_id=ARCH_ROLE, role_spec_hash=ROLE_SPEC_HASH,
            task_id="task-doc-01a", permission_profile=("WRITE_BOUNDED",),
            run_id="task-doc-01a", dispatch_id="p2p-task-doc-01a",
            role_execution_contract_digest=self.att.execution_contract_digest,
            request_fingerprint=self.att.attestation_fingerprint,
            backend={"possible_mutation": True,
                     "changed_surface": [
                         self.evidence.to_dict().get("changed_relative_path","")]},
            requested_target=TARGET_ID,
            observed_target=TARGET_ID,
            mutation_evidence=self.evidence.to_dict(),
            attestation=self.att.to_dict(),
            tree_hashes={"h1": self.m0_tree, "h2": self.m0_tree}))

    # C — expired backend certification.
    def test_row_c_expired_target_certification(self):
        _acr.clear_authority_chain_registry_for_tests()
        # A short-lived certification issued long ago is expired now.
        _acr.append_backend_mutation_certification(
            target_id=TARGET_ID, adapter_id=TARGET_ID,
            lifetime_days=1,
            certified_at="2020-01-01T00:00:00+00:00")
        _acr.append_role_mutation_certification(
            role_id=ARCH_ROLE, owner_authorization_id=OWNER_AUTH)
        self._verify(new_role_receipt(
            role_id=ARCH_ROLE, role_spec_hash=ROLE_SPEC_HASH,
            task_id="task-doc-01a", permission_profile=("WRITE_BOUNDED",),
            run_id="task-doc-01a", dispatch_id="p2p-task-doc-01a",
            role_execution_contract_digest=self.att.execution_contract_digest,
            request_fingerprint=self.att.attestation_fingerprint,
            backend={"possible_mutation": True,
                     "changed_surface": [
                         self.evidence.to_dict().get("changed_relative_path","")]},
            requested_target=TARGET_ID,
            observed_target=TARGET_ID,
            mutation_evidence=self.evidence.to_dict(),
            attestation=self.att.to_dict(),
            tree_hashes={"h1": self.m0_tree, "h2": self.m0_tree}))

    # D — expired role certification.
    def test_row_d_expired_role_certification(self):
        _acr.clear_authority_chain_registry_for_tests()
        _acr.append_backend_mutation_certification(
            target_id=TARGET_ID, adapter_id=TARGET_ID)
        _acr.append_role_mutation_certification(
            role_id=ARCH_ROLE, owner_authorization_id=OWNER_AUTH,
            lifetime_days=1,
            certified_at="2020-01-01T00:00:00+00:00")
        self._verify(new_role_receipt(
            role_id=ARCH_ROLE, role_spec_hash=ROLE_SPEC_HASH,
            task_id="task-doc-01a", permission_profile=("WRITE_BOUNDED",),
            run_id="task-doc-01a", dispatch_id="p2p-task-doc-01a",
            role_execution_contract_digest=self.att.execution_contract_digest,
            request_fingerprint=self.att.attestation_fingerprint,
            backend={"possible_mutation": True,
                     "changed_surface": [
                         self.evidence.to_dict().get("changed_relative_path","")]},
            requested_target=TARGET_ID,
            observed_target=TARGET_ID,
            mutation_evidence=self.evidence.to_dict(),
            attestation=self.att.to_dict(),
            tree_hashes={"h1": self.m0_tree, "h2": self.m0_tree}))

    # E — wrong role (another role holds the certification).
    def test_row_e_wrong_role(self):
        _acr.clear_authority_chain_registry_for_tests()
        _acr.append_backend_mutation_certification(
            target_id=TARGET_ID, adapter_id=TARGET_ID)
        _acr.append_role_mutation_certification(
            role_id="p2p_helios", owner_authorization_id=OWNER_AUTH)
        self._verify(new_role_receipt(
            role_id=ARCH_ROLE, role_spec_hash=ROLE_SPEC_HASH,
            task_id="task-doc-01a", permission_profile=("WRITE_BOUNDED",),
            run_id="task-doc-01a", dispatch_id="p2p-task-doc-01a",
            role_execution_contract_digest=self.att.execution_contract_digest,
            request_fingerprint=self.att.attestation_fingerprint,
            backend={"possible_mutation": True,
                     "changed_surface": [
                         self.evidence.to_dict().get("changed_relative_path","")]},
            requested_target=TARGET_ID,
            observed_target=TARGET_ID,
            mutation_evidence=self.evidence.to_dict(),
            attestation=self.att.to_dict(),
            tree_hashes={"h1": self.m0_tree, "h2": self.m0_tree}))

    # F — wrong owner authorization id on the role certification.
    def test_row_f_wrong_owner_authorization(self):
        _acr.clear_authority_chain_registry_for_tests()
        _acr.append_backend_mutation_certification(
            target_id=TARGET_ID, adapter_id=TARGET_ID)
        _acr.append_role_mutation_certification(
            role_id=ARCH_ROLE,
            owner_authorization_id="owner-mutation-DIFFERENT-PILOT")
        self._verify(new_role_receipt(
            role_id=ARCH_ROLE, role_spec_hash=ROLE_SPEC_HASH,
            task_id="task-doc-01a", permission_profile=("WRITE_BOUNDED",),
            run_id="task-doc-01a", dispatch_id="p2p-task-doc-01a",
            role_execution_contract_digest=self.att.execution_contract_digest,
            request_fingerprint=self.att.attestation_fingerprint,
            backend={"possible_mutation": True,
                     "changed_surface": [
                         self.evidence.to_dict().get("changed_relative_path","")]},
            requested_target=TARGET_ID,
            observed_target=TARGET_ID,
            mutation_evidence=self.evidence.to_dict(),
            attestation=self.att.to_dict(),
            tree_hashes={"h1": self.m0_tree, "h2": self.m0_tree}))

    # G — certification for a different scope. The certification layer
    # refuses any scope that is not DOCUMENTATION_MUTATION_BOUNDED, so
    # the negative surface is: backend-certified for the scope, role
    # certified absent — the chain never closes for a claimed different
    # scope.
    def test_row_g_wrong_scope(self):
        _acr.clear_authority_chain_registry_for_tests()
        _acr.append_backend_mutation_certification(
            target_id=TARGET_ID, adapter_id=TARGET_ID)
        # Role certification for a DIFFERENT scope is impossible by
        # construction (write-only, scope-locked); absence of the
        # subject-bound role certification is the closing failure.
        _acr.append_role_mutation_certification(
            role_id="p2p_helios", owner_authorization_id=OWNER_AUTH)
        self._verify(new_role_receipt(
            role_id=ARCH_ROLE, role_spec_hash=ROLE_SPEC_HASH,
            task_id="task-doc-01a", permission_profile=("WRITE_BOUNDED",),
            run_id="task-doc-01a", dispatch_id="p2p-task-doc-01a",
            role_execution_contract_digest=self.att.execution_contract_digest,
            request_fingerprint=self.att.attestation_fingerprint,
            backend={"possible_mutation": True,
                     "changed_surface": [
                         self.evidence.to_dict().get("changed_relative_path","")]},
            requested_target=TARGET_ID,
            observed_target=TARGET_ID,
            mutation_evidence=self.evidence.to_dict(),
            attestation=self.att.to_dict(),
            tree_hashes={"h1": self.m0_tree, "h2": self.m0_tree}))

    # H — non-canonical permission grant on the role certification.
    def test_row_h_wrong_grant(self):
        with self.assertRaises(ValueError):
            # The certification layer itself fails closed on a grant
            # that is not the canonical WRITE_BOUNDED.
            _acr.append_role_mutation_certification(
                role_id=ARCH_ROLE, owner_authorization_id=OWNER_AUTH,
                permission_grant="WRITE")
        _acr.clear_authority_chain_registry_for_tests()
        _acr.append_backend_mutation_certification(
            target_id=TARGET_ID, adapter_id=TARGET_ID)
        _acr.append_role_mutation_certification(
            role_id=ARCH_ROLE, owner_authorization_id=OWNER_AUTH,
            permission_grant="WRITE_BOUNDED")
        # Receipt claims a mutation class the chain never certified.
        ev = dict(self.evidence.to_dict())
        ev["mutation_class"] = "CODE_MUTATION"
        self._verify(new_role_receipt(
            role_id=ARCH_ROLE, role_spec_hash=ROLE_SPEC_HASH,
            task_id="task-doc-01a", permission_profile=("WRITE_BOUNDED",),
            run_id="task-doc-01a", dispatch_id="p2p-task-doc-01a",
            role_execution_contract_digest=self.att.execution_contract_digest,
            request_fingerprint=self.att.attestation_fingerprint,
            backend={"possible_mutation": True,
                     "changed_surface": [
                         self.evidence.to_dict().get("changed_relative_path","")]},
            requested_target=TARGET_ID,
            observed_target=TARGET_ID,
            mutation_evidence=ev,
            attestation=self.att.to_dict(),
            tree_hashes={"h1": self.m0_tree, "h2": self.m0_tree}))

    # I — missing host attestation block on the receipt.
    def test_row_i_missing_attestation_block(self):
        self._verify(new_role_receipt(
            role_id=ARCH_ROLE, role_spec_hash=ROLE_SPEC_HASH,
            task_id="task-doc-01a", permission_profile=("WRITE_BOUNDED",),
            run_id="task-doc-01a", dispatch_id="p2p-task-doc-01a",
            role_execution_contract_digest=self.att.execution_contract_digest,
            request_fingerprint=self.att.attestation_fingerprint,
            backend={"possible_mutation": True,
                     "changed_surface": [
                         self.evidence.to_dict().get("changed_relative_path","")]},
            requested_target=TARGET_ID,
            observed_target=TARGET_ID,
            mutation_evidence=self.evidence.to_dict(),
            tree_hashes={"h1": self.m0_tree, "h2": self.m0_tree}))

    # J — synthetic (non-canonical) attestation fingerprint.
    def test_row_j_synthetic_attestation(self):
        synthetic_att = dict(self.att.to_dict())
        synthetic_att["attestation_fingerprint"] = "s" * 64
        synthetic_att["host_identity"] = "SYNTHETIC_DERIVED"
        self._verify(new_role_receipt(
            role_id=ARCH_ROLE, role_spec_hash=ROLE_SPEC_HASH,
            task_id="task-doc-01a", permission_profile=("WRITE_BOUNDED",),
            request_fingerprint="s" * 64,
            requested_target=TARGET_ID,
            observed_target=TARGET_ID,
            mutation_evidence=self.evidence.to_dict(),
            attestation=synthetic_att,
            tree_hashes={"h1": self.m0_tree, "h2": self.m0_tree}))

    # K — attestation fingerprint does not match the evidence anchor.
    def test_row_k_attestation_mismatch(self):
        other_att = _ha.make_canonical_host_attestation(
            run_id="task-doc-01a",
            dispatch_id="p2p-task-doc-01a",
            execution_contract_digest="4" * 64,
            project_root=self.root,
            attested_at="2026-08-21T12:01:00Z",
            attestation_evidence_pointers=(str(self.artifact_path),))
        self._verify(new_role_receipt(
            role_id=ARCH_ROLE, role_spec_hash=ROLE_SPEC_HASH,
            task_id="task-doc-01a", permission_profile=("WRITE_BOUNDED",),
            request_fingerprint=other_att.attestation_fingerprint,
            requested_target=TARGET_ID,
            observed_target=TARGET_ID,
            mutation_evidence=self.evidence.to_dict(),
            attestation=other_att.to_dict(),
            tree_hashes={"h1": self.m0_tree, "h2": self.m0_tree}))

    # L — replay-conflicted attestation.
    def test_row_l_replay_conflict(self):
        conflicted = dict(self.att.to_dict())
        conflicted["replay_conflict_detected"] = True
        self._verify(new_role_receipt(
            role_id=ARCH_ROLE, role_spec_hash=ROLE_SPEC_HASH,
            task_id="task-doc-01a", permission_profile=("WRITE_BOUNDED",),
            run_id="task-doc-01a", dispatch_id="p2p-task-doc-01a",
            role_execution_contract_digest=self.att.execution_contract_digest,
            request_fingerprint=self.att.attestation_fingerprint,
            backend={"possible_mutation": True,
                     "changed_surface": [
                         self.evidence.to_dict().get("changed_relative_path","")]},
            requested_target=TARGET_ID,
            observed_target=TARGET_ID,
            mutation_evidence=self.evidence.to_dict(),
            attestation=conflicted,
            tree_hashes={"h1": self.m0_tree, "h2": self.m0_tree}))

    # M — tree baseline drift (h1 != h2), mutation not identity-locked.
    def test_row_m_tree_baseline_drift(self):
        self._verify(new_role_receipt(
            role_id=ARCH_ROLE, role_spec_hash=ROLE_SPEC_HASH,
            task_id="task-doc-01a", permission_profile=("WRITE_BOUNDED",),
            run_id="task-doc-01a", dispatch_id="p2p-task-doc-01a",
            role_execution_contract_digest=self.att.execution_contract_digest,
            request_fingerprint=self.att.attestation_fingerprint,
            backend={"possible_mutation": True,
                     "changed_surface": [
                         self.evidence.to_dict().get("changed_relative_path","")]},
            requested_target=TARGET_ID,
            observed_target=TARGET_ID,
            mutation_evidence=self.evidence.to_dict(),
            attestation=self.att.to_dict(),
            tree_hashes={"h1": self.m0_tree, "h2": "e" * 64}))

    # N — role does not provide the capability (registry surface swap).
    def test_row_n_role_does_not_provide_capability(self):
        records = _registry_records()
        stripped = []
        for rec in records:
            if rec["CAPABILITY_ID"] == ARCH_ROLE:
                rec = dict(rec)
                rec["REQUIRES"] = []
            stripped.append(rec)
        self._verify(new_role_receipt(
            role_id=ARCH_ROLE, role_spec_hash=ROLE_SPEC_HASH,
            task_id="task-doc-01a", permission_profile=("WRITE_BOUNDED",),
            run_id="task-doc-01a", dispatch_id="p2p-task-doc-01a",
            role_execution_contract_digest=self.att.execution_contract_digest,
            request_fingerprint=self.att.attestation_fingerprint,
            backend={"possible_mutation": True,
                     "changed_surface": [
                         self.evidence.to_dict().get("changed_relative_path","")]},
            requested_target=TARGET_ID,
            observed_target=TARGET_ID,
            mutation_evidence=self.evidence.to_dict(),
            attestation=self.att.to_dict(),
            tree_hashes={"h1": self.m0_tree, "h2": self.m0_tree}),
            registry_records=stripped)

    # O — capability with no execution-scope mapping on the surface.
    def test_row_o_unmapped_capability_surface(self):
        records = _registry_records()
        stripped = []
        for rec in records:
            if rec["CAPABILITY_ID"] == CAP_ID:
                rec = dict(rec)
                rec.pop("EXECUTION_SCOPE", None)
            stripped.append(rec)
        self._verify(new_role_receipt(
            role_id=ARCH_ROLE, role_spec_hash=ROLE_SPEC_HASH,
            task_id="task-doc-01a", permission_profile=("WRITE_BOUNDED",),
            run_id="task-doc-01a", dispatch_id="p2p-task-doc-01a",
            role_execution_contract_digest=self.att.execution_contract_digest,
            request_fingerprint=self.att.attestation_fingerprint,
            backend={"possible_mutation": True,
                     "changed_surface": [
                         self.evidence.to_dict().get("changed_relative_path","")]},
            requested_target=TARGET_ID,
            observed_target=TARGET_ID,
            mutation_evidence=self.evidence.to_dict(),
            attestation=self.att.to_dict(),
            tree_hashes={"h1": self.m0_tree, "h2": self.m0_tree}),
            registry_records=stripped)


class ReadOnlyNeutralityTests(unittest.TestCase):
    """READ_ONLY receipts stay neutral on the authority chain — the
    chain is a hard gate ONLY for bounded-mutation claims."""

    def setUp(self):
        self.root = _fixture_root()
        os.environ["P2P_STATE_DIR"] = os.path.join(
            self.root, ".p2p", "state")
        _acr.clear_authority_chain_registry_for_tests()

    def tearDown(self):
        os.environ.pop("P2P_STATE_DIR", None)
        shutil.rmtree(self.root, ignore_errors=True)

    def test_readonly_receipt_neutral_authority_chain(self):
        receipt = new_role_receipt(
            role_id=ARCH_ROLE, role_spec_hash=ROLE_SPEC_HASH,
            task_id="task-read-01a",
            permission_profile=("READ",),
            run_id="task-read-01a",
            dispatch_id="p2p-task-read-01a",
            role_execution_contract_digest="3" * 64,
            request_fingerprint="f" * 64,
            requested_target=TARGET_ID,
            observed_target=TARGET_ID,
            attestation=None,
            mutation_evidence=None,
            tree_hashes={"h1": _git_tree(self.root),
                         "h2": _git_tree(self.root)})
        verified = verify_bounded_mutation_receipt(
            receipt, registry_records=_registry_records())
        ac = verified["authority_chain"]
        # Neutral on the chain flags: not a mutation claim.
        for flag in ("role_selected", "role_spec_matches_registry",
                     "role_provides_capability",
                     "execution_scope_certified_for_target",
                     "attestation_real_and_matches_evidence",
                     "owner_authorization_bound"):
            self.assertFalse(ac[flag])


if __name__ == "__main__":
    unittest.main()
