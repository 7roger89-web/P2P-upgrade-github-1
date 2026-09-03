"""Focused productization tests for the provider-neutral video continuity contract."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / ".p2p" / "system"))

from p2p_capabilities import video_continuity as vc  # noqa: E402


def _valid_director_spec() -> dict[str, object]:
    return {
        "schema": "p2p-video-director-spec/1",
        "canonical_refs": {"character": "char-skydiver-01", "world": "world-tv-01", "style": "style-ltv-01"},
        "identity_constraints": {"face": "skydiver-face-01"},
        "element_constraints": {"costume": "suit-01", "prop": "rig-01"},
        "timeline_duration_seconds": 5.0,
        "action_performance": {"action": "solo skydive", "tempo": "deliberate"},
        "camera": {"move": "locked", "scene": "skydive bay"},
        "lighting": {"key": "sun", "rim": "rim-soft"},
        "physics": {"gravity": "realistic"},
        "dialogue_audio": {"lines": ["live tv commentary"], "music": "none"},
        "continuity_state": {"start": "approved-start-frame-01"},
        "negative_constraints": ["no extra faces", "no costume change"],
        "provider_projection_hints": {"max_prompt_chars": 500},
    }


def _valid_canonical() -> dict[str, object]:
    return {
        "schema": "p2p-canonical-visual-contract/1",
        "identity_face": {"face": "canonical"},
        "hair": {"hair": "canonical"},
        "body_proportions": {"proportions": "canonical"},
        "costume": {"costume": "canonical"},
        "prop_weapon": {"prop": "canonical"},
        "environment": {"environment": "canonical"},
        "visual_style": {"style": "canonical"},
        "image_consistency": "canonical",
        "temporal_video_consistency": "canonical",
        "shot_to_shot_continuity": "canonical",
    }


def _valid_performance() -> dict[str, object]:
    return {
        "schema": "p2p-performance-bible/1",
        "movement_style": "grounded",
        "gesture_amplitude": "small",
        "action_tempo": "deliberate",
        "body_posture_tendencies": "upright",
        "camera_feel_inertia": "slow-pan",
        "cues": {"turn": "shoulder-led"},
    }


class VideoDirectorSpecTests(unittest.TestCase):
    def test_valid_spec_parses_and_hashes(self) -> None:
        spec = vc.VideoDirectorSpec.from_mapping(_valid_director_spec())
        self.assertEqual(spec.timeline_duration_seconds, 5.0)
        self.assertEqual(len(spec.identity_hash()), 64)
        self.assertIn("character", spec.canonical_refs)

    def test_invalid_spec_missing_field_fails_closed(self) -> None:
        payload = _valid_director_spec()
        del payload["camera"]
        with self.assertRaises(vc.VideoContinuityError):
            vc.VideoDirectorSpec.from_mapping(payload)

    def test_invalid_spec_non_positive_duration_fails_closed(self) -> None:
        payload = _valid_director_spec()
        payload["timeline_duration_seconds"] = 0
        with self.assertRaises(vc.VideoContinuityError):
            vc.VideoDirectorSpec.from_mapping(payload)

    def test_invalid_spec_unsupported_schema_fails_closed(self) -> None:
        payload = _valid_director_spec()
        payload["schema"] = "p2p-other-spec/1"
        with self.assertRaises(vc.VideoContinuityError):
            vc.VideoDirectorSpec.from_mapping(payload)


class CanonicalVisualContractTests(unittest.TestCase):
    def test_contract_exposes_all_required_dimensions(self) -> None:
        contract = vc.CanonicalVisualContract.from_mapping(_valid_canonical())
        self.assertEqual(
            contract.dimensions(),
            (
                "identity_face",
                "hair",
                "body_proportions",
                "costume",
                "prop_weapon",
                "environment",
                "visual_style",
                "image_consistency",
                "temporal_video_consistency",
                "shot_to_shot_continuity",
            ),
        )

    def test_contract_missing_dimension_fails_closed(self) -> None:
        payload = _valid_canonical()
        del payload["hair"]
        with self.assertRaises(vc.VideoContinuityError):
            vc.CanonicalVisualContract.from_mapping(payload)


class PerformanceBibleTests(unittest.TestCase):
    def test_performance_bible_is_bounded_not_an_animation_engine(self) -> None:
        bible = vc.PerformanceBible.from_mapping(_valid_performance())
        self.assertEqual(bible.action_tempo, "deliberate")
        self.assertEqual(bible.cues["turn"], "shoulder-led")

    def test_performance_bible_missing_key_fails_closed(self) -> None:
        payload = _valid_performance()
        del payload["movement_style"]
        with self.assertRaises(vc.VideoContinuityError):
            vc.PerformanceBible.from_mapping(payload)


class ContinuityGateTests(unittest.TestCase):
    def test_gate_is_manual_external_evidence_and_does_not_inspect_media(self) -> None:
        verdict = vc.evaluate_continuity_gate(
            shot={"identity": True},
            canonical=vc.CanonicalVisualContract.from_mapping(_valid_canonical()),
            start_keyframe={"identity": "canonical"},
            expected_end_state={"end": "canonical"},
        )
        self.assertEqual(verdict.evidence_source, "MANUAL_OR_EXTERNAL_EVIDENCE")
        self.assertFalse(verdict.inspects_media)
        self.assertEqual(verdict.to_dict()["evidence_source"], "MANUAL_OR_EXTERNAL_EVIDENCE")
        self.assertFalse(verdict.to_dict()["inspects_media"])

    def test_passing_shot_propagates_state(self) -> None:
        verdict = vc.evaluate_continuity_gate(
            shot={
                "identity": True,
                "hair_body": True,
                "costume": True,
                "prop_weapon": True,
                "environment_style": True,
                "expected_start_state": True,
                "expected_end_state": True,
                "action_camera_continuity": True,
            },
            canonical=vc.CanonicalVisualContract.from_mapping(_valid_canonical()),
            start_keyframe={"identity": "canonical", "camera": "locked"},
            expected_end_state={"end": "canonical"},
        )
        self.assertTrue(verdict.passed)
        self.assertTrue(verdict.propagate_allowed)
        self.assertIsNone(verdict.blocker)

    def test_drift_shot_blocks_propagation(self) -> None:
        verdict = vc.evaluate_continuity_gate(
            shot={"identity": "drift"},
            canonical=vc.CanonicalVisualContract.from_mapping(_valid_canonical()),
            start_keyframe={"identity": "canonical"},
            expected_end_state={"end": "canonical"},
        )
        self.assertFalse(verdict.passed)
        self.assertFalse(verdict.propagate_allowed)
        self.assertEqual(verdict.blocker, "identity")

    def test_failed_shot_cannot_become_source_of_truth(self) -> None:
        cycle = vc.ReanchorCycle(
            start_keyframe={"identity": "canonical"},
            candidate_takes=[{"id": "t1"}],
            best_take={"id": "t1"},
            last_good_frame={"drift": True},
            canonical_reanchor={},
            next_approved_keyframe={"identity": "canonical"},
            drift_detected=True,
            gate_passed=False,
        )
        self.assertFalse(cycle.safe_to_reanchor)
        with self.assertRaises(vc.VideoContinuityError):
            cycle.next_start()


class ReanchorCycleTests(unittest.TestCase):
    def test_clean_frame_reanchors_to_next_keyframe(self) -> None:
        cycle = vc.ReanchorCycle(
            start_keyframe={"identity": "canonical"},
            candidate_takes=[{"id": "t1"}],
            best_take={"id": "t1"},
            last_good_frame={"drift": False},
            canonical_reanchor={},
            next_approved_keyframe={"identity": "approved-next"},
            drift_detected=False,
            gate_passed=True,
        )
        self.assertTrue(cycle.safe_to_reanchor)
        self.assertEqual(cycle.next_start(), {"identity": "approved-next"})

    def test_drifted_frame_never_auto_becomes_canonical_input(self) -> None:
        cycle = vc.ReanchorCycle(
            start_keyframe={"identity": "canonical"},
            candidate_takes=[{"id": "t1"}],
            best_take={"id": "t1"},
            last_good_frame={"drift": True},
            canonical_reanchor={},
            next_approved_keyframe={"identity": "approved-next"},
            drift_detected=True,
            gate_passed=True,
        )
        self.assertFalse(cycle.safe_to_reanchor)
        with self.assertRaises(vc.VideoContinuityError):
            cycle.next_start()


class ProviderProjectionTests(unittest.TestCase):
    def _setup(self):
        spec = vc.VideoDirectorSpec.from_mapping(_valid_director_spec())
        canonical = vc.CanonicalVisualContract.from_mapping(_valid_canonical())
        bible = vc.PerformanceBible.from_mapping(_valid_performance())
        return spec, canonical, bible

    def test_projection_respects_provider_ceiling_and_uses_pointers(self) -> None:
        spec, canonical, bible = self._setup()
        profile = vc.ProviderProfile.from_mapping(
            {"provider_id": "arena-video", "max_prompt_chars": 220, "accepts_image_reference": True, "model_identity_stable": False}
        )
        result = vc.project_provider_shot(spec, canonical, bible, profile, shot={})
        self.assertTrue(result["within_limit"])
        self.assertLessEqual(result["chars"], profile.max_prompt_chars)
        self.assertFalse(result["duplicated_master_spec"])
        self.assertTrue(result["reference_pointers_only"])
        self.assertFalse(result["model_identity_stable"])
        self.assertTrue(result["mandatory_constraints_preserved"])
        self.assertFalse(result["fails_closed"])
        self.assertEqual(result["mode"], "PRIORITY_AWARE_PROJECTION")

    def test_forbidden_token_in_mandatory_constraint_fails_closed(self) -> None:
        spec, canonical, bible = self._setup()
        profile = vc.ProviderProfile.from_mapping(
            {"provider_id": "designarena", "max_prompt_chars": 4000, "accepts_image_reference": False, "model_identity_stable": False, "forbidden_tokens": ["locked"]}
        )
        # Mandatory camera segment uses the forbidden token 'locked'; this must
        # fail closed explicitly rather than silently truncate or strip it.
        with self.assertRaises(vc.VideoContinuityError) as ctx:
            vc.project_provider_shot(spec, canonical, bible, profile, shot={})
        self.assertIn("FAIL_CLOSED", str(ctx.exception))
        self.assertIn("forbidden token", str(ctx.exception))

    def test_mandatory_constraints_fit_intact_within_limit(self) -> None:
        spec, canonical, bible = self._setup()
        profile = vc.ProviderProfile.from_mapping(
            {"provider_id": "arena-video", "max_prompt_chars": 5000, "accepts_image_reference": True, "model_identity_stable": False}
        )
        result = vc.project_provider_shot(spec, canonical, bible, profile, shot={})
        self.assertTrue(result["mandatory_constraints_preserved"])
        self.assertFalse(result["fails_closed"])
        self.assertTrue(result["within_limit"])
        # Mandatory segments must remain intact (no silent truncation marker).
        self.assertIn("negative:no extra faces; no costume change", result["provider_prompt"])

    def test_required_constraints_fit_or_fail_closed_with_explicit_reason(self) -> None:
        spec, canonical, bible = self._setup()
        # Very tight limit: mandatory constraints cannot fit -> fail closed.
        profile = vc.ProviderProfile.from_mapping(
            {"provider_id": "tiny", "max_prompt_chars": 20, "accepts_image_reference": True, "model_identity_stable": False}
        )
        with self.assertRaises(vc.VideoContinuityError) as ctx:
            vc.project_provider_shot(spec, canonical, bible, profile, shot={})
        self.assertIn("FAIL_CLOSED", str(ctx.exception))
        self.assertIn("exceed", str(ctx.exception))


class CandidateRenderingTests(unittest.TestCase):
    def test_best_of_n_is_planning_state_not_actual_rendering(self) -> None:
        spec = vc.VideoDirectorSpec.from_mapping(_valid_director_spec())
        rendering = vc.build_candidate_set(spec, 5, seed="seed-1")
        self.assertEqual(len(rendering.candidates), 5)
        self.assertEqual(rendering.state, "BEST_OF_N_CANDIDATE")
        self.assertEqual(rendering.render_mode, "PLANNING_STATE_ONLY")
        self.assertFalse(rendering.model_identity_stable)
        self.assertTrue(all(c["model_identity_stable"] is False for c in rendering.candidates))
        d = rendering.to_dict()
        self.assertFalse(d["invoked_rendering"])
        self.assertFalse(d["scores_real_takes"])

    def test_candidate_set_requires_positive_n(self) -> None:
        spec = vc.VideoDirectorSpec.from_mapping(_valid_director_spec())
        with self.assertRaises(vc.VideoContinuityError):
            vc.build_candidate_set(spec, 0)


if __name__ == "__main__":
    unittest.main()
