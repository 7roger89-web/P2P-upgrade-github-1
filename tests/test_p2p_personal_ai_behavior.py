from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = REPO_ROOT / ".p2p" / "system"
if str(SYSTEM_ROOT) not in sys.path:
    sys.path.insert(0, str(SYSTEM_ROOT))

from p2p_capabilities.personal_ai_behavior import (  # noqa: E402
    InteractionSignals,
    InteractionState,
    MemoryCandidate,
    ResponseSignals,
    VoiceProfile,
    advance_interaction_state,
    build_interaction_directives,
    build_render_packet,
    classify_memory_candidate,
    lint_response,
    locked_facts_unchanged,
    reflect_assistant_outcome,
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

    def test_session_correction_after_completion_forces_focused_evidence_mode(self) -> None:
        state = reflect_assistant_outcome(
            InteractionState(open_loop=True),
            claimed_complete=True,
        )
        state = advance_interaction_state(
            state,
            InteractionSignals(correction=True),
        )
        self.assertEqual(state.mode, "focused")
        self.assertEqual(state.friction, 1)
        self.assertTrue(state.completion_claim_contradicted)
        directives = build_interaction_directives(state)
        self.assertTrue(any("fresh evidence" in item for item in directives))

    def test_positive_feedback_reduces_bounded_friction(self) -> None:
        state = InteractionState(mode="focused", friction=2)
        state = advance_interaction_state(
            state,
            InteractionSignals(positive=True, substantive=False),
        )
        self.assertEqual(state.friction, 1)
        self.assertEqual(state.mode, "focused")

    def test_continuation_keeps_open_loop_and_reuses_session_history(self) -> None:
        state = InteractionState(open_loop=True)
        state = advance_interaction_state(
            state,
            InteractionSignals(continuation=True, substantive=False),
        )
        self.assertTrue(state.open_loop)
        self.assertEqual(state.continuation_count, 1)
        directives = build_interaction_directives(state, continuation=True)
        text = " ".join(directives)
        self.assertIn("continues the active task", text)
        self.assertIn("do not restart from scratch", text)

    def test_reflection_closes_completed_loop_and_preserves_unresolved_loop(self) -> None:
        active = InteractionState(open_loop=True)
        completed = reflect_assistant_outcome(active, claimed_complete=True)
        blocked = reflect_assistant_outcome(completed, unresolved=True)
        self.assertFalse(completed.open_loop)
        self.assertTrue(blocked.open_loop)

    def test_anti_slop_linter_catches_strong_generic_markers(self) -> None:
        text = (
            "Câu hỏi rất hay. Tôi hoàn toàn hiểu. "
            "Nếu bạn muốn, tôi có thể làm thêm."
        )
        codes = {finding.code for finding in lint_response(text, self.profile)}
        self.assertIn("SYCOPHANTIC_OPENER", codes)
        self.assertIn("GENERIC_UNDERSTANDING_CLAIM", codes)
        self.assertIn("GENERIC_FOLLOWUP_OFFER", codes)

    def test_followup_offer_detector_does_not_flag_mid_answer_business_conditional(self) -> None:
        text = (
            "Nếu bạn muốn tiết kiệm, tôi có thể dùng container 20ft: cước 780 USD, "
            "thời gian 28-32 ngày. Phương án nhanh hơn là đi đường bộ."
        )
        codes = {finding.code for finding in lint_response(text, self.profile)}
        self.assertNotIn("GENERIC_FOLLOWUP_OFFER", codes)

    def test_sycophantic_opener_detector_is_position_specific(self) -> None:
        text = (
            "Phương án A rẻ hơn. Về câu hỏi rất hay của bạn ở tin nhắn trước, "
            "dữ liệu hiện tại vẫn chưa đủ để kết luận."
        )
        codes = {finding.code for finding in lint_response(text, self.profile)}
        self.assertNotIn("SYCOPHANTIC_OPENER", codes)

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
