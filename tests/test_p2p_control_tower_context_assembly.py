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
from p2p_capabilities import control_tower_handoff as handoff  # noqa: E402
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

    def test_control_tower_runtime_has_exactly_one_nine_law_capsule(self) -> None:
        lines = tuple(line for line in handoff.SUPREME_LAW_CAPSULE.splitlines() if line.strip())
        self.assertEqual(9, len(lines))
        for index, identifier in enumerate(control_tower._CANONICAL_LAW_IDENTIFIERS):
            self.assertIn(identifier, lines[index])
        joined = "\n".join(lines)
        self.assertNotIn("PROMPT_AUTHORING_DISCIPLINE_V1", joined)
        self.assertNotIn("PROJECT_AGENT_INSTRUCTIONS_PREFLIGHT", joined)
        self.assertNotIn("EXECUTOR_GITHUB_ACCESS != OWNER_GITHUB_CONNECTOR_STATUS", joined)

    def test_matching_retrieval_is_read_only_and_block_is_bounded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            correction = "Run destination preflight, canonical Extended JSON round-trip proof, dry-run, then source-immutability verification."
            experience_id = self._activate_experience(
                root,
                triggers=("mongodb", "pilot", "snapshot"),
                lesson="Verify destination pristineness and BSON round-trip fidelity before a MongoDB pilot snapshot mutation.",
                correction=correction,
            )
            ledger = root / LEDGER_RELATIVE_PATH
            before = ledger.read_bytes()

            summary = control_tower._experience_summary(root, "Clone MongoDB pilot snapshot safely")
            block = control_tower._render_context_block(
                summary,
                "Clone MongoDB pilot snapshot safely",
                max_chars=900,
            )

            self.assertEqual(before, ledger.read_bytes())
            self.assertIn(control_tower.CONTEXT_MARKER, block)
            self.assertIn("LAW_AUTHORITY=ONE", block)
            self.assertIn("P2P_LAW_PREFLIGHT=", block)
            self.assertIn("repo-scoped portable=fresh|inline", block)
            self.assertIn("OE_GATE=", block)
            self.assertIn("XP=USE_ACTIVE_EXPERIENCE", block)
            self.assertIn("NONAUTHORITATIVE", block)
            self.assertIn(experience_id, block)
            self.assertIn("PRIMARY_RISK_WRAPPER=", block)
            risk_line = next(
                line for line in block.splitlines() if line.startswith("PRIMARY_RISK_WRAPPER=")
            )
            rendered_risk = risk_line.split("=", 1)[1]
            semantic_prefix = rendered_risk.removesuffix("…")
            self.assertTrue(semantic_prefix)
            self.assertTrue(correction.startswith(semantic_prefix))
            self.assertLessEqual(
                len(rendered_risk),
                control_tower.MAX_PRIMARY_RISK_WRAPPER_CHARS,
            )
            self.assertLessEqual(len(block), 900)

    def test_unrelated_experience_and_guidance_are_not_injected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            lesson = "Require official provision-level provenance before claiming Vietnamese legal text correctness."
            self._activate_experience(
                root,
                triggers=("vnlaw", "official", "provenance"),
                lesson=lesson,
                correction="Compare parsed text against the official source and preserve provenance refs.",
            )

            summary = control_tower._experience_summary(root, "Fix MongoDB shipment import pagination")
            block = control_tower._render_context_block(
                summary,
                "Fix MongoDB shipment import pagination",
                max_chars=900,
            )

            self.assertIn("XP=NO_MATCH", block)
            self.assertNotIn("PRIMARY_RISK_WRAPPER=", block)
            self.assertNotIn(lesson, block)
            self.assertNotIn("GITHUB_GUIDANCE=", block)
            self.assertNotIn("PROMPT_AUTHORING_DISCIPLINE_V1=", block)
            self.assertNotIn("OPEN_CODE_REVIEW_DELEGATION=", block)

    def test_task_specific_guidance_is_trigger_scoped(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            empty = control_tower._experience_summary(root, "ordinary task")
            github_block = control_tower._render_context_block(
                empty,
                "Review GitHub PR and exact HEAD before merge",
                max_chars=1300,
            )
            prompt_block = control_tower._render_context_block(
                empty,
                "Revise the executor prompt for Arena",
                max_chars=1500,
            )
            ordinary_block = control_tower._render_context_block(
                empty,
                "Analyze shipment totals",
                max_chars=1300,
            )
            generic_review_block = control_tower._render_context_block(
                empty,
                "Review this code for correctness",
                max_chars=1300,
            )
            gap_block = control_tower._render_context_block(
                empty,
                "Second repair round: review coverage gap after an omitted changed file",
                max_chars=1600,
            )

            self.assertIn("GITHUB_GUIDANCE=", github_block)
            self.assertNotIn("PROMPT_AUTHORING_DISCIPLINE_V1=", github_block)
            self.assertIn("PROMPT_AUTHORING_DISCIPLINE_V1=", prompt_block)
            self.assertNotIn("GITHUB_GUIDANCE=", prompt_block)
            self.assertNotIn("GITHUB_GUIDANCE=", ordinary_block)
            self.assertNotIn("PROMPT_AUTHORING_DISCIPLINE_V1=", ordinary_block)
            self.assertNotIn("OPEN_CODE_REVIEW_DELEGATION=", generic_review_block)
            self.assertIn("OPEN_CODE_REVIEW_DELEGATION=USE_IF_AVAILABLE", gap_block)
            self.assertIn("GAP=MISSED_FILE,COVERAGE_GAP,REPEATED_REPAIR", gap_block)
            self.assertIn("NATIVE_REVIEW_FALLBACK", gap_block)
            self.assertIn("NONAUTHORITATIVE", gap_block)
            self.assertIn("Shield/native-code-impact/tests/task acceptance still required", gap_block)

    def test_identified_review_gap_cannot_be_silently_dropped_for_budget(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            empty = control_tower._experience_summary(root, "ordinary task")
            task = "Large diff with review coverage uncertainty"
            full = control_tower._render_context_block(empty, task, max_chars=1600)
            self.assertIn("OPEN_CODE_REVIEW_DELEGATION=", full)
            too_small = control_tower._render_context_block(empty, task, max_chars=650)
            self.assertEqual("", too_small)

    def test_start_command_preserves_law_and_persists_bounded_context(self) -> None:
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
                        "--root", str(root),
                        "start",
                        "--host", "CODEX",
                        "--goal-id", "CTX-ASSEMBLY",
                        "--goal", "GitHub merge exact head",
                        "--task-id", "TASK-1",
                        "--json",
                    ]
                )
            self.assertEqual(0, code)
            result = json.loads(output.getvalue())
            prompt = result["recommendation"]["PROMPT"]
            self.assertIn("P2P_SUPREME_LAW_PREFLIGHT:", prompt)
            self.assertIn("Canonical law source:", prompt)
            self.assertIn("SUPREME_LAW_CAPSULE:", prompt)
            self.assertIn(control_tower.CONTEXT_MARKER, prompt)
            self.assertIn("P2P_LAW_PREFLIGHT=", prompt)
            self.assertIn("repo-scoped portable=fresh|inline", prompt)
            self.assertIn("OE_GATE=", prompt)
            self.assertIn("GITHUB_GUIDANCE=", prompt)
            self.assertIn("XP=USE_ACTIVE_EXPERIENCE", prompt)
            self.assertIn(experience_id, prompt)
            self.assertLessEqual(len(prompt), control_tower.PROMPT_GUARD_CHARS)

            second = io.StringIO()
            with contextlib.redirect_stdout(second):
                second_code = control_tower.main(
                    [
                        "--root", str(root),
                        "start",
                        "--host", "CODEX",
                        "--goal-id", "CTX-ASSEMBLY",
                        "--goal", "GitHub merge exact head",
                        "--task-id", "TASK-1",
                        "--json",
                    ]
                )
            self.assertEqual(0, second_code)
            second_result = json.loads(second.getvalue())
            self.assertTrue(second_result["idempotent"])
            self.assertEqual(prompt, second_result["recommendation"]["PROMPT"])

    def test_review_gap_is_present_in_persisted_executor_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = control_tower.main(
                    [
                        "--root", str(root),
                        "start",
                        "--host", "ARENA",
                        "--goal-id", "OCR-GAP",
                        "--goal", "Second repair round after omitted files caused review coverage uncertainty",
                        "--task-id", "TASK-OCR-GAP",
                        "--json",
                    ]
                )
            self.assertEqual(0, code)
            prompt = json.loads(output.getvalue())["recommendation"]["PROMPT"]
            self.assertIn("OPEN_CODE_REVIEW_DELEGATION=USE_IF_AVAILABLE", prompt)
            self.assertIn("NATIVE_REVIEW_FALLBACK", prompt)
            self.assertLessEqual(len(prompt), control_tower.PROMPT_GUARD_CHARS)

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
                        "--root", str(root),
                        "start",
                        "--host", "ARENA",
                        "--goal-id", "BOUNDED-CONTEXT",
                        "--goal", "MongoDB pilot snapshot",
                        "--task-id", "TASK-LONG",
                        "--json",
                    ]
                )

            self.assertEqual(0, code)
            result = json.loads(output.getvalue())
            prompt = result["recommendation"]["PROMPT"]
            self.assertLessEqual(len(prompt), control_tower.PROMPT_GUARD_CHARS)
            self.assertIn("P2P_SUPREME_LAW_PREFLIGHT:", prompt)
            self.assertIn(control_tower.CONTEXT_MARKER, prompt)
            self.assertIn("XP=USE_ACTIVE_EXPERIENCE", prompt)
            self.assertNotIn("C" * 500, prompt)

    def test_exact_final_prompt_budget_never_weakens_guard(self) -> None:
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
            final_prompt = handoff.build_execution_prompt(binding, contextual)
            self.assertLessEqual(len(final_prompt), control_tower.PROMPT_GUARD_CHARS)
            self.assertIn("P2P_SUPREME_LAW_PREFLIGHT:", final_prompt)
            self.assertIn("P2P_LAW_PREFLIGHT=", final_prompt)
            self.assertIn("repo-scoped portable=fresh|inline", final_prompt)
            self.assertIn("OE_GATE=", final_prompt)


if __name__ == "__main__":
    unittest.main()
