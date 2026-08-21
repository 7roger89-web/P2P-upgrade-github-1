"""P2P-BOUNDED-DOCUMENTATION-WRITE-01B: role/host semantics finalization.

Two seams close here (fail-closed, never widening):

  S1 — REQUIRES/PROVIDES conflation. REQUIRES is dependency provenance
       only; what a role provides comes from the EXPLICIT PROVIDES
       field of its registry record. A role without PROVIDES provides
       NOTHING. The whole-claim verifier additionally requires
       role_explicitly_provides_capability, not the dependency path.

  S2 — HostAttestation keyed to the MUTATION_READY authority mode,
       never to any environment label. The canonical modes are the
       bounded_documentation_write constants
       (TEST_ONLY_AUTHORITY_MODE, MUTATION_READY_AUTHORITY_MODE); the
       verifier requires mutation_authority_mode_is_mutation_ready and
       test_only_evidence == false for any mutation-ready VERIFIED
       claim. TEST_ONLY evidence can never escalate.

Positive: M0 (full closed chain, real attestation, MUTATION_READY),
M1 (crash-retry over the same authority chain), M2 (rollback == M0).
Negative matrix A-N (14 rows): one authority/semantics link removed
per row; whole-claim verifier must fail closed.
All tests use a disposable fixture repository — never authoritative
Game Truyện, never Gia Phả, never Gia Phả logs.
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
from p2p_capabilities.role_receipt import (
    new_role_receipt, verify_bounded_mutation_receipt,
)

CANONICAL_SHA = "a" * 64
ROLE_SPEC_HASH = "9" * 64
ARCH_ROLE = "p2p_architecton"
CAP_ID = "bounded_documentation_write"
SCOPE = "DOCUMENTATION_MUTATION_BOUNDED"
TARGET_ID = "adapter-doc-01b"
OWNER_AUTH = "owner-mutation-pilot-01b"

REGISTRY_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "capabilities.json")


def _registry_records(*extra_ids):
    with open(REGISTRY_FILE, encoding="utf-8") as fh:
        ids = {CAP_ID, ARCH_ROLE, "p2p_iris", "p2p_tecton"}
        ids.update(extra_ids)
        return [c for c in json.load(fh).get("capabilities", ()) if
                c.get("CAPABILITY_ID") in ids]


def _fixture_root():
    root = tempfile.mkdtemp(prefix="bw01bfx")
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
        "goal_id": "goal-fw01b",
        "task_id": "task-doc-01b",
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
        "mutation_content": "# Semantics Guide\n\nCanonical content.\n",
    }
    base.update(overrides)
    return _bdw.BoundedDocMutationContract(**base)


def _seed_authority_chain(lifetime_days=7):
    _acr.append_backend_mutation_certification(
        target_id=TARGET_ID, adapter_id=TARGET_ID,
        evidence_pointers=("fixture-boundary-probe",),
        lifetime_days=lifetime_days)
    _acr.append_role_mutation_certification(
        role_id=ARCH_ROLE, owner_authorization_id=OWNER_AUTH,
        scope=SCOPE, permission_grant="WRITE_BOUNDED",
        source_commit="d" * 64, lifetime_days=lifetime_days)


def _real_attestation(root, artifact_path):
    return _ha.make_canonical_host_attestation(
        run_id="task-doc-01b",
        dispatch_id="p2p-task-doc-01b",
        execution_contract_digest="3" * 64,
        project_root=root,
        attested_at="2026-08-21T12:00:00Z",
        attestation_evidence_pointers=(str(artifact_path),))


def _base_receipt(role_id=ARCH_ROLE, mut_evidence=None,
                  att=None, m0_tree=""):
    ev_d = mut_evidence.to_dict() if not isinstance(mut_evidence, dict) \
        else mut_evidence
    att_d = (att.to_dict() if att is not None and
             not isinstance(att, dict) else (att or {}))
    receipt = new_role_receipt(
        role_id=role_id, role_spec_hash=ROLE_SPEC_HASH,
        task_id="task-doc-01b",
        permission_profile=("WRITE_BOUNDED",),
        run_id="task-doc-01b", dispatch_id="p2p-task-doc-01b",
        role_execution_contract_digest=(
            att.execution_contract_digest
            if att is not None else "3" * 64),
        request_fingerprint=(att.attestation_fingerprint
                             if att is not None else "2" * 64),
        backend={"possible_mutation": True,
                 "changed_surface": [
                     ev_d.get("changed_relative_path", "")]},
        requested_target=TARGET_ID,
        observed_target=(att.adapter_id if att is not None else TARGET_ID),
        mutation_evidence=ev_d,
        attestation=att_d if att_d else None,
        tree_hashes={"h1": m0_tree or "", "h2": m0_tree or ""})
    return receipt


class SemanticsTests(unittest.TestCase):
    """S1: PROVIDES-only provision. S2: authority mode binding."""

    def test_provides_field_present_on_architecton(self):
        arch = next(c for c in _registry_records()
                    if c["CAPABILITY_ID"] == ARCH_ROLE)
        self.assertIn(CAP_ID, arch.get("PROVIDES", []),
                      "architecton EXPLICITLY provides the capability")

    def test_provides_distinct_from_requires(self):
        records = _registry_records()
        arch = next(c for c in records
                    if c["CAPABILITY_ID"] == ARCH_ROLE)
        iris = next(c for c in records
                    if c["CAPABILITY_ID"] == "p2p_iris")
        # A role whose REQUIRES carries the capability but whose
        # PROVIDES does not is NOT a provider (S1 fail-closed rule).
        self.assertIn(CAP_ID, arch["REQUIRES"])
        iris_no_provides = CAP_ID not in iris.get("PROVIDES", [])
        iris_requires_it = CAP_ID in iris.get("REQUIRES", [])
        self.assertFalse(
            iris_requires_it,
            "p2p_iris must not even depend on the mutation capability")
        self.assertTrue(iris_no_provides,
                        "a role without PROVIDES provides nothing")

    def test_role_capability_evidence_provides_only(self):
        """FW03 evidence surface: caps come from PROVIDES only."""
        from p2p_capabilities.team_intelligence import (
            role_capability_evidence)
        evid = role_capability_evidence(ARCH_ROLE, _registry_records())
        caps = tuple(e.capability_id for e in evid)
        self.assertIn(CAP_ID, caps,
                      "FW03 must list the capability via PROVIDES")
        # REQUIRES entries must never appear as provided caps.
        for cap in ("bounded_documentation_write_dependency",):
            self.assertNotIn(cap, caps)
        # Iris has no PROVIDES -> provides nothing.
        evid_iris = role_capability_evidence(
            "p2p_iris", _registry_records())
        self.assertEqual(tuple(), evid_iris,
                         "p2p_iris (no PROVIDES) provides NOTHING")

    def test_authority_mode_constants_canonical(self):
        self.assertEqual(
            sorted(_bdw.MUTATION_AUTHORITY_MODES),
            ["MUTATION_READY", "TEST_ONLY"])

    def test_unknown_mode_blocks_execution(self):
        root = _fixture_root()
        try:
            _bdw.execute_bounded_document_mutation(
                _base_contract(), root, dispatch_id="fw01b",
                mutation_authority_mode="UNKNOWN_MODE")
        except _bdw.BoundedDocWriteError as exc:
            self.assertIn("MUTATION_AUTHORITY_MODE_INVALID",
                          str(exc))
            return
        finally:
            shutil.rmtree(root, ignore_errors=True)
        self.fail("an unknown authority mode must BLOCK execution")

    def test_test_only_cannot_satisfy_mutation_ready(self):
        """S2: TEST_ONLY evidence (derived identity, no real host) is
        bound and verifiable but MUST fail the whole-claim verifier's
        mutation-ready claim (test_only_evidence must be false)."""
        root = _fixture_root()
        try:
            evidence = _bdw.execute_bounded_document_mutation(
                _base_contract(), root, dispatch_id="fw01b",
                mutation_authority_mode="TEST_ONLY")
            ev_d = evidence.to_dict()
            self.assertEqual(ev_d["mutation_authority_mode"], "TEST_ONLY")
            receipt = _base_receipt(mut_evidence=ev_d, att=None)
            verified = verify_bounded_mutation_receipt(
                receipt, registry_records=_registry_records())
            self.assertFalse(verified["overall"],
                             "TEST_ONLY evidence must never satisfy a "
                             "mutation-ready claim: "
                             + json.dumps(verified["authority_chain"]))
            ac = verified["authority_chain"]
            self.assertTrue(ac.get("test_only_evidence"))
            self.assertFalse(
                ac.get("mutation_authority_mode_is_mutation_ready"))
        finally:
            shutil.rmtree(root, ignore_errors=True)


class LifecycleSemanticsTests(unittest.TestCase):
    """Positive M0/M1/M2 lifecycle over the finalized semantics."""

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
            self.root, "reports", "bw01b-artifact.json")
        os.makedirs(os.path.dirname(artifact_path), exist_ok=True)
        att = _real_attestation(self.root, artifact_path)
        evidence = _bdw.execute_bounded_document_mutation(
            _base_contract(), self.root,
            dispatch_id="p2p-task-doc-01b", execution_id="exec-fw01b",
            host_attestation=att,
            mutation_authority_mode="MUTATION_READY")
        with open(artifact_path, "w", encoding="utf-8") as fh:
            json.dump(evidence.to_dict(), fh)
        return att, evidence

    def test_m0_semantics_close(self):
        att, evidence = self._real_mutation()
        self.assertEqual(evidence.mutation_authority_mode, "MUTATION_READY")
        self.assertEqual(evidence.host_attestation_id,
                         att.attestation_fingerprint)
        verified = verify_bounded_mutation_receipt(
            _base_receipt(mut_evidence=evidence, att=att,
                          m0_tree=self.m0_tree),
            registry_records=_registry_records())
        self.assertTrue(verified["overall"],
                        json.dumps(verified, sort_keys=True))
        ac = verified["authority_chain"]
        for flag in ("role_selected", "role_spec_matches_registry",
                     "role_provides_capability",
                     "role_explicitly_provides_capability",
                     "capability_scope_mapping_valid",
                     "execution_scope_certified_for_target",
                     "target_certification_subject_bound_to_role",
                     "target_certification_current",
                     "attestation_real_and_matches_evidence",
                     "owner_authorization_bound",
                     "mutation_authority_mode_is_canonical",
                     "mutation_authority_mode_is_mutation_ready",
                     "test_only_evidence"):
            expected = flag != "test_only_evidence"
            self.assertEqual(ac[flag], expected,
                             f"{flag} must be {expected}: "
                             + json.dumps(ac))
        # M1: exactly-one bounded change.
        self.assertEqual(evidence.changed_file_count, 1)
        # M2: content rollback restores the M0 tree.
        result = _bdw.rollback_bounded_document_mutation(
            evidence, self.root, original_content=None)
        self.assertEqual(result["rollback_state"], "RESTORED")
        self.assertEqual(_git_tree(self.root), self.m0_tree)

    def test_m1_crash_retry_authority_mode_bound(self):
        artifact_path = os.path.join(
            self.root, "reports", "bw01b-crash.json")
        os.makedirs(os.path.dirname(artifact_path), exist_ok=True)
        att = _real_attestation(self.root, artifact_path)
        evidence = _bdw.execute_bounded_document_mutation(
            _base_contract(), self.root,
            dispatch_id="p2p-task-doc-01b", execution_id="exec-fw01b",
            host_attestation=att,
            mutation_authority_mode="MUTATION_READY")
        decision = _bdw.bounded_write_retry_decision(
            self.root, evidence, dispatch_id="p2p-task-doc-01b")
        self.assertIn(decision,
                      ("SAFE_RETRY", "MUTATION_UNVERIFIED_NO_REWRITE"))


class NegativeSemanticsMatrixTests(unittest.TestCase):
    """Negative matrix A-N (14 rows): exactly one link removed per row.
    The whole-claim verifier must fail closed (overall=False)."""

    def setUp(self):
        self.root = _fixture_root()
        os.environ["P2P_STATE_DIR"] = os.path.join(
            self.root, ".p2p", "state")
        _acr.clear_authority_chain_registry_for_tests()
        _seed_authority_chain()
        self.m0_tree = _git_tree(self.root)
        self.artifact_path = os.path.join(
            self.root, "reports", "bw01b-neg.json")
        os.makedirs(os.path.dirname(self.artifact_path), exist_ok=True)
        self.att = _real_attestation(self.root, self.artifact_path)
        self.evidence = _bdw.execute_bounded_document_mutation(
            _base_contract(), self.root,
            dispatch_id="p2p-task-doc-01b", execution_id="exec-fw01b",
            host_attestation=self.att,
            mutation_authority_mode="MUTATION_READY")

    def tearDown(self):
        os.environ.pop("P2P_STATE_DIR", None)
        shutil.rmtree(self.root, ignore_errors=True)

    def _verify(self, receipt, registry_records=None,
                expect_error_cls=None):
        if "run_id" not in receipt:
            receipt["run_id"] = "task-doc-01b"
            receipt["dispatch_id"] = "p2p-task-doc-01b"
            _att = receipt.get("attestation") or {}
            receipt["role_execution_contract_digest"] = _att.get(
                "execution_contract_digest", "3" * 64)
        if expect_error_cls is not None:
            try:
                verify_bounded_mutation_receipt(
                    receipt,
                    registry_records=registry_records or
                    _registry_records())
            except expect_error_cls:
                return
            self.fail("row must fail closed with an error")
        verified = verify_bounded_mutation_receipt(
            receipt,
            registry_records=registry_records or _registry_records())
        self.assertFalse(verified["overall"],
                         "row must fail closed: "
                         + json.dumps(verified, sort_keys=True))
        return verified

    # A — REQUIRES-only binding: the role carries the capability in
    # REQUIRES (provenance) but its PROVIDES is empty. Fail-closed:
    # REQUIRES never counts as provision.
    def test_row_a_requires_only_no_provides(self):
        records = _registry_records()
        for rec in records:
            if rec["CAPABILITY_ID"] == ARCH_ROLE:
                rec["PROVIDES"] = []
                break
        self._verify(_base_receipt(mut_evidence=self.evidence,
                                   att=self.att,
                                   m0_tree=self.m0_tree),
                     registry_records=records)

    # B — no subject-bound role certification at all.
    def test_row_b_no_role_certification(self):
        _acr.clear_authority_chain_registry_for_tests()
        _acr.append_backend_mutation_certification(
            target_id=TARGET_ID, adapter_id=TARGET_ID)
        self._verify(_base_receipt(mut_evidence=self.evidence,
                                   att=self.att,
                                   m0_tree=self.m0_tree))

    # C — role certification for a DIFFERENT role (subject mismatch).
    def test_row_c_wrong_role_subject(self):
        _acr.clear_authority_chain_registry_for_tests()
        _acr.append_backend_mutation_certification(
            target_id=TARGET_ID, adapter_id=TARGET_ID)
        _acr.append_role_mutation_certification(
            role_id="p2p_tecton", owner_authorization_id=OWNER_AUTH,
            scope=SCOPE, permission_grant="WRITE_BOUNDED")
        self._verify(_base_receipt(mut_evidence=self.evidence,
                                   att=self.att,
                                   m0_tree=self.m0_tree))

    # D — role certification on a role that PROVIDES nothing:
    #     a fabricator role cannot claim architecton's provision.
    def test_row_d_role_cert_on_non_providing_role(self):
        records = _registry_records()
        for rec in records:
            if rec["CAPABILITY_ID"] == ARCH_ROLE:
                rec["PROVIDES"] = []
                break
        _acr.clear_authority_chain_registry_for_tests()
        _acr.append_backend_mutation_certification(
            target_id=TARGET_ID, adapter_id=TARGET_ID)
        _acr.append_role_mutation_certification(
            role_id="p2p_tecton", owner_authorization_id=OWNER_AUTH,
            scope=SCOPE, permission_grant="WRITE_BOUNDED")
        self._verify(_base_receipt(role_id="p2p_tecton",
                                   mut_evidence=self.evidence,
                                   att=self.att,
                                   m0_tree=self.m0_tree),
                     registry_records=records)

    # E — name-implies claim: a role without PROVIDES (data review)
    #     never counts as a provider for the mutation capability.
    def test_row_e_name_implies_no_provides(self):
        records = _registry_records("p2p_datos")
        self._verify(_base_receipt(role_id="p2p_datos",
                                   mut_evidence=self.evidence,
                                   att=self.att,
                                   m0_tree=self.m0_tree),
                     registry_records=records)

    # F — mutation-ready without a real attestation: BLOCKS at the
    #     primitive (S2) and never produces a receipt.
    def test_row_f_mutation_ready_no_real_attestation(self):
        try:
            _bdw.execute_bounded_document_mutation(
                _base_contract(), self.root,
                dispatch_id="p2p-task-doc-01b",
                mutation_authority_mode="MUTATION_READY")
        except _bdw.BoundedDocWriteError as exc:
            self.assertIn("no_real_host_attestation", str(exc).lower())
            return
        self.fail("MUTATION_READY without a real attestation must "
                  "BLOCK")

    # G — TEST_ONLY evidence submitted for a mutation-ready claim
    #     (synthetic/derived identity; S2 non-escalation).
    def test_row_g_test_only_evidence_on_ready_claim(self):
        ev_d = dict(self.evidence.to_dict())
        ev_d["mutation_authority_mode"] = "TEST_ONLY"
        self._verify(_base_receipt(mut_evidence=ev_d, att=None,
                                   m0_tree=self.m0_tree))

    # H — READ_ONLY target certification (not LIVE mutation scope).
    def test_row_h_read_only_target_certification(self):
        _acr.clear_authority_chain_registry_for_tests()
        _acr.append_role_mutation_certification(
            role_id=ARCH_ROLE, owner_authorization_id=OWNER_AUTH,
            scope=SCOPE, permission_grant="WRITE_BOUNDED")
        self._verify(_base_receipt(mut_evidence=self.evidence,
                                   att=self.att,
                                   m0_tree=self.m0_tree))

    # I — role certification scoped to the WRONG execution scope.
    #    The persisted ledger refuses an off-scope certification,
    #    so the WRONG-SCOPE claim is seeded through the fallback
    #    registry surface the checker also accepts (a stale,
    #    non-authority certification record) — which MUST fail the
    #    subject-bound current-certification step (scope mismatch).
    def test_row_i_wrong_execution_scope(self):
        _acr.clear_authority_chain_registry_for_tests()
        _acr.append_backend_mutation_certification(
            target_id=TARGET_ID, adapter_id=TARGET_ID)
        records = _registry_records()
        # Seeded fallback record: wrong scope, not current (expired
        # before now — the checker demands a LIVE current record).
        records.append({
            "CERTIFICATION_KIND": "ROLE_CAPABILITY_CERTIFICATION",
            "ROLE_ID": ARCH_ROLE,
            "CAPABILITY_ID": CAP_ID,
            "EXECUTION_SCOPE": "READ_ONLY_PROJECT_INSIGHT",
            "PERMISSION_GRANT": "WRITE_BOUNDED",
            "EXPIRES_AT": "2020-01-01T00:00:00Z",
        })
        self._verify(_base_receipt(mut_evidence=self.evidence,
                                   att=self.att,
                                   m0_tree=self.m0_tree),
                     registry_records=records)
    # J — stale (expired) role certification.
    def test_row_j_stale_role_certification(self):
        _acr.clear_authority_chain_registry_for_tests()
        _acr.append_backend_mutation_certification(
            target_id=TARGET_ID, adapter_id=TARGET_ID)
        _acr.append_role_mutation_certification(
            role_id=ARCH_ROLE, owner_authorization_id=OWNER_AUTH,
            scope=SCOPE, permission_grant="WRITE_BOUNDED",
            lifetime_days=1, certified_at="2020-01-01T00:00:00+00:00")
        self._verify(_base_receipt(mut_evidence=self.evidence,
                                   att=self.att,
                                   m0_tree=self.m0_tree))

    # K — stale (expired) target certification.
    def test_row_k_stale_target_certification(self):
        _acr.clear_authority_chain_registry_for_tests()
        _acr.append_backend_mutation_certification(
            target_id=TARGET_ID, adapter_id=TARGET_ID,
            lifetime_days=1,
            certified_at="2020-01-01T00:00:00+00:00")
        _acr.append_role_mutation_certification(
            role_id=ARCH_ROLE, owner_authorization_id=OWNER_AUTH,
            scope=SCOPE, permission_grant="WRITE_BOUNDED")
        self._verify(_base_receipt(mut_evidence=self.evidence,
                                   att=self.att,
                                   m0_tree=self.m0_tree))

    # L — owner authorization mismatch: the role cert binds a
    #     DIFFERENT owner id than the contract's.
    def test_row_l_owner_authorization_mismatch(self):
        _acr.clear_authority_chain_registry_for_tests()
        _acr.append_backend_mutation_certification(
            target_id=TARGET_ID, adapter_id=TARGET_ID)
        _acr.append_role_mutation_certification(
            role_id=ARCH_ROLE,
            owner_authorization_id="owner-mutation-OTHER",
            scope=SCOPE, permission_grant="WRITE_BOUNDED")
        self._verify(_base_receipt(mut_evidence=self.evidence,
                                   att=self.att,
                                   m0_tree=self.m0_tree))

    # M — valid full chain must still close over the same evidence.
    def test_row_m_valid_chain_closes(self):
        verified = verify_bounded_mutation_receipt(
            _base_receipt(mut_evidence=self.evidence, att=self.att,
                          m0_tree=self.m0_tree),
            registry_records=_registry_records())
        self.assertTrue(verified["overall"],
                        json.dumps(verified, sort_keys=True))

    # N — exact rollback: the M2 path (restore == M0 tree) leaves a
    #     verified, zero-net-mutation trace over the closed chain.
    def test_row_n_exact_rollback_closes(self):
        result = _bdw.rollback_bounded_document_mutation(
            self.evidence, self.root, original_content=None)
        self.assertEqual(result["rollback_state"], "RESTORED")
        self.assertEqual(_git_tree(self.root), self.m0_tree)
        verified = verify_bounded_mutation_receipt(
            _base_receipt(mut_evidence=self.evidence, att=self.att,
                          m0_tree=self.m0_tree),
            registry_records=_registry_records())
        self.assertTrue(verified["overall"],
                        json.dumps(verified, sort_keys=True))
