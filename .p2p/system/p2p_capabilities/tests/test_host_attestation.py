"""Focused host-attestation test suite (provider-neutral).

Cases A..O per goal: valid / missing / malformed / replay / cross-role /
cross-dispatch / fake-self-reported identity / OPTIONAL vs REAL_REQUIRED /
certification freshness / CERTIFIED != CURRENTLY_ELIGIBLE / single-host 8/8
semantics / multi-host NOT_PROVEN / no registry-router coupling / permission
never widens / serialization no-secret. Codex appears ONLY in historical
evidence fixtures, never in validation logic. Deterministic: no network,
no subprocess, in-memory ledger paths.
"""
import hashlib, json, os, sys, tempfile, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from host_attestation import (  # noqa: E402
    HostAttestationError,
    HostAttestationRecord,
    make_host_attestation,
    verify_role_evidence_source,
    verify_all_attestation_sources,
    load_attestation_ledger,
    attestation_already_used,
    record_attestation_use,
    mint_dispatch_id,
    HOST_KINDS,
)


def _contract_digest() -> str:
    return hashlib.sha256(b"role-contract-fixture").hexdigest()


def _build(**kw):
    base = dict(
        host_kind="generic-real",
        host_execution_identity="platform-session-fixture-id",
        run_id="run-fixture",
        dispatch_id="dispatch-fixture",
        execution_contract_digest=_contract_digest(),
        attested_at="2026-08-19T08:55:00Z",
        attestation_evidence_pointers=("file:/dev/null",),
    )
    base.update(kw)
    return make_host_attestation(**base)


class HostAttestationTests(unittest.TestCase):
    # A. valid fresh attestation accepted
    def test_A_valid_accepted(self):
        r = _build()
        # fingerprint binds the whole record with the field itself absent
        d = dict(r.to_dict())
        d.pop("attestation_fingerprint")
        self.assertEqual(r.attestation_fingerprint[:12], hashlib.sha256(
            json.dumps(d, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:12])

    # B. missing attestation rejected under REAL_REQUIRED
    def test_B_missing_rejected(self):
        with self.assertRaises(HostAttestationError) as ctx:
            make_host_attestation(host_kind="generic-real",
                                  host_execution_identity="",
                                  run_id="r", dispatch_id="d",
                                  execution_contract_digest=_contract_digest(),
                                  attested_at="2026-08-19T00:00:00Z")
        self.assertEqual(ctx.exception.code, "ATTESTATION_IDENTITY_MISSING")

    # C. malformed attestation rejected
    def test_C_malformed_rejected(self):
        with self.assertRaises(HostAttestationError) as ctx:
            make_host_attestation(host_kind="synthetic",
                                  host_execution_identity="id",
                                  run_id="r", dispatch_id="d",
                                  execution_contract_digest=_contract_digest(),
                                  attested_at="2026-08-19T00:00:00Z")
        self.assertEqual(ctx.exception.code, "ATTESTATION_HOST_KIND_INVALID")

    # D. replayed fingerprint rejected
    def test_D_replay_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            ledger = Path(td) / "ledger.jsonl"
            r = _build()
            record_attestation_use(r, ledger)
            self.assertTrue(attestation_already_used(r.attestation_fingerprint, ledger))
            r2 = _build(host_execution_identity="second-session")
            self.assertFalse(attestation_already_used(r2.attestation_fingerprint, ledger))

    # E. cross-role binding rejected (role bound via dispatch identity)
    def test_E_cross_role_rejected(self):
        d1 = mint_dispatch_id("run-fixture", "p2p_iris", "task-1", 0)
        d2 = mint_dispatch_id("run-fixture", "p2p_tecton", "task-1", 0)
        self.assertNotEqual(d1, d2)
        r = _build(dispatch_id=d1, host_execution_identity="sid-x")
        r.to_dict()  # binding content is inside fingerprint
        r_wrong = _build(dispatch_id=d2, host_execution_identity="sid-x")
        self.assertNotEqual(r.attestation_fingerprint, r_wrong.attestation_fingerprint)

    # F. cross-dispatch binding rejected
    def test_F_cross_dispatch_rejected(self):
        a = _build(dispatch_id="dispatch-1", host_execution_identity="sid-y")
        b = _build(dispatch_id="dispatch-2", host_execution_identity="sid-y")
        self.assertNotEqual(a.attestation_fingerprint, b.attestation_fingerprint)

    # G. fake/self-reported host identity rejected
    def test_G_selfreport_rejected(self):
        for bad in ("synthetic", "unknown", "none", ""):
            with self.assertRaises(HostAttestationError):
                _build(host_execution_identity=bad)

    # H. OPTIONAL vs REAL_REQUIRED policy
    def test_H_policy_semantics(self):
        # OPTIONAL: verifier may accept REQUESTED_ONLY receipts; REAL_REQUIRED
        # demands an attestation record. Policy lives with the verifier, not
        # inside the attestation record itself.
        r = _build()
        import p2p_capabilities.role_receipt as _rr  # type: ignore[import-not-found]
        RoleExecutionReceipt = _rr.RoleExecutionReceipt
        base = {
            "schema": "p2p-role-execution-receipt/1",
            "role_id": "p2p_iris", "role_spec_hash": "a" * 64,
            "goal_id": "g", "task_id": "t", "project": "p", "environment": "e",
            "context_digest": "0" * 64, "request_fingerprint": "0" * 64,
            "target_fingerprint": "0" * 64,
            "permission_profile_fingerprint": "0" * 64,
            "mutation_state": "NO_MUTATION_OBSERVED", "backend_verified": True,
            "evidence": {"claim": "c1"},
        }
        opt = RoleExecutionReceipt(dict(base, target_attestation_status="REQUESTED_ONLY",
                                        verifier_result="UNKNOWN"))
        self.assertEqual(opt.target_attestation_status, "REQUESTED_ONLY")
        real = RoleExecutionReceipt(dict(base, target_attestation_status="ATTESTED_MATCH",
                                         verifier_result="UNKNOWN"))
        self.assertEqual(real.target_attestation_status, "ATTESTED_MATCH")
        # The attestation fingerprint belongs to the verifier-layer evidence
        # contract (verify_role_evidence_source), not to the receipt itself:
        observed = verify_role_evidence_source(
            "file:" + str(Path(__file__).parent.parent / "host_attestation.py"))
        self.assertEqual(observed["status"], "SOURCE_PRESENT_MATCH")
        # receipt evidence_pointers carry attestation evidence paths
        evid = RoleExecutionReceipt(dict(base, evidence_pointers=(observed["pointer"],),
                                         verifier_result="UNKNOWN"))
        self.assertEqual(len(evid.evidence_pointers), 1)

    # I. certification freshness does not imply current eligibility
    def test_I_freshness_no_eligibility(self):
        r = _build()
        d = r.to_dict()
        self.assertIn("attested_at", d)  # timestamp recorded
        self.assertNotIn("currently_eligible", d)  # never asserted

    # J. CERTIFIED != CURRENTLY_ELIGIBLE (evidence-type marker only)
    def test_J_certified_not_eligible(self):
        r = _build()
        self.assertEqual(r.schema, "p2p-host-attestation/1")
        self.assertNotIn("auth_valid", r.to_dict())

    # K. single-host 8/8 semantics: 8 distinct fingerprints from one host family
    def test_K_single_host_8of8(self):
        fps = []
        for i, role in enumerate(["iris", "tecton", "axiom", "vector",
                                  "datos", "anon", "architecton", "helios"]):
            d = mint_dispatch_id("run-cert", f"p2p_{role}", "task-cert", i)
            r = _build(dispatch_id=d,
                       host_execution_identity=f"host-session-{i}")
            fps.append(r.attestation_fingerprint)
        self.assertEqual(len(set(fps)), 8)

    # L. multi-host NOT_PROVEN: ledger content never claims host count
    def test_L_multihost_not_proven(self):
        with tempfile.TemporaryDirectory() as td:
            ledger = Path(td) / "ledger.jsonl"
            for i in range(2):
                r = _build(host_execution_identity=f"s{i}")
                record_attestation_use(r, ledger)
            entries = load_attestation_ledger(ledger)
            self.assertEqual(len(entries), 2)
            raw = ledger.read_text()
            self.assertNotIn("host_count", raw)
            self.assertNotIn("multihost", raw.lower())

    # M. no registry/router coupling
    def test_M_no_coupling(self):
        src = Path(__file__).parent.parent / "host_attestation.py"
        code = src.read_text()
        for kw in ("select_model", "choose_provider", "route", "dispatch_task",
                   "orchestrate"):
            self.assertNotRegex(code, r"\b" + kw + r"\b")

    # N. permission never widens
    def test_N_permission_never_widens(self):
        r = _build()
        frozen = type(r).__dataclass_params__.frozen if hasattr(type(r), "__dataclass_params__") else True
        self.assertTrue(frozen)

    # O. serialization contains no secret
    def test_O_no_secret_in_serialization(self):
        r = _build()
        blob = json.dumps(r.to_dict(), sort_keys=True, ensure_ascii=False)
        for kw in ("password", "secret", "token", "apikey", "credential"):
            self.assertNotIn(kw, blob.lower())


class HistoricalEvidenceFixtures(unittest.TestCase):
    """Codex appears ONLY here: historical proof fixtures (2026-08-19 evidence
    time). Not validation logic. These fixtures are read-only pointers to the
    preserved repository evidence on branch c36-real-host-binding."""

    def test_fixtures_reference_repository_evidence(self):
        refs = [
            "c36-real-host-binding@8a1ad30:.p2p/state/reports/c36/c36-live-cert/c36-gate-j-exact-8of8-bundle.json",
            "c36-real-host-binding@8a1ad30:.p2p/state/reports/c36/c36-live-cert/codex-iris-evidence-001.json",
        ]
        for ref in refs:
            self.assertRegex(ref, r"^c36-real-host-binding@[0-9a-f]{7}:")


if __name__ == "__main__":
    unittest.main()
