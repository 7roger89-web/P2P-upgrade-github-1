from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
for candidate in (ROOT / "scripts", ROOT / ".p2p" / "system", ROOT):
    value = str(candidate)
    if value not in sys.path:
        sys.path.insert(0, value)

import p2p_control_tower as control_tower  # noqa: E402
from p2p_capabilities.control_tower_handoff import SessionBinding  # noqa: E402
from p2p_capabilities.experience_evolution import (  # noqa: E402
    LEDGER_RELATIVE_PATH,
    activate_verified,
    create_candidate,
    verify_candidate,
)


class ControlTowerContextAssemblyTests(unittest.TestCase):
    def _activate_experience(
        self,
        root: Path,
        *,
        triggers: tuple[str, ...],
        lesson: str,
        correction: str,
        suffix: str = "",
    ) -> str:
        candidate = create_candidate(
            root,
            task_id=f"HISTORICAL-TASK{suffix}",
            kind="PROCEDURAL",
            trigger_tokens=triggers,
            lesson=lesson,
            evidence=(
                {
                    "kind": "TEST_RESULT",
                    "ref": f"evidence://historical/source{suffix}",
                    "verdict": "PASS",
                },
            ),
            outcome="CORRECTED",
            failure_class="REPEATED_PREFLIGHT_GAP",
            correction=correction,
            source_revision=f"historical-sha{suffix}",
        )
        experience_id = str(candidate["experience_id"])
        verify_candidate(
            root,
            experience_id,
            task_id=f"VERIFY-HISTORICAL-TASK{suffix}",
            verification_evidence=(
                {
                    "kind": "TEST_RESULT",
                    "ref": f"evidence://verify/behavior{suffix}",
                    "role": "BEHAVIOR_PROOF",
                    "verdict": "PASS",
                },
                {
                    "kind": "TEST_RESULT",
                    "ref": f"evidence://verify/regression{suffix}",
                    "role": "REGRESSION_PROOF",
                    "verdict": "PASS",
                },
                {
                    "kind": "ADVERSARIAL_CHECK",
                    "ref": f"evidence://verify/challenge{suffix}",
                    "role": "CHALLENGE_PROOF",
                    "verdict": "PASS",
                },
            ),
        )
        activate_verified(root, experience_id, task_id=f"ACTIVATE-HISTORICAL-TASK{suffix}")
        return experience_id

    def _binding(self, goal: str = "MongoDB pilot snapshot") -> SessionBinding:
        return SessionBinding(
            session_id="session-arena-context-test-123456789abc",
            host="ARENA",
            goal_id="CTX-ASSEMBLY",
            goal=goal,
        )

    def test_matching_retrieval_is_read_only_and_block_is_bounded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            lesson = "Verify destination pristineness and BSON round-trip fidelity before a MongoDB pilot snapshot mutation."
            correction = "Run destination preflight, canonical Extended JSON round-trip proof, dry-run, then source-immutability verification."
            experience_id = self._activate_experience(
                root,
                triggers=("mongodb", "pilot", "snapshot"),
                lesson=lesson,
                correction=correction,
            )
            ledger = root / LEDGER_RELATIVE_PATH
            before = ledger.read_bytes()

            summary = control_tower._experience_summary(root, "Clone MongoDB pilot snapshot safely")
            block = control_tower._render_context_block(summary, max_chars=512)

            self.assertEqual(before, ledger.read_bytes())
            self.assertIn(control_tower.CONTEXT_MARKER, block)
            self.assertIn("XP=USE_ACTIVE_EXPERIENCE", block)
            self.assertIn("NONAUTH", block)
            self.assertIn(experience_id, block)
            self.assertIn("RISK=", block)
            self.assertIn(correction, block)
            self.assertLessEqual(len(block), 512)

    def test_unrelated_experience_is_not_injected_as_risk(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            lesson = "Require official provision-level provenance before claiming Vietnamese legal text correctness."
            self._activate_experience(
                root,
                triggers=("vnlaw", "official", "provenance"),
                lesson=lesson,
                correction="Compare the parsed provision against the official source and preserve provenance refs.",
            )

            summary = control_tower._experience_summary(root, "Fix MongoDB shipment import pagination")
            block = control_tower._render_context_block(summary, max_chars=512)

            self.assertIn("XP=NO_MATCH", block)
            self.assertNotIn("RISK=", block)
            self.assertNotIn(lesson, block)

    def test_start_command_preserves_supreme_law_and_persists_budgeted_context(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            correction = "Compare current main, exact candidate head, mergeability, and exact-head checks before merge."
            experience_id = self._activate_experience(
                root,
                triggers=("github", "merge", "head"),
                lesson="Fresh-check the exact Git head before any merge or completion claim.",
                correction=correction,
            )
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = control_tower.main(
                    [
                        "--root",
                        str(root),
                        "start",
                        "--host",
                        "CODEX",
                        "--goal-id",
                        "CTX-ASSEMBLY",
                        "--goal",
                        "GitHub merge exact head",
                        "--task-id",
                        "TASK-1",
                        "--json",
                    ]
                )
            self.assertEqual(0, code)
            result = json.loads(output.getvalue())
            prompt = result["recommendation"]["PROMPT"]
            self.assertIn("P2P_SUPREME_LAW_PREFLIGHT:", prompt)
            self.assertIn("Canonical law source:", prompt)
            self.assertIn("SUPREME_LAW_CAPSULE:", prompt)
            self.assertLessEqual(len(prompt), control_tower.PROMPT_GUARD_CHARS)

            # The experience wrapper is optional when the existing prompt has no
            # safe slack. If included, it must stay non-authoritative and bounded.
            if control_tower.CONTEXT_MARKER in prompt:
                self.assertIn("XP=USE_ACTIVE_EXPERIENCE", prompt)
                self.assertIn("NONAUTH", prompt)
                self.assertIn(experience_id, prompt)

            second = io.StringIO()
            with contextlib.redirect_stdout(second):
                second_code = control_tower.main(
                    [
                        "--root",
                        str(root),
                        "start",
                        "--host",
                        "CODEX",
                        "--goal-id",
                        "CTX-ASSEMBLY",
                        "--goal",
                        "GitHub merge exact head",
                        "--task-id",
                        "TASK-1",
                        "--json",
                    ]
                )
            self.assertEqual(0, second_code)
            second_result = json.loads(second.getvalue())
            self.assertTrue(second_result["idempotent"])
            self.assertEqual(prompt, second_result["recommendation"]["PROMPT"])

    def test_three_long_active_experiences_cannot_break_prompt_guard(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for index in range(3):
                self._activate_experience(
                    root,
                    triggers=("mongodb", "pilot", "snapshot"),
                    lesson=(f"Long historical lesson {index} " + "L" * 1800),
                    correction=(f"Risk wrapper {index}: " + "C" * 1800),
                    suffix=f"-{index}",
                )

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = control_tower.main(
                    [
                        "--root",
                        str(root),
                        "start",
                        "--host",
                        "ARENA",
                        "--goal-id",
                        "BOUNDED-CONTEXT",
                        "--goal",
                        "MongoDB pilot snapshot",
                        "--task-id",
                        "TASK-LONG",
                        "--json",
                    ]
                )

            self.assertEqual(0, code)
            result = json.loads(output.getvalue())
            prompt = result["recommendation"]["PROMPT"]
            self.assertLessEqual(len(prompt), control_tower.PROMPT_GUARD_CHARS)
            self.assertIn("P2P_SUPREME_LAW_PREFLIGHT:", prompt)
            self.assertNotIn("C" * 500, prompt)
            if control_tower.CONTEXT_MARKER in prompt:
                self.assertIn("XP=USE_ACTIVE_EXPERIENCE", prompt)
                self.assertIn("NONAUTH", prompt)

    def test_exact_prompt_budget_never_weakens_existing_guard(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._activate_experience(
                root,
                triggers=("mongodb", "pilot", "snapshot"),
                lesson="Historical lesson " + "L" * 1800,
                correction="Historical correction " + "C" * 1800,
            )
            binding = self._binding()
            contextual = control_tower._contextual_task_for_session(
                root,
                binding,
                "MongoDB pilot snapshot",
            )
            from p2p_capabilities.control_tower_handoff import build_execution_prompt

            final_prompt = build_execution_prompt(binding, contextual)
            self.assertLessEqual(len(final_prompt), control_tower.PROMPT_GUARD_CHARS)
            self.assertIn("P2P_SUPREME_LAW_PREFLIGHT:", final_prompt)


if __name__ == "__main__":
    unittest.main()
