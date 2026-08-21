import sys
import os
import unittest

# Thêm đường dẫn runtime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../.p2p/system/p2p_capabilities")))

from quality_intelligence import AdaptiveVerificationHardeningV2, VerificationLadder

class TestAdaptiveVerificationV2Wiring(unittest.TestCase):
    def setUp(self):
        self.hardening = AdaptiveVerificationHardeningV2()

    def test_ladder_levels(self):
        self.assertEqual(VerificationLadder.L0_NONE, 0)
        self.assertEqual(VerificationLadder.L6_FORMAL, 6)

    def test_nfr_gate(self):
        # Giả lập NFR gate
        self.assertTrue(self.hardening.check_nfr_applicability("PERFORMANCE"))
        self.assertFalse(self.hardening.check_nfr_applicability("UNKNOWN_CATEGORY"))

    def test_evidence_invariant(self):
        # Kiểm tra invariant: RIGHT EVIDENCE, NOT MAXIMUM TEST COUNT
        self.assertEqual(self.hardening.get_required_evidence_level("CODE_MUTATION"), VerificationLadder.L3_INTEGRATION)

if __name__ == "__main__":
    unittest.main()
