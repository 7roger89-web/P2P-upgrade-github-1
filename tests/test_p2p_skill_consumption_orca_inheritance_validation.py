from __future__ import annotations

import sys
import unittest
from copy import deepcopy
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = REPO_ROOT / ".p2p" / "system"
if str(SYSTEM_ROOT) not in sys.path:
    sys.path.insert(0, str(SYSTEM_ROOT))

from p2p_capabilities.bounded_delegation import PermissionEnvelope  # noqa: E402
from p2p_capabilities.orca_candidate_fanout import (  # noqa: E402
    CandidateSpec,
    plan_candidate_fanout,
    permission_fingerprint,
)
from p2p_capabilities.skill_consumption import (  # noqa: E402
    HANDOFF_SCHEMA,
    SkillConsumptionError,
    freeze_skill_handoff_for_orca_candidates,
    prepare_skill_handoff,
    validate_orca_skill_inheritance,
)


class SkillConsumptionOrcaInheritanceValidationTests(unittest.TestCase):
    def _orca_candidate_ids(self) -> tuple[str, str]:
        parent = PermissionEnvelope(grants=("READ",), scope=("src/a.py",))
        child = PermissionEnvelope(grants=("READ",), scope=("src/a.py",))
        common = dict(
            base_revision="a" * 40,
            permission_fingerprint=permission_fingerprint(child),
            permission=child,
        )
        a = CandidateSpec(
            spec_ref="candidate/a",
            candidate_ordinal=0,
            acceptance_fingerprint="acceptance-a",
            **common,
        )
        b = CandidateSpec(
            spec_ref="candidate/b",
            candidate_ordinal=1,
            acceptance_fingerprint="acceptance-b",
            **common,
        )
        plan = plan_candidate_fanout((a, b), parent)
        return plan.candidate_ids

    def _real_scope_handoff(self) -> dict:
        handoff = prepare_skill_handoff(
            REPO_ROOT,
            "@Scope Reality Check phản biện gắt kế hoạch này",
            host="ARENA",
        )
        self.assertEqual(handoff["SKILL_CHECK"], "PASS")
        self.assertIn("scope-reality-check", handoff["SKILLS_SELECTED"])
        self.assertEqual(handoff["SKILL_LOAD_STAGE"], "LOAD")
        self.assertEqual(handoff["PERMISSION_WIDENED"], "NO")
        return handoff

    def test_actual_orca_candidates_inherit_one_frozen_skill_handoff(self) -> None:
        handoff = self._real_scope_handoff()
        candidate_ids = self._orca_candidate_ids()
        inheritance = freeze_skill_handoff_for_orca_candidates(
            handoff, candidate_ids
        )
        bindings = inheritance["CANDIDATE_BINDINGS"]
        self.assertEqual(len(bindings), 2)
        self.assertEqual(
            [row["candidate_id"] for row in bindings],
            list(candidate_ids),
        )
        fingerprints = {
            row["skill_handoff_fingerprint"] for row in bindings
        }
        self.assertEqual(
            fingerprints,
            {inheritance["FROZEN_SKILL_HANDOFF_FINGERPRINT"]},
        )
        self.assertEqual(
            inheritance["FROZEN_SKILL_HANDOFF"]["SKILLS_SELECTED"],
            handoff["SKILLS_SELECTED"],
        )
        self.assertEqual(
            inheritance["FROZEN_SKILL_HANDOFF"]["SKILL_SOURCE_HASHES"],
            handoff["SKILL_SOURCE_HASHES"],
        )
        self.assertEqual(
            inheritance["CANDIDATE_SKILL_RESELECTION"], "FORBIDDEN"
        )
        self.assertEqual(inheritance["PERMISSION_WIDENED"], "NO")
        self.assertEqual(
            validate_orca_skill_inheritance(
                inheritance, handoff, candidate_ids
            ),
            {"valid": True, "reason_codes": []},
        )

    def test_candidate_local_skill_swap_fails_closed(self) -> None:
        handoff = self._real_scope_handoff()
        candidate_ids = self._orca_candidate_ids()
        inheritance = freeze_skill_handoff_for_orca_candidates(
            handoff, candidate_ids
        )
        tampered = deepcopy(inheritance)
        tampered["CANDIDATE_BINDINGS"][1]["skill_handoff_fingerprint"] = "0" * 64
        result = validate_orca_skill_inheritance(
            tampered, handoff, candidate_ids
        )
        self.assertFalse(result["valid"])
        self.assertIn(
            "ORCA_CANDIDATE_SKILL_BINDING_MISMATCH",
            result["reason_codes"],
        )

    def test_frozen_source_hash_tamper_fails_closed(self) -> None:
        handoff = self._real_scope_handoff()
        candidate_ids = self._orca_candidate_ids()
        inheritance = freeze_skill_handoff_for_orca_candidates(
            handoff, candidate_ids
        )
        tampered = deepcopy(inheritance)
        selected = handoff["SKILLS_SELECTED"][0]
        tampered["FROZEN_SKILL_HANDOFF"]["SKILL_SOURCE_HASHES"][selected] = "f" * 64
        result = validate_orca_skill_inheritance(
            tampered, handoff, candidate_ids
        )
        self.assertFalse(result["valid"])
        self.assertIn(
            "FROZEN_SKILL_HANDOFF_MISMATCH",
            result["reason_codes"],
        )

    def test_orca_fanout_cap_and_no_match_contract_remain_bounded(self) -> None:
        handoff = self._real_scope_handoff()
        with self.assertRaisesRegex(
            SkillConsumptionError,
            "ORCA_CANDIDATE_FANOUT_CAP_EXCEEDED",
        ):
            freeze_skill_handoff_for_orca_candidates(
                handoff, ("candidate-a", "candidate-b", "candidate-c")
            )

        no_match = {
            "schema": HANDOFF_SCHEMA,
            "SKILL_CHECK": "NO_MATCH",
            "SKILLS_SELECTED": [],
            "SKILL_LOAD_STAGE": "DISCOVERY",
            "SKILL_SOURCE_HASHES": {},
            "SKILL_SOURCE_PATHS": {},
            "SKILL_HOST_MODE": "ARENA_EXACT_REPO_READ",
            "SKILL_CONSUMPTION": "NO_SKILL_NEEDED",
            "PERMISSION_WIDENED": "NO",
            "SINGLE_ROUTER_REUSED": "YES",
        }
        candidate_ids = self._orca_candidate_ids()
        inheritance = freeze_skill_handoff_for_orca_candidates(
            no_match, candidate_ids
        )
        self.assertEqual(
            inheritance["FROZEN_SKILL_HANDOFF"]["SKILLS_SELECTED"], []
        )
        self.assertTrue(
            validate_orca_skill_inheritance(
                inheritance, no_match, candidate_ids
            )["valid"]
        )


if __name__ == "__main__":
    unittest.main()
