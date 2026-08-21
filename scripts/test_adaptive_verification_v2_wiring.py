import sys
import pathlib
import unittest
from dataclasses import dataclass
from typing import Optional, Tuple, FrozenSet

# Thêm đường dẫn để import từ .p2p/system/p2p_capabilities/
sys.path.append(str(pathlib.Path(__file__).parent.parent / ".p2p" / "system" / "p2p_capabilities"))

from quality_intelligence import plan_verification, VerificationInput, NFR, VerificationPlan

class TestAdaptiveVerificationV2Wiring(unittest.TestCase):
    def test_basic_wiring(self):
        inp = VerificationInput(
            change_class="VALIDATION",
            lifecycle_stage="DEVELOPMENT",
            nfrs=(),
            requested_checks=frozenset(["UNIT"])
        )
        plan = plan_verification(inp)
        self.assertIsInstance(plan, VerificationPlan)
        self.assertIn("L1_TARGETED", plan.levels)

    def test_nfr_applicability_gate(self):
        nfr = NFR(nfr_id="SECURITY_SCAN", requirement="SCAN", applicability="NOT_APPLICABLE")
        inp = VerificationInput(
            change_class="READ_ONLY",
            lifecycle_stage="DEVELOPMENT",
            nfrs=(nfr,),
            requested_checks=frozenset(["SECURITY"])
        )
        plan = plan_verification(inp)
        self.assertNotIn("NFR_APPLICABLE:SECURITY_SCAN", plan.escalation_reasons)
        self.assertIn("NFR_NOT_APPLICABLE:SECURITY_SCAN", plan.deferred)

    def test_hard_nfr_fail_closed(self):
        nfr = NFR(nfr_id="DATA_INTEGRITY", requirement="INTEGRITY", applicability="UNKNOWN", hard_gate=True)
        inp = VerificationInput(
            change_class="CODE_EDIT",
            lifecycle_stage="DEVELOPMENT",
            nfrs=(nfr,),
            requested_checks=frozenset()
        )
        plan = plan_verification(inp)
        self.assertIn("NFR_APPLICABILITY_UNRESOLVED:DATA_INTEGRITY", plan.fail_closed_reasons)

    def test_max_reasoning_does_not_widen_scope(self):
        inp = VerificationInput(
            change_class="READ_ONLY",
            lifecycle_stage="DEVELOPMENT",
            nfrs=(),
            requested_checks=frozenset(["LOAD"])
        )
        plan = plan_verification(inp)
        self.assertIn("BROAD_CHECK_NEEDS_APPLICABILITY:LOAD", plan.deferred)
        self.assertNotIn("LOAD", plan.checks)

    def test_release_policy_l6(self):
        inp = VerificationInput(
            change_class="CODE_EDIT",
            lifecycle_stage="RELEASE",
            nfrs=(),
            requested_checks=frozenset(["UNIT"]),
            release_policy_full_suite=True
        )
        plan = plan_verification(inp)
        self.assertIn("L6_RELEASE", plan.levels)

if __name__ == "__main__":
    unittest.main()
