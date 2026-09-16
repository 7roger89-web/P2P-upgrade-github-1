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

    def test_context_assembly_uses_only_matching_active_experience_and_is_read_only(self) -> None:
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

            task = control_tower._contextual_task(root, "Clone MongoDB pilot snapshot safely")

            self.assertEqual(before, ledger.read_bytes())
            self.assertIn(control_tower.CONTEXT_MARKER, task)
            self.assertIn("EXPERIENCE=USE_ACTIVE_EXPERIENCE", task)
            self.assertIn(experience_id, task)
            self.assertIn(correction, task)
            self.assertNotIn(lesson, task)
            self.assertIn("LAW_AUTHORITY=ONE", task)
            self.assertIn("projection/fallback only", task)
            self.assertIn("NON_AUTHORITATIVE", task)
            self.assertNotIn("CANONICAL_SUPREME_LAW: 7roger89-web", task)

    def test_unrelated_experience_is_not_injected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            lesson = "Require official provision-level provenance before claiming Vietnamese legal text correctness."
            self._activate_experience(
                root,
                triggers=("vnlaw", "official", "provenance"),
                lesson=lesson,
                correction="Compare the parsed provision against the official source and preserve provenance refs.",
            )

            task = control_tower._contextual_task(root, "Fix MongoDB shipment import pagination")

            self.assertIn("EXPERIENCE=NO_MATCH", task)
            self.assertNotIn(lesson, task)
            self.assertIn("LAW_AUTHORITY=ONE", task)

    def test_start_command_persists_compact_context_assembled_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            correction = "Compare current main, exact candidate head, mergeability, and exact-head checks before merge."
            self._activate_experience(
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
            self.assertIn(control_tower.CONTEXT_MARKER, prompt)
            self.assertIn("EXPERIENCE=USE_ACTIVE_EXPERIENCE", prompt)
            self.assertIn(correction, prompt)
            self.assertIn("P2P_SUPREME_LAW_PREFLIGHT:", prompt)
            self.assertLessEqual(len(prompt), 8192)

            # Same session is durable/idempotent: re-running start does not rebuild
            # the prompt from later chat context or create a second session record.
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

    def test_three_long_active_experiences_do_not_break_prompt_guard(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ids = []
            for index in range(3):
                ids.append(
                    self._activate_experience(
                        root,
                        triggers=("mongodb", "pilot", "snapshot"),
                        lesson=(f"Long historical lesson {index} " + "L" * 1800),
                        correction=(f"Risk wrapper {index}: " + "C" * 1800),
                        suffix=f"-{index}",
                    )
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
            self.assertLessEqual(len(prompt), 8192)
            self.assertEqual(1, prompt.count("ACTIVE_EXPERIENCE_REFS="))
            self.assertEqual(1, prompt.count("PRIMARY_RISK_WRAPPER="))
            for experience_id in ids:
                self.assertIn(experience_id, prompt)
            self.assertLess(prompt.count("C"), 400)


if __name__ == "__main__":
    unittest.main()
