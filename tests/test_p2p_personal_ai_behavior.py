from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = REPO_ROOT / ".p2p" / "system"
if str(SYSTEM_ROOT) not in sys.path:
    sys.path.insert(0, str(SYSTEM_ROOT))

from p2p_capabilities.personal_ai_behavior import (  # noqa: E402
    MemoryCandidate,
    ResponseSignals,
    VoiceProfile,
    build_render_packet,
    classify_memory_candidate,
    lint_response,
    locked_facts_unchanged,
    select_response_policy,
)


class PersonalAIBehaviorHarnessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.profile = VoiceProfile()

    def test_serious_override_disables_humor(self) -> None:
        policy = select_response_policy(
            self.profile,
            ResponseSignals(explicit_serious=True),
        )
        self.assertEqual(policy.seriousness, 1.0)
        self.assertFalse(policy.humor_allowed)
        self.assertTrue(any("Serious-mode override" in item for item in policy.style_directives))

    def test_research_and_tool_actions_are_selected_before_answer(self) -> None:
        policy = select_response_policy(
            self.profile,
            ResponseSignals(requires_fresh_information=True, requires_tool=True),
        )
        self.assertEqual(policy.pre_actions, ("RESEARCH_FIRST", "USE_REQUIRED_TOOL"))

    def test_blocking_ambiguity_is_the_only_question_first_path(self) -> None:
        blocked = select_response_policy(
            self.profile,
            ResponseSignals(blocking_ambiguity=True, requires_tool=True),
        )
        direct = select_response_policy(self.profile, ResponseSignals())
        self.assertEqual(blocked.pre_actions, ("ASK_ONLY_IF_BLOCKING",))
        self.assertEqual(direct.pre_actions, ("ANSWER_DIRECTLY",))

    def test_user_depth_request_is_preserved(self) -> None:
        short = select_response_policy(
            self.profile,
            ResponseSignals(user_requested_short=True),
        )
        deep = select_response_policy(
            self.profile,
            ResponseSignals(user_requested_deep=True),
        )
        self.assertEqual(short.depth, "short")
        self.assertEqual(deep.depth, "deep")

    def test_anti_slop_linter_catches_strong_generic_markers(self) -> None:
        text = (
            "Câu hỏi rất hay. Tôi hoàn toàn hiểu. "
            "Nếu bạn muốn, tôi có thể làm thêm."
        )
        codes = {finding.code for finding in lint_response(text, self.profile)}
        self.assertIn("SYCOPHANTIC_OPENER", codes)
        self.assertIn("GENERIC_UNDERSTANDING_CLAIM", codes)
        self.assertIn("GENERIC_FOLLOWUP_OFFER", codes)

    def test_linter_does_not_require_a_joke_or_analogy_by_regex(self) -> None:
        self.assertEqual(lint_response("Dữ liệu này chưa đủ để kết luận.", self.profile), ())

    def test_explicit_owner_memory_is_promotion_eligible_but_not_written(self) -> None:
        candidate = MemoryCandidate(
            kind="communication_preference",
            text="Do not end completed answers with generic offers.",
            explicit_owner_instruction=True,
        )
        self.assertEqual(classify_memory_candidate(candidate), "PROMOTE_ELIGIBLE")

    def test_uncertain_memory_is_held_separately(self) -> None:
        candidate = MemoryCandidate(
            kind="inference",
            text="Maybe the owner dislikes tables.",
            evidence_count=5,
            confirmed=False,
            uncertain=True,
        )
        self.assertEqual(classify_memory_candidate(candidate), "HOLD_UNCERTAIN")

    def test_repeated_confirmed_memory_requires_review_not_auto_promotion(self) -> None:
        candidate = MemoryCandidate(
            kind="preference",
            text="Prefer concise status updates.",
            evidence_count=3,
            confirmed=True,
        )
        self.assertEqual(classify_memory_candidate(candidate), "REVIEW_ELIGIBLE")

    def test_render_packet_separates_locked_facts_from_style(self) -> None:
        facts = {
            "amount": 14000,
            "currency": "USD",
            "route": "China -> Vietnam",
        }
        policy = select_response_policy(self.profile, ResponseSignals())
        packet = build_render_packet(
            core_answer="Quoted shipment facts are locked.",
            locked_facts=facts,
            profile=self.profile,
            policy=policy,
        )
        self.assertEqual(packet["locked_facts"], facts)
        self.assertTrue(locked_facts_unchanged(facts, packet["locked_facts"]))

    def test_fact_lock_detects_renderer_drift(self) -> None:
        before = {"amount": 14000, "currency": "USD"}
        after = {"amount": 15000, "currency": "USD"}
        self.assertFalse(locked_facts_unchanged(before, after))


if __name__ == "__main__":
    unittest.main()
