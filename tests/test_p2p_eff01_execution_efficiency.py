import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = REPO_ROOT / ".p2p" / "system"
if str(SYSTEM_ROOT) not in sys.path:
    sys.path.insert(0, str(SYSTEM_ROOT))

from p2p_capabilities.orchestration_policy import (  # noqa: E402
    CRITICAL,
    EXECUTION_LANES,
    FAST,
    MINIMUM_SUFFICIENT_WORK,
    RISK_PROPORTIONAL_EXECUTION,
    STANDARD,
    STRICT,
    derive_requirement,
)


class ExecutionEfficiencyPolicyTests(unittest.TestCase):
    def test_policy_exposes_one_canonical_four_lane_order(self) -> None:
        self.assertEqual(EXECUTION_LANES, (FAST, STANDARD, STRICT, CRITICAL))
        result = derive_requirement({})
        self.assertEqual(
            result["policy_principles"],
            [MINIMUM_SUFFICIENT_WORK, RISK_PROPORTIONAL_EXECUTION],
        )
        self.assertEqual(result["execution_policy"]["default_lane"], FAST)
        self.assertTrue(result["execution_policy"]["escalation_requires_material_evidence"])

    def test_case_a_fast_read_only_closure_stops_at_targeted_evidence(self) -> None:
        result = derive_requirement({"task_kind": "RECONCILIATION"})
        self.assertEqual(result["execution_lane"], FAST)
        self.assertEqual(result["jit_skills"]["required"], [])
        self.assertFalse(result["jit_skills"]["coder"])
        self.assertFalse(result["jit_skills"]["debugging"])
        self.assertFalse(result["jit_skills"]["qa"])
        self.assertFalse(result["jit_skills"]["supervisor"])
        self.assertEqual(result["test_ceiling"]["selected_level"], "TARGETED_EVIDENCE")
        self.assertFalse(result["test_ceiling"]["broad_full_regression"])
        self.assertTrue(result["stop_rule"]["do_not_prove_more_than_task_requires"])

    def test_case_b_standard_small_fix_uses_only_jit_mutation_evidence(self) -> None:
        result = derive_requirement(
            {"source_mutation": True, "acceptance_requires_testing": True}
        )
        self.assertEqual(result["execution_lane"], STANDARD)
        self.assertEqual(result["jit_skills"]["required"], ["coder", "qa"])
        self.assertFalse(result["jit_skills"]["debugging"])
        self.assertFalse(result["jit_skills"]["supervisor"])
        self.assertEqual(
            result["test_ceiling"]["selected_level"], "DIRECTLY_AFFECTED_MODULE"
        )
        self.assertFalse(result["test_ceiling"]["broad_full_regression"])

    def test_case_c_strict_registry_and_runtime_changes_use_neighbor_validation(self) -> None:
        registry_only = derive_requirement({"registry_change": True})
        self.assertEqual(registry_only["execution_lane"], STRICT)
        self.assertEqual(registry_only["jit_skills"]["required"], ["qa"])
        self.assertFalse(registry_only["jit_skills"]["coder"])
        self.assertFalse(registry_only["jit_skills"]["supervisor"])
        self.assertEqual(
            registry_only["test_ceiling"]["selected_level"], "DEPENDENCY_NEIGHBOR"
        )
        self.assertFalse(registry_only["test_ceiling"]["broad_full_regression"])

        runtime_code = derive_requirement(
            {"runtime_change": True, "source_mutation": True}
        )
        self.assertEqual(runtime_code["execution_lane"], STRICT)
        self.assertEqual(runtime_code["jit_skills"]["required"], ["coder", "qa"])

    def test_case_d_critical_promotion_keeps_owner_and_fail_closed_controls(self) -> None:
        profile = {
            "promotion": True,
            "owner_gate": "REQUIRED",
            "security_risk": True,
            "source_mutation": True,
        }
        result = derive_requirement(profile)
        self.assertEqual(result["execution_lane"], CRITICAL)
        self.assertEqual(result["jit_skills"]["required"], ["coder", "qa", "supervisor"])
        self.assertTrue(result["test_ceiling"]["broad_full_regression"])
        self.assertEqual(
            result["test_ceiling"]["broad_full_justification"],
            "CRITICAL_SECURITY_PRODUCTION_AUTHORITY_OR_DESTRUCTIVE_PREDICATE",
        )
        self.assertEqual(result["safety_invariants"]["canonical_integrity"], "PRESERVED")
        self.assertFalse(result["safety_invariants"]["permission_expansion"])
        self.assertEqual(result["safety_invariants"]["owner_approval"], "REQUIRED")
        self.assertEqual(result["safety_invariants"]["promotion"], "OWNER_GATE_REQUIRED")
        self.assertEqual(result["safety_invariants"]["deployment"], "NOT_AUTHORIZED_BY_POLICY")
        self.assertEqual(result["safety_invariants"]["live_activation"], "NOT_AUTHORIZED_BY_POLICY")
        self.assertEqual(result["safety_invariants"]["force_push"], "NOT_AUTHORIZED_BY_POLICY")

        accepted = derive_requirement({**profile, "acceptance_proven": True})
        self.assertEqual(accepted["execution_lane"], CRITICAL)
        self.assertEqual(accepted["test_ceiling"]["selected_level"], "ACCEPTANCE_PROVEN")

    def test_case_e_unrelated_baseline_failure_is_recorded_without_escalation(self) -> None:
        result = derive_requirement({"baseline_failure": True})
        self.assertEqual(result["execution_lane"], FAST)
        self.assertEqual(result["baseline_failure"]["status"], "PRE_EXISTING_UNRELATED")
        self.assertEqual(result["baseline_failure"]["action"], "RECORD_CLASSIFY_CONTINUE")
        self.assertFalse(result["baseline_failure"]["investigation_required"])
        self.assertFalse(result["baseline_failure"]["lane_escalation"])
        self.assertEqual(result["jit_skills"]["required"], [])

    def test_case_f_acceptance_proven_is_a_hard_stop_for_optional_checks(self) -> None:
        result = derive_requirement(
            {"source_mutation": True, "acceptance_proven": True}
        )
        self.assertEqual(result["execution_lane"], STANDARD)
        self.assertEqual(result["test_ceiling"]["ordered_levels"], [])
        self.assertEqual(result["test_ceiling"]["selected_level"], "ACCEPTANCE_PROVEN")
        self.assertFalse(result["test_ceiling"]["optional_checks_executed"])
        self.assertTrue(result["stop_rule"]["acceptance_proven"])
        self.assertEqual(result["stop_rule"]["stop_after"], "ACCEPTANCE_PROVEN")


if __name__ == "__main__":
    unittest.main()
