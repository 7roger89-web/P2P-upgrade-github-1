"""AERG provider-neutral falsification matrix and contract tests."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
import inspect
import pathlib
import sys
import unittest

_HERE = pathlib.Path(__file__).resolve()
_SYSTEM = _HERE.parents[2]
if str(_SYSTEM) not in sys.path:
    sys.path.insert(0, str(_SYSTEM))

from p2p_capabilities import quality_intelligence as qi
from p2p_capabilities.aerg_engine import AERGEngine
from p2p_capabilities.aerg_model import ClaimExpectation, EvidenceObservation, SubjectBinding


NOW = "2026-08-24T12:00:00+00:00"
CURRENT_COMMIT = "a" * 40
OLD_COMMIT = "b" * 40
TREE = "c" * 64
ARTIFACT_A = "d" * 64
ARTIFACT_B = "e" * 64


def subject() -> SubjectBinding:
    return SubjectBinding(
        subject_id="project:current/task:aerg",
        source_commit=CURRENT_COMMIT,
        tree_sha256=TREE,
        path="tests/fixture.py",
    )


def observation(**overrides) -> EvidenceObservation:
    values = {
        "evidence_ref": "evidence/aerg-proof.json",
        "source": "tool:aerg",
        "origin": "TOOL_OUTPUT",
        "observed_at": "2026-08-24T11:59:55+00:00",
        "fingerprint": "f" * 64,
        "subject_id": subject().subject_id,
        "source_commit": CURRENT_COMMIT,
        "tree_sha256": TREE,
        "observed_status": "PASS",
        "exit_code": 0,
        "mutation_state": "UNCHANGED",
        "live": True,
        "execution_scope": "EXTERNAL",
    }
    values.update(overrides)
    return EvidenceObservation(**values)


class AERGMatrixTests(unittest.TestCase):
    def evaluate(self, statement: str, *, expectation=None, evidence=None):
        engine = AERGEngine(subject(), now=NOW)
        claim = engine.create_claim(statement, expectation=expectation)
        if evidence is not None:
            self.assertTrue(engine.add_evidence(claim.claim_id, evidence))
        return engine.evaluate_claim(claim.claim_id)

    def test_a_to_z_matrix(self):
        cases = {
            "A": (self.evaluate("tests PASS"), "INSUFFICIENT"),
            "B": (self.evaluate("tests PASS", evidence=observation()), "SUPPORTED"),
            "C": (self.evaluate("tests PASS", evidence=observation(source_commit=OLD_COMMIT)), "STALE"),
            "D": (self.evaluate("tests PASS", evidence=observation(subject_id="project:other/task:aerg")), "SUBJECT_MISMATCH"),
            "E": (self.evaluate("artifact SHA = A", expectation=ClaimExpectation(expected_artifact_sha256=ARTIFACT_A), evidence=observation(artifact_sha256=ARTIFACT_B)), "CONTRADICTED"),
            "F": (self.evaluate("source commit A", expectation=ClaimExpectation(expected_source_commit=CURRENT_COMMIT), evidence=observation(source_commit=OLD_COMMIT)), "CONTRADICTED"),
            "G": (self.evaluate("Doctor HEALTHY", evidence=observation(observed_status="PASS", doctor_status="UNHEALTHY")), "CONTRADICTED"),
            "H": (self.evaluate("tests PASS", evidence=observation(exit_code=2)), "CONTRADICTED"),
            "I": (self.evaluate("external proof", expectation=ClaimExpectation(requires_external=True), evidence=observation(external_id=None)), "INSUFFICIENT"),
            "J": (self.evaluate("live proof", expectation=ClaimExpectation(requires_live=True), evidence=observation(live=False, fixture=True)), "INSUFFICIENT"),
            "K": (self.evaluate("live proof", expectation=ClaimExpectation(requires_live=True), evidence=observation(mock=True)), "INSUFFICIENT"),
            "L": (self.evaluate("external child", expectation=ClaimExpectation(requires_external=True), evidence=observation(execution_scope="INTERNAL", external_id="child-1")), "INSUFFICIENT"),
            "M": (self.evaluate("tests PASS", evidence=observation(observed_status="NOT_RUN", exit_code=None)), "INSUFFICIENT"),
            "N": (self.evaluate("tests VERIFIED", evidence=observation(observed_status="UNKNOWN", exit_code=None)), "INSUFFICIENT"),
            "O": (self.evaluate("Doctor HEALTHY", evidence=observation(observed_status="PASS", doctor_status="WARN")), "INSUFFICIENT"),
            "P": (self.evaluate("independently verified", expectation=ClaimExpectation(requires_independent=True), evidence=observation(producer_identity="executor", verifier_identity="executor", independent_verifier_status="VERIFIED", verifier_evidence_ref="evidence/aerg-proof.json")), "INSUFFICIENT"),
            "Q": (self.evaluate("tests PASS", evidence=observation()), "SUPPORTED"),
            "R": (self.evaluate("tests PASS", evidence=observation()), "SUPPORTED"),
            "S": (self.evaluate("tests PASS", evidence=observation(origin="MODEL_INFERENCE", exit_code=None)), "INSUFFICIENT"),
            "T": (self.evaluate("original claim: tests PASS", evidence=observation()), "SUPPORTED"),
            "U": (self.evaluate("tests PASS", evidence=observation()), "SUPPORTED"),
            "V": (self.evaluate("tests PASS", expectation=ClaimExpectation(required_assurance="DETERMINISTIC"), evidence=observation(exit_code=None, observed_status="PASS")), "INSUFFICIENT"),
            "W": (self.evaluate("tests PASS", evidence=observation(producer_identity="executor", verifier_identity="executor")), "SUPPORTED"),
            "X": (self.evaluate("tests PASS", evidence=observation()), "SUPPORTED"),
            "Y": (self.evaluate("tests PASS", evidence=observation()), "SUPPORTED"),
            "Z": (self.evaluate("tests PASS", evidence=observation(observed_status="PASS", exit_code=1)), "CONTRADICTED"),
        }
        self.assertEqual(set(cases), set("ABCDEFGHIJKLMNOPQRSTUVWXYZ"))
        for case_id, (result, expected) in cases.items():
            with self.subTest(case=case_id):
                self.assertEqual(result.decision, expected)

    def test_claim_id_is_deterministic(self):
        left = AERGEngine(subject(), now=NOW).create_claim("tests PASS")
        right = AERGEngine(subject(), now="2026-08-24T12:00:59+00:00").create_claim("tests PASS")
        self.assertEqual(left.claim_id, right.claim_id)

    def test_claim_and_provenance_are_preserved(self):
        claim_text = "original claim: no files changed"
        result = self.evaluate(claim_text, evidence=observation(mutation_state="MUTATED", changed_paths=("src/a.py",)))
        self.assertEqual(result.original_claim, claim_text)
        self.assertEqual(result.decision, "CONTRADICTED")
        self.assertEqual(result.contradiction, "CONTRADICTED")
        self.assertIn("MUTATION_CONTRADICTS_NO_MUTATION", result.reasons)
        contract = result.to_dict()
        self.assertEqual(contract["original_claim"], claim_text)
        self.assertEqual(contract["evidence_refs"], ["evidence/aerg-proof.json"])
        self.assertEqual(contract["can_promote"], False)
        self.assertEqual(contract["can_release"], False)
        self.assertEqual(contract["can_deploy"], False)

    def test_contradiction_precedes_stale_and_insufficient(self):
        result = self.evaluate(
            "tests PASS",
            expectation=ClaimExpectation(expected_source_commit=CURRENT_COMMIT),
            evidence=observation(source_commit=OLD_COMMIT, exit_code=1),
        )
        self.assertEqual(result.decision, "CONTRADICTED")
        self.assertEqual(result.contradiction, "CONTRADICTED")

    def test_current_evidence_claim_uses_existing_contract(self):
        result = self.evaluate("tests PASS", evidence=observation())
        self.assertEqual(result.evidence_claims[0].effective_status(), "VERIFIED")
        self.assertEqual(result.evidence_claims[0].as_contract()["STATUS"], "VERIFIED")

    def test_no_provider_specific_core_branching(self):
        source = inspect.getsource(AERGEngine)
        for provider_name in ("Manus", "Codex", "Claude", "Gemini"):
            self.assertNotIn(provider_name, source)

    def test_no_second_control_plane_or_persistence_api(self):
        source = inspect.getsource(AERGEngine)
        for forbidden in ("sqlite", "event_bus", "scheduler", "WorkQueue", "LaneRegistry", "promote(", "release(", "deploy("):
            self.assertNotIn(forbidden, source)
        engine = AERGEngine(subject(), now=NOW)
        self.assertFalse(hasattr(engine, "persist"))

    def test_executor_evidence_never_widens_authority(self):
        result = self.evaluate(
            "tests PASS",
            evidence=observation(
                producer_identity="executor",
                verifier_identity="executor",
                independent_verifier_status="VERIFIED",
                verifier_evidence_ref="evidence/aerg-proof.json"),
        )
        self.assertEqual(result.authority, "NOT_PROVEN")
        self.assertFalse(result.to_dict()["can_promote"])
        self.assertFalse(result.to_dict()["can_release"])
        self.assertFalse(result.to_dict()["can_deploy"])


class AERGQualityIntegrationTests(unittest.TestCase):
    def test_fw01_uses_existing_post_execution_aerg_seam(self):
        from p2p_capabilities import p2p_fw01_loop

        source = inspect.getsource(p2p_fw01_loop)
        self.assertIn("AERGEngine", source)
        self.assertIn("git_source_commit", source)
        self.assertIn("aerg_result", source)
        self.assertLess(source.index("self.loop.step()"), source.index("AERGEngine"))

    def test_quality_intelligence_rejects_contradiction(self):
        result = AERGEngine(subject(), now=NOW)
        claim = result.create_claim("tests PASS")
        result.add_evidence(claim.claim_id, observation(exit_code=1))
        verdict = qi.build_quality_verdict(
            "SUCCESS",
            required_eval_results={},
            aerg_result=result.evaluate_claim(claim.claim_id).as_quality_input(),
        )
        self.assertEqual(verdict["quality_status"], "QUALITY_REJECTED")
        self.assertFalse(verdict["checkpoint_allowed"])

    def test_quality_intelligence_does_not_upgrade_unknown(self):
        result = AERGEngine(subject(), now=NOW)
        claim = result.create_claim("tests PASS")
        verdict = qi.build_quality_verdict(
            "SUCCESS",
            required_eval_results={},
            aerg_result=result.evaluate_claim(claim.claim_id).as_quality_input(),
        )
        self.assertEqual(verdict["quality_status"], "QUALITY_REJECTED")
        self.assertFalse(verdict["checkpoint_allowed"])

    def test_existing_quality_contract_remains_valid_without_aerg(self):
        verdict = qi.build_quality_verdict("SUCCESS", required_eval_results={})
        self.assertEqual(verdict["quality_status"], "QUALITY_VERIFIED")
        self.assertTrue(verdict["checkpoint_allowed"])


if __name__ == "__main__":
    unittest.main()
