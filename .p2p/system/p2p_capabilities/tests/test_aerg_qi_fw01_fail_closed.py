# -*- coding: utf-8 -*-
"""Regressions for the AERG -> QI -> FW01 checkpoint boundary.

These tests deliberately exercise the current production surfaces before the
repair.  The QI matrix proves that a required non-proof status must not be
treated as proof.  The FW01 cases use the real step path and an actual AERG
result (or an absent result) while the compatibility callable omits the
optional ``aerg_result`` parameter.
"""

from datetime import datetime, timedelta, timezone
from functools import wraps
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_SYSTEM = _HERE.parents[1]
if str(_SYSTEM) not in sys.path:
    sys.path.insert(0, str(_SYSTEM))

import p2p_capabilities.p2p_fw01_loop as fw01  # noqa: E402
import p2p_capabilities.quality_intelligence as qi  # noqa: E402
from p2p_capabilities.aerg_engine import AERGEngine  # noqa: E402
from p2p_capabilities.aerg_model import (  # noqa: E402
    ClaimExpectation,
    EvidenceObservation,
    SubjectBinding,
)
from test_checkpoint_quality_gate import (  # noqa: E402
    _QAMock,
    _build_loop,
    _last_checkpoint,
    _make_composition_pass,
    _patch_qa,
    _restore_composition,
    _restore_qa,
)


REAL_PROJECT = _HERE.parents[3]


def _make_repo_local_root() -> Path:
    """Create an isolated Git worktree under this repository's .tmp root."""
    temp_root = Path(tempfile.mkdtemp(
        prefix="aerg_qi_fw01_", dir=str(REAL_PROJECT / ".tmp")))
    subprocess.run(
        ["git", "-C", str(REAL_PROJECT), "worktree", "add", "--detach",
         str(temp_root), "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    (temp_root / ".p2p" / "system").mkdir(parents=True, exist_ok=True)
    (temp_root / ".p2p" / "state").mkdir(parents=True, exist_ok=True)
    return temp_root


def _remove_repo_local_root(root: Path) -> None:
    subprocess.run(
        ["git", "-C", str(REAL_PROJECT), "worktree", "remove", "--force",
         str(root)],
        capture_output=True,
        text=True,
    )
    shutil.rmtree(root, ignore_errors=True)


def _actual_aerg_result(*, observed_at=None, subject_id=None,
                        observed_status="PASS", exit_code=0,
                        add_evidence=True):
    now = datetime.now(timezone.utc)
    subject = SubjectBinding(
        subject_id="task:actual-aerg",
        source_commit="a" * 40)
    engine = AERGEngine(subject, now=now.isoformat())
    claim = engine.create_claim(
        "Execution outcome is VERIFIED",
        expectation=ClaimExpectation(
            expected_status="VERIFIED",
            required_assurance="MECHANICAL"))
    if add_evidence:
        observation = EvidenceObservation(
            evidence_ref="actual-aerg-evidence",
            source="fw01.goal-state",
            origin="RUNTIME_EVIDENCE",
            observed_at=(observed_at or now.isoformat()),
            fingerprint="b" * 64,
            subject_id=subject_id or subject.subject_id,
            source_commit=subject.source_commit,
            observed_status=observed_status,
            exit_code=exit_code,
            mutation_state="UNCHANGED")
        engine.add_evidence(claim.claim_id, observation)
    return engine.evaluate_claim(claim.claim_id).as_quality_input()


class RequiredEvaluationFailClosedTests(unittest.TestCase):
    def _verdict(self, result: str, *, optional=False):
        return qi.build_quality_verdict(
            "SUCCESS",
            required_eval_results={"eval": result},
            optional_eval_results={"optional": "WARN"} if optional else None,
            declared_required_evals={"eval": {}})

    def test_only_explicit_proof_statuses_allow_required_evaluation(self):
        for result in ("PASS", "VERIFIED", "VERIFIED_IMPLEMENTED"):
            with self.subTest(result=result):
                verdict = self._verdict(result)
                self.assertEqual(verdict["quality_status"],
                                 "QUALITY_VERIFIED", verdict)
                self.assertTrue(verdict["checkpoint_allowed"], verdict)

    def test_required_nonproof_and_unknown_statuses_fail_closed(self):
        cases = {
            "STALE": "STALE_EVIDENCE",
            "EXPIRED": "STALE_EVIDENCE",
            "WARN": "MISSING_REQUIRED_EVIDENCE",
            "WARNING": "MISSING_REQUIRED_EVIDENCE",
            "UNKNOWN": "MISSING_REQUIRED_EVIDENCE",
            "NOT_RUN": "MISSING_REQUIRED_EVIDENCE",
            "NOT_AVAILABLE": "EVAL_NOT_AVAILABLE",
            "UNAVAILABLE": "EVAL_NOT_AVAILABLE",
            "SKIPPED": "MISSING_REQUIRED_EVIDENCE",
            "INCOMPLETE": "MISSING_REQUIRED_EVIDENCE",
            "NOT_VERIFIED": "MISSING_REQUIRED_EVIDENCE",
            "UNRECOGNIZED_STATUS": "MISSING_REQUIRED_EVIDENCE",
        }
        for result, failure in cases.items():
            with self.subTest(result=result):
                verdict = self._verdict(result)
                self.assertNotEqual(verdict["quality_status"],
                                    "QUALITY_VERIFIED", verdict)
                self.assertFalse(verdict["checkpoint_allowed"], verdict)
                self.assertIn(failure, verdict["quality_failures"], verdict)

    def test_optional_nonproof_evaluation_does_not_become_required(self):
        verdict = qi.build_quality_verdict(
            "SUCCESS",
            required_eval_results={},
            optional_eval_results={"optional": "WARN"},
            declared_required_evals={})
        self.assertEqual(verdict["quality_status"], "QUALITY_VERIFIED",
                         verdict)
        self.assertTrue(verdict["checkpoint_allowed"], verdict)

    def test_actual_aerg_result_uses_existing_qi_failure_vocabulary(self):
        now = datetime.now(timezone.utc)
        cases = {
            "STALE": (
                _actual_aerg_result(
                    observed_at=(now - timedelta(seconds=360)).isoformat()),
                "QUALITY_UNKNOWN",
                "STALE_EVIDENCE",
            ),
            "CONTRADICTED": (
                _actual_aerg_result(exit_code=1),
                "QUALITY_REJECTED",
                "QUALITY_CONFLICT",
            ),
            "SUBJECT_MISMATCH": (
                _actual_aerg_result(subject_id="task:other-subject"),
                "QUALITY_UNKNOWN",
                "CERTIFICATION_SCOPE_MISMATCH",
            ),
            "INSUFFICIENT": (
                _actual_aerg_result(add_evidence=False),
                "QUALITY_REJECTED",
                "MISSING_REQUIRED_EVIDENCE",
            ),
        }
        for expected_decision, (aerg_result, quality_status, failure) in cases.items():
            with self.subTest(expected_decision=expected_decision):
                verdict = qi.build_quality_verdict(
                    "SUCCESS",
                    required_eval_results={},
                    declared_required_evals={},
                    aerg_result=aerg_result,
                )
                self.assertEqual(aerg_result["decision"], expected_decision,
                                 aerg_result)
                self.assertEqual(verdict["quality_status"], quality_status,
                                 verdict)
                self.assertIn(failure, verdict["quality_failures"], verdict)
                self.assertFalse(verdict["checkpoint_allowed"], verdict)


class Fw01ProductionQualityCheckpointTests(unittest.TestCase):
    def test_real_production_qi_fresh_execution_reaches_checkpoint(self):
        """Bind the real FW01 -> AERG -> QI -> checkpoint path.

        The wrapper calls the production QI implementation and records its
        actual verdict only to make the RED state observable.  The expected
        tuple intentionally includes the canonical execution projection so
        the pre-repair failure reports both the status mismatch and the
        resulting durable QUALITY_REVIEW/BLOCKED checkpoint.
        """
        root = _make_repo_local_root()
        composition_original = _make_composition_pass()
        qi_original = qi.build_quality_verdict
        captured = {}

        @wraps(qi_original)
        def observe_qi(*args, **kwargs):
            verdict = qi_original(*args, **kwargs)
            captured["kwargs"] = dict(kwargs)
            captured["verdict"] = dict(verdict)
            return verdict

        qi.build_quality_verdict = observe_qi
        try:
            output = _build_loop(root).step()
            checkpoint = _last_checkpoint(root)
        finally:
            qi.build_quality_verdict = qi_original
            _restore_composition(composition_original)
            _remove_repo_local_root(root)

        aerg_result = captured["kwargs"].get("aerg_result") or {}
        observed = (
            captured["kwargs"].get("execution_status"),
            captured["verdict"].get("quality_status"),
            captured["verdict"].get("checkpoint_allowed"),
            aerg_result.get("decision"),
            aerg_result.get("status"),
            aerg_result.get("freshness"),
            output.get("status"),
            checkpoint.get("verification_state") if checkpoint else None,
            checkpoint.get("loop_status") if checkpoint else None,
        )
        self.assertEqual(
            observed,
            (
                "SUCCESS",
                "QUALITY_VERIFIED",
                True,
                "SUPPORTED",
                "VERIFIED",
                "CURRENT",
                "TASK_DONE_CONTINUE",
                "VERIFIED",
                "CHECKPOINTED",
            ),
        )


class Fw01CompatibilityFailClosedTests(unittest.TestCase):
    def _step_with_compatibility_qi(self, *, stale=False,
                                    source_commit_available=True):
        root = _make_repo_local_root()
        composition_original = _make_composition_pass()
        qa_original = _patch_qa(_QAMock(
            checkpoint_allowed=True,
            quality_status="QUALITY_VERIFIED",
            failures=()))
        now_original = fw01._now_iso
        source_original = qi.git_source_commit
        try:
            if stale:
                old_stamp = (
                    datetime.now(timezone.utc) - timedelta(seconds=360)
                ).isoformat()
                fw01._now_iso = lambda: old_stamp
            if not source_commit_available:
                qi.git_source_commit = lambda project_root: ""
            output = _build_loop(root).step()
            checkpoint = _last_checkpoint(root)
            return output, checkpoint
        finally:
            fw01._now_iso = now_original
            qi.git_source_commit = source_original
            _restore_qa(qa_original)
            _restore_composition(composition_original)
            _remove_repo_local_root(root)

    def test_compatibility_qi_cannot_checkpoint_actual_stale_aerg(self):
        output, checkpoint = self._step_with_compatibility_qi(stale=True)
        self.assertEqual(output.get("status"), "STOP_BLOCKED", output)
        self.assertEqual(output.get("reason"),
                         "QUALITY_REVIEW_REQUIRED", output)
        self.assertEqual(checkpoint["verification_state"], "QUALITY_REVIEW",
                         checkpoint)
        self.assertEqual(checkpoint["loop_status"], "BLOCKED", checkpoint)

    def test_compatibility_qi_cannot_checkpoint_without_actual_aerg(self):
        output, checkpoint = self._step_with_compatibility_qi(
            source_commit_available=False)
        self.assertEqual(output.get("status"), "STOP_BLOCKED", output)
        self.assertEqual(output.get("reason"),
                         "QUALITY_REVIEW_REQUIRED", output)
        self.assertEqual(checkpoint["verification_state"], "QUALITY_REVIEW",
                         checkpoint)
        self.assertEqual(checkpoint["loop_status"], "BLOCKED", checkpoint)

    def test_compatibility_qi_preserves_fresh_actual_aerg_behavior(self):
        output, checkpoint = self._step_with_compatibility_qi()
        self.assertEqual(output.get("status"), "TASK_DONE_CONTINUE", output)
        self.assertEqual(checkpoint["verification_state"], "VERIFIED",
                         checkpoint)
        self.assertEqual(checkpoint["loop_status"], "CHECKPOINTED", checkpoint)

    def test_clamp_blocks_actual_unsafe_aerg_result_shapes(self):
        now = datetime.now(timezone.utc)
        cases = {
            "STALE": _actual_aerg_result(
                observed_at=(now - timedelta(seconds=360)).isoformat()),
            "CONTRADICTED": _actual_aerg_result(exit_code=1),
            "SUBJECT_MISMATCH": _actual_aerg_result(
                subject_id="task:other-subject"),
            "INSUFFICIENT": _actual_aerg_result(add_evidence=False),
        }
        for expected_decision, aerg_result in cases.items():
            with self.subTest(expected_decision=expected_decision):
                self.assertEqual(aerg_result["decision"], expected_decision,
                                 aerg_result)
                clamped = fw01._clamp_quality_verdict_to_aerg(
                    {"quality_status": "QUALITY_VERIFIED",
                     "checkpoint_allowed": True,
                     "quality_failures": ()},
                    aerg_result)
                self.assertFalse(clamped["checkpoint_allowed"], clamped)
                self.assertNotEqual(clamped["quality_status"],
                                    "QUALITY_VERIFIED", clamped)
                self.assertEqual(clamped["aerg_result"], aerg_result)


if __name__ == "__main__":
    raise SystemExit(unittest.main())
