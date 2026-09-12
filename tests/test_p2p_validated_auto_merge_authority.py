"""P2P_AUTO_MERGE_AUTHORITY_01: focused acceptance evidence.

Proves the Owner's standing `VALIDATED_PR_AUTO_MERGE_AUTHORITY` is
synchronized into canonical P2P law, the thin installed entrypoint, and the
existing machine-readable classifier — without weakening any non-merge Owner
Gate and without creating a parallel policy artifact.

A. A validated merge under standing authorization needs no redundant Owner
   prompt.
B. An unvalidated / changed-head / blocked / unmergeable / changed-scope /
   separately-gated merge fails closed to the Owner Gate.
C. Production deployment/release — including a merge that IS the promotion —
   stays an Owner Gate.
D. Secrets, destructive mutation, paid spend/infrastructure, hard rollback,
   and genuine scope-changing blockers stay Owner Gates.
E. Canonical notebook, thin installed entrypoint, and the dev digest agree;
   the thin entrypoint stays thin; no parallel policy file was created.
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = REPO_ROOT / ".p2p" / "system"
if str(SYSTEM_ROOT) not in sys.path:
    sys.path.insert(0, str(SYSTEM_ROOT))

from p2p_capabilities.orchestration_policy import (  # noqa: E402
    OWNER_GATE_CLASSES,
    OWNER_MICRO_REPAIR_CLASSES,
    STANDING_AUTHORITY_MERGE,
    VALIDATED_MERGE_CONDITIONS,
    VALIDATED_PR_AUTO_MERGE_AUTHORITY,
    VALIDATED_PR_MERGE,
    OrchestrationPolicyError,
    classify_owner_escalation,
)


NOTEBOOK = REPO_ROOT / "docs" / "p2p-development" / "P2P-OPERATIONS-NOTEBOOK.md"
THIN = REPO_ROOT / "docs" / "p2p-development" / "P2P-AGENTS-INSTALL.md"
AGENTS = REPO_ROOT / "AGENTS.md"
DOCS_DIR = REPO_ROOT / "docs"
P2P_DIR = REPO_ROOT / ".p2p"
# Same cap the instruction-contract check enforces on the thin entrypoint.
MAX_THIN_BYTES = 9_000


def validated_merge(**overrides: object) -> dict[str, bool]:
    evidence = {name: True for name in VALIDATED_MERGE_CONDITIONS}
    evidence.update(overrides)
    return evidence  # type: ignore[return-value]


def rule11_section() -> str:
    text = NOTEBOOK.read_text(encoding="utf-8")
    start = text.index("### RULE 11 — OWNER_GATE_ONLY_WHEN_REAL")
    end = text.index("### RULE 12 —", start)
    return text[start:end]


class A_ValidatedMergeUnderStandingAuthorizationTests(unittest.TestCase):
    """A. Validated merge => no redundant Owner prompt."""

    def test_fully_validated_merge_needs_no_owner_prompt(self) -> None:
        result = classify_owner_escalation(
            VALIDATED_PR_MERGE, validated_merge=validated_merge()
        )
        self.assertEqual(result["route"], STANDING_AUTHORITY_MERGE)
        self.assertFalse(result["owner_gate_required"])
        self.assertEqual(result["auto_merge"], "YES")
        self.assertEqual(result["policy"], VALIDATED_PR_AUTO_MERGE_AUTHORITY)
        self.assertTrue(result["real_owner_gates_preserved"])

    def test_standing_authorization_scope_is_merge_only(self) -> None:
        result = classify_owner_escalation(
            VALIDATED_PR_MERGE, validated_merge=validated_merge()
        )
        self.assertEqual(result["standing_authorization_scope"], "MERGE_ONLY")
        # MERGE != PROMOTION != RELEASE != DEPLOYMENT: none of the high-risk
        # classes is authorized by the standing merge authorization.
        for excluded in (
            "MERGE_PROMOTION",
            "PRODUCTION_DEPLOY",
            "SECRETS",
            "DESTRUCTIVE_MUTATION",
            "MAJOR_SPEND_INFRASTRUCTURE",
            "HARD_ROLLBACK",
        ):
            self.assertIn(excluded, result["not_authorized_by_standing_authority"])
            self.assertIn(excluded, result["owner_gate_classes"])

    def test_condition_vocabulary_is_the_canonical_seven(self) -> None:
        self.assertEqual(
            set(VALIDATED_MERGE_CONDITIONS),
            {
                "exact_head_fresh_checked",
                "validation_evidence_sufficient",
                "required_checks_passed_or_baseline_unrelated",
                "no_unresolved_blocker",
                "mergeable_against_current_target",
                "scope_unchanged_since_validation",
                "no_separately_gated_side_effect",
            },
        )


class B_MergeFailsClosedTests(unittest.TestCase):
    """B. Any false or uncertain condition => AUTO_MERGE=NO (fail closed)."""

    def test_absent_evidence_fails_closed(self) -> None:
        for absent in (None, {}, "YES", True):
            result = classify_owner_escalation(
                VALIDATED_PR_MERGE, validated_merge=absent
            )
            self.assertEqual(result["route"], "OWNER_GATE", repr(absent))
            self.assertTrue(result["owner_gate_required"])
            self.assertEqual(result["auto_merge"], "NO")
            self.assertEqual(
                result["fail_closed_reason"], "VALIDATED_MERGE_EVIDENCE_MISSING"
            )

    def test_every_unmet_condition_fails_closed(self) -> None:
        for condition in VALIDATED_MERGE_CONDITIONS:
            result = classify_owner_escalation(
                VALIDATED_PR_MERGE, validated_merge=validated_merge(**{condition: False})
            )
            self.assertEqual(result["route"], "OWNER_GATE", condition)
            self.assertEqual(result["auto_merge"], "NO", condition)
            self.assertEqual(result["unmet_conditions"], [condition], condition)
            self.assertEqual(
                result["fail_closed_reason"], "VALIDATED_MERGE_CONDITION_UNMET"
            )

    def test_omitted_condition_fails_closed(self) -> None:
        evidence = validated_merge()
        del evidence["exact_head_fresh_checked"]
        result = classify_owner_escalation(
            VALIDATED_PR_MERGE, validated_merge=evidence
        )
        self.assertEqual(result["route"], "OWNER_GATE")
        self.assertEqual(result["unmet_conditions"], ["exact_head_fresh_checked"])

    def test_non_boolean_or_truthy_condition_fails_closed(self) -> None:
        # Only an affirmative boolean True counts as proven evidence.
        for value in (1, "true", "YES", None):
            result = classify_owner_escalation(
                VALIDATED_PR_MERGE,
                validated_merge=validated_merge(no_unresolved_blocker=value),
            )
            self.assertEqual(result["route"], "OWNER_GATE", repr(value))
            self.assertEqual(result["auto_merge"], "NO", repr(value))

    def test_unknown_condition_key_raises_instead_of_narrowing(self) -> None:
        with self.assertRaises(OrchestrationPolicyError):
            classify_owner_escalation(
                VALIDATED_PR_MERGE,
                validated_merge={**validated_merge(), "head_verified": True},
            )

    def test_changed_head_is_the_named_unmet_condition(self) -> None:
        result = classify_owner_escalation(
            VALIDATED_PR_MERGE, validated_merge=validated_merge(
                exact_head_fresh_checked=False
            )
        )
        self.assertIn("exact_head_fresh_checked", result["unmet_conditions"])


class C_PromotionAndReleaseStayOwnerGatedTests(unittest.TestCase):
    """C. Production deploy/release/promotion remain Owner Gates."""

    def test_production_deploy_is_owner_gate(self) -> None:
        result = classify_owner_escalation("PRODUCTION_DEPLOY")
        self.assertEqual(result["route"], "OWNER_GATE")
        self.assertTrue(result["owner_gate_required"])
        self.assertNotIn("auto_merge", result)

    def test_merge_that_is_the_promotion_is_owner_gate(self) -> None:
        # MERGE_PROMOTION = the merge itself constitutes canonical
        # promotion/release. It is NOT reachable by the standing merge
        # authorization, even with full validation evidence supplied.
        result = classify_owner_escalation(
            "MERGE_PROMOTION", validated_merge=validated_merge()
        )
        self.assertEqual(result["route"], "OWNER_GATE")
        self.assertTrue(result["owner_gate_required"])
        self.assertEqual(result["policy"], "OWNER_MICRO_LOOP_SUPPRESSION")

    def test_gated_side_effect_condition_blocks_the_merge(self) -> None:
        result = classify_owner_escalation(
            VALIDATED_PR_MERGE,
            validated_merge=validated_merge(no_separately_gated_side_effect=False),
        )
        self.assertEqual(result["route"], "OWNER_GATE")
        self.assertEqual(result["unmet_conditions"], ["no_separately_gated_side_effect"])


class D_NonMergeOwnerGatesPreservedTests(unittest.TestCase):
    """D. Every non-merge Owner Gate is unchanged."""

    def test_all_owner_gate_classes_still_route_to_owner(self) -> None:
        for gate in OWNER_GATE_CLASSES:
            result = classify_owner_escalation(gate)
            self.assertEqual(result["route"], "OWNER_GATE", gate)
            self.assertTrue(result["owner_gate_required"], gate)
            self.assertTrue(result["real_owner_gates_preserved"], gate)

    def test_required_gate_vocabulary_is_exact(self) -> None:
        self.assertEqual(
            set(OWNER_GATE_CLASSES),
            {
                "MERGE_PROMOTION",
                "PRODUCTION_DEPLOY",
                "DESTRUCTIVE_MUTATION",
                "SECRETS",
                "MAJOR_SPEND_INFRASTRUCTURE",
                "HARD_ROLLBACK",
                "SCOPE_CHANGING_BLOCKER",
            },
        )

    def test_micro_repair_loop_and_unknown_actions_unchanged(self) -> None:
        for action in OWNER_MICRO_REPAIR_CLASSES:
            result = classify_owner_escalation(action, finding_ref="finding/1")
            self.assertEqual(result["route"], "WRITER_REPAIR_LOOP", action)
            self.assertFalse(result["owner_gate_required"], action)
        with self.assertRaises(OrchestrationPolicyError):
            classify_owner_escalation("VAGUE_REQUEST")


class E_CanonicalAndThinEntrypointAlignedTests(unittest.TestCase):
    """E. Canonical law, thin entrypoint, and dev digest agree."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.notebook_text = NOTEBOOK.read_text(encoding="utf-8")
        cls.thin_text = THIN.read_text(encoding="utf-8")
        cls.agents_text = AGENTS.read_text(encoding="utf-8")
        cls.rule11 = rule11_section()

    def test_canonical_law_states_the_standing_authorization(self) -> None:
        self.assertIn("VALIDATED_PR_AUTO_MERGE_AUTHORITY=YES", self.rule11)
        self.assertIn("AUTO_MERGE=YES only when ALL are true", self.rule11)
        self.assertIn("MERGE != PROMOTION != RELEASE != DEPLOYMENT", self.rule11)
        self.assertIn("ANY condition false or uncertain => AUTO_MERGE=NO", self.rule11)
        self.assertIn("### RULE 11 — OWNER_GATE_ONLY_WHEN_REAL", self.notebook_text)
        # The supreme law no longer treats a validated merge as an authority
        # decision that must be re-asked.
        self.assertIn("VALIDATED_PR_AUTO_MERGE_AUTHORITY", self.notebook_text)

    def test_rule11_no_longer_gates_every_merge(self) -> None:
        self.assertNotIn("- canonical merge/promotion", self.rule11)
        self.assertIn("- canonical promotion/release", self.rule11)
        self.assertIn("not inherently a per-PR Owner Gate", self.rule11)
        self.assertIn(
            "The Writer of a PR never merges its own PR before independent validation",
            self.rule11,
        )

    def test_non_merge_owner_gates_are_explicitly_preserved_in_law(self) -> None:
        for preserved in (
            "production deployment/release",
            "destructive or hard-to-reverse mutation",
            "secrets/credentials",
            "material paid spending",
            "infrastructure commitment",
            "hard rollback",
            "genuine scope/outcome/authority change",
            "validation, HEAD, mergeability, or blocker state is uncertain",
        ):
            self.assertIn(preserved, self.rule11, preserved)
        # Merge-is-release semantics fail closed.
        self.assertIn("fails closed to the Owner Gate", self.rule11)

    def test_thin_entrypoint_carries_the_compact_rule(self) -> None:
        self.assertIn("standing Owner authorization", self.thin_text)
        self.assertIn("Validated PR merge may proceed", self.thin_text)
        for condition in (
            "exact HEAD",
            "sufficient evidence",
            "mergeability",
            "unchanged scope",
            "blocker-free state",
        ):
            self.assertIn(condition, self.thin_text, condition)
        for excluded in (
            "promotion",
            "deployment/release",
            "secrets",
            "destructive actions",
            "spend",
            "infrastructure",
            "hard rollback",
        ):
            self.assertIn(excluded, self.thin_text, excluded)
        self.assertIn("fails closed to an Owner Gate", self.thin_text)
        # The thin entrypoint stays a map: the detailed law body is NOT copied.
        self.assertNotIn("AUTO_MERGE=YES only when ALL are true", self.thin_text)
        self.assertNotIn("VALIDATED_PR_AUTO_MERGE_AUTHORITY=YES", self.thin_text)

    def test_thin_entrypoint_stays_thin(self) -> None:
        self.assertLessEqual(len(self.thin_text.encode("utf-8")), MAX_THIN_BYTES)

    def test_dev_digest_matches_canonical_semantics(self) -> None:
        # The dev-repo digest is prose-wrapped, so compare normalized text.
        flat = re.sub(r"\s+", " ", self.agents_text)
        self.assertIn("VALIDATED_PR_AUTO_MERGE_AUTHORITY", flat)
        self.assertIn("canonical promotion/release", flat)
        self.assertNotIn("canonical merge/promotion", flat)
        self.assertIn("not itself a per-PR Owner Gate", flat)
        self.assertIn("promotion, release, and deployment stay Owner Gates", flat)

    def test_no_parallel_policy_artifact_created(self) -> None:
        parallel = [
            path
            for path in list(DOCS_DIR.rglob("*.md")) + list(P2P_DIR.rglob("*.md"))
            if "auto" in path.name.lower() and "merge" in path.name.lower()
        ]
        self.assertEqual(parallel, [])
        # The canonical notebook is still the single operations notebook.
        notebooks = [
            path for path in REPO_ROOT.rglob("P2P-OPERATIONS-NOTEBOOK.md")
            if ".git" not in path.parts
        ]
        self.assertEqual(len(notebooks), 1)


if __name__ == "__main__":
    unittest.main()
